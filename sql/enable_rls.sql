-- ATLAS — Habilitar Row Level Security en todas las tablas
-- Ejecutar en: supabase.com/dashboard → SQL Editor

-- 1. Habilitar RLS
ALTER TABLE documents          ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_doc_ids  ENABLE ROW LEVEL SECURITY;
ALTER TABLE blacklist_vendors  ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_trail        ENABLE ROW LEVEL SECURITY;

-- 2. Políticas: solo el service_role tiene acceso (el backend usa service_role)
--    El anon key (frontend directo) queda bloqueado por defecto.

CREATE POLICY "service_role_all_documents"
  ON documents FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all_audit_results"
  ON audit_results FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all_processed_doc_ids"
  ON processed_doc_ids FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all_blacklist_vendors"
  ON blacklist_vendors FOR ALL
  USING (auth.role() = 'service_role');

CREATE POLICY "service_role_all_audit_trail"
  ON audit_trail FOR ALL
  USING (auth.role() = 'service_role');
