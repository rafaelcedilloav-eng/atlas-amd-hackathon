# MANUAL DE OPERACIÓN: DESPLIEGUE MI300X - ATLAS v3.0

**Arquitecto Jefe: Kimi-K2 | Estado: CRÍTICO | Ejecutar en orden estricto**

---

## 1. CONFIGURACIÓN DEL SERVIDOR DE PÁGINA (API/FRONTEND)

### Puertos Firewall - API SERVER
```bash
# Ejecutar como root
sudo ufw --force reset
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 11434/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
sudo ufw --force enable
```

### Variables de Entorno - .env (Frontend/API)
```bash
# En /opt/atlas/.env
cat > /opt/atlas/.env << 'EOF'
# CRÍTICO: Backend API endpoint
REACT_APP_API_BASE_URL=http://<GPU_SERVER_IP>:5000
API_HOST=0.0.0.0
API_PORT=5000

# Motor 8000 - Dragon-LLaMA
DRAGON_API_URL=http://<GPU_SERVER_IP>:8000
DRAGON_API_KEY=atlas_dragon_k3y_v3

# Motor 8002 - InternVL2
INTERNVL_API_URL=http://<GPU_SERVER_IP>:8002
INTERNVL_API_KEY=atlas_internvl_k3y_v3

# Motor 11434 - Ollama
OLLAMA_API_URL=http://<GPU_SERVER_IP>:11434
OLLAMA_API_KEY=atlas_ollama_k3y_v3

# Seguridad
JWT_SECRET=$(openssl rand -hex 32)
CORS_ORIGIN=http://<FRONTEND_IP>:3000
EOF
```

---

## 2. PARÁMETROS GPU SERVER (MI300X)

### Pre-Flight Check
```bash
# Validar MI300X detectada
rocm-smi --showtopo
rocminfo | grep gfx942

# Si no detecta:
export HSA_OVERRIDE_GFX_VERSION=9.4.2
```

### Docker Run - Motor 8000 (Dragon-LLaMA-8B)
```bash
docker run -d --name dragon-llama \
  --device=/dev/kfd --device=/dev/dri \
  --security-opt seccomp=unconfined \
  --group-add video \
  -p 8000:8000 \
  -e HSA_OVERRIDE_GFX_VERSION=9.4.2 \
  -e HSA_ENABLE_SDMA=0 \
  -e HIP_VISIBLE_DEVICES=0,1 \
  -e NUM_GPUS=2 \
  -e CUDA_VISIBLE_DEVICES=0,1 \
  -e MODEL_PATH=/models/dragon-llama-8b \
  -e MAX_MODEL_LEN=32768 \
  -e TENSOR_PARALLEL_SIZE=2 \
  -e GPU_MEMORY_UTILIZATION=0.95 \
  -e DTYPE=auto \
  -e API_KEY=atlas_dragon_k3y_v3 \
  --ipc host \
  --cap-add SYS_PTRACE \
  -v /opt/atlas/models:/models \
  --restart unless-stopped \
  ghcr.io/atlas-dragon/llama-rocm:v3.0 \
  --model /models/dragon-llama-8b \
  --tensor-parallel-size 2 \
  --enforce-eager \
  --host 0.0.0.0 \
  --port 8000
```

### Docker Run - Motor 8002 (InternVL2-40B)
```bash
docker run -d --name internvl2-40b \
  --device=/dev/kfd --device=/dev/dri \
  --security-opt seccomp=unconfined \
  --group-add video \
  -p 8002:8002 \
  -e HSA_OVERRIDE_GFX_VERSION=9.4.2 \
  -e HIP_VISIBLE_DEVICES=2,3 \
  -e CUDA_VISIBLE_DEVICES=2,3 \
  -e NUM_GPUS=2 \
  -e MODEL_PATH=/models/internvl2-40b \
  -e MAX_NUM_BATCHED_TOKENS=32768 \
  -e TENSOR_PARALLEL_SIZE=2 \
  -e GPU_MEMORY_UTILIZATION=0.90 \
  -e DTYPE=fp16 \
  -e API_KEY=atlas_internvl_k3y_v3 \
  -e PORT=8002 \
  --ipc host \
  --cap-add SYS_PTRACE \
  -v /opt/atlas/models:/models \
  --restart unless-stopped \
  ghcr.io/atlas-vision/internvl2-rocm:v3.0 \
  --model /models/internvl2-40b \
  --tensor-parallel-size 2 \
  --host 0.0.0.0 \
  --port 8002
```

### Docker Run - Motor 11434 (Ollama)
```bash
docker run -d --name ollama-mi300x \
  --device=/dev/kfd --device=/dev/dri \
  --security-opt seccomp=unconfined \
  --group-add video \
  -p 11434:11434 \
  -e HSA_OVERRIDE_GFX_VERSION=9.4.2 \
  -e HIP_VISIBLE_DEVICES=4 \
  -e OLLAMA_NUM_PARALLEL=4 \
  -e OLLAMA_MAX_LOADED_MODELS=1 \
  -e OLLAMA_DEBUG=1 \
  -e OLLAMA_HOST=0.0.0.0 \
  -e OLLAMA_PORT=11434 \
  -e OLLAMA_API_KEY=atlas_ollama_k3y_v3 \
  -v ollama:/root/.ollama \
  --ipc host \
  --restart unless-stopped \
  ghcr.io/atlas-ollama/ollama-rocm:v3.0
```

---

## 3. INTEGRACIÓN - EL PUENTE

### Backend Configuration
```python
# File: /opt/atlas/backend/config.yaml
gpu_server:
  # IP ESTÁTICA DEL MI300X SERVER
  host: 10.0.0.100
  ports:
    dragon: 8000
    internvl: 8002
    ollama: 11434
  
# Validación de conexión
validation:
  timeout: 30s
  retry_count: 3
  endpoints:
    - http://10.0.0.100:8000/health
    - http://10.0.0.100:8002/health
    - http://10.0.0.100:11434/api/tags
```

### Pre-Launch Validation Checklist
```bash
#!/bin/bash
# Guardar como /opt/atlas/validar_gpus.sh
echo "[ATLAS] VALIDACIÓN DE CEREBROS..."

# Dragon-LLaMA
curl -s -X GET http://10.0.0.100:8000/health \
  -H "Authorization: Bearer atlas_dragon_k3y_v3" | jq .

# InternVL2
curl -s -X GET http://10.0.0.100:8002/health \
  -H "Authorization: Bearer atlas_internvl_k3y_v3" | jq .

# Ollama
curl -s -X GET http://10.0.0.100:11434/api/tags \
  -H "Authorization: Bearer atlas_ollama_k3y_v3" | jq .

echo "[ATLAS] Si ves respuestas JSON en los 3, el puente está OPERATIVO."
```

### Comando de Validación Final
```bash
chmod +x /opt/atlas/validar_gpus.sh
/opt/atlas/validar_gpus.sh

# Salida exitosa debe ser:
# {"status":"healthy","model":"dragon-llama-8b"}
# {"status":"healthy","model":"internvl2-40b"}
# {"models":[{"name":"llama3.1:latest"}]}
```

### Inicio Secuencial
```bash
# ORDEN DE ENCIENDIDO - NO ALTERAR
systemctl start docker
docker start dragon-llama && sleep 5
docker start internvl2-40b && sleep 10
docker start ollama-mi300x && sleep 5
/opt/atlas/validar_gpus.sh && echo "ATLAS v3.0 OPERATIVO"
```

---

**ESTADO: SISTEMAS ARMADOS. EJECUTAR VALIDACIÓN ANTIES DE CUALQUIER INGESTA DE PDF.**

**FIN DE MANUAL.**