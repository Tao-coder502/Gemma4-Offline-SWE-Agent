# Failure Classification & Test-Driven Repair Playbook

When `pytest` or test execution fails during the repair cycle, map the error signature
to the corresponding surgical fix:

| Failure Signature | Probable Root Cause | Corrective Action |
| :--- | :--- | :--- |
| `SyntaxError`, `IndentationError` | Malformed edit string or indentation mismatch | Revert edit with `git checkout -- <file>` and re-apply with verified indentation. |
| `AttributeError: 'NoneType' object has no attribute ...` | Missing null check or missing initialization | Add defensive `if obj is not None:` guard before attribute dereference. |
| `ValueError`, `TypeError` | Invalid parameter received or wrong type passed | Verify parameter constraints and add explicit validation guard clause. |
| `DID NOT RAISE <class 'ValueError'>` | Missing guard clause / validation | Add check `if <condition>: raise ValueError(...)`. |
| `AssertionError: expected X, got Y` | Off-by-one, wrong return value, or bad branch | Re-read specification and adjust conditional expression or return value. |
| Existing tests broken (regression) | Over-editing or breaking existing API contract | Revert with `git checkout -- <file>` and switch to a more targeted minimal edit. |

## Maximum Iteration Rule
Do not iterate more than 3 repair cycles on a single hypothesis.
If 3 repair cycles fail, cleanly reset via `git checkout -- .` and evaluate the secondary hypothesis from the Diagnostic Manifesto.
