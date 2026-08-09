# Task 1：Bundle 机械层同步与 retro 归属修正 — 实现报告

## 范围

`openspec/changes/absorb-gstack-autoplan/impl-reports/task1-brief.md` 全 7 项验收，逐项完成。

## 1. `lens-metric-contract.md` fold 块 + 散文同步

文件：`sdflow-init/assets/workflow/lens-metric-contract.md`

- **机读折叠块**（`lens-metric-fold` fence）：`autoplan-ceo/design/eng/dx: broad` 四行直接替换为
  `strategy: broad` + `plan-eng: broad`（不共存），`scope-audit: broad` 保留。
- **折叠表散文注记**（§折叠表）：示例句 `autoplan(CEO/Eng/DX/design)+scope-audit→broad` 改为
  `strategy/plan-eng+scope-audit→broad`；新增一条 `absorb-gstack-autoplan` 沿革注记（比照既有
  `absorb-gstack-review` 注记先例），说明四行→两行替换的语义（自持化为 strategy/plan-eng 两镜）。
- **跨模型性段（§跨模型性，:19-20 附近）**：原文声称矩阵关系式判定逻辑由「`anchor_lint` 与
  `outside_voice_guard` 各自本地重实现」（双实现表述）——改为「收敛为 `anchor_lint` 单一本地实现」，
  并注记 `outside_voice_guard` 的跨工具重实现随其复用路径退役（本 change 后续 task 3.1/3.2）而并入。
- **机读取值域块的同款回声（§机读取值域，:23 附近）**：该段原样重复了「`anchor_lint`/`outside_voice_guard`
  各自本地重实现」的说法并显式引用「见上「跨模型性」段」——若只改 :20 不改 :23，文档会自相矛盾（:23
  仍声称 :20 说了双实现）。判定为同一事实在同文件内的两处回声，非独立范围扩张，一并同步修正为
  「`anchor_lint` 单一本地实现」。tasks.md 1.5 原文只显式点了 :19/:44 两处，但基于 DOC-1（正文一致性）
  与规则①（改一处先 grep 影响面）判定 :23 必须同步，否则归档后文档内部矛盾。

## 2. `anchor_lint` golden 测试补用例

文件：`sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`（新增于
「absorb-gstack-autoplan Task 1」小节，紧接既有「absorb-gstack-review Task 1」小节之后）

枚举常量（`_MIRRORS_LEGAL`/`_FANOUT_MIRRORS`）零改动，仅补测试覆盖新形态：

- `test_fanout_spec_review_single_batch_mirrors_broad_scenario`：DD1 单批 dispatch 下，spec-review
  报告 `mirrors=` 同时含 `broad,domain,adversarial,grounding,history`、`subagents="available"` 时合法放行。
- `test_fanout_spec_review_unavailable_mirrors_broad_alone_ok`：spec-review 广审降级为主 session 亲做
  （DD3）时，`mirrors="broad"` 单独出现于 `unavailable` 场景合法放行（不进 dead-fanout 计数集）。
- `test_step1_broad_review_mode_main_session_lint_passes`：`step1-broad-review` 锚新枚举值
  `mode="main-session"`（对照既有 `mode="subagent"` 测试）不触发任何与 mode 相关的校验——lint 只验
  锚族存在性，mode 值为主 session 自报、无机械枚举校验（design.md DD3 诚实边界）。

同时把既有 `test_fanout_mirrors_unknown_token_hint_mentions_sdflow_init_update` 改名为
`..._mentions_setup_sh` 并更新断言（见第 4 项）。

## 3. `sdflow-retro` `stage_walltimes` 归属语义修正

文件：`sdflow-retro/scripts/retro_report.py` + `sdflow-retro/scripts/tests/test_retro_report.py`

- **attribute-to-next**：相邻提交差 `[cur,nxt)` 原计入 `cur`（前一提交）的阶段，改为计入 `nxt`
  （后一提交，checkpoint 语义=工作完成点）的阶段。修正既有错账：旧口径下
  `checkpoint(sdflow-spec-generate)→checkpoint(spec-review-autoplan)` 区间因 `cur` 映射
  `stage="ff"` 而把 Step1 广审墙钟误归 `ff`；新口径下该区间归 `nxt` 的阶段（`spec-review-autoplan`/
  `spec-review` 均映射 `spec-review`），归属正确。
- **`is_archive_rename` 判定对象**由 `cur` 换 `nxt`（主循环内），归档 rename 提交与前一 checkpoint
  之间的墙钟正确归 `done`，不再误归前一 checkpoint 自身的阶段。
- 边界特例：原「末提交若是 archive rename，单独标记 done 存在（无后继 Δ）」对称翻转为
  「首提交若是 archive rename，单独标记 done 存在（无前驱 Δ）」——旧口径下末提交从不作为 `cur`、
  新口径下首提交从不作为 `nxt`，两者是同一类边界情形在语义翻转后的对称位置。
- `_STAGE_RULES` 枚举本身零改动——task1-brief 中「修正 `("sdflow-spec-generate","ff")` 映射」核实
  为 tasks.md 1.3 对**根因**的描述（该映射规则 + 旧 attribute-to-previous 语义组合导致误账），不是要求
  改映射规则的取值；attribute-to-next 语义切换后误账自动消失，规则本身继续有效（`sdflow-spec-generate`
  checkpoint 自身代表的仍是 ff 阶段工作，只是其归属机制变为由「谁在其之后完成」决定）。
- 补 4 个回归测试：
  - `test_stage_walltimes_and_negative_clamp`（既有测试，按新语义更新断言——TDD 先改断言确认在旧实现
    下会红，再改实现使其转绿）。
  - `test_stage_walltimes_historical_spec_review_autoplan_sequence_no_longer_misattributed`：历史序列
    （含 `checkpoint(spec-review-autoplan)` 中间标签）不再误归 ff。
  - `test_stage_walltimes_new_single_checkpoint_sequence_attributes_to_spec_review`：新序列（DD1 退役
    中间 checkpoint 后的单 checkpoint 形态）整体归 spec-review。
  - `test_stage_walltimes_archive_rename_attributed_via_nxt_not_cur`：真实 git 仓库场景验证
    `is_archive_rename` 的 cur→nxt 翻转（归档收尾墙钟不再误归前一 checkpoint 的阶段）。
- `openspec/retro/report.md` 已重跑再生（`python3 sdflow-retro/scripts/retro_report.py --root .`）。
  覆盖从设计文档撰写时的 49 归档 change 增长为当前 68 归档 + 1 活动 = 69（正常时间推移导致，非本次
  改动引入）；已验证再生幂等（连续跑两次 diff 无变化）。

## 4. `_MIRRORS_UPGRADE_HINT` 失效指引修复

文件：`sdflow-init/assets/workflow/tools/anchor_lint.py`

`"若本仓 openspec/workflow/ 为旧版，请先跑 sdflow-init update"` 改为
`"若本仓 openspec/workflow/ 为旧版，请回运行 checkout 跑 bash setup.sh"`（真实部署模型 adr/0039 下，
消费仓规则经全局 canonical 实时解析，不再有本地 bundle 副本靠 `update` 刷新；真正过时的是运行 checkout
未 `git pull` + `bash setup.sh`）。对应测试改名为
`test_fanout_mirrors_unknown_token_hint_mentions_setup_sh` 并更新断言（含反向断言
`"sdflow-init update" not in detail`，防止改一半留旧文案残留）。

## TDD 纪律记录

- `_MIRRORS_UPGRADE_HINT` 文案：先改测试断言 → 跑确认红（旧文案 `sdflow-init update` 命中断言失败）
  → 改实现 → 转绿。
- `stage_walltimes` attribute-to-next：先改 4 个测试（1 个既有断言更新 + 3 个新增）→ 跑确认全部 4 个红
  （旧实现下断言值不符）→ 改实现（cur→nxt 双处翻转）→ 全部转绿。
- anchor_lint 新增的 3 个 golden 用例针对**零代码改动**的既有行为（枚举/判定逻辑本就支持 broad 与
  `main-session`），非 TDD 意义上的红→绿新增行为，而是补测试覆盖面——补充前已确认对应生产代码路径
  （`_parse_mirrors`/`check_fanout_consistency`/`check_existence` 对 `step1-broad-review` 只验族存在性）
  确实未变，新用例是纯覆盖面而非实现变更。

## 验证

```
/usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q   # 155 passed
/usr/bin/python3 -m pytest sdflow-retro/scripts/tests/test_retro_report.py -q               # 45 passed
/usr/bin/python3 -m pytest -q                                                                # 2481 passed, 10 skipped, 1 failed
```

全仓跑出 1 个失败：`sdflow-init/tests/test_outside_voice_job.py::
test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`。已核实与本票改动**无关**——
`git stash` 掉本票全部改动后单独重跑该测试，**同样失败**、报错文本完全一致（对照组 `claude --bg --exec`
的裸输出在本沙盒环境里未出现在 `claude logs` 中，是该测试自身对沙盒环境 `claude` CLI 行为的前置假设
不成立，与 fold 表 / anchor_lint / retro 归属逻辑无任何耦合）。这是本仓 pre-existing 环境相关失败，
不在本票 blocked-by 链范围内，未做处理。

## 改动文件清单

- `sdflow-init/assets/workflow/lens-metric-contract.md`
- `sdflow-init/assets/workflow/tools/anchor_lint.py`
- `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`
- `sdflow-retro/scripts/retro_report.py`
- `sdflow-retro/scripts/tests/test_retro_report.py`
- `openspec/retro/report.md`（再生产物）
