import os
from pathlib import Path

def generate_full_dump():
    output_file = "final_massive_audit_dump.txt"
    with open(output_file, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk("."):
            # Ignorar directorios pesados
            if any(x in root for x in ["node_modules", ".git", ".next", "venv", "__pycache__", "Viejos"]):
                continue
                
            for file in files:
                if file.endswith((".py", ".ts", ".tsx", ".md")):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        out.write(f"\n--- FILE: {file_path} ---\n")
                        out.write(content)
                        out.write("\n")
                    except Exception as e:
                        out.write(f"\n--- ERROR READING {file_path}: {e} ---\n")

    print(f"Dump generado: {output_file}")

if __name__ == "__main__":
    generate_full_dump()
