import json
import os
import sys
import time
import requests
import google.auth
from google.auth.transport.requests import Request

# === CONFIGURACIÓN DE RUTAS ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.deepseek_client import DeepSeekClient

OUTPUT_PATH = "data/atlas_training_dataset.jsonl"

# === SUPER PROMPT BLINDADO ===
SUPER_PROMPT_TEMPLATE = """
### ROL: SENIOR FORENSIC AUDITOR & AML/BSA COMPLIANCE EXPERT (ATLAS CORE)
Genera {batch_size} ejemplos de entrenamiento de ALTA FIDELIDAD para ATLAS (Golden Dataset v3.1).

### 📜 REGLAS DE ORO (CONTENIDO)
1. JURISDICCIÓN: Alterna entre México (Ley Fintech, LFPIORPI, LIC, CNBV) y Estados Unidos (BSA, Patriot Act, 31 CFR, OCC, FinCEN).
2. REALISMO: Usa nombres de entidades, montos ($5k-$50M), fechas (2024-2026) y perfiles de riesgo complejos.
3. LEGALIDAD: Cita artículos ESPECÍFICOS y REALES vigentes a Mayo 2026.
4. RAZONAMIENTO: Usa <think> con: Paso 1 (Red Flags), Paso 2 (Marco Legal), Paso 3 (Intencionalidad), Paso 4 (Dictamen).

### 🛠️ REGLAS DE FORMATO (ESTRICTO JSONL)
- UNA LÍNEA, UN OBJETO.
- SIN bloques de código (```json), SIN comas entre objetos, SIN corchetes [ ] envolviendo el resultado.
- SIN líneas vacías. SIN caracteres de control invisibles.
- PRESERVA UTF-8 (¿, á, ñ).

### 🚀 ESCENARIO ESPECÍFICO:
{topic}
"""

def sanitize_output(content):
    """Limpia el output de DeepSeek de cualquier 'cochinada' de formato."""
    lines = content.strip().split('\n')
    valid_jsonl = []
    for line in lines:
        line = line.strip()
        # Eliminar posibles decoraciones de Markdown
        if line.startswith('```') or line == '[' or line == ']' or line == ',':
            continue
        # Limpiar comas al final si DeepSeek intentó hacer un array
        if line.endswith(','):
            line = line[:-1].strip()
        
        if line.startswith('{') and line.endswith('}'):
            try:
                # Validar que sea JSON real
                json.loads(line)
                valid_jsonl.append(line)
            except:
                continue
    return valid_jsonl

def run_generation_phase(name, target, topics, batch_size=10):
    client = DeepSeekClient()
    generated = 0
    print(f"\n--- INICIANDO FASE: {name} ({target} ejemplos) ---")
    
    while generated < target:
        topic = topics[generated % len(topics)]
        prompt = SUPER_PROMPT_TEMPLATE.format(batch_size=batch_size, topic=topic)
        
        print(f"📡 [{name}] Solicitando {batch_size} ejemplos sobre: {topic[:50]}...")
        response = client.generate_batch(prompt)
        
        if "❌" in response:
            print(f"⚠️ Error en API: {response}")
            time.sleep(15)
            continue
            
        clean_lines = sanitize_output(response)
        if clean_lines:
            with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
                for line in clean_lines:
                    f.write(line + "\n")
            
            generated += len(clean_lines)
            print(f"✅ Progresión {name}: {generated}/{target}")
        else:
            print("⚠️ Bloque inválido recibido. Reintentando con más rigor...")
        
        time.sleep(1) # Rate limiting preventivo

def main():
    # BATCH A: Core Compliance & Banking (10k)
    topics_a = [
        "Reportes SAR y CTR bajo 31 CFR 1010.311",
        "Debida diligencia mejorada (EDD) para PEPs en México",
        "Cumplimiento de Capitalización SOFIPOS bajo LIC",
        "Reglas de corresponsalía bancaria transfronteriza"
    ]
    
    # BATCH B: Advanced Financial Crimes (10k)
    topics_b = [
        "Trade-Based Money Laundering (TBML) en la frontera MX-USA",
        "Fraude con Deepfakes en KYC de Neobancos",
        "Mezcladores de Criptoactivos y evasión de sanciones OFAC",
        "Estructuración masiva en redes de remesas"
    ]
    
    # BATCH C: Relevancia Inmediata Mayo 2026 (4k)
    topics_c = [
        "Nueva Regla Residencial de FinCEN (Reporte de BOI en Real Estate)",
        "Auditoría de Modelos de IA bajo Guía Interagencial de Abril 2026",
        "Riesgos de Stablecoins en la Ley Fintech MX (Actualización 2026)",
        "Controles de debida diligencia para el sector de Semiconductores"
    ]

    # Ejecución secuencial completa
    run_generation_phase("BATCH_A", 10000, topics_a)
    run_generation_phase("BATCH_B", 10000, topics_b)
    run_generation_phase("BATCH_C", 4000, topics_c)
    
    # PRUEBA DE CALIDAD (Comentada para producción)
    # run_generation_phase("PRUEBA_CALIDAD", 10, topics_a, batch_size=10)

if __name__ == "__main__":
    main()
