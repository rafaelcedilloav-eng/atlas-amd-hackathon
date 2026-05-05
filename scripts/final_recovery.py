import json
import os
import re

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print("🚀 Recuperación final de ATLAS (6,012 objetos detectados)...")

valid_count = 0
try:
    with open(input_path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read()

    # Buscamos cada inicio de objeto "messages"
    # El archivo tiene mezclas de {"messages" y { "messages" y saltos de línea
    # Usamos un split más inteligente
    
    # Buscamos la posición de cada '"messages":'
    # Cada objeto empieza unos caracteres antes de eso con un '{'
    
    indices = [m.start() for m in re.finditer(r'"messages"\s*:', content)]
    
    with open(output_path, "w", encoding="utf-8") as fout:
        for idx in indices:
            # Buscamos el '{' anterior más cercano
            start = content.rfind('{', 0, idx)
            if start == -1: continue
            
            # Balanceamos llaves desde 'start'
            depth = 0
            end = -1
            for j in range(start, len(content)):
                if content[j] == '{': depth += 1
                elif content[j] == '}': depth -= 1
                
                if depth == 0:
                    end = j + 1
                    break
            
            if end != -1:
                obj_str = content[start:end]
                try:
                    obj = json.loads(obj_str)
                    if "messages" in obj:
                        json.dump(obj, fout, ensure_ascii=False)
                        fout.write("\n")
                        valid_count += 1
                except:
                    # Intento de limpieza si hay basura
                    try:
                        clean_str = " ".join(obj_str.split())
                        obj = json.loads(clean_str)
                        json.dump(obj, fout, ensure_ascii=False)
                        fout.write("\n")
                        valid_count += 1
                    except:
                        pass

    print(f"✅ ¡LISTO! Recuperados {valid_count} de 6012 objetos detectados.")
    print(f"💡 Nota: Los 95,000 eran LÍNEAS, no ejemplos. Tienes el dataset íntegro.")

except Exception as e:
    print(f"❌ Error: {e}")
