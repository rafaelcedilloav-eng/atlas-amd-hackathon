# ATLAS: ARCHITECTURE & DESIGN DECISIONS
## Agentic Task-Level Reasoning System — AMD MI300X Optimized
**Versión:** 1.1 (Post-Hackathon Edition)

---

## Arquitectura de Alto Nivel

```
Next.js 16 Frontend (AMD Visual DNA)
    ↓ [Auth: X-API-Key]
FastAPI Backend (Python 3.12)
    ├── Orchestrator (src/orchestrator.py)
    │   ├── Agent 1: Vision Extractor (OCR & Layout)
    │   ├── Agent 2: Reasoning Engine (DeepSeek-R1 @ AMD MI300X)
    │   ├── Agent 3: Mathematical Validator (Inconsistency Detection)
    │   └── Agent 4: Forensic Explainer (es-MX Report)
    └── Integrations
        ├── Supabase (Persistence & Audit Logs)
        ├── vLLM (High-Performance Inference on MI300X)
        └── Local API (Secured endpoints)
```

## El Pipeline de Inferencia (The 52s Loop)

1. **Ingesta:** El frontend sube el PDF y recibe un `document_id` (SHA256).
2. **Visión:** Agente 1 extrae campos clave (Monto, RFC, Concepto, etc.)
3. **Razonamiento Profundo:** Agente 2 (DeepSeek-R1) ejecuta un Chain-of-Thought forense buscando trampas, errores o malas prácticas financieras.
4. **Validación:** Agente 3 cruza los datos extraídos con el razonamiento lógico para detectar inconsistencias matemáticas.
5. **Explicación:** Agente 4 destila el análisis técnico en un reporte legible con severidad asignada.

## Stack Tecnológico del Frontend

- **Framework:** Next.js 16 (App Router) + React 19.
- **Styling:** Tailwind CSS 4 con configuración inline en `globals.css`.
- **Diseño:** AMD Frontend Architecture (Dark Mode, Rojo #ED1C24, JetBrains Mono).
- **Inferencia Visual:** Framer Motion 12 para representar los estados de procesamiento de la GPU.

---

## Decisiones de Diseño Críticas

- **Auth:** Implementación de `X-API-Key` para proteger el acceso a la potencia de cómputo de la MI300X.
- **Polling:** El frontend implementa polling reactivo para manejar inferencias de larga duración (~52s) sin bloquear la experiencia del usuario.
- **DNA AMD:** El sistema visual comunica potencia y precisión, alineado con el hardware subyacente.

---
*Generado el 27 de Abril 2026 — ATLAS Forensic Unit*
