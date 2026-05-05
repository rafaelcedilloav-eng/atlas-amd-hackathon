import os
import sys

# Añadir raíz al path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.kimi_hunter import KimiHunter

def create_atlas_expert_skill():
    hunter = KimiHunter()
    
    prompt = """
    ATLAS es un ecosistema de auditoría financiera. Colabora conmigo para generar el contenido detallado de una nueva 'Skill' llamada 'atlas-specialist'.
    
    El objetivo es crear un documento de especificación técnica de nivel experto que cubra:
    1. ARQUITECTURA: Relación exacta entre 'frontend' (Next.js), 'backend' (FastAPI/Python) y 'core' (Motor de razonamiento Kimi/Qwen).
    2. FLUJOS DE DATOS: Cómo un documento PDF llega al sistema, se extrae mediante agents, se audita por el Core Engine y se refleja en el front (WorldMap/XRayPanel).
    3. CONEXIONES: Protocolos de comunicación, autenticación con GCP/Vertex AI y manejo de estados.
    4. OPERACIONES TÉCNICAS: Cómo depurar el parser JSONL, ajustar LoRA para Qwen 35B y monitorear el pipeline.
    
    Proporciona un manual técnico minucioso que un ingeniero sénior necesitaría para 'poner las piezas finales' como si lo hubiera hecho mil veces.
    """
    
    system_prompt = "Eres Kimi-K2, co-arquitecto de ATLAS. Tu conocimiento es total, técnico y orientado a la excelencia de implementación."
    
    try:
        response = hunter.extract_data(prompt, system_prompt=system_prompt)
        # Asegurar que el directorio de skills personalizadas exista
        os.makedirs(r"D:\Proyectos\Skills Personalizadas", exist_ok=True)
        with open(r"D:\Proyectos\Skills Personalizadas\atlas-specialist.md", "w", encoding="utf-8") as f:
            f.write("# Skill: atlas-specialist\n\n" + response)
        print("✅ Skill 'atlas-specialist' creada con éxito en D:\\Proyectos\\Skills Personalizadas")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_atlas_expert_skill()
