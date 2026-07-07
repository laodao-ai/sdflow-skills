import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import init


def test_copy_bundle_refreshes_contract(tmp_path):
    init.copy_bundle(str(tmp_path), full=False)
    contract = tmp_path / "openspec" / "workflow" / "lens-metric-contract.md"
    assert contract.exists(), "非 full 模式须一并铺 lens-metric-contract.md"
    assert "lens-metric-enums" in contract.read_text(encoding="utf-8")
    assert (tmp_path / "openspec" / "workflow" / "tools" / "anchor_lint.py").exists()
