#!/usr/bin/env python3
"""init.py — 把 openspec/workflow/ bundle 铺进一个项目（或更新已铺过的项目）。

skill `opsx-project-init` 的执行核心。权威源 = 本 skill 的 assets/workflow/（单一源）。
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
HACK_SRC = os.path.join(ASSETS, "hack")
SNIPPETS = os.path.join(ASSETS, "snippets")

MARK_DOC = ("<!-- opsx-init:start —— 由 opsx-project-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:end -->")
MARK_IDX = ("<!-- opsx-init:rules:start —— 由 opsx-project-init 维护，勿手改本区块 -->",
            "<!-- opsx-init:rules:end -->")

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
    {
        "name": "change-review-stub.py",
        "src": os.path.join(ASSETS, "hooks", "change-review-stub.py"),
        "event": "PostToolUse",
        "matcher": "Bash",
        "cmd": 'python3 "$HOME/.claude/hooks/change-review-stub.py"',
    },
]


# ── 标记区块幂等注入 ─────────────────────────────────────────

def inject(path, start, end, content, header=""):
    """有标记则替换标记间内容；无标记则追加；文件不存在则以 header 起头新建。返回动作描述。"""
    block = f"{start}\n{content.rstrip()}\n{end}\n"
    if os.path.exists(path):
        text = open(path, encoding="utf-8").read()
        if start in text and end in text:
            pre = text[:text.index(start)]
            post = text[text.index(end) + len(end):]
            new = pre + block.rstrip("\n") + post.lstrip("\n")
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

def copy_bundle(root):
    dst = os.path.join(root, "openspec", "workflow")
    shutil.copytree(BUNDLE_SRC, dst, dirs_exist_ok=True)
    n = sum(len(fs) for _, _, fs in os.walk(dst))
    return dst, n


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
    （供 change-review-stub.py / gen_review_stub.py 两个生产者读作源）。update 覆盖刷新。
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


def copy_hack(root):
    """铺设 hack/ 工作流脚本（checkpoint-commit.sh 等）到项目 repo 根 hack/。
    源 = assets/hack/*.sh（工作流「过场提交」等自动化脚本，随 bundle 部署，供 step prompt 调用）。
    update 模式覆盖刷新（托管内容，与 copy_bundle 同款语义；用户勿手改，要改改 assets/hack/ 再 update）。
    保留可执行权限。返回铺设的文件数（源目录不存在则 0）。
    """
    if not os.path.isdir(HACK_SRC):
        return 0
    dst_dir = os.path.join(root, "hack")
    os.makedirs(dst_dir, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(HACK_SRC)):
        src = os.path.join(HACK_SRC, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dst_dir, name)
        shutil.copyfile(src, dst)
        shutil.copymode(src, dst)
        n += 1
    return n


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
    tmpl = os.path.join(root, "openspec", "workflow", "config.template.yaml")
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


# ── 主流程 ──────────────────────────────────────────────────

def run(root, mode):
    osroot = os.path.join(root, "openspec")
    if mode == "init":
        os.makedirs(osroot, exist_ok=True)
    elif not os.path.isdir(osroot):
        _die("openspec/ 不存在——update 需在已铺设的项目里跑；空项目请用 init")

    report = []
    made = ensure_dirs(root)
    if made:
        report.append("建目录：" + " ".join(made))

    dst, n = copy_bundle(root)
    report.append(f"铺 bundle：openspec/workflow/（{n} 文件，{'覆盖' if mode=='update' else '写入'}）")

    n_review = copy_review_tool(root)
    report.append(
        f"铺 review 根锚：openspec/review.html + openspec/serve.sh"
        f"（{n_review} 文件，{'覆盖' if mode=='update' else '写入'}；tools/ 随 bundle 入 openspec/workflow/tools/）"
    )

    n_hack = copy_hack(root)
    if n_hack:
        report.append(
            f"铺 hack 脚本：hack/（{n_hack} 文件，{'覆盖' if mode=='update' else '写入'}；含 checkpoint-commit.sh）"
        )

    report.append("全局 hooks：\n" + ensure_global_hooks())

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

    print(f"✓ opsx-project-init {mode} 完成 @ {os.path.abspath(root)}\n")
    for r in report:
        print("  - " + r)
    if cstat in ("created", "exists"):
        print("\n下一步（模型/人工）：")
        if cstat == "created":
            print("  · 编辑 openspec/config.yaml 的「## 本项目」context 段，填本项目 tech stack/约定")
        else:
            print("  · 合并 openspec/config.yaml：把模版的「通用」context 段 + rules 并入，保留你的「本项目」段")
        print("  · 安装配套 skill：bash ~/.skills/laodao-skills/setup.sh（/spec-review /impl-review /opsx-done）")


def _die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="把 openspec/workflow bundle 铺进项目")
    p.add_argument("mode", choices=["init", "update"], help="init=首次铺设 / update=重拉最新 bundle")
    p.add_argument("--root", default=".", help="目标项目根（默认当前目录）")
    args = p.parse_args()
    run(args.root, args.mode)


if __name__ == "__main__":
    main()
