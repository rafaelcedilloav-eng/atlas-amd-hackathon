import paramiko
import time

# Configuración
HOST = "165.245.138.52"
USER = "root"
PASSWORD = "***REMOVED***"  # SE REQUIERE CONTRASEÑA O CLAVE
PORT = 22

# Comandos de despliegue según protocolo Kimi-K2
COMMANDS = [
    "docker rm -f atlas-router atlas-vision atlas-core 2>/dev/null || true",
    "docker run -d --name atlas-core -p 8000:8000 --restart unless-stopped atlas-core:latest",
    "docker run -d --name atlas-vision -p 8002:8002 --restart unless-stopped atlas-vision:latest",
    "docker run -d --name atlas-router -p 11434:11434 --restart unless-stopped atlas-router:latest",
    "docker ps --filter 'name=atlas-*' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
]

def deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[*] Conectando a {HOST}...")
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD)
        
        for cmd in COMMANDS:
            print(f"[→] Ejecutando: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            
            # Esperar a que termine
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output: print(f"[↓] Output:\n{output}")
            if error: print(f"[✗] Error:\n{error}")
            
            time.sleep(2)
            
        ssh.close()
        print("[✓] Despliegue completado.")

    except Exception as e:
        print(f"[✗] Error en despliegue: {e}")

if __name__ == "__main__":
    deploy()
