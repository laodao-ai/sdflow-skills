## Context

当前工作流有双轨入口（分支 A/B）、wayfinder chart 条件步、embedded-test-sop 自动触发、sdflow-spec 手动限制等历史复杂度。动机见 [proposal.md](./proposal.md)。

## Goals / Non-Goals

见 proposal.md。本设计只关注 HOW。

## Approach

### 1. 流程简化为唯一线性路径

```
  explore(条件：模糊/未定)
       │  人示意收敛 → 模型自动 invoke
       ↓
  /sdflow-spec (澄清→拷问→生成)
       │
  ═══ /clear ═══  (cache隔离 + 产/审错档)
       │
  /sdflow-spec-review (autoplan + 多镜)
       │
  ★ HARD-GATE ★  (唯一人类停点)
       │
  ═══ /clear ═══  (盘面纪律 + 产物自足性 + 去作者偏置)
       │
  /sdflow-ship ─── sdflow-implement → sdflow-code-review → sdflow-done → merge
```

### 2. 文件级变更清单

#### 2.1 删除的文件

| 文件 | 理由 |
|------|------|
| `embedded-test-sop/` 整个 skill 目录 | D3: 彻底删除 |
| `sdflow-init/assets/workflow/prompts/step2-ff.md` | 旧三步独立入口，不再在流程中引导 |
| `sdflow-init/assets/workflow/prompts/step3-grill.md` | 同上 |
| `sdflow-init/assets/workflow/prompts/step5_5-embedded-sop.md` | D3 |

#### 2.2 重写的文件

| 文件 | 改动概要 |
|------|----------|
| `sdflow-init/assets/workflow/workflow.md` | 流程图改为线性单轨；步骤表从 10 行降到 6 行；§三设计决策精简（G1 分析移入附录）；删除 wayfinder/embedded-test-sop/分支 B 全部引用 |
| `sdflow-init/assets/workflow/generation-process.md` | 删 §四 分支 B + 四入口选择规则；简化为单入口描述（explore 条件 → sdflow-spec 默认）；删手动限制语言 |
| `sdflow-init/assets/workflow/WORKFLOW-GUIDE.md` | **生成物，MUST NOT 手改**——改 workflow.md 步骤表 + 更新 `hack/gen_workflow_guide.py` 的 STEP_FILES 字典（重编号键）→ `python3 hack/gen_workflow_guide.py --write` 重新生成 [spec-review-amendment] |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | 删 §wayfinder→ff 衔接契约（≈30 行） |
| `CLAUDE.md`（本仓） | 删「四入口选择规则」段；删「旧入口 sunset 条件」段；删 grill-with-docs 段落；更新 impl-pipeline 缺省描述；删手动限制引用 |
| `sdflow-init/assets/snippets/claude-section.md` | 同步 CLAUDE.md 的删改（此为下推给消费项目的模板） |

#### 2.3 局部修改的文件

| 文件 | 改动概要 |
|------|----------|
| `sdflow-spec/SKILL.md` | frontmatter 删 `disable-model-invocation: true`；description 删「由人显式触发」 |
| `sdflow-ship/SKILL.md` | 删 `RUN_SOP` gate 分支描述；更新 impl-pipeline 缺省说明 |
| `sdflow-ship/scripts/ship_gate.py` | 删 `RUN_SOP` verdict 定义 + `tg02_hit` 检测函数 + `emit_windowed` 中 RUN_SOP 调用点（≈17 处） |
| `sdflow-ship/tests/*.py` | 删 RUN_SOP 相关测试用例（≈21 处） |
| `openspec/config.yaml`（本仓） | 更新 impl-pipeline 注释（缺省说明改为 tickets） |

### 3. ship_gate.py RUN_SOP 删除策略

RUN_SOP 在 gate 状态机中的角色：
- **verdict**: 当 proposal 命中 `〔TG-02` 且 `{change}-sop.md` 缺失时输出
- **emit_windowed 入口**: 与 RUN_PLAN/CONTINUE_IMPL 共享 `guard_design_freshness` 窗口检查

删除策略：
1. 删除 `tg02_hit()` 函数及其调用
2. 删除 `decide()` 中 RUN_SOP 分支（verdict 定义 + emit_windowed 调用）
3. 保留 `guard_design_freshness` 和 `emit_windowed` 函数不变——它们仍被 RUN_PLAN/CONTINUE_IMPL 使用
4. 删除 verdict 契约表中 `RUN_SOP` 行
5. 从所有 docstring/注释中移除 `RUN_SOP` 引用

**测试策略**：删除 RUN_SOP 相关测试用例，确保剩余测试全绿。`emit_windowed` 的窗口行为由 RUN_PLAN/CONTINUE_IMPL 的测试覆盖。

### 4. impl-pipeline 缺省翻转

| 项 | 旧 | 新 |
|----|----|----|
| config.yaml 无 `impl-pipeline` 键 | 走 superpowers（writing-plans → subagent-dev） | 走 tickets（sdflow-implement） |
| config.yaml `impl-pipeline: tickets` | 走 tickets | 走 tickets（不变） |
| config.yaml `impl-pipeline: superpowers` | 走 superpowers | 走 superpowers（不变） |

翻转点在 `sdflow-implement/scripts/impl_route.py`（`route` 子命令的缺省值，9 处 `return "superpowers"` 硬编码 + `_cmd_route` 的展示折叠逻辑需对称翻转）和 `sdflow-ship/SKILL.md`（文档描述）。[spec-review-amendment: 路径修正 + 复杂度补充]

### 5. sdflow-spec 自动触发规则

写入 workflow 文档和 `claude-section.md`：

> 判断需要开 change 时，模型 SHALL 直接 invoke `/sdflow-spec`。explore 中人示意收敛（如"开搞"、"做吧"、"开 change"）→ 模型自动 invoke `/sdflow-spec`。模型 MUST NOT 自主判断「该开 change 了」——须有人的示意信号。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

## Risks / Trade-offs

- **下游静默翻转**：15 个无显式 `impl-pipeline` 键的项目在 `sdflow-init update` 后从 superpowers 翻到 tickets。风险可接受（tickets 是超集，不退化；需旧管线显式加 `impl-pipeline: superpowers`）。
- **embedded-test-sop 不可恢复**：skill 目录和 gate 代码同时删除，`git revert` 是唯一恢复路径。
- **sdflow-spec 误触发**：模型可能在不恰当时机自动触发 sdflow-spec。诚实边界：唯一兜底是指令层自报，无机械门；副作用（分支/文件）在 HARD-GATE 之前已产生，误报后果是需要人工清理（分支可删、change 目录可删，纯本地可逆），而非被 HARD-GATE 拦截。五问速算：概率低、影响小可逆、完美成本高 → 接受。[spec-review-amendment: 修正 HARD-GATE 兜底措辞为诚实边界]

## Compliance

- **DOC-1**（正文即最终态）：workflow.md G1 分析移入附录（D4）。
- **通则③**（以目标为准）：不因「现有文档量大」而保留无用段落。
- **通则④**（简化方案）：不重构 ship_gate.py 整体架构，只删 RUN_SOP 分支。
