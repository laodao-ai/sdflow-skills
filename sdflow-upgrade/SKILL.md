---
name: sdflow-upgrade
description: 升级 sdflow 工具链运行 checkout（~/.skills/sdflow-skills）：git pull → bash setup.sh（skills 软链 + ~/.sdflow canonical/hack 同步刷新，堵 pull→setup 窗口期）→ 显示版本与最新变更，并提示消费仓按需跑 sdflow-init update。当用户说"升级 sdflow"、"更新 sdflow skills"、"sdflow upgrade"、"sdflow 有新版本吗"、"刷新 sdflow"，或使用 /sdflow-upgrade 时触发。
---

# sdflow-upgrade — 运行 checkout 一键升级

对**运行 checkout** `~/.skills/sdflow-skills/` 执行升级三连。pull 与 setup 必须连跑——
SKILL.md 软链即时生效、`~/.sdflow/hack/` 脚本拷贝生效，只 pull 不 setup 会造成两者版本错位（陈旧遮蔽的脚本变体）。

## 步骤

1. **pull**：`git -C ~/.skills/sdflow-skills pull --ff-only`
   - 非 ff（本地被改过）→ 停下报告，不强推；提示"运行 checkout 只读，改动应发生在开发 checkout"。
2. **setup**：`bash ~/.skills/sdflow-skills/setup.sh`
   - 刷 skills 软链 + `~/.sdflow/workflow` canonical + `~/.sdflow/hack/{checkpoint-commit.sh,resolve-workflow.sh}`。
3. **展示**：`cat ~/.skills/sdflow-skills/VERSION 2>/dev/null || echo unknown` + `git -C ~/.skills/sdflow-skills log --oneline -5`，向用户汇报版本与最新变更。
4. **提示**：各消费仓如需拿最新 tools/ 或看陈旧遮蔽告警 → 在该仓跑 `sdflow-init update`（本 skill 不代跑）。

## 回滚

推坏一版规则时：`git -C ~/.skills/sdflow-skills checkout <上一已知良好 commit> && bash ~/.skills/sdflow-skills/setup.sh`。

## 注意

- 只动运行 checkout；开发 checkout（编辑规则/skill 的 clone）不归本 skill 管。
- 运行 checkout remote 必须是 `laodao-ai/sdflow-skills.git`——不是则先按 minimize-repo-footprint 的 0.1 迁移。
