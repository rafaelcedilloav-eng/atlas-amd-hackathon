import os
import sys

# Añadir el directorio raíz al path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.kimi_hunter import KimiHunter

def ask_kimi_for_training_fix():
    hunter = KimiHunter()
    
    prompt = """
    Hola Kimi, soy el sistema ATLAS. Tengo un problema crítico:
    Estamos entrenando un modelo Qwen y el dataset 'data/atlas_training_dataset.jsonl' tiene un formato incorrecto.
    Hay líneas vacías entre cada objeto JSON. Esto rompe el parser del entrenamiento.
    
    Además, necesito generar 60 ejemplos del Batch 1: CoT Compliance siguiendo el estándar Golden Dataset v3.1.
    El usuario está muy molesto por la inestabilidad de Gemini.
    
    Necesito que:
    1. Me des el comando exacto para limpiar el archivo .jsonl de líneas vacías de la forma más eficiente posible.
    2. Me des un consejo táctico para calmar la situación y asegurar que el entrenamiento sea exitoso en los MI300X.
    3. Generes los primeros 5 ejemplos del Batch 1 (MX/USA compliance) con razonamiento <think> para validar tu calidad.
    """
    
    system_prompt = "Eres el Agente Kimi-K2 de ATLAS, el cerebro estratégico de auditoría. Tu prioridad es la estabilidad del sistema y el cumplimiento normativo."
    
    print("Consultando a Kimi...")
    try:
        response = hunter.extract_data(prompt, system_prompt=system_prompt)
        print("\n--- RESPUESTA DE KIMI ---")
        print(response)
        print("--------------------------")
    except Exception as e:
        print(f"Error al contactar a Kimi: {e}")

if __name__ == "__main__":
    ask_kimi_for_training_fix()
