import json
import os
import sys

# === CONFIGURACIÓN DE ATAQUE ===
INPUT = "data/atlas_training_dataset_BACKUP.jsonl"
OUTPUT = "data/atlas_training_dataset.jsonl"

print("🎯 INYECTANDO RECONSTRUCCIÓN DE BLOQUES COMPLETOS...", file=sys.stderr)

if not os.path.exists(INPUT):
    print(f"❌ Error: No se encuentra el respaldo en {INPUT}", file=sys.stderr)
    sys.exit(1)

valid_count = 0
current_obj_str = ""
in_object = False
brace_depth = 0

try:
    # Eliminamos el archivo de salida previo para empezar limpio
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    with open(INPUT, "r", encoding="utf-8-sig", errors="replace") as f:
        # Abrimos el archivo de salida en modo append
        with open(OUTPUT, "a", encoding="utf-8") as fout:
            for line in f:
                line_content = line.strip()
                if not line_content:
                    continue
                
                # Detectar el inicio de un objeto de mensajes si no estamos en uno
                if not in_object and '"messages":' in line_content:
                    in_object = True
                    # Retroceder al inicio del objeto si la línea no empieza con {
                    # Pero en este archivo, parece que el { está en la línea anterior o misma
                    current_obj_str = "{" 
                    brace_depth = 1
                    # Si la línea ya tiene el {, lo ignoramos porque ya lo pusimos
                    if '{' in line_content:
                        # Contamos llaves en el resto de la línea
                        content_after_brace = line_content[line_content.find('{')+1:]
                        for char in content_after_brace:
                            if char == '{': brace_depth += 1
                            elif char == '}': brace_depth -= 1
                        current_obj_str += content_after_brace
                    else:
                        current_obj_str += line_content
                elif in_object:
                    # Acumular y balancear
                    for char in line_content:
                        if char == '{': brace_depth += 1
                        elif char == '}': brace_depth -= 1
                    
                    current_obj_str += line_content
                    
                    if brace_depth <= 0:
                        # Hemos cerrado el objeto raíz
                        try:
                            # Limpieza rápida antes de parsear
                            clean_json = current_obj_str.strip()
                            # Quitar posibles caracteres de cierre de array si se colaron
                            if clean_json.endswith(','): clean_json = clean_json[:-1]
                            
                            obj = json.loads(clean_json)
                            if "messages" in obj:
                                json.dump(obj, fout, ensure_ascii=False)
                                fout.write("\n")
                                valid_count += 1
                                if valid_count % 1000 == 0:
                                    print(f"✅ Recuperados: {valid_count}", file=sys.stderr)
                        except:
                            pass
                        
                        # Reset
                        in_object = False
                        current_obj_str = ""
                        brace_depth = 0

    print(f"✅ OPERACIÓN EXITOSA. {valid_count} objetos reconstruidos en: {OUTPUT}", file=sys.stderr)

except Exception as e:
    print(f"❌ Fallo crítico: {e}", file=sys.stderr)
