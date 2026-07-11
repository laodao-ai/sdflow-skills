# design — harden-hr-tg-anchor-consistency

> **grill 收敛（2026-07-11，全深度·目标态·零妥协）`[grill-amendment]`**：以三条基准重导（CLAUDE.md「设计/分析基准原则」+ [[change-scope-one-complete-stage-result]]）：
> - **Q1〔schema〕**：hr-tg 锚两套活 schema——主 spec `spec-workflow:550` 写 `hit=/evidence=`（无 declared），mlh-p4 码却要 `declared=`。裁定 `declared=` canonical 必填、`evidence=` 并存人读；**回灌 :550**。
> - **目标态机械化面治（撤"覆盖薄"降级）**：曾用「corpus 多数锚手写 evidence= → T136 覆盖薄」论证降级，违基准（拿现状反驳目标）。正解：锚目标态（所有锚走脚本必有 declared=），把 hr-tg 锚一致性拆 M1/M2/M3/M4/M-new **全机械化**；仅 S1「declared=真命中集」无信号 → 语义残余。
> - **零妥协〔碎片化根治〕**：原 fragment 视角拟的三处妥协——`--trigger-catalog` WARN 降级、`--allow-legacy` flag、declared grace——**全删**：一次做完整、fail-closed，妥协不产生（`--trigger-catalog` 必需、缺 declared 硬违规、无迁移旁路）。
> - **M-new fold**：grill 中发现「TG 只查 shape 不查存在」漏网格，与本功能相关 → 立即 fold 做掉。
> - **scope 收窄**：T139（outside_voice_guard）是另一 capability，**剥出另开**（todolist T139）；本 change = hr-tg 锚一致性单一完整交付物。

## Context

MLH 阶段 4·4.D 三校验器 SHIPPED 后冷审 defer。本 change 收「hr-tg 锚一致性机械化」一件完整的事（`hr_tg_intersect` 出锚 + `anchor_lint` 校验），一次到目标态。

**接地事实（已 grep 核验，带行锚，D-1）：**

- **M3（T138）** `hr_tg_intersect.py`：`parse_tg_set`（`:57` split → `:58 [t for t in tokens if t]` 静默过滤空 cell → `:60` strict）→ `TG-04,,TG-16` 误过、`,` 误判空集。成员抽取 `:45 _TG_TOKEN_RE.findall`（`:14 r'TG-\d+'` 宽松）→ `TG-04x` 被抽 `TG-04`。
- **M-new** 两工具**均只查 shape、不查存在**：`parse_tg_set` 只 `_TG_STRICT_RE.match`（`^TG-\d+$`），`load_hr_tg_subset` 只取 HR-TG 成员——`TG-99`/`TG-1`（合法 shape、catalog 无此定义）不被拦，与 HR-TG 求交时当"非成员"静默丢出 hit。
- **M1/M2/M4** `anchor_lint.py`：`check_hr_tg`（`:163-174`）`for f in HR_TG_REQUIRED_FIELDS`（`:171`，`:160 =("hit","declared")`）只查在场；docstring（`:164-165`）明写「字段值任意合法，命中判定归模型，脚本不校验 CSV 内容」——**无 `--trigger-catalog`、无重算、无 evidence 校验**。anchor_lint 规格权威地 = 主 spec `spec-workflow`（:753 锚自检 requirement + :550 hr-tg 锚定义）。
- **HR-TG 单一源 + catalog TG 全集**：`trigger-catalog.md` `## 七、HR-TG` `> 成员：`（8 个）；全 TG 定义在 A–G 段表行 `| TG-NN |`（TG-01..TG-26）。`hr_tg_intersect.parse_members`（`:26-51`）已解析 HR-TG 单一源，M-new 复用同源加解析「全 TG 集」。

## Goals / Non-Goals

**Goals**：hr-tg 锚可确定性校验的一致性一次机械化到位、全 fail-closed、零妥协：M1 declared 硬必填 / M2 hit⟺declared∩HR-TG 重算 / M3 严格解析 / M4 evidence 在场 / M-new TG 存在性；`--trigger-catalog` 必需；回灌 spec:550。续纯 stdlib、门控外置。

**Non-Goals**：T139（另 capability，剥出）、T137（config，用户裁断）；S1（declared 正确性）无信号 → 留语义残余、不冒充 tamper-proof；不引第三方依赖、不改 setup.sh/ship_gate.py。

## Decisions

### D1〔TG-23〕anchor_lint hr-tg 锚一致性机械化面治（M1/M2/M4/M-new），零妥协 `[grill-amendment]`
**决策：`check_hr_tg` 接必需 `--trigger-catalog`，把全部确定性一致性一次机械化：M1 `declared=` 硬必填（缺→违规，无 grace）；M2 重算 `declared∩HR-TG` 要 `hit=` 逐元素一致（none⟺空交集）；M4 `hit≠none⟹evidence=` 在场非空；M-new declared/hit 每 TG 须存在于 catalog 全 TG 集。`--trigger-catalog` 未传 → 非零退出（fail-closed），MUST NOT WARN 降级放行。**

- **目标态非现状**〔基准〕：所有锚目标态经脚本产出、必有 declared=；现状 evidence=-only 存量是 rollout 债，不作覆盖面论据。
- **零妥协**〔碎片化根治〕：`--trigger-catalog` 必需 fail-closed（非 WARN 降级——降级=fail-open 架空 M2/M4；本 change 原子接线两 SKILL 调用点，无未接线残留，故可硬要求）；无 `--allow-legacy`（B3 实证归档不重 lint，为不存在的场景留旁路 = YAGNI）；无 declared grace（同）。
- **adr 合规**：M1/M2/M4/M-new 是 adr/0006(b)「机械 prose MUST 脚本化」的完整落实；未越 adr/0018「命中判定归模型」（`declared` 仍模型给）。
- **主次**：一次机械化全确定性面 + fail-closed（目标态、无妥协）> fragment 逐个补 + 现状妥协。

### D2〔TG-23〕S1 语义残余划分：declared 正确性留语义，不冒充 tamper-proof `[grill-amendment]`
**决策：脚本只机械化 `hit=declared∩HR-TG`（确定性派生）；`declared` 是否=真命中集（S1）无确定性信号 → 留模型判定 + evidence= 人读 + git 审计。docs/SKILL MUST 声明「M2 只堵内部一致性、不使锚 tamper-proof」。**
- M2 堵「手改单字段 `hit=none declared=TG-04` 内部矛盾」，**堵不住**「同改 hit+declared 一致但错」——那需 declared 正确性、无机械信号。**这是完整机械化后剩下的合法残余划分，非弱点、非妥协。**
- **主次**：诚实标注残余边界 > 冒充 tamper-proof（会假绿）。

### D3〔TG-23〕hr_tg_intersect 严格解析 + TG 存在性（M3+M-new）`[grill-amendment]`
**决策：`parse_tg_set` 删空 cell 静默过滤（仅原始空串表空集，空 cell/前后逗号→EmitError）；成员抽取词边界严格（`TG-04x`→EmitError）；declared/hit 每 TG 须存在于 catalog 全 TG 集（`TG-99`/`TG-1`→EmitError）。M-new 双侧落地（emit 时 hr_tg_intersect + lint 时 anchor_lint）。**
- **M-new 价值**：`TG-16`手误`TG-1`（合法 shape、不存在）→ 静默丢出 hit → 漏一个 HR-TG 命中、不开 cross-model。有确定性信号（catalog 全集单一源）→ MUST 机械化。
- **主次**：显式空串表空集（保留合法空集入口）> 一律非空。

### D5〔切片建议·scope 决定管线，非反向〕`[grill-amendment]`
> 本 change 按内聚性收窄后自然 ~2 片（emit 侧 / lint 侧）→ **跌破 tickets 3–6 下限** → ship 时按 merit 走 **superpowers**，**不再是 Phase A tickets 样本#2**（样本另找天生 3+ 片单一能力）。管线是 ship 时决策、不反向绑 scope（decomposition standard）。

参考切分（superpowers task 粒度更细，此处仅示意内聚边界）：
- **hr_tg_intersect 出锚侧**（R1）：M3 严格解析 + M-new 存在性 + catalog 全集解析 helper。
- **anchor_lint 校验侧**（R2）：M1/M2/M4/M-new（复用出锚侧 helper）+ `--trigger-catalog` 必需 + spec:550 回灌 + 两 SKILL 接线。

## Risks / Trade-offs

- **[部署 skew：工具经 sdflow-init update、SKILL 经 setup.sh，两路径可能不同步]** → `--trigger-catalog` 必需时 skew 会**响亮 fail-closed**（逼修），非 fail-open 静默降级门；由 CLAUDE.md pull→setup 原子纪律兜。这是架构事实、非现状妥协。
- **[M-new catalog 全集解析]** → 复用既有成员解析口径、同单一源；catalog 表行 `| TG-NN |` 稳定可 parse，坏则 fail-closed。
- **[M2 被误读 tamper-proof]** → docs 显式声明 + 「一致但错→仍过」边界确认负例。
- **[bundle 回灌遗忘]** → Migration 段固化。

## 失败模式表〔TG-12/15〕

| 工具 | 坏输入/失败 | 行为 | 可观测 |
|---|---|---|---|
| hr_tg_intersect | tg-set 空 cell（`TG-04,,TG-16`/`,`）（M3） | `EmitError` | `[hr_tg_intersect] FAIL: 空 cell` |
| hr_tg_intersect | 成员/tg-set 畸形 token（`TG-04x`）（M3） | `EmitError` | 解析失败 |
| 两工具 | TG 不存在于 catalog 全集（`TG-99`）（M-new） | `EmitError` | TG 未定义 |
| anchor_lint | 缺 `declared=`（M1，无 grace） | 违规、非零 | `missing-field` |
| anchor_lint | `hit`≠`declared∩HR-TG`（M2） | 违规 | `hit-declared-mismatch` |
| anchor_lint | `hit≠none` 缺/空 `evidence=`（M4） | 违规 | `evidence-missing` |
| anchor_lint | 未传 `--trigger-catalog`（fail-closed） | 非零退出（**非 WARN**） | `[anchor_lint] FAIL: 缺 --trigger-catalog` |

## 组件 / 数据流图〔TG-11〕

```
单一源 / 入参                             工具（tools/，纯 stdlib）                消费方
trigger-catalog 七.HR-TG 成员 + 全 TG 集 ─┐
tg-set（模型判定，M3 严格 + M-new 存在）  ─┼─► hr_tg_intersect.py ─► hit/none｜依据模型判定 + 锚(hit/declared) ─► spec/code-review
评审报告 hr-tg 锚 + trigger-catalog(必需) ──► anchor_lint.check_hr_tg [M1/M2/M4/M-new] ─► 违规/通过 ─► spec/code-review 自检
  权威源改动 ── sdflow-init update ──► openspec/workflow/tools/（下游副本，不含 tests/）
  anchor_lint 复用 hr_tg_intersect 的成员/全集解析 + 严格 tg-set 口径（同单一源、非 import）
```

## Migration Plan（bundle 回灌纪律）

1. 两工具面治 + 扩 `tests/` 写权威源 `sdflow-init/assets/workflow/tools/(tests/)`。
2. `sdflow-code-review`/`sdflow-spec-review` 的 anchor_lint 调用步补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`（M2 前提，**与工具改动同一 change 原子落**，防 skew 期硬失败）。
3. dev checkout 跑 `bash setup.sh` 同步 canonical。
4. `sdflow-init update` 推下游副本（下游不含 tests/，核对脚本本体）。
5. 回滚：还原两工具 + SKILL 接线；无数据迁移。

## Open Questions（grill 已消解）
- ~~有无流程重 lint 归档报告~~ → B3 已核验：无 → 无需 grace（D1 零妥协）。
- 违规 `kind` 命名（`hit-declared-mismatch`/`evidence-missing`）实现期可微调。
- catalog「全 TG 集」解析：以 A–G 段表行 `| TG-NN |` 为源（删除的空号自然不在集）；实现期确认解析口径与成员解析一致。

## Compliance

- **adr/0006(b)**「机械 prose MUST 脚本化」：M1/M2/M3/M4/M-new 全部下沉脚本、fail-closed。
- **adr/0018（Proposed）**「机械校验器输出诚实」：M2 诚实标注只堵内部一致性、S1 留语义、不冒充 tamper-proof。本 change 为 adr/0018 首形态 dogfood 加固、补升 Accepted 实证。
- **机械/语义残余划分（D-6 核对 adr/0018）**：确定性派生（M1/M2/M4/M-new）机械；declared 正确性（S1）无信号 → 语义。**未越界**。
- **单一源**：HR-TG 成员 + 全 TG 集续从 trigger-catalog 读、不硬编码。
- **纯 stdlib / 门控外置 / fail-closed**：两工具无第三方依赖、无 subprocess、不读 config、坏输入非零退出。
- **decomposition standard**：一个完整内聚交付物（hr-tg 锚一致性）、不拆碎不混做、M-new 相关即 fold、T139/T137 剥出。
- **adr/0019（Proposed）**（hr-tg 锚 canonical schema + 一致性机械化面治 vs 语义残余划分）——本 change 收敛时立，待 ship+dogfood 升 Accepted。
