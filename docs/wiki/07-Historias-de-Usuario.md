# 07 Historias de Usuario

AlertaBarrio tiene **21 historias de usuario** agrupadas en **6 épicas**, escritas a partir de lo que hace el código. Cada historia está también como *Issue* del repositorio (HU_001 a HU_021).

Formato: *Como [rol], quiero [acción], para [beneficio]*. Prioridad con **MoSCoW** y estimación en **puntos de historia** (Fibonacci: 1, 2, 3, 5, 8, 13).

## 7.1 Roles

| Rol | Descripción |
|-----|-------------|
| Visitante | Persona sin sesión; ve el panel, el mapa, la ruta segura y Vigía |
| Vecino | Usuario registrado (`citizen`); reporta, confirma alertas y recibe notificaciones |
| Moderador | `moderator` o `admin`; revisa la cola, publica, rechaza y deshace |

## 7.2 Épicas

| ID | Épica | Componente (Vista Funcional) | Dónde está en el código | Historias |
|----|-------|------------------------------|-------------------------|-----------|
| EP-01 | Cuenta y seguridad | Autenticación y Seguridad | `auth.py, security.py · /login, /registro, /cuenta` | HU_001, HU_002, HU_003, HU_004 |
| EP-02 | Reportes de incidentes | Gestión de Reportes | `reports.py, ai.py · /alertas, /mis-reportes` | HU_005, HU_006, HU_007, HU_008 |
| EP-03 | Moderación | Gestión de Reportes (puerto de gestión) | `moderation.py · /moderacion` | HU_009, HU_010, HU_011 |
| EP-04 | Alertas comunitarias | Gestión de Reportes | `reports.py · /alertas, /mapa` | HU_012, HU_013, HU_014 |
| EP-05 | Notificaciones | Notificaciones | `notifications.py · /notificaciones` | HU_015, HU_016 |
| EP-06 | Inteligencia artificial y prevención | Componente de IA (Vigía) + Rutas Seguras | `ai.py, routes.py · /vigia, /rutas, /mapa, /` | HU_017, HU_018, HU_019, HU_020, HU_021 |

## 7.3 Backlog del producto

| ID | Épica | Historia de usuario | Prioridad | Puntos |
|----|-------|---------------------|-----------|--------|
| [HU_001](../issues/1) | EP-01 | Como **vecino**, quiero crear una cuenta con mi nombre, correo y contraseña, para poder reportar incidentes y recibir alertas. | Alta (Must) | 3 |
| [HU_002](../issues/2) | EP-01 | Como **usuario**, quiero iniciar sesión con mi correo y contraseña, para entrar a las funciones de mi rol. | Alta (Must) | 3 |
| [HU_003](../issues/3) | EP-01 | Como **usuario**, quiero cambiar mi contraseña y cerrar todas mis sesiones abiertas, para proteger mi cuenta si alguien más la usó. | Media (Should) | 2 |
| [HU_004](../issues/4) | EP-01 | Como **usuario**, quiero activar la verificación en dos pasos con una app autenticadora, para que nadie entre a mi cuenta solo con mi contraseña. | Baja (Could) | 5 |
| [HU_005](../issues/5) | EP-02 | Como **vecino**, quiero reportar un incidente eligiendo el tipo, escribiendo qué pasó y marcando el punto en el mapa, para avisar a mi barrio de un problema de seguridad. | Alta (Must) | 5 |
| [HU_006](../issues/6) | EP-02 | Como **vecino**, quiero contarle a Vigía por voz o por texto lo que pasó, para reportar rápido sin llenar un formulario. | Media (Should) | 8 |
| [HU_007](../issues/7) | EP-02 | Como **vecino**, quiero ver qué tipo de incidente sugiere la IA y qué tan riesgosa es la zona, para saber si mi reporte quedó bien clasificado. | Alta (Must) | 5 |
| [HU_008](../issues/8) | EP-02 | Como **vecino**, quiero ver mis reportes y el historial de estados de cada uno, para saber si fueron publicados, verificados o rechazados. | Alta (Must) | 3 |
| [HU_009](../issues/9) | EP-03 | Como **moderador**, quiero ver los reportes pendientes ordenados por prioridad y tomar el siguiente, para atender primero los incidentes más graves. | Alta (Must) | 5 |
| [HU_010](../issues/10) | EP-03 | Como **moderador**, quiero publicar o rechazar un reporte con una nota, para que solo lleguen a los vecinos las alertas reales. | Alta (Must) | 3 |
| [HU_011](../issues/11) | EP-03 | Como **moderador**, quiero deshacer el último cambio de estado de un reporte, para corregir una alerta publicada por error. | Media (Should) | 3 |
| [HU_012](../issues/12) | EP-04 | Como **vecino**, quiero ver las alertas publicadas de mi barrio y de la ciudad, para saber qué está pasando cerca de mí. | Alta (Must) | 3 |
| [HU_013](../issues/13) | EP-04 | Como **vecino**, quiero ver las alertas en un mapa coloreadas por gravedad, para reconocer de un vistazo las zonas peligrosas. | Alta (Must) | 5 |
| [HU_014](../issues/14) | EP-04 | Como **vecino**, quiero confirmar que una alerta publicada es real, para que la comunidad sepa que es confiable. | Media (Should) | 2 |
| [HU_015](../issues/15) | EP-05 | Como **vecino**, quiero seguir los barrios que me interesan, para recibir avisos solo de esos barrios. | Media (Should) | 2 |
| [HU_016](../issues/16) | EP-05 | Como **vecino**, quiero recibir una notificación cuando se publique una alerta en un barrio que sigo, para enterarme a tiempo. | Alta (Must) | 3 |
| [HU_017](../issues/17) | EP-06 | Como **vecino**, quiero ver qué barrios, días y horas tienen más riesgo, para evitar esas zonas en esos momentos. | Media (Should) | 5 |
| [HU_018](../issues/18) | EP-06 | Como **vecino**, quiero leer un resumen diario de lo que pasó en mi barrio, para informarme sin revisar todas las alertas. | Baja (Could) | 3 |
| [HU_019](../issues/19) | EP-06 | Como **vecino**, quiero preguntarle a Vigía, por ejemplo, qué barrio debo evitar hoy, para recibir consejos basados en las alertas reales. | Baja (Could) | 5 |
| [HU_020](../issues/20) | EP-06 | Como **vecino**, quiero pedir la ruta más segura entre dos barrios, para moverme evitando las zonas con alertas. | Media (Should) | 8 |
| [HU_021](../issues/21) | EP-06 | Como **visitante**, quiero ver un panel con el estado del sistema, los reportes por día y por tipo y el ranking de barrios, para entender la situación de seguridad de la ciudad. | Media (Should) | 3 |

**Total: 84 puntos.** Must = 10 historias (38 puntos), Should = 8 historias (33 puntos), Could = 3 historias (13 puntos).

## 7.4 Criterios de aceptación

### HU_001 — Registro de vecino

- Dado un visitante en /registro, cuando ingresa nombre, correo y contraseña válidos (teléfono y barrio son opcionales), entonces se crea su cuenta con rol vecino (citizen) y queda con la sesión iniciada.
- Dada una contraseña sin 8 caracteres, mayúscula, minúscula, número o símbolo, entonces el sistema indica qué le falta y no crea la cuenta.
- Dado un correo ya registrado, entonces el sistema rechaza el registro.
- La contraseña se guarda como hash bcrypt (costo 12), nunca en texto plano.

### HU_002 — Inicio de sesión

- Dadas credenciales correctas, entonces el sistema entrega un token JWT y muestra las opciones de su rol (vecino o moderador/administrador).
- Dado un correo que falla la contraseña 5 veces seguidas, entonces queda bloqueado 10 minutos (respuesta 429).
- Si el correo no existe, la respuesta tarda lo mismo que con un correo real, para no revelar qué correos están registrados.
- Las pantallas privadas (/alertas, /mis-reportes, /cuenta, /notificaciones) redirigen a /login si no hay sesión.

### HU_003 — Cambiar contraseña y cerrar sesiones

- Dado un usuario en /cuenta, cuando ingresa su contraseña actual y una nueva contraseña fuerte, entonces la contraseña se actualiza.
- Cuando elige "cerrar todas las sesiones", entonces los tokens anteriores dejan de funcionar (token_version aumenta).

### HU_004 — Verificación en dos pasos

- Cuando activa la opción, entonces el sistema genera un código secreto para registrar en una app autenticadora como Google Authenticator.
- La verificación solo queda activa después de ingresar un código válido de 6 dígitos.
- Con la verificación activa, el inicio de sesión pide el código además de la contraseña.

### HU_005 — Reportar con formulario

- Dado un vecino con sesión, cuando completa tipo de incidente, título, descripción y ubicación, entonces el reporte se guarda con estado created.
- Al marcar el punto en el mapa (o buscar la dirección), el barrio se elige automáticamente según la ubicación.
- Puede adjuntar una foto opcional.
- Si la fecha del incidente está en el futuro, el sistema rechaza el reporte.

### HU_006 — Reportar hablando con Vigía

- Cuando el vecino dice o escribe lo que pasó, entonces Vigía arma un borrador con tipo de incidente, título y descripción.
- El barrio del borrador sale de la ubicación GPS del celular.
- El vecino revisa el borrador y lo publica con un toque; puede corregirlo antes.
- Si el navegador no tiene reconocimiento de voz, se puede escribir.

### HU_007 — Clasificación del reporte por la IA

- Al crear un reporte, el backend lo envía al componente de IA y muestra el tipo sugerido, la confianza y el riesgo de la zona.
- Si la IA tiene 70 % o más de confianza en un tipo más grave, la prioridad se calcula con esa gravedad.
- El vecino ve en qué posición de la cola de moderación quedó su reporte.
- Si la IA no responde, el reporte se guarda igual sin el análisis.

### HU_008 — Mis reportes e historial

- Dado un vecino en /mis-reportes, entonces ve sus reportes con su estado actual.
- Al abrir un reporte, ve cada cambio de estado con fecha, nota y responsable.

### HU_009 — Cola de moderación por prioridad

- Dado un moderador en /moderacion, entonces ve la cola de reportes con estado created, la más alta prioridad primero.
- La prioridad = gravedad × 20 + riesgo de la zona × 20 + 5 si tiene foto.
- Cuando toma el siguiente, el reporte sale de la cola y pasa a in_review.
- Un vecino sin rol de moderador o administrador recibe 403 si intenta entrar.

### HU_010 — Publicar o rechazar

- Cuando publica, el reporte pasa a published, entra al feed del barrio y se encolan notificaciones para los vecinos que siguen ese barrio.
- Cuando rechaza, el reporte pasa a rejected y no se muestra a los vecinos.
- Solo se permiten los cambios created → in_review → published → verified, y created o in_review → rejected.

### HU_011 — Deshacer una decisión

- Cuando presiona deshacer, se saca el último estado de la pila del reporte y vuelve al estado anterior.
- Si la alerta deja de estar publicada, sale del feed y los suscritos reciben un aviso de que se retiró.
- Si el reporte vuelve a created, regresa a la cola de moderación.

### HU_012 — Alertas de mi barrio

- Dado un vecino en /alertas, entonces ve las alertas publicadas y verificadas, las más recientes primero.
- Puede filtrar por barrio.
- Cada alerta muestra tipo, barrio, hora, descripción, foto y número de confirmaciones.

### HU_013 — Mapa de alertas

- Dado cualquier visitante en /mapa, entonces ve un mapa de Pasto con un punto por alerta activa.
- El color del punto corresponde al tipo de incidente (gravedad de 1 a 5).
- Puede superponer el mapa de calor de la IA.

### HU_014 — Confirmar una alerta

- Solo se pueden confirmar alertas publicadas o verificadas.
- Un vecino no puede confirmar su propio reporte ni confirmar dos veces el mismo.
- Con 2 confirmaciones (configurable), la alerta pasa a verified.

### HU_015 — Seguir barrios

- Dado un vecino en /notificaciones, cuando sigue un barrio, entonces queda suscrito a él.
- Puede dejar de seguirlo en cualquier momento.
- No puede suscribirse dos veces al mismo barrio.

### HU_016 — Recibir notificaciones

- Cuando un moderador publica una alerta, cada suscrito del barrio recibe la notificación (excepto el autor del reporte).
- Las notificaciones salen de una cola FIFO y quedan guardadas en la base de datos.
- El vecino puede marcar cada notificación como leída.

### HU_017 — Mapa de calor predictivo

- El mapa de calor se calcula en el componente de IA con los reportes de los últimos meses.
- Se muestra el riesgo por barrio, día de la semana y franja de 6 horas.
- Si la IA no está disponible, la pantalla lo indica y el resto de la app sigue funcionando.

### HU_018 — Resumen diario

- El resumen se genera por barrio y por día con el componente de IA.
- Si el proveedor de IA externo falla, se genera con una plantilla y la respuesta lo indica.
- El resumen indica cuántos reportes tuvo en cuenta.

### HU_019 — Preguntar a Vigía

- Dado un vecino en /vigia, cuando escribe o dice una pregunta, entonces Vigía responde usando datos reales: ranking de barrios, horas de riesgo y alertas recientes.
- Si la IA está despertando (Render plan gratis), la app espera hasta 45 segundos y avisa al vecino.

### HU_020 — Ruta segura

- Dado un vecino en /rutas, cuando elige barrio de origen y destino, entonces el sistema muestra la ruta más segura (Dijkstra con castigo por alertas), la más corta y la de menos saltos (BFS).
- También puede pedirla por voz a Vigía ("estoy en la universidad, necesito ir al centro"); el origen sale de su ubicación.
- Si no hay conexión entre los barrios, el sistema lo indica.

### HU_021 — Panel de indicadores

- La página de inicio muestra si backend, base de datos e IA están en línea.
- Muestra reportes por día de los últimos 14 días, reportes por tipo y el ranking de barrios con más alertas activas.
- Muestra las últimas alertas y el resumen de la IA.


---

[← 06 Arquitectura 4+1 Vistas](06-Arquitectura-4+1-Vistas)
