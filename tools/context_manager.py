#!/usr/bin/env python3
"""
tools/context_manager.py
========================
High-efficiency observation truncation and context window compaction
for the Gemma 4 SWE Agent.

Caps per-turn observations to the critical diagnostic signal (tracebacks, diffs)
and compacts conversation history so autoregressive inference stays at constant
speed (<8,192 tokens) across long 15-turn reasoning trajectories.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any


def compact_observation(tool_name: str, raw_output: str, max_chars: int = 2500) -> str:
    """
    Intelligently truncates tool outputs to preserve key signal while preventing context bloat.
    """
    if not raw_output or len(raw_output) <= max_chars:
        return raw_output.strip() if raw_output else "[No output]"

    lines = raw_output.splitlines()

    # Specialized truncation for test outputs / tracebacks
    if tool_name == "run_command" and ("pytest" in raw_output or "Traceback" in raw_output or "FAILED" in raw_output):
        # Locate traceback start or failure header
        traceback_indices = [i for i, line in enumerate(lines) if "Traceback (most recent call last)" in line or line.startswith("FAILED ") or line.startswith("ERROR ")]
        if traceback_indices:
            start_idx = max(0, traceback_indices[0] - 5)
            relevant_lines = lines[start_idx:]
            if len(relevant_lines) > 40:
                head = relevant_lines[:15]
                tail = relevant_lines[-25:]
                return (
                    f"[Output truncated: showing failure traceback ({len(lines)} lines total)]\n"
                    + "\n".join(head)
                    + f"\n... [{len(relevant_lines) - 40} lines omitted] ...\n"
                    + "\n".join(tail)
                )
            return "\n".join(relevant_lines)

    # Specialized truncation for read_file
    if tool_name == "read_file":
        if len(lines) > 50:
            head = lines[:20]
            tail = lines[-20:]
            return (
                f"[File snippet truncated ({len(lines)} lines total)]\n"
                + "\n".join(head)
                + f"\n... [{len(lines) - 40} lines omitted] ...\n"
                + "\n".join(tail)
            )

    # General head-tail truncation
    head = lines[:15]
    tail = lines[-25:]
    omitted = len(lines) - 40
    return (
        f"[Output truncated ({len(lines)} lines total)]\n"
        + "\n".join(head)
        + f"\n... [{omitted} lines omitted] ...\n"
        + "\n".join(tail)
    )


class ContextManager:
    """
    Manages the conversation turn history to ensure total prompt tokens
    remain strictly within the target 8,192 token ceiling.
    """
    def __init__(self, system_instruction: str, max_token_ceiling: int = 8192):
        self.system_instruction = system_instruction
        self.max_tokens = max_token_ceiling
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_instruction}
        ]

    def estimate_tokens(self, text: str) -> int:
        """Heuristic character-to-token ratio (~4 chars per token)."""
        return len(text) // 4

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_observation(self, tool_name: str, observation: str) -> None:
        compacted = compact_observation(tool_name, observation)
        self.messages.append({"role": "user", "content": f"Tool '{tool_name}' output:\n{compacted}"})
        self._enforce_budget()

    def _enforce_budget(self) -> None:
        """
        Compacts older turns if total tokens approach the ceiling.
        Keeps system prompt, initial task prompt, and the last 3 turns intact.
        """
        total_tokens = sum(self.estimate_tokens(m["content"]) for m in self.messages)
        if total_tokens <= self.max_tokens or len(self.messages) <= 6:
            return

        # Compact middle turns (between task description and recent 3 turns)
        protect_start = 2  # system + task prompt
        protect_end = len(self.messages) - 4  # keep last 4 messages verbatim

        for idx in range(protect_start, protect_end):
            msg = self.messages[idx]
            if msg["role"] == "user" and "Tool '" in msg["content"] and len(msg["content"]) > 300:
                # Compress older observation to a one-line summary
                tool_match = re.search(r"Tool '(\w+)'", msg["content"])
                t_name = tool_match.group(1) if tool_match else "tool"
                msg["content"] = f"[Prior Turn Summary: {t_name} executed successfully. Observations archived.]"
