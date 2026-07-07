# mlh-p1-issues-sweep

> roadmap `mechanical-layer-hardening` 阶段 1（Leg 1 脚本化开路）。见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` §阶段 1 + `design.md` §候选表 P1。

## Why

`sdflow-done` 收尾的 issues sweep（§2.1）现在是**模型手跑 4 步 bash 循环**——SKILL 自认「纯机械 bash」：`scan` 两池 → 解析 JSON 取每个 id → 逐 id `triage --批次 {change}` → `batch add` → `reindex`。这类「模型解析 JSON + for 循环调子脚本」是确定性机械活，模型手跑易漏/重、且违反 adr/0006「机械 prose 协议 MUST 脚本化」。这是 roadmap 里**最就绪、最低爆炸半径**的固化候选（纯新增子命令，零现有行为改动）。

## What Changes

- **`issues.py` 新增 `sweep --change X` 原子子命令**：内部 `scan` buglist+todolist 两池 → 按 `源==X ∧ status 非终态 ∧ 批次空` 过滤 → 逐项 `triage` 入批次（bug/todo 各走对应脚本，幂等：已 PROPOSED no-op）→ `batch add X`（已存在跳过）→ `reindex`，一路做完。模型只提供 `--change` 名。
- **`sdflow-done/SKILL.md` §2.1** 手循环 prose 替换为一行 `sweep` 调用（保留「孤儿项(源="")不归本 sweep」边界声明）。
- **`sdflow-issues/SKILL.md`** 命令面补 `sweep` 文档。

## Impact

- Affected: `sdflow-issues/scripts/issues.py`（+ `tests/test_issues.py`）、`sdflow-done/SKILL.md`、`sdflow-issues/SKILL.md`。
- **行为对齐 done SKILL 文档边界**〔spec-review Q1〕：sweep 语义对齐 done §2.1 文档边界「源==X ∧ 非终态 ∧ 批次空」（用既有 `scan --open-ungrouped`），**比原手循环的 `scan --status OPEN` 更精确**——补了原命令漏的「批次空」过滤、纳入非 OPEN 的非终态项。不改 triage/batch add/reindex 各自行为。（非逐字复刻有 bug 的原命令，故「行为保持」按「对齐文档边界」理解。）
- 数据类 skill：改 `scripts/` 必跑 `pytest sdflow-issues/tests/`。
- 无 spec 破坏性变更；spec delta = spec-workflow 新增「issues sweep 原子子命令」需求。
- **爆炸半径**：issues.py 走 skill symlink，非 bundle 回灌；sdflow-done SKILL.md 同理。
