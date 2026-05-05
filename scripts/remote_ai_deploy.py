#!/usr/bin/env python3
import sys, time, ssl, urllib3, json
import requests, websocket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JUPYTER_HOST = "165.245.138.52"
JUPYTER_PORT = 8888
TOKEN = "***REMOVED***"
BASE_URL = f"http://{JUPYTER_HOST}:{JUPYTER_PORT}"
HEADERS = {"Authorization": f"token {TOKEN}"}

# Comandos corregidos por Kimi-K2 y Gemini
COMMANDS = [
    # 1. Limpieza radical
    "docker rm -f atlas-router atlas-vision atlas-core dc34431e4d66 2>&1 || true",
    
    # 2. Lanzar Core (Motor 8000) - Dragon-LLaMA
    "docker run -d --name atlas-core --device=/dev/kfd --device=/dev/dri -p 8000:8000 "
    "-v /mnt/scratch/models:/models -v /mnt/atlas_data/adapters:/adapters "
    "-e HSA_OVERRIDE_GFX_VERSION=9.4.2 vllm/vllm-openai-rocm:v0.17.1 "
    "vllm serve /models/dragon-llama-finance-8b --enable-lora "
    "--lora-modules phi=/adapters/phi qwen=/adapters/qwen "
    "--tensor-parallel-size 2 --gpu-memory-utilization 0.40",
    
    # 3. Lanzar Vision (Motor 8002) - InternVL2-40B (Tarda unos minutos en subir)
    "docker run -d --name atlas-vision --device=/dev/kfd --device=/dev/dri -p 8002:8000 "
    "-v /mnt/scratch/models:/models -e HSA_OVERRIDE_GFX_VERSION=9.4.2 "
    "vllm/vllm-openai-rocm:v0.17.1 vllm serve --model /models/InternVL2-40B "
    "--tensor-parallel-size 4 --gpu-memory-utilization 0.45 --trust-remote-code",
    
    # 4. Lanzar Router (Motor 11434) - Ollama
    "docker run -d --name atlas-router --device=/dev/kfd --device=/dev/dri -p 11434:11434 "
    "-v /mnt/scratch/ollama:/root/.ollama -e HSA_OVERRIDE_GFX_VERSION=9.4.2 "
    "ollama/ollama:rocm",
    
    # 5. Check de status final
    "docker ps"
]

def create_terminal():
    print(f"[→] Intentando crear terminal en {BASE_URL}...")
    r = requests.post(f"{BASE_URL}/api/terminals", headers=HEADERS, verify=False, timeout=15)
    r.raise_for_status()
    return r.json()['name']

def execute(terminal_id, cmd):
    ws_url = f"ws://{JUPYTER_HOST}:{JUPYTER_PORT}/terminals/websocket/{terminal_id}?token={TOKEN}"
    ws = websocket.create_connection(ws_url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=30)
    # Formato de mensaje Jupyter Terminal: ["stdin", "comando\r"]
    msg = json.dumps(["stdin", f"{cmd}\r"])
    ws.send(msg)
    time.sleep(3)
    # Recibir respuesta para ver que paso
    try:
        result = ws.recv()
        # print(f"    Respuesta: {result[:100]}...")
    except:
        pass
    ws.close()

def main():
    print("=" * 70)
    print("ATLAS MI300X REMOTE AI TEAM DEPLOYMENT")
    print("=" * 70)

    try:
        terminal_id = create_terminal()
        print(f"[✓] Terminal remoto creado: {terminal_id}")

        for idx, cmd in enumerate(COMMANDS, 1):
            print(f"[→] Paso {idx}/{len(COMMANDS)}: {cmd[:60]}...")
            execute(terminal_id, cmd)
            print(f"    Comando enviado.")
            time.sleep(2)

        print("\n" + "=" * 70)
        print("[✓] OPERACIÓN REMOTA COMPLETADA")
        print("Los cerebros están cargando en las GPUs MI300X.")
        print("Espera ~3 minutos para que InternVL2 (Motor 8002) termine de cargar.")
        print("=" * 70)

    except Exception as e:
        print(f"[✗] Error fatal en la conexión: {e}")

if __name__ == "__main__":
    main()
