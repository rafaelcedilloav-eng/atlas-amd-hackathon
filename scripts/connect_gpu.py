import paramiko
import time
import os

# Configuración obtenida del entorno (evitando hardcoding)
HOST = "165.245.138.52"
USER = "root"
PASSWORD = os.getenv("REMOTE_SSH_PASSWORD")
PORT = 22

def execute_remote_cmd(cmd):
    """Conecta via SSH y ejecuta comando"""
    if not PASSWORD:
        print("[✗] Error: REMOTE_SSH_PASSWORD no configurado en variables de entorno.")
        return None

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD)
        print(f"[✓] Conectado a {HOST}")

        stdin, stdout, stderr = ssh.exec_command(cmd)

        output = stdout.read().decode()
        error = stderr.read().decode()

        print(f"[→] Comando: {cmd}")
        print(f"[↓] Output:\n{output}")
        if error:
            print(f"[✗] Error:\n{error}")

        ssh.close()
        return output

    except Exception as e:
        print(f"[✗] Error de conexión: {e}")
        return None

if __name__ == "__main__":
    print("--- Diagnóstico ATLAS V3.0 ---")
    execute_remote_cmd("docker logs atlas-core | tail -20")
    execute_remote_cmd("docker ps")
    execute_remote_cmd("rocm-smi")
