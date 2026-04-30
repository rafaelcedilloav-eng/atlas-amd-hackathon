"""
Mock for Supabase persistence to allow testing pipeline logic locally.
"""
import copy

# Campos sensibles que deben ser sanitizados
SENSITIVE_FIELDS = {
    'vendor_rfc', 'vendor_name', 'vendor_address', 'vendor_email',
    'client_rfc', 'client_name', 'client_address', 'client_email'
}

def sanitize_data(data):
    """Sanitiza los campos sensibles del diccionario de datos."""
    if not isinstance(data, dict):
        return data
    
    sanitized = copy.deepcopy(data)
    
    # Sanitizar campos sensibles en el nivel superior
    for field in SENSITIVE_FIELDS:
        if field in sanitized:
            sanitized[field] = "[REDACTED]"
    
    # Sanitizar campos anidados en result_json
    if 'result_json' in sanitized and isinstance(sanitized['result_json'], dict):
        result_json = sanitized['result_json']
        for field in SENSITIVE_FIELDS:
            if field in result_json:
                result_json[field] = "[REDACTED]"
            # Sanitizar campos dentro de extracted_fields
            if 'vision' in result_json and isinstance(result_json['vision'], dict):
                extracted = result_json['vision'].get('extracted_fields', {})
                if isinstance(extracted, dict) and field in extracted:
                    extracted[field] = "[REDACTED]"
    
    return sanitized

def save_audit_result(data):
    sanitized_data = sanitize_data(data)
    print(f"MOCK: Saving audit result for doc_id: {sanitized_data.get('doc_id')}")
    return "mock_success"

def log_agent_action(doc_id, agent, action, input_data, output_data, duration_ms, success=True, error_message=None):
    print(f"MOCK: Logging action for agent {agent}: {action}")

def is_duplicate(doc_id, doc_hash):
    return False

def is_blacklisted(vendor_name, vendor_rfc):
    return {"blacklisted": False}

def register_processed_doc(data):
    return True
