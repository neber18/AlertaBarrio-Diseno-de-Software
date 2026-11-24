# 🛡️ AlertaBarrio - Resumen de implementación

## ✅ Componentes

### 1. Backend (`backend/`)
- **FastAPI** con API REST versionada en `/api/v1` y Swagger en `/docs`.
- **MongoDB 7** con PyMongo: 6 colecciones, documentos embebidos para el reporte (fotos, historial, confirmaciones) e ids enteros con `counters`.
- **Estructuras de datos propias** (`app/structures/`): arreglo dinámico, lista doblemente enlazada, pila, cola circular, cola de prioridad (heap), tabla hash, AVL, grafo (Dijkstra, BFS, DFS), merge sort, quick sort y búsqueda binaria. Todas usadas por `AlertEngine`.
- **Seguridad**: bcrypt (costo 12), JWT, bloqueo tras 5 intentos, límite de solicitudes por IP, verificación en dos pasos (TOTP), cierre de todas las sesiones y cabeceras de seguridad.

### 2. Base de datos
- Local: `docker compose up mongodb` (+ mongo-express con `--profile tools`).
- Producción: **MongoDB Atlas** (clúster M0).
- Modelo en `backend/database/README.md`.

### 3. CI/CD (GitHub Actions)
- `ci.yml`: lint con ruff, **32 pruebas del backend contra MongoDB 7**, imagen Docker y deploy hooks de Render.
- `keep-alive.yml`: despierta el backend en Render cada 10 minutos.

### 4. Ejecución local
- `docker-compose.yml`: MongoDB, mongo-express y backend.
- `run.sh`: levanta todo con un comando (usa el MongoDB de la máquina si ya existe).
- `.devcontainer/`: entorno listo para VS Code / Codespaces.

### 5. Despliegue
- `render.yaml` (Blueprint del backend).
- Guía en `docs/DESPLIEGUE.md`.

### 6. Documentación
- Wiki (requisitos IEEE 830 + arquitectura 4+1), 16 historias de usuario activas (5 de IA retiradas) y diagramas en `docs/`.

## 📊 Números

| Elemento | Cantidad |
|----------|----------|
| Colecciones de MongoDB | 6 (+ `counters`) |
| Barrios de Pasto | 338 (12 comunas) |
| Endpoints de la API | 40 |
| Pruebas automáticas | 32 (backend) |
| Historias de usuario | 16 activas (de 21) |
