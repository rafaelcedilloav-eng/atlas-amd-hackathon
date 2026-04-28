#!/usr/bin/env python3
"""
ATLAS Setup Script
AMD Developer Hackathon 2026
Automatiza: carpetas, archivos, dependencias, validación
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

# Project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Carpetas a crear
FOLDERS = [
    'docs',
    'src',
    'frontend',
    'tests',
    'test_documents',
    'sql',
    'logs'
]

# Contenido de archivos
FILES = {
    'docs/00_MASTER_ATLAS.md': '''# ATLAS: MASTER SPECIFICATION
## Agentic Task-Level Reasoning System for Enterprise Documents
**Proyecto:** AMD Developer Hackathon 2026  
**Equipo:** Rafael Cedillo (1) + IA (Claude + Gemini)  
**Deadline:** 10 Mayo 2026 (entrega) | 10 Mayo San Francisco (presentación)  
**Status:** FASE 1 — SETUP INFRAESTRUCTURA  
**Versión:** 1.0

---

## REFERENCIA COMPLETA

Ver documento completo en GitHub: https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon

### Definición del Problema
Empresas automatizan procesos con IA generativa, pero fallan cuando la decisión requiere análisis visual, razonamiento complejo y consistencia.

### Por qué ATLAS
- Visión integrada (Llama 3.2 Vision)
- Razonamiento avanzado (DeepSeek-R1 en MI300X)
- Hardware AMD (MI300X sin fragmentación)

### Criterios de Éxito (igual peso)
1. Aplicación Tecnológica
2. Valor de Negocio
3. Originalidad
4. Presentación

### Timeline
- Viernes 25: Setup infraestructura
- Sábado 26: Agent 1 (Vision)
- Domingo 27: Agents 2-4 + POST 1
- Lunes 28: MI300X real + POST 2
- Martes 29: Video + slides + SUBMIT

---

Para setup completo, ver `docs/02_SETUP.md`
''',

    'docs/01_ARCHITECTURE.md': '''# ATLAS: ARCHITECTURE & DESIGN DECISIONS
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
''',

    'docs/02_SETUP.md': '''# ATLAS: SETUP & CONFIGURATION GUIDE
## Local Development Environment

---

## Setup Completado Automáticamente

✅ Carpetas creadas
✅ Archivos generados
✅ .gitignore configurado
✅ requirements.txt listo

---

## Próximos Pasos Manuales

### 1. Instalar dependencias
```bash
cd D:\\Proyectos\\atlas-amd-hackathon
venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Descargar Ollama
- Ir a https://ollama.ai
- Descargar para Windows
- Instalar

### 3. Descargar modelos
```bash
ollama pull llama2:7b-vision
ollama pull llama2:7b
```

### 4. Iniciar Ollama
```bash
ollama serve
```

### 5. Crear .env
```bash
SUPABASE_URL=https://[tu_proyecto].supabase.co
SUPABASE_KEY=[tu_key]
OLLAMA_BASE_URL=http://localhost:11434
```

### 6. Conseguir documentos de prueba
- Mínimo 5-10 PDFs en `test_documents/`
- Facturas, contratos, reportes

---

## Validación

```bash
python --version  # 3.12+
pip list | grep fastapi
curl http://localhost:11434/api/tags  # Ollama running
```

---

## Siguiente Paso

Sábado 08:00 - Claude Code genera Agent 1 (Vision Analyzer)
''',

    'requirements.txt': '''## ATLAS: Python Dependencies
## AMD Developer Hackathon 2026
## Python 3.12+

# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0

# AI/ML Orchestration
crewai==0.1.0
langchain==0.0.340
langchain-community==0.0.10

# LLM Providers
ollama==0.1.0
openai==1.3.0

# Document Processing
pypdf==3.17.1
pillow==10.1.0

# Database
supabase==2.0.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Embeddings & Search
sentence-transformers==2.2.2
numpy==1.24.3
scipy==1.11.4

# Web Framework
streamlit==1.28.1

# Utilities
requests==2.31.0
aiohttp==3.9.1
pydantic-settings==2.1.0

# Logging
python-json-logger==2.0.7

# Dev/Testing (optional)
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
''',

    '.gitignore': '''# Environment & Secrets
.env
.env.local
.env.*.local
*.pem
*.key
*.pub

# Virtual Environment
venv/
env/
ENV/
.venv

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
logs/
*.log
*.log.*
nohup.out

# Test Documents
test_documents/
*.pdf
*.PDF

# Models
models/
.ollama/

# Database
*.db
*.sqlite
*.sqlite3

# Cache
.cache/
*.cache

# OS
Thumbs.db
.AppleDouble
.LSOverride
._*

# Temporary
tmp/
temp/
*.tmp

# Streamlit
.streamlit/secrets.toml

# SSH Keys
.ssh/
do_atlas
''',

    'README.md': '''# ATLAS: Agentic Task-Level Reasoning System
## AMD Developer Hackathon 2026

Razonamiento visual empresarial powered by AMD MI300X.

### Quick Start

1. **Setup**
   ```bash
   pip install -r requirements.txt
   ollama pull llama2:7b-vision
   ollama pull llama2:7b
   ollama serve  # Terminal separada
   ```

2. **Run**
   ```bash
   uvicorn src.api:app --reload
   streamlit run frontend/app.py
   ```

3. **Test**
   Upload PDF → Get decision + reasoning + explanation

### Architecture
- Frontend: Streamlit
- Backend: FastAPI + CrewAI
- Database: Supabase (PostgreSQL + pgvector)
- Inference: vLLM (DeepSeek-R1) + Ollama (Llama 3.2)

### Documentation
- `docs/00_MASTER_ATLAS.md` - Project specification
- `docs/01_ARCHITECTURE.md` - Technical architecture
- `docs/02_SETUP.md` - Setup guide

### Team
- **Executor:** Rafael Cedillo
- **Architect:** Claude
- **Auditor:** Gemini

### Deadline
10 Mayo 2026 (Entrega + Presentación en San Francisco)

---

Build in Public: @lablabai @AIatAMD
'''
}

def create_folders():
    """Crear todas las carpetas necesarias"""
    print_info("Creando carpetas...")
    for folder in FOLDERS:
        folder_path = PROJECT_ROOT / folder
        folder_path.mkdir(exist_ok=True)
        print_success(f"Carpeta creada: {folder}")

def create_files():
    """Crear todos los archivos"""
    print_info("Creando archivos...")
    for file_path, content in FILES.items():
        full_path = PROJECT_ROOT / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        print_success(f"Archivo creado: {file_path}")

def create_env_template():
    """Crear template de .env"""
    print_info("Creando .env.example...")
    env_content = '''# ATLAS Environment Variables
# Copiar este archivo a .env y llenar tus valores

# Supabase (llenar con tus datos)
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[ANON_KEY]
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres

# DigitalOcean MI300X
DIGITALOCEAN_IP=[IP_PÚBLICA]
DIGITALOCEAN_SSH_USER=root
DIGITALOCEAN_SSH_KEY_PATH=~/.ssh/do_atlas

# vLLM (DeepSeek-R1)
VLLM_BASE_URL=http://[DIGITALOCEAN_IP]:8000/v1
VLLM_MODEL=deepseek-r1

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VISION_MODEL=llama2:7b-vision
OLLAMA_EXPLAINER_MODEL=llama2:7b

# App config
DEBUG=True
LOG_LEVEL=INFO
'''
    
    env_path = PROJECT_ROOT / '.env.example'
    env_path.write_text(env_content, encoding='utf-8')
    print_success("Archivo creado: .env.example")

def verify_structure():
    """Verificar que todo se creó correctamente"""
    print_info("Verificando estructura...")
    
    # Verificar carpetas
    for folder in FOLDERS:
        if (PROJECT_ROOT / folder).exists():
            print_success(f"✓ Carpeta: {folder}")
        else:
            print_error(f"✗ Carpeta faltante: {folder}")
    
    # Verificar archivos
    for file_path in FILES.keys():
        if (PROJECT_ROOT / file_path).exists():
            print_success(f"✓ Archivo: {file_path}")
        else:
            print_error(f"✗ Archivo faltante: {file_path}")

def print_summary():
    """Imprimir resumen final"""
    print("\n" + "="*60)
    print_success("SETUP COMPLETADO")
    print("="*60)
    print(f"""
PROJECT ROOT: {PROJECT_ROOT}

ESTRUCTURA CREADA:
{Colors.GREEN}✓ docs/
  ├── 00_MASTER_ATLAS.md
  ├── 01_ARCHITECTURE.md
  └── 02_SETUP.md
✓ src/ (vacío - código generado mañana)
✓ frontend/ (vacío)
✓ tests/ (vacío)
✓ test_documents/ (llenar con PDFs)
✓ sql/ (vacío)
✓ logs/ (vacío)
✓ .gitignore
✓ requirements.txt
✓ README.md
✓ .env.example{Colors.RESET}

PRÓXIMOS PASOS:
1. pip install -r requirements.txt
2. Descargar Ollama (https://ollama.ai)
3. ollama pull llama2:7b-vision && ollama pull llama2:7b
4. ollama serve (en terminal separada)
5. Llenar .env con tus credenciales (copiar .env.example → .env)
6. Conseguir 5-10 PDFs en test_documents/

MAÑANA (SÁBADO 08:00):
Claude Code genera Agent 1 (Vision Analyzer)

{Colors.BLUE}TEAM:
• Executor: Rafael Cedillo
• Architect: Claude
• Auditor: Gemini{Colors.RESET}

DEADLINE: 10 Mayo 2026
""")

def main():
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BLUE}║ ATLAS SETUP AUTOMATION                 ║{Colors.RESET}")
    print(f"{Colors.BLUE}║ AMD Developer Hackathon 2026           ║{Colors.RESET}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════╝{Colors.RESET}\n")
    
    try:
        create_folders()
        create_files()
        create_env_template()
        verify_structure()
        print_summary()
        print_success("¡Setup completado exitosamente!")
        return 0
    except Exception as e:
        print_error(f"Error durante setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
