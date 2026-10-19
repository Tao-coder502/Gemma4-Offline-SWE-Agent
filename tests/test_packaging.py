"""
tests/test_packaging.py
=======================
Validates the packaging script and archive integrity.
"""

import tempfile
import zipfile
from pathlib import Path

from package_submission import build_zip, collect_entries

ROOT = Path(__file__).resolve().parent.parent


def test_collect_entries():
    entries = collect_entries(ROOT, phase=5)
    names = [name for name, _ in entries]
    assert "agent.yaml" in names
    assert "prompts/system.md" in names
    assert "configs/sampling.yaml" in names
    assert "adapters/README.md" in names


def test_build_zip_dry_run():
    # Should not raise exception
    build_zip(ROOT, output_file="dummy.zip", phase=5, dry_run=True)


def test_build_zip_temporary():
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_zip = Path(tmp_dir) / "test_submission.zip"
        build_zip(ROOT, output_file=str(temp_zip), phase=5, dry_run=False)
        assert temp_zip.exists()
        assert temp_zip.stat().st_size < 100 * 1024  # <100KB

        with zipfile.ZipFile(temp_zip, "r") as zf:
            names = set(zf.namelist())
            assert "agent.yaml" in names
            assert "prompts/system.md" in names
            assert "configs/sampling.yaml" in names
            assert "adapters/README.md" in names
            # Ensure zero leaks
            leaks = [n for n in names if n.startswith(("tools/", "docs/", "tests/", "results/", "data/"))]
            assert len(leaks) == 0
