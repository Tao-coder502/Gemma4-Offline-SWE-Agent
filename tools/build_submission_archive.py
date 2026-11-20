#!/usr/bin/env python3
"""
tools/build_submission_archive.py
=================================
Packages the full production submission archive (submission.zip) conforming
to the Google Gemma 4 Developer Agent Competition specification:
  - Root agent config (agent.yaml)
  - Sampling hyperparameters (configs/sampling.yaml)
  - System instructions (prompts/system.md, prompts/analyzer.md)
  - Sub-agent definitions (sub_agents/code_analyzer.yaml)
  - LoRA adapters (adapters/main_lora/adapter_config.json, adapter_model.safetensors)
  - ADK Skills (skills/repo_navigation/SKILL.md, resources/, scripts/)
"""

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
ZIP_PATH = ROOT / "submission.zip"

COMPONENTS = [
    # Root configs
    "agent.yaml",
    "configs/sampling.yaml",
    
    # Prompts
    "prompts/system.md",
    "prompts/analyzer.md",
    
    # Sub-agents
    "sub_agents/code_analyzer.yaml",
    
    # LoRA adapters
    "adapters/main_lora/adapter_config.json",
    "adapters/main_lora/adapter_model.safetensors",
    "adapters/main_lora/README.md",
    "adapters/README.md",
    
    # Skills
    "skills/repo_navigation/SKILL.md",
    "skills/repo_navigation/resources/graph_traversal_rules.md",
    "skills/repo_navigation/resources/patch_hygiene.md",
    "skills/repo_navigation/resources/failure_classification.md",
    "skills/repo_navigation/scripts/find_symbol_definition.py",
    "skills/repo_navigation/scripts/audit_diff_hygiene.py",
]

def build_zip():
    print(f"Building submission archive at: {ZIP_PATH}...")
    
    # Remove old zip if present
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
        
    missing = []
    for rel_path in COMPONENTS:
        p = ROOT / rel_path
        if not p.exists():
            missing.append(rel_path)
            
    if missing:
        print(f"[ERROR] Missing required submission components: {missing}")
        return False
        
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in COMPONENTS:
            abs_p = ROOT / rel_path
            zf.write(abs_p, rel_path)
            print(f"  + Added: {rel_path} ({abs_p.stat().st_size:,} bytes)")
            
    zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] submission.zip created successfully ({zip_size_mb:.2f} MB)")
    return True

if __name__ == "__main__":
    build_zip()
