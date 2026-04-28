# ATLAS — Variables de entorno para DigitalOcean App Platform

Copia cada KEY y VALUE en el Environment Variable Editor.

---

## vLLM (AMD MI300X)

| KEY | VALUE |
|-----|-------|
| `VLLM_BASE_URL` | `http://165.245.138.52:8000/v1` |
| `VLLM_MODEL` | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` |
| `VLLM_TIMEOUT` | `120` |
| `VLLM_MAX_TOKENS` | `4096` |
| `VLLM_TEMPERATURE` | `0.1` |
| `VLLM_API_KEY` | `not-needed` |

---

## Supabase

| KEY | VALUE |
|-----|-------|
| `SUPABASE_URL` | `https://fkjwaubqwvcereilllow.supabase.co` |
| `SUPABASE_REST_API` | `https://fkjwaubqwvcereilllow.supabase.co/rest/v1/` |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZrandhdWJxd3ZjZXJlaWxsbG93Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzA4MjkyMSwiZXhwIjoyMDkyNjU4OTIxfQ.x4KoSp7gVcSGWHhfUnliBezsnYsSDiuXJ4yHPXjZlfk` |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZrandhdWJxd3ZjZXJlaWxsbG93Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwODI5MjEsImV4cCI6MjA5MjY1ODkyMX0.Rph267KUNhk7sTjR_dCtqRUxq3miiMrfgSmnHg8gu9k` |

---

## Seguridad API

| KEY | VALUE |
|-----|-------|
| `ATLAS_API_KEY` | `5b477b525d43c080c7921cc9a5ef31b93da59cb5b7d299b0cb383417626b8091` |
| `ATLAS_CORS_ORIGINS` | `https://atlas-hackathon.com,https://www.atlas-hackathon.com,https://atlas-amd-qs5g4.ondigitalocean.app` |
| `ATLAS_DOCS_DIR` | `/tmp/atlas_uploads` |

---

## Sistema (Linux — paths del contenedor Docker)

| KEY | VALUE |
|-----|-------|
| `TESSERACT_CMD` | `/usr/bin/tesseract` |
| `POPPLER_PATH` | `/usr/bin` |

---

## Logging

| KEY | VALUE |
|-----|-------|
| `LOG_LEVEL` | `INFO` |
| `DEBUG` | `False` |
