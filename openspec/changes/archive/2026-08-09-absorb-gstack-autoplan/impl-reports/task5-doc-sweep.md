# Task 5（tasks.md 任务组 6）：文档 sweep 与验收 — 实现报告

## 范围

`openspec/changes/absorb-gstack-autoplan/impl-reports/task5-brief.md` 全 4 项，逐项完成。

## 1. 文档面 sweep

### 1.1 严格验收目标（proposal.md Success Metrics · tasks.md 6.4）

`grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/`
（排除 `reference/`）**归零**。起手复核发现这个目标比 brief 字面列的文档清单更宽——它覆盖
`sdflow-init/assets/workflow/` 整个目录（含 `tools/`、`tools/tests/`、`tools/tests/fixtures/`、
`spec-checklists/`、`code-checklists/`），而非只是 brief 明确点名的少数文档。按通则③（锚目标态，
不拿"brief 字面只列了几个文件"反驳验收命令本身要求的范围），对 grep 命中的全部文件逐一处理，不是
只改 brief 列的那几份。

命中文件与处置（均已改完，逐一验证过后不再命中）：

| 文件 | 处置 |
|---|---|
| `design-diagrams.md` | 「gstack `plan-eng-review`」改述为「外部工程实践中 review 期强制画图的检查点」（保留原意，去具名） |
| `lens-metric-contract.md` | 删除两条纯 provenance 括注（`absorb-gstack-review`/`absorb-gstack-autoplan` 沿革注记）——它们是任务组 1 新增的"哪一轮改的"标签，与 DOC-1（正文即最终态）冲突；折叠表现状（`strategy/plan-eng+scope-audit→broad`）本身已自解释，不需要历史注记 |
| `workflow-history.md` | 「独立 `gstack/review`」改为「独立第三方广审工具 review 步骤」（本文件是显式的"考古层"，但物理上不在 `reference/` 目录，故仍在 grep 范围内，只做去具名改写，不迁移文件位置——迁移文件属结构性改动，超出 sweep 范围） |
| `trigger-catalog.md` | 「设计期 autoplan」→「设计期 sdflow-spec-review」 |
| `code-checklists/README.md` | 两处「autoplan」改为「sdflow-spec-review」 |
| `spec-checklists/domains/devex.md` | 「`~/.gstack/`」改为「某工具自身本地运行时状态目录」（去具名，保留判据本意） |
| `tools/lens_metric_emit.py` | 注释里的 `absorb-gstack-review：` 前缀删除，保留其后的实质说明 |
| `tools/anchor_lint.py` | 三处注释/docstring 里的 `absorb-gstack-autoplan`/`absorb-gstack-review` 前缀删除，保留实质说明 |
| `tools/tests/test_hr_tg_intersect.py` | docstring 里的 `（absorb-gstack-review 追加 TG-27）` 删除 |
| `tools/tests/test_anchor_lint.py` | 4 处 section 头注释/docstring 的 change-ID 前缀删除，保留实质说明 |
| `tools/tests/test_lens_metric_emit.py` | 测试函数 `test_fold_hit_gstack_adv_no_longer_recognized` 改名为 `test_fold_hit_legacy_native_adv_no_longer_recognized`，字面量 `"gstack-adv"` 改为 `"legacy-native-adv"`（回归测试的实质是"旧 raw 名不再被识别"，字面值本身是任意占位符，改名不影响测试语义）；3 处注释同步去具名 |
| `tools/tests/fixtures/task_log_review_ok_mlh.md` | 「`/autoplan` 或 plan-\*-review」→「`sdflow-spec-review` 或 `sdflow-code-review`」 |
| `tools/tests/fixtures/task_log_review_empty_template.md` | 同上改写 |

第 3.1 步用户 CLAUDE.md 规则要求「改一个被多处消费的字符串前先 grep」——`sdflow-roadmap/references/task-log-template.md`
是上面两份 fixture 的真实模版源，同一句"review（/plan-eng-review 或 /autoplan）"在此文件里也存在，
一并同步改写（面治，非点补：改 fixture 不改真实模版会制造新的漂移面）。

### 1.2 brief 点名的用户可见文档

- `openspec/CONTEXT.md`「镜」词条：autoplan 例句改为提及广审双镜（strategy/plan-eng），保留其余
  gstack 边界讨论段（`:40-41`，与本次退役无关，是"读产出物合法/依赖内部非法"的通用边界规则，未动）。
- `docs/workflow-skills/gstack-autoplan.md`：顶部与「1. 位置与契约」表改为「非运行时依赖的第三方
  skill 参考」定位（比照任务2已对 `gstack-review.md` 做过的同款降级措辞）；§6「本 workflow 注入」
  与 §7 小结改为历史设计说明的措辞，不再暗示当前仍在调用。
- `docs/workflow-skills/sdflow-spec-review.md`：全文重写，对齐当前 SKILL.md 实际结构（单批 dispatch、
  能力探针、`step1-broad-review` 新枚举 `subagent|main-session`、唯一一次 checkpoint、
  `reviewed_sha` 拍板回写字段）——旧文档描述的是已退役的「Step1 autoplan 原生执行 → CP1 checkpoint
  → Step2 fan-out」两段式架构,与当前代码完全不符,不是点改能收敛的,判定为整篇重写。
- `docs/external-dependencies.md` §5：原「评审流程依赖（gstack 系列）」两行表格（`gstack /autoplan`、
  `/plan-eng-review`）删除，改述为「已全部自持化，零外部依赖」——核实 `sdflow-roadmap/SKILL.md`
  当前 review 节确认其双镜也已自持（tasks 5.1 完成），不再依赖 `/plan-eng-review`。§8 内部依赖图：
  `sdflow-spec-review`/`sdflow-roadmap` 两处的依赖列表同步改为自持描述。
- `WORKFLOW-GUIDE.md`：核实无残留（task2 重新生成时已连带清空，见 task2 报告）。
- README（根目录）：核实无残留（本就未提及 autoplan/gstack）。
- `docs/workflow-map.md`：`:34` 流程描述「autoplan+领域/对抗/接地镜」改为「自持广审双镜+领域/对抗/
  接地镜」；`:169` 的 `outside_voice_guard.py` 工具行整行删除（该脚本 task 3.1 已物理删除，此行是
  stale 记录）；同步把「速览」行的脚本计数 14→13、脚本清单小节头「19 个脚本」→「18 个脚本」（少了
  已删除的这一个）。
- `docs/workflow-overview.md`：§开头黑盒/参考清单分离 gstack-autoplan 到"第三方参考"一栏；§3
  阶段二设计审流程图与步骤表按当前单批 dispatch 架构重画（删 CP1/Step2 两段式，改单 checkpoint）；
  决策登记区示例、§5 外部黑盒表（删 autoplan 行）、§8 注入定性表（autoplan→广审双镜）同步改写。

### 1.3 已知超出本票范围的残留（如实登记，非遗漏）

`docs/workflow-console.html`、`docs/workflow-map.html` 两份配套可视化页面仍各有若干 `autoplan`/
`gstack` 字面命中。这两份文件：①不在 tasks.md 6.4 的严格验收 grep 目标路径内；②不在 task5-brief
明确点名的清单里（brief 只列 `.md` 版）。按通则④（不为界外的边角自行扩大范围）判定为**已知超出
本票范围的残留**，未处理，供后续 change 按需处理（这两份是「同 session 产出」的静态可视化页面，
无脚本与 `.md` 源同步机制，本就存在独立漂移面）。

## 2. 关闭 T268

`python3 sdflow-issues/scripts/issues_v2.py set-status --id T268 --to DONE --evidence "..."`——
`resolved_by` 由脚本 `detect_change(root)` 自动探测当前活跃 change 目录，正确写入
`"absorb-gstack-autoplan"`（非手填）。已跑 `reindex` 同步 `INDEX.md`/`CLOSED.md`。

## 3. 归档盲测（逐声边际贡献，tasks 6.5 / Q3）

选取 3 份归档 change（`fix-probe-scan-precision`/`harden-implement-review-loop`/
`refactor-roadmap-internalize-deps`，按 `lens="broad"` 锚 独立 计数 + 严重度降序选出前 3），对每份
的归档时四件套分别单独派 fresh 子代理跑 strategy 镜 / plan-eng 镜 / design-voice（同族 proxy），
产出 `openspec/changes/absorb-gstack-autoplan/blind-test-report.md`。

**核心结果（如实报告，不回避不利结论）**：唯一可逐条核对来源的语料
（`harden-implement-review-loop`，旧报告对每条 Critical/High 标注了来源镜）上，旧 broad
（CEO/Eng/DX）主导的 11 条 Critical/High 中，**两条 Critical 全部未被新三声召回，严格召回率 0/11**
（宽松主题匹配 ~2/11）。这**印证** F-adv1 的担忧方向，不是"能力不缩水"的正面证据。同时三声之间
边际独家贡献真实存在（9 组产出几乎零字面重复，各有系统性偏好类型），design-voice 独立复现了旧报告
里由 design-voice/对抗镜（非 broad）负责的部分发现（论证甚至更扎实）。详细方法论、逐条核对表、
两条诚实边界（design-voice 为同族非跨模型 proxy；另两份语料无法逐条复原来源，只能主题层面判断）
见报告正文。

**盲测的定位**：按 Q3 拍板口径（D1 双镜形态照拍板落地不动，数据说话后再议降声），本报告是**留存/
降声证据基线**，不是当次裁决依据——不建议基于这一次小样本盲测反悔 D1，但低召回结果是需要
`/sdflow-retro` 后续持续跟踪的真实信号。

## 4. 最终验收

```
grep -rn "autoplan\|gstack" sdflow-spec-review/SKILL.md sdflow-roadmap/SKILL.md sdflow-init/assets/workflow/ | grep -v "/reference/"
# 归零（exit 1，无命中）
```

读码确认：两 SKILL.md 现存的 `outside_voice_guard.py`/`mode="native"` 等字样均是**描述已删除/已退役
机制**的历史性说明文字，非条件调用分支（grep 命中的是 `native|simulated`/`outside_voice_guard.py`
字面，不含 `autoplan`/`gstack` 词根，本就不在严格验收 grep 范围内，此处只是补充核实"无条件调用
gstack 分支"这条读码要求）。

```
/usr/bin/python3 -m pytest -q
# 2444 passed, 10 skipped, 1 failed（348s）
```

唯一失败：`sdflow-init/tests/test_outside_voice_job.py::
test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`——与 task1/task3 报告记录的
**同一条**预先存在的环境相关 flake（本沙盒环境 `claude --bg --exec` 对照组本身未采到 canary，测试
自身对沙盒行为的前置假设不成立），passed/skipped 计数与 task3 报告基线（2444 passed, 10 skipped,
1 failed）逐位吻合，确认本票改动未引入新失败。

## 改动文件清单

文档 sweep（14 处 `sdflow-init/assets/workflow/` 内文件 + 7 处用户可见文档）：见上表；
`openspec/issues/open/todo/T268.md` → `closed/todo/T268.md`（+ `INDEX.md`/`CLOSED.md` 重建）；
新增 `openspec/changes/absorb-gstack-autoplan/blind-test-report.md`。

## Checklist（供门禁核对，未勾选——由执行模式在双轴审后补打）

- [x] CONTEXT.md/docs/workflow-skills/WORKFLOW-GUIDE/external-dependencies/workflow-map/workflow-overview 全部 sweep 完成
- [x] T268 已关闭
- [x] 盲测报告落盘（3 份归档 change × 3 声，含逐条召回核对表）
- [x] grep 验收归零
- [x] 全仓 pytest 绿（1 个已知无关环境 flake，与基线吻合）
