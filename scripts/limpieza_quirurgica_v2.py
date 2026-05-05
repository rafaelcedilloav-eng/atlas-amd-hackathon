import json
import os
import sys

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO LIMPIEZA QUIRÚRGICA VELOZ...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

valid_objects = []
current_obj_lines = []
depth = 0

try:
    with open(INPUT, "r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            # Limpieza rápida de la línea
            clean_line = line.strip()
            if not clean_line:
                continue
                
            # Escanear caracteres de la línea para balancear las llaves
            for char in clean_line:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
            
            current_obj_lines.append(clean_line)
            
            # Si depth es 0, hemos cerrado un objeto completo (o estamos fuera de uno)
            if depth == 0 and current_obj_lines:
                # Unimos las líneas acumuladas
                candidate = "".join(current_obj_lines).strip()
                
                # Limpieza quirúrgica de "decoraciones" de JSON array ([, ], ,)
                # Eliminamos caracteres de inicio/fin que no sean parte del objeto JSON {}
                while candidate and not candidate.startswith('{'):
                    candidate = candidate[1:].strip()
                while candidate and not candidate.endswith('}'):
                    candidate = candidate[:-1].strip()
                
                if candidate.startswith('{') and candidate.endswith('}'):
                    try:
                        obj = json.loads(candidate)
                        # Verificamos que sea un objeto de entrenamiento ATLAS (tiene 'messages')
                        if isinstance(obj, dict) and "messages" in obj:
                            valid_objects.append(json.dumps(obj, ensure_ascii=False))
                    except:
                        pass # Si no es un JSON válido, lo ignoramos silenciosamente
                
                # Resetear para el siguiente objeto
                current_obj_lines = []

    # === ESCRIBIR RESULTADO PURO ===
    # Usamos escritura incremental si fuera necesario, pero 44MB caben en memoria.
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_objects))

    print(f"✅ OPERACIÓN EXITOSA. {len(valid_objects)} objetos purificados en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico en la inyección: {e}", file=sys.stderr)
