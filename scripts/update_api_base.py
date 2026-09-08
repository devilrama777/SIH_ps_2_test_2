import os
from pathlib import Path

comp_dir = Path("apps/desktop/src/components")
target = 'const API_BASE = "http://127.0.0.1:8765";'
replacement = 'import { API_BASE } from "../services/config";'

count = 0
for path in comp_dir.glob("*.tsx"):
    text = path.read_text(encoding="utf-8")
    if target in text:
        text = text.replace(target, replacement)
        path.write_text(text, encoding="utf-8")
        print(f"Updated {path.name}")
        count += 1

print(f"Successfully updated {count} component files.")
