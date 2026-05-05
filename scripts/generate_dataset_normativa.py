import json
import asyncio
import random

# Escenarios de Normativa Financiera y Cumplimiento (MX-USA)
ESCENARIOS = [
    "LFPIORPI (Anti-Lavado): Detección de actividades vulnerables en operaciones inmobiliarias.",
    "Ley del Mercado de Valores (LMV): Auditoría de abuso de información privilegiada (insider trading).",
    "Sarbanes-Oxley Act (SOX): Fallos en controles internos de integridad financiera.",
    "Bank Secrecy Act (BSA): Auditoría de programas AML y monitoreo de riesgos en banca.",
    "Código de Comercio: Auditoría de libros sociales y actas de asamblea fraudulentas.",
    "Securities Act 1933: Incumplimiento en el registro de ofertas de valores privados.",
    "NOM-151: Validación de integridad en documentos digitales de transacciones financieras."
]

def generar_ejemplo(tema, escenario):
    pregunta = f"Audita el siguiente caso de cumplimiento: {escenario}. ¿Qué red flags detectas y bajo qué normativa se debe sustentar la auditoría?"
    respuesta = f"ANÁLISIS DE ATLAS: Para este escenario sobre {escenario}, el marco normativo clave es la {tema}. Los puntos críticos incluyen: 1. Verificación de controles internos y trazabilidad de los flujos financieros. 2. Identificación de beneficiarios finales (UBO). Las red flags observadas son: omisión de reportes de cumplimiento, falta de soporte documental con valor probatorio (NOM-151), y patrones de actividad sospechosa que se desvían de los estándares establecidos en la normativa (BSA/LFPIORPI). Se recomienda ejecutar una revisión de integridad corporativa conforme a los estándares de auditoría forense aplicables."
    
    return {
        "messages": [
            {"role": "system", "content": "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. Responde con precisión legal, citando artículos y fuentes oficiales. Usa razonamiento paso a paso cuando el caso lo requiera. Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."},
            {"role": "user", "content": pregunta},
            {"role": "assistant", "content": respuesta}
        ]
    }

async def generar_dataset_normativa(cantidad=1000):
    ruta = "docs/dataset_raw/DATASET_GEN/Normativa_Auditoria_Block4.jsonl"
    print(f"🚀 Iniciando generación de {cantidad} ejemplos en {ruta}...")
    
    with open(ruta, "w", encoding="utf-8") as f:
        for i in range(cantidad):
            escenario = random.choice(ESCENARIOS)
            ejemplo = generar_ejemplo("Normativa Corporativa/Financiera", escenario)
            linea = json.dumps(ejemplo, ensure_ascii=False)
            f.write(linea + "\n")
            if (i + 1) % 100 == 0:
                print(f"✅ Generados {i+1} ejemplos...")
    print("✨ Dataset Normativa generado exitosamente.")

if __name__ == "__main__":
    asyncio.run(generar_dataset_normativa())
