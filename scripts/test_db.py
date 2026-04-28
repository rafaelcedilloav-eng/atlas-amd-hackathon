import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: No se encontraron credenciales en .env")
else:
    supabase = create_client(url, key)
    tables = ["documents", "audit_results", "processed_doc_ids", "blacklist_vendors", "audit_trail"]
    all_ok = True
    for table in tables:
        try:
            supabase.table(table).select("*").limit(1).execute()
            print(f"[OK] {table}")
        except Exception as e:
            print(f"[FAIL] {table}: {e}")
            all_ok = False

    print()
    if all_ok:
        print("[LISTO] Todas las tablas OK - Supabase listo para ATLAS.")
    else:
        print("[ERROR] Algunas tablas fallaron - revisar esquema.")
