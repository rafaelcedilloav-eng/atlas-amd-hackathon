import json, os

path = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset_final.jsonl"
records = []
with open(path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

print(f"Total records: {len(records)}")
size_kb = os.path.getsize(path) / 1024
print(f"File size: {size_kb:.0f} KB")

r = records[0]
roles = [m["role"] for m in r["messages"]]
print(f"\nFirst record roles: {roles}")
print(f"System: {r['messages'][0]['content'][:60]}")
print(f"User:   {r['messages'][1]['content'][:80]}")

r2 = records[6100]
roles2 = [m["role"] for m in r2["messages"]]
print(f"\nRecord 6100 roles: {roles2}")
print(f"User: {r2['messages'][1]['content'][:80]}")
