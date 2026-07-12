#!/usr/bin/env python3
"""sad_scaffold.py — SAD 脚手架：init / preflight 两级 / 原子写 / 单例分流 / log 追加（DEC-8）；
状态机（transition/set-fact/set-assumption，Task 4）。

CLI: sad_scaffold.py <sub> --root <消费仓根> …
exit 码约定：0=ok / 2=坏输入 / 3=preflight无openspec布局 / 4=单例冲突 / 5=迁移拒绝（表外迁移/前置复检未过）

argparse subparsers 结构：main() 的 dispatch 按子命令名查表，新增子命令（adr-new/
context-add，Task 5）只需新增一个 _cmd_xxx(args) 函数 + 一个 add_parser 注册，
不需要改动既有子命令的实现或 dispatch 逻辑。
"""
import argparse
import pathlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sad_schema  # noqa: E402  (共享解析源，DEC-1；本脚本只写模版骨架，不重实现解析)

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "references" / "sad-template.md"

SAD_LOG_HEADER = "# sad-log（append-only 判定留痕）\n"
CONTEXT_STUB = "# Context\n\n## Language\n"

# ---- Task 5: scaffold 分家（adr-new / context-add）常量 --------------------------------
ADR_NUM_RE = re.compile(r"^(\d{4})-")
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
LANGUAGE_HEADING = "## Language"


def _die(code, msg):
    print(f"[sad_scaffold] FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def atomic_write(path, text):
    """temp+rename 同目录（DEC-8）：中断只留 temp，不留半写正式文件。"""
    tmp = path.with_name(path.name + ".tmp-scaffold")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def append_log(root, line):
    """append-only：不读不改既有行，仅追加一行。"""
    logp = root / "openspec" / "architecture" / "sad-log.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(logp, "a", encoding="utf-8") as f:
        f.write(f"- {ts} | {line}\n")


def load_sad(root):
    path = root / sad_schema.SAD_REL_PATH
    if not path.is_file():
        _die(2, "sad.md 不存在——先跑 init 建骨架")
    return path, path.read_text(encoding="utf-8")


def preflight(root, out):
    """两级 preflight：level 1 无 openspec/ → fail-closed 拒绝并指引；
    level 2 openspec/ 存在但缺 adr/CONTEXT.md → 补齐并留痕（首次创建）。
    """
    if not (root / "openspec").is_dir():
        _die(
            3,
            "消费仓无 openspec/ 布局——先运行 /sdflow-init 铺设 OpenSpec 工作流"
            "（安装：bash ~/.skills/sdflow-skills/setup.sh，然后在消费仓会话执行 /sdflow-init；"
            "装完回来重跑本命令）。MUST NOT 自造半套布局。",
        )
    for rel, kind in (("openspec/adr", "dir"), ("openspec/CONTEXT.md", "file")):
        p = root / rel
        if not p.exists():
            out.append(f"首次创建 {rel}")
            if kind == "dir":
                p.mkdir(parents=True)
            else:
                atomic_write(p, CONTEXT_STUB)
    (root / "openspec" / "architecture").mkdir(exist_ok=True)


def _load_template():
    """读模版正文（is_file 前置校验留在 _cmd_init 开头，此处只做读取）。"""
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _cmd_init(args):
    if not TEMPLATE_PATH.is_file():
        _die(2, "skill 安装不完整：references/sad-template.md 缺失——重跑 bash setup.sh")

    root = Path(args.root).resolve()
    announcements = []
    preflight(root, announcements)
    for line in announcements:
        print(line)

    sad_path = root / sad_schema.SAD_REL_PATH
    if sad_path.exists():
        if args.on_exists is None:
            _die(
                4,
                "SAD 已存在：--on-exists continue（增量续写）或 replan"
                "（重规划，旧内容归 git 历史）。",
            )
        if args.on_exists == "continue":
            print("SAD 已存在，续跑：直接编辑 openspec/architecture/sad.md 增量续写")
            return 0
        # replan
        if not args.reason or not args.reason.strip():
            _die(2, "--on-exists replan 须提供非空 --reason")
        template_text = _load_template()
        atomic_write(sad_path, template_text)
        append_log(root, f"replan: {args.reason}")
        return 0

    # 全新
    template_text = _load_template()
    atomic_write(sad_path, template_text)
    log_path = root / sad_schema.LOG_REL_PATH
    atomic_write(log_path, SAD_LOG_HEADER)
    append_log(root, "init")
    return 0


def _cmd_log(args):
    root = Path(args.root).resolve()
    log_path = root / sad_schema.LOG_REL_PATH
    if not log_path.is_file():
        _die(2, "sad-log.md 不存在——先跑 init 建骨架再记留痕")
    append_log(root, args.line)
    return 0


# ---- Task 5: scaffold 分家机械化（adr-new / context-add，REQ-9）------------------------
# adr-new / context-add 合法运行在 sad init 尚未跑过的仓状态（preflight 只保证
# openspec/adr、openspec/CONTEXT.md 存在，不保证 sad.md/sad-log.md 已建）——
# ADR 分家、术语并入不该被「SAD 生命周期还没开始」阻塞。


def _maybe_log(root, line):
    """sad-log.md 缺失时 MUST NOT 静默跳过、也 MUST NOT die——显式提示 + 继续，exit 0。"""
    log_path = root / sad_schema.LOG_REL_PATH
    if log_path.is_file():
        append_log(root, line)
    else:
        print("提示：sad-log.md 不存在（尚未跑 sad_scaffold init）——本次跳过留痕，不影响本次操作")


def _cmd_adr_new(args):
    root = Path(args.root).resolve()
    announcements = []
    preflight(root, announcements)
    for line in announcements:
        print(line)

    if not SLUG_RE.fullmatch(args.slug):
        _die(2, f"--slug 须匹配 [a-z0-9][a-z0-9-]*（ascii kebab），得到 {args.slug!r}")

    adr_dir = root / "openspec" / "adr"

    if args.number is not None:
        if args.number < 0:
            _die(2, f"--number 须为非负整数，得到 {args.number}")
        number = args.number
    else:
        md_files = sorted(p for p in adr_dir.glob("*.md") if p.name != "README.md")
        max_n = 0
        for p in md_files:
            m = ADR_NUM_RE.match(p.name)
            if not m:
                _die(2, f"无法识别编号模式（{p.name}）——人工指定 --number 越过扫描")
            max_n = max(max_n, int(m.group(1)))
        number = max_n + 1

    nnnn = f"{number:04d}"
    target = adr_dir / f"{nnnn}-{args.slug}.md"

    # Fix 1: 检查同号 ADR 是否已被占用（同号双 ADR 破坏编号唯一引用）
    existing = [p.name for p in adr_dir.glob(f"{nnnn}-*.md") if p.name != target.name]
    if existing:
        _die(2, f"ADR 编号 {nnnn} 已被占用: {existing[0]}——同号双 ADR 破坏编号唯一引用")

    if target.exists():
        _die(2, f"目标 ADR 已存在：openspec/adr/{target.name}——MUST NOT 覆盖，"
                f"换 --number 或人工核对已有文件后处理")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    skeleton = (f"# ADR {nnnn}: {args.title}\n\n"
                f"- Status: Proposed\n- Date: {date}\n\n"
                f"## Context\n\n## Decision\n\n## Consequences\n")
    atomic_write(target, skeleton)
    print(str(target))
    _maybe_log(root, f"adr-new {nnnn}-{args.slug}")
    return 0


def _cmd_context_add(args):
    root = Path(args.root).resolve()
    announcements = []
    preflight(root, announcements)
    for line in announcements:
        print(line)

    ctx_path = root / "openspec" / "CONTEXT.md"
    text = ctx_path.read_text(encoding="utf-8")
    term_marker = f"**{args.term}**"

    # 行锚定 + fence-aware（复用 sad_schema.body_lines——DEC-1/DEC-2 同一套扫描核心，
    # 不为 CONTEXT.md 另写一份 ad hoc 扫描）。
    for ln, line in sad_schema.body_lines(text):
        if line.startswith(term_marker):
            _die(2, f"术语 {args.term!r} 已存在（CONTEXT.md:{ln}: {line.strip()}）——"
                    f"不覆盖，如需修订请人工编辑该行")

    lines = text.splitlines()
    entry_block = [""] + [f"{term_marker}:"] + args.definition.splitlines() + [""]
    lang_ln = next((ln for ln, l in sad_schema.body_lines(text) if l.strip() == LANGUAGE_HEADING), None)
    if lang_ln is None:
        new_lines = lines + ["", LANGUAGE_HEADING] + entry_block
    else:
        end_ln = next((ln for ln, l in sad_schema.body_lines(text)
                        if ln > lang_ln and l.startswith("## ")), None)
        idx = (end_ln - 1) if end_ln is not None else len(lines)
        # Fix 2: 检查插入点前是否已是空行，若是则不加前导空行（避免空行翻倍）
        if idx > 0 and lines[idx - 1].strip() == "":
            entry_block_to_insert = entry_block[1:]  # 去掉前导空行
        else:
            entry_block_to_insert = entry_block
        new_lines = lines[:idx] + entry_block_to_insert + lines[idx:]

    new_text = "\n".join(new_lines) + "\n"
    atomic_write(ctx_path, new_text)
    _maybe_log(root, f"context-add {args.term}")
    return 0


# ---- 状态机（Task 4）：迁移表 + 锁 draft 正文实扫复检 + facts/假设处置把手 -----------------

TRANSITIONS = {
    ("draft", "skeleton-ready"):    "precheck+insert_slice",
    ("skeleton-ready", "draft"):    "reason+remove_slice",
    ("skeleton-ready", "validated"): "dod+remove_slice",
    ("validated", "draft"):         "reason",
}


def _precheck_skeleton(fm, text, args, subsys):
    """draft→skeleton-ready 前置复检：facts 三键 + 假设对账走正文实扫（DEC-1 共用核心），
    MUST NOT 读 assumptions_open 缓存作门禁数据源——缓存只是回写产物，不是真相源。
    """
    missing = [k for k in sad_schema.FACT_KEYS if fm["facts"].get(k, "missing") != "answered"]
    if missing:
        _die(5, f"事实三问未齐（缺 {','.join(missing)}）——锁 draft（fail-closed）。"
                f"人实际作答后跑 set-fact 记录。")
    v = sad_schema.check_assumptions(text)            # 正文实扫，缓存 MUST NOT 参与门禁
    if v:
        _die(5, "假设对账未过：" + "; ".join(f"{c}({d})" for c, d in v))
    if not args.slice_file:
        _die(5, "缺 --slice-file（骨架切片建议内容，模型撰写、scaffold 机械插入）")
    if not pathlib.Path(args.slice_file).is_file():
        _die(2, f"slice 文件不存在: {args.slice_file}")
    pierce = [m.group(1) for l in pathlib.Path(args.slice_file).read_text(encoding="utf-8").splitlines()
              if (m := sad_schema.PIERCE_RE.match(l))]
    if len(pierce) != len(set(pierce)):
        _die(5, f"穿越点存在重复条目: {sorted(set(p for p in pierce if pierce.count(p) > 1))}")
    if set(pierce) != set(subsys):
        _die(5, f"穿越点集≠第5节子系统集：穿越点{sorted(set(pierce))} vs 子系统{sorted(set(subsys))}")


def _heading_ln(text, heading):
    """定位顶级标题所在原始行号（1-indexed，fence-aware——复用 sad_schema.body_lines）。"""
    return next((ln for ln, l in sad_schema.body_lines(text) if l.strip() == heading), None)


def insert_slice(text, slice_content):
    """在 APPENDIX_ANCHOR 标题行之前插入「## 骨架切片建议」+ 空行 + slice-file 内容；
    无附录节则插在文末。"""
    lines = text.splitlines()
    block = [sad_schema.SLICE_ANCHOR, ""] + slice_content.rstrip("\n").splitlines() + [""]
    ln = _heading_ln(text, sad_schema.APPENDIX_ANCHOR)
    if ln is None:
        new_lines = lines + block
    else:
        idx = ln - 1
        new_lines = lines[:idx] + block + lines[idx:]
    return "\n".join(new_lines) + "\n"


def remove_slice(text):
    """删除从 SLICE_ANCHOR 标题行起、至下一 `## ` 顶级标题行前（或 EOF）的整段。
    无该节则原样返回（幂等）。"""
    lines = text.splitlines()
    start_ln = _heading_ln(text, sad_schema.SLICE_ANCHOR)
    if start_ln is None:
        return text
    body = sad_schema.body_lines(text)
    end_ln = next((ln for ln, l in body if ln > start_ln and l.startswith("## ")), None)
    start_idx = start_ln - 1
    end_idx = (end_ln - 1) if end_ln is not None else len(lines)
    new_lines = lines[:start_idx] + lines[end_idx:]
    return "\n".join(new_lines) + "\n"


def _frontmatter_end(lines):
    return next(i for i in range(1, len(lines)) if lines[i].strip() == "---")


def _rewrite_top_key(text, prefix, new_line):
    """重写 frontmatter 中以 prefix 开头的顶层键行（sad_status: / assumptions_open:）。"""
    lines = text.splitlines()
    end = _frontmatter_end(lines)
    for i in range(1, end):
        if lines[i].startswith(prefix):
            lines[i] = new_line
            break
    return "\n".join(lines) + "\n"


def _rewrite_status(text, to):
    return _rewrite_top_key(text, "sad_status:", f"sad_status: {to}")


def _recompute_assumptions_cache(text):
    """回写 assumptions_open = 附录表中处置为「未处置」的行数（每次写命令后必做）。"""
    _, rows = sad_schema.scan_assumptions(text)
    open_count = sum(1 for _, d in rows if d == "未处置")
    return _rewrite_top_key(text, "assumptions_open:", f"assumptions_open: {open_count}")


def _rewrite_facts_line(text, key, value):
    lines = text.splitlines()
    end = _frontmatter_end(lines)
    for i in range(1, end):
        if lines[i].startswith("  ") and lines[i].strip().split(":", 1)[0].strip() == key:
            lines[i] = f"  {key}: {value}"
            return "\n".join(lines) + "\n"
    _die(2, f"frontmatter facts 缺子键 {key}——sad.md 结构损坏")


def _rewrite_appendix_row(line, new_disposition):
    m = sad_schema.APPENDIX_ROW_RE.match(line)
    start, end = m.span(2)
    return line[:start] + new_disposition + line[end:]


def _cmd_transition(args):
    root = Path(args.root).resolve()
    path, text = load_sad(root)
    try:
        fm = sad_schema.parse_frontmatter(text)
    except sad_schema.SadParseError as e:
        _die(2, str(e))

    cur, to = fm["sad_status"], args.to
    if (cur, to) not in TRANSITIONS:
        _die(5, f"表外迁移 {cur}→{to}——合法迁移表见 design 状态机节")
    tokens = TRANSITIONS[(cur, to)].split("+")

    if "precheck" in tokens:
        subsys = sad_schema.scan_subsystems(text)
        _precheck_skeleton(fm, text, args, subsys)
    if "reason" in tokens and (not args.reason or not args.reason.strip()):
        _die(2, "该回落迁移须提供非空 --reason")
    if "dod" in tokens and not args.dod_confirmed:
        _die(2, "skeleton-ready→validated 须提供 --dod-confirmed")

    new_text = text
    if "insert_slice" in tokens:
        slice_content = pathlib.Path(args.slice_file).read_text(encoding="utf-8")
        new_text = insert_slice(new_text, slice_content)
    if "remove_slice" in tokens:
        new_text = remove_slice(new_text)
    new_text = _rewrite_status(new_text, to)
    new_text = _recompute_assumptions_cache(new_text)
    atomic_write(path, new_text)

    if "precheck" in tokens:
        log_line = f"transition {cur}→{to}"
    elif "dod" in tokens:
        log_line = f"{to}：骨架 DoD 已确认"
    else:
        log_line = f"fallback {cur}→{to}: {args.reason}"
    append_log(root, log_line)
    return 0


def _cmd_set_fact(args):
    root = Path(args.root).resolve()
    path, text = load_sad(root)
    try:
        sad_schema.parse_frontmatter(text)
    except sad_schema.SadParseError as e:
        _die(2, str(e))

    k, sep, v = args.fact.partition("=")
    k, v = k.strip(), v.strip()
    if not sep or k not in sad_schema.FACT_KEYS or v not in sad_schema.FACT_VALUES:
        _die(2, f"--fact 须为 <key>=<value>，key∈{sad_schema.FACT_KEYS}，"
                f"value∈{sad_schema.FACT_VALUES}，得到 {args.fact!r}")

    new_text = _rewrite_facts_line(text, k, v)
    new_text = _recompute_assumptions_cache(new_text)
    atomic_write(path, new_text)
    append_log(root, f"set-fact {k}={v}")
    return 0


def _cmd_set_assumption(args):
    root = Path(args.root).resolve()
    path, text = load_sad(root)
    try:
        sad_schema.parse_frontmatter(text)
    except sad_schema.SadParseError as e:
        _die(2, str(e))

    raw_n, sep, d = args.assumption.partition("=")
    if not sep or not raw_n.strip().isdigit():
        _die(2, f"--assumption 须为 <N>=<接受|待校准>，得到 {args.assumption!r}")
    n, d = int(raw_n.strip()), d.strip()
    if d not in ("接受", "待校准"):
        _die(2, f"处置须∈(接受, 待校准)——「未处置」不可经本把手写入，得到 {d!r}")

    lines = text.splitlines()
    found = False
    for i, line in enumerate(lines):
        m = sad_schema.APPENDIX_ROW_RE.match(line)
        if m and int(m.group(1)) == n:
            lines[i] = _rewrite_appendix_row(line, d)
            found = True
            break
    if not found:
        _die(2, f"假设-{n} 行不存在于附录表——先补行再处置")

    new_text = "\n".join(lines) + "\n"
    new_text = _recompute_assumptions_cache(new_text)
    atomic_write(path, new_text)
    append_log(root, f"set-assumption 假设-{n}={d}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="sad_scaffold.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="preflight + 建 sad.md/sad-log.md（单例分流）")
    p_init.add_argument("--root", required=True)
    p_init.add_argument("--on-exists", choices=("continue", "replan"), default=None)
    p_init.add_argument("--reason", default=None)
    p_init.set_defaults(func=_cmd_init)

    p_log = sub.add_parser("log", help="append_log 直通（SKILL 判定留痕）")
    p_log.add_argument("--root", required=True)
    p_log.add_argument("--line", required=True)
    p_log.set_defaults(func=_cmd_log)

    p_transition = sub.add_parser("transition", help="迁移表驱动的状态迁移 + 锁 draft 正文实扫复检")
    p_transition.add_argument("--root", required=True)
    p_transition.add_argument("--to", required=True, choices=sad_schema.STATUS_ENUM)
    p_transition.add_argument("--reason", default=None)
    p_transition.add_argument("--slice-file", default=None)
    p_transition.add_argument("--dod-confirmed", action="store_true")
    p_transition.set_defaults(func=_cmd_transition)

    p_set_fact = sub.add_parser("set-fact", help="记录 facts 三问之一的问答状态")
    p_set_fact.add_argument("--root", required=True)
    p_set_fact.add_argument("--fact", required=True, help="<key>=<answered|missing>")
    p_set_fact.set_defaults(func=_cmd_set_fact)

    p_set_assumption = sub.add_parser("set-assumption", help="改写附录假设表行处置")
    p_set_assumption.add_argument("--root", required=True)
    p_set_assumption.add_argument("--assumption", required=True, help="<N>=<接受|待校准>")
    p_set_assumption.set_defaults(func=_cmd_set_assumption)

    p_adr_new = sub.add_parser("adr-new", help="ADR 新建：编号扫描 max+1，未知模式 fail-closed（--number 可越）")
    p_adr_new.add_argument("--root", required=True)
    p_adr_new.add_argument("--title", required=True)
    p_adr_new.add_argument("--slug", required=True)
    p_adr_new.add_argument("--number", type=int, default=None)
    p_adr_new.set_defaults(func=_cmd_adr_new)

    p_context_add = sub.add_parser("context-add", help="CONTEXT.md ## Language 追加，同名冲突 fail-closed 不覆盖")
    p_context_add.add_argument("--root", required=True)
    p_context_add.add_argument("--term", required=True)
    p_context_add.add_argument("--definition", required=True)
    p_context_add.set_defaults(func=_cmd_context_add)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
