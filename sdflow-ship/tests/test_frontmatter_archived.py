# [mlh-p5 Task3] archived_verify_state dual-read（frontmatter 优先→absent 回退 inline，坏→fail-safe none）。
# 沿用 test_gate_anchor_scope.py 的 git fixture 构造法：写 archive/{dir}/verify-report.md 后 commit，
# 再用 archived_verify_state(root, ref, archive_dir) 直接断言（D13：行为构造，非硬编码篇数）。
import importlib.util
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)   # __main__ 守卫，加载无副作用

VPASS = "<!-- ship-gate: verify=PASS -->"
VFAIL = "<!-- ship-gate: verify=FAIL -->"


def _git(root, *a):
    subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True)


def _seed_archive(tmp_path, content, dirname="2026-07-06-demo"):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / dirname
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(content, encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "arch")
    return dirname


def test_archived_frontmatter_read(tmp_path):
    # 归档 verify-report frontmatter verify: PASS（无 inline 锚）→ archived_verify_state == 'pass'
    dirname = _seed_archive(
        tmp_path, "---\nship-gate:\n  verify: PASS\n---\n# 验证报告\n")
    assert _sg.archived_verify_state(tmp_path, "main", dirname) == "pass"


def test_archived_inline_read(tmp_path):
    # 无 frontmatter，旧 inline <!-- ship-gate: verify=PASS --> → absent 回退 inline 读出（保留）
    dirname = _seed_archive(tmp_path, f"{VPASS}\n")
    assert _sg.archived_verify_state(tmp_path, "main", dirname) == "pass"


def test_archived_frontmatter_bad_fail_safe(tmp_path):
    # frontmatter 越域值（MAYBE）→ 坏 → fail-safe 'none'；正文另塞 inline PASS 诱饵证明未回退掩盖
    dirname = _seed_archive(
        tmp_path,
        f"---\nship-gate:\n  verify: MAYBE\n---\n{VPASS}\n")
    assert _sg.archived_verify_state(tmp_path, "main", dirname) == "none"


def test_archived_q4_frontmatter_wins(tmp_path):
    # 好 frontmatter verify: PASS + 残留 inline FAIL 锚 → Q4：frontmatter 即真相，不交叉扫 inline，仍 'pass'
    dirname = _seed_archive(
        tmp_path,
        f"---\nship-gate:\n  verify: PASS\n---\n{VFAIL}\n")
    assert _sg.archived_verify_state(tmp_path, "main", dirname) == "pass"


def test_archived_bad_scalar_no_inline_fallback(tmp_path):
    # [impl-review-fix FIX-2] 顶层 ship-gate 带内联标量值（坏 bad-type）+ 残留 inline PASS 诱饵
    # → 坏 frontmatter fail-safe 'none'，MUST NOT 回退 inline 误判 'pass'（假 SHIPPED）。
    dirname = _seed_archive(
        tmp_path,
        f"---\nship-gate: []\n---\n{VPASS}\n")
    assert _sg.archived_verify_state(tmp_path, "main", dirname) == "none"


def test_archived_unclosed_no_inline_none(tmp_path):
    # [T74 3.5/目标态 fail-safe] 首行 --- 无闭合 + 正文无 inline 锚（模拟 producer 迁后漏闭合）
    # → parse 判 absent → 回退 inline 扫空 → archived_verify_state 判 'none'（不 SHIPPED，方向安全）。
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-08-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n无闭合横线，正文继续\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch-unclosed")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-08-demo") == "none"


def test_archived_unclosed_with_inline_pass_is_registered_blindspot(tmp_path):
    # [T74 3.5/登记盲区] 对照：首行 --- 无闭合 + 正文独占一行 inline PASS 锚 → 回退 inline
    # 扫到独占行 → 判 'pass'。**记录其为已登记越权盲区、非正常可达**（producer 不产此形态）。
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-08-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(
        "---\n无闭合首块\n" + _sg.ANCHOR_VERIFY_PASS + "\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch-hybrid")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-08-demo") == "pass"
