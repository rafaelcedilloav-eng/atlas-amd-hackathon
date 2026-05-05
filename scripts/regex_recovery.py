import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando recuperación por bloques de fuerza bruta...")

valid_count = 0
error_count = 0

# Leemos todo el archivo como una cadena
try:
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Buscamos todos los objetos JSON que comiencen con {"messages"
    # El patrón busca desde {"messages" hasta el cierre } que le corresponde
    # Nota: esto asume que no hay objetos anidados complejos que usen "messages" fuera de la raíz
    
    import re
    # Buscamos el patrón de un objeto JSON que contiene "messages"
    # Usamos una expresión regular no codiciosa para capturar cada objeto individual
    matches = re.finditer(r'\{"messages":\s*\[.*?\}\s*\}\s*\}', content, re.DOTALL)
    
    with open(output_path, "w", encoding="utf-8") as fout:
        for match in matches:
            json_str = match.group(0)
            try:
                # Validar JSON
                obj = json.loads(json_str)
                # Escribir en formato compacto
                json.dump(obj, fout, ensure_ascii=False)
                fout.write("\n")
                valid_count += 1
                if valid_count % 5000 == 0:
                    print(f"✅ Procesados: {valid_count}")
            except:
                error_count += 1

    print(f"\n✅ RECUPERACIÓN TERMINADA.")
    print(f"📊 Registros recuperados: {valid_count}")
    print(f"⚠️ Errores de parseo: {error_count}")

except Exception as e:
    print(f"❌ Error crítico: {e}")
