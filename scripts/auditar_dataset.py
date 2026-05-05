import json
import os
import hashlib

def limpiar_dataset(directorio):
    vistos = set()
    total_procesados = 0
    total_unicos = 0
    archivos = [f for f in os.listdir(directorio) if f.endswith('.jsonl')]
    
    archivo_salida = os.path.join(directorio, "Dataset_Unificado_Limpio.jsonl")
    
    with open(archivo_salida, "w", encoding="utf-8") as salida:
        for archivo in archivos:
            ruta = os.path.join(directorio, archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    total_procesados += 1
                    try:
                        data = json.loads(linea)
                        # Crear un hash único basado en el contenido del prompt (user) y respuesta (assistant)
                        contenido = json.dumps(data['messages'][1:], sort_keys=True)
                        h = hashlib.sha256(contenido.encode('utf-8')).hexdigest()
                        
                        if h not in vistos:
                            vistos.add(h)
                            salida.write(linea)
                            total_unicos += 1
                    except Exception as e:
                        continue
    
    print(f"Auditoría Finalizada:")
    print(f"Total procesados: {total_procesados}")
    print(f"Casos únicos conservados: {total_unicos}")
    print(f"Duplicados eliminados: {total_procesados - total_unicos}")

if __name__ == "__main__":
    limpiar_dataset("docs/dataset_raw/DATASET_GEN")
