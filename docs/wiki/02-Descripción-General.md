# 02 Descripción General

## 2.1 Perspectiva del producto

AlertaBarrio es un sistema nuevo formado por un **backend (API REST)** y una base de datos que se comunican por HTTP/JSON. **No tiene interfaz gráfica propia:** se usa a través de la API REST (Swagger en `/docs`, Postman o `curl`), y cualquier cliente web o móvil puede conectarse después.

| Servicio | Tecnología | Dónde corre |
|----------|------------|-------------|
| Backend (API REST) | Python + FastAPI + PyMongo | Render |
| Base de datos | MongoDB 7 (6 colecciones) | MongoDB Atlas (clúster M0) |

El backend es el único que habla con la base de datos.

## 2.2 Funciones del producto

| Función | Descripción |
|---------|-------------|
| Cuenta y seguridad | Registro, inicio de sesión con JWT, bloqueo por intentos, cambio de contraseña, cierre de sesiones y verificación en dos pasos |
| Reportes | Reporte con coordenadas por la API; el barrio más cercano sale de las coordenadas |
| Prioridad | Cada reporte recibe una prioridad (gravedad del tipo + foto) para la cola de moderación |
| Moderación | Cola de prioridad, publicar, rechazar y deshacer |
| Alertas comunitarias | Feed por barrio, alertas con coordenadas para mapa y confirmación entre vecinos |
| Notificaciones | Seguir barrios y recibir avisos de nuevas alertas |
| Prevención | Ruta segura entre barrios y ranking de barrios con más alertas |
| Indicadores | Estado del sistema, indicadores y ranking de barrios |

## 2.3 Características de los usuarios

| Usuario | Rol en el sistema | Características | Endpoints principales |
|---------|-------------------|-----------------|-----------------------|
| Visitante | (sin sesión) | Cualquier persona | `/stats`, `/reports/map`, `/routes/safe`, `/neighborhoods/ranking` |
| Vecino | `citizen` | Habitante de Pasto con celular o computador; conocimientos básicos | `/reports`, `/reports/mine`, `/notifications/me`, `/auth/*` |
| Moderador | `moderator` | Líder comunitario o integrante del equipo | `/moderation/*` |
| Administrador | `admin` | Equipo técnico | `/moderation/*` y todos los anteriores |

## 2.4 Restricciones

- El sistema se entrega sin interfaz gráfica: se opera con un cliente HTTP (Swagger, Postman o `curl`).
- El backend corre en el plan gratuito de Render, que lo "duerme" sin uso: la primera llamada puede tardar unos segundos.
- Las coordenadas de los barrios de Pasto son aproximadas.
- El tratamiento de datos personales debe cumplir la Ley 1581 de 2012.
- Las colecciones y los campos de la base de datos se nombran en inglés.
- MongoDB Atlas (plan gratis) exige permitir la conexión desde cualquier IP (`0.0.0.0/0`) porque Render no tiene IP fija; la seguridad la dan el usuario y la clave de la base.

## 2.5 Supuestos y dependencias

- El cliente envía las coordenadas (latitud y longitud) del incidente.
- Hay al menos un moderador activo para revisar la cola.


---

[← 01 Introducción](01-Introducción) | [03 Requisitos de interfaz externa →](03-Requisitos-de-interfaz-externa)
