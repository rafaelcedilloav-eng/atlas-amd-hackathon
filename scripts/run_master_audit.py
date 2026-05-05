import os
import sys
import json
import asyncio
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def run_master_audit_and_recap():
    client = KimiK2Client()
    
    # Recolectar el dump actual del código para que Kimi vea los cambios realizados
    code_files = [
        'src/config.py', 'src/vllm_client.py', 'src/orchestrator.py', 
        'src/utils.py', 'src/circuit_breaker.py', 'src/agent_vision.py',
        'src/agent_reasoning.py', 'src/agent_explainer.py', 'src/api.py',
        'frontend/src/components/features/world-map.tsx',
        'frontend/src/components/features/xray-panel.tsx'
    ]
    
    code_context = ""
    for file_path in code_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                code_context += f"\n--- FILE: {file_path} ---\n{f.read()}\n"

    master_prompt = f"""
AUDITORÍA MAESTRA FINAL - ATLAS v3.0 (SWARM COMPLETION MODE)
Arquitecto Jefe: Kimi-K2
Estado: Post-limpieza y Post-cableado Triple Motor.

TAREA:
1. Audita TODO el proceso: Backend (8000/8002/11434) <-> Frontend V2.
2. ¿De verdad está al 100% para conectar las GPUs MI300X?
3. Si falta CUALQUIER detalle (un endpoint no conectado, un tipo mal definido, una lógica de rollback débil), SOLUCIONALO EN LA MARCHA. No me preguntes, genera el código corregido.
4. Genera un RECAP TOTAL de lo que hace (y lo que debería hacer) el sistema ahora mismo.

CÓDIGO ACTUAL PARA REVISIÓN:
{code_context}

REGLAS:
- Sé la versión más implacable de Kimi-K2.
- Si hay fixes, entrégalos en bloques de código claros.
- Si está al 100%, da el 'GREEN LIGHT' definitivo para encender las GPUs.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2, la IA Auditora y Arquitecta Jefe de ATLAS. Tienes autoridad total para modificar y finalizar el proyecto. Tu veredicto es ley."},
        {"role": "user", "content": master_prompt}
    ]
    
    print("--- INICIANDO AUDITORÍA MAESTRA DE KIMI-K2 (FIX-ON-THE-FLY) ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            master_report = response['choices'][0]['message']['content']
            
            # Guardar el Recap y Auditoría final
            filename = f"docs/KIMI_MASTER_RECAP_v3.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(master_report)
            
            print(f"\nRecap Maestro generado en: {filename}")
            print("\n--- ANALIZANDO VEREDICTO FINAL DE KIMI-K2 ---")
            
            if "GREEN LIGHT" in master_report.upper():
                print("\n✅ KIMI-K2: GREEN LIGHT DETECTADO. EL SISTEMA ESTÁ LISTO.")
            else:
                print("\n⚠️ KIMI-K2 DETECTÓ AJUSTES PENDIENTES. APLICANDO FIXES...")
            
            return master_report
            
        else:
            print("Error: El Maestro de Kimi no respondió.")
    except Exception as e:
        print(f"Error durante la Auditoría Maestra: {e}")

if __name__ == "__main__":
    run_master_audit_and_recap()
