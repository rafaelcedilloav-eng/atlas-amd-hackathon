import json

# Read the original R1 file
path_r1 = r"D:\Proyectos\atlas-amd-hackathon\Trainning_Steps\atlas_training_dataset.jsonl"
with open(path_r1, encoding="utf-8") as f:
    first_line = f.readline().strip()

obj = json.loads(first_line)
user_content = obj["messages"][0]["content"]
print("Raw string (first 40 chars):", repr(user_content[:40]))
print("Codepoints:", [hex(ord(c)) for c in user_content[:10]])

# Try fix
try:
    fixed = user_content.encode("latin-1").decode("utf-8")
    print("Fixed:", fixed[:40])
except Exception as e:
    print("Fix failed:", e)

# Try reading as latin-1 instead
with open(path_r1, encoding="latin-1") as f:
    first_line2 = f.readline().strip()
obj2 = json.loads(first_line2)
user2 = obj2["messages"][0]["content"]
print("Read as latin-1:", user2[:40])
