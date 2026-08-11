### Task 4: bundle 资产与 config 收口

**Blocked-by:** 2,3
**R-ID:** R7, R10, R11

**step6 删除**：删除 `sdflow-init/assets/workflow/prompts/step6-writing-plans.md`（唯一运行时消费者即被删 ship 分支）。守卫测试同步：`test_workflow_authority.py` 的 step6 断言退役；`test_workflow_split.py` / `test_checkpoint_slug_coverage.py` 名单去 step6 条目。

**六份 bundle 资产收口**：`workflow.md`（子步骤 A、显式 superpowers 段、检查清单行）/ `WORKFLOW-GUIDE.md`（同上）/ `ff-generation-constraints.md`（切片建议条件恒真化 → 改无条件）/ `config.template.yaml`（键注释删）/ `snippets/claude-section.md`（「缺省 tickets / 显式 superpowers」→「唯一管线」表述）/ `reference/quality-layering.md`（superpowers SDD 注入点 A/B 与「用 superpowers 跑实现时」清单节退役）。

**config 键退役**：本仓 `openspec/config.yaml` 删 `impl-pipeline` 键 + 注释。

**托管区块刷新**：`sdflow-init update` 刷本仓 CLAUDE.md / AGENTS.md 托管区块。

**INDEX 同步**：`openspec/INDEX.md` 的 impl-orchestration 描述行（「手动路由三跳」）改单管线表述。

**specs delta**：`specs/yq-yaml-operations/spec.md` delta——R3/R5/R6 的 impl-pipeline Scenario 删除落主 spec；主 spec Purpose 脚本枚举去 `impl_route.py`；`test_yq_wrapper_consistency.py` 成员表核验（Task 1 已完成去条目）。

- [ ] `step6-writing-plans.md` 已删除，三份守卫测试名单已同步
- [ ] 六份 bundle 资产 superpowers 叙述已收口
- [ ] 本仓 `openspec/config.yaml` 的 `impl-pipeline` 键已删除
- [ ] `sdflow-init update` 已执行，CLAUDE.md / AGENTS.md 托管区块已刷新
- [ ] `openspec/INDEX.md` 描述行已更新
- [ ] yq-yaml-operations delta spec 已同步

