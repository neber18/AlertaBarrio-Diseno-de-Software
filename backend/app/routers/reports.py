"""
Reportes de seguridad.

Los routers son los CONTROLADORES (GRASP): reciben la peticion, delegan en
services/report_service.py y arman la respuesta. El ciclo completo de un reporte
(guardar -> prioridad -> cola de moderacion) esta en report_service.create_report().
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.database import Database

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..security import get_current_user
from ..serializers import report_out, reports_in_order
from ..services import report_service
from ..services.engine import engine
from ..services.report_service import change_status, get_report_or_404

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.post("/reports", response_model=schemas.ReportCreatedOut, status_code=201)
def create_report(
    data: schemas.ReportIn,
    db: Database = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Controlador del caso de uso "reportar": solo recibe, delega y responde."""
    created = report_service.create_report(db, user, data)
    return schemas.ReportCreatedOut(
        report=report_out(created.report, 0),
        queue_position=created.queue_position,
        queue_size=len(engine.moderation_queue),
    )



@router.get("/reports", response_model=List[schemas.ReportOut])
def list_reports(
    date_from: Optional[datetime] = Query(None, alias="from"),
    date_to: Optional[datetime] = Query(None, alias="to"),
    neighborhood_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(200, le=1000),
    db: Database = Depends(get_db),
):
    """Historial por rango de fechas usando el ARBOL BINARIO DE BUSQUEDA."""
    end = date_to or datetime.now(timezone.utc)
    start = date_from or (end - timedelta(days=30))
    ids = engine.range_ids(start, end)
    ids.reverse()  # mas recientes primero
    if neighborhood_id is not None or status_filter is not None:
        filtered = []
        for rid in ids:
            item = engine.get_item(rid)
            if item is None:
                continue
            if neighborhood_id is not None and item.neighborhood_id != neighborhood_id:
                continue
            if status_filter is not None and item.status != status_filter:
                continue
            filtered.append(rid)
        ids = filtered
    return reports_in_order(db, ids[:limit])


@router.get("/reports/map", response_model=List[schemas.ReportOut])
def map_reports(db: Database = Depends(get_db)):
    """Alertas activas (publicadas o verificadas) para pintar en el mapa."""
    return reports_in_order(db, engine.feed_ids(None, limit=500))


@router.get("/reports/mine", response_model=List[schemas.ReportOut])
def my_reports(db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = models.Report.find(db, {"user_id": user.id}, sort=[("created_at", -1)])
    return [report_out(r, r.confirmations) for r in rows]


@router.get("/feed", response_model=List[schemas.ReportOut])
def feed(neighborhood_id: Optional[int] = None, limit: int = Query(50, le=200), db: Database = Depends(get_db)):
    """Feed de alertas activas. Por barrio = LISTA ENLAZADA; general = merge sort por prioridad."""
    return reports_in_order(db, engine.feed_ids(neighborhood_id, limit))


@router.get("/reports/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: int, db: Database = Depends(get_db)):
    report = get_report_or_404(db, report_id)
    return report_out(report, report.confirmations)


@router.get("/reports/{report_id}/history", response_model=List[schemas.StatusEntryOut])
def report_history(report_id: int, db: Database = Depends(get_db)):
    """La PILA de estados del reporte, del tope a la base."""
    get_report_or_404(db, report_id)
    return [schemas.StatusEntryOut(**e.to_dict()) for e in engine.status_stack(report_id)]


@router.post("/reports/{report_id}/verify", response_model=schemas.ReportOut)
def verify_report(
    report_id: int,
    data: schemas.VerifyIn,
    db: Database = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Un vecino confirma que la alerta es real. Con N confirmaciones pasa a 'verified'."""
    report = get_report_or_404(db, report_id)
    if report.status not in ("published", "verified"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se pueden confirmar alertas publicadas")
    if report.user_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes confirmar tu propio reporte")
    verification = models.ReportVerification(user_id=user.id, is_confirmed=data.is_confirmed, comment=data.comment)
    # $push solo si este vecino aun no aparece en la lista (una confirmacion por vecino, atomico)
    result = db.reports.update_one(
        {"_id": report.id, "verifications.user_id": {"$ne": user.id}},
        {"$push": {"verifications": verification.to_dict()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya confirmaste este reporte")
    report.verifications.append(verification)
    count = report.confirmations
    if report.status == "published" and count >= get_settings().verifications_required:
        change_status(db, report, "verified", user, f"Verificado por {count} vecinos")
    return report_out(report, count)
