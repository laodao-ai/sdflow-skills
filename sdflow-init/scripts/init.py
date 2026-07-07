#!/usr/bin/env python3
"""init.py — 把 openspec/workflow/ bundle 铺进一个项目（或更新已铺过的项目）。

skill `sdflow-init` 的执行核心。权威源 = 本 skill 的 assets/workflow/（单一源）。
两种模式：
  init   —— 空项目首次铺设：建目录骨架、拷 bundle、从模版生成 config.yaml、注入
           INDEX.md / CLAUDE.md / AGENTS.md 的托管区块。
  update —— 已铺过的项目重拉最新 bundle：覆盖 workflow/ 托管文件、重注入托管区块；
           **不动 config.yaml 的本项目段、不覆盖用户内容**。

确定性操作交脚本（拷贝、建目录、标记区块幂等注入）；需判断的（填 config 的「本项目」段、
合并已存在的 config.yaml）留给模型，见 SKILL.md。

标记区块（HTML 注释包裹，幂等替换；用户勿手改区块内）：
  CLAUDE.md / AGENTS.md : <!-- opsx-init:start --> ... <!-- opsx-init:end -->
  INDEX.md             : <!-- opsx-init:rules:start --> ... <!-- opsx-init:rules:end -->

用法见 `python init.py --help`。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# [T48] 本模块用 f-string，需 Python 3.6+。**版本把关在调用侧**（setup.sh 探测 3.6+ 才喂）：
# 整模块编译先于任何语句执行，f-string 在 py<3.6 上是解析期 SyntaxError——模块内加
# `sys.version_info` 守卫无从拦截自身 parse，故这里只声明契约、不放无功能的假守卫。

try:
    import fcntl  # POSIX 独有；Windows 无 → T49 锁降级为 best-effort 无锁
except ImportError:  # pragma: no cover （沙箱恒 POSIX，Windows 分支无法在此覆盖）
    fcntl = None

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
BUNDLE_SRC = os.path.join(ASSETS, "workflow")
REVIEW_TOOL_SRC = os.path.join(ASSETS, "review-tool")
SNIPPETS = os.path.join(ASSETS, "snippets")

MARK_DOC = ("<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:end -->")
MARK_IDX = ("<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:rules:end -->")

def _find_all_marker_lines(text, token):
    """[T21] 逐行累加 offset，产出 text 中**所有** marker 行的 (start, end) offset。
    「marker 行」= 含 token ∧ lstrip 后以 "<!--" 起。`_find_marker_line` 取其首个作安全
    offset 定位。注：判据尚非 fence-aware（会命中 ``` 代码块内演示的 marker）——多块收敛的
    fence-aware + 配对校验版本已 defer todolist（本仓满是 marker 示例，naive 收敛会劫持注入）。"""
    off = 0
    for line in text.splitlines(keepends=True):
        if token in line and line.lstrip().startswith("<!--"):
            yield off, off + len(line)
        off += len(line)


def _find_marker_line(text, token):
    """按 token 定位**第一个** marker 整行（返回该行起止 offset），找不到返回 None。
    [T21] 逐行累加 offset 定位（经 _find_all_marker_lines），**非** `text.index(line)`
    子串查找——marker 串若在真 marker 行之前以行内嵌入（非行首）出现，text.index 会锚到
    那个 inline 子串位置（错位、破坏区块替换）。"""
    for start, end in _find_all_marker_lines(text, token):
        return start, end
    return None

CORE_DIRS = ["changes", "specs"]  # openspec 核心；buglists/todolists 由各自 recorder skill 首用时建

# 全局 hooks：通用功能，全局安装一次（~/.claude/），跨所有项目生效，不随 per-project bundle 铺设。
HOOKS = [
    {
        "name": "ff0-branch-guard.py",
        "src": os.path.join(ASSETS, "hooks", "ff0-branch-guard.py"),
        "event": "PreToolUse",
        "matcher": "Bash",
        "cmd": 'python3 "$HOME/.claude/hooks/ff0-branch-guard.py"',
    },
]

# 退役 hook 名单（ADR-1）：hook 安装本是「只增不减」，退役一个 hook 时存量安装的
# ~/.claude/settings.json 会留孤儿注册 + ~/.claude/hooks/ 残留脚本 → 之后每次 Bash 触发失败
# hook。retire_hooks() 在 init/update 每次跑时自愈：外科式摘 settings 注册 + 删脚本；
# fresh 安装无残留则全 no-op。后续任何 hook 退役都往这里加名即可。
RETIRED_HOOKS = ["change-review-stub.py"]


# ── 标记区块幂等注入 ─────────────────────────────────────────

def inject(path, start, end, content, header=""):
    """有标记则按 token 定位既有区块（含历史 marker 文案，如旧 skill 名）并原位替换为新
    marker + 新内容；无标记则追加；文件不存在则以 header 起头新建。返回动作描述。

    定位用 token（如 "opsx-init:start"）而非全串精确匹配——marker 文案随 skill 改名演化时
    （如 opsx-project-init → sdflow-init），旧区块仍需被命中替换，而不是被判定"未找到"而追加
    出重复区块。token 从 start/end 的 marker 文案中提取：格式固定为
    "<!-- <token> —— ... -->"（start）/ "<!-- <token> -->"（end），token 即第二个空白分隔词。
    """
    start_token = start.split()[1]
    end_token = end.split()[1]
    block = f"{start}\n{content.rstrip()}\n{end}\n"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        s_loc = _find_marker_line(text, start_token)
        e_loc = _find_marker_line(text, end_token)
        if s_loc and e_loc and s_loc[0] <= e_loc[0]:
            # [T21] 仅替换**第一对** start..end（经安全的逐行 offset 定位，见 _find_marker_line）。
            # 注：多重复托管块只收敛首块（次块残留），是**已知残差**——正确的多块收敛须
            # fence-aware（不误命中 ``` 代码块内演示的 marker）+ start/end 配对校验（不跨孤儿
            # marker 吞用户内容），否则在本仓这类满是 marker 示例的 workflow-doc 仓会劫持注入/
            # 静默丢内容（code-review adv 镜实证 F1/F2）。已 defer todolist，非本轻量批 scope。
            pre = text[:s_loc[0]]
            post = text[e_loc[1]:]
            new = pre + block.rstrip("\n") + "\n" + post.lstrip("\n")
            if not new.endswith("\n"):
                new += "\n"
            action = "更新托管区块"
        else:
            new = text.rstrip("\n") + "\n\n" + block
            action = "追加托管区块"
    else:
        new = (header.rstrip("\n") + "\n\n" if header else "") + block
        action = "新建并写入"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return action


def read_snippet(name):
    with open(os.path.join(SNIPPETS, name), encoding="utf-8") as f:
        return f.read()


# ── bundle 铺设 ──────────────────────────────────────────────

def copy_bundle(root, full=False):
    """R-MRF-1 分层部署：默认只铺 tools/ 子树（规则经全局 canonical 解析，不复制进消费仓）。
    full=True 整 bundle 铺设——仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用。

    非 full 模式收敛性：拷贝前若 dst/tools 已存在则先 rmtree 再 copytree——tools/ 是随
    workflow bundle 托管的子树（update 覆盖刷新语义），不落入"绝不自动删消费仓文件"红线；
    清后拷保收敛，上游删文件不再残留（B2-F4）。full 模式维持 dirs_exist_ok 现状不变。

    非 full 模式排除 tools/tests/：那是 tools/ 脚本（如 trivial_shape.py）的内部 pytest，
    只服务 toolkit 源仓自身开发，铺进消费仓既无用又污染其 pytest 收集（消费仓 `pytest` 会误
    捡进 test_trivial_shape.py）。脚本本体仍随 tools/ 正常部署，只是不带 tests/ 子目录
    （# [impl-review-fix CF-6]）。full 模式（--dev，仅 toolkit 源仓自身用）不排除——dogfood 场景
    就是要连 tests/ 一起刷回 toolkit 源仓工作树。"""
    dst = os.path.join(root, "openspec", "workflow")
    if full:
        shutil.copytree(BUNDLE_SRC, dst, dirs_exist_ok=True)
    else:
        tools_dst = os.path.join(dst, "tools")
        if os.path.isdir(tools_dst):
            shutil.rmtree(tools_dst)
        shutil.copytree(os.path.join(BUNDLE_SRC, "tools"), tools_dst,
                         ignore=shutil.ignore_patterns("tests"))
        # [mlh-p2-anchor-lint] 契约是 tools/anchor_lint.py 的运行时机读依赖（读 lens-metric-enums 块），
        # 须与 tools/ 同批刷新，否则本地 pin 消费仓 update 后「新脚本+旧契约无块」永久 fail-closed。
        contract_src = os.path.join(BUNDLE_SRC, "lens-metric-contract.md")
        if os.path.isfile(contract_src):
            shutil.copy2(contract_src, os.path.join(dst, "lens-metric-contract.md"))
    n = sum(len(fs) for _, _, fs in os.walk(dst))
    return dst, n


RULE_MARKERS = ("workflow.md", "spec-checklists", "code-checklists")


def stale_shadow_warnings(root):
    """反静默守卫·陈旧遮蔽（R-MRF-3）：update 内联为主 + sdflow-maintain 兜底（同款判据）。只告警，绝不删。"""
    warns = []
    wf = os.path.join(root, "openspec", "workflow")
    found = [m for m in RULE_MARKERS if os.path.exists(os.path.join(wf, m))]
    if found:
        warns.append(
            "⚠ openspec/workflow/ 残留规则副本（" + "、".join(found) + "）——遮蔽全局 bundle 且不再被 update 刷新："
            "想跟全局最新 → 手动删净；想 pin 这一版 → 留着（显式逃生口）")
    if os.path.isfile(os.path.join(root, "hack", "checkpoint-commit.sh")):
        warns.append(
            "⚠ hack/checkpoint-commit.sh 为旧版仓内副本（checkpoint 已全局化 → ~/.sdflow/hack/）："
            "本仓无规则副本 → 可删改用全局；若保留本地 workflow.md 副本（pin）且其仍引用仓内路径 → 勿删")
    return warns


def copy_review_tool(root):
    """铺设 review 工具的「服务器根锚」文件：serve.sh + 根 review.html 到 openspec/ 根。

    tools/（engine.js, engine.css, vendor/, review-stub.html）已随 workflow bundle 由
    copy_bundle 铺到 openspec/workflow/tools/（B1 归位）——本函数**不再拷 tools/**。

    为何 serve.sh / 根 review.html 留 openspec/ 根、不进 workflow/：review 工具靠「HTTP
    服务器根 = openspec/」+ 根相对资产路径（/workflow/tools/engine.js）工作；被审内容
    （changes/ specs/ roadmaps/）在 openspec/ 层、在 workflow/ 之上——serve.sh 须从
    openspec/ 起服务才覆盖得到它们，engine.js 从 window.location.pathname 推 scope、根
    review.html 须落 /review.html 才得 scope=""（全树）。故这两个根锚留根，仅工具机械
    （tools/）归 workflow bundle。见 design.md 决策表 B1 / 原则6〔grill-amendment〕。

    根 review.html = openspec/workflow/tools/review-stub.html 模板替换 __PROJECT_NAME__ 为
    项目目录名（该值对一次安装永不变，不重蹈 __SCOPE__ 过时症）。模板本身保持原始未替换
    （作本函数渲染根 review.html 的源模板）。update 覆盖刷新。
    """
    osroot = os.path.join(root, "openspec")

    serve_src = os.path.join(REVIEW_TOOL_SRC, "serve.sh")
    serve_dst = os.path.join(osroot, "serve.sh")
    shutil.copyfile(serve_src, serve_dst)
    shutil.copymode(serve_src, serve_dst)

    stub_path = os.path.join(osroot, "workflow", "tools", "review-stub.html")
    project_name = os.path.basename(os.path.abspath(root))
    with open(stub_path, encoding="utf-8") as f:
        template_text = f.read()
    rendered = template_text.replace("__PROJECT_NAME__", project_name)
    with open(os.path.join(osroot, "review.html"), "w", encoding="utf-8") as f:
        f.write(rendered)

    return 2  # serve.sh + 根 review.html（tools/ 已由 copy_bundle 计入 openspec/workflow/）


def ensure_dirs(root):
    made = []
    for d in CORE_DIRS:
        p = os.path.join(root, "openspec", d)
        if not os.path.isdir(p):
            os.makedirs(p, exist_ok=True)
            open(os.path.join(p, ".gitkeep"), "a").close()
            made.append(f"openspec/{d}/")
    return made


def handle_config(root, mode):
    """init: 缺则从模版生成，存在则报告需合并。update: 不动。返回 (状态, 提示)。"""
    cfg = os.path.join(root, "openspec", "config.yaml")
    tmpl = os.path.join(BUNDLE_SRC, "config.template.yaml")
    if mode == "update":
        return ("skip", "update 不动 config.yaml（如模版有变，模型按需合并通用段/rules）")
    if os.path.exists(cfg):
        return ("exists", "config.yaml 已存在 → 模型合并「通用」context 段 + rules，保留「本项目」段与用户键")
    shutil.copyfile(tmpl, cfg)
    return ("created", "已从 config.template.yaml 生成 config.yaml → 填写「本项目」context 段")


# ── config-lint（mlh-p3-determ-guards Task 2）──────────────────
#
# openspec/config.yaml 结构 fail-closed 校验门：只校验结构（顶层键存在 / 子键归属），
# 不碰内容文案。**手写 stdlib 行级扫描**（follow anchor_lint.py::read_metrics_enabled 范式，
# MUST NOT `import yaml`——本脚本被 symlink 进消费仓，消费仓多数无 PyYAML，import 会
# ImportError 崩溃，与 fail-closed 相悖）。顶层块（model-tiers / metrics）「先探测存在再
# 校验」，块整段缺失一律条件化放行（mlh-p2 假阳教训，memory dogfood-blind-spot-source-config：
# sdflow-init update 从不注入新顶层键，故 100% 存量消费仓 config 无这些块，缺块是正常态、
# 不是违规）；绝不裸 `cfg["k"]["j"]` 式取键，坏了是 KeyError 裸 traceback，不是人可读 reason。

TIER_ALLOWED_SUBKEYS = {"strong", "mid", "light"}
RULES_REQUIRED_SUBKEYS = ("proposal", "specs", "design", "tasks")


def _find_top_level_block(lines, key):
    """定位顶层 `<key>:` 行；返回 (key行索引, 块内容范围终点) 或 None（键整段不存在）。
    「顶层」= 行首即键名（不缩进）；块终点 = 下一处非缩进/非空/非注释行（同 anchor_lint 的
    「至下一顶层键前」口径），中途的空行/注释行跳过不计入终止判据。"""
    start = None
    for i, ln in enumerate(lines):
        if ln.rstrip() == f"{key}:" or ln.startswith(f"{key}:"):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.strip() == "" or ln.strip().startswith("#"):
            continue
        if not ln.startswith((" ", "\t")):
            end = i
            break
    return start, end


def _second_level_keys(lines, start, end):
    """在 [start+1, end) 范围内收集二级子键名（恰 2 空格缩进、非 3+ 空格、以 `:` 结尾的行）。
    3+ 空格缩进的行是子键下的列表项/更深层级，不计入子键集合。"""
    keys = set()
    for ln in lines[start + 1:end]:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if ln.startswith("  ") and not ln.startswith("   ") and ":" in s:
            keys.add(s.split(":", 1)[0].strip())
    return keys


def lint_config(root):
    """校验 <root>/openspec/config.yaml 的结构，返回 reason 字符串列表（空 = 干净）。
    校验项：① 顶层 `schema:` 键存在 ② 顶层 `rules:` 块存在且含 proposal/specs/design/tasks
    四子键（无条件必填） ③ 顶层 `model-tiers:`（若存在）子键 ⊆ {strong,mid,light}
    ④ 顶层 `metrics:`（若存在）`enabled:` 值 ∈ {true,false}。config.yaml 本身缺失/不可读
    单独报一条 reason（不当 KeyError 崩）。"""
    cfg_path = os.path.join(root, "openspec", "config.yaml")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            text = f.read()
    # [impl-review-fix] F2：此前只捕 OSError——非 UTF-8 config.yaml 会让 f.read() 抛
    # UnicodeDecodeError，未被捕获、以裸 traceback 崩溃。补捕获，与本 bundle 范式源
    # anchor_lint.py::read_metrics_enabled / load_enums 的既有 except (OSError,
    # UnicodeDecodeError) 写法对齐（commit 8f1d2bc 已确立的口径，本文件新写时漏跟）。
    except (OSError, UnicodeDecodeError) as e:
        return [f"config.yaml 不可读: {cfg_path}: {e}"]
    lines = text.splitlines()
    reasons = []

    if _find_top_level_block(lines, "schema") is None:
        reasons.append("缺顶层 schema: 键")

    rules_block = _find_top_level_block(lines, "rules")
    if rules_block is None:
        reasons.append("缺顶层 rules: 块")
    else:
        start, end = rules_block
        sub = _second_level_keys(lines, start, end)
        missing = [k for k in RULES_REQUIRED_SUBKEYS if k not in sub]
        if missing:
            reasons.append(f"rules: 缺子键 {missing}（须含 proposal/specs/design/tasks）")

    tiers_block = _find_top_level_block(lines, "model-tiers")  # 条件化：块整段缺失 → 跳过（放行）
    if tiers_block is not None:
        start, end = tiers_block
        sub = _second_level_keys(lines, start, end)
        bad = sorted(sub - TIER_ALLOWED_SUBKEYS)
        if bad:
            reasons.append(f"model-tiers: 子键越域 {bad}（须 ⊆ {{strong,mid,light}}）")

    metrics_block = _find_top_level_block(lines, "metrics")  # 条件化：块整段缺失 → 跳过（放行）
    if metrics_block is not None:
        start, end = metrics_block
        valid = False
        for ln in lines[start + 1:end]:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("enabled:") and s.split(":", 1)[1].strip() in ("true", "false"):
                valid = True
        if not valid:
            reasons.append("metrics: enabled 值非法或缺失（须为 true|false）")

    return reasons


def cmd_config_lint(root):
    """跑 lint_config 并落 stdout/stderr + 退出码：干净 0，违规非零、reason 逐条 stderr。"""
    reasons = lint_config(root)
    if reasons:
        for r in reasons:
            print(f"[config-lint] VIOLATION: {r}", file=sys.stderr)
        return 1
    print("[config-lint] CLEAN", file=sys.stderr)
    return 0


def _git_root_or_dot():
    """config-lint 专用 --root 缺省探测：`git rev-parse --show-toplevel` 探 git 仓根；
    非 git 仓 / 命令失败 → 降级当前目录 "."（M7）。**不复用** init/update/retire-hooks 的
    `default="."`——那三个 mode 的 "." 语义是「就地铺设/操作当前目录」，config-lint 校验的是
    openspec/config.yaml，在 git 仓子目录里跑时应回溯到仓根而非误判"当前子目录没有 openspec/"。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        top = out.stdout.strip()
        return top if top else "."
    except (OSError, subprocess.CalledProcessError):
        return "."


def ensure_global_hook(spec):
    """幂等把单个全局 hook 装好：脚本拷进 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json
    对应 event 的 hooks 列表。spec 形如 HOOKS 里的一项。返回动作描述。
    """
    home_claude = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    acts = []

    hooks_dir = os.path.join(home_claude, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    dst = os.path.join(hooks_dir, spec["name"])
    if not os.path.exists(spec["src"]):
        return f"跳过（hook 源缺失：{spec['src']}）"
    with open(spec["src"], encoding="utf-8") as f:
        new_src = f.read()
    old_src = None
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            old_src = f.read()
    if old_src != new_src:
        shutil.copyfile(spec["src"], dst)
        acts.append("脚本已" + ("更新" if old_src is not None else "安装") + f" {dst}")
    else:
        acts.append("脚本已最新")

    # [F-C] settings 注册走 <settings>.lock（与 deregister 同一把锁）——register×deregister
    # 跨进程并发不再互相 lost-update（否则一进程基于旧 snapshot 写回会复活退役 hook / 丢当前 hook）。
    settings = os.path.join(home_claude, "settings.json")
    lock_fd = _acquire_settings_lock(settings)
    try:
        acts.append(_register_hook_in_settings_locked(settings, spec))
    finally:
        _release_settings_lock(lock_fd)
    return "；".join(acts)


def _register_hook_in_settings_locked(settings, spec):
    """在持 <settings>.lock 下把 spec 幂等注册进 settings.json，返回注册状态描述。
    [F-B] 遍历既有条目用 isinstance 守卫 + `_hook_command`——畸形 settings（非 dict entry /
    非 str command，用户/三方工具可写）不再裸抛 AttributeError/TypeError（原 `entry.get`/
    `h.get`/`name in (... or "")` 会崩，与 _deregister 的 CR-F1 口径不对称，此处对齐）。
    [F-C] 写走共享 _atomic_write_settings（tmp+os.replace，与 deregister 同口径）。"""
    if os.path.exists(settings):
        try:
            with open(settings, encoding="utf-8") as f:
                data = json.load(f)
        except (ValueError, OSError):
            return "跳过注册（~/.claude/settings.json 非合法 JSON，请手动注册）"
        if not isinstance(data, dict):
            return "跳过注册（~/.claude/settings.json 顶层非对象）"
    else:
        data = {}

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks
    event_list = hooks.get(spec["event"])
    if not isinstance(event_list, list):
        event_list = []
        hooks[spec["event"]] = event_list

    for entry in event_list:
        inner = entry.get("hooks") if isinstance(entry, dict) else None
        for h in (inner or []):
            if spec["name"] in _hook_command(h):
                return "已注册（全局）"

    event_list.append({
        "matcher": spec["matcher"],
        "hooks": [{"type": "command", "command": spec["cmd"]}],
    })
    if _atomic_write_settings(settings, data):
        return f"已注册 → ~/.claude/settings.json（{spec['event']}）"
    return "跳过注册（settings.json 写失败，请手动注册）"


def ensure_global_hooks():
    """按 HOOKS 逐个幂等安装，返回多行汇总。"""
    return "\n".join(f"  · {spec['name']}：{ensure_global_hook(spec)}" for spec in HOOKS)


def _home_claude():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def _hook_command(h):
    """安全取一个 hook entry 的 command 字符串：h 非 dict、或 command 非 str（含缺失）
    一律回 ''——让调用方的 `name in ...` 判为不匹配、原样保留。settings.json 用户/三方
    工具可写，畸形条目（非 dict 元素 / 非 str command）不得让反注册抛异常（[impl-review-fix] CR-F1）。"""
    if not isinstance(h, dict):
        return ""
    c = h.get("command")
    return c if isinstance(c, str) else ""


def _acquire_settings_lock(settings):
    """T49：在独立 lockfile `<settings>.lock` 上取 fcntl.flock(LOCK_EX)，串行化整个
    读-改-写-replace 临界区——杜绝并发 deregister「各基于旧内容读→写→replace，一次修改
    被静默覆盖」的 lost-update。lockfile 独立于 settings.json（后者被 os.replace 换 inode，
    锁须挂在不被替换的稳定 inode 上）且**不 unlink**（unlink-while-locked 经典竞态会破坏互斥）。
    fcntl 仅 POSIX——Windows（fcntl 缺失）或加锁失败 → 返回 None，best-effort 降级为无锁
    （保持既有行为、不新增崩溃面，局限：Windows 上并发 lost-update 窗口仍在）。返回持锁 fd 或 None。"""
    if fcntl is None:
        return None
    try:
        fd = os.open(settings + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except OSError:
        os.close(fd)
        return None
    return fd


def _release_settings_lock(fd):
    """释放 _acquire_settings_lock 取得的锁并关 fd（fd 为 None 时 no-op）。
    [F-D] flock(LOCK_UN)/os.close 的 OSError（EBADF/EINTR 等罕见态）一律吞——retire-hooks
    CLI 模式无 run() 的外层 try 兜底，此处裸抛会打断 RETIRED_HOOKS 循环 + 留裸 traceback，
    违「绝不中止、坏则跳过」（fail-safe 与 FB-3 一致）。os.close 恒在 finally 执行。"""
    if fd is None:
        return
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    except OSError:
        pass


def _atomic_write_settings(settings, data):
    """[F-C] 原子写 settings.json（tmp + os.replace）——deregister 与 register 共用同一写口径。
    **须在持 <settings>.lock 下调用**。写成功返回 True；OSError（只读/满盘/权限）→ 不裸抛、
    返回 False（FB-3：绝不中止 retire_hooks 循环 / setup.sh，坏则跳过）。tmp 用固定名
    `<settings>.tmp`，失败残渣下次成功写覆盖消费（唯一名 tempfile 化已 defer todolist）。"""
    try:
        tmp = settings + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, settings)   # 原子替换（POSIX + Windows 同名卷内保证）
    except OSError:
        return False
    return True


def _deregister_hook_in_settings(settings, name):
    """从 settings.json 各 event 列表外科式摘除 command 引用 `name` 脚本的条目：
    entry 内多 hook 时只删匹配的那个、保留兄弟；entry 内 hook 全被删则整条 entry 丢弃；
    保留其余用户/其它 skill 的 hook。改动则回写。坏 JSON / 结构异常一律 fail-safe 跳过。
    返回是否发生了摘除。

    [T49] 整个读-改-写-replace 在 <settings>.lock 的排他 flock 下串行化（并发 lost-update
    收窗）；锁在 POSIX 生效、Windows best-effort 降级无锁。"""
    if not os.path.exists(settings):
        return False
    lock_fd = _acquire_settings_lock(settings)
    try:
        return _deregister_hook_in_settings_locked(settings, name)
    finally:
        _release_settings_lock(lock_fd)


def _deregister_hook_in_settings_locked(settings, name):
    """_deregister_hook_in_settings 的临界区实现（须在持 <settings>.lock 下调用）。"""
    try:
        with open(settings, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return False
    if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
        return False
    changed = False
    for event, event_list in list(data["hooks"].items()):
        if not isinstance(event_list, list):
            continue
        new_list = []
        for entry in event_list:
            inner = entry.get("hooks") if isinstance(entry, dict) else None
            if isinstance(inner, list):
                kept = [h for h in inner if name not in _hook_command(h)]
                if len(kept) != len(inner):
                    changed = True
                    if kept:
                        entry["hooks"] = kept
                        new_list.append(entry)
                    # kept 为空 → 该 entry 仅剩退役 hook，整条丢弃
                else:
                    new_list.append(entry)
            else:
                new_list.append(entry)
        data["hooks"][event] = new_list
    if changed:
        # [impl-review-fix] FB-3：写路径 fail-safe（与读路径一致），走共享 _atomic_write_settings
        # （tmp+os.replace，OSError→False 不裸抛，不打断 retire_hooks 循环 / setup.sh）。
        if not _atomic_write_settings(settings, data):
            return False
    return changed


def retire_hooks():
    """反注册 RETIRED_HOOKS 里的每个退役 hook（自愈存量安装，ADR-1）：
    ① 从 ~/.claude/settings.json 外科式摘除其注册；② 删 ~/.claude/hooks/ 里的脚本。
    幂等、fail-safe（坏 JSON / 缺文件不崩）、fresh 安装无残留则 no-op。返回多行动作汇总。"""
    home_claude = _home_claude()
    settings = os.path.join(home_claude, "settings.json")
    hooks_dir = os.path.join(home_claude, "hooks")
    acts = []
    for name in RETIRED_HOOKS:
        deregistered = _deregister_hook_in_settings(settings, name)
        script = os.path.join(hooks_dir, name)
        removed_file = False
        if os.path.isfile(script):
            try:
                os.remove(script)
                removed_file = True
            except OSError:
                pass
        notes = []
        if deregistered:
            notes.append("摘 settings 注册")
        if removed_file:
            notes.append("删脚本")
        if notes:
            acts.append(f"{name}：" + " + ".join(notes))
    return "\n".join(f"  · {a}" for a in acts) if acts else "  · 无退役 hook 残留"


# ── 主流程 ──────────────────────────────────────────────────

def run(root, mode, dev=False):
    if dev:
        toolkit_root = os.path.realpath(os.path.dirname(SKILL_DIR))
        if os.path.realpath(root) != toolkit_root:
            _die("--dev 仅用于 toolkit 源仓自身（防把整套规则灌进消费仓）；当前 --root 不是本脚本所在仓")

    try:
        osroot = os.path.join(root, "openspec")
        if mode == "init":
            os.makedirs(osroot, exist_ok=True)
        elif not os.path.isdir(osroot):
            _die("openspec/ 不存在——update 需在已铺设的项目里跑；空项目请用 init")

        report = []
        made = ensure_dirs(root)
        if made:
            report.append("建目录：" + " ".join(made))

        dst, n = copy_bundle(root, full=dev)
        dev_suffix = "（--dev 整刷）" if dev else ""
        report.append(f"铺 bundle：openspec/workflow/{dev_suffix}（{n} 文件，{'覆盖' if mode=='update' else '写入'}）")

        n_review = copy_review_tool(root)
        report.append(
            f"铺 review 根锚：openspec/review.html + openspec/serve.sh"
            f"（{n_review} 文件，{'覆盖' if mode=='update' else '写入'}；tools/ 随 bundle 入 openspec/workflow/tools/）"
        )

        report.append("hack 脚本：不再铺进仓（checkpoint 已全局化 → ~/.sdflow/hack/，由 setup.sh 安装）")

        report.append("全局 hooks：\n" + ensure_global_hooks())

        # 退役 hook 反注册（ADR-1）：init 与 update 都跑，自愈存量安装（fresh 则 no-op）。
        report.append("退役 hook 清理：\n" + retire_hooks())

        # init 与 update 都跑：fresh init 无残留自然零告警；老仓误跑 init 不再假绿（B2-F3）。
        for w in stale_shadow_warnings(root):
            report.append(w)

        cstat, cmsg = handle_config(root, mode)
        report.append(f"config.yaml：{cmsg}")

        # INDEX.md 托管区块
        idx = os.path.join(osroot, "INDEX.md")
        a = inject(idx, *MARK_IDX, read_snippet("index-section.md"),
                   header="# OpenSpec Index\n\n本文件是当前仓库 OpenSpec 资产索引。")
        report.append(f"openspec/INDEX.md：{a}")

        # CLAUDE.md / AGENTS.md 托管区块
        sec = read_snippet("claude-section.md")
        for fn in ("CLAUDE.md", "AGENTS.md"):
            p = os.path.join(root, fn)
            a = inject(p, *MARK_DOC, sec,
                       header=f"# {fn.split('.')[0]}\n\n本文件为项目级 AI 指令。")
            report.append(f"{fn}：{a}")
    except (OSError, shutil.Error) as e:
        _die(f"文件系统操作失败：{e}")

    print(f"✓ sdflow-init {mode} 完成 @ {os.path.abspath(root)}\n")
    for r in report:
        print("  - " + r)
    if cstat in ("created", "exists"):
        print("\n下一步（模型/人工）：")
        if cstat == "created":
            print("  · 编辑 openspec/config.yaml 的「## 本项目」context 段，填本项目 tech stack/约定")
        else:
            print("  · 合并 openspec/config.yaml：把模版的「通用」context 段 + rules 并入，保留你的「本项目」段")
        print("  · 安装配套 skill：bash ~/.skills/sdflow-skills/setup.sh（/sdflow-spec-review /sdflow-code-review /sdflow-done）")


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="把 openspec/workflow bundle 铺进项目")
    p.add_argument("mode", choices=["init", "update", "retire-hooks", "config-lint"],
                   help="init=首次铺设 / update=重拉最新 bundle / retire-hooks=只反注册退役 hook（自愈，"
                        "不碰 openspec/） / config-lint=校验 openspec/config.yaml 结构（fail-closed）")
    p.add_argument("--root", default=None,
                   help="目标项目根（init/update/retire-hooks 默认当前目录；config-lint 缺省探 git 仓根，"
                        "非 git 仓降级当前目录）")
    p.add_argument("--dev", action="store_true",
                   help="update 专用：整 bundle 刷新（toolkit 源仓 dogfood 用，消费仓勿用）")
    args = p.parse_args()
    if args.mode == "config-lint":         # 早分支：mode 第 4 值，不引入 add_subparsers 重构
        root = args.root if args.root is not None else _git_root_or_dot()
        sys.exit(cmd_config_lint(root))
    if args.mode == "retire-hooks":       # A4: 早分支，先于 osroot/dev——只自愈全局 hook，与项目无关
        print("退役 hook 清理：\n" + retire_hooks())
        return
    if args.dev and args.mode != "update":
        _die("--dev 仅配 update 使用")
    run(args.root if args.root is not None else ".", args.mode, dev=args.dev)


if __name__ == "__main__":
    main()
