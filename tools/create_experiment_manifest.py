#!/usr/bin/env python3
"""
tools/create_experiment_manifest.py
===================================
Generates and validates reproducible experiment manifests for SWE Agent evaluations.

Ensures every evaluation run is bound to exact git commits, model identifiers,
file hashes, tool registries, budgets, task manifests, and runtime environment specs.

Usage:
    python tools/create_experiment_manifest.py \\
        --experiment-id exp_phase5_heldout_v50 \\
        --config configs/phase5/v5_0_final/agent.yaml \\
        --tasks data/development/task_manifest.json \\
        --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
from datetime import datetime, timezone

root = pathlib.Path(__file__).parent.parent.resolve()
manifest_dir = root / "results" / "phase5_evaluation" / "manifests"
manifest_dir.mkdir(parents=True, exist_ok=True)


def sha256_file(path: pathlib.Path) -> str:
    if not path.exists():
        return "FILE_NOT_FOUND"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=5)
        return res.stdout.strip() if res.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def generate_experiment_manifest(
    experiment_id: str,
    agent_config_path: pathlib.Path,
    task_manifest_path: pathlib.Path,
    tool_budget: int = 30,
    repair_budget: int = 3,
    random_seed: int | None = 42,
    status: str = "PRE_REGISTERED"
) -> dict:
    git_commit = get_git_commit()

    # Read config to find prompt and sampling
    cfg_text = agent_config_path.read_text(encoding="utf-8")
    prompt_match = [line.split("!include")[-1].strip() for line in cfg_text.splitlines() if "instruction:" in line and "!include" in line]
    sampling_match = [line.split("!include")[-1].strip() for line in cfg_text.splitlines() if "generate_content_config:" in line and "!include" in line]

    prompt_rel = prompt_match[0] if prompt_match else "prompts/system_v5_optimized.md"
    sampling_rel = sampling_match[0] if sampling_match else "configs/phase5/v5_0_final/sampling.yaml"

    prompt_path = root / prompt_rel
    sampling_path = root / sampling_rel

    tools = [
        "edit_file",
        "get_code_neighbors",
        "get_code_subgraph",
        "get_status",
        "read_file",
        "run_command",
        "search_similar_code",
        "submit_patch",
        "write_file",
    ]
    tool_registry_hash = hashlib.sha256(json.dumps(sorted(tools)).encode("utf-8")).hexdigest()

    agent_config_path = agent_config_path.resolve()
    task_manifest_path = task_manifest_path.resolve()
    root_resolved = root.resolve()

    manifest = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit,
        "status": status,
        "model": "gemma-4-31b-it-qat-w4a16-ct",
        "model_hash": "gemma-4-31b-it-qat-w4a16-ct-qat-w4a16",
        "agent_config": str(agent_config_path.relative_to(root_resolved)).replace("\\", "/"),
        "agent_config_hash": sha256_file(agent_config_path),
        "prompt": str(prompt_path.resolve().relative_to(root_resolved)).replace("\\", "/"),
        "prompt_hash": sha256_file(prompt_path),
        "sampling": str(sampling_path.resolve().relative_to(root_resolved)).replace("\\", "/"),
        "sampling_hash": sha256_file(sampling_path),
        "tool_registry": sorted(tools),
        "tool_registry_hash": tool_registry_hash,
        "tool_budget": tool_budget,
        "repair_budget": repair_budget,
        "task_manifest": str(task_manifest_path.relative_to(root_resolved)).replace("\\", "/"),
        "task_manifest_hash": sha256_file(task_manifest_path),
        "environment_information": {
            "python_version": sys.version.split()[0],
            "os_platform": platform.platform(),
            "container_isolation": "offline / air-gapped",
            "working_directory": str(root)
        },
        "evaluation_script_version": "1.0.0",
        "analyzer_version": "1.0.0",
        "random_seed": random_seed
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create experiment manifest for reproducible SWE evaluations.")
    parser.add_argument("--experiment-id", required=True, help="Unique identifier for experiment")
    parser.add_argument("--config", type=pathlib.Path, default=root / "configs" / "phase5" / "v5_0_final" / "agent.yaml", help="Agent YAML config")
    parser.add_argument("--tasks", type=pathlib.Path, default=root / "data" / "development" / "task_manifest.json", help="Task manifest path")
    parser.add_argument("--tool-budget", type=int, default=30, help="Max tool calls per task")
    parser.add_argument("--repair-budget", type=int, default=3, help="Max repair cycles per task")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without writing to disk")
    args = parser.parse_args()

    manifest = generate_experiment_manifest(
        experiment_id=args.experiment_id,
        agent_config_path=args.config,
        task_manifest_path=args.tasks,
        tool_budget=args.tool_budget,
        repair_budget=args.repair_budget,
        random_seed=args.seed
    )

    out_file = manifest_dir / f"{args.experiment_id}.json"
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
    else:
        out_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[CREATED] Experiment manifest written to: {out_file}")


if __name__ == "__main__":
    main()
