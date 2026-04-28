"""
Capa de persistencia para ATLAS.
Centraliza todas las operaciones de lectura/escritura a Supabase.
"""
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import logging
from src.supabase_client import get_client

logger = logging.getLogger(__name__)

class AtlasPersistence:

    def __init__(self):
        # El cliente se obtiene bajo demanda para evitar errores de importación circular
        pass

    @property
    def db(self):
        return get_client()

    # ─────────────────────────────────────────────
    # DOCUMENTOS
    # ─────────────────────────────────────────────

    def save_document(self, document_data: dict) -> str:
        """Guarda metadatos del documento. Retorna el UUID generado."""
        try:
            result = self.db.table("documents").insert(document_data).execute()
            doc_uuid = result.data[0]['id']
            logger.info(f"Documento guardado: {doc_uuid} | doc_id: {document_data.get('doc_id')}")
            return doc_uuid
        except Exception as e:
            # Si ya existe (duplicado), retornar el ID existente
            if "duplicate" in str(e).lower() or "23505" in str(e) or "unique" in str(e).lower():
                try:
                    existing = self.db.table("documents").select("id").eq("doc_id", document_data.get("doc_id")).execute()
                    if existing.data:
                        return existing.data[0]['id']
                except Exception:
                    pass
            logger.error(f"Error guardando documento: {e}")
            return None

    # ─────────────────────────────────────────────
    # CONTROL DE DUPLICADOS (Agente 3)
    # ─────────────────────────────────────────────

    def is_duplicate(self, doc_id: str, document_hash: str) -> bool:
        """
        Verifica si el documento ya fue procesado.
        Usa doc_id Y hash para máxima precisión.
        """
        try:
            # Verificar por ID
            by_id = self.db.table("processed_doc_ids")\
                .select("id")\
                .eq("doc_id", doc_id)\
                .execute()
            if by_id.data:
                logger.warning(f"Duplicado detectado por doc_id: {doc_id}")
                return True

            # Verificar por hash de contenido
            by_hash = self.db.table("processed_doc_ids")\
                .select("id")\
                .eq("document_hash", document_hash)\
                .execute()
            if by_hash.data:
                logger.warning(f"Duplicado detectado por hash: {document_hash[:16]}...")
                return True

            return False
        except Exception as e:
            logger.error(f"Error verificando duplicado: {e}")
            return False  # fail-safe: no bloquear si hay error de DB

    def register_processed_doc(self, doc_data: dict) -> None:
        """Registra documento como procesado para futuras verificaciones."""
        try:
            self.db.table("processed_doc_ids").insert(doc_data).execute()
            logger.info(f"Documento registrado como procesado: {doc_data.get('doc_id')}")
        except Exception as e:
            if "duplicate" in str(e).lower() or "23505" in str(e) or "unique" in str(e).lower():
                return  # Ya estaba registrado — OK
            logger.error(f"Error registrando documento procesado: {e}")

    # ─────────────────────────────────────────────
    # BLACKLIST (Agente 3)
    # ─────────────────────────────────────────────

    def is_blacklisted(self, vendor_name: str, vendor_rfc: Optional[str] = None) -> dict:
        """
        Verifica si el proveedor está en la lista negra.
        Retorna {'blacklisted': bool, 'reason': str, 'severity': str}
        """
        try:
            # Búsqueda por nombre (case-insensitive)
            if vendor_name:
                by_name = self.db.table("blacklist_vendors")\
                    .select("*")\
                    .eq("is_active", True)\
                    .ilike("vendor_name", f"%{vendor_name}%")\
                    .execute()
                if by_name.data:
                    entry = by_name.data[0]
                    return {
                        'blacklisted': True,
                        'reason': entry['reason'],
                        'severity': entry['severity']
                    }

            # Búsqueda por RFC si está disponible
            if vendor_rfc:
                by_rfc = self.db.table("blacklist_vendors")\
                    .select("*")\
                    .eq("is_active", True)\
                    .eq("vendor_rfc", vendor_rfc)\
                    .execute()
                if by_rfc.data:
                    entry = by_rfc.data[0]
                    return {
                        'blacklisted': True,
                        'reason': entry['reason'],
                        'severity': entry['severity']
                    }

            return {'blacklisted': False, 'reason': None, 'severity': None}
        except Exception as e:
            logger.error(f"Error consultando blacklist: {e}")
            return {'blacklisted': False, 'reason': None, 'severity': None}

    # ─────────────────────────────────────────────
    # RESULTADOS DE AUDITORÍA
    # ─────────────────────────────────────────────

    def save_audit_result(self, result_data: dict) -> str:
        """Guarda el resultado completo del pipeline en audit_results."""
        try:
            result = self.db.table("audit_results").insert(result_data).execute()
            result_uuid = result.data[0]['id']
            logger.info(f"Resultado de auditoría guardado: {result_uuid} | doc_id: {result_data.get('doc_id')}")
            return result_uuid
        except Exception as e:
            logger.error(f"Error guardando resultado de auditoría: {e}")
            return None

    # ─────────────────────────────────────────────
    # AUDIT TRAIL (trazabilidad por agente)
    # ─────────────────────────────────────────────

    def log_agent_action(
        self,
        doc_id: str,
        agent: str,
        action: str,
        input_data: dict,
        output_data: dict,
        duration_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Registra la acción de cada agente en el audit trail."""
        try:
            self.db.table("audit_trail").insert({
                "doc_id":        doc_id,
                "agent":         agent,
                "action":        action,
                "input_data":    input_data,
                "output_data":   output_data,
                "duration_ms":   duration_ms,
                "success":       success,
                "error_message": error_message
            }).execute()
        except Exception as e:
            logger.error(f"Error en audit trail: {e}")
            # No re-raise — el audit trail no debe romper el pipeline


# Singleton instance
persistence = AtlasPersistence()

# Funciones de compatibilidad para llamadas directas
def save_document(data: dict): return persistence.save_document(data)
def save_audit_result(data: dict): return persistence.save_audit_result(data)
def is_duplicate(doc_id: str, hash: str): return persistence.is_duplicate(doc_id, hash)
def is_blacklisted(name: str, rfc: str = None): return persistence.is_blacklisted(name, rfc)
def register_processed_doc(data: dict): return persistence.register_processed_doc(data)
def log_agent_action(**kwargs): return persistence.log_agent_action(**kwargs)
