import os

# Las pruebas usan un MongoDB REAL: el de MONGODB_URI (servicio "mongo" en
# GitHub Actions) o, si no viene, el de la maquina (docker compose up mongodb).
# Siempre en una base aparte, "alertabarrio_test", que se borra al empezar.
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/alertabarrio_test")
# bcrypt con pocas rondas para que las pruebas sean rapidas
os.environ.setdefault("BCRYPT_ROUNDS", "4")
os.environ.setdefault("AUTH_RATE_LIMIT", "1000")

import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import get_client, get_database
from app.main import app

PASSWORD = "Alerta2026*"



@pytest.fixture(scope="session")
def client():
    get_client().drop_database(get_database().name)
    models.catalog.clear()
    with TestClient(app) as c:
        yield c


def login(client, email: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
