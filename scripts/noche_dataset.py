import json
import time
import requests
import os

# CONFIGURACIÓN
MODEL = "qwen2.5:1.5b"
URL = "http://localhost:11434/api/chat"
TOTAL_TARGET = 5000
OUTPUT_FILE = "docs/dataset_raw/DATASET_GEN/dataset_completo_v1.jsonl"
LOG_FILE = "logs/generador_nocturno.log"
BATCH_SIZE = 250 

def generar_ejemplo(ctx):
    prompt = f"Basado en este fragmento legal: '{ctx}'. Genera UN solo caso de auditoría financiera (MX o USA) estrictamente en formato JSON: {{\"system\": \"Auditor Financiero\", \"user\": \"Analiza este caso\", \"assistant\": {{\"descripcion\": \"...\", \"red_flags\": [\"...\"], \"fundamento_legal\": \"...\"}}}}. Responde solo el JSON."
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    try:
        response = requests.post(URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['message']['content']
    except Exception:
        pass
    return None

def run_nocturno():
    os.makedirs("logs", exist_ok=True)
    count = 0
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
            count = sum(1 for _ in f)
            
    print(f"🚀 Iniciando generación desde {count} ejemplos...")
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        while count < TOTAL_TARGET:
            for path in ["docs/dataset_raw/MX/Leyes/CFF_Maestro_2026.txt", "docs/dataset_raw/MX/Leyes/LISR_Maestro_2026.txt", "docs/dataset_raw/USA/Fiscal/Legal_Framework/CFR_Maestro_2026.txt", "docs/dataset_raw/USA/Fiscal/IRS_Manuals_Audit/IRM_Maestro_2026.txt"]:
                if not os.path.exists(path): continue
                with open(path, "r", encoding="utf-8") as f_ctx:
                    context_data = f_ctx.read()
                    
                for i in range(0, len(context_data), BATCH_SIZE):
                    if count >= TOTAL_TARGET: break
                    try:
                        res = generar_ejemplo(context_data[i:i+BATCH_SIZE])
                        if res:
                            limpio = res.replace('\n', ' ').replace('```json', '').replace('```', '').strip()
                            json.loads(limpio)
                            f.write(limpio + "\n")
                            count += 1
                            if count % 5 == 0: print(f"✅ {count}/{TOTAL_TARGET}")
                            f.flush()
                            time.sleep(1)
                    except:
                        pass
    print("¡Finalizado!")

if __name__ == "__main__":
    run_nocturno()
