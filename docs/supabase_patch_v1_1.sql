-- ============================================================
-- ATLAS -- Patch v1.1: columnas faltantes detectadas en runtime
-- Ejecutar en: supabase.com/dashboard/project/fkjwaubqwvcereilllow/sql
-- ============================================================

-- Tabla: audit_results -- columnas requeridas por el orchestrator y la API
ALTER TABLE audit_results
    ADD COLUMN IF NOT EXISTS result_json    JSONB;

ALTER TABLE audit_results
    ADD COLUMN IF NOT EXISTS human_decision TEXT;

-- Tabla: documents -- columna requerida por agent_vision._persist_results()
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS total_amount   NUMERIC(15, 2);

-- Verificar resultado
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'audit_results' AND column_name IN ('result_json', 'human_decision'))
    OR
    (table_name = 'documents'     AND column_name = 'total_amount')
  )
ORDER BY table_name, column_name;
