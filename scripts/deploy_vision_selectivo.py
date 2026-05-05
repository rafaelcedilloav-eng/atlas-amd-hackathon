import requests
import json

HOST = "165.245.138.52"
PORT = 8888
TOKEN = "***REMOVED***"
BASE_URL = f"http://{HOST}:{PORT}"
HEADERS = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}

def deploy_vision_only():
    print("[*] Iniciando despliegue selectivo: solo atlas-vision...")
    
    # Intentar ejecutar comando vía terminal de Jupyter
    # Primero obtenemos terminales existentes o creamos uno
    term_url = f"{BASE_URL}/api/terminals"
    try:
        response = requests.post(term_url, headers=HEADERS)
        term_name = response.json()['name']
        print(f"[+] Terminal creada: {term_name}")
        
        # Como no tengo acceso WebSocket, probaré si hay un endpoint de ejecución directa
        # Si el servidor lo deniega, el log me lo dirá claramente
        print("[!] Nota: API de Jupyter requiere WebSocket para ejecutar comandos.")
        print("[!] Si el despliegue falla, el servidor requiere SSH.")
        
    except Exception as e:
        print(f"[!] Error de conexión: {e}")

if __name__ == "__main__":
    deploy_vision_only()
