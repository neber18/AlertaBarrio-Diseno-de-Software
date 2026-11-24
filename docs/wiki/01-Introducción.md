# 01 Introducción

## 1.1 Propósito

Este documento especifica los requisitos y la arquitectura de **AlertaBarrio**, versión 2.0. Está dirigido al docente del curso de Diseño de Software, al equipo de desarrollo y a cualquier persona que necesite entender qué hace el sistema y cómo está construido.

## 1.2 Alcance del producto

AlertaBarrio permite:

- **A los vecinos:** reportar incidentes de seguridad con formulario o hablando con el asistente **Vigía**, ver las alertas de su barrio en lista y en mapa, confirmar alertas, seguir barrios y recibir notificaciones, consultar el mapa de calor de riesgo y pedir la **ruta más segura** entre dos barrios.
- **A los moderadores:** revisar los reportes en una **cola de prioridad** (primero el más grave), publicarlos o rechazarlos y **deshacer** una decisión equivocada.
- **A los administradores:** las mismas funciones del moderador, con acceso a todos los endpoints de gestión.

**Fuera del alcance de la versión 2.0:** contacto directo con la Policía o la línea 123, aplicación móvil nativa (la web funciona en el celular), chat entre vecinos y gestión de usuarios desde la interfaz.

## 1.3 Definiciones, acrónimos y abreviaturas

| Término | Definición |
|---------|------------|
| Vecino | Usuario con rol `citizen`; reporta y recibe alertas |
| Moderador | Usuario con rol `moderator` o `admin`; decide qué reportes se publican |
| Reporte | Incidente enviado por un vecino; estados: created, in_review, published, verified, rejected |
| Alerta | Reporte que ya fue publicado por un moderador |
| Vigía | Asistente de IA de la app; entiende voz y texto |
| Componente de IA | Servicio independiente (alertabarrio-ai) que clasifica reportes, calcula riesgo y genera resúmenes |
| Prioridad | Puntaje que ordena la cola de moderación: gravedad × 20 + riesgo de la zona × 20 + 5 si tiene foto |
| JWT | JSON Web Token; credencial de la sesión |
| TOTP / 2FA | Código de 6 dígitos de una app autenticadora; verificación en dos pasos |
| Dijkstra / BFS | Algoritmos de grafos usados para la ruta segura y la ruta de menos saltos |
| HU / RF / RNF | Historia de usuario / requisito funcional / requisito no funcional |

## 1.4 Referencias

- IEEE 830-1998, *Recommended Practice for Software Requirements Specifications*.
- Kruchten, P. (1995). *The 4+1 View Model of Architecture*. IEEE Software.
- Ley 1581 de 2012 (Colombia), protección de datos personales.
- Código del proyecto: carpetas `backend/` y `ai/` de este repositorio.

## 1.5 Visión general del documento

- **02 Descripción General:** contexto, usuarios, restricciones y supuestos.
- **03 Requisitos de interfaz externa:** API REST (sin interfaz gráfica), hardware, software y comunicaciones.
- **04 Características del sistema:** requisitos funcionales agrupados por épica.
- **05 Requisitos del sistema:** requisitos no funcionales y atributos de calidad.
- **06 Arquitectura 4+1 Vistas:** vistas de Contexto, Funcional, Lógica y Desarrollo, más los escenarios.
- **07 Historias de Usuario:** backlog con prioridad, estimación y criterios de aceptación.


---

[← Hogar](Home) | [02 Descripción General →](02-Descripción-General)
