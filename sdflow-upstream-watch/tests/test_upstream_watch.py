"""upstream_watch.py 机械层测试（Task 1：脚手架 + anchors 基础设施 + cwd 守卫）。

标的：`guard_cwd`（cwd 守卫，proposal A4）+ `load_anchors`/`get_source_anchor`/
`write_anchors`（anchors.yaml 三态读写层，R1）+ `SUBPROCESS_TIMEOUT_SECONDS` 单点超时常量 +
`main` 的 collect/advance argparse 入口。四源采集与 advance 报告+facts 绑定门属 Task 2，
不在本文件范围内。

全部用例走 tmp_path + `monkeypatch.chdir`（禁裸 `os.chdir`，见仓根 conftest.py 纪律），
零全局影响；真实 mikefarah/yq 二进制默认参与（本机/CI 均已安装，同 `retro_report` 测试先例
不 stub 正常路径），仅"非 mikefarah 家族"场景需要一个假 yq 可执行文件注入 PATH。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import upstream_watch as W  # noqa: E402

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "upstream_watch.py")


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True,
        encoding="utf-8", errors="replace",
    )


def _init_repo(path, remote=None):
    path.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=path)
    _git("config", "user.email", "test@example.com", cwd=path)
    _git("config", "user.name", "Test", cwd=path)
    if remote:
        _git("remote", "add", "origin", remote, cwd=path)
    return path


# ============================ cwd 守卫（guard_cwd，unit-level）============================

def test_guard_cwd_rejects_dir_outside_any_git_repo(tmp_path, monkeypatch):
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    monkeypatch.chdir(outside)
    with pytest.raises(W.CwdGuardError):
        W.guard_cwd()


def test_guard_cwd_rejects_git_repo_with_wrong_remote(tmp_path, monkeypatch):
    other = _init_repo(tmp_path / "other-repo", remote="https://github.com/someone/else.git")
    monkeypatch.chdir(other)
    with pytest.raises(W.CwdGuardError):
        W.guard_cwd()


def test_guard_cwd_rejects_git_repo_with_no_remote(tmp_path, monkeypatch):
    bare = _init_repo(tmp_path / "no-remote-repo")
    monkeypatch.chdir(bare)
    with pytest.raises(W.CwdGuardError):
        W.guard_cwd()


def test_guard_cwd_accepts_matching_remote_and_returns_toplevel(tmp_path, monkeypatch):
    repo = _init_repo(
        tmp_path / "sdflow-skills",
        remote="https://github.com/laodao-ai/sdflow-skills.git",
    )
    monkeypatch.chdir(repo)
    root = W.guard_cwd()
    assert Path(root).resolve() == repo.resolve()


def test_guard_cwd_accepts_from_subdirectory_of_matching_repo(tmp_path, monkeypatch):
    repo = _init_repo(
        tmp_path / "sdflow-skills",
        remote="https://github.com/laodao-ai/sdflow-skills.git",
    )
    sub = repo / "some" / "nested" / "dir"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    root = W.guard_cwd()
    assert Path(root).resolve() == repo.resolve()


# ==================== cwd 守卫（CLI 层，零写入验收，proposal A4 acceptance）====================

def test_cli_collect_in_non_repo_cwd_fails_loud_and_writes_nothing(tmp_path):
    outside = tmp_path / "some-other-project"
    outside.mkdir()
    r = subprocess.run(
        [sys.executable, SCRIPT, "collect"], cwd=str(outside),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode != 0
    assert "fail-loud" in r.stderr
    assert "sdflow-skills" in r.stderr
    # 零写入：guard 失败后目录下没有任何新增条目（尤其不能出现 openspec/）
    assert list(outside.iterdir()) == []


def test_cli_advance_in_non_repo_cwd_fails_loud_and_writes_nothing(tmp_path):
    outside = tmp_path / "some-other-project-2"
    outside.mkdir()
    r = subprocess.run(
        [sys.executable, SCRIPT, "advance"], cwd=str(outside),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode != 0
    assert "fail-loud" in r.stderr
    assert list(outside.iterdir()) == []


def test_cli_collect_in_wrong_remote_repo_fails_loud_and_writes_nothing(tmp_path):
    other = _init_repo(tmp_path / "wrong-remote", remote="https://github.com/someone/else.git")
    r = subprocess.run(
        [sys.executable, SCRIPT, "collect"], cwd=str(other),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode != 0
    assert "fail-loud" in r.stderr
    # .git 是 git init 自带的唯一条目，守卫必须没有额外新增任何文件/目录
    assert set(p.name for p in other.iterdir()) == {".git"}


# ============================ argparse 入口可用 ============================

def test_cli_help_lists_both_subcommands():
    r = subprocess.run(
        [sys.executable, SCRIPT, "--help"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0
    assert "collect" in r.stdout
    assert "advance" in r.stdout


def test_cli_missing_subcommand_errors():
    r = subprocess.run(
        [sys.executable, SCRIPT],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode != 0


def test_main_dispatches_to_collect_inside_matching_repo(tmp_path, monkeypatch):
    repo = _init_repo(
        tmp_path / "sdflow-skills",
        remote="https://github.com/laodao-ai/sdflow-skills.git",
    )
    monkeypatch.chdir(repo)
    rc = W.main(["collect"])
    # 守卫已通过（未抛 CwdGuardError）；Task 1 阶段占位实现返回非零"未实现"信号，
    # 但绝不是守卫拒绝——用返回码类型与守卫失败路径（1）区分开。
    assert rc == 2


# ============================ 超时常量单点定义 ============================

def test_timeout_constant_is_single_point_definition():
    assert W.SUBPROCESS_TIMEOUT_SECONDS == 60
    assert isinstance(W.SUBPROCESS_TIMEOUT_SECONDS, int)


# ============================ anchors.yaml 三态读取（load_anchors，R1）====================

def test_load_anchors_missing_file_returns_init_skeleton(tmp_path):
    path = tmp_path / "anchors.yaml"
    assert not path.exists()
    anchors = W.load_anchors(path)
    assert anchors["schema_version"] == W.SCHEMA_VERSION
    assert anchors["remind_after_days"] == W.DEFAULT_REMIND_AFTER_DAYS
    assert anchors["last_run"] is None
    assert anchors["sources"] == {}
    # 首轮初始化语义下任意源都是"无锚"
    assert W.get_source_anchor(anchors, "gstack") is None


def test_load_anchors_malformed_yaml_fail_loud(tmp_path):
    path = tmp_path / "anchors.yaml"
    # 真实语法错误（未闭合的 flow sequence）——真 yq 对此返回非零退出
    path.write_text("schema_version: 1\nsources: [unclosed\n", encoding="utf-8")
    with pytest.raises(W.AnchorsError):
        W.load_anchors(path)


def test_load_anchors_valid_file_with_missing_source_value_treated_as_no_anchor(tmp_path):
    path = tmp_path / "anchors.yaml"
    path.write_text(
        "schema_version: 1\n"
        "last_run: 2026-08-01T00:00:00Z\n"
        "remind_after_days: 30\n"
        "sources:\n"
        "  gstack:\n"
        "    anchor_sha: abc123\n",
        encoding="utf-8",
    )
    anchors = W.load_anchors(path)
    assert anchors["last_run"] == "2026-08-01T00:00:00Z"
    assert W.get_source_anchor(anchors, "gstack") == {"anchor_sha": "abc123"}
    # matt 字段在文件中完全缺失 —— 值缺失 = 该源视为无锚
    assert W.get_source_anchor(anchors, "matt") is None


def test_yq_not_installed_fail_loud(tmp_path, monkeypatch):
    path = tmp_path / "anchors.yaml"
    path.write_text("schema_version: 1\nsources: {}\n", encoding="utf-8")
    monkeypatch.setattr(W.shutil, "which", lambda name: None)
    with pytest.raises(W.AnchorsError):
        W.load_anchors(path)


def test_yq_non_mikefarah_flavor_rejected(tmp_path, monkeypatch):
    """mikefarah-flavor 探测：伪造一个非 mikefarah 的 yq 可执行文件，MUST 报错阻止误用。"""
    path = tmp_path / "anchors.yaml"
    path.write_text("schema_version: 1\nsources: {}\n", encoding="utf-8")

    fake_bin_dir = tmp_path / "fakebin"
    fake_bin_dir.mkdir()
    fake_yq = fake_bin_dir / "yq"
    fake_yq.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "--version" ]; then echo "yq 2.14.0 (kislyuk/yq)"; exit 0; fi\n'
        "exit 1\n",
        encoding="utf-8",
    )
    fake_yq.chmod(0o755)
    monkeypatch.setattr(W.shutil, "which", lambda name: str(fake_yq) if name == "yq" else None)

    with pytest.raises(W.AnchorsError, match="检测到的 yq 不是 mikefarah/yq"):
        W.load_anchors(path)


# ============================ anchors.yaml 写入 + round-trip（write_anchors，R1）==========

def test_write_anchors_then_load_roundtrip(tmp_path):
    path = tmp_path / "nested" / "anchors.yaml"
    anchors = {
        "schema_version": W.SCHEMA_VERSION,
        "last_run": "2026-08-11T09:00:00Z",
        "remind_after_days": 45,
        "sources": {
            "gstack": {"anchor_sha": "960c3a8deadbeef"},
            "openspec": {"anchor_version": "1.8.0"},
        },
    }
    W.write_anchors(path, anchors)
    assert path.is_file()

    reloaded = W.load_anchors(path)
    assert reloaded["schema_version"] == W.SCHEMA_VERSION
    assert reloaded["last_run"] == "2026-08-11T09:00:00Z"
    assert reloaded["remind_after_days"] == 45
    assert W.get_source_anchor(reloaded, "gstack") == {"anchor_sha": "960c3a8deadbeef"}
    assert W.get_source_anchor(reloaded, "openspec") == {"anchor_version": "1.8.0"}
    assert W.get_source_anchor(reloaded, "matt") is None


def test_write_anchors_only_writer_of_anchors_yaml(tmp_path):
    """R1: anchors.yaml SHALL 只由 watch 机械层脚本读写——本用例只断言 write_anchors
    产出的文件人类可读为 YAML（非 JSON 字面量),佐证走 yq 转换而非手写字符串拼接。"""
    path = tmp_path / "anchors.yaml"
    W.write_anchors(path, {"schema_version": 1, "sources": {}})
    text = path.read_text(encoding="utf-8")
    assert "schema_version: 1" in text
    assert not text.strip().startswith("{")
