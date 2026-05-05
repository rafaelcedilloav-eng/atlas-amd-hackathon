import os
import sys

# Añadir raíz al path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.kimi_hunter import KimiHunter

def get_perfect_code():
    hunter = KimiHunter()
    
    prompt = """
    Como experta codificadora de ATLAS, genera el script final de Python para entrenamiento (fine-tuning) de Qwen 2.5 en un entorno de 8x MI300X (ROCm).
    
    REQUISITOS CRÍTICOS:
    1. Error a corregir: 'ValueError: lora.ParamWrapper does not work with lora_dropout != 0.'. Asegúrate de que lora_dropout=0.
    2. Entorno: MI300X. Usa torch_dtype=torch.bfloat16 y bf16=True.
    3. Dataset: Carga desde 'data/atlas_training_dataset.jsonl'.
    4. Formato: Devuelve UNICAMENTE el código Python. Sin números de línea, sin explicaciones, sin bloques de código Markdown (```). Solo el texto que se pegaría en una celda de Jupyter.
    5. Indentación: Perfecta, sin espacios extras al inicio de la primera línea.
    6. Incluye: BitsAndBytesConfig para 4-bit, LoraConfig (r=16, alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]), Trainer y TrainingArguments.
    """
    
    system_prompt = "Eres la Coder Skill de Kimi-K2. Tu salida es código Python puro, ejecutable y perfecto."
    
    try:
        response = hunter.extract_data(prompt, system_prompt=system_prompt)
        # Limpiar cualquier residuo de Markdown que Kimi pudiera poner a pesar de la instrucción
        clean_code = response.strip()
        if clean_code.startswith("```python"):
            clean_code = clean_code[9:]
        if clean_code.startswith("```"):
            clean_code = clean_code[3:]
        if clean_code.endswith("```"):
            clean_code = clean_code[:-3]
        
        print(clean_code.strip())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_perfect_code()
