import json
import os
import sys

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO RECONSTRUCCIÓN HÍBRIDA POR LÍNEAS...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

valid_count = 0
buffer = []
depth = 0

try:
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    with open(INPUT, "r", encoding="utf-8-sig", errors="replace") as f:
        with open(OUTPUT, "a", encoding="utf-8") as fout:
            for line in f:
                clean_line = line.strip()
                if not clean_line:
                    continue
                
                # Caso rápido: Línea única que ya es JSONL
                if depth == 0 and clean_line.startswith('{') and clean_line.endswith('}'):
                    try:
                        obj = json.loads(clean_line)
                        if "messages" in obj:
                            json.dump(obj, fout, ensure_ascii=False)
                            fout.write("\n")
                            valid_count += 1
                            if valid_count % 5000 == 0:
                                print(f"✅ Procesados: {valid_count}", file=sys.stderr)
                            continue
                    except:
                        pass

                # Caso acumulativo: Multilínea
                for char in clean_line:
                    if char == '{': depth += 1
                    elif char == '}': depth -= 1
                
                buffer.append(clean_line)
                
                if depth == 0 and buffer:
                    candidate = " ".join(buffer).strip()
                    # Limpieza rápida de basura externa
                    while candidate and not candidate.startswith('{'): candidate = candidate[1:]
                    while candidate and not candidate.endswith('}'): candidate = candidate[:-1]
                    
                    if candidate.startswith('{') and candidate.endswith('}'):
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict) and "messages" in obj:
                                json.dump(obj, fout, ensure_ascii=False)
                                fout.write("\n")
                                valid_count += 1
                                if valid_count % 5000 == 0:
                                    print(f"✅ Procesados: {valid_count}", file=sys.stderr)
                        except:
                            pass
                    buffer = []

    print(f"✅ OPERACIÓN EXITOSA. {valid_count} objetos reconstruidos en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico: {e}", file=sys.stderr)
