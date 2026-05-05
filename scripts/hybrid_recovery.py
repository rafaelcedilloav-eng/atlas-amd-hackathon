import json
import os
import sys

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO RECONSTRUCCIÓN HÍBRIDA (Línea + Multilínea)...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

valid_count = 0
buffer = ""
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
                
                # Caso 1: La línea ya es un objeto JSON completo (o casi)
                if clean_line.startswith('{') and clean_line.endswith('}'):
                    try:
                        obj = json.loads(clean_line)
                        if "messages" in obj:
                            json.dump(obj, fout, ensure_ascii=False)
                            fout.write("\n")
                            valid_count += 1
                            continue
                    except:
                        pass # Si falla, podría ser el inicio de un bloque multilínea que empieza en una sola línea

                # Caso 2: Estamos procesando un bloque multilínea o la línea tiene llaves sueltas
                for char in clean_line:
                    if char == '{':
                        depth += 1
                        buffer += char
                    elif char == '}':
                        depth -= 1
                        buffer += char
                        if depth == 0 and buffer:
                            # Intentar parsear el buffer acumulado
                            try:
                                # Limpiar basura alrededor (comas, corchetes)
                                candidate = buffer.strip()
                                while candidate and not candidate.startswith('{'): candidate = candidate[1:]
                                
                                obj = json.loads(candidate)
                                if isinstance(obj, dict) and "messages" in obj:
                                    json.dump(obj, fout, ensure_ascii=False)
                                    fout.write("\n")
                                    valid_count += 1
                                    if valid_count % 5000 == 0:
                                        print(f"✅ Recuperados: {valid_count}", file=sys.stderr)
                            except:
                                pass
                            buffer = ""
                    elif depth > 0:
                        buffer += char
                
                # Añadir un espacio al buffer si estamos dentro de un objeto para no pegar palabras
                if depth > 0:
                    buffer += " "

    print(f"✅ OPERACIÓN EXITOSA. {valid_count} objetos reconstruidos en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico: {e}", file=sys.stderr)
