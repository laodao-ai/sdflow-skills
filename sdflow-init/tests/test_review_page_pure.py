"""评审页模板内纯函数的 node --test 包装（add-html-review-and-dispatch-watchdog · tasks 4.4）。

纯函数的断言写在 review_page_pure.test.js；无 node 时整体 skip。
"""
import shutil
import subprocess
from pathlib import Path

import pytest

NODE = shutil.which("node")
JS_TEST = Path(__file__).resolve().parent / "review_page_pure.test.js"


@pytest.mark.skipif(NODE is None, reason="node 不可用，评审页纯函数单测跳过")
def test_review_page_pure_functions_node_suite():
    r = subprocess.run(
        [NODE, "--test", str(JS_TEST)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-2000:]
