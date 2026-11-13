from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_moderator
from ..services import report_service
from ..services.engine import engine

router = APIRouter(prefix="/api/v1", tags=["subscriptions & notifications"])


# ----------------------------------------------------------- suscripciones
@router.get("/subscriptions/me", response_model=List[schemas.SubscriptionOut])
def my_subscriptions(db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = models.Subscription.find(db, {"user_id": user.id}, sort=[("_id", 1)])
    return [
        schemas.SubscriptionOut(neighborhood=schemas.NeighborhoodOut.model_validate(s.neighborhood), created_at=s.created_at)
        for s in rows
    ]


@router.post("/subscriptions/{neighborhood_id}", status_code=201)
def subscribe(neighborhood_id: int, db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    if models.Neighborhood.get(db, neighborhood_id) is None:
        raise HTTPException(404, "Barrio no encontrado")
    try:
        models.Subscription(user_id=user.id, neighborhood_id=neighborhood_id).insert(db)
    except DuplicateKeyError:  # indice unico (user_id, neighborhood_id)
        raise HTTPException(409, "Ya estas suscrito a ese barrio")
    engine.subscribe(neighborhood_id, user.id)
    return {"subscribed": True, "subscribers_in_zone": engine.subscriber_count(neighborhood_id)}


@router.delete("/subscriptions/{neighborhood_id}")
def unsubscribe(neighborhood_id: int, db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    deleted = db.subscriptions.delete_one({"user_id": user.id, "neighborhood_id": neighborhood_id})
    if deleted.deleted_count == 0:
        raise HTTPException(404, "No estabas suscrito a ese barrio")
    engine.unsubscribe(neighborhood_id, user.id)
    return {"subscribed": False}


# --------------------------------------------------------- notificaciones
@router.get("/notifications/me", response_model=List[schemas.NotificationOut])
def my_notifications(db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    return models.Notification.find(db, {"user_id": user.id}, sort=[("created_at", -1), ("_id", -1)], limit=100)


@router.post("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(notification_id: int, db: Database = Depends(get_db), user: models.User = Depends(get_current_user)):
    n = models.Notification.get(db, notification_id)
    if n is None or n.user_id != user.id:
        raise HTTPException(404, "Notificacion no encontrada")
    n.is_read = True
    n.save(db)
    return n


@router.post("/notifications/dispatch")
def dispatch(db: Database = Depends(get_db), _: models.User = Depends(require_moderator)):
    """Despacha manualmente la COLA de notificaciones pendientes."""
    pending_before = len(engine.notification_queue)
    sent = report_service.dispatch_notifications(db)
    return {"pending_before": pending_before, "dispatched": sent}
