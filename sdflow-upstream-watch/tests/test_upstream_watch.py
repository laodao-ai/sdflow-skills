"""upstream_watch.py 机械层测试。

Task 1：脚手架 + anchors 基础设施 + cwd 守卫 —— `guard_cwd`（proposal A4）+
`load_anchors`/`get_source_anchor`/`write_anchors`（anchors.yaml 三态读写层，R1）+
`SUBPROCESS_TIMEOUT_SECONDS` 单点超时常量 + `main` 的 collect/advance argparse 入口。

Task 2：四源采集器（gstack/matt/superpowers/openspec）+ facts JSON 输出 + `advance`
报告+facts 双参数绑定门 + R5 不改池不变量。四源全部用**真实本地 git 仓**（`file://` 之外
的本地路径 clone，等价行为、零网络）做 fixture，不 stub git 语义本身——只有 openspec
采集器（依赖真实安装的 `openspec` CLI / npm registry）用 `monkeypatch` 桩子进程调用。

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


# ============================ Task 2 共用 git fixture 小工具 ============================

def _commit_file(repo, relname, content, message):
    """在 `repo` 里写/改一个文件并提交，返回新提交的完整 sha。"""
    p = repo / relname
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    _git("add", relname, cwd=repo)
    _git("commit", "-q", "-m", message, cwd=repo)
    return _git("rev-parse", "HEAD", cwd=repo).stdout.strip()


def _make_bare_upstream(path):
    """建一个真实（非 bare）本地 git 仓，充当"上游"——可被 clone/fetch，行为与远程仓
    等价，测试零网络。"""
    _init_repo(path)
    _commit_file(path, "README.md", "seed\n", "seed commit")
    return path


def _marketplace_json_text(sha, name="superpowers"):
    return json.dumps({
        "plugins": [
            {"name": name, "source": {"source": "url",
                                       "url": "https://github.com/obra/superpowers.git",
                                       "sha": sha}},
        ]
    })


def _rev(repo):
    return _git("rev-parse", "HEAD", cwd=repo).stdout.strip()


def _force_rewrite_history_away_from(repo, branch="main"):
    """强制用一条全新孤立历史替换 `branch`——替换前的全部提交（含当前 anchor）都不再是
    新 HEAD 的祖先，模拟上游 force-push 历史重写（区别于"在锚上继续提交"，那仍保持祖先关系，
    不是真的历史重写）。"""
    _git("checkout", "-q", "--orphan", "__rewrite_tmp__", cwd=repo)
    _git("commit", "-q", "--allow-empty", "-m", "rewritten history", cwd=repo)
    _git("branch", "-q", "-f", branch, "__rewrite_tmp__", cwd=repo)
    _git("checkout", "-q", branch, cwd=repo)
    _git("branch", "-q", "-D", "__rewrite_tmp__", cwd=repo)


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
    """守卫通过后 main() 正确路由到 cmd_collect（Task 2：真实四源采集逻辑已落地，
    此处只验证 CLI 分发 + facts 落盘的编排接线——用 monkeypatch 隔断 `collect_all`
    本体，四源各自的采集逻辑由下方专门的 collect_* 用例覆盖，不在此处重复触发真实
    git/npm 子进程（零网络依赖纪律）。"""
    repo = _init_repo(
        tmp_path / "sdflow-skills",
        remote="https://github.com/laodao-ai/sdflow-skills.git",
    )
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        W, "collect_all",
        lambda anchors, *, repo_root, home=None: {
            "gstack": {"status": "ok", "head_sha": "deadbeef", "commits": [], "changed_paths": []},
        },
    )
    rc = W.main(["collect"])
    assert rc == 0
    facts_dir = repo / "openspec" / "upstream" / ".facts"
    facts_files = list(facts_dir.glob("*.json"))
    assert len(facts_files) == 1
    facts = json.loads(facts_files[0].read_text(encoding="utf-8"))
    assert facts["sources"]["gstack"]["head_sha"] == "deadbeef"


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


# =========================================================================================
# Task 2: gstack 采集器
# =========================================================================================

def test_collect_gstack_missing_checkout_degrades():
    with pytest.raises(W.CollectError, match="本地 checkout 不存在"):
        W.collect_gstack(None, checkout_dir=Path("/nonexistent/gstack/checkout"))


def test_collect_gstack_first_run_uses_local_head_as_natural_anchor(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "gstack-upstream")
    checkout = tmp_path / "gstack-checkout"
    _git("clone", "-q", str(upstream), str(checkout), cwd=tmp_path)

    # 上游产出新提交（本地 checkout 尚未见过）
    c2 = _commit_file(upstream, "f.txt", "two", "second commit")

    fact = W.collect_gstack(None, checkout_dir=checkout)
    assert fact["status"] == "ok"
    assert fact["head_sha"] == c2
    assert [c["sha"] for c in fact["commits"]] == [c2]
    assert "f.txt" in fact["changed_paths"]


def test_collect_gstack_with_persisted_anchor_delta_since_anchor(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "gstack-upstream")
    checkout = tmp_path / "gstack-checkout"
    _git("clone", "-q", str(upstream), str(checkout), cwd=tmp_path)
    anchor_sha = _rev(checkout)

    c2 = _commit_file(upstream, "g.txt", "two", "second commit")

    fact = W.collect_gstack({"anchor_sha": anchor_sha}, checkout_dir=checkout)
    assert fact["status"] == "ok"
    assert [c["sha"] for c in fact["commits"]] == [c2]


def test_collect_gstack_no_new_commits_zero_delta(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "gstack-upstream")
    checkout = tmp_path / "gstack-checkout"
    _git("clone", "-q", str(upstream), str(checkout), cwd=tmp_path)
    anchor_sha = _rev(checkout)

    fact = W.collect_gstack({"anchor_sha": anchor_sha}, checkout_dir=checkout)
    assert fact["status"] == "ok"
    assert fact["commits"] == []
    assert fact["changed_paths"] == []


def test_collect_gstack_rewritten_history_degrades_stale_anchor(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "gstack-upstream")
    checkout = tmp_path / "gstack-checkout"
    _git("clone", "-q", str(upstream), str(checkout), cwd=tmp_path)
    stale_anchor = _commit_file(upstream, "g.txt", "two", "second commit")

    # 模拟上游 force-push 历史重写：回退并另开分叉提交，原 stale_anchor 不再是祖先
    _git("reset", "-q", "--hard", "HEAD~1", cwd=upstream)
    _commit_file(upstream, "h.txt", "rewritten", "rewritten history commit")

    with pytest.raises(W.CollectError, match="锚失效"):
        W.collect_gstack({"anchor_sha": stale_anchor}, checkout_dir=checkout)


# =========================================================================================
# Task 2: bare 缓存层（matt / superpowers 共用 `_ensure_bare_cache`）
# =========================================================================================

def test_ensure_bare_cache_clones_when_missing(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "cache-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    result = W._ensure_bare_cache(cache_dir, str(upstream))
    assert result == cache_dir
    assert cache_dir.is_dir()
    assert W._rev_parse(cache_dir, "HEAD") == _rev(upstream)


def test_ensure_bare_cache_fetches_when_present(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "cache-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    W._ensure_bare_cache(cache_dir, str(upstream))

    c2 = _commit_file(upstream, "new.txt", "x", "new upstream commit")
    W._ensure_bare_cache(cache_dir, str(upstream))
    assert W._rev_parse(cache_dir, "HEAD") == c2


def test_ensure_bare_cache_self_heals_on_fetch_failure(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "cache-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    W._ensure_bare_cache(cache_dir, str(upstream))

    # 损坏缓存（删 objects 目录）令后续 fetch 必然非零退出
    import shutil as _shutil
    _shutil.rmtree(cache_dir / "objects")

    c2 = _commit_file(upstream, "healed.txt", "x", "commit after corruption")
    result = W._ensure_bare_cache(cache_dir, str(upstream))
    assert result == cache_dir
    assert W._rev_parse(cache_dir, "HEAD") == c2


def test_ensure_bare_cache_degrades_when_self_heal_also_fails(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "cache-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    W._ensure_bare_cache(cache_dir, str(upstream))

    import shutil as _shutil
    _shutil.rmtree(cache_dir / "objects")

    bogus_upstream = tmp_path / "does-not-exist"
    with pytest.raises(W.CollectError, match=str(cache_dir)):
        W._ensure_bare_cache(cache_dir, str(bogus_upstream))


# =========================================================================================
# Task 2: matt 采集器
# =========================================================================================

def test_collect_matt_first_run_zero_delta_no_persisted_anchor(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    fact = W.collect_matt(
        None, cache_dir=cache_dir, skill_lock_path=tmp_path / "no-such-lock.json",
        upstream_url=str(upstream),
    )
    assert fact["status"] == "ok"
    assert fact["commits"] == []
    assert fact["changed_paths"] == []
    assert "installed_skills" not in fact


def test_collect_matt_delta_since_anchor(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    anchor_sha = _rev(upstream)
    c2 = _commit_file(upstream, "skills/new-skill/SKILL.md", "content", "add new skill")

    fact = W.collect_matt(
        {"anchor_sha": anchor_sha}, cache_dir=cache_dir,
        skill_lock_path=tmp_path / "no-such-lock.json", upstream_url=str(upstream),
    )
    assert fact["status"] == "ok"
    assert [c["sha"] for c in fact["commits"]] == [c2]
    assert "skills/new-skill/SKILL.md" in fact["changed_paths"]


def test_collect_matt_rewritten_history_degrades(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    W.collect_matt(None, cache_dir=cache_dir, skill_lock_path=tmp_path / "no-lock.json",
                    upstream_url=str(upstream))
    stale_anchor = _rev(upstream)
    _force_rewrite_history_away_from(upstream)

    with pytest.raises(W.CollectError, match="锚失效"):
        W.collect_matt({"anchor_sha": stale_anchor}, cache_dir=cache_dir,
                        skill_lock_path=tmp_path / "no-lock.json", upstream_url=str(upstream))


def test_collect_matt_skill_lock_absent_is_not_an_error(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    fact = W.collect_matt(None, cache_dir=cache_dir, skill_lock_path=tmp_path / "absent.json",
                           upstream_url=str(upstream))
    assert fact["status"] == "ok"


def test_collect_matt_skill_lock_key_path_assertion_failure_degrades(tmp_path):
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    lock_path = tmp_path / ".skill-lock.json"
    # mattpocock/skills 来源的条目缺 skillFolderHash 键 —— 格式漂移
    lock_path.write_text(json.dumps({
        "skills": {
            "handoff": {"source": "mattpocock/skills", "skillPath": "skills/productivity/handoff"},
        }
    }), encoding="utf-8")

    with pytest.raises(W.CollectError, match="格式漂移"):
        W.collect_matt(None, cache_dir=cache_dir, skill_lock_path=lock_path, upstream_url=str(upstream))


def test_collect_matt_skill_lock_ignores_non_matt_sources(tmp_path):
    """键路径断言只针对 `source == mattpocock/skills` 的条目——其余来源缺键不该误报。"""
    upstream = _make_bare_upstream(tmp_path / "matt-upstream")
    cache_dir = tmp_path / "cache" / "matt.git"
    lock_path = tmp_path / ".skill-lock.json"
    lock_path.write_text(json.dumps({
        "skills": {
            "find-skills": {"source": "vercel-labs/skills"},  # 无 skillFolderHash，但非 matt 来源
            "handoff": {"source": "mattpocock/skills", "skillFolderHash": "abc123"},
        }
    }), encoding="utf-8")

    fact = W.collect_matt(None, cache_dir=cache_dir, skill_lock_path=lock_path, upstream_url=str(upstream))
    assert fact["status"] == "ok"
    assert fact["installed_skills"] == {"handoff": "abc123"}


# =========================================================================================
# Task 2: superpowers 采集器
# =========================================================================================

def _installed_plugins_json(records):
    return json.dumps({"plugins": {"superpowers@claude-plugins-official": records}})


def test_extract_superpowers_source_sha_direct():
    text = _marketplace_json_text("aaa111")
    assert W._extract_superpowers_source_sha(text) == "aaa111"


def test_extract_superpowers_source_sha_missing_entry_raises():
    with pytest.raises(W.CollectError, match="未找到 superpowers 条目"):
        W._extract_superpowers_source_sha(json.dumps({"plugins": []}))


def test_collect_superpowers_first_run_zero_delta(tmp_path):
    marketplace_upstream = tmp_path / "marketplace-upstream"
    _init_repo(marketplace_upstream)
    _commit_file(marketplace_upstream, ".claude-plugin/marketplace.json",
                  _marketplace_json_text("aaa111"), "seed marketplace")

    installed = tmp_path / "installed_plugins.json"
    installed.write_text(_installed_plugins_json([
        {"scope": "user", "version": "6.2.0"},
    ]), encoding="utf-8")

    fact = W.collect_superpowers(
        None, cache_dir=tmp_path / "cache" / "marketplace.git",
        installed_plugins_path=installed, upstream_url=str(marketplace_upstream),
    )
    assert fact["status"] == "ok"
    assert fact["commits"] == []
    assert fact["source_sha_sequence"] == []
    assert fact["installed_version"] == "6.2.0"


def test_collect_superpowers_tracks_source_sha_sequence_via_path_filtered_commits(tmp_path):
    marketplace_upstream = tmp_path / "marketplace-upstream"
    _init_repo(marketplace_upstream)
    _commit_file(marketplace_upstream, ".claude-plugin/marketplace.json",
                  _marketplace_json_text("aaa111"), "seed marketplace")
    anchor_sha = _rev(marketplace_upstream)

    c2 = _commit_file(marketplace_upstream, ".claude-plugin/marketplace.json",
                       _marketplace_json_text("bbb222"), "bump superpowers pin")
    # 与 superpowers 追踪无关的提交（未触碰 marketplace.json）—— path filter 必须排除它
    _commit_file(marketplace_upstream, "other-plugin/README.md", "noise", "unrelated commit")

    installed = tmp_path / "installed_plugins.json"
    installed.write_text(_installed_plugins_json([{"scope": "user", "version": "6.2.0"}]),
                          encoding="utf-8")

    fact = W.collect_superpowers(
        {"anchor_sha": anchor_sha}, cache_dir=tmp_path / "cache" / "marketplace.git",
        installed_plugins_path=installed, upstream_url=str(marketplace_upstream),
    )
    assert fact["status"] == "ok"
    assert [c["sha"] for c in fact["commits"]] == [c2]
    assert fact["source_sha_sequence"] == ["bbb222"]


def test_collect_superpowers_installed_plugins_missing_file_degrades(tmp_path):
    marketplace_upstream = _make_bare_upstream(tmp_path / "marketplace-upstream")
    with pytest.raises(W.CollectError, match="本地锚源缺失"):
        W.collect_superpowers(
            None, cache_dir=tmp_path / "cache" / "marketplace.git",
            installed_plugins_path=tmp_path / "no-such-file.json",
            upstream_url=str(marketplace_upstream),
        )


def test_collect_superpowers_installed_plugins_missing_version_key_degrades(tmp_path):
    marketplace_upstream = _make_bare_upstream(tmp_path / "marketplace-upstream")
    installed = tmp_path / "installed_plugins.json"
    installed.write_text(_installed_plugins_json([{"scope": "user"}]), encoding="utf-8")  # 缺 version

    with pytest.raises(W.CollectError, match="格式漂移"):
        W.collect_superpowers(
            None, cache_dir=tmp_path / "cache" / "marketplace.git",
            installed_plugins_path=installed, upstream_url=str(marketplace_upstream),
        )


def test_collect_superpowers_multi_scope_prefers_user_scope(tmp_path):
    marketplace_upstream = _make_bare_upstream(tmp_path / "marketplace-upstream")
    installed = tmp_path / "installed_plugins.json"
    installed.write_text(_installed_plugins_json([
        {"scope": "project", "version": "9.9.9"},
        {"scope": "user", "version": "6.2.0"},
        {"scope": "project", "version": "1.0.0"},
    ]), encoding="utf-8")

    fact = W.collect_superpowers(
        None, cache_dir=tmp_path / "cache" / "marketplace.git",
        installed_plugins_path=installed, upstream_url=str(marketplace_upstream),
    )
    assert fact["installed_version"] == "6.2.0"


def test_collect_superpowers_multi_scope_no_user_takes_max_version_numeric_not_lexicographic(tmp_path):
    marketplace_upstream = _make_bare_upstream(tmp_path / "marketplace-upstream")
    installed = tmp_path / "installed_plugins.json"
    # 词典序会误判 "1.9.0" > "1.10.0"；数值化 tokenizing 必须选出真正的 1.10.0
    installed.write_text(_installed_plugins_json([
        {"scope": "project", "version": "1.9.0"},
        {"scope": "project", "version": "1.10.0"},
    ]), encoding="utf-8")

    fact = W.collect_superpowers(
        None, cache_dir=tmp_path / "cache" / "marketplace.git",
        installed_plugins_path=installed, upstream_url=str(marketplace_upstream),
    )
    assert fact["installed_version"] == "1.10.0"


def test_collect_superpowers_rewritten_history_degrades(tmp_path):
    marketplace_upstream = tmp_path / "marketplace-upstream"
    _init_repo(marketplace_upstream)
    _commit_file(marketplace_upstream, ".claude-plugin/marketplace.json",
                  _marketplace_json_text("aaa111"), "seed marketplace")
    installed = tmp_path / "installed_plugins.json"
    installed.write_text(_installed_plugins_json([{"scope": "user", "version": "6.2.0"}]),
                          encoding="utf-8")

    cache_dir = tmp_path / "cache" / "marketplace.git"
    W.collect_superpowers(None, cache_dir=cache_dir, installed_plugins_path=installed,
                           upstream_url=str(marketplace_upstream))
    stale_anchor = _rev(marketplace_upstream)
    _force_rewrite_history_away_from(marketplace_upstream)

    with pytest.raises(W.CollectError, match="锚失效"):
        W.collect_superpowers({"anchor_sha": stale_anchor}, cache_dir=cache_dir,
                               installed_plugins_path=installed, upstream_url=str(marketplace_upstream))


# =========================================================================================
# Task 2: OpenSpec 采集器（版本对照 + schema fork drift）
# =========================================================================================

def _fake_completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_diff_dirs_sha256_changed_added_removed(tmp_path):
    fork = tmp_path / "fork"
    upstream = tmp_path / "upstream"
    fork.mkdir(); upstream.mkdir()
    (fork / "schema.yaml").write_text("v1", encoding="utf-8")
    (upstream / "schema.yaml").write_text("v2", encoding="utf-8")  # changed
    (upstream / "new-template.md").write_text("new", encoding="utf-8")  # added(上游有fork没有)
    (fork / "old-template.md").write_text("old", encoding="utf-8")  # removed(fork有上游没有)

    drift = W._diff_dirs_sha256(fork, upstream)
    assert drift["changed"] == ["schema.yaml"]
    assert drift["added"] == ["new-template.md"]
    assert drift["removed"] == ["old-template.md"]


def test_collect_openspec_version_compare_and_schema_drift(tmp_path, monkeypatch):
    fork_dir = tmp_path / "fork"
    upstream_schema_root = tmp_path / "npm-root-g"
    upstream_dir = upstream_schema_root / "@fission-ai" / "openspec" / "schemas" / "spec-driven"
    fork_dir.mkdir(parents=True)
    upstream_dir.mkdir(parents=True)
    (fork_dir / "schema.yaml").write_text("same", encoding="utf-8")
    (upstream_dir / "schema.yaml").write_text("same", encoding="utf-8")

    monkeypatch.setattr(W.shutil, "which", lambda name: "/usr/bin/openspec")

    def fake_run(cmd, input=None):
        if cmd[:2] == ["/usr/bin/openspec", "--version"]:
            return _fake_completed(stdout="1.8.0\n")
        if cmd[:3] == ["npm", "view", W.OPENSPEC_NPM_PACKAGE]:
            return _fake_completed(stdout="1.9.0\n")
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(W, "_run", fake_run)

    fact = W.collect_openspec(repo_root=tmp_path, fork_dir=fork_dir, npm_root_g=str(upstream_schema_root))
    assert fact["status"] == "ok"
    assert fact["installed_version"] == "1.8.0"
    assert fact["latest_version"] == "1.9.0"
    assert fact["schema_drift"] == {"status": "ok", "changed": [], "added": [], "removed": []}


def test_collect_openspec_upstream_schema_dir_missing_degrades_subitem_only(tmp_path, monkeypatch):
    fork_dir = tmp_path / "fork"
    fork_dir.mkdir()
    (fork_dir / "schema.yaml").write_text("x", encoding="utf-8")

    monkeypatch.setattr(W.shutil, "which", lambda name: "/usr/bin/openspec")

    def fake_run(cmd, input=None):
        if cmd[:2] == ["/usr/bin/openspec", "--version"]:
            return _fake_completed(stdout="1.8.0\n")
        if cmd[:3] == ["npm", "view", W.OPENSPEC_NPM_PACKAGE]:
            return _fake_completed(stdout="1.8.0\n")
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(W, "_run", fake_run)

    fact = W.collect_openspec(
        repo_root=tmp_path, fork_dir=fork_dir, npm_root_g=str(tmp_path / "no-such-npm-root"),
    )
    # 版本对照子项不受影响
    assert fact["status"] == "ok"
    assert fact["installed_version"] == "1.8.0"
    assert fact["latest_version"] == "1.8.0"
    # schema drift 子项独立降级
    assert fact["schema_drift"]["status"] == "degraded"
    assert "reason" in fact["schema_drift"]


def test_collect_openspec_cli_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(W.shutil, "which", lambda name: None)
    with pytest.raises(W.CollectError, match="本地锚源缺失"):
        W.collect_openspec(repo_root=tmp_path)


# =========================================================================================
# Task 2: collect_all 单源失败不传染 + 超时降级
# =========================================================================================

def test_collect_all_single_source_unreachable_others_unaffected(tmp_path, monkeypatch):
    monkeypatch.setattr(W, "collect_gstack", lambda anchor, **kw: {"status": "ok", "head_sha": "g1",
                                                                     "commits": [], "changed_paths": []})
    monkeypatch.setattr(W, "collect_matt", lambda anchor, **kw: (_ for _ in ()).throw(
        W.CollectError("matt 上游不可达")))
    monkeypatch.setattr(W, "collect_superpowers", lambda anchor, **kw: {
        "status": "ok", "head_sha": "s1", "commits": [], "source_sha_sequence": [],
        "installed_version": "6.2.0"})
    monkeypatch.setattr(W, "collect_openspec", lambda **kw: {"status": "ok",
                                                               "installed_version": "1.8.0",
                                                               "latest_version": "1.8.0"})

    sources = W.collect_all({}, repo_root=tmp_path, home=tmp_path)
    assert sources["gstack"]["status"] == "ok"
    assert sources["matt"]["status"] == "degraded"
    assert "matt 上游不可达" in sources["matt"]["reason"]
    assert sources["superpowers"]["status"] == "ok"
    assert sources["openspec"]["status"] == "ok"


def test_collect_source_safe_converts_timeout_to_degraded():
    def _times_out():
        raise subprocess.TimeoutExpired(cmd=["git", "fetch"], timeout=W.SUBPROCESS_TIMEOUT_SECONDS)

    result = W._collect_source_safe(_times_out)
    assert result["status"] == "degraded"
    assert "超时" in result["reason"]


# =========================================================================================
# Task 2: advance 双参数门
# =========================================================================================

def _write_facts(path, sources):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "collected_at": "2026-08-11T09:00:00Z",
                                 "sources": sources}), encoding="utf-8")


def test_cmd_advance_rejects_when_report_missing(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    facts_path = repo / "facts.json"
    _write_facts(facts_path, {"gstack": {"status": "ok", "head_sha": "abc",
                                          "commits": [{"sha": "abc", "subject": "x"}]}})

    args = argparse_ns(report=str(repo / "no-such-report.md"), facts=str(facts_path))
    with pytest.raises(W.AdvanceGateError, match="报告文件不存在"):
        W.cmd_advance(args)
    assert not (repo / "openspec" / "upstream" / "anchors.yaml").exists()


def argparse_ns(**kwargs):
    class _NS:
        pass
    ns = _NS()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_cmd_advance_rejects_when_report_missing_a_commit_sha(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    facts_path = repo / "facts.json"
    _write_facts(facts_path, {"gstack": {"status": "ok", "head_sha": "abc123",
                                          "commits": [{"sha": "abc123", "subject": "x"}]}})
    report_path = repo / "report.md"
    report_path.write_text("这份报告没有提到那个 commit sha\n", encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    with pytest.raises(W.AdvanceGateError, match="abc123"):
        W.cmd_advance(args)
    assert not (repo / "openspec" / "upstream" / "anchors.yaml").exists()


def test_cmd_advance_advances_anchors_when_report_transcribes_all_shas(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    facts_path = repo / "facts.json"
    _write_facts(facts_path, {
        "gstack": {"status": "ok", "head_sha": "abc123",
                   "commits": [{"sha": "abc123", "subject": "x"}]},
        "openspec": {"status": "ok", "installed_version": "1.9.0", "commits": []},
    })
    report_path = repo / "report.md"
    report_path.write_text("gstack 节：commit abc123 已核查。openspec 节：1.9.0。\n", encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    rc = W.cmd_advance(args)
    assert rc == 0

    anchors_path = repo / "openspec" / "upstream" / "anchors.yaml"
    anchors = W.load_anchors(anchors_path)
    assert W.get_source_anchor(anchors, "gstack") == {"anchor_sha": "abc123"}
    assert W.get_source_anchor(anchors, "openspec") == {"anchor_version": "1.9.0"}
    assert anchors["last_run"] is not None


def test_cmd_advance_preserves_degraded_source_anchor_verbatim(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    anchors_path = repo / "openspec" / "upstream" / "anchors.yaml"
    W.write_anchors(anchors_path, {
        "schema_version": 1, "last_run": "2026-08-01T00:00:00Z", "remind_after_days": 30,
        "sources": {"matt": {"anchor_sha": "old-matt-sha-unchanged"}},
    })

    facts_path = repo / "facts.json"
    _write_facts(facts_path, {
        "gstack": {"status": "ok", "head_sha": "new-gstack-sha",
                   "commits": [{"sha": "new-gstack-sha", "subject": "x"}]},
        "matt": {"status": "degraded", "reason": "matt 上游不可达", "commits": []},
    })
    report_path = repo / "report.md"
    report_path.write_text("gstack: new-gstack-sha 已核查。matt: 采集降级，下轮重试同一窗口。\n",
                            encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    W.cmd_advance(args)

    anchors = W.load_anchors(anchors_path)
    assert W.get_source_anchor(anchors, "matt") == {"anchor_sha": "old-matt-sha-unchanged"}
    assert W.get_source_anchor(anchors, "gstack") == {"anchor_sha": "new-gstack-sha"}


def test_cmd_advance_first_run_creates_anchors_file(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    anchors_path = repo / "openspec" / "upstream" / "anchors.yaml"
    assert not anchors_path.exists()

    facts_path = repo / "facts.json"
    _write_facts(facts_path, {"openspec": {"status": "ok", "installed_version": "1.8.0", "commits": []}})
    report_path = repo / "report.md"
    report_path.write_text("首轮建锚：openspec 1.8.0。\n", encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    W.cmd_advance(args)
    assert anchors_path.is_file()
    anchors = W.load_anchors(anchors_path)
    assert W.get_source_anchor(anchors, "openspec") == {"anchor_version": "1.8.0"}


def test_cmd_advance_rejects_null_anchor_sha_for_ok_source(tmp_path, monkeypatch):
    """[impl-review-fix] Fix 5：status=ok 但 head_sha=None（gstack/matt/superpowers 用
    anchor_sha）时拒绝推进，anchors.yaml 不落盘——空锚一旦写入会被下轮误判"无锚首轮"。"""
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    facts_path = repo / "facts.json"
    _write_facts(facts_path, {
        "gstack": {"status": "ok", "head_sha": None, "commits": []},
    })
    report_path = repo / "report.md"
    report_path.write_text("gstack 节：本轮无新 commit。\n", encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    with pytest.raises(W.AdvanceGateError, match="gstack"):
        W.cmd_advance(args)
    assert not (repo / "openspec" / "upstream" / "anchors.yaml").exists()


def test_cmd_advance_rejects_null_anchor_version_for_openspec(tmp_path, monkeypatch):
    """[impl-review-fix] Fix 5：openspec 源用 anchor_version，installed_version=None 时
    同样拒绝推进（不同源种类的观测值字段名不同，两条分支都要覆盖）。"""
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    facts_path = repo / "facts.json"
    _write_facts(facts_path, {
        "openspec": {"status": "ok", "installed_version": None, "commits": []},
    })
    report_path = repo / "report.md"
    report_path.write_text("openspec 节：版本读取异常。\n", encoding="utf-8")

    args = argparse_ns(report=str(report_path), facts=str(facts_path))
    with pytest.raises(W.AdvanceGateError, match="openspec"):
        W.cmd_advance(args)
    assert not (repo / "openspec" / "upstream" / "anchors.yaml").exists()


def test_cli_advance_missing_args_in_valid_repo_rejects_via_main(tmp_path, monkeypatch):
    """main() 层：cwd 合法但零参数调用 advance —— 报告路径缺失须拒绝推进（非 argparse
    usage error，也不是 CwdGuardError），退出码非零，anchors.yaml 不被创建。"""
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    rc = W.main(["advance"])
    assert rc == 3
    assert not (repo / "openspec" / "upstream" / "anchors.yaml").exists()


# =========================================================================================
# Task 2: R5 不改池不变量
# =========================================================================================

def test_collect_and_advance_do_not_touch_issues_tree(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)
    issues_dir = repo / "openspec" / "issues" / "open"
    issues_dir.mkdir(parents=True)
    (issues_dir / "T1.md").write_text("existing issue\n", encoding="utf-8")
    before = sorted(p.relative_to(repo) for p in (repo / "openspec" / "issues").rglob("*"))

    monkeypatch.setattr(
        W, "collect_all",
        lambda anchors, *, repo_root, home=None: {
            "gstack": {"status": "ok", "head_sha": "deadbeef",
                       "commits": [{"sha": "deadbeef", "subject": "x"}], "changed_paths": []},
        },
    )
    rc_collect = W.main(["collect"])
    assert rc_collect == 0

    facts_files = list((repo / "openspec" / "upstream" / ".facts").glob("*.json"))
    assert len(facts_files) == 1
    report_path = repo / "openspec" / "upstream" / "reports" / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("gstack: deadbeef 已核查。\n", encoding="utf-8")

    rc_advance = W.main(["advance", str(report_path), str(facts_files[0])])
    assert rc_advance == 0

    after = sorted(p.relative_to(repo) for p in (repo / "openspec" / "issues").rglob("*"))
    assert before == after
    assert (issues_dir / "T1.md").read_text(encoding="utf-8") == "existing issue\n"


# =========================================================================================
# Task 2: facts JSON 形状快照断言
# =========================================================================================

def test_facts_json_shape_snapshot(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "sdflow-skills",
                       remote="https://github.com/laodao-ai/sdflow-skills.git")
    monkeypatch.chdir(repo)

    monkeypatch.setattr(
        W, "collect_all",
        lambda anchors, *, repo_root, home=None: {
            "gstack": {"status": "ok", "head_sha": "g1",
                       "commits": [{"sha": "g1", "subject": "s"}], "changed_paths": ["a.md"]},
            "matt": {"status": "degraded", "reason": "matt 上游不可达"},
            "superpowers": {"status": "ok", "head_sha": "s1", "commits": [],
                             "source_sha_sequence": [], "installed_version": "6.2.0"},
            "openspec": {"status": "ok", "installed_version": "1.8.0", "latest_version": "1.8.0",
                         "schema_drift": {"status": "ok", "changed": [], "added": [], "removed": []}},
        },
    )
    rc = W.main(["collect"])
    assert rc == 0

    facts_files = list((repo / "openspec" / "upstream" / ".facts").glob("*.json"))
    assert len(facts_files) == 1
    facts = json.loads(facts_files[0].read_text(encoding="utf-8"))

    assert facts["schema_version"] == W.SCHEMA_VERSION
    assert "collected_at" in facts
    assert set(facts["sources"].keys()) == {"gstack", "matt", "superpowers", "openspec"}
    assert facts["sources"]["gstack"]["status"] == "ok"
    assert facts["sources"]["matt"]["status"] == "degraded"
    assert facts["sources"]["matt"]["reason"] == "matt 上游不可达"
    assert facts["sources"]["superpowers"]["installed_version"] == "6.2.0"
    assert facts["sources"]["openspec"]["schema_drift"]["changed"] == []


def test_facts_dot_facts_dir_has_gitignore():
    gitignore = Path(__file__).parent.parent.parent / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "openspec/upstream/.facts" in text
