"""Logica de negocio de los reportes (cambios de estado + estructuras)."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from pymongo.database import Database

from .. import models
from ..config import get_settings
from ..database import next_id
from .engine import ReportItem, compute_priority, ensure_aware, engine

# Transiciones permitidas (maquina de estados del reporte)
ALLOWED = {
    "created": {"in_review", "rejected"},
    "in_review": {"published", "rejected"},
    "published": {"verified"},
    "verified": set(),
    "rejected": set(),
}

STATUS_ES = {
    "created": "creado",
    "in_review": "en revision",
    "published": "publicado",
    "verified": "verificado",
    "rejected": "rechazado",
}


def to_local(dt: datetime) -> datetime:
    return ensure_aware(dt).astimezone(ZoneInfo(get_settings().timezone))


def get_report_or_404(db: Database, report_id: int) -> models.Report:
    report = models.Report.get(db, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado")
    return report


def change_status(
    db: Database, report: models.Report, new_status: str, user: Optional[models.User], note: Optional[str] = None
) -> models.ReportStatusHistory:
    if new_status not in ALLOWED[report.status]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"No se puede pasar de '{STATUS_ES[report.status]}' a '{STATUS_ES[new_status]}'",
        )
    history = models.ReportStatusHistory(
        id=next_id(db, "report_status_history"),
        previous_status=report.status,
        new_status=new_status,
        changed_by=user.id if user else None,
        note=note,
    )
    report.status = new_status
    report.history.append(history)
    # El historial va embebido en el reporte: un solo update atomico
    # ($set del estado + $push a la lista), sin pisar otros campos.
    db.reports.update_one(
        {"_id": report.id},
        {"$set": {"status": new_status, "updated_at": models.utcnow()}, "$push": {"history": history.to_dict()}},
    )
    engine.push_status(report.id, history)  # PUSH en la pila de estados
    return history


def publish(db: Database, report: models.Report, moderator: models.User, note: Optional[str]) -> int:
    change_status(db, report, "published", moderator, note)
    message = f"Nueva alerta en {report.neighborhood.name}: {report.incident_type.name} - {report.title}"
    return engine.publish(report.id, report.user_id, message)


def undo(db: Database, report: models.Report) -> tuple[str, str]:
    """POP de la pila de estados + revertir en BD y en las demas estructuras."""
    try:
        undone, current = engine.pop_status(report.id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    report.history = [h for h in report.history if h.id != undone.history_id]
    report.status = current.new_status
    db.reports.update_one(
        {"_id": report.id},
        {"$set": {"status": report.status, "updated_at": models.utcnow()}, "$pull": {"history": {"id": undone.history_id}}},
    )

    was_active = undone.new_status in ("published", "verified")
    is_active = current.new_status in ("published", "verified")
    if was_active and not is_active:
        engine.unpublish(
            report.id,
            message=f"Se retiro la alerta '{report.title}' en {report.neighborhood.name} (publicada por error).",
        )
    if current.new_status == "created":
        engine.requeue(report.id)  # vuelve a la cola de prioridad
    return undone.new_status, current.new_status


def dispatch_notifications(db: Database) -> int:
    """Saca de la COLA las notificaciones pendientes y las guarda en la BD."""
    pending = engine.drain_notifications()
    for n in pending:
        models.Notification(user_id=n.user_id, report_id=n.report_id, message=n.message).insert(db)
    return len(pending)


# ===================================================================== crear reporte
@dataclass
class CreatedReport:
    """Resultado de crear un reporte: el documento y su puesto en la cola de moderacion."""

    report: models.Report
    queue_position: int


def create_report(db: Database, user: models.User, data) -> CreatedReport:
    """Ciclo completo de un reporte nuevo.

    1) valida tipo, barrio y fecha
    2) guarda en MongoDB con estado "created" (fotos e historial EMBEBIDOS)
    3) calcula la prioridad (gravedad + foto) y lo mete a la COLA DE PRIORIDAD de moderacion
    """
    incident_type = models.IncidentType.get(db, data.incident_type_id)
    neighborhood = models.Neighborhood.get(db, data.neighborhood_id)
    if incident_type is None or neighborhood is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tipo de incidente o barrio invalido")
    occurred_at = data.occurred_at or datetime.now(timezone.utc)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    if occurred_at > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha del incidente no puede ser futura")

    has_photo = bool(data.photo_url)
    first = models.ReportStatusHistory(
        id=next_id(db, "report_status_history"),
        previous_status=None,
        new_status="created",
        changed_by=user.id,
        note="Reporte creado",
    )
    report = models.Report(
        user_id=user.id,
        reporter_name=user.full_name,
        neighborhood_id=neighborhood.id,
        incident_type_id=incident_type.id,
        title=data.title.strip(),
        description=data.description.strip(),
        latitude=data.latitude,
        longitude=data.longitude,
        address=(data.address or "").strip() or None,
        occurred_at=occurred_at,
        status="created",
        priority_score=compute_priority(incident_type.severity_level, has_photo),
        photos=[models.ReportPhoto(url=data.photo_url)] if has_photo else [],
        history=[first],
    )
    report.insert(db)

    position = engine.add_report(ReportItem.from_model(report), first)
    return CreatedReport(report=report, queue_position=position)
