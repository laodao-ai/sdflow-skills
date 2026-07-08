# 设计：lens-metric 计数确定性 emitter

## Context

**现状（D-1 代码事实）**：lens-metric 锚的计数当前由主 session 手做——
- 两审 SKILL 落锚步：主 session 手折叠原始镜名 → canonical `lens`、手数 `findings/采纳/裁掉/defer/独立`、手写 `sev` rollup、手拼锚行〔spec-review-amendment 接地订正：精确锚点为 `sdflow-spec-review/SKILL.md` 手折叠 :73 + emission Step4 :99-101、`sdflow-code-review/SKILL.md` 计数 :110-112 + emission Step5 :116；原引 :79/:124 落在 anchor_lint 自检门子步、非 emission 步〕。
- `lens-metric-contract.md`（`~/.sdflow/workflow/`，bundle 单一源）钉死锚形 + 枚举（`lens-metric-enums` 机读块）+ 折叠表（ADR-2，**prose**）+ 归属规则，并明写「数值跨源一致性 = 主 session 信任边界、非机械可验」。
- `anchor_lint.py`（bundle tool，`check_lens_metric`）机验锚**格式/枚举/sev/计数 int≥0**，但 `REQUIRED_FIELDS` 只校验存在性与域，**诚实声明不保证数值正确**。
- `lens_metric_aggregate.py`（skill-local，`sdflow-retro/scripts/`）跨 change 聚合归档锚：`group_key`(:116) **只按 `(layer,lens,runner,site)` group、不 fold**（读的归档锚 `lens` 值早已 canonical），另硬编码 `LENS_ENUM`/`LAYER_ENUM`(:17-18) 副本仅作越域 flag（消费仓无 sdflow-retro，故不与 emitter 互 import）〔spec-review-amendment 接地订正：原句「内部 group_key/fold 硬编码折叠逻辑」系 grill 前残留错误表述，与真实代码及本文档 ADR-2 自身结论「aggregator 无折叠」冲突，已更正〕。

**约束**：emitter 作 bundle tool 铺进消费仓 `openspec/workflow/tools/`，运行时**禁 import** `lens_metric_aggregate`/`ship_gate`（消费仓无 sdflow-retro/sdflow-ship）；**禁 import yaml**（消费仓无 PyYAML）——同 `anchor_lint` 零依赖 + 重实现惯例。

## Goals / Non-Goals

**Goals:**
- 把「结构化 findings → per-lens 计数 + 合规锚行」这段**确定性归约**从主 session 手做下沉给 `lens_metric_emit.py`。
- 收窄信任边界：计数环节机械化；残余边界收敛到「模型分类每条 finding（命中镜集/裁决/sev）是否正确」并诚实声明。
- emitter 输出**按构造过 `check_lens_metric`**（非 anchor_lint 整门）〔spec-review-amendment C5：anchor_lint.main 无条件先跑 check_existence、强制 outside-voice/hr-tg/step1-broad-review 三非-lens 锚族存在，emitter 不产之，故「过整门 exit 0」是过度声明；精确不变量 = 过 check_lens_metric 子校验〕；坏输入 fail-closed。

**Non-Goals:**
- **不做去重 / 对抗裁决 / 严重度定级**——这三者是判断，留模型（产出结构化输入）。
- **不改锚形/枚举/契约版本**（v1 不变）；不迁归档旧锚。
- **emitter 不读 config**〔spec-review-amendment ADR-10〕——门控归属 SKILL 层（关时不调 emitter），故 emitter 无「复刻 config 四态」需求。
- **不动 `anchor_lint`/`aggregator` 代码**（emitter 与它们同读契约枚举，产出↔校验/聚合一致）；但 aggregator 的硬编码 enum 副本纳入**一致性测试**漂移守卫〔spec-review-amendment C23〕。
- 不追求消灭信任边界（分类正确性本质是 judgment）；且诚实计入 emitter 引入的**新**手工错误面（roster 完备性 + JSON 誊写，见 Risks）〔spec-review-amendment C19〕。

## 数据流（TG-11）

```
主 session（判断层，保留）                emitter（机械归约层，新增）              校验/聚合（既有）
──────────────────────────────────────────────────────────────────────────────────────────
SKILL 门控: metrics 关→不调 emitter (ADR-10); 开→调 (emitter 不读 config)
Step3 去重+对抗裁决+定级
  ↓ 产出结构化 findings + roster〔spec-review-amendment：粒度升至行键 (lens,runner,site)〕
  { roster:[ {lens,runner,site}…本轮每个行键各一条 (含零-finding 镜) ],
    findings:[ {hits:[{raw镜名, runner?, site?}…], verdict:采纳|裁掉|defer,
                sev:致|高|中|低 }, … ] }          # 无 per-finding layer (ADR-9, 单一源=--layer)
        │
        └──▶ lens_metric_emit --layer L --input in.json   # emitter 被调即视 metrics-on
                 1. 读契约 lens-metric-enums + lens-metric-fold 块（enums+折叠 单一源）
                    load_fold 后自校验 codomain⊆lens-enum，越界 fail-closed (ADR-2/C3)
                 2. 逐 finding.hit: fold(raw)= raw if∈enum(恒等) elif fold_map else fail-closed (ADR-7)
                    → 行键 (canonical lens, runner|claude, site|—)；集内去重
                 3. 归属: 每命中行键记 findings/verdict +1 (键=落锚键, ADR-8)
                 4. 独立: |行键集|==1 ∧ verdict==采纳 → 该行 独立 +1 (对抗镜1/2 同行仍算独立)
                 5. sev rollup: 每行按采纳项 sev 级累加 → 致N/高N/中N/低N (采纳⟹sev 必填)
                 6. 不变量: 所有 finding 行键 MUST ⊆ roster，否则 fail-closed (C4 反方向)
                 7. all-or-nothing: 全校验过才 emit；任一失败→stdout 无锚+exit≠0 (C13)
                 8. emit 每 **roster 行键** 一行：有 finding→归约计数，零→全零行 ──▶ check_lens_metric 过(构造保证)
                    (强制 broad/outside-voice 恒有行, 一致性测试守 MIN_LENS_ROWS) ────▶ 归档后 aggregator 聚合
```

## 组件清单（TG-14 · BASE-25）

| 组件 | 类型 | 落点 | 职责 | 分发 |
|------|------|------|------|------|
| `lens_metric_emit.py` | 新增脚本 | `sdflow-init/assets/workflow/tools/`（bundle 权威源）| 结构化 findings → 归约 → 合规锚行；fail-closed | bundle（`sdflow-init update` 铺消费仓）|
| `test_lens_metric_emit.py` | 新增测试 | `sdflow-init/tests/`（或 tools 同侧 tests/）| 折叠/归属/独立/sev/fail-closed/幂等/emit-then-lint | 随 skill |
| `lens-metric-contract.md` | 既有契约 | `assets/workflow/` | 枚举单一源（emitter 读）；补一句「emitter 为归约产者」注记（不改枚举、不升版本）| bundle |
| spec-review / code-review SKILL | 既有 | skill 目录 | 落锚步改「构造 findings → 调 emitter → 落输出」 | skill |

## Decisions

### ADR-1〔grill-amendment；spec-review-amendment 升粒度〕：输入 = per-finding 结构化 findings **+ 行键 roster**，emitter 内聚合
- **决策**：emitter 吃两部分——① 逐条 finding（每条带 hits 命中行键集/裁决/sev）；② **本轮跑了哪些行键的名册 `roster`**（`(lens,runner,site)` 三元组列表，独立于是否有 finding）。聚合在 emitter 内做。
- **〔spec-review-amendment 粒度修正（C1，7 镜命中）〕**：roster 元素由「canonical lens」升为**行键 `(lens,runner,site)`**——因锚唯一键 = `(layer,lens,runner,site,轮)` 且 `anchor_lint.REQUIRED_FIELDS` 强制每行含 `runner`；lens-only roster **推不出零-finding 行的 runner/site**（outside-voice 零行 runner∈{codex,claude-fallback}、site∈{code-voice,hr-tg,design-voice} 无源可推），且 SR-D 的 site 拆分在零-finding 路径不可实现。升行键后零行 runner/site 由 roster 三元组直接给定。详见 ADR-8 归属键。
- **为何（grill 揭穿 2 驱动）**：per-finding 归约只能为「有 finding 的镜」产行；但 anchor_lint `MIN_LENS_ROWS=("broad","outside-voice")`（:135）在 metrics 开时**强制** broad/outside-voice 行存在，且「一个镜跑了但零 finding」**无法从 findings 推出**（findings 里根本没它）。故必须显式喂 roster，emitter 才能为零-finding 的镜落零行、满足强制行——否则 emitter 输出**过不了 anchor_lint**（自相矛盾 ADR-4）。
- **Alt（弃）**：只喂 findings、emitter 从 findings 推 roster——grill 揭穿其推不出「跑了但零 finding」的镜，强制行缺失。

### ADR-5〔grill-amendment；spec-review-amendment 升行键 + 门控归属〕：零-finding 行落全零行，强制 broad/outside-voice 恒有行
- **决策**：emitter 为 `roster` 中每个**行键 `(lens,runner,site)`** 恒落一行——有 finding 则归约计数，零 finding 则落全零行（`findings=采纳=裁掉=defer=独立=0`、`sev=致0/高0/中0/低0`，runner/site 取自 roster 行键）。emitter **被调即视 metrics-on**（门控在 SKILL 层，ADR-10），无条件校验 roster MUST 含 `broad` 与 `outside-voice`（满足 MIN_LENS_ROWS），缺则 fail-closed 报明。
- **为何**：MIN_LENS_ROWS 是 anchor_lint 硬约束；零行是「本镜跑了但没抓到」的诚实留痕（反静默——空箱也显形，同 hr-tg 空箱纪律）。
- **〔spec-review-amendment C17（分叉①=B）〕MIN_LENS_ROWS 单一源守卫**：emitter 需知「哪些行是强制的」（broad/outside-voice），此集与 `anchor_lint.MIN_LENS_ROWS` 是**跨消费者共享值**。选 **B（一致性测试）**——不提升为契约块（MIN_LENS_ROWS 仅 2 值、极少变，单一源块的边际收益低于其成本），改由测试断言 `emitter 强制集 == anchor_lint.MIN_LENS_ROWS`，捕获二者漂移。见 ADR-11 单一源边界。
- **Alt（弃）**：零-finding 行不落——过不了 anchor_lint 且「跑了没抓到」被静默吞（违反元原则）。

### ADR-2〔grill-amendment〕：折叠表提升为契约机读块 `lens-metric-fold`，emitter 从单一源读（根治）
- **决策**：在 `lens-metric-contract.md` 新增机读块 `lens-metric-fold`（同 `lens-metric-enums` 格式，`原始镜名: canonical-lens` 映射），emitter **从该块读折叠**（layer/lens/runner/sev 仍从 `lens-metric-enums` 读）——折叠**单一源**、emitter 非第二拷贝。枚举/折叠均不在脚本内复制清单。
- **为何（grill 揭穿驱动）**：grill 证伪原「emitter 折叠 ≡ aggregator 折叠」缓解——`lens_metric_aggregate.group_key`（:116）**只 group、不 fold**，读的归档锚 `lens` 值早已 canonical（模型写锚时手折叠过）；**折叠表当前只活在契约 prose（ADR-2/SR-D），从无代码单一源**。若 emitter「重实现折叠」，它就是**折叠的第一份且唯一代码拷贝**，与契约 prose 漂移无守卫（治标）。提升为机读块 = 折叠从此单一源、emitter/未来任何消费者都读它（根治，与契约「各生产者引用而 MUST NOT 复制清单」纪律一致）。
- **版本**：`lens-metric-fold` 是把**既有** prose 折叠映射机读化、**非新增镜类型**，故契约版本 v1 不升（enum 扩展治理只管新 lens 值）；块内新增/改映射走同块单一源更新。
- **Alt（弃）**：emitter 内硬编码折叠 + fixture 测试对契约 prose——grill 揭穿其仍是「prose + 一份代码拷贝」，fixture 与 prose 仍漂移（治标）。用户拍板取根治。

### ADR-3：信任边界一分为二——计数归约（机械）vs 输入分类（残余 judgment）
- **决策**：脚本保证「计数是**所给输入**的正确归约」；**不**保证「输入 findings 集 == 合并池实收 finding」。后者（模型对每条 finding 的镜集/裁决/sev 分类）显式声明为**残余主 session 信任边界**。
- **为何**：去重/裁决/定级本质 judgment（契约 SR-B 一脉）；诚实标边界，不谎称机械保证——与 anchor_lint「不谎称数值正确」同纪律。

### ADR-4〔spec-review-amendment C5/C10 收窄〕：emit-then-lint 构造一致（emitter 输出过 check_lens_metric，非整门）
- **决策**：emitter 与 anchor_lint 同读契约 `lens-metric-enums`、同 fence-aware 纪律；emitter 输出 MUST 按构造过 **`check_lens_metric`**（字段/枚举/sev/layer==--layer/计数 int≥0）。测试口径二选一：(a) fixture 报告**预置** outside-voice/hr-tg/step1-broad-review 三 MANDATORY 锚族 + emitter 产的 lens 行 → 跑完整 anchor_lint 断言 exit 0；**或** (b) 只对 emitter 输出调 `check_lens_metric` 断言无违规。**MUST NOT** 声明「emitter 单独输出过 anchor_lint 整门 exit 0」（emitter 不产三 MANDATORY 族，整门必 exit 1）。
- **〔spec-review-amendment C10〕两份 load_enums 等价性**：「同读一个文件」≠「同一解析器」——emitter 与 anchor_lint 各自重实现 fence-aware 读取。加**等价性测试**：`emitter.load_enums(contract) == anchor_lint.load_enums(contract)` 逐字段相等，杜绝二者对 fence 缩进/trim/闭合判定的细微分歧读出不同 enum 集。
- **为何**：二者同源 + 等价性测试保证产出↔校验无口径分歧；杜绝「emitter 产的锚被 anchor_lint 拒」的自相矛盾。

### ADR-6〔spec-review-amendment〕：权威 input schema，字段名钉死
- **决策**：input schema（roster + findings）由 spec `lens-metric-emit` 一个机读块 + golden fixture 承载单一权威定义，两审 SKILL 落锚步**直引不复述**。字段名一律英文：`roster/findings/hits/raw/verdict/sev/runner/site/lens`；取值中文（采纳/致…）。proposal 的 `命中镜集`/`裁决` 中文别名统一改英文键名。
- **为何（C16）**：现状 schema 散落 proposal/design/spec、键名中英混杂，模型每轮现拼易猜错字段名 → fail-closed 阻塞评审流。权威 schema + fixture 消歧。

### ADR-7〔spec-review-amendment；分叉②=A〕：折叠恒等 pass-through，fold 块只列非恒等
- **决策**：`fold(raw) = raw if raw∈lens_enum（恒等 pass-through，复用 enum 块、不复制清单）; elif raw∈fold_map → 映射值; else fail-closed`。契约 `lens-metric-fold` 块**只列非恒等**映射（对抗镜1/2/3→adversarial、领域镜→domain、历史镜→history、接地镜/完整性镜→grounding、codex/claude-fallback→outside-voice、autoplan子声/gstack-adv→broad 等）。
- **为何（C2，4 镜命中）**：tasks 原「恒等项 domain/grounding/history 可省略」建立在 raw==canonical 的**类别错误**——契约折叠表实为中文→英文非恒等映射，raw 名是「领域镜/历史镜/接地镜」而非 domain/history/grounding。若省略则 `fold("领域镜")` 对最常见输入 fail-closed。pass-through 用「raw∈lens_enum→恒等」承载恒等（复用 enum、零清单重复），fold 块只列真映射，二义消解。
- **Alt（弃·分叉②-B）**：fold 块显式列全恒等项——无隐式规则但清单变长 4 行，且制造「改 enum 忘改 fold」新漂移面。

### ADR-8〔spec-review-amendment〕：归属/独立键 = 落锚键 = `(lens,runner,site)`
- **决策**：所有计数（findings/采纳/裁掉/defer/独立）以**行键 `(lens,runner,site)`** 为单位、与落锚键一致。独立 = 一条 finding 去重后**行键集 size==1 ∧ verdict==采纳** → 该行 独立+1。
- **为何（C18/adv1F4）**：原归属按 canonical lens、落锚按 `(lens,runner,site)`（SR-D site 拆行）—— 粒度错配使「per-lens 独立数落哪一 site 行」未定义。统一到行键后：对抗镜1+2 folds 到同一 `(adversarial,claude,—)` 行→集 size1→仍算独立（保「同类型多实例算独立」）；唯一命中 outside-voice hr-tg 行的采纳 finding 把独立记到 hr-tg 行。契约「独立在折叠后计」的 prose 精化为「折叠到行键后计」。

### ADR-9〔spec-review-amendment〕：layer 单一源 = `--layer`，删 per-finding layer
- **决策**：input schema **无 per-finding `layer` 字段**；锚 layer 恒取 CLI `--layer`。
- **为何（C8，4 镜命中）**：一次 emit 本就是单层调用，per-finding layer 冗余、且 anchor_lint 硬查 `layer==--layer`，双源邀请漂移（finding.layer≠--layer 时产出必被 anchor_lint 拒）。删冗余字段消除冲突面。

### ADR-10〔spec-review-amendment〕：门控归属 = SKILL 层，emitter 不读 config
- **决策**：**emitter 永不读 config.yaml**。metrics 门控留在 SKILL 层（本就在此，spec-review/code-review 落锚前读 `metrics.enabled`）——关时 SKILL 不调 emitter、不落锚；开时才调，emitter 被调即视 metrics-on、无条件强制 mandatory rows。proposal「emitter 受 config 门控」改措辞为「由 SKILL 门控、emitter 被调即落锚」。
- **为何（C6，4 镜命中 + dogfood 盲区）**：若 emitter 自读 config，因禁 import yaml 须**重实现** anchor_lint `read_metrics_enabled` 四态（缺文件/无块/**块坏 fail-closed**/解出）——tasks 原只测「关」漏「坏块」，正是 MEMORY 记的「缺失=放行 vs 存在坏=fail-closed 要分治」盲区。**门控归 SKILL 后此整类问题从根删除**（emitter 无 config 依赖、无第三份四态重实现）。
- **Alt（弃）**：emitter 自读 config——须复刻四态 + 坏块测试，且与 anchor_lint 口径须逐一对齐，复杂度净增。

### ADR-11〔spec-review-amendment〕：单一源边界清单（把「单一源」从口号变有边界的清单）
- **决策**：明列跨消费者共享值的治理方式，避免「只治被 grill 点到的折叠表、相邻面漏治」：
  | 共享值 | 治理 |
  |--------|------|
  | `lens/layer/runner/sev-format` enums | 契约 `lens-metric-enums` 块单一源，emitter+anchor_lint 读 |
  | 折叠表 | 契约 `lens-metric-fold` 块单一源；+ codomain⊆lens-enum 守卫（见 Risks） |
  | MIN_LENS_ROWS | **本地常量 + 一致性测试**守（分叉①=B，不提升块） |
  | verdict `{采纳,裁掉,defer}` | **本地常量豁免**——emitter 输入独有、不写进锚、不与 anchor_lint 共享，故非跨消费者单一源项；design 显式声明豁免理由 |
  | sev 输入级 `{致,高,中,低}` | 从契约 `sev-format` 模板**解析**（不硬编码） |
  | 两份 load_enums | **等价性测试**守（ADR-4） |
  | aggregator LENS_ENUM/LAYER_ENUM | **一致性测试**断言 == 契约 enums（C23） |
- **为何（C3/C10/C15/C17/C23）**：单一源根治须「面治」——逐项裁定「已单一源 / 提升 / 本地豁免 / 一致性测试守」，而非只治一处留相邻面。

## 契约套件 scope-check（TG-25 · BASE-29 · D-6 边界合规）

lens-metric 是跨模块共享契约；本 change 加 emitter 产者，MUST 确认不越 `lens-metric-contract` 边界、不与套件其他消费者漂移：

| 套件成员 | 角色 | 本 change 义务 | 是否改 |
|----------|------|----------------|--------|
| `lens-metric-contract.md` | 枚举+折叠单一源 | emitter 读取，MUST NOT 复制/分叉 | 〔grill〕**加 `lens-metric-fold` 机读块**（既有 prose 折叠机读化，非新 lens 值 → 不升版本）+ 补 emitter 注记 |
| `lens_metric_emit.py`（新）| 产者（归约）| 折叠/归属/sev 严守契约、折叠+枚举均读契约单一源 | 新增 |
| `anchor_lint.py` | 校验者 | emitter 输出按构造过 `check_lens_metric`；同读枚举（等价性测试守） | 不改 |
| `lens_metric_aggregate.py` | 消费者（聚合）| **仅 group 已 canonical 值、不 fold**（grill 确认）；其硬编码 `LENS_ENUM/LAYER_ENUM` 纳入一致性测试（==契约 enums）〔spec-review-amendment C23〕 | 不改（仅测试守） |
| spec-review/code-review SKILL | 产者调用点 + 门控 | 落锚步改调 emitter；构造 findings+行键 roster；**门控 metrics（关时不调 emitter）**〔ADR-10〕 | 改落锚步 |

**D-6 声明〔grill-amendment；spec-review-amendment 补守卫〕**：本 change **触** lens-metric 共享契约（加 `lens-metric-fold` 机读块）但**未越界**——不改锚形/枚举/契约版本（fold 块是既有 prose 折叠的机读化、非新 lens 类型）；折叠从此**单一源**。套件一致性由多重守卫（非单一声明）保：① emitter 输出过 `check_lens_metric`（ADR-4）；② 折叠/枚举读契约单一源 + `load_fold` 后 **codomain⊆lens-enum 自校验**（ADR-2/C3）；③ 两份 load_enums 等价性测试 + aggregator enum 一致性测试（ADR-11）——单一源边界见 ADR-11 清单。

## Risks / Trade-offs

- **[折叠/enum 块漂移]**〔spec-review-amendment C3 守卫方向修正〕：aggregator **无折叠**（只 group 已 canonical 值），真风险是**契约 `lens-metric-fold` 块 codomain vs `lens-metric-enums` 的 lens 域漂移**（fold 块加一个映射到 enum 外 canonical）。原 mitigation「断言 aggregator ⊆ fold_codomain」**方向反了、在此漂移下恒真（空转）**——aggregator 6 值 ⊆ fold 7 值仍成立。**修正 Mitigation**：① 测试断言 `fold_codomain ⊆ enums.lens` **双向**（fold 每 canonical 目标 ∈ lens enum；反向 lens enum 每值可被 fold 命中）；② emitter `load_fold` 后**自校验** codomain⊆lens-enum、越界 fail-closed（运行期兜底，不等 finding 出现）；③ 断言 `aggregator.LENS_ENUM/LAYER_ENUM == 契约 enums`（纳硬编码副本入守卫）。此三重守卫使「加映射到新 canonical」被测试红逼着走「先改 lens-enum→触发 v2 治理」，治理边界从人判变机验（兼收 F-G）。
- **[输入分类错但计数"正确"]〔spec-review-amendment C19 诚实账〕** 模型把 finding 归错行键/错裁决，emitter 仍机械归约出"自洽但错"的计数 → **Mitigation**：不可机械消除（judgment），ADR-3 诚实声明为残余边界。**诚实计入新错误面**：emitter 引入 roster + 结构化 JSON 两道**新**手工工序——roster 完备性（漏/多列行键，emitter 无从校验真跑了啥）+ JSON 誊写（verdict 采纳↔裁掉写反、sev 填错，都在枚举域内 fail-closed 抓不到）。诚实结论 = 「**算术**错误面消除，但**分类+誊写+roster** 错误面从 1 处终态锚**迁移并细化**到每条 finding，非总错误面单调下降」——本 change 净效果 = 以更结构化的手工输入换算术确定性，非无损收窄。
- **[emitter 与 anchor_lint 枚举读取时机不一致]** 若契约升 v2 而 emitter 缓存旧枚举 → **Mitigation**：二者均运行时读契约、不缓存；enum 扩展治理（SR-E）要求升版本同步；等价性测试守二者解析口径一致（ADR-4/C10）。
- **[site 未消毒注入]〔spec-review-amendment C7〕** site 自由文本含 `"`/换行/`-->` 可破坏锚语法且绕过 anchor_lint（对 site 免检）→ **Mitigation**：emitter 拒绝 site 含 `"`/换行/`-->`/`=` → fail-closed（R2 坏输入清单覆盖）。
- **[消费仓 config 关 metrics]** → SKILL 不调 emitter（门控归 SKILL，ADR-10），非风险。

## Migration Plan

- 纯新增脚本 + 改两 SKILL 落锚步 prose；无数据迁移、无 schema 变更、无回滚复杂度。
- 部署：改 bundle 权威源 → `sdflow-init update` 下发消费仓（本仓 dogfood 直接 symlink 生效）。
- 回滚：删脚本 + SKILL 落锚步 revert 回手数（无状态残留）。
- **〔spec-review-amendment X1〕新旧锚跨轮口径 caveat**：归档旧锚是手数产、新锚 emitter 归约产，若历史手数在归属/独立口径有错则跨轮趋势含新旧混合。aggregator 已有「独立率跨轮不保证同口径」caveat 兜底且只呈现不决策——非硬风险；比对以 emitter 起始轮为准。

## Open Questions〔grill 两问 + spec-review 已收敛，无遗留〕

- ~~折叠表机读化~~ → **已拍定（grill 共识 = 根治）**：加契约 `lens-metric-fold` 机读块、emitter 单一源读折叠（ADR-2）+ codomain 守卫（C3）。
- ~~sev 单级 vs 多级~~ → **已拍定单级**：一条 finding 一个严重度，emitter 按采纳项 rollup（采纳⟹sev 必填，C12）。
- ~~roster 粒度 / 门控归属 / layer 口径 / 折叠恒等语义~~ → **spec-review 已拍定**：行键 roster（ADR-1/8）· 门控归 SKILL（ADR-10）· 删 per-finding layer（ADR-9）· 恒等 pass-through（ADR-7，分叉②=A）· MIN_LENS_ROWS 一致性测试（ADR-5，分叉①=B）。无遗留。
