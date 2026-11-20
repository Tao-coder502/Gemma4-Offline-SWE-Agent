# Graph Traversal & Inspection Rules

When localizing defect origins across complex software repositories, follow these
deterministic traversal policies to prevent tool-call budget exhaustion:

## 1. Two-Tier Localization Priority
- **Tier 1 (Lexical Exact Search)**:
  If the issue description mentions an exact class, function, or exception name,
  query `run_command("rg -n 'def <symbol>|class <symbol>' /workspace")` first.
  Lexical search is $O(1)$ and eliminates graph search overhead when identifiers are known.

- **Tier 2 (Semantic Embedding Search)**:
  If symbol names are ambiguous, generic, or unknown, call `search_similar_code(query=..., k=10)`.
  Select the top 2–3 symbols with highest cosine similarity for graph inspection.

## 2. Confidence-Gated Neighbor Expansion
- Call `get_code_neighbors(node=..., edge_type='called_by')` to trace callers who passed faulty arguments.
- Call `get_code_neighbors(node=..., edge_type='calls')` to inspect downstream callee implementations.
- **Pruning Rule**: Never expand neighbors beyond depth 2. If depth 2 does not isolate the defect, re-evaluate the primary query.

## 3. Subgraph Extraction
- When 2–4 symbols appear in the traceback or issue discussion, call `get_code_subgraph(nodes=[...])`.
- Inspect the induced relational subgraph to understand the coupling and verify whether the bug is at the interface or the implementation level.
