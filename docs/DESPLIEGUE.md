# Despliegue: MongoDB Atlas + Render

## 1. Crear la base de datos en MongoDB Atlas

1. Entra a https://cloud.mongodb.com y crea una cuenta (puedes entrar con GitHub o Google).
2. **Clúster:** *Create* → plan **M0 (Free)** → proveedor **AWS** → región **us-east-1** (o la más cercana) → *Create Deployment*.
3. **Usuario de la base:** *Security → Database Access → Add New Database User*.
   - Método **Password** → **Autogenerate Secure Password** → **Copy**. Guárdala en un lugar seguro (no la mandes por chat).
   - Rol: *Read and write to any database*.
   - Clic en **Add User** / **Update User**. Sin este clic la clave no se guarda.
4. **Acceso desde Render:** *Security → Network Access → Add IP Address* → **Allow access from anywhere** (`0.0.0.0/0`).
   Render no tiene IP fija en el plan gratis. `0.0.0.0/0` **no es la contraseña**.
5. **Cadena de conexión:** *Database → Connect → Drivers* → copia algo así:

   ```
   mongodb+srv://USUARIO:<db_password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
   ```

   Arma la URI final:
   - Cambia `<db_password>` por la clave (sin `< >`).
   - Pon el nombre de la base después de `.net/`: **`alertabarrio`**.

   ```
   mongodb+srv://USUARIO:TU_CLAVE@cluster0.xxxxx.mongodb.net/alertabarrio?retryWrites=true&w=majority&appName=Cluster0
   ```

   Si la clave tiene `@ : / ? #`, hay que codificarlos (`@` → `%40`). Por eso conviene la clave autogenerada.

## 2. Backend e IA en Render

**Con el Blueprint (`render.yaml` en la raíz):** *New → Blueprint* → elige el repositorio. Render crea `alertabarrio-backend` y `alertabarrio-ai` y te pide los valores marcados con `sync: false`.

**A mano:**

1. *New → Web Service* → el repositorio → **Root Directory:** `backend` → **Runtime:** Docker.
2. *Environment* → agrega:

| Variable | Valor |
|----------|-------|
| `MONGODB_URI` | La URI completa de Atlas (paso 1.5) |
| `JWT_SECRET` | Un texto largo y secreto |
| `AI_SERVICE_URL` | URL del servicio de IA en Render |
| `CORS_ORIGINS` | `*` (o los dominios que vayan a consumir la API, separados por coma) |
| `SEED_ON_STARTUP` | `true` (carga los datos de ejemplo si la base está vacía) |
| `PROFESOR_PASSWORD` | (opcional) clave de la cuenta del profesor |

3. Si venías de PostgreSQL, **borra** `DATABASE_URL`.
4. **Save, rebuild, and deploy.** En *Logs* debe salir `Estructuras cargadas: ...`.
   Si sale `bad auth : authentication failed`, la clave de la URI está mal.
5. Repite con **Root Directory:** `ai` para el componente de IA (variable opcional `GEMINI_API_KEY`).

> Primero crea `MONGODB_URI` y después despliega: sin ella el backend no arranca.

## 3. Probar la API publicada

Abre `https://TU-BACKEND.onrender.com/docs` (Swagger), haz `POST /api/v1/auth/login` con `ana@alertabarrio.co` / `Alerta2026*`, copia el `access_token` y pégalo en **Authorize**.

## 4. CI y servidores despiertos

- `.github/workflows/ci.yml` corre las pruebas del backend contra un **MongoDB 7** real, las de la IA y construye las imágenes Docker.
- Para desplegar desde el CI, crea los secretos `RENDER_DEPLOY_HOOK_BACKEND` y `RENDER_DEPLOY_HOOK_AI` (*Settings → Secrets and variables → Actions*).
- `keep-alive.yml` despierta Render cada 10 minutos: crea las variables `BACKEND_URL` y `AI_URL`.

## Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `bad auth : authentication failed` | La URI tiene `<db_password>` o una clave vieja | Pon la clave real del *Database User* |
| `ServerSelectionTimeoutError` | Atlas no deja entrar a Render | *Network Access* → `0.0.0.0/0` |
| Clave nueva que no funciona | Faltó **Update User** en Atlas | Edita el usuario, genera la clave y dale **Update User** |
| `502` o la primera llamada tarda | Render estaba dormido | Espera unos segundos o activa `keep-alive.yml` |
