"""render-review-page.py 的行为契约（add-html-review-and-dispatch-watchdog · RVP-01/02/03，tasks 3.4）。

只经公共接口测：子进程跑 CLI，读写文件，解析输出 HTML。
浏览器里的渲染行为（marked / 标注）不在本文件，留给浏览器冒烟。
"""
import base64
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HACK = REPO / "sdflow-init" / "assets" / "hack"
SCRIPT = HACK / "render-review-page.py"
ASSETS = HACK / "review-page"

MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js"
# 页面里两个 JSON 数据块的取块正则；取块的用例都用这两个，不各写一份。
DOCS_BLOCK_RE = re.compile(r'<script type="application/json" id="sdflow-docs">(.*?)</script>', re.S)
SAVED_BLOCK_RE = re.compile(r'<script type="application/json" id="sdflow-saved-notes">(.*?)</script>', re.S)


def run_cli(*args, cwd=None, script=SCRIPT):
    return subprocess.run(
        [sys.executable, "-I", str(script), *map(str, args)],
        cwd=str(cwd) if cwd else None,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )


def write_md(path, text="# 标题\n\n正文\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


@pytest.fixture
def md_a(tmp_path):
    return write_md(tmp_path / "a.md", "# A 文档\n\n正文 A\n")


def gen(tmp_path, *docs, out=None, extra=()):
    out = out or tmp_path / "review" / "page.html"
    args = ["--out", out, "--title", "测试页", "--no-open"]
    for d in docs:
        args += ["--doc", d]
    args += list(extra)
    return run_cli(*args, cwd=tmp_path), out


def html_of(out):
    return Path(out).read_bytes().decode("utf-8")


# ── 基本生成 · 确定性 · 总打印路径 ───────────────────────────────────────────

def test_generates_page_and_prints_absolute_path(tmp_path, md_a):
    r, out = gen(tmp_path, f"甲={md_a}")
    assert r.returncode == 0, r.stderr
    assert out.is_file()
    assert f"评审页：{out}" in r.stdout


def test_creates_missing_parent_directory(tmp_path, md_a):
    out = tmp_path / "x" / "y" / "review" / "p.html"
    r, _ = gen(tmp_path, f"甲={md_a}", out=out)
    assert r.returncode == 0, r.stderr
    assert out.is_file()


def test_output_is_byte_identical_across_runs(tmp_path, md_a):
    r1, out = gen(tmp_path, f"甲={md_a}")
    first = out.read_bytes()
    r2, _ = gen(tmp_path, f"甲={md_a}")
    assert r1.returncode == r2.returncode == 0
    assert out.read_bytes() == first


def test_docs_keep_command_line_order(tmp_path):
    a = write_md(tmp_path / "a.md", "# A\n")
    b = write_md(tmp_path / "b.md", "# B\n")
    r, out = gen(tmp_path, f"乙={b}", f"甲={a}")
    assert r.returncode == 0, r.stderr
    docs = parse_docs(html_of(out))
    assert [d["label"] for d in docs] == ["乙", "甲"]


def test_doc_text_roundtrips_exactly(tmp_path):
    body = "# T\r\n\r\n含 CRLF 与 unicode：中文 😀\r\n"
    md = write_md(tmp_path / "a.md", body)
    r, out = gen(tmp_path, f"甲={md}")
    assert r.returncode == 0, r.stderr
    assert parse_docs(html_of(out))[0]["text"] == body


def parse_docs(html):
    m = DOCS_BLOCK_RE.search(html)
    assert m, "找不到文档数据块"
    return json.loads(m.group(1))


# ── 退出码与三段 stderr ──────────────────────────────────────────────────────

def stderr_lines(r):
    return [ln for ln in r.stderr.splitlines() if ln.strip()]


def decode_error_text(raw, encoding):
    """按 Python 自己的报错文案取解码失败的原因，用来逐字比对告警行。"""
    try:
        raw.decode(encoding)
    except UnicodeDecodeError as exc:
        return str(exc)
    raise AssertionError("预期解码失败")


def assert_three_segments(r):
    lines = stderr_lines(r)
    assert lines, "stderr 为空"
    for ln in lines:
        assert re.fullmatch(r"render-review-page: ✗ problem=.+ cause=.+ fix=.+", ln), ln


def test_no_docs_is_usage_error_64(tmp_path):
    r = run_cli("--out", tmp_path / "p.html", "--title", "t", "--no-open", cwd=tmp_path)
    assert r.returncode == 64
    assert_three_segments(r)
    assert not (tmp_path / "p.html").exists()


def test_duplicate_label_is_usage_error_64(tmp_path, md_a):
    r, out = gen(tmp_path, f"甲={md_a}", f"甲={md_a}")
    assert r.returncode == 64
    assert_three_segments(r)
    assert not out.exists()


def test_doc_without_equals_is_usage_error_64(tmp_path, md_a):
    r, out = gen(tmp_path, str(md_a))
    assert r.returncode == 64
    assert_three_segments(r)


def test_missing_title_without_preset_is_usage_error_64(tmp_path, md_a):
    r = run_cli("--out", tmp_path / "p.html", "--doc", f"甲={md_a}", "--no-open", cwd=tmp_path)
    assert r.returncode == 64
    assert_three_segments(r)


def test_unknown_argument_is_usage_error_64(tmp_path, md_a):
    r, _ = gen(tmp_path, f"甲={md_a}", extra=["--bogus"])
    assert r.returncode == 64
    assert_three_segments(r)


def test_doc_label_splits_on_first_equals_only(tmp_path):
    md = write_md(tmp_path / "a=b.md", "# x\n")
    r, out = gen(tmp_path, f"甲={md}")
    assert r.returncode == 0, r.stderr
    assert parse_docs(html_of(out))[0]["label"] == "甲"


def test_missing_md_exit_2_and_no_file_left(tmp_path, md_a):
    ghost = tmp_path / "nope.md"
    r, out = gen(tmp_path, f"甲={md_a}", f"乙={ghost}")
    assert r.returncode == 2
    assert_three_segments(r)
    assert f"原文不存在：{ghost}" in r.stderr
    assert not out.exists()
    assert not out.parent.exists() or list(out.parent.iterdir()) == []


@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                    reason="需要 POSIX 权限语义且非 root")
def test_unwritable_target_exit_2_without_temp_residue(tmp_path, md_a):
    target_dir = tmp_path / "ro"
    target_dir.mkdir()
    target_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        r, out = gen(tmp_path, f"甲={md_a}", out=target_dir / "p.html")
    finally:
        target_dir.chmod(stat.S_IRWXU)
    assert r.returncode == 2
    assert_three_segments(r)
    assert "无法写出" in r.stderr
    assert list(target_dir.iterdir()) == []


def test_out_is_a_directory_exit_2_without_temp_residue(tmp_path, md_a):
    target = tmp_path / "isdir"
    target.mkdir()
    r, _ = gen(tmp_path, f"甲={md_a}", out=target)
    assert r.returncode == 2
    assert_three_segments(r)
    assert list(target.iterdir()) == []
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".")] == []


def test_missing_assets_exit_2(tmp_path, md_a):
    """脚本按自身所在目录找 review-page/：把脚本单独拷到没有资产的目录 ⇒ exit 2。"""
    lone = tmp_path / "lone"
    lone.mkdir()
    copy = lone / "render-review-page.py"
    copy.write_bytes(SCRIPT.read_bytes())
    out2 = tmp_path / "o2.html"
    r2 = run_cli("--out", out2, "--title", "t", "--doc", f"甲={md_a}", "--no-open",
                 cwd=tmp_path, script=copy)
    assert r2.returncode == 2
    assert_three_segments(r2)
    assert "评审页资产缺失" in r2.stderr
    assert "bash setup.sh" in r2.stderr
    assert not out2.exists()


# ── 安全：CSP · 内联脚本哈希 · 外部引用 · 嵌入转义 ───────────────────────────

# 开发期对 mermaid@12.2.0 dist/mermaid.min.js 实际下载后独立算出的 sha384（见 impl-report），
# 这里是已知好值，不是由模板里的常量推出来的。
MERMAID_SRI = "sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp"


def make_page(tmp_path, text="# 标题\n\n正文\n", label="甲"):
    md = write_md(tmp_path / "doc.md", text)
    r, out = gen(tmp_path, f"{label}={md}")
    assert r.returncode == 0, r.stderr
    return html_of(out)


def csp_of(page):
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', page)
    assert m, "找不到 CSP meta"
    return m.group(1)


def inline_classic_scripts(page):
    """内联的非数据块 <script>…</script> 正文（CSP 哈希对应的就是这段文本）。"""
    return [m.group(2) for m in re.finditer(r"<script((?:(?!>)[^>])*)>(.*?)</script>", page, re.S)
            if "application/json" not in m.group(1)]


def test_csp_is_first_element_in_head(tmp_path):
    page = make_page(tmp_path)
    head = page[page.index("<head>") + len("<head>"):]
    assert head.lstrip().startswith('<meta http-equiv="Content-Security-Policy"')
    assert page.index("Content-Security-Policy") < page.index("<script")


def test_charset_meta_is_within_first_1024_bytes(tmp_path):
    page = make_page(tmp_path)
    assert page.encode("utf-8").index(b'<meta charset="utf-8">') < 1024


def test_csp_directives_and_mermaid_single_file_only(tmp_path):
    csp = csp_of(make_page(tmp_path))
    for directive in ("default-src 'none'", "style-src 'unsafe-inline'", "img-src data:",
                      "connect-src 'none'", "base-uri 'none'", "form-action 'none'"):
        assert directive in csp, directive
    assert MERMAID_URL in csp
    # 不放行整个 jsDelivr 主机：主机名只允许作为 mermaid 完整路径的一部分出现
    assert csp.replace(MERMAID_URL, "").find("cdn.jsdelivr.net") == -1
    assert not re.search(r"https?://[^/\s;]+(?=[\s;]|$)", csp), "CSP 含裸主机源"
    assert "*" not in csp


def test_csp_hashes_match_inline_scripts(tmp_path):
    page = make_page(tmp_path)
    csp = csp_of(page)
    scripts = inline_classic_scripts(page)
    assert len(scripts) == 2
    hashes = re.findall(r"'sha256-([A-Za-z0-9+/=]+)'", csp)
    assert len(hashes) == 2
    computed = [base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode() for s in scripts]
    assert sorted(hashes) == sorted(computed)
    assert "{{" not in csp


def strip_data_and_vendor(page):
    page = DOCS_BLOCK_RE.sub("", page)
    page = SAVED_BLOCK_RE.sub("", page)
    return re.sub(r'<script id="sdflow-marked">.*?</script>', "", page, flags=re.S)


def test_no_external_references_in_template_markup(tmp_path):
    own = strip_data_and_vendor(make_page(tmp_path))
    assert not re.search(r"""\b(?:src|href|action)\s*=\s*["']?\s*(?:https?:)?//""", own, re.I)
    assert "@import" not in own
    assert not re.search(r"url\(\s*[\"']?\s*(?:https?:)?//", own, re.I)
    urls = set(re.findall(r"https?://[^\s'\"<>;)]+", own))
    # 页面里唯一允许出现的网络地址：CSP 与脚本常量里的 mermaid 固定文件
    assert urls == {MERMAID_URL}
    assert own.count(MERMAID_URL) == 2


def test_mermaid_sri_and_version_are_pinned_in_template(tmp_path):
    own = strip_data_and_vendor(make_page(tmp_path))
    assert MERMAID_SRI in own
    assert own.count("mermaid@") == 2  # CSP + 脚本常量
    assert own.count("mermaid@12.2.0") == 2


def test_no_inline_event_handler_attributes(tmp_path):
    own = strip_data_and_vendor(make_page(tmp_path))
    markup = re.sub(r'<script id="sdflow-app">.*?</script>', "", own, flags=re.S)
    assert not re.search(r"\son[a-z]+\s*=", markup, re.I)
    app = re.search(r'<script id="sdflow-app">(.*?)</script>', own, re.S).group(1)
    assert not re.search(r"""setAttribute\(\s*['"]on""", app)


def test_vendored_marked_is_safe_to_inline_and_pinned():
    marked = (ASSETS / "marked.umd.js").read_text(encoding="utf-8")
    assert "</script" not in marked.lower()
    assert "<script" not in marked.lower()
    assert "\r" not in marked
    assert "marked v18.1.1" in marked
    assert (ASSETS / "LICENSE.marked").read_text(encoding="utf-8").lstrip().startswith("# License information")


HOSTILE = (
    "# 危险\n\n"
    "<script>alert(1)</script>\n\n"
    "段落里有 </script> 和 <!-- 未闭合注释\n\n"
    "<script>\nvar x = 1;\n</script>\n"
    "```html\n</script><!--<script>\n```\n"
)


def test_hostile_markdown_does_not_break_data_block(tmp_path):
    page = make_page(tmp_path, HOSTILE)
    m = DOCS_BLOCK_RE.search(page)
    assert m
    block = m.group(1)
    assert "<" not in block and ">" not in block and "&" not in block
    assert json.loads(block)[0]["text"] == HOSTILE
    # 整页的脚本元素：两个数据块 + marked + app
    assert len(re.findall(r"<script\b", page)) == 4
    assert len(re.findall(r"</script>", page)) == 4


def test_json_escapes_line_separators(tmp_path):
    text = "# t\n\nA\u2028B\u2029C\n"
    page = make_page(tmp_path, text)
    assert "\u2028" not in page and "\u2029" not in page
    assert "\\u2028" in page and "\\u2029" in page
    assert parse_docs(page)[0]["text"] == text


def test_placeholder_lookalikes_in_content_are_not_substituted(tmp_path):
    text = "# t\n\n{{TITLE}} {{MARKED}} {{HASH_APP}} {{DOCS_JSON}}\n"
    md = write_md(tmp_path / "doc.md", text)
    out = tmp_path / "p.html"
    r = run_cli("--out", out, "--title", "{{DOCS_JSON}}", "--doc", f"{{{{TITLE}}}}={md}",
                "--no-open", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    page = html_of(out)
    docs = parse_docs(page)
    assert docs[0]["text"] == text
    assert docs[0]["label"] == "{{TITLE}}"
    assert "<title>{{DOCS_JSON}}</title>" in page


def test_title_is_html_escaped(tmp_path):
    md = write_md(tmp_path / "doc.md")
    out = tmp_path / "p.html"
    r = run_cli("--out", out, "--title", '<img src=x onerror=alert(1)> "&"', "--doc", f"<b>={md}",
                "--no-open", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    page = html_of(out)
    assert "<title>&lt;img src=x onerror=alert(1)&gt; &quot;&amp;&quot;</title>" in page
    assert "<img src=x" not in page


# ── 预设 ─────────────────────────────────────────────────────────────────────

def make_change(base):
    for rel in ("spec-review-report.md", "proposal.md", "design.md", "tasks.md", "decision-memo.md",
                "specs/zeta/spec.md", "specs/alpha/spec.md"):
        write_md(base / rel, f"# {rel}\n")
    return base


def preset_run(tmp_path, preset, base, *extra):
    return run_cli("--preset", preset, "--dir", base, "--no-open", *extra, cwd=tmp_path)


def test_design_gate_preset_order(tmp_path):
    base = make_change(tmp_path / "chg")
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 0, r.stderr
    out = base / "review" / "design-gate.html"
    assert out.is_file()
    labels = [d["label"] for d in parse_docs(html_of(out))]
    assert labels == ["spec-review-report", "proposal", "design", "spec:alpha", "spec:zeta",
                      "tasks", "decision-memo"]


def test_design_gate_optional_memo_missing_is_skipped(tmp_path):
    base = make_change(tmp_path / "chg")
    (base / "decision-memo.md").unlink()
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 0, r.stderr
    labels = [d["label"] for d in parse_docs(html_of(base / "review" / "design-gate.html"))]
    assert "decision-memo" not in labels and labels[-1] == "tasks"


def test_design_gate_required_missing_exit_2_no_file(tmp_path):
    base = make_change(tmp_path / "chg")
    (base / "design.md").unlink()
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 2
    assert_three_segments(r)
    assert "design.md" in r.stderr
    assert not (base / "review").exists()


def test_shipped_preset_without_code_review_report(tmp_path):
    base = tmp_path / "arch"
    write_md(base / "hand-off.md")
    write_md(base / "verify-report.md")
    r = preset_run(tmp_path, "shipped", base)
    assert r.returncode == 0, r.stderr
    labels = [d["label"] for d in parse_docs(html_of(base / "review" / "shipped.html"))]
    assert labels == ["hand-off", "verify-report"]


def test_shipped_preset_includes_code_review_report_last(tmp_path):
    base = tmp_path / "arch"
    for n in ("hand-off", "verify-report", "code-review-report"):
        write_md(base / f"{n}.md")
    r = preset_run(tmp_path, "shipped", base)
    assert r.returncode == 0, r.stderr
    labels = [d["label"] for d in parse_docs(html_of(base / "review" / "shipped.html"))]
    assert labels == ["hand-off", "verify-report", "code-review-report"]


def test_roadmap_preset(tmp_path):
    base = tmp_path / "rm"
    write_md(base / "roadmap.md")
    write_md(base / "design.md")
    r = preset_run(tmp_path, "roadmap-review", base)
    assert r.returncode == 0, r.stderr
    labels = [d["label"] for d in parse_docs(html_of(base / "review" / "roadmap-review.html"))]
    assert labels == ["roadmap", "design"]


def test_code_review_preset(tmp_path):
    base = tmp_path / "chg"
    write_md(base / "code-review-report.md")
    r = preset_run(tmp_path, "code-review", base)
    assert r.returncode == 0, r.stderr
    labels = [d["label"] for d in parse_docs(html_of(base / "review" / "code-review.html"))]
    assert labels == ["code-review-report"]


def test_code_review_preset_missing_report_exit_2_no_file(tmp_path):
    base = tmp_path / "chg"
    base.mkdir()
    r = preset_run(tmp_path, "code-review", base)
    assert r.returncode == 2
    assert_three_segments(r)
    assert "code-review-report.md" in r.stderr
    assert not (base / "review").exists()


def test_preset_respects_explicit_out_and_title(tmp_path):
    base = make_change(tmp_path / "chg")
    out = tmp_path / "elsewhere" / "p.html"
    r = preset_run(tmp_path, "design-gate", base, "--out", out, "--title", "自定标题")
    assert r.returncode == 0, r.stderr
    assert "<title>自定标题</title>" in html_of(out)


def test_preset_usage_errors(tmp_path, md_a):
    base = make_change(tmp_path / "chg")
    r1 = run_cli("--preset", "design-gate", "--no-open", cwd=tmp_path)
    r2 = run_cli("--preset", "design-gate", "--dir", base, "--doc", f"甲={md_a}", "--no-open", cwd=tmp_path)
    r3 = run_cli("--preset", "nope", "--dir", base, "--no-open", cwd=tmp_path)
    for r in (r1, r2, r3):
        assert r.returncode == 64, r.stderr
        assert_three_segments(r)


# ── 路径显示 ─────────────────────────────────────────────────────────────────

def vcs_available():
    try:
        return subprocess.run(["git", "--version"], capture_output=True).returncode == 0
    except OSError:
        return False


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_paths_are_repo_relative_inside_a_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    md = write_md(repo / "openspec" / "changes" / "x" / "design.md")
    out = repo / "openspec" / "changes" / "x" / "review" / "p.html"
    r = run_cli("--out", out, "--title", "t", "--doc", f"设计={md}", "--no-open", cwd=repo)
    assert r.returncode == 0, r.stderr
    assert parse_docs(html_of(out))[0]["path"] == "openspec/changes/x/design.md"


def test_paths_fall_back_to_out_dir_relative_outside_a_repo(tmp_path):
    work = tmp_path / "plain"
    md = write_md(work / "docs" / "a.md")
    out = work / "review" / "p.html"
    r = run_cli("--out", out, "--title", "t", "--doc", f"甲={md}", "--no-open", cwd=work)
    assert r.returncode == 0, r.stderr
    assert parse_docs(html_of(out))[0]["path"] == "../docs/a.md"


# ── 打开浏览器 ───────────────────────────────────────────────────────────────

@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location("render_review_page_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(module, tmp_path, md, capsys):
    code = module.main(["--out", str(tmp_path / "o" / "p.html"), "--title", "t", "--doc", f"甲={md}"])
    return code, capsys.readouterr().out


# 打桩 linux + DISPLAY，不打桩 darwin：darwin 打桩会让 Path.as_uri() 在 Python 3.14 下
# 导入 Linux 上不存在的 _scproxy（urllib.request 在 darwin 分支导入它）。
def test_open_success_prints_attempted(module, tmp_path, md_a, capsys, monkeypatch):
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(module.webbrowser, "open", lambda url: True)
    code, out = run_main(module, tmp_path, md_a, capsys)
    assert code == 0
    assert "已尝试在浏览器打开" in out and "评审页：" in out


@pytest.mark.parametrize("behaviour", ["false", "raise"])
def test_open_failure_keeps_exit_0_and_prints_path(module, tmp_path, md_a, capsys, monkeypatch, behaviour):
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    calls = []

    def fake(url):
        calls.append(url)
        if behaviour == "raise":
            raise RuntimeError("no browser")
        return False

    monkeypatch.setattr(module.webbrowser, "open", fake)
    code, out = run_main(module, tmp_path, md_a, capsys)
    assert code == 0
    assert len(calls) == 1  # 确实走到了 webbrowser.open，而不是在更早处就判为失败
    assert "未能自动打开，请手动打开上面的路径" in out
    assert f"评审页：{tmp_path / 'o' / 'p.html'}" in out
    assert (tmp_path / "o" / "p.html").is_file()


def test_headless_linux_does_not_call_webbrowser(module, tmp_path, md_a, capsys, monkeypatch):
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    def forbidden(url):
        raise AssertionError("无图形环境不应调用 webbrowser.open")

    monkeypatch.setattr(module.webbrowser, "open", forbidden)
    code, out = run_main(module, tmp_path, md_a, capsys)
    assert code == 0
    assert "未能自动打开" in out


def test_no_open_flag_never_calls_webbrowser(module, tmp_path, md_a, capsys, monkeypatch):
    monkeypatch.setattr(module.sys, "platform", "darwin")

    def forbidden(url):
        raise AssertionError("called")

    monkeypatch.setattr(module.webbrowser, "open", forbidden)
    code = module.main(["--out", str(tmp_path / "p.html"), "--title", "t", "--doc", f"甲={md_a}", "--no-open"])
    assert code == 0
    assert "评审页：" in capsys.readouterr().out


def test_script_has_reconfigure_prelude():
    src = SCRIPT.read_text(encoding="utf-8")
    assert re.search(r"import sys\n\nfor _s in \(sys\.stdout, sys\.stderr\):\n"
                     r"    try: _s\.reconfigure\(encoding=\"utf-8\", errors=\"replace\"\)\n"
                     r"    except Exception: pass\n", src)


# ── 补强：可选文档读不出 · 不可编码标题 · 未知 preset ─────────────────────────

def test_optional_doc_not_utf8_warns_and_is_skipped(tmp_path):
    base = tmp_path / "chg"
    for name in ("hand-off.md", "verify-report.md"):
        write_md(base / name, "# %s\n" % name)
    (base / "code-review-report.md").write_bytes(b"\xff\xfe\x00bad")
    r = preset_run(tmp_path, "shipped", base)
    assert r.returncode == 0
    assert stderr_lines(r) == [
        "render-review-page: ⚠ problem=可选原文已跳过：%s cause=%s fix=确认文件是可读的 UTF-8 文本后重跑"
        % (base / "code-review-report.md", decode_error_text(b"\xff\xfe\x00bad", "utf-8"))]
    page = html_of(base / "review" / "shipped.html")
    assert "code-review-report" not in page


def test_unencodable_title_exit_2_without_traceback(tmp_path, md_a):
    r, out = gen(tmp_path, f"甲={md_a}", extra=("--title", "bad\udcff"))
    # 后一个 --title 覆盖前一个
    assert r.returncode == 2
    assert "Traceback" not in r.stderr
    assert_three_segments(r)


def test_preset_docs_unknown_preset_raises():
    spec = importlib.util.spec_from_file_location("render_review_page_bogus", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with pytest.raises(ValueError):
        mod.preset_docs("bogus", ".")


# ── 已落盘意见：read_saved_notes · locate_line · 嵌入（RVP-10，tasks 3.1–3.3）────────

HEX_A = "0123456789abcdef"
HEX_B = "fedcba9876543210"


def note(**kw):
    base = {"n": 1, "id": HEX_A, "doc": "design", "path": "openspec/changes/x/design.md",
            "heading": "H", "quote": "原文一", "before": "", "after": "", "comment": "意见一"}
    base.update(kw)
    return base


def notes_block(page, notes, fence="```", copied_at=None, v=2):
    payload = {"v": v, "page": page, "notes": notes}
    if copied_at is not None:
        payload["copied_at"] = copied_at
    return "%sjson\n%s\n%s\n" % (fence, json.dumps(payload, ensure_ascii=False), fence)


def write_notes(path, *chunks):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("".join(chunks).encode("utf-8"))
    return path


def read_notes(module, path, page="design-gate.html"):
    return module.read_saved_notes(Path(path), page)


PAGE_PATH = "openspec/changes/x/review/design-gate.html"


def test_read_saved_notes_missing_file_returns_empty_silently(module, tmp_path, capsys):
    assert read_notes(module, tmp_path / "review-notes.md") == []
    assert capsys.readouterr().err == ""


def test_read_saved_notes_basic_fields_and_defaults(module, tmp_path, capsys):
    p = write_notes(tmp_path / "n.md", "前言\n\n",
                    notes_block(PAGE_PATH, [{"quote": "q", "comment": "c"}], copied_at="2026-10-20 10:00"))
    got = read_notes(module, p)
    assert got == [{"id": "", "n": 0, "doc": "", "path": "", "heading": "", "quote": "q",
                    "before": "", "after": "", "comment": "c", "copied_at": "2026-10-20 10:00",
                    "inFigure": False}]
    assert capsys.readouterr().err == ""


def test_read_saved_notes_bom_prefixed_file_keeps_first_block(module, tmp_path):
    """[impl-review-fix] 文件以 UTF-8 BOM 开头时，第一个块的开围栏不受 BOM 影响。"""
    p = tmp_path / "n.md"
    p.write_bytes(b"\xef\xbb\xbf" + notes_block(PAGE_PATH, [note(comment="首块")]).encode("utf-8"))
    assert [n["comment"] for n in read_notes(module, p)] == ["首块"]


def test_read_saved_notes_copied_at_defaults_to_empty_string(module, tmp_path):
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [note()]))
    assert read_notes(module, p)[0]["copied_at"] == ""


def test_two_pages_share_one_file_each_takes_its_own(module, tmp_path):
    p = write_notes(tmp_path / "n.md",
                    notes_block("openspec/changes/x/review/design-gate.html", [note(id=HEX_A, comment="设计门")]),
                    "\n",
                    notes_block("openspec/changes/x/review/code-review.html", [note(id=HEX_B, comment="代码审")]))
    assert [n["comment"] for n in read_notes(module, p, "design-gate.html")] == ["设计门"]
    assert [n["comment"] for n in read_notes(module, p, "code-review.html")] == ["代码审"]


def test_other_pages_blocks_are_not_counted_as_unparseable(module, tmp_path, capsys):
    p = write_notes(tmp_path / "n.md", notes_block("a/b/code-review.html", [note()]))
    assert read_notes(module, p) == []
    assert capsys.readouterr().err == ""


def test_fence_of_four_backticks_needs_four_to_close(module, tmp_path):
    p = write_notes(tmp_path / "n.md",
                    notes_block(PAGE_PATH, [note(comment="含 ``` 围栏")], fence="````"))
    assert read_notes(module, p)[0]["comment"] == "含 ``` 围栏"


def test_closing_fence_of_wrong_length_is_plain_text(module, tmp_path, capsys):
    text = "````json\n%s\n```\n" % json.dumps({"page": PAGE_PATH, "notes": [note()]})
    p = write_notes(tmp_path / "n.md", text)
    assert read_notes(module, p) == []
    assert capsys.readouterr().err == ""  # 不是块，当普通文本，不计入无法解析


def test_lone_json_fence_line_in_comment_body_is_plain_text(module, tmp_path, capsys):
    body = ("# 评审意见\n\n## 1. design\n\n> q\n\n```json\n正文里单独一行围栏\n\n"
            + notes_block(PAGE_PATH, [note(comment="真意见")]))
    p = write_notes(tmp_path / "n.md", body)
    got = read_notes(module, p)
    assert [n["comment"] for n in got] == ["真意见"]
    assert capsys.readouterr().err == ""


def test_json_line_must_start_with_open_brace(module, tmp_path, capsys):
    text = "```json\n  [1,2]\n```\n"
    p = write_notes(tmp_path / "n.md", text)
    assert read_notes(module, p) == []
    assert capsys.readouterr().err == ""


def test_same_id_takes_last_but_keeps_first_position(module, tmp_path):
    p = write_notes(tmp_path / "n.md",
                    notes_block(PAGE_PATH, [note(id=HEX_A, comment="旧"), note(id=HEX_B, comment="乙")]),
                    notes_block(PAGE_PATH, [note(id=HEX_A, comment="新")]))
    got = read_notes(module, p)
    assert [(n["id"], n["comment"]) for n in got] == [(HEX_A, "新"), (HEX_B, "乙")]


def test_invalid_id_is_treated_as_missing_and_keyed_by_doc_quote_comment(module, tmp_path):
    a = note(id="NOT-HEX", comment="同")
    b = note(id="ALSO-BAD", comment="同")           # doc+quote+comment 相同 => 同一条
    c = note(id="", comment="异")
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [a, c]), notes_block(PAGE_PATH, [b]))
    got = read_notes(module, p)
    assert [(n["id"], n["comment"]) for n in got] == [("", "同"), ("", "异")]


def test_missing_id_notes_dedupe_by_doc_quote_comment(module, tmp_path):
    n1 = {"doc": "d", "quote": "q", "comment": "c", "n": 1}
    n2 = {"doc": "d", "quote": "q", "comment": "c", "n": 7}
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [n1]), notes_block(PAGE_PATH, [n2]))
    got = read_notes(module, p)
    assert len(got) == 1 and got[0]["n"] == 7


def test_id_as_list_skips_that_note_without_crashing(module, tmp_path, capsys):
    p = write_notes(tmp_path / "n.md",
                    notes_block(PAGE_PATH, [note(id=["x"]), note(id=HEX_B, comment="好")]))
    got = read_notes(module, p)
    assert [n["comment"] for n in got] == ["好"]
    assert "已跳过 1 个无法解析的意见块（第 1 行）" in capsys.readouterr().err


def test_null_before_skips_that_note(module, tmp_path, capsys):
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [note(before=None)]))
    assert read_notes(module, p) == []
    assert "已跳过 1 个" in capsys.readouterr().err


@pytest.mark.parametrize("bad", [
    {"quote": 1, "comment": "c"},
    {"quote": "q", "comment": None},
    {"quote": "q"},
    {"comment": "c"},
    "not-an-object",
    {"quote": "q", "comment": "c", "n": "1"},
    {"quote": "q", "comment": "c", "n": True},
    {"quote": "q", "comment": "c", "heading": 3},
    {"quote": "q", "comment": "c", "inFigure": "true"},
    {"quote": "q", "comment": "c", "inFigure": None},
])
def test_ill_typed_notes_are_skipped_and_counted(module, tmp_path, capsys, bad):
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [bad, note(id=HEX_B, comment="好")]))
    got = read_notes(module, p)
    assert [n["comment"] for n in got] == ["好"]
    assert "已跳过 1 个无法解析的意见块" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [
    "{not json",
    '{"page": 1, "notes": []}',
    '{"page": "%s", "notes": {}}' % PAGE_PATH,
    '{"notes": []}',
])
def test_malformed_blocks_are_skipped_with_line_numbers(module, tmp_path, capsys, payload):
    text = "头\n```json\n%s\n```\n" % payload
    p = write_notes(tmp_path / "n.md", text, notes_block(PAGE_PATH, [note(comment="好")]))
    got = read_notes(module, p)
    assert [n["comment"] for n in got] == ["好"]
    err = capsys.readouterr().err
    assert "已跳过 1 个无法解析的意见块（第 2 行）" in err
    assert err.count("\n") == 1  # 汇总一行


def test_multiple_skips_summarised_in_one_line(module, tmp_path, capsys):
    bad = "```json\n{oops\n```\n"
    p = write_notes(tmp_path / "n.md", bad, "x\n", bad)
    read_notes(module, p)
    assert capsys.readouterr().err == (
        "render-review-page: ⚠ problem=已跳过 2 个无法解析的意见块（第 1、5 行）"
        " cause=review-notes.md 中的 json 块被改写或不是评审页产出的格式"
        " fix=对照评审页「复制意见」的原文修正该块，或忽略（不影响生成）\n")


def test_skip_count_is_per_block_not_per_note(module, tmp_path, capsys):
    """同一块里两条意见不合格、另一块整块坏：按块计 2，不按条计 3。"""
    p = write_notes(tmp_path / "n.md",
                    notes_block(PAGE_PATH, [{"quote": 1, "comment": "c"}, {"quote": "q"}, note(comment="好")]),
                    "```json\n{oops\n```\n")
    assert [n["comment"] for n in read_notes(module, p)] == ["好"]
    assert "已跳过 2 个无法解析的意见块（第 1、4 行）" in capsys.readouterr().err


def test_in_figure_flag_is_kept_and_defaults_to_false(module, tmp_path):
    p = write_notes(tmp_path / "n.md", notes_block(PAGE_PATH, [
        note(id=HEX_A, inFigure=True), note(id=HEX_B, comment="旧块没有该字段")]))
    assert [(n["id"], n["inFigure"]) for n in read_notes(module, p)] == [(HEX_A, True), (HEX_B, False)]


def test_lone_surrogate_in_quote_is_replaced_not_fatal(module, tmp_path):
    raw = ('```json\n{"page":"%s","notes":[{"quote":"截断\\ud83d","comment":"c\\ude00"}]}\n```\n'
           % PAGE_PATH)
    p = write_notes(tmp_path / "n.md", raw)
    got = read_notes(module, p)
    assert got[0]["quote"] == "截断�" and got[0]["comment"] == "c�"
    got[0]["quote"].encode("utf-8")  # 不抛


def test_valid_surrogate_pair_is_kept(module, tmp_path):
    raw = '```json\n{"page":"%s","notes":[{"quote":"\\ud83d\\ude00","comment":"c"}]}\n```\n' % PAGE_PATH
    p = write_notes(tmp_path / "n.md", raw)
    assert read_notes(module, p)[0]["quote"] == "\U0001F600"


def test_unreadable_file_warns_and_returns_empty(module, tmp_path, capsys):
    p = tmp_path / "n.md"
    p.write_bytes(b"\xff\xfe\x00bad")
    assert read_notes(module, p) == []
    assert capsys.readouterr().err == (
        "render-review-page: ⚠ problem=无法读取 %s cause=UnicodeDecodeError: %s"
        " fix=检查文件权限与编码（应为 UTF-8）；本次页面不含已落盘意见\n"
        % (p, decode_error_text(b"\xff\xfe\x00bad", "utf-8-sig")))


def test_directory_as_notes_file_warns_and_returns_empty(module, tmp_path, capsys):
    d = tmp_path / "review-notes.md"
    d.mkdir()
    assert read_notes(module, d) == []
    assert "⚠ problem=无法读取 " in capsys.readouterr().err


def test_crlf_notes_file_is_parsed(module, tmp_path):
    raw = notes_block(PAGE_PATH, [note(comment="crlf")]).replace("\n", "\r\n")
    p = write_notes(tmp_path / "n.md", raw)
    assert [n["comment"] for n in read_notes(module, p)] == ["crlf"]


# locate_line ----------------------------------------------------------------

DOC_TEXT = "# 标题\n\n第一段 重复句。\n\n中间\n\n第二段 重复句。\n\n唯一句子在此。\n"
DOCS = [{"label": "design", "path": "openspec/changes/x/design.md", "text": DOC_TEXT}]


def loc(module, **kw):
    n = note(**kw)
    return module.locate_line(n, DOCS)


def test_locate_level1_before_quote_after(module):
    # 两处「重复句。」：前后文都给出，命中第二处（第 7 行）
    assert loc(module, quote="重复句。", before="第二段 ", after="\n\n唯一") == 7


def test_locate_level2_before_quote_when_after_does_not_match(module):
    assert loc(module, quote="重复句。", before="第二段 ", after="不存在的后文") == 7


def test_locate_level3_unique_quote(module):
    assert loc(module, quote="唯一句子在此。", before="不匹配", after="不匹配") == 9


def test_locate_truncated_quote_with_adjacent_after_hits_level1(module):
    """页面截断超长原文后，后文紧接截断后的原文：第一级「前文+原文+后文」直接命中第二处。"""
    head = "x" * 20
    text = "前 %s甲甲\n前 %s乙乙\n" % (head, head)
    docs = [{"label": "d", "path": "p.md", "text": text}]
    assert module.locate_line(note(path="p.md", quote=head[:15], before="前 ", after="xxxxx乙"), docs) == 2


def test_locate_level2_needs_nonempty_before(module):
    # 只有后文且后文对不上：不退回「原文」去取第一处
    assert loc(module, quote="重复句。", before="", after="不存在的后文") is None


def test_locate_uniqueness_counts_overlapping_occurrences(module):
    docs = [{"label": "d", "path": "p.md", "text": "aaa\n"}]
    assert module.locate_line(note(path="p.md", quote="aa"), docs) is None


def test_locate_returns_none_when_quote_repeats_without_usable_context(module):
    assert loc(module, quote="重复句。", before="", after="") is None
    assert loc(module, quote="重复句。", before="错的前文", after="错的后文") is None


def test_locate_returns_none_when_quote_crosses_markdown_markup(module):
    docs = [{"label": "d", "path": "p.md", "text": "这里有 **加粗** 文字\n"}]
    n = note(path="p.md", quote="这里有 加粗 文字")
    assert module.locate_line(n, docs) is None


def test_locate_none_for_missing_quote_or_unknown_path(module):
    assert loc(module, quote="") is None
    assert loc(module, path="openspec/changes/other/design.md", quote="唯一句子在此。") is None
    assert loc(module, path="", quote="唯一句子在此。") is None


def test_locate_does_not_open_any_file(module, monkeypatch):
    import builtins

    def forbidden(*a, **k):
        raise AssertionError("locate_line 不得打开文件")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(module.Path, "read_bytes", forbidden)
    monkeypatch.setattr(module.Path, "read_text", forbidden)
    monkeypatch.setattr(module.Path, "open", forbidden)
    assert loc(module, path="../../etc/hosts", quote="localhost") is None


# CLI：嵌入 · stdout · 确定性 · 转义 --------------------------------------------

def repo_with_change(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    base = repo / "openspec" / "changes" / "x"
    write_md(base / "design.md", DOC_TEXT)
    return repo, base


def saved_notes_of(page):
    m = SAVED_BLOCK_RE.search(page)
    assert m, "找不到已落盘意见数据块"
    return json.loads(m.group(1))


def gen_page(repo, base, *extra):
    out = base / "review" / "design-gate.html"
    r = run_cli("--out", out, "--title", "t", "--doc", f"design={base / 'design.md'}", "--no-open",
                *extra, cwd=repo)
    return r, out


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_no_notes_file_embeds_empty_array_and_no_count_line(tmp_path):
    repo, base = repo_with_change(tmp_path)
    r, out = gen_page(repo, base)
    assert r.returncode == 0, r.stderr
    assert saved_notes_of(html_of(out)) == []
    assert "已嵌入" not in r.stdout


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_notes_are_embedded_with_line_and_count_line(tmp_path):
    repo, base = repo_with_change(tmp_path)
    write_notes(base / "review" / "review-notes.md", "说明\n",
                notes_block(PAGE_PATH, [
                    note(id=HEX_A, n=1, quote="唯一句子在此。", comment="找得到"),
                    note(id=HEX_B, n=2, quote="不存在的原文", comment="找不到"),
                ], copied_at="2026-10-20 10:00"))
    r, out = gen_page(repo, base)
    assert r.returncode == 0, r.stderr
    assert r.stderr == ""
    assert "已嵌入 2 条已落盘意见（1 条未找到行号）" in r.stdout
    saved = saved_notes_of(html_of(out))
    assert [(s["id"], s["line"], s["copied_at"]) for s in saved] == [
        (HEX_A, 9, "2026-10-20 10:00"), (HEX_B, None, "2026-10-20 10:00")]
    assert set(saved[0]) == {"id", "n", "doc", "path", "heading", "quote", "before", "after",
                             "comment", "copied_at", "line", "inFigure"}


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_in_figure_flag_is_embedded(tmp_path):
    repo, base = repo_with_change(tmp_path)
    write_notes(base / "review" / "review-notes.md",
                notes_block(PAGE_PATH, [note(id=HEX_A, inFigure=True), note(id=HEX_B, comment="旧")]))
    r, out = gen_page(repo, base)
    assert r.returncode == 0, r.stderr
    assert [(s["id"], s["inFigure"]) for s in saved_notes_of(html_of(out))] == [(HEX_A, True), (HEX_B, False)]


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_embedding_is_byte_identical_across_runs(tmp_path):
    repo, base = repo_with_change(tmp_path)
    write_notes(base / "review" / "review-notes.md",
                notes_block(PAGE_PATH, [note(id=HEX_A), note(id=HEX_B, comment="乙")]))
    r1, out = gen_page(repo, base)
    first = out.read_bytes()
    r2, _ = gen_page(repo, base)
    assert r1.returncode == r2.returncode == 0
    assert out.read_bytes() == first


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_hostile_notes_do_not_close_the_data_block(tmp_path):
    repo, base = repo_with_change(tmp_path)
    nasty = "</script><script>alert(1)</script> & A\u2028B\u2029C <!--"
    write_notes(base / "review" / "review-notes.md",
                notes_block(PAGE_PATH, [note(comment=nasty, quote="q" + nasty)]))
    r, out = gen_page(repo, base)
    assert r.returncode == 0, r.stderr
    page = html_of(out)
    assert "\u2028" not in page and "\u2029" not in page
    block = SAVED_BLOCK_RE.search(page).group(1)
    assert "<" not in block and ">" not in block and "&" not in block
    assert json.loads(block)[0]["comment"] == nasty
    assert len(re.findall(r"<script\b", page)) == 4


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_note_path_escaping_the_repo_is_not_read(tmp_path):
    repo, base = repo_with_change(tmp_path)
    secret = tmp_path / "secret.md"
    secret.write_text("CANARY-TEXT\n", encoding="utf-8")
    # repo/openspec/changes/x/../../../../secret.md 即 tmp_path/secret.md
    write_notes(base / "review" / "review-notes.md",
                notes_block(PAGE_PATH, [note(path="openspec/changes/x/../../../../secret.md",
                                             quote="CANARY-TEXT")]))
    r, out = gen_page(repo, base)
    assert r.returncode == 0, r.stderr
    assert saved_notes_of(html_of(out))[0]["line"] is None


@pytest.mark.skipif(not vcs_available(), reason="需要 git")
def test_unreadable_notes_file_keeps_exit_0_with_warning(tmp_path):
    repo, base = repo_with_change(tmp_path)
    (base / "review").mkdir(parents=True)
    (base / "review" / "review-notes.md").write_bytes(b"\xff\xfe\x00bad")
    r, out = gen_page(repo, base)
    assert r.returncode == 0
    assert "⚠ problem=无法读取 " in r.stderr
    assert saved_notes_of(html_of(out)) == []


# 输出权限 · 缺 specs（RVP-17，tasks 3.4）--------------------------------------

@pytest.mark.skipif(os.name == "nt", reason="需要 POSIX 权限语义")
def test_output_mode_follows_umask_022(tmp_path, md_a):
    old = os.umask(0o022)
    try:
        r, out = gen(tmp_path, f"甲={md_a}")
    finally:
        os.umask(old)
    assert r.returncode == 0, r.stderr
    assert stat.S_IMODE(out.stat().st_mode) == 0o644


def test_design_gate_without_specs_warns_once_and_exits_0(tmp_path):
    base = make_change(tmp_path / "chg")
    for spec in (base / "specs").glob("*/spec.md"):
        spec.unlink()
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 0, r.stderr
    assert stderr_lines(r) == [
        "render-review-page: ⚠ problem=设计门页缺少 specs cause=chg/specs/ 下没有 */spec.md"
        " fix=确认本 change 是否应有 delta spec；页面已照常生成"]
    assert (base / "review" / "design-gate.html").is_file()


def test_design_gate_without_specs_dir_also_warns(tmp_path):
    base = make_change(tmp_path / "chg")
    shutil.rmtree(base / "specs")
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 0, r.stderr
    assert "⚠ problem=设计门页缺少 specs" in r.stderr


def test_design_gate_with_specs_has_no_warning(tmp_path):
    base = make_change(tmp_path / "chg")
    r = preset_run(tmp_path, "design-gate", base)
    assert r.returncode == 0 and r.stderr == ""


# 用法错误文案（tasks 3.5）--------------------------------------------------------

FIXED_USAGE_CAUSE = "参数写错，或脚本版本旧于调用它的 SKILL"
FIXED_USAGE_FIX = "按 --help 修正，或跑 bash setup.sh"


@pytest.mark.parametrize("args, detail", [
    (["--preset", "design-gate", "--doc", "甲=x.md", "--dir", "d"], "--preset 与 --doc 不能同时使用"),
    (["--preset", "design-gate"], "--preset 需要 --dir"),
    (["--dir", "d", "--out", "o.html", "--title", "t", "--doc", "甲=x.md"], "--dir 只与 --preset 一起使用"),
    (["--out", "o.html", "--title", "t"], "至少需要一个 --doc（或改用 --preset）"),
    (["--title", "t", "--doc", "甲=x.md"], "缺少 --out"),
    (["--out", "o.html", "--doc", "甲=x.md"], "未用 --preset 时必须给 --title"),
    (["--out", "o.html", "--title", "t", "--doc", "无等号"], "--doc 必须写成 标签=路径"),
    (["--out", "o.html", "--title", "t", "--doc", "=x.md"], "--doc 的标签与路径都不能为空"),
    (["--out", "o.html", "--title", "t", "--doc", "甲=x.md", "--doc", "甲=y.md"], "标签重复：甲"),
])
def test_usage_errors_use_fixed_cause_and_put_detail_in_problem(tmp_path, args, detail):
    r = run_cli(*args, "--no-open", cwd=tmp_path)
    assert r.returncode == 64
    assert len(stderr_lines(r)) == 1
    assert re.fullmatch(r"render-review-page: ✗ problem=未知参数或参数不合法「[^」]+」：%s cause=%s fix=%s"
                        % (re.escape(detail), re.escape(FIXED_USAGE_CAUSE), re.escape(FIXED_USAGE_FIX)),
                        stderr_lines(r)[0])


def test_usage_failure_puts_detail_in_problem_and_keeps_fixed_cause(module):
    # 「没有任何可用文档」走的 usage_failure：现有 preset 都含必有文档、--doc 全按必有处理，
    # 命令行到不了这条分支，只能直接调函数测文案。
    f = module.usage_failure("--doc", "没有任何可用文档")
    assert (f.code, f.problem, f.cause, f.fix) == (
        64, "未知参数或参数不合法「--doc」：没有任何可用文档", FIXED_USAGE_CAUSE, FIXED_USAGE_FIX)
