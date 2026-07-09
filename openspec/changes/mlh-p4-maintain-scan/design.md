> **〔spec-review 状态·2026-07-09〕** 6 冷镜审出 3 HIGH（含致），机械面 12 条 amendment 已落（本文件 + spec + tasks 标 `[spec-review-amendment]`），**2 决策待设计门拍板**（见 `spec-review-report.md` 决策登记区）：**Q1** = 「少读→假一致」堵法（反转 grill D2 对 N 对账的否决，推荐链接路径 join + 表体行严格解析）；**Q2** = 删 MARK_IDX 全串守卫、改 token 子串（推荐直接采）。设计门过 Q1/Q2 + amendment 落定后，建议对 H1/H2 补一轮轻 grill 或接地复核再批实现。

## Context

`sdflow-maintain` 现为纯 Markdown 编排类 skill（零脚本）。其 SKILL.md 步骤 1-3 用 prose 指令让模型手做三类确定性 set-diff：① specs/rules ↔ INDEX 表格行、② CLAUDE.md 过时引用、③ workflow bundle 陈旧遮蔽兜底扫描（判据清单：`openspec/workflow/` 下残留 `workflow.md` / `spec-checklists/` / `code-checklists/` 任一 + 仓根 `hack/checkpoint-commit.sh` 孤儿副本）。步骤 4（按报告修复 INDEX）、步骤 5（提示 retro）是判断/编排。

本 change 属 MLH roadmap 阶段4·4.B（design §143 P6 行），把机械的三类 set-diff 下沉为脚本，判断/编排保留。约束：MLH 全局红线（fail-closed + 可观测 + 坏输入非零退出 + MUST NOT 引入静默面，见 roadmap §决策5）；adr/0006 硬约束「凡机械 prose 协议 MUST 脚本化」。

现存耦合信号：todolist T17 已记「陈旧遮蔽判据两处（脚本常量 vs SKILL prose 复述）无同步机制，改常量会漂」——本 change 把判据落进脚本常量、SKILL prose 改为「见脚本」，顺带收敛为单一源。

## Goals / Non-Goals

**Goals:**
- 三类 set-diff 由 `maintain_scan.py` 确定性产出只读报告；SKILL 步骤 1-3 改为调脚本。
- 坏输入全 fail-closed（非零退出 + 响亮 stderr），pytest 有负例断言。
- `sdflow-maintain` 升数据类（首个 `scripts/`+`tests/`），对齐仓内既有数据类 skill 形态。
- 陈旧遮蔽判据跨脚本一致性由守卫测试机验（闭 T17 隐忧，见 D4）。

> **目标态锚定（grill A1）**：本工具按**目标态消费仓结构**设计（specs/ + 可选 rules/ + INDEX），非按本仓（bundle 源仓）现状快照。`openspec/rules/` 是**可选**目标态目录（`sdflow-init/SKILL.md:105`「不在 bundle，按需自行加」）——maintain 处理之，**缺失=合法空集非 fatal**（见 D2/失败模式表）。本仓无 rules/ 是非典型特例，MUST NOT 据此砍 rules 半场（避免以现状否定目标，adr/0011 目标态论证）。

**Non-Goals:**
- 脚本不自动改 INDEX/任何文件（修复留模型步骤 4）。
- 不下沉「新 spec 归哪主题分组」内容判断。
- 不动 4.D 组 / ◐ 组。

## Decisions

### D1 只读报告，不自动修复（判断留人）
脚本零写文件，只出结构化差异报告；SKILL 步骤 4 由模型按报告判断是否改 INDEX、新 spec 归哪组。**理由**：「是否修复 / 归哪组」是内容判断（§1.3 判断权留人/模型红线）；set-diff 本身才是确定性机械活。**备选**：脚本直接改 INDEX——否决，越权且把内容判断塞回脚本。

### D2 INDEX 解析 fail-closed——重锚到「防假『一致』」〔grill-amendment〕
解析 `INDEX.md` 提取已列 spec/rule 名。**grill 揭穿原方向锚错**：原设计把 fail-closed 锚在「畸形不当空」上，但两方向失效危险度不对称——「读到 0 条 → 报全部 specs 新增未索引」是**响亮自纠**（人一眼见幻影差异去查），真正的静默风险是**「误读少读 → 漏报某条已删未清理 → 报『一致』」= 假绿同构**（该红报绿）。故 fail-closed 判据**重锚到「解析不可信 → 防假一致」**：
- 「读到 0 条 spec 条目」= **合法**（报全部为新增未索引，响亮不 fail）；
- 「INDEX 结构骨架缺失 / 预期分节表头整个不见 / 托管 marker 不配对（见 D7）/ 表格行畸形到解析器无法确信」= **fail-closed 非零退出**，绝不带半信半疑的解析结果输出「一致」。
**理由**：报告工具的反静默方向是堵「假一致」（misparse→false-consistent），不是机械纠结「空 vs 畸形」——区别于门的 all-or-nothing（呼应 §1.3 反静默 + adr/0013 记录维护 vs 正确性门）。**备选**：INDEX 放机器锚行声明「共 N 条」、解析数 vs 声明数对账——否决，过度设计，结构骨架校验已足够。

### D3 归组建议不下沉（定 Q1）
脚本只报「新增未索引」条目名 + 类型（spec/rule），**不**建议归入哪个 INDEX 主题分组。**理由**：归组是内容判断，留模型步骤 4。

### D4 陈旧遮蔽判据——canonical-in-init + 一致性守卫，非物理单一源〔grill-amendment〕
**grill 揭穿原「收敛单一源」不可达**：`init.py:169` 已有 canonical `RULE_MARKERS = ("workflow.md","spec-checklists","code-checklists")` + `stale_shadow_warnings()`，其 docstring 明写「update 内联为主 + **sdflow-maintain 兜底（同款判据）**」——设计意图本就让 maintain 做兜底消费者。maintain_scan 若自建常量 = 第 4 份副本（另有 `resolve-workflow.sh:46` bash 第 3 份），正是 T17 的漂移；跨 skill import init.py 破自包含且运行时脆（独立 symlink，init scripts 目录不在 maintain sys.path 上）；抽共享模块无基建。故：
- **canonical 留 `init.py:RULE_MARKERS`**；
- maintain_scan.py 保**自己一份副本**（自包含）+ **跨脚本一致性守卫 pytest**（照 determ-guards 终态集守卫范式）断言 `maintain_scan.RULE_MARKERS == init.RULE_MARKERS`，不等即 fail；
- **T17 真闭合 = 机验同步（守卫测试），非物理单一源**（跨 skill 做不到）；
- 第 3 份 bash 副本（`resolve-workflow.sh` 行 40-42/70-72 内联三处检查，非具名常量；design 原写「:46」实为告警 echo〔spec-review-amendment L2 订正〕）跨语言难同守 → **已知残差 defer**（不扩本 change scope，记 todolist）。
**备选**：R3 整个留 init.py、maintain 不做兜底——否决，init 的检查只在 init/update 动作时跑，maintain 周期性兜底能抓「有人手塞规则副本却没跑 update」的 gap，有独立价值。
**三镜主次判定〔spec-review-amendment L1/D12〕**：系统镜（真相源单一 vs 副本漂移）与开发循环镜（跨 skill import 运行时脆+破自包含 vs 双常量副本维护面）权衡——**开发循环镜主导**：跨 skill import 的运行时脆 + 破自包含成本 > 保副本 + 一致性守卫的维护面，故取守卫；用户镜无关（内部硬化）。

### D5 退出码语义（镜像 anchor_lint 口径）
`0` = 扫描完成（**含有差异**，差异是正常结果，不是错误）；`非0` = 坏输入/无法可靠完成（INDEX 缺失/畸形、目录缺失）。实现镜像 `anchor_lint.py`：typed error（如 `MaintainScanError`）→ `main(argv)` 捕获打 stderr → `sys.exit(非0)`；`sys.exit(main())`。**理由**：与仓内既有数据类脚本一致，降认知成本。**备选**：有差异也非零（类 lint 门禁）——否决，maintain 是「报告→人判修」不是门禁，有差异非零会误导编排。

### D6 maintain 数据类化骨架
新增 `sdflow-maintain/scripts/maintain_scan.py`（Python stdlib，无三方依赖）+ `sdflow-maintain/tests/test_maintain_scan.py`。skill 走 symlink，改源即时生效，`setup.sh` 逻辑不动（仅含 `SKILL.md` 目录才装的规则不变，本目录已有 SKILL.md）。

### D7 职责边界：maintain vs sdflow-init 的 INDEX 分治 + 机器锚行界定〔grill-amendment〕
INDEX 里「rules」撞两义：**义1** workflow bundle 规则（`openspec/workflow/*.md`）索引在 `<!-- opsx-init:rules:start..end -->` **托管块**、归 **sdflow-init**（`update` 刷新）；**义2** 消费仓通用规则（`openspec/rules/*.md`，可选）索引在托管块**之外**、归 **maintain**。maintain_scan 只 set-diff 义2：
- 解析 INDEX 时**用机器锚行界定**（盘面即状态/机器锚行范式）——**跳过 `opsx-init:rules:start..end` 整段**，只在托管块之外提取 spec/rule 条目；不跳则 workflow bundle 条目被误当「已列 rule」→ 满屏「已删未清理」误报 + 诱导改 init 托管块（越界）；
- 两个 marker 字符串 = `init.py:MARK_IDX` 常量——同 D4，maintain 保副本 + **一致性守卫 pytest**（第二处跨脚本常量守卫）；
- 托管 marker **不配对**（只 start 无 end / 反之）→ fail-closed（畸形托管块不静默当边界，接 D2）。

**双常量耦合诚实注**：maintain 依赖 init 两常量（`RULE_MARKERS`+`MARK_IDX`），是真耦合成本；但两处均一致性守卫兜底、且跨 skill import 更糟，取守卫。**备选**：目标态把 specs 索引与 init 托管块物理分家到两文件——否决，改动面波及 init 铺设契约，超本 change scope。

### 数据流（TG-11）

```
openspec/specs/*/spec.md ┐
openspec/rules/*.md      ┤
openspec/INDEX.md        ┼─► maintain_scan.py ─► 只读差异报告(4 类分节)
CLAUDE.md(根+子目录)     ┤    (纯读·fail-closed)      ├ 新增未索引
openspec/workflow/*      ┘                            ├ 已删未清理
                                                      ├ CLAUDE.md 过时引用
                                                      └ bundle 陈旧遮蔽
                                                             │
                                        SKILL 步骤4(模型判断是否修复 INDEX)◄┘
                                        SKILL 步骤5(提示跑 retro)
```

## Risks / Trade-offs

- **[INDEX 误解析致漏报「已删未清理」→ 假『一致』]**〔grill A4〕 → D2 fail-closed 重锚「解析不可信→防假一致」（真静默风险方向）；pytest 断言「结构骨架缺失/marker 不配对→非零」+「0 条→响亮报全新非 fail」。
- **[陈旧遮蔽/托管块 marker 判据跨脚本漂移]**〔grill A2/A3〕 → canonical 留 init.py，maintain 副本 + 两处一致性守卫 pytest 机验（闭 T17）；bash 第 3 份 defer。
- **[误把本仓现状（无 rules/）当目标限制]**〔grill A1〕 → 目标态锚定：rules/ 可选、缺失=合法空；不据现状砍半场。
- **[归组误判风险]** → D3 归组不下沉，留模型，脚本层无此风险面。
- **[maintain 数据类化 + 双常量耦合 init]** → 可接受：确定性+可测换维护面；双常量耦合由守卫兜底（D7），优于跨 skill import。

## 失败模式表（TG-08）〔grill-amendment〕

| 失败模式 | 触发条件 | 脚本行为 | 可观测 |
|---|---|---|---|
| INDEX 缺失 | 无 `openspec/INDEX.md` | 非零退出 | stderr 明示「INDEX 缺失」 |
| INDEX 结构不可信 | 分节骨架缺失 / 托管 marker 不配对 / 行畸形到无法确信 | **非零退出（防假『一致』）** | stderr 明示「INDEX 结构不可信，拒绝输出一致」 |
| INDEX 读到 0 条 spec 条目 | 合法空 INDEX（结构完好、无条目） | **退出 0**（报全部为新增未索引） | 响亮列出全部 specs 为「新增未索引」，人可自纠 |
| specs/ 目录缺失 | `openspec/specs/` 不存在 | 非零退出 | stderr 明示「specs/ 缺失」 |
| rules/ 目录缺失（可选） | `openspec/rules/` 不存在 | **退出 0（合法空集）** | rules 半场按「无规则可索引」处理，不 fail |
| CLAUDE.md / workflow/ / hack/ 缺失〔spec-review-amendment M5/D8〕 | 可选输入目录/文件不存在 | **退出 0（空集 benign）** | 无文件即无过时引用 / 无残留即干净 |
| CLAUDE.md 不可读 | 权限/编码异常 | 非零退出（fail-closed，不跳过） | stderr 明示文件 + 原因 |
| INDEX 表体行少读→漏报已删〔spec-review-amendment H2/Q1 待精化〕 | 坏链接/微畸形行被静默跳过 | **（Q1 拍板后）表体 `\|` 行解析不出条目→fail-closed** | 现无正向信号，Q1 拍板落实前为已知缺口 |
| 正常有差异 | set-diff 非空 | 退出 0 | 报告四类分节列出条目 |
| 正常无差异 | 全一致 | 退出 0 | 报告「一致，无差异」 |

## Migration Plan

- 新增脚本 + 测试，改 SKILL.md 步骤 1-3；无数据迁移、无破坏性变更。
- 回滚：删 `scripts/`/`tests/`、还原 SKILL.md 步骤 1-3 prose 即可（skill symlink，无安装态残留）。

## Open Questions

- 无阻塞性开放问题（Q1 归 D3、Q2 归 D4 均已定）。

## Compliance

- **MLH 全局红线**：遵守——fail-closed（失败模式表全非零退出）+ 可观测（stderr 明示）+ 坏输入 pytest 负例 + MUST NOT 引入静默面（D2 显式堵「畸形当空」静默面）。
- **§1.3 判断权留人/模型**：遵守——D1/D3 归组与是否修复不下沉。
- **adr/0006 机械 prose MUST 脚本化**：遵守——三类 set-diff 全脚本化。
- **仓库审查顺序**（本地 /review → PR → /code-review）：遵守，不颠倒。
- **bundle 边界**：本 change 不触 `sdflow-init/assets/`，无回灌链影响——遵守。
