## Why

lens-metric 锚的计数（`findings`/`采纳`/`裁掉`/`defer`/`独立` + `sev` rollup）当前由主 session **手数**：两审 SKILL 与 `lens-metric-contract.md` 都白纸黑字承认「数值跨源一致性 = 主 session 信任边界、非机械可验、自核无独立性」（即承认会错、只是没脚本兜底）。P2 的 `anchor_lint` 只机验锚**格式/枚举**、并诚实声明「不谎称保证数值正确」——那句声明正是本洞未合的自供状。adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」，而「按归属规则把结构化 findings 折叠成 per-镜计数」是纯确定性归约。本变更是 roadmap `mechanical-layer-hardening` 阶段 4（4.C），目标态重评判为 **★ 该做未做**（直闭 requirements §1.2 痛点 #2「模型手数 → 自认信任边界」）。

## What Changes

- **新增 `lens_metric_emit.py`**（bundle tool，经 `sdflow-init update` 铺进消费仓 `openspec/workflow/tools/`）：吃**主 session 给的行键 roster + 结构化 findings**（JSON，字段名英文/取值中文，权威 schema 见能力 `lens-metric-emit`〔spec-review-amendment ADR-6〕：roster=`(lens,runner,site)` 行键列表；findings 每条带 `hits`（命中行）/`verdict`∈{采纳,裁掉,defer}/`sev`；**无 per-finding layer**，layer 单一源=`--layer`〔ADR-9〕），按 `lens-metric-contract.md` 的**折叠表 + 归属规则**确定性归约出——① 每**行键 `(lens,runner,site)`** 一行**格式/枚举/字段合法**的 lens-metric 锚；② per-行键计数（`findings`/`采纳`/`裁掉`/`defer`/`独立`，`独立`=唯一报过 ∧ 被采纳、折叠到行键后计〔ADR-8〕）；③ `sev` rollup（`致/高/中/低`，仅采纳项计入，零也写 0）。枚举从契约 **`lens-metric-enums` 块**、折叠从 **`lens-metric-fold` 块**单一源读（不在脚本内复制清单，follow anchor_lint 惯例）。
- **信任边界收窄（非消灭，诚实声明）**：计数从「手数」收敛为「脚本对**已给结构化输入**的确定性归约」；残余信任边界 = 「模型是否把每条 finding 分类正确（`命中镜集`/`裁决`/`sev`）」。脚本 MUST NOT 谎称保证「输入 findings 与合并池实收 finding 吻合」——它只保证**计数是所给输入的正确归约**。去重 + 对抗裁决 + sev 定级仍是模型的活（产出结构化输入）。
- **两审 SKILL 落锚步改调 emitter**：`sdflow-spec-review` Step3 / `sdflow-code-review` Step3-5 的 lens-metric 落锚由「手折叠 + 手写锚」改为「构造结构化 findings → 调 `lens_metric_emit` → 落其输出」。
- **产出侧闭环**：emitter 输出的锚**按构造即通过 `anchor_lint`**（二者同读契约 `lens-metric-enums` 单一源）；fail-closed——坏输入（越域 enum / 缺字段 / 非法裁决值 / 坏 JSON）非零退出 + 可读 reason，绝不静默产出空锚或 exit 0。
- **门控由 SKILL 层承担、emitter 不读 config**〔spec-review-amendment ADR-10〕：`metrics.enabled` 关时 SKILL 不调 emitter（不落锚）、开时才调；emitter 被调即视 metrics-on、无条件强制 mandatory rows。此举从根消除「emitter 复刻 config 四态 fail-closed」整类问题（含 dogfood 缺失/坏块分治盲区）。

## Capabilities

### New Capabilities
- `lens-metric-emit`: 确定性 lens-metric 锚 emitter 的行为契约——结构化 findings 输入 schema、折叠/归属/计数/sev-rollup 归约规则、fail-closed 语义、契约单一源读取、与 anchor_lint 的产出↔校验一致性。

### Modified Capabilities
- `workflow-metrics`: 度量锚计数从「主 session 手数（信任边界、非机械）」收敛为「emitter 对结构化 findings 的确定性归约」；信任边界收窄至「模型分类正确性」并诚实保留；「独立贡献在 Step3 去重时导出」的计数环节改由 emitter 机械归约。

## Impact

- **新增**：`sdflow-init/assets/workflow/tools/lens_metric_emit.py`（bundle 权威源）+ pytest（坏输入 fail-closed / 折叠归属 / 独立计数 / sev rollup / 幂等）。
- **修改**：`sdflow-spec-review/SKILL.md`、`sdflow-code-review/SKILL.md` 落锚步（构造行键 roster + hits findings、门控关时不调 emitter）；`lens-metric-contract.md` 加 `lens-metric-fold` 机读块（只列非恒等映射）+ 补「emitter 为归约产者」注记（不改枚举、不升版本）；`独立在折叠后计` prose 精化为「折叠到行键后计」。
- **无外部依赖**：纯 stdlib + 读契约文件（禁 import yaml / 禁读 config〔ADR-10 门控外置〕/ 禁 import lens_metric_aggregate——消费仓无 sdflow-retro，同 anchor_lint 重实现折叠/fence 逻辑）。
- **兼容**：不改锚形/枚举/契约版本（v1 不变）；归档旧锚不受影响；关 metrics 的消费仓无行为变化。
