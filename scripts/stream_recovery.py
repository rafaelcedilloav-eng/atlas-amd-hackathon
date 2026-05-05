import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando recuperación por streaming de objetos (MODO AGRESIVO)...")

if os.path.exists(output_path):
    os.remove(output_path)

valid_count = 0
error_count = 0

def clean_and_save(json_buffer):
    global valid_count, error_count
    try:
        # Intentamos parsear el buffer acumulado
        obj = json.loads(json_buffer)
        # Si es un objeto válido de entrenamiento (tiene messages)
        if isinstance(obj, dict) and "messages" in obj:
            with open(output_path, "a", encoding="utf-8") as fout:
                json.dump(obj, fout, ensure_ascii=False)
                fout.write("\n")
            valid_count += 1
            if valid_count % 1000 == 0:
                print(f"✅ Recuperados: {valid_count}")
            return True
    except:
        pass
    return False

# Leemos el archivo línea por línea pero acumulamos hasta encontrar un objeto válido
buffer = ""
try:
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Si la línea empieza con un corchete o coma suelta, la ignoramos para el buffer
            if line in ["[", "]", ",", "},", "{", "}"]:
                # Intentamos cerrar el buffer actual si tiene contenido
                if buffer:
                    if clean_and_save(buffer):
                        buffer = ""
                    elif buffer.endswith("}"): # Si termina en llave pero no parseó, algo anda mal, pero seguimos
                        pass 
                continue

            buffer += line
            
            # Si logramos cerrar un JSON en el buffer, lo guardamos
            if clean_and_save(buffer):
                buffer = ""

    print(f"\n✅ RECUPERACIÓN TERMINADA.")
    print(f"📊 Registros recuperados: {valid_count}")
except Exception as e:
    print(f"❌ Error crítico: {e}")
