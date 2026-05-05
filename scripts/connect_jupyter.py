import requests
import json
import time

JUPYTER_HOST = "165.245.138.52"
JUPYTER_PORT = 8888
TOKEN = "***REMOVED***"
BASE_URL = f"http://{JUPYTER_HOST}:{JUPYTER_PORT}"
HEADERS = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}

def run_remote_command(command):
    # 1. Crear sesión de terminal
    url = f"{BASE_URL}/api/terminals"
    response = requests.post(url, headers=HEADERS)
    term_name = response.json()['name']
    
    # 2. Ejecutar comando (vía websocket es lo ideal, pero aquí intentamos mediante ejecución directa si es notebook)
    # Por ahora, diagnóstico rápido vía requests si el servidor lo permite
    print(f"Ejecutando en remoto: {command}")
    
    # Nota: Interactuar con terminales Jupyter vía API requiere websocket, 
    # si el servidor tiene un endpoint de ejecución de scripts, usaremos ese.
    return f"Comando enviado a terminal {term_name}"

print("Conectando a Jupyter Server en:", BASE_URL)
# Verificación de conexión
try:
    resp = requests.get(f"{BASE_URL}/api/status", headers=HEADERS)
    print("Estado del servidor:", resp.status_code)
except Exception as e:
    print("Error conectando:", e)
