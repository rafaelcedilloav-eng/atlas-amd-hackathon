"""
ATLAS System Configuration v3.0
"""
from pydantic_settings import BaseSettings

class AtlasSettings(BaseSettings):
    # Umbrales
    math_tolerance: float = 0.05
    
    # ── Modelos fine-tuned ATLAS (AMD MI300X) ──────────────────────────────
    # Qwen3-14B: core reasoning + explainer + sandbox estándar  (puerto 8000)
    core_url: str = "http://localhost:8000"
    core_model: str = "atlas-r2-qwen3-14b"

    # DeepSeek-R1-8B: sandbox Red Team / adversarial reasoning   (puerto 8001)
    deepseek_url: str = "http://localhost:8001"
    deepseek_model: str = "atlas-finanzas-deepseek-r1-8b"

    # Mistral-7B-R2: compliance router / document triage          (puerto 8003)
    router_url: str = "http://localhost:8003"
    router_model: str = "atlas-mistral-7b-legal-r2"

    # Vision: InternVL2 OCR                                       (puerto 8002)
    vision_url: str = "http://localhost:8002"
    vision_model: str = "InternVL2-Llama3-76B"

    # Fallback interno (no se usa en producción AMD)
    primary_model: str = "atlas-r2-qwen3-14b"
    fallback_model: str = "atlas-finanzas-deepseek-r1-8b"

    # Finance / Compliance
    FINANCE_SERVICE_URL: str = "http://localhost:8080" # Placeholder o mismo API
    
    ALLOWED_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = AtlasSettings()
