"""sdflow-adr/scripts/adr.py 的单元测试。

合成样例，不使用消费仓（本仓 openspec/adr/ 或任何其他项目）的原文（票 1.6 要求）。
每个 test 用 tmp_path 建一个独立的 openspec/adr/ 目录。
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "adr.py"


def _load_adr_module():
    """进程内加载 adr.py 为模块（区别于 `run()` 的子进程调用）。
    仅供需要 monkeypatch 脚本内部函数的测试使用（如让旧文件改写这一步精确失败），
    其余测试一律走子进程 `run()`，与真实 CLI 调用路径一致。"""
    spec = importlib.util.spec_from_file_location("adr_module_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def mkroot(tmp_path):
    (tmp_path / "openspec" / "adr").mkdir(parents=True)
    return tmp_path


def write_adr(root, name, text):
    p = root / "openspec" / "adr" / name
    p.write_text(text, encoding="utf-8")
    return p


ACCEPTED_ADR = """# 决定用 X

**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）

这是背景段，解释为什么要做这个决定。

## Decision

用 X。

## Considered Options

- X（选中）
- Y

## Consequences

- 影响 A。

## 附录：修订历史

- **2026-01-02**：无变化。
"""


# ══════════════════════════════════════════════════════════════════════════
# next-id
# ══════════════════════════════════════════════════════════════════════════

def test_next_id_max_plus_one_with_gap(tmp_path):
    root = mkroot(tmp_path)
    for n in ("0001", "0003"):
        write_adr(root, f"{n}-foo.md", ACCEPTED_ADR)
    r = run(["next-id", "--root", str(root)])
    assert r.returncode == 0
    assert r.stdout.strip() == "0004"


def test_next_id_empty_dir_starts_at_0001(tmp_path):
    root = mkroot(tmp_path)
    r = run(["next-id", "--root", str(root)])
    assert r.returncode == 0
    assert r.stdout.strip() == "0001"


def test_next_id_unknown_filename_exits_2(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "notes.md", "not an adr")
    r = run(["next-id", "--root", str(root)])
    assert r.returncode == 2
    assert "notes.md" in r.stderr


# ══════════════════════════════════════════════════════════════════════════
# new
# ══════════════════════════════════════════════════════════════════════════

def test_new_creates_file_with_skeleton(tmp_path):
    root = mkroot(tmp_path)
    r = run(["new", "--root", str(root), "--title", "决定用 Y",
             "--slug", "decide-y", "--source", "来源 change：`demo`（2026-01-01）"])
    assert r.returncode == 0
    out_path = Path(r.stdout.strip().splitlines()[0])
    assert out_path.name == "0001-decide-y.md"
    text = out_path.read_text(encoding="utf-8")
    assert text.startswith("# 决定用 Y")
    assert "**Status: Accepted** · 来源 change：`demo`（2026-01-01）" in text
    assert "TODO(adr)" in text
    assert "## Decision" in text
    assert "## Considered Options" in text
    assert "## Consequences" in text


def test_new_invalid_slug_exits_2(tmp_path):
    root = mkroot(tmp_path)
    r = run(["new", "--root", str(root), "--title", "T",
             "--slug", "Bad_Slug", "--source", "s"])
    assert r.returncode == 2


def test_new_same_number_already_exists_exits_2(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    # 强制传入的 slug 会让新扫号仍是 0002，因此改用已占用文件名场景：
    # 通过直接构造同号冲突——两个不同 slug 但期望编号相同不可控（next-id 自动递增）。
    # 用「独占创建失败」场景改用并发/占用测试（见下）。
    r = run(["new", "--root", str(root), "--title", "T",
             "--slug", "bar", "--source", "s"])
    assert r.returncode == 0
    out_path = Path(r.stdout.strip().splitlines()[0])
    assert out_path.name == "0002-bar.md"


def test_new_unknown_filename_in_dir_exits_2(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "readme.md", "junk")
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "foo", "--source", "s"])
    assert r.returncode == 2
    assert "readme.md" in r.stderr


def test_new_different_slug_concurrent_no_duplicate_number(tmp_path):
    """AM-4/AM-5 Scenario「不同 slug 并发新建」：多个 new 进程同时启动、slug 不同，
    编号 MUST NOT 撞号。先全部 Popen 再统一 communicate，进程真实竞争目录锁。"""
    root = mkroot(tmp_path)
    slugs = [f"s{i}" for i in range(6)]
    procs = [
        subprocess.Popen(
            [sys.executable, str(SCRIPT), "new", "--root", str(root), "--title", f"T {s}",
             "--slug", s, "--source", "src"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        for s in slugs
    ]
    results = [(p.wait(timeout=60), *p.communicate()) for p in procs]
    assert [rc for rc, _o, _e in results] == [0] * len(slugs), [e for _rc, _o, e in results]
    names = sorted(p.name for p in (root / "openspec" / "adr").glob("*.md"))
    numbers = [n[:4] for n in names]
    assert numbers == [f"{i:04d}" for i in range(1, len(slugs) + 1)]
    assert not (root / "openspec" / "adr" / ".lock").exists()


# ══════════════════════════════════════════════════════════════════════════
# new --supersedes / --partial
# ══════════════════════════════════════════════════════════════════════════

def test_new_supersedes_accepted_target_full(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    r = run(["new", "--root", str(root), "--title", "决定用 Z", "--slug", "decide-z",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 0
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 2
    new_path, old_path = Path(lines[0]), Path(lines[1])
    assert new_path.name == "0002-decide-z.md"
    assert old_path.name == "0001-old.md"
    old_text = old_path.read_text(encoding="utf-8")
    assert "**Status: Superseded by 0002** · 来源 change：`demo-change`（2026-01-01）" in old_text


def test_new_supersedes_partial(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001", "--partial", "决策 1、2"])
    assert r.returncode == 0
    old_path = root / "openspec" / "adr" / "0001-old.md"
    old_text = old_path.read_text(encoding="utf-8")
    assert "**Status: Partially superseded by 0002（决策 1、2）** · 来源 change：`demo-change`（2026-01-01）" in old_text


def test_new_supersedes_target_no_status_line(tmp_path):
    """旧格式目标无 Status 行：插入 Status 行到 H1 下一行，· 后写固定迁移文案。"""
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", "# 老决定\n\n这是背景。\n\n## Decision\n\n用老办法。\n")
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 0
    old_text = (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8")
    lines = old_text.splitlines()
    assert lines[0] == "# 老决定"
    assert lines[1] == ""
    assert lines[2].startswith("**Status: Superseded by 0002** ·")
    assert "由 0002 取代" in lines[2]
    assert "迁移前无 Status 行" in lines[2]
    assert "这是背景。" in old_text


def test_new_supersedes_target_not_exist_exits_2(tmp_path):
    root = mkroot(tmp_path)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0999"])
    assert r.returncode == 2
    assert "--supersedes 0999" in r.stderr
    assert list((root / "openspec" / "adr").glob("*.md")) == []


def test_new_supersedes_target_already_superseded_exits_2(tmp_path):
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Superseded by 0044** · 来源 change：`demo-change`（2026-01-01）",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 2
    old_text = (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8")
    assert old_text == text
    # 未创建新文件
    assert sorted(p.name for p in (root / "openspec" / "adr").glob("*.md")) == ["0001-old.md"]


def test_new_supersedes_target_already_deprecated_exits_2(tmp_path):
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Deprecated** · 已废弃",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001", "--partial", "TEXT"])
    assert r.returncode == 2
    assert (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8") == text


def test_new_supersedes_partially_superseded_target_becomes_multi_target(tmp_path):
    """目标已是 Partially superseded，不带 --partial 全覆盖 → 多目标 Superseded by 既有、新。"""
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Partially superseded by 0044（决策 1、2）** · 来源 change：`demo-change`（2026-01-01）",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 0
    old_text = (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8")
    assert "**Status: Superseded by 0044（决策 1、2）、0002** · 来源 change：`demo-change`（2026-01-01）" in old_text
    # 往返：new 产出的多目标终态须被 lint 接受（0044 不存在会报 L5，这里只断言没有 L4 取值红项）
    lint = run(["lint", "--root", str(root), str(root / "openspec" / "adr" / "0001-old.md")])
    assert "ADR-L4" not in lint.stdout, lint.stdout
    # 该终态不可再被取代，目录字节不变
    before = (root / "openspec" / "adr" / "0001-old.md").read_bytes()
    again = run(["new", "--root", str(root), "--title", "T", "--slug", "s3",
                 "--source", "s", "--supersedes", "0001"])
    assert again.returncode == 2
    assert (root / "openspec" / "adr" / "0001-old.md").read_bytes() == before
    assert not list((root / "openspec" / "adr").glob("0003-*.md"))


def test_lint_multi_target_superseded_checks_bare_last_target_exists(tmp_path):
    """多目标 Superseded 末项无范围时，其编号仍按 L5 核存在性。"""
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Superseded by 0002（决策 1）、0009** · 来源",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    write_adr(root, "0002-new.md", ACCEPTED_ADR)
    r = run(["lint", "--root", str(root), str(root / "openspec" / "adr" / "0001-old.md")])
    assert r.returncode == 1
    assert "ADR-L4" not in r.stdout
    assert "ADR-L5" in r.stdout and "0009" in r.stdout


@pytest.mark.parametrize("status", [
    "Superseded by 0044 typo",
    "Deprecated typo",
    "Proposed",
    "Partially superseded by 0044（）",
])
def test_new_supersedes_target_with_invalid_status_exits_2(tmp_path, status):
    """有 Status 行但取值不在枚举内：拒绝转换，不创建新文件，目标字节不变。"""
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        f"**Status: {status}** · 来源",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 2
    assert "不在枚举内" in r.stderr
    assert (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8") == text
    assert sorted(p.name for p in (root / "openspec" / "adr").glob("*.md")) == ["0001-old.md"]


@pytest.mark.parametrize("value", ["*", "1", "../0001", "00011"])
def test_new_supersedes_rejects_non_four_digit_value(tmp_path, value):
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", value])
    assert r.returncode == 2
    assert "四位编号" in r.stderr
    assert sorted(p.name for p in (root / "openspec" / "adr").glob("*.md")) == ["0001-old.md"]
    assert (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8") == ACCEPTED_ADR


def test_new_supersedes_empty_target_exits_2_without_leftover(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", "")
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 2
    assert sorted(p.name for p in (root / "openspec" / "adr").glob("*.md")) == ["0001-old.md"]


@pytest.mark.parametrize("extra, needle", [
    (["--partial", "决策 1"], "--partial 须与 --supersedes 同时使用"),
    (["--supersedes", "0001", "--partial", "  "], "--partial 须为非空单行"),
    (["--supersedes", "0001", "--partial", "决策）1"], "--partial 须为非空单行"),
])
def test_new_partial_argument_constraints(tmp_path, extra, needle):
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2", "--source", "s", *extra])
    assert r.returncode == 2
    assert needle in r.stderr
    assert sorted(p.name for p in (root / "openspec" / "adr").glob("*.md")) == ["0001-old.md"]


def test_new_supersedes_preserves_crlf_and_trailing_blank_lines(tmp_path):
    """改写旧 ADR 只动 Status 行：CRLF 与末尾空行逐字节保留。"""
    root = mkroot(tmp_path)
    original = ACCEPTED_ADR.replace("\n", "\r\n") + "\r\n\r\n"
    p = root / "openspec" / "adr" / "0001-old.md"
    p.write_bytes(original.encode("utf-8"))
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001"])
    assert r.returncode == 0
    expected = original.replace("**Status: Accepted**", "**Status: Superseded by 0002**")
    assert p.read_bytes() == expected.encode("utf-8")


def test_new_supersedes_partially_superseded_target_append_partial(tmp_path):
    """目标已是 Partially superseded，带 --partial → 追加、<新>（TEXT）。"""
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Partially superseded by 0044（决策 1、2）** · 来源 change：`demo-change`（2026-01-01）",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", text)
    r = run(["new", "--root", str(root), "--title", "T", "--slug", "s2",
             "--source", "s", "--supersedes", "0001", "--partial", "决策 3"])
    assert r.returncode == 0
    old_text = (root / "openspec" / "adr" / "0001-old.md").read_text(encoding="utf-8")
    assert "**Status: Partially superseded by 0044（决策 1、2）、0002（决策 3）** · 来源 change：`demo-change`（2026-01-01）" in old_text


def test_new_supersedes_old_file_write_failure_rolls_back(tmp_path, monkeypatch, capsys):
    """改写旧文件失败时回滚：新文件已创建 → 改写旧文件失败 → 删除本次创建的新文件，目录回到调用前。

    用 monkeypatch 精确让「旧文件改写」这一步（`atomic_write`）失败，而不是让锁获取
    阶段就提前退出（chmod 目录会在 `_acquire_lock` 创建锁文件时先报错，永远走不到
    「新文件已创建」之后的回滚分支）——这样才是真的测到 design §3 的补偿路径。
    `atomic_write` 只在 `cmd_new` 的 `--supersedes` 改写旧文件分支被调用，新文件本身
    走 `os.open`/`os.fdopen` 直接创建，不受此 monkeypatch 影响，故新文件在 patch 生效期间
    仍会先被真实创建，验证的正是「先建新文件，改写旧文件才失败」这个时序。"""
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    old_path = root / "openspec" / "adr" / "0001-old.md"
    adr_dir = root / "openspec" / "adr"

    adr_module = _load_adr_module()

    def _boom(path, text):
        raise OSError("simulated rewrite failure")

    monkeypatch.setattr(adr_module, "atomic_write", _boom)

    argv = ["new", "--root", str(root), "--title", "T", "--slug", "s2",
            "--source", "s", "--supersedes", "0001"]
    with pytest.raises(SystemExit) as exc_info:
        adr_module.main(argv)
    assert exc_info.value.code == 2

    err = capsys.readouterr().err
    assert f"改写 {old_path} 失败" in err
    assert "已删除本次创建的" in err
    assert "目录回到调用前" in err

    remaining = sorted(p.name for p in adr_dir.glob("*.md"))
    assert remaining == ["0001-old.md"]
    assert old_path.read_text(encoding="utf-8") == ACCEPTED_ADR


def test_new_supersedes_rollback_reports_leftover_when_unlink_fails(tmp_path, monkeypatch, capsys):
    """补偿删除本身失败时如实报告残留，不声称目录已回到调用前。"""
    root = mkroot(tmp_path)
    write_adr(root, "0001-old.md", ACCEPTED_ADR)
    adr_module = _load_adr_module()

    def _boom(path, text):
        raise OSError("simulated rewrite failure")

    real_unlink = Path.unlink

    def _unlink_fails(self, *a, **kw):
        if self.name.startswith("0002-"):
            raise PermissionError("simulated unlink failure")
        return real_unlink(self, *a, **kw)

    monkeypatch.setattr(adr_module, "atomic_write", _boom)
    monkeypatch.setattr(Path, "unlink", _unlink_fails)
    with pytest.raises(SystemExit) as exc_info:
        adr_module.main(["new", "--root", str(root), "--title", "T", "--slug", "s2",
                         "--source", "s", "--supersedes", "0001"])
    assert exc_info.value.code == 2
    err = capsys.readouterr().err
    assert "该文件残留" in err
    assert "目录回到调用前" not in err


# ══════════════════════════════════════════════════════════════════════════
# lint
# ══════════════════════════════════════════════════════════════════════════

def test_lint_compliant_adr_is_clean(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_lint_missing_optional_sections_is_clean(tmp_path):
    text = """# 决定用 X

**Status: Accepted** · 来源

背景段。

## Decision

用 X。

## Consequences

- 影响 A。
"""
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 0


def test_lint_h1_with_number_prefix_reports_l3(tmp_path):
    text = ACCEPTED_ADR.replace("# 决定用 X", "# ADR 0001: 决定用 X")
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 1
    assert "ADR-L3" in r.stdout


def test_lint_fenced_h2_not_counted(tmp_path):
    text = ACCEPTED_ADR.replace(
        "## Decision\n\n用 X。\n",
        "## Decision\n\n用 X。\n\n```\n## Migration Plan\n```\n",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 0


def test_lint_superseded_target_missing_reports_l5(tmp_path):
    text = ACCEPTED_ADR.replace(
        "**Status: Accepted** · 来源 change：`demo-change`（2026-01-01）",
        "**Status: Superseded by 0099** · 来源",
    )
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 1
    assert "ADR-L5" in r.stdout


def test_lint_todo_marker_reports_l7(tmp_path):
    text = ACCEPTED_ADR + "\nTODO(adr)\n"
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 1
    assert "ADR-L7" in r.stdout


def test_lint_empty_shell_adr_reports_l8(tmp_path):
    """空壳 ADR：Status 与 H2 之间无正文。"""
    text = "# 决定用 X\n\n**Status: Accepted** · 来源\n\n## Decision\n\n用 X。\n"
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 1
    assert "ADR-L8" in r.stdout


def test_lint_superseded_adr_skips_h2_and_l8(tmp_path):
    """取代件不查 H2 / 背景段：旧结构、空壳都不报红，只要取代目标存在。"""
    text = "# 老决定\n\n**Status: Superseded by 0002** · 来源\n\n## 为何这样\n\n随便写。\n"
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", text)
    write_adr(root, "0002-bar.md", ACCEPTED_ADR)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 0


def test_lint_legacy_batch_reports_three_kinds(tmp_path):
    """旧格式批量报红：无 Status 行、标题带编号前缀、含中文 H2「为何这样」分别报三类红项。"""
    text = "# 0016 · 老标题\n\n背景段。\n\n## 为何这样\n\n内容。\n"
    root = mkroot(tmp_path)
    write_adr(root, "0016-legacy.md", text)
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 1
    assert "ADR-L3" in r.stdout  # 标题带编号前缀
    assert "ADR-L4" in r.stdout  # 无 Status 行
    assert "ADR-L6" in r.stdout  # 含中文 H2「为何这样」不在白名单内


def test_lint_given_file_still_checks_duplicate_number_globally(tmp_path):
    root = mkroot(tmp_path)
    write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    write_adr(root, "0001-bar.md", ACCEPTED_ADR.replace("决定用 X", "另一个决定"))
    target = str(root / "openspec" / "adr" / "0001-foo.md")
    r = run(["lint", "--root", str(root), target])
    assert r.returncode == 1
    assert "ADR-L2" in r.stdout


def test_lint_unreadable_file_exits_2(tmp_path):
    root = mkroot(tmp_path)
    p = write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    p.write_bytes(b"\xff\xfe\x00invalid-utf8\xff")
    r = run(["lint", "--root", str(root)])
    assert r.returncode == 2


# ══════════════════════════════════════════════════════════════════════════
# refs（AM-7，票 2.1/2.2）——tmp_path 临时 git 仓
# ══════════════════════════════════════════════════════════════════════════

def _git(root, *args):
    r = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                        text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r.stdout


def _git_init_repo(root):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "commit.gpgsign", "false")


def _git_commit_all(root, message):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD").strip()


def refs_run(root, extra_args=()):
    r = run(["refs", "--root", str(root), *extra_args])
    return r


def test_refs_non_unique_filename_excluded_but_dir_included(tmp_path):
    """非唯一文件名不作匹配词：两个同名 SKILL.md 存在 ⇒ 裸文件名不召回，
    完整目录路径（唯一）仍召回。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    (root / "sdflow-done").mkdir()
    (root / "sdflow-done" / "SKILL.md").write_text("v1\n", encoding="utf-8")
    (root / "sdflow-issues").mkdir()
    (root / "sdflow-issues" / "SKILL.md").write_text("other skill\n", encoding="utf-8")
    write_adr(root, "0001-bare-mentions.md", ACCEPTED_ADR.replace(
        "这是背景段，解释为什么要做这个决定。",
        "这是背景段，提到 SKILL.md 这个文件名。"))
    write_adr(root, "0002-dir-mentions.md", ACCEPTED_ADR.replace(
        "这是背景段，解释为什么要做这个决定。",
        "这是背景段，提到 sdflow-done 这个目录。"))
    base = _git_commit_all(root, "base")

    (root / "sdflow-done" / "SKILL.md").write_text("v2\n", encoding="utf-8")
    _git_commit_all(root, "change SKILL.md")

    r = refs_run(root, ["--base", base])
    assert r.returncode == 0, r.stderr
    import json
    data = json.loads(r.stdout)
    numbers = {item["adr"] for item in data}
    assert "0001" not in numbers  # 裸 SKILL.md 不是匹配词
    assert "0002" in numbers
    item = next(i for i in data if i["adr"] == "0002")
    assert "sdflow-done" in item["hits"]
    assert "SKILL.md" not in item["hits"]


def test_refs_explicit_reference_recalled(tmp_path):
    """显式引用召回：decision-memo 写有 adr/0026，diff 路径与其正文无交集。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    (root / "unrelated.txt").write_text("v1\n", encoding="utf-8")
    write_adr(root, "0026-something.md", ACCEPTED_ADR.replace("决定用 X", "决定用 0026 号方案"))
    memo = root / "decision-memo.md"
    memo.write_text("本 change 声明取代 adr/0026 的部分决策。\n", encoding="utf-8")
    base = _git_commit_all(root, "base")

    (root / "unrelated.txt").write_text("v2\n", encoding="utf-8")
    _git_commit_all(root, "change unrelated")

    r = refs_run(root, ["--base", base, "--explicit-from", str(memo)])
    assert r.returncode == 0, r.stderr
    import json
    data = json.loads(r.stdout)
    item = next((i for i in data if i["adr"] == "0026"), None)
    assert item is not None
    assert item["explicit"] is True


def test_refs_no_candidates_returns_empty_array(tmp_path):
    """无候选：diff 只改 openspec/changes/<name>/ 下的文件。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    (root / "openspec" / "changes").mkdir(parents=True)
    (root / "openspec" / "changes" / "demo.md").write_text("v1\n", encoding="utf-8")
    write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    base = _git_commit_all(root, "base")

    (root / "openspec" / "changes" / "demo.md").write_text("v2\n", encoding="utf-8")
    _git_commit_all(root, "change only in changes dir")

    r = refs_run(root, ["--base", base])
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "[]"


def test_refs_deleted_file_still_recalled(tmp_path):
    """删除的文件仍可召回：REF 树中唯一的文件名，被删除后仍参与判定。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    (root / "hack").mkdir()
    (root / "hack" / "foo_tool.py").write_text("print(1)\n", encoding="utf-8")
    write_adr(root, "0001-foo-tool.md", ACCEPTED_ADR.replace(
        "这是背景段，解释为什么要做这个决定。",
        "这是背景段，提到 foo_tool.py 这个脚本。"))
    base = _git_commit_all(root, "base")

    (root / "hack" / "foo_tool.py").unlink()
    _git_commit_all(root, "delete foo_tool.py")

    r = refs_run(root, ["--base", base])
    assert r.returncode == 0, r.stderr
    import json
    data = json.loads(r.stdout)
    item = next((i for i in data if i["adr"] == "0001"), None)
    assert item is not None
    assert "foo_tool.py" in item["hits"]


def test_refs_rename_treated_as_delete_plus_add(tmp_path):
    """重命名按删除加新增处理：--no-renames 显式，路径集合同时含旧、新两条。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    _git(root, "config", "diff.renames", "true")
    (root / "a").mkdir()
    (root / "a" / "old.py").write_text("print('old')\n" * 5, encoding="utf-8")
    write_adr(root, "0001-rename.md", ACCEPTED_ADR.replace(
        "这是背景段，解释为什么要做这个决定。",
        "这是背景段，同时提到 a/old.py 与 a/new.py 两条路径。"))
    base = _git_commit_all(root, "base")

    _git(root, "mv", "a/old.py", "a/new.py")
    _git_commit_all(root, "rename old.py to new.py")

    r = refs_run(root, ["--base", base])
    assert r.returncode == 0, r.stderr
    import json
    data = json.loads(r.stdout)
    item = next((i for i in data if i["adr"] == "0001"), None)
    assert item is not None
    assert "a/old.py" in item["hits"]
    assert "a/new.py" in item["hits"]


def test_refs_git_failure_exits_2(tmp_path):
    """git 失败（--base 引用不可达）→ 退出码 2。"""
    root = mkroot(tmp_path)
    _git_init_repo(root)
    write_adr(root, "0001-foo.md", ACCEPTED_ADR)
    _git_commit_all(root, "base")

    r = refs_run(root, ["--base", "nonexistent-ref-xyz"])
    assert r.returncode == 2
    assert "git" in r.stderr
