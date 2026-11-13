# 03 Requisitos de interfaz externa

## 3.1 Interfaces de usuario

| Ruta | Pantalla | Acceso |
|------|----------|--------|
| `/` | Panel: estado de backend, BD e IA; reportes por día y por tipo; mapa; últimas alertas; resumen de la IA; ranking de barrios | Público |
| `/login`, `/registro` | Inicio de sesión (switch Usuario / Administrador) y registro | Público |
| `/mapa` | Mapa de alertas coloreadas por gravedad y mapa de calor de la IA | Público |
| `/alertas` | Alertas del barrio, nuevo reporte (formulario o Vigía) y confirmación de alertas | Vecino |
| `/mis-reportes` | Reportes propios con su historial de estados | Vecino |
| `/notificaciones` | Notificaciones y barrios que sigo | Vecino |
| `/cuenta` | Cambio de contraseña, cierre de sesiones y verificación en dos pasos | Vecino |
| `/vigia` | Asistente de IA: preguntas, reporte hablado y ruta por voz | Público |
| `/rutas` | Ruta más segura entre dos barrios | Público |
| `/moderacion` | Cola de prioridad, publicar, rechazar y deshacer | Moderador / Administrador |
| `/documentacion` | Documentación y estado interno de las estructuras de datos | Público |

## 3.2 Interfaces de hardware

- **GPS / ubicación** del dispositivo, para elegir el barrio del reporte y el origen de la ruta.
- **Micrófono**, para hablar con Vigía.
- **Cámara o galería**, para la foto opcional del reporte.

## 3.3 Interfaces de software

| Sistema | Uso | Tipo |
|---------|-----|------|
| Componente de IA (alertabarrio-ai) | Clasificar reportes (Naive Bayes), riesgo de zona, mapa de calor (KDE), resumen diario, borrador de reporte y chat | API REST HTTP/JSON |
| OpenStreetMap | Mosaicos del mapa | HTTPS |
| Nominatim (OpenStreetMap) | Búsqueda de direcciones | HTTPS |
| Reconocimiento de voz del navegador | Convertir la voz del vecino en texto | API del navegador |
| MongoDB 7 (MongoDB Atlas) | Almacenamiento (9 colecciones) | PyMongo · TCP 27017 con TLS (`mongodb+srv://`) |

## 3.4 Interfaces de comunicaciones

- Frontend → Backend → IA: **HTTP/JSON** sobre HTTPS en producción.
- La API está versionada en `/api/v1` y documentada con Swagger en `/docs`.
- Las rutas privadas exigen el encabezado `Authorization: Bearer <token JWT>`.
- Backend → MongoDB Atlas: protocolo de MongoDB sobre TCP 27017 con TLS; la cadena de conexión va en la variable `MONGODB_URI`.


---

[← 02 Descripción General](02-Descripción-General) | [04 Características del sistema →](04-Características-del-sistema)
