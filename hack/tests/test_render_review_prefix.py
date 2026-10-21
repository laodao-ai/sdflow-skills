"""`render-review-prefix.sh` 契约测试（task4，implement-workflow-optimization-2026-08-p4）。

【这测的是什么】评审 SKILL 镜 dispatch prompt 段① 稳定前缀渲染器：
`--layer code-review|spec-review` → stdout = 固定序（通则区块全文 + 内嵌通用契约段
+ 该层 base checklist 全文）。核心契约见 spec `specs/spec-workflow/spec.md`
Requirement「评审镜 dispatch prompt 按三段组装序构造，稳定前缀为脚本输出原文」：

1. **byte-stable**：同一规则集状态下，同 layer 连续两跑 stdout 逐字节相同。
2. **源缺失 fail-loud**：任一源（通则/resolver/base checklist）不可达 ⇒ 非零退出 +
   stderr 含 problem+cause+fix，**MUST NOT 输出半段前缀**（stdout 必须为空）。

【怎么跑】不碰真实 `~/.sdflow/`——用 `SDFLOW_HOME` 重定向到 `tmp_path` 自备的最小
canonical（既有测试隔离契约，`resolve-workflow.sh` 头注释「env: SDFLOW_HOME…测试用它
重定向，绝不写真实 $HOME」+ CLAUDE.md「开发期测试三层」第 2 层）。`resolve-workflow.sh`
本体用**真实仓源码**拷贝（不重新实现其逻辑），只有 canonical 内容是 fixture 造的最小
形状（过 `sane()` 的四件套：workflow.md / spec-checklists 非空 / code-checklists 非空 /
tools 非空 / lens-metric-contract.md 非空）。

【本文件照不到的面】resolve-workflow.sh 自身解析逻辑的正确性——那是它自己的测试职责
（本文件只当它是黑盒依赖，验证 render-review-prefix.sh 对其 exit code / stdout 的消费）。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="resolve-workflow.sh 不兼容 Windows 路径格式（SDFLOW_HOME C:\\... 被判非绝对路径）；"
    "这些测试在 mechanical-gates.yml 的 ubuntu runner 上已覆盖",
)

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "render-review-prefix.sh"
REAL_RESOLVER = REPO / "sdflow-init" / "assets" / "hack" / "resolve-workflow.sh"
REAL_PRINCIPLES = REPO / "sdflow-init" / "assets" / "hack" / "skill-principles.md"
REAL_CODE_CHECKLIST = (
    REPO / "sdflow-init" / "assets" / "workflow" / "code-checklists" / "code-review-base.md"
)
REAL_SPEC_CHECKLIST = (
    REPO / "sdflow-init" / "assets" / "workflow" / "spec-checklists" / "spec-quality-base.md"
)


def _make_sandbox_home(tmp_path: Path) -> Path:
    """造一个过 resolve-workflow.sh `sane()` 检查的最小 SDFLOW_HOME。"""
    home = tmp_path / "sdflow_home"
    hack = home / "hack"
    hack.mkdir(parents=True)
    (hack / "skill-principles.md").write_bytes(REAL_PRINCIPLES.read_bytes())
    (hack / "resolve-workflow.sh").write_bytes(REAL_RESOLVER.read_bytes())
    (hack / "resolve-workflow.sh").chmod(0o755)

    workflow = home / "workflow"
    (workflow / "spec-checklists").mkdir(parents=True)
    (workflow / "code-checklists").mkdir(parents=True)
    (workflow / "tools").mkdir(parents=True)
    (workflow / "workflow.md").write_text("# fixture workflow.md\n", encoding="utf-8")
    (workflow / "lens-metric-contract.md").write_text("# fixture contract\n", encoding="utf-8")
    (workflow / "tools" / "placeholder.py").write_text("# fixture\n", encoding="utf-8")
    (workflow / "code-checklists" / "code-review-base.md").write_bytes(
        REAL_CODE_CHECKLIST.read_bytes()
    )
    (workflow / "spec-checklists" / "spec-quality-base.md").write_bytes(
        REAL_SPEC_CHECKLIST.read_bytes()
    )
    # 占位文件：确保「删掉 base checklist 单个文件」不会把整个目录清空——resolve-workflow.sh
    # 的 sane() 检查目录非空即可通过（不检查具体成员），若目录因此变空，resolve-workflow.sh
    # 会先判「canonical 整体不可达」，掩盖了本文件真正要测的「base checklist 单文件缺失」场景。
    (workflow / "code-checklists" / "_placeholder.md").write_text("# fixture\n", encoding="utf-8")
    (workflow / "spec-checklists" / "_placeholder.md").write_text("# fixture\n", encoding="utf-8")
    return home


def _run(home: Path, *args: str):
    env = dict(os.environ)
    env["SDFLOW_HOME"] = str(home)
    return subprocess.run(
        [bash_executable(), bash_path(SCRIPT), *args],
        cwd=str(home),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        errors="replace",
    )


@pytest.fixture()
def sandbox_home(tmp_path):
    return _make_sandbox_home(tmp_path)


def test_script_is_executable():
    assert SCRIPT.exists(), f"缺 {SCRIPT}"
    assert os.access(SCRIPT, os.X_OK), "render-review-prefix.sh 必须可执行（chmod +x）"


@pytest.mark.parametrize("layer", ["code-review", "spec-review"])
def test_layer_produces_nonempty_output(sandbox_home, layer):
    r = _run(sandbox_home, "--layer", layer)
    assert r.returncode == 0, f"stderr:\n{r.stderr}"
    assert r.stdout.strip(), f"--layer {layer} 输出为空"


@pytest.mark.parametrize("layer", ["code-review", "spec-review"])
def test_output_is_byte_stable_across_two_runs(sandbox_home, layer):
    """同规则集状态下连续两跑，stdout 逐字节相同（spec Scenario：稳定前缀 byte-stable）。"""
    first = _run(sandbox_home, "--layer", layer)
    second = _run(sandbox_home, "--layer", layer)
    assert first.returncode == 0 and second.returncode == 0
    assert first.stdout == second.stdout, "两次运行 stdout 不是逐字节相同"


def test_output_contains_all_three_fixed_sections_in_order(sandbox_home):
    """固定序 = 通则区块 + 内嵌通用契约段 + base checklist 全文，三段都在且顺序不变。"""
    r = _run(sandbox_home, "--layer", "code-review")
    assert r.returncode == 0, f"stderr:\n{r.stderr}"
    out = r.stdout
    principles_marker = "sdflow:principles:start"
    contract_marker = "回传目标"  # T103 输出封顶句关键字
    checklist_text = REAL_CODE_CHECKLIST.read_text(encoding="utf-8")
    checklist_marker = checklist_text.strip().splitlines()[0]

    assert principles_marker in out
    assert contract_marker in out
    assert checklist_marker in out
    assert out.index(principles_marker) < out.index(contract_marker) < out.index(checklist_marker), (
        "三段顺序不对：MUST 是 通则 → 通用契约 → base checklist"
    )


def test_common_contract_section_has_required_clauses(sandbox_home):
    """内嵌通用契约段 MUST 含：结构化 findings schema / 引文纪律 / T103 输出封顶句 / 不问人。"""
    r = _run(sandbox_home, "--layer", "spec-review")
    assert r.returncode == 0, f"stderr:\n{r.stderr}"
    out = r.stdout
    assert "回传目标" in out and "≤2k token" in out, "缺 T103 输出封顶句"
    assert "引文" in out, "缺引文纪律"
    assert "findings" in out.lower(), "缺结构化 findings schema"
    assert "不问人" in out or "AskUserQuestion" in out, "缺不问人条款"


def test_missing_layer_arg_is_usage_error(sandbox_home):
    r = _run(sandbox_home)
    assert r.returncode != 0
    assert r.stdout == ""


def test_invalid_layer_value_is_usage_error(sandbox_home):
    r = _run(sandbox_home, "--layer", "bogus-layer")
    assert r.returncode != 0
    assert r.stdout == ""


def test_missing_principles_fails_loud_with_guidance(sandbox_home):
    (sandbox_home / "hack" / "skill-principles.md").unlink()
    r = _run(sandbox_home, "--layer", "code-review")
    assert r.returncode != 0
    assert r.stdout == "", "源缺失时 MUST NOT 输出半段前缀"
    assert "skill-principles" in r.stderr
    assert "setup.sh" in r.stderr, "stderr 须含修复动作指引（fix）"


def test_missing_resolver_fails_loud_with_guidance(sandbox_home):
    (sandbox_home / "hack" / "resolve-workflow.sh").unlink()
    r = _run(sandbox_home, "--layer", "code-review")
    assert r.returncode != 0
    assert r.stdout == ""
    assert "resolve-workflow" in r.stderr


def test_resolver_failure_propagates_fail_loud(sandbox_home):
    """resolve-workflow.sh 本体存在但解析失败（canonical 不 sane）⇒ 非零退出 + stderr，无半段输出。"""
    shutil.rmtree(sandbox_home / "workflow")
    r = _run(sandbox_home, "--layer", "code-review")
    assert r.returncode != 0
    assert r.stdout == ""
    assert r.stderr.strip() != ""


def test_missing_base_checklist_no_partial_output(sandbox_home):
    """base checklist 缺失 ⇒ 非零退出 + stdout 必须为空（MUST NOT 半段前缀，即便通则/契约段已就绪）。"""
    (sandbox_home / "workflow" / "code-checklists" / "code-review-base.md").unlink()
    r = _run(sandbox_home, "--layer", "code-review")
    assert r.returncode != 0
    assert r.stdout == "", "base checklist 缺失时不得输出通则等前段内容"
    assert "code-review-base" in r.stderr


def test_missing_base_checklist_other_layer_still_works(sandbox_home):
    """缺失只影响该 layer——同一 sandbox 下另一 layer（spec-review）不受影响，证明门是按需读取。"""
    (sandbox_home / "workflow" / "code-checklists" / "code-review-base.md").unlink()
    r = _run(sandbox_home, "--layer", "spec-review")
    assert r.returncode == 0, f"stderr:\n{r.stderr}"
    assert r.stdout.strip()


# ── implement-optimize-codex-workflow-quickwins · Task 1：新参数与写文件 ──────────
# 对应 design.md「渲染器接口」组合表，一行一个用例。

VARIANTS = ["spec-review", "spec-review-np", "code-review", "code-review-np", "principles"]


def _args_for(variant: str):
    if variant == "principles":
        return ["--layer", "principles"]
    if variant.endswith("-np"):
        return ["--layer", variant[:-3], "--no-principles"]
    return ["--layer", variant]


def _assert_three_part_stderr(stderr: str):
    for key in ("problem", "cause", "fix"):
        assert key in stderr, f"stderr 缺 {key} 段:\n{stderr}"


def test_legacy_stdout_unchanged_shape(sandbox_home):
    """行 1：不带新参数，stdout = 通则原文 + 契约 + checklist 原文（首尾由真实源文件独立给出）。"""
    for layer, checklist in (("code-review", REAL_CODE_CHECKLIST), ("spec-review", REAL_SPEC_CHECKLIST)):
        r = _run(sandbox_home, "--layer", layer)
        assert r.returncode == 0
        out = r.stdout.encode("utf-8")
        assert out.startswith(REAL_PRINCIPLES.read_bytes())
        assert out.endswith(checklist.read_bytes())
        assert "评审子代理通用契约" in r.stdout
        # 整段逐字节：通则文件字节 + --no-principles 输出
        no_principles = _run(sandbox_home, "--layer", layer, "--no-principles").stdout.encode("utf-8")
        assert out == REAL_PRINCIPLES.read_bytes() + no_principles


def test_layer_principles_outputs_principles_only(sandbox_home):
    """行 2：stdout = 通则段；不调 resolver、不读 checklist。"""
    (sandbox_home / "hack" / "resolve-workflow.sh").unlink()
    shutil.rmtree(sandbox_home / "workflow")
    r = _run(sandbox_home, "--layer", "principles")
    assert r.returncode == 0, r.stderr
    assert r.stdout.encode("utf-8") == REAL_PRINCIPLES.read_bytes()


@pytest.mark.parametrize("layer", ["code-review", "spec-review"])
def test_no_principles_outputs_contract_plus_checklist(sandbox_home, layer):
    """行 3：stdout = 契约 + checklist，不含通则。"""
    checklist = REAL_CODE_CHECKLIST if layer == "code-review" else REAL_SPEC_CHECKLIST
    full = _run(sandbox_home, "--layer", layer).stdout.encode("utf-8")
    r = _run(sandbox_home, "--layer", layer, "--no-principles")
    assert r.returncode == 0, r.stderr
    out = r.stdout.encode("utf-8")
    assert full == REAL_PRINCIPLES.read_bytes() + out
    assert out.endswith(checklist.read_bytes())
    assert "sdflow:principles:start" not in r.stdout


def test_principles_with_no_principles_is_usage_error(sandbox_home):
    """行 4。"""
    r = _run(sandbox_home, "--layer", "principles", "--no-principles")
    assert r.returncode == 64
    assert r.stdout == ""


@pytest.mark.parametrize("extra", [["--no-principles"], ["--out-dir", "x"]])
def test_new_flags_without_layer_is_usage_error(sandbox_home, extra):
    """行 5。"""
    r = _run(sandbox_home, *extra)
    assert r.returncode == 64
    assert r.stdout == ""


@pytest.mark.parametrize(
    "args",
    [
        ["--layer", "code-review", "--out-dir"],
        ["--layer", "code-review", "--out-dir", "--no-principles"],  # 值以 -- 开头按缺值处理
        ["--layer", "code-review", "--out-dir", ""],  # [impl-review-fix] 空串不得静默退回 stdout 模式
        ["--layer", "code-review", "--layer", "spec-review"],
        ["--layer", "code-review", "--no-principles", "--no-principles"],
        ["--layer", "code-review", "--out-dir", "a", "--out-dir", "b"],
    ],
)
def test_missing_value_or_duplicate_is_usage_error(sandbox_home, args):
    """行 6。"""
    r = _run(sandbox_home, *args)
    assert r.returncode == 64
    assert r.stdout == ""


@pytest.mark.parametrize("variant", VARIANTS)
def test_out_dir_writes_versioned_file_and_json(sandbox_home, tmp_path, variant):
    """行 7：文件名、首行版本、哈希与正文一致、JSON 字段。"""
    out_dir = tmp_path / "run"
    out_dir.mkdir()
    r = _run(sandbox_home, *_args_for(variant), "--out-dir", str(out_dir))
    assert r.returncode == 0, r.stderr
    info = json.loads(r.stdout)
    target = out_dir / f"prefix-{variant}.md"
    assert info["path"] == str(target.resolve())
    raw = target.read_bytes()
    assert info["bytes"] == len(raw)
    first, _, body = raw.partition(b"\n")
    sha12 = hashlib.sha256(body).hexdigest()[:12]
    assert first.decode() == f"<!-- prefix-version: {variant}-{sha12} -->"
    assert info["version"] == f"{variant}-{sha12}"
    # 正文与 stdout 模式一致（独立来源）
    plain = _run(sandbox_home, *_args_for(variant)).stdout.encode("utf-8")
    assert body == plain
    assert [p.name for p in out_dir.iterdir()] == [f"prefix-{variant}.md"], "不得残留临时文件"


@pytest.mark.parametrize("variant", VARIANTS)
def test_out_dir_rerender_is_byte_identical(sandbox_home, tmp_path, variant):
    d1, d2 = tmp_path / "a", tmp_path / "b"
    d1.mkdir()
    d2.mkdir()
    _run(sandbox_home, *_args_for(variant), "--out-dir", str(d1))
    _run(sandbox_home, *_args_for(variant), "--out-dir", str(d2))
    assert (d1 / f"prefix-{variant}.md").read_bytes() == (d2 / f"prefix-{variant}.md").read_bytes()


def test_relative_out_dir_yields_absolute_path(sandbox_home):
    (sandbox_home / "rel").mkdir()
    r = _run(sandbox_home, "--layer", "principles", "--out-dir", "rel")
    assert r.returncode == 0, r.stderr
    path = json.loads(r.stdout)["path"]
    assert os.path.isabs(path)
    assert Path(path) == (sandbox_home / "rel" / "prefix-principles.md").resolve()
    assert Path(path).exists()


def test_out_dir_nonexistent_is_exit2_no_file(sandbox_home, tmp_path):
    r = _run(sandbox_home, "--layer", "code-review", "--out-dir", str(tmp_path / "nope"))
    assert r.returncode == 2
    assert r.stdout == ""
    _assert_three_part_stderr(r.stderr)
    assert not (tmp_path / "nope").exists()


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 不受目录权限约束")
def test_out_dir_unwritable_is_exit2_no_file(sandbox_home, tmp_path):
    d = tmp_path / "ro"
    d.mkdir()
    d.chmod(0o555)
    try:
        r = _run(sandbox_home, "--layer", "code-review", "--out-dir", str(d))
        assert r.returncode == 2
        assert r.stdout == ""
        _assert_three_part_stderr(r.stderr)
        assert list(d.iterdir()) == []
    finally:
        d.chmod(0o755)


def test_out_dir_without_python3_is_exit2_no_file(sandbox_home, tmp_path):
    """[impl-review-fix] PATH 里没有 python3：exit 2 + 三段 stderr，而非 shell 裸 127。"""
    d = tmp_path / "run"
    d.mkdir()
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = dict(os.environ)
    env["SDFLOW_HOME"] = str(sandbox_home)
    env["PATH"] = str(empty_bin)
    r = subprocess.run(
        [bash_executable(), bash_path(SCRIPT), "--layer", "principles", "--out-dir", str(d)],
        cwd=str(sandbox_home),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 2
    assert r.stdout == ""
    _assert_three_part_stderr(r.stderr)
    assert "python3" in r.stderr
    assert list(d.iterdir()) == []


def test_unknown_arg_three_part_stderr(sandbox_home):
    """行 8：未知参数 exit 64，stderr 三段指向 setup.sh。"""
    r = _run(sandbox_home, "--layer", "code-review", "--bogus")
    assert r.returncode == 64
    assert r.stdout == ""
    _assert_three_part_stderr(r.stderr)
    assert "setup.sh" in r.stderr
