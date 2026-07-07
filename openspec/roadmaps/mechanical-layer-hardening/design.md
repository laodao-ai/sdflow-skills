# workflow 机械层固化 整体设计

> 版本：v1（2026-07-07）
>
> 相关文档（全部位于 `openspec/roadmaps/mechanical-layer-hardening/`）：
> - 需求综述：`requirements.md`
> - 实施路线图：`roadmap.md`
> - 任务日志：`task-log.md`

## 1. 架构概览

### 1.1 根契约与两腿

```
┌─ adr/0006 硬约束（CONTEXT.md）：机械 prose 协议 MUST 脚本化/结构化 ─┐
│  动机 = 反静默元原则：弱档模型跑 prose 协议 → 典型失效 = 静默跳步     │
│  （「机械活交脚本、模型只做判断」的升格；脚本化在本 workflow 非可选）  │
└──────────────────┬────────────────────────┬──────────────────────┘
          ┌────────┴─────────┐     ┌────────┴──────────┐
          │ Leg 1 机械活脚本化 │     │ Leg 2 去字符串化    │
          │ 活下沉给脚本       │     │ 改机器状态的表示     │
          │ （多为新增.py+test │     │ （字符串嵌 md →     │
          │   低爆炸半径）     │     │   YAML frontmatter）│
          └──────────────────┘     └───────────────────┘
                   │                          │
     判据=枚举/集合/正则/set-diff       整块状态+正文歧义+有专门解析机
     → 脚本 own；判断切出留模型/人      → 迁结构、删解析机器；边缘锚只补 lint
```

**共享锚层**：两腿都触及「锚」这一层——Leg 1 的 anchor-lint 校验**度量层锚**（lens-metric/outside-voice/hr-tg/step1，产出侧存在性+enum），Leg 2 的 S1 迁移**gate 状态锚**（design-approved/verify/code-review）。二者目标锚集不同（度量层 vs 状态判据）、无文件冲突，但**方法同源**（都在收敛「叙述随模型写、机判形态不许错」），放一个 roadmap 一起推理胜过分家。

### 1.2 演进路径

```
现状：
  机械活散落 SKILL prose（模型手 grep/手数/手循环）+ 状态字符串嵌 md 正文（gate 靠解析机区分提及vs标记）

Leg 1 完成（脚本化优先，就绪高 ROI 低爆炸）：
  确定性步 → 脚本 own（sweep/anchor-lint/镜像一致性测试/config·batches lint/…）
  模型只留判断；每步失败 fail-closed

Leg 2 S1 完成（家族① gate 锚 → frontmatter）：
  gate 状态在 frontmatter 结构数据 → 删 _line_scoped_hits 整套解析机器
  正文提及锚串不再误判；57 篇归档 dual-read 窗口收敛

Leg 2 S2（家族② recorder 索引，north-star，ROI 触发才起）：
  recorder 索引层 YAML frontmatter + prose 块 → 腐蚀类蒸发 + 删 ~40处/文件表解析
```

## 2. 技术栈

| 层 | 选型 | 作用 |
|---|---|---|
| 脚本 | Python 3 + pytest（各 skill 自包含 `tests/`） | 确定性判据 own + 测试兜底 |
| 结构化状态 | YAML frontmatter（`yaml.safe_load`） | 机器状态载体（替字符串嵌正文） |
| 复用纯函数 | `ship_gate.anchor_set`/`_line_scoped_hits`、`lens_metric_aggregate.parse_anchor`/`_fence_aware_lines` | anchor-lint 直接复用，不重实现 |
| 契约单一源 | `lens-metric-contract.md`（enum/折叠）、`trigger-catalog.md`（HR-TG 子集）、`model-tiers.md`（档位） | lint/校验从单一源读取，不复制清单 |

## 3. 架构决策

### 决策 1：两腿同归一个 roadmap（不拆两个、不并入 cost-optimization）

**决策**：脚本化 + 去字符串化合为**一个** roadmap，同以 adr/0006 为根契约。

**替代方案**：
- **A. 两个独立 roadmap（去字符串化 / 脚本化各一）** → 割裂共享锚层推理（anchor-lint 与 anchor-frontmatter 是同一层的两种动作），两份真相源维护成本翻倍。
- **B. 并入 `workflow-cost-optimization`** → 主题错位：那条是成本（token/墙钟/轮次），这条是正确性/反静默（adr/0006 动机是可靠性非成本）。硬塞会稀释两个 roadmap 的立论。
- **C. 只做去字符串化（原始 scope）** → 漏掉更就绪、更高 ROI、更低爆炸半径的脚本化半（survey 实测 P1/P2 可立即执行，而去字符串化首阶段高仪式、S2 已 defer）。

**选择理由**：
- adr/0006 本就把「脚本化/结构化」并列为**同一条**硬约束——一个 roadmap 承载它的完整执行面，天然内聚。
- 两腿共享锚层，一起推理避免重复/冲突。
- 一个长期真相源，未来「还有哪没固化」一处可查。

### 决策 2：Leg 1（脚本化）先于 Leg 2（去字符串化）

**决策**：先做脚本化 P1-P4，再做去字符串化 S1；S2 north-star 不排期。

**替代方案**：
- **A. 先做去字符串化 S1（T65）** → 高仪式（触 ship_gate.py + 3 producer SKILL + 57 篇归档 dual-read）、且 T65 自我告诫「先评 ROI 再决定做不做」、还有 gate 铺设路径待核实——不适合当开路阶段。

**选择理由**（三维排序：就绪度 / ROI / 爆炸半径）：
- **P1 `issues.py sweep`**：SKILL 自认「纯机械 bash」，纯新增子命令 + 一个测试，零爆炸半径，收益最直接 → 开路。
- **P2 anchor-lint**：复用现成纯函数，把每轮 review 必跑的手 grep+肉眼核 enum 降为机验 → 高频门禁，高 ROI。
- **P3/P4 守卫补全**：镜像一致性测试 + config/batches lint，纯增测/增校验器，护消费仓。
- 去字符串化 S1 放到脚本化把「锚层机验」补齐之后做，迁移期更稳。

### 决策 3：去字符串化只搬「整块 + 歧义 + 有解析机」的家族①②，边缘度量锚只补 lint 不迁载体

**决策**：迁 frontmatter 的仅家族①（gate 状态锚）、家族②（recorder 索引，defer）。度量层锚（lens-metric/outside-voice/hr-tg/step1）**保留 HTML 注释 KV 载体**，只在 Leg 1 补产出侧 lint。

**替代方案**：
- **A. 度量锚也迁 frontmatter** → 它们已是注释内严格 KV + fence 护栏压住「示范锚 vs 真锚」歧义，且是**逐镜多行**（一份报告 N 行，位置无关行集），迁 frontmatter 净收益远低于家族①，还要动聚合器读侧。YAGNI。

**选择理由**：
- 家族① 是**整块状态**（每报告一个终态）、歧义**已致 P1 bug**（B4/B5）、有**可整套删**的专门解析机——三判据全中，最够格。
- 度量锚歧义**已被现有 fence 护栏缓解**，剩余风险低；补 lint（Leg 1）即够，不必伤筋动骨换载体。

### 决策 4：家族③（逐条 inline tag）、家族④（模版槽位）留 inline

**决策**：`[impl-review-fix]`/`〔TG-N〕`/`task<N>-` checkpoint/item ID/`<待填>` 一律不搬。

**选择理由**：
- 家族③ 语义 = **位置相关**（绑定所在句/所在行），或载体是 **git commit subject**（checkpoint tag → `TAG_RE`，非 markdown 正文），frontmatter 不适用。
- 〔TG-02〕声明的语义**就是**「在 proposal 头部声明区」，位置即语义（`tg02_hit` 头部区判定），移走即失去「声明 vs 提及」的位置区分。
- 家族④ 占位符必须在其结构位置上，本就是待人填的正文槽。

### 决策 5：每个脚本化候选显式切出判断部分保留给模型/人

**决策**：下沉脚本只 own 机械归约；判断部分（去重同一条 finding / 对抗裁决 / 需求代码有没有真实现 / 砍哪镜 / 新 spec 归哪组）显式保留。

**选择理由**：这是「机械活交脚本、模型只做判断」的对称面——脚本越权做判断 = 假绿风险（弱模型误分类）。survey 每个候选都已标注「保留给模型」的部分，落地 change 时照此切。

### 决策 6：S1 的两处失败面预置为设计约束（dual-read 窗口 + LLM 坏 YAML fail-closed）

**决策**：S1 迁移必须同时交付——① gate 对 57 篇归档 inline 锚的 **dual-read 兼容窗口**（`archived_verify_state` 读归档、B5 聚合测试扫归档语料都依赖旧锚）；② 报告 frontmatter 被 LLM 写坏时 `safe_load` 抛异常的 **fail-closed 兜底**（判为「无有效状态」→ gate 停下报告，绝不静默当已过门）。

**选择理由**：去字符串化 MUST NOT 引入比「缺 inline 锚」更糙的新静默面（R3）。frontmatter 的 parse 失败面比 inline grep 更集中，兜底策略是迁移的前提而非可选。

### 决策 7：recorder 镜像一致性用测试兜底，不抽公共模块

**决策**：~10 个 verbatim helper 的漂移用 `inspect.getsource` 相等断言（或等价源码级一致性测试）兜底，**不**跨 recorder 抽 import。

**替代方案**：
- **A. 抽公共模块共享 import** → 撞 D4 红线（三 recorder 刻意无共享 import，`issues.py` 以 subprocess 调另两个，「绝不解析人写行」的隔离设计）。

**选择理由**：D4 隔离是有意的架构约束；一致性测试在不破隔离的前提下兜住漂移（终态集测试 `test_issues.py:171` 已树范式）。

## 4. 候选全表（survey 实证，落地 change 的 backing）

> 三镜（机器状态字符串编码 / skill 可脚本化机械活 / 现有脚本边界缺口）盘点结果。每条附归属阶段（见 roadmap.md）。

### Leg 1 · 脚本化候选

| 编号 | 候选 | 现在模型/人做什么 | 下沉成 | 保留给模型/人 | ROI | 落点阶段 |
|---|---|---|---|---|---|---|
| P1 | `issues.py sweep --change X` | done §2.1 手跑 4 步 bash（scan两池→逐id triage→batch add→reindex） | 一个原子子命令 | 无（纯机械） | 高 | 阶段 1 |
| P2 | anchor-lint 产出侧校验器 | 出报告后手 grep 四类 v1 锚 + 肉眼核 enum/子格式 | `anchor_lint.py`（复用 `ship_gate.anchor_set`/`parse_anchor`；enum 从 contract 单一源读） | `findings=N` 与实收数的数值一致性 | 高 | 阶段 2 |
| P3 | 三 recorder 镜像 helper 一致性 | 靠 docstring「镜像 buglist」注释维系，无测试 | `inspect.getsource` 相等断言（不破 D4 隔离） | — | 高 | 阶段 3 |
| P4 | config.yaml + batches.md lint | 无 validator；`优先级`/`计划` 只挡 `\|`/换行不校验取值 | `config_lint`（yaml 可解析+必填键+tier 枚举）+ `batch lint`（优先级枚举、计划非占位） | — | 高 | 阶段 3 |
| P5 | embedded-test-sop 日志判定 | 手读长串口日志逐条按 `log-checks.yaml` 匹配 | `log_check.py` 解释器（时间窗+子串+severity rollup） | yaml 标「需人眼」的平台侧项 | 中 | 阶段 4 |
| P6 | maintain INDEX 对账 | 手扫 specs/rules ↔ INDEX 表格 set-diff + CLAUDE.md 过时引用 | `maintain_scan.py` 只读差异报告 | 新 spec 归哪组 + 是否修复 | 中 | 阶段 4 |
| P7 | lens-metric 计数折叠落锚 | 手折叠 canonical lens + 手数 + 手写锚（自认「信任边界」） | `lens_metric_emit.py`（吃结构化 findings→归约出锚） | 去重 + 对抗裁决 | 中 | 阶段 4 |
| P8 | outside-voice 复用守卫 / HR-TG 判定 / SOP 常量收割 / roadmap Review 处置对账 | 手判锚+时间戳+结构 / 手查 TG∩HR-TG / 手 grep 常量 / 目视扫处置状态 | 各一小脚本（reason_code 二分 / 集合查表 / 正则收割 / 状态枚举扫描） | 内容判断（哪些 TG 命中/evidence/处置内容） | 中-低 | 阶段 4 |
| — | `reindex --strict` 接 done sweep | 裸 reindex，problems 只回显 stderr | 让 sweep 走 --strict 成硬门 | — | — | 已 defer T66/T67（触行为面，另开） |

### Leg 2 · 去字符串化候选

| 编号 | 候选 | 载体现状 | 迁移后 | 就绪度 | 落点阶段 |
|---|---|---|---|---|---|
| S1 | 家族① gate 状态锚（design-approved/verify=PASS\|FAIL/code-review=pass\|blocked） | inline HTML 注释嵌报告正文；靠 `_line_scoped_hits` fence-aware 独占行区分提及vs标记 | YAML frontmatter；删整套解析机器；正文提及不再误判 | 就绪（B4/B5 实证）需先评 ROI + 核 gate 铺设路径 | 阶段 5 |
| S2 | 家族② recorder 索引行（ID/module/summary/priority/status/time/change/batch） | markdown 总览表 `strip("\|").split("\|")` 位置切列 | YAML frontmatter 索引 + prose 块；腐蚀蒸发 + 删 ~40处/文件表解析 | **north-star**（ADR 0010 defer，ROI 触发才起） | 阶段 6（不排期） |

## 5. 目录结构（本 roadmap 相关）

```
openspec/roadmaps/mechanical-layer-hardening/
  requirements.md  design.md  roadmap.md  task-log.md  memo.md
openspec/changes/plan-mechanical-layer-hardening/   ← 承载本次规划产出（归档后进 archive/）
未来实施变更（每阶段一个）：
  implement-mechanical-layer-hardening-p1-issues-sweep
  implement-mechanical-layer-hardening-p2-anchor-lint
  ... （见 roadmap.md 附录 C）
```

## 6. 风险、权衡与回滚

### 6.1 风险清单

| 风险 | 级别 | 缓解 |
|---|---|---|
| **S1 bundle 爆炸半径**：改 ship_gate/报告模版回灌所有消费仓 | 中（可能被高估） | 先核实：ship_gate.py 现只在 `sdflow-ship/scripts/`、走 skill symlink，**不在** bundle 路径 → 若确认非回灌，风险大降；行为面路径仍硬排除、绝不 fold/sweep |
| **S1 LLM 写坏 frontmatter YAML** | 中 | 决策 6：`safe_load` 异常 → fail-closed 判「无有效状态」，gate 停下报告 |
| **S1 57 篇归档 inline 锚不兼容** | 中 | 决策 6：dual-read 兼容窗口（gate 同时认 frontmatter + 旧 inline 锚，读归档路径不断） |
| **脚本越权做判断致假绿** | 中 | 决策 5：每候选显式切判断留模型；lint/校验只 own 机械归约 |
| **脚本化引入新静默面**（异常吞+exit0） | 高 | R3 红线：所有新脚本 fail-closed + 可观测，pytest 覆盖坏输入断言非零退出 |
| **清理惯性反应式开工**（T65 自我告诫） | 中 | S1 前置一道 ROI 评估门（inline 锚这套是否会反复出同类 bug）；S2 干脆 north-star 不排期 |

### 6.2 关键权衡（明确接受的代价）

- **家族① 迁 frontmatter 期间 gate 要 dual-read**：接受「兼容窗口内 gate 逻辑更复杂（认两种锚）」，换「窗口后可删整套 line-scoped 解析机器」。窗口关闭条件写进 S1 的 change。
- **recorder 镜像用测试兜底而非重构**：接受「~10 helper 仍是 verbatim 复制、改动要手动同步三处」，换「不破 D4 隔离红线」。测试兜住漂移即可。
- **度量锚不迁载体**：接受「lens-metric 等仍是字符串 KV」，换「不动聚合器读侧 + 省一次大迁移」——因歧义已被 fence 护栏压住。

### 6.3 回滚

| 故障场景 | 回滚动作 |
|---|---|
| 某脚本化 change 引入回归 | 该 change 独立可回滚（各阶段一个 change，归档前 verify+code-review 门）；恢复 SKILL 手做步 |
| S1 frontmatter 迁移致 gate 误判 | dual-read 窗口内旧 inline 锚仍有效 → 回退 producer SKILL 到写 inline 锚即可，gate 兼容 |

### 6.4 作废处置

- S1 完成后，`ship_gate.py` 的 `_line_scoped_hits` 及相关 fence-aware/互斥/fail-safe 机器 → 在 dual-read 窗口关闭后删除（该删除本身是 S1 change 的收尾任务，非本规划动）。

## 7. 规范层契约（与 OpenSpec specs 的映射）

本规划变更（`plan-mechanical-layer-hardening`）**只产出 roadmap 文档包，不定义 capability spec**。各阶段的规范增量由未来实施变更产出：多数落 `spec-workflow`（ship-gate 锚契约 MODIFIED、review 自检 MODIFIED），recorder 相关落各 recorder skill 自包含约定。映射见 roadmap.md 附录 C。

## 8. 已决议档案（Q&A）

### Q1 ✅ roadmap 边界：新建 + 就绪度分级

**原问题**：去字符串化两阶段里 T65 就绪、Path B 已被 ADR defer，该新建 roadmap 还是折进已有 / 只写 T65？

**决策**：新建 roadmap，就绪度分级（S1 就绪、S2 north-star）。

**理由**：主线成立值得独立长期真相源；诚实标注 S2 触发式非排期，避免空洞。

### Q2 ✅ scope：拓宽成双腿（脚本化 + 去字符串化）

**原问题**：survey 挖出脚本化半（C1-C9 + 脚本 gap），比去字符串化更就绪、ROI 更高、爆炸半径更低。roadmap 守窄还是拓宽？

**决策**：拓宽成双腿 roadmap（本文件即此），改名「机械层固化」，Leg 1 脚本化优先、Leg 2 去字符串化作一腿。

**理由**：adr/0006 本把两者并列为同一硬约束；两腿共享锚层一起推理；首批可执行阶段落在就绪的脚本化项，roadmap 不空。

## 9. 未决 / 可延后事项

- **S1 是否真开工**：前置 ROI 评估门（inline 锚这套是否会反复出同类 bug）——B4/B5 是两个数据点，是否够立项待评。**未决，S1 change 起手先评**。
- **ship_gate.py 真实铺设路径**：核实是否 bundle 回灌消费仓（影响 S1 爆炸半径判定）。**S1 起手第一步核**。
- **S2（Path B）触发器**：「recorder 持续出腐蚀 bug / 想在数据上建工具」何时满足——**不排期，被动触发**。
- **Leg 1 阶段 4（P5-P8 中 ROI 项）粒度**：可能进一步拆分或按需只做子集——**留到阶段 4 起手时按当时痛点排**。
