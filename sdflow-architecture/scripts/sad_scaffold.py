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
import contextlib
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sad_schema  # noqa: E402  (共享解析源，DEC-1；本脚本只写模版骨架，不重实现解析)
import sad_lint    # noqa: E402  ([impl-review-fix] B1：迁移前目标态全量不变式复检复用读侧检查核心)

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "references" / "sad-template.md"

SAD_LOG_HEADER = "# sad-log（append-only 判定留痕）\n"
CONTEXT_STUB = "# Context\n\n## Language\n"

# ---- Task 5: scaffold 分家（adr-new / context-add）常量 --------------------------------
ADR_NUM_RE = re.compile(r"^(\d{4})-")
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
LANGUAGE_HEADING = "## Language"

# ---- [impl-review-fix] B8: 仓级写互斥锁 --------------------------------------------------
LOCK_REL = "openspec/.sad-scaffold.lock"
LOCK_RETRIES = 20          # 20 × 0.1s ≈ 2s 重试预算
LOCK_INTERVAL = 0.1
LOCK_STALE_SEC = 120       # mtime 超此秒数视为残留锁（提示人工删，不自动删）


def _die(code, msg):
    print(f"[sad_scaffold] FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def _read_or_die(path, label):
    """[impl-review-fix] B5：统一读守卫——非 UTF-8 / IO 错误 → die(2)，杜绝裸 read_text traceback。"""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        _die(2, f"{label} 不可读（非 UTF-8 或 IO 错误）: {path}: {e}")
        return None  # 不可达，安抚静态检查


def _reject_newline(value, field):
    """[impl-review-fix] B9：审计/日志入参含 \\n 或 \\r → die(2)，堵伪造 append-only 审计行。"""
    if value is not None and ("\n" in value or "\r" in value):
        _die(2, f"{field} 不得含换行符（\\n / \\r）——append-only 审计行完整性，拒绝多行注入")


def atomic_write(path, text):
    """temp+rename 同目录（DEC-8）：中断只留 temp，不留半写正式文件。
    [impl-review-fix] B8 tmp 名唯一化（tempfile.mkstemp，杜绝固定名并发撞车）；
    [impl-review-fix] B6 OSError（只读目录等）→ die(2) 不 traceback。"""
    d = path.parent
    try:
        fd, tmpname = tempfile.mkstemp(dir=str(d), prefix=path.name + ".", suffix=".tmp-scaffold")
    except OSError as e:
        _die(2, f"原子写失败（无法在 {d} 建临时文件，检查目录可写性）: {e}")
        return  # 不可达
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            os.chmod(tmpname, 0o644)   # mkstemp 默认 0600，回到常规可读（跨平台尽力而为）
        except OSError:
            pass
        os.replace(tmpname, str(path))
    except OSError as e:
        with contextlib.suppress(OSError):
            os.unlink(tmpname)
        _die(2, f"原子写失败（IO 错误）: {path}: {e}")


def append_log(root, line):
    """append-only：不读不改既有行，仅追加一行。[impl-review-fix] B6 OSError → die(2)。"""
    logp = root / sad_schema.LOG_REL_PATH
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        with open(logp, "a", encoding="utf-8") as f:
            f.write(f"- {ts} | {line}\n")
    except OSError as e:
        _die(2, f"日志追加失败（IO 错误）: {logp}: {e}")


def _require_log_appendable(root):
    """[impl-review-fix] B3②：写 SAD 之前先探测 sad-log.md 可追加（open 'a' 探针即关）。
    不可写 → die(2) 且不动 SAD，杜绝"改了 SAD 却留不下审计行"的未审计迁移窗口。"""
    logp = root / sad_schema.LOG_REL_PATH
    try:
        with open(logp, "a", encoding="utf-8"):
            pass
    except OSError as e:
        _die(2, f"sad-log.md 不可追加（审计留痕必需）: {logp}: {e}——"
                f"修复日志可写性后重试，本次未改 SAD")


# ---- [impl-review-fix] B8: 仓级写互斥锁（跨平台 O_CREAT|O_EXCL，不用 fcntl） -----------------


def _acquire_lock(root):
    lockp = root / LOCK_REL
    for _ in range(LOCK_RETRIES):
        try:
            fd = os.open(str(lockp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.close(fd)
            return lockp
        except FileExistsError:
            try:
                age = time.time() - lockp.stat().st_mtime
            except OSError:
                age = 0
            if age > LOCK_STALE_SEC:
                _die(2, f"另一 scaffold 写操作进行中（锁 mtime 超 {LOCK_STALE_SEC}s，疑似残留）；"
                        f"若确认无并发进程，删除 {lockp} 后重试")
            time.sleep(LOCK_INTERVAL)
        except OSError as e:
            _die(2, f"无法创建锁文件 {lockp}: {e}")
    _die(2, f"另一 scaffold 写操作进行中；若确认无并发进程，删除 {lockp} 后重试")


def _release_lock(lockp):
    if lockp is not None:
        with contextlib.suppress(OSError):
            lockp.unlink()


@contextlib.contextmanager
def _repo_lock(root):
    """获取仓级写锁；退出（含 die 的 SystemExit）时 finally 释放。"""
    lockp = _acquire_lock(root)
    try:
        yield
    finally:
        _release_lock(lockp)


def load_sad(root):
    path = root / sad_schema.SAD_REL_PATH
    if not path.is_file():
        if path.exists():
            _die(2, "sad.md 不是常规文件——先跑 init 建骨架")
        else:
            _die(2, "sad.md 不存在——先跑 init 建骨架")
    try:
        return path, path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        _die(2, f"sad 文件不可读（非 UTF-8 或 IO 错误）: {e}")
        return path, None  # 不可达，安抚静态检查


def preflight(root, out):
    """两级 preflight：level 1 无 openspec/ → fail-closed 拒绝并指引；
    level 2 openspec/ 存在但缺 adr/CONTEXT.md → 补齐并留痕（首次创建）。
    [impl-review-fix] B6：路径类型冲突（adr 非目录 / CONTEXT.md 非文件 / architecture 非目录）
    → die(3) 指明冲突；mkdir/atomic_write 的 OSError → die(3) 不 traceback。
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
        if p.exists():
            if kind == "dir" and not p.is_dir():
                _die(3, f"{rel} 已存在但不是目录——路径类型冲突，人工核对后处理")
            if kind == "file" and not p.is_file():
                _die(3, f"{rel} 已存在但不是常规文件——路径类型冲突，人工核对后处理")
            continue
        out.append(f"首次创建 {rel}")
        try:
            if kind == "dir":
                p.mkdir(parents=True, exist_ok=True)
            else:
                atomic_write(p, CONTEXT_STUB)
        except OSError as e:
            _die(3, f"创建 {rel} 失败（IO 错误）: {e}")
    arch = root / "openspec" / "architecture"
    if arch.exists() and not arch.is_dir():
        _die(3, "openspec/architecture 已存在但不是目录——路径类型冲突，人工核对后处理")
    try:
        arch.mkdir(exist_ok=True)
    except OSError as e:
        _die(3, f"创建 openspec/architecture 失败（IO 错误）: {e}")


def _load_template():
    """读模版正文（is_file 前置校验留在 _cmd_init 开头，此处只做读取）。
    [impl-review-fix] B5：经 _read_or_die 兜 IO/编码错误。"""
    return _read_or_die(TEMPLATE_PATH, "sad-template.md")


def _cmd_init(args):
    if not TEMPLATE_PATH.is_file():
        _die(2, "skill 安装不完整：references/sad-template.md 缺失——重跑 bash setup.sh")
    _reject_newline(args.reason, "--reason")   # [impl-review-fix] B9

    root = Path(args.root).resolve()
    announcements = []
    preflight(root, announcements)
    for line in announcements:
        print(line)

    with _repo_lock(root):   # [impl-review-fix] B8
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
            _require_log_appendable(root)   # [impl-review-fix] B3②：先探测 log 可写再动 SAD
            template_text = _load_template()
            atomic_write(sad_path, template_text)
            append_log(root, f"replan: {args.reason}")
            return 0

        # 全新
        template_text = _load_template()
        atomic_write(sad_path, template_text)
        log_path = root / sad_schema.LOG_REL_PATH
        # [impl-review-fix] B3①：log 已存在时 MUST NOT 用 header 覆写旧日志（破 append-only/REQ-12）——
        # 仅在缺失时才建带 header 的空日志；存在则直接续 append。
        if not log_path.exists():
            atomic_write(log_path, SAD_LOG_HEADER)
        append_log(root, "init")
    return 0


def _cmd_log(args):
    _reject_newline(args.line, "--line")   # [impl-review-fix] B9
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

    # [impl-review-fix] B8：扫号-查占-写在锁内即原子（闭合并发同号双写的静默双号）。
    with _repo_lock(root):
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

        # 检查同号 ADR 是否已被占用（同号双 ADR 破坏编号唯一引用）
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

    with _repo_lock(root):   # [impl-review-fix] B8
        text = _read_or_die(ctx_path, "CONTEXT.md")   # [impl-review-fix] B5
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
            # 检查插入点前是否已是空行，若是则不加前导空行（避免空行翻倍）
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
    if not Path(args.slice_file).is_file():
        _die(2, f"slice 文件不存在: {args.slice_file}")
    slice_text = _read_or_die(Path(args.slice_file), "slice-file")   # [impl-review-fix] B5
    # [impl-review-fix] B10：穿越点解析后 NFC 归一（schema 侧 scan_subsystems 已归一，写侧对称）。
    pierce = [unicodedata.normalize("NFC", m.group(1))
              for l in slice_text.splitlines() if (m := sad_schema.PIERCE_RE.match(l))]
    if len(pierce) != len(set(pierce)):
        _die(5, f"穿越点存在重复条目: {sorted(set(p for p in pierce if pierce.count(p) > 1))}")
    if set(pierce) != set(subsys):
        _die(5, f"穿越点集≠第5节子系统集：穿越点{sorted(set(pierce))} vs 子系统{sorted(set(subsys))}")


def _precheck_walkthrough_logs(root):
    """[impl-review-fix] B13：机械投影 REQ-7「MUST NOT 无走查静默过人门」——
    skeleton-ready 前须有 ≥1 行含「走查」+ ≥1 行含「升档判定」的留痕。
    诚实边界：仅锚**存在性**（有留痕行），内容真实性归人门，本检查不判定内容真伪。"""
    log_path = root / sad_schema.LOG_REL_PATH
    if not log_path.is_file():
        _die(5, "缺冷走查/升档判定留痕——先完成步骤④并 log 留痕")
    log_lines = _read_or_die(log_path, "sad-log.md").splitlines()
    has_walkthrough = any("走查" in l for l in log_lines)
    has_upgrade = any("升档判定" in l for l in log_lines)
    if not (has_walkthrough and has_upgrade):
        _die(5, "缺冷走查/升档判定留痕——先完成步骤④并 log 留痕")


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


def _rewrite_top_key(text, prefix, new_line):
    """重写 frontmatter 中以 prefix 开头的顶层键行（sad_status: / assumptions_open:）。
    [impl-review-fix] B7：改用 sad_schema.frontmatter_end（删除本地复刻）；找不到目标键 →
    die(2) 而非静默返回未改文本（旧行为假成功）。"""
    lines = text.splitlines()
    end = sad_schema.frontmatter_end(lines)
    if end is None:
        _die(2, "frontmatter 未闭合（缺结束 ---）——sad.md 结构损坏")
    for i in range(1, end):
        if lines[i].startswith(prefix):
            lines[i] = new_line
            return "\n".join(lines) + "\n"
    _die(2, f"frontmatter 缺目标键（{prefix.rstrip(':')}）——sad.md 结构损坏，未静默改写")


def _rewrite_status(text, to):
    return _rewrite_top_key(text, "sad_status:", f"sad_status: {to}")


def _recompute_assumptions_cache(text):
    """回写 assumptions_open = 附录表中处置为「未处置」的行数（每次写命令后必做）。"""
    _, rows = sad_schema.scan_assumptions(text)
    open_count = sum(1 for _, d in rows if d == "未处置")
    return _rewrite_top_key(text, "assumptions_open:", f"assumptions_open: {open_count}")


def _rewrite_facts_line(text, key, value):
    lines = text.splitlines()
    end = sad_schema.frontmatter_end(lines)   # [impl-review-fix] B7 共享 helper
    if end is None:
        _die(2, "frontmatter 未闭合（缺结束 ---）——sad.md 结构损坏")
    for i in range(1, end):
        if lines[i].startswith("  ") and lines[i].strip().split(":", 1)[0].strip() == key:
            lines[i] = f"  {key}: {value}"
            return "\n".join(lines) + "\n"
    _die(2, f"frontmatter facts 缺子键 {key}——sad.md 结构损坏")


def _rewrite_appendix_row(line, new_disposition):
    m = sad_schema.APPENDIX_ROW_RE.match(line)
    start, end = m.span(2)
    return line[:start] + new_disposition + line[end:]


def _lint_candidate_or_die(new_text, to):
    """[impl-review-fix] B1：迁移前对**完成后的候选全文**（status 已改、slice 已插/删）跑读侧
    检查核心；非空违规 → die(5) 不写盘。目标态导向：validated 不得留 contract[draft]、
    回落 draft 不得残留 contract[validated/frozen]，均在此拦截（不落盘先验）。"""
    try:
        violations, _ = sad_lint.lint_text(new_text)
    except sad_schema.SadParseError as e:
        _die(2, f"迁移候选结构损坏，无法复检: {e}")
        return  # 不可达
    if violations:
        codes = ",".join(sorted({c for c, _ in violations}))
        if to == "draft" and any(c == "contract-invariant-violation" for c, _ in violations):
            _die(5, f"迁移将产生 lint 违规: {codes}——先把 contract 标签降回 planned/draft 再回落")
        _die(5, f"迁移将产生 lint 违规: {codes}——先修正文再迁移")


def _cmd_transition(args):
    _reject_newline(args.reason, "--reason")   # [impl-review-fix] B9
    root = Path(args.root).resolve()
    with _repo_lock(root):   # [impl-review-fix] B8
        path, text = load_sad(root)
        try:
            fm = sad_schema.parse_frontmatter(text)
        except sad_schema.SadParseError as e:
            _die(2, str(e))

        cur, to = fm["sad_status"], args.to
        if (cur, to) not in TRANSITIONS:
            _die(5, f"表外迁移 {cur}→{to}——合法迁移表见 design 状态机节")
        tokens = TRANSITIONS[(cur, to)].split("+")

        if "reason" not in tokens and args.reason:   # [impl-review-fix] B11
            print("--reason 本迁移未使用，未留痕")

        if "precheck" in tokens:
            subsys = sad_schema.scan_subsystems(text)
            _precheck_skeleton(fm, text, args, subsys)
            _precheck_walkthrough_logs(root)          # [impl-review-fix] B13
        if "reason" in tokens and (not args.reason or not args.reason.strip()):
            _die(2, "该回落迁移须提供非空 --reason")
        if "dod" in tokens and not args.dod_confirmed:
            _die(2, "skeleton-ready→validated 须提供 --dod-confirmed")

        _require_log_appendable(root)   # [impl-review-fix] B3②：探测 log 可写再动 SAD

        new_text = text
        if "insert_slice" in tokens:
            # [impl-review-fix] B12：正文已有 SLICE_ANCHOR（遗留手写）→ 拒（insert 只允许零存在）。
            if any(l.strip() == sad_schema.SLICE_ANCHOR for _, l in sad_schema.body_lines(new_text)):
                _die(5, "正文已存在「骨架切片建议」节——先删除遗留重复节再迁移")
            slice_content = _read_or_die(Path(args.slice_file), "slice-file")   # [impl-review-fix] B5
            new_text = insert_slice(new_text, slice_content)
        if "remove_slice" in tokens:
            # [impl-review-fix] B12：多个 SLICE_ANCHOR → 拒（删错节留残）。
            cnt = sum(1 for _, l in sad_schema.body_lines(new_text)
                      if l.strip() == sad_schema.SLICE_ANCHOR)
            if cnt > 1:
                _die(5, f"正文存在 {cnt} 个「骨架切片建议」节——先删重复保唯一再迁移")
            new_text = remove_slice(new_text)
        new_text = _rewrite_status(new_text, to)
        new_text = _recompute_assumptions_cache(new_text)

        _lint_candidate_or_die(new_text, to)   # [impl-review-fix] B1

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
    with _repo_lock(root):   # [impl-review-fix] B8
        path, text = load_sad(root)
        try:
            fm = sad_schema.parse_frontmatter(text)
        except sad_schema.SadParseError as e:
            _die(2, str(e))

        k, sep, v = args.fact.partition("=")
        k, v = k.strip(), v.strip()
        if not sep or k not in sad_schema.FACT_KEYS or v not in sad_schema.FACT_VALUES:
            _die(2, f"--fact 须为 <key>=<value>，key∈{sad_schema.FACT_KEYS}，"
                    f"value∈{sad_schema.FACT_VALUES}，得到 {args.fact!r}")

        # [impl-review-fix] B2：高阶态（非 draft）不可 set-fact missing 破 facts-status 持续不变量。
        if v == "missing" and fm["sad_status"] != "draft":
            _die(5, "高阶状态不可回写 missing——先 transition --to draft --reason <原因> 回落")

        _require_log_appendable(root)   # [impl-review-fix] B3②
        new_text = _rewrite_facts_line(text, k, v)
        new_text = _recompute_assumptions_cache(new_text)
        atomic_write(path, new_text)
        append_log(root, f"set-fact {k}={v}")
    return 0


def _cmd_set_assumption(args):
    root = Path(args.root).resolve()
    with _repo_lock(root):   # [impl-review-fix] B8
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

        # [impl-review-fix] B4：走共享 fence-aware 附录扫描定位目标行号——只改真附录节内该编号行，
        # 不误伤 fence 内示例行 / 附录外同号行（旧实现遍历全文改首个正则匹配，可静默改错行假成功）。
        appendix_lns = sad_schema._appendix_line_set(text)
        lines = text.splitlines()
        target_idx = None
        for ln, line in sad_schema.body_lines(text):
            if ln in appendix_lns and (m := sad_schema.APPENDIX_ROW_RE.match(line)) and int(m.group(1)) == n:
                target_idx = ln - 1
                break
        if target_idx is None:
            _die(2, f"假设-{n} 行不存在于附录表——先补行再处置")
        lines[target_idx] = _rewrite_appendix_row(lines[target_idx], d)
        new_text = "\n".join(lines) + "\n"

        # 写后复扫验证：该编号处置确已更新为 d，否则 die(2)（fail-closed，不假成功）。
        _, rows = sad_schema.scan_assumptions(new_text)
        if not any(rn == n and rd == d for rn, rd in rows):
            _die(2, f"set-assumption 写后复扫失败：假设-{n} 处置未更新为 {d}——sad.md 附录结构异常")

        _require_log_appendable(root)   # [impl-review-fix] B3②
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
