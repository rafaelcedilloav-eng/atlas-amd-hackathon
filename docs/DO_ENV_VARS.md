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
| `SUPABASE_SERVICE_KEY` | `***REMOVED***` |
| `SUPABASE_ANON_KEY` | `***REMOVED***` |

---

## Seguridad API

| KEY | VALUE |
|-----|-------|
| `ATLAS_API_KEY` | `***REMOVED***` |
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
