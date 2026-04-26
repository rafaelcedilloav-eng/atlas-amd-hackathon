# ATLAS: SETUP & CONFIGURATION GUIDE
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
cd D:\Proyectos\atlas-amd-hackathon
venv\Scripts\activate
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
