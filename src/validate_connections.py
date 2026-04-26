"""
Script de validación de todas las conexiones de ATLAS.
Ejecutar antes de correr el pipeline: python src/validate_connections.py
"""
import os
import sys
import logging

# Configurar logging básico para validación
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que el directorio raíz esté en el path para las importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def validate_all():
    results = {}
    print("\n" + "="*50)
    print("ATLAS — INICIANDO VALIDACIÓN DE CONEXIONES")
    print("="*50)

    # 1. vLLM / AMD
    logger.info("Validando conexión vLLM (AMD MI300X)...")
    try:
        from src.vllm_client import verify_connection
        results['vllm'] = verify_connection()
        if results['vllm']:
            print("  ✅ vLLM: OK — Servidor AMD MI300X accesible")
        else:
            print("  ❌ vLLM: FALLO — Servidor conectado pero modelo no encontrado")
    except Exception as e:
        logger.error(f"vLLM error: {e}")
        results['vllm'] = False
        print(f"  ❌ vLLM: FALLO — {e}")

    # 2. Supabase
    logger.info("Validando conexión Supabase...")
    try:
        from src.supabase_client import get_client
        db = get_client()
        # Intentar una operación simple
        test = db.table("blacklist_vendors").select("id").limit(1).execute()
        results['supabase'] = True
        print("  ✅ Supabase: OK — Conexión establecida")
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        results['supabase'] = False
        print(f"  ❌ Supabase: FALLO — {e}")

    # 3. Tablas de Supabase (Schema)
    logger.info("Validando schema de tablas...")
    required_tables = ['documents', 'audit_results', 'processed_doc_ids', 'blacklist_vendors', 'audit_trail']
    schema_ok = True
    try:
        from src.supabase_client import get_client
        db = get_client()
        for table in required_tables:
            try:
                db.table(table).select("id").limit(1).execute()
                print(f"    ✅ Tabla '{table}': OK")
            except Exception as te:
                print(f"    ❌ Tabla '{table}': ERROR — {te}")
                schema_ok = False
        results['schema'] = schema_ok
    except Exception as e:
        results['schema'] = False
        print(f"  ❌ Schema: FALLO — {e}")

    # 4. OCR / Extracción
    logger.info("Validando motores de extracción local...")
    try:
        import fitz
        print("    ✅ PyMuPDF: OK")
        import pymupdf4llm
        print("    ✅ pymupdf4llm: OK")
        import pytesseract
        # Tesseract requiere el binario en el sistema, esta es solo la lib de python
        print("    ✅ pytesseract (lib): OK")
        results['ocr'] = True
    except ImportError as ie:
        logger.warning(f"Motores OCR incompletos: {ie}")
        results['ocr'] = False
        print(f"  ⚠️ OCR: INCOMPLETO — {ie}")

    # Reporte final
    print("\n" + "="*50)
    print("ATLAS — REPORTE DE VALIDACIÓN")
    print("="*50)
    all_ok = True
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.upper()}: {'OK' if status else 'FALLO'}")
        if not status:
            all_ok = False

    print("="*50)
    if all_ok:
        print("🚀 ATLAS listo para procesar documentos")
    else:
        print("⚠️  Resuelve los fallos antes de ejecutar el pipeline")
    print("="*50 + "\n")
    
    return all_ok

if __name__ == "__main__":
    validate_all()
