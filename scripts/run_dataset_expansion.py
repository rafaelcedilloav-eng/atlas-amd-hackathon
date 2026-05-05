import json
from src.qwen_hunter import QwenHunter
from tqdm import tqdm
import os

def run_expansion():
    hunter = QwenHunter()
    # Asegurar que el directorio de datos existe
    if not os.path.exists("data"):
        os.makedirs("data")
    output_file = "data/atlas_training_dataset.jsonl"
    
    seeds = [
        "Beneficial owners: FinCEN CDD Rule (31 CFR 1010.230) requires 25% threshold for ownership.",
        "BSA/AML Patriot Act Section 326: Customer Identification Program (CIP) requirements.",
        "OCC BSA/AML Examination Procedures: Risk-based approach for community banks.",
        "Ley Fintech MX: Obligaciones de crowdfunding y debida diligencia de proyectos.",
        "LFPIORPI Artículo 17: Operaciones inusuales y reporte de umbrales."
    ]
    
    print(f"🚀 Iniciando expansión de {len(seeds)} semillas...")
    
    # Barra de progreso con tqdm
    with tqdm(total=len(seeds) * 200, desc="Expansión de Dataset") as pbar:
        with open(output_file, "a", encoding="utf-8") as f:
            for seed in seeds:
                for i in range(200):
                    prompt = f"""Eres ATLAS Expander. Semilla técnica: {seed}.
                    Genera un bloque de 10 pares JSONL (5 en español, 5 en inglés):
                    - 3 pares directos (Pregunta/Respuesta).
                    - 1 par usuario confundido.
                    - 1 par usuario complejo.
                    
                    Formato: {{"messages": [{{"role": "user", "content": "..."}}, {{"role": "assistant", "content": "..."}}]}}
                    Reglas: Referencias legales exactas, técnico, conciso.
                    """
                    
                    response = hunter.generate(prompt)
                    
                    if isinstance(response, dict) and "candidates" in response:
                        text = response["candidates"][0]["content"]["parts"][0]["text"]
                        f.write(text.strip() + "\n")
                    else:
                        print(f"\n⚠️ Error en semilla {seed} (bloque {i}): {response}")
                    
                    pbar.update(1)

if __name__ == "__main__":
    run_expansion()
    print("\n✅ Expansión masiva completada.")
