import json
import os

input_path = "data/atlas_training_dataset_BACKUP.jsonl"
output_path = "data/atlas_training_dataset.jsonl"

print(f"🚀 Iniciando recuperación por balance de llaves...")

valid_count = 0
error_count = 0

try:
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Buscamos el inicio de cada objeto {"messages"
    start_pos = 0
    while True:
        start_pos = content.find('{"messages"', start_pos)
        if start_pos == -1:
            break
            
        # Intentamos encontrar el final del objeto balanceando llaves { }
        brace_count = 0
        end_pos = -1
        for i in range(start_pos, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos != -1:
            json_str = content[start_pos:end_pos]
            try:
                obj = json.loads(json_str)
                with open(output_path, "a", encoding="utf-8") as fout:
                    json.dump(obj, fout, ensure_ascii=False)
                    fout.write("\n")
                valid_count += 1
                if valid_count % 1000 == 0:
                    print(f"✅ Recuperados: {valid_count}")
            except:
                error_count += 1
            start_pos = end_pos
        else:
            # Si no encontramos el cierre, saltamos este inicio
            start_pos += 1

    print(f"\n✅ RECUPERACIÓN TERMINADA.")
    print(f"📊 Registros recuperados: {valid_count}")
    print(f"⚠️ Errores: {error_count}")

except Exception as e:
    print(f"❌ Error crítico: {e}")
