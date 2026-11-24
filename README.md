# 🛡️ AlertaBarrio — Alertas de seguridad entre vecinos

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688.svg)](https://fastapi.tiangolo.com/)
[![MongoDB 7](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![CI](https://github.com/neber18/AlertaBarrio-Diseno-de-Software/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Plataforma para que los vecinos de **San Juan de Pasto** **reporten incidentes de seguridad** (robos, hurtos, actividad sospechosa…) y reciban **alertas de su barrio**. Los reportes pasan por moderación, se ordenan por gravedad y una **inteligencia artificial** ayuda a clasificarlos, predecir zonas de riesgo y calcular rutas seguras.

🔗 **[Wiki del proyecto](../../wiki)** · Se usa desde la **API REST** con su documentación interactiva (Swagger) en `/docs`.

Proyecto final de **Diseño de Software** — Universidad Cooperativa de Colombia, Campus Pasto.

## 🚀 Características principales

- **Reportes geolocalizados** por la API o **escribiéndole a Vigía** (el asistente de IA arma el reporte a partir del texto).
- **IA** (servicio aparte): clasifica el reporte (Naive Bayes), calcula el riesgo de la zona, mapa de calor (KDE) y resumen diario.
- **Moderación con cola de prioridad**: sale primero el reporte más grave; publicar, rechazar y **deshacer**.
- **Alertas por barrio** en lista y mapa, **confirmación entre vecinos** y **notificaciones** a los suscritos.
- **Ruta segura** entre barrios con un grafo y Dijkstra.
- **Seguridad**: bcrypt, JWT, bloqueo por intentos, límite de solicitudes y verificación en dos pasos (TOTP).
- **MongoDB** con documentos embebidos para el reporte (fotos, historial y confirmaciones).

## 📁 Estructura del repositorio

| Carpeta | Qué es | Tecnología |
|---|---|---|
| [`backend/`](backend) | API REST, base de datos y **todas las estructuras de datos** | Python + FastAPI + **MongoDB** (PyMongo) |
| [`ai/`](ai) | Componente de IA independiente | Python + FastAPI |
| [`docs/`](docs) | Wiki (requisitos, arquitectura 4+1), historias de usuario y diagramas | Markdown + PlantUML |
| `docker-compose.yml` | MongoDB, mongo-express, backend e IA | Docker |
| `run.sh` | Levanta todo en local con un comando | Bash |

## 📋 Requisitos

- Python 3.11+
- MongoDB 7 (o Docker para levantarlo)

## 🔧 Configuración rápida

### Opción 1: todo con Docker

```bash
cp .env.example .env
docker compose up --build
```

- Backend (Swagger): http://localhost:8000/docs
- IA: http://localhost:8001/docs
- mongo-express (ver la base): `docker compose --profile tools up mongo-express` → http://localhost:8081

### Opción 2: con el script

```bash
./run.sh
```

Levanta MongoDB (usa el de tu PC si ya hay uno en el puerto 27017, si no lo levanta con Docker), la IA y el backend.

### Opción 3: paso a paso

```bash
docker compose up -d mongodb

# IA (puerto 8001)
cd ai && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt && cp .env.example .env
uvicorn app.main:app --reload --port 8001

# Backend (puerto 8000), en otra terminal
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env   # MONGODB_URI y AI_SERVICE_URL
uvicorn app.main:app --reload --port 8000
```

### Cuentas de prueba

| Correo | Clave | Entrar como |
|---|---|---|
| `ana@alertabarrio.co` | `Alerta2026*` | Usuario |
| `moderador@alertabarrio.co` | `Alerta2026*` | Administrador |
| `admin@alertabarrio.co` | `Alerta2026*` | Administrador |

---

## Cómo se usa sin interfaz gráfica

Este repositorio no trae página web: todo se hace contra la **API REST**.

1. Abre **http://localhost:8000/docs** (Swagger).
2. `POST /api/v1/auth/login` con una cuenta de prueba y copia el `access_token`.
3. Botón **Authorize** → pega el token. Ya puedes reportar, moderar, pedir rutas, etc.

Con `curl`:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"ana@alertabarrio.co","password":"Alerta2026*"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s localhost:8000/api/v1/feed -H "Authorization: Bearer $TOKEN"
```

---

## 1. Arquitectura

```
 ┌──────────────┐   HTTP/JSON   ┌──────────────────┐   HTTP/JSON   ┌──────────────────┐
 │   Cliente    │ ────────────► │     Backend      │ ────────────► │  Componente IA   │
 │ Swagger/curl │ ◄──────────── │     FastAPI      │ ◄──────────── │     FastAPI      │
 │  /Postman    │               │     (Render)     │               │     (Render)     │
 └──────────────┘               └────────┬─────────┘               └──────────────────┘
                                         │ PyMongo
                                ┌────────▼─────────┐
                                │    MongoDB 7     │
                                │  9 colecciones   │
                                │ (MongoDB Atlas)  │
                                └──────────────────┘
```

- **MongoDB** es la fuente de verdad: ahí se guarda todo (en producción, un clúster de **MongoDB Atlas**).
- Al arrancar, el backend carga los datos en memoria dentro de **nuestras propias estructuras de datos** (`AlertEngine`) para responder rápido.
- La **IA es un servicio aparte**: el backend le pega por HTTP y no sabe qué modelo hay detrás. Si la IA no responde, el backend sigue funcionando sin ella.

---

## 2. ¿Qué pasa cuando un vecino reporta algo?

1. El vecino envía el reporte con `POST /api/v1/reports` (tipo, barrio, descripción y coordenadas), o se lo **cuenta a Vigía** por texto: "robaron un celular en la Avenida Santander" y la IA saca el tipo de incidente, el título y la descripción.
2. El backend guarda el reporte con estado `created` y lo mete en la **pila** de historial de ese reporte.
3. El backend le manda el texto a la **IA**, que responde:
   - qué tipo de incidente cree que es (clasificador **Naive Bayes**) y con qué confianza,
   - qué tan riesgosa es esa zona en ese día y hora.
4. Si la IA está muy segura (≥ 70 %) de que es algo **más grave** de lo que marcó el vecino, se usa esa gravedad. Ejemplo: marcó "hurto" pero escribió que fue un robo con pistola.
5. Se calcula la **prioridad** (gravedad + riesgo de la zona + si tiene foto) y el reporte entra a la **cola de prioridad** de moderación.
6. El moderador saca siempre **el más grave primero**, lo publica o lo rechaza, y puede **deshacer** (pop de la pila).
7. Al publicarse, entra al **feed** del barrio (lista enlazada) y se encolan **notificaciones** (cola FIFO) para los vecinos suscritos.
8. Cuando otros vecinos lo confirman (2 verificaciones por defecto), pasa a `verified`.

```
created ─► in_review ─► published ─► verified
   └──────────┴──► rejected
```

---

## 3. Estructuras de datos (el corazón del proyecto)

Todas están implementadas **a mano, sin librerías**, en `backend/app/structures/`, y se usan de verdad dentro de `app/services/engine.py`.

| Estructura | Archivo | Para qué la usamos en AlertaBarrio |
|---|---|---|
| **Arreglo dinámico** | `dynamic_array.py` | Catálogo de barrios ordenado por nombre (se duplica cuando se llena) |
| **Lista doblemente enlazada** | `linked_list.py` | Feed de alertas activas por barrio y vecinos suscritos por barrio |
| **Pila (Stack)** | `stack.py` | Historial de estados de cada reporte → botón **deshacer** |
| **Cola (Queue)** | `queue.py` | Notificaciones pendientes (FIFO, buffer circular, O(1)) |
| **Cola de prioridad (max-heap)** | `priority_queue.py` | Cola de moderación: sale primero el más grave |
| **Tabla hash** | `hash_table.py` | Índice reporte → pila y barrio → lista (encadenamiento, rehash al 0.75) |
| **Árbol binario de búsqueda (AVL)** | `bst.py` | Historial de reportes por fecha → consultas por rango |
| **Grafo ponderado** | `graph.py` | Barrios = vértices, vías = aristas → **ruta más segura** con Dijkstra, BFS y DFS |
| **Ordenamiento y búsqueda** | `sorting.py` | `merge_sort` (feed general), `quick_sort` (ranking de barrios), búsqueda binaria |

El estado interno de todas se consulta en vivo con `GET /api/v1/ds/state`.

---

## 4. Componente de IA

Servicio independiente (como recomendó el profe). Los modelos se cambian **solo con variables de entorno** o en caliente con `POST /api/v1/models/switch`, sin tocar el backend.

| Función | Modelo por defecto | Alternativas |
|---|---|---|
| Clasificar el reporte | **Naive Bayes multinomial** hecho a mano con suavizado de Laplace, entrenado con frases típicas de grupos de barrio | `keywords` |
| Riesgo de la zona | peso = gravedad/5 × 0.5^(edad/vida_media), por barrio, día y franja de 6 h | — |
| Mapa de calor predictivo | **KDE** (kernel gaussiano sobre grilla 36×36) | `frequency` (histograma 2D) |
| Resumen diario | `template` (plantilla) | `ollama` (modelos open source locales), `openai_compatible` (Groq, OpenRouter, LM Studio), `anthropic` |

Si un proveedor externo falla, el resumen se genera con la plantilla y la respuesta lo dice. Cada llamada a la IA queda registrada en la colección `ai_analyses` (modelo, latencia, resultado).

---

## 5. Base de datos (MongoDB)

**MongoDB 7**: local con Docker y en producción con **MongoDB Atlas**. Las 14 tablas que tenía la versión con PostgreSQL quedaron en **9 colecciones** (+ `counters`).

| Relación en el diagrama de clases | En MongoDB | Ejemplo |
|---|---|---|
| Composición | Documento **embebido** | fotos, historial de estados y confirmaciones van dentro del reporte; las vías, dentro del barrio |
| Asociación | **Referencia por id** | el reporte guarda `user_id`, `neighborhood_id`, `incident_type_id` (+ copia de `reporter_name`) |
| Rol del usuario | **Un campo** | `role: citizen \| moderator \| admin` en `users` |

Colecciones: `users`, `neighborhoods`, `incident_types`, `reports`, `subscriptions`, `notifications`, `ai_analyses`, `daily_summaries`, `risk_hotspots`.

Los ids siguen siendo **enteros** gracias a la colección `counters` (incremento atómico con `$inc`), así las URLs y las estructuras de datos no cambiaron. Detalle, diagrama y ejemplos JSON en [`backend/database/README.md`](backend/database/README.md).

Datos de ejemplo: 338 barrios de las 12 comunas de **Pasto**, 8 tipos de incidente, 8 usuarios y unos 150 reportes. Contraseña demo: `Alerta2026*`. El backend crea los índices y carga los datos solo si la base está vacía.

**Contraseñas:** se guardan como hash **bcrypt** (costo 12, sal por usuario), se exige contraseña fuerte (8+ caracteres, mayúscula, minúscula, número y símbolo) y tras 5 intentos fallidos el correo queda bloqueado 10 minutos.

---

## 6. Endpoints principales del backend

Documentación interactiva (Swagger) en `/docs` del backend.

| Método | Ruta | Estructura que usa |
|---|---|---|
| POST | `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/change-password` | — (bcrypt + JWT) |
| GET | `/api/v1/stats` | indicadores generales |
| POST | `/api/v1/reports` | IA → PriorityQueue + AVL + Stack |
| GET | `/api/v1/feed?neighborhood_id=` | LinkedList / merge sort |
| GET | `/api/v1/reports?from=&to=` | AVL (rango por fecha) |
| GET | `/api/v1/reports/{id}/history` | Stack |
| POST | `/api/v1/reports/{id}/verify` | — |
| GET | `/api/v1/moderation/queue` | PriorityQueue (heap) |
| POST | `/api/v1/moderation/next` | pop del heap |
| POST | `/api/v1/moderation/reports/{id}/publish` | LinkedList + Queue de notificaciones |
| POST | `/api/v1/moderation/reports/{id}/undo` | pop de la Stack |
| GET | `/api/v1/routes/safe?from_id=&to_id=` | Graph + Dijkstra + BFS |
| GET | `/api/v1/neighborhoods/search?name=` | búsqueda binaria |
| GET | `/api/v1/neighborhoods/ranking` | quick sort |
| GET | `/api/v1/ai/heatmap`, `/api/v1/ai/daily-summary` | llaman al componente de IA |
| GET | `/api/v1/ds/state` | estado de todas las estructuras |

---

## 7. Variables de entorno

| Carpeta | Variable | Para qué |
|---|---|---|
| backend | `MONGODB_URI` | Conexión a MongoDB (local o Atlas), con el nombre de la base |
| backend | `AI_SERVICE_URL` | URL del componente de IA |
| backend | `JWT_SECRET` | Secreto para firmar los tokens |
| backend | `TEAM_MEMBERS`, `CORS_ORIGINS`, `SEED_ON_STARTUP`, `TIMEZONE`, `VERIFICATIONS_REQUIRED` | Configuración general |
| ai | `CLASSIFIER_MODEL`, `HEATMAP_MODEL`, `SUMMARY_PROVIDER` | Qué modelo usar ("el switch") |
| ai | `GEMINI_API_KEY`, `SUMMARY_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`, `ADMIN_TOKEN` | Proveedor externo y protección del switch |

## 🧪 8. Pruebas y CI

| Carpeta | Comando | Qué revisa |
|---|---|---|
| backend | `pytest` | 40 pruebas: estructuras de datos y API **contra un MongoDB real** |
| ai | `pytest` | 19 pruebas de los modelos y endpoints |

GitHub Actions (`.github/workflows/ci.yml`) corre en cada push: lint (`ruff`), pruebas del backend con un servicio **MongoDB 7**, pruebas de la IA y las imágenes de Docker.

## ☁️ 9. Despliegue

| Parte | Dónde |
|---|---|
| Backend | **Render** (`render.yaml`) + **MongoDB Atlas** (clúster M0 gratis) |
| IA | **Render** |

Pasos para Atlas y Render en [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md). Los planes gratis de Render duermen el servidor tras 15 minutos sin uso; el workflow `keep-alive.yml` le hace ping cada 10 minutos (variables `BACKEND_URL` y `AI_URL` en *Settings → Secrets and variables → Actions → Variables*).

## 👤 Autor

- Neber Camilo Melo Pantoja
