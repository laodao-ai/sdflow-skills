# spec-review 报告 — mlh-p3-determ-guards

> 阶段二设计评审编排（连续跑）：Step1 广审（simulated 降级）+ Step2 六镜并行（领域/对抗A/对抗B/接地/outside-voice codex→fallback）+ Step3 对抗裁决合并。
> **总判**：设计骨架站得住（AST 契约实测吻合、拓扑正确、无副作用、归一回归真实），但 **3.B（config_lint + batch lint）多处前提遗漏须先订正**——已全部回写 [spec-review-amendment]。**1 项需设计门拍板**（Q1 config_lint 手写 vs PyYAML）。

## 命中范围

- 栈：无 backend·go/embedded/frontend 领域命中（数据类 tooling：recorder scripts + init/issues + 测试）
- 镜：广审(EM,simulated) + 领域(本项目约定) + 对抗A(隐藏假设/失败模式) + 对抗B(乐观估计/边界) + 接地(代码事实) + outside-voice(codex→claude-fallback,timeout)
- TG：TG-15(新codepath)/TG-18(测试计划)/TG-22(未验证前提·已证伪并解决)/TG-23(≥2方案→Q1)
- HR-TG：**none**（命中 TG ∩ HR-TG子集{04,06,07,08,09,16,17,26}=∅）
- Step1 广审：EM 视角冷镜 simulated（autoplan 非原生暴露），6 findings 全采纳，详见 gstack-review.md

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="TG命中15/18/22/23,均不属HR-TG子集;无DB迁移/跨模块数据/API合约/外部依赖/状态机/NFR/信任边界/并发" -->

## 决策登记区

```
┌─────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  config_lint yaml 处理：手写 stdlib 扫描 vs 引 PyYAML     │
│ [自动决策] D1  优先级<待填>占位符豁免（H1，五镜收敛）→ D5 扩两字段     │
│ [自动决策] D2  优先级前导 token 后不校验剩余（H4）→ D4 订正           │
│ [自动决策] D3  block_ranges 两处 AST 差异均归一（H3）→ D6/Task1.1     │
│ [自动决策] D4  config_lint 手写 stdlib+mode第4值+条件化（H2/M2/M3）   │
│ [自动决策] D5  PRIORITIES 值相等断言非 getsource（M1）→ R4           │
│ [自动决策] D6  model-tiers overrides措辞/注释态回归（M4）+ Metrics分层│
│              (M5) + Compliance拆D4(M6) + --root(M7) + helper删test(L1)│
│ [已裁掉]  （无）——六镜 findings 全部经实测复现，无假阳可裁            │
└─────────────────────────────────────────────────────────────────┘
```

### [需拍板] Q1：config_lint 的 yaml 处理路径

**背景**：proposal 原称「纯 stdlib + 现有 yaml 处理」，接地实测**双重证伪**——init.py 全文无 `import yaml`、从不解析 config 内容；全仓无 PyYAML、无依赖声明机制。「纯 stdlib」与「需 yaml.safe_load」自相矛盾。

**选项**：
- **A（推荐·已回写为默认）手写 stdlib 行级结构扫描**：follow 仓内既有范式 `anchor_lint.py::read_metrics_enabled`（手写行锚正则、零依赖）。只扫本 lint 需要的特定顶层键，非全量 yaml 解析。
- **B 引 PyYAML 依赖**：`yaml.safe_load` 全量解析。

**三面后果**：
- 系统：A 零新依赖、消费仓 symlink 运行不炸；B 引入全仓首个第三方依赖，消费仓无依赖管理机制 → `import yaml` ImportError 崩（非 fail-closed）。
- 用户（消费仓）：A 无感；B 须每个消费仓装 PyYAML 否则 config_lint 不可用。
- 开发循环：A 手写多层缩进扫描比 anchor_lint 单层 metrics 复杂、工作量略增；B 解析代码更短，但要新建依赖声明+降级策略（本设计不含）。

**主次判定**：**系统面（零依赖 + 消费仓安全）为主**，压过 B 的「解析代码更短」次要便利。推荐 A。已按 A 回写 design D3/proposal/spec/tasks；设计门若否推荐、改 B，须补依赖机制。

### [自动决策] D1-D6

均高置信、实测复现、有唯一正确修法，已回写 [spec-review-amendment]，默认采纳、设计门可覆盖。详见下「Findings + 裁决」。

## Findings + 裁决（合并去重后 12 条，全采纳）

| # | 收敛镜 | 严重度 | 发现（实测复现） | 裁决/回写 |
|---|---|---|---|---|
| H1 | broad+adv-A+adv-B+ov | 高 | 优先级 lint 无占位符豁免；现存 3 条 `优先级: <待填>` 假阳 | 采纳 → D5 扩两字段豁免 + spec scenario + Task3.1 用例 |
| H2 | adv-B+ov+接地 | 高 | config_lint「现有 yaml 处理」证伪；init.py 无 yaml、PyYAML 非 stdlib | 采纳 → Q1 拍板(推荐手写) + D3 改手写 stdlib |
| H3 | broad | 高 | block_ranges 第二处 AST 差异（消费循环签名），只归一 starts 不够 | 采纳 → D6/Task1.1 列两处 |
| H4 | broad+adv-A+接地 | 高 | 优先级 `P1 ★` 后缀非括注，「容忍括注」措辞会拒之 | 采纳 → D4 前导 token 后不校验 + spec scenario |
| M1 | adv-B+broad+ov | 中 | PRIORITIES 塞函数-AST 守护集 → getsource([...]) TypeError | 采纳 → R4 值相等 `==` 断言(独立路径) |
| M2 | adv-A+接地 | 中 | init.py 无 add_subparsers（扁平 mode），加子命令有破坏既有 mode 风险 | 采纳 → D3 加 mode 第4值+早分支(非重构) + CLI 冒烟测试 |
| M3 | domain+adv-A | 中 | metrics.enabled 无条件校验 → 无 metrics 块消费仓假阳（mlh-p2 教训） | 采纳 → D3 条件化 + spec 块缺失 scenario + fixture |
| M4 | 接地+adv-B | 中 | 失败表 `model-tiers.overrides` 措辞 vs 扁平结构；model-tiers 现注释态 | 采纳 → 失败表订正 + 注明越域分支靠构造样例测 |
| M5 | broad | 中 | 3.B「写了没人跑」触发可靠性 vs 3.A 自动跑，未区分 | 采纳 → Success Metrics 分层 |
| M6 | domain | 中 | Compliance 引 D4「绝不解析人写行」全句易混（batch lint 是只读语法窄化例外） | 采纳 → Compliance 拆两层 |
| M7 | adv-B | 低-中 | config_lint --root「git 根」探测不存在（init.py default="."） | 采纳 → D3 定义 --root=git rev-parse 降级 "." |
| L1 | broad | 低 | helper-删除 scenario 无 test、try/except 吞 AttributeError 无把关 | 采纳 → Task1.8 属性访问约束 + 注释锁 |

**低置信/已排除（不静默丢，可审计）**：
- 模块顶层副作用 → 接地+对抗A+ov 三镜实测排除（`if __name__` 保护，importlib 加载无副作用）。
- AST-after-docstring-strip 契约本身 → 三镜独立复现全 11 helper，与 D2/D6 吻合。
- 归一回归空头支票 → 对抗A 排除（todolist 71 测经 subprocess CLI 重度命中 split_sections/block_ranges）。
- em-dash 编码 → 接地实测 U+2014，与 D4 正则字面一致。
- `_split_batches_entries` 复用 → 接地确认返回 (preamble, entries)、entry_lines 原始行、须新写字段正则（design 未夸大，属实）。

## 度量锚（lens-metric，config metrics.enabled=true）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="3" sev="致0/高3/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="4" sev="致0/高3/中5/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="claude-fallback" site="design-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="0" sev="致0/高2/中1/低0" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="timeout" findings="3" truncated="false" -->

> 说明：codex outside-voice 超时（exit 124，gpt-5.5 high reasoning 未在 300s 内完成）→ 按协议回落 fresh 只读 Claude 子代理（runner=claude-fallback）。数值一致性（findings 与合并池实收）仍是主 session 信任边界、非机械可验。采纳/独立为设计门拍板前草稿值，拍板回写时最终化。

## 结论

**建议进设计 HARD-GATE**——12 findings 全采纳并已回写（design/proposal/spec/tasks 标 [spec-review-amendment]），openspec validate ✓。**唯一需拍板 = Q1**（config_lint 手写 stdlib vs PyYAML，推荐手写 A，已按 A 回写）。用户批准 → 进 writing-plans（SDD）。

## 拍板记录区

- **2026-07-07 设计门批准**：用户过报告拍板 → **Q1 = 手写 stdlib 行扫描（A，推荐项）**，与已回写 design D3 一致，无需再改设计。其余 D1-D6 自动决策默认采纳、无覆盖。批准进 writing-plans（SDD）。
- lens-metric 锚最终化：所有 finding 均采纳、无裁掉、无 defer——Step3 草稿值 == 门后终值（Q1 未翻改任何 finding 去向），上方度量锚即最终值。

<!-- ship-gate: design-approved -->
