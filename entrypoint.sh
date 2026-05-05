#!/bin/bash
set -euo pipefail

# Esperar servicios dependientes
if [ "${WAIT_FOR_SERVICES:-false}" = "true" ]; then
    echo "Waiting for dependencies..."
    /app/src/scripts/wait-for-it.sh "${DATABASE_HOST:-db}:${DATABASE_PORT:-5432}" -t 60
fi

# Ejecutar migraciones
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

exec "$@"
