import json
from sentence_transformers import SentenceTransformer, util

embedder = SentenceTransformer("all-MiniLM-L6-v2")

with open("/root/results/atlas_eval_report.json") as f:
    report = json.load(f)

case = report["datasets"][0]["results"][0]
print("Case:", case["case_id"])
print("Response len:", len(case["response"]))
print("Response:", case["response"][:400])
print()

expected = [
    "Missing transfer pricing study",
    "Thin capitalization breach LISR Art. 28-XXIII",
    "Royalty deductibility denied",
    "transfer pricing",
    "LISR",
    "documentation",
]
text = case["response"]
for phrase in expected:
    chunks = [text[i:i+200] for i in range(0, len(text), 80)]
    e = embedder.encode(phrase, convert_to_tensor=True)
    c = embedder.encode(chunks, convert_to_tensor=True)
    scores = util.cos_sim(e, c)[0]
    best = float(scores.max())
    print(f"{phrase!r:50s} -> best sim: {best:.3f}  {'HIT' if best >= 0.45 else 'miss'}")
