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
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL_DIR, "assets")
BUNDLE_SRC = os.path.join(ASSETS, "workflow")
REVIEW_TOOL_SRC = os.path.join(ASSETS, "review-tool")
SNIPPETS = os.path.join(ASSETS, "snippets")

MARK_DOC = ("<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:end -->")
MARK_IDX = ("<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:rules:end -->")

def _find_marker_line(text, token):
    """按 token 定位 marker 整行（返回该行起止 offset），找不到返回 None。"""
    for line in text.splitlines(keepends=True):
        if token in line and line.lstrip().startswith("<!--"):
            start = text.index(line)
            return start, start + len(line)
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
        text = open(path, encoding="utf-8").read()
        s_loc = _find_marker_line(text, start_token)
        e_loc = _find_marker_line(text, end_token)
        if s_loc and e_loc and s_loc[0] <= e_loc[0]:
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
    return open(os.path.join(SNIPPETS, name), encoding="utf-8").read()


# ── bundle 铺设 ──────────────────────────────────────────────

def copy_bundle(root, full=False):
    """R-MRF-1 分层部署：默认只铺 tools/ 子树（规则经全局 canonical 解析，不复制进消费仓）。
    full=True 整 bundle 铺设——仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用。

    非 full 模式收敛性：拷贝前若 dst/tools 已存在则先 rmtree 再 copytree——tools/ 是随
    workflow bundle 托管的子树（update 覆盖刷新语义），不落入"绝不自动删消费仓文件"红线；
    清后拷保收敛，上游删文件不再残留（B2-F4）。full 模式维持 dirs_exist_ok 现状不变。"""
    dst = os.path.join(root, "openspec", "workflow")
    if full:
        shutil.copytree(BUNDLE_SRC, dst, dirs_exist_ok=True)
    else:
        tools_dst = os.path.join(dst, "tools")
        if os.path.isdir(tools_dst):
            shutil.rmtree(tools_dst)
        shutil.copytree(os.path.join(BUNDLE_SRC, "tools"), tools_dst)
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
    template_text = open(stub_path, encoding="utf-8").read()
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
    new_src = open(spec["src"], encoding="utf-8").read()
    old_src = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
    if old_src != new_src:
        shutil.copyfile(spec["src"], dst)
        acts.append("脚本已" + ("更新" if old_src is not None else "安装") + f" {dst}")
    else:
        acts.append("脚本已最新")

    settings = os.path.join(home_claude, "settings.json")
    if os.path.exists(settings):
        try:
            data = json.load(open(settings, encoding="utf-8"))
        except (ValueError, OSError):
            return "脚本已就位；跳过注册（~/.claude/settings.json 非合法 JSON，请手动注册）"
        if not isinstance(data, dict):
            return "脚本已就位；跳过注册（~/.claude/settings.json 顶层非对象）"
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
        for h in (entry.get("hooks") or []):
            if spec["name"] in (h.get("command") or ""):
                acts.append("已注册（全局）")
                return "；".join(acts)

    event_list.append({
        "matcher": spec["matcher"],
        "hooks": [{"type": "command", "command": spec["cmd"]}],
    })
    with open(settings, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    acts.append(f"已注册 → ~/.claude/settings.json（{spec['event']}）")
    return "；".join(acts)


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


def _deregister_hook_in_settings(settings, name):
    """从 settings.json 各 event 列表外科式摘除 command 引用 `name` 脚本的条目：
    entry 内多 hook 时只删匹配的那个、保留兄弟；entry 内 hook 全被删则整条 entry 丢弃；
    保留其余用户/其它 skill 的 hook。改动则回写。坏 JSON / 结构异常一律 fail-safe 跳过。
    返回是否发生了摘除。"""
    if not os.path.exists(settings):
        return False
    try:
        data = json.load(open(settings, encoding="utf-8"))
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
        tmp = settings + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, settings)   # 原子替换（POSIX + Windows 同名卷内保证）
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
    p.add_argument("mode", choices=["init", "update", "retire-hooks"],
                   help="init=首次铺设 / update=重拉最新 bundle / retire-hooks=只反注册退役 hook（自愈，不碰 openspec/）")
    p.add_argument("--root", default=".", help="目标项目根（默认当前目录）")
    p.add_argument("--dev", action="store_true",
                   help="update 专用：整 bundle 刷新（toolkit 源仓 dogfood 用，消费仓勿用）")
    args = p.parse_args()
    if args.mode == "retire-hooks":       # A4: 早分支，先于 osroot/dev——只自愈全局 hook，与项目无关
        print("退役 hook 清理：\n" + retire_hooks())
        return
    if args.dev and args.mode != "update":
        _die("--dev 仅配 update 使用")
    run(args.root, args.mode, dev=args.dev)


if __name__ == "__main__":
    main()
