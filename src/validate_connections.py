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
    print("ATLAS - INICIANDO VALIDACION DE CONEXIONES")
    print("="*50)

    OK  = "[OK]"
    ERR = "[FALLO]"
    WARN = "[AVISO]"

    # 1. vLLM / AMD
    logger.info("Validando conexion vLLM (AMD MI300X)...")
    try:
        from src.vllm_client import verify_connection
        results['vllm'] = verify_connection()
        if results['vllm']:
            print(f"  {OK} vLLM: Servidor AMD MI300X accesible")
        else:
            print(f"  {ERR} vLLM: Servidor conectado pero modelo no encontrado")
    except Exception as e:
        logger.error(f"vLLM error: {e}")
        results['vllm'] = False
        print(f"  {ERR} vLLM: {e}")

    # 2. Supabase
    logger.info("Validando conexion Supabase...")
    try:
        from src.supabase_client import get_client
        db = get_client()
        db.table("blacklist_vendors").select("id").limit(1).execute()
        results['supabase'] = True
        print(f"  {OK} Supabase: Conexion establecida")
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        results['supabase'] = False
        print(f"  {ERR} Supabase: {e}")

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
                print(f"    {OK} Tabla '{table}'")
            except Exception as te:
                print(f"    {ERR} Tabla '{table}': {te}")
                schema_ok = False
        results['schema'] = schema_ok
    except Exception as e:
        results['schema'] = False
        print(f"  {ERR} Schema: {e}")

    # 4. OCR / Extraccion
    logger.info("Validando motores de extraccion local...")
    try:
        import fitz
        print(f"    {OK} PyMuPDF")
        import pymupdf4llm
        print(f"    {OK} pymupdf4llm")
        import pytesseract
        print(f"    {OK} pytesseract (lib)")
        results['ocr'] = True
    except ImportError as ie:
        logger.warning(f"Motores OCR incompletos: {ie}")
        results['ocr'] = False
        print(f"  {WARN} OCR: {ie}")

    # Reporte final
    print("\n" + "="*50)
    print("ATLAS - REPORTE DE VALIDACION")
    print("="*50)
    all_ok = True
    for component, status in results.items():
        icon = OK if status else ERR
        print(f"{icon} {component.upper()}: {'OK' if status else 'FALLO'}")
        if not status:
            all_ok = False

    print("="*50)
    if all_ok:
        print(">> ATLAS listo para procesar documentos")
    else:
        print(">> Resuelve los fallos antes de ejecutar el pipeline")
    print("="*50 + "\n")
    
    return all_ok

if __name__ == "__main__":
    validate_all()
