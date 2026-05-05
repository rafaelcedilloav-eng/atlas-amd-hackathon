#!/usr/bin/env python3
"""
Merge final ATLAS training dataset:
  - atlas_training_dataset.jsonl  (6002 records, Round 1, sin system prompt, encoding roto)
  - atlas_training_dataset_v3.jsonl (435 records, v2+new, con system prompt, encoding OK)

Output: atlas_training_dataset_final.jsonl
"""
import json, os

SYSTEM = (
    "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. "
    "Responde con precisión legal, citando artículos y fuentes oficiales. "
    "Usa razonamiento paso a paso cuando el caso lo requiera. "
    "Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."
)

R1_PATH  = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset.jsonl"
V3_PATH  = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset_v3.jsonl"
OUT_PATH = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset_final.jsonl"


def fix_mojibake(s: str) -> str:
    """Fix UTF-8 text that was stored as Latin-1 (mojibake)."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return s


def fix_record(obj: dict) -> dict:
    """Fix encoding in all message content strings."""
    fixed_msgs = []
    for msg in obj.get("messages", []):
        fixed_msgs.append({
            "role": msg["role"],
            "content": fix_mojibake(msg["content"])
        })
    return {"messages": fixed_msgs}


def add_system(obj: dict) -> dict:
    """Prepend system message if not present."""
    msgs = obj.get("messages", [])
    if msgs and msgs[0]["role"] == "system":
        return obj
    return {"messages": [{"role": "system", "content": SYSTEM}] + msgs}


def load_jsonl(path: str, encoding: str = "utf-8") -> list:
    records = []
    with open(path, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def main():
    print("Loading Round 1 (6002 records, latin-1)...")
    r1 = load_jsonl(R1_PATH, encoding="latin-1")
    print(f"  Loaded: {len(r1)}")

    print("Adding system prompt to Round 1...")
    r1_fixed = [add_system(rec) for rec in r1]

    # Verify on first record
    sample = r1_fixed[0]["messages"][1]["content"]
    print(f"  Sample: {sample[:80]}")

    print("\nLoading v3 (435 records — already clean)...")
    v3 = load_jsonl(V3_PATH)
    print(f"  Loaded: {len(v3)}")

    merged = r1_fixed + v3
    print(f"\nTotal merged: {len(merged)} records")

    print(f"Writing to {OUT_PATH}...")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"\n{'='*55}")
    print(f"DONE")
    print(f"   Round 1 (fixed): {len(r1_fixed)}")
    print(f"   v3 (clean):      {len(v3)}")
    print(f"   Total:           {len(merged)}")
    print(f"   Size:            {size_kb:.0f} KB")
    print(f"   Output:          {OUT_PATH}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
