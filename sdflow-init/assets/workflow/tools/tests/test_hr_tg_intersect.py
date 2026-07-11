import subprocess, sys, ast, importlib.util
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "hr_tg_intersect.py"


def _mod():
    spec = importlib.util.spec_from_file_location("hr_tg_intersect", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# --- 夹具：造一份 trigger-catalog（HR-TG 段 + `> 成员：` 行），成员集可参数化 ---

# 真实 catalog 的 8 成员（仅夹具用，非从脚本复制清单——脚本 MUST 从单一源读）
REAL_MEMBERS = "TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26"


def _catalog(tmp_path, members=REAL_MEMBERS, heading="## 七、HR-TG 子集（评审 cross-model 层单一源）",
             member_line=None, trailing="\n*目录 v1 · 项目无关*\n"):
    """写一份最小 trigger-catalog；member_line=None 则用标准 `> 成员：**...**` 行。"""
    if member_line is None:
        member_line = f"> 成员：**{members}**"
    body = (
        "# 触发目录\n\n## 六、检查清单\n\n- [ ] 无关小节\n\n"
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
    m = _mod()
    # 造一个成员集迥异于真实 8 成员的 catalog：仅 TG-99
    cat = _catalog(tmp_path, members="TG-99")
    subset = m.load_hr_tg_subset(cat)
    assert subset == {"TG-99"}                              # 完全由单一源决定
    hits, _ = m.intersect(m.parse_tg_set("TG-99, TG-04"), subset)
    assert hits == ["TG-99"]                                # TG-04 现在不再命中（真实清单里它属 HR-TG）


def test_reads_real_catalog_members(tmp_path):
    """从真实权威源 trigger-catalog.md 读，成员集须 = 文档声明的 8 个。"""
    m = _mod()
    real_cat = TOOLS.parent / "trigger-catalog.md"
    subset = m.load_hr_tg_subset(real_cat)
    assert subset == {"TG-04", "TG-06", "TG-07", "TG-08", "TG-09", "TG-16", "TG-17", "TG-26"}


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


# --- CLI 契约（子进程；exit 码 + stdout/stderr 分流）---

def _run(tg_set, catalog):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--tg-set", tg_set, "--trigger-catalog", str(catalog)],
        capture_output=True, text=True)


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
