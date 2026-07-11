# design — mlh-p4-validators-hardening

## Context

MLH 阶段 4·4.D 三 reason_code 校验器（`mlh-p4-reason-code-validators`）SHIPPED 后，冷层 `sdflow-code-review` 独家抓出 2 中危 fence-aware 假绿（已内修）+ 5 条 hardening defer。本 change 收 4 条代码类（T136/T138/T139/T140），对同族第二遍加固；T137（config blast radius）非代码，剔除留人裁。

**接地事实（已 grep 核验，带行锚，D-1）：**

- **T138** `hr_tg_intersect.py`：`parse_tg_set`（`:54-62`）body = `tokens = [t.strip() for t in raw.split(",")]`（`:57`）→ `tokens = [t for t in tokens if t]`（`:58`，**空 cell 静默过滤**）→ 逐 token `_TG_STRICT_RE.match`（`:60`）。故 `TG-04,,TG-16` 过滤空 cell 后返合法列表、单个 `,` → `[]` 空集。成员抽取 `_MEMBER_RE` 行内 `_TG_TOKEN_RE.findall`（`:45`，`_TG_TOKEN_RE = re.compile(r'TG-\d+')`, `:14` **宽松**）→ 成员行 `TG-04x` 被 findall 抽出 `TG-04`。
- **T139** `outside_voice_guard.py`：`parse_mode`（`:51-61`）= `m = _S1_RE.search(_fence_outside_text(text))`（`:54`，**`.search` 取首个**）；`_S1_RE = re.compile(r'<!--\s*sdflow:step1-broad-review\s+v1\b(.*?)-->')`（`:17`）。双 step1 锚（native 前 / simulated 后）→ search 命中首个 native，simulated 静默丢。`VALID_MODES = ("native","simulated")`（`:14`）。
- **T136/T140** `anchor_lint.py`：`check_hr_tg`（`:163-174`）遍历 fence 外 hr-tg 锚，`for f in HR_TG_REQUIRED_FIELDS`（`:171`，`HR_TG_REQUIRED_FIELDS = ("hit","declared")`, `:160`）只查**字段在场**、`kind="missing-field"`（`:173`）；docstring（`:164-165`）明写「只断言字段在场——字段值任意合法，命中判定归模型，脚本不校验 CSV 内容」。**无 `--trigger-catalog` 入参、无重算**。anchor_lint 的检查规格权威地 = 主 spec `spec-workflow`（锚自检 requirement）。
- **HR-TG 单一源**：`trigger-catalog.md` `## 七、HR-TG` `> 成员：` 行 = TG-04/06/07/08/09/16/17/26；`hr_tg_intersect.parse_members`（`:26-51`）已从此单一源 parse——T136 重算复用此解析口径、不另建成员副本。

## Goals / Non-Goals

**Goals**：三校验器**次要解析路径**坏输入从静默正规化改 fail-closed；anchor_lint hr-tg 锚从「字段在场」升「字段在场 + 内部一致性重算」，堵单字段手改绕过；declared= 破坏性收紧补向后兼容 grace；各配坏输入 pytest（TG-18）。续纯 stdlib、门控外置、fail-closed。

**Non-Goals**：不裁 T137（归人）；T136 不做 tamper-proof（declared 正确性仍归模型）；不动 review_disposition_check；不引第三方依赖、不改 setup.sh / ship_gate.py。

## Decisions

### D1〔TG-23〕T136：check_hr_tg 从「字段在场」升「内部一致性重算」，诚实边界不冒充 tamper-proof
**决策：`check_hr_tg` 接 `--trigger-catalog` 入参，对新格式 hr-tg 锚重算 `declared ∩ HR-TG`（复用 `hr_tg_intersect` 的成员解析口径 + 严格 tg-set 解析），要求锚 `hit=` 与重算结果**逐元素一致**（含 `none` ⟺ 空交集），不一致 / declared 畸形 / hit 畸形 → 违规。**MUST NOT 校验 declared 本身是否为「真命中集」**——只校验 hit 对 declared 的确定性派生。**

- **为何是「内部一致性」而非「正确性」**：`declared` = 模型判定的命中 TG 集，「命中哪些 TG」无确定性信号（adr/0018 D3 的根、spec-review Q-D 已定）。脚本能确定性重算的只有 `hit = declared ∩ HR-TG`（集合运算），故只校验这一派生的内部一致性。
- **堵住什么 / 堵不住什么（诚实边界，adr/0018）**：堵住「手改**单字段** `hit=none declared=TG-04`」（内部矛盾即违规）；**堵不住**「同时改 hit+declared 成一致但错」——那需要 declared 正确性，无机械信号。故 T136 把手改绕过的成本从「改 1 字段」抬到「改 2 个一致字段且骗过 git 审计」，是**抬门一格、非焊死**。SKILL/design MUST 显式这样声明，MUST NOT 宣称 anchor_lint 使 hr-tg 锚 tamper-proof。
- **D-6 / adr/0018 边界核对**：重算 `declared∩HR-TG` 是**确定性派生**（有信号）→ 机械归脚本，**未越** adr/0018「命中判定归模型」边界（命中集 `declared` 仍由模型给、脚本不产）。属 adr/0006(b)「机械 prose 脚本化」的正当延伸（原「肉眼核 hit 对不对」本是机械可算却留给了人/静默）。
- **主次**：内部一致性重算（确定性、可机械）> 宣称 tamper-proof（不可达、会假绿）。

### D2〔TG-23·TG-22〕T140：declared= 旧格式向后兼容 grace
**决策：`check_hr_tg` 按锚形态分流——新格式（含 `declared=`）走 D1 全重算；旧格式（含 `evidence=` 且无 `declared=`，即 mlh-p4 前的 hr-tg 锚）→ 缺 `declared` 降级 **WARN**（human 行提示「旧格式锚、declared 缺失、跳过重算」）而非 exit1。纯 `hit=` 无 evidence 无 declared 的畸形锚仍按缺字段违规。**

- **为何 grace 而非「确认不会重 lint 后接受现状」**：proposal Assumption「无既有流程重 lint spec-review-report.md」**须在 design 期 grep 核验**（下 Open Questions）；即便本仓成立，消费仓/未来流程重 lint 旧报告会硬失败——grace 成本极低（一个形态分支）、消除破坏性收紧的迁移悬崖，优于赌假设永真。
- **与 D1 的张力消解**：D1 令锚更严（要 declared present + consistent），D2 对**旧格式**开豁免——两者不冲突：grace 只认「evidence= 无 declared」这一可识别的旧形态，新格式无豁免。
- **主次**：向后兼容 grace（迁移安全）> 一刀切必填（会炸旧报告）。

### D3〔TG-23〕T138：hr_tg_intersect 严格解析、畸形 fail-closed
**决策：`parse_tg_set` 删「空 cell 静默过滤」——仅 `raw == ""`（原始空串）表空集；`raw.split(",")` 出现空/纯空白 cell（含前导/尾随/连续逗号）→ `EmitError`。成员抽取改边界严格：成员行 token 须整体形如 `TG-<数字>`（词边界锚定），`TG-04x` 之类残余畸形 → `EmitError`（单一源损坏不静默正规化）。**
- 依据：mlh 全局红线「坏输入断言非零退出」；畸形静默正规化可能掩盖模型侧记号错误（`declared=` 虽暴露但机械层本应挡）。
- **主次**：显式空串表空集（保留合法空集入口）> 一律非空（会误伤真空集场景）。

### D4〔TG-23〕T139：parse_mode 收集全部锚、数量/一致性校验
**决策：`parse_mode` 改 `_S1_RE.findall`（或 finditer）收集 fence 外全部 step1-broad-review 锚的 mode；0 锚 → 既有 `EmitError`；1 锚 → 取之；≥2 锚且 mode 全一致 → 取该 mode（容重复）；≥2 锚且 mode 冲突 → `EmitError`（不静默取首）。**
- 依据：违「数量与 mode 一致否则 fail-closed」稳健取向（单锚是常态，双锚构造性/低概率但不该静默）。
- **主次**：多锚冲突 fail-closed（暴露异常）> 静默取首（假绿）。

### D5〔切片建议·仓 impl-pipeline: tickets〕
> 本节按 ff-generation-constraints「切片建议」条款产出（**建议非契约**，出票模式可自主）。**不用** `wayfinder-resolved:` 前缀。

3 张 tracer-bullet 垂直切片，依赖图稀疏：

- **T-a · anchor_lint hr-tg 锚加固**（T136 + T140）：一票——两者同碰 `check_hr_tg`、同属「hr-tg 锚 schema 演进」（重算 + 旧格式 grace），拆开会撕裂同一函数的形态分流逻辑。`Blocked-by: none`。R-ID: R3。
- **T-b · hr_tg_intersect 严格解析**（T138）：`Blocked-by: none`。R-ID: R1。（T-a 复用其成员/tg-set 解析口径，但 T138 是**收紧**该口径——T-a 依赖的是 T138 后的严格版；若并行，T-a 出票时按严格口径实现即可，无硬阻塞，故仍标 none、由 frontier 串行天然序化。）
- **T-c · outside_voice_guard 双锚一致性**（T139）：完全独立。`Blocked-by: none`。R-ID: R2。

3 票均单文件、单校验器、逻辑独立 → 天然稀疏依赖图，适合观察 frontier 严格串行契约（本身首版红线仍串行）。

## Risks / Trade-offs

- **[T136 被误读为 tamper-proof]** → design/SKILL 显式声明「只堵内部一致性、非焊死」（D1 诚实边界）；测试含「hit+declared 同改一致但错 → 仍过 lint」的**边界确认负例**（证明不宣称能挡）。
- **[T140 grace 被滥用成永久旁路]** → grace 只认「evidence= 无 declared」旧形态；新格式无豁免，随旧报告归档消亡而自然收敛。
- **[T138 严格化误伤真空集]** → 仅 `raw==""` 表空集的入口保留；测试含空集正例。
- **[T-a/T-b 解析口径耦合]** → T-a 复用 T-b 严格口径；frontier 串行下 T-b 先落则 T-a 直接用严格版，无 dual 实现。
- **[bundle 回灌遗忘]** → Migration 段固化 sdflow-init update + dev setup.sh。

## 失败模式表〔TG-12/15〕

| 校验器 | 坏输入/失败 | 行为 | 可观测 |
|---|---|---|---|
| hr_tg_intersect | tg-set 含空 cell / 前后逗号（`TG-04,,TG-16` / `,`） | `EmitError`（非静默过滤/空集） | `[hr_tg_intersect] FAIL: tg-set 空 cell` |
| hr_tg_intersect | 成员行畸形 token（`TG-04x`） | `EmitError`（单一源损坏 fail-closed） | 成员解析失败 |
| outside_voice_guard | ≥2 step1 锚 mode 冲突 | `EmitError`（不取首） | 锚数量/mode 冲突 |
| anchor_lint | 新格式锚 `hit` ≠ `declared∩HR-TG`（含手改单字段） | 违规、非零退出 | `missing-field` 之外新增 `hit-declared-mismatch` |
| anchor_lint | 旧格式锚（evidence= 无 declared） | WARN 降级、不 exit1（T140 grace） | human 行提示旧格式跳重算 |

## 组件 / 数据流图〔TG-11〕

```
单一源 / 入参                          校验器（tools/，纯 stdlib）                消费方
trigger-catalog 七.HR-TG 成员 ─┐
tg-set（模型判定，严格解析）  ─┼──► hr_tg_intersect.py [T138 严格] ──► hit/none｜依据模型判定 + 锚 ─► spec/code-review
gstack-review 全部 step1 锚  ───► outside_voice_guard.py [T139 全收集] ──► reason_code(6) ─────────► spec-review
评审报告 hr-tg 锚 + trigger-catalog ─► anchor_lint.check_hr_tg [T136 重算/T140 grace] ─► 违规/WARN ─► spec/code-review 自检
  权威源改动 ── sdflow-init update ──► openspec/workflow/tools/（下游副本，不含 tests/）
  三工具互不 import；anchor_lint 复用 hr_tg_intersect 成员解析口径（同单一源、非 import）
```

## Migration Plan（bundle 回灌纪律）

1. 三工具加固 + 扩 `tests/` 写权威源 `sdflow-init/assets/workflow/tools/(tests/)`。
2. T136 若需 SKILL 侧接线（`sdflow-code-review`/`sdflow-spec-review` 的 anchor_lint 调用补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`），薄改对应 SKILL.md 步、引用单一源不复述。
3. dev checkout 跑 `bash setup.sh` 同步 canonical。
4. `sdflow-init update` 推下游副本（下游不含 tests/，一致核对仅脚本本体）。
5. 回滚：还原三工具 + SKILL.md 接线；无数据迁移、无消费方破坏（T140 grace 保证旧报告不炸）。

## Open Questions

- **[design 期须 grep 核验]** proposal Assumption——本仓有无流程重 lint `spec-review-report.md`（grep `anchor_lint.*spec-review` 调用点）。核验结果写回 D2：若确无 → T140 grace 定位 nice-to-have（消费仓保险）；若有 → 升硬需求。
- T136 新增违规 `kind` 命名（`hit-declared-mismatch` 为建议名）实现期可微调。
- anchor_lint `--trigger-catalog` 缺省行为：未传时 T136 重算是否降级为「仅 presence 检查 + WARN 未重算」（保持向后兼容调用点），或强制必传——实现期定，倾向前者（渐进接线，防未接线调用点硬失败）。

## Compliance

- **adr/0006(b)**「机械 prose MUST 脚本化」：坏输入判定（T138/T139）、hit-declared 一致性（T136）从「模型手 grep / 静默正规化」下沉脚本。
- **adr/0018（Proposed）**「机械校验器输出诚实」：T136 诚实标注只堵内部一致性（不冒充 tamper-proof）；T138/T139 坏输入 fail-closed 不静默正规化。**本 change 是 adr/0018 首形态 dogfood 加固**——为其升 Accepted 补实证。
- **机械/判断切分（D-6 核对 adr/0018 硬边界）**：T136 重算 `declared∩HR-TG` 是确定性派生（有信号）→ 机械；「命中哪些 TG」「declared 对不对」无信号 → 仍归模型。**未越界**（D1 论证）。
- **单一源**：HR-TG 成员续从 trigger-catalog 读；T136 复用 hr_tg_intersect 成员解析口径、不建副本。
- **纯 stdlib / 门控外置 / fail-closed**：三工具无第三方依赖、无 subprocess、不读 config、坏输入非零退出。
- **bundle 回灌**：改 assets/workflow 须 sdflow-init update + dev setup.sh，无沉默例外。
