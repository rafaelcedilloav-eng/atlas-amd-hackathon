import os
import sys
import json
import requests

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def remote_gpu_setup():
    client = KimiK2Client()
    
    # Credenciales proporcionadas
    target_ip = "165.245.138.52"
    jupyter_token = "***REMOVED***"
    
    prompt = f"""
OPERACIÓN REMOTA: CONFIGURACIÓN DE GPU MI300X VIA JUPYTER API
IP: {target_ip}
Token: {jupyter_token}

TAREA:
1. Diseña la secuencia de llamadas CURL para interactuar con la API de Jupyter (Terminals) y ejecutar los comandos de limpieza y encendido.
2. Comandos a ejecutar:
   - Limpieza: docker rm -f atlas-router atlas-vision dc34431e4d66
   - Lanzamiento atlas-core (puerto 8000)
   - Lanzamiento atlas-vision (puerto 8002)
   - Lanzamiento atlas-router (puerto 11434)
3. Genera un script Python que yo (Gemini) pueda ejecutar localmente para enviar estos comandos al servidor remoto.

Responde con el script Python exacto y el orden de ejecución.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2, el cerebro táctico de ATLAS. Estás coordinando una operación remota de despliegue en hardware AMD MI300X."},
        {"role": "user", "content": prompt}
    ]
    
    print("--- COORDINANDO CON KIMI-K2 PARA EL ACCESO REMOTO ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            plan = response['choices'][0]['message']['content']
            
            filename = "docs/REMOTE_DEPLOY_PLAN.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(plan)
            
            print(f"\nPlan de acceso remoto generado en: {filename}")
            return plan
    except Exception as e:
        print(f"Error en coordinación remota: {e}")

if __name__ == "__main__":
    remote_gpu_setup()
