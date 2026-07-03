#!/usr/bin/env python3
"""Change review-stub hook —— PostToolUse hook（change 目录建好后补一份 review.html）。

为什么挂在 CLI 这层：/opsx:new、/opsx:propose、/opsx:ff、/opsx:onboard 都殊途同归调用同一条命令
`openspec new change <name>` 来 scaffold 变更（这几个 skill 本身不在本仓库）。只需拦这一条 Bash
命令，即覆盖所有「创建变更」入口，参见 ff0-branch-guard.py 的同一思路（那个拦 PreToolUse 做 deny，
这个挂 PostToolUse 做补文件，互不冲突）。

行为：
  · 仅对 Bash 工具、且命令实际执行 `openspec new change <name>` 时介入（PostToolUse：命令已跑完）。
  · 解析出 <name>；若 openspec/changes/<name>/ 不存在（如被 FF-0 拦下、或命令本身失败）→ 静默放行。
  · 若项目根 openspec/review.html 或 openspec/workflow/tools/review-stub.html 不存在（还没跑过
    opsx-project-init）→ 静默放行，不强迫铺设顺序。
  · 否则读模板、替换 __PROJECT_NAME__（项目根目录名，对一次安装永不变，故不重蹈 __SCOPE__ 的
    过时症）为项目名后写入 openspec/changes/<name>/review.html（幂等：内容已一致则跳过写入）。
    目录 scope 不再靠模板占位符固化，而由 engine.js 在加载时从 window.location.pathname 推导，
    故本 hook 只需保证目录里有一份与「项目名已替换」的模板内容一致的 review.html。
  · 任何异常 → 静默放行（fail-open，绝不因本 hook 故障阻断正常工作）。

铺设/注册：全局装于 ~/.claude/hooks/ + 注册进 ~/.claude/settings.json 的 PostToolUse.Bash
          （opsx-project-init 的 ensure_global_hooks() 负责，见 scripts/init.py 的 HOOKS 列表）。
"""
import json
import os
import re
import sys

NEW_CHANGE_RE = re.compile(r"openspec\s+(?:new\s+change|change\s+new)\s+(\S+)")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "") or ""
    m = NEW_CHANGE_RE.search(command)
    if not m:
        sys.exit(0)

    name = m.group(1).strip().strip("'\"")
    cwd = payload.get("cwd") or "."

    change_dir = os.path.join(cwd, "openspec", "changes", name)
    if not os.path.isdir(change_dir):
        sys.exit(0)  # 命令没真正建出目录（被拦 / 失败）→ 放行

    stub_template_path = os.path.join(cwd, "openspec", "workflow", "tools", "review-stub.html")
    root_review_path = os.path.join(cwd, "openspec", "review.html")
    if not (os.path.isfile(stub_template_path) and os.path.isfile(root_review_path)):
        sys.exit(0)  # 项目还没跑过 opsx-project-init → 静默跳过

    try:
        template = open(stub_template_path, encoding="utf-8").read()
    except OSError:
        sys.exit(0)

    project_name = os.path.basename(os.path.abspath(cwd))
    rendered = template.replace("__PROJECT_NAME__", project_name)

    dst = os.path.join(change_dir, "review.html")
    existing = None
    if os.path.exists(dst):
        try:
            existing = open(dst, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            existing = None
    if existing != rendered:
        try:
            with open(dst, "w", encoding="utf-8") as f:
                f.write(rendered)
        except OSError:
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
