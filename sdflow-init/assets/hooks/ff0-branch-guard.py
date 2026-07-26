#!/usr/bin/env python3
"""FF-0 branch guard —— PreToolUse hook（硬拦在受保护分支上创建 OpenSpec 变更）。

为什么挂在 CLI 这层：/opsx:new、/opsx:propose、/opsx:ff、/opsx:onboard、/sdflow-spec
（分支 A，相位 B ③ 建 change 目录）是各自独立的 workflow，但**全都殊途同归调同一条命令
`openspec new change`** 来 scaffold 变更。故只需拦这一条 Bash 命令，即覆盖所有「创建变更」
入口，无需逐个 skill 拦 —— 分支 A 与分支 B 同样受本守卫管辖，没有哪条入口能绕过。

行为（FF-0 三分支判定，与 workflow/ff-generation-constraints.md §FF-0 同一条规则）：
  · 仅对 Bash 工具、且命令实际执行 `openspec new change` 时介入。
  · 当前在受保护分支（master / main / 该仓的默认分支）→ deny，提示先
    `git checkout -b feat/<change>`。**这一支没有逃生口**（见下）。
  · 已在 `feat/<该 change>` → 放行（真幂等，FF-0 满足）。
  · 在【其它】feature 分支 → deny，要求先问人（从当前切出 / 回 base 切出 / 就地继续）。
    人拍板「就地继续」后**分两步**敲：先单独 `touch <仓根>/openspec/.ff0-ack`，**再重跑**
    `openspec new change <name>`（一次性哨兵，守卫读到即删）。⚠️ 该 ack 是给【人】用的
    逃生口 —— 模型 MUST NOT 自行 touch 它绕过本守卫。
  · 任何解析/探测异常、或判不出当前在哪个分支（detached HEAD 等）→ 放行
    （fail-open，绝不因守卫自身故障阻断正常工作）。

【为什么受保护集不能写死 {main, master}】
规则文本（ff-generation-constraints.md §FF-0）写的是「main / master / **默认分支**」。
写死两个名字 ⇒ 默认分支叫 `trunk` / `develop` 的仓里，默认分支会被**误分类成分支③**，
而分支③**有** ack 逃生口、分支①**没有** ⇒ misclassify 直接等于给「在默认分支上建
change」开了后门。故默认分支须探测（best-effort，取不到就退回 {main, master}）。

【逃生口 = 一次性哨兵文件，MUST NOT 从命令串里认口令】（基准 5：无界语法面别手搓）
判据是「仓根下 `openspec/.ff0-ack` 在不在、且够新」——一个**有界**的语义面（存在性 + 一个
时间差），守卫读到即 `os.remove` 消费掉，故**放行 ⇔ 这一次成功消费掉了一个未过期的哨兵**。
🔴 MUST NOT 退回「从命令串里认口令」：deny 文案必然把逃生口原样回传给模型，判据一旦落在命令串上，
「这段文字是命令还是注释 / 在不在命令起始位置」就是**解析 shell**——而 shell 的语法面无界，
每堵一种形态就会冒出下一种（行尾注释 → 行首注释 → …），补丁循环不收敛。

【逃生口必须是两步，MUST NOT 写成一条 `touch … && openspec …`】
PreToolUse 在命令**执行前**判定 ⇒ 判定发生时 touch 还没跑、哨兵还不存在 ⇒ 本守卫会把这条
一行命令连同 touch 一起 deny，唯一合规出路变成死循环。故 deny 文案分两条给：
先单独 `touch <token>`（不含 `openspec new change`，本守卫不触发），**再重跑**创建命令。

【残留令牌是真实的绕过口 —— 如实写明，只做有界压缩】
人若在**自己的终端**里敲 `openspec new change`（本 hook 根本不触发），哨兵**永不被消费**，
会原样留在盘上，下一次任意「其它 feature 分支」调用就被它静默放行一次。故哨兵带
`ACK_TTL_SECONDS` 的**有界时效**：超窗即视为失效**并顺手删除**（自愈残留），把「常驻绕过口」
压成一个短窗口。窗口内的残留仍是真洞，本守卫 MUST NOT 声称堵死它（见信任级别）。
⚠️ 窗口长度**只在 `ACK_TTL_SECONDS` 一处**给出，deny 文案按 `// 60` 自报分钟数；
散文（含本 docstring）MUST NOT 手抄一份数字——那是与常量分叉、改常量不会红的第二份口径。
配套：`openspec/.ff0-ack` 已进 canonical runtime gitignore（`assets/snippets/runtime-gitignore.txt`），
防 `checkpoint-commit.sh` 的无条件 `git add -A` 把残留令牌提交入库、让每个 clone 都带一个。

**信任级别（如实写明，MUST NOT 声称它是安全边界）**：哨兵和口令一样**分不出人和模型**——
模型同样能 `touch` 它。它买到的只有两件事：①「顺手引用一次 deny 文案就绕过」变成
**一次独立的、可在 transcript 里审计的有意动作**；② 消灭了那个无界解析面。
真正的防线是纪律 + review，不是本 hook。

认不出 ack ⇒ 分支③的 deny 照常成立（deny 文案里就写着该敲的确切命令），
不是 fail-open 的适用场景 —— fail-open 管的是「探测不出上下文」，不是「人没拍板」。

【为什么「取不到 change 名」也放行】（基准 5：无界语法面别手搓）
shell 命令行的语法面是无界的（管道、环境变量、别名、嵌套引号…）。本守卫只认
`openspec new change <bare|'quoted'|"quoted">` 这一种【有界】形态；认不出就放行，
而不是猜。fail-open 是既有纪律：守卫拿不准时不挡人干活，规则的文档层与 review 兜底。

铺设/注册：全局装于 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json 的 PreToolUse.Bash
          （通用功能，跨项目生效；非 openspec 项目里命令不匹配即放行）。
"""
import json
import os
import re
import subprocess
import sys
import time

# 受保护分支的**固定**部分；实际受保护集 = 本集合 ∪ {探测到的默认分支}（见 protected_branches）。
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

# 人拍板「就地继续」后的逃生口：仓根下的一次性哨兵文件，**只放行「其它 feature 分支」这一支**
# （分支③）。判据是「文件在不在」，与命令串无关 —— 见模块 docstring。
ACK_FILE = os.path.join("openspec", ".ff0-ack")

# 哨兵的**有界时效**（秒），**全仓唯一的窗口长度出口**（deny 文案按 `// 60` 自报分钟数）。
# 人 touch 完立刻重跑命令是秒级动作，故这里取的是一个极宽裕的上界。
# 它买到的是「残留令牌从常驻变成一个短窗口」——见模块 docstring「残留令牌是真实的绕过口」。
ACK_TTL_SECONDS = 600


def _git(cwd: str, *args: str) -> str:
    """跑一条 git 命令，返回 stdout（strip 过）；失败/异常一律返回空串。"""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd or ".",
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def current_branch(cwd: str) -> str:
    """返回 cwd 所在 git 仓库的当前分支名；**判不出分支时返回空串**。

    `git rev-parse --abbrev-ref HEAD` 在 detached HEAD 下返回字面量 `HEAD`
    （worktree / bisect / tag checkout 都会命中）——那不是分支名，一律归为
    「判不出」，交调用方 fail-open。
    """
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    return "" if branch == "HEAD" else branch


def default_branch(cwd: str) -> str:
    """best-effort 探测该仓的默认分支名；探测不到返回空串。

    两个信号，按可靠度降序（都取不到 → 调用方退回固定的 {main, master}）：
      ① `refs/remotes/origin/HEAD` —— `git clone` 时由 git 自己写入，是**这个仓**
         的远端认的默认分支，最权威。
      ② `init.defaultBranch` —— 本地 `git init` 出来的仓没有 ①；这条是次优信号
         （严格说它是「新建仓用什么名」，多为全局配置，与本仓实际默认分支高度相关
         但非等价）。误判方向是「多保护一个分支名」，而受保护分支的 deny 文案会明确
         告诉人该敲什么，代价可接受。
    """
    head = _git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head.startswith("origin/") and len(head) > len("origin/"):
        return head[len("origin/"):]
    return _git(cwd, "config", "--get", "init.defaultBranch")


def repo_root(cwd: str) -> str:
    """cwd 所在 git 工作树的根；取不到返回空串。哨兵锚仓根，不锚 cwd（人可能在子目录里跑）。"""
    return _git(cwd, "rev-parse", "--show-toplevel")


def consume_ack(root: str) -> bool:
    """一次性哨兵：存在、**且 mtime 在 ACK_TTL_SECONDS 窗口内** ⇒ 消费（删除）并返回 True。

    三种情况返回 False：不存在 / 删不掉（是目录、无权限）/ **已过期**。
    ⚠️ 过期的哨兵**照样删掉**——残留令牌本身就是绕过口（人在自己终端跑 openspec 时哨兵
    永不被消费），顺手清掉它比留着强；只是这一次不放行。

    ⚠️ 时效比较 MUST 是**双边**的：`(now - mtime) <= TTL` 单边式在 mtime 落在**未来**时
    恒真 ⇒ 哨兵永不过期，窗口退回常驻后门。未来 mtime 不需要恶意就会出现（系统时钟回拨、
    从备份/归档恢复保留原 mtime、`rsync -t` 从一台钟更快的机器带回）。故判据是
    `0 <= age <= TTL`：未来 mtime 与超窗一样，视为失效并顺手删除。
    """
    if not root:
        return False
    path = os.path.join(root, ACK_FILE)
    try:
        mtime = os.stat(path).st_mtime
    except OSError:  # 不存在 / 取不到 —— 「没拍板」
        return False
    age = time.time() - mtime
    fresh = 0 <= age <= ACK_TTL_SECONDS
    try:
        os.remove(path)
    except OSError:  # 是目录 / 无权限 —— 删不掉就不放行（否则它不再是一次性的）
        return False
    return fresh


def protected_branches(cwd: str) -> set:
    """固定受保护集 ∪ 探测到的默认分支（规则文本：main / master / 默认分支）。"""
    detected = default_branch(cwd)
    return PROTECTED_BRANCHES | ({detected} if detected else set())


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

    cwd = payload.get("cwd") or "."
    branch = current_branch(cwd)
    if not branch:
        sys.exit(0)  # 探测不到分支 / detached HEAD → 放行（fail-open）

    # 分支①：受保护分支（含该仓的默认分支）→ deny。**本支无 ack 逃生口**。
    if branch in protected_branches(cwd):
        deny(
            f"FF-0 守卫：当前在受保护分支 `{branch}`，禁止在此创建 OpenSpec 变更。\n"
            "请先开 feature 分支再重试：\n"
            "  git checkout -b feat/<change-name>\n"
            "（FF-0：变更工件须随 feature 分支落地，merge 后 PR 完整呈现设计→实现故事）"
        )

    name = change_name(command)
    if not name:
        sys.exit(0)  # 认不出 change 名 → 无从区分②③ → 放行（fail-open）

    # 分支②：已在 feat/{本 change} → 放行（真幂等）。
    if branch == f"feat/{name}":
        sys.exit(0)

    # 分支③：在其它 feature 分支 → deny，要求先问人（stacking 不是默认动作）。
    root = repo_root(cwd)
    if consume_ack(root):
        sys.exit(0)  # 人已拍板「就地继续」（哨兵已被消费掉，只对这一次生效）

    token = os.path.join(root, ACK_FILE) if root else ACK_FILE
    deny(
        f"FF-0 守卫：当前在 feature 分支 `{branch}`，而你要创建的是另一个变更 `{name}`。\n"
        "MUST NOT 因「已经在 feature 分支上」就直接建——那会把两个 change 的工件与 "
        "checkpoint 交错落进同一段历史（stacking）。\n"
        "先停下问人，三选一：\n"
        f"  a) 从当前分支切出：git checkout -b feat/{name}\n"
        f"  b) 回 base 再切出：git checkout <base> && git checkout -b feat/{name}\n"
        "  c) 就地继续 —— 人明确拍板后，由**人**分两步敲（本守卫在命令执行【前】判定，\n"
        "     写成 `touch … && openspec …` 一条会连同 touch 一起被 deny）：\n"
        f"       touch {token}\n"
        f"     然后重跑：\n"
        f"       openspec new change {name}\n"
        f"     （该哨兵用后即焚：守卫读到就删，只对下一次调用生效；\n"
        f"       且 {ACK_TTL_SECONDS // 60} 分钟内未被消费即失效并自动删除）\n"
        "⚠️ c) 只能由人决定 —— 模型 MUST NOT 自行 touch 哨兵绕过本守卫。"
    )


if __name__ == "__main__":
    main()
