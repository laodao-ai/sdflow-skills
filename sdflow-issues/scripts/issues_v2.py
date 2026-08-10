#!/usr/bin/env python3
"""issues_v2.py — issues-v2-single-file-model 的单入口 CLI（Task 1）。

一个 issue 一个 `.md` 文件（YAML frontmatter 为权威数据源，body 为自由格式 Markdown），
`open/` / `closed/` 两目录按状态分层，`INDEX.md` / `CLOSED.md` 为 `reindex` 再生的派生物。

**与 v1（`issues.py` + `sdflow_issues_core`）架构脱钩**（design.md「与 v1 的架构差异」）：
本文件不 import `sdflow_issues_core`——单文件模型下 pool 差异收窄为几个内联常量，
无需 POOL_SPEC 注入模式或跨脚本共享包。Task 3 会删除 v1 的三脚本 + 共享包；本文件
从第一天起就是独立可用的，不依赖即将被删除的东西。

命令：`add` / `set-status` / `scan` / `reindex` / `next-id` / `migrate`。

`migrate`（Task 2）是 v1 → v2 的一次性转换工具，自成一体地内联了 v1 双格式（legacy 表格 +
frontmatter overlay）的**只读**解析——不 import `sdflow_issues_core`（Task 3 会连同 v1 三脚本一并
删除该包；本文件从第一天起就不能依赖即将消失的东西，见上方模块级架构说明）。它复用的是
`_build_effective_snapshot` 的 **shadow 算法**（先收 legacy 表格行、frontmatter overlay 同 ID 覆盖），
不是那份代码本身——迁移只读旧文件、不回写，故不需要 core 里写路径相关的锁 / 校验 / 转义机器。
"""

import argparse
import datetime
import glob
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


def _issues_dir(root, location, pool=None):
    base = os.path.join(root, "openspec", "issues", location)
    if pool is not None:
        return os.path.join(base, pool)
    return base


def _pool_subdir(issue_id):
    """ID 前缀 → pool 子目录名（T→todo, B→bug）。"""
    m = ID_RE.match(issue_id)
    if m and m.group(1) in PREFIX_POOL:
        return PREFIX_POOL[m.group(1)]
    return None


def find_issue(root, issue_id):
    """按 ID 在 `open/` 和 `closed/` 中定位，返回 `(path, location)`；
    未找到返回 `(None, None)`。"""
    pool = _pool_subdir(issue_id)
    for location in ("open", "closed"):
        path = os.path.join(_issues_dir(root, location, pool), f"{issue_id}.md")
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
        d = _issues_dir(root, location, pool)
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
        path = os.path.join(_issues_dir(root, "open", pool), f"{issue_id}.md")
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
        closed_path = os.path.join(_issues_dir(root, "closed", pool), f"{issue_id}.md")
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
# cmd_reopen —— 终态唯一受控逆转换（design.md D3 / R-IS1）
#
# 与 cmd_set_status 对称但方向相反：closed/ → open/。守卫顺序：ID 格式合法 → 必须位于
# closed/（在 open/ 则拒绝，MUST NOT 绕过 set-status 的终态守卫）→ ID 前缀与 pool 一致 →
# --to 只接受非终态值。中断残留判定（closed/ 内文件 status 已非终态）在守卫之后、字段清理
# 之前分支：残留 ⇒ 跳过字段清理与历史行追加，只补 M-2 原子序的第二步（git mv）+ reindex。
# ══════════════════════════════════════════════════════════════════════════════

REOPEN_TARGET_STATUSES = ("OPEN", "PROPOSED")


def cmd_reopen(args):
    root = args.root
    issue_id = args.id
    reason = args.reason
    to = args.to

    _reject_line_unsafe(reason, "reason")

    if not ID_RE.match(issue_id):
        _die(f"ID 格式非法：{issue_id!r}（须匹配 [A-Z][1-9][0-9]*）")

    path, location = find_issue(root, issue_id)
    if path is None:
        _die(f"未找到 ID：{issue_id}")

    if location == "open":
        _die(f"ID {issue_id} 不在终态（位于 open/），无需 reopen")

    frontmatter, body = read_issue(path)
    pool = frontmatter.get("pool")
    if pool not in STATUS_VALUES:
        _die(f"file={path} frontmatter.pool 非法：{pool!r}")
    if _pool_for_id(issue_id) != pool:
        _die(f"file={path} ID 前缀与 frontmatter.pool 不符：id={issue_id} pool={pool}")

    if to not in REOPEN_TARGET_STATUSES:
        _die(f"--to 只接受非终态状态（{'|'.join(REOPEN_TARGET_STATUSES)}），收到 {to}")

    old = frontmatter["status"]
    # 中断残留：文件仍在 closed/，但 status 已被上一次（被打断的）reopen 改为非终态——
    # 说明「原位原子写」已完成，只差 git mv。此时 MUST NOT 重复字段清理/历史行追加。
    residue = old not in TERMINAL_STATUSES[pool]

    if residue:
        print(
            f"WARNING: {path} 判为中断残留（closed/ 内 status={old} 已非终态）——"
            "跳过字段清理与历史行追加，仅续跑迁移",
            file=sys.stderr,
        )
        new_status = old
    else:
        orig_closed_reason = frontmatter.get("closed_reason")
        orig_note = orig_closed_reason if orig_closed_reason else "（无 closed_reason）"
        today = datetime.date.today().isoformat()
        hist_line = (
            f"> {today} 状态：{old} → {to}（reopen：{reason}；原 closed_reason：{orig_note}）"
        )
        if body and not body.endswith("\n"):
            body += "\n"
        new_body = body + hist_line + "\n"

        frontmatter["status"] = to
        frontmatter["closed_date"] = None
        frontmatter["closed_reason"] = None
        frontmatter["resolved_by"] = None

        # M-2 原子序（镜像 cmd_set_status）：先在原位置（closed/）原子写完更新后的
        # frontmatter+body，再执行移动——中途被杀时文件仍在 closed/ 但 status 已非终态，
        # 上面的 residue 分支据此检测并幂等续跑。
        write_issue(path, frontmatter, new_body, create=False)
        new_status = to

    open_dir = _issues_dir(root, "open", pool)
    open_path = os.path.join(open_dir, f"{issue_id}.md")
    os.makedirs(open_dir, exist_ok=True)
    rel_closed = os.path.relpath(path, root)
    rel_open = os.path.relpath(open_path, root)
    if _is_git_repo(root):
        tracked = subprocess.run(
            ["git", "-C", root, "ls-files", "--error-unmatch", rel_closed],
            capture_output=True, timeout=30,
        )
        if tracked.returncode != 0:
            subprocess.run(
                ["git", "-C", root, "add", rel_closed],
                capture_output=True, timeout=30,
            )
        mv = subprocess.run(
            ["git", "-C", root, "mv", rel_closed, rel_open],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        if mv.returncode != 0:
            _die(f"git mv 失败（{rel_closed} → {rel_open}）：{mv.stderr.strip()}")
    else:
        os.rename(path, open_path)

    try:
        cmd_reindex(args)
    except SystemExit:
        raise
    except Exception as exc:
        _die(f"重开已生效，重跑 reindex 即自愈：{exc}")

    print(json.dumps(
        {
            "id": issue_id, "pool": pool, "old": old, "new": new_status,
            "file": os.path.relpath(open_path, root).replace(os.sep, "/"),
        },
        ensure_ascii=False,
    ))


# ══════════════════════════════════════════════════════════════════════════════
# cmd_scan
# ══════════════════════════════════════════════════════════════════════════════

def _scan_dir(root, location):
    items = []
    for pool in ("bug", "todo"):
        d = _issues_dir(root, location, pool)
        if not os.path.isdir(d):
            continue
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


def _id_link(issue_id, location):
    pool = _pool_subdir(issue_id) or "unknown"
    return f"[{issue_id}]({location}/{pool}/{issue_id}.md)"


def generate_index_md(items):
    lines = [
        INDEX_BANNER, "", "# Issues Index (Open)", "",
        "| ID | Pool | Status | Date | Module | Summary |",
        "|----|------|--------|------|--------|---------|",
    ]
    for it in items:
        cells = [_id_link(it["id"], "open")] + [
            _escape_cell(it.get(k)) for k in
            ("pool", "status", "date", "module", "summary")
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def generate_closed_md(items):
    lines = [
        INDEX_BANNER, "", "# Issues Index (Closed)", "",
        "| ID | Pool | Status | Date | Module | Summary | Closed Date | Resolved By | Closed Reason |",
        "|----|------|--------|------|--------|---------|-------------|-------------|----------------|",
    ]
    for it in items:
        cells = [_id_link(it["id"], "closed")] + [
            _escape_cell(it.get(k)) for k in (
                "pool", "status", "date", "module", "summary",
                "closed_date", "resolved_by", "closed_reason",
            )
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def cmd_reindex(args):
    root = args.root
    open_items = scan_issues(root, include_closed=False)
    closed_items = _scan_dir(root, "closed")
    closed_items.sort(key=_semantic_sort_key)

    # reopen 中断残留可被检出（design.md D3）：closed/ 内文件 status 已非终态 = 上一次
    # reopen 在原位原子写之后、git mv 之前被打断，尚未完成迁移。
    for it in closed_items:
        item_pool = it.get("pool")
        item_status = it.get("status")
        if item_pool in TERMINAL_STATUSES and item_status not in TERMINAL_STATUSES[item_pool]:
            print(
                f"WARNING: closed/ 内文件状态非终态：id={it.get('id')} pool={item_pool} "
                f"status={item_status}（疑似 reopen 中断残留，未完成 git mv；"
                "对该 ID 重跑 reopen 即可续跑迁移）",
                file=sys.stderr,
            )

    index_path = os.path.join(root, "openspec", "issues", "INDEX.md")
    closed_path = os.path.join(root, "openspec", "issues", "CLOSED.md")
    atomic_write_text(index_path, generate_index_md(open_items))
    atomic_write_text(closed_path, generate_closed_md(closed_items))
    print(
        f"reindex：已重建 {index_path}（open {len(open_items)} 项）与 "
        f"{closed_path}（closed {len(closed_items)} 项）"
    )


# ══════════════════════════════════════════════════════════════════════════════
# cmd_reorganize — flat → pool 子目录一次性迁移
# ══════════════════════════════════════════════════════════════════════════════

def cmd_reorganize(args):
    root = args.root
    is_git = _is_git_repo(root)
    moved = 0
    for location in ("open", "closed"):
        base = _issues_dir(root, location)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if not name.endswith(".md"):
                continue
            src = os.path.join(base, name)
            if not os.path.isfile(src):
                continue
            issue_id = name[:-3]
            pool = _pool_subdir(issue_id)
            if pool is None:
                print(f"WARNING: 跳过无法识别 pool 的文件 {name}", file=sys.stderr)
                continue
            dest_dir = _issues_dir(root, location, pool)
            dest = os.path.join(dest_dir, name)
            if os.path.exists(dest):
                continue
            os.makedirs(dest_dir, exist_ok=True)
            rel_src = os.path.relpath(src, root)
            rel_dest = os.path.relpath(dest, root)
            if is_git:
                mv = subprocess.run(
                    ["git", "-C", root, "mv", rel_src, rel_dest],
                    capture_output=True, text=True, timeout=30,
                    encoding="utf-8", errors="replace",
                )
                if mv.returncode != 0:
                    print(f"WARNING: git mv 失败 {rel_src} → {rel_dest}: {mv.stderr.strip()}",
                          file=sys.stderr)
                    continue
            else:
                os.rename(src, dest)
            moved += 1
    cmd_reindex(args)
    print(f"reorganize：已移动 {moved} 个文件到 pool 子目录")


# ══════════════════════════════════════════════════════════════════════════════
# cmd_next_id
# ══════════════════════════════════════════════════════════════════════════════

def cmd_next_id(args):
    print(next_id(args.root, args.pool))


# ══════════════════════════════════════════════════════════════════════════════
# cmd_migrate —— v1 → v2 一次性迁移（design.md「migrate 命令」/「字段映射」）
#
# 只读解析 v1 两种格式（legacy 表格 / frontmatter overlay），逐 item 去重
# （frontmatter 覆盖同 ID 的 legacy 表格行——shadow 算法，MIG-01），字段映射到 v2
# schema（MIG-02），已存在的目标文件幂等跳过（MIG-03），完成后自动 reindex
# （MIG-04），PLANNED 批次计划文本搬入成员 issue body（MIG-05）。
# ══════════════════════════════════════════════════════════════════════════════

_V1_ITEM_LINE_RE = re.compile(r'^    ([A-Z][1-9][0-9]*): (\{.*\})$')
_V1_TABLE_HDR_RE = re.compile(r'^\s*\|\s*ID\s*\|')
_V1_ROW_ID_RE = re.compile(r'^\s*\|\s*([A-Z][1-9][0-9]*)\s*\|')
_V1_MARKER_RE = re.compile(r'^<!-- sdflow-issue-block:(start|end) id=([A-Z][1-9][0-9]*) -->\s*$')
_V1_HEADING_RE = re.compile(r'^##\s+([A-Z][1-9][0-9]*)\s*:')
_V1_BUGLIST_NAME_RE = re.compile(r'(\d{4}-\d{2}-\d{2})-buglist\.md$')
_V1_TODOLIST_NAME_RE = re.compile(r'(\d{4}-\d{2})-todolist\.md$')
_V1_HIST_LINE_RE = re.compile(
    r'^>\s*(?P<date>\S+)\s*状态[:：]\s*\S+\s*→\s*(?P<new>[A-Z_]+)(?:（(?P<note>.*)）)?\s*$',
    re.MULTILINE,
)
_V1_CHANGE_TOKEN_RE = re.compile(r'^(?:change\s+)?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)')
_V1_ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_V1_BATCH_BLOCK_RE = re.compile(
    r'^### (?P<key>\S+) — .*\n'
    r'状态: (?P<status>\S+)\n'
    r'成员: \(生成\)(?P<members>.*)\n'
    r'优先级: .*\n'
    r'计划: (?P<plan>.*)$',
    re.MULTILINE,
)


def _v1_collect_files(root):
    """扫描 `openspec/issues/buglist/*.md` + `openspec/issues/todolist/*.md`，返回
    `[(path, pool), ...]`（各自按文件名排序，buglist 在前）。"""
    files = []
    bug_dir = os.path.join(root, "openspec", "issues", "buglist")
    todo_dir = os.path.join(root, "openspec", "issues", "todolist")
    if os.path.isdir(bug_dir):
        files += [(p, "bug") for p in sorted(glob.glob(os.path.join(bug_dir, "*.md")))]
    if os.path.isdir(todo_dir):
        files += [(p, "todo") for p in sorted(glob.glob(os.path.join(todo_dir, "*.md")))]
    return files


def _v1_file_date(path):
    """date 字段来源（design.md 字段映射表）：buglist 从文件名 `YYYY-MM-DD` 取；
    todolist 从文件名 `YYYY-MM` 取，补 `-01`。"""
    name = os.path.basename(path)
    m = _V1_BUGLIST_NAME_RE.search(name)
    if m:
        return m.group(1)
    m = _V1_TODOLIST_NAME_RE.search(name)
    if m:
        return m.group(1) + "-01"
    _fail(
        f"文件名不含可识别日期: {name}", "既不匹配 buglist 也不匹配 todolist 命名约定",
        "文件名须为 YYYY-MM-DD-buglist.md 或 YYYY-MM-todolist.md",
    )


def _v1_split_frontmatter(text):
    """有 `sdflow-issues:` frontmatter 则返回 `(items_dict, body_after_fm)`；
    否则返回 `({}, text)`（纯 legacy 格式，MIG-01 Scenario 1）。"""
    header = "---\nsdflow-issues:\n"
    if not text.startswith(header):
        return {}, text
    close = text.find("\n---\n", 4)
    if close < 0:
        _fail("v1 frontmatter envelope 非法", "找不到闭合的 `---` 围栏", "补全闭合围栏后重试")
    fm_text = text[4:close]
    body = text[close + len("\n---\n"):]
    items = {}
    for line in fm_text.splitlines():
        m = _V1_ITEM_LINE_RE.match(line)
        if not m:
            continue  # schema/pool/mode/items: 等 header 行——迁移不校验（只读，best-effort）
        item_id, payload = m.group(1), m.group(2)
        try:
            items[item_id] = json.loads(payload)
        except json.JSONDecodeError as exc:
            _fail(f"item {item_id} JSON 非法", str(exc), "修正该行 JSON 后重试")
    return items, body


def _v1_legacy_table_rows(lines, pool):
    """解析 `## 状态总览` 表格行，返回 `{id: fields_dict}`（MIG-01 Scenario 1）。
    只认第一个 `状态总览` 区域（真实语料每文件恰一个）。"""
    specific_field = "priority" if pool == "bug" else "type"
    rows = {}
    for i, line in enumerate(lines):
        if not re.match(r'^##\s+状态总览', line):
            continue
        hdr_idx = None
        for j in range(i + 1, min(len(lines), i + 6)):
            if not lines[j].strip():
                continue
            if _V1_TABLE_HDR_RE.match(lines[j]):
                hdr_idx = j
            break
        if hdr_idx is None:
            continue
        k = hdr_idx + 2
        while k < len(lines) and lines[k].lstrip().startswith("|"):
            m = _V1_ROW_ID_RE.match(lines[k])
            if m:
                cells = [c.strip() for c in lines[k].strip().strip("|").split("|")]
                rows[m.group(1)] = {
                    "module": cells[1] if len(cells) > 1 else "",
                    "summary": cells[2] if len(cells) > 2 else "",
                    specific_field: cells[3] if len(cells) > 3 else None,
                    "status": cells[4] if len(cells) > 4 else "",
                    "change": (
                        cells[6] if len(cells) > 6 and cells[6] not in ("", "-") else None
                    ),
                }
            k += 1
        break
    return rows


def _v1_marker_block_bodies(lines):
    """成对 marker（`<!-- sdflow-issue-block:start/end id=X -->`）之间的原文，去掉 marker
    标签本身（design.md 字段映射表：「marker block 内容 → body 原样搬入（去掉 marker 标签）」）。"""
    bodies = {}
    active = None
    start_idx = None
    for idx, line in enumerate(lines):
        m = _V1_MARKER_RE.match(line.rstrip("\n"))
        if not m:
            continue
        kind, item_id = m.group(1), m.group(2)
        if kind == "start":
            active, start_idx = item_id, idx
        elif kind == "end" and active == item_id:
            bodies[item_id] = "".join(lines[start_idx + 1:idx])
            active, start_idx = None, None
    return bodies


def _v1_heading_block_bodies(lines):
    """`## {ID}: ...` 标题块（含标题行本身）到下一个 `---` 或下一个标题为止的原文
    （legacy-owned item 的 detail section，MIG-01 Scenario 1）。"""
    starts = []
    for i, line in enumerate(lines):
        m = _V1_HEADING_RE.match(line)
        if m:
            starts.append((i, m.group(1)))
    bodies = {}
    for i, item_id in starts:
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "---" or _V1_HEADING_RE.match(lines[j]):
                end = j
                break
        bodies[item_id] = "".join(lines[i:end])
    return bodies


def _v1_pick_body(item_id, marker_blocks, heading_blocks):
    if item_id in marker_blocks:
        return marker_blocks[item_id]
    if item_id in heading_blocks:
        return heading_blocks[item_id]
    return ""


def _v1_parse_file(path, pool):
    """解析单个 v1 文件，返回 `(items, shadowed_count)`；`items` = `{id: entry}`，
    entry = `{"pool", "fields", "body", "file_date", "source_file"}`。

    逐 item 去重（MIG-01）：先收 legacy 表格行，frontmatter overlay 同 ID 覆盖
    （shadow 算法，被覆盖的 legacy 行计入 shadowed_count 但不进入 items）。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    frontmatter_items, body_text = _v1_split_frontmatter(text)
    lines = body_text.splitlines(keepends=True)
    legacy_rows = _v1_legacy_table_rows(lines, pool)
    marker_blocks = _v1_marker_block_bodies(lines)
    heading_blocks = _v1_heading_block_bodies(lines)
    file_date = _v1_file_date(path)

    fm_keys = set(frontmatter_items)
    shadowed = 0
    items = {}
    for row_id, fields in legacy_rows.items():
        if row_id in fm_keys:
            shadowed += 1
            continue
        items[row_id] = {
            "pool": pool, "fields": fields,
            "body": _v1_pick_body(row_id, marker_blocks, heading_blocks),
            "file_date": file_date, "source_file": path,
        }
    for fm_id, fields in frontmatter_items.items():
        items[fm_id] = {
            "pool": pool, "fields": fields,
            "body": _v1_pick_body(fm_id, marker_blocks, heading_blocks),
            "file_date": file_date, "source_file": path,
        }
    return items, shadowed


def _v1_last_terminal_history_match(body, pool):
    """扫 body 里 `> {date} 状态：X → Y（note）` 历史行，返回**最后一条**新状态落在该 pool
    终态集里的 `(date, note)`；none 则无匹配（closed_date/resolved_by 均 best-effort，MIG-02）。"""
    result = None
    for m in _V1_HIST_LINE_RE.finditer(body):
        if m.group("new") in TERMINAL_STATUSES[pool]:
            result = (m.group("date"), m.group("note"))
    return result


def _v1_extract_change_token(note):
    """从历史行的括注文本提取形如 `fix-xxx` 的 change 名（kebab-case，≥2 段）；
    提取不到（如中文散文、无连字符）返回 None（resolved_by 提取不到则 null）。"""
    if not note:
        return None
    m = _V1_CHANGE_TOKEN_RE.match(note.strip())
    return m.group(1) if m else None


def _v1_build_v2_issue(item_id, entry, stats, known_changes=frozenset()):
    """字段映射（design.md 字段映射表）：v1 fields + body → v2 (frontmatter, body)。
    映射失败（status 越出 v2 词表 / 值含 CR/LF/NUL）时 raise，调用方负责跳过。"""
    pool = entry["pool"]
    fields = entry["fields"]
    body = entry["body"]
    file_date = entry["file_date"]
    specific_field = "priority" if pool == "bug" else "type"

    status = fields.get("status")
    if status not in STATUS_VALUES[pool]:
        _fail(
            f"{item_id} status 非法", f"{status!r} 不在 v2 词表 {sorted(STATUS_VALUES[pool])}",
            "人工核对该条历史 status 后手动迁移，或先在 v1 侧修正",
        )

    terminal = status in TERMINAL_STATUSES[pool]
    resolved_by = None
    closed_date = None
    closed_reason = None
    if terminal:
        closed_date = file_date  # best-effort 兜底（design.md：格式不匹配或不存在则取文件日期）
        match = _v1_last_terminal_history_match(body, pool)
        if match is None:
            stats["resolved_by"]["no_history_line"] += 1
        else:
            date_str, note = match
            if date_str and _V1_ISO_DATE_RE.match(date_str):
                closed_date = date_str
            token = _v1_extract_change_token(note)
            if token and (not known_changes or token in known_changes):
                resolved_by = token
                stats["resolved_by"]["matched"] += 1
            else:
                stats["resolved_by"]["note_no_token"] += 1
            if status in ("WONTFIX", "WONTDO") and note:
                closed_reason = note

    module = fields.get("module") or ""
    summary = fields.get("summary") or ""
    specific_value = fields.get(specific_field) or None
    source_change = fields.get("change") or None

    for value, name in (
        (module, "module"), (summary, "summary"), (specific_value, specific_field),
        (source_change, "source_change"), (resolved_by, "resolved_by"),
        (closed_reason, "closed_reason"),
    ):
        _reject_line_unsafe(value, name)

    frontmatter = {
        "id": item_id, "pool": pool, "status": status,
        "priority": specific_value if pool == "bug" else None,
        "type": specific_value if pool == "todo" else None,
        "date": file_date,
        "source_change": source_change,
        "module": module, "summary": summary,
        "resolved_by": resolved_by, "closed_date": closed_date,
        "closed_reason": closed_reason,
    }
    return frontmatter, body


def _v1_planned_batch_notes(root):
    """解析 `batches.md`，返回 `{member_id: [{"key", "plan"}, ...]}`——只含 PLANNED 批次
    （MIG-05）。文件缺失则返回空 dict（batches.md 是可选历史产物）。"""
    path = os.path.join(root, "openspec", "issues", "batches.md")
    notes = {}
    if not os.path.isfile(path):
        return notes
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for m in _V1_BATCH_BLOCK_RE.finditer(text):
        if m.group("status") != "PLANNED":
            continue
        key = m.group("key")
        plan = m.group("plan").strip()
        for raw in m.group("members").split(","):
            member_id = raw.strip()
            if ID_RE.match(member_id):
                notes.setdefault(member_id, []).append({"key": key, "plan": plan})
    return notes


def _v1_id_sort_key(item_id):
    m = ID_RE.match(item_id)
    return (m.group(1), int(m.group(2))) if m else (item_id, 0)


def cmd_migrate(args):
    root = args.root
    stats = {
        "files_scanned": 0, "parse_errors": 0, "shadowed": 0,
        "migrated": 0, "skipped_existing": 0, "mapping_errors": 0,
        "batch_notes_applied": 0,
        "resolved_by": {"matched": 0, "note_no_token": 0, "no_history_line": 0},
    }
    all_items = {}
    for path, pool in _v1_collect_files(root):
        stats["files_scanned"] += 1
        try:
            file_items, shadowed = _v1_parse_file(path, pool)
        except ValueError as exc:
            print(f"WARNING: 跳过不可解析文件 {path}: {exc}", file=sys.stderr)
            stats["parse_errors"] += 1
            continue
        stats["shadowed"] += shadowed
        for item_id, entry in file_items.items():
            if item_id in all_items:
                print(
                    f"WARNING: ID {item_id} 跨文件重复（"
                    f"{all_items[item_id]['source_file']} 与 {path}），保留先出现者",
                    file=sys.stderr,
                )
                continue
            all_items[item_id] = entry

    batch_notes = _v1_planned_batch_notes(root)

    known_changes = set()
    for d in (os.path.join(root, "openspec", "changes"),
              os.path.join(root, "openspec", "changes", "archive")):
        if os.path.isdir(d):
            for e in os.listdir(d):
                if os.path.isdir(os.path.join(d, e)) and not e.startswith("."):
                    known_changes.add(e)
                    stripped = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", e)
                    if stripped != e:
                        known_changes.add(stripped)

    for item_id in sorted(all_items, key=_v1_id_sort_key):
        entry = all_items[item_id]
        try:
            frontmatter, body = _v1_build_v2_issue(item_id, entry, stats, known_changes)
        except ValueError as exc:
            print(f"WARNING: 跳过字段映射失败 {item_id}: {exc}", file=sys.stderr)
            stats["mapping_errors"] += 1
            continue

        pool = frontmatter["pool"]
        terminal = frontmatter["status"] in TERMINAL_STATUSES[pool]
        location = "closed" if terminal else "open"
        fname = f"{item_id}.md"
        if os.path.isfile(os.path.join(_issues_dir(root, "open", pool), fname)) or \
           os.path.isfile(os.path.join(_issues_dir(root, "closed", pool), fname)):
            stats["skipped_existing"] += 1
            continue
        path = os.path.join(_issues_dir(root, location, pool), fname)

        notes = batch_notes.get(item_id)
        if notes:
            if body and not body.endswith("\n"):
                body += "\n"
            for note in notes:
                body += f"\n> [迁移自批次 {note['key']}] 原计划: {note['plan']}\n"
            stats["batch_notes_applied"] += 1

        write_issue(path, frontmatter, body, create=True)
        stats["migrated"] += 1

    cmd_reindex(args)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


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

    sp = sub.add_parser("reopen", help="终态唯一受控逆转换：closed/ 迁回 open/")
    sp.add_argument("--id", required=True)
    sp.add_argument("--reason", required=True, help="reopen 理由（必填）")
    sp.add_argument("--to", default="OPEN", help="非终态目标状态：OPEN（默认）或 PROPOSED")
    sp.set_defaults(func=cmd_reopen)

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

    sm = sub.add_parser("migrate", help="v1（buglist/todolist）→ v2（open/closed）一次性迁移")
    sm.set_defaults(func=cmd_migrate)

    so = sub.add_parser("reorganize", help="flat → pool 子目录一次性迁移（open/T*.md → open/todo/T*.md）")
    so.set_defaults(func=cmd_reorganize)

    args = p.parse_args()
    try:
        args.root = repo_root(args.root)
        args.func(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
