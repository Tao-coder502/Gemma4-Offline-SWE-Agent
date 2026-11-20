---
name: repo_navigation
description: Deterministic graph traversal, AST localization heuristics, and patch hygiene rules for repository code reasoning.
---

# Repository Navigation & Code Comprehension Skill

This skill guides the agent in navigating large-scale unfamiliar codebases using
graph-based symbol lookups, semantic search, and surgical AST analysis.

## Core Capabilities
1. **Graph Traversal Heuristics**: Deterministic rules for querying symbol neighbors and subgraphs without combinatorial explosion.
2. **Patch Hygiene Invariants**: Strict validation rules to ensure patches apply cleanly, touch only source files, and avoid regression failures.
3. **Failure Classification**: Diagnostic mapping from test error messages to surgical code adjustments.

## Available Domain Resources
The following domain resources are available via `load_skill_resource`:
- `resources/graph_traversal_rules.md`: Confidence-gated graph inspection policies.
- `resources/patch_hygiene.md`: Invariants for clean, minimal unified diffs.
- `resources/failure_classification.md`: Error signature resolution playbook.

## Available Sandbox Scripts
The following deterministic scripts can be executed via `run_skill_script`:
- `scripts/find_symbol_definition.py`: AST-based class/function definition locator.
- `scripts/audit_diff_hygiene.py`: Pre-submission git diff auditor.
