"""delta_sync_check.py：归档后核对 delta 已同步进主 spec（T390）。"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "delta_sync_check.py"


def _spec(*names):
    body = "".join(f"### Requirement: {n}\n\n系统 SHALL 做 {n}。\n\n#### Scenario: s\n- **WHEN** x\n- **THEN** y\n\n"
                   for n in names)
    return f"# cap Specification\n\n## Purpose\np\n\n## Requirements\n\n{body}"


def _layout(tmp_path, delta_text, main_text=None, cap="cap"):
    root = tmp_path / "openspec"
    archive = root / "changes" / "archive" / "2026-10-21-demo"
    (archive / "specs" / cap).mkdir(parents=True)
    (archive / "specs" / cap / "spec.md").write_text(delta_text, encoding="utf-8")
    (root / "specs").mkdir(parents=True)
    if main_text is not None:
        (root / "specs" / cap).mkdir()
        (root / "specs" / cap / "spec.md").write_text(main_text, encoding="utf-8")
    return archive


def _run(archive):
    return subprocess.run([sys.executable, str(SCRIPT), "--archive-dir", str(archive)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_fully_synced_delta_passes(tmp_path):
    delta = ("## ADDED Requirements\n\n### Requirement: 新增\n\nSHALL\n\n"
             "## MODIFIED Requirements\n\n### Requirement: 修改\n\nSHALL\n\n"
             "## REMOVED Requirements\n\n### Requirement: 删掉\n\n"
             "## RENAMED Requirements\n\n- FROM: `### Requirement: 旧名`\n- TO: `### Requirement: 新名`\n")
    r = _run(_layout(tmp_path, delta, _spec("新增", "修改", "新名")))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "✓" in r.stdout


def test_each_gap_kind_is_reported(tmp_path):
    delta = ("## ADDED Requirements\n\n### Requirement: 漏了\n\nSHALL\n\n"
             "## MODIFIED Requirements (补充) [spec-review-amendment]\n\n### Requirement: 追加了两份\n\nSHALL\n\n"
             "## REMOVED Requirements\n\n### Requirement: 没删\n\n"
             "## RENAMED Requirements\n\n- FROM: `### Requirement: 旧名`\n- TO: `### Requirement: 新名`\n")
    r = _run(_layout(tmp_path, delta, _spec("追加了两份", "追加了两份", "没删", "旧名")))
    assert r.returncode == 1
    for needle in ("ADDED 未同步：漏了", "出现 2 次（应替换而非追加）：追加了两份",
                   "REMOVED 仍在主 spec：没删", "RENAMED 旧名仍在主 spec：旧名",
                   "RENAMED 新名在主 spec 出现 0 次：新名"):
        assert needle in r.stdout, r.stdout


def test_new_capability_without_main_spec_is_reported(tmp_path):
    r = _run(_layout(tmp_path, "## ADDED Requirements\n\n### Requirement: 新能力\n\nSHALL\n", None))
    assert r.returncode == 1
    assert "主 spec 不存在" in r.stdout


def test_removed_only_delta_without_main_spec_passes(tmp_path):
    r = _run(_layout(tmp_path, "## REMOVED Requirements\n\n### Requirement: 早没了\n", None))
    assert r.returncode == 0, r.stdout


def test_requirement_lines_inside_code_fence_are_ignored(tmp_path):
    delta = ("## ADDED Requirements\n\n### Requirement: 真的\n\nSHALL\n\n```markdown\n"
             "### Requirement: 示例里的\n```\n")
    r = _run(_layout(tmp_path, delta, _spec("真的")))
    assert r.returncode == 0, r.stdout


def test_rename_name_with_backticks_inside(tmp_path):
    delta = ("## RENAMED Requirements\n\n- FROM: `### Requirement: R12 — 7 份 `_yq()` 一致性`\n"
             "- TO: `### Requirement: R12 — `_yq()` 一致性`\n")
    r = _run(_layout(tmp_path, delta, _spec("R12 — `_yq()` 一致性")))
    assert r.returncode == 0, r.stdout


def test_missing_archive_dir_is_usage_error(tmp_path):
    r = _run(tmp_path / "nope")
    assert r.returncode == 2
