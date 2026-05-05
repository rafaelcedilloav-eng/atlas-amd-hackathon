import os
import sys
import json

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from src.kimi_client import KimiK2Client

def add_pdf_export_feature():
    client = KimiK2Client()
    
    pdf_prompt = """
TAREA FINAL: Implementar Exportación a PDF de Auditorías.
El usuario quiere poder descargar los reportes en PDF para compartirlos.

INSTRUCCIONES:
1. Diseña un endpoint `/api/v2/report/download/{audit_id}` en `src/api.py`.
2. Implementa una clase `ReportGenerator` en un nuevo archivo `src/report_generator.py` que:
   - Reciba el JSON del resultado de la auditoría.
   - Use una librería ligera (ej. `fpdf2`) para generar un PDF profesional con:
     - Logo de ATLAS (placeholder).
     - Resumen Ejecutivo.
     - Gráfica de Riesgo (placeholder o texto).
     - Tabla de hallazgos de compliance.
     - Cadena de razonamiento forense.
     - Pie de página con el audit_id (UUIDv7).
3. Asegura que el PDF sea estéticamente impecable (grado gubernamental).

Responde con el código para:
- src/report_generator.py
- Las modificaciones necesarias en src/api.py para servir el PDF.
- El comando para instalar la dependencia necesaria.
    """

    messages = [
        {"role": "system", "content": "Eres Kimi-K2, Arquitecta de ATLAS. Estás poniendo el toque final de lujo al proyecto."},
        {"role": "user", "content": pdf_prompt}
    ]
    
    print("--- SOLICITANDO IMPLEMENTACIÓN DE PDF EXPORT A KIMI-K2 ---")
    try:
        response = client.chat_completion(messages)
        if response and 'choices' in response:
            pdf_code = response['choices'][0]['message']['content']
            
            filename = "docs/KIMI_PDF_FEATURE_PLAN.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pdf_code)
            
            print(f"\nPlan de Exportación a PDF generado en: {filename}")
            return pdf_code
    except Exception as e:
        print(f"Error al solicitar PDF feature: {e}")

if __name__ == "__main__":
    add_pdf_export_feature()
