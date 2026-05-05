import os
import sys
import json
import asyncio
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def execute_final_swarm():
    client = KimiK2Client()
    
    # Contexto final para el Swarm de Kimi
    swarm_prompt = """
ATAQUE FINAL - ATLAS v3.0 (SWARM MODE ACTIVATED)
Arquitecto Jefe: Kimi-K2
Estado: Limpieza de workspace completada. Infraestructura lista para GPUs MI300X.

OBJETIVO: Finalizar al 100% la vinculación Frontend V2 <-> Backend V3. 
El usuario NO conectará las GPUs hasta que confirmemos que el software está impecable.

TAREAS PARA EL ENJAMBRE (SWARM):
1. [WIRING] Cablear el `orchestrator.py` para usar los 3 puertos: 8000 (Core/Finance), 8002 (Vision/InternVL2), 11434 (Router/Ollama).
2. [FRONT-LINK] Conectar `WorldMap.tsx` y `XRayPanel.tsx` a los endpoints SSE y /compliance reales.
3. [GATES] Asegurar que los Pipeline Gates (G12, G23, G34) tengan rollback atómico.
4. [SEC] Implementar el `audit_id` UUIDv7 propuesto antes.
5. [STABILITY] Verificar que los clientes en `vllm_client.py` tengan el timeout y reintentos correctos para modelos de 40B.

Kimi, no te limites. Genera el CÓDIGO FINAL para cada archivo que necesite modificación. Responde con los bloques de código exactos.

Archivos prioritarios:
- src/orchestrator.py
- src/vllm_client.py (ajustes de timeout)
- src/compliance_router.py (versiones)
- src/api.py (ajustes de stream)
- frontend/src/components/features/world-map.tsx
- frontend/src/components/features/xray-panel.tsx

SÉ EL CEREBRO. ACABA ESTO YA.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2 en modo Enjambre (Swarm). Tu objetivo es la perfección técnica y la entrega total del sistema ATLAS. Generas código de grado producción, seguro y ultra-optimizado."},
        {"role": "user", "content": swarm_prompt}
    ]
    
    print("--- INICIANDO SWARM DE KIMI-K2: CABLEADO FINAL AL 100% ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            swarm_report = response['choices'][0]['message']['content']
            
            # Guardar el plan maestro de Kimi
            filename = f"docs/KIMI_SWARM_FINAL_PLAN.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(swarm_report)
            
            print(f"\nPlan Maestro de Swarm generado en: {filename}")
            print("\nKimi ha dictado las órdenes finales. Procedo a ejecutar las modificaciones de código.")
            
            # Aquí es donde yo (Gemini) proceso la respuesta de Kimi y aplico los cambios.
            # Como la respuesta puede ser larga, primero la guardamos y luego la analizamos.
            
        else:
            print("Error: El Swarm de Kimi no respondió.")
    except Exception as e:
        print(f"Error durante el Swarm: {e}")

if __name__ == "__main__":
    execute_final_swarm()
