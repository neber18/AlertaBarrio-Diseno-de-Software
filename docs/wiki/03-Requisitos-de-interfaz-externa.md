# 03 Requisitos de interfaz externa

## 3.1 Interfaces de usuario

El sistema **no tiene interfaz gráfica propia**. El usuario interactúa con la **API REST** desde:

- **Swagger UI** en `/docs` del backend: formulario por cada endpoint, botón *Authorize* para pegar el token.
- **Postman**, `curl` o cualquier cliente web o móvil que se conecte después.

| Grupo de endpoints | Qué permite | Acceso |
|--------------------|-------------|--------|
| `/api/v1/auth/*` | Registro, inicio de sesión, cambio de contraseña, cierre de sesiones y verificación en dos pasos | Público / Vecino |
| `/api/v1/stats`, `/health` | Estado de backend y BD e indicadores | Público |
| `/api/v1/reports`, `/feed`, `/reports/map` | Crear reportes, alertas por barrio y alertas con coordenadas | Vecino / Público |
| `/api/v1/reports/mine`, `/reports/{id}/history`, `/reports/{id}/verify` | Mis reportes, historial de estados y confirmar alertas | Vecino |
| `/api/v1/subscriptions/*`, `/notifications/*` | Seguir barrios y leer notificaciones | Vecino |
| `/api/v1/routes/safe` | Ruta más segura entre dos barrios | Público |
| `/api/v1/moderation/*` | Cola de prioridad, publicar, rechazar y deshacer | Moderador / Administrador |
| `/api/v1/ds/state` | Estado interno de las estructuras de datos | Público |

## 3.2 Interfaces de hardware

- Servidor con Docker o Python 3.11 para el backend.
- El cliente aporta las **coordenadas** del incidente (por ejemplo, el GPS de un celular) en el cuerpo del reporte.

## 3.3 Interfaces de software

| Sistema | Uso | Tipo |
|---------|-----|------|
| MongoDB 7 (MongoDB Atlas) | Almacenamiento (6 colecciones) | PyMongo · TCP 27017 con TLS (`mongodb+srv://`) |

## 3.4 Interfaces de comunicaciones

- Cliente → Backend: **HTTP/JSON** sobre HTTPS en producción.
- La API está versionada en `/api/v1` y documentada con Swagger en `/docs`.
- Las rutas privadas exigen el encabezado `Authorization: Bearer <token JWT>`.
- Backend → MongoDB Atlas: protocolo de MongoDB sobre TCP 27017 con TLS; la cadena de conexión va en la variable `MONGODB_URI`.


---

[← 02 Descripción General](02-Descripción-General) | [04 Características del sistema →](04-Características-del-sistema)
