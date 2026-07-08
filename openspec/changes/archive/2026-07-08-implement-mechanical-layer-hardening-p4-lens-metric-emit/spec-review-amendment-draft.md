# Amendment 草案 · lens-metric-emit（两次面治 pass）

> **状态：草案·待你审定**。审定后回流 design/specs/tasks（标 `[spec-review-amendment]`）。
> 组织原则：不逐条打 Q1–Q6 补丁（点驱动会再留相邻面），而是两次「面治」——
> **Pass 1** 把 emitter 输入契约提为一等公民（收 C1/C2/C4/C6/C7/C8/C11/C12/C13/C14/C16）；
> **Pass 2** 单一源系统扫（收 C3/C10/C15/C17/C23）。

---

## Pass 1 · emitter 输入契约面治

### 1.1 统一粒度模型（Q1 + adv1F4/C18 的根）

**一句话**：所有计数与落锚都以**行键 `(lens, runner, site)`** 为单位——与锚唯一键 `(layer,lens,runner,site,轮)` 对齐（layer=--layer 单一源、轮=一次 emit）。roster、归属、独立、零行 全部建在这个键上，不再建在更粗的「canonical lens」上。

- **fold 的产物升级**：raw 镜命中 → `(canonical lens, runner, site)` 行键。
  - 非 outside-voice 镜：`runner=claude`、`site=—`（由 fold 恒定补齐，不需模型填）。
  - outside-voice 命中：`runner∈{codex,claude-fallback}`、`site∈{code-voice,hr-tg,design-voice}` **由 finding 的 hit-ref 显式携带**（raw「codex」对 site 有歧义，必须显式）。
- **独立**：一条 finding 命中的**去重行键集大小==1 ∧ verdict==采纳** → 该行 `独立+1`。
  - 「同类型多实例算独立」保留：对抗镜1+对抗镜2 都 fold 到同一行 `(adversarial,claude,—)` → 集大小仍 1 → 独立（与旧 task 2.5 一致）。
  - outside-voice 的 hr-tg 行 vs design-voice 行是**不同行键** → 唯一命中 hr-tg 的采纳 finding 把独立记到 hr-tg 行（C18 消解）。

### 1.2 权威 input schema（收 C16，字段名钉死，粒度对齐）

草案 schema（拟放 spec `lens-metric-emit` 一个机读块 + SKILL 落锚步直引）：

```
INPUT = {
  "roster": [                      # 本轮跑过的每个行键各一条（含零-finding 镜）
    {"lens": "<canonical>", "runner": "<runner>", "site": "<site|—>"}, ...
  ],
  "findings": [
    {
      "hits": [                    # 该 finding 被哪些行命中（替代旧 lenses:[raw...]）
        {"raw": "<原始镜名>", "runner": "<runner?>", "site": "<site?>"}, ...
      ],
      "verdict": "采纳|裁掉|defer",
      "sev": "致|高|中|低"          # verdict==采纳 时必填非空；否则忽略（见 R2）
    }, ...
  ]
}
```

- `raw` 走 fold → canonical lens；`runner/site` 对 outside-voice 必填，其余可省（fold 恒定补 claude/—）。
- 字段名一律英文（roster/findings/hits/raw/verdict/sev/runner/site/lens），**取值**中文（采纳/致…）。proposal:7 的 `命中镜集`/`裁决` 中文别名统一改英文键名。
- 附一份 **golden fixture**（合法输入 + 期望锚输出）供 SKILL 与测试共引。

### 1.3 ADR 增补（把口径从 task TODO 提回 design）

| 新 ADR | 决策 | 收 |
|--------|------|----|
| **ADR-6** roster 三元组 | roster 元素 = `(lens,runner,site)` 行键列表；emitter 按行键落零行 | Q1/C1 |
| **ADR-7** 折叠恒等语义 | `fold(raw)= raw if raw∈lens_enum（恒等 pass-through，复用 enum 块不复制清单）; elif raw∈fold_map → 映射值; else fail-closed`；fold 块**只列非恒等**映射 | Q2/C2 |
| **ADR-8** 归属/独立键 | 计数键 = 落锚键 = `(lens,runner,site)`；独立=去重行键集size1∧采纳 | C18/adv1F4 |
| **ADR-9** layer 单一源 | 从 input schema **删 per-finding layer**；锚 layer 恒取 `--layer` | Q6/C8 |
| **ADR-10** 门控归属 = SKILL | **emitter 不读 config**；SKILL 关 metrics 时不调 emitter、on 时才调。emitter 被调即视 metrics-on、**无条件强制** mandatory rows（见 Pass2 C17）。→ 彻底消除 emitter 侧「复刻 config 四态」需求 | Q5/C6 |

> **ADR-10 是关键简化**：把「emitter 自读 config 四态」整类问题（C6 + dogfood 分治盲区）从根上删掉——emitter 永不碰 config，门控留在它本就在的 SKILL 层。proposal:11「emitter 受 config 门控」改措辞为「由 SKILL 门控、emitter 被调即落锚」。

### 1.4 spec R2 坏输入**穷举**（收 C7/C11/C12/C13/C14；schema 驱动而非举例）

对 input schema 每字段 × {缺失 / present-but-empty / 越域 / 注入 / 边界} 逐格定 fail-closed：

| 坏输入 | 现状 | 草案 fail-closed 规则 | 收 |
|--------|------|----------------------|----|
| `hits:[]` 空数组 | 只查「缺 hits」 | present-but-empty 也 fail-closed（非空数组） | C11 |
| `verdict=采纳` 缺/空 `sev` | 只查「sev 级非法」 | 采纳⟹sev∈{致,高,中,低} 必填非空，否则 fail-closed；加不变量 `Σ(致+高+中+低)==采纳` 自检 | C12 |
| `site` 含 `"`/换行/`-->`/`=` | 无（anchor_lint 对 site 免检） | emitter 拒绝这些字符 → fail-closed（消毒，防注入绕过） | C7 |
| 边归约边写 → 部分锚 | 仅 prose 承诺 | **all-or-nothing**：任一校验失败 ⟹ stdout 无任何锚行 + exit≠0（validate-all→emit）；SKILL「exit 0 才用 stdout」 | C13 |
| fold 块重复/冲突 raw 键 | 未定义 | `load_fold` 遇重复/冲突 → fail-closed | C14 |
| roster 重复行键 | 未定义 | 去重或重复即 fail-closed | C14 |
| finding hits 行键 ∉ roster | 未处理（静默漏计） | **不变量：所有 finding 的行键 ⊆ roster，否则 fail-closed 报明** | C4 |

### 1.5 tasks 调整（Pass 1）
- 改 2.8：roster 恒落行按**行键**（非 lens）；零行 runner/site 由 roster 三元组给定。
- 新增：C4 反方向不变量测试、C11 空 hits、C12 采纳缺 sev + Σ 不变量、C7 site 注入、C13 all-or-nothing + stdout 空、C14 重复键（fold/roster）。
- 改 3.3：删 per-finding layer（ADR-9），测「finding 无 layer 字段」。
- 改 3.4：门控测试从「emitter 不落锚」改为「SKILL 关时不调 emitter」（emitter 不再读 config）。
- 新增：golden fixture 测试。

---

## Pass 2 · 单一源系统扫

### 2.1 单一源清单 + 逐项裁定（收 C3/C10/C15/C17/C23）

| 共享值 | 现状 | 草案裁定 | 收 |
|--------|------|----------|----|
| `lens/layer/runner/sev-format` enums | 契约 `lens-metric-enums` 块（已单一源） | 保持；emitter 读之 | — |
| **折叠表** | 本 change 提升为 `lens-metric-fold` 块 | 保持；+ **codomain⊆lens-enum 守卫**（见 2.2） | C3 |
| **MIN_LENS_ROWS** | anchor_lint 硬编码 `("broad","outside-voice")`、不在契约 | **二选一**（见 2.3 分叉①）：(a) 提升为契约块 `lens-metric-mandatory-rows` 双读；(b) 一致性测试断言 emitter 强制集==anchor_lint.MIN_LENS_ROWS | C17 |
| **verdict** `{采纳,裁掉,defer}` | 拟脚本内常量 | **显式豁免**：verdict 是 emitter 输入独有、不写进锚、不与 anchor_lint 共享 → 作脚本内常量 OK，但 design **须写明豁免理由**；不进契约块 | C15 |
| **sev 输入级** `{致,高,中,低}` | 拟脚本内常量 | 从契约 `sev-format` 模板**解析**得出（不硬编码），复用 enum 块 | C15 |
| **两份 load_enums** | anchor_lint 一份、emitter 一份（独立重实现） | 加**等价性测试**：`emitter.load_enums(contract)==anchor_lint.load_enums(contract)` 逐字段相等 | C10 |
| **aggregator LENS_ENUM/LAYER_ENUM** | 硬编码副本 | 纳入漂移守卫：一致性测试断言 `aggregator.LENS_ENUM/LAYER_ENUM==契约 enums`（见 2.2） | C23 |

### 2.2 C3 守卫方向修正（核心卖点落地）

tasks 4.2 从 `aggregator ⊆ fold_codomain`（在目标漂移下恒真、空转）改为**双向 + 三方一致**：
- `fold_codomain ⊆ enums.lens` **且** `enums.lens ⊆ fold_codomain 的 canonical 目标`（fold 块每个 canonical 目标必在 lens enum 内、且 lens enum 每值可被 fold 命中）；
- `aggregator.LENS_ENUM == enums.lens` 且 `aggregator.LAYER_ENUM == enums.layer`；
- emitter `load_fold` 后**自校验** codomain⊆lens-enum，越界 fail-closed（运行期兜底，不等 finding 出现才触发）。

### 2.3 ADR 增补（Pass 2）
- **ADR-11 单一源边界**：明列「哪些是跨消费者单一源（enums/fold）、哪些是本地常量豁免（verdict）、哪些靠一致性测试守（MIN_LENS_ROWS 若选 b、aggregator 硬编码、两份解析器）」，把「单一源」从口号变成有边界的清单。

### 2.4 tasks 调整（Pass 2）
- 改 4.2：按 2.2 双向+三方断言。
- 新增：load_enums 等价性测试、aggregator enum 一致性测试、fold codomain 自校验测试、MIN_LENS_ROWS 守卫测试（依分叉①）。
- 改 7.1：区分「机械测试锚点」vs「文档保留锚点」（收 X2/adv3F-I），诚实声明类 Scenario 不算 pytest 绿。

---

## 需你拍板的分叉点（其余为推荐直修）

| # | 分叉 | 选项 A（推荐） | 选项 B |
|---|------|---------------|--------|
| ① MIN_LENS_ROWS | C17 治法 | **提升为契约机读块**（与 fold 同纪律、真单一源） | 仅一致性测试（更轻、MIN_LENS_ROWS 稳定少变） |
| ② 折叠恒等 | Q2 语义 | **`raw∈enum 则恒等 pass-through`**（复用 enum、fold 块只列非恒等） | fold 块显式列全恒等项（无隐式规则、但清单变长） |

> 其余（Q1 roster 三元组、Q3 守卫方向、Q4 反方向不变量、Q5 门控归属=SKILL、Q6 删 per-finding layer）**推荐直修**，无实质分叉。

---

## C/Q → 改动映射（对账）

- **Pass 1**：C1→ADR-6 · C2→ADR-7(分叉②) · C4→R2不变量 · C6→ADR-10(消除) · C7→R2消毒 · C8→ADR-9 · C11/C12/C13/C14→R2穷举 · C16→1.2 schema · C18→ADR-8
- **Pass 2**：C3→2.2 · C10→等价性测试 · C15→豁免声明+sev解析 · C17→分叉① · C23→enum一致性测试
- **已回流**：C20/C21（design 接地订正，已 amend）
- **记录不阻断**：C19（ADR-3 补诚实账）· X1（Migration 加口径 caveat 一句）· X2/7.1（并入 2.4）
