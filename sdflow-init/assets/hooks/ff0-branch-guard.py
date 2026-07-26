#!/usr/bin/env python3
"""FF-0 branch guard —— PreToolUse hook（硬拦在受保护分支上创建 OpenSpec 变更）。

为什么挂在 CLI 这层：/opsx:new、/opsx:propose、/opsx:ff、/opsx:onboard 是各自独立的
workflow，但**全都殊途同归调同一条命令 `openspec new change`** 来 scaffold 变更。
故只需拦这一条 Bash 命令，即覆盖所有「创建变更」入口，无需逐个 skill 拦。

行为（FF-0 三分支判定，与 workflow/ff-generation-constraints.md §FF-0 同一条规则）：
  · 仅对 Bash 工具、且命令实际执行 `openspec new change` 时介入。
  · 当前在受保护分支（master/main）→ deny，提示先 `git checkout -b feat/<change>`。
  · 已在 `feat/<该 change>` → 放行（真幂等，FF-0 满足）。
  · 在【其它】feature 分支 → deny，要求先问人（从当前切出 / 回 base 切出 / 就地继续）。
    人拍板「就地继续」后，用 `SDFLOW_FF0_ACK=1 openspec new change …` 重跑即放行。
    ⚠️ 该 ack 是给【人】用的逃生口 —— 模型 MUST NOT 自行加上它绕过本守卫。
  · 任何解析/探测异常 → 放行（fail-open，绝不因守卫自身故障阻断正常工作）。

【为什么「取不到 change 名」也放行】（基准 5：无界语法面别手搓）
shell 命令行的语法面是无界的（管道、环境变量、别名、嵌套引号…）。本守卫只认
`openspec new change <bare|'quoted'|"quoted">` 这一种【有界】形态；认不出就放行，
而不是猜。fail-open 是既有纪律：守卫拿不准时不挡人干活，规则的文档层与 review 兜底。

铺设/注册：全局装于 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json 的 PreToolUse.Bash
          （通用功能，跨项目生效；非 openspec 项目里命令不匹配即放行）。
"""
import json
import re
import subprocess
import sys

# 受保护分支：在其上禁止创建变更（变更工件须落在 feature 分支）。
PROTECTED_BRANCHES = {"master", "main"}

# 匹配实际执行的 `openspec new change`（容忍多空格 / 命令前有路径前缀 / 子命令顺序）。
NEW_CHANGE_RE = re.compile(r"openspec\s+(?:new\s+change|change\s+new)\b")

# 从命令里取 change 名：只认紧跟其后的一个 bare / 单引号 / 双引号 token（有界形态）。
# 取不到 → 认不出这是不是「本 change 的分支」→ fail-open 放行（见模块 docstring）。
CHANGE_NAME_RE = re.compile(
    r"openspec\s+(?:new\s+change|change\s+new)\s+"
    r"(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z0-9._-]+))"
)

# change 名的合法字符集（它要当目录名用）。抽出来的 token 不符即视为「认不出」→ 放行：
# 带 `$`/反引号/通配符的 token 是 shell 待展开的东西，本守卫不展开、也不猜。
CHANGE_NAME_OK_RE = re.compile(r"\A[A-Za-z0-9._-]+\Z")

# 人拍板「就地继续」后的逃生口：命令前缀带上它即放行「其它 feature 分支」这一支。
ACK_RE = re.compile(r"\bSDFLOW_FF0_ACK=1\b")


def current_branch(cwd: str) -> str:
    """返回 cwd 所在 git 仓库的当前分支名；探测失败返回空串。"""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd or ".",
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def deny(reason: str) -> None:
    """输出 PreToolUse deny 决策并退出（reason 回传给模型）。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def change_name(command: str) -> str:
    """从命令里取 change 名；取不到返回空串（→ 调用方 fail-open）。"""
    m = CHANGE_NAME_RE.search(command)
    if not m:
        return ""
    name = next((g for g in m.groups() if g), "")
    return name if CHANGE_NAME_OK_RE.match(name) else ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 读不到/解析失败 → 放行

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "") or ""
    if not NEW_CHANGE_RE.search(command):
        sys.exit(0)  # 不是创建变更的命令 → 放行

    branch = current_branch(payload.get("cwd") or ".")

    # 分支①：受保护分支 → deny。
    if branch in PROTECTED_BRANCHES:
        deny(
            f"FF-0 守卫：当前在受保护分支 `{branch}`，禁止在此创建 OpenSpec 变更。\n"
            "请先开 feature 分支再重试：\n"
            "  git checkout -b feat/<change-name>\n"
            "（FF-0：变更工件须随 feature 分支落地，merge 后 PR 完整呈现设计→实现故事）"
        )

    if not branch:
        sys.exit(0)  # 探测不到分支 → 放行（fail-open）

    name = change_name(command)
    if not name:
        sys.exit(0)  # 认不出 change 名 → 无从区分②③ → 放行（fail-open）

    # 分支②：已在 feat/{本 change} → 放行（真幂等）。
    if branch == f"feat/{name}":
        sys.exit(0)

    # 分支③：在其它 feature 分支 → deny，要求先问人（stacking 不是默认动作）。
    if ACK_RE.search(command):
        sys.exit(0)  # 人已拍板「就地继续」

    deny(
        f"FF-0 守卫：当前在 feature 分支 `{branch}`，而你要创建的是另一个变更 `{name}`。\n"
        "MUST NOT 因「已经在 feature 分支上」就直接建——那会把两个 change 的工件与 "
        "checkpoint 交错落进同一段历史（stacking）。\n"
        "先停下问人，三选一：\n"
        f"  a) 从当前分支切出：git checkout -b feat/{name}\n"
        f"  b) 回 base 再切出：git checkout <base> && git checkout -b feat/{name}\n"
        "  c) 就地继续（人明确拍板后，用 "
        f"`SDFLOW_FF0_ACK=1 openspec new change {name}` 重跑）\n"
        "⚠️ c) 的 ack 只能由人决定 —— 模型 MUST NOT 自行加上它绕过本守卫。"
    )


if __name__ == "__main__":
    main()
