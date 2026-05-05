import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando recuperación definitiva (MODO BRUTO)...")

valid_count = 0
error_count = 0

# Vamos a leer línea por línea y usar un método manual para extraer el JSON
# No confiamos en la codificación de Python
with open(input_path, "rb") as f:
    for i, line_bytes in enumerate(f):
        # 1. Decodificar ignorando basura
        line_str = line_bytes.decode('utf-8', errors='ignore').strip()
        
        if not line_str:
            continue
            
        # 2. Si la línea no empieza con {, buscamos el primer {
        if not line_str.startswith('{'):
            start = line_str.find('{')
            if start != -1:
                line_str = line_str[start:]
            else:
                continue

        # 3. Intentar cargar JSON
        try:
            obj = json.loads(line_str)
            # 4. Guardar inmediatamente en modo append para no perder nada si crashea
            with open(output_path, "a", encoding="utf-8") as fout:
                json.dump(obj, fout, ensure_ascii=False)
                fout.write("\n")
            valid_count += 1
            if valid_count % 1000 == 0:
                print(f"✅ Recuperados: {valid_count}")
        except:
            error_count += 1

print(f"\n✅ PROCESO TERMINADO.")
print(f"📊 Recuperados: {valid_count}")
print(f"⚠️ Fallidos: {error_count}")
