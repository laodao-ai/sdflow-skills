## Why

spec-review Step3 / code-review Step5 出报告后，靠**主 session 手 grep 四类 v1 锚行 + 肉眼核 `layer`/`lens`/`runner`/`sev` 枚举与子格式**来自检报告完整性。这是一条典型的「机械 prose 协议」——弱档/走神的执行模型极易静默跳过或核错（adr/0006 硬约束的靶心：凡机械 prose 协议 MUST 脚本化）。同族的确定性化已在 `resolve-workflow.sh`、`ship_gate.py`、`trivial_shape.py` 三处落地；锚自检是仅剩的高频手工核验点（每轮 spec/code 评审各触发一次），ROI 兑现最快。

本变更是 roadmap `mechanical-layer-hardening` **阶段 2（Leg1 高频门禁）** 的实施，背景见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` 阶段 2、设计复用同目录 `design.md`。

## What Changes

- **新增 `anchor_lint.py`** 于 workflow bundle 工具目录（`sdflow-init/assets/workflow/tools/`，`trivial_shape.py` 同款先例）：`anchor_lint.py --report <path> --layer spec-review|code-review`，确定性校验一份评审报告——
  - **四类锚存在性**：`sdflow:outside-voice` / `sdflow:hr-tg` / `sdflow:step1-broad-review` 恒须存在；`sdflow:lens-metric` 受 `config.yaml metrics.enabled` 门控（关闭时缺此类不阻塞）。
  - **lens-metric 字段/枚举/子格式**：`layer` ∈ {spec-review, code-review}、`lens` ∈ {domain, adversarial, grounding, history, outside-voice, broad}、`runner` ∈ {claude, codex, claude-fallback}、`sev` = `致N/高N/中N/低N`；**`site` 不纳入越域自检**（契约 CF-补2：任意值只多一分组行、MUST NOT 报错）。
  - **枚举单一源**：从 `lens-metric-contract.md` 读（`__file__` 相对定位同 bundle 的 `../lens-metric-contract.md`），**不复制清单**。
  - **退出码承载判定**（trivial_shape 先例）：0=干净、非零=违规；脚本自身错误/读不到报告→非零（fail-closed）；双输出（human 行 + JSON）。
  - **复用而不重写** `lens_metric_aggregate.parse_anchor` / `_fence_aware_lines`（度量锚变长 KV 走前缀匹配）；**绝不用** `ship_gate.anchor_set` / `_line_scoped_hits`（gate 锚定长整行原语、匹配不了变长度量锚，冷审 F1）。
- **新增 `tools/tests/test_anchor_lint.py`**：坏样本（缺锚 / 越域枚举 / 缺字段 / fence 内示范锚）→ 断言非零退出；干净样本 → 0；metrics 门控关闭时 lens-metric 缺锚不阻塞。
- **改 `sdflow-spec-review/SKILL.md`（Step3 自检步）与 `sdflow-code-review/SKILL.md`（Step5 自检步）**：把「模型手 grep 四类锚 + 肉眼核枚举」改为调 `anchor_lint`；**保留诚实声明**——`findings=N` 与合并池实收数的数值一致性仍是主 session 信任边界、非机械可验（脚本不谎称能保证数值正确）。
- repo-root `openspec/workflow/tools/anchor_lint.py` 副本由 `sdflow-init update` 托管刷新（不手 copy，与 trivial_shape.py 一致）。

## Capabilities

### New Capabilities
<!-- 无新 capability——本变更强化现有评审自检行为，不引入新领域 -->

### Modified Capabilities
- `spec-workflow`: 新增需求——评审报告锚自检 MUST 由确定性脚本 `anchor_lint` 判定（存在性 + lens-metric 枚举/字段/子格式），MUST NOT 依模型手 grep；数值一致性 MUST 显式声明为主 session 信任边界、脚本不越权谎称机验（与 line 221 `resolve-workflow.sh`、line 327 `ship_gate.py` 的「机械协议脚本化」同族）。

## Impact

- **改动文件集**：新增 `sdflow-init/assets/workflow/tools/anchor_lint.py` + `tools/tests/test_anchor_lint.py`；改 `sdflow-spec-review/SKILL.md`、`sdflow-code-review/SKILL.md` 各一处自检步；spec delta 落 `spec-workflow`。
- **触 TG-02（Python 脚本技术栈）**：下游按 `spec-checklists/` 无命中领域（非 backend·go / embedded / frontend），走通用 BASE 清单。
- **依赖**：纯 stdlib（复用 `lens_metric_aggregate` 的 `parse_anchor`/`_fence_aware_lines`；无 yaml 依赖——repo 无 yaml，metrics.enabled 用受限 stdlib 读，见 design）。
- **发布边界**：改 bundle 权威源后须在开发 checkout 跑 `setup.sh`（刷新全局 canonical）才能让两审 SKILL 运行时解析到新 `anchor_lint.py`；消费仓经 `sdflow-init update` 拿到 tools 副本。
- **并行红线**：本变更改两审 SKILL.md——与 roadmap P4'/P5（同触两审或 producer SKILL）若同期须串行；P3 不触两审 SKILL，与本变更文件集不相交。

## Success Metrics

- 坏样本报告（缺任一恒须锚 / lens-metric 越域枚举 / 缺必填字段 / fence 内示范锚被误当真锚）→ `anchor_lint` 非零退出；干净样本 → 0。
- `metrics.enabled=false` 时 lens-metric 一类不校验不阻塞（与两审 SKILL 现有门控一致）。
- 两审 SKILL 自检步不再含「模型手 grep」措辞，改为调脚本；`pytest sdflow-init/assets/workflow/tools/tests/` 全绿。

## Non-Goals

- **不改** lens-metric 锚形/字段/枚举本身（契约 `lens-metric-contract.md` 不动）。
- **不做**数值一致性机验（`findings=N` vs 合并池实收数——主 session 信任边界，脚本诚实不兜）。
- **不改** `lens_metric_aggregate.py`（只复用其纯函数；aggregator 自身硬编码 enum 的潜在不一致留作 design 记录的 out-of-scope 后续）。
- **不做** config.yaml / batches.md 结构 lint（那是 roadmap 阶段 3 P3.B 的 scope）。
- **不迁** gate 状态锚 → frontmatter（roadmap 阶段 5）。

## Compliance

- 遵守 adr/0006（机械协议脚本化）、design §决策 5（fail-closed + 可观测 + 判断留人）、D4 无关（不碰 recorder）。
- 遵守 bundle 权威源纪律：改 `sdflow-init/assets/workflow/` 后经 `sdflow-init update` 下发，不直接改消费仓副本。
- 无安全/数据保护面（TG-17 N/A）；无外部服务成本（TG-24 N/A）。
