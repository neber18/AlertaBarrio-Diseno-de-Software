# 🛡️ AlertaBarrio - Resumen de implementación

## ✅ Componentes

### 1. Backend (`backend/`)
- **FastAPI** con API REST versionada en `/api/v1` y Swagger en `/docs`.
- **MongoDB 7** con PyMongo: 9 colecciones, documentos embebidos para el reporte (fotos, historial, confirmaciones) e ids enteros con `counters`.
- **Estructuras de datos propias** (`app/structures/`): arreglo dinámico, lista doblemente enlazada, pila, cola circular, cola de prioridad (heap), tabla hash, AVL, grafo (Dijkstra, BFS, DFS), merge sort, quick sort y búsqueda binaria. Todas usadas por `AlertEngine`.
- **Seguridad**: bcrypt (costo 12), JWT, bloqueo tras 5 intentos, límite de solicitudes por IP, verificación en dos pasos (TOTP), cierre de todas las sesiones y cabeceras de seguridad.

### 2. Componente de IA (`ai/`)
- Servicio aparte (FastAPI). Clasificador **Naive Bayes** hecho a mano, riesgo por zona con decaimiento temporal, mapa de calor **KDE**, resumen diario y asistente **Vigía** (Gemini, Ollama, Groq o plantillas).
- El modelo se cambia con variables de entorno, sin tocar el backend.

### 3. Base de datos
- Local: `docker compose up mongodb` (+ mongo-express con `--profile tools`).
- Producción: **MongoDB Atlas** (clúster M0).
- Modelo en `backend/database/README.md`.

### 4. CI/CD (GitHub Actions)
- `ci.yml`: lint con ruff, **40 pruebas del backend contra MongoDB 7**, 19 pruebas de la IA, imágenes Docker y deploy hooks de Render.
- `keep-alive.yml`: despierta los servicios de Render cada 10 minutos.

### 5. Ejecución local
- `docker-compose.yml`: MongoDB, mongo-express, IA y backend.
- `run.sh`: levanta todo con un comando (usa el MongoDB de la máquina si ya existe).
- `.devcontainer/`: entorno listo para VS Code / Codespaces.

### 6. Despliegue
- `render.yaml` (Blueprint de backend e IA).
- Guía en `docs/DESPLIEGUE.md`.

### 7. Documentación
- Wiki (requisitos IEEE 830 + arquitectura 4+1), 21 historias de usuario y diagramas en `docs/`.

## 📊 Números

| Elemento | Cantidad |
|----------|----------|
| Colecciones de MongoDB | 9 (+ `counters`) |
| Barrios de Pasto | 338 (12 comunas) |
| Endpoints de la API | 40+ |
| Pruebas automáticas | 59 (40 backend + 19 IA) |
| Historias de usuario | 21 |
