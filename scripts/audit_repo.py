"""
MineIntel Master Repository Audit Script
Scans workspace for audit terms and classifies findings into:
PRODUCTION, TEST, FIXTURE, DEVELOPMENT, LEGACY, UNUSED
"""

import os
import re
from pathlib import Path

AUDIT_TERMS = [
    "mock",
    "mockData",
    "demo",
    "synthetic",
    "sample",
    "fixture",
    "fake",
    "hardcoded",
    "RuleBased",
    "autonomousCorpus",
    "synthesize",
    "simulated",
    "placeholder",
    "RTX 4090",
    "48290",
    "fake progress",
    "fixed metrics",
    "hardcoded charts",
    "hardcoded report facts",
    "localhost",
    "127.0.0.1",
    "cloud",
    "telemetry",
    "upload",
    "subprocess",
    "sidecar",
    "launcher",
    "desktop_app",
    "installer",
    "8765",
    "8080",
    "11434"
]

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "dist",
    "target",
    ".gemini"
}

def classify(path_str: str, term: str, line: str) -> str:
    p = path_str.replace("\\", "/").lower()
    
    if "tests/" in p or "test_" in p or "testdata" in p:
        if "fixture" in term or "mock" in term or "sample" in term or "synthetic" in term:
            return "FIXTURE"
        return "TEST"
    
    if "apps/desktop/src/services/mockdata.ts" in p:
        return "LEGACY"
        
    if "run_desktop.bat" in p or "scripts/" in p:
        return "DEVELOPMENT"
        
    if "desktop_app" in term or "mineintellauncher" in term:
        return "LEGACY"
        
    if term in ["127.0.0.1", "localhost", "11434", "sidecar", "8765", "upload", "subprocess"]:
        return "PRODUCTION"
        
    if term in ["rulebased"]:
        return "DEVELOPMENT"
        
    return "PRODUCTION"

def run_audit(root_path: Path):
    findings = {
        "PRODUCTION": [],
        "TEST": [],
        "FIXTURE": [],
        "DEVELOPMENT": [],
        "LEGACY": [],
        "UNUSED": []
    }
    
    compiled_patterns = [(term, re.compile(re.escape(term), re.IGNORECASE)) for term in AUDIT_TERMS]
    
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            file_path = Path(root) / f
            ext = file_path.suffix.lower()
            if ext not in [".py", ".ts", ".tsx", ".rs", ".toml", ".json", ".bat", ".md", ".cs"]:
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
                
            rel_path = str(file_path.relative_to(root_path))
            for line_no, line in enumerate(content.splitlines(), start=1):
                for term, pat in compiled_patterns:
                    if pat.search(line):
                        category = classify(rel_path, term, line)
                        findings[category].append({
                            "file": rel_path,
                            "line": line_no,
                            "term": term,
                            "text": line.strip()[:100]
                        })

    print("=== MINEINTEL MASTER AUDIT SUMMARY ===")
    for cat, items in findings.items():
        print(f"[{cat}]: {len(items)} occurrences")
        
    return findings

if __name__ == "__main__":
    workspace = Path(__file__).resolve().parent.parent
    run_audit(workspace)
