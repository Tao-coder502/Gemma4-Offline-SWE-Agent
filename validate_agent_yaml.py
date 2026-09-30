"""
validate_agent_yaml.py — Multi-Phase agent.yaml correctness validator.

Validates:
  - Phase 2 frozen baseline configuration (configs/phase2/agent.yaml: exactly 7 tools)
  - Phase 3 full graph configuration (configs/phase3/agent.yaml: exactly 9 tools)
  - Root competition entry point (agent.yaml: Phase 3 9-tool configuration)

Usage:
    python validate_agent_yaml.py             # Validates all configs
    python validate_agent_yaml.py --phase 2   # Validates Phase 2 only
    python validate_agent_yaml.py --phase 3   # Validates Phase 3 only
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import yaml

root = pathlib.Path(__file__).parent.resolve()
errors = 0


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def fail(msg: str) -> None:
    global errors
    errors += 1
    print(f"  [FAIL] {msg}")


def validate_config(yaml_path: pathlib.Path, expected_phase: int) -> None:
    print(f"\n========================================================")
    print(f" Validating: {yaml_path.relative_to(root)} (Phase {expected_phase})")
    print(f"========================================================")

    if not yaml_path.exists():
        fail(f"Configuration file does not exist: {yaml_path}")
        return

    # 1. YAML syntax parsing
    try:
        raw = yaml_path.read_text(encoding="utf-8")
        # Replace !include directives with dummy strings for safe PyYAML loading
        import re
        safe = re.sub(r"!include\s+\S+", '"__include_placeholder__"', raw)
        data = yaml.safe_load(safe)
        ok("Parses as valid YAML")
    except Exception as e:
        fail(f"YAML parse error: {e}")
        return

    # 2. Required fields
    for field in ("name", "model", "description", "instruction", "tools", "generate_content_config"):
        if field in data:
            ok(f"Required field '{field}' present")
        else:
            fail(f"Required field '{field}' MISSING")

    # 3. Model identifier
    model = data.get("model", "")
    expected_model = "gemma-4-31b-it-qat-w4a16-ct"
    if model == expected_model:
        ok(f"model = '{model}'")
    else:
        fail(f"model = '{model}' (expected '{expected_model}')")

    # 4. Tool Registry Audit
    tools = data.get("tools", [])
    core_tools = [
        "run_command",
        "read_file",
        "edit_file",
        "write_file",
        "get_status",
        "submit_patch",
        "search_similar_code",
    ]
    graph_tools = [
        "get_code_neighbors",
        "get_code_subgraph",
    ]

    for t in core_tools:
        if t in tools:
            ok(f"Core tool '{t}' present")
        else:
            fail(f"Core tool '{t}' MISSING")

    if expected_phase == 2 or (expected_phase == 4 and "mode_a" in str(yaml_path)):
        # Semantic only: Graph tools MUST be absent
        for t in graph_tools:
            if t not in tools:
                ok(f"Graph tool '{t}' correctly absent")
            else:
                fail(f"Graph tool '{t}' MUST NOT be present")
        if len(tools) == 7:
            ok("Tool count = 7 (semantic-only suite)")
        else:
            fail(f"Tool count = {len(tools)} (expected exactly 7)")

    else:
        # Full graph suite: Graph tools MUST be present
        for t in graph_tools:
            if t in tools:
                ok(f"Graph tool '{t}' present")
            else:
                fail(f"Graph tool '{t}' MISSING")
        if len(tools) == 9:
            ok("Tool count = 9 (full repository reasoning suite)")
        else:
            fail(f"Tool count = {len(tools)} (expected exactly 9)")

    # 5. Unsupported / Forbidden fields
    unsupported = ("sub_agents", "adapters", "lora", "agent_fn", "agent_class")
    for field in unsupported:
        if field not in data:
            ok(f"Forbidden field '{field}' absent")
        else:
            fail(f"Forbidden field '{field}' should NOT be in agent config")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate agent YAML configurations.")
    parser.add_argument("--phase", type=int, choices=[2, 3, 4], help="Specific phase to validate")
    args = parser.parse_args()

    phase4_configs = [
        root / "configs" / "phase4" / "mode_a" / "agent.yaml",
        root / "configs" / "phase4" / "mode_b" / "agent.yaml",
        root / "configs" / "phase4" / "mode_c" / "agent.yaml",
        root / "configs" / "phase4" / "mode_d" / "agent.yaml",
    ]

    if args.phase == 2:
        validate_config(root / "configs" / "phase2" / "agent.yaml", 2)
    elif args.phase == 3:
        validate_config(root / "configs" / "phase3" / "agent.yaml", 3)
        validate_config(root / "agent.yaml", 3)
    elif args.phase == 4:
        for cfg in phase4_configs:
            validate_config(cfg, 4)
    else:
        # Validate all configurations
        validate_config(root / "configs" / "phase2" / "agent.yaml", 2)
        validate_config(root / "configs" / "phase3" / "agent.yaml", 3)
        validate_config(root / "agent.yaml", 3)
        for cfg in phase4_configs:
            validate_config(cfg, 4)

    print()
    if errors == 0:
        print("Result: ALL CONFIGURATIONS PASSED VALIDATION.")
        sys.exit(0)
    else:
        print(f"Result: {errors} CHECK(S) FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
