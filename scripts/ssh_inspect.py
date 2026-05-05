import paramiko
import time

# Configuración
HOST = "165.245.138.52"
USER = "root"
PASSWORD = "***REMOVED***"
PORT = 22

def execute_remote_cmd(ssh, cmd):
    print(f"\n[→] Ejecutando: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    # Leer output
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if output: print(f"[↓] Output:\n{output}")
    if error: print(f"[✗] Error:\n{error}")
    return output, error

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[→] Conectando a {HOST}...")
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD)
        print(f"[✓] Conectado.")

        # 1. Revisar estado actual
        execute_remote_cmd(ssh, "docker ps -a")
        
        # 2. Revisar logs detallados de los que fallan
        execute_remote_cmd(ssh, "docker logs atlas-core --tail 50")
        execute_remote_cmd(ssh, "docker logs atlas-vision --tail 50")
        
        # 3. Revisar GPUs
        execute_remote_cmd(ssh, "rocm-smi")

        ssh.close()
        print("\n[✓] Inspección finalizada.")

    except Exception as e:
        print(f"[✗] Error de conexión: {e}")

if __name__ == "__main__":
    main()
