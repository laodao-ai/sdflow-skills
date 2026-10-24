#!/usr/bin/env python3
"""record-review-disposition.py — 把一批意见的处置追加进 review-notes.md（RVP-24）。

用法（路径与处置都经带引号定界符的 here-doc 从 stdin 传入，不进命令行）：
  python3 ~/.sdflow/hack/record-review-disposition.py --stdin <<'SDFLOW_DISPOSITION'
  openspec/changes/x/review/review-notes.md
  {"page":"design-gate.html","dispositions":[{"id":"9f2c4e1a0b7d3c55","action":"采纳","detail":"已改 design"}]}
  SDFLOW_DISPOSITION

stdin 第 1 行是 review-notes.md 的仓库相对路径，其余行是一个 JSON 对象：
  page          评审页文件名（如 design-gate.html）
  dispositions  [{id, action, detail[, issue]}, ...]
                action 取 采纳 / 部分采纳 / 不采纳 / 转 issue；转 issue 必带 issue 编号，其余类别不得带 issue。

校验：路径过 check-notes-path.py 同一判定；review-notes.md 必须已存在；每个 id 都属于该页已落盘的意见
（由 render-review-page.py 的 read_saved_blocks 读出）；同批 id 不重复。任一项不通过则不写任何内容。
通过后追加一个 {"v":1,"kind":"disposition",...} 块；原文件末尾无换行时先补一个换行；
读原文 + 新块 → 临时文件 → 原子替换，原文件权限位原样保留。

退出码：0 已写入 | 1 校验不通过或写入失败 | 64 用法错误。
stderr 失败行：✗ problem=… cause=… fix=…
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

import contextlib
import importlib.util
import io
import json
import os
import stat
import tempfile
from pathlib import Path

PROG = "record-review-disposition"
EXIT_OK, EXIT_REJECT, EXIT_USAGE = 0, 1, 64
HERE = Path(__file__).resolve().parent
ITEM_KEYS = {"id", "action", "detail", "issue"}
_renderer = None


def get_renderer():
    """加载同目录的渲染器并缓存；失败抛 OSError/ImportError/SyntaxError。"""
    global _renderer
    if _renderer is None:
        _renderer = load_sibling("render-review-page.py", "sdflow_render_review_page")
    return _renderer


def fail(problem, cause, fix, code=EXIT_REJECT):
    problem, cause, fix = (" ".join(str(x).split()) for x in (problem, cause, fix))
    try:
        get_renderer().emit(problem, cause, fix, prog=PROG)
    except (OSError, ImportError, SyntaxError):
        # 渲染器加载不上时（装机不全）才走到这里；格式与 emit 相同。
        print("%s: ✗ problem=%s cause=%s fix=%s" % (PROG, problem, cause, fix), file=sys.stderr)
    return code


def load_sibling(filename, name):
    spec = importlib.util.spec_from_file_location(name, str(HERE / filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage():
    return fail("用法错误", "需要且只能给 --stdin 一个参数",
                "python3 ~/.sdflow/hack/record-review-disposition.py --stdin <<'SDFLOW_DISPOSITION'",
                EXIT_USAGE)


def parse_payload(raw):
    """stdin 全文 → (相对路径, 载荷 dict)；形状不对返回 (None, 错误原因)。"""
    first, _, rest = raw.partition("\n")
    path = first[:-1] if first.endswith("\r") else first
    if not path:
        return None, "stdin 第 1 行（review-notes.md 路径）为空"
    try:
        payload = json.loads(rest)
    except (ValueError, RecursionError) as exc:
        return None, "第 2 行起不是合法 JSON：%s" % exc
    if not isinstance(payload, dict):
        return None, "JSON 顶层必须是对象"
    if not isinstance(payload.get("page"), str) or not payload["page"]:
        return None, "缺少 page（评审页文件名）"
    if not isinstance(payload.get("dispositions"), list) or not payload["dispositions"]:
        return None, "dispositions 必须是非空数组"
    return path, payload


def check_items(items, legal_ids, actions):
    """返回 (规整后的处置列表, 问题列表)。问题全部收集，一次报全。"""
    problems, clean, seen, unknown = [], [], set(), []
    for pos, item in enumerate(items, 1):
        label = "第 %d 条" % pos
        if not isinstance(item, dict):
            problems.append("%s不是对象" % label)
            continue
        extra = sorted(set(item) - ITEM_KEYS)
        if extra:
            problems.append("%s含未知字段 %s" % (label, "、".join(extra)))
        ident = item.get("id")
        if not isinstance(ident, str):
            problems.append("%s缺少 id" % label)
        elif ident in seen:
            problems.append("%s的 id %s 在同批中重复" % (label, ident))
        elif ident not in legal_ids:
            unknown.append(ident)
        if isinstance(ident, str):
            seen.add(ident)
        action = item.get("action")
        if action not in actions:
            problems.append("%s的类别 %r 不在 %s 内" % (label, action, "/".join(actions)))
        detail = item.get("detail")
        if not isinstance(detail, str) or not detail.strip():
            problems.append("%s缺少一句说明（detail）" % label)
        if action == get_renderer().TRANSFER:
            issue = item.get("issue")
            if not isinstance(issue, str) or not issue.strip():
                problems.append("%s类别为「转 issue」但没有 issue 编号" % label)
        elif "issue" in item:
            problems.append("%s类别为「%s」，不得带 issue 编号" % (label, action))
        # 只要有任何问题调用方就不写，所以这里不必区分本条是否合格。
        entry = {"id": ident, "action": action, "detail": detail}
        if action == get_renderer().TRANSFER:
            entry["issue"] = item.get("issue")
        clean.append(entry)
    if unknown:
        problems.insert(0, "意见 ID 不属于该页已落盘的意见：%s" % "、".join(unknown))
    return clean, problems


def append_block(target, block_text):
    """原文 + 补换行 + 新块 → 同目录临时文件 → 原子替换；任一步失败不改原文件。"""
    original = Path(target).read_bytes()
    mode = stat.S_IMODE(os.stat(target).st_mode)
    data = original
    if data and not data.endswith(b"\n"):
        data += b"\n"
    data += block_text.encode("utf-8")
    directory = os.path.dirname(target)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".record-disposition-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        # mkstemp 建的文件是 0600；原文件的权限位原样带过去，共享目录里别人才读得了。
        os.chmod(tmp, mode)
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def run(argv):
    if argv != ["--stdin"]:
        return usage()
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    except OSError:
        return usage()
    rel_path, payload = parse_payload(raw)
    if rel_path is None:
        return fail("处置输入格式不对", payload,
                    "第 1 行写 review-notes.md 路径，第 2 行起写 {\"page\":…,\"dispositions\":[…]}")

    try:
        checker = load_sibling("check-notes-path.py", "sdflow_check_notes_path")
        renderer = get_renderer()
    except (OSError, ImportError, SyntaxError) as exc:
        return fail("缺少同目录脚本", "%s: %s" % (type(exc).__name__, exc),
                    "在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh")

    # check() 不通过时自己已向 stderr 打了 ✗ problem= 行
    code, target = checker.check(rel_path)
    if code != 0:
        return EXIT_REJECT
    if not os.path.isfile(target):
        return fail("review-notes.md 不存在", "%s 尚无已落盘意见，没有可处置的意见 ID" % rel_path,
                    "先把意见追加进 review-notes.md，再记录处置")

    # [impl-review-fix] C2: 先自己读一次；非 UTF-8 / 读失败要如实报，不能落成下面「意见 ID 不属于该页」
    try:
        with open(target, "r", encoding="utf-8-sig") as fh:
            fh.read()
    except (UnicodeDecodeError, OSError) as exc:
        return fail("review-notes.md 无法读取", "%s: %s" % (type(exc).__name__, exc),
                    "把 %s 改回 UTF-8 编码或修正读权限后重跑" % rel_path)

    page_name = payload["page"].rsplit("/", 1)[-1]
    # read_saved_blocks 对坏块与对不上的处置会自行告警；这里只要合法 ID，告警属于生成时的事。
    with contextlib.redirect_stderr(io.StringIO()):
        notes, _ = renderer.read_saved_blocks(Path(target), page_name)
    legal_ids = {n["id"] for n in notes if n["id"]}
    clean, problems = check_items(payload["dispositions"], legal_ids, renderer.ACTIONS)
    if problems:
        legal = "、".join(sorted(legal_ids)) if legal_ids else "（该页没有带 ID 的已落盘意见）"
        return fail("处置不能写入", "；".join(problems),
                    "改正后重跑；%s 的合法意见 ID：%s" % (page_name, legal))

    block = {"v": 1, "kind": "disposition", "page": payload["page"], "at": renderer.revision_time(),
             "dispositions": [{k: renderer.clean_text(v) for k, v in item.items()} for item in clean]}
    # 围栏取 3 个反引号：JSON 是单行，不可能等于围栏行，说明里含反引号也不会提前闭合。
    text = "```json\n%s\n```\n" % json.dumps(block, ensure_ascii=False, separators=(",", ":"))
    try:
        append_block(target, text)
    except OSError as exc:
        return fail("写入失败", "%s: %s" % (type(exc).__name__, exc), "检查 %s 的权限与磁盘空间后重跑" % rel_path)
    print("已记录 %d 条处置：%s" % (len(clean), rel_path))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
