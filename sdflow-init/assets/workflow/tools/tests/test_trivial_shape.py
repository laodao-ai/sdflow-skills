"""trivial_shape 判器测试 — 覆盖 spec-workflow code-review 两层 MODIFIED 的白名单/守卫场景。

直接调纯函数 classify_diff(diff_text)，构造合成 unified diff，不依赖真实 git。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from trivial_shape import classify_diff  # noqa: E402


def _diff(path, added=(), removed=(), new=False, rename_to=None):
    """构造最小 unified diff 文本。"""
    lines = []
    b = rename_to or path
    lines.append(f"diff --git a/{path} b/{b}")
    if new:
        lines.append("new file mode 100644")
        lines.append("index 0000000..abcdef0")
        lines.append("--- /dev/null")
        lines.append(f"+++ b/{b}")
    elif rename_to:
        lines.append("similarity index 100%")
        lines.append(f"rename from {path}")
        lines.append(f"rename to {rename_to}")
    else:
        lines.append("index abcdef0..1234567 100644")
        lines.append(f"--- a/{path}")
        lines.append(f"+++ b/{b}")
    lines.append("@@ -1,1 +1,1 @@")
    for r in removed:
        lines.append(f"-{r}")
    for a in added:
        lines.append(f"+{a}")
    return "\n".join(lines) + "\n"


def _verdict(diff_text):
    return classify_diff(diff_text)[0]


# ---- ① 注释/文档 ----

def test_py_comment_only_exempt():
    d = _diff("foo.py", added=["# new comment"], removed=["# old comment"])
    assert _verdict(d) == "EXEMPT"

def test_js_line_comment_only_exempt():
    d = _diff("app.js", added=["  // updated note"])
    assert _verdict(d) == "EXEMPT"

def test_comment_plus_logic_not_exempt():
    d = _diff("foo.py", added=["# a comment", "x = compute()"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_block_comment_conservative_not_exempt():
    # 块注释不支持 → 保守判逻辑（正确方向：宁可多审）
    d = _diff("x.c", added=["/* a block comment */"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_doc_path_readme_exempt():
    d = _diff("README.md", added=["新增一行说明"])
    assert _verdict(d) == "EXEMPT"

def test_docs_dir_exempt():
    d = _diff("docs/guide.md", added=["任意文档改动"])
    assert _verdict(d) == "EXEMPT"

def test_non_doc_root_markdown_not_exempt():
    # 任意非约定文档 .md 可能承载行为 → 保守 NOT
    d = _diff("NOTES.md", added=["some note"])
    assert _verdict(d) == "NOT_EXEMPT"


# ---- 行为面路径守卫（bundle markdown 承载行为）----

def test_skill_md_behavior_path_not_exempt():
    d = _diff("sdflow-code-review/SKILL.md", added=["改一行指令"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_workflow_md_behavior_path_not_exempt():
    d = _diff("sdflow-init/assets/workflow/workflow.md", added=["改路由政策一行"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_assets_workflow_behavior_path_not_exempt():
    d = _diff("sdflow-init/assets/workflow/trigger-catalog.md", added=["# 看似注释"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_ship_gate_behavior_path_not_exempt():
    d = _diff("sdflow-ship/scripts/ship_gate.py", added=["# just a comment"])
    assert _verdict(d) == "NOT_EXEMPT"


# ---- ③ 版本常量：收窄为 VERSION/CHANGELOG，拒代码里 load-bearing ----

def test_version_file_exempt():
    d = _diff("VERSION", added=["v0.9.1"], removed=["v0.9.0"])
    assert _verdict(d) == "EXEMPT"

def test_changelog_exempt():
    d = _diff("CHANGELOG.md", added=["## v0.9.1"])
    assert _verdict(d) == "EXEMPT"

def test_api_version_in_code_not_exempt():
    # load-bearing 版本常量在代码里 → 不判白名单（无法机判是否切 code-path）
    d = _diff("config.py", added=["API_VERSION = 2"], removed=["API_VERSION = 1"])
    assert _verdict(d) == "NOT_EXEMPT"


# ---- ② 仅新增 tests/ ----

def test_new_test_file_exempt():
    d = _diff("tests/test_new.py", added=["def test_foo(): assert True"], new=True)
    assert _verdict(d) == "EXEMPT"

def test_new_conftest_not_exempt():
    d = _diff("tests/conftest.py", added=["import pytest"], new=True)
    assert _verdict(d) == "NOT_EXEMPT"

def test_new_non_test_codepath_not_exempt():
    d = _diff("src/newmod.py", added=["def f(): pass"], new=True)
    assert _verdict(d) == "NOT_EXEMPT"


# ---- 其余守卫 ----

def test_unsupported_lang_not_exempt():
    d = _diff("index.php", added=["$x = 1;"])
    assert _verdict(d) == "NOT_EXEMPT"

def test_rename_not_exempt():
    d = _diff("old.py", rename_to="new.py")
    assert _verdict(d) == "NOT_EXEMPT"

def test_empty_diff_not_exempt():
    assert _verdict("") == "NOT_EXEMPT"


# ---- 多文件混合 ----

def test_mixed_all_whitelist_exempt():
    d = (_diff("foo.py", added=["# comment"])
         + _diff("README.md", added=["doc"])
         + _diff("tests/test_a.py", added=["def test_a(): pass"], new=True))
    assert _verdict(d) == "EXEMPT"

def test_mixed_one_logic_file_not_exempt():
    d = (_diff("foo.py", added=["# comment"])
         + _diff("bar.py", added=["y = 1"]))
    assert _verdict(d) == "NOT_EXEMPT"
