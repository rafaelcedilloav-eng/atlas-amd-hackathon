#!/usr/bin/env python3
"""
ATLAS MI300X REMOTE DEPLOYMENT SCRIPT
========================================
Configura GPU AMD MI300X remotamente via Jupyter API.
Optimizado para arquitectura v3.0 Triple-Engine.
"""

import sys
import time
import ssl
import urllib3
import socket
import json
import requests
import websocket

# ============================================
# CONFIGURACIÓN DE ACCESO (PROVIDE BY USER)
# ============================================
JUPYTER_HOST = "165.245.138.52"
JUPYTER_PORT = 80 # Jupyter suele estar en 8888 o 80 segun config, usuario dio URL base
TOKEN = "***REMOVED***"
BASE_URL = f"http://{JUPYTER_HOST}"
HEADERS = {"Authorization": f"token {TOKEN}"}

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# SECUENCIA DE COMANDOS (Triple-Engine Architecture)
# ============================================
COMMANDS = [
    # 1. Limpieza total
    "docker rm -f atlas-router atlas-vision dc34431e4d66 atlas-core 2>&1 || true",
    
    # 2. Lanzamiento Core (Motor 8000) - Dragon-LLaMA
    "docker run -d --name atlas-core --device=/dev/kfd --device=/dev/dri -p 8000:8000 "
    "-v /mnt/scratch/models:/models -v /mnt/atlas_data/adapters:/adapters "
    "-e HSA_OVERRIDE_GFX_VERSION=9.4.2 vllm/vllm-openai-rocm:v0.17.1 "
    "vllm serve /models/dragon-llama-finance-8b --enable-lora "
    "--lora-modules phi=/adapters/phi qwen=/adapters/qwen "
    "--tensor-parallel-size 2 --gpu-memory-utilization 0.40",
    
    # 3. Lanzamiento Vision (Motor 8002) - InternVL2-40B
    "docker run -d --name atlas-vision --device=/dev/kfd --device=/dev/dri -p 8002:8000 "
    "-v /mnt/scratch/models:/models -e HSA_OVERRIDE_GFX_VERSION=9.4.2 "
    "vllm/vllm-openai-rocm:v0.17.1 vllm serve --model /models/InternVL2-40B "
    "--tensor-parallel-size 4 --gpu-memory-utilization 0.45 --trust-remote-code",
    
    # 4. Lanzamiento Router (Motor 11434) - Ollama
    "docker run -d --name atlas-router --device=/dev/kfd --device=/dev/dri -p 11434:11434 "
    "-v /mnt/scratch/ollama:/root/.ollama -e HSA_OVERRIDE_GFX_VERSION=9.4.2 "
    "ollama/ollama:rocm"
]

def check_connectivity():
    print(f"[→] Verificando conectividad a {JUPYTER_HOST}...")
    try:
        r = requests.get(f"{BASE_URL}/api/status?token={TOKEN}", timeout=10)
        if r.status_code == 200:
            print("[✓] Jupyter Server responde correctamente.")
            return True
        else:
            print(f"[✗] Error de acceso: {r.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Error de conexión: {e}")
        return False

def create_terminal():
    url = f"{BASE_URL}/api/terminals?token={TOKEN}"
    try:
        r = requests.post(url, timeout=10)
        r.raise_for_status()
        t_id = r.json()['name']
        print(f"[✓] Terminal remoto creado: {t_id}")
        return t_id
    except Exception as e:
        print(f"[✗] Error creando terminal: {e}")
        return None

def execute_remote(t_id, cmd):
    # En Jupyter API, enviamos el comando via websocket como si fuera tecleado
    ws_url = f"ws://{JUPYTER_HOST}/terminals/websocket/{t_id}?token={TOKEN}"
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        # Formato de mensaje Jupyter Terminal: ["stdin", "comando\r"]
        msg = json.dumps(["stdin", f"{cmd}\r"])
        ws.send(msg)
        time.sleep(2)
        ws.close()
        return True
    except Exception as e:
        print(f"[✗] Fallo WebSocket: {e}")
        return False

def run_deployment():
    print("=== ATLAS v3.0 REMOTE DEPLOYMENT SWARM ===")
    if not check_connectivity(): return
    
    t_id = create_terminal()
    if not t_id: return
    
    print(f"\n[!] Iniciando despliegue de los 3 Cerebros...")
    for i, cmd in enumerate(COMMANDS, 1):
        print(f"[{i}/{len(COMMANDS)}] Ejecutando comando remoto...")
        if execute_remote(t_id, cmd):
            print("    Enviado exitosamente.")
            time.sleep(5) # Delay para estabilidad
        else:
            print("    ERROR en envío.")
            break
            
    print("\n[✓] Operación finalizada. Los contenedores están arrancando en el MI300X Cluster.")
    print("Puertos: Core (8000), Vision (8002), Router (11434)")

if __name__ == "__main__":
    run_deployment()
