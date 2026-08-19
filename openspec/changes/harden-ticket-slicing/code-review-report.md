---
ship-gate:
  code_review: pass
  reviewed_sha: 966e4d2c720c881395a6303e11371573d89a9ef0
---

## code-review 报告 — harden-ticket-slicing

### 命中范围

- **栈**：本 change 的交付物是 **Markdown 指令文本与 workflow 规则 bundle**（4 个 SKILL.md + bundle
  规则 + 新增标准文 + INDEX/snippet + issues 记录），非某语言的生产代码。
- **清单**：`code-review-base.md` CR-01~11。
  🔴 **领域清单未覆盖（显式降级声明）**：`~/.sdflow/workflow/code-checklists/domains/` 下现有 8 个
  领域清单（`backend` / `backend-go` / `embedded*` / `frontend*` / `llm`）**均不命中**本 change 的
  改动面，无领域 delta 可叠加。领域镜按 base 清单跑并对规则做语义映射（这些 Markdown 的「运行时」是
  按其执行的 agent，故 CR-02「错误路径完整性」→「新规则的失败/边界分支是否都定义了处置」、
  CR-11「枚举完备性」→「新增触发条件/取值是否被各消费点处理」）。**MUST NOT** 读作「本项目无此评审层」。
- **diff base**：`1540703315309ca5a774d99427d276c0c89010a5`（`git merge-base origin/main HEAD`）。
- **`trivial_shape` 判定**：`NOT_EXEMPT`（`non-doc-markdown:openspec/INDEX.md` + 多个 behavior-path）
  ⇒ 照常 fan-out，未走无逻辑面豁免。
- **TG 判定（模型判定，交脚本做确定性交集）**：`TG-19`（多条需求 P0/P1）· `TG-23`（≥2 方案，memo D1/D4
  有被否候选）· `TG-25`（多文件规则契约套件）· `TG-28`（developer-facing 交付面）。
  **HR-TG ∩ = ∅** ⇒ 未开领域专属 cross-model；`declared-sites` = `code-voice` 单站点。
- **历史镜条件化判定**：命中判据 (a)（`git diff --diff-filter=R -M` 非空 —— `T141.md` open→closed
  rename）⇒ 本轮**派**历史镜。判据 (b)（既有文件 ≥200 行改动）未命中。
- **Step1 自持 scope 审计结论**：**scope-drift 零**；完成度 **12/12 DONE**（tasks.md 1.1–4.2 逐条有
  diff 内证据）。两条 `UNVERIFIABLE` 记录经核后判定不构成 scope-drift（详见下方「已裁掉」区）。

<!-- sdflow:step1-broad-review v1 mode="subagent" -->

  执行位 = `subagent`（fresh 中档子代理独立完成，非主 session 降级亲做）。

<!-- sdflow:hr-tg v1 hit="none" declared="TG-19,TG-23,TG-25,TG-28" evidence="改动面为 workflow 规则 bundle 与 SKILL 指令文本，无 DB/API/并发/信任边界/外部依赖面；TG-27 被其排除句明文排除（评审工作流自身读取受信任 agent 自报的控制面锚不算）" -->

<!-- sdflow:declared-sites v1 declared="code-voice" -->

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history,broad" -->

`host=claude` ⇒ 免探针、恒可用。本轮实际独立完成的镜：Step1 broad（scope 审计）· 领域镜 ×1 ·
对抗镜 ×2 · 历史镜 ×1，另加 outside-voice（跨模型，不占镜位）。**无降级**。

> **诚实边界**：「机制活但主 session 自代多镜」无机械守，属残余语义层。本轮各镜均为实际派出的
> fresh 子代理（对抗镜 A 首次派发因 API 错误中止，已**重派**并取得结果——该次失败与重派如实记录，
> MUST NOT 当作"跑过了"）。

### outside-voice 锚

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->

- **分支**：`host=claude` ∧ 后台能力自探 `PROBE_OK` ∧ 主 session 已确证 ⇒ **async·harness**，
  内层 `--timeout 900`（config 的 `outside-voice.async-timeout-seconds` 为注释态 ⇒ 回落默认 900）。
- **终态取值**：读 sidecar `{run-dir}/code-voice.rc` = `0` ⇒ `reason_code="ok"`，stdout 进合并池。
  `OV_TRUNCATED=false`。
- 🔴 **context 范围偏离（须知情）**：全量 `DIFF_BASE..HEAD` diff 为 **304,223 字节**，超过 helper 的
  200KB 截断阈值（保头尾各 100KB、**中段整段丢失**）。若照「全量」原样喂入，真正的交付物（4 个
  SKILL.md 与 bundle 规则的改动）会落在被丢弃的中段，voice 只能读到 impl-reports。∴ 本轮 context
  **收敛到生产代码面**（35,931 字节）+ 四件套设计意图（57,227 字节），合计 81,145 字节；**排除**的是
  `impl-reports/` 下的实现报告与 `*-review-package.diff` 过程产物（流程留痕，非交付物）。
  该偏离**是本轮 voice 能读到核心实现的前提**，如实记录于此。

### 机械引用核锚

<!-- sdflow:ref-check v1 status="ran" pass="7" fail="0" uncheckable="0" -->

- **执行位偏离（如实声明）**：Step3 规定的机械引用核**未在其规定位置（裁决之前）运行**——彼时主
  session 是**逐条亲自打开被引文件核验**（每条 finding 的 `file:line` 与引文均由主 session 实读确认）。
  机械核在**自动修之后**补跑，且因修复已移动行号，**对修复前盘面**（`7e53407`，即各镜实际所审的
  状态）建 scratch worktree 后运行 `findings_ref_check.py --root <该 worktree>`，取得**真实**三态结果
  `7 pass / 0 fail / 0 uncheckable`（非降级、非 `degraded`）。
- 该偏离的影响：机械核的**结论**未变（7 条引文全部真实指向所声明位置），但它**没有起到「进裁决前
  的前置门」作用**——本轮把不合格引文挡在裁决外的，是主 session 的人工核验。**MUST NOT** 读作
  「机械前置门按设计生效了」。

### Findings（已采纳，按置信降序）

| # | 严重度 | 规则 | 位置（修复前盘面 `7e53407`） | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|---|---|
| F1 | high | CR-02 | `sdflow-init/assets/workflow/ff-generation-constraints.md:43` + `sdflow-implement/SKILL.md:284` + `specs/impl-orchestration/spec.md:5` | **「单票交付」合规路径与「3–6 张垂直切片」预算互相矛盾**。本 change 新增的必触发条件① 把「缺席理由蕴含单票交付而实际出票 **1 张**功能票」列为**合规**；而票数预算句只规定「**超出**预算须注明 expand–contract 例外」、未规定不足，出票小标题与 delta spec 的 SHALL 均**无条件**要求 3–6 张。小修 change 的执行者会卡在「按 design 出 1 张」与「按预算出 3–6 张」之间，两种执行都合法可辩。 | outside-voice(codex) | 已修 `[impl-review-fix]` |
| F2 | high | CR-11 | `sdflow-init/assets/workflow/ff-generation-constraints.md:1`（+ `:3` 定位声明） | **新增的「切片建议」规范节落在该文件自述的 `D-1~D-6` 范围之外**。标题与定位声明均写「FF-0 + D-1~D-6」，且该文件自己教「所有调用方只引用编号、不复制定义内容」；新增节在 `:38`、无 D 编号、不在 D 表（`:112-117`）内。四处摘要投放面（`openspec/config.yaml:10` / `config.template.yaml:26` / `index-section.md:12` → `INDEX.md:17` / `workflow-rules-guide.html:263,352`）亦全部复述为 `D-1~D-6`。⇒ 按该文件惯例行事的生成侧读者会**结构性漏读**这节新规范，**且漏读不留痕**（design.md 缺节且无理由，与"认真读了判断不适用"事后无法区分）。 | 对抗镜2 | 已修 `[impl-review-fix]` |
| F3 | high | CR-11 | `sdflow-implement/SKILL.md:611` ↔ `:615-618` | **「票外发现上报」未接入既有的 implementer↔编排层通信契约**。`:611` 规定返回值**只能**是「四值状态词 + 一行摘要」；`:615-618`（本 change 新增）却要求「在返回中上报」票外发现，而 BASE-18 AND 门需判「同 capability / 高耦合 / 低增量」三维信息——一行摘要装不下。四值状态词中只有 `DONE_WITH_CONCERNS` 有配套的 report-file 小节 + 编排层 Read 契约，票外发现**无同构机制**，全文未定义落点与读取义务。 | **领域镜 + 对抗镜1（2 镜独立收敛）** | 已修 `[impl-review-fix]` |
| F4 | medium | CR-02 | `sdflow-implement/SKILL.md:653` | **fold 新增的票未声明是否须过出票期治理**。只说 fold 进的工作「均走正常 implementer + 双轴审」，未提出票模式的强制项（`Blocked-by` / `R-ID` / 验收复选框 / 语法面有界性闸门）对**执行期新增的票**是否同样适用；两种读法都能自圆其说且无文本裁断。 | 对抗镜1 | 已修 `[impl-review-fix]` |

**F1–F4 的修复内容**（提交 `966e4d2`，8 文件 +34/−16，仅源码）：

- **F1** — 三处补**与 expand–contract 并列**的显式例外（决策区写明成立的「单票交付」缺席理由 + 出票
  确为 1 张功能票 ⇒ 合规，不受 3–6 预算约束），`ff-generation-constraints.md` / `sdflow-implement/SKILL.md`
  / delta spec 三方口径一致。
  **`T10-choice` 定案依据（有客观判据档 ①）**：`decision-memo.md` 的 **D2** 明写「单文件小修强制产
  草图是样板税」——该 change 的既定设计意图就是允许小修走轻路径，故「补例外」而非「取消单票路径」
  有客观判据，无需派对抗镜复核。
- **F2** — **扩摘要口径**（非编 D-7）：改文件标题 + 定位声明 + 五处摘要投放面。
  **定案依据**：编 D-7 要动 D 表、触发条件表、「附：可直接注入的 prompt 片段」、检查清单四处结构，
  爆炸半径远超本次范围（通则③ 不加宽）；而**根因是「摘要与全文范围不一致」**，改摘要口径即消除。
- **F3** — **比照 `DONE_WITH_CONCERNS` 的既有形状**（不发明新机制）：report file 固定小节
  `## 票外发现` + 返回摘要标注 `[has-off-ticket-finding]` + 编排层 **MUST Read 该小节全文**再判 AND 门；
  SKILL 与 delta spec（Requirement 正文 + Scenario THEN 分支）同步。
- **F4** — 明示执行期新增票 SHALL 补齐出票模式的强制字段与闸门（指针引用既有节，不复制清单）；
  编排层另行补齐 delta spec 侧的同款条款（fix 子代理原任务只指名 SKILL，主 session 收口）。

**另有两处由编排层直接收口**（非镜报出，主 session 复核修复 diff 时发现）：

- delta spec 未同步 F4 条款 ⇒ 已补（否则留 spec↔SKILL 分歧，正是 F2 那一类问题）。
- F1 修复初稿写「**本节**写明成立的『单票交付』缺席理由」——指代不自洽（按该文件定义，缺席理由是节
  **缺席**时写在**决策区**的，不可能写在「本节」里）⇒ 已改为「**决策区**写明…（即本节合规缺席）」。

### 已裁掉（反静默压制，可审计）

| # | 原始发现 | 裁决理由 |
|---|---|---|
| X1 | **Step1 scope 审计 `UNVERIFIABLE-01`**：`sdflow-spec/SKILL.md` 除任务清单外还有 4 处无关文字压缩 | **不成立（非 scope-drift）**。该文件卡在 18,000 Unicode 字符体量门（`hack/tests/test_sdflow_spec_resident_contract.py:106`），改动前余量仅 3 字符；为塞入指针行被迫做等量压缩，是**目标态达成的必要副作用**。4 处压缩已在 Task 3 的 Standards 轴逐处核过无承重语义丢失，并已记 T287 追踪体量门余量风险。 |
| X2 | **Step1 scope 审计 `UNVERIFIABLE-02`**：`specs/impl-orchestration/spec.md` 新增 148 行远超本 change 描述 | **不成立**。OpenSpec MODIFIED-Requirement 惯例是完整重放基线 Requirement 全文后插入新增段，非本 change 引入的额外范围。 |
| X3 | **对抗镜2 已核验未成立的四点**：BASE-31 归镜默认规则是否真存在 / B.7 item 3 是否有加载门槛 / 机械层零改动声明是否属实 / 三条必触发的诚实边界是否冒充机械保证 | 对抗镜2 自行核验后判**均不成立**（默认规则确在 `sdflow-spec-review/SKILL.md:248,252`；`scope-cohesion-check.md` 已在按需资料路由清单内且 B.7 是强制步；`git diff --stat -- '*.py' '*.sh'` 为空；诚实边界句措辞正确）。如实记录，不计入 finding。 |

> **无 `[ref-check]` 机械裁掉项**——本轮 7 条引用全部 `pass`（见上方机械引用核锚）。

### 修复 / defer 台账

自动修 **4** 项 `[impl-review-fix]`（F1–F4，提交 `966e4d2`）；自动选推荐 **1** 项（F1 走 `T10-choice`
有客观判据档 ①，依据见上）；本轮新增待处理 **3** 项（recorder 已确认各自 `source_change` = 本 change）。

**复审一轮已执行**（硬上限 1，范围限定 `966e4d2` 本身）：**通过**——四条逐条消解、三方口径一致、
五处摘要补全、指代自洽、零越界、`.py`/`.sh` 零改动、`sdflow:principles` 托管块未动。
**未触及上限**（复审未报出新的 Critical/Important，无需 defer 残差）。

| id | 池 | 摘要 | critique（裁决理由） |
|---|---|---|---|
| T289 | todo | 收尾票机械门只校验唯一 `R-ID: all` + `Blocked-by` 覆盖，不校验该票确为实现验证票；任意普通票伪标 `R-ID: all` 即可绕过聚合回归 | outside-voice(codex) 报出，属实。但这是**既有** gate 弱点（H12/M17 早于本 change），且本 change 的 Goals 明写「`ship_gate.py` 及一切机械层脚本零改动」⇒ 修它=越界（通则③ 不加宽）。defer 而非裁掉——它是真问题，只是不属本 change。 |
| T290 | todo | 新增的「切片偏离」审计行格式落 `planning-decisions.md` 后全仓零消费方（grep 仅命中定义处本身） | 对抗镜2 报出，grep 亲验属实。但 proposal 措辞已诚实（只承诺「有触发即有记录，**可 git 审计**」，未承诺「被审计」）⇒ 不构成假机械保证；而「给它接一个消费方」（如并进 code-review Step1 输入清单做偏离-diff 对账）是**另一片面的设计决策**，超本 change 范围。 |
| T291 | todo | `workflow-rules-guide.html` 里 `ff-generation-constraints.md` 的「198 行」计数与实际（现 207）不符 | 复审轮建议。属历次改动累积的**历史遗留漂移**，与本轮四条无因果；顺手修=自加范围（通则③）。修法按既有惯例=删掉硬编码数字让工具自己报，不再手工对齐。 |

### 度量锚

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="2" sev="致0/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="2" 采纳="1" 裁掉="0" defer="1" 独立="1" sev="致0/高1/中0/低0" -->

> **本轮的一个可复用观察**（供 `/sdflow-retro` 聚合，本报告不做复评判断）：**4 条采纳里 2 条独家出自
> 对抗镜、1 条出自跨模型 voice、1 条由领域镜与对抗镜收敛**；`broad` 与 `history` 本轮 findings=0。
> 跨模型 voice 独家贡献了 F1（且它是本 change 新引入的**最实质**的一条执行分叉），与既往「跨模型
> voice 产出碾压同族温镜」的观察一致。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☑ 本轮新增待处理项已入池（T289 / T290 / T291，见上方台账，hand-off 会引用）

**残余风险（交 verify 与异步再入口）**：
- 本 change 未新增任何自动化测试（交付物为指令文本，仓内无守其措辞的机械门；硬造断言文本的脆弱
  测试会撞 CLAUDE.md 基准 5「无界语法禁手搓」）。**新规则的生效与否依赖执行方遵守指令**，这是
  已声明的诚实边界，非本轮可消除。
- 机械引用核未在规定位置作为前置门运行（见上方锚下声明）。
