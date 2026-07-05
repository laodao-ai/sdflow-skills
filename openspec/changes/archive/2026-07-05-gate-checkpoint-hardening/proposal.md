## Why

阶段三 gate（`ship_gate.py`）与 checkpoint 标签契约在多轮 change（sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source / gate-anchor-line-scoped）中各自留下 6 个**同一 capability、低增量**的硬化残项，散在 4 个批次里。按 fold-vs-defer 判据（BASE-18）三条齐（同 cap = gate+checkpoint 契约 · 高耦合 = 同 `ship_gate.py` / 同标签契约 · 低增量 = 6 小项机械）→ 合一个 change 清 3 整批，比逐批各走一轮 workflow 循环省得多。含 checkpoint-tag 的 B4 元 bug 上下文 + T43 防 gate 误判，属正确性骨架，优先级 P1。

## What Changes

- **T26**（ADR-2，spec-review Q1 定稿）`sdflow-ship/SKILL.md` + `ship_gate.py` — 熔断：持久化计数不可做（撞三红线，登记接受取舍）；触发判据 = **该步 ship-gate 锚行集合是否变化**（复用 `_line_scoped_hits`，HEAD/mtime 不作免疫信号），做成**无状态比较 helper**（快照作参数、不落地、可 CI 测）。〔spec-review SR-1 推翻了 grill 的 HEAD/mtime 判据〕
- **T35**（ADR-1，spec-review Q2 缩简版）`ship_gate.py` + `sdflow-ship/SKILL.md` + `sdflow-done/SKILL.md` — gate 新鲜度守 committed-only（T33/T35 gate 侧 WONTDO）；软提示（sdflow-ship）+ **merge 前只查「分支内新产 untracked」→ halt+报告（非交互，不引入阶段三 AskUserQuestion）**。〔tracked 经 git add -u 一路 defer todolist T51〕
- **T36**（ADR-3）`ship_gate.py` TAG_RE + `workflow.md` + `sdflow-ship/SKILL.md` — checkpoint 标签**格式/规则分治单源**：格式权威 = TAG_RE（加 canonical-shape 头注释，`checkpoint-commit.sh` format-agnostic 非源）；规则「每任务用命名空间标签」就地留 workflow.md 一处，SKILL 引用（TG-25）。
- **T37** `spec-workflow` — Scenario 复述标签形状标注为"样例非权威"（权威在 TAG_RE），消除又一份 doc 副本。
- **T38** `spec-workflow` — Scenario 用词 `<当前change>` → `<change-slug>`，消除"须填真实 slug"歧义。
- **T43** ship-gate 机器锚模板（`sdflow-spec-review/SKILL.md:102` 带反引号、`sdflow-code-review/SKILL.md:149-150` 带同行尾注）收紧为独占 bare line，与真产报告一致；防报告照抄模板致 gate 行级锚 `strip()≠字面` 漏判（对齐主 spec 行 306 既有「独占行」MUST）。

## Capabilities

### New Capabilities
（无——全部是既有 gate/checkpoint 行为的硬化与澄清）

### Modified Capabilities
- `spec-workflow`: 收紧 checkpoint 标签契约的**单一真相源**与**模板样例一致性**（T36/T37/T38/T43），并对 gate 熔断计数（T26）与工作树 dirty 新鲜度（T35）两处未决设计点作 ADR 定夺后落为可验证需求。

> **scope 边界**〔grill Q5〕：grill 中 fold 了 sdflow-done merge 硬检查（T35 的另一半）；**就此打住，不再扩容**。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（T26 熔断触发对照逻辑或注释、T35 committed-only 注释、T36 TAG_RE canonical-shape 头注释）
- **skill**：`sdflow-ship/SKILL.md`（T26 触发硬化 + T35 软提示 + T36 引用式）、`sdflow-done/SKILL.md`（T35 merge 硬检查）、`sdflow-spec-review/SKILL.md:102` + `sdflow-code-review/SKILL.md:149-150`（T43 锚模板裸行）
- **规则**：`sdflow-init/assets/workflow/workflow.md`（T36 规则源一处 + 引用）
- **spec**：`openspec/specs/spec-workflow/spec.md` delta（T36 单源 / T35 committed-only+merge 检查 / T26 熔断触发不下沉 / T37/T38 措辞 / T43 锚独占行）
- **非改**：`checkpoint-commit.sh`（format-agnostic、非格式源）、`test_producer_parser_contract.py`（守卫，不改格式本身）
- **部署**：改 assets/workflow 须在开发 checkout 跑 `setup.sh` 使全局 canonical 生效
- **清账**：merge 后 sdflow-ship / ship-gate-hardening-2 / checkpoint-tag-single-source 三批可关，gate-anchor-line-scoped 的 T43 关（余 T41/T42 留 REC-2）
