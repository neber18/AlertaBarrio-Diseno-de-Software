"""
Datos de ejemplo para que el sistema arranque con informacion realista:
barrios de Pasto, sus conexiones (grafo), tipos de incidente, usuarios de
prueba y ~3 meses de reportes historicos con PATRONES (por ejemplo, robos
en el Centro los jueves y viernes en la noche) para que el ranking y las consultas por fecha muestren datos reales.

Se ejecuta solo si la base de datos esta vacia (coleccion "users" sin documentos).
Uso manual:  python -m app.seed
"""

import math
import random
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from pymongo import ReplaceOne
from pymongo.database import Database

from . import models
from .barrios_pasto import BARRIOS
from .config import get_settings
from .database import ensure_indexes, get_database, reserve_ids
from .security import hash_password


CITY = get_settings().city

# Barrios de San Juan de Pasto (coordenadas aproximadas del centro de cada barrio)
NEIGHBORHOODS = [
    ("Centro", 1.2136, -77.2811),
    ("Pandiaco", 1.2295, -77.2862),
    ("Las Cuadras", 1.2188, -77.2783),
    ("Palermo", 1.2236, -77.2742),
    ("Torobajo", 1.2318, -77.2927),
    ("Anganoy", 1.2163, -77.2985),
    ("Mijitayo", 1.2068, -77.2925),
    ("Lorenzo de Aldana", 1.1968, -77.2728),
    ("Chapultepec", 1.2022, -77.2838),
    ("Obrero", 1.2085, -77.2762),
    ("Potrerillo", 1.2028, -77.2693),
    ("San Felipe", 1.2167, -77.2848),
    ("Santa Monica", 1.2118, -77.2668),
    ("El Tejar", 1.2052, -77.2603),
]

CONNECTIONS = [
    ("Pandiaco", "Torobajo", "Avenida Panamericana"),
    ("Pandiaco", "Palermo", "Avenida de los Estudiantes"),
    ("Pandiaco", "Las Cuadras", "Carrera 27"),
    ("Torobajo", "Anganoy", "Avenida Panamericana"),
    ("Torobajo", "San Felipe", "Calle 22"),
    ("Palermo", "Las Cuadras", "Calle 20"),
    ("Palermo", "Santa Monica", "Avenida Panamericana"),
    ("Las Cuadras", "Centro", "Carrera 25"),
    ("Las Cuadras", "San Felipe", "Carrera 24"),
    ("San Felipe", "Centro", "Calle 18"),
    ("San Felipe", "Anganoy", "Calle 18"),
    ("Anganoy", "Mijitayo", "Avenida Mijitayo"),
    ("Mijitayo", "Chapultepec", "Avenida Idema"),
    ("Chapultepec", "Centro", "Carrera 27"),
    ("Chapultepec", "Obrero", "Carrera 22"),
    ("Chapultepec", "Lorenzo de Aldana", "Avenida Panamericana"),
    ("Centro", "Obrero", "Avenida Boyaca"),
    ("Centro", "Santa Monica", "Calle 19"),
    ("Obrero", "Potrerillo", "Calle 16"),
    ("Potrerillo", "Lorenzo de Aldana", "Avenida Chile"),
    ("Potrerillo", "El Tejar", "Avenida Julian Bucheli"),
    ("Santa Monica", "El Tejar", "Avenida Santander"),
    ("Santa Monica", "Potrerillo", "Carrera 16"),
]

INCIDENT_TYPES = [
    ("armed_robbery", "Robo armado", 5, "#b91c1c"),
    ("assault", "Agresion o rina", 4, "#dc2626"),
    ("home_burglary", "Robo a vivienda", 4, "#ea580c"),
    ("vehicle_theft", "Robo de vehiculo", 4, "#f97316"),
    ("theft", "Hurto", 3, "#f59e0b"),
    ("drug_dealing", "Expendio de drogas", 3, "#9333ea"),
    ("vandalism", "Vandalismo", 2, "#2563eb"),
    ("suspicious_activity", "Actividad sospechosa", 2, "#64748b"),
]

TEXTS = {
    "armed_robbery": [
        ("Atraco con arma blanca", "Dos hombres en moto me amenazaron con cuchillo y se llevaron el celular."),
        ("Robo con pistola en la esquina", "Un sujeto armado con pistola robo a una pareja que salia del restaurante."),
        ("Asalto a mano armada", "Atracaron a un domiciliario con arma de fuego y le quitaron la moto."),
    ],
    "assault": [
        ("Rina en la salida del bar", "Varias personas se agarraron a golpes, hay un herido."),
        ("Agresion a un vecino", "Un hombre golpeo a un vecino en el parque, llamamos a la policia."),
    ],
    "home_burglary": [
        ("Se metieron a una casa", "Forzaron la puerta y se llevaron el televisor y un computador."),
        ("Robo en apartamento", "Entraron por la ventana del primer piso mientras la familia dormia."),
    ],
    "vehicle_theft": [
        ("Se robaron un carro", "Hurtaron un carro parqueado en la calle, rompieron el vidrio."),
        ("Robo de moto", "Se llevaron una moto que estaba frente a la panaderia."),
    ],
    "theft": [
        ("Raponazo de celular", "Le arrebataron el celular a una senora en el paradero del bus."),
        ("Hurto en el transporte", "En el bus le sacaron la billetera del bolsillo a un estudiante."),
        ("Cosquilleo en el centro comercial", "Le robaron el bolso a una mujer sin que se diera cuenta."),
    ],
    "drug_dealing": [
        ("Venta de droga en el parque", "Todas las noches hay personas vendiendo droga cerca a los columpios."),
        ("Olla en la cuadra", "Hay mucho movimiento de gente comprando sustancias en una casa."),
    ],
    "vandalism": [
        ("Danaron el alumbrado", "Rompieron las lamparas del parque y quedo totalmente oscuro."),
        ("Grafitis y vidrios rotos", "Rayaron las paredes del colegio y rompieron vidrios."),
    ],
    "suspicious_activity": [
        ("Persona sospechosa mirando casas", "Un hombre lleva varias horas mirando las casas y tomando fotos."),
        ("Carro sospechoso estacionado", "Un carro sin placas lleva rato parqueado con dos personas adentro."),
    ],
}

# (barrio, tipos, dias_semana, franjas_horarias, peso) -> patrones de ejemplo en los datos
PATTERNS = [
    ("Centro", ["armed_robbery", "theft"], [3, 4], [19, 20, 21, 22, 23], 40),  # jueves/viernes noche
    ("Lorenzo de Aldana", ["theft", "assault"], [5, 6], [13, 14, 15, 16, 17], 14),  # fin de semana tarde
    ("Potrerillo", ["theft", "drug_dealing"], [0, 1, 2, 3, 4], [9, 10, 11, 12], 14),  # entre semana manana
    ("Torobajo", ["home_burglary", "vehicle_theft"], [0, 1, 2, 3, 4, 5, 6], [1, 2, 3, 4], 12),  # madrugada
    ("San Felipe", ["theft"], [4, 5], [18, 19, 20], 8),
    ("El Tejar", ["assault", "drug_dealing"], [4, 5], [21, 22, 23], 8),
]


def _distance_m(a, b) -> float:
    """Distancia aproximada (haversine) * 1.3 porque las calles no son rectas."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * 6371000 * math.asin(math.sqrt(h)) * 1.3, 0)


class _Ids:
    """Ids enteros consecutivos para el seed (se asignan en memoria y al final
    se sube el contador de cada coleccion, asi no se hace una consulta por id)."""

    def __init__(self) -> None:
        self.last = {}

    def next(self, name: str) -> int:
        self.last[name] = self.last.get(name, 0) + 1
        return self.last[name]

    def save(self, db: Database) -> None:
        for name, value in self.last.items():
            db.counters.update_one({"_id": name}, {"$max": {"seq": value}}, upsert=True)


def seed(db: Database) -> bool:
    if db.users.count_documents({}, limit=1):
        return False  # ya tiene datos

    rng = random.Random(2026)
    tz = ZoneInfo(get_settings().timezone)
    now = datetime.now(timezone.utc)
    ids = _Ids()

    hoods = {
        name: models.Neighborhood(id=ids.next("neighborhoods"), name=name, city=CITY, latitude=lat, longitude=lon)
        for name, lat, lon in NEIGHBORHOODS
    }
    # Las vias (aristas del grafo) van EMBEBIDAS en el barrio de origen
    for a, b, road in CONNECTIONS:
        ha, hb = hoods[a], hoods[b]
        ha.connections.append(
            models.Connection(
                to_neighborhood_id=hb.id,
                distance_meters=_distance_m((ha.latitude, ha.longitude), (hb.latitude, hb.longitude)),
                road_name=road,
            )
        )
    db.neighborhoods.insert_many([h.to_doc() for h in hoods.values()])

    types = {
        code: models.IncidentType(id=ids.next("incident_types"), code=code, name=name, severity_level=sev, color=color)
        for code, name, sev, color in INCIDENT_TYPES
    }
    db.incident_types.insert_many([t.to_doc() for t in types.values()])

    pwd = hash_password(get_settings().demo_password)
    users_data = [
        ("Administrador AlertaBarrio", "admin@alertabarrio.co", "admin", None),
        ("Moderador Central", "moderador@alertabarrio.co", "moderator", "Centro"),
        ("Ana Rodriguez", "ana@alertabarrio.co", "citizen", "Centro"),
        ("Carlos Gomez", "carlos@alertabarrio.co", "citizen", "Centro"),
        ("Laura Martinez", "laura@alertabarrio.co", "citizen", "Lorenzo de Aldana"),
        ("Pedro Sanchez", "pedro@alertabarrio.co", "citizen", "Torobajo"),
        ("Valentina Ruiz", "valentina@alertabarrio.co", "citizen", "Potrerillo"),
        ("Jorge Herrera", "jorge@alertabarrio.co", "citizen", "Las Cuadras"),
    ]
    users = [
        models.User(
            id=ids.next("users"),
            full_name=full_name,
            email=email,
            password_hash=pwd,
            phone=f"300{rng.randint(1000000, 9999999)}",
            role=role,
            neighborhood_id=hoods[hood].id if hood else None,
        )
        for full_name, email, role, hood in users_data
    ]
    db.users.insert_many([u.to_doc() for u in users])
    citizens = [u for u in users if u.role == "citizen"]
    moderator = users[1]

    # Suscripciones: cada vecino a su barrio + algunos barrios extra
    subs = {(u.id, u.neighborhood_id) for u in citizens}
    subs |= {(citizens[0].id, hoods["Las Cuadras"].id), (citizens[1].id, hoods["Potrerillo"].id), (citizens[5].id, hoods["Centro"].id)}
    subs |= {(moderator.id, hoods["Centro"].id)}
    db.subscriptions.insert_many(
        [models.Subscription(id=ids.next("subscriptions"), user_id=uid, neighborhood_id=nid).to_doc() for uid, nid in sorted(subs)]
    )

    # -------------------------------------------------- reportes historicos
    def random_moment(days_back_max: int, weekdays, hours) -> datetime:
        while True:
            d = now.astimezone(tz) - timedelta(days=rng.randint(1, days_back_max))
            if d.weekday() in weekdays:
                local = d.replace(hour=rng.choice(hours), minute=rng.randint(0, 59), second=0, microsecond=0)
                return local.astimezone(timezone.utc)

    plan = []
    for hood, codes, days, hours, count in PATTERNS:
        for _ in range(count):
            plan.append((hood, rng.choice(codes), random_moment(90, days, hours)))
    # ruido: reportes al azar en toda la ciudad
    for _ in range(45):
        hood = rng.choice(NEIGHBORHOODS)[0]
        code = rng.choice(list(TEXTS.keys()))
        plan.append((hood, code, random_moment(90, range(7), list(range(24)))))
    # reportes de HOY (para el resumen diario) y pendientes de moderar
    recent = [
        ("Centro", "armed_robbery", 1, "published"),
        ("Centro", "theft", 3, "verified"),
        ("Centro", "suspicious_activity", 5, "published"),
        ("Lorenzo de Aldana", "assault", 2, "published"),
        ("Potrerillo", "theft", 4, "published"),
        ("Centro", "theft", 0.5, "created"),
        ("Torobajo", "home_burglary", 0.8, "created"),
        ("Las Cuadras", "suspicious_activity", 0.3, "created"),
        ("Lorenzo de Aldana", "armed_robbery", 0.2, "created"),
        ("El Tejar", "vandalism", 0.6, "created"),
        ("Anganoy", "vehicle_theft", 1.5, "in_review"),
    ]
    reports = []

    def make_report(hood_name, code, occurred, status_target):
        hood = hoods[hood_name]
        it = types[code]
        title, desc = rng.choice(TEXTS[code])
        reporter = rng.choice(citizens)
        created = occurred + timedelta(minutes=rng.randint(3, 40))
        if created > now:
            created = now - timedelta(minutes=1)
        r = models.Report(
            id=ids.next("reports"),
            user_id=reporter.id,
            reporter_name=reporter.full_name,
            neighborhood_id=hood.id,
            incident_type_id=it.id,
            title=title,
            description=desc,
            latitude=hood.latitude + rng.gauss(0, 0.0018),
            longitude=hood.longitude + rng.gauss(0, 0.0018),
            occurred_at=occurred,
            status=status_target,
            priority_score=it.severity_level * 20.0,
            created_at=created,
            updated_at=created,
        )
        # Historial de estados (la PILA) coherente con el estado final, embebido en el reporte
        path = {
            "created": ["created"],
            "in_review": ["created", "in_review"],
            "published": ["created", "in_review", "published"],
            "verified": ["created", "in_review", "published", "verified"],
            "rejected": ["created", "in_review", "rejected"],
        }[status_target]
        t = created
        prev = None
        for st in path:
            r.history.append(
                models.ReportStatusHistory(
                    id=ids.next("report_status_history"),
                    previous_status=prev,
                    new_status=st,
                    changed_by=reporter.id if st == "created" else moderator.id,
                    note="Reporte creado" if st == "created" else None,
                    changed_at=t,
                )
            )
            prev = st
            t = min(t + timedelta(minutes=rng.randint(5, 50)), now)
        if status_target == "verified":
            others = [c for c in citizens if c.id != reporter.id]
            for v in rng.sample(others, 2):
                r.verifications.append(models.ReportVerification(user_id=v.id, is_confirmed=True))
        reports.append(r)
        return r

    plan.sort(key=lambda p: p[2])
    for hood_name, code, occurred in plan:
        status_target = rng.choices(["published", "verified", "rejected"], weights=[55, 35, 10])[0]
        make_report(hood_name, code, occurred, status_target)
    last = None
    for hood_name, code, hours_ago, status_target in recent:
        last = make_report(hood_name, code, now - timedelta(hours=hours_ago), status_target)
    db.reports.insert_many([r.to_doc() for r in reports])

    ana = citizens[0]
    db.notifications.insert_many(
        [
            models.Notification(
                id=ids.next("notifications"), user_id=ana.id, report_id=last.id if last else None, message=msg
            ).to_doc()
            for msg in [
                "Nueva alerta en Centro: Robo armado - Atraco con arma blanca",
                "Nueva alerta en Centro: Hurto - Raponazo de celular",
            ]
        ]
    )
    ids.save(db)
    return True


def _norm(name: str) -> str:
    """Minusculas y sin tildes: 'Santa Mónica' y 'Santa Monica' son el mismo barrio."""
    return "".join(c for c in unicodedata.normalize("NFD", name.lower()) if unicodedata.category(c) != "Mn").strip()


def sync_pasto_barrios(db: Database) -> int:
    """
    Agrega los barrios de Pasto que falten (lista completa por comuna en
    barrios_pasto.py) y conecta cada barrio nuevo con sus vecinos en el grafo.

    No borra nada y conserva los ids. Si un barrio que ya existia cambia de
    punto (para quedar dentro de su comuna), sus reportes se corren con el.
    Devuelve cuantos barrios agrego; si ya esta todo, no hace nada.
    """
    hoods = models.Neighborhood.find(db)
    by_norm = {_norm(h.name): h for h in hoods}
    if all(_norm(n) in by_norm and by_norm[_norm(n)].comuna == k for n, k, _, _ in BARRIOS):
        return 0

    missing = [b for b in BARRIOS if _norm(b[0]) not in by_norm]
    new_ids_iter = iter(reserve_ids(db, "neighborhoods", len(missing)) if missing else [])
    added = []
    for name, comuna, lat, lon in BARRIOS:
        hood = by_norm.get(_norm(name))
        if hood is None:
            hood = models.Neighborhood(id=next(new_ids_iter), name=name, city=CITY, comuna=comuna, latitude=lat, longitude=lon)
            by_norm[_norm(name)] = hood
            hoods.append(hood)
            added.append(hood)
            continue
        if hood.comuna is None and (hood.latitude, hood.longitude) != (lat, lon):
            dlat, dlon = lat - hood.latitude, lon - hood.longitude
            # los reportes del barrio se corren con el (un solo update_many)
            db.reports.update_many({"neighborhood_id": hood.id}, {"$inc": {"latitude": dlat, "longitude": dlon}})
            hood.latitude, hood.longitude = lat, lon
        hood.comuna = comuna

    # Grafo: cada barrio se une con sus 3 vecinos mas cercanos y luego se
    # agregan las uniones minimas (Kruskal) para que toda la ciudad quede conectada.
    by_id = {h.id: h for h in hoods}
    pos = {h.id: (h.latitude, h.longitude) for h in hoods}
    pairs = set()
    for h in hoods:
        for c in h.connections:
            pairs.add(frozenset((h.id, c.to_neighborhood_id)))

    def connect(a: int, b: int) -> None:
        key = frozenset((a, b))
        if a == b or key in pairs:
            return
        pairs.add(key)
        by_id[a].connections.append(
            models.Connection(to_neighborhood_id=b, distance_meters=_distance_m(pos[a], pos[b]), road_name=None)
        )

    new_ids = {h.id for h in added}
    for h in added:
        near = sorted((o for o in pos if o != h.id), key=lambda o: _distance_m(pos[h.id], pos[o]))[:3]
        for o in near:
            connect(h.id, o)

    parent = {i: i for i in pos}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for key in pairs:
        a, b = tuple(key)
        parent[find(a)] = find(b)
    if len({find(i) for i in pos}) > 1:
        ids_ = list(pos)
        edges = sorted(
            (_distance_m(pos[a], pos[b]), a, b) for i, a in enumerate(ids_) for b in ids_[i + 1 :] if a in new_ids or b in new_ids
        )
        for _, a, b in edges:
            if find(a) != find(b):
                parent[find(a)] = find(b)
                connect(a, b)

    # un solo viaje a Mongo para guardar todos los barrios (con sus vias embebidas)
    db.neighborhoods.bulk_write([ReplaceOne({"_id": h.id}, h.to_doc(), upsert=True) for h in hoods])
    return len(added)


def ensure_profesor(db: Database) -> None:
    """Crea (o actualiza la clave de) la cuenta del profesor con rol admin."""
    settings = get_settings()
    if not settings.profesor_password:
        return
    email = settings.profesor_email.lower()
    user = models.User.by_email(db, email)
    if user is None:
        centro = models.Neighborhood.find_one(db, {"name": "Centro"})
        user = models.User(full_name="Profesor", email=email, role="admin", neighborhood_id=centro.id if centro else None)
    user.password_hash = hash_password(settings.profesor_password)
    user.save(db)


def init_db(with_seed: bool = True) -> None:
    """En Mongo no hay CREATE TABLE: las colecciones se crean solas al insertar.
    Aqui solo se crean los indices y se cargan los datos de ejemplo."""
    db = get_database()
    ensure_indexes(db)
    if with_seed:
        seed(db)
    sync_pasto_barrios(db)
    ensure_profesor(db)
    models.catalog.clear()  # barrios y tipos se vuelven a leer de Mongo


if __name__ == "__main__":
    init_db(True)
    print("Base de datos MongoDB creada y con datos de ejemplo.")
