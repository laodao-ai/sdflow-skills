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


# design D2 负例矩阵：每条 MUST NOT match，封住"TAG_RE 被放松后 happy 例仍绿"的漏报。
# [spec-review-amendment DF1] 每条注释=其唯一哨兵的放松类（对抗镜#1 mutation 模拟核实：
# 放松该类 → 该负例从 None 翻转为 match）。task-1-（号位空/含前导符号）与 taskab-（号位加宽
# 为字母数字）是两类不同放松，需各自负例——单靠 task-1- 挡不住 task[a-z0-9]+ 的纯字母加宽。
NEGATIVE_CASES = [
    ("checkpoint(task1slug)",   "尾 dash 变可选（task(\\d+)-? → 丢 task1/task12 边界锚）"),
    ("checkpoint(DEMO:task1-)", "命名空间允许大写（[a-z0-9]→[A-Za-z0-9]，破 kebab 锁）"),
    ("checkpoint(task-1-)",     "号位空或含前导符号（task(\\d*)- / task(-?\\d+)- 变体）"),
    ("checkpoint(taskab-slug)", "号位加宽为字母数字（task(\\d+)- → task([a-z0-9]+)-）"),
    ("checkpoint(:task1-)",     "空命名空间（[a-z0-9]+ → [a-z0-9]* 允许 0 字符）"),
]


@pytest.mark.parametrize("subject,relaxation", NEGATIVE_CASES,
                         ids=[c[0] for c in NEGATIVE_CASES])
def test_tag_re_rejects_relaxations(subject, relaxation):
    assert TAG_RE.match(subject) is None, \
        f"负例 {subject!r} 竟被 match——{relaxation} 类放松未被挡住"
