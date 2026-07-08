# Tasks: lens-metric 计数确定性 emitter

> 实现走 TDD（先写失败测试 → 最小实现 → 绿）。脚本落 `sdflow-init/assets/workflow/tools/lens_metric_emit.py`（bundle 权威源），测试落 sibling `tests/`。禁 import yaml / lens_metric_aggregate / ship_gate（消费仓无）。

## 1. 契约枚举读取（单一源，follow anchor_lint）

- [ ] 1.1 写失败测试：`load_enums` 从 `lens-metric-contract.md` 的 `lens-metric-enums` fenced 块读 layer/lens/runner + sev-format 正则；缺块/空块 → `EnumsError`（fail-closed）。
- [ ] 1.2 实现 `load_enums`（重实现 fence-aware 读取，MUST NOT import anchor_lint/aggregator；可与 anchor_lint 同构但独立）；测试转绿。
- [ ] 1.3 写测试断言：emitter 内**无**硬编码 layer/lens/runner 枚举清单（枚举仅从契约读）。

## 2. 归约核心（折叠 + 归属 + 独立 + sev rollup）

- [ ] 2.1 写失败测试：单条 `采纳` finding、`lenses=["domain"]` → 输出一行 `lens=domain` 锚，`findings/采纳=1`、`独立=1`、`sev=致0/高1/中0/低0`（若 sev=高）。
- [ ] 2.2 实现折叠 `fold(raw)`：`对抗镜1/2/3→adversarial`、`完整性镜/完整性接地镜→grounding`、`autoplan/gstack 子声→broad`、`codex/claude-fallback→outside-voice`、`domain/grounding/history/broad` 恒等；未知 raw → fail-closed（不静默塞 broad，SR-E）。
- [ ] 2.3 写失败测试 + 实现归属：per-finding 折叠成 canonical lens 集（集内去重），每命中 lens 记 `findings/{采纳|裁掉|defer}` +1。
- [ ] 2.4 写失败测试 + 实现独立：`|canonical 集|==1 ∧ verdict==采纳` → 该 lens `独立` +1；共抓（集大小≥2）不计任一独立（spec Scenario：domain+outside-voice 共抓）。
- [ ] 2.5 写失败测试 + 实现「同类型多实例算独立」：`lenses=["对抗镜1","对抗镜2"]` 折叠后 canonical 集 `{adversarial}` size==1 → `adversarial.独立` +1（spec Scenario）。
- [ ] 2.6 写失败测试 + 实现 sev rollup：每 lens 按**采纳项**的 sev 级累加成 `致N/高N/中N/低N`（四级定序、零写 0、分隔恒 `/`）；裁掉/defer 项不计入 sev。
- [ ] 2.7 写失败测试 + 实现 site 分组：`outside-voice` 同轮 `site=code-voice`/`hr-tg` 各落独立一行；非 outside-voice `site=—`。

## 3. 输入校验 fail-closed

- [ ] 3.1 写失败测试：非法 JSON / 缺必填字段（无 `lenses`/`verdict`）→ 非零退出 + stderr 含被拒字段名 + 失败类别；MUST NOT 产锚、MUST NOT exit 0。
- [ ] 3.2 写失败测试 + 实现：`verdict` 越域（如 `通过`）/ `layer` 越域（如 `review`）/ `runner` 越域 / `sev` 级非法 → fail-closed 非零退出。
- [ ] 3.3 写失败测试 + 实现：`--layer` 与 finding 内 `layer` 冲突或缺失的处理（钉死一种口径并测试）。
- [ ] 3.4 写测试：config `metrics.enabled` 关 → emitter 不落锚（门控一致），退出 0 空产出。

## 4. 产出↔校验/聚合一致性（ADR-2 / ADR-4）

- [ ] 4.1 写测试（emit-then-lint）：emitter 对合法输入产锚写入临时报告 → 跑 `anchor_lint --layer L` → 断言 exit 0（字段/枚举/sev/layer==--layer/计数 int≥0 全过）。
- [ ] 4.2 写源仓一致性测试：断言 emitter 折叠 ≡ `lens_metric_aggregate` 折叠（同 raw 镜名映射同 canonical lens；二者跨 skill 不 import，靠本测试守漂移）。
- [ ] 4.3 写幂等测试：同一输入两次 emit 产出字节一致。

## 5. 两审 SKILL 落锚步接 emitter

- [ ] 5.1 改 `sdflow-spec-review/SKILL.md` Step3 落锚步：由「手折叠+手数+手写锚」改为「构造结构化 findings → 调 `lens_metric_emit` → 落输出」；**保留**残余信任边界声明（分类正确性仍是主 session 边界，非机械可验）。
- [ ] 5.2 改 `sdflow-code-review/SKILL.md` Step3-5 落锚步：同 5.1。
- [ ] 5.3 核对两 SKILL 未删「emitter 输出仍过 anchor_lint 自检」步（emit 与 lint 两步都在）。

## 6. 契约注记 + 部署

- [ ] 6.1 `lens-metric-contract.md` 补一句「计数由 `lens_metric_emit` 从结构化 findings 归约产出」注记（**不改枚举、不升版本**）。
- [ ] 6.2 `pytest sdflow-init/tests/`（或脚本 sibling tests）全绿；`pytest -W error` 无 warning。
- [ ] 6.3 本仓 dogfood：跑一次 `bash setup.sh` 使 bundle symlink 生效（新 tool 可被两审 SKILL 调到）。

## 7. 验收对账

- [ ] 7.1 逐条核对 specs（lens-metric-emit R1-R3 + workflow-metrics MODIFIED 信任边界 Scenario）均有测试锚点。
- [ ] 7.2 确认 D-6：未改锚形/枚举/版本；套件四成员一致性由 4.1 + 4.2 两测试守。
