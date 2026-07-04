# superpowers-plan — ship-gate-hardening-2

> 阶段三实现计划（writing-plans 生成，TDD 逐任务）。追溯 design ADR-1/2/3 + specs R1/R2 + tasks §1-3。
> **本 change 自 checkpoint 用裸格式**〔设计门 Q1=A〕：每任务 commit 步 = `bash ~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "<描述>"`（裸，非命名空间——本 change dogfood parser/consumer，producer 格式靠测试验证、下个 change 首消费）。

## Global Constraints（design 领域约束逐字）

- gate 只读零副作用不变；假✅ 头号失效模式，取舍向假阴安全、假阳（假 SHIPPED/RUN_CODE_REVIEW/齐）禁止。
- 既有 B1/B2/B3/B4 语义**逐字不变**（全部裸格式回归测试 + test_gate_terminal 等仓级 328 不得回归）。
- 命名空间归属用**精确 `==change`**（非前缀）；正则命名组限 `[a-z0-9][a-z0-9-]*`。
- T32 回归测试 MUST 用**真实 git commit fixture**（非字符串 mock），否则测不出 startswith:263 漏改洞。
- 契约 9 点同批改齐（design scope-check 表）；漏权威源 workflow.md = T32 对主路径形同虚设。

### Task 1: T32 命名空间解析器 + 归属规则（parser/consumer 先行）
- [x] TDD 先写失败测试 `test_gate_namespace.py`：①判别性负例（plan={1,2}、当前 `checkpoint(demo:task1-)`、另一 `checkpoint(other:task2-)` 落同窗口 → done_tasks==["1"] CONTINUE_IMPL，用真实 git commit）；②向后兼容（全裸标签 → 计入=升级前行为）
- [x] 实现：`TAG_RE` 加可选命名组 `checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`；`done_task_ids(root, sha, change)` 归属规则（命名组非空→仅 `==change` 计入；空→窗口计入）；**`startswith("checkpoint(task")` 放宽为 `startswith("checkpoint(")`**〔A-F1，否则命名标签整条跳过〕；`decide()` 传 `change`
- [x] 回归：既有裸格式测试全绿（test_gate_impl_progress/tail/freshness）
- [x] commit: `checkpoint-commit.sh task1-namespace "T32 命名空间解析器+归属+startswith放宽"`

### Task 2: T32 producer 格式三契约点（权威源同批改齐）
- [x] `sdflow-init/assets/workflow/workflow.md:74`（bundle 唯一权威源）：checkpoint 步名 `task<N>-<slug>`→`<change>:task<N>-<slug>` + 注裸格式兼容
- [x] `sdflow-ship/SKILL.md:29`（消费引用）：同步改
- [x] `sdflow-ship/tests/test_workflow_authority.py:16`：断言 token 更新为命名空间格式（防旧 token 钉死反挡新格式）
- [x] commit: `checkpoint-commit.sh task2-producer "producer 三契约点同批改齐(权威源workflow.md+SKILL+authority测试)"`

### Task 3: T34 复选框分段绑定（行锚定+忽略代码块+重号 UNKNOWN）
- [x] TDD 先写失败测试：①全局单勾不放行未勾 task；②分段+checkpoint 并集；③fenced code 内伪框不算；④重号 Task→UNKNOWN
- [x] 实现：`checkbox_done_ids(plan)` 替换 `checkboxes_all`（按 TASK_TITLE_RE 切段、前言段忽略、行锚定 `^\s*-\s+\[[ xX]\]`、忽略 ```fenced```）；`plan_task_ids` 侧重号检测→UNKNOWN；`decide()` 合并 `done_ids=checkpoint_done ∪ checkbox_done`
- [x] 回归：test_checkbox_fallback_advances / test_uncommitted_plan_no_checkbox_unknown 绿
- [x] commit: `checkpoint-commit.sh task3-segment "T34 分段绑定+行锚定+忽略代码块+重号UNKNOWN"`

### Task 4: 头注释「已知不覆盖」+ :32 引用同步
- [x] `ship_gate.py` 头部：更新 line 32 `checkpoint(task<k>-` 引用为命名空间；「已知不覆盖」+「裸格式污染方 stacking+撞号残留（MUST NOT 用独立分支纪律缓解，见 adr/0008）」+ T33 工作树 dirty 停置
- [x] commit: `checkpoint-commit.sh task4-headnote "头注释已知不覆盖+命名空间引用同步"`

### Task 5: 全量 pytest 绿 + 收敛
- [x] `pytest sdflow-ship/tests/` 全绿（新增 R1/R2 锚测计入）+ 仓级 `pytest`（≥328 不回归）
- [x] commit: `checkpoint-commit.sh task5-green "全量 pytest 绿(仓级不回归)"`
