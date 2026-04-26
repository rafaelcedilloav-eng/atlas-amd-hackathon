# ATLAS: ARCHITECTURE & DESIGN DECISIONS
## Agentic Task-Level Reasoning System
**Versión:** 1.0

---

## Arquitectura de Alto Nivel

```
Streamlit Frontend (Upload PDF)
    ↓
FastAPI Backend (Python 3.12)
    ├── CrewAI Orchestrator
    │   ├── Agent 1: Vision Analyzer (Llama 3.2 Vision)
    │   ├── Agent 2: Reasoning Engine (DeepSeek-R1 MI300X)
    │   ├── Agent 3: Validator (Qwen3-Coder)
    │   └── Agent 4: Explainer (Llama 3.2 turbo)
    └── Integrations
        ├── Supabase (PostgreSQL + pgvector)
        ├── vLLM (DigitalOcean MI300X)
        └── Ollama (Local)
```

## Flujo de Procesamiento

1. **Agent 1 (Vision):** Extrae datos de documentos
2. **Agent 2 (Reasoning):** Razona sobre la decisión
3. **Agent 3 (Validator):** Valida contra políticas
4. **Agent 4 (Explainer):** Genera explicación

## Output Esperado

```json
{
  "decision": "APROBADA",
  "confidence": 0.92,
  "reasoning": "Chain-of-thought completo",
  "explanation": "Explicación legible para humanos"
}
```

---

Para arquitectura detallada, ver GitHub repo
