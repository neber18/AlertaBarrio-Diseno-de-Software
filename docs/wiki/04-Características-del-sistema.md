# 04 Características del sistema

Los requisitos funcionales se agrupan en 6 épicas. Cada uno está ligado a sus historias de usuario (ver *07 Historias de Usuario*).

## 4.1 EP-01 Cuenta y seguridad

**Prioridad:** Alta

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-01 | El sistema debe permitir registrar vecinos con nombre, correo y contraseña; teléfono y barrio son opcionales. | HU_001 |
| RF-02 | El sistema debe exigir contraseñas de 8 o más caracteres con mayúscula, minúscula, número y símbolo, y guardarlas con bcrypt. | HU_001 |
| RF-03 | El sistema debe autenticar con correo y contraseña y entregar un token JWT. | HU_002 |
| RF-04 | El sistema debe bloquear 10 minutos un correo después de 5 intentos fallidos. | HU_002 |
| RF-05 | El sistema debe permitir cambiar la contraseña y cerrar todas las sesiones. | HU_003 |
| RF-06 | El sistema debe permitir activar y desactivar la verificación en dos pasos (TOTP). | HU_004 |

## 4.2 EP-02 Reportes de incidentes

**Prioridad:** Alta

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-07 | El sistema debe permitir crear un reporte con tipo de incidente, título, descripción, ubicación, fecha y foto opcional. | HU_005 |
| RF-08 | El sistema debe asignar el barrio del reporte según la ubicación marcada. | HU_005 |
| RF-09 | El sistema debe rechazar reportes con fecha futura. | HU_005 |
| RF-10 | El sistema debe generar un borrador de reporte a partir de lo que el vecino dice o escribe a Vigía. | HU_006 |
| RF-11 | El sistema debe enviar cada reporte al componente de IA y guardar el tipo sugerido, la confianza y el riesgo de la zona. | HU_007 |
| RF-12 | El sistema debe calcular la prioridad del reporte y ubicarlo en la cola de moderación. | HU_007 |
| RF-13 | El sistema debe entregar al vecino sus reportes y el historial de estados. | HU_008 |

## 4.3 EP-03 Moderación

**Prioridad:** Alta

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-14 | El sistema debe ordenar los reportes pendientes por prioridad (el más grave primero). | HU_009 |
| RF-15 | El sistema debe restringir la moderación a los roles moderador y administrador. | HU_009 |
| RF-16 | El sistema debe permitir publicar o rechazar un reporte con una nota. | HU_010 |
| RF-17 | El sistema debe registrar cada cambio de estado y solo permitir las transiciones válidas. | HU_010 |
| RF-18 | El sistema debe permitir deshacer el último cambio de estado de un reporte. | HU_011 |

## 4.4 EP-04 Alertas comunitarias

**Prioridad:** Alta

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-19 | El sistema debe entregar las alertas publicadas, filtrables por barrio. | HU_012 |
| RF-20 | El sistema debe entregar las alertas activas con sus coordenadas y el color de su tipo de incidente, para pintarlas en un mapa. | HU_013 |
| RF-21 | El sistema debe permitir a otros vecinos confirmar una alerta y marcarla como verificada al alcanzar 2 confirmaciones. | HU_014 |

## 4.5 EP-05 Notificaciones

**Prioridad:** Media

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-22 | El sistema debe permitir seguir y dejar de seguir barrios. | HU_015 |
| RF-23 | El sistema debe notificar a los suscritos de un barrio cuando se publique o retire una alerta allí. | HU_016, HU_011 |

## 4.6 EP-06 Inteligencia artificial y prevención

**Prioridad:** Media

| ID | Requisito funcional | HU |
|----|---------------------|----|
| RF-24 | El sistema debe entregar el riesgo por barrio, día y franja horaria (mapa de calor). | HU_017 |
| RF-25 | El sistema debe generar un resumen diario por barrio. | HU_018 |
| RF-26 | El sistema debe responder preguntas del vecino con datos reales de las alertas. | HU_019 |
| RF-27 | El sistema debe calcular la ruta más segura, la más corta y la de menos saltos entre dos barrios. | HU_020 |
| RF-28 | El sistema debe entregar el estado de los servicios e indicadores de reportes (`GET /api/v1/stats`). | HU_021 |

## 4.7 Ciclo de vida de un reporte

```
created ─► in_review ─► published ─► verified
   │            │
   └────────────┴──► rejected
```

- **created:** el vecino lo envió; está en la cola de moderación.
- **in_review:** un moderador lo está revisando.
- **published:** es una alerta visible para los vecinos.
- **verified:** al menos 2 vecinos confirmaron que es real.
- **rejected:** el moderador lo descartó.


---

[← 03 Requisitos de interfaz externa](03-Requisitos-de-interfaz-externa) | [05 Requisitos del sistema →](05-Requisitos-del-sistema)
