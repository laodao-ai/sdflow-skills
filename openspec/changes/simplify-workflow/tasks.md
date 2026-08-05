# Tasks — simplify-workflow

## Global Constraints

- 改 workflow bundle（`sdflow-init/assets/workflow/`）= 改权威源，下游通过 `sdflow-init update` 拉取
- 改 `sdflow-init/assets/snippets/claude-section.md` = 改下推给消费项目的 CLAUDE.md 模板
- 改 `CLAUDE.md`（本仓）= 仅影响本仓，与 snippet 保持一致但措辞可不同
- ship_gate.py 改动后必须 `pytest sdflow-ship/tests/` 全绿
- embedded-test-sop 删除后必须 `bash setup.sh` 清孤儿链接

## Context

本 change 是纯文档+脚本改动（无前端/后端/数据库），不命中任何领域 TG。核心是 ≈18 个文件的增删改，按依赖关系分组。

---

### Task 1: 删除 embedded-test-sop skill 目录 + ship_gate.py RUN_SOP 逻辑

**Req**: 阶段三编排不含 embedded-test-sop 自动触发

- [ ] 删除 `embedded-test-sop/` 整个 skill 目录
- [ ] 从 `sdflow-ship/scripts/ship_gate.py` 删除：`tg02_hit()` 函数、`RUN_SOP` verdict 定义、`decide()` 中 RUN_SOP 分支、`emit_windowed` 中 RUN_SOP 调用点、所有 docstring/注释中 RUN_SOP 引用
- [ ] 从 `sdflow-ship/tests/*.py` 删除 RUN_SOP 相关测试用例
- [ ] 更新 `sdflow-ship/SKILL.md`：删 RUN_SOP gate 分支描述、删链序中 `RUN_SOP→跑 embedded-test-sop` 段
- [ ] `pytest sdflow-ship/tests/` 全绿
- [ ] `bash setup.sh` 清孤儿链接

### Task 2: 翻转 impl-pipeline 缺省为 tickets

**Req**: impl-pipeline 缺省为 tickets

- [ ] 修改 `sdflow-ship/scripts/impl_route.py`：`route` 子命令缺省值从 `superpowers` 改为 `tickets`
- [ ] 更新 `sdflow-ship/SKILL.md`：缺省描述改为 tickets
- [ ] 更新 `openspec/config.yaml`（本仓）：impl-pipeline 注释改缺省说明
- [ ] 更新 `sdflow-init/assets/workflow/workflow.md`：impl-pipeline 缺省描述
- [ ] `pytest sdflow-ship/tests/` 全绿（缺省值相关测试更新）

### Task 3: 解除 sdflow-spec 手动触发限制

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [ ] `sdflow-spec/SKILL.md`：删除 frontmatter `disable-model-invocation: true`
- [ ] `sdflow-spec/SKILL.md`：description 删「由人显式触发」「只能人触发」

### Task 4: 重写 workflow bundle 文档（权威源）

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [ ] `sdflow-init/assets/workflow/workflow.md`：流程图改为线性单轨；步骤表精简（删步骤 0/1/1b/2/3/5.5）；§三设计决策精简（G1 分析移入附录）；删全部 wayfinder/embedded-test-sop/分支 B 引用
- [ ] `sdflow-init/assets/workflow/generation-process.md`：删 §四 分支 B + 四入口选择规则；简化为单入口描述；删手动限制语言；加 explore→sdflow-spec 自动衔接规则
- [ ] `sdflow-init/assets/workflow/ff-generation-constraints.md`：删 §wayfinder→ff 衔接契约
- [ ] `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`：删步骤 1b/2/3/5.5；步骤重编号
- [ ] 删除 `sdflow-init/assets/workflow/prompts/step2-ff.md`
- [ ] 删除 `sdflow-init/assets/workflow/prompts/step3-grill.md`
- [ ] 删除 `sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md`

### Task 5: 更新 snippets + 本仓 CLAUDE.md

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [ ] `sdflow-init/assets/snippets/claude-section.md`：删分支 B/wayfinder/grill-with-docs/手动限制段落；加 sdflow-spec 自动触发规则；更新 impl-pipeline 缺省描述；更新 embedded-test-sop 引用（从编排类 skill 列表移除）
- [ ] `CLAUDE.md`（本仓）：删「四入口选择规则」段；删「旧入口 sunset 条件」段（≈40 行）；删 grill-with-docs 引用段落；更新编排类 skill 列表；更新 impl-pipeline 缺省描述；删手动限制引用；更新「使用路径」段

### Task 6: 全量验证 + README 更新

**Req**: 阶段三编排不含 embedded-test-sop 自动触发

- [ ] `pytest` 全仓全绿
- [ ] `bash setup.sh` 运行正常（无 embedded-test-sop 报错）
- [ ] `grep -rn "embedded-test-sop\|RUN_SOP\|wayfinder\|分支 B\|分支B\|disable-model-invocation" --include="*.md" --include="*.py"` 扫残留引用（允许 workflow-history.md 和本 change 目录内）
- [ ] README.md Skills 列表移除 embedded-test-sop
