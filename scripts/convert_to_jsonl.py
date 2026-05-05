import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando conversión de JSON Estructurado a JSONL...")

if not os.path.exists(input_path):
    print(f"❌ Error: No se encuentra el respaldo en {input_path}")
    exit(1)

try:
    # 1. Intentar cargar el archivo completo como un solo objeto JSON
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    
    print(f"📦 Archivo cargado. Tipo de datos: {type(data)}")
    
    # 2. Si es una lista, procesamos cada elemento
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # A veces el dataset está dentro de una llave como 'examples' o 'data'
        potential_keys = ['examples', 'data', 'messages', 'rows']
        items = None
        for key in potential_keys:
            if key in data and isinstance(data[key], list):
                items = data[key]
                print(f"🔍 Encontrada lista de datos en la llave: '{key}'")
                break
        if items is None:
            items = [data] # Tratar como un solo objeto
    else:
        items = [data]

    # 3. Escribir como JSONL
    with open(output_path, "w", encoding="utf-8") as fout:
        count = 0
        for item in items:
            json.dump(item, fout, ensure_ascii=False)
            fout.write("\n")
            count += 1
            
    print(f"✅ ¡ÉXITO TOTAL!")
    print(f"📊 Registros convertidos a JSONL: {count}")
    print(f"💾 Archivo listo: {output_path}")

except Exception as e:
    print(f"❌ Error durante la conversión: {e}")
    print("💡 Intentando modo de recuperación por fragmentos...")
    # Si el archivo es demasiado grande o está mal formado al final, intentamos leerlo como texto
    try:
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
            # Si empieza con [ y termina con ], quitamos los corchetes
            if content.startswith('[') and content.endswith(']'):
                content = content[1:-1]
            
            # Dividir por "}," que es el separador común en arrays de JSON
            # Nota: Esto es arriesgado pero útil como último recurso
            parts = content.split('},')
            with open(output_path, "w", encoding="utf-8") as fout:
                count = 0
                for part in parts:
                    part = part.strip()
                    if not part.endswith('}'):
                        part += '}'
                    try:
                        obj = json.loads(part)
                        json.dump(obj, fout, ensure_ascii=False)
                        fout.write("\n")
                        count += 1
                    except:
                        continue
            print(f"✅ Recuperación por fragmentos completada: {count} registros.")
    except Exception as e2:
        print(f"❌ Fallo crítico: {e2}")
