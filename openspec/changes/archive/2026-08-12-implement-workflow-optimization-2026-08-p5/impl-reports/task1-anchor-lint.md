# Task 1 · anchor_lint 拍板三问机验实现

> Change: `implement-workflow-optimization-2026-08-p5` · Task 1（R-ID: GQ）
> 执行分支：`worktree-agent-ab920dadb96d4f28b`（隔离 worktree，base = `main` @ `f2fac39d`）
> 说明：本 worktree 与 `feat/implement-workflow-optimization-2026-08-p5`（承载四件套 + tickets.md 的
> 分支）非同一分支——`task1-brief.md` 未在本 worktree 落盘，故本报告开工前先从
> `feat/implement-workflow-optimization-2026-08-p5` 分支用 `git show` 取回 `tasks.md`/`tickets.md`/
> `design.md` 三份权威文本核实任务全文（详见下方「任务来源核验」），未凭空猜测契约细节。

## 任务来源核验

未见 `impl-reports/task1-brief.md`（本 worktree 未 checkout 到 change 分支）。改为：

```
git show feat/implement-workflow-optimization-2026-08-p5:openspec/changes/implement-workflow-optimization-2026-08-p5/tasks.md
git show feat/implement-workflow-optimization-2026-08-p5:openspec/changes/implement-workflow-optimization-2026-08-p5/tickets.md
git show feat/implement-workflow-optimization-2026-08-p5:openspec/changes/implement-workflow-optimization-2026-08-p5/design.md
```

三份文本口径一致（design「Db 机验锚形态」+ tasks.md 1.1/1.2/1.4 + tickets.md「Task 1」），据此实现。

## 实现内容

### 1. `sdflow-init/assets/workflow/tools/anchor_lint.py`

- `ANCHOR_PREFIXES` 新增一行：`"<!-- sdflow:gate-questions v1": "gate-questions"`。
- 新增 `GATE_QUESTIONS_Q_VALUE = "scope,deps,risk"` 常量（q 值单一真相源，供 check 函数比对）。
- 新增函数 `check_gate_questions(report_text, layer, findings)`：
  - 签名严格照 design/tickets 锚定形——第三参 `findings` 为调用方传入的可变 list，函数体内
    `findings.append(...)` 就地写入、**不 return**（与其余 `check_*` 的 return-list 惯例不同，
    这是 design Db 明确拍板的形态，非随手改）。
  - `if layer != "spec-review": return` —— 早返回，`layer=code-review` 恒不查（D2）。沿
    `check_declared_sites` 的 layer-conditional 模式；**MUST NOT** 照抄 `check_fanout_consistency`
    「无 layer 签名、`main()` 无条件调用」的形态（那样会让 code-review 报告也被检查，违反 D2）。
  - fence 外存在性恒须：`fence_outside_lines()` 取非围栏行，用既有 `anchor_prefix()` 识别
    `gate-questions` 锚族——**未新起裸 grep**，复用既有 fence-aware 口径（fence 内示范锚天然不算）。
  - 缺锚 → `{"kind": "missing-gate-questions", ...}`。
  - fence 外 ≥2 条 → `{"kind": "duplicate-gate-questions-anchor", ...}`（fail-closed，沿
    `check_fanout_consistency` 的 `duplicate-fanout-anchor` 先例，早返回不继续解析 kv）。
  - 缺 `q=` 属性（`parse_kv` 结果无 `q` 键）→ `{"kind": "missing-field", "field": "q", ...}`。
  - `q` 值与 `GATE_QUESTIONS_Q_VALUE` 逐字不等（缺项/增项/乱序皆不等）→
    `{"kind": "q-value-mismatch", "field": "q", ...}`。
  - **未复用/扩展** `check_existence`/`MANDATORY` 列表（design 明令：该函数 `layer` 参数是死参，
    从不真按 layer 分流，混进去会让 code-review 也被强制要求该锚）。
- `main()` 接线：在 `check_declared_sites(...)` 之后、`if metrics_on:` 分支之前插入一行
  `check_gate_questions(report_text, args.layer, violations)`（always-on，不受 `metrics_on` 门控，
  与 `check_fanout_consistency`/`check_declared_sites` 同一律）。

净增 44 行（`git diff --stat`）。

### 2. `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`

新增 10 个测试函数，覆盖「七组契约测试」+ 3 个 main()-接线端到端回归锁：

| # | 测试函数 | 覆盖组 |
|---|---|---|
| 1 | `test_gq_positive_no_violation` | 正例 |
| 2 | `test_gq_missing_anchor_violation` | 缺锚 |
| 3 | `test_gq_q_value_variants_all_mismatch` | q 变异（缺项·增项·乱序，同一测试三子案例） |
| 4 | `test_gq_missing_q_attribute_violation` | 整个缺 `q=` 属性（含互斥断言：非 q-value-mismatch） |
| 5 | `test_gq_duplicate_anchor_fail_closed` | 重复锚 |
| 6 | `test_gq_fence_inside_anchor_not_counted` | fence 内示范不算 |
| 7 | `test_gq_code_review_layer_not_checked` | code-review layer 不查（含畸形锚场景） |
| 8 | `test_gq_cli_end_to_end_violation_spec_review` | main() 接线回归锁：spec-review 缺锚端到端 VIOLATION |
| 9 | `test_gq_cli_end_to_end_clean_spec_review` | main() 接线回归锁：spec-review 补锚端到端 CLEAN |
| 10 | `test_gq_cli_code_review_layer_no_gate_questions_needed` | 回归锁：既有 code-review 端到端正例不被误伤 |

第 8–10 组超出 tasks.md 字面「七组」，是本人主动加的 main() 接线验证（`check_gate_questions` 只在单测
层面调用无法证明真的接进了 CLI；design scope-check 表要求「实现时逐行核对」全部站点，main() 是站点
之一）——按四条通则④判断：成本低（复用既有 `_run`/`_ov`/`_ds` 夹具）、防「函数写对但忘接线」的真实
失效模式，未扩大改动面（仍在 `test_anchor_lint.py` 单文件内）。

### 3. Task 1.4：p4 归档报告副本回放核验（手工验收）

样本：`openspec/changes/archive/2026-08-12-implement-workflow-optimization-2026-08-p4/spec-review-report.md`
（该报告产出于本 change 之前，天然缺 `sdflow:gate-questions` 锚）。

操作（副本，**未改动归档原件**——`git status --porcelain` 核对该目录全程空输出）：

1. 复制到 scratchpad：`.../scratchpad/gq-replay/spec-review-report.md`。
2. 原样跑：
   ```
   python sdflow-init/assets/workflow/tools/anchor_lint.py \
     --report <copy> --layer spec-review \
     --trigger-catalog sdflow-init/assets/workflow/trigger-catalog.md --root .
   ```
   结果：`[anchor_lint] VIOLATION {'kind': 'missing-gate-questions', ...}`，**exit=1**（FAIL，符合预期）。
3. 手工在副本的 `<!-- sdflow:declared-sites v1 declared="design-voice" -->` 行后插入一行
   `<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->`。
4. 再跑同一命令：`[anchor_lint] CLEAN`，**exit=0**（PASS，符合预期）。
5. `git status --porcelain openspec/changes/archive/2026-08-12-implement-workflow-optimization-2026-08-p4/`
   输出为空 —— 归档原件全程未被触碰。

## 测试结果

```
python -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q
168 passed in 10.41s
```

168 = 158 既有 + 10 新增，既有测试**零回归**（含此前 code-review 层端到端正例，未因新 always-on
检查被误伤——见上表第 10 组）。

全仓 `pytest -q` 属 Task 6（实现验证收尾）范围，Task 1 checklist 只要求 `test_anchor_lint.py` 自身
无回归（已满足）；本次未额外跑全仓套件（跑一次逼近 10 分钟量级，超出本票范围，留给 Task 6 汇总）。

## Global Constraints 逐条核对

- 拍板三问是增量锚：新锚不改动既有 6 个锚族（`hr-tg`/`lens-metric`/`outside-voice`/
  `fanout-capability`/`declared-sites`/`step1-broad-review`）的任何检查语义——本次只新增
  `ANCHOR_PREFIXES` 一行 + 一个独立新函数，未改动任何既有 `check_*` 函数体。✅
- MUST NOT 动 ship_gate.py、评审镜 roster、裁决协议（adr/0041）、model/effort 分档链——本票未触碰
  这些文件（`git diff --stat` 只列 anchor_lint.py 及其测试文件两处）。✅
- anchor_lint 改动走权威源 `sdflow-init/assets/workflow/tools/`，未在消费仓改——✅（本仓项目侧无
  `openspec/workflow/tools/` 镜像，D13 后消费仓经全局 canonical 解析，无需同步）。

## 改动文件清单

- `sdflow-init/assets/workflow/tools/anchor_lint.py`（+44 行）
- `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`（+116 行）

## 完成状态

Task 1 全部四项验收标准均已满足：

- [x] `ANCHOR_PREFIXES` 登记 + `check_gate_questions` 函数实现（layer 分治、q 值校验、重复锚
      fail-closed、fence-aware）
- [x] 七组契约测试全部通过（正例 / 缺锚 / q 变异四子项 / 重复锚 / fence 内 / code-review 不查）
- [x] p4 归档报告副本回放：原样 FAIL → 加段后 PASS
- [x] 既有 anchor_lint 测试无回归（158/158 绿）

> 注：`tickets.md` 的验收复选框本身不由本 report 勾选（信号权威表：双轴审通过后由执行模式补打）。

## 遗留说明（诚实边界，非本票缺陷）

- 本 worktree 未持有 `feat/implement-workflow-optimization-2026-08-p5` 分支上的四件套/tickets.md/
  audit 目录（该分支被其他 worktree 占用，无法在本 worktree checkout）。本报告落在本 worktree 的
  `openspec/changes/implement-workflow-optimization-2026-08-p5/impl-reports/` 下（新建目录，仅含
  本报告），后续需由编排层把本 worktree 的两处代码改动与该报告一并合并/cherry-pick 回
  `feat/implement-workflow-optimization-2026-08-p5` 分支。
- `sdflow:gate-questions` 锚是否真被 `sdflow-spec-review/SKILL.md` Step4 正确落锚（三问正文小节
  真实在场）不属本票范围——那是 Task 3（Blocked-by: 1）的工作；本票只交付机验检查器本身。
