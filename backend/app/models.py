"""
Modelo de datos en MongoDB (documentos y colecciones).

Reglas que usamos para pasar las 14 tablas de PostgreSQL a documentos
(salen del diagrama de clases):

    Composicion (solo existe dentro del otro)   -> documento EMBEBIDO
        fotos, historial de estados y confirmaciones van DENTRO del reporte;
        las vias (aristas del grafo) van DENTRO del barrio de origen.
    Asociacion (los dos tienen vida propia)     -> REFERENCIA por id
        el reporte guarda user_id, neighborhood_id, incident_type_id
        (+ copia del nombre del vecino, reporter_name, porque se muestra mucho).
    Rol del usuario                             -> un campo de texto en "users"
        (citizen, moderator o admin) en vez de la tabla "roles".

Colecciones:
    users, neighborhoods, incident_types, reports, subscriptions,
    notifications, counters

Cada clase es un "documento": from_doc() lo lee de Mongo y to_doc() lo
convierte para guardarlo. A diferencia de SQLAlchemy, en Mongo NO hay
guardado automatico: despues de cambiar un objeto hay que llamar save().
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Type, TypeVar

from pymongo.database import Database

from .database import get_database, next_id

REPORT_STATUSES = ("created", "in_review", "published", "verified", "rejected")
ROLES = {
    "citizen": "Vecino que reporta y recibe alertas",
    "moderator": "Revisa, publica o rechaza reportes",
    "admin": "Administra el sistema",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


T = TypeVar("T", bound="Document")


# =====================================================================
# Base: documento con coleccion propia
# =====================================================================
@dataclass
class Document:
    collection: ClassVar[str] = ""
    id: Optional[int] = None

    # ---------------------------------------------------- conversion
    @classmethod
    def from_doc(cls: Type[T], doc: Optional[dict]) -> Optional[T]:
        if doc is None:
            return None
        data = dict(doc)
        data["id"] = data.pop("_id", None)
        names = {f.name for f in fields(cls)}
        obj = cls(**{k: v for k, v in data.items() if k in names})
        obj._after_load()
        return obj

    def _after_load(self) -> None:
        """Las subclases convierten aqui los documentos embebidos."""

    def to_doc(self) -> dict:
        doc: Dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name == "id":
                doc["_id"] = value
            elif isinstance(value, list):
                doc[f.name] = [v.to_dict() if hasattr(v, "to_dict") else v for v in value]
            else:
                doc[f.name] = value
        return doc

    # ---------------------------------------------------- operaciones
    def insert(self, db: Database) -> "Document":
        if self.id is None:
            self.id = next_id(db, self.collection)
        db[self.collection].insert_one(self.to_doc())
        return self

    def save(self, db: Database) -> "Document":
        """Guarda TODO el documento (reemplaza el que habia)."""
        if self.id is None:
            return self.insert(db)
        db[self.collection].replace_one({"_id": self.id}, self.to_doc(), upsert=True)
        return self

    def delete(self, db: Database) -> None:
        db[self.collection].delete_one({"_id": self.id})

    @classmethod
    def get(cls: Type[T], db: Database, id_: Optional[int]) -> Optional[T]:
        if id_ is None:
            return None
        return cls.from_doc(db[cls.collection].find_one({"_id": int(id_)}))

    @classmethod
    def find_one(cls: Type[T], db: Database, query: dict) -> Optional[T]:
        return cls.from_doc(db[cls.collection].find_one(query))

    @classmethod
    def find(cls: Type[T], db: Database, query: Optional[dict] = None, sort: Optional[list] = None, limit: int = 0) -> List[T]:
        cursor = db[cls.collection].find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return [cls.from_doc(d) for d in cursor]

    @classmethod
    def count(cls, db: Database, query: Optional[dict] = None) -> int:
        return db[cls.collection].count_documents(query or {})


# =====================================================================
# Catalogos (barrios y tipos de incidente): casi nunca cambian, asi que se
# guardan en memoria para no ir a Mongo cada vez que un reporte muestra
# el nombre de su barrio o la gravedad de su tipo.
# =====================================================================
class _Catalog:
    def __init__(self) -> None:
        self.neighborhoods: Dict[int, "Neighborhood"] = {}
        self.incident_types: Dict[int, "IncidentType"] = {}

    def clear(self) -> None:
        self.neighborhoods.clear()
        self.incident_types.clear()

    def neighborhood(self, nid: Optional[int]) -> Optional["Neighborhood"]:
        if nid is None:
            return None
        if nid not in self.neighborhoods:
            hood = Neighborhood.get(get_database(), nid)
            if hood is None:
                return None
            self.neighborhoods[nid] = hood
        return self.neighborhoods[nid]

    def incident_type(self, tid: Optional[int]) -> Optional["IncidentType"]:
        if tid is None:
            return None
        if tid not in self.incident_types:
            t = IncidentType.get(get_database(), tid)
            if t is None:
                return None
            self.incident_types[tid] = t
        return self.incident_types[tid]


catalog = _Catalog()


# =====================================================================
# Documentos embebidos (no tienen coleccion propia)
# =====================================================================
@dataclass
class Embedded:
    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, d: dict):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})


@dataclass
class Connection(Embedded):
    """Via entre dos barrios (arista del grafo). Va dentro del barrio de origen."""

    to_neighborhood_id: int = 0
    distance_meters: float = 0.0
    road_name: Optional[str] = None


@dataclass
class ReportPhoto(Embedded):
    url: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class ReportStatusHistory(Embedded):
    """Cada elemento es un elemento de la PILA de estados del reporte."""

    id: int = 0  # id propio para poder deshacer (pop) exactamente ese cambio
    previous_status: Optional[str] = None
    new_status: str = "created"
    changed_by: Optional[int] = None
    note: Optional[str] = None
    changed_at: datetime = field(default_factory=utcnow)


@dataclass
class ReportVerification(Embedded):
    user_id: int = 0
    is_confirmed: bool = True
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)


# =====================================================================
# Colecciones
# =====================================================================
@dataclass
class Neighborhood(Document):
    collection: ClassVar[str] = "neighborhoods"
    name: str = ""
    city: str = ""
    comuna: Optional[int] = None  # comuna de Pasto (1 a 12)
    latitude: float = 0.0
    longitude: float = 0.0
    created_at: datetime = field(default_factory=utcnow)
    connections: List[Connection] = field(default_factory=list)

    def _after_load(self) -> None:
        self.connections = [Connection.from_dict(c) for c in self.connections]


@dataclass
class IncidentType(Document):
    collection: ClassVar[str] = "incident_types"
    code: str = ""
    name: str = ""
    severity_level: int = 1  # 5 = mas grave
    color: str = "#64748b"  # color en el mapa


@dataclass
class User(Document):
    collection: ClassVar[str] = "users"
    full_name: str = ""
    email: str = ""
    password_hash: str = ""
    phone: Optional[str] = None
    role: str = "citizen"  # citizen, moderator, admin
    neighborhood_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=utcnow)
    # Seguridad: al subir token_version se invalidan todas las sesiones abiertas
    token_version: int = 0
    # Verificacion en dos pasos (TOTP, compatible con Google Authenticator)
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    last_login_at: Optional[datetime] = None

    @property
    def neighborhood(self) -> Optional[Neighborhood]:
        return catalog.neighborhood(self.neighborhood_id)

    @classmethod
    def by_email(cls, db: Database, email: str) -> Optional["User"]:
        return cls.find_one(db, {"email": email.lower()})


@dataclass
class Report(Document):
    collection: ClassVar[str] = "reports"
    user_id: int = 0
    reporter_name: str = ""  # copia del nombre del vecino (se muestra en cada alerta)
    neighborhood_id: int = 0
    incident_type_id: int = 0
    title: str = ""
    description: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    address: Optional[str] = None  # direccion escrita o encontrada en el mapa
    occurred_at: datetime = field(default_factory=utcnow)
    status: str = "created"
    priority_score: float = 0.0
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    # ---- embebidos (composicion)
    photos: List[ReportPhoto] = field(default_factory=list)
    history: List[ReportStatusHistory] = field(default_factory=list)
    verifications: List[ReportVerification] = field(default_factory=list)

    def _after_load(self) -> None:
        self.photos = [ReportPhoto.from_dict(p) for p in self.photos]
        self.history = [ReportStatusHistory.from_dict(h) for h in self.history]
        self.verifications = [ReportVerification.from_dict(v) for v in self.verifications]

    def save(self, db: Database) -> "Report":
        self.updated_at = utcnow()
        return super().save(db)

    @property
    def neighborhood(self) -> Neighborhood:
        return catalog.neighborhood(self.neighborhood_id)

    @property
    def incident_type(self) -> IncidentType:
        return catalog.incident_type(self.incident_type_id)

    @property
    def confirmations(self) -> int:
        return sum(1 for v in self.verifications if v.is_confirmed)

    @classmethod
    def find_light(cls, db: Database, query: Optional[dict] = None, sort: Optional[list] = None) -> List["Report"]:
        """Reportes sin los embebidos (fotos, historial, confirmaciones): para estadisticas."""
        cursor = db[cls.collection].find(query or {}, {"photos": 0, "history": 0, "verifications": 0})
        if sort:
            cursor = cursor.sort(sort)
        return [cls.from_doc(d) for d in cursor]

    @classmethod
    def by_ids(cls, db: Database, ids: Iterable[int]) -> Dict[int, "Report"]:
        return {r.id: r for r in cls.find(db, {"_id": {"$in": list(ids)}})}


@dataclass
class Subscription(Document):
    """Vecino <-> barrio que sigue (asociacion: los dos existen por su cuenta)."""

    collection: ClassVar[str] = "subscriptions"
    user_id: int = 0
    neighborhood_id: int = 0
    created_at: datetime = field(default_factory=utcnow)

    @property
    def neighborhood(self) -> Neighborhood:
        return catalog.neighborhood(self.neighborhood_id)


@dataclass
class Notification(Document):
    collection: ClassVar[str] = "notifications"
    user_id: int = 0
    report_id: Optional[int] = None
    message: str = ""
    is_read: bool = False
    created_at: datetime = field(default_factory=utcnow)

