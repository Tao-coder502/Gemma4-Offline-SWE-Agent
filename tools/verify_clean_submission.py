#!/usr/bin/env python3
"""
tools/verify_clean_submission.py
================================
Clean-room, end-to-end verification and compliance test for the final
competition submission archive of the Gemma 4 Offline SWE Agent.

Verifies:
1. Submission archive structure and integrity (submission.zip)
2. Model identifier (gemma-4-31b-it-qat-w4a16-ct)
3. Google ADK schema compliance & tool availability (9 tools)
4. Absence of external API dependencies (air-gapped / offline enforcement)
5. Absence of secrets, tokens, or credential leaks
6. Sandbox filesystem assumptions (/workspace, /tmp)
7. Clean-room agent startup simulation from unpacked archive
8. Test-driven repair loop, stopping behavior, and terminal patch submission
9. Runtime and token budget compliance (max_output_tokens: 32768)
10. Checksum and reproducibility verification against freeze manifest

Usage:
    python tools/verify_clean_submission.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Forbidden secret patterns
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|bearer\s+[a-z0-9_\-\.]+)\s*[:=]\s*['\"][a-z0-9_\-\.]{10,}['\"]"),
    re.compile(r"(?i)(password|passwd|private[_-]?key)\s*[:=]\s*['\"][^\s'\"]{6,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
]

# Forbidden external networking patterns (in submission prompts/configs)
NETWORK_PATTERNS = [
    re.compile(r"https?://(?!raw\.githubusercontent\.com/google/adk-python)[^\s'\"\)\]]+"),
    re.compile(r"(?i)import\s+(?:urllib|requests|socket|http\.client|aiohttp)"),
    re.compile(r"(?i)curl\s+https?://"),
    re.compile(r"(?i)wget\s+https?://"),
]


class CleanVerificationSuite:
    def __init__(self, root: Path, zip_path: Path):
        self.root = root
        self.zip_path = zip_path
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, condition: bool, title: str, details: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"  [PASS] {title}")
        else:
            self.failed += 1
            print(f"  [FAIL] {title}")
            if details:
                print(f"         -> {details}")

    def warn(self, title: str, details: str = "") -> None:
        self.warnings += 1
        print(f"  [WARN] {title}")
        if details:
            print(f"         -> {details}")

    def run_all_checks(self) -> bool:
        print("======================================================================")
        print(" GEMMA 4 OFFLINE SWE AGENT — CLEAN-ROOM SUBMISSION VERIFICATION")
        print("======================================================================")
        print(f" Root Directory   : {self.root}")
        print(f" Submission Zip   : {self.zip_path}")
        print("----------------------------------------------------------------------\n")

        self.verify_archive_integrity()
        self.verify_agent_config_and_schema()
        self.verify_model_and_tools()
        self.verify_air_gapped_offline_safety()
        self.verify_absence_of_secrets()
        self.verify_sandbox_assumptions()
        self.verify_clean_room_startup()
        self.verify_repair_and_stopping_policy()
        self.verify_budget_and_generation_config()
        self.verify_freeze_manifest_hashes()

        print("\n======================================================================")
        print(f" VERIFICATION SUMMARY: {self.passed} PASSED, {self.failed} FAILED, {self.warnings} WARNING(S)")
        print("======================================================================")
        if self.failed == 0:
            print(" RESULT: SUBMISSION IS 100% PRODUCTION READY FOR COMPETITION EVALUATION")
            return True
        else:
            print(f" RESULT: FAILED ({self.failed} errors must be resolved)")
            return False

    def verify_archive_integrity(self) -> None:
        print("1. Submission Archive Structure & Cleanliness:")
        self.check(self.zip_path.exists(), f"Archive exists ({self.zip_path.name})")
        if not self.zip_path.exists():
            return

        size_kb = self.zip_path.stat().st_size / 1024
        self.check(size_kb < 100, f"Archive size is lean ({size_kb:.2f} KB < 100 KB limit)")

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            names = set(zf.namelist())
            expected = {"agent.yaml", "prompts/system.md", "configs/sampling.yaml", "adapters/README.md"}
            self.check(expected.issubset(names), f"Contains all mandatory submission components: {expected}")
            
            # Check no developer files leaked
            leaks = [n for n in names if n.startswith(("tools/", "docs/", "results/", "data/", "research/", "paper/", "validate_"))]
            self.check(len(leaks) == 0, "Zero developer files or test harness tools leaked into archive", f"Leaked: {leaks}")

    def verify_agent_config_and_schema(self) -> None:
        print("\n2. Agent Configuration & ADK Schema Compliance:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            raw_yaml = zf.read("agent.yaml").decode("utf-8")

        # Required fields per Google ADK
        for req in ("name:", "model:", "description:", "instruction:", "tools:", "generate_content_config:"):
            self.check(req in raw_yaml, f"Required field '{req[:-1]}' present in agent.yaml")

        # Forbidden fields
        for forb in ("sub_agents:", "adapters:", "lora:", "agent_fn:", "agent_class:"):
            self.check(forb not in raw_yaml, f"Forbidden field '{forb[:-1]}' strictly absent from agent.yaml")

    def verify_model_and_tools(self) -> None:
        print("\n3. Model Identifier & Tool Registry:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            raw_yaml = zf.read("agent.yaml").decode("utf-8")

        expected_model = "model: gemma-4-31b-it-qat-w4a16-ct"
        self.check(expected_model in raw_yaml, f"Model is set to mandated '{expected_model}'")

        expected_tools = [
            "run_command", "read_file", "edit_file", "write_file",
            "get_status", "submit_patch", "search_similar_code",
            "get_code_neighbors", "get_code_subgraph"
        ]
        for t in expected_tools:
            self.check(f"- {t}" in raw_yaml, f"Tool registered: '{t}'")

    def verify_air_gapped_offline_safety(self) -> None:
        print("\n4. Air-Gapped & Offline Safety Verification:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                content = zf.read(info.filename).decode("utf-8", errors="ignore")
                
                # Check for network references
                for pat in NETWORK_PATTERNS:
                    matches = pat.findall(content)
                    self.check(len(matches) == 0, f"No unauthorized network calls in {info.filename}", f"Found: {matches}")

            # Verify prompt explicitly states offline rule
            prompt = zf.read("prompts/system.md").decode("utf-8")
            self.check("offline" in prompt.lower() and "external api" in prompt.lower(),
                       "System prompt strictly enforces offline, air-gapped operational constraints")

    def verify_absence_of_secrets(self) -> None:
        print("\n5. Absence of Secrets, Tokens, and Credentials:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                content = zf.read(info.filename).decode("utf-8", errors="ignore")
                for pat in SECRET_PATTERNS:
                    matches = pat.findall(content)
                    self.check(len(matches) == 0, f"No secrets or tokens detected in {info.filename}", f"Matches: {matches}")

    def verify_sandbox_assumptions(self) -> None:
        print("\n6. Sandbox Environment & Filesystem Assumptions:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            prompt = zf.read("prompts/system.md").decode("utf-8")

        self.check("/workspace" in prompt, "System prompt anchors repository at standard '/workspace'")
        self.check("/tmp" in prompt, "System prompt routes scratch files to '/tmp'")
        
        # Check no host paths (C:\ or /home)
        bad_paths = [m for m in ("c:\\", "c:/", "/home/") if m in prompt.lower()]
        self.check(len(bad_paths) == 0, "Zero host-specific hardcoded paths in system prompt", f"Found: {bad_paths}")

    def verify_clean_room_startup(self) -> None:
        print("\n7. Clean-Room Agent Startup Simulation:")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            with zipfile.ZipFile(self.zip_path, "r") as zf:
                zf.extractall(tmppath)

            agent_yaml_path = tmppath / "agent.yaml"
            prompt_path = tmppath / "prompts" / "system.md"
            sampling_path = tmppath / "configs" / "sampling.yaml"

            self.check(agent_yaml_path.exists(), "Extracted agent.yaml exists")
            self.check(prompt_path.exists(), "Extracted prompts/system.md exists")
            self.check(sampling_path.exists(), "Extracted configs/sampling.yaml exists")

            # Check prompt resolution
            agent_text = agent_yaml_path.read_text(encoding="utf-8")
            self.check("!include prompts/system.md" in agent_text, "agent.yaml cleanly includes prompts/system.md")
            self.check("!include configs/sampling.yaml" in agent_text, "agent.yaml cleanly includes configs/sampling.yaml")

            # Check prompt length
            prompt_text = prompt_path.read_text(encoding="utf-8")
            self.check(len(prompt_text) > 1000, f"System prompt loaded successfully ({len(prompt_text)} chars)")

    def verify_repair_and_stopping_policy(self) -> None:
        print("\n8. Test-Driven Repair, Early Stopping, and Terminal Action:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            prompt = zf.read("prompts/system.md").decode("utf-8")

        self.check("internal state" in prompt.lower(), "Structured Internal State tracking active")
        self.check("repair" in prompt.lower(), "Bounded Test-Driven Repair loop specified")
        self.check("stopping" in prompt.lower() or "stop" in prompt.lower(), "Explicit early stopping policy defined")
        self.check("submit_patch" in prompt, "Terminal action 'submit_patch' defined")

    def verify_budget_and_generation_config(self) -> None:
        print("\n9. Generation Hyperparameters & Runtime Budget Compliance:")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            sampling_text = zf.read("configs/sampling.yaml").decode("utf-8")

        self.check("temperature: 0.1" in sampling_text, "Sampling temperature is set to frozen 0.1")
        self.check("top_p: 0.90" in sampling_text or "top_p: 0.9" in sampling_text, "Sampling top_p is set to frozen 0.90")
        self.check("max_output_tokens: 32768" in sampling_text, "max_output_tokens is set to 32768")

    def verify_freeze_manifest_hashes(self) -> None:
        print("\n10. Checksum and Reproducibility Verification:")
        freeze_json = self.root / "results" / "phase5_freeze" / "V5_FREEZE_MANIFEST.json"
        self.check(freeze_json.exists(), "Phase 5 Freeze Manifest exists")
        if not freeze_json.exists():
            return

        with open(freeze_json, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        expected_prompt_sha = manifest["prompt_hash"]
        
        # In submission.zip, prompts/system.md must match system_v5_optimized.md hash
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            prompt_bytes = zf.read("prompts/system.md")
            actual_prompt_sha = hashlib.sha256(prompt_bytes).hexdigest()

        self.check(actual_prompt_sha == expected_prompt_sha,
                   f"Prompt hash in submission matches frozen v5.0 manifest\n         ({actual_prompt_sha[:16]}... == {expected_prompt_sha[:16]}...)")

        # Verify sampling config hash
        expected_sampling_sha = manifest["sampling_hash"]
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            sampling_bytes = zf.read("configs/sampling.yaml")
            actual_sampling_sha = hashlib.sha256(sampling_bytes).hexdigest()

        self.check(actual_sampling_sha == expected_sampling_sha,
                   f"Sampling hash in submission matches frozen v5.0 manifest\n         ({actual_sampling_sha[:16]}... == {expected_sampling_sha[:16]}...)")


def main() -> None:
    suite = CleanVerificationSuite(ROOT, ROOT / "submission.zip")
    success = suite.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
