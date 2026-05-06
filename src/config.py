"""
ATLAS System Configuration v3.0
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings


class AtlasSettings(BaseSettings):
    math_tolerance: float = 0.05

    # ── DO App Platform injects these ─────────────────────────────────────────
    # VLLM_BASE_URL = "http://165.245.138.52:8000/v1"  (includes /v1)
    # VLLMClient appends /v1/chat/completions, so we strip the trailing /v1
    VLLM_BASE_URL: str = "http://localhost:8000/v1"
    VLLM_MODEL: str = "atlas-r3-qwen3-14b"
    VLLM_TIMEOUT: float = 30.0

    # ── Derived fields (overwritten by model_validator below) ─────────────────
    core_url: str = "http://localhost:8000"
    core_model: str = "atlas-r3-qwen3-14b"
    vision_url: str = "http://localhost:8000"
    vision_model: str = "atlas-r3-qwen3-14b"
    router_url: str = "http://localhost:8000"
    router_model: str = "atlas-r3-qwen3-14b"
    deepseek_url: str = "http://localhost:8000"
    deepseek_model: str = "atlas-r3-qwen3-14b"
    primary_model: str = "atlas-r3-qwen3-14b"
    fallback_model: str = "atlas-r3-qwen3-14b"

    FINANCE_SERVICE_URL: str = "http://localhost:8080"
    ALLOWED_ORIGINS: list = ["*"]

    @model_validator(mode="after")
    def apply_vllm_env(self) -> "AtlasSettings":
        """Map VLLM_BASE_URL / VLLM_MODEL to all client configs."""
        base = self.VLLM_BASE_URL.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        model = self.VLLM_MODEL
        self.core_url = base
        self.core_model = model
        self.vision_url = base
        self.vision_model = model
        self.router_url = base
        self.router_model = model
        self.deepseek_url = base
        self.deepseek_model = model
        self.primary_model = model
        self.fallback_model = model
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = AtlasSettings()
