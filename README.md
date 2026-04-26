# ATLAS: Agentic Task-Level Reasoning System
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
