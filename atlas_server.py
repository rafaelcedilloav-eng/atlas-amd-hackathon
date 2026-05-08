"""
ATLAS Inference Server — OpenAI-compatible, Qwen3-14B, AMD MI300X ROCm
Endpoints: GET /health, POST /v1/chat/completions
"""
import os
import time
import logging
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("MODEL_DIR", "/root/models/atlas-r3-qwen3-14b")
MODEL_NAME = "atlas-r3-qwen3-14b"

app = FastAPI(title="ATLAS Inference Server")

tokenizer = None
model = None


@app.on_event("startup")
async def load_model():
    global tokenizer, model
    logger.info(f"Loading model from {MODEL_DIR} ...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
    # Load to CPU first — device_map={'': 'cuda:0'} breaks on ROCm
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    ).to("cuda")
    model.eval()
    elapsed = time.time() - t0
    logger.info(f"Model loaded in {elapsed:.1f}s — cuda available: {torch.cuda.is_available()}")

    # Warmup inference to compile ROCm kernels
    logger.info("Warming up ROCm kernels ...")
    warmup_messages = [{"role": "user", "content": "hello"}]
    text = tokenizer.apply_chat_template(
        warmup_messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        model.generate(**inputs, max_new_tokens=8)
    logger.info("Warmup complete — server ready")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = MODEL_NAME
    messages: List[Message]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: list
    usage: dict


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "cuda": torch.cuda.is_available(),
        "device": str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else "cpu",
    }


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,  # suppress Qwen3 <think> tokens
    )
    inputs = tokenizer(text, return_tensors="pt").to("cuda")
    input_len = inputs["input_ids"].shape[1]

    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=req.max_tokens or 1024,
            temperature=max(req.temperature or 0.1, 1e-4),
            do_sample=(req.temperature or 0.1) > 0.01,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.time() - t0

    new_tokens = outputs[0][input_len:]
    response_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    output_len = len(new_tokens)

    logger.info(f"Generated {output_len} tokens in {elapsed:.2f}s ({output_len/elapsed:.1f} tok/s)")

    return {
        "id": f"chatcmpl-atlas-{int(time.time())}",
        "object": "chat.completion",
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": input_len,
            "completion_tokens": output_len,
            "total_tokens": input_len + output_len,
        },
    }
