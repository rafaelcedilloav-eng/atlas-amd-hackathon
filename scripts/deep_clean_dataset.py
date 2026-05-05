import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando recuperación definitiva del dataset...")

if not os.path.exists(input_path):
    print(f"❌ Error: No se encuentra el respaldo en {input_path}")
    exit(1)

valid_count = 0
error_count = 0

# Abrimos con utf-8-sig para ignorar el BOM
# Usamos errors='replace' para no morir por caracteres extraños
with open(input_path, "r", encoding="utf-8-sig", errors="replace") as fin, \
     open(output_path, "w", encoding="utf-8") as fout:
    
    for i, line in enumerate(fin):
        # Limpieza básica de la línea
        cleaned = line.strip()
        
        # Si la línea está vacía, la ignoramos totalmente
        if not cleaned:
            continue
            
        # El problema es que a veces las líneas vacías se ven como JSON inválidos
        # Intentamos cargar el JSON. Si falla, es que la línea es basura o está mal formateada.
        try:
            obj = json.loads(cleaned)
            # Si logramos cargarlo, lo guardamos limpio en una sola línea
            json.dump(obj, fout, ensure_ascii=False)
            fout.write("\n")
            valid_count += 1
        except Exception:
            # Aquí está el truco: si falla, podría ser por caracteres de control invisibles
            # Intentamos una limpieza más agresiva solo si falla el primer intento
            try:
                # Eliminar caracteres de control y nulos
                ultra_cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32).strip()
                if ultra_cleaned:
                    obj = json.loads(ultra_cleaned)
                    json.dump(obj, fout, ensure_ascii=False)
                    fout.write("\n")
                    valid_count += 1
                else:
                    error_count += 1
            except:
                error_count += 1
                if error_count <= 10:
                    pass # Silencioso para no saturar

print(f"\n✅ RECUPERACIÓN COMPLETADA.")
print(f"📊 Registros válidos (JSONL puro): {valid_count}")
print(f"⚠️ Líneas ignoradas/basura: {error_count}")
print(f"💾 Archivo listo para Jupyter: {output_path}")
print(f"💡 Ya puedes darle 'Run' al entrenamiento.")
