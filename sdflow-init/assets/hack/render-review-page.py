#!/usr/bin/env python3
"""render-review-page.py — 把一组 Markdown 生成一页自包含的评审 HTML（RVP-01/02/03）。

用法：
  render-review-page.py --out <页面.html> --title "<标题>" --doc "<标签>=<md 路径>" [--doc ...] [--event "<说明>"] [--no-open]
  render-review-page.py --preset design-gate|shipped|roadmap-review|code-review --dir <目录> [--out ...] [--title ...] [--event ...] [--no-open]

只做机械活：读 md 原文、读页面同目录 review-notes.md 里本页自产的意见块与处置块、维护页面旁的
修改日志 <页名>.revisions.json、套模板、算 CSP 哈希、写出文件。Markdown 由页面里内联的 marked 渲染，
本脚本不解析 Markdown。

时间只出现在修改日志里：内容（各文档原文、已嵌入意见、已嵌入处置）有变化才追加一条，该条时间取
SOURCE_DATE_EPOCH（未设或非法时取当前时间），带本地时区偏移；页面显示最后一条的时间。
内容无变化时不追加，同样输入（同一时区）重复生成逐字节相同，不依赖 SOURCE_DATE_EPOCH。
先写日志、再写页面，均原子替换；日志写入失败时页面不动。

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
from datetime import datetime, timezone
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


def emit(problem, cause, fix, prog=None):
    """prog 供 record-review-disposition.py 复用本函数，失败行前缀用它自己的程序名。"""
    print("%s: ✗ problem=%s cause=%s fix=%s" % (prog or PROG, problem, cause, fix), file=sys.stderr)


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
    p.add_argument("--event", help="本次生成写进修改日志的事件说明；缺省首条为「首次生成」，其后为「重新生成」")
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


def repo_relative(path, root):
    """仓库相对路径（POSIX 写法）；不在仓内或不在仓库里时返回 None。"""
    absolute = Path(os.path.abspath(path))
    # 仓根取真实路径与原样各试一次：原文路径可能经符号链接给出，也可能不经。
    bases = [] if root is None else [Path(os.path.realpath(root)), Path(root)]
    for base in bases:
        try:
            return absolute.relative_to(base).as_posix()
        except ValueError:
            continue
    return None


def display_path(path, root, out_dir):
    """页面里显示的路径：优先仓库相对；不在仓内则相对 --out 所在目录。"""
    inside = repo_relative(path, root)
    if inside is not None:
        return inside
    absolute = Path(os.path.abspath(path))
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


ACTIONS = ("采纳", "部分采纳", "不采纳", "转 issue")
TRANSFER = ACTIONS[3]  # 「转 issue」：record-review-disposition.py 复用，不得另写一份


def clean_disposition(raw, at):
    """校验并规整一条处置；不合格返回 None。detail、issue 缺省按空处理，在场则须为字符串。

    严格校验（detail 非空、拒未知字段）在 record-review-disposition.py。
    这里是读取侧，故意宽松：只丢弃无法使用的条目。
    """
    if not isinstance(raw, dict):
        return None
    ident, action = raw.get("id"), raw.get("action")
    if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
        return None
    if not isinstance(action, str) or action not in ACTIONS:
        return None
    out = {"id": ident, "action": action, "at": at}
    for key in ("detail", "issue"):
        value = raw.get(key, "")
        if not isinstance(value, str):
            return None
        out[key] = clean_text(value)
    return out


def read_saved_blocks(notes_path, page_name):
    """读 review-notes.md，返回 (意见列表, 处置表)，都只含本页（page 文件名等于 page_name）的内容。

    只认三行形态的块：开围栏（3 个以上反引号加 json）、一行以 { 开头的 JSON、同长闭围栏；
    其余行当普通文本。含 notes 列表的块是意见块；kind 为 disposition 且含 dispositions 列表的块是处置块。
    意见同 id 取最后一次，位置按首次出现。处置按意见 id 关联、同 id 取最后一次，处置表按意见顺序
    给出 {id: {action, detail, issue, at}}；对不上任何已落盘意见的处置忽略并在 stderr 汇总条数。
    不合格的块或条目跳过并在 stderr 汇总一行。文件不存在返回空；读失败告警并返回空。
    """
    try:
        # utf-8-sig：去掉文件开头的 BOM，否则第一个块的开围栏行带 BOM 而匹配不上
        text = Path(notes_path).read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        return [], {}
    except (OSError, UnicodeDecodeError) as exc:
        warn("无法读取 %s" % notes_path,
             "%s: %s" % (type(exc).__name__, one_line(exc)),
             "检查文件权限与编码（应为 UTF-8）；本次页面不含已落盘意见")
        return [], {}

    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]
    notes = {}          # 保持首次出现顺序；同键后写覆盖值但不换位置
    dispositions = {}   # 意见 id → 最后一次处置
    skipped = set()     # 无法解析的块（整块或其中有条目被跳过）开围栏的 1 基行号
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
        if not (isinstance(data, dict) and isinstance(data.get("page"), str)):
            skipped.add(block_line)
            continue
        is_notes = isinstance(data.get("notes"), list)
        is_dispositions = (not is_notes and data.get("kind") == "disposition"
                           and isinstance(data.get("dispositions"), list))
        if not (is_notes or is_dispositions):
            skipped.add(block_line)
            continue
        if clean_text(data["page"]).rsplit("/", 1)[-1] != page_name:
            continue
        stamp_key = "copied_at" if is_notes else "at"
        stamp = data.get(stamp_key, "")
        stamp = clean_text(stamp) if isinstance(stamp, str) else ""
        if is_notes:
            for raw in data["notes"]:
                note = clean_note(raw, stamp)
                if note is None:
                    skipped.add(block_line)
                    continue
                notes[note_key(note)] = note
        else:
            for raw in data["dispositions"]:
                item = clean_disposition(raw, stamp)
                if item is None:
                    skipped.add(block_line)
                    continue
                dispositions[item["id"]] = item

    if skipped:
        where = "、".join(str(n) for n in sorted(skipped))
        warn("已跳过 %d 个无法解析的意见块（第 %s 行）" % (len(skipped), where),
             "review-notes.md 中的 json 块被改写或不是评审页产出的格式",
             "对照评审页「复制意见」的原文修正该块，或忽略（不影响生成）")

    note_list = list(notes.values())
    matched = {}
    for note in note_list:
        item = dispositions.get(note["id"]) if note["id"] else None
        if item is not None:
            matched[note["id"]] = {k: item[k] for k in ("action", "detail", "issue", "at")}
    unmatched = len(dispositions) - len(matched)
    if unmatched:
        warn("已忽略 %d 条对不上已落盘意见的处置" % unmatched,
             "处置的意见 ID 不属于本页已落盘的意见（意见被删，或处置记在了别的页）",
             "确认 review-notes.md 中该处置块的 page 与 id；不影响生成")
    return note_list, matched


def read_saved_notes(notes_path, page_name):
    """本页已落盘意见列表；处置块的读取与告警同 read_saved_blocks。"""
    return read_saved_blocks(notes_path, page_name)[0]


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


# ── 生成时间与修改日志 ───────────────────────────────────────────────────────

EPOCH_RE = re.compile(r"[0-9]+")  # [0-9] 只匹配 ASCII 数字；int() 自己还接受全角数字、下划线与空白
REVISIONS_V = 1


def revision_time():
    """一条新日志的时间：SOURCE_DATE_EPOCH 合法时取它，否则取当前时间；带本地时区偏移的 ISO-8601。"""
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is not None:
        if EPOCH_RE.fullmatch(raw):
            try:
                stamp = datetime.fromtimestamp(int(raw), timezone.utc).astimezone()
                return stamp.isoformat(timespec="seconds")
            except (OverflowError, OSError, ValueError):
                pass
        warn("SOURCE_DATE_EPOCH 不合法：%s" % one_line(raw)[:40],
             "须为纯 ASCII 十进制整数秒，且在可表示的日期范围内",
             "改正或取消该环境变量；本次改用当前时间")
    return datetime.now().astimezone().isoformat(timespec="seconds")


def revisions_path(out):
    """页面 review/<页名>.html 对应的修改日志 review/<页名>.revisions.json。"""
    return out.with_name(out.stem + ".revisions.json")


def empty_revisions(page_name):
    return {"v": REVISIONS_V, "page": page_name, "revisions": []}


def valid_revisions(data, page_name):
    if not (isinstance(data, dict) and data.get("v") == REVISIONS_V and data.get("page") == page_name
            and isinstance(data.get("revisions"), list)):
        return False
    for rev in data["revisions"]:
        if not (isinstance(rev, dict) and isinstance(rev.get("n"), int) and isinstance(rev.get("at"), str)
                and isinstance(rev.get("event"), str) and isinstance(rev.get("docs"), dict)):
            return False
    return True


def load_revisions(path, page_name):
    """读修改日志，返回 (日志, 损坏时的原始字节或 None)。不存在返回空日志；
    损坏（非 JSON、形状不对、page 不是本页）按空日志重建，并把原字节交给调用方，
    由调用方在新日志写成功前留 .bak。读不了（权限等）按写入失败处理。"""
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return empty_revisions(page_name), None
    except OSError as exc:
        raise Failure(EXIT_FAIL, "无法读取修改日志 %s" % path, one_line(exc), "检查文件权限后重跑")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        data = None
    if valid_revisions(data, page_name):
        return data, None
    return empty_revisions(page_name), raw


def doc_records(docs, entries, root):
    """{标签: {path, sha256}}：path 是仓库相对路径（仓外为 None），sha256 对文件原始字节计算。

    docs 的 text 由 UTF-8 严格解码得来，编码回去与原始字节逐字节相同（BOM、换行都保留）。
    """
    paths = {label: path for label, path, _ in entries}
    return {d["label"]: {"path": repo_relative(paths[d["label"]], root),
                         "sha256": hashlib.sha256(d["text"].encode("utf-8")).hexdigest()}
            for d in docs}


def fingerprint(records, saved_notes, dispositions):
    """内容指纹：各文档原文哈希 + 已嵌入意见 + 已嵌入处置。事件说明、时间、版本号都不进。"""
    payload = {"docs": {label: rec["sha256"] for label, rec in records.items()},
               "notes": saved_notes, "dispositions": dispositions}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def changed_labels(records, previous):
    """相对上一条日志：哈希不同或新增的文档（按本次顺序），其后是消失的文档。"""
    before = previous.get("docs") if isinstance(previous, dict) else None
    if not isinstance(before, dict):
        before = {}

    def sha_of(rec):
        return rec.get("sha256") if isinstance(rec, dict) else None

    changed = [label for label, rec in records.items()
               if label not in before or sha_of(before[label]) != rec["sha256"]]
    changed += [label for label in before if label not in records]
    return changed


def next_revisions(log, records, saved_notes, dispositions, event):
    """返回 (新日志, 是否追加)。指纹与最后一条相同则原样返回。"""
    revs = log["revisions"]
    fp = fingerprint(records, saved_notes, dispositions)
    if revs and revs[-1].get("fp") == fp:
        return log, False
    first = not revs
    entry = {"n": len(revs) + 1, "at": revision_time(),
             "event": event or ("首次生成" if first else "重新生成"),
             "docs": records, "notes": len(saved_notes), "dispositions": len(dispositions),
             "changed": [] if first else changed_labels(records, revs[-1]),
             # fp 是生成器判「内容是否变化」的内部字段，模板不读它。
             "fp": fp}
    return dict(log, revisions=revs + [entry]), True


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


def render(template, marked, title, docs, saved_notes, dispositions, revisions):
    m = APP_SCRIPT_RE.search(template)
    if not m:
        raise Failure(EXIT_FAIL, "评审页资产缺失：模板缺少 sdflow-app 脚本块", "模板文件损坏或版本不匹配",
                      "在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh")
    values = {
        "TITLE": html.escape(title, quote=True),
        "DOCS_JSON": json_for_script(docs),
        "SAVED_NOTES_JSON": json_for_script(saved_notes),
        "DISPOSITIONS_JSON": json_for_script(dispositions),
        "REVISIONS_JSON": json_for_script(revisions),
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
        # mkstemp 建的文件是 0600；沿用原文件 mode，无原文件时按 umask 取默认，共享目录里别的账号才读写得了。
        try:
            mode = os.stat(str(out)).st_mode & 0o777
        except FileNotFoundError:
            # 新文件与普通创建一致取 0o666 & ~umask，不写死 mode
            um = os.umask(0)
            os.umask(um)
            mode = 0o666 & ~um
        os.chmod(tmp, mode)
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
    # git 子进程只起一次，结果同时给 read_docs 与 doc_records。
    root = repo_root_or_none()
    docs, failures = read_docs(entries, root, out.parent)
    if failures:
        for f in failures:
            emit(f.problem, f.cause, f.fix)
        return EXIT_FAIL
    if not docs:
        raise usage_failure("--doc", "没有任何可用文档")

    saved_notes, dispositions = read_saved_blocks(out.parent / NOTES_FILENAME, out.name)
    for item in saved_notes:
        item["line"] = locate_line(item, docs)

    log_file = revisions_path(out)
    log, corrupt_raw = load_revisions(log_file, out.name)
    revisions, appended = next_revisions(log,
                                         doc_records(docs, entries, root),
                                         saved_notes, dispositions, args.event)
    template, marked = load_assets()
    try:
        page = render(template, marked, title, docs, saved_notes, dispositions,
                      revisions).encode("utf-8")
        log_bytes = (json.dumps(revisions, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Failure(EXIT_FAIL, "页面无法编码为 UTF-8", one_line(exc),
                      "检查 --title 或原文里是否含无法编码的字符后重跑")
    # 先日志后页面：日志写失败时页面不动；页面写失败时日志已含本次条目，重跑指纹相同、只重写页面。
    if appended:
        if corrupt_raw is not None:
            # 损坏日志先复制为 .bak 再写新日志：任一步失败，原日志文件都不被改名或删除。
            bak = log_file.with_name(log_file.name + ".bak")
            write_atomic(bak, corrupt_raw)
            warn("修改日志损坏，已重建：%s" % log_file.name,
                 "文件不是合法的修改日志，或记的页面不是 %s" % out.name,
                 "原内容保留为 %s；需要旧记录时从中取回" % bak.name)
        write_atomic(log_file, log_bytes)
    write_atomic(out, page)

    print("评审页：%s" % out)
    if appended:
        print("已追加修改日志：第 %d 版（%s）" % (revisions["revisions"][-1]["n"],
                                           revisions["revisions"][-1]["event"]))
    else:
        print("内容无变化，未追加修改日志")
    if saved_notes:
        missing = sum(1 for item in saved_notes if item["line"] is None)
        print("已嵌入 %d 条已落盘意见（%d 条未找到行号）" % (len(saved_notes), missing))
    if dispositions:
        print("已嵌入 %d 条处置" % len(dispositions))
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
