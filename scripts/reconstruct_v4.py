import json
import os
import sys

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO RECONSTRUCCIÓN POR DELIMITADOR 'messages'...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

valid_count = 0

try:
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    with open(INPUT, "r", encoding="utf-8-sig", errors="replace") as f:
        # Cargamos el archivo por fragmentos si es necesario, pero 44MB es pequeño
        content = f.read()

    # Dividimos por la cadena '{"messages":' que parece ser el inicio de cada objeto
    # IMPORTANTE: El archivo tiene {"messages" en una línea y luego saltos de línea
    # Vamos a usar una división que sea flexible
    
    # Normalizamos el contenido quitando comas y corchetes de array que estén entre objetos
    import re
    # Buscamos todos los bloques que empiezan con { y contienen "messages"
    # El truco es buscar el inicio de cada objeto y luego balancear llaves
    
    start_indices = [m.start() for m in re.finditer(r'\{\s*"messages"', content)]
    
    with open(OUTPUT, "a", encoding="utf-8") as fout:
        for i in range(len(start_indices)):
            start = start_indices[i]
            # El fin es el inicio del siguiente o el final del archivo
            end = start_indices[i+1] if i+1 < len(start_indices) else len(content)
            
            chunk = content[start:end].strip()
            
            # Limpiamos el chunk desde el final para encontrar el último '}'
            last_brace = chunk.rfind('}')
            if last_brace != -1:
                chunk = chunk[:last_brace+1]
            
            try:
                # Intentamos parsear el chunk como JSON
                obj = json.loads(chunk)
                if "messages" in obj:
                    json.dump(obj, fout, ensure_ascii=False)
                    fout.write("\n")
                    valid_count += 1
                    if valid_count % 1000 == 0:
                        print(f"✅ Reconstruidos: {valid_count}", file=sys.stderr)
            except:
                # Si falla, intentamos una limpieza más agresiva (quitar saltos de línea internos)
                try:
                    # Re-intentar quitando saltos de línea literales
                    flat_chunk = " ".join(chunk.split())
                    obj = json.loads(flat_chunk)
                    if "messages" in obj:
                        json.dump(obj, fout, ensure_ascii=False)
                        fout.write("\n")
                        valid_count += 1
                except:
                    continue

    print(f"✅ OPERACIÓN EXITOSA. {valid_count} objetos reconstruidos en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico: {e}", file=sys.stderr)
