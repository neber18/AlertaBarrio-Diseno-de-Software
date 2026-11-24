# Documentación de AlertaBarrio

| Carpeta / archivo | Contenido |
|-------------------|-----------|
| [`wiki/`](wiki) | Páginas de la wiki de GitHub: Hogar, 01 a 07 y barra lateral |
| [`issues/`](issues) | Historias de usuario HU_001 a HU_021, una por archivo, para crear como *Issues* |
| [`diagramas/`](diagramas) | PlantUML e imágenes de referencia de las vistas 4+1 (+ despliegue). Los definitivos se hacen en Visual Paradigm |
| [`DESPLIEGUE.md`](DESPLIEGUE.md) | MongoDB Atlas + Render paso a paso |
| [`MIGRACION_MONGODB.md`](MIGRACION_MONGODB.md) | Qué cambió al pasar de PostgreSQL a MongoDB |

El modelo de documentos de la base de datos está en [`backend/database/README.md`](../backend/database/README.md).

## Publicar la wiki

En la pestaña **Wiki** del repositorio: *Create the first page* → pega `wiki/Home.md`. Luego *New page* por cada archivo de `wiki/`, con el título igual al nombre del archivo sin `.md`. La barra lateral es `_Sidebar.md`.

## Crear los issues

Pestaña **Issues** → *New issue*, en orden de HU_001 a HU_021, para que el número de cada issue coincida con su historia. En cada archivo está el título, las etiquetas sugeridas y el texto que va en la descripción.
