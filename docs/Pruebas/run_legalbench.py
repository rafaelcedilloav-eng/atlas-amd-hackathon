import json
import re
import torch
from pathlib import Path
from datetime import datetime
from datasets import load_dataset
from transformers import pipeline

MODEL_PATH = "Rafaelcedav/atlas-r3-qwen3-14b"
RESULTS    = Path("/root/atlas_results")
RESULTS.mkdir(exist_ok=True)

TASKS = [
    ("contract_nli_explicit_identification", "answer"),
    ("opp115_data_retention",                "answer"),
    ("cuad_anti-assignment",                 "answer"),
    ("hearsay",                              "answer"),
    ("overruling",                           "answer"),
]

SYSTEM = "You are a legal expert. Answer with only the word Yes or No. Do not explain."

print(f"Loading model from {MODEL_PATH}...")
pipe = pipeline(
    "text-generation",
    model=MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
print("Model loaded.\n")

_think_re = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

def extract_yn(raw: str) -> str:
    """Strip thinking tokens then return 'yes' or 'no' (or first word)."""
    text = _think_re.sub("", raw).strip().lower()
    # grab first word, strip punctuation
    first = re.split(r"[\s,.\n]", text)[0].strip(".,;:!?")
    return first

results = {}
for task_name, label_col in TASKS:
    try:
        ds     = load_dataset("nguha/legalbench", task_name, split="test")
        sample = ds.select(range(min(100, len(ds))))
        correct = 0
        for row in sample:
            messages = [
                {"role": "system",  "content": SYSTEM},
                {"role": "user",    "content": row["text"]},
            ]
            out  = pipe(messages, max_new_tokens=32, do_sample=False,
                        temperature=None, top_p=None)
            raw  = out[0]["generated_text"][-1]["content"]
            pred = extract_yn(raw)
            gold = str(row.get(label_col, "")).strip().lower()
            correct += int(pred == gold)
        acc = round(correct / len(sample), 4)
        results[task_name] = {"accuracy": acc, "correct": correct, "total": len(sample)}
        print(f"  {task_name}: {acc:.1%} ({correct}/{len(sample)})")
    except Exception as e:
        print(f"  {task_name}: FAILED -- {e}")
        results[task_name] = {"accuracy": 0, "error": str(e)}

out_path = RESULTS / "legalbench_results.json"
with open(out_path, "w") as f:
    json.dump({
        "model":     MODEL_PATH,
        "timestamp": datetime.utcnow().isoformat(),
        "results":   results,
    }, f, indent=2)

valid = [r["accuracy"] for r in results.values() if "accuracy" in r and "error" not in r]
avg = round(sum(valid) / len(valid), 4) if valid else 0
print(f"\nLegalBench avg accuracy: {avg:.1%}")
print(f"Saved: {out_path}")
