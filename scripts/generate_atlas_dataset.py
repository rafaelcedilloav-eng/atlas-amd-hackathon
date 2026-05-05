#!/usr/bin/env python3
"""
ATLAS Training Dataset Generator
Reads raw .md files and uses Claude API to generate JSONL training examples.
Output: atlas_training_dataset_v3.jsonl (merges with v2)
"""

import os
import json
import time
import glob
from pathlib import Path
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR = r"D:\Proyectos\atlas-amd-hackathon\data\Data_Cruda"
V2_FILE  = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset_v2_real.jsonl"
OUT_FILE = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset_v3.jsonl"

EXAMPLES_PER_FILE = 40          # 11 files × 40 = 440 examples
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap for data gen

SYSTEM_PROMPT = (
    "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. "
    "Responde con precisión legal, citando artículos y fuentes oficiales. "
    "Usa razonamiento paso a paso cuando el caso lo requiera. "
    "Si detectas una premisa falsa en la pregunta, corrígela explícitamente antes de responder."
)

GEN_PROMPT = """\
Basándote ÚNICAMENTE en el siguiente documento de referencia, genera exactamente {n} ejemplos \
de entrenamiento para un modelo de IA llamado ATLAS (auditor forense financiero MX-USA).

DOCUMENTO:
---
{content}
---

REGLAS ESTRICTAS:
1. Cada ejemplo debe ser un objeto JSON en UNA SOLA LÍNEA con este formato exacto:
   {{"messages":[{{"role":"system","content":"{system}"}},{{"role":"user","content":"..."}},{{"role":"assistant","content":"..."}}]}}
2. Las respuestas de ATLAS deben citar artículos/fuentes reales del documento (CFF, LISR, IRS, etc.)
3. Para preguntas complejas: usar "Paso 1: ... Paso 2: ... Paso 3: ..." en la respuesta
4. Incluir al menos 5 preguntas donde el usuario tiene una premisa incorrecta — ATLAS la corrige
5. Mix de dificultad: 30% definiciones simples, 40% análisis de casos, 30% casos edge complejos
6. 15% de ejemplos en inglés (contexto USA/internacional)
7. NO inventar artículos — solo citar los que aparecen en el documento
8. NO incluir comentarios, código Python, ni texto fuera de los JSON

Genera exactamente {n} líneas JSONL válidas, una por línea, sin nada más."""


def load_v2(path: str) -> list[dict]:
    records = []
    if not os.path.exists(path):
        print(f"  [!] v2 not found at {path}, skipping merge")
        return records
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    print(f"  Loaded {len(records)} records from v2")
    return records


def generate_examples(client: anthropic.Anthropic, file_path: str, n: int) -> list[dict]:
    content = Path(file_path).read_text(encoding="utf-8")
    fname = Path(file_path).name

    prompt = GEN_PROMPT.format(
        n=n,
        content=content[:12000],  # cap to avoid huge prompts
        system=SYSTEM_PROMPT.replace('"', '\\"'),
    )

    print(f"  Generating {n} examples from {fname}...")
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as e:
        print(f"  [ERROR] API call failed for {fname}: {e}")
        return []

    records = []
    for line_num, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        # strip markdown code fences if model added them
        if line.startswith("```"):
            continue
        try:
            obj = json.loads(line)
            # validate structure
            msgs = obj.get("messages", [])
            if (
                len(msgs) == 3
                and msgs[0].get("role") == "system"
                and msgs[1].get("role") == "user"
                and msgs[2].get("role") == "assistant"
            ):
                records.append(obj)
            else:
                print(f"  [SKIP] line {line_num}: wrong message structure")
        except json.JSONDecodeError:
            print(f"  [SKIP] line {line_num}: invalid JSON")

    print(f"  ✅ {len(records)}/{n} valid examples from {fname}")
    return records


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("❌ ANTHROPIC_API_KEY not set. Export it and re-run.")

    client = anthropic.Anthropic(api_key=api_key)

    md_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.md")))
    if not md_files:
        raise SystemExit(f"❌ No .md files found in {DATA_DIR}")

    print(f"\n🔍 Found {len(md_files)} source files")
    print(f"📊 Target: {len(md_files)} × {EXAMPLES_PER_FILE} = ~{len(md_files)*EXAMPLES_PER_FILE} new examples")

    # Load v2 base
    print("\n📂 Loading v2 dataset...")
    all_records = load_v2(V2_FILE)

    # Generate from each file
    print(f"\n🤖 Generating with {MODEL}...\n")
    for i, fpath in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] {Path(fpath).name}")
        new_records = generate_examples(client, fpath, EXAMPLES_PER_FILE)
        all_records.extend(new_records)
        print(f"  Running total: {len(all_records)} records\n")
        if i < len(md_files):
            time.sleep(1)  # be gentle with rate limits

    # Save merged dataset
    print(f"\n💾 Saving {len(all_records)} total records to:\n   {OUT_FILE}")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"\n{'='*55}")
    print(f"✅ DONE")
    print(f"   Records:  {len(all_records)}")
    print(f"   v2 base:  320 examples")
    print(f"   New:      {len(all_records) - 320} examples")
    print(f"   Size:     {size_kb:.0f} KB")
    print(f"   Output:   {OUT_FILE}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
