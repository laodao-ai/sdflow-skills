"""Task 6.1 — CLI 逐命令行为等价**留存** param 化 harness（SC-R3 / R5）。

这不是一次性 smoke：它是**持久**的 param 化契约，遍历 `sdflow-issues` 三薄入口
（`buglist.py`/`todolist.py`/`issues.py`）注册的**全部 argparse subcommand**，对每个命令
断言三个外部可观测面——**stdout（JSON envelope / token / 文本）+ 落盘字节 + 退出码**。

合并前后（三物理脚本 → 一 package + 三薄入口）CLI 外部行为必须逐命令等价；本 harness 就是
那份「等价」的可执行定义，长期留存、每次跑 pytest 都复核。**面治**（CLAUDE.md 基准 3）：
不是只测被点名的几个命令，而是遍历 argparse 全 subcommand——覆盖闭包由
`test_task6_coverage_gate.py` 用 argparse 自身的 subparser 枚举机械核对（那份 gate import 本
文件的 `CASES`，断言枚举 ⊆ 本 harness 覆盖）。

覆盖的 subcommand（canonical label 与 coverage gate 的 argparse 枚举对齐）：
  core（buglist.py + todolist.py，两池各跑）:
    core:next-id · core:add · core:set-status · core:triage · core:scan
  issues.py:
    issues:reindex · issues:sweep
    issues:batch:add · issues:batch:set-status · issues:batch:rename · issues:batch:lint
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"
BUG = str(SCRIPTS / "buglist.py")
TODO = str(SCRIPTS / "todolist.py")
ISS = str(SCRIPTS / "issues.py")
CORE_SCRIPT = {"bug": BUG, "todo": TODO}

TOKEN_RE = re.compile(r"^[A-Z][0-9]+$")


# ── CLI 调用 helper ────────────────────────────────────────────────────────────
def _run(script, root, *args, stdin=None):
    """跑一个真实 CLI 子进程（不借道内部函数），返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, script, "--root", str(root), *args],
        input=stdin, capture_output=True, text=True,
    )


def _bug_payload(**overrides):
    p = {"module": "foo.c:1", "summary": "s", "priority": "P1", "phenomenon": "p"}
    p.update(overrides)
    return p


def _todo_payload(**overrides):
    p = {"module": "foo.c:1", "summary": "s", "type": "代码质量"}
    p.update(overrides)
    return p


POOL_PAYLOAD = {"bug": _bug_payload, "todo": _todo_payload}
# 各池非终态 set-status 目标（避免终态要求 evidence）
POOL_SET_STATUS_TARGET = {"bug": "VERIFIED", "todo": "PROPOSED"}


def _seed_item(pool, root, **extra):
    """经真实 `add` CLI 造一条 item（用真实 producer，避免 fixture 格式漂移）。返回 id。"""
    proc = _run(CORE_SCRIPT[pool], root, "add", stdin=json.dumps(POOL_PAYLOAD[pool](**extra)))
    assert proc.returncode == 0, f"seed add failed: {proc.stderr}"
    return json.loads(proc.stdout)["id"], json.loads(proc.stdout)["file"]


# ── 每个 subcommand 的 case 定义 ────────────────────────────────────────────────
# 每个 case: (param_id, subcommand_label, run(root)->proc, check(proc, root))
#   run 完成命令自身的前置 setup 后跑目标命令，返回目标命令的 proc。
#   check 断言 exit + stdout 形态 + 落盘字节。

def _c_next_id(pool):
    def run(root):
        return _run(CORE_SCRIPT[pool], root, "next-id")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        token = proc.stdout.strip()
        assert TOKEN_RE.match(token), f"next-id token 非法: {token!r}"

    return (f"core:next-id[{pool}]", "core:next-id", run, check)


def _c_add(pool):
    def run(root):
        return _run(CORE_SCRIPT[pool], root, "add", stdin=json.dumps(POOL_PAYLOAD[pool]()))

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        assert TOKEN_RE.match(out["id"]), out
        landed = Path(root) / out["file"]
        assert landed.exists(), f"落盘文件缺失: {landed}"
        assert out["id"].encode("utf-8") in landed.read_bytes()  # 落盘字节含该 id

    return (f"core:add[{pool}]", "core:add", run, check)


def _c_scan(pool):
    def run(root):
        _seed_item(pool, root)
        return _run(CORE_SCRIPT[pool], root, "scan", "--json")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON envelope
        # scan envelope key 各池各异（bugs / items），必存在 + 含 seeded item
        key = "bugs" if pool == "bug" else "items"
        assert key in out, f"scan envelope 缺 {key}: {list(out)}"
        assert "problems" in out
        assert len(out[key]) == 1

    return (f"core:scan[{pool}]", "core:scan", run, check)


def _c_set_status(pool):
    def run(root):
        iid, _ = _seed_item(pool, root)
        target = POOL_SET_STATUS_TARGET[pool]
        return _run(CORE_SCRIPT[pool], root, "set-status", "--id", iid, "--to", target)

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        target = POOL_SET_STATUS_TARGET[pool]
        assert out["new"] == target, out
        landed = Path(root) / out["file"]
        assert target.encode("utf-8") in landed.read_bytes()  # 落盘反映新态

    return (f"core:set-status[{pool}]", "core:set-status", run, check)


def _c_triage(pool):
    def run(root):
        iid, _ = _seed_item(pool, root)
        return _run(CORE_SCRIPT[pool], root, "triage", "--id", iid, "--批次", "batch-x")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        assert out["batch"] == "batch-x", out
        landed = Path(root) / out["file"]
        assert b"batch-x" in landed.read_bytes()  # 落盘含批次

    return (f"core:triage[{pool}]", "core:triage", run, check)


def _c_reindex():
    def run(root):
        _seed_item("bug", root)
        return _run(ISS, root, "reindex")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        index = Path(root) / "openspec" / "issues" / "INDEX.md"
        assert index.exists(), "reindex 未落 INDEX.md"
        assert b"DO NOT EDIT" in index.read_bytes()  # 落盘 banner

    return ("issues:reindex", "issues:reindex", run, check)


def _c_sweep():
    def run(root):
        _seed_item("bug", root, change="change-a")
        return _run(ISS, root, "sweep", "--change", "change-a")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        assert "tagged 1" in proc.stdout, proc.stdout  # stdout = 文本汇总
        batches = Path(root) / "openspec" / "issues" / "batches.md"
        assert batches.exists(), "sweep 未落 batches.md"

    return ("issues:sweep", "issues:sweep", run, check)


def _c_batch_add():
    def run(root):
        return _run(ISS, root, "batch", "add", "batch-x")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        assert out["key"] == "batch-x", out
        batches = Path(root) / "openspec" / "issues" / "batches.md"
        assert b"batch-x" in batches.read_bytes()  # 落盘含 key

    return ("issues:batch:add", "issues:batch:add", run, check)


def _c_batch_set_status():
    def run(root):
        _run(ISS, root, "batch", "add", "batch-x")
        return _run(ISS, root, "batch", "set-status", "batch-x", "IN_PROGRESS")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        assert out["new_status"] == "IN_PROGRESS", out
        batches = Path(root) / "openspec" / "issues" / "batches.md"
        assert b"IN_PROGRESS" in batches.read_bytes()  # 落盘反映新态

    return ("issues:batch:set-status", "issues:batch:set-status", run, check)


def _c_batch_rename():
    def run(root):
        iid, _ = _seed_item("bug", root)
        _run(CORE_SCRIPT["bug"], root, "triage", "--id", iid, "--批次", "batch-old")
        _run(ISS, root, "batch", "add", "batch-old")
        return _run(ISS, root, "batch", "rename", "batch-old", "batch-new")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout)  # stdout = JSON
        assert out["new_key"] == "batch-new" and out["items_changed"] >= 1, out
        batches = Path(root) / "openspec" / "issues" / "batches.md"
        assert b"batch-new" in batches.read_bytes()  # 落盘含新 key

    return ("issues:batch:rename", "issues:batch:rename", run, check)


def _c_batch_lint():
    def run(root):
        _run(ISS, root, "batch", "add", "batch-x")
        return _run(ISS, root, "batch", "lint")

    def check(proc, root):
        assert proc.returncode == 0, proc.stderr  # read-only、合法字段 → exit 0
        assert "通过" in proc.stdout, proc.stdout

    return ("issues:batch:lint", "issues:batch:lint", run, check)


# ── CASES 清单（coverage gate import 此常量核对覆盖闭包）─────────────────────────
CASES = [
    _c_next_id("bug"), _c_next_id("todo"),
    _c_add("bug"), _c_add("todo"),
    _c_scan("bug"), _c_scan("todo"),
    _c_set_status("bug"), _c_set_status("todo"),
    _c_triage("bug"), _c_triage("todo"),
    _c_reindex(),
    _c_sweep(),
    _c_batch_add(),
    _c_batch_set_status(),
    _c_batch_rename(),
    _c_batch_lint(),
]

# coverage gate 用：本 harness 触达的 canonical subcommand label 集合。
COVERED_SUBCOMMANDS = frozenset(subcommand for (_pid, subcommand, _run, _check) in CASES)


@pytest.mark.parametrize(
    "run,check",
    [(run, check) for (_pid, _sub, run, check) in CASES],
    ids=[pid for (pid, _sub, _run, _check) in CASES],
)
def test_cli_command_behavior_equivalence(run, check, tmp_path):
    """逐命令行为等价：跑真实 CLI，断言 stdout（JSON/token/文本）+ 落盘字节 + 退出码。"""
    proc = run(tmp_path)
    check(proc, tmp_path)
