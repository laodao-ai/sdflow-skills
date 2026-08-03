#!/usr/bin/env python3
"""issues_v2.py — issues-v2-single-file-model 的单入口 CLI（Task 1）。

一个 issue 一个 `.md` 文件（YAML frontmatter 为权威数据源，body 为自由格式 Markdown），
`open/` / `closed/` 两目录按状态分层，`INDEX.md` / `CLOSED.md` 为 `reindex` 再生的派生物。

**与 v1（`issues.py` + `sdflow_issues_core`）架构脱钩**（design.md「与 v1 的架构差异」）：
本文件不 import `sdflow_issues_core`——单文件模型下 pool 差异收窄为几个内联常量，
无需 POOL_SPEC 注入模式或跨脚本共享包。Task 3 会删除 v1 的三脚本 + 共享包；本文件
从第一天起就是独立可用的，不依赖即将被删除的东西。

命令：`add` / `set-status` / `scan` / `reindex` / `next-id`。
迁移命令 `migrate`（v1 → v2 一次性转换）在本 change 的 Task 2 实现，不在本文件范围内。
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
try: sys.stdin.reconfigure(encoding="utf-8", errors="strict")
except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
# pool 差异 —— 内联常量（design.md：无 POOL_SPEC 注入模式）
# ══════════════════════════════════════════════════════════════════════════════

POOL_PREFIX = {"bug": "B", "todo": "T"}
PREFIX_POOL = {v: k for k, v in POOL_PREFIX.items()}

# C7：bug 终态 = FIXED|WONTFIX，todo 终态 = DONE|WONTDO（design.md 状态生命周期图）。
STATUS_VALUES = {
    "bug": frozenset({"OPEN", "PROPOSED", "FIXED", "WONTFIX"}),
    "todo": frozenset({"OPEN", "PROPOSED", "DONE", "WONTDO"}),
}
TERMINAL_STATUSES = {
    "bug": frozenset({"FIXED", "WONTFIX"}),
    "todo": frozenset({"DONE", "WONTDO"}),
}
# STOR-01：frontmatter 字段固定顺序。
FRONTMATTER_FIELDS = (
    "id", "pool", "status", "priority", "type", "date", "source_change",
    "module", "summary", "resolved_by", "closed_date", "closed_reason",
)

ID_RE = re.compile(r"^([A-Z])([1-9][0-9]*)$", re.ASCII)
BRANCH_PREFIX_RE = re.compile(r"^[a-z]+/")


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def _fail(problem, cause, fix):
    raise ValueError(f"ERROR: {problem}; cause: {cause}; fix: {fix}")


def _reject_line_unsafe(value, field):
    """frontmatter 值与 body 历史行都是单行结构——CR/LF/NUL 会破坏格式。"""
    if value is None:
        return
    if any(char in str(value) for char in ("\r", "\n", "\0")):
        _fail(
            f"字段 {field} 非法", f"CR/LF/NUL 不能写入单行结构：{value!r}",
            f"为 {field} 提供不含 CR/LF/NUL 的单行值后重试",
        )


# ══════════════════════════════════════════════════════════════════════════════
# repo_root —— 从 sdflow_issues_core 原样移植（design.md「消费方更新清单」：
# recorder-root-resolution 逻辑单点解析、语义不变，仅去掉 recorder_child_env 依赖
# ——v2 无仓级锁，无需清洗 RECORDER_LOCK_ENV 类变量，只保留 git discovery 环境净化）
# ══════════════════════════════════════════════════════════════════════════════

def repo_root(start=None):
    """探测并证明起点所属 git 仓库的根；非 git 仓库（或 git 命令失败）退化为
    `os.path.abspath(start)`。单点解析边界 = 进程：`main()` 调用一次，写回 `args.root`，
    其余 `cmd_*` 一律直接用 `args.root`，MUST NOT 再次调用本函数。"""
    discovery_env = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
        "GIT_INDEX_FILE", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
    )
    discovery_env_prefixes = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
    if start is not None and not os.path.isdir(start):
        raise ValueError(
            "ERROR: 仓根探测起点不是既存目录: " + ascii(start)[:200]
            + "; cause: 显式指定的起点路径不存在或不是目录; "
            "fix: 指定一个既存目录作为起点"
        )
    if start is None or not os.path.isabs(start):
        try:
            cwd = os.getcwd()
        except OSError:
            raise ValueError(
                "ERROR: 无法确定仓根探测起点; cause: 进程当前工作目录已不存在或不可访问; "
                "fix: 切换到一个既存目录后重试，或显式指定一个绝对路径作为起点"
            ) from None
        start = cwd if start is None else os.path.join(cwd, start)
    env = dict(os.environ)
    for name in [
        n for n in env
        if n in discovery_env or n.startswith(discovery_env_prefixes)
    ]:
        env.pop(name, None)
    git_timeout = 30
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, check=True,
            env=env, timeout=git_timeout,
        )
    except subprocess.TimeoutExpired:
        raise ValueError(
            "ERROR: 仓根探测超时; cause: git rev-parse --show-toplevel 在 "
            + str(git_timeout) + " 秒内未返回; "
            "fix: 确认该目录所在文件系统未挂起（网络盘/自动挂载卷最常见），"
            "再在该目录手动跑 git rev-parse --show-toplevel 看是否同样卡住"
        ) from None
    except (OSError, subprocess.CalledProcessError):
        out = None
    start_real = os.path.realpath(start)
    marker_dir = None
    probe = start_real
    while True:
        if os.path.exists(os.path.join(probe, ".git")):
            marker_dir = probe
            break
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    if out is None:
        if marker_dir is not None:
            raise ValueError(
                "ERROR: 起点位于 git 仓库内但 git 拒绝作答: " + ascii(start_real)[:200]
                + "; cause: 上溯找到 .git marker，而 git rev-parse --show-toplevel 以非 0 退出"
                "（dubious ownership / 配置损坏 / git 不可用等）; "
                "fix: 在该目录手动跑 git rev-parse --show-toplevel 看完整报错；"
                "若是 dubious ownership 则 git config --global --add safe.directory <仓根>"
            )
        return os.path.abspath(start)
    try:
        top = out.stdout.decode("utf-8").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "ERROR: git 输出不可解码; cause: " + str(exc) + "; "
            "fix: 检查该路径是否含非 UTF-8 字节的文件名/符号链接目标"
        ) from None
    if not top or not os.path.isabs(top) or not os.path.isdir(top):
        raise ValueError(
            "ERROR: git 返回的仓根不可用: " + ascii(top)[:200]
            + "; cause: git rev-parse --show-toplevel 的输出不是既存的绝对路径目录; "
            "fix: 在该起点手动跑 git rev-parse --show-toplevel 比对输出，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    top_real = os.path.realpath(top)
    try:
        common = os.path.commonpath([
            os.path.normcase(start_real), os.path.normcase(top_real),
        ])
    except ValueError:
        raise ValueError(
            "ERROR: 无法比较 git 返回的仓根与探测起点: " + ascii(top)[:200]
            + "; cause: 两者不在同一个路径根下（如 Windows 跨盘符），无公共前缀可比; "
            "fix: 检查 .git/config 的 core.worktree 是否把工作树指到了另一个盘符，"
            "并清除 GIT_WORK_TREE / GIT_DIR 等重定向后重试"
        ) from None
    if common != os.path.normcase(top_real):
        raise ValueError(
            "ERROR: git 返回的仓根不包含探测起点: " + ascii(top)[:200]
            + "; cause: 工作树被 core.worktree 或环境变量重定向到起点之外; "
            "fix: 清除 .git/config 的 core.worktree 与 GIT_* 重定向后重试"
        )
    if not os.path.exists(os.path.join(top_real, ".git")):
        raise ValueError(
            "ERROR: git 返回的仓根缺少 .git: " + ascii(top)[:200]
            + "; cause: 该目录不带 worktree marker，不是一个仓库根; "
            "fix: 确认 .git/config 的 core.worktree 未指向非仓库目录，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    if os.path.normcase(marker_dir) != os.path.normcase(top_real):
        raise ValueError(
            "ERROR: git 返回的仓根不是起点所属的最近仓库: " + ascii(top)[:200]
            + "; cause: 自起点上溯遇到的第一个 .git 位于 " + ascii(marker_dir)[:200]
            + "，git 却返回了更外层的仓库（core.worktree 指向祖先仓 / git 被替换）; "
            "fix: 清除 .git/config 的 core.worktree 重定向，"
            "并用 which -a git 确认 PATH 上的 git 未被 wrapper 替换"
        )
    return top_real


def detect_change(root):
    """自动探测当前所处 OpenSpec change 名（add 填 source_change / set-status 填
    resolved_by 共用）。优先级：openspec/changes/ 下唯一未归档目录 → git branch 名去前缀 → 空字符串。"""
    changes_dir = os.path.join(root, "openspec", "changes")
    dirs = []
    if os.path.isdir(changes_dir):
        dirs = sorted(
            d for d in os.listdir(changes_dir)
            if d != "archive" and os.path.isdir(os.path.join(changes_dir, d))
        )
    if len(dirs) == 1:
        return dirs[0]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace",
        )
        branch = out.stdout.strip()
    except Exception:
        branch = ""
    candidate = BRANCH_PREFIX_RE.sub("", branch) if branch else ""
    if candidate and (not dirs or candidate in dirs):
        return candidate
    return ""


def _is_git_repo(root):
    try:
        proc = subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


# ══════════════════════════════════════════════════════════════════════════════
# 原子写 IO
# ══════════════════════════════════════════════════════════════════════════════

def atomic_write_text(path, text):
    """已存在文件的原子替换写入：同目录 .tmp + os.replace。"""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# ══════════════════════════════════════════════════════════════════════════════
# frontmatter 编解码（C9：手写有界子集，不引入 PyYAML）
# ══════════════════════════════════════════════════════════════════════════════

_FM_QUOTED_RE = re.compile(r'^([a-z_]+): "(.*)"$')
_FM_NULL_RE = re.compile(r'^([a-z_]+): null$')


def _quote_value(value):
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def _unquote_value(raw):
    return raw.replace('\\"', '"')


def render_frontmatter(frontmatter):
    """按 FRONTMATTER_FIELDS 固定顺序渲染 frontmatter 行（不含围栏）。"""
    lines = []
    for key in FRONTMATTER_FIELDS:
        value = frontmatter.get(key)
        if value is None:
            lines.append(f"{key}: null")
        else:
            _reject_line_unsafe(value, key)
            lines.append(f"{key}: {_quote_value(value)}")
    return "\n".join(lines) + "\n"


def parse_frontmatter(fm_text):
    """解析 `---` 围栏内的文本，返回 dict。只认 `^key: "value"$` 或 `^key: null$`。"""
    result = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        m = _FM_QUOTED_RE.match(line)
        if m:
            result[m.group(1)] = _unquote_value(m.group(2))
            continue
        m = _FM_NULL_RE.match(line)
        if m:
            result[m.group(1)] = None
            continue
        _fail(
            "frontmatter 行非法", repr(line),
            '每行必须匹配 `key: "value"` 或 `key: null`',
        )
    return result


def render_document(frontmatter, body):
    return "---\n" + render_frontmatter(frontmatter) + "---\n" + body


def split_frontmatter(text):
    if not text.startswith("---\n"):
        _fail("frontmatter envelope 非法", "文件不以 `---\\n` 开头", "修正文件头部围栏后重试")
    close = text.find("\n---\n", 4)
    if close < 0:
        _fail("frontmatter envelope 非法", "找不到闭合的 `---` 围栏", "补全闭合围栏后重试")
    fm_text = text[4:close]
    body = text[close + len("\n---\n"):]
    return fm_text, body


# ══════════════════════════════════════════════════════════════════════════════
# read_issue / write_issue / find_issue
# ══════════════════════════════════════════════════════════════════════════════

def read_issue(path):
    """读单文件 issue，返回 `(frontmatter dict, body str)`；body 未被修改或解析。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm_text, body = split_frontmatter(text)
    return parse_frontmatter(fm_text), body


def write_issue(path, frontmatter, body, create=False):
    """写单文件 issue。`create=True`（新建）用 `O_CREAT|O_EXCL`（并发写同 ID 时
    后到者收到 `FileExistsError`，调用方负责重取 ID 重试）；否则原子替换（.tmp + rename）。"""
    text = render_document(frontmatter, body)
    if create:
        d = os.path.dirname(path) or "."
        os.makedirs(d, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        except Exception:
            try:
                os.remove(path)
            except OSError:
                pass
            raise
    else:
        atomic_write_text(path, text)


def _issues_dir(root, location):
    return os.path.join(root, "openspec", "issues", location)


def find_issue(root, issue_id):
    """按 ID 在 `open/` 和 `closed/` 中定位，返回 `(path, location)`；
    未找到返回 `(None, None)`。"""
    for location in ("open", "closed"):
        path = os.path.join(_issues_dir(root, location), f"{issue_id}.md")
        if os.path.isfile(path):
            return path, location
    return None, None


def _pool_for_id(issue_id):
    m = ID_RE.match(issue_id)
    if not m or m.group(1) not in PREFIX_POOL:
        _die(f"ID 前缀非法：{issue_id}（须以 B 或 T 起头，如 B7 / T257）")
    return PREFIX_POOL[m.group(1)]


# ══════════════════════════════════════════════════════════════════════════════
# next_id
# ══════════════════════════════════════════════════════════════════════════════

def next_id(root, pool):
    """STOR-04：扫描 `open/` + `closed/` 全部文件名，取该 pool 前缀的 max(N)+1。"""
    prefix = POOL_PREFIX[pool]
    pattern = re.compile(rf"^{prefix}([1-9][0-9]*)\.md$", re.ASCII)
    max_n = 0
    for location in ("open", "closed"):
        d = _issues_dir(root, location)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            m = pattern.match(name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1}"


# ══════════════════════════════════════════════════════════════════════════════
# cmd_add
# ══════════════════════════════════════════════════════════════════════════════

_ADD_ALLOWED_KEYS = frozenset({"module", "summary", "priority", "type", "source_change"})


def _load_add_payload(raw_json):
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        _die(f"--json 不是合法 JSON：{exc}")
    if not isinstance(payload, dict):
        _die("--json 必须是一个 JSON object")
    return payload


def cmd_add(args):
    root = args.root
    pool = args.pool
    payload = _load_add_payload(args.json)

    unknown = sorted(set(payload) - _ADD_ALLOWED_KEYS)
    if unknown:
        _die(f"--json 含未知字段：{unknown}（允许字段：{sorted(_ADD_ALLOWED_KEYS)}）")

    other_field = "type" if pool == "bug" else "priority"
    if other_field in payload:
        _die(f"--pool {pool} 不接受字段 {other_field!r}（{other_field} 仅属于另一 pool）")

    module = payload.get("module")
    summary = payload.get("summary")
    if not isinstance(module, str) or not module.strip():
        _die("--json 缺少非空字符串字段 module")
    if not isinstance(summary, str) or not summary.strip():
        _die("--json 缺少非空字符串字段 summary")
    for field in ("module", "summary", "priority", "type", "source_change"):
        if field in payload:
            _reject_line_unsafe(payload.get(field), field)

    source_change = payload.get("source_change")
    if source_change is None:
        source_change = detect_change(root) or None

    while True:
        issue_id = next_id(root, pool)
        path = os.path.join(_issues_dir(root, "open"), f"{issue_id}.md")
        frontmatter = {
            "id": issue_id,
            "pool": pool,
            "status": "OPEN",
            "priority": payload.get("priority") if pool == "bug" else None,
            "type": payload.get("type") if pool == "todo" else None,
            "date": datetime.date.today().isoformat(),
            "source_change": source_change,
            "module": module,
            "summary": summary,
            "resolved_by": None,
            "closed_date": None,
            "closed_reason": None,
        }
        try:
            write_issue(path, frontmatter, "", create=True)
            break
        except FileExistsError:
            continue

    if _is_git_repo(root):
        rel = os.path.relpath(path, root)
        try:
            subprocess.run(
                ["git", "-C", root, "add", rel],
                capture_output=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    print(json.dumps(
        {
            "id": issue_id, "pool": pool, "status": "OPEN",
            "file": os.path.relpath(path, root).replace(os.sep, "/"),
            "source_change": source_change,
        },
        ensure_ascii=False,
    ))


# ══════════════════════════════════════════════════════════════════════════════
# cmd_set_status
# ══════════════════════════════════════════════════════════════════════════════

def cmd_set_status(args):
    root = args.root
    issue_id = args.id
    new = args.to

    _reject_line_unsafe(args.evidence, "evidence")
    _reject_line_unsafe(args.reason, "reason")

    if not ID_RE.match(issue_id):
        _die(f"ID 格式非法：{issue_id!r}（须匹配 [A-Z][1-9][0-9]*）")

    path, location = find_issue(root, issue_id)
    if path is None:
        _die(f"未找到 ID：{issue_id}")

    frontmatter, body = read_issue(path)
    pool = frontmatter.get("pool")
    if pool not in STATUS_VALUES:
        _die(f"file={path} frontmatter.pool 非法：{pool!r}")
    if _pool_for_id(issue_id) != pool:
        _die(f"file={path} ID 前缀与 frontmatter.pool 不符：id={issue_id} pool={pool}")

    if location == "closed":
        _die(f"ID {issue_id} 已处于终态（位于 closed/），不可再改 status")

    if new not in STATUS_VALUES[pool]:
        _die(f"状态码非法：{new}（pool={pool} 合法值={sorted(STATUS_VALUES[pool])}）")

    if pool == "bug" and new == "FIXED" and not args.evidence:
        _die("置为 FIXED 必须提供 --evidence（commit hash 或 change 名）")
    if pool == "todo" and new == "DONE" and not args.evidence:
        _die("置为 DONE 必须提供 --evidence（关联的 change 名或 commit hash）")
    if new in ("WONTFIX", "WONTDO") and not args.reason:
        _die(f"置为 {new} 必须提供 --reason（不做的理由）")

    old = frontmatter["status"]
    note = args.evidence or args.reason or ""
    today = datetime.date.today().isoformat()
    hist_line = f"> {today} 状态：{old} → {new}" + (f"（{note}）" if note else "")
    if body and not body.endswith("\n"):
        body += "\n"
    new_body = body + hist_line + "\n"

    frontmatter["status"] = new
    terminal = new in TERMINAL_STATUSES[pool]
    if terminal:
        frontmatter["closed_date"] = today
        frontmatter["resolved_by"] = detect_change(root) or None
        if new in ("WONTFIX", "WONTDO"):
            frontmatter["closed_reason"] = args.reason

    # M-2（spec-review-report）：先在原位置（open/）原子写完更新后的 frontmatter+body，
    # 再执行移动——中途被杀时文件仍在 open/ 但 status 已是新值，reindex 可据此检测不一致，
    # 不会出现「文件已在 closed/ 但内容是旧值」的更隐蔽的窗口。
    write_issue(path, frontmatter, new_body, create=False)

    closed_path = None
    if terminal:
        closed_path = os.path.join(_issues_dir(root, "closed"), f"{issue_id}.md")
        os.makedirs(os.path.dirname(closed_path), exist_ok=True)
        rel_open = os.path.relpath(path, root)
        rel_closed = os.path.relpath(closed_path, root)
        if _is_git_repo(root):
            tracked = subprocess.run(
                ["git", "-C", root, "ls-files", "--error-unmatch", rel_open],
                capture_output=True, timeout=30,
            )
            if tracked.returncode != 0:
                subprocess.run(
                    ["git", "-C", root, "add", rel_open],
                    capture_output=True, timeout=30,
                )
            mv = subprocess.run(
                ["git", "-C", root, "mv", rel_open, rel_closed],
                capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace",
            )
            if mv.returncode != 0:
                _die(f"git mv 失败（{rel_open} → {rel_closed}）：{mv.stderr.strip()}")
        else:
            os.rename(path, closed_path)

    out_path = closed_path if closed_path else path
    print(json.dumps(
        {
            "id": issue_id, "pool": pool, "old": old, "new": new,
            "file": os.path.relpath(out_path, root).replace(os.sep, "/"),
        },
        ensure_ascii=False,
    ))


# ══════════════════════════════════════════════════════════════════════════════
# cmd_scan
# ══════════════════════════════════════════════════════════════════════════════

def _scan_dir(root, location):
    d = _issues_dir(root, location)
    items = []
    if not os.path.isdir(d):
        return items
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(d, name)
        try:
            frontmatter, _body = read_issue(path)
        except (ValueError, OSError) as exc:
            print(f"WARNING: 跳过不可解析文件 {path}: {exc}", file=sys.stderr)
            continue
        items.append(frontmatter)
    return items


def _semantic_sort_key(frontmatter):
    m = ID_RE.match(frontmatter.get("id", ""))
    return (m.group(1), int(m.group(2))) if m else (frontmatter.get("id", ""), 0)


def scan_issues(root, pools=None, statuses=None, source_change=None, include_closed=False):
    """纯函数式扫描：返回按语义 ID 排序的 frontmatter dict 列表。"""
    locations = ["open", "closed"] if include_closed else ["open"]
    items = []
    for location in locations:
        items.extend(_scan_dir(root, location))
    if pools is not None:
        items = [it for it in items if it.get("pool") in pools]
    if statuses is not None:
        items = [it for it in items if it.get("status") in statuses]
    if source_change is not None:
        items = [it for it in items if it.get("source_change") == source_change]
    items.sort(key=_semantic_sort_key)
    return items


def cmd_scan(args):
    root = args.root
    pools = {args.pool} if args.pool else None
    statuses = set(args.status) if args.status else None
    items = scan_issues(
        root, pools=pools, statuses=statuses,
        source_change=args.source_change, include_closed=args.all,
    )
    if args.json:
        print(json.dumps(items, ensure_ascii=False))
        return
    if not items:
        print("（无匹配项）")
        return
    for it in items:
        specific = it.get("priority") or it.get("type") or "-"
        print(
            f"{it.get('id', '?'):<6} {it.get('pool', '?'):<4} "
            f"{it.get('status', '?'):<10} {specific:<12} "
            f"{it.get('module', ''):<24} {it.get('summary', '')}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# cmd_reindex
# ══════════════════════════════════════════════════════════════════════════════

INDEX_BANNER = "<!-- GENERATED by issues_v2.py reindex — DO NOT EDIT -->"


def _escape_cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def generate_index_md(items):
    lines = [
        INDEX_BANNER, "", "# Issues Index (Open)", "",
        "| ID | Pool | Status | Date | Module | Summary |",
        "|----|------|--------|------|--------|---------|",
    ]
    for it in items:
        lines.append(
            "| " + " | ".join(_escape_cell(it.get(k)) for k in
                               ("id", "pool", "status", "date", "module", "summary"))
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_closed_md(items):
    lines = [
        INDEX_BANNER, "", "# Issues Index (Closed)", "",
        "| ID | Pool | Status | Date | Module | Summary | Closed Date | Resolved By | Closed Reason |",
        "|----|------|--------|------|--------|---------|-------------|-------------|----------------|",
    ]
    for it in items:
        lines.append(
            "| " + " | ".join(_escape_cell(it.get(k)) for k in (
                "id", "pool", "status", "date", "module", "summary",
                "closed_date", "resolved_by", "closed_reason",
            )) + " |"
        )
    lines.append("")
    return "\n".join(lines)


def cmd_reindex(args):
    root = args.root
    open_items = scan_issues(root, include_closed=False)
    closed_items = _scan_dir(root, "closed")
    closed_items.sort(key=_semantic_sort_key)

    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    closed_path = os.path.join(root, "openspec", "issues", "CLOSED.md")
    atomic_write_text(index_path, generate_index_md(open_items))
    atomic_write_text(closed_path, generate_closed_md(closed_items))
    print(
        f"reindex：已重建 {index_path}（open {len(open_items)} 项）与 "
        f"{closed_path}（closed {len(closed_items)} 项）"
    )


# ══════════════════════════════════════════════════════════════════════════════
# cmd_next_id
# ══════════════════════════════════════════════════════════════════════════════

def cmd_next_id(args):
    print(next_id(args.root, args.pool))


# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="issues_v2 — 单文件 issue 存储模型 CLI")
    p.add_argument("--root", default=None, help="目标项目根；默认自动探测 git 根")
    sub = p.add_subparsers(dest="cmd", required=True)

    sa = sub.add_parser("add", help="创建新 issue 到 open/")
    sa.add_argument("--pool", required=True, choices=["bug", "todo"])
    sa.add_argument("--json", required=True, help="JSON object：module/summary 必填，"
                     "priority(bug only)/type(todo only)/source_change 可选")
    sa.set_defaults(func=cmd_add)

    ss = sub.add_parser("set-status", help="修改 issue 状态；终态自动 git mv 到 closed/")
    ss.add_argument("--id", required=True)
    ss.add_argument("--to", required=True)
    ss.add_argument("--evidence", default=None, help="FIXED(bug)/DONE(todo) 必填")
    ss.add_argument("--reason", default=None, help="WONTFIX/WONTDO 必填")
    ss.set_defaults(func=cmd_set_status)

    sc = sub.add_parser("scan", help="扫描 issue 列表")
    sc.add_argument("--pool", choices=["bug", "todo"], default=None)
    sc.add_argument("--status", action="append", default=None, help="可重复传多个")
    sc.add_argument("--source-change", dest="source_change", default=None)
    sc.add_argument("--all", action="store_true", help="含 closed/（默认只看 open/）")
    sc.add_argument("--json", action="store_true", help="JSON 列表输出")
    sc.set_defaults(func=cmd_scan)

    sr = sub.add_parser("reindex", help="再生 INDEX.md + CLOSED.md")
    sr.set_defaults(func=cmd_reindex)

    sn = sub.add_parser("next-id", help="输出下一个可用 ID")
    sn.add_argument("--pool", required=True, choices=["bug", "todo"])
    sn.set_defaults(func=cmd_next_id)

    args = p.parse_args()
    try:
        args.root = repo_root(args.root)
        args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
