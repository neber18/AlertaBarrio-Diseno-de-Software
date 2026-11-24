"""Convierte objetos de la BD en los esquemas de salida."""

from typing import List, Optional

from pymongo.database import Database

from . import models, schemas
from .services.engine import ensure_aware


def user_out(user: models.User) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        neighborhood=schemas.NeighborhoodOut.model_validate(user.neighborhood) if user.neighborhood else None,
        created_at=ensure_aware(user.created_at),
        two_factor_enabled=bool(user.totp_enabled),
        last_login_at=ensure_aware(user.last_login_at) if user.last_login_at else None,
    )


def report_out(r: models.Report, confirmations: Optional[int] = None) -> schemas.ReportOut:
    return schemas.ReportOut(
        id=r.id,
        title=r.title,
        description=r.description,
        latitude=r.latitude,
        longitude=r.longitude,
        address=r.address,
        occurred_at=ensure_aware(r.occurred_at),
        created_at=ensure_aware(r.created_at),
        status=r.status,
        priority_score=r.priority_score,
        neighborhood=schemas.NeighborhoodOut.model_validate(r.neighborhood),
        incident_type=schemas.IncidentTypeOut.model_validate(r.incident_type),
        reporter_name=r.reporter_name,
        photos=[p.url for p in r.photos],
        confirmations=confirmations,
    )


def reports_in_order(db: Database, ids: List[int]) -> List[schemas.ReportOut]:
    """Trae los reportes de la BD respetando el orden que dio la estructura."""
    if not ids:
        return []
    by_id = models.Report.by_ids(db, ids)
    # las confirmaciones vienen embebidas en cada reporte
    return [report_out(by_id[i], by_id[i].confirmations) for i in ids if i in by_id]
