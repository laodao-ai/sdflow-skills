# Tasks — simplify-workflow

## Global Constraints

- 改 workflow bundle（`sdflow-init/assets/workflow/`）= 改权威源，下游通过 `sdflow-init update` 拉取
- 改 `sdflow-init/assets/snippets/claude-section.md` = 改下推给消费项目的 CLAUDE.md 模板
- 改 `CLAUDE.md`（本仓）= 仅影响本仓，与 snippet 保持一致但措辞可不同
- ship_gate.py 改动后必须 `pytest sdflow-ship/tests/` 全绿
- impl_route.py 改动后必须 `pytest sdflow-implement/tests/` 全绿 [spec-review-amendment]
- embedded-test-sop 删除后必须 `bash setup.sh` 清孤儿链接
- `WORKFLOW-GUIDE.md` 是生成物（`hack/gen_workflow_guide.py`），MUST NOT 手改——改源 + 重新生成 [spec-review-amendment]
- `openspec/workflow/` 本地 pin（48 文件）须与权威源同步或删除（恢复全局解析） [spec-review-amendment]

## Context

本 change 是纯文档+脚本改动（无前端/后端/数据库），不命中任何领域 TG。核心是 ≈18 个文件的增删改，按依赖关系分组。

---

### Task 1: 删除 embedded-test-sop skill 目录 + ship_gate.py RUN_SOP 逻辑

**Req**: 阶段三编排不含 embedded-test-sop 自动触发

- [x] 删除 `embedded-test-sop/` 整个 skill 目录
- [x] 从 `sdflow-ship/scripts/ship_gate.py` 删除：`tg02_hit()` 函数、`RUN_SOP` verdict 定义、`decide()` 中 RUN_SOP 分支、`emit_windowed` 中 RUN_SOP 调用点、所有 docstring/注释中 RUN_SOP 引用（注意"三个入口"计数改为"两个"） [spec-review-amendment: 计数同步]
- [x] 从 `sdflow-ship/tests/*.py` 处理 RUN_SOP 引用：纯 RUN_SOP 专属测试**删除**；断言元组/fixture 里附带提及 RUN_SOP 的测试**编辑保留**（改元组/注释，不删函数） [spec-review-amendment: 拆为"删除"和"编辑保留"两类]
- [x] 更新 `sdflow-ship/SKILL.md`：删 RUN_SOP gate 分支描述、删链序中 `RUN_SOP→跑 embedded-test-sop` 段
- [x] `pytest sdflow-ship/tests/` 全绿
- [x] `bash setup.sh` 清孤儿链接

### Task 2: 翻转 impl-pipeline 缺省为 tickets

**Req**: impl-pipeline 缺省为 tickets

- [x] 修改 `sdflow-implement/scripts/impl_route.py`：`read_config_pipeline` 的 6 处 + `read_plan_marker` 的 2 处 `return "superpowers"` 按语义分类改为 `"tickets"`（缺配置/缺键/空值 → tickets；非法值/YAML 损坏 → tickets；已有 plan 缺 frontmatter/marker → 保持 superpowers 不变以免静默切换在途 change） [spec-review-amendment: 路径修正 + 9 处分语义处理]
- [x] 修改 `sdflow-implement/scripts/impl_route.py`：`_cmd_route` 展示折叠逻辑（L540 附近）对称翻转 [spec-review-amendment]
- [x] 更新 `sdflow-ship/SKILL.md`：缺省描述改为 tickets
- [x] 更新 `openspec/config.yaml`（本仓）：impl-pipeline 注释改缺省说明 + 删除 wayfinder 规则引用（L38/48） [spec-review-amendment]
- [x] 更新 `sdflow-init/assets/workflow/workflow.md`：impl-pipeline 缺省描述
- [x] 更新两份 `config.template.yaml`（`sdflow-init/assets/workflow/` + `openspec/workflow/`）：注释改"缺省…一律 tickets" [spec-review-amendment]
- [x] `pytest sdflow-implement/tests/` 全绿（缺省值相关测试更新） [spec-review-amendment: 路径修正]

### Task 3: 解除 sdflow-spec 手动触发限制

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [x] `sdflow-spec/SKILL.md`：删除 frontmatter `disable-model-invocation: true`
- [x] `sdflow-spec/SKILL.md`：description 删「由人显式触发」「只能人触发」

### Task 4: 重写 workflow bundle 文档（权威源）

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [x] `sdflow-init/assets/workflow/workflow.md`：流程图改为线性单轨；步骤表精简（删步骤 0/1/1b/2/3/5.5）；§三设计决策精简（G1 分析移入附录）；删全部 wayfinder/embedded-test-sop/分支 B 引用
- [x] `sdflow-init/assets/workflow/generation-process.md`：删 §四 分支 B + 四入口选择规则；简化为单入口描述；删手动限制语言；加 explore→sdflow-spec 自动衔接规则
- [x] `sdflow-init/assets/workflow/ff-generation-constraints.md`：删 §wayfinder→ff 衔接契约
- [x] `hack/gen_workflow_guide.py`：更新 STEP_FILES 字典（删除旧步骤键、重编号）→ `python3 hack/gen_workflow_guide.py --write` 重新生成 `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md`（MUST NOT 手改生成物） [spec-review-amendment]
- [x] 删除 `sdflow-init/assets/workflow/prompts/step2-ff.md`
- [x] 删除 `sdflow-init/assets/workflow/prompts/step3-grill.md`
- [x] 删除 `sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md`

### Task 5: 更新 snippets + 本仓 CLAUDE.md

**Req**: 阶段一入口为唯一线性路径，模型可自动触发

- [x] `sdflow-init/assets/snippets/claude-section.md`：删分支 B/wayfinder/grill-with-docs/手动限制段落；加 sdflow-spec 自动触发规则；更新 impl-pipeline 缺省描述；更新 embedded-test-sop 引用（从编排类 skill 列表移除）
- [x] `CLAUDE.md`（本仓）：删「四入口选择规则」段；删「旧入口 sunset 条件」段（≈40 行）；删 grill-with-docs 引用段落；更新编排类 skill 列表；更新 impl-pipeline 缺省描述；删手动限制引用；更新「使用路径」段
- [x] `AGENTS.md`（本仓）：删旧双轨/手动触发/ff→grill 引用（L125/139-144/262-268） [spec-review-amendment]
- [x] `sdflow-init/tests/test_grill_handoff.py`：整体删除（grill 不再是流程中的独立步骤，该回归门随之退役） [spec-review-amendment]

### Task 5b: 处理本地 pin + companion 文档 [spec-review-amendment]

**Req**: 阶段一入口为唯一线性路径

- [x] `openspec/workflow/` 本地 pin 处置：删除规则文件（恢复全局解析）或 `sdflow-init update` 同步刷新 48 文件
- [x] companion 文档同步：`docs/workflow-map.md`（4 处 RUN_SOP）、`docs/workflow-overview.md`（6 处）、`docs/criteria-mechanization-tracker.md`（tg02_hit 行）、`docs/sdflow-fable5/02-module-reference.md`（5 处）
- [x] `ff-generation-constraints.md`：更新§切片建议触发条件措辞，反映缺省=tickets [spec-review-amendment]

### Task 6: 全量验证 + README 更新

**Req**: 阶段三编排不含 embedded-test-sop 自动触发

- [x] `pytest` 全仓全绿
- [x] `bash setup.sh` 运行正常（无 embedded-test-sop 报错）
- [x] `grep -rn "embedded-test-sop\|RUN_SOP\|wayfinder\|分支 B\|分支B\|disable-model-invocation" --include="*.md" --include="*.py" --include="*.yaml"` 扫残留引用（允许清单：workflow-history.md、本 change 目录内、归档 change、ADR 历史引用、issue/roadmap） [spec-review-amendment: 加 .yaml + 扩展 allowlist]
- [x] README.md Skills 列表移除 embedded-test-sop
