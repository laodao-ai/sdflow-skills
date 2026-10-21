#!/usr/bin/env python3
"""render-review-page.py — 把一组 Markdown 生成一页自包含的评审 HTML（RVP-01/02/03）。

用法：
  render-review-page.py --out <页面.html> --title "<标题>" --doc "<标签>=<md 路径>" [--doc ...] [--no-open]
  render-review-page.py --preset design-gate|shipped|roadmap-review|code-review --dir <目录> [--out ...] [--title ...] [--no-open]

只做机械活：读 md 原文、读页面同目录 review-notes.md 里本页自产的意见块、套模板、算 CSP 哈希、
写出文件。Markdown 由页面里内联的 marked 渲染，本脚本不解析 Markdown。
输出不含时间戳，同样输入逐字节相同。

退出码：0 成功 | 2 原文/模板/渲染库缺失或写入失败 | 64 用法错误。
stderr 每条一行，两种前缀：
  render-review-page: ✗ problem=… cause=… fix=…   失败，随非 0 退出码
  render-review-page: ⚠ problem=… cause=… fix=…   告警（可选原文已跳过、意见块被跳过、
                                                  notes 读失败、设计门缺 specs），不改变退出码
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

import argparse
import base64
import hashlib
import html
import json
import os
import re
import subprocess
import tempfile
import webbrowser
from pathlib import Path

PROG = "render-review-page"
EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 2, 64
ASSET_DIR = Path(__file__).resolve().parent / "review-page"

# 节点预设：(默认页面文件名, 默认标题前缀)。
# 文档清单（标签、路径、必有?）由 preset_docs() 按 preset 展开；
# design-gate 的 spec 清单是 specs/*/spec.md 按路径排序。
PRESETS = {
    "design-gate": ("design-gate.html", "设计门评审"),
    "shipped": ("shipped.html", "收尾评审"),
    "roadmap-review": ("roadmap-review.html", "roadmap 评审"),
    "code-review": ("code-review.html", "代码审评审"),
}


class Failure(Exception):
    def __init__(self, code, problem, cause, fix):
        super().__init__(problem)
        self.code, self.problem, self.cause, self.fix = code, problem, cause, fix


def emit(problem, cause, fix):
    print("%s: ✗ problem=%s cause=%s fix=%s" % (PROG, problem, cause, fix), file=sys.stderr)


def warn(problem, cause, fix):
    print("%s: ⚠ problem=%s cause=%s fix=%s" % (PROG, problem, cause, fix), file=sys.stderr)


def one_line(text):
    return " ".join(str(text).split())


USAGE_CAUSE = "参数写错，或脚本版本旧于调用它的 SKILL"


def usage_failure(arg, detail=None):
    """原因文案固定；具体是哪里不对写进 problem。"""
    problem = "未知参数或参数不合法「%s」" % one_line(arg)
    if detail:
        problem += "：%s" % one_line(detail)
    return Failure(EXIT_USAGE, problem, USAGE_CAUSE, "按 --help 修正，或跑 bash setup.sh")


class Parser(argparse.ArgumentParser):
    """argparse 默认用户错误退出码 2，与「原文缺失」冲突；改为抛 64。"""

    def error(self, message):
        raise usage_failure(message)


def build_parser():
    p = Parser(prog=PROG, description="把一组 Markdown 生成一页自包含评审 HTML")
    p.add_argument("--out", help="输出的 HTML 路径；用 --preset 时缺省为 <dir>/review/<节点页>.html")
    p.add_argument("--title", help="页面标题；用 --preset 时可缺省")
    p.add_argument("--doc", action="append", default=[], metavar="标签=路径",
                   help="文档，可重复；以第一个 = 切分标签与路径")
    p.add_argument("--preset", choices=sorted(PRESETS), help="按节点预设确定文档清单与顺序")
    p.add_argument("--dir", help="--preset 用的 change 或 roadmap 目录")
    p.add_argument("--no-open", action="store_true", help="不尝试打开浏览器（测试用）")
    return p


# ── 文档清单 ────────────────────────────────────────────────────────────────

def preset_docs(preset, base):
    """返回 [(标签, 路径, 必有?)]。"""
    base = Path(base)
    if preset == "design-gate":
        docs = [("spec-review-report", base / "spec-review-report.md", True),
                ("proposal", base / "proposal.md", True),
                ("design", base / "design.md", True)]
        specs = base / "specs"
        if specs.is_dir():
            for spec in sorted(specs.glob("*/spec.md"), key=lambda p: p.as_posix()):
                docs.append(("spec:%s" % spec.parent.name, spec, True))
        docs.append(("tasks", base / "tasks.md", True))
        docs.append(("decision-memo", base / "decision-memo.md", False))
        return docs
    if preset == "shipped":
        return [("hand-off", base / "hand-off.md", True),
                ("verify-report", base / "verify-report.md", True),
                ("code-review-report", base / "code-review-report.md", False)]
    if preset == "roadmap-review":
        return [("roadmap", base / "roadmap.md", True),
                ("design", base / "design.md", True),
                ("task-log", base / "task-log.md", False)]
    if preset == "code-review":
        return [("code-review-report", base / "code-review-report.md", True)]
    raise ValueError("未知 preset：%s" % preset)


def parse_doc_args(raw_docs):
    docs, seen = [], set()
    for raw in raw_docs:
        if "=" not in raw:
            raise usage_failure(raw, "--doc 必须写成 标签=路径")
        label, path = raw.split("=", 1)
        if not label or not path:
            raise usage_failure(raw, "--doc 的标签与路径都不能为空")
        if label in seen:
            raise usage_failure(raw, "标签重复：%s" % label)
        seen.add(label)
        docs.append((label, Path(path), True))
    return docs


def repo_root_or_none():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=10)
    except Exception:
        return None
    top = r.stdout.strip()
    return Path(top) if r.returncode == 0 and top else None


def display_path(path, root, out_dir):
    """页面里显示的路径：优先仓库相对；不在仓内则相对 --out 所在目录。"""
    absolute = Path(os.path.abspath(path))
    # 仓根取真实路径与原样各试一次：原文路径可能经符号链接给出，也可能不经。
    bases = [] if root is None else [Path(os.path.realpath(root)), Path(root)]
    for base in bases:
        try:
            return absolute.relative_to(base).as_posix()
        except ValueError:
            continue
    try:
        return Path(os.path.relpath(absolute, out_dir)).as_posix()
    except ValueError:  # Windows 跨盘符
        return absolute.as_posix()


def read_docs(entries, root, out_dir):
    """读每个 md 的原文。必有的缺失/不可读收集后一并报；可选的缺失跳过。"""
    docs, failures = [], []
    for label, path, required in entries:
        if not path.is_file():
            if required:
                failures.append(Failure(EXIT_FAIL, "原文不存在：%s" % path,
                                        "节点产物未生成或路径写错", "确认该文件已生成后重跑"))
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            if required:
                failures.append(Failure(EXIT_FAIL, "原文不可读：%s" % path, one_line(exc),
                                        "确认文件是可读的 UTF-8 文本后重跑"))
            else:
                # 可选文档读不出：页面照出但缺这一份，告警让人知道
                warn("可选原文已跳过：%s" % path, one_line(exc), "确认文件是可读的 UTF-8 文本后重跑")
            continue
        docs.append({"label": label, "path": display_path(path, root, out_dir), "text": text})
    return docs, failures


# ── 已落盘意见（review-notes.md） ───────────────────────────────────────────

NOTES_FILENAME = "review-notes.md"
FENCE_OPEN_RE = re.compile(r"(`{3,})json")
ID_RE = re.compile(r"[0-9a-f]{16}")
SURROGATE_RE = re.compile("[\ud800-\udfff]")
STR_FIELDS = ("id", "doc", "path", "heading", "before", "after")


def clean_text(value):
    """孤立代理项换成 U+FFFD，使结果一定能编码为 UTF-8。成对的代理项在 json.loads 时已合并。"""
    return SURROGATE_RE.sub("\ufffd", value)


def clean_note(raw, copied_at):
    """校验并规整一条意见；不合格返回 None。字段缺省按空处理，在场则须为规定类型。"""
    if not isinstance(raw, dict):
        return None
    if not isinstance(raw.get("quote"), str) or not isinstance(raw.get("comment"), str):
        return None
    out = {}
    for key in STR_FIELDS:
        value = raw.get(key, "")
        if not isinstance(value, str):
            return None
        out[key] = clean_text(value)
    n = raw.get("n", 0)
    if isinstance(n, bool) or not isinstance(n, int):
        return None
    out["n"] = n
    # 图内划选的意见（评审页据此标「未在正文高亮」）；旧块没有该字段按 False。
    in_figure = raw.get("inFigure", False)
    if not isinstance(in_figure, bool):
        return None
    out["inFigure"] = in_figure
    out["quote"] = clean_text(raw["quote"])
    out["comment"] = clean_text(raw["comment"])
    out["copied_at"] = copied_at
    if not ID_RE.fullmatch(out["id"]):
        out["id"] = ""
    return out


def note_key(note):
    if note["id"]:
        return ("id", note["id"])
    return ("text", note["doc"], note["quote"], note["comment"])


def read_saved_notes(notes_path, page_name):
    """读 review-notes.md，返回本页（page 文件名等于 page_name）自产的意见列表。

    只认三行形态的块：开围栏（3 个以上反引号加 json）、一行以 { 开头的 JSON、同长闭围栏；
    其余行当普通文本。同 id 取最后一次，位置按首次出现。不合格的块或意见跳过并在 stderr 汇总一行。
    文件不存在返回空；读失败告警并返回空。
    """
    try:
        # utf-8-sig：去掉文件开头的 BOM，否则第一个块的开围栏行带 BOM 而匹配不上
        text = Path(notes_path).read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as exc:
        warn("无法读取 %s" % notes_path,
             "%s: %s" % (type(exc).__name__, one_line(exc)),
             "检查文件权限与编码（应为 UTF-8）；本次页面不含已落盘意见")
        return []

    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]
    notes = {}          # 保持首次出现顺序；同键后写覆盖值但不换位置
    skipped = set()     # 无法解析的块（整块或其中有意见被跳过）开围栏的 1 基行号
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.fullmatch(lines[i])
        if not (m and i + 2 < len(lines) and lines[i + 1].startswith("{") and lines[i + 2] == m.group(1)):
            i += 1
            continue
        block_line = i + 1
        payload = lines[i + 1]
        i += 3
        try:
            data = json.loads(payload)
        except (ValueError, RecursionError):
            skipped.add(block_line)
            continue
        if not (isinstance(data, dict) and isinstance(data.get("page"), str)
                and isinstance(data.get("notes"), list)):
            skipped.add(block_line)
            continue
        if clean_text(data["page"]).rsplit("/", 1)[-1] != page_name:
            continue
        copied_at = data.get("copied_at", "")
        copied_at = clean_text(copied_at) if isinstance(copied_at, str) else ""
        for raw in data["notes"]:
            note = clean_note(raw, copied_at)
            if note is None:
                skipped.add(block_line)
                continue
            notes[note_key(note)] = note

    if skipped:
        where = "、".join(str(n) for n in sorted(skipped))
        warn("已跳过 %d 个无法解析的意见块（第 %s 行）" % (len(skipped), where),
             "review-notes.md 中的 json 块被改写或不是评审页产出的格式",
             "对照评审页「复制意见」的原文修正该块，或忽略（不影响生成）")
    return list(notes.values())


def locate_line(note, docs):
    """在本次已读入的文档里找意见原文的 1 基行号；找不到返回 None。不按 path 读磁盘。

    查找顺序：前文+原文+后文 → 前文+原文 → 原文在全篇唯一，与页面的 locateNote 一致。
    前两级只在对应的上下文非空时才用：上下文为空时它们退化成「取第一处」。
    """
    quote = note.get("quote", "")
    path = note.get("path", "")
    if not quote or not path:
        return None
    doc = next((d for d in docs if d["path"] == path), None)
    if doc is None:
        return None
    before, after, text = note.get("before", ""), note.get("after", ""), doc["text"]
    candidates = []
    if before or after:
        candidates.append(before + quote + after)
    if before:
        candidates.append(before + quote)
    for needle in candidates:
        idx = text.find(needle)
        if idx >= 0:
            return text.count("\n", 0, idx + len(before)) + 1
    idx = text.find(quote)
    # 唯一性按可重叠出现判（与页面一致）：「aa」在「aaa」里算出现两次。
    if idx >= 0 and text.find(quote, idx + 1) < 0:
        return text.count("\n", 0, idx) + 1
    return None


# ── 模板 ────────────────────────────────────────────────────────────────────

def load_assets():
    template = ASSET_DIR / "template.html"
    marked = ASSET_DIR / "marked.umd.js"
    texts = []
    for p in (template, marked):
        try:
            texts.append(p.read_bytes().decode("utf-8"))
        except (OSError, UnicodeDecodeError):
            raise Failure(EXIT_FAIL, "评审页资产缺失：%s" % p, "~/.sdflow/hack/ 未随本版安装",
                          "在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh")
    return texts[0], texts[1]


def sha256_b64(text):
    return base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")


def json_for_script(value):
    """JSON 嵌进 <script type=application/json>：< > & 与 U+2028/2029 全部写成 \\u 转义。"""
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for ch in ("<", ">", "&", "\u2028", "\u2029"):
        raw = raw.replace(ch, "\\u%04x" % ord(ch))
    return raw


APP_SCRIPT_RE = re.compile(r'<script id="sdflow-app">(.*?)</script>', re.S)
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


def render(template, marked, title, docs, saved_notes):
    m = APP_SCRIPT_RE.search(template)
    if not m:
        raise Failure(EXIT_FAIL, "评审页资产缺失：模板缺少 sdflow-app 脚本块", "模板文件损坏或版本不匹配",
                      "在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh")
    values = {
        "TITLE": html.escape(title, quote=True),
        "DOCS_JSON": json_for_script(docs),
        "SAVED_NOTES_JSON": json_for_script(saved_notes),
        "MARKED": marked,
        "HASH_MARKED": sha256_b64(marked),
        "HASH_APP": sha256_b64(m.group(1)),
    }
    # 单趟替换：替换值不会被再次扫描，原文里出现 {{TITLE}} 之类字样不会被替换。
    return PLACEHOLDER_RE.sub(lambda mo: values.get(mo.group(1), mo.group(0)), template)


# ── 写出与打开 ──────────────────────────────────────────────────────────────

def write_atomic(out, data):
    out_dir = out.parent
    tmp = None
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(out_dir), prefix=".render-review-", suffix=".tmp")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        # mkstemp 建的文件是 0600；页面是给人看的普通产物，权限按 umask 与新建文件一致。
        current_umask = os.umask(0)
        os.umask(current_umask)
        os.chmod(tmp, 0o666 & ~current_umask)
        os.replace(tmp, str(out))
        tmp = None
    except OSError as exc:
        raise Failure(EXIT_FAIL, "无法写出 %s" % out, one_line(exc), "检查目录权限与磁盘空间")
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def try_open(path):
    """返回是否已尝试打开。Linux 等无图形环境时不调 webbrowser（避免选中终端浏览器阻塞）。"""
    if sys.platform not in ("darwin", "win32") and not (
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        return bool(webbrowser.open(path.as_uri()))
    except Exception:
        return False


# ── 入口 ────────────────────────────────────────────────────────────────────

def run(argv):
    args = build_parser().parse_args(argv)

    if args.preset:
        if args.doc:
            raise usage_failure("--doc", "--preset 与 --doc 不能同时使用")
        if not args.dir:
            raise usage_failure("--dir", "--preset 需要 --dir")
        base = Path(args.dir)
        entries = preset_docs(args.preset, base)
        if args.preset == "design-gate" and not any((base / "specs").glob("*/spec.md")):
            warn("设计门页缺少 specs",
                 "%s/specs/ 下没有 */spec.md" % base.resolve().name,
                 "确认本 change 是否应有 delta spec；页面已照常生成")
        default_page, default_title = PRESETS[args.preset]
        out = Path(args.out) if args.out else base / "review" / default_page
        title = args.title or "%s · %s" % (default_title, base.resolve().name)
    else:
        if args.dir:
            raise usage_failure("--dir", "--dir 只与 --preset 一起使用")
        if not args.doc:
            raise usage_failure("--doc", "至少需要一个 --doc（或改用 --preset）")
        if not args.out:
            raise usage_failure("--out", "缺少 --out")
        if not args.title:
            raise usage_failure("--title", "未用 --preset 时必须给 --title")
        entries = parse_doc_args(args.doc)
        out = Path(args.out)
        title = args.title

    out = Path(os.path.abspath(out))
    docs, failures = read_docs(entries, repo_root_or_none(), out.parent)
    if failures:
        for f in failures:
            emit(f.problem, f.cause, f.fix)
        return EXIT_FAIL
    if not docs:
        raise usage_failure("--doc", "没有任何可用文档")

    saved_notes = read_saved_notes(out.parent / NOTES_FILENAME, out.name)
    for item in saved_notes:
        item["line"] = locate_line(item, docs)

    template, marked = load_assets()
    try:
        page = render(template, marked, title, docs, saved_notes).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Failure(EXIT_FAIL, "页面无法编码为 UTF-8", one_line(exc),
                      "检查 --title 或原文里是否含无法编码的字符后重跑")
    write_atomic(out, page)

    print("评审页：%s" % out)
    if saved_notes:
        missing = sum(1 for item in saved_notes if item["line"] is None)
        print("已嵌入 %d 条已落盘意见（%d 条未找到行号）" % (len(saved_notes), missing))
    if not args.no_open:
        if try_open(out):
            print("已尝试在浏览器打开")
        else:
            print("未能自动打开，请手动打开上面的路径")
    return EXIT_OK


def main(argv=None):
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except Failure as f:
        emit(f.problem, f.cause, f.fix)
        return f.code


if __name__ == "__main__":
    sys.exit(main())
