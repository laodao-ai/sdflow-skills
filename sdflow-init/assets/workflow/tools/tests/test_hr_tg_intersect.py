import subprocess, sys, ast, importlib.util
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "hr_tg_intersect.py"


def _mod():
    spec = importlib.util.spec_from_file_location("hr_tg_intersect", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# --- 夹具：造一份 trigger-catalog（触发词目录全集表段 + HR-TG 段 + `> 成员：` 行），可参数化 ---

# 真实 catalog 的 8 成员（仅夹具用，非从脚本复制清单——脚本 MUST 从单一源读）
REAL_MEMBERS = "TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26"

# 「触发词目录」全集表段（F4 retrofit）：含所有测试用到的 TG 号 + TG-99（F5 重设计用：全集内、非 HR-TG 成员）。
# M-new「不存在」负例（如 TG-77/TG-88）刻意不入此表 —— 用以证全集边界钉死。
_ALL_TG_TABLE = (
    "## 三、触发词目录\n\n"
    "| ID | 触发 |\n|---|---|\n"
    + "".join(f"| TG-{n:02d} | x |\n" for n in (1, 4, 6, 7, 8, 9, 16, 17, 19, 26, 99))
    + "\n"
)


def _catalog(tmp_path, members=REAL_MEMBERS, heading="## 七、HR-TG 子集（评审 cross-model 层单一源）",
             member_line=None, trailing="\n*目录 v1 · 项目无关*\n", prose_extra=""):
    """写一份最小 trigger-catalog；member_line=None 则用标准 `> 成员：**...**` 行。
    prose_extra：插在「触发词目录」表段之后、下一标题之前的游离正文（F8 边界测试用）。"""
    if member_line is None:
        member_line = f"> 成员：**{members}**"
    body = (
        "# 触发目录\n\n"
        f"{_ALL_TG_TABLE}"
        f"{prose_extra}"
        "## 六、检查清单\n\n- [ ] 无关小节\n\n"
        f"{heading}\n\n"
        "> 高风险触发子集——命中任一 → 单开领域 cross-model。\n"
        f"{member_line}\n"
        f"{trailing}"
    )
    p = tmp_path / "trigger-catalog.md"; p.write_text(body, encoding="utf-8")
    return p


# --- 三类正例：命中 / 无交集 / 空集，含格式与确定序 ---

def test_hit_members(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    hits, declared = m.intersect(m.parse_tg_set("TG-04, TG-16, TG-19"), m.load_hr_tg_subset(cat))
    assert hits == ["TG-04", "TG-16"]                       # TG-19 不属 HR-TG
    assert declared == ["TG-04", "TG-16", "TG-19"]          # 依据全可见、sorted
    out = m.render(hits, declared)
    assert out.splitlines()[0] == "hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]"


def test_no_intersection(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    hits, declared = m.intersect(m.parse_tg_set("TG-01, TG-19"), m.load_hr_tg_subset(cat))
    assert hits == []
    assert m.render(hits, declared).splitlines()[0] == "none｜依据模型判定:[TG-01,TG-19]"


def test_empty_declared_set(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    hits, declared = m.intersect(m.parse_tg_set(""), m.load_hr_tg_subset(cat))
    assert hits == [] and declared == []
    assert m.render(hits, declared).splitlines()[0] == "none｜依据模型判定:[]"   # 依据可见、非裸 none


# --- 确定序 / 去重（乱序 + 重复输入 → sorted(set)）---

def test_dedup_and_sorted_numeric(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    # 乱序 + 重复；数值序确保 TG-8 排在 TG-16 前（非字典序 '8' > '1'）
    hits, declared = m.intersect(m.parse_tg_set("TG-16, TG-08, TG-08, TG-04"), m.load_hr_tg_subset(cat))
    assert hits == ["TG-04", "TG-08", "TG-16"]
    assert declared == ["TG-04", "TG-08", "TG-16"]


# --- 规范锚串：hit / none 两态，扩 declared= 字段 ---

def test_anchor_hit(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    hits, declared = m.intersect(m.parse_tg_set("TG-04, TG-19"), m.load_hr_tg_subset(cat))
    anchor = m.render(hits, declared).splitlines()[1]
    assert anchor == '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04,TG-19" -->'


def test_anchor_none(tmp_path):
    m = _mod(); cat = _catalog(tmp_path)
    hits, declared = m.intersect(m.parse_tg_set("TG-01"), m.load_hr_tg_subset(cat))
    anchor = m.render(hits, declared).splitlines()[1]
    assert anchor == '<!-- sdflow:hr-tg v1 hit="none" declared="TG-01" -->'


# --- 单一源可变性：改 catalog 即改行为（证明非硬编码副本）---

def test_single_source_mutability(tmp_path):
    """改 HR-TG 段成员即改命中行为，全集（触发词目录）不变。用 TG-19（全集内、非 HR-TG 8 员）。"""
    m = _mod()
    cat = _catalog(tmp_path, members="TG-19")   # TG-19 在全集表内，非真实 HR-TG 成员
    subset = m.load_hr_tg_subset(cat)
    assert subset == {"TG-19"}                              # 完全由单一源决定
    hits, _ = m.intersect(m.parse_tg_set("TG-19,TG-04"), subset)
    assert hits == ["TG-19"]                                # TG-04 不再命中（本 catalog HR-TG 段只列 TG-19）


# --- M-new：declared/成员须存在于「触发词目录」全集（存在性）+ F8 全集边界 + F7 内部一致 ---

def test_mnew_declared_tg_not_in_catalog_fail_closed(tmp_path):
    """declared 含 catalog 全集外 TG（TG-77 shape 合法不存在）→ 非零退出。"""
    m = _mod(); cat = _catalog(tmp_path)
    rc = m.main(["--tg-set", "TG-77", "--trigger-catalog", str(cat)])
    assert rc == m.EXIT_FAIL


def test_mnew_full_set_boundary_ignores_prose_tg(tmp_path):
    """正文游离 TG（'参见 TG-88 草案'）不入全集；引用它 → fail-closed。"""
    m = _mod()
    cat = _catalog(tmp_path, prose_extra="\n参见 TG-88 草案，非表行。\n")
    rc = m.main(["--tg-set", "TG-88", "--trigger-catalog", str(cat)])
    assert rc == m.EXIT_FAIL


def test_mnew_token_fullmatch_rejects_residue(tmp_path):
    """表行 token 逐个 fullmatch，残留后缀 TG-04.0 不当 TG-04 纳入全集。"""
    m = _mod()
    subset_all = m.load_all_tg_set(_catalog(tmp_path))
    assert "TG-04" in subset_all and "TG-04.0" not in subset_all


def test_f7_hr_tg_must_subset_full_set(tmp_path):
    """HR-TG 成员含全集外 TG → 加载 fail-closed（catalog 内部一致）。"""
    m = _mod()
    # 成员 TG-77 不在全集表行内
    cat = _catalog(tmp_path, members="TG-77")
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(cat)


def test_reads_real_catalog_members(tmp_path):
    """从真实权威源 trigger-catalog.md 读，成员集须 = 文档声明的 9 个（absorb-gstack-review 追加 TG-27）。"""
    m = _mod()
    real_cat = TOOLS.parent / "trigger-catalog.md"
    subset = m.load_hr_tg_subset(real_cat)
    assert subset == {"TG-04", "TG-06", "TG-07", "TG-08", "TG-09", "TG-16", "TG-17", "TG-26", "TG-27"}


# --- 单一源损坏 fail-closed（不静默按空子集放行）---

def test_missing_catalog_fail_closed(tmp_path):
    m = _mod()
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(tmp_path / "nonexistent.md")


def test_missing_hr_tg_section_fail_closed(tmp_path):
    m = _mod()
    p = tmp_path / "trigger-catalog.md"
    p.write_text("# 触发目录\n\n## 五、扩展约定\n\n> 成员：**TG-04**\n", encoding="utf-8")  # 无 HR-TG 段
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(p)


def test_missing_member_line_fail_closed(tmp_path):
    m = _mod()
    p = tmp_path / "trigger-catalog.md"
    p.write_text("## 七、HR-TG 子集\n\n> 高风险触发子集说明。\n\n## 八、别的\n", encoding="utf-8")  # HR-TG 段无成员行
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(p)


def test_empty_member_line_fail_closed(tmp_path):
    m = _mod()
    cat = _catalog(tmp_path, member_line="> 成员：**（暂无）**")   # 成员行存在但无 TG 记号
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(cat)


def test_member_line_in_other_section_not_leaked(tmp_path):
    """HR-TG 段自身无成员行，但别的段有 `> 成员：` → 不得跨段泄漏借用。"""
    m = _mod()
    p = tmp_path / "trigger-catalog.md"
    p.write_text(
        "## 六、别的\n\n> 成员：**TG-04**\n\n## 七、HR-TG 子集\n\n> 只有说明没有成员行。\n\n## 八、尾\n",
        encoding="utf-8")
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(p)


# --- tg-set 坏输入 fail-closed ---

def test_malformed_tg_token_fail_closed():
    m = _mod()
    with pytest.raises(m.EmitError):
        m.parse_tg_set("TG-04, banana")


def test_tg_set_empty_cell_fail_closed():
    """TG-04,,TG-16 连续逗号空 cell → EmitError（非静默过滤）。"""
    m = _mod()
    for raw in ("TG-04,,TG-16", ",", "TG-04,", ",TG-16", " , "):
        with pytest.raises(m.EmitError):
            m.parse_tg_set(raw)


def test_tg_set_empty_string_is_empty_set():
    """仅原始空串表空集（合法空集入口保留）。"""
    m = _mod()
    assert m.parse_tg_set("") == []


def test_member_strict_token_rejects_malformed():
    """成员/tg-set 畸形 token TG-04x → EmitError，不宽松正规化抽 TG-04。"""
    m = _mod()
    with pytest.raises(m.EmitError):
        m.parse_tg_set("TG-04x")


# --- 纯 stdlib / 无 subprocess / 无 git / 无 __file__ 推导 catalog（静态断言）---

def test_no_subprocess_no_os_import_ast():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported
    assert "os" not in imported


def test_no_exec_tokens_in_source():
    src = SCRIPT.read_text(encoding="utf-8")
    for tok in ("os.system", "os.popen", "os.fork", "os.exec", "Popen",
                "check_output", "check_call", "git"):
        assert tok not in src


def test_no_file_derived_catalog_path():
    """trigger-catalog 路径 MUST 由入参，MUST NOT 用 __file__ 推导（A3）。
    AST 断言无 `__file__` 名字节点（代码里不用；docstring 里作 prose 提及不算）。"""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "__file__" not in names        # 代码中不引 __file__ → 无从其推导 catalog 路径


def test_no_hardcoded_member_list():
    """脚本 MUST NOT 硬编码 HR-TG 成员副本（真实 8 成员中任一序列不得成串出现）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "TG-04" not in src and "TG-26" not in src and "TG-16" not in src


# --- [impl-review-fix] F-A：成员行严格抽取，拒畸形 token（TG-04x 非法后缀），不宽松 findall ---

def test_famember_line_rejects_suffixed_token(tmp_path):
    """F-A: `> 成员：**TG-04x**` 畸形 token（非法后缀）→ EmitError，不得宽松抽出 TG-04。"""
    m = _mod()
    cat = _catalog(tmp_path, member_line="> 成员：**TG-04x**")
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(cat)


def test_famember_line_rejects_mixed_valid_and_malformed(tmp_path):
    """F-A: 成员行混入一个畸形 token（TG-06x）→ 整行 fail-closed，不局部放行合法 token。"""
    m = _mod()
    cat = _catalog(tmp_path, member_line="> 成员：**TG-04, TG-06x**")
    with pytest.raises(m.EmitError):
        m.load_hr_tg_subset(cat)


def test_famember_line_normal_still_ok(tmp_path):
    """F-A 正例：正常 `**TG-04, TG-06**` 成员行严格解析仍正常通过。"""
    m = _mod()
    cat = _catalog(tmp_path, member_line="> 成员：**TG-04, TG-06**")
    subset = m.load_hr_tg_subset(cat)
    assert subset == {"TG-04", "TG-06"}


# --- [impl-review-fix] F-B：「触发词目录」段标题歧义 → fail-closed（拒 next() 静默取首劫持段边界）---

def test_fb_ambiguous_section_heading_fail_closed(tmp_path):
    """更早出现同含「触发词目录」子串的诱饵标题（`## 零、触发词目录草案（历史存档）`）
    → 段定位歧义，MUST EmitError（旧 next() 取首会静默把诱饵段（含 TG-77）当真全集，fail-open）。"""
    m = _mod()
    p = tmp_path / "trigger-catalog.md"
    body = (
        "# 触发目录\n\n"
        "## 零、触发词目录草案（历史存档）\n\n"
        "| ID | 触发 |\n|---|---|\n| TG-77 | x |\n\n"
        "## 三、触发词目录\n\n"
        "| ID | 触发 |\n|---|---|\n| TG-04 | x |\n| TG-16 | x |\n\n"
        "## 七、HR-TG 子集（评审 cross-model 层单一源）\n\n"
        "> 成员：**TG-04, TG-16**\n"
    )
    p.write_text(body, encoding="utf-8")
    with pytest.raises(m.EmitError):
        m.load_all_tg_set(p)


# --- [impl-review-fix] F-C：catalog 解析 fence-aware，段内围栏示例表行不纳入全集 ---

def test_fc_fence_aware_catalog_parsing(tmp_path):
    """段内 ``` 围栏代码块里的示例表行 `| TG-88 | 仅示例 |` 不得纳入「触发词目录」全集。"""
    m = _mod()
    cat = _catalog(tmp_path, prose_extra="\n```\n| TG-88 | 仅示例 |\n```\n")
    all_tg = m.load_all_tg_set(cat)
    assert "TG-88" not in all_tg


def test_fc_fence_aware_catalog_cli_fail_closed(tmp_path):
    """端到端：declared=TG-88（仅存在于围栏示例内）→ M-new 存在性校验判其「全集外」，CLI fail-closed。"""
    m = _mod()
    cat = _catalog(tmp_path, prose_extra="\n```\n| TG-88 | 仅示例 |\n```\n")
    rc = m.main(["--tg-set", "TG-88", "--trigger-catalog", str(cat)])
    assert rc == m.EXIT_FAIL


# --- CLI 契约（子进程；exit 码 + stdout/stderr 分流）---

def _run(tg_set, catalog):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--tg-set", tg_set, "--trigger-catalog", str(catalog)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_cli_hit_exit0(tmp_path):
    cat = _catalog(tmp_path)
    r = _run("TG-04, TG-16, TG-19", cat)
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines[0] == "hit:[TG-04,TG-16]｜依据模型判定:[TG-04,TG-16,TG-19]"
    assert lines[1] == '<!-- sdflow:hr-tg v1 hit="TG-04,TG-16" declared="TG-04,TG-16,TG-19" -->'


def test_cli_none_exit0(tmp_path):
    cat = _catalog(tmp_path)
    r = _run("TG-01, TG-19", cat)
    assert r.returncode == 0 and r.stdout.splitlines()[0] == "none｜依据模型判定:[TG-01,TG-19]"


def test_cli_empty_set_exit0(tmp_path):
    cat = _catalog(tmp_path)
    r = _run("", cat)
    assert r.returncode == 0 and r.stdout.splitlines()[0] == "none｜依据模型判定:[]"


def test_cli_corrupt_source_fail_closed_stderr_no_stdout(tmp_path):
    p = tmp_path / "bad.md"; p.write_text("# no HR-TG here\n", encoding="utf-8")
    r = _run("TG-04", p)
    assert (r.returncode != 0 and r.stdout.strip() == ""
            and "[hr_tg_intersect] FAIL" in r.stderr and "Traceback" not in r.stderr)


def test_cli_missing_catalog_fail_closed(tmp_path):
    r = _run("TG-04", tmp_path / "nonexistent.md")
    assert (r.returncode != 0 and r.stdout.strip() == ""
            and "[hr_tg_intersect] FAIL" in r.stderr)
