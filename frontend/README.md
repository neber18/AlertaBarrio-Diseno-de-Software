# AlertaBarrio · Frontend

Página web de AlertaBarrio: **React 19 + TypeScript + Vite + Leaflet**. Habla solo con el backend (`VITE_API_URL`); no sabe qué base de datos hay detrás, por eso el cambio a MongoDB no la tocó.

```bash
npm ci
cp .env.example .env     # VITE_API_URL=http://localhost:8000
npm run dev              # http://localhost:5173
npm run build            # revisa tipos y genera dist/
```

- Rutas y pantallas: `src/App.tsx` y `src/pages/`
- Cliente de la API: `src/api/client.ts`
- Sesión (JWT): `src/auth/AuthContext.tsx`
- Configuración (ciudad, centro del mapa, URLs): `src/config.ts`

Despliegue en **Vercel** (`vercel.json` redirige todas las rutas a `index.html`). También tiene `Dockerfile` con nginx.

La documentación completa del proyecto está en el [README de la raíz](../README.md).
