import json
from sentence_transformers import SentenceTransformer, util

embedder = SentenceTransformer("all-MiniLM-L6-v2")

with open("/root/results/atlas_eval_report.json") as f:
    report = json.load(f)

case = report["datasets"][0]["results"][0]
with open("/root/atlas_real_cases.jsonl") as f:
    cases = {json.loads(l)["id"]: json.loads(l) for l in f if l.strip()}

orig = cases[case["case_id"]]
text = case["response"]
print("Response len:", len(text))
print()

print("=== EXPECTED ISSUES ===")
for issue in orig["expected_issues"]:
    chunks = [text[i:i+300] for i in range(0, len(text), 100)]
    e = embedder.encode(issue, convert_to_tensor=True)
    c = embedder.encode(chunks, convert_to_tensor=True)
    best = float(util.cos_sim(e, c)[0].max())
    print(f"  [{'+' if best>=0.45 else ' '}] {best:.3f}  {issue}")

print()
print("=== CRITICAL RISKS ===")
for risk in orig["critical_risks"]:
    phrase = risk.replace("_", " ")
    chunks = [text[i:i+300] for i in range(0, len(text), 100)]
    e = embedder.encode(phrase, convert_to_tensor=True)
    c = embedder.encode(chunks, convert_to_tensor=True)
    best = float(util.cos_sim(e, c)[0].max())
    print(f"  [{'+' if best>=0.45 else ' '}] {best:.3f}  {phrase}")
