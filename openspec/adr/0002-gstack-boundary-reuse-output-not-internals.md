# gstack 边界：复用产出物、不依赖内部实现

自制 skill 与 gstack/superpowers 的边界按一条线切：**读它们的产出物（output artifact）合法，依赖它们的内部实现非法。**

- gstack 自家 skill（autoplan、gstack review）的能力**原样不动、照常使用**，包括读它们产出的文件（如 `gstack-review.md`）。spec-review "复用" autoplan 的设计 outside voice = 读 `gstack-review.md` 里 `codex#N`-标签的 findings，属**复用产出物**，合规。
- "不引用 / 不依赖 gstack·superpowers 内部工具" 只约束**我们自制的 skill**（spec-review 自跑的 cross-model、impl-review 的 code outside voice、codex 共享 helper）：它们**不得**调用 gstack 内部 bin / 探针 / config，须自包含重写。

配套两道焊缝防"读产出物"退化成静默失效：(1) 读不到 / 解析不出 / 0 条时显式降级并回落自带 outside voice，不静默当"无 voice"；(2) "复用"依赖 autoplan 每次都跑（P2b），若 P2b 回退条件触发，自制 skill 须自跑设计 outside voice。

## Considered Options

- **复用产出物 + 自制机制不碰内部（选中）**：普通变更省一次 codex（读 autoplan 已产出的 gstack-review.md），高风险域和 code 侧走自包含重写的 helper。兼顾效率与升级安全，但需守卫防 gstack 输出格式漂移。
- **全自包含、连产出物也不读**：spec-review 每次自跑设计 outside voice，彻底断 gstack 耦合。最干净，但普通变更**双 codex**（autoplan + spec-review 各一次），浪费且慢。
- **裸复用、无守卫**：直接读 gstack-review.md 不做降级处理。gstack 改格式即静默捞到 0 条、丢整层评审覆盖而不报错——"假绿"同构，不可接受。

## Consequences

- spec-review 需实现"读 gstack-review.md → 解析 codex 段 → 缺失/0 条则回落自带 voice + 打降级日志"这段 fallback 逻辑。
- codex 共享 helper（探针 / exec 包装 / prompt 模板 / off-switch）**只依赖 codex CLI 本身**，不继承 gstack 修复；gstack 改 codex 接口时须手动更新这份拷贝（低频可控）。
- C2 与 P2b 之间是硬依赖，两条决策落地时须交叉引用；OQ2 回退 P2b 时必须同步启用 spec-review 自跑路径，否则漏评审覆盖。
- gstack 若重命名 gstack-review.md 或改 codex#N 标签约定，只会触发降级回落（多跑一次自带 codex），不会静默失效——可接受的退化方向。
