#!/bin/bash
# ATLAS v3.0 MASTER DEPLOYMENT SCRIPT
set -e

echo "--- 1. Preparando entorno ---"
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends docker-compose-plugin curl git

echo "--- 2. Creando directorios y caché ---"
mkdir -p /mnt/scratch/{models,ollama}
mkdir -p /mnt/atlas_data/adapters
chmod -R 755 /mnt/scratch /mnt/atlas_data

echo "--- 3. Generando Docker Compose ---"
cat > docker-compose.yml << 'EOF'
services:
  core:
    image: vllm/vllm-openai:latest
    container_name: atlas-core
    restart: unless-stopped
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    volumes:
      - "/mnt/scratch/models:/models:ro"
      - "/mnt/atlas_data/adapters:/adapters:ro"
    ports: ["8000:8000"]
    command: >
      python3 -m vllm.entrypoints.openai.api_server
      --model /models/dragon-llama-finance-8b
      --enable-lora 
      --lora-modules phi=/adapters/phi qwen=/adapters/qwen
      --gpu-memory-utilization 0.40

  router:
    image: ollama/ollama:rocm
    container_name: atlas-router
    restart: unless-stopped
    devices: ["/dev/kfd", "/dev/dri"]
    volumes: ["/mnt/scratch/ollama:/root/.ollama"]
    ports: ["11434:11434"]

  vision:
    image: vllm/vllm-openai:latest
    container_name: atlas-vision
    restart: unless-stopped
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    volumes: ["/mnt/scratch/models:/models:ro"]
    ports: ["8002:8000"]
    command: >
      python3 -m vllm.entrypoints.openai.api_server
      --model /models/InternVL2-40B
      --gpu-memory-utilization 0.40
EOF

echo "--- 4. Lanzando Ecosistema ---"
docker compose up -d

echo "--- 5. Verificación ---"
sleep 5
docker compose ps
echo "--- ATLAS 3.0 LISTO ---"
EOF
