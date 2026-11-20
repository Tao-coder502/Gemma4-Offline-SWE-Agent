# Patch Hygiene & Minimality Invariants

To achieve high PASS% scores in SWE-bench and competition evaluation, generated diffs
must satisfy strict hygiene invariants:

## 1. Zero Modification to Test Files
- **Mandatory Invariant**: NEVER edit or commit files in `tests/`, `test/`, or matching `test_*.py`.
- In SWE-bench evaluation, the test suite is used to validate the patch. Modifying the validation tests themselves can cause immediate test failure, evaluation masking, or disqualification.
- If you write a temporary reproduction script, write it to `/tmp/reproduce_issue.py` via `run_command` — never into `/workspace`.

## 2. Surgical Minimality
- Keep edits strictly focused on the root cause logic.
- Target diff size: $<25$ lines modified.
- Avoid modifying comments, docstrings, typing imports, or formatting unless explicitly required by the issue.
- Never reformat adjacent code or clean up whitespace in untouched functions.

## 3. Formatting & Line Ending Integrity
- Retain the exact indentation style of the surrounding file (4 spaces, 2 spaces, or tabs).
- Use standard Unix LF (`\n`) line endings.
- When replacing strings via `edit_file`, ensure the `old_string` includes enough surrounding context (2–3 lines) to be unique in the file.
