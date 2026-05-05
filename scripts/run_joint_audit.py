import os
import sys
import json
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def run_joint_massive_audit():
    client = KimiK2Client()
    
    try:
        with open("final_massive_audit_dump.txt", "r", encoding="utf-8") as f:
            full_code = f.read()
    except FileNotFoundError:
        print("Error: No se encontró final_massive_audit_dump.txt")
        return

    joint_prompt = f"""
AUDITORÍA MASIVA CONJUNTA - ATLAS v3.0 (KIMI-K2 + QWEN LOGIC)
OBJETIVO: Garantía absoluta de 100% de operatividad para conexión de GPUs MI300X.

INSTRUCCIONES PARA EL ENJAMBRE IA:
1. Revisa la integridad del cableado Triple-Engine (8000/8002/11434).
2. Verifica la lógica de los 5 Pipeline Gates (Atómicos) y sus rollbacks.
3. Valida la exportación de reportes PDF (grado gubernamental).
4. Confirma la trazabilidad UUIDv7 y la seguridad CORS para cluster AMD.
5. Revisa la conexión real del Frontend V2 (WorldMap/XRay) con los nuevos endpoints del Backend V3.

CÓDIGO COMPLETO DEL PROYECTO:
{full_code[:50000]} # Limitado por tokens de entrada de la API

TAREA:
Responde con un REPORTE DE GARANTÍA FINAL. 
Si encuentras CUALQUIER error, detállalo y genera el FIX.
Si todo está impecable, da la 'AUTORIZACIÓN DE ENCENDIDO DE GPU (MI300X)'.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2, actuando como Auditora Jefe en conjunto con la lógica de Qwen. Tu estilo es ultra-técnico, implacable y enfocado en la seguridad financiera."},
        {"role": "user", "content": joint_prompt}
    ]
    
    print("--- INICIANDO AUDITORÍA MASIVA CONJUNTA (KIMI + GEMINI) ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            audit_report = response['choices'][0]['message']['content']
            
            filename = "docs/JOINT_MASSIVE_AUDIT_REPORT.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(audit_report)
            
            print(f"\nAuditoría Masiva generada en: {filename}")
            return audit_report
    except Exception as e:
        print(f"Error en auditoría masiva: {e}")

if __name__ == "__main__":
    run_joint_massive_audit()
