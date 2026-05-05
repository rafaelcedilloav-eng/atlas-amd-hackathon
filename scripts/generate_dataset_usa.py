import json
import asyncio
import random

# Escenarios de USA (CFR Title 26 / IRM)
ESCENARIOS = [
    "Auditoría bajo IRC 482: Precios de transferencia en operaciones entre entidades controladas.",
    "Incumplimiento de reporte FBAR (FinCEN 114) para cuentas extranjeras.",
    "Auditoría de nóminas (Employment Tax - IRM 4.23): Clasificación errónea de contratistas.",
    "Detección de estructuración de efectivo (smurfing) bajo la Bank Secrecy Act (BSA).",
    "Técnicas indirectas de examen (Bank Deposits Method - IRM 4.10) para ingresos no reportados.",
    "Aplicación de multas por falta de diligencia bajo la Circular 230.",
    "Revisión de deducciones personales infladas en declaraciones de individuos (Subchapter A)."
]

def generar_ejemplo(tema, escenario):
    pregunta = f"Analiza el caso legal en USA: {escenario}. ¿Qué procedimientos del IRM y qué secciones del CFR 26 son aplicables?"
    respuesta = f"ANÁLISIS DE ATLAS: Para el caso de {escenario}, el procedimiento base se encuentra en el IRM Part 4 (Examining Process). Los puntos críticos son: 1. Aplicación de las técnicas de examen del IRM 4.10. 2. Validación de cumplimiento contra el CFR Title 26. Las red flags identificadas incluyen: inconsistencias en la conciliación bancaria, patrones de omisión en reportes internacionales y fallos en la estructura de precios de transferencia. Se recomienda emitir un IDR (Information Document Request) formal para profundizar en la verificación de los soportes documentales."
    
    return {
        "messages": [
            {"role": "system", "content": "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. Responde con precisión legal, citando artículos y fuentes oficiales. Usa razonamiento paso a paso cuando el caso lo requiera. Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."},
            {"role": "user", "content": pregunta},
            {"role": "assistant", "content": respuesta}
        ]
    }

async def generar_dataset_usa(cantidad=1000):
    ruta = "docs/dataset_raw/DATASET_GEN/USA_Auditoria_Block3.jsonl"
    print(f"🚀 Iniciando generación de {cantidad} ejemplos en {ruta}...")
    
    with open(ruta, "w", encoding="utf-8") as f:
        for i in range(cantidad):
            escenario = random.choice(ESCENARIOS)
            ejemplo = generar_ejemplo("USA", escenario)
            linea = json.dumps(ejemplo, ensure_ascii=False)
            f.write(linea + "\n")
            if (i + 1) % 100 == 0:
                print(f"✅ Generados {i+1} ejemplos...")
    print("✨ Dataset USA generado exitosamente.")

if __name__ == "__main__":
    asyncio.run(generar_dataset_usa())
