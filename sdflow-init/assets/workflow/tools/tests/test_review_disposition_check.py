import subprocess, sys, ast, importlib.util
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "review_disposition_check.py"
FIX = Path(__file__).resolve().parent / "fixtures"

OK = "section-ok-DISPOSITION-UNCHECKED"
MISSING = "section-missing"
EMPTY = "section-empty"


def _mod():
    spec = importlib.util.spec_from_file_location("review_disposition_check", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _classify_text(text):
    return _mod().classify(text)


def _classify_file(name):
    return _mod().classify((FIX / name).read_text(encoding="utf-8"))


# --- 三 reason_code 各有正例（真实 in-repo task-log 夹具）---

def test_ok_real_mlh(): assert _classify_file("task_log_review_ok_mlh.md") == OK
def test_ok_real_wco(): assert _classify_file("task_log_review_ok_wco.md") == OK
def test_empty_real_template(): assert _classify_file("task_log_review_empty_template.md") == EMPTY
def test_missing_real(): assert _classify_file("task_log_review_missing.md") == MISSING


# --- 收尾声明句「无『未处置』」不触发假阳（真实负例夹具，含 fence/结构感知核心）---

def test_closing_declaration_not_false_positive_mlh():
    """MLH 真实夹具含 blockquote 组头「不存在「未处置」状态」+ bullet「无「未处置」状态条目」两处子串——判 OK 而非误报。"""
    assert _classify_file("task_log_review_ok_mlh.md") == OK


def test_closing_declaration_not_false_positive_wco():
    """WCO 真实夹具含收尾声明「无「未处置」」——判 OK 而非误报。"""
    assert _classify_file("task_log_review_ok_wco.md") == OK


def test_closing_declaration_bracket_variant_double_corner():
    """『未处置』（双角括号）括号变体同样不假阳——校验器根本不匹配「未处置」子串，括号无关。"""
    assert _classify_file("task_log_review_ok_bracket_variant.md") == OK


def test_no_naive_substring_match_on_weichuzhi():
    """静态断言：源码不出现裸子串「未处置」比较（结构感知，非 grep）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "未处置" not in src


# --- fence 感知：fence 内的伪标题不算小节存在（结构感知负例）---

def test_fence_trap_section_inside_code_fence_is_missing():
    """`## Review 处置` 仅出现在 ```markdown fence 内（示例文本）→ section-missing，不得当作小节存在。"""
    assert _classify_file("task_log_review_fence_trap.md") == MISSING


# --- 空/脚手架判定：仅 HTML 注释 / 空白 / 水平线 = 空 ---

def test_section_only_html_comments_is_empty():
    text = "# t\n\n## Review 处置\n\n<!-- 脚手架说明，逐条追加 -->\n\n<!-- 另一条注释 -->\n\n## 2026-07-08\n"
    assert _classify_text(text) == EMPTY


def test_section_only_whitespace_is_empty():
    text = "# t\n\n## Review 处置\n\n   \n\t\n\n## 2026-07-08\n"
    assert _classify_text(text) == EMPTY


def test_section_only_thematic_break_is_empty():
    text = "# t\n\n## Review 处置\n\n---\n\n<!-- c -->\n\n## next\n"
    assert _classify_text(text) == EMPTY


def test_section_multiline_comment_stripped_is_empty():
    text = "# t\n\n## Review 处置\n\n<!-- 多行\n注释\n跨多行 -->\n\n## next\n"
    assert _classify_text(text) == EMPTY


def test_section_with_bullet_content_is_ok():
    text = "# t\n\n## Review 处置\n\n<!-- 脚手架 -->\n- F1 采纳：已改 design。\n\n## next\n"
    assert _classify_text(text) == OK


def test_section_at_eof_no_next_heading_ok():
    text = "# t\n\n## Review 处置\n\n- F1 采纳。\n"
    assert _classify_text(text) == OK


def test_section_at_eof_empty():
    text = "# t\n\n## Review 处置\n\n<!-- 仅脚手架 -->\n"
    assert _classify_text(text) == EMPTY


# --- 小节边界：level-3 子标题属小节内（内容），sibling level-2 结束小节 ---

def test_subheading_level3_is_content_within_section():
    text = "# t\n\n## Review 处置\n\n### 冷镜发现\n采纳 F1。\n\n## next\n"
    assert _classify_text(text) == OK


def test_content_after_next_h2_not_counted():
    """内容在下一个 ## 之后，不计入本小节；本小节自身只有注释 → empty。"""
    text = "# t\n\n## Review 处置\n\n<!-- c -->\n\n## 2026-07-08\n\n- 真实内容但属别的小节\n"
    assert _classify_text(text) == EMPTY


# --- 标题匹配严格性：非 level-2 / 标题不符 不算命中 ---

def test_level3_review_heading_not_matched():
    """`### Review 处置`（level-3）不是目标小节（模版规定 level-2）→ missing。"""
    text = "# t\n\n### Review 处置\n\n- F1 采纳。\n\n## next\n"
    assert _classify_text(text) == MISSING


def test_similar_but_different_title_not_matched():
    text = "# t\n\n## Review 处置记录汇总\n\n- F1 采纳。\n\n## next\n"
    assert _classify_text(text) == MISSING


# --- fail-closed：文件缺失 / 不可读 ---

def test_cli_missing_file_fail_closed(tmp_path):
    r = _run(tmp_path / "nonexistent.md")
    assert (r.returncode != 0 and r.stdout.strip() == ""
            and "[review_disposition_check] FAIL" in r.stderr and "Traceback" not in r.stderr)


def test_cli_directory_path_fail_closed(tmp_path):
    r = _run(tmp_path)
    assert (r.returncode != 0 and r.stdout.strip() == ""
            and "[review_disposition_check] FAIL" in r.stderr)


# --- CLI 契约：exit 码分流（OK exit0；missing/empty stdout 载码 + exit 非0）---

def _run(task_log):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--task-log", str(task_log)],
        capture_output=True, text=True)


def test_cli_ok_exit0(tmp_path):
    r = _run(FIX / "task_log_review_ok_mlh.md")
    assert r.returncode == 0 and r.stdout.strip() == OK


def test_cli_missing_exit_nonzero_stdout_carries_code():
    r = _run(FIX / "task_log_review_missing.md")
    assert r.returncode != 0 and r.stdout.strip() == MISSING and r.stderr.strip() == ""


def test_cli_empty_exit_nonzero_stdout_carries_code():
    r = _run(FIX / "task_log_review_empty_template.md")
    assert r.returncode != 0 and r.stdout.strip() == EMPTY and r.stderr.strip() == ""


# --- 纯 stdlib / 无 subprocess / 无 git（静态断言）---

def _imported_modules():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    return imported


def test_no_subprocess_no_os_no_yaml_import_ast():
    imported = _imported_modules()
    assert "subprocess" not in imported
    assert "os" not in imported
    assert "yaml" not in imported          # 门控外置：不读 config（无 yaml 解析）


def test_no_exec_tokens_in_source():
    """无实际执行/子进程/git 调用记号（docstring 里的 prose 提及由 AST import 测试覆盖，此处只查调用面）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    for tok in ("os.system", "os.popen", "os.fork", "os.exec", "Popen",
                "check_output", "check_call", "subprocess.run", "git log", "git status"):
        assert tok not in src


def test_does_not_read_config_file():
    """门控外置：不读任何 config 文件（无 config.yaml 字面、无 yaml 导入）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "config.yaml" not in src
    assert "yaml" not in _imported_modules()
