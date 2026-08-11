# Hand-off · remove-superpowers-pipeline

## ✅ 完成了什么

- **路由切除**（Task 1）：`impl_route.py` route 半场全部删除，保留半场（frontier/task-text/parse_blocked_by）接口与行为逐字不变。锚：`test_impl_route.py` 35 条保留用例全绿、`test_gate_closing_ticket.py` sibling-import 回归绿。
- **gate 单名 resolver**（Task 2）：`PLAN_FILENAMES` 缩为单名 `("tickets.md",)`，新增 `LegacyPlanNameFound` fail-closed 兜底，grandfather 删除，收尾票校验无条件化。锚：342 passed（sdflow-ship/tests/）、Q1 兜底测试 `test_legacy_plan_name_alone_gate_fails_closed_unknown` 绿。
- **SKILL 文案收口**（Task 3）：sdflow-ship/implement/done 三份 SKILL.md 双轨表述全部收口为单管线直连。gate `next` 字段从 `writing-plans`/`subagent-dev` 同步改为 `sdflow-implement`。
- **bundle 资产与 config**（Task 4）：step6 prompt 删除 + 守卫测试同步；6 份 bundle 资产收口；config.yaml `impl-pipeline` 键退役；CLAUDE.md/AGENTS.md 托管区块刷新（手工同步，init.py 有预存 bug）。
- **docs 与扫尾**（Task 5）：obsolete 标注、4 份现役视图文档收口、ADR 0033/0042 互指、grep 扫尾通过（额外修复 3 处 SDD 短名残留 + 删除孤儿 step7）。
- **聚合回归**（Task 6）：2560 passed, 0 failed @ SHA `474e412`。
- **代码审**：5 镜 fan-out（领域+对抗×2+历史+scope）+ code-voice = pass，2 条 auto-fix（gate 契约表 + test 注释），1 条 defer。

## ⏳ 未完成 / 延后

- **sdflow-spec-review/SKILL.md:366 收敛口仍写 `writing-plans`**：该文件不在本 change 的 proposal scope（仅 ship/implement/done 三份 SKILL），需另开 change 修复为 `/sdflow-ship`。建议：同步更新 sdflow-code-review/SKILL.md 的「注入点 B 关系」§2.4 表格里的 `subagent-dev` 表述。
- **`sdflow-init/scripts/init.py` 不兼容 openspec CLI v1.8.0 的 `.openspec.yaml` 双键格式**：`_marker_schema()` 遇 `schema:`+`created:` 双键报错，`sdflow-init update` 无法执行。预存 bug，非本 change 引入。
- **gate 文件头契约表 `SDD 勿重派` 残句**：CONTINUE_IMPL 行 reason 列已在 auto-fix 中改去 `SDD` 引用，但 `勿重派` 措辞可能仍需审视（Minor）。
- **主 spec 尚未同步**（`openspec/specs/impl-orchestration/spec.md` 与 `spec-workflow/spec.md`）：正常 pre-archive 状态，由 sdflow-done archive 步骤的 delta-sync 解决。

## ▶ 下一阶段建议

1. **优先**：开一个 `cleanup-skill-superpowers-residuals` change，收口 sdflow-spec-review 与 sdflow-code-review 两份 SKILL.md 的 superpowers/writing-plans/subagent-dev 残留。scope 小、无代码改动、仅文案。
2. **低优先**：修 init.py `_marker_schema()` 兼容 openspec CLI v1.8.0 双键格式（影响面：所有用 `sdflow-init update` 刷新托管区块的仓）。
3. **Roadmap 回填**：未检测到 roadmap 关联标记；本 change 属 T277 独立决策。
