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


def collect_entries(root: Path, phase: int = 5) -> list[tuple[str, Path]]:
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

    elif phase == 3:
        # Phase 3: Adaptive code-graph reasoning (9 tools)
        agent_yaml = root / "configs" / "phase3" / "agent.yaml" if (root / "configs" / "phase3" / "agent.yaml").exists() else root / "agent.yaml"
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

    elif phase == 5:
        # Phase 5 (Final Production): v5.0 Optimized Agent
        agent_yaml = root / "configs" / "phase5" / "v5_0_final" / "agent.yaml"
        system_md = root / "prompts" / "system_v5_optimized.md"
        sampling_yaml = root / "configs" / "phase5" / "v5_0_final" / "sampling.yaml"

        if not agent_yaml.exists():
            raise FileNotFoundError(f"Phase 5 agent.yaml missing: {agent_yaml}")
        if not system_md.exists():
            raise FileNotFoundError(f"Phase 5 prompt missing: {system_md}")
        if not sampling_yaml.exists():
            raise FileNotFoundError(f"Sampling config missing: {sampling_yaml}")

        entries.append(("agent.yaml", agent_yaml))
        entries.append(("prompts/system.md", system_md))
        entries.append(("configs/sampling.yaml", sampling_yaml))
        adapters_readme = root / "adapters" / "README.md"
        if adapters_readme.exists():
            entries.append(("adapters/README.md", adapters_readme))
        eval_config = root / "eval_config.yaml"
        if eval_config.exists():
            entries.append(("eval_config.yaml", eval_config))

    else:
        # Phase 4: Mode D — Adaptive graph + structured patch planning + test-driven repair
        agent_yaml = root / "configs" / "phase4" / "mode_d" / "agent.yaml"
        system_md = root / "prompts" / "system_mode_d.md"
        sampling_yaml = root / "configs" / "sampling.yaml"

        if not agent_yaml.exists():
            raise FileNotFoundError(f"Phase 4 Mode D agent.yaml missing: {agent_yaml}")
        if not system_md.exists():
            raise FileNotFoundError(f"Phase 4 Mode D prompt missing: {system_md}")
        if not sampling_yaml.exists():
            raise FileNotFoundError(f"Sampling config missing: {sampling_yaml}")

        entries.append(("agent.yaml", agent_yaml))
        entries.append(("prompts/system.md", system_md))
        entries.append(("configs/sampling.yaml", sampling_yaml))
        adapters_readme = root / "adapters" / "README.md"
        if adapters_readme.exists():
            entries.append(("adapters/README.md", adapters_readme))

    return entries


def build_zip(root: Path, output_file: str = "submission.zip", phase: int = 5, dry_run: bool = False) -> None:
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
            if arc == "agent.yaml" and phase in (4, 5):
                content = fp.read_text(encoding="utf-8").replace("\r\n", "\n")
                content = content.replace("prompts/system_mode_d.md", "prompts/system.md")
                content = content.replace("prompts/system_v5_optimized.md", "prompts/system.md")
                content = content.replace("configs/phase5/v5_0_final/sampling.yaml", "configs/sampling.yaml")
                zf.writestr("agent.yaml", content)
                print(f"  added: {arc} (with prompts/system.md include)")
            else:
                try:
                    content = fp.read_text(encoding="utf-8").replace("\r\n", "\n")
                    zf.writestr(arc, content)
                except UnicodeDecodeError:
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
    parser.add_argument("--phase", type=int, choices=[2, 3, 4, 5], default=5,
                        help="Phase to package (default: 5)")
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
