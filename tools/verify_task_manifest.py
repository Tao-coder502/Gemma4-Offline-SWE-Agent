#!/usr/bin/env python3
"""
tools/verify_task_manifest.py
=============================
Deterministic validator for SWE Agent task manifests.

Validates:
  1. Unique task IDs across the manifest.
  2. Unique task hashes across the manifest.
  3. Valid git commit SHA-1 format (40-char hex).
  4. Category validity against the 8 canonical structural categories.
  5. Correct 'development' vs 'heldout' partition labeling.
  6. Non-overlap check: ensures zero intersection between development and heldout sets.
  7. Contamination guard: blocks any optimization workflow from accessing heldout data.

Usage:
    python tools/verify_task_manifest.py --manifest data/development/task_manifest.json
    python tools/verify_task_manifest.py --check-separation
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ALLOWED_CATEGORIES = {
    "self-contained/local",
    "caller-callee dependency",
    "dynamic dispatch",
    "inheritance",
    "registration/factory",
    "cross-module dependency",
    "test/fixture indirection",
    "multi-file behavioral change",
    # Backward compatibility with Phase 4 development labels
    "complex transformation",
}

COMMIT_REGEX = re.compile(r"^[0-9a-fA-F]{40}$")
HASH_REGEX   = re.compile(r"^[0-9a-fA-F]{64}$")


def assert_optimization_safe(path: pathlib.Path | str) -> None:
    """Contamination guard: call before any optimization script loads tasks."""
    p_str = str(path).replace("\\", "/").lower()
    if "heldout" in p_str:
        print("\n" + "=" * 70, file=sys.stderr)
        print("ERROR: Held-out evaluation data cannot be accessed by optimization workflow.", file=sys.stderr)
        print("Contamination violation prevented by research boundary.", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        raise PermissionError("Held-out evaluation data cannot be accessed by optimization workflow.")


def validate_manifest(manifest_path: pathlib.Path, expected_partition: str | None = None) -> list[dict]:
    print(f"\n========================================================")
    print(f" Validating Task Manifest: {manifest_path}")
    print(f"========================================================")

    if not manifest_path.exists():
        print(f"[FAIL] Manifest does not exist: {manifest_path}")
        sys.exit(1)

    try:
        tasks = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] JSON parsing error: {exc}")
        sys.exit(1)

    if not isinstance(tasks, list):
        print("[FAIL] Manifest root must be a JSON array of task objects.")
        sys.exit(1)

    task_ids = set()
    task_hashes = set()
    errors = 0

    for i, t in enumerate(tasks, 1):
        tid = t.get("task_id")
        if not tid:
            print(f"  [FAIL] Task #{i} missing 'task_id'")
            errors += 1
            continue

        if tid in task_ids:
            print(f"  [FAIL] Duplicate task_id found: {tid}")
            errors += 1
        task_ids.add(tid)

        # Hash check
        thash = t.get("task_hash")
        if not thash or not HASH_REGEX.match(thash):
            print(f"  [FAIL] Task '{tid}' missing or invalid 64-char task_hash")
            errors += 1
        elif thash in task_hashes:
            print(f"  [FAIL] Duplicate task_hash found: {thash}")
            errors += 1
        else:
            task_hashes.add(thash)

        # Commit check
        commit = t.get("commit")
        if not commit or not COMMIT_REGEX.match(commit):
            print(f"  [FAIL] Task '{tid}' invalid 40-char commit SHA: {commit}")
            errors += 1

        # Category check
        cat = t.get("category")
        if cat not in ALLOWED_CATEGORIES:
            print(f"  [FAIL] Task '{tid}' invalid category: {cat}")
            errors += 1

        # Partition check
        part = t.get("development_or_heldout")
        if part not in ("development", "heldout"):
            print(f"  [FAIL] Task '{tid}' invalid partition: {part}")
            errors += 1
        elif expected_partition and part != expected_partition:
            print(f"  [FAIL] Task '{tid}' expected partition '{expected_partition}', got '{part}'")
            errors += 1

    if errors == 0:
        print(f"  [OK] Validated {len(tasks)} tasks: all unique, valid categories, consistent partitions.")
        return tasks
    else:
        print(f"  [FAIL] Manifest validation failed with {errors} error(s).")
        sys.exit(1)


def check_separation(dev_path: pathlib.Path, heldout_path: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Checking Development vs. Held-Out Dataset Non-Overlap")
    print(f"========================================================")

    if not dev_path.exists():
        print(f"[FAIL] Development manifest missing: {dev_path}")
        sys.exit(1)

    dev_tasks = json.loads(dev_path.read_text(encoding="utf-8"))
    dev_ids = {t["task_id"] for t in dev_tasks if "task_id" in t}
    dev_hashes = {t["task_hash"] for t in dev_tasks if "task_hash" in t}

    if not heldout_path.exists():
        print(f"  [NOTE] Held-out manifest does not exist yet ({heldout_path}). Status: NOT_READY.")
        print(f"  [OK] Zero contamination possible. Separation maintained.")
        return

    heldout_tasks = json.loads(heldout_path.read_text(encoding="utf-8"))
    heldout_ids = {t["task_id"] for t in heldout_tasks if "task_id" in t}
    heldout_hashes = {t["task_hash"] for t in heldout_tasks if "task_hash" in t}

    overlap_ids = dev_ids.intersection(heldout_ids)
    overlap_hashes = dev_hashes.intersection(heldout_hashes)

    if overlap_ids:
        print(f"  [FAIL] Contamination detected! Overlapping task IDs: {overlap_ids}")
        sys.exit(1)
    if overlap_hashes:
        print(f"  [FAIL] Contamination detected! Overlapping task hashes: {overlap_hashes}")
        sys.exit(1)

    print(f"  [OK] Verified zero overlap: {len(dev_ids)} dev tasks vs {len(heldout_ids)} heldout tasks.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate task manifests and separation.")
    parser.add_argument("--manifest", type=pathlib.Path, help="Path to manifest JSON file to validate")
    parser.add_argument("--partition", choices=["development", "heldout"], help="Expected partition")
    parser.add_argument("--check-separation", action="store_true", help="Check non-overlap between dev and heldout")
    args = parser.parse_args()

    root = pathlib.Path(__file__).parent.parent.resolve()

    if args.check_separation or (not args.manifest and not args.partition):
        dev = root / "data" / "development" / "task_manifest.json"
        heldout = root / "data" / "heldout" / "task_manifest.json"
        validate_manifest(dev, expected_partition="development")
        check_separation(dev, heldout)
    elif args.manifest:
        validate_manifest(args.manifest, expected_partition=args.partition)


if __name__ == "__main__":
    main()
