#!/usr/bin/env python3
"""
ATLAS Sandbox Dataset Generator
Usa Qwen3-14B fine-tuned para generar registros sintéticos del Regulatory Sandbox.
Input:  10 gold records (seed) + schema
Output: atlas_sandbox_generated.jsonl (~250 records)
"""

import json
import random
import time
import re
import os
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_PATH = "/outputs/r2_qwen3_14b_finetuned"
SEED_FILE  = "/data/atlas_sandbox_batch1_10records.jsonl"
SCHEMA_FILE = "/data/atlas_sandbox_schema_v1.0.json"
OUTPUT_FILE = "/data/atlas_sandbox_generated.jsonl"
TARGET_RECORDS = 240  # + 10 seed = 250 total

SCENARIO_TYPES = [
    "constitucion_LLC", "adquisicion_activo", "contrato_servicios",
    "operacion_combustible", "venta_digital", "fusion_adquisicion",
    "constitucion_fideicomiso", "operacion_inmobiliaria",
    "prestamo_transfronterizo", "joint_venture"
]

JURISDICTION_COMBOS = [
    ["MX"], ["USA"], ["MX", "USA", "CROSS"],
    ["USA", "CROSS"], ["MX", "CROSS"]
]

RECOMMENDATIONS = [
    "PROCEED_WITH_CAUTION", "RESTRUCTURE_BEFORE_EXECUTING",
    "ABORT", "ESCALATE_LEGAL"
]

def load_seed_records(path: str) -> list:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def build_prompt(seed_records: list, scenario_type: str, jurisdictions: list, batch_num: int) -> str:
    # Pick 2 diverse seed examples as few-shot context
    examples = random.sample(seed_records, min(2, len(seed_records)))
    examples_str = "\n\n".join(json.dumps(e, ensure_ascii=False, indent=2) for e in examples)

    return f"""Eres ATLAS Regulatory Sandbox, un simulador avanzado de riesgo normativo cross-border.

Tu tarea: generar UN registro de entrenamiento en formato JSON válido para el sandbox, siguiendo EXACTAMENTE la misma estructura de los ejemplos.

EJEMPLOS DE REFERENCIA:
{examples_str}

INSTRUCCIONES:
- scenario_type: "{scenario_type}"
- jurisdictions_involved: {json.dumps(jurisdictions)}
- Genera un caso DIFERENTE y REALISTA con normativa específica
- El id debe ser "sandbox-{(batch_num):03d}"
- Incluye regulatory_heat_map, compound_risks, alternative_scenarios y timeline completos
- La recomendación debe ser coherente con el overall_risk_score
- Usa artículos específicos reales (CFF, LISR, IRM, etc.)
- Solo responde con el JSON, sin texto adicional

GENERA EL REGISTRO JSON AHORA:"""

def extract_json(text: str) -> dict | None:
    # Intenta extraer JSON del texto generado
    text = text.strip()
    # Busca el primer { y último }
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        return None
    json_str = text[start:end+1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Intento 2: regex para limpiar
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        try:
            return json.loads(json_str)
        except:
            return None

def validate_record(record: dict) -> bool:
    required = ["id", "scenario_type", "operation_proposed", "parties",
                "simulation_engine", "output", "metadata"]
    if not all(k in record for k in required):
        return False
    if "overall_risk_score" not in record.get("output", {}):
        return False
    if "reasoning_chain" not in record.get("simulation_engine", {}):
        return False
    return True

def main():
    print("=" * 60)
    print("  ATLAS Sandbox Dataset Generator")
    print(f"  Target: {TARGET_RECORDS} new records")
    print(f"  Model: {MODEL_PATH}")
    print("=" * 60)

    # Load seed records
    print(f"Loading seed records from {SEED_FILE}...")
    seed_records = load_seed_records(SEED_FILE)
    print(f"  Loaded {len(seed_records)} seed records")

    # Load model
    print(f"Loading model from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
        device_map="auto"
    )
    model.eval()
    print("  Model loaded!")

    # Generate records
    generated = []
    failed = 0
    batch_num = 11  # Starts after the 10 seed records

    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_f:
        while len(generated) < TARGET_RECORDS:
            scenario = random.choice(SCENARIO_TYPES)
            jurisdictions = random.choice(JURISDICTION_COMBOS)

            print(f"\n[{len(generated)+1}/{TARGET_RECORDS}] Generating sandbox-{batch_num:03d} | {scenario} | {jurisdictions}")

            prompt = build_prompt(seed_records, scenario, jurisdictions, batch_num)

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )

            response = tokenizer.decode(
                output[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            )

            record = extract_json(response)

            if record and validate_record(record):
                record["id"] = f"sandbox-{batch_num:03d}"
                record["batch"] = (batch_num // 10) + 1
                record["mode"] = "sandbox"
                generated.append(record)
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
                print(f"  ✓ Generated | score={record['output'].get('overall_risk_score', '?')} | rec={record['output'].get('recommendation', '?')}")
                batch_num += 1
            else:
                failed += 1
                print(f"  ✗ Invalid JSON (failed: {failed})")
                if failed > 30:
                    print("Too many failures, stopping early")
                    break

            # Small pause to avoid GPU thermal issues
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"  GENERATION COMPLETE")
    print(f"  Generated: {len(generated)} records")
    print(f"  Failed:    {failed} records")
    print(f"  Output:    {OUTPUT_FILE}")
    print("=" * 60)

    # Combine with seed records
    combined_path = "/data/atlas_sandbox_master.jsonl"
    print(f"\nCombining seed + generated → {combined_path}")
    with open(combined_path, "w", encoding="utf-8") as f:
        for r in seed_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(OUTPUT_FILE, "r", encoding="utf-8") as gen_f:
            for line in gen_f:
                f.write(line)
    print(f"  Total combined: {len(seed_records) + len(generated)} records")
    print(f"  Ready for fine-tuning: {combined_path}")

if __name__ == "__main__":
    main()
