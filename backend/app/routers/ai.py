"""
Endpoints que usan el componente de IA:
    - Mapa de calor predictivo (patrones por zona, dia y hora)
    - Resumen diario en lenguaje natural de un barrio
    - Vigia: asistente, reportes dictados por voz y ruta segura pedida por voz
"""

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from .. import models, schemas
from ..config import get_settings
from ..database import get_db
from ..security import get_current_user, get_optional_user
from ..serializers import reports_in_order
from ..services.engine import engine, ensure_aware
from ..services import ai_client
from ..services.geo import nearest_neighborhood
from ..services.report_service import to_local
from .routes import compute_safe_route

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    """Que modelos tiene configurados el componente de IA."""
    return ai_client.status()


@router.get("/heatmap", response_model=schemas.HeatmapOut)
def heatmap(
    days: int = Query(120, ge=7, le=730),
    neighborhood_id: Optional[int] = None,
    db: Database = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query: dict = {"occurred_at": {"$gte": since}, "status": {"$ne": "rejected"}}
    if neighborhood_id is not None:
        query["neighborhood_id"] = neighborhood_id
    reports = models.Report.find_light(db, query)
    neighborhoods = models.Neighborhood.find(db)
    names = {n.id: n.name for n in neighborhoods}

    payload = {
        "reports": [
            {
                "id": r.id,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "occurred_at": to_local(r.occurred_at).isoformat(),
                "severity": r.incident_type.severity_level,
                "incident_type_code": r.incident_type.code,
                "neighborhood_id": r.neighborhood_id,
            }
            for r in reports
        ],
        "neighborhoods": [
            {"id": n.id, "name": n.name, "latitude": n.latitude, "longitude": n.longitude} for n in neighborhoods
        ],
    }
    result = ai_client.heatmap(db, payload, neighborhood_id)

    if result is None:
        # Plan B si la IA no responde: pintamos los puntos crudos sin prediccion
        return schemas.HeatmapOut(
            available=False,
            model="sin-ia (puntos crudos)",
            reports_analyzed=len(reports),
            cells=[
                schemas.HeatCellOut(latitude=r.latitude, longitude=r.longitude, intensity=r.incident_type.severity_level / 5)
                for r in reports
            ],
            hotspots=[],
            neighborhood_risk=[],
            insights=["El componente de IA no esta disponible en este momento."],
        )

    # Guardamos las zonas calientes en la coleccion risk_hotspots
    hotspots = result.get("hotspots", [])
    affected = {h["neighborhood_id"] for h in hotspots}
    if affected:
        db.risk_hotspots.delete_many({"neighborhood_id": {"$in": list(affected)}})
    for h in hotspots:
        models.RiskHotspot(
            neighborhood_id=h["neighborhood_id"],
            day_of_week=h["day_of_week"],
            hour_block=h["hour_block"],
            risk_score=h["risk_score"],
            model_name=result.get("model", "unknown"),
        ).insert(db)

    return schemas.HeatmapOut(
        available=True,
        model=result.get("model", "unknown"),
        reports_analyzed=len(reports),
        cells=[schemas.HeatCellOut(**c) for c in result.get("cells", [])],
        hotspots=[
            schemas.HotspotOut(neighborhood_name=names.get(h["neighborhood_id"], "?"), **h) for h in hotspots[:20]
        ],
        neighborhood_risk=[
            {**nr, "neighborhood_name": names.get(nr["neighborhood_id"], "?")} for nr in result.get("neighborhood_risk", [])
        ],
        insights=result.get("insights", []),
    )


@router.get("/daily-summary", response_model=schemas.SummaryOut)
def daily_summary(
    neighborhood_id: int,
    summary_date: Optional[date] = Query(None, alias="date"),
    refresh: bool = False,
    db: Database = Depends(get_db),
):
    neighborhood = models.Neighborhood.get(db, neighborhood_id)
    if neighborhood is None:
        raise HTTPException(404, "Barrio no encontrado")
    tz = ZoneInfo(get_settings().timezone)
    day = summary_date or datetime.now(tz).date()

    cached = models.DailySummary.find_one(
        db, {"neighborhood_id": neighborhood_id, "summary_date": models.DailySummary.key(day)}
    )
    if cached is not None and not refresh:
        return schemas.SummaryOut(
            available=True,
            neighborhood=schemas.NeighborhoodOut.model_validate(neighborhood),
            summary_date=day,
            reports_count=cached.reports_count,
            summary_text=cached.summary_text,
            model=cached.model_name,
            cached=True,
        )

    day_start = datetime.combine(day, time.min, tzinfo=tz)
    week_start = day_start - timedelta(days=6)
    day_end = day_start + timedelta(days=1)
    rows = models.Report.find_light(
        db,
        {
            "neighborhood_id": neighborhood_id,
            "occurred_at": {"$gte": week_start, "$lt": day_end},
            "status": {"$ne": "rejected"},
        },
        sort=[("occurred_at", 1)],
    )

    def as_dict(r: models.Report) -> dict:
        return {
            "title": r.title,
            "description": r.description,
            "incident_type": r.incident_type.name,
            "severity": r.incident_type.severity_level,
            "status": r.status,
            "occurred_at": to_local(r.occurred_at).isoformat(),
        }

    today = [as_dict(r) for r in rows if to_local(r.occurred_at).date() == day]
    week = [as_dict(r) for r in rows]
    hotspots = models.RiskHotspot.find(db, {"neighborhood_id": neighborhood_id}, sort=[("risk_score", -1)], limit=3)

    payload = {
        "neighborhood_name": neighborhood.name,
        "city": neighborhood.city,
        "date": day.isoformat(),
        "reports": today,
        "week_reports": week,
        "hotspots": [{"day_of_week": h.day_of_week, "hour_block": h.hour_block, "risk_score": h.risk_score} for h in hotspots],
    }
    result = ai_client.summary(db, payload, neighborhood_id)
    if result is None:
        return schemas.SummaryOut(
            available=False,
            neighborhood=schemas.NeighborhoodOut.model_validate(neighborhood),
            summary_date=day,
            reports_count=len(today),
            summary_text=f"Hoy hay {len(today)} reportes en {neighborhood.name}. (El componente de IA no respondio.)",
            model="sin-ia",
        )

    if cached is None:
        cached = models.DailySummary(neighborhood_id=neighborhood_id, summary_date=models.DailySummary.key(day))
    cached.summary_text = result["summary"]
    cached.model_name = result.get("model", "unknown")
    cached.reports_count = len(today)
    cached.save(db)
    return schemas.SummaryOut(
        available=True,
        neighborhood=schemas.NeighborhoodOut.model_validate(neighborhood),
        summary_date=day,
        reports_count=len(today),
        summary_text=cached.summary_text,
        model=cached.model_name,
    )


@router.get("/hotspots", response_model=list[schemas.HotspotOut])
def stored_hotspots(neighborhood_id: Optional[int] = None, db: Database = Depends(get_db)):
    """Zonas calientes guardadas en la BD por el ultimo analisis."""
    query = {} if neighborhood_id is None else {"neighborhood_id": neighborhood_id}
    rows = models.RiskHotspot.find(db, query, sort=[("risk_score", -1)], limit=50)
    # En vez del JOIN de SQL, el nombre del barrio sale del catalogo en memoria
    return [
        schemas.HotspotOut(
            neighborhood_id=h.neighborhood_id,
            neighborhood_name=hood.name,
            day_of_week=h.day_of_week,
            hour_block=h.hour_block,
            risk_score=h.risk_score,
        )
        for h in rows
        if (hood := models.catalog.neighborhood(h.neighborhood_id)) is not None
    ]


def _time_ago(dt: datetime) -> str:
    minutes = int((datetime.now(timezone.utc) - ensure_aware(dt)).total_seconds() // 60)
    if minutes < 60:
        return f"hace {max(minutes, 1)} min"
    if minutes < 60 * 24:
        return f"hace {minutes // 60} h"
    return f"hace {minutes // (60 * 24)} dias"


@router.post("/chat", response_model=schemas.ChatOut)
def chat(
    data: schemas.ChatIn,
    db: Database = Depends(get_db),
    user: Optional[models.User] = Depends(get_optional_user),
):
    """Asistente: el vecino pregunta y la IA responde con los datos reales de la ciudad."""
    hood_id = data.neighborhood_id or (user.neighborhood_id if user else None)
    hood = models.Neighborhood.get(db, hood_id) if hood_id else None
    names = {d["_id"]: d["name"] for d in db.neighborhoods.find({}, {"name": 1})}
    counts = engine.active_count_by_zone()
    ranking = [
        {"neighborhood": names.get(nid, str(nid)), "active_alerts": counts.get(nid, 0), "active_severity": sev}
        for nid, sev in engine.ranking()
    ]

    since = datetime.now(timezone.utc) - timedelta(days=90)
    slots: Counter = Counter()
    for r in models.Report.find_light(db, {"occurred_at": {"$gte": since}, "status": {"$ne": "rejected"}}):
        local = to_local(r.occurred_at)
        slots[(r.neighborhood_id, local.weekday(), min(3, local.hour // 6))] += r.incident_type.severity_level
    hotspots = [
        {"neighborhood": names.get(nid, str(nid)), "day_of_week": d, "hour_block": b}
        for (nid, d, b), _ in slots.most_common(5)
    ]

    recent = reports_in_order(db, engine.feed_ids(hood.id if hood else None, 8))
    payload = {
        "question": data.question.strip(),
        "history": [h.model_dump() for h in data.history],
        "context": {
            "city": get_settings().city,
            "neighborhood": hood.name if hood else None,
            "neighborhoods": sorted(names.values()),
            "active_alerts": sum(counts.values()),
            "ranking": ranking[:8],
            "hotspots": hotspots,
            "recent": [
                {
                    "incident_type": r.incident_type.name,
                    "neighborhood": r.neighborhood.name,
                    "when": _time_ago(r.occurred_at),
                    "title": r.title,
                }
                for r in recent
            ],
        },
    }
    result = ai_client.chat(db, payload, hood.id if hood else None)
    if result is None:
        return schemas.ChatOut(
            available=False,
            model="no disponible",
            answer="La IA no esta disponible en este momento. Intenta de nuevo en un minuto.",
        )
    return schemas.ChatOut(available=True, answer=result["answer"], model=result["model"])


def _places(db: Database) -> list:
    return [{"id": d["_id"], "name": d["name"]} for d in db.neighborhoods.find({}, {"name": 1})]


@router.post("/report-draft", response_model=schemas.ReportDraftOut)
def report_draft(
    data: schemas.VoiceIn,
    db: Database = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """
    El vecino cuenta lo que paso (voz o texto) y Vigia arma el reporte.
    El barrio sale de la ubicacion del celular (GPS), salvo que nombre otro
    barrio; si no hay ninguno, se usa su barrio registrado. El vecino solo confirma.
    """
    types = models.IncidentType.find(db, sort=[("severity_level", -1)])
    payload = {
        "text": data.text.strip(),
        "city": get_settings().city,
        "incident_types": [{"code": t.code, "name": t.name} for t in types],
        "neighborhoods": _places(db),
    }
    result = ai_client.interpret_report(db, payload, user.neighborhood_id)
    if result is None:
        return schemas.ReportDraftOut(
            available=False, model="no disponible", message="Vigia no responde en este momento. Puedes usar el formulario."
        )

    incident_type = next((t for t in types if t.code == result.get("incident_type_code")), types[0])
    # Si nombra un barrio distinto al de su GPS, el incidente fue alla; si no, vale el GPS
    hood, source = None, None
    named = models.Neighborhood.get(db, result["neighborhood_id"]) if result.get("neighborhood_id") else None
    if data.latitude is not None and data.longitude is not None:
        hood, source = nearest_neighborhood(db, data.latitude, data.longitude), "gps"
    if named is not None and (hood is None or hood.id != named.id):
        hood, source = named, "texto"
    if hood is None and user.neighborhood_id:
        hood, source = models.Neighborhood.get(db, user.neighborhood_id), "perfil"

    lat, lng = (data.latitude, data.longitude) if source == "gps" else ((hood.latitude, hood.longitude) if hood else (None, None))
    title = (result.get("title") or incident_type.name).strip()
    description = (result.get("description") or data.text).strip()
    if len(description) < 10:
        description = f"{title}. {data.text.strip()}"
    return schemas.ReportDraftOut(
        available=True,
        model=result.get("model", "unknown"),
        message="" if hood else "No pude saber donde fue. Elige el barrio.",
        incident_type=schemas.IncidentTypeOut.model_validate(incident_type),
        neighborhood=schemas.NeighborhoodOut.model_validate(hood) if hood else None,
        title=title[:150] if len(title) >= 4 else incident_type.name,
        description=description[:2000],
        place=result.get("place"),
        latitude=lat,
        longitude=lng,
        location_source=source,
    )


@router.post("/route", response_model=schemas.VoiceRouteOut)
def voice_route(
    data: schemas.VoiceIn,
    db: Database = Depends(get_db),
    user: Optional[models.User] = Depends(get_optional_user),
):
    """'Estoy en la U, necesito ir al centro': Vigia entiende origen y destino y calcula la ruta segura."""
    payload = {"text": data.text.strip(), "city": get_settings().city, "neighborhoods": _places(db)}
    result = ai_client.interpret_route(db, payload, user.neighborhood_id if user else None)
    if result is None:
        return schemas.VoiceRouteOut(available=False, model="no disponible", message="Vigia no responde en este momento. Elige los barrios a mano.")

    origin_id, source = result.get("origin_id"), "texto"
    if origin_id is None and data.latitude is not None and data.longitude is not None:
        hood = nearest_neighborhood(db, data.latitude, data.longitude)
        origin_id, source = (hood.id if hood else None), "gps"
    if origin_id is None and user and user.neighborhood_id:
        origin_id, source = user.neighborhood_id, "perfil"
    destination_id = result.get("destination_id")
    model = result.get("model", "unknown")

    if destination_id is None:
        return schemas.VoiceRouteOut(available=True, model=model, message="¿Hacia donde vas? Dime el barrio o un lugar conocido.")
    if origin_id is None:
        return schemas.VoiceRouteOut(available=True, model=model, message="¿Desde donde sales? Activa tu ubicacion o dime el barrio.")
    if origin_id == destination_id:
        return schemas.VoiceRouteOut(available=True, model=model, message="Ya estas en ese barrio.", origin_source=source)
    try:
        route = compute_safe_route(db, origin_id, destination_id)
    except HTTPException as exc:
        return schemas.VoiceRouteOut(available=True, model=model, message=str(exc.detail), origin_source=source)
    names = " → ".join(n.name for n in route.safe_path)
    return schemas.VoiceRouteOut(
        available=True,
        model=model,
        message=f"Tu ruta segura: {names} ({route.safe_path_meters / 1000:.1f} km). {route.explanation}",
        origin_source=source,
        route=route,
    )
