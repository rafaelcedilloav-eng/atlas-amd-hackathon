# ATLAS — Registro Histórico de Construcción
**AMD Hackathon 2026 · Build in Public Edition**
_Última actualización: 27 de abril de 2026_

---

## Índice
1. [Qué es ATLAS](#1-qué-es-atlas)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Los 4 agentes](#3-los-4-agentes)
4. [Stack tecnológico](#4-stack-tecnológico)
5. [API endpoints](#5-api-endpoints)
6. [Esquema de datos (Pydantic)](#6-esquema-de-datos-pydantic)
7. [Infraestructura de deploy](#7-infraestructura-de-deploy)
8. [Seguridad implementada](#8-seguridad-implementada)
9. [Desafíos técnicos y soluciones](#9-desafíos-técnicos-y-soluciones)
10. [Historial de commits](#10-historial-de-commits)
11. [Variables de entorno](#11-variables-de-entorno)
12. [Cómo correr el proyecto](#12-cómo-correr-el-proyecto)

---

## 1. Qué es ATLAS

**ATLAS** (Automated Threat & Liability Analysis System) es un pipeline de inteligencia artificial para detección forense de anomalías en documentos financieros.

Dado un PDF (factura, contrato, estado de cuenta), ATLAS:
- Extrae texto y campos estructurados con OCR
- Detecta errores matemáticos, inconsistencias y valores sospechosos
- Valida integridad: deduplicación + blacklist de proveedores
- Genera un reporte ejecutivo con severidad, acción recomendada y explicación en lenguaje natural

**Hackathon:** lablab.ai × AMD · Categoría "Extra Challenge: Ship It + Build in Public"
**Repositorio:** https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon
**Demo en vivo:** https://atlas-amd-qs5g4.ondigitalocean.app

---

## 2. Arquitectura del sistema

```
Usuario
  │
  ▼
Frontend Next.js 15 (App Router)
  │  POST /api/upload → DO strips /api → POST /upload
  ▼
FastAPI Backend (src/api.py)
  │
  ├─ /upload ──────────────────────────┐
  ├─ /analyze (path en servidor)       │
  ├─ /result/{doc_id}                  │
  ├─ /audit-list                       │
  ├─ /stats (público)                  │  run_pipeline()
  └─ /human_decision                   │
                                       ▼
                              src/orchestrator.py
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                   ▼
              Agent 1            Agent 2            Agent 3
              Vision             Reasoning          Validator
                    │                  │                   │
                    └──────────────────┴──────────────────┘
                                       │
                                  Agent 4
                                  Explainer
                                       │
                                       ▼
                              Supabase PostgreSQL
                              (tabla audit_results)
```

### Flujo de datos

```
PDF → VisionOutput → ReasoningOutput → ValidatorOutput → ExplainerOutput → PipelineResult → Supabase
```

Cada agente recibe el output del anterior como input. El Orchestrator (`src/orchestrator.py`) maneja:
- Short-circuit si Vision falla (confidence < 0.1 y sin campos)
- Fallback de emergencia en cada agente (nunca rompe la cadena)
- Persistencia final en `audit_results`

---

## 3. Los 4 agentes

### Agent 1 — Vision Analyzer (`src/agent_vision.py`)
- **Input:** ruta del PDF
- **Proceso:** OCR con Tesseract/Poppler → extrae campos clave (proveedor, monto, fecha, IVA)
- **Output:** `VisionOutput` con `extracted_fields`, `detected_issues`, `confidence`
- **Fallback:** si OCR falla, devuelve campos vacíos con confidence=0

### Agent 2 — Reasoning Agent (`src/agent_reasoning.py`)
- **Input:** `VisionOutput`
- **Proceso:** Prompt a DeepSeek-R1-Distill-Qwen-32B via vLLM
  - Detecta: Math Error, Missing Field, Inconsistency, Unclear Value, No Trap
  - Genera `reasoning_chain` de mínimo 3 pasos (pensamiento paso a paso del LLM)
- **Output:** `ReasoningOutput` con `trap_detected`, `trap_severity`, `reasoning_chain`
- **Fallback:** Si vLLM no responde → crea razonamiento de emergencia con `used_fallback=True`

### Agent 3 — Validator / Integrity Gate (`src/agent_validator.py`)
- **Input:** `VisionOutput` + `ReasoningOutput`
- **Proceso:**
  - Verifica matemáticamente los cálculos del documento
  - Consulta `processed_doc_ids` en Supabase para detectar duplicados
  - Consulta `blacklist_vendors` para proveedores bloqueados
  - LLM confirma o rechaza el hallazgo del Agente 2
- **Output:** `ValidatorOutput` con `validation_result`, `is_duplicate`, `is_blacklisted`

### Agent 4 — Explainer Agent (`src/agent_explainer.py`)
- **Input:** `PipelineResult` parcial (vision + reasoning + validation)
- **Proceso:** Genera reporte ejecutivo en Markdown, en español (es-MX)
  - Título, resumen, explicación detallada, impacto financiero
  - Desglose de confianza: vision + reasoning + validation → overall
  - Acción recomendada: `AUTO_APPROVE` / `ESCALATE` / `AWAIT_HUMAN_DECISION`
- **Output:** `ExplainerOutput` con `markdown_report`, `confidence_breakdown`, `next_action`

---

## 4. Stack tecnológico

### Backend
| Componente | Tecnología |
|---|---|
| Framework | FastAPI 0.115 + Uvicorn |
| LLM Inference | vLLM en AMD MI300X (192GB HBM3) |
| Modelo | DeepSeek-R1-Distill-Qwen-32B |
| GPU | AMD MI300X via AMD Developer Cloud |
| OCR | Tesseract 5 + Poppler (pdf2image) |
| Base de datos | Supabase PostgreSQL |
| Cliente Supabase | supabase-py (singleton con HTTP/1.1) |
| Validación | Pydantic v2 |
| Runtime | Python 3.12 |
| Contenedor | Docker (python:3.12-slim) |

### Frontend
| Componente | Tecnología |
|---|---|
| Framework | Next.js 15 (App Router) |
| Lenguaje | TypeScript |
| Estilos | Tailwind CSS v4 |
| Estado / Fetch | TanStack Query v5 |
| Animaciones | Framer Motion |
| Iconos | Lucide React |
| Build mode | `output: standalone` |
| Contenedor | Docker (node:20-alpine multistage) |

### Infraestructura
| Componente | Servicio |
|---|---|
| Deploy backend | DigitalOcean App Platform |
| Deploy frontend | DigitalOcean App Platform |
| Base de datos | Supabase (proyecto: fkjwaubqwvcereilllow) |
| GPU / LLM | AMD Developer Cloud (Oregon) |
| Dominio | atlas-amd-qs5g4.ondigitalocean.app |
| CI/CD | DO App Platform (deploy_on_push: true → rama main) |

---

## 5. API endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/upload` | X-API-Key | Sube PDF como multipart/form-data, devuelve `PipelineResult` |
| `POST` | `/analyze` | X-API-Key | Analiza PDF por path del servidor (solo `ATLAS_DOCS_DIR`) |
| `GET` | `/result/{doc_id}` | X-API-Key | Obtiene resultado de una auditoría por SHA256 doc_id |
| `GET` | `/audit-list?limit=N` | X-API-Key | Lista últimas N auditorías (máx 100) |
| `GET` | `/stats` | Público | Estadísticas agregadas para el dashboard |
| `POST` | `/human_decision` | X-API-Key | Registra decisión humana (APPROVE/REJECT/REQUEST_MORE_INFO) |

**Nota importante sobre routing en DO App Platform:**
El frontend llama a `https://atlas-amd-qs5g4.ondigitalocean.app/api/upload`.
La regla de ingress `prefix: /api` de DO **strips** el prefijo antes de forwardear.
El backend recibe `POST /upload` correctamente.

---

## 6. Esquema de datos (Pydantic)

```
PipelineResult
├── document_id: str (SHA256 del contenido del PDF)
├── pdf_path: str
├── status: COMPLETE | PARTIAL | FAILED
├── vision: VisionOutput
│   ├── document_type: invoice | contract | unknown
│   ├── extracted_fields: dict[str, ExtractedField]
│   │   └── ExtractedField: {value, confidence}
│   ├── detected_issues: list[str]
│   └── confidence: float [0-1]
├── reasoning: ReasoningOutput
│   ├── trap_detected: Math Error | Missing Field | Inconsistency | Unclear Value | No Trap
│   ├── trap_severity: CRITICAL | HIGH | MEDIUM | LOW | NONE
│   ├── reasoning_chain: list[ReasoningStep] (min 3)
│   │   └── ReasoningStep: {step, description, evidence, conclusion}
│   ├── confidence: float [0-1]
│   └── used_fallback: bool
├── validation: ValidatorOutput
│   ├── validation_result: ValidationResult
│   │   ├── logically_sound: bool
│   │   ├── trap_is_real: bool
│   │   ├── severity_confirmed: CRITICAL | HIGH | MEDIUM | LOW | NONE
│   │   ├── math_verified: bool | None
│   │   └── math_verification_detail: str | None
│   ├── recommendation: APPROVE | FLAG | UNCERTAIN
│   └── issues_found: list[str]
└── explanation: ExplainerOutput
    ├── explanation: ExplanationContent
    │   ├── title, summary, detailed_explanation
    │   ├── why_its_a_trap, what_to_do, financial_impact
    ├── confidence_breakdown: {vision, reasoning, validation, overall}
    ├── next_action: AWAIT_HUMAN_DECISION | AUTO_APPROVE | ESCALATE
    └── markdown_report: str
```

### Tabla `audit_results` en Supabase
```sql
doc_id                TEXT PRIMARY KEY  -- SHA256 del PDF
result_json           JSONB             -- PipelineResult completo
fraud_type            TEXT              -- trap_detected del agente 2
fraud_classification  TEXT              -- LIMPIO | SOSPECHOSO | FRAUDE_CONFIRMADO
severity              TEXT              -- CRÍTICO | ALTO | MEDIO | BAJO | NINGUNO
confidence_score      FLOAT
math_validation       BOOLEAN
is_duplicate          BOOLEAN
is_blacklisted        BOOLEAN
integrity_passed      BOOLEAN
final_status          TEXT              -- APPROVE | ESCALATE | FLAG
executive_report      TEXT              -- Markdown del agente 4
recommended_action    TEXT
pipeline_version      TEXT
processing_time_ms    INTEGER
human_decision        TEXT              -- APPROVE | REJECT | REQUEST_MORE_INFO (post-humano)
created_at            TIMESTAMPTZ
```

---

## 7. Infraestructura de deploy

### DigitalOcean App Platform — 2 servicios

**Backend (`atlas-amd-hackathon`)**
- Source: `/` (raíz del repo)
- Dockerfile: `/Dockerfile`
- Puerto: 8080
- Instance: `apps-s-1vcpu-1gb`
- Workers: 2 Uvicorn workers

**Frontend (`atlas-frontend`)**
- Source: `/frontend`
- Dockerfile: `/frontend/Dockerfile`
- Puerto: 3000
- Instance: `apps-s-1vcpu-1gb`
- Build: multistage node:20-alpine → `output: standalone`

### Ingress routing
```yaml
rules:
  - match: { path: { prefix: /api } }
    component: atlas-amd-hackathon   # backend (DO strips /api)
  - match: { path: { prefix: / } }
    component: atlas-frontend        # frontend (catch-all)
```

### Spec de deploy
Archivo: `deploy/do-app-spec.yaml`
Para actualizar la app desde CLI:
```bash
doctl apps update <APP_ID> --spec deploy/do-app-spec.yaml
```

---

## 8. Seguridad implementada

### Autenticación API
- Header `X-API-Key` requerido en todos los endpoints excepto `/stats`
- Key configurada en `.env` como `ATLAS_API_KEY`
- Sin key configurada → modo dev, acceso libre (solo localhost)

### Validaciones en `/upload`
- Extensión `.pdf` obligatoria
- Límite de 20 MB
- Verificación de magic bytes (`%PDF-`)
- Sanitización de filename (regex `[^\w\-.]` → `_`, truncado a 100 chars)
- Path traversal protection: el archivo temporal solo se escribe en `tempfile.gettempdir()/atlas_uploads`

### Validaciones en `/analyze`
- Path traversal mitigation: `Path.resolve()` + `is_relative_to(ATLAS_DOCS_DIR)`
- Solo acepta archivos `.pdf`

### CORS
- Origins explícitas: frontend DO + dominio custom
- `allow_credentials: False`
- Solo métodos `GET` y `POST`

### Supabase RLS
- Row Level Security habilitado en las 5 tablas
- Políticas: solo `service_role` tiene acceso (backend)
- `anon` key bloqueada por defecto (el frontend nunca llama directo a Supabase)
- Script: `sql/enable_rls.sql`

### Secrets en producción
- `.env` en `.gitignore` (nunca en el repo)
- Dockerfile NO copia `.env` al imagen
- Secrets inyectados como env vars en DO App Platform dashboard
- `deploy/do-app-spec.yaml` usa placeholders `SET_IN_DO_DASHBOARD`

### Validación de doc_id
- Se valida con regex `[a-f0-9]{64}` (formato SHA256 exacto) en `/result` y `/human_decision`

---

## 9. Desafíos técnicos y soluciones

### 1. Path stripping en DO App Platform
**Problema:** Con prefijo `/upload` en ingress, DO strippea el path y el backend recibe `POST /` → 404.
**Solución:** Un solo prefijo `/api` en ingress. El frontend llama `BASE_URL/api/upload`, DO strips `/api`, backend recibe `/upload`.

### 2. Conflicto de rutas `/audits`
**Problema:** Frontend tiene una página en `/audits` y el backend tenía un endpoint `GET /audits`. DO no puede diferenciar — ambos caen al mismo prefijo.
**Solución:** Renombrar el endpoint del backend a `GET /audit-list`.

### 3. StreamReset HTTP/2 entre DO y Supabase
**Problema:** En producción (DO Oregon → Supabase) aparecía `StreamReset` en los logs. Conexiones Supabase fallaban intermitentemente.
**Solución:**
- Forzar `Connection: keep-alive` en `ClientOptions` del cliente Supabase → downgrade a HTTP/1.1
- `reset_client()` en el error handler de `/stats` para recrear el singleton en el próximo request

```python
# src/supabase_client.py
_client = create_client(url, key,
    options=ClientOptions(headers={"Connection": "keep-alive"}))

def reset_client() -> None:
    global _client
    _client = None
```

### 4. Credenciales corruptas en DO dashboard
**Problema:** Al pegar el service key JWT de Supabase en el UI de DO, el campo lo cortaba por los saltos de línea → "Invalid API key".
**Solución:** Usar `doctl apps update --spec do-app-spec.yaml` con el YAML bien formateado (valores entre comillas dobles) en vez del UI.

### 5. Secrets expuestos en git
**Problema:** `docs/DO_ENV_VARS.md` y una versión temprana de `do-app-spec.yaml` tenían el service key real y ATLAS API key. GitHub Security lo detectó.
**Solución:**
- Borrar `docs/DO_ENV_VARS.md` del historial con `git rm`
- Sanitizar `do-app-spec.yaml` reemplazando keys reales con `SET_IN_DO_DASHBOARD`
- El historial ya tiene los commits con las keys — como no hubo visitas confirmadas al repo en ese período, se decidió no rotar. Las keys están ahora solo en el DO dashboard.
- RLS activado en Supabase como capa adicional de protección

### 6. Next.js `output: standalone` vs Vercel
**Problema:** Se configuró inicialmente `output: "export"` para Vercel, luego se revirtió a `standalone` al decidir usar DO con Docker.
**Solución:** `next.config.ts` con `output: "standalone"` fijo, Dockerfile multistage copia `./next/standalone`.

### 7. Bug de precedencia de operadores en dashboard
**Problema:** `stats?.avg_processing_time_ms ?? 0 / 1000` — JavaScript evalúa la división antes que el nullish coalescing.
**Solución:** `(stats?.avg_processing_time_ms ?? 0) / 1000` (paréntesis explícitos).

### 8. `math_verified` assertion invertida en tests
**Problema:** `test_pipeline.py` afirmaba `math_verified is True` para una factura con error matemático deliberado.
**Solución:** Cambiar a `is False` — el documento de test tiene un error intencional, el validator debe detectarlo.

---

## 10. Historial de commits

| Hash | Descripción |
|---|---|
| `4000496` | Initial commit |
| `eda6e6d` | feat: ATLAS v1.0 — 4-agent forensic pipeline + full deployment |
| `28dbe76` | merge: keep ATLAS gitignore and README over GitHub defaults |
| `2bd95b0` | fix: add missing frontend/src/lib/utils.ts excluded by gitignore |
| `e0654bc` | fix: remove type-incompatible Recharts Tooltip formatter |
| `2bf331e` | fix: use requirements_server.txt in Dockerfile to avoid build failures |
| `a42f88c` | feat: complete AMD-inspired frontend redesign and repo reorganization |
| `7502cdc` | fix: harden deploy config — remove secrets from image, inject frontend API key as build arg |
| `f8749f8` | fix: use Vercel-compatible Next.js output mode |
| `acb7250` | revert: restore standalone output for Docker self-hosting on DigitalOcean |
| `2b24188` | fix: update API URL to DigitalOcean App Platform deployment |
| `ccf661f` | fix: force HTTP/1.1 for Supabase client + reset singleton on StreamReset |
| `981d427` | feat: create missing pages + fix API routing for DO App Platform |
| `510b009` | fix: use single /api prefix for DO ingress path stripping |
| `ba5f72e` | security: remove credentials from repo + enable Supabase RLS |
| `d3f3134` | chore: remove accidental screenshot folder from repo |

---

## 11. Variables de entorno

### Backend (`.env` local / DO dashboard)
```env
# LLM
VLLM_BASE_URL=http://165.245.138.52:8000/v1
VLLM_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
VLLM_TIMEOUT=120
VLLM_MAX_TOKENS=4096
VLLM_TEMPERATURE=0.1
VLLM_API_KEY=not-needed

# Supabase
SUPABASE_URL=https://fkjwaubqwvcereilllow.supabase.co
SUPABASE_REST_API=https://fkjwaubqwvcereilllow.supabase.co/rest/v1/
SUPABASE_SERVICE_KEY=<en DO dashboard>
SUPABASE_ANON_KEY=<en DO dashboard>

# App
ATLAS_API_KEY=<en DO dashboard>
ATLAS_CORS_ORIGINS=https://atlas-amd-qs5g4.ondigitalocean.app
ATLAS_DOCS_DIR=/tmp/atlas_uploads
TESSERACT_CMD=/usr/bin/tesseract
POPPLER_PATH=/usr/bin
LOG_LEVEL=INFO
DEBUG=False
```

### Frontend (`.env.local` / DO build args)
```env
NEXT_PUBLIC_API_URL=https://atlas-amd-qs5g4.ondigitalocean.app/api
NEXT_PUBLIC_API_KEY=<en DO dashboard>
NEXT_PUBLIC_SUPABASE_URL=https://fkjwaubqwvcereilllow.supabase.co
```

---

## 12. Cómo correr el proyecto

### Desarrollo local (backend)
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements_server.txt

# Copiar y configurar variables
cp .env.example .env
# Editar .env con tus valores

# Correr backend
uvicorn src.api:app --reload --port 8080
```

### Desarrollo local (frontend)
```bash
cd frontend
npm install

# Copiar y configurar variables
cp .env.local.example .env.local  # o crear manualmente

# Correr frontend
npm run dev
# → http://localhost:3000
```

### Docker (producción local)
```bash
# Backend
docker build -t atlas-backend .
docker run -p 8080:8080 --env-file .env atlas-backend

# Frontend
cd frontend
docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8080 -t atlas-frontend .
docker run -p 3000:3000 atlas-frontend
```

### Tests
```bash
pytest tests/ -v
```

### SQL — Habilitar RLS en Supabase
1. Ir a supabase.com/dashboard → proyecto → SQL Editor
2. Pegar y ejecutar el contenido de `sql/enable_rls.sql`

### Deploy a DigitalOcean (CLI)
```bash
# Instalar doctl
winget install DigitalOcean.Doctl

# Autenticar
doctl auth init  # pegar DO API token

# Ver apps
doctl apps list

# Actualizar spec (si se cambia do-app-spec.yaml)
doctl apps update <APP_ID> --spec deploy/do-app-spec.yaml
```

---

_ATLAS fue construido en el AMD Hackathon 2026 por Rafael Cedillo (@rafaelcedilloav-eng) en colaboración con Claude Sonnet 4.6._
