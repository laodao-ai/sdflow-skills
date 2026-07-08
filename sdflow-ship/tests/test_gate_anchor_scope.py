"""锚检测行锚定 + fence-aware（B4）：_line_scoped_hits / archived_verify_state。
[T75] 旧 live inline 读半场专属用例已随死符号删除退役，仅保留归档 dual-read 守卫 +
语料契约（详见 ship_gate.py 头注释「保留边界」）。"""
import importlib.util
import json
import sys
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)   # __main__ 守卫，加载无副作用

DESIGN = "<!-- ship-gate: design-approved -->"
VPASS = "<!-- ship-gate: verify=PASS -->"
VFAIL = "<!-- ship-gate: verify=FAIL -->"


def _git(root, *a):
    subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True)


def test_core_descriptive_pass_not_hit():
    # 核心单元：描述性提及 PASS 的文本 → hits 不含 PASS
    text = f"归档说明：曾写过 `{VPASS}` 但后撤。\n```\n{VPASS}\n```\n"
    hits, unbalanced = _sg._line_scoped_hits(text, [VPASS, VFAIL])
    assert VPASS not in hits


def test_archived_descriptive_pass_none(tmp_path):
    # 端到端：git fixture，归档 verify-report 仅描述性提及 PASS（无真锚）→ archived_verify_state 判 none
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"结论待定；模板锚示例：`{VPASS}`。\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"


def test_archived_true_pass_and_conflict(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "pass")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "pass"
    (d / "verify-report.md").write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "conflict")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "conflict"


def test_archived_unbalanced_none(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "unb")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"


GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"


def _run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change, "--root", str(root)],
                       capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    return r.returncode, (json.loads(lines[-1]) if lines else {})


def test_decide_b4_board_refuse_start(tmp_path):
    # B4 盘面：spec-review-report 仅描述性提及 design-approved（无独占锚）→ REFUSE_START
    from conftest import mkchange, commit_all
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text("〔TG-25：契约〕\n", encoding="utf-8")   # 非嵌入式，避免 RUN_SOP
    d.joinpath("spec-review-report.md").write_text(
        f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    commit_all(tmp_path, "seed")
    code, js = _run_gate(tmp_path)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_contract_archived_corpus_anchor_hits():
    # 契约：归档报告语料【聚合】实证 gate 关键锚以【独占裸行】承载——模板若悄悄去独占行，
    # 这些锚会从聚合集里消失（防模板假设静默失效）。
    # 【B5 修正】原契约"子串出现即断言行级命中"不自洽：报告正文会把锚串作为【讨论对象】
    # inline 提及（如 2026-07-05-gate-checkpoint-hardening/verify-report.md 在表格里讨论
    # "锚模板独占裸行"），那类 inline/fenced 提及本就不该被 _line_scoped_hits 计入——
    # "提及"与"标记"只有 _line_scoped_hits 能区分，故拿子串交叉校验它天生必误红。
    # 改为聚合不变量：只断言"语料里 gate 真读的锚各至少一篇以独占行承载"，对 inline 提及免疫。
    archive = REPO / "openspec" / "changes" / "archive"
    samples = list(archive.glob("*/spec-review-report.md")) + \
              list(archive.glob("*/verify-report.md")) + \
              list(archive.glob("*/code-review-report.md"))
    assert samples, "无归档报告语料"
    exclusive = set()
    for f in samples:
        text = f.read_text(encoding="utf-8", errors="replace")
        hits, _ = _sg._line_scoped_hits(text, [VPASS, VFAIL])   # [T75] verify-only 锚，fence-aware 独占行判据
        exclusive.update(hits)
    # 聚合断言（非"每处子串"）：gate 关键锚在语料里实证以独占行承载；模板全局回退即缺锚。
    # [T75/BR-3] gate 从不从归档读 design/CR 锚（那些 inline 读半场已退役），故只断言
    # verify 锚以独占行承载；原 `DESIGN in exclusive` 测的是 gate 消费不到的东西，删。
    assert VPASS in exclusive or VFAIL in exclusive, "归档 verify 语料无一以独占行承载 verify=PASS/FAIL"


def test_contract_live_frontmatter_corpus_fields():
    # [mlh-p5 Task5 Step4] B5 聚合语料 live 侧对应契约：above 的
    # test_contract_archived_corpus_anchor_hits 只扫【归档】语料（本仓 openspec/changes/archive/，
    # 保留 inline，永久不迁）——本仓目前尚无第二个 producer 已迁移 frontmatter 的活跃报告可扫
    # （本 change 自身报告的迁移属 tasks.md 5.3，非本步范围），故用与三 producer SKILL.md
    # 模板一致的代表性 frontmatter 样本（覆盖三字段各自的全部枚举取值）构造聚合语料，断言
    # gate 真读的 parse_ship_gate_frontmatter 在聚合层面对每个枚举值都能解析出【非 inline】
    # 承载的字段——对应「live 侧」不再依赖 _line_scoped_hits 独占行判据，与归档聚合契约
    # （行级判据）形成 live/归档两套承载形态的对照证据，防止某一侧模板漂移后另一侧假绿掩盖。
    samples = [
        ("---\nship-gate:\n  design_approved: true\n---\n# 设计审报告\n", "design_approved", True),
        ("---\nship-gate:\n  verify: PASS\n---\n# 验证报告\n", "verify", "PASS"),
        ("---\nship-gate:\n  verify: FAIL\n---\n# 验证报告\n", "verify", "FAIL"),
        ("---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", "code_review", "pass"),
        ("---\nship-gate:\n  code_review: blocked\n---\n# 代码审报告\n", "code_review", "blocked"),
    ]
    covered = set()
    for text, field, want in samples:
        state, err = _sg.parse_ship_gate_frontmatter(text)
        assert err is None, f"live 语料样本解析出错: {err}\n{text}"
        assert state.get(field) == want, f"live 语料样本 {field}={want!r} 未被 frontmatter 解析器识别: {state!r}"
        covered.add(field)
    # 聚合断言：三个 gate 关键字段各至少一枚举值经 frontmatter 承载被识别（不依赖任一 inline 锚常量）
    assert covered == set(_sg.FIELD_ENUMS), "live frontmatter 语料聚合未覆盖全部 gate 字段"
