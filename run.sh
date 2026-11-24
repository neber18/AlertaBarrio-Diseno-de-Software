#!/usr/bin/env bash
# Levanta AlertaBarrio en local: MongoDB + backend.
# Uso: ./run.sh      (Ctrl+C para detener todo)
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS="$PROJECT_DIR/.logs"
mkdir -p "$LOGS"

# ── 1. Liberar puertos ────────────────────────────────────────────────────────
echo "[1/3] Liberando el puerto 8000..."
for port in 8000; do
  (lsof -ti:"$port" | xargs kill -9) 2>/dev/null || true
done

# ── 2. MongoDB: usa el de la maquina si ya hay uno en :27017; si no, Docker ───
echo "[2/3] Preparando MongoDB..."
if (ss -tln 2>/dev/null || netstat -tln 2>/dev/null) | grep -q ':27017'; then
  echo "       Ya hay un MongoDB en :27017, se usa ese."
else
  echo "       Levantando el contenedor de MongoDB..."
  docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d mongodb
  until docker exec alertabarrio-mongo mongosh --quiet --eval 'db.adminCommand("ping").ok' >/dev/null 2>&1; do
    sleep 2
  done
fi
export MONGODB_URI="mongodb://localhost:27017/alertabarrio"
echo "       MongoDB listo: $MONGODB_URI"

# ── helper: crea el entorno virtual de Python si no existe ───────────────────
setup_python() {
  cd "$PROJECT_DIR/$1"
  if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements-dev.txt
  fi
  [ -f .env ] || cp .env.example .env
}

# ── 3. Backend (8000) ─────────────────────────────────────────────────────────
echo "[3/3] Iniciando el backend..."
setup_python backend
PIDS=""
.venv/bin/uvicorn app.main:app --port 8000 > "$LOGS/backend.log" 2>&1 &
BACKEND_PID=$!
PIDS="$PIDS $BACKEND_PID"
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "ERROR: el backend no arranco. Revisa $LOGS/backend.log"
    tail -30 "$LOGS/backend.log"
    exit 1
  fi
  sleep 2
done
echo "       Backend listo en http://localhost:8000 (Swagger en /docs)"

trap 'echo; echo "Deteniendo..."; kill $PIDS 2>/dev/null; exit 0' INT TERM
echo ""
echo "=============================================="
echo "  AlertaBarrio esta corriendo"
echo "  Backend:   http://localhost:8000/docs"
echo "  Logs:      $LOGS"
echo "  Cuenta:    ana@alertabarrio.co / Alerta2026*"
echo "=============================================="
echo "Ctrl+C para detener."
wait
