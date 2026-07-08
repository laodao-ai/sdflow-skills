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
- emitter 输出**按构造过 `anchor_lint`**；坏输入 fail-closed。

**Non-Goals:**
- **不做去重 / 对抗裁决 / 严重度定级**——这三者是判断，留模型（产出结构化输入）。
- **不改锚形/枚举/契约版本**（v1 不变）；不迁归档旧锚。
- **不动 `anchor_lint`/`aggregator`**（emitter 与它们同读契约枚举，产出↔校验/聚合一致，无需改它们）。
- 不追求消灭信任边界（分类正确性本质是 judgment）。

## 数据流（TG-11）

```
主 session（判断层，保留）                emitter（机械归约层，新增）              校验/聚合（既有）
──────────────────────────────────────────────────────────────────────────────────────────
Step3 去重+对抗裁决+定级                                                          
  ↓ 产出结构化 findings + roster〔grill-amendment〕                               
  { roster:[canonical lens…本轮跑了哪些镜],                                       
    findings:[ {lenses:[raw镜名…], verdict:采纳|裁掉|defer,                       
                sev:致|高|中|低, layer, runner, site?}, … ] }                     
        │                                                                        
        └──▶ lens_metric_emit --layer L --input in.json                          
                 1. 读契约 lens-metric-enums + lens-metric-fold 块（enums+折叠 单一源）
                 2. 逐 finding: fold 每 raw 镜名 → canonical lens 集(去重)          
                 3. 归属: 每命中 canonical lens 记 findings/verdict +1            
                 4. 独立: |canonical 集|==1 ∧ verdict==采纳 → 该 lens 独立 +1       
                 5. sev rollup: 每 lens 按采纳项 sev 级累加 → 致N/高N/中N/低N       
                 6. emit 每 **roster** lens 一行：有 finding→归约计数，零→全零行 ──▶ anchor_lint 过(构造保证)
                    (强制 broad/outside-voice 恒有行; site 分组各独立行)           ────▶ 归档后 aggregator 聚合
```

## 组件清单（TG-14 · BASE-25）

| 组件 | 类型 | 落点 | 职责 | 分发 |
|------|------|------|------|------|
| `lens_metric_emit.py` | 新增脚本 | `sdflow-init/assets/workflow/tools/`（bundle 权威源）| 结构化 findings → 归约 → 合规锚行；fail-closed | bundle（`sdflow-init update` 铺消费仓）|
| `test_lens_metric_emit.py` | 新增测试 | `sdflow-init/tests/`（或 tools 同侧 tests/）| 折叠/归属/独立/sev/fail-closed/幂等/emit-then-lint | 随 skill |
| `lens-metric-contract.md` | 既有契约 | `assets/workflow/` | 枚举单一源（emitter 读）；补一句「emitter 为归约产者」注记（不改枚举、不升版本）| bundle |
| spec-review / code-review SKILL | 既有 | skill 目录 | 落锚步改「构造 findings → 调 emitter → 落输出」 | skill |

## Decisions

### ADR-1〔grill-amendment〕：输入 = per-finding 结构化 findings **+ lens roster**，emitter 内聚合
- **决策**：emitter 吃两部分——① 逐条 finding（每条带命中镜集/裁决/sev）；② **本轮跑了哪些镜的名册 `roster`**（canonical lens 列表，独立于是否有 finding）。聚合在 emitter 内做。
- **为何（grill 揭穿 2 驱动）**：per-finding 归约只能为「有 finding 的镜」产行；但 anchor_lint `MIN_LENS_ROWS=("broad","outside-voice")`（:135）在 metrics 开时**强制** broad/outside-voice 行存在，且「一个镜跑了但零 finding」**无法从 findings 推出**（findings 里根本没它）。故必须显式喂 roster，emitter 才能为零-finding 的镜落零行、满足强制行——否则 emitter 输出**过不了 anchor_lint**（自相矛盾 ADR-4）。
- **Alt（弃）**：只喂 findings、emitter 从 findings 推 roster——grill 揭穿其推不出「跑了但零 finding」的镜，强制行缺失。

### ADR-5〔grill-amendment〕：零-finding 镜落全零行，强制 broad/outside-voice 恒有行
- **决策**：emitter 为 `roster` 中每个 canonical lens 恒落一行——有 finding 则归约计数，零 finding 则落全零行（`findings=采纳=裁掉=defer=独立=0`、`sev=致0/高0/中0/低0`）。metrics 开时 roster MUST 含 `broad` 与 `outside-voice`（满足 MIN_LENS_ROWS），emitter 若发现 roster 缺此二者 → fail-closed 报明（防产出被 anchor_lint 拒）。
- **为何**：MIN_LENS_ROWS 是 anchor_lint 硬约束；零行是「本镜跑了但没抓到」的诚实留痕（反静默——空箱也显形，同 hr-tg 空箱纪律）。
- **Alt（弃）**：零-finding 镜不落行——过不了 anchor_lint 且「跑了没抓到」被静默吞（违反元原则）。

### ADR-2〔grill-amendment〕：折叠表提升为契约机读块 `lens-metric-fold`，emitter 从单一源读（根治）
- **决策**：在 `lens-metric-contract.md` 新增机读块 `lens-metric-fold`（同 `lens-metric-enums` 格式，`原始镜名: canonical-lens` 映射），emitter **从该块读折叠**（layer/lens/runner/sev 仍从 `lens-metric-enums` 读）——折叠**单一源**、emitter 非第二拷贝。枚举/折叠均不在脚本内复制清单。
- **为何（grill 揭穿驱动）**：grill 证伪原「emitter 折叠 ≡ aggregator 折叠」缓解——`lens_metric_aggregate.group_key`（:116）**只 group、不 fold**，读的归档锚 `lens` 值早已 canonical（模型写锚时手折叠过）；**折叠表当前只活在契约 prose（ADR-2/SR-D），从无代码单一源**。若 emitter「重实现折叠」，它就是**折叠的第一份且唯一代码拷贝**，与契约 prose 漂移无守卫（治标）。提升为机读块 = 折叠从此单一源、emitter/未来任何消费者都读它（根治，与契约「各生产者引用而 MUST NOT 复制清单」纪律一致）。
- **版本**：`lens-metric-fold` 是把**既有** prose 折叠映射机读化、**非新增镜类型**，故契约版本 v1 不升（enum 扩展治理只管新 lens 值）；块内新增/改映射走同块单一源更新。
- **Alt（弃）**：emitter 内硬编码折叠 + fixture 测试对契约 prose——grill 揭穿其仍是「prose + 一份代码拷贝」，fixture 与 prose 仍漂移（治标）。用户拍板取根治。

### ADR-3：信任边界一分为二——计数归约（机械）vs 输入分类（残余 judgment）
- **决策**：脚本保证「计数是**所给输入**的正确归约」；**不**保证「输入 findings 集 == 合并池实收 finding」。后者（模型对每条 finding 的镜集/裁决/sev 分类）显式声明为**残余主 session 信任边界**。
- **为何**：去重/裁决/定级本质 judgment（契约 SR-B 一脉）；诚实标边界，不谎称机械保证——与 anchor_lint「不谎称数值正确」同纪律。

### ADR-4：emit-then-lint 构造一致（emitter 输出过 anchor_lint）
- **决策**：emitter 与 anchor_lint 同读契约 `lens-metric-enums`、同 fence-aware 纪律；emitter 输出 MUST 按构造过 `check_lens_metric`。加测试：emitter 产锚 → 跑 anchor_lint → 断言 exit 0。
- **为何**：二者同源保证产出↔校验无口径分歧；杜绝「emitter 产的锚被 anchor_lint 拒」的自相矛盾。

## 契约套件 scope-check（TG-25 · BASE-29 · D-6 边界合规）

lens-metric 是跨模块共享契约；本 change 加 emitter 产者，MUST 确认不越 `lens-metric-contract` 边界、不与套件其他消费者漂移：

| 套件成员 | 角色 | 本 change 义务 | 是否改 |
|----------|------|----------------|--------|
| `lens-metric-contract.md` | 枚举+折叠单一源 | emitter 读取，MUST NOT 复制/分叉 | 〔grill〕**加 `lens-metric-fold` 机读块**（既有 prose 折叠机读化，非新 lens 值 → 不升版本）+ 补 emitter 注记 |
| `lens_metric_emit.py`（新）| 产者（归约）| 折叠/归属/sev 严守契约、折叠+枚举均读契约单一源 | 新增 |
| `anchor_lint.py` | 校验者 | emitter 输出按构造过它；同读枚举 | 不改 |
| `lens_metric_aggregate.py` | 消费者（聚合）| **仅 group 已 canonical 值、不 fold**（grill 确认）；其 canonical lens 输出 ⊆ fold 块 canonical 集 | 不改 |
| spec-review/code-review SKILL | 产者调用点 | 落锚步改调 emitter；构造 findings+roster | 改落锚步 |

**D-6 声明〔grill-amendment〕**：本 change **触** lens-metric 共享契约（加 `lens-metric-fold` 机读块）但**未越界**——不改锚形/枚举/契约版本（fold 块是既有 prose 折叠的机读化、非新 lens 类型）；折叠从此**单一源**（根治原「prose 无代码单一源」）。套件一致性由「emitter 输出过 anchor_lint」（ADR-4）+「折叠/枚举均读契约单一源」（ADR-2，无双实现可漂移）守。

## Risks / Trade-offs

- **[折叠漂移]**〔grill-amendment，原「双实现漂移」判据已证伪〕：grill 揭穿 aggregator **无折叠**（只 group 已 canonical 值），故不存在「emitter vs aggregator 双实现」；真风险是 emitter 折叠 vs 契约折叠表漂移 → **Mitigation**：折叠提升为契约 `lens-metric-fold` 机读块、emitter 读单一源（ADR-2 根治），**无第二拷贝可漂移**；另加测试断言 aggregator 消费的 canonical lens ⊆ fold 块输出集。
- **[输入分类错但计数"正确"]** 模型把 finding 归错镜/错裁决，emitter 仍机械归约出"自洽但错"的计数 → **Mitigation**：不可机械消除（judgment），ADR-3 诚实声明为残余边界；这与现状同等（现状手数也依赖分类正确），本 change 不使其变糟、只把计数环节的错误面消除。
- **[emitter 与 anchor_lint 枚举读取时机不一致]** 若契约升 v2 而 emitter 缓存旧枚举 → **Mitigation**：二者均运行时读契约、不缓存；enum 扩展治理（SR-E）要求升版本同步。
- **[消费仓 config 关 metrics]** → emitter 不落锚（门控一致），非风险，测试覆盖。

## Migration Plan

- 纯新增脚本 + 改两 SKILL 落锚步 prose；无数据迁移、无 schema 变更、无回滚复杂度。
- 部署：改 bundle 权威源 → `sdflow-init update` 下发消费仓（本仓 dogfood 直接 symlink 生效）。
- 回滚：删脚本 + SKILL 落锚步 revert 回手数（无状态残留）。

## Open Questions〔grill：两问已收敛，无遗留〕

- ~~折叠表机读化~~ → **已拍定（grill 共识 = 根治）**：本 change 即加契约 `lens-metric-fold` 机读块、emitter 单一源读折叠（见 ADR-2）。不再是未来项。
- ~~sev 单级 vs 多级~~ → **已拍定单级**：一条 finding 一个严重度（致/高/中/低），emitter 按采纳项 sev 级 rollup。无遗留。
