# 05 Requisitos del sistema

## 5.1 Requisitos no funcionales

| ID | Categoría | Requisito |
|----|-----------|-----------|
| RNF-01 | Seguridad | Contraseñas con hash bcrypt de costo 12 y sal aleatoria por usuario; nunca en texto plano. |
| RNF-02 | Seguridad | Sesiones con JWT que vencen a las 12 horas; las rutas privadas exigen token. |
| RNF-03 | Seguridad | Bloqueo de 10 minutos tras 5 intentos fallidos y límite de solicitudes a registro e inicio de sesión. |
| RNF-04 | Seguridad | Ningún secreto en el código: todo se configura con variables de entorno (`.env`). |
| RNF-05 | Disponibilidad | Si el componente de IA no responde, el backend sigue atendiendo reportes sin análisis. |
| RNF-06 | Rendimiento | Las consultas frecuentes (cola, feed, rango de fechas, ranking) se resuelven en memoria con estructuras de datos propias (heap, lista enlazada, AVL, tabla hash). |
| RNF-07 | Mantenibilidad | El modelo de IA se cambia con variables de entorno sin tocar backend ni frontend. |
| RNF-08 | Portabilidad | Cada servicio tiene Dockerfile y `docker-compose.yml` levanta todo con MongoDB; en producción: Vercel (frontend), Render (backend e IA) y MongoDB Atlas (base de datos). |
| RNF-09 | Usabilidad | Todo se puede hacer hablando con Vigía; si no hay voz, se puede escribir. |
| RNF-10 | Trazabilidad | Cada cambio de estado de un reporte queda en su historial embebido (`reports.history`) con fecha, responsable y nota; cada llamada a la IA queda en la colección `ai_analyses`. |
| RNF-11 | Calidad | Pruebas automáticas (pytest) contra un MongoDB real e integración continua con GitHub Actions. |
| RNF-12 | Privacidad | El tratamiento de datos personales cumple la Ley 1581 de 2012. |

## 5.2 Atributos de calidad y decisiones de diseño

| Atributo | Decisión |
|----------|----------|
| Disponibilidad | La IA es un servicio aparte; el backend la llama con tiempo límite y continúa si falla |
| Rendimiento | Al arrancar, el backend carga los datos de MongoDB en `AlertEngine` (estructuras en memoria); el reporte trae fotos, historial y confirmaciones en una sola lectura porque van embebidos |
| Integridad | Índices únicos (correo, nombre de barrio, suscripción) y actualizaciones atómicas (`$set` + `$push`) al cambiar el estado o confirmar una alerta |
| Seguridad | Un solo módulo (`security.py`) valida tokens, roles y contraseñas |
| Modificabilidad | Arquitectura por capas: routers → services → structures/models → MongoDB; los ids siguen siendo enteros (colección `counters`), así el cambio de base no tocó el frontend |

## 5.3 Definición de Terminado (DoD)

- [ ] El código fue revisado mediante un pull request.
- [ ] Las pruebas automáticas pasan en GitHub Actions.
- [ ] Se verificaron los criterios de aceptación de la historia.
- [ ] Funciona en la página publicada.
- [ ] La documentación (README o wiki) está actualizada.


---

[← 04 Características del sistema](04-Características-del-sistema) | [06 Arquitectura 4+1 Vistas →](06-Arquitectura-4+1-Vistas)
