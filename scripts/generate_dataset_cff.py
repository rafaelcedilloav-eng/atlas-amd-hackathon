import json
import asyncio
import random

# Definición de escenarios para el CFF Título III (Facultades de Auditoría)
ESCENARIOS = [
    "Detección de empresas factureras (Art. 69-B CFF).",
    "Incumplimiento en notificaciones electrónicas (Buzón Tributario).",
    "Discrepancias en CFDI 4.0 contra depósitos bancarios.",
    "Revisiones electrónicas y requerimientos de contabilidad.",
    "Defensa legal ante el PAE (Procedimiento Administrativo de Ejecución)."
]

def generar_ejemplo(tema, escenario):
    pregunta = f"Audita el siguiente caso: {escenario}. ¿Cuáles son las red flags y qué artículos del CFF se deben aplicar?"
    respuesta = f"ANÁLISIS DE ATLAS: Para el escenario de {escenario}, primero identificamos que el Art. 42 del CFF faculta a la autoridad. Los puntos clave son: 1. Sustancia económica. 2. Trazabilidad de CFDI. La normativa aplicable es el Título III del CFF. Las red flags detectadas son: falta de capacidad operativa y discrepancia en flujos. Se recomienda verificar el listado definitivo del Art. 69-B."
    
    return {
        "messages": [
            {"role": "system", "content": "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. Responde con precisión legal, citando artículos y fuentes oficiales. Usa razonamiento paso a paso cuando el caso lo requiera. Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."},
            {"role": "user", "content": pregunta},
            {"role": "assistant", "content": respuesta}
        ]
    }

async def generar_dataset_cff(cantidad=500):
    ruta = "docs/dataset_raw/DATASET_GEN/CFF_Auditoria_Block1.jsonl"
    print(f"🚀 Iniciando generación de {cantidad} ejemplos en {ruta}...")
    
    with open(ruta, "w", encoding="utf-8") as f:
        for i in range(cantidad):
            escenario = random.choice(ESCENARIOS)
            ejemplo = generar_ejemplo("CFF Titulo III", escenario)
            # Asegurar formato JSONL estricto sin saltos
            linea = json.dumps(ejemplo, ensure_ascii=False)
            f.write(linea + "\n")
            if (i + 1) % 100 == 0:
                print(f"✅ Generados {i+1} ejemplos...")
    print("✨ Dataset generado exitosamente.")

if __name__ == "__main__":
    asyncio.run(generar_dataset_cff())
