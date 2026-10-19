"""
tests/test_code_graph.py
========================
Validates in-memory SQLite AST code graph indexing, symbol lookups,
and caller/callee neighbor queries.
"""

import tempfile
from pathlib import Path
from tools.code_graph_index import SQLiteCodeGraph


def test_code_graph_symbol_and_call_indexing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws = Path(tmp_dir)
        
        # Create dummy python files
        foo_py = ws / "foo.py"
        foo_py.write_text("""
def helper_func():
    return 42

def caller_func():
    return helper_func()
""", encoding="utf-8")

        bar_py = ws / "bar.py"
        bar_py.write_text("""
from foo import helper_func

class Service:
    def execute(self):
        return helper_func()
""", encoding="utf-8")

        graph = SQLiteCodeGraph(workspace=ws)
        graph.build_index()

        # 1. Query definition of a class without calls
        res_def = graph.query_neighbors(symbol="Service", direction="both")
        assert "defines class Service" in res_def
        assert "bar.py" in res_def

        # 2. Query incoming calls to helper_func
        res_calls = graph.query_neighbors(symbol="helper_func", direction="incoming")
        assert "calls helper_func" in res_calls

        # 3. Query subgraph
        subgraph = graph.query_subgraph(symbol="helper_func", max_depth=1)
        assert "helper_func" in subgraph

        # 4. Alias compatibility check (node, nodes)
        res_alias = graph.query_neighbors(node="helper_func", edge_type="caller")
        assert "calls helper_func" in res_alias

        res_nodes = graph.query_subgraph(nodes=["helper_func", "caller_func"])
        assert "--- Subgraph for 'helper_func' ---" in res_nodes
