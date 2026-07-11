## Why

样本 #1（`mlh-p4-reason-code-validators`，SHIPPED 2026-07-11）冷层 `sdflow-code-review` 抓出 2 中危 fence-aware 假绿（已在该 change 内修）+ **5 条 hardening defer**（T136/T137/T138/T139/T140，批次 `mlh-p4-reason-code-validators`）。本 change 收束其中 **4 条代码类**（T136/T138/T139/T140），对**同一校验器族做第二遍加固**；**T137 剔除**——config 全局翻键的 blast radius 是纯用户意图裁断（全局切换 vs 仅 pilot）、非代码，留 hand-off 独立处置。

动机同源：三校验器的**次要解析路径**在 mlh-p4 内未被每票双轴审覆盖（双轴审只验主路径验收达标），坏输入被**静默正规化**而非 fail-closed——违 MLH 全局红线「pytest 覆盖坏输入断言非零退出」与 adr/0018「机械校验器输出诚实」。

> 本 change 亦作 tickets 管线 Phase A 第二个试点样本：**单桶**（代码质量·校验器/anchor 加固）、**同族第二遍**（去样本 #1 的 first-of-kind confounder）、**多单元**（3 票）——判据口径见归档 `pilot-briefing.md`，逐 change 留档进 `openspec/roadmaps/workflow-cost-optimization/tickets-pilot-log.md`。

## What Changes

- **T138 · hr_tg_intersect 严格解析**：`parse_tg_set`（`hr_tg_intersect.py:54-62`）当前 `tokens = [t for t in tokens if t]`（`:58`）静默过滤空 cell → `TG-04,,TG-16` 误通过、单个 `,` 误判空集；成员抽取用宽松 `_TG_TOKEN_RE = TG-\d+`（`:14`，`:45` findall）令成员行 `TG-04x` → `TG-04`。改为：仅**原始空串**表空集；CSV 含空 cell / 前后逗号 → `EmitError`；成员行边界严格 token、残余畸形 fail-closed。
- **T139 · outside_voice_guard 双锚一致性**：`parse_mode`（`outside_voice_guard.py:51-61`）用 `_S1_RE.search`（`:54`）取**首个** step1-broad-review 锚，双锚（native 在前 simulated 在后）静默取 native、忽略 simulated。改为：收集 fence 外**全部** step1 锚，数量 >1 且 mode 不一致 → fail-closed，不静默取首。
- **T136 · anchor_lint.check_hr_tg 内部一致性重算**：`check_hr_tg`（`anchor_lint.py:163-174`）当前只查 `hit=`/`declared=` **在场**（`HR_TG_REQUIRED_FIELDS`, `:160`），docstring 明写「不校验 CSV 内容、命中判定归模型」——手改 `hit=none declared=TG-04`（TG-04 ∈ HR-TG）能过 lint、静默跳过必开的领域 cross-model。接 `--trigger-catalog`，重算 `declared ∩ HR-TG`、要求 `hit` 与之**一致**，不一致/畸形 → 违规。**诚实边界**：只堵单字段内部不一致，**堵不住**同时改 hit+declared 成「一致但错」（declared 正确性无确定性信号、仍归模型 + git 审计，adr/0018 不变）。
- **T140 · declared= 向后兼容 grace**：mlh-p4 令 `declared=` 成 `check_hr_tg` 必填是破坏性收紧无 grace；旧格式锚（`hit=`+`evidence=` 无 `declared`）重 lint 会 exit1。给**旧格式**（有 `evidence=` 无 `declared`）迁移 grace：缺 `declared` 降级 WARN 而非硬失败，新格式（有 `declared`）走 T136 全重算。
- 经 `sdflow-init update` 推下游 + dev `setup.sh`；扩三工具 `tests/` 坏输入断言。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `hr-tg-intersection-check`：**ADDED** 一条 Requirement——命中 TG 集与成员行严格解析、畸形 fail-closed（T138）。
- `outside-voice-reuse-guard`：**ADDED** 一条 Requirement——step1-broad-review 锚数量一致性、多锚 mode 冲突 fail-closed（T139）。
- `spec-workflow`：**ADDED** 一条 Requirement——anchor_lint hr-tg 锚内部一致性重算 + 旧格式向后兼容 grace（T136/T140）。

## Impact

- **文件**：`sdflow-init/assets/workflow/tools/{hr_tg_intersect,outside_voice_guard,anchor_lint}.py` + 各 `tests/`；`sdflow-code-review/SKILL.md`（HR-TG 判定步若需 anchor_lint 侧新增 `--trigger-catalog` 接线则薄补，引用为单一源、不复述细节）。
- **分发**：bundle 权威源改动 → `sdflow-init update` 推消费仓 `openspec/workflow/tools/` + 本仓 `setup.sh` 刷新 `~/.sdflow`。
- **不涉及** `ship_gate.py`、`review_disposition_check.py`（T82 无 defer）、`config.yaml`（T137 剔除）。

## Success Metrics

- 坏输入 fail-closed 覆盖 — 基准 mlh-p4 后 4 类静默正规化（空 cell / 宽松成员 / 双锚取首 / hit-declared 单字段不一致）→ 目标 4 类全 `EmitError` 或判违规 — 度量方式 三工具 `tests/` 新增坏输入用例全绿（断言非零退出 / 违规计数 ≥1）。
- hr-tg 锚防绕过 — 基准 手改 `hit=none declared=TG-04` 可过 lint → 目标 anchor_lint 判违规、非零退出 — 度量方式 anchor_lint tests 增手改绕过负例。
- 向后兼容无回归 — 基准 declared= 破坏性必填、旧格式 exit1 → 目标 旧格式锚（`evidence=` 无 `declared`）重 lint 降级 WARN 不 exit1 — 度量方式 anchor_lint tests 增旧格式 grace 用例。

## Non-Goals

- **不裁 T137**（config 全局翻键 blast radius）：属用户意图裁断（全局切换 vs 仅 pilot），非代码活。**可证伪假设**：若发现 config 键当前状态已在误路由某活跃 change（如 `scoped-test-per-task` 被错送 tickets 且已致害），则本 Non-Goal 失效、须并入处理。
- **不做 tamper-proof**：T136 只堵 `hit ⟺ declared∩HR-TG` 内部一致性，不校验 declared 本身正确。**可证伪假设**：若「命中哪些 TG」出现确定性机械来源（推翻 adr/0018 D3 前提），则可进一步机械化、本 Non-Goal 失效。
- **不动 `review_disposition_check`（T82）**：其无 defer 项。**可证伪假设**：若 dogfood 发现 T82 次要解析路径同类假绿，则须补入。
- **不引第三方依赖、不改 `setup.sh`、不改 `ship_gate.py`**：三工具续纯 stdlib。**可证伪假设**：若 T136 重算需超 stdlib 能力（不会——纯集合运算 + 既有 fence-aware 原语），则重评设计。

## Assumptions〔TG-22〕

- **假设**：无既有流程重 lint `spec-review-report.md`——`sdflow-code-review` 只 lint `code-review-report.md`（`--layer code-review`），`sdflow-done` 的 verify/archive 不重跑 anchor_lint 的 spec-review 层。**失效影响**：若某消费仓/流程重 lint 带旧格式锚的 `spec-review-report.md`，则 T140 grace 从 nice-to-have 升为硬需求；由 T140 grace 用例 + 本仓 grep 核验兜住（design D2）。

## Compliance

遵 `spec-workflow` 既有 Requirement「workflow bundle 改在权威源、经部署下发」：改动落 `sdflow-init/assets/workflow/tools/` 权威源，经 `sdflow-init update` 下发，不在下游直接改。不涉及数据/安全/外部服务合规——N/A（T136 的越权通道属评审自检完整性、git 留痕可审计，非应用安全/敏感数据边界，故未命中 HR-TG，详 design 触发判定）。
