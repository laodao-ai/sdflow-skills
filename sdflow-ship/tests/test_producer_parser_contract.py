"""producer→parser 契约：checkpoint-commit.sh 真产的 subject ↔ ship_gate.TAG_RE。
锚的是脚本真吐的字节 ↔ gate 真跑的正则（design D1），非文档占位符。"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "checkpoint-commit.sh"

# D4：scripts 不在 sys.path，注入后 import。ship_gate.py 有 __main__ 守卫，import 无副作用。
sys.path.insert(0, str(REPO / "sdflow-ship" / "scripts"))
from ship_gate import TAG_RE  # noqa: E402


def run_producer(repo, step):
    """在 repo 里造一处变更 → 调真实脚本 → 返回最后一个 commit 的 subject。"""
    (repo / f"f-{step}.txt").write_text(step, encoding="utf-8")  # 制造非空 porcelain
    subprocess.run(["bash", str(SCRIPT), step, "msg"], cwd=repo, check=True,
                   capture_output=True, text=True)
    out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%s"],
                         check=True, capture_output=True, text=True)
    return out.stdout.strip()


def test_namespaced_subject_matches_and_captures(repo):
    subject = run_producer(repo, "demo:task1-slug")
    assert subject == "checkpoint(demo:task1-slug): msg"
    m = TAG_RE.match(subject)
    assert m is not None
    assert (m.group(1), m.group(2)) == ("demo", "1")


def test_bare_subject_matches_with_null_namespace(repo):
    subject = run_producer(repo, "task1-slug")
    assert subject == "checkpoint(task1-slug): msg"
    m = TAG_RE.match(subject)
    assert m is not None
    assert m.group(1) is None
    assert m.group(2) == "1"
