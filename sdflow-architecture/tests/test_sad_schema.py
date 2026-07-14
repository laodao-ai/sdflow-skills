import sys, pathlib, unicodedata, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad

ANSWERED = {"positioning": "answered", "external_systems": "answered", "hard_constraints": "answered"}

TEMPLATE = pathlib.Path(__file__).parent.parent / "references" / "sad-template.md"

def test_body_lines_skips_fences():
    text = "a\n```\n[假设-9]\n## 1. 目标与质量属性\n```\nb\n"
    lines = [l for _, l in S.body_lines(text)]
    assert lines == ["a", "b"]          # fence 内标记/节锚不进行流

def test_parse_frontmatter_ok():
    fm = S.parse_frontmatter(make_sad(facts={"positioning": "answered",
        "external_systems": "answered", "hard_constraints": "missing"}))
    assert fm["sad_status"] == "draft" and fm["facts"]["hard_constraints"] == "missing"

@pytest.mark.parametrize("mutate,label", [
    (lambda t: t.replace("sad_status: draft", "sad_status: draft\nsad_status: draft"), "duplicate-key"),
    (lambda t: t.replace("assumptions_open", "unknown_key"), "out-of-domain"),
    (lambda t: t.replace("sad_schema: 1", "sad_schema: one"), "bad-type"),
    (lambda t: t.replace("  positioning", "\tpositioning"), "tab-indent"),
    (lambda t: t.replace("facts:\n  positioning: missing\n", "facts: inline\n  positioning: missing\n"), "facts-inline"),
    (lambda t: t.replace("sad_status: draft", "sad_status: approved"), "enum-invalid"),
    (lambda t: t.replace("  positioning: missing", "  color: red"), "facts-unknown-subkey"),
], ids=lambda x: x if isinstance(x, str) else "")
def test_parse_frontmatter_bad_forms_fail_closed(mutate, label):
    with pytest.raises(S.SadParseError):
        S.parse_frontmatter(mutate(make_sad()))

def test_facts_key_missing_means_missing_not_crash():
    text = make_sad().replace("  hard_constraints: missing\n", "")
    fm = S.parse_frontmatter(text)
    assert fm["facts"].get("hard_constraints", "missing") == "missing"

def test_scan_assumptions_and_check():
    ok = make_sad(assumptions=[(1, "接受"), (2, "待校准")], cache=0)
    assert S.check_assumptions(ok) == []
    dup = make_sad(assumptions=[(1, "接受")],
                   extra="[假设-1] 重号内联\n")           # 内联两个1，表一行 → 集合仍相等但重号
    codes = [c for c, _ in S.check_assumptions(dup)]
    assert "assumption-set-mismatch" in codes
    unresolved = make_sad(assumptions=[(1, "未处置")])
    codes = [c for c, _ in S.check_assumptions(unresolved)]
    assert "assumption-unresolved" in codes

def test_scan_subsystems_and_pierce():
    t = make_sad(subsystems=("采集端", "上报端"), slice_section=True, status="skeleton-ready")
    assert S.scan_subsystems(t) == ["采集端", "上报端"]
    assert S.scan_pierce_refs(t) == ["采集端", "上报端"]

def test_every_reason_code_has_next_step():
    for code in ("missing-section", "na-without-reason", "assumption-set-mismatch",
                 "assumption-unresolved", "assumption-cache-mismatch",
                 "quality-attr-order-broken", "schema-version-mismatch",
                 "contract-invariant-violation", "slice-section-missing",
                 "slice-section-stale", "slice-pierce-set-mismatch",
                 "malformed-appendix-row", "duplicate-section",
                 "duplicate-subsystem", "facts-status-invariant"):
        assert S.REASON_NEXT_STEP[code].strip()


# ---- A1 fence CommonMark 语义子集 -------------------------------------------------
def test_body_lines_tilde_fence_markers_not_counted():
    text = "x\n~~~\n[假设-9]\n## 1. 目标与质量属性\n~~~\ny\n"
    assert [l for _, l in S.body_lines(text)] == ["x", "y"]

def test_body_lines_four_backtick_not_closed_by_three():
    # ```` 开启，内含 ``` 行不提前关，须 ```` 才闭合
    text = "````\n```\ninner [假设-3]\n````\nafter\n"
    assert [l for _, l in S.body_lines(text)] == ["after"]

def test_body_lines_unclosed_fence_raises():
    with pytest.raises(S.SadParseError):
        S.body_lines("a\n```\n未闭合内容\n")


# ---- A3 frontmatter 顶格精确定界 --------------------------------------------------
def test_frontmatter_end_skips_indented_dashes():
    # 缩进 `  ---` 不当结束定界；顶格 `---` 才是边界（旧 strip 版会返回 index 2 → 早截断）
    lines = ["---", "sad_schema: 1", "  ---", "sad_status: draft", "assumptions_open: 7", "---", "body"]
    assert S.frontmatter_end(lines) == 5

def test_frontmatter_topgrid_dashes_close_and_read_true_value():
    fm = S.parse_frontmatter(make_sad(cache=7, assumptions=[(7, "接受")]))
    assert fm["assumptions_open"] == 7        # 顶格 --- 正常闭合，读到真值

def test_frontmatter_indented_dashes_fail_closed():
    # 有了 A3 修复，facts 块内一行 `  ---` 不再被当边界静默截断（旧 bug 读 assumptions_open=0），
    # 而是被送进 facts 解析 → fail-closed raise（诚实报坏输入，不静默）
    bad = ("---\nsad_schema: 1\nsad_status: draft\nfacts:\n  positioning: answered\n"
           "  ---\n  external_systems: answered\n  hard_constraints: answered\n"
           "assumptions_open: 7\n---\n\n# body\n")
    with pytest.raises(S.SadParseError):
        S.parse_frontmatter(bad)


# ---- A8 NFC 归一 -----------------------------------------------------------------
def test_nfc_normalization_subsystem_pierce():
    nfc = "café"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfc != nfd                          # 不同码点、同形
    text = (
        "---\nsad_schema: 1\nsad_status: skeleton-ready\nfacts:\n"
        "  positioning: answered\n  external_systems: answered\n  hard_constraints: answered\n"
        "assumptions_open: 0\n---\n\n"
        f"## 5. 子系统分解与 contract\n\n### 5.1 {nfd}\n- contract[draft] x：语法/语义/错误语义主干\n\n"
        f"## 骨架切片建议\n\n- 穿越点[{nfc}]：§5\n\n"
        "## 附录：假设清单\n\n| 编号 | 位置 | 内容 | 依据 | 处置 |\n|---|---|---|---|---|\n"
    )
    assert S.scan_subsystems(text) == [nfc]                       # 归一到 NFC
    assert set(S.scan_subsystems(text)) == set(S.scan_pierce_refs(text))  # 集合相等


# ---- A4 duplicate_anchors helper ------------------------------------------------
def test_duplicate_anchors_helper():
    text = make_sad().replace("## 9. 风险登记\n", "## 9. 风险登记\n\n占位\n\n## 9. 风险登记\n")
    dups = dict(S.duplicate_anchors(text))
    assert dups.get("## 9. 风险登记") == 2
    assert S.duplicate_anchors(make_sad()) == []                  # 无重复


# ---- A2 malformed appendix row helper -------------------------------------------
def test_scan_malformed_appendix_row_helper():
    bad = make_sad(extra="| 假设-9 | §2 | 某推测 | 类比 | 未　处置 |\n")   # U+3000 混入处置格
    mal = S.scan_malformed_appendix_rows(bad)
    assert len(mal) == 1 and "假设-9" in mal[0][1]
    # 表头/分隔行不误报
    assert S.scan_malformed_appendix_rows(make_sad()) == []


# ---- A6 contract 捕获 + 限节 -----------------------------------------------------
def test_scan_contract_tags_section5_only_any_payload():
    # 附录散文里的 contract[frozen] 不被 section-5 扫描误捕
    text = make_sad().replace("contract[draft]", "contract[Validated]")
    text += "\n类比 contract[frozen] 模式（附录散文）\n"
    tags = dict((p, ln) for ln, p in S.scan_contract_tags(text))
    assert "Validated" in tags and "frozen" not in tags          # 任意载荷 + 限第5节

def test_scan_contract_malformed_unclosed():
    text = make_sad().replace("contract[draft]", "contract[draft")   # 去掉闭合 ]
    mal = S.scan_contract_malformed(text)
    assert len(mal) == 1 and "contract[" in mal[0][1]

def test_template_contains_all_anchors_verbatim():
    text = TEMPLATE.read_text(encoding="utf-8")
    lines = [l for _, l in S.body_lines(text)]
    for anchor in S.SECTION_ANCHORS + (S.APPENDIX_ANCHOR,):
        assert anchor in lines, anchor

def test_template_marker_examples_fenced():
    """模版里的标记示例 MUST NOT 被实扫命中（自指安全 —— `sad_scaffold init` 会把模版拷成用户的 sad.md）。

    🔴 **两种标记，两种转义机制，别混**：

      `[假设-N]` / 穿越点 → 靠 **fence**（`body_lines` 剥 fence，DEC-2）
      `contract[...]`     → 靠 **放在 §5 之外**（contract 扫描【含 fence 内的行】）

    **contract 为什么不能靠 fence 转义**（devenv 试点在真 SAD 上抓到的假绿）：
    `sad-template.md` 曾把 contract 示例放在 §5 的 fence 里，于是真实 SAD 也照抄——
    **contract 全写进 fence，而 parser 剥 fence ⇒ 扫出 0 条 ⇒ 不变式校验从来没触发过。**
    （mqtt-console 实证：44 条 contract 全在 fence 里，`sad_lint` 一条都没看见。）

    ⇒ fence 曾同时兼职「示例的转义」和「内容的容器」，两个职责互斥。
      现在：**内容可以在 fence 里（照扫）；示例靠「不在 §5」来转义。**
    """
    text = TEMPLATE.read_text(encoding="utf-8")
    inline, rows = S.scan_assumptions(text)
    assert inline == [] and rows == []
    assert S.scan_pierce_refs(text) == []
    assert S.scan_contract_tags(text) == []
    assert {h for h, _ in S._section_spans(text)} == set(S.SECTION_ANCHORS) | {S.APPENDIX_ANCHOR}

def test_template_frontmatter_parses_as_fresh_draft():
    fm = S.parse_frontmatter(TEMPLATE.read_text(encoding="utf-8"))
    assert fm["sad_status"] == "draft" and fm["sad_schema"] == S.SAD_SCHEMA_VERSION
    assert all(fm["facts"][k] == "missing" for k in S.FACT_KEYS)
