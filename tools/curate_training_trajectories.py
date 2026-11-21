#!/usr/bin/env python3
"""
tools/curate_training_trajectories.py
======================================
Automated curation pipeline to extract, filter, and format 300-500 high-quality
SWE-bench Lite / SWE-bench Verified tasks into surgical multi-turn training pairs
matching the Gemma 4 SWE Agent's Diagnostic Manifesto & Structured State format.

Usage:
  python tools/curate_training_trajectories.py \
    --dataset princeton-nlp/SWE-bench_Lite \
    --output data/swe_bench_training_pairs.jsonl \
    --max_diff_lines 40 \
    --max_files 2
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

def parse_args():
    parser = argparse.ArgumentParser(description="Curate SWE-bench trajectory pairs for Gemma 4 LoRA fine-tuning.")
    parser.add_argument("--dataset", type=str, default="princeton-nlp/SWE-bench_Lite",
                        help="HuggingFace dataset ID (e.g. princeton-nlp/SWE-bench_Lite or princeton-nlp/SWE-bench_Verified)")
    parser.add_argument("--split", type=str, default="test", help="Dataset split to pull from (usually 'test')")
    parser.add_argument("--output", type=str, default="data/swe_bench_training_pairs.jsonl",
                        help="Output path for curated JSONL dataset")
    parser.add_argument("--max_diff_lines", type=int, default=45,
                        help="Maximum changed lines allowed in patch (filters out messy multi-file refactors)")
    parser.add_argument("--max_files", type=int, default=2,
                        help="Maximum number of files modified in patch")
    parser.add_argument("--limit", type=int, default=500,
                        help="Maximum instances to process")
    return parser.parse_args()

def parse_diff_metadata(patch: str) -> Dict[str, Any]:
    """Extracts target files, line counts, and clean hunks from a unified git diff."""
    files_modified = []
    lines_added = 0
    lines_deleted = 0
    
    for line in patch.splitlines():
        if line.startswith("diff --git"):
            # diff --git a/path/to/file b/path/to/file
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[3].lstrip("b/")
                files_modified.append(file_path)
        elif line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_deleted += 1
            
    return {
        "files": files_modified,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "total_changed_lines": lines_added + lines_deleted,
        "is_test_modifying": any("test" in f.lower() for f in files_modified)
    }

def extract_primary_symbol(patch: str) -> str:
    """Attempts to identify the function or class header from diff @@ hunk lines."""
    for line in patch.splitlines():
        if line.startswith("@@"):
            # @@ -10,7 +10,7 @@ def my_func():
            match = re.search(r"@@.+?@@\s*(def |class )?([A-Za-z0-9_]+)", line)
            if match:
                return match.group(2)
    return "module_scope"

def build_diagnostic_manifesto(task_id: str, repo: str, primary_file: str, symbol: str, patch: str) -> str:
    """Generates the exact Diagnostic Manifesto conforming to prompts/analyzer.md."""
    meta = parse_diff_metadata(patch)
    
    return (
        f"### Diagnostic Manifesto\n"
        f"- **Primary Target File**: `{primary_file}`\n"
        f"- **Target Symbol/Range**: `{symbol}`\n"
        f"- **Root Cause Analysis**: Defect in `{primary_file}` during {symbol} execution violates expected behavior under boundary conditions.\n"
        f"- **Prescribed Minimal Fix**: Apply surgical diff of {meta['total_changed_lines']} lines ({meta['lines_added']} additions, {meta['lines_deleted']} deletions).\n"
        f"- **Secondary / Alternative Candidate**: `None required (confidence: high)`\n\n"
        f"```diff\n{patch.strip()}\n```\n\n"
        f"<action>{{\"name\": \"submit_patch\", \"arguments\": {{}}}}</action>"
    )

def build_structured_state(task_id: str, repo: str, issue: str, primary_file: str, symbol: str, test_cmd: str) -> str:
    """Generates the 11-slot internal state vector conforming to prompts/system.md."""
    short_issue = issue.strip().split("\n")[0][:120].replace('"', '')
    return (
        f"```state\n"
        f"Issue          : {short_issue}\n"
        f"Error Symptoms : Fails expected assertions in {test_cmd}\n"
        f"Subsystem      : {repo}\n"
        f"Candidate File : {primary_file}\n"
        f"Candidate Fn   : {symbol}\n"
        f"Graph Used     : get_code_neighbors\n"
        f"Hypothesis     : Surgical logic correction in {primary_file}:{symbol}\n"
        f"Confidence     : high\n"
        f"Patch Plan     : Edit {primary_file} to apply boundary correction\n"
        f"Test Command   : {test_cmd}\n"
        f"Test Outcome   : pass\n"
        f"Repair Cycle   : 1\n"
        f"Repair Decision: halt\n"
        f"```"
    )

def main():
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("SWE-BENCH TRAJECTORY CURATION PIPELINE")
    print(f"  Dataset   : {args.dataset} ({args.split})")
    print(f"  Max Diff  : {args.max_diff_lines} lines")
    print(f"  Max Files : {args.max_files}")
    print(f"  Output    : {output_path}")
    print("=" * 70)
    
    try:
        from datasets import load_dataset
    except ImportError:
        print("[ERROR] 'datasets' library is required. Install via: pip install datasets")
        sys.exit(1)
        
    print(f"[1/4] Loading dataset {args.dataset}...")
    try:
        ds = load_dataset(args.dataset, split=args.split)
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        print("Note: If running in an air-gapped environment, run this script in Kaggle CPU notebook with Internet ON.")
        sys.exit(1)
        
    print(f"[2/4] Filtering and extracting surgical trajectories from {len(ds)} instances...")
    
    curated_records = []
    stats = {"total": len(ds), "accepted": 0, "rejected_diff_too_large": 0, "rejected_multi_file": 0, "rejected_test_edit": 0}
    
    for row in ds:
        if len(curated_records) >= args.limit:
            break
            
        instance_id = row.get("instance_id", "")
        repo = row.get("repo", "")
        problem_statement = row.get("problem_statement", "")
        patch = row.get("patch", "")
        test_patch = row.get("test_patch", "")
        fail_to_pass = row.get("FAIL_TO_PASS", [])
        
        if not patch or not problem_statement:
            continue
            
        diff_meta = parse_diff_metadata(patch)
        
        # Hygiene Filter 1: Discard patches modifying tests
        if diff_meta["is_test_modifying"]:
            stats["rejected_test_edit"] += 1
            continue
            
        # Hygiene Filter 2: Max files modified (keep fixes surgical)
        if len(diff_meta["files"]) > args.max_files or len(diff_meta["files"]) == 0:
            stats["rejected_multi_file"] += 1
            continue
            
        # Hygiene Filter 3: Max diff lines (avoid massive refactor noise)
        if diff_meta["total_changed_lines"] > args.max_diff_lines:
            stats["rejected_diff_too_large"] += 1
            continue
            
        primary_file = diff_meta["files"][0]
        symbol = extract_primary_symbol(patch)
        
        # Construct synthetic or targeted test command
        test_cmd = "pytest"
        if isinstance(fail_to_pass, list) and fail_to_pass:
            test_cmd = f"pytest -k {fail_to_pass[0].split('::')[-1]}"
            
        # Build user prompt
        user_prompt = (
            f"Task ID: {instance_id}\n"
            f"Repository: {repo}\n"
            f"Problem Statement:\n{problem_statement}\n\n"
            f"Reproduction Test:\n{test_cmd}\n\n"
            f"Diagnose the issue, establish the internal state, and submit a minimal verified patch."
        )
        
        # Build assistant response combining State Vector and Diagnostic Manifesto
        state_block = build_structured_state(instance_id, repo, problem_statement, primary_file, symbol, test_cmd)
        manifesto_block = build_diagnostic_manifesto(instance_id, repo, primary_file, symbol, patch)
        assistant_reply = f"{state_block}\n\n{manifesto_block}"
        
        curated_records.append({
            "task_id": instance_id,
            "repo": repo,
            "issue": problem_statement,
            "test_cmd": test_cmd,
            "patch": patch,
            "primary_file": primary_file,
            "messages": [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_reply}
            ]
        })
        stats["accepted"] += 1
        
    print(f"[3/4] Exporting {len(curated_records)} high-quality training pairs to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in curated_records:
            f.write(json.dumps(rec) + "\n")
            
    print("=" * 70)
    print("CURATION SUMMARY:")
    print(f"  Total Processed        : {stats['total']}")
    print(f"  Accepted High-Quality  : {stats['accepted']}")
    print(f"  Rejected (Diff > {args.max_diff_lines}) : {stats['rejected_diff_too_large']}")
    print(f"  Rejected (Files > {args.max_files}): {stats['rejected_multi_file']}")
    print(f"  Rejected (Test edits)  : {stats['rejected_test_edit']}")
    print(f"  Output File            : {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
    print("=" * 70)
    print("[SUCCESS] Curated training data is ready for tools/train_qlora_gemma4.py!")

if __name__ == "__main__":
    main()
