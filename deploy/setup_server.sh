#!/bin/bash
# ATLAS — Setup completo del servidor Ubuntu (AMD MI300X)
# Ejecutar como root: bash setup_server.sh

set -e
echo "=== ATLAS Server Setup ==="

# 1. Sistema base
apt-get update -y
apt-get install -y \
    nginx certbot python3-certbot-nginx \
    docker.io docker-compose-plugin \
    git curl ufw

# 2. Firewall — permitir solo lo necesario
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
# NO abrir 8080 ni 3000 al exterior — solo nginx los expone
ufw --force enable

# 3. Docker
systemctl enable docker
systemctl start docker

# 4. Clonar proyecto
cd /opt
if [ -d "atlas-amd-hackathon" ]; then
    cd atlas-amd-hackathon && git pull origin main
else
    git clone https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon.git
    cd atlas-amd-hackathon
fi

# 5. Crear .env de producción (se copia el template y se llena manualmente)
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo ">>> IMPORTANTE: Edita /opt/atlas-amd-hackathon/.env con las credenciales reales"
    echo ">>> Luego vuelve a ejecutar: bash deploy/setup_server.sh"
    exit 0
fi

# 6. nginx config
cp deploy/nginx.conf /etc/nginx/sites-available/atlas
ln -sf /etc/nginx/sites-available/atlas /etc/nginx/sites-enabled/atlas
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 7. SSL con Let's Encrypt
certbot --nginx \
    -d atlas-hackathon.com \
    -d www.atlas-hackathon.com \
    -d api.atlas-hackathon.com \
    --non-interactive \
    --agree-tos \
    --email cedillo.rafael@icloud.com \
    --redirect

# 8. Build y levantar contenedores
docker compose build --no-cache
docker compose up -d

# 9. Verificar que todo corre
sleep 5
echo ""
echo "=== Verificación ==="
docker compose ps
curl -s http://localhost:8080/stats && echo " <- API OK"
curl -s -o /dev/null -w "Frontend HTTP %{http_code}" http://localhost:3000
echo ""
echo "=== Deploy completado ==="
echo "Frontend: https://www.atlas-hackathon.com"
echo "API:      https://api.atlas-hackathon.com"
echo "Docs:     https://api.atlas-hackathon.com/docs"
