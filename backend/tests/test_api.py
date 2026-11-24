"""Pruebas del ciclo completo de la API."""

from datetime import datetime, timedelta, timezone

from app.services.engine import engine

from .conftest import PASSWORD, login


def test_hello(client):
    r = client.get("/api/v1/hello")
    assert r.status_code == 200
    body = r.json()
    assert body["project"] == "AlertaBarrio" and len(body["team"]) >= 1


def test_register_login_me(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Vecina Nueva", "email": "nueva@test.co", "password": "Secreta.123", "neighborhood_id": 1},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "nueva@test.co" and me.json()["role"] == "citizen"
    # correo repetido
    assert client.post(
        "/api/v1/auth/register", json={"full_name": "Otra", "email": "nueva@test.co", "password": "Secreta.123"}
    ).status_code == 409
    # contrasena mala
    assert client.post("/api/v1/auth/login", json={"email": "nueva@test.co", "password": "malamala"}).status_code == 401


def test_requires_auth(client):
    assert client.post("/api/v1/reports", json={}).status_code == 401
    citizen = login(client, "ana@alertabarrio.co")
    assert client.get("/api/v1/moderation/queue", headers=citizen).status_code == 403


def _type_id(client, code: str) -> int:
    return next(t["id"] for t in client.get("/api/v1/incident-types").json() if t["code"] == code)


def _new_report(client, headers, title="Me robaron con pistola", code="armed_robbery", hood=1, photo=True):
    body = {
        "title": title,
        "description": "Un hombre con pistola me quito el celular frente a la tienda",
        "incident_type_id": _type_id(client, code),
        "neighborhood_id": hood,
        "latitude": 1.2136,
        "longitude": -77.2811,
    }
    if photo:
        body["photo_url"] = "https://example.com/foto.jpg"
    return client.post("/api/v1/reports", headers=headers, json=body)


def test_full_cycle_with_priority_queue_and_stack(client):
    ana = login(client, "ana@alertabarrio.co")
    mod = login(client, "moderador@alertabarrio.co")

    # 1) El vecino crea el reporte -> cola de prioridad
    r = _new_report(client, ana)
    assert r.status_code == 201, r.text
    data = r.json()
    rid = data["report"]["id"]
    assert "ai" not in data
    # robo armado (gravedad 5) con foto: 5*20 + 5 = 105
    assert data["report"]["priority_score"] == 105.0
    assert data["queue_position"] == 1  # es el mas grave de la cola

    queue = client.get("/api/v1/moderation/queue", headers=mod).json()
    assert queue["reports"][0]["id"] == rid

    # 2) El moderador toma el siguiente (pop del heap) -> es este
    nxt = client.post("/api/v1/moderation/next", headers=mod).json()
    assert nxt["id"] == rid and nxt["status"] == "in_review"
    assert rid not in engine.moderation_queue

    # 3) Publicar -> entra al feed (lista enlazada) y se notifican los suscritos
    pub = client.post(f"/api/v1/moderation/reports/{rid}/publish", headers=mod, json={}).json()
    assert pub["report"]["status"] == "published" and pub["notifications_queued"] >= 1
    feed = client.get("/api/v1/feed", params={"neighborhood_id": 1}).json()
    assert feed[0]["id"] == rid
    carlos = login(client, "carlos@alertabarrio.co")
    notes = client.get("/api/v1/notifications/me", headers=carlos).json()
    assert any(n["report_id"] == rid for n in notes)

    # 4) Historial = pila (tope primero)
    hist = client.get(f"/api/v1/reports/{rid}/history").json()
    assert [h["new_status"] for h in hist] == ["published", "in_review", "created"]

    # 5) Deshacer publicacion -> sale del feed, vuelve a "en revision"
    undo = client.post(f"/api/v1/moderation/reports/{rid}/undo", headers=mod).json()
    assert undo["undone_status"] == "published" and undo["current_status"] == "in_review"
    assert rid not in [x["id"] for x in client.get("/api/v1/feed", params={"neighborhood_id": 1}).json()]

    # 6) Deshacer otra vez -> "created" y vuelve a la cola de prioridad
    undo = client.post(f"/api/v1/moderation/reports/{rid}/undo", headers=mod).json()
    assert undo["current_status"] == "created" and rid in engine.moderation_queue

    # 7) Ya no hay mas que deshacer
    assert client.post(f"/api/v1/moderation/reports/{rid}/undo", headers=mod).status_code == 409


def test_verification_by_neighbors(client):
    ana = login(client, "ana@alertabarrio.co")
    mod = login(client, "moderador@alertabarrio.co")
    rid = _new_report(client, ana, title="Robo para verificar").json()["report"]["id"]
    client.post(f"/api/v1/moderation/reports/{rid}/publish", headers=mod, json={})
    assert client.post(f"/api/v1/reports/{rid}/verify", headers=ana, json={}).status_code == 409  # propio
    r1 = client.post(f"/api/v1/reports/{rid}/verify", headers=login(client, "carlos@alertabarrio.co"), json={})
    assert r1.json()["status"] == "published"
    r2 = client.post(f"/api/v1/reports/{rid}/verify", headers=login(client, "laura@alertabarrio.co"), json={})
    assert r2.json()["status"] == "verified" and r2.json()["confirmations"] == 2


def test_reject_invalid_transition(client):
    ana = login(client, "ana@alertabarrio.co")
    mod = login(client, "moderador@alertabarrio.co")
    rid = _new_report(client, ana, title="Reporte falso").json()["report"]["id"]
    assert client.post(f"/api/v1/moderation/reports/{rid}/reject", headers=mod, json={}).json()["status"] == "rejected"
    assert client.post(f"/api/v1/moderation/reports/{rid}/publish", headers=mod, json={}).status_code == 409


def test_range_query_bst(client):
    now = datetime.now(timezone.utc)
    r = client.get("/api/v1/reports", params={"from": (now - timedelta(days=7)).isoformat(), "to": now.isoformat()})
    assert r.status_code == 200
    for rep in r.json():
        assert datetime.fromisoformat(rep["created_at"]) >= now - timedelta(days=7, seconds=1)


def test_safe_route_and_search(client):
    r = client.get("/api/v1/routes/safe", params={"from_id": 2, "to_id": 12})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["safe_path"][0]["id"] == 2 and body["safe_path"][-1]["id"] == 12
    assert client.get("/api/v1/neighborhoods/search", params={"name": "palermo"}).json()["name"] == "Palermo"




def test_ds_state(client):
    state = client.get("/api/v1/ds/state").json()
    for key in ("priority_queue", "status_stacks", "zone_feeds", "notification_queue", "timeline_bst", "city_graph"):
        assert key in state
    assert state["city_graph"]["connected"] is True


def test_weak_passwords_are_rejected(client):
    base = {"full_name": "Vecino Debil", "email": "debil@test.co"}
    for weak in ["Cort1*a", "sinmayuscula1*", "SINMINUSCULA1*", "SinNumero*", "SinSimbolo123", "A1*" + "ñ" * 40]:
        r = client.post("/api/v1/auth/register", json={**base, "password": weak[:72]})
        assert r.status_code == 422, weak
    assert client.post("/api/v1/auth/register", json={**base, "password": "Bien.Fuerte9"}).status_code == 201


def test_password_is_hashed_with_bcrypt(client):
    from app.database import get_database

    u = get_database().users.find_one({"email": "debil@test.co"})
    assert u["password_hash"].startswith("$2") and "Bien.Fuerte9" not in u["password_hash"]


def test_change_password(client):
    r = client.post("/api/v1/auth/login", json={"email": "debil@test.co", "password": "Bien.Fuerte9"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    bad = client.post("/api/v1/auth/change-password", headers=h, json={"current_password": "otra", "new_password": "Nueva.Clave1"})
    assert bad.status_code == 400
    ok = client.post("/api/v1/auth/change-password", headers=h, json={"current_password": "Bien.Fuerte9", "new_password": "Nueva.Clave1"})
    assert ok.status_code == 204
    assert client.post("/api/v1/auth/login", json={"email": "debil@test.co", "password": "Nueva.Clave1"}).status_code == 200


def test_login_lockout_after_failed_attempts(client):
    from app.security import login_throttle

    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "jorge@alertabarrio.co", "password": "mala"}).status_code == 401
    # ni con la contrasena correcta entra mientras este bloqueado
    r = client.post("/api/v1/auth/login", json={"email": "jorge@alertabarrio.co", "password": "Alerta2026*"})
    assert r.status_code == 429 and "Retry-After" in r.headers
    login_throttle.reset("jorge@alertabarrio.co")
    assert client.post("/api/v1/auth/login", json={"email": "jorge@alertabarrio.co", "password": "Alerta2026*"}).status_code == 200


def test_city_is_pasto_and_stats(client):
    assert client.get("/api/v1/hello").json()["city"] == "Pasto"
    hoods = client.get("/api/v1/neighborhoods").json()
    assert {h["city"] for h in hoods} == {"Pasto"} and any(h["name"] == "Centro" for h in hoods)
    stats = client.get("/api/v1/stats").json()
    assert stats["total_reports"] > 100 and len(stats["timeline"]) == 14
    assert stats["active_alerts"] == stats["by_status"]["published"] + stats["by_status"]["verified"]


def test_mongodb_document_model(client):
    """Composicion -> embebido (fotos, historial, confirmaciones); asociacion -> referencia por id."""
    from app.database import get_database

    db = get_database()
    # colecciones del modelo
    names = set(db.list_collection_names())
    assert {"users", "neighborhoods", "incident_types", "reports", "subscriptions", "notifications", "counters"} <= names
    assert "report_photos" not in names and "report_status_history" not in names and "roles" not in names

    # un reporte nuevo: ids enteros, referencias por id y TODO lo demas embebido
    ana = login(client, "ana@alertabarrio.co")
    hood = client.get("/api/v1/neighborhoods/search", params={"name": "Centro"}).json()
    it = client.get("/api/v1/incident-types").json()[0]
    r = client.post(
        "/api/v1/reports",
        headers=ana,
        json={
            "title": "Prueba de documento",
            "description": "Reporte para revisar como queda guardado en MongoDB",
            "incident_type_id": it["id"],
            "neighborhood_id": hood["id"],
            "latitude": hood["latitude"],
            "longitude": hood["longitude"],
            "photo_url": "https://example.com/foto.jpg",
        },
    )
    assert r.status_code == 201, r.text
    rid = r.json()["report"]["id"]
    doc = db.reports.find_one({"_id": rid})
    assert isinstance(doc["_id"], int)
    assert doc["neighborhood_id"] == hood["id"] and doc["incident_type_id"] == it["id"]
    assert doc["reporter_name"] == "Ana Rodriguez"
    assert doc["photos"][0]["url"] == "https://example.com/foto.jpg"
    assert [h["new_status"] for h in doc["history"]] == ["created"]
    assert doc["verifications"] == []

    # el correo es unico gracias al indice
    assert "email_1" in db.users.index_information()
    assert db.users.index_information()["email_1"].get("unique") is True





def _new_user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"full_name": "Prueba Segura", "email": email, "password": "Segura.2026"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_two_factor_login_flow(client):
    from app.security import totp_code

    h = _new_user(client, "dospasos@test.co")
    setup = client.post("/api/v1/auth/2fa/setup", headers=h).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/AlertaBarrio:")
    assert client.post("/api/v1/auth/2fa/enable", headers=h, json={"code": "000000"}).status_code == 400
    r = client.post("/api/v1/auth/2fa/enable", headers=h, json={"code": totp_code(setup["secret"])})
    assert r.status_code == 200 and r.json()["two_factor_enabled"] is True

    creds = {"email": "dospasos@test.co", "password": "Segura.2026"}
    r = client.post("/api/v1/auth/login", json=creds)
    assert r.status_code == 401 and r.headers.get("X-2FA-Required") == "true"
    assert client.post("/api/v1/auth/login", json={**creds, "otp": "123456"}).status_code == 401
    r = client.post("/api/v1/auth/login", json={**creds, "otp": totp_code(setup["secret"])})
    assert r.status_code == 200 and r.json()["user"]["last_login_at"]

    h2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
    off = client.post("/api/v1/auth/2fa/disable", headers=h2, json={"password": "Segura.2026", "code": totp_code(setup["secret"])})
    assert off.status_code == 200 and off.json()["two_factor_enabled"] is False
    assert client.post("/api/v1/auth/login", json=creds).status_code == 200


def test_logout_all_invalidates_old_tokens(client):
    old = _new_user(client, "sesiones@test.co")
    assert client.get("/api/v1/auth/me", headers=old).status_code == 200
    r = client.post("/api/v1/auth/logout-all", headers=old)
    assert r.status_code == 200
    assert client.get("/api/v1/auth/me", headers=old).status_code == 401
    new = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=new).status_code == 200


def test_rate_limiter_and_security_headers(client):
    from app.security import RateLimiter, totp_code, verify_totp

    limiter = RateLimiter()
    assert [limiter.hit("1.2.3.4", 3, 60) for _ in range(3)] == [0, 0, 0]
    assert limiter.hit("1.2.3.4", 3, 60) > 0
    assert limiter.hit("5.6.7.8", 3, 60) == 0
    # vector de prueba del RFC 6238 (secreto "12345678901234567890", t = 59 s)
    assert totp_code("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", at=59) == "287082"
    assert not verify_totp("GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ", "abc")
    r = client.get("/api/v1/hello")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"



def test_login_checks_account_type(client):
    def login_as(email, kind):
        return client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD, "account_type": kind})

    assert login_as("ana@alertabarrio.co", "user").status_code == 200
    assert login_as("ana@alertabarrio.co", "admin").status_code == 403
    assert login_as("moderador@alertabarrio.co", "admin").status_code == 200
    assert login_as("moderador@alertabarrio.co", "user").status_code == 403


def test_cuenta_profesor(client, monkeypatch):
    from app.config import get_settings
    from app.database import get_database
    from app.seed import ensure_profesor

    monkeypatch.setattr(get_settings(), "profesor_password", "Profe.Pasto26")
    db = get_database()
    ensure_profesor(db)
    ensure_profesor(db)  # no duplica
    assert db.users.count_documents({"email": "profesor@alertabarrio.co"}) == 1
    r = client.post("/api/v1/auth/login", json={"email": "profesor@alertabarrio.co", "password": "Profe.Pasto26"})
    assert r.status_code == 200, r.text
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).json()
    assert me["role"] == "admin"


def test_nearest_neighborhood(client):
    r = client.get("/api/v1/neighborhoods/nearest", params={"lat": 1.2136, "lng": -77.2811})
    assert r.status_code == 200 and r.json()["name"] == "Centro"




def test_priority_without_photo_is_lower(client):
    ana = login(client, "ana@alertabarrio.co")
    r = _new_report(client, ana, title="Hurto sin foto", code="theft", photo=False)
    assert r.status_code == 201, r.text
    theft = next(t for t in client.get("/api/v1/incident-types").json() if t["code"] == "theft")
    assert r.json()["report"]["priority_score"] == theft["severity_level"] * 20.0
