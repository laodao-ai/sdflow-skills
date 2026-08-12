# Task 4 impl-report: render-review-prefix.sh 与部署链

**R-ID:** SW-1
**执行位置说明**：本票由 worktree-isolated implementer 子代理执行；子代理所在 git worktree
（`agent-a201f332ce0de049a`）分支于 main（含 `remove-superpowers-pipeline` 归档），**不在**
`feat/implement-workflow-optimization-2026-08-p4` 分支上——`openspec/changes/implement-workflow-optimization-2026-08-p4/`
四件套在该 worktree 里不存在。design.md / specs / brief 均通过主检出（同仓「Additional working
directories」路径）以 Read 只读方式取得；本报告与全部代码/测试改动写在本 worktree 内，供上游按
既定流程合并回 p4 分支。

## 做了什么

### 1. `sdflow-init/assets/hack/render-review-prefix.sh`（新建，权威源）

按 brief / design / spec 的固定契约实现：

- `--layer code-review|spec-review`（必填）；缺失或非法值 → exit 64 用法错误。
- 三段固定序输出（**校验全部通过后才开始输出**，任何一段失败都在首次 `cat` 之前 exit，
  不存在半段前缀）：
  1. `$SDFLOW_HOME/hack/skill-principles.md` 全文（通则区块）
  2. 脚本内嵌 heredoc「评审子代理通用契约」：结构化 findings schema（`id/file/line/quote`
     或 `evidence_pack`/`severity`/`suggestion`/`confidence`）+ 引文纪律 + 输出封顶句
     「回传目标 ≤2k token，超出按严重度截优先」（T103，原文照抄 spec 措辞）+ 不问人
     （MUST NOT AskUserQuestion）
  3. 经 `$SDFLOW_HOME/hack/resolve-workflow.sh` 解析出的 `$RULES_ROOT` 下对应层
     base checklist 全文（`code-checklists/code-review-base.md` 或
     `spec-checklists/spec-quality-base.md`）
- 三个源分别校验存在性/可执行性/解析成功；任一失败 → `problem=/cause=/fix=` 三段式
  stderr + 非零退出（`skill-principles.md` 缺失、`resolve-workflow.sh` 缺失或不可执行、
  `resolve-workflow.sh` 解析失败〔canonical 不 sane〕、base checklist 缺失，四类均覆盖）。
- 复用 `resolve-workflow.sh` 既有的 `SDFLOW_HOME` 环境变量隔离契约（缺省 `~/.sdflow`，
  测试可重定向、绝不写真实 `$HOME`）——与仓内既有 hack 脚本同风格，不另造一套配置口径。
- 已 `chmod +x`。

**实现期发现并修复的一个真实 bug（非脑内假设，实测复现）**：macOS 系统 `/bin/bash`
（3.2.57，非 GNU bash 新版）在 `set -u` 下，裸 `$VAR` 变量展开若紧邻全角标点（如
`）`「」，，`）且中间无 ASCII 分隔符，会把该标点的首字节误判进变量名，触发
`unbound variable` 崩溃（`SDFLOW_HOME`：`$SDFLOW_HOME，` → 报错变量名
`SDFLOW_HOME<mojibake>`）。修法：改用 `${VAR}` 显式加花括号消歧（`resolve-workflow.sh`
既有代码对同一变量已用此写法，本次对齐）。已扫描全文件消灭其余同类裸引用（面治非点补）。
此坑由本票新写的 fail-loud 分支测试（`test_missing_base_checklist_*`）在本机 GNU
bash 3.2 环境下实测触发并抓获，非凭空猜测。

### 2. setup.sh 部署链

**核验结论：无需改动。** `setup.sh` 第 536 行起对 `sdflow-init/assets/hack/*.sh` 做
glob 遍历、逐个 `cp` + `chmod +x` 到 `$sdflow/hack/`，不做任何显式文件名枚举——新增的
`render-review-prefix.sh` 会被自动纳入下一次 `setup.sh` 运行。另核验了
`outside-voice-job.py` 的 `capability-manifest.json`（`MANIFEST_ENTRIES` 硬编码
`("outside-voice-job.py", "outside-voice.sh", "skill-principles.md")` 三项）——
该清单是 outside-voice 异步 job 能力探针的专属子集，与本脚本无关，未纳入也不需要纳入。

## 测试

新建 `hack/tests/test_render_review_prefix.py`（14 用例，TDD：先写全部用例确认红态
——脚本不存在时 11/14 失败 —— 再实现使其转绿）。用真实 `resolve-workflow.sh` /
`skill-principles.md` / 两份 base checklist 的**字节拷贝**放进 `tmp_path` 自备的
`SDFLOW_HOME` 沙盒（过 `resolve-workflow.sh` 自身 `sane()` 检查的最小形状：
`workflow.md` / `spec-checklists` 非空 / `code-checklists` 非空 / `tools` 非空 /
`lens-metric-contract.md` 非空），零全局副作用（CLAUDE.md「开发期测试三层」第 2 层，
不碰真实 `~/.sdflow/`）。覆盖：

- `test_script_is_executable`
- `test_layer_produces_nonempty_output`（parametrize 两层）
- `test_output_is_byte_stable_across_two_runs`（parametrize 两层，spec Scenario
  「稳定前缀 byte-stable」）
- `test_output_contains_all_three_fixed_sections_in_order`（三段固定序）
- `test_common_contract_section_has_required_clauses`（四子项字面存在）
- `test_missing_layer_arg_is_usage_error` / `test_invalid_layer_value_is_usage_error`
- `test_missing_principles_fails_loud_with_guidance`
- `test_missing_resolver_fails_loud_with_guidance`
- `test_resolver_failure_propagates_fail_loud`（canonical 不 sane）
- `test_missing_base_checklist_no_partial_output`（spec Scenario「前缀源缺失
  fail-loud」，MUST NOT 半段前缀）
- `test_missing_base_checklist_other_layer_still_works`（缺失只影响该 layer，证明
  门按需读取而非启动时全量预检）

```
$ /usr/bin/python3 -m pytest hack/tests/test_render_review_prefix.py -q
14 passed in 2.79s
```

全仓回归：`/usr/bin/python3 -m pytest -q`（全量套件，含既有 hack/tests 与各 skill
tests）在本次执行中因套件体量超出前台 120s 超时被移入后台运行；结果将在完成后另行确认，
本报告先如实标注该项**尚待补充**（见下「未尽事项」），不假称已验证全绿。

## 验收对照（brief 五条）

- [x] `render-review-prefix.sh --layer code-review` 按固定序输出通则 + 通用契约段 + base checklist
- [x] `render-review-prefix.sh --layer spec-review` 同构输出对应层
- [x] 任一源缺失 ⇒ 非零退出 + stderr 含 problem+cause+fix（MUST NOT 输出半段前缀）
- [x] byte-stable golden 测试：连续两跑逐字节同 + 源缺失非零退出
- [x] setup.sh 部署链：脚本随 hack 拷贝到 `~/.sdflow/hack/`（核验既有 glob 机制已覆盖，无需改动）

（按流程纪律，复选框由双轴审通过后统一补打进 `tasks.md`，此处只做自查对照。）

## 未尽事项 / 遗留

- **全仓 pytest 全量结果未在本报告落锚**：因超时被移至后台，尚未拿到最终 exit code。
  上游合并前建议在合并后的 p4 分支上补跑一次 `pytest -q` 确认无回归（本票新增文件本身
  不改动任何既有脚本/测试，预期零冲突，但未亲验不敢断言）。
- **未在真实 `~/.sdflow/` 上做端到端 `setup.sh` 全局窗口验证**（CLAUDE.md「开发期测试
  三层」第 3 层，机器级影响、需时间盒）——按纪律，日常开发只需到第 2 层（沙盒消费仓层），
  本票测试已满足该层；第 3 层留给本 change 的「Migration Plan 步骤 0：实现期自审窗口」
  统一执行，不在单票内单独开窗。
- worktree 隔离导致本 worktree 不在 p4 分支：本报告与代码改动需要上游按其编排机制合并回
  `feat/implement-workflow-optimization-2026-08-p4` 分支，本票不负责该合并动作。

## 涉及文件

- `sdflow-init/assets/hack/render-review-prefix.sh`（新建，可执行）
- `hack/tests/test_render_review_prefix.py`（新建，14 用例）
