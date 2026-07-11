## Why

`sdflow-spec-review` / `sdflow-code-review` / `sdflow-roadmap` 三处评审/规划步各有一段**由模型手做的机械判定**：outside-voice「两审复用守卫」（锚 mode + 时间戳 + 结构三判是否复用合法）、HR-TG 交集判定（TG 命中集 ∩ 高风险 TG 子集）、roadmap task-log『Review 处置』对账（断言无「未处置」残留）。三者都是「有确定性信号、口径固定、可测」的判定，却靠 prose 让模型每次手扫手比对——存漂移风险（漏项 / 误判 / 每次口径不一）且不可测，正是 adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」的直接对象，也是 MLH 阶段 4·4.D（批次 `mlh-p4-target-state`，目标态该做未做项）点名的三张票。同族的 4.C `lens_metric_emit` 已把「手数信任边界」下沉脚本并跑绿（merge `bd7c05f`），本 change 是其三个同型兄弟的收口。

> 背景：本 change 亦选作**首个 tickets 实现管线试点**——三校验器逻辑独立、依赖图稀疏，适合观测阶段三 frontier 契约。试点为阶段三**执行模式**选择，不影响本 change 的设计内容（config 翻键 / PIPELINE_RECEIPT 归试点执行，不入本设计）。

## What Changes

- **新增** 三个确定性只读校验器脚本（纯 Python stdlib，同 4.C `lens_metric_emit.py` 形态：`EmitError` / `EXIT_FAIL` all-or-nothing fail-closed + argparse `main` + 单一源机读块）：
  - `outside_voice_guard.py`（4.D.1 / T80）：吃 outside-voice 产物 → 锚 mode + 时间戳 + 结构三判 → reason_code 退出码。
  - `hr_tg_check.py`（4.D.2 / T81）：吃 TG 命中集 → 与 HR-TG 子集求交 → hit 列表 / none + 规范锚串；HR-TG 清单从 `trigger-catalog.md` **单一源读**（不硬编码副本），匹配口径复用 `ship_gate.py:tg02_hit` 的声明式匹配先例（防描述性提及 / 否定句假触发）。
  - `roadmap_review_reconcile.py`（4.D.4 / T82）：吃 roadmap task-log → parse『Review 处置』小节 → 断言无「未处置」状态 → reason_code 退出码。
- **新增** 三者 pytest（含坏输入 fail-closed 非零退出断言）。
- **修改** 三处对应 SKILL.md 的手做步 → 改为「调校验器出 reason_code」；**判断 / 编排语义保留给模型**（脚本只出信号，不替代裁决 / 处置 / 复用与否的决定）。
- 三校验器 + 测试落 bundle 权威源 `sdflow-init/assets/workflow/tools/`（+ `tools/tests/`），随 `sdflow-init update` 推 `openspec/workflow/tools/`——同 4.C 位置与形态。

## Capabilities

### New Capabilities
- `outside-voice-reuse-guard`: outside-voice 复用合法性的确定性校验——锚 mode / 时间戳 / 结构三判 → reason_code；不做「是否采纳该 voice」的裁决。
- `hr-tg-intersection-check`: TG 命中集与高风险 TG 子集交集的确定性判定——单一源读清单 + 声明式匹配 → hit 列表 / none + 规范锚串。
- `roadmap-review-reconcile`: roadmap task-log『Review 处置』小节的确定性对账——断言无「未处置」残留 → reason_code。

### Modified Capabilities
<!-- 无既有 spec 的 requirement 变更：三者均为新增脚本能力；被接入的三处 SKILL.md 现无 spec，其判断/编排语义不变。 -->

## Impact

- **代码**：+3 校验器脚本 + 3 测试于 `sdflow-init/assets/workflow/tools/`（`tests/`）；改 3 处 SKILL.md 手做步（`sdflow-spec-review` / `sdflow-code-review` / `sdflow-roadmap`）。
- **技术栈（TG-01）**：纯 Python stdlib（对齐仓内数据类 skill 与 4.C 取向）；不命中 backend·go / embedded / frontend 领域清单，仅适用 BASE 清单。
- **bundle 回灌纪律**：改的是 `sdflow-init/assets/workflow/` 权威源 → 须 `sdflow-init update` 推下游、dev checkout 须跑一次 `setup.sh` 才测得到（design.md Compliance 展开操作序）。
- **无外部服务 / API / 数据库变更。**

## Success Metrics

- 三处 SKILL.md 手做 prose（手扫 / 手比对 / 手断言）全部替换为「调校验器」，无残留手做口径。
- 三校验器各有 pytest 正例 + 坏输入 fail-closed（非零退出）断言，全绿。
- 口径与单一源一致：HR-TG 清单不硬编码（改 `trigger-catalog.md` 即生效）、matching 复用 `tg02_hit` 声明式口径；三校验器均门控外置（不读 config）。

## Non-Goals

- 不改变三处的**判断 / 裁决语义**——脚本只出 reason_code 信号，采纳 / 处置 / 复用与否仍由模型 / 人决。
- 不做 4.D.3（待 embedded 契约，◐组不排期）与 4.A。
- 不引入第三方依赖、不改 `setup.sh` 逻辑。
- 试点执行专属机制（config 翻键、PIPELINE_RECEIPT 核对、implementer 档位钉死）**不入本设计**——归阶段三执行。

## Assumptions（TG-22）

- **假设**：三处现状手做步的判定口径已稳定、可被确定性 parse（各有可锚的单一源 / 固定格式）。**失效影响**：若某校验器的单一源不存在或格式不足以支撑确定性断言（重点风险：T81 的 HR-TG 子集定义、T82 的『Review 处置』小节格式），该子项须先补单一源 / 格式契约再脚本化，否则该子项退回 prose（**不硬编码兜底**），并从本 change 剥离另排。起 change 时已派接地子代理核验此假设，结论并入 `design.md`；若接地判定某子项接口不确定（违 briefing 拒绝条件③），在设计门显式呈现供裁。

## Compliance

- **adr/0006**「凡机械 prose 协议 MUST 脚本化」：本 change 正向落实（三处手做 → 脚本）。
- **「机械活交脚本、模型只做判断」**：脚本只出 reason_code，不越权做裁决 / 处置 / 编排。
- **bundle 回灌纪律**（CLAUDE.md）：改 `assets/workflow/` 权威源须 `sdflow-init update` 推下游，禁只改下游遗忘回灌——`design.md` 展开操作序，遵守或显式豁免、禁沉默例外。
- **单一源原则**：HR-TG 清单从 `trigger-catalog.md` 读，禁硬编码副本。
