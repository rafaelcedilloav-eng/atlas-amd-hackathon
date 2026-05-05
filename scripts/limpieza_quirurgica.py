import json
import sys
import os

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO LIMPIEZA QUIRÚRGICA...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

# === TRUCO LETAL: CONTADOR DE LLAVES ===
buffer = ""
depth = 0
valid_objects = []

# Leemos en modo binario y decodificamos con utf-8-sig para ser más robustos con el BOM
try:
    with open(INPUT, "rb") as f:
        content = f.read().decode('utf-8-sig', errors='replace')
        
    for char in content:
        if char == '{':
            depth += 1
            buffer += char
        elif char == '}':
            depth -= 1
            buffer += char
            if depth == 0 and buffer:
                # OBJETO COMPLETO DETECTADO
                try:
                    obj = json.loads(buffer)
                    # Solo nos interesan los que tienen la estructura de ATLAS
                    if isinstance(obj, dict) and "messages" in obj:
                        valid_objects.append(json.dumps(obj, ensure_ascii=False))
                    buffer = ""
                except:
                    buffer = ""
        elif depth > 0:
            buffer += char

    # === ESCRIBIR RESULTADO PURO ===
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_objects))

    print(f"✅ ASESINATO COMPLETADO. {len(valid_objects)} objetos purificados en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico en la inyección: {e}", file=sys.stderr)
