"""
Conexion a MongoDB con PyMongo.

- MONGODB_URI trae el servidor y el nombre de la base:
    local:  mongodb://localhost:27017/alertabarrio
    Atlas:  mongodb+srv://USUARIO:CLAVE@cluster0.xxxxx.mongodb.net/alertabarrio?retryWrites=true&w=majority
- Los ids siguen siendo NUMEROS ENTEROS (1, 2, 3...) para que el frontend y las
  estructuras de datos no cambien. Mongo no los genera solo, asi que usamos la
  coleccion "counters" (un contador por coleccion, incremento atomico con $inc).
"""

from functools import lru_cache
from typing import Generator

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database

from .config import get_settings

DEFAULT_DB_NAME = "alertabarrio"


@lru_cache
def get_client() -> MongoClient:
    # tz_aware=True: las fechas vuelven con zona horaria (UTC), igual que antes
    return MongoClient(get_settings().mongodb_uri, tz_aware=True, serverSelectionTimeoutMS=10_000)


def get_database() -> Database:
    client = get_client()
    try:
        return client.get_default_database()  # el nombre que viene en la URI
    except Exception:  # la URI no trae nombre de base
        return client[DEFAULT_DB_NAME]


def get_db() -> Generator[Database, None, None]:
    """Dependencia de FastAPI: entrega la base de datos (el cliente es compartido)."""
    yield get_database()


def next_id(db: Database, collection: str) -> int:
    """Siguiente id entero de una coleccion (contador atomico en 'counters')."""
    doc = db.counters.find_one_and_update(
        {"_id": collection}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return int(doc["seq"])


def reserve_ids(db: Database, collection: str, how_many: int) -> range:
    """Reserva varios ids seguidos con una sola consulta (para cargas masivas)."""
    doc = db.counters.find_one_and_update(
        {"_id": collection}, {"$inc": {"seq": how_many}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    last = int(doc["seq"])
    return range(last - how_many + 1, last + 1)


def ensure_indexes(db: Database) -> None:
    """Indices: unicos donde antes habia UNIQUE y simples donde se filtra mucho."""
    db.users.create_index("email", unique=True)
    db.neighborhoods.create_index("name", unique=True)
    db.incident_types.create_index("code", unique=True)
    db.reports.create_index("user_id")
    db.reports.create_index("neighborhood_id")
    db.reports.create_index("status")
    db.reports.create_index([("created_at", ASCENDING)])
    db.reports.create_index([("occurred_at", DESCENDING)])
    db.subscriptions.create_index([("user_id", ASCENDING), ("neighborhood_id", ASCENDING)], unique=True)
    db.subscriptions.create_index("neighborhood_id")
    db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
