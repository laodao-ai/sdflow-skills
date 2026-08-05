---
impl-pipeline: tickets
---

## Global Constraints

- 改 workflow bundle（`sdflow-init/assets/workflow/`）= 改权威源，下游通过 `sdflow-init update` 拉取
- 改 `sdflow-init/assets/snippets/claude-section.md` = 改下推给消费项目的 CLAUDE.md 模板
- 改 `CLAUDE.md`（本仓）= 仅影响本仓，与 snippet 保持一致但措辞可不同
- ship_gate.py 改动后必须 `pytest sdflow-ship/tests/` 全绿
- impl_route.py 改动后必须 `pytest sdflow-implement/tests/` 全绿
- embedded-test-sop 删除后必须 `bash setup.sh` 清孤儿链接
- `WORKFLOW-GUIDE.md` 是生成物（`hack/gen_workflow_guide.py`），MUST NOT 手改——改源 + 重新生成
- `openspec/workflow/` 本地 pin（48 文件）须与权威源同步或删除（恢复全局解析）
- 旧入口（opsx:ff、grill-with-docs、opsx:explore）作为 skill 不删除（两个是 CLI 生成物，一个在仓外），只从 workflow 流程文档中移除
- 删除策略：保留 `guard_design_freshness` 和 `emit_windowed` 函数不变——它们仍被 RUN_PLAN/CONTINUE_IMPL 使用
- DOC-1（正文即最终态，演进史/分析进附录）适用于 workflow.md G1 段

### Task 1: 删除 embedded-test-sop skill 并清除 ship_gate.py RUN_SOP 逻辑

**Blocked-by:** none
**R-ID:** R2

删除 `embedded-test-sop/` skill 目录，并从 ship_gate.py 状态机中移除 RUN_SOP verdict 的全部实现：`tg02_hit()` 函数体及其调用、`RUN_SOP` verdict 定义行、`decide()` 中的 RUN_SOP 分支、`emit_windowed` 中的 RUN_SOP 调用点、所有 docstring/注释中的 RUN_SOP 引用（含"三个入口"计数改为"两个"）。测试文件中纯 RUN_SOP 专属测试删除，断言元组/fixture 里附带提及的测试编辑保留（改元组/注释，不删函数）。删除后 `pytest sdflow-ship/tests/` 全绿，`bash setup.sh` 清孤儿链接。

- [x] `embedded-test-sop/` 整个目录已删除
- [x] ship_gate.py 中 `tg02_hit()` 函数已删除
- [x] ship_gate.py 中 RUN_SOP verdict 定义、decide() 分支、emit_windowed 调用点已删除
- [x] ship_gate.py 中所有 docstring/注释的 RUN_SOP 引用已清理（含计数同步）
- [x] 测试文件中纯 RUN_SOP 专属测试已删除，附带提及的测试已编辑保留
- [x] `pytest sdflow-ship/tests/` 全绿
- [x] `bash setup.sh` 运行正常，`~/.claude/skills/` 下无 `embedded-test-sop` 链接

### Task 2: 翻转 impl-pipeline 缺省为 tickets 并更新相关配置文档

**Blocked-by:** none
**R-ID:** R3

修改 `impl_route.py` 的 `read_config_pipeline` 和 `read_plan_marker` 函数：缺配置/缺键/空值的 return 改为 `"tickets"`，非法值/YAML 损坏的 return 改为 `"tickets"`；已有 plan 缺 frontmatter/marker 的 return 保持 `"superpowers"` 不变（避免静默切换在途 change）。同步修改 `_cmd_route` 展示折叠逻辑使其对称翻转。更新 `openspec/config.yaml`（本仓）impl-pipeline 注释 + 删除 wayfinder 规则引用。更新两份 `config.template.yaml`（`sdflow-init/assets/workflow/` + `openspec/workflow/`）注释改"缺省一律 tickets"。更新 `sdflow-ship/SKILL.md` 缺省描述。更新 `sdflow-init/assets/workflow/workflow.md` impl-pipeline 缺省描述。`pytest sdflow-implement/tests/` 全绿。

- [ ] impl_route.py 中缺配置/缺键/空值/非法值的 return 已改为 `"tickets"`
- [ ] impl_route.py 中 `_cmd_route` 展示折叠逻辑已对称翻转
- [ ] `openspec/config.yaml` impl-pipeline 注释已更新 + wayfinder 引用已删
- [ ] 两份 `config.template.yaml` 注释已改为"缺省 tickets"
- [ ] `sdflow-ship/SKILL.md` 缺省描述已更新
- [ ] `pytest sdflow-implement/tests/` 全绿

### Task 3: 解除 sdflow-spec 手动触发限制并删除旧 workflow prompts

**Blocked-by:** none
**R-ID:** R1

从 `sdflow-spec/SKILL.md` 删除 frontmatter `disable-model-invocation: true`，description 删「由人显式触发」「只能人触发」等语句。删除三个旧步骤的 prompt 文件：`sdflow-init/assets/workflow/prompts/step2-ff.md`、`sdflow-init/assets/workflow/prompts/step3-grill.md`、`sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md`。删除 `sdflow-init/tests/test_grill_handoff.py`（grill 不再是独立步骤，回归门退役）。

- [ ] `sdflow-spec/SKILL.md` frontmatter 无 `disable-model-invocation: true`
- [ ] `sdflow-spec/SKILL.md` description 无手动触发限制语言
- [ ] `prompts/step2-ff.md`、`prompts/step3-grill.md`、`prompts/step5_5-embedded-sop.md` 已删除
- [ ] `sdflow-init/tests/test_grill_handoff.py` 已删除

### Task 4: 重写 workflow bundle 核心文档为单轨线性流程

**Blocked-by:** 1,2,3
**R-ID:** R1

重写 workflow bundle 三个核心文档（权威源）：① `workflow.md` 流程图改为线性单轨，步骤表精简（删旧步骤），G1 分析移入附录正文只留一条规则，删全部 wayfinder/embedded-test-sop/分支 B 引用；② `generation-process.md` 删分支 B + 四入口选择规则，简化为单入口描述，加 explore→sdflow-spec 自动衔接规则；③ `ff-generation-constraints.md` 删 wayfinder→ff 衔接契约，更新切片建议触发条件措辞反映缺省=tickets。更新 `hack/gen_workflow_guide.py` 的 STEP_FILES 字典并重新生成 `WORKFLOW-GUIDE.md`。

- [ ] `workflow.md` 流程图为线性单轨，步骤表精简，G1 分析在附录
- [ ] `generation-process.md` 为单入口描述，含 explore→sdflow-spec 自动衔接规则
- [ ] `ff-generation-constraints.md` 无 wayfinder 衔接契约，切片建议反映缺省=tickets
- [ ] `WORKFLOW-GUIDE.md` 已通过 `python3 hack/gen_workflow_guide.py --write` 重新生成

### Task 5: 更新 snippets、CLAUDE.md、AGENTS.md、本地 pin 与 companion 文档

**Blocked-by:** 4
**R-ID:** R1

更新 `sdflow-init/assets/snippets/claude-section.md`：删分支 B/wayfinder/grill-with-docs/手动限制段落，加 sdflow-spec 自动触发规则，更新 impl-pipeline 缺省描述，从编排类 skill 列表移除 embedded-test-sop。更新本仓 `CLAUDE.md`：删「四入口选择规则」段、「旧入口 sunset 条件」段（≈40 行）、grill-with-docs 引用段落，更新编排类/使用路径/impl-pipeline 描述，删手动限制引用。更新 `AGENTS.md`：删旧双轨/手动触发/ff→grill 引用。处理 `openspec/workflow/` 本地 pin：删除规则文件恢复全局解析或同步刷新。同步 companion 文档：`docs/workflow-map.md`、`docs/workflow-overview.md`、`docs/criteria-mechanization-tracker.md`、`docs/sdflow-fable5/02-module-reference.md` 中的 RUN_SOP/embedded-test-sop/wayfinder/分支 B 引用。更新 README.md Skills 列表移除 embedded-test-sop。

- [ ] `claude-section.md` 已更新为单轨描述
- [ ] `CLAUDE.md` 已删除四入口选择规则段、sunset 条件段、grill-with-docs 段
- [ ] `AGENTS.md` 已删旧双轨/手动触发/ff→grill 引用
- [ ] `openspec/workflow/` 本地 pin 已处置（删除或同步）
- [ ] companion 文档中 RUN_SOP/embedded-test-sop/wayfinder/分支 B 引用已清理
- [ ] README.md Skills 列表无 embedded-test-sop

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task6-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。全仓残留引用扫描：`grep -rn "embedded-test-sop\|RUN_SOP\|wayfinder\|分支 B\|分支B\|disable-model-invocation" --include="*.md" --include="*.py" --include="*.yaml"` 只允许 allowlist（workflow-history.md、本 change 目录内、归档 change、ADR 历史引用、issue/roadmap）。`bash setup.sh` 运行正常。

- [ ] `pytest` 全仓全绿（证据含命令原文、退出码、SHA）
- [ ] `bash setup.sh` 运行正常
- [ ] 残留引用扫描通过（仅 allowlist 内存在）
