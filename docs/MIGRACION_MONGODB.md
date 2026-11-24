# Migración de PostgreSQL a MongoDB

AlertaBarrio empezó con **PostgreSQL + SQLAlchemy** (14 tablas). Esta versión usa **MongoDB 7 + PyMongo** (9 colecciones). Las 40 pruebas del backend pasan contra un MongoDB real y la API no cambió.

## 1. Cómo se pensó el modelo

| Relación en el diagrama | En MongoDB | En AlertaBarrio |
|-------------------------|------------|-----------------|
| Composición | Embebido | `photos`, `history` y `verifications` dentro de `reports`; `connections` dentro de `neighborhoods` |
| Asociación | Referencia por id (+ copia del nombre) | `reports.user_id`, `neighborhood_id`, `incident_type_id`, `reporter_name` |
| Tabla de roles | Un campo | `users.role` |

| Antes (tablas) | Ahora (colecciones) |
|----------------|---------------------|
| `users` + `roles` | `users` |
| `neighborhoods` + `neighborhood_connections` | `neighborhoods` |
| `reports` + `report_photos` + `report_status_history` + `report_verifications` | `reports` |
| `incident_types`, `subscriptions`, `notifications`, `ai_analyses`, `daily_summaries`, `risk_hotspots` | igual |
| secuencias `SERIAL` | `counters` |

## 2. Qué cambió en el código (`backend/`)

| Archivo | Antes | Ahora |
|---------|-------|-------|
| `requirements.txt` | `SQLAlchemy`, `psycopg2-binary` | `pymongo` |
| `app/config.py` | `DATABASE_URL` | `MONGODB_URI` |
| `app/database.py` | `create_engine`, `SessionLocal` | `MongoClient`, `get_db()`, `next_id()` con `counters`, `ensure_indexes()` |
| `app/models.py` | 14 clases `Base` de SQLAlchemy | Clases `Document` (colección) y `Embedded` (dentro de otro documento) |
| Routers y servicios | `select(...)`, `db.add()`, `db.commit()` | `Model.find()`, `Model.get()`, `obj.save()`, `update_one` con `$set` / `$push` / `$pull` |
| `app/seed.py` | `create_all` + `INSERT` + migraciones de columnas | Índices + `insert_many` (sin esquema: Mongo crea las colecciones al insertar) |
| `tests/conftest.py` | SQLite temporal | Base `alertabarrio_test` en un MongoDB real |
| `database/` | `schema.sql`, `seed.sql`, diagrama entidad-relación | Modelo de documentos, diagrama y ejemplos JSON |

## 3. Decisiones

1. **Ids enteros con `counters`.** Mongo usaría ObjectId (texto largo). Se mantuvieron números para no tocar los clientes de la API, las URLs ni las estructuras de datos (tabla hash, AVL, grafo).
2. **Guardar a mano.** En Mongo no hay `commit()` que guarde lo que cambió: se llama `save()` o `update_one` después de cada cambio.
3. **Operaciones atómicas.** Cambio de estado = un `update_one` con `$set` + `$push`. Deshacer = `$pull`. Confirmar = `$push` solo si el vecino no está en la lista (evita confirmar dos veces).
4. **Índices únicos** en vez de `UNIQUE`: correo, nombre de barrio, código de tipo, suscripción (usuario + barrio) y resumen (barrio + fecha). Si se repite, Mongo lanza `DuplicateKeyError` y la API responde **409**.
5. **Catálogo en memoria** de barrios y tipos de incidente, en vez de los `JOIN`.

## 4. Diagramas que cambiaron

| Vista | Cambio |
|-------|--------|
| Contexto | Ninguno (no muestra la base) |
| Funcional | Ninguno |
| Lógica | Estereotipos «document» y «embedded»; `CambioEstado`, `FotoReporte`, `Verificacion` y `Via` embebidas; `Rol` pasa a enumeración |
| Desarrollo | `Database` (PyMongo, `counters`, índices) y el paquete de persistencia con las colecciones |
| Despliegue (nueva) | Nodo **MongoDB Atlas - clúster M0 (AWS)**, ambiente **MongoDB 7**, conexión **MongoDB / TCP 27017 (TLS)** |
