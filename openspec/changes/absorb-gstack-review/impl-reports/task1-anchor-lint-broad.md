# Task 1: anchor_lint 接纳 broad 镜而不误判降级为自相矛盾

## 环境前置说明

本 worktree 初始时未包含 `openspec/changes/absorb-gstack-review/` 目录（分支
`worktree-agent-a706bba930029dd5c` 的起点 `9a7e09d` 是 `feat/absorb-gstack-review`
的父提交，落该 change 四件套 + tickets.md 的提交 `2445355`
`checkpoint(absorb-gstack-review:plan): 出 ticket 落盘（B1 窗口锚）` 未同步进本 worktree），
且 `impl-reports/task1-brief.md` 在任何分支上都不存在——不是本 worktree 独有的缺失。

处置：确认 `feat/absorb-gstack-review` 相对本 worktree HEAD 的唯一差异是该提交且**纯新增
文件**（`git diff --stat` 核实，12 个文件、只新增不改动任何已有代码），执行
`git merge --ff-only feat/absorb-gstack-review` 补齐（fast-forward，非破坏性、不改写任何历史）。
补齐后以 `tickets.md`「### Task 1」段（第 68–88 行）为本票权威来源——它是比缺失的
`task1-brief.md` 更上游的定稿材料（tasks.md 2.2/2.3/2.5 的展开版），并非我自拟的替代品。

## 做了什么

修改 `sdflow-init/assets/workflow/tools/anchor_lint.py`（权威源）：

1. 把原来身兼两职的单一常量 `_FANOUT_MIRRORS` 拆成两个独立常量：
   - `_FANOUT_MIRRORS`（值不变，仍是 `{domain,adversarial,grounding,history}`）——继续专职
     `check_fanout_consistency` 里 dead-fanout-multi-mirror 的去重计数域。
   - 新增 `_MIRRORS_LEGAL = _FANOUT_MIRRORS | {"broad"}`——专职 `_parse_mirrors` 的合法性判据，
     常量名按 `design.md:106` / `tickets.md:87` 钉死为 `_MIRRORS_LEGAL`（供 Task 3 的 skew 探测
     信号读此常量名）。
2. `_parse_mirrors` 的 unknown-token 判据从 `_FANOUT_MIRRORS` 改读 `_MIRRORS_LEGAL`——`broad`
   进合法集,`check_fanout_consistency` 第 774 行的计数逻辑仍读原值不变的 `_FANOUT_MIRRORS`，
   两者互不影响。
3. `mirrors-unknown-token` 违规新增 `detail` 字段（新常量 `_MIRRORS_UPGRADE_HINT`），文案：
   「若本仓 openspec/workflow/ 为旧版，请先跑 sdflow-init update」。

`step1-broad-review` 锚的 `mode=` 值本来就不被 `check_existence` 校验（只校验锚族存在性，
不解析 `mode=` 的值），故「lint 不校验 mode 值」这条不变量无需改代码，只需补一条回归锁测试。

## 每条验收标准的证据

| 验收标准 | 证据 |
|---|---|
| `mirrors=` 含 `broad` 时 lint 判合法通过 | `test_parse_mirrors_broad_token_valid`：`_parse_mirrors("broad")` → `(["broad"], None)` |
| `subagents="unavailable"` + `mirrors="broad,history"` 不触发 dead-fanout | `test_fanout_unavailable_broad_history_not_dead_fanout`：`check_fanout_consistency(...) == []` |
| `subagents="unavailable"` + `mirrors="broad,domain,history"` 仍触发 dead-fanout | `test_fanout_unavailable_broad_domain_history_still_dead_fanout`：命中 `dead-fanout-multi-mirror` |
| `step1-broad-review` 锚 `mode="subagent"` 时 lint 通过（锁定不变量） | `test_step1_broad_review_mode_subagent_lint_passes`：`check_existence(...) == []` |
| mirrors-unknown-token 报错文案含升级指引 | `test_fanout_mirrors_unknown_token_hint_mentions_sdflow_init_update`：断言 `detail` 含 `"sdflow-init update"` |
| 合法集与计数集为两个独立常量，改前者不影响后者，且合法集常量名钉死为 `_MIRRORS_LEGAL` | `test_mirrors_legal_and_fanout_constants_split`：`"broad" in _MIRRORS_LEGAL`、`"broad" not in _FANOUT_MIRRORS`、两者 `!=` |
| `test_anchor_lint.py` 既有用例全绿 | 见下方测试输出（152 passed，含 146 条既有 + 6 条新增） |

## 部署副本判定（仓根 `openspec/workflow/tools/anchor_lint.py`）

**判定：不动。** 已 grep 全仓所有 `.py`/`.sh`/`.yml` 对
`openspec/workflow/tools/anchor_lint.py` 的引用：

- `hack/tests/test_yq_wrapper_consistency.py`——只做 `_yq()` 辅助函数的结构性 golden 校验，
  不触及 `mirrors`/`_FANOUT_MIRRORS`/`check_fanout_consistency` 任何逻辑。
- `sdflow-ship/scripts/ship_gate.py` / `hack/check_encoding_hygiene.py` /
  `hack/tests/test_encoding_hygiene.py`——只按路径前缀做「是否为真运行代码/编码卫生」判断，
  不解析文件内容语义。
- `sdflow-init/tests/test_init_contract_sync.py` / `test_task5_regression.py`——用
  `tmp_path` 沙盒验证 `sdflow-init` 铺设/更新机制本身能把 bundle 的 `tools/anchor_lint.py`
  拷进消费仓，不断言该文件的具体内容与本仓根副本一致。

即：仓根这份是 `sdflow-init update` 托管的部署副本（CLAUDE.md 明文：`sdflow-init update` 托管刷新，
勿手改），本仓测试没有任何一处直接消费它的 mirrors/fanout 逻辑。按 CLAUDE.md「改规则先改 assets、
再 `sdflow-init update` 推下游」的纪律，本票不手动同步这份副本——它会在 Task 6 dogfood 开全局
窗口时随 `sdflow-init update`（或本 change 收尾时的常规刷新）自然对齐，手改反而会形成
「仓根有本地改动，掩盖 sdflow-init update 应有的回灌路径」的假同步。

## 测试命令与输出

```
$ /usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q
........................................................................ [ 49%]
........................................................................ [ 98%]
......                                                                   [100%]
152 passed in 0.66s
```

（红→绿：加测试后先跑一次确认 5 条新增用例失败——`test_mirrors_legal_and_fanout_constants_split`
`AttributeError: no attribute '_MIRRORS_LEGAL'`、`test_parse_mirrors_broad_token_valid`
`unknown-token`、两条 dead-fanout broad 用例、hint 文案用例；`test_step1_broad_review_mode_subagent_lint_passes`
作为既有行为的回归锁测试，写下即绿属预期——它验证的是「本来就不校验 mode 值」这条不变量，
非本票新增代码。实现后重跑，5 条转绿 + 既有 146 条无回归 = 152 passed。）

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_codex_subagent_authorization.py -q
...........
11 passed in 0.02s
```

（该文件含对 `_FANOUT_MIRRORS` 值的反漂移锁——`_FANOUT_MIRRORS` 值本身未变，确认无回归。）

按 TDD 契约，本票 `Blocked-by: none` ⇒ 只需单元层，MUST NOT 跑与本票无依赖关系的集成/e2e 套件——
全仓 `pytest -q` 含其它 change 的 outside-voice 真子进程 dispatch/worker/await 集成测试（900s 级
timeout），与本票无依赖关系，故未等待其跑完/未作为本票证据；本票证据以上方两条定向测试
（`test_anchor_lint.py` 全量 + `test_codex_subagent_authorization.py`，后者是 `_FANOUT_MIRRORS`
值的既有反漂移锁，用于确认本次拆分未改变其值）为准。

## Concerns

无。范围内五条验收标准 + 既有回归全部核验通过；仓根部署副本判定为"不动"并已写明依据。
