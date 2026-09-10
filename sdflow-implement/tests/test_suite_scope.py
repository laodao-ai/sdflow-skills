"""pytest for `impl_route.py suite-scope`（adr/0045 · design.md §2 · Task 1）。

沙盒 git 仓（`tmp_path`，零全局影响）golden 覆盖：
- 纯工具域 / 纯项目域 / 跨域并集
- `domains` 缺席 ⇒ 三层原样（逐字等同今日）
- 最长前缀（跨域、含默认域内部）
- `openspec/` 硬排除
- 未跟踪文件计入 / 已删除文件按路径归域 / 空 changed ⇒ 默认域
- `--base` 显式与自动 merge-base 一致 / `--head` 提交范围模式不含未跟踪
- 分档规范化（字符串、缺 quick、缺 full、非 unit 层同规则）/ `layers:` 空值 ≡ `{}`
- 无尾斜杠精确匹配不命中同名目录
- 非 UTF-8 路径解码契约（direct-call，规避 macOS 文件系统对非法字节名的限制）
- merge-base 失败 ⇒ 退出 6
- 坏配置 8 类 + yq 缺失/身份不对 ⇒ 退出 6 + stderr 含 problem/cause/fix

调用方式：多数用例走真实 CLI 子进程（贴近生产路径）；`_run_git_z` 的 surrogateescape 解码
契约与「yq 缺失/身份不对」两类用直接函数调用 + monkeypatch（前者受 macOS APFS 对非法字节
文件名的限制，后者需要跨进程篡改 PATH，二者走直接调用更精确、更省沙盒开销）。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "impl_route.py"
sys.path.insert(0, str(SCRIPT.parent))
import impl_route as ir  # noqa: E402


# ---------------------------------------------------------------------------
# 沙盒仓夹具
# ---------------------------------------------------------------------------

def _git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo)] + list(args),
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args} failed: {r.stderr}")
    return r


def _init_repo(tmp_path, name="repo", default_branch="main"):
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-b", default_branch)
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def _write(repo, rel, content=""):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _commit(repo, msg="c"):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", msg, "--allow-empty")


def _write_config(repo, body):
    """写 openspec/config.yaml，body 为 YAML 文本（不含 test-suites 外的必需键——
    yq 只读它需要的路径，其余键缺席不影响本子命令）。"""
    _write(repo, "openspec/config.yaml", body)


DOMAINS_CONFIG = """\
test-suites:
  domains:
    tools:
      paths: [hack/]
      layers:
        tools: "echo tools-cmd"
    project:
      default: true
      paths: [hack/run-tests.sh]
      layers:
        unit: "echo unit-cmd"
        integration: "echo integration-cmd"
        e2e: "echo e2e-cmd"
"""


def _base_repo_with_domains(tmp_path):
    """建仓：main 分支落基线 config + 一份 hack/foo.sh，切到 feature 分支供后续测试改动。"""
    repo = _init_repo(tmp_path)
    _write_config(repo, DOMAINS_CONFIG)
    _write(repo, "hack/foo.sh", "echo hi\n")
    _write(repo, "README.md", "readme\n")
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    return repo


def _run_suite_scope(repo, *, base=None, head=None, env=None, check_exit=None):
    cmd = [sys.executable, str(SCRIPT), "suite-scope", "--root", str(repo)]
    if base is not None:
        cmd += ["--base", base]
    if head is not None:
        cmd += ["--head", head]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                        env=env)
    if check_exit is not None:
        assert r.returncode == check_exit, (
            f"exit={r.returncode} (expected {check_exit})\nstdout={r.stdout}\nstderr={r.stderr}")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _parse(out):
    return json.loads(out)


# ---------------------------------------------------------------------------
# 纯工具域 / 纯项目域 / 跨域并集
# ---------------------------------------------------------------------------

def test_pure_tools_domain(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "echo bar\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is True
    assert data["hit_domains"] == ["tools"]
    assert data["layers"] == {"tools": {"quick": "echo tools-cmd", "full": "echo tools-cmd"}}
    assert data["skipped_layers"] == {
        "unit": "project", "integration": "project", "e2e": "project"}


def test_pure_project_domain(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "src/main.py", "print(1)\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["hit_domains"] == ["project"]
    assert data["layers"] == {
        "unit": {"quick": "echo unit-cmd", "full": "echo unit-cmd"},
        "integration": {"quick": "echo integration-cmd", "full": "echo integration-cmd"},
        "e2e": {"quick": "echo e2e-cmd", "full": "echo e2e-cmd"},
    }
    assert data["skipped_layers"] == {"tools": "tools"}


def test_cross_domain_union(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "echo bar\n")
    _write(repo, "src/main.py", "print(1)\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["hit_domains"] == ["project", "tools"]
    assert set(data["layers"].keys()) == {"tools", "unit", "integration", "e2e"}
    assert data["skipped_layers"] == {}


# ---------------------------------------------------------------------------
# [closeout-suite-scope-leftovers Task 2 用例①] 域声明顺序不影响输出
# ---------------------------------------------------------------------------

DOMAINS_CONFIG_REORDERED = """\
test-suites:
  domains:
    project:
      default: true
      paths: [hack/run-tests.sh]
      layers:
        unit: "echo unit-cmd"
        integration: "echo integration-cmd"
        e2e: "echo e2e-cmd"
    tools:
      paths: [hack/]
      layers:
        tools: "echo tools-cmd"
"""


def test_domain_declaration_order_does_not_affect_output(tmp_path):
    # [closeout-suite-scope-leftovers Task 2 用例①] 两份仅域声明顺序互换的 config，
    # 对同一变更集合求值，输出 JSON（按键排序规范化后）逐字相同——`_validate_domains`
    # 只按 `default: true` 与最长前缀判定，不依赖 YAML 映射键的声明顺序。
    repo_a = _init_repo(tmp_path, name="repo_a")
    _write_config(repo_a, DOMAINS_CONFIG)
    _write(repo_a, "hack/foo.sh", "echo hi\n")
    _commit(repo_a, "baseline")
    _git(repo_a, "checkout", "-b", "feat/x")
    _write(repo_a, "hack/bar.sh", "echo bar\n")
    _write(repo_a, "src/main.py", "print(1)\n")
    code_a, out_a, err_a = _run_suite_scope(repo_a, check_exit=0)

    repo_b = _init_repo(tmp_path, name="repo_b")
    _write_config(repo_b, DOMAINS_CONFIG_REORDERED)
    _write(repo_b, "hack/foo.sh", "echo hi\n")
    _commit(repo_b, "baseline")
    _git(repo_b, "checkout", "-b", "feat/x")
    _write(repo_b, "hack/bar.sh", "echo bar\n")
    _write(repo_b, "src/main.py", "print(1)\n")
    code_b, out_b, err_b = _run_suite_scope(repo_b, check_exit=0)

    data_a = _parse(out_a)
    data_b = _parse(out_b)
    # base/head 是各自沙盒仓的提交 SHA，天然不同；域顺序不影响输出的判据是「刨去
    # 这两个环境相关字段后逐字相同」，而不是整份 stdout 字面相等。
    for d in (data_a, data_b):
        del d["base"], d["head"]
    assert json.dumps(data_a, sort_keys=True) == json.dumps(data_b, sort_keys=True)


# ---------------------------------------------------------------------------
# domains 缺席 ⇒ 三层原样（逐字等同今日）
# ---------------------------------------------------------------------------

NO_DOMAINS_CONFIG_STRING = """\
test-suites:
  unit: "go test ./..."
  integration: "make integration"
"""

NO_DOMAINS_CONFIG_MAPPING = """\
test-suites:
  unit:
    quick: "go test -short ./..."
    full: "go test ./..."
  integration:
    full: "make integration"
"""


def test_domains_absent_string_layers_verbatim(tmp_path):
    # [impl-review-fix F1] 层集合逐字等同今日（只含配置里存在的层）；值不再原样透传——
    # 统一走 `_normalize_layer_value`（SKILL.md「聚合套件发现契约」第 2 条：消费方直接读
    # `layers[<层>].quick`/`.full`，规则对全部层名一致，无 unit 特例）。
    repo = _init_repo(tmp_path)
    _write_config(repo, NO_DOMAINS_CONFIG_STRING)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/main.go", "package main\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is False
    assert data["hit_domains"] == []
    assert data["skipped_layers"] == {}
    # 层集合等同今日（unit/integration 两层，无 e2e）；值统一规范化为 {quick, full}
    assert data["layers"] == {
        "unit": {"quick": "go test ./...", "full": "go test ./..."},
        "integration": {"quick": "make integration", "full": "make integration"},
    }


def test_domains_absent_mapping_layers_verbatim(tmp_path):
    # [impl-review-fix F1] 同上：层集合等同今日，值统一规范化（缺 full 的 integration 层
    # 被脚本补全为 quick==full，不再原样透传半截映射）。
    repo = _init_repo(tmp_path)
    _write_config(repo, NO_DOMAINS_CONFIG_MAPPING)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/main.go", "package main\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is False
    assert data["layers"] == {
        "unit": {"quick": "go test -short ./...", "full": "go test ./..."},
        "integration": {"quick": "make integration", "full": "make integration"},
    }


# ---------------------------------------------------------------------------
# [closeout-suite-scope-leftovers Task 2 用例②] domains 缺席时 mapping 三键齐全 + null
# ---------------------------------------------------------------------------

def test_domains_absent_mapping_fields_present_with_null(tmp_path):
    # [closeout-suite-scope-leftovers Task 2 用例②] `domains_configured=false` 时
    # `mapping[]` 每项仍 SHALL 含 `path`/`domain`/`prefix` 三键，`domain`/`prefix`
    # 恒为 `null`——字段 MUST NOT 省略（SKILL.md「聚合套件发现契约」第 0 条）。
    repo = _init_repo(tmp_path)
    _write_config(repo, NO_DOMAINS_CONFIG_STRING)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/main.go", "package main\n")
    _write(repo, "src/util.go", "package main\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is False
    assert data["mapping"] == [
        {"path": "src/main.go", "domain": None, "prefix": None},
        {"path": "src/util.go", "domain": None, "prefix": None},
    ]
    for item in data["mapping"]:
        assert set(item.keys()) == {"path", "domain", "prefix"}


def test_domains_absent_layer_value_bad_shape_exit6(tmp_path):
    # [impl-review-fix F1] 缺席路径层值形状非法（既非字符串也非 quick/full 映射）
    # ⇒ 与 domains 存在时的坏配置同路径退出 6，不再静默透传非法形状。
    config = """\
test-suites:
  unit: ["not", "a", "string"]
"""
    repo = _init_repo(tmp_path)
    _write_config(repo, config)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/main.go", "package main\n")
    code, out, err = _run_suite_scope(repo, check_exit=6)
    assert "problem:" in err and "cause:" in err and "fix:" in err


def test_domains_absent_no_test_suites_section_at_all(tmp_path):
    repo = _init_repo(tmp_path)
    _write_config(repo, "operations:\n  archive:\n    guidance: []\n")
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/main.go", "package main\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is False
    assert data["layers"] == {}


# ---------------------------------------------------------------------------
# 最长前缀 / 无尾斜杠精确匹配 / 默认域更长前缀胜出
# ---------------------------------------------------------------------------

def test_longest_prefix_exact_path_beats_dir_prefix(tmp_path):
    # hack/run-tests.sh 同时匹配 tools 域的 "hack/" 目录前缀与 project 默认域的精确路径
    # "hack/run-tests.sh"——后者更长，胜出，归默认域（design.md §1 示例）。
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/run-tests.sh", "#!/bin/sh\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    mapping = {m["path"]: m for m in data["mapping"]}
    assert mapping["hack/run-tests.sh"]["domain"] == "project"
    assert mapping["hack/run-tests.sh"]["prefix"] == "hack/run-tests.sh"
    assert data["hit_domains"] == ["project"]


def test_no_trailing_slash_exact_match_does_not_hit_similarly_named_dir(tmp_path):
    config = """\
test-suites:
  domains:
    tools:
      paths: [hack]
      layers:
        tools: "echo tools-cmd"
    project:
      default: true
      paths: []
      layers:
        unit: "echo unit-cmd"
"""
    repo = _init_repo(tmp_path)
    _write_config(repo, config)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "hackathon/notes.md", "x\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    mapping = {m["path"]: m for m in data["mapping"]}
    # "hack"（无尾斜杠）= 精确相等，不命中 "hackathon/notes.md" ⇒ 归默认域
    assert mapping["hackathon/notes.md"]["domain"] == "project"
    assert mapping["hackathon/notes.md"]["prefix"] is None


# ---------------------------------------------------------------------------
# openspec/ 硬排除
# ---------------------------------------------------------------------------

def test_openspec_paths_hard_excluded(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "openspec/changes/x/proposal.md", "why\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    paths = [m["path"] for m in data["mapping"]]
    assert not any(p.startswith("openspec/") for p in paths)
    # 只有 openspec/ 改动 ⇒ changed 有效集为空 ⇒ 保守落到默认域
    assert data["hit_domains"] == ["project"]


# ---------------------------------------------------------------------------
# 未跟踪文件计入 / 已删除文件按路径归域 / 空 changed ⇒ 默认域
# ---------------------------------------------------------------------------

def test_untracked_file_counted_in_worktree_mode(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/new-untracked.sh", "echo new\n")  # 不 add，不 commit
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    paths = [m["path"] for m in data["mapping"]]
    assert "hack/new-untracked.sh" in paths
    assert data["hit_domains"] == ["tools"]


def test_deleted_file_classified_by_its_own_path(tmp_path):
    # 文件须在 base（fork point）已存在，才会在 base→worktree 的 diff 里以「已删除」现身
    # ——若改在 feature 分支上先加后删（均在 base 之后），net diff 对 base 无差异，不会
    # 出现在 changed 集合里（这本身是 git diff 的正确行为，不是待测行为）。
    repo = _init_repo(tmp_path)
    _write_config(repo, DOMAINS_CONFIG)
    _write(repo, "hack/to-delete.sh", "echo del\n")
    _commit(repo, "baseline with file to delete")
    _git(repo, "checkout", "-b", "feat/x")
    (repo / "hack" / "to-delete.sh").unlink()
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    mapping = {m["path"]: m for m in data["mapping"]}
    assert mapping["hack/to-delete.sh"]["domain"] == "tools"


def test_empty_changed_falls_back_to_default_domain(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    # 未做任何改动（工作树与 base 完全一致，无未跟踪文件）
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["mapping"] == []
    assert data["hit_domains"] == ["project"]
    assert data["layers"] == {
        "unit": {"quick": "echo unit-cmd", "full": "echo unit-cmd"},
        "integration": {"quick": "echo integration-cmd", "full": "echo integration-cmd"},
        "e2e": {"quick": "echo e2e-cmd", "full": "echo e2e-cmd"},
    }


# ---------------------------------------------------------------------------
# --base 显式与自动 merge-base 一致 / --head 提交范围模式不含未跟踪
# ---------------------------------------------------------------------------

def test_explicit_base_matches_auto_merge_base(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "echo bar\n")
    auto_code, auto_out, _ = _run_suite_scope(repo, check_exit=0)
    merge_base_sha = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "main", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    explicit_code, explicit_out, _ = _run_suite_scope(repo, base=merge_base_sha, check_exit=0)
    assert _parse(auto_out) == _parse(explicit_out)


def test_head_commit_range_mode_excludes_untracked(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/committed.sh", "echo committed\n")
    _commit(repo, "committed change")
    head_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace").stdout.strip()
    _write(repo, "src/untracked.py", "print(1)\n")  # 未跟踪，提交范围模式应看不见
    merge_base_sha = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "main", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    code, out, err = _run_suite_scope(repo, base=merge_base_sha, head=head_sha, check_exit=0)
    data = _parse(out)
    paths = [m["path"] for m in data["mapping"]]
    assert "hack/committed.sh" in paths
    assert "src/untracked.py" not in paths
    assert data["head"] == head_sha


# ---------------------------------------------------------------------------
# 分档规范化 / layers: 空值 ≡ {}
# ---------------------------------------------------------------------------

def test_layer_normalization_string_missing_quick_missing_full(tmp_path):
    config = """\
test-suites:
  domains:
    project:
      default: true
      paths: []
      layers:
        a_string: "cmd-a"
        b_missing_quick:
          full: "cmd-b-full"
        c_missing_full:
          quick: "cmd-c-quick"
        integration_missing_quick:
          full: "cmd-int-full"
"""
    repo = _init_repo(tmp_path)
    _write_config(repo, config)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/x.py", "1\n")  # 触发默认域命中
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    layers = data["layers"]
    assert layers["a_string"] == {"quick": "cmd-a", "full": "cmd-a"}
    assert layers["b_missing_quick"] == {"quick": "cmd-b-full", "full": "cmd-b-full"}
    assert layers["c_missing_full"] == {"quick": "cmd-c-quick", "full": "cmd-c-quick"}
    # 非 unit 层同规则，无特例：缺 quick 同样取 full
    assert layers["integration_missing_quick"] == {"quick": "cmd-int-full", "full": "cmd-int-full"}


def test_layers_null_equals_empty_mapping(tmp_path):
    config = """\
test-suites:
  domains:
    docs:
      paths: [docs/]
      layers:
    project:
      default: true
      paths: []
      layers: {}
"""
    repo = _init_repo(tmp_path)
    _write_config(repo, config)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "docs/x.md", "1\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["hit_domains"] == ["docs"]
    assert data["layers"] == {}
    assert data["skipped_layers"] == {}


# ---------------------------------------------------------------------------
# merge-base 失败 ⇒ 退出 6（默认分支三段式兜底 "main" 但仓内实际不存在该分支）
# ---------------------------------------------------------------------------

def test_merge_base_failure_exit6_when_default_branch_absent(tmp_path):
    repo = _init_repo(tmp_path, default_branch="trunk")
    _commit(repo, "baseline")
    code, out, err = _run_suite_scope(repo, check_exit=6)
    assert out == ""
    assert "problem:" in err and "cause:" in err and "fix:" in err


def test_explicit_base_not_in_repo_exit6(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "baseline")
    code, out, err = _run_suite_scope(repo, base="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                                       check_exit=6)
    assert "problem:" in err


# ---------------------------------------------------------------------------
# 坏配置 8 类（各一例）
# ---------------------------------------------------------------------------

def _run_bad_config(tmp_path, config_body):
    repo = _init_repo(tmp_path)
    _write_config(repo, config_body)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/x.py", "1\n")
    return _run_suite_scope(repo, check_exit=6)


def test_bad_domains_explicit_null_is_present_but_bad(tmp_path):
    # [impl-review-fix F2] `domains:`（显式空值）是「键存在但坏」，MUST NOT 被误判为
    # 「键缺席」静默降级到今日三层透传路径——`test-suites` 顶层还残留 `unit` 亦不豁免
    # （domains 存在 ⇒ 走坏配置分支，不是并存冲突分支，二者判据独立）。
    code, out, err = _run_bad_config(tmp_path, "test-suites:\n  domains:\n")
    assert "problem:" in err and "cause:" in err and "fix:" in err


def test_domains_key_truly_absent_stays_domains_configured_false(tmp_path):
    # [impl-review-fix F2] 对照组：`domains` 键真缺席（顶层只有 unit）⇒ domains_configured
    # 仍为 false，走缺席路径，不受 F2 修复影响。
    repo = _init_repo(tmp_path)
    _write_config(repo, "test-suites:\n  unit: \"go test ./...\"\n")
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/x.py", "1\n")
    code, out, err = _run_suite_scope(repo, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is False


def test_bad_domains_not_a_mapping(tmp_path):
    code, out, err = _run_bad_config(tmp_path, "test-suites:\n  domains: []\n")
    assert "problem:" in err


def test_bad_domains_empty_mapping(tmp_path):
    code, out, err = _run_bad_config(tmp_path, "test-suites:\n  domains: {}\n")
    assert "problem:" in err


def test_bad_domain_missing_paths(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      default: true
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_domain_missing_layers(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      default: true
      paths: []
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_paths_not_a_string_list(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      default: true
      paths: "hack/"
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_layer_value_shape(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      default: true
      paths: []
      layers:
        unit:
          quick: "ok"
          bogus: "unknown-key"
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_no_default_domain(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      paths: []
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_multiple_default_domains(tmp_path):
    cfg = """\
test-suites:
  domains:
    a:
      default: true
      paths: [a/]
      layers: {}
    b:
      default: true
      paths: [b/]
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_default_value_not_boolean(tmp_path):
    cfg = """\
test-suites:
  domains:
    project:
      default: "true"
      paths: []
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_same_prefix_two_domains(tmp_path):
    cfg = """\
test-suites:
  domains:
    a:
      paths: [hack/]
      layers:
        a_layer: "cmd-a"
    b:
      default: true
      paths: [hack/]
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_same_domain_duplicate_path(tmp_path):
    # [closeout-suite-scope-leftovers T302] 同一域 paths 内出现重复字面路径——诊断 MUST NOT
    # 自指（不得表述为「域 'tools' 与 'tools'」），须指明「域 X 的 paths 内重复路径 p」。
    cfg = """\
test-suites:
  domains:
    tools:
      paths: [hack/, hack/]
      layers: {}
    project:
      default: true
      paths: []
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err
    assert "域 'tools' 的 paths 内重复路径 'hack/'" in err
    assert "域 'tools' 与 'tools'" not in err


def test_bad_same_layer_name_two_domains(tmp_path):
    cfg = """\
test-suites:
  domains:
    a:
      paths: [hack/]
      layers:
        unit: "cmd-a"
    b:
      default: true
      paths: []
      layers:
        unit: "cmd-b"
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err


def test_bad_domains_coexist_with_top_level_three_layers(tmp_path):
    cfg = """\
test-suites:
  unit: "go test ./..."
  domains:
    project:
      default: true
      paths: []
      layers: {}
"""
    code, out, err = _run_bad_config(tmp_path, cfg)
    assert "problem:" in err
    assert "domains" in err


# ---------------------------------------------------------------------------
# yq 缺失 / 身份不对 ⇒ 同路径退出 6（跨进程篡改 PATH——须保留 git 所在目录，只摘掉/
# 顶替真实 yq 所在目录，否则 git 本身先找不到、报的是无关的 FileNotFoundError）。
# ---------------------------------------------------------------------------

def _git_only_path_env(extra_dir=None):
    import os
    import shutil as _shutil
    git_bin = _shutil.which("git")
    assert git_bin, "本机需有 git 才能跑这组测试"
    git_dir = str(Path(git_bin).parent)
    parts = [str(extra_dir)] if extra_dir is not None else []
    parts.append(git_dir)
    env = dict(os.environ)
    env["PATH"] = ":".join(parts)
    return env


def test_cli_yq_missing_exit6(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "x\n")
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = _git_only_path_env(empty_bin)
    code, out, err = _run_suite_scope(repo, env=env, check_exit=6)
    assert "problem:" in err
    # [closeout-suite-scope-leftovers T304 用例⑥] fix 含安装指引
    assert "brew install yq" in err


def test_cli_yq_wrong_identity_exit6(tmp_path):
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "x\n")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_yq = fake_bin / "yq"
    fake_yq.write_text("#!/bin/sh\necho 'kislyuk/yq fakeversion'\nexit 0\n", encoding="utf-8")
    fake_yq.chmod(0o755)
    env = _git_only_path_env(fake_bin)
    code, out, err = _run_suite_scope(repo, env=env, check_exit=6)
    assert "problem:" in err


def test_cli_yq_version_probe_nonzero_exit6(tmp_path):
    # [closeout-suite-scope-leftovers T304 用例⑦] 伪 yq 对 --version 探针非零退出、无
    # stdout ⇒ 退出 6，problem 含「损坏或不可执行」，且不得误判为「不是 mikefarah」
    # （那是身份校验分支的措辞，两种成因 MUST 分流）。
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "x\n")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_yq = fake_bin / "yq"
    fake_yq.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_yq.chmod(0o755)
    env = _git_only_path_env(fake_bin)
    code, out, err = _run_suite_scope(repo, env=env, check_exit=6)
    assert "problem:" in err
    assert "损坏或不可执行" in err
    assert "重装" in err  # T308：fix 含重装指引
    assert "不是 mikefarah" not in err


def test_cli_yq_config_yaml_syntax_error_exit6(tmp_path):
    # [closeout-suite-scope-leftovers T304 用例④] config.yaml YAML 语法错误（未闭合 `[`）
    # ⇒ 退出 6，fix 不得含安装指引（这不是 yq 安装问题）。
    repo = _init_repo(tmp_path)
    _write_config(repo, "test-suites:\n  domains: [unclosed\n")
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/x.py", "1\n")
    code, out, err = _run_suite_scope(repo, check_exit=6)
    assert "problem:" in err
    assert "openspec/config.yaml" in err  # T307：fix 正面指向配置文件
    assert "brew install yq" not in err
    assert "winget install" not in err


def test_cli_yq_non_json_stdout_exit6(tmp_path):
    # [closeout-suite-scope-leftovers impl-review-fix A1] 伪 yq 身份校验通过、主调用 exit 0
    # 但 stdout 非 JSON ⇒ 退出 6 + 三段诊断（不得裸 traceback / exit 1），fix 不含安装指引。
    repo = _base_repo_with_domains(tmp_path)
    _write(repo, "hack/bar.sh", "x\n")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_yq = fake_bin / "yq"
    fake_yq.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in --version) echo 'yq (https://github.com/mikefarah/yq/) version v4.0.0';;"
        " *) echo 'this is not json';; esac\n",
        encoding="utf-8")
    fake_yq.chmod(0o755)
    env = _git_only_path_env(fake_bin)
    code, out, err = _run_suite_scope(repo, env=env, check_exit=6)
    assert "problem:" in err
    assert "非合法 JSON" in err
    assert "Traceback" not in err
    assert "brew install yq" not in err


def test_cli_yq_multi_document_yaml_exit6(tmp_path):
    # [closeout-suite-scope-leftovers T304 用例⑤] 多文档 YAML（`---` 分隔）⇒ 退出 6，
    # fix 提示合并单文档，不得含重装指引。
    repo = _init_repo(tmp_path)
    cfg = """\
test-suites:
  domains:
    project:
      default: true
      paths: []
      layers: {}
---
test-suites:
  domains:
    project:
      default: true
      paths: []
      layers: {}
"""
    _write_config(repo, cfg)
    _commit(repo, "baseline")
    _git(repo, "checkout", "-b", "feat/x")
    _write(repo, "src/x.py", "1\n")
    code, out, err = _run_suite_scope(repo, check_exit=6)
    assert "problem:" in err
    assert "合并" in err and "单文档" in err
    assert "brew install yq" not in err
    assert "winget install" not in err


# ---------------------------------------------------------------------------
# 非 UTF-8 路径：direct-call 测 surrogateescape 解码契约（macOS APFS 不接受非法字节
# 文件名，走真实文件系统无法可靠构造——直接测 _run_git_z 的解码逻辑更精确）。
# ---------------------------------------------------------------------------

def test_run_git_z_surrogateescape_decodes_invalid_utf8_without_crashing(tmp_path, monkeypatch):
    class _FakeResult:
        returncode = 0
        stdout = b"hack/\xffbad.sh\x00hack/good.sh\x00"
        stderr = b""

    def _fake_run(cmd, **kwargs):
        return _FakeResult()

    monkeypatch.setattr(ir.subprocess, "run", _fake_run)
    paths = ir._run_git_z(tmp_path, ["diff", "--name-only", "-z", "base"])
    assert len(paths) == 2
    assert "hack/good.sh" in paths
    bad = [p for p in paths if p != "hack/good.sh"][0]
    assert bad.startswith("hack/")
    # 非法字节经 surrogateescape 保真往返（无崩溃，无 U+FFFD 替换丢损）
    assert bad.encode("utf-8", errors="surrogateescape") == b"hack/\xffbad.sh"


def test_classify_changed_matches_non_utf8_path_by_ascii_prefix():
    domains = {
        "tools": {"paths": ["hack/"], "layers": {}},
    }
    bad_path = "hack/\udcffbad.sh"  # surrogateescape 解码后的形态
    hit, mapping = ir._classify_changed({bad_path}, domains, "project")
    assert hit == ["tools"]
    assert mapping[0]["domain"] == "tools"
    assert mapping[0]["prefix"] == "hack/"


# ---------------------------------------------------------------------------
# [impl-review-fix F3] --head 提交范围模式读 head 快照的 config，不读工作树
# ---------------------------------------------------------------------------

def test_head_mode_reads_config_from_head_snapshot_not_worktree(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "README.md", "r\n")
    _commit(repo, "root")
    root_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace").stdout.strip()
    _write_config(repo, DOMAINS_CONFIG)
    _write(repo, "hack/foo.sh", "echo hi\n")
    _commit(repo, "c1 with domains")
    c1_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace").stdout.strip()
    # 提交后弄脏工作树 config（不提交）——若工具错读工作树，domains 会"消失"，
    # 归域结果会跟 C1 的真实内容不一致。sdflow-done verify 正是在 code-review
    # 改过 config 之后重跑同命令，此处复现同一场景。
    _write_config(repo, "test-suites:\n  unit: \"legacy-worktree-cmd\"\n")
    code, out, err = _run_suite_scope(repo, base=root_sha, head=c1_sha, check_exit=0)
    data = _parse(out)
    assert data["domains_configured"] is True
    assert data["hit_domains"] == ["tools"]
    assert data["head"] == c1_sha


# ---------------------------------------------------------------------------
# [impl-review-fix F4] `_detect_default_branch` 三段式分支①②直接调用测
# ---------------------------------------------------------------------------

def test_detect_default_branch_reads_symbolic_ref(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "c")
    _git(repo, "remote", "add", "origin", str(tmp_path / "fake-origin"))
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/develop")
    assert ir._detect_default_branch(repo) == "develop"


def test_detect_default_branch_falls_back_to_origin_master_ref(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "c")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/master", sha)
    assert ir._detect_default_branch(repo) == "master"
