#!/usr/bin/env python3
"""
package_submission.py — Competition submission archive packager.
================================================================
Creates submission.zip conforming to the Google Gemma 4 Developer Agent Competition.

Usage:
    python package_submission.py                  # packages Phase 3 (default)
    python package_submission.py --phase 2        # packages Phase 2 frozen baseline
    python package_submission.py --validate       # validates submission.zip
    python package_submission.py --dry-run        # preview manifest only
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path


def collect_entries(root: Path, phase: int = 3) -> list[tuple[str, Path]]:
    entries: list[tuple[str, Path]] = []

    if phase == 2:
        # Phase 2: Exact search + semantic localization (7 tools)
        agent_yaml = root / "configs" / "phase2" / "agent.yaml"
        system_md = root / "prompts" / "phase2_system.md"
        sampling_yaml = root / "configs" / "sampling.yaml"

        if not agent_yaml.exists():
            raise FileNotFoundError(f"Phase 2 agent.yaml missing: {agent_yaml}")
        if not system_md.exists():
            raise FileNotFoundError(f"Phase 2 prompt missing: {system_md}")
        if not sampling_yaml.exists():
            raise FileNotFoundError(f"Sampling config missing: {sampling_yaml}")

        entries.append(("agent.yaml", agent_yaml))
        entries.append(("prompts/system.md", system_md))
        entries.append(("configs/sampling.yaml", sampling_yaml))
        adapters_readme = root / "adapters" / "README.md"
        if adapters_readme.exists():
            entries.append(("adapters/README.md", adapters_readme))

    else:
        # Phase 3: Adaptive code-graph reasoning (9 tools)
        agent_yaml = root / "agent.yaml"
        system_md = root / "prompts" / "system.md"
        sampling_yaml = root / "configs" / "sampling.yaml"

        if not agent_yaml.exists():
            raise FileNotFoundError(f"agent.yaml missing: {agent_yaml}")
        if not system_md.exists():
            raise FileNotFoundError(f"prompts/system.md missing: {system_md}")
        if not sampling_yaml.exists():
            raise FileNotFoundError(f"configs/sampling.yaml missing: {sampling_yaml}")

        entries.append(("agent.yaml", agent_yaml))
        entries.append(("prompts/system.md", system_md))
        entries.append(("configs/sampling.yaml", sampling_yaml))
        adapters_readme = root / "adapters" / "README.md"
        if adapters_readme.exists():
            entries.append(("adapters/README.md", adapters_readme))

    return entries


def build_zip(root: Path, output_file: str = "submission.zip", phase: int = 3, dry_run: bool = False) -> None:
    entries = collect_entries(root, phase=phase)

    print(f"-- Submission Manifest (Phase {phase}) -------------------------------")
    for arc, src in entries:
        print(f"  {arc:<24} <- {src.relative_to(root)}")
    print("---------------------------------------------------------")

    if dry_run:
        print("[dry-run] Skipping zip creation.")
        return

    out = root / output_file
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, fp in entries:
            zf.write(fp, arc)
            print(f"  added: {arc}")

    size_kb = out.stat().st_size / 1024
    print(f"\n[OK] Created {output_file} ({size_kb:.1f} KB)")
    print(f"  Path: {out}")


def validate_zip(root: Path, output_file: str = "submission.zip") -> None:
    out = root / output_file
    if not out.exists():
        print(f"[FAIL] {output_file} does not exist.")
        sys.exit(1)

    with zipfile.ZipFile(out, "r") as zf:
        names = zf.namelist()
        print(f"\nValidating {output_file}:")
        for n in names:
            print(f"  - {n}")

        if "agent.yaml" not in names:
            print("\n[FAIL] 'agent.yaml' is MISSING from root of zip.")
            sys.exit(1)
        if "prompts/system.md" not in names:
            print("\n[FAIL] 'prompts/system.md' is MISSING from zip.")
            sys.exit(1)
        if "configs/sampling.yaml" not in names:
            print("\n[FAIL] 'configs/sampling.yaml' is MISSING from zip.")
            sys.exit(1)

        # Ensure no developer tools leaked into zip
        for n in names:
            if n.startswith(("tools/", "docs/", "results/", "data/", "validate_")):
                print(f"\n[FAIL] Developer file leaked into zip: {n}")
                sys.exit(1)

        print("\n[OK] Validation passed: submission.zip satisfies all competition archive rules.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Package competition submission.")
    parser.add_argument("--phase", type=int, choices=[2, 3], default=3,
                        help="Phase to package (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print manifest without creating zip.")
    parser.add_argument("--validate", action="store_true",
                        help="Validate existing submission.zip.")
    parser.add_argument("--output", default="submission.zip",
                        help="Output zip filename (default: submission.zip).")
    args = parser.parse_args()

    root = Path(__file__).parent.resolve()

    if args.validate:
        validate_zip(root, output_file=args.output)
    else:
        build_zip(root, output_file=args.output, phase=args.phase, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
