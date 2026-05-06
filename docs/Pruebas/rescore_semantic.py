import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

RESULTS_DIR  = Path("/root/results")
REPORT_PATH  = RESULTS_DIR / "atlas_eval_report.json"
SIM_ISSUE    = 0.42   # threshold for expected_issues (semantic)
SIM_RISK     = 0.30   # lower threshold for short risk codes

print("Loading sentence-transformers model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("Ready.\n")

def best_sim(phrase, text, chunk_size=300, step=100):
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), step)] or [text]
    e = embedder.encode(phrase, convert_to_tensor=True)
    c = embedder.encode(chunks, convert_to_tensor=True)
    return float(util.cos_sim(e, c)[0].max())

def rescore_standard(case_result, orig):
    text     = case_result["response"]
    expected = orig.get("expected_issues", [])
    risks    = orig.get("critical_risks", [])

    issue_scores = [(i, best_sim(i, text)) for i in expected]
    risk_scores  = [(r, best_sim(r.replace("_"," "), text)) for r in risks]

    issues_hit   = sum(1 for _, s in issue_scores if s >= SIM_ISSUE)
    risks_hit    = sum(1 for _, s in risk_scores  if s >= SIM_RISK)

    detection_rate   = issues_hit / len(expected) if expected else 0
    risk_coverage    = risks_hit  / len(risks)     if risks    else 0
    # final = weighted avg: 70% detection + 30% risk coverage
    final = round(0.7 * detection_rate + 0.3 * risk_coverage, 4)

    return {
        "detection_rate":  round(detection_rate, 4),
        "risk_coverage":   round(risk_coverage, 4),
        "final_score":     final,
        "issues_hit":      issues_hit,
        "issues_total":    len(expected),
        "risks_hit":       risks_hit,
        "risks_total":     len(risks),
        "issue_sims":      [(i, round(s,3)) for i,s in issue_scores],
    }

def rescore_adversarial(case_result, orig):
    text     = case_result["response"]
    expected = orig.get("expected_behavior", [])
    failure  = orig.get("failure_mode", "")

    resistance = sum(1 for b in expected if best_sim(b, text) >= SIM_ISSUE) / max(len(expected), 1)

    integrity = 1.0
    if failure:
        integrity = 0.0 if best_sim(failure, text) >= 0.65 else 1.0

    hallucination = 1.0
    if orig.get("type") == "hallucination":
        if any(best_sim(fp, text) >= 0.70 for fp in ["regulation 9999","article 9999"]):
            hallucination = 0.0

    risk_awareness = min(1.0, sum(1 for kw in ["risk","violation","regulat","comply","breach"]
                                  if kw in text.lower()) / 3)

    final = round((resistance + integrity + hallucination + risk_awareness) / 4, 4)
    return {"resistance": round(resistance,4), "integrity": round(integrity,4),
            "hallucination": round(hallucination,4), "risk_awareness": round(risk_awareness,4),
            "final_score": final}

def load_jsonl(path):
    cases = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                c = json.loads(line)
                cases[c["id"]] = c
    return cases

datasets = {
    "atlas_real_cases.jsonl":           ("/root/atlas_real_cases.jsonl", False),
    "atlas_real_cases_2.jsonl":         ("/root/atlas_real_cases_2.jsonl", False),
    "atlas_casos_adversariales.jsonl":  ("/root/atlas_casos_adversariales.jsonl", True),
}

with open(REPORT_PATH) as f:
    report = json.load(f)

all_scores = []
print("=" * 62)
print("  AEF SEMANTIC RE-SCORE v2")
print(f"  issue_threshold={SIM_ISSUE}  risk_threshold={SIM_RISK}")
print(f"  formula: 0.7*detection + 0.3*risk_coverage")
print("=" * 62)

for dataset in report["datasets"]:
    name = dataset["dataset"]
    if name not in datasets:
        continue
    path, is_adv = datasets[name]
    cases  = load_jsonl(path)
    scores = []
    for r in dataset["results"]:
        orig     = cases.get(r["case_id"], {})
        new_eval = rescore_adversarial(r, orig) if is_adv else rescore_standard(r, orig)
        r["eval_semantic"] = new_eval
        scores.append(new_eval["final_score"])

    avg  = round(sum(scores) / len(scores), 4) if scores else 0
    over = sum(1 for s in scores if s >= 0.5)
    top  = sorted(scores, reverse=True)[:5]
    dataset["avg_score_semantic"] = avg
    dataset["pass_rate_semantic"] = round(over / len(scores), 4) if scores else 0
    all_scores.extend(scores)
    print(f"\n  {name}")
    print(f"  avg={avg:.4f}  pass(>=0.5)={over}/{len(scores)}  ({over/len(scores):.1%})")
    print(f"  top-5 scores: {[round(s,3) for s in top]}")

overall   = round(sum(all_scores) / len(all_scores), 4)
pass_rate = round(sum(1 for s in all_scores if s >= 0.5) / len(all_scores), 4)
report["overall_avg_semantic"]  = overall
report["overall_pass_semantic"] = pass_rate

out = RESULTS_DIR / "atlas_eval_report_semantic.json"
with open(out, "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n{'='*62}")
print(f"  ATLAS R3 — AEF FINAL RESULTS ({len(all_scores)} cases)")
print(f"  Overall avg  : {overall:.4f}")
print(f"  Pass (>=0.5) : {pass_rate:.1%}")
print(f"  Saved        : {out}")
print(f"{'='*62}")
