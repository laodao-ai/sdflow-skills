## Why

阶段三 gate（`ship_gate.py`）与 checkpoint 标签契约在多轮 change（sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source / gate-anchor-line-scoped）中各自留下 6 个**同一 capability、低增量**的硬化残项，散在 4 个批次里。按 fold-vs-defer 判据（BASE-18）三条齐（同 cap = gate+checkpoint 契约 · 高耦合 = 同 `ship_gate.py` / 同标签契约 · 低增量 = 6 小项机械）→ 合一个 change 清 3 整批，比逐批各走一轮 workflow 循环省得多。含 checkpoint-tag 的 B4 元 bug 上下文 + T43 防 gate 误判，属正确性骨架，优先级 P1。

## What Changes

- **T26** `sdflow-ship/SKILL.md` — 熔断重试计数脚本化探索：现「同一 invocation 内同步重跑一次仍无锚行 → UNKNOWN」靠 prose 计数（gate 零副作用约束下不落 state 文件）；探索计数下沉到确定性判据或显式登记为不下沉的取舍（TG-23 需 ADR）。
- **T35** `ship_gate.py` — 新鲜度是否可选纳入工作树 dirty 状态（T33 曾 WONTDO 的延续复议）：定夺纳入/不纳入并登记理由（TG-23 需 ADR）。
- **T36** `workflow.md` + `sdflow-ship/SKILL.md` — checkpoint 派发指令文案收敛为单一真相源（broad-F2）：现同一「`checkpoint-commit.sh <change>:task<N>-<slug>` 派发指令」在两处各写一份，改常量会漂（TG-25 契约文档套件一致性）。
- **T37** `spec-workflow` — 主 spec 内 checkpoint 标签形状（`<change>:task<号>-<slug>`）的 Scenario prose 复述是又一份需人工与 workflow.md/SKILL.md 保持一致的 doc 副本，澄清/收敛其表述。
- **T38** `spec-workflow` — Scenario 用词 `<当前change>` 易被误读为「须填本 change 真实 slug」，实现实际用任意占位 demo；改措辞消歧。
- **T43** checkpoint 标签 producer 模板 — 模板*展示*的机器锚收紧为独占 bare line（现带反引号/同行尾注），与真产报告一致；防未来报告照抄模板致 gate 行级锚解析误判（主 spec 行 306 已 MUST「各模板把锚写在独占一行」，本项让样例展示对齐该既有需求）。

## Capabilities

### New Capabilities
（无——全部是既有 gate/checkpoint 行为的硬化与澄清）

### Modified Capabilities
- `spec-workflow`: 收紧 checkpoint 标签契约的**单一真相源**与**模板样例一致性**（T36/T37/T38/T43），并对 gate 熔断计数（T26）与工作树 dirty 新鲜度（T35）两处未决设计点作 ADR 定夺后落为可验证需求。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（T26 熔断计数、T35 dirty 新鲜度）
- **规则/skill**：`sdflow-ship/SKILL.md`（T26/T36）、`sdflow-init/assets/workflow/workflow.md`（T36 派发文案单源）
- **契约脚本/模板**：`sdflow-init/assets/hack/checkpoint-commit.sh` 或其 producer 模板展示（T43 独占 bare line）
- **spec**：`openspec/specs/spec-workflow/spec.md` delta（T37/T38 措辞、T43 模板样例 Scenario、T26/T35 ADR 落地需求）
- **部署**：改 assets/workflow 与 assets/hack 须在开发 checkout 跑 `setup.sh` 使全局 canonical 生效
- **清账**：merge 后 sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source 三批可关，gate-anchor-line-scoped 的 T43 关（余 T41/T42 留 REC-2）
