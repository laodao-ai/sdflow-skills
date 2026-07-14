import subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_lint.py"

def lint(tmp_path, text):
    p = tmp_path / "sad.md"; p.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--sad", str(p)],
                          capture_output=True, text=True)

def test_pass_honest_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=0))
    assert r.returncode == 0 and r.stdout.splitlines()[0] == S.PASS_CODE
    assert "假设计数: 1" in r.stdout

def test_missing_section_reason_code(tmp_path):
    text = make_sad().replace("## 8. 横切概念\n\nN/A — v1 无横切面\n\n", "")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "missing-section" in r.stdout and "8" in r.stdout
    assert "next-step:" in r.stdout

def test_na_without_reason(tmp_path):
    r = lint(tmp_path, make_sad().replace("N/A — v1 无横切面", "N/A"))
    assert r.returncode == 1 and "na-without-reason" in r.stdout

def test_duplicate_number_set_reconciliation(tmp_path):
    # 正文两个[假设-1] + 表 假设-1/假设-2 → 计数2==2 但集合对账拦截（REQ-5 场景逐字）
    text = make_sad(assumptions=[(1, "接受"), (2, "接受")], cache=0)
    text = text.replace("[假设-1] [假设-2]", "[假设-1] [假设-1]")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "assumption-set-mismatch" in r.stdout

def test_cache_mismatch_independent_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=5))
    assert r.returncode == 1 and "assumption-cache-mismatch" in r.stdout

def test_quality_attr_order(tmp_path):
    r = lint(tmp_path, make_sad().replace("1. 可靠性\n2. 可维护性", "- 可靠性\n- 可维护性"))
    assert r.returncode == 1 and "quality-attr-order-broken" in r.stdout
    r2 = lint(tmp_path, make_sad().replace("2. 可维护性", "3. 可维护性"))  # 跳号
    assert r2.returncode == 1 and "quality-attr-order-broken" in r2.stdout

def test_schema_version_mismatch_not_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad(schema=0))
    assert r.returncode == 1 and "schema-version-mismatch" in r.stdout   # 独立码+指引
    assert "FAIL" not in r.stderr                                        # 不与损坏共用出口

ANSWERED = {"positioning": "answered", "external_systems": "answered", "hard_constraints": "answered"}

def test_contract_invariant(tmp_path):
    bad = make_sad(status="validated")  # validated 下残留 contract[draft]
    r = lint(tmp_path, bad)
    assert r.returncode == 1 and "contract-invariant-violation" in r.stdout
    # validated 下 facts 须全 answered（A7），否则 facts-status-invariant 会独立拦截
    ok = make_sad(status="validated", facts=ANSWERED).replace("contract[draft]", "contract[validated]")
    assert lint(tmp_path, ok).returncode == 0

def test_slice_branch_assertions(tmp_path):
    r = lint(tmp_path, make_sad(status="skeleton-ready", slice_section=False,
                                facts={"positioning": "answered", "external_systems": "answered",
                                       "hard_constraints": "answered"}))
    assert r.returncode == 1 and "slice-section-missing" in r.stdout
    r2 = lint(tmp_path, make_sad(status="validated", slice_section=True)
              .replace("contract[draft]", "contract[validated]"))
    assert r2.returncode == 1 and "slice-section-stale" in r2.stdout

def test_bad_input_fail_closed(tmp_path):
    r = lint(tmp_path, "no frontmatter at all\n")
    assert r.returncode == 2 and r.stderr.startswith("[sad_lint] FAIL:") and S.PASS_CODE not in r.stdout
    r2 = subprocess.run([sys.executable, str(SCRIPT), "--sad", str(tmp_path / "nope.md")],
                        capture_output=True, text=True)
    assert r2.returncode == 2 and "[sad_lint] FAIL:" in r2.stderr

def test_enum_invalid_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad().replace("sad_status: draft", "sad_status: approved"))
    assert r.returncode == 2 and "approved" in r.stderr      # REQ-6 场景：stderr 区别于 reason_code

def test_crlf_bom_tolerated(tmp_path):
    text = "﻿" + make_sad(assumptions=[(1, "接受")], cache=0).replace("\n", "\r\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0

def test_fence_inside_markers_not_counted(tmp_path):
    text = make_sad(extra="```\n[假设-7]\n## 11. 假节\n```\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0        # fence 内标记/节锚不计

def test_non_utf8_fail_closed(tmp_path):
    p = tmp_path / "sad.md"
    p.write_bytes(b"---\nsad_schema: 1\nsad_status: draft\n---\nbad \x92 byte\n")
    r = subprocess.run([sys.executable, str(SCRIPT), "--sad", str(p)],
                        capture_output=True, text=True)
    assert r.returncode == 2
    assert r.stderr.startswith("[sad_lint] FAIL:")
    assert "structure-ok" not in r.stdout

def test_slice_pierce_set_mismatch(tmp_path):
    text = make_sad(subsystems=("采集端", "上报端"), status="skeleton-ready", slice_section=True)
    text = text.replace("- 穿越点[上报端]：§5 contract 条目", "")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "slice-pierce-set-mismatch" in r.stdout

def test_assumption_unresolved_code(tmp_path):
    text = make_sad(assumptions=[(1, "未处置")])
    r = lint(tmp_path, text)
    assert r.returncode == 1
    assert "assumption-unresolved" in r.stdout
    assert "next-step:" in r.stdout

def test_contract_invariant_other_branches_frozen_under_draft(tmp_path):
    # status=draft 但 contract[frozen]——draft/skeleton-ready ⇒ contract∈{planned,draft}
    text_a = make_sad(status="draft").replace("contract[draft]", "contract[frozen]")
    r_a = lint(tmp_path, text_a)
    assert r_a.returncode == 1 and "contract-invariant-violation" in r_a.stdout

def test_contract_invariant_other_branches_unknown_tag(tmp_path):
    # 未知 contract 标签
    text_b = make_sad(status="draft").replace("contract[draft]", "contract[bogus]")
    r_b = lint(tmp_path, text_b)
    assert r_b.returncode == 1 and "contract-invariant-violation" in r_b.stdout


# ---- A1 未闭合 fence fail-closed（lint 侧） ----------------------------------------
def test_unclosed_fence_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad(extra="```\n未闭合 fence 内容\n"))
    assert r.returncode == 2 and r.stderr.startswith("[sad_lint] FAIL:")
    assert "未闭合" in r.stderr and S.PASS_CODE not in r.stdout


# ---- A2 附录畸形行 fail-closed ---------------------------------------------------
def test_malformed_appendix_row(tmp_path):
    bad = make_sad(extra="| 假设-9 | §2 | 某推测 | 类比 | 未　处置 |\n")  # U+3000 全角空格
    r = lint(tmp_path, bad)
    assert r.returncode == 1 and "malformed-appendix-row" in r.stdout
    assert lint(tmp_path, make_sad()).returncode == 0        # 表头/分隔行不误报


# ---- A4 重复结构锚 fail-closed ---------------------------------------------------
def test_duplicate_section(tmp_path):
    dup_sec = make_sad().replace("## 9. 风险登记\n", "## 9. 风险登记\n\n占位\n\n## 9. 风险登记\n")
    r = lint(tmp_path, dup_sec)
    assert r.returncode == 1 and "duplicate-section" in r.stdout
    dup_slice = (make_sad(status="skeleton-ready", slice_section=True, facts=ANSWERED)
                 .replace("## 骨架切片建议\n", "## 骨架切片建议\n\n占位\n\n## 骨架切片建议\n"))
    r2 = lint(tmp_path, dup_slice)
    assert r2.returncode == 1 and "duplicate-section" in r2.stdout


# ---- A5 同名子系统 / 穿越点重复 fail-closed --------------------------------------
def test_duplicate_subsystem(tmp_path):
    dup_sub = make_sad(subsystems=("采集端", "采集端"), status="skeleton-ready",
                       slice_section=True, facts=ANSWERED)
    r = lint(tmp_path, dup_sub)
    assert r.returncode == 1 and "duplicate-subsystem" in r.stdout
    # 子系统不重名，但穿越点行重复 → 同 code 对称断言
    dup_pierce = make_sad(subsystems=("采集端", "上报端"), status="skeleton-ready",
                          slice_section=True, facts=ANSWERED)
    dup_pierce = dup_pierce.replace(
        "- 穿越点[采集端]：§5 contract 条目",
        "- 穿越点[采集端]：§5 contract 条目\n- 穿越点[采集端]：§5 contract 条目")
    r2 = lint(tmp_path, dup_pierce)
    assert r2.returncode == 1 and "duplicate-subsystem" in r2.stdout


# ---- A6 contract 捕获 + 限节（lint 侧） -------------------------------------------
def test_contract_capture_and_section_scope(tmp_path):
    for bad_tag in ("contract[Validated]", "contract[]", "contract[draft"):   # 大小写/空/未闭合
        text = make_sad(status="draft").replace("contract[draft]", bad_tag)
        r = lint(tmp_path, text)
        assert r.returncode == 1 and "contract-invariant-violation" in r.stdout, bad_tag
    # 附录散文提及 contract[frozen] 不再误伤 draft
    ok = make_sad(status="draft") + "类比 contract[frozen] 模式（附录散文）\n"
    assert lint(tmp_path, ok).returncode == 0


# ---- A7 facts×status 持续不变量（lint 侧） ---------------------------------------
def test_facts_status_invariant(tmp_path):
    partial = {"positioning": "answered", "external_systems": "answered", "hard_constraints": "missing"}
    text = make_sad(status="validated", facts=partial).replace("contract[draft]", "contract[validated]")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "facts-status-invariant" in r.stdout


# ---------- fence 内的 contract 行（devenv 试点在真 SAD 上抓到的假绿）----------

FENCED_SAD = """---
sad_schema: 1
sad_status: draft
facts: {positioning: answered, external_systems: answered, hard_constraints: answered}
assumptions_open: 0
---
# X

## 5. 子系统分解与 contract

### 5.1 连接与传输

- **对外 contract**：
```
- contract[frozen] Engine 接口：语法=Connect/Subscribe；语义=非阻塞
- contract[draft] SSH 隧道 DialFunc：语法=NewDialer→DialFunc
```

## 附录：假设清单
散文里提到 contract[frozen] 只是类比，MUST NOT 被扫进来（§5 限定挡住它）。
"""


def test_fenced_contract_lines_are_scanned():
    """⭐ 回归：contract 行写在 ``` fence 内时，MUST 仍被扫到。

    【这个假绿怎么来的】（devenv 试点在 mqtt-console 的真 SAD 上抓到）：
      · `sad-template.md` 明确要求 contract 行写在 fence 内（「contract 行格式示例（fence 内）」）
      · 而 `_section5_body_lines` 原走 `body_lines`（DEC-2，**剥 fence**）
      · ⇒ 真实 SAD 上抽出 **0 条**，`_check_contract_invariants` **从来没触发过**
      · 而测试是绿的 —— 因为 `conftest.py` 的 fixture 恰好把 contract 行写在 fence **外**

    **producer 说 fence 内，parser 剥 fence，fixture 站在 parser 这边 ⇒ 三方各说各话。**
    修复后在 mqtt-console 的真 SAD 上当场抓到 3 条真违规（status=skeleton-ready 但 contract[validated]）。
    """
    names = S.scan_contract_names(FENCED_SAD)
    assert [n for _, n in names] == ["Engine 接口", "SSH 隧道 DialFunc"]

    tags = [t for _, t in S.scan_contract_tags(FENCED_SAD)]
    assert tags == ["frozen", "draft"]        # 附录里那条类比提及【没有】被扫进来（§5 限定挡住）


def test_fenced_contract_invariant_actually_fires():
    """⭐ 不变式校验对 fence 内的 contract MUST 真的生效（原本恒不触发）。

    sad_status=draft ⇒ contract ∈ {planned, draft}；上面 fixture 里有 contract[frozen] ⇒ 必须红。
    """
    violations = []
    import sad_lint; sad_lint._check_contract_invariants(FENCED_SAD, "draft", violations)
    assert any("frozen" in msg for _, msg in violations), \
        "fence 内的 contract[frozen] 没被抓到 —— 不变式校验又变回了空转"
