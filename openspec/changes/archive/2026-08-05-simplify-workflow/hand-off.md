# Hand-off — simplify-workflow

## ✅ 完成了什么

- 合并双轨入口（分支 A/B）为唯一线性路径：explore(条件) → sdflow-spec → /clear → spec-review → HARD-GATE → /clear → sdflow-ship
  - 锚：`sdflow-init/assets/workflow/workflow.md` 流程图 + 步骤表（commit `ab8f746`）
- 删除 embedded-test-sop skill + ship_gate.py RUN_SOP 逻辑（345 tests passed）
  - 锚：`grep -n "RUN_SOP\|tg02_hit" sdflow-ship/scripts/ship_gate.py` = 零命中
- 翻转 impl-pipeline 缺省为 tickets（79 tests passed）
  - 锚：`sdflow-implement/scripts/impl_route.py` 6 处 return `"tickets"`
- 解除 sdflow-spec 手动触发限制（`disable-model-invocation: true` 已删）
  - 锚：`sdflow-spec/SKILL.md` frontmatter 无该行
- 删除 3 个旧 prompt 文件 + test_grill_handoff.py
- 重写 workflow bundle 核心文档（workflow.md/generation-process.md/ff-generation-constraints.md）+ 重新生成 WORKFLOW-GUIDE.md
- 更新 CLAUDE.md/AGENTS.md/claude-section.md 为单轨描述，删 sunset 条件/四入口选择规则/grill-with-docs 段
- 删除 40 个过期本地 pin 规则文件（恢复全局解析）
- 同步 companion 文档（docs/*.md + docs/*.html）
- 全仓 pytest 2443 passed, 0 failed

## ⏳ 未完成 / 延后

- [Minor] ship_gate.py:268 FenceTracker 消费者计数注释"三个"实为四个（`_plan_task_r_ids` 漏计）——comment-only，无逻辑影响
- [Minor] impl_route.py 重复字面量 `"tickets"` 可提取为 `DEFAULT_PIPELINE` 常量——预存模式
- 无本 change 新增的 bug/todo（issues scan 返回空）

## ▶ 下一阶段建议

- 两项 Minor defer 可在下次涉及 ship_gate.py / impl_route.py 的 change 中顺手修复，不需要单独开 change
- 下游 15 个无显式 impl-pipeline 键的项目在 `sdflow-init update` 后将从 superpowers 翻到 tickets——发布后通知下游用户
- toolkit 源仓（本仓）：push 后新会话跑 `/sdflow-upgrade` 激活
