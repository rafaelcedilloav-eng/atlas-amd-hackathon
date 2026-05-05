import json
import asyncio
import random

# Escenarios de LISR (Personas Morales y Físicas)
ESCENARIOS = [
    "Deducciones no indispensables (Art. 27 LISR) en Personas Morales.",
    "Ajuste anual por inflación artificial en estados financieros.",
    "Incumplimiento de requisitos de CFDI en gastos corporativos.",
    "Residencia fiscal y discrepancias en plataformas tecnológicas (RESICO).",
    "Uso indebido de pérdidas fiscales de ejercicios anteriores.",
    "Transferencia de intangibles a empresas relacionadas en jurisdicciones de baja imposición.",
    "Simulación de servicios para deducir pagos por asesoría no comprobable."
]

def generar_ejemplo(tema, escenario):
    pregunta = f"Audita el siguiente caso: {escenario}. ¿Cuáles son los puntos clave bajo la LISR y qué red flags debe considerar ATLAS?"
    respuesta = f"ANÁLISIS DE ATLAS: Para el caso de {escenario}, el fundamento legal recae en el Título II o IV de la LISR. Los puntos de control son: 1. Estricta indispensabilidad del gasto (Art. 27). 2. Sustancia comercial frente a la forma legal. Las red flags detectadas son: inconsistencias en los flujos de efectivo, falta de documentación de soporte (entregables) y correlación de gastos con ingresos. Se debe verificar el CFDI de origen y la realidad operativa de los proveedores involucrados."
    
    return {
        "messages": [
            {"role": "system", "content": "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. Responde con precisión legal, citando artículos y fuentes oficiales. Usa razonamiento paso a paso cuando el caso lo requiera. Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."},
            {"role": "user", "content": pregunta},
            {"role": "assistant", "content": respuesta}
        ]
    }

async def generar_dataset_lisr(cantidad=1000):
    ruta = "docs/dataset_raw/DATASET_GEN/LISR_Auditoria_Block2.jsonl"
    print(f"🚀 Iniciando generación de {cantidad} ejemplos en {ruta}...")
    
    with open(ruta, "w", encoding="utf-8") as f:
        for i in range(cantidad):
            escenario = random.choice(ESCENARIOS)
            ejemplo = generar_ejemplo("LISR", escenario)
            linea = json.dumps(ejemplo, ensure_ascii=False)
            f.write(linea + "\n")
            if (i + 1) % 100 == 0:
                print(f"✅ Generados {i+1} ejemplos...")
    print("✨ Dataset LISR generado exitosamente.")

if __name__ == "__main__":
    asyncio.run(generar_dataset_lisr())
