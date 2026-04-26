#!/bin/bash
# ATLAS — Redeploy rápido (usar después del setup inicial)
set -e
cd /opt/atlas-amd-hackathon
git pull origin main
docker compose build --no-cache
docker compose up -d --force-recreate
docker compose ps
echo "Redeploy completado."
