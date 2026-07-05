## Why

review.html 查看器工具目前有**三个入口**产出 `review.html`：① 根锚 `openspec/review.html`（HTTP 服务根，engine.js 从 `window.location.pathname` 推 scope，靠它一份即可导航到任意 change/roadmap）；② `change-review-stub.py`（全局 PostToolUse hook，`openspec new change` 后自动补 `changes/<name>/review.html`）；③ `sdflow-roadmap` 的 `gen_review_stub.py`（roadmap 流程显式一步，产 `roadmaps/<name>/review.html`）。

②③ 这两份**每目录 stub 与根锚内容同源**（同一模板替换 `__PROJECT_NAME__`），scope 已由 engine.js 从路径推导、不再靠占位符固化——即根锚一份就够看，每目录 stub 是**冗余产物 + 每次建 change 都自动落一份文件的足迹噪音**（违 adr/0003「最小部署足迹」精神）。移除这两个生产者即可，根查看器保留不变。

## What Changes

- **删 change-review-stub hook**：移除 `sdflow-init/assets/hooks/change-review-stub.py` 及其在 `init.py` `HOOKS` 列表的注册项。
- **删 roadmap 生产者**：移除 `sdflow-roadmap/scripts/gen_review_stub.py` 及 SKILL.md 里调用它的那一步。
- **新增"退役 hook 反注册"迁移**（唯一设计点，见 design.md ADR-1）：`init.py` 当前只幂等**安装** hook、从不移除；直接删会在存量安装的 `~/.claude/settings.json` 留孤儿注册 + `~/.claude/hooks/change-review-stub.py` 残留 → 之后每次 Bash 触发该 hook 命令报「文件不存在」。故加一个 `RETIRED_HOOKS` 机制：init/update 每次跑主动从 settings.json 摘除退役 hook 的注册条目 + 删 `~/.claude/hooks/` 里的脚本（幂等、跨存量安装自愈；fresh 安装无残留则 no-op）。
- **删对应测试**：`sdflow-init/tests/test_change_review_stub_hook.py`、`sdflow-roadmap/tests/test_gen_review_stub.py`；`test_init.py` 里断言 change-review-stub 被安装的片段改为断言其被反注册。
- **改文档**：`sdflow-roadmap/SKILL.md`、`sdflow-init/SKILL.md` 去掉每目录 stub / hook 描述；`openspec/ROADMAP.md` 顺带提及行更新。

**保留不动**：根锚 `openspec/review.html` + `serve.sh` + `workflow/tools/` engine bundle + `assets/review-tool/`；`ff0-branch-guard.py` hook；archive 里各历史 change 的 `review.html`。

## Success Metrics

- `openspec new change X` 后 `changes/X/` **不再**出现 `review.html`；`sdflow-roadmap` 流程不再产 `roadmaps/X/review.html`。
- 存量安装跑一次 `sdflow-init update` 后：`~/.claude/settings.json` 的 PostToolUse.Bash 中**无** change-review-stub 条目、`~/.claude/hooks/change-review-stub.py` **不存在**，且**每次 Bash 调用不再有 hook 报错**。
- 根查看器 `serve.sh` + `openspec/review.html` 打开后仍能导航到任意 change/roadmap（能力不回退）。
- `sdflow-init/tests/` 与 `sdflow-roadmap/tests/` 全绿；仓级 pytest 无回归。

## Non-Goals

- **不下线整个 review 查看器**：根锚 + engine bundle + serve.sh 全部保留（用户明确选窄范围）。
- **不动 archive 内历史 `review.html`**（已归档产物是留档，不追溯清理）。
- **不改 `spec.md:99` 根锚复制需求**本身（根锚照旧铺）；本 change 只在同一需求的 hooks 枚举里摘掉一个退役 hook。
- **不重构 `ff0-branch-guard` hook**或 hook 安装框架其余部分（只加反注册能力，不改安装语义）。

## Capabilities

### New Capabilities
<!-- 无新能力 -->

### Modified Capabilities
- `spec-workflow`: MODIFIED「workflow bundle 改在权威源、经部署下发」——部署的全局 hooks 集从 `{ff0-branch-guard, change-review-stub}` 收缩为 `{ff0-branch-guard}`；明确 review UI 以**根锚单一查看面**提供、不再生成每-change/每-roadmap 的 `review.html` stub；`sdflow-init` 部署 MUST 具备退役 hook 的反注册能力（存量安装自愈）。

## Impact

- **skill**：`sdflow-init`（assets/hooks、scripts/init.py、SKILL.md、tests）、`sdflow-roadmap`（scripts、SKILL.md、tests）。
- **领域清单**：纯 Python skill 脚本，**不命中** domains（backend·go / embedded / frontend 均不涉），无领域镜。
- **部署/迁移**：动 `assets/` 权威源（hook 资产 + init 逻辑）→ 合并后运行 checkout 须 `sdflow-init update`（触发反注册自愈）+ 开发 checkout 跑 `setup.sh`。**存量安装的迁移一次性**：update 幂等反注册，重复跑安全。
- **无运行时行为变更**（对根查看器）：仅去掉冗余产物 + 一个自动 hook；查看能力由根锚承接不变。
- **scope 外**：整查看器下线（用户否决）；archive 历史 stub 清理（留档不动）。

## Compliance

N/A（无外部合规/隐私/许可影响；纯内部工具足迹清理）。
