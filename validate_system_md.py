"""
validate_system_md.py — Multi-Phase prompts/system.md correctness checker.

Validates:
  - Phase 2 frozen baseline prompt (prompts/phase2_system.md: 7 tools, graph tools prohibited)
  - Phase 3 full graph prompt (prompts/system.md: 9 tools, adaptive graph policy)

Usage:
    python validate_system_md.py             # Validates both prompts
    python validate_system_md.py --phase 2   # Validates Phase 2 prompt only
    python validate_system_md.py --phase 3   # Validates Phase 3 prompt only
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

root = pathlib.Path(__file__).parent.resolve()
errors = 0
warnings = 0


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def fail(msg: str) -> None:
    global errors
    errors += 1
    print(f"  [FAIL] {msg}")


def warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"  [WARN] {msg}")


def validate_phase2_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Phase 2 Prompt: {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    text_lower = text.lower()

    # 1. Graph tools prohibited
    for tool in ("get_code_neighbors", "get_code_subgraph"):
        matches = [(i + 1, l.strip()) for i, l in enumerate(lines) if tool in l]
        if not matches:
            ok(f"'{tool}' does not appear in file")
        else:
            all_negated = True
            for lineno, content in matches:
                negation_words = ("not", "cannot", "do not", "don't", "avoid", "must not", "unavailable", "not available")
                if not any(w in content.lower() for w in negation_words):
                    all_negated = False
                    fail(f"'{tool}' appears as an instruction on line {lineno}: {content}")
            if all_negated:
                ok(f"'{tool}' correctly restricted to negation/prohibition context")

    # 2. Required 7 tools
    core_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code"
    ]
    for tool in core_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Phase 2 prompt")

    # 3. Offline constraint
    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    # 4. Chain-of-thought exposure check
    cot_mandate = re.search(r"(write|output|print|expose|show|state|say|express|declare)\s+(your\s+)?(reason|thinking|chain.of.thought|internal|cot)", text_lower)
    if cot_mandate:
        warn(f"Possible CoT mandate: {cot_mandate.group()}")
    else:
        ok("No mandatory CoT exposure")

    # 5. submit_patch finality
    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_phase3_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Phase 3 Prompt: {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    # 1. All 9 tools must be present
    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Phase 3 prompt")

    # 2. Adaptive policy check
    if "if semantic evidence is sufficient" in text_lower:
        ok("Adaptive policy: high-confidence bypass defined")
    else:
        fail("Adaptive policy: high-confidence bypass MISSING")

    if any(k in text_lower for k in ("else", "optional adaptive graph expansion")):
        ok("Adaptive policy: conditional graph expansion defined")
    else:
        fail("Adaptive policy: conditional graph expansion MISSING")

    if any(k in text_lower for k in ("callers", "callees", "dependencies")):
        ok("Graph reasoning target scopes defined (callers/callees/dependencies)")
    else:
        fail("Graph reasoning target scopes MISSING")

    # 3. Offline constraint
    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    # 4. Chain-of-thought exposure check
    cot_mandate = re.search(r"(write|output|print|expose|show|state|say|express|declare)\s+(your\s+)?(reason|thinking|chain.of.thought|internal|cot)", text_lower)
    if cot_mandate:
        warn(f"Possible CoT mandate: {cot_mandate.group()}")
    else:
        ok("No mandatory CoT exposure")

    # 5. submit_patch finality
    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_mode_b_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Mode B Prompt (Mandatory Graph): {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Mode B prompt")

    if any(k in text_lower for k in ("mandatory", "unconditionally", "unconditional")):
        ok("Mandatory graph policy stated")
    else:
        warn("Explicit mandatory graph terminology not found")

    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_mode_d_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Mode D Prompt (Structured State + TDR): {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Mode D prompt")

    # Structured Internal State check
    if "internal state" in text_lower and "patch plan" in text_lower and "confidence" in text_lower:
        ok("Structured internal state tracking defined")
    else:
        fail("Structured internal state tracking MISSING")

    # Failure taxonomy & TDR loop check
    if any(k in text_lower for k in ("patch_defect", "repair", "pre_existing")):
        ok("Test-driven repair and failure classification defined")
    else:
        fail("Test-driven repair and failure classification MISSING")

    # Adaptive policy check
    if "confidence = high" in text_lower or "if confidence" in text_lower:
        ok("Adaptive graph decision policy defined")
    else:
        fail("Adaptive graph decision policy MISSING")

    # Offline check
    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    # submit_patch finality
    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_mode_c1_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Mode C1 Prompt (Adaptive + Structured State): {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Mode C1 prompt")

    if "internal state" in text_lower and "patch plan" in text_lower:
        ok("Structured internal state tracking defined")
    else:
        fail("Structured internal state tracking MISSING")

    if any(k in text_lower for k in ("adaptive", "optional adaptive graph expansion")):
        ok("Adaptive graph decision policy defined")
    else:
        fail("Adaptive graph decision policy MISSING")

    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_mode_c2_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Mode C2 Prompt (Adaptive + TDR): {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from Mode C2 prompt")

    if any(k in text_lower for k in ("test-driven repair", "repair loop", "patch_defect")):
        ok("Test-driven repair loop defined")
    else:
        fail("Test-driven repair loop MISSING")

    if any(k in text_lower for k in ("adaptive", "optional adaptive graph expansion")):
        ok("Adaptive graph decision policy defined")
    else:
        fail("Adaptive graph decision policy MISSING")

    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def validate_v5_prompt(p: pathlib.Path) -> None:
    print(f"\n========================================================")
    print(f" Validating Phase 5 / v5.0 Optimized Prompt: {p.relative_to(root)}")
    print(f"========================================================")

    if not p.exists():
        fail(f"Prompt file missing: {p}")
        return

    text = p.read_text(encoding="utf-8")
    text_lower = text.lower()

    all_9_tools = [
        "run_command", "read_file", "edit_file", "write_file",
        "get_status", "submit_patch", "search_similar_code",
        "get_code_neighbors", "get_code_subgraph"
    ]
    for tool in all_9_tools:
        if tool in text:
            ok(f"'{tool}' referenced")
        else:
            fail(f"'{tool}' MISSING from v5.0 prompt")

    if "internal state" in text_lower and "patch plan" in text_lower:
        ok("Structured internal state tracking defined")
    else:
        fail("Structured internal state tracking MISSING")

    if any(k in text_lower for k in ("adaptive", "optional adaptive graph expansion", "gating policy")):
        ok("Adaptive graph decision policy defined")
    else:
        fail("Adaptive graph decision policy MISSING")

    if any(k in text_lower for k in ("test-driven repair", "repair", "patch_defect")):
        ok("Test-driven repair loop defined")
    else:
        fail("Test-driven repair loop MISSING")

    if any(k in text_lower for k in ("stopping", "early stop", "terminal action")):
        ok("Early stopping policy defined")
    else:
        fail("Early stopping policy MISSING")

    if any(s in text_lower for s in ("offline", "air-gapped", "external api")):
        ok("Offline constraint stated")
    else:
        fail("Offline constraint MISSING")

    if "submit_patch" in text_lower and any(w in text_lower for w in ("final", "last", "exactly once", "terminal")):
        ok("submit_patch framed as final action")
    else:
        fail("submit_patch not framed as final action")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate system prompt markdown files.")
    parser.add_argument("--phase", type=int, choices=[2, 3, 4, 5], help="Specific phase prompt to validate")
    args = parser.parse_args()

    if args.phase == 2:
        validate_phase2_prompt(root / "prompts" / "phase2_system.md")
    elif args.phase == 3:
        validate_phase3_prompt(root / "prompts" / "system.md")
    elif args.phase == 4:
        validate_phase2_prompt(root / "prompts" / "system_mode_a.md")
        validate_mode_b_prompt(root / "prompts" / "system_mode_b.md")
        validate_phase3_prompt(root / "prompts" / "system.md")
        validate_mode_c1_prompt(root / "prompts" / "system_mode_c1.md")
        validate_mode_c2_prompt(root / "prompts" / "system_mode_c2.md")
        validate_mode_d_prompt(root / "prompts" / "system_mode_d.md")
    elif args.phase == 5:
        validate_v5_prompt(root / "prompts" / "system_v5_optimized.md")
    else:
        validate_phase2_prompt(root / "prompts" / "phase2_system.md")
        validate_phase3_prompt(root / "prompts" / "system.md")
        validate_phase2_prompt(root / "prompts" / "system_mode_a.md")
        validate_mode_b_prompt(root / "prompts" / "system_mode_b.md")
        validate_mode_c1_prompt(root / "prompts" / "system_mode_c1.md")
        validate_mode_c2_prompt(root / "prompts" / "system_mode_c2.md")
        validate_mode_d_prompt(root / "prompts" / "system_mode_d.md")
        validate_v5_prompt(root / "prompts" / "system_v5_optimized.md")

    print()
    if errors == 0 and warnings == 0:
        print("Result: ALL PROMPT FILES PASSED VALIDATION.")
        sys.exit(0)
    elif errors == 0:
        print(f"Result: PASSED with {warnings} warning(s).")
        sys.exit(0)
    else:
        print(f"Result: {errors} FAILURE(S), {warnings} warning(s).")
        sys.exit(1)


if __name__ == "__main__":
    main()
