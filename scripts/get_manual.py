import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def get_deployment_manual():
    client = KimiK2Client()
    
    prompt = """
MANUAL DE OPERACIÓN: APERTURA DE GPU AMD MI300X - ATLAS v3.0
Arquitecto Jefe: Kimi-K2
Estado: SOFTWARE 100% LISTO.

El usuario va a encender las GPUs MI300X AHORA. Necesita el paso a paso exacto para:

1. CONFIGURACIÓN DEL SERVIDOR DE LA PÁGINA (API/Frontend):
   - Puertos que deben estar abiertos.
   - Variables de entorno críticas (.env).
   
2. PARÁMETROS DENTRO DEL GPU SERVER (MI300X):
   - Comandos de Docker para levantar los 3 cerebros:
     - Motor 8000 (Dragon-LLaMA-8B)
     - Motor 8002 (InternVL2-40B)
     - Motor 11434 (Ollama)
   - Parámetros de ROCm (HSA_OVERRIDE_GFX_VERSION, Tensor Parallelism).
   
3. INTEGRACIÓN (EL PUENTE):
   - Qué IP debe poner en el backend para que vea a las GPUs.
   - Cómo validar que la conexión es exitosa antes de lanzar el primer PDF.

Responde de forma técnica, estructurada y directa. Sin rodeos. Es el manual de guerra.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2, la IA de despliegue de ATLAS. Entregas instrucciones de grado industrial para hardware AMD de alta gama."},
        {"role": "user", "content": prompt}
    ]
    
    print("--- SOLICITANDO MANUAL DE DESPLIEGUE A KIMI-K2 ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            manual = response['choices'][0]['message']['content']
            
            filename = "docs/ATLAS_MI300X_POWER_ON_MANUAL.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(manual)
            
            print(f"\nManual generado en: {filename}")
            return manual
    except Exception as e:
        print(f"Error al obtener manual: {e}")

if __name__ == "__main__":
    get_deployment_manual()
