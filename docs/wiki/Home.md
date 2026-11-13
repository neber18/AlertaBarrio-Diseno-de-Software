# Hogar

## *AlertaBarrio — Plataforma de alertas de seguridad entre vecinos*

**Diseño de Software — Universidad Cooperativa de Colombia, Campus Pasto**

**Autor:** Neber Camilo Melo Pantoja
**Versión del documento:** 2.1 (base de datos MongoDB)
**Última actualización:** 13/11/2026

---

## Descripción del Documento

Este repositorio contiene la **documentación de requisitos y arquitectura** de *AlertaBarrio*, una aplicación web donde los vecinos de San Juan de Pasto **reportan incidentes de seguridad** (robos, hurtos, actividad sospechosa…) y reciben **alertas de su barrio**. Los reportes pasan por **moderación**, se ordenan por gravedad y un **componente de inteligencia artificial** ayuda a clasificarlos, predecir zonas de riesgo y calcular rutas seguras.

Este documento describe:

- La funcionalidad del sistema
- El comportamiento esperado
- Las restricciones
- Los requisitos funcionales y no funcionales
- La interacción con usuarios y sistemas externos
- La arquitectura del sistema según el modelo de **4+1 vistas**
- Las historias de usuario del producto

---

## Índice

| Nº | Sección | Ir a |
|----|---------|------|
| 1 | Introducción | [01 Introducción](01-Introducción) |
| 2 | Descripción General | [02 Descripción General](02-Descripción-General) |
| 3 | Requisitos de interfaz externa | [03 Requisitos de interfaz externa](03-Requisitos-de-interfaz-externa) |
| 4 | Características del sistema | [04 Características del sistema](04-Características-del-sistema) |
| 5 | Requisitos del sistema | [05 Requisitos del sistema](05-Requisitos-del-sistema) |
| 6 | Arquitectura 4+1 Vistas | [06 Arquitectura 4+1 Vistas](06-Arquitectura-4+1-Vistas) |
| 7 | Historias de Usuario | [07 Historias de Usuario](07-Historias-de-Usuario) |

---

## Resumen del proyecto

| Elemento | Detalle |
|----------|---------|
| Nombre | AlertaBarrio |
| Ciudad | San Juan de Pasto, Nariño |
| Problema | Los vecinos se enteran de los robos y riesgos de su barrio tarde y por rumores en grupos de chat, sin saber si son ciertos |
| Solución | Reportes geolocalizados y moderados, alertas por barrio, confirmación entre vecinos, mapa de calor y ruta segura con IA |
| Usuarios | Vecinos, Moderadores, Administradores |
| Página publicada | https://alertabarrio-frontend.vercel.app |
| Tecnología | React + TypeScript (frontend), Python + FastAPI (backend e IA), **MongoDB 7 en MongoDB Atlas** |
| Código | Carpetas `frontend/`, `backend/` y `ai/` de este repositorio |
| Historias de usuario | 21 (ver *Issues* HU_001 a HU_021) |
