import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.kimi_hunter import KimiHunter

def ask_kimi_for_injection_trick():
    hunter = KimiHunter()
    prompt = """
    Hola Kimi, el dataset 'data/atlas_training_dataset_BACKUP.jsonl' (4.4MB) es un caos. 
    A veces parece JSONL (un objeto por línea con saltos de línea vacíos), pero más adelante se vuelve un JSON multilínea indentado con comas entre objetos.
    
    El usuario quiere una 'inyección' quirúrgica:
    1. Volar corchetes [ ] y comas que separan objetos.
    2. Eliminar espacios y saltos de línea basura.
    3. Asegurar que los caracteres UTF-8 (como ¿ y á) se preserven.
    4. Que el resultado sea un JSONL puro (una línea, un objeto).
    
    ¿Cuál es el 'truco' o comando de inyección más letal para limpiar esta inconsistencia sin romper los datos? 
    Proporciona un script de Python o comando sed/awk que haga esta 'limpieza de choque'.
    """
    system_prompt = "Eres Kimi-K2, el estratega de ATLAS. Proporcionas soluciones de ingeniería de datos brutales y efectivas."
    print("Consultando el truco a Kimi...")
    response = hunter.extract_data(prompt, system_prompt=system_prompt)
    print("\n--- EL TRUCO DE KIMI ---")
    print(response)

if __name__ == "__main__":
    ask_kimi_for_injection_trick()
