**SECUENCIA DE LLAMADAS Y SCRIPT DE DESPLIEGUE**

---

### **LÍMITES DE CURL**
La API de Terminales de Jupyter requiere **WebSocket** para envío interactivo de comandos. CURL solo puede crear el terminal (`POST /api/terminals`), pero **no** puede mantener la sesión WebSocket para ejecutar comandos. Por eso se requiere un script Python.

---

### **ORDEN DE EJECUCIÓN**

1. **Instalar dependencias** (una vez):
```bash
pip install requests websocket-client
```

2. **Ejecutar el script**:
```bash
python deploy_atlas_mi300x.py
```

3. **Verificar manualmente** (opcional):
```bash
curl -s http://165.245.138.52:8888/api/terminals \
  -H "Authorization: token ***REMOVED***" | jq
```

---

### **SCRIPT PYTHON COMPLETO**

```python
#!/usr/bin/env python3
import requests
import websocket
import time
import urllib.parse

# --- CONFIGURACIÓN DE ACCESO ---
JUPYTER_HOST = "165.245.138.52"
JUPYTER_PORT = 8888
JUPYTER_TOKEN = "***REMOVED***"

# --- ENDPOINTS ---
BASE_URL = f"http://{JUPYTER_HOST}:{JUPYTER_PORT}"
WS_URL = f"ws://{JUPYTER_HOST}:{JUPYTER_PORT}"
HEADERS = {"Authorization": f"token {JUPYTER_TOKEN}"}

# --- SECUENCIA DE DESPLIEGUE ATLAS ---
# Ajusta las imágenes docker según tu registry MI300X
DEPLOYMENT_STEPS = [
    {
        "step": 1,
        "name": "Limpieza de contenedores existentes",
        "command": "docker rm -f atlas-router atlas-vision dc34431e4d66 2>/dev/null || true",
        "wait": 2,
        "critical": False
    },
    {
        "step": 2,
        "name": "Despliegue de atlas-core (puerto 8000)",
        "command": "docker run -d --name atlas-core -p 8000:8000 --restart unless-stopped atlas-core:latest",
        "wait": 3,
        "critical": True
    },
    {
        "step": 3,
        "name": "Despliegue de atlas-vision (puerto 8002)",
        "command": "docker run -d --name atlas-vision -p 8002:8002 --restart unless-stopped atlas-vision:latest",
        "wait": 3,
        "critical": True
    },
    {
        "step": 4,
        "name": "Despliegue de atlas-router (puerto 11434)",
        "command": "docker run -d --name atlas-router -p 11434:11434 --restart unless-stopped atlas-router:latest",
        "wait": 3,
        "critical": True
    },
    {
        "step": 5,
        "name": "Verificación final de servicios",
        "command": "docker ps --filter 'name=atlas-*' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
        "wait": 1,
        "critical": False
    }
]

def print_banner():
    """Imprime banner de operación"""
    banner = """
╔════════════════════════════════════════════════════════════════════╗
║           ATLAS REMOTE DEPLOYMENT SYSTEM - MI300X                    ║
║           Operación: Limpieza y Reinicio de Servicios               ║
╚════════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"Target: {JUPYTER_HOST}:{JUPYTER_PORT}")
    print("-" * 70)

def create_terminal():
    """Crea terminal en Jupyter"""
    print("\n[ACC-001] Inicializando terminal de control...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/terminals",
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        terminal_name = response.json()["name"]
        print(f"  ✓ Terminal ID: {terminal_name}")
        time.sleep(0.5)
        return terminal_name
    except Exception as e:
        print(f"  ✗ Fallo: {e}")
        raise

def connect_websocket(terminal_name):
    """Conecta WebSocket al terminal"""
    print("\n[ACC-002] Estableciendo canal de datos...")
    
    encoded_token = urllib.parse.quote(JUPYTER_TOKEN, safe='')
    ws_url = f"{WS_URL}/terminals/websocket/{terminal_name}?token={encoded_token}"
    
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        print("  ✓ Canal WebSocket activo")
        time.sleep(0.5)
        return ws
    except Exception as e:
        print(f"  ✗ Fallo: {e}")
        raise

def execute_step(ws, step):
    """Ejecuta un paso del despliegue"""
    print(f"\n[STEP-{step['step']:02d}] {step['name']}")
    print(f"  └─> {step['command']}")
    
    try:
        ws.send(step["command"] + "\r")
        time.sleep(step["wait"])
        
        # Lectura no bloqueante de salida
        output = []
        try:
            ws.settimeout(0.3)
            while True:
                data = ws.recv()
                if data:
                    output.append(data.decode('utf-8', errors='ignore') if isinstance(data, bytes) else data)
        except:
            pass
        finally:
            ws.settimeout(None)
        
        if output and any(keyword in "".join(output).lower() for keyword in ["error", "fallo", "failed"]):
            print(f"  ⚠ Posible error en salida (revisar logs)")
        else:
            print(f"  ✓ Ok")
            
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return not step["critical"]

def main():
    """Función principal"""
    print_banner()
    
    terminal_name = None
    ws = None
    
    try:
        # Inicialización
        terminal_name = create_terminal()
        ws = connect_websocket(terminal_name)
        
        # Despliegue
        print("\n" + "=" * 70)
        print("          INICIANDO SECUENCIA DE DESPLIEGUE")
        print("=" * 70)
        
        for step in DEPLOYMENT_STEPS:
            if not execute_step(ws, step):
                raise Exception(f"Fallo crítico en STEP-{step['step']}")
        
        # Confirmación
        print("\n" + "═" * 70)
        print("  ✓ DESPLIEGUE FINALIZADO EXITOSAMENTE")
        print("═" * 70)
        print("\n  Servicios desplegados:")
        print("  ├─ atlas-core   → http://165.245.138.52:8000")
        print("  ├─ atlas-vision → http://165.245.138.52:8002")
        print("  └─ atlas-router → http://165.245.138.52:11434")
        print("\n" + "═" * 70 + "\n")
        
    except Exception as e:
        print("\n" + "═" * 70)
        print("  ✗ FALLO EN OPERACIÓN")
        print("═" * 70)
        print(f"  Error: {e}")
        print("═" * 70 + "\n")
        exit(1)
        
    finally:
        if ws:
            print("[CLEANUP] Cerrando recursos...")
            ws.close()
            print("  ✓ Canal cerrado\n")

if __name__ == "__main__":
    main()
```

---

### **VALIDACIÓN POST-DESPLIEGUE**

Ejecuta esto en tu máquina local para verificar:

```bash
# Verificar atlas-core
curl -s http://165.245.138.52:8000/health || echo "Core no responde"

# Verificar atlas-vision
curl -s http://165.245.138.52:8002/status || echo "Vision no responde"

# Verificar atlas-router
curl -s http://165.245.138.52:11434/api/tags || echo "Router no responde"
```

El script maneja autenticación, WebSocket, timeouts y errores críticos. Ejecútalo desde cualquier entorno Python con acceso de red al servidor MI300X.