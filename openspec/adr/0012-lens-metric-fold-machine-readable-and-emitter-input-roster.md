# lens-metric 折叠表机读化为契约单一源，emitter 输入 = findings + lens roster

`mlh-p4-lens-metric-emit` 把 lens-metric 计数从主 session 手数下沉给确定性 `lens_metric_emit.py`（roadmap P4·4.C，闭 requirements §1.2 痛点#2「手数信任边界」）。grill design.md 揭穿两处「代码与主张不符」，据此定本 ADR。

## Context（grill 两揭穿）

**揭穿①：折叠表无代码单一源。** design 初版 ADR-2 靠「源仓测试断言 emitter 折叠 ≡ `lens_metric_aggregate` 折叠」守漂移。grill 证伪——`lens_metric_aggregate.group_key`（:116）**只 group、不 fold**：它读的归档锚 `lens` 值早已 canonical（模型写锚时手折叠过）。折叠映射（`对抗镜N→adversarial`/`完整性镜→grounding`/`codex→outside-voice`/`autoplan·gstack→broad`）**当前只活在契约 prose（度量锚契约 ADR-2/SR-D），从无代码单一源**。若 emitter「脚本内重实现折叠」，它是折叠的**第一份且唯一代码拷贝**，与契约 prose 漂移无守卫——治标。

**揭穿②：强制行不可从 findings 推。** `anchor_lint.MIN_LENS_ROWS=("broad","outside-voice")`（:135）在 metrics 开时**强制**此二 lens 行存在，缺则 `missing-lens-row` 违规。但「一个镜跑了但零 finding」**无法从 findings 集推出**（findings 里根本没它）。故 emitter 若只吃 findings，无法为零-finding 的强制镜落行 → 输出**过不了 anchor_lint**，与「emitter 输出按构造过 anchor_lint」自相矛盾。

## Decision

1. **折叠表提升为契约机读块 `lens-metric-fold`**（同 `lens-metric-enums` 格式，`原始镜名: canonical-lens`），emitter 从该块读折叠、枚举仍从 `lens-metric-enums` 读——折叠**单一源**、emitter 及未来任何消费者读之，非第二拷贝。属既有 prose 折叠的**机读化**（非新 lens 类型）→ 契约版本 v1 不升（enum 扩展治理只管新 lens 值）。
2. **emitter 输入 = findings + lens roster**：除逐条 finding（命中镜集/裁决/sev/layer/runner/site）外，MUST 显式喂 `roster`（本轮跑了哪些 canonical lens，独立于是否有 finding）。emitter 为 roster 中每个 lens 恒落一行——有 finding 归约计数、零 finding 落全零行；metrics 开时 roster 缺 `broad`/`outside-voice` → fail-closed。

## Considered Options

- **折叠机读块 + roster 输入（选中）**：折叠单一源根治漂移面（与契约「各生产者引用而 MUST NOT 复制清单」纪律一致）；roster 让强制行可满足且「跑了没抓到」诚实留痕（反静默元原则）。代价：触共享契约加一机读块（D-6，非越界、非升版本）+ 输入多一字段。与 workflow「根治非治标」「盘面即状态」一脉。
- **emitter 内硬编码折叠 + 对契约 prose 的 fixture 测试（弃）**：仍是「prose + 一份代码拷贝」，fixture 与 prose 仍可漂移（治标）；grill 揭穿后用户拍板取根治。
- **只喂 findings、emitter 从 findings 推 roster（弃）**：推不出「跑了但零 finding」的镜，强制行缺失、输出被 anchor_lint 拒。
- **零-finding 镜不落行（弃）**：过不了 MIN_LENS_ROWS，且「本镜跑了没抓到」被静默吞（违反「任何评审覆盖不得无声蒸发」元原则，同 hr-tg 空箱纪律）。

## Consequences

- **mlh-p4-lens-metric-emit 落地本 ADR**：design 订正 ADR-1（补 roster）/ADR-2（折叠改契约机读块、揭穿 aggregator 无折叠）+ 新增 ADR-5（roster 零行 + 强制行 fail-closed）；specs 补「roster 零行」「强制 broad/outside-voice」「折叠单一源」Scenario；tasks 补「加 `lens-metric-fold` 块」「`load_fold`」「roster 恒落行」，并把原「emitter 折叠≡aggregator 折叠」测试订正为「aggregator 消费的 canonical lens ⊆ fold 块输出域」。
- **折叠从此单一源**：`lens-metric-fold` 块是折叠唯一权威；新增/改镜折叠映射 MUST 只改此块（同 enums 单一源纪律）；aggregator 虽不 fold，其 group 到的 canonical lens 亦须 ⊆ 该块输出域（测试守）。
- **与度量锚契约（workflow-metrics）互补**：契约原「lens 为 canonical 投影、映射表见 design ADR-2」的 prose 折叠，本 ADR 给它一个机读落点；「数值一致性=信任边界」经本 change 收窄为「计数机械归约（emitter）+ 分类残余判断（模型）」两层，诚实声明（见 CONTEXT.md 新术语）。
- **与 adr/0006 同哲学**：机械 prose 协议 MUST 脚本化/结构化——折叠表是「机械 prose」的又一实例，本 ADR 把它从 prose 升为机读单一源，是 adr/0006 的又一次落地。
- **CONTEXT.md**：新增术语「计数归约 vs 分类判断（Count Reduction vs Classification Judgment）」——emitter 机械归约计数、模型保留分类，残余信任边界 = 分类正确性。
