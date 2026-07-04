# spec-review 报告 — ship-gate-hardening-2

## 命中范围

- **栈**：Python + bash 工具链（gate 脚本）。backend-go / embedded / frontend 领域清单均不适配 → 无领域镜专属清单，接地镜承担核心。
- **TG**：TG-01/12/19/22/23/25（判定见 proposal 头）。**HR-TG ∩ 命中 = ∅**（TG-25/23/19/22/12 均不在 HR-TG 子集 {04,06,07,08,09,16,17,26}）→ 不单开领域 cross-model，仅 always-on outside-voice。
- **评审层**：Step1 广审（simulated，子代理模拟 autoplan 四视角）+ codex outside-voice（design-voice，真跑）+ Step2 三镜（接地 / 对抗 A / 对抗 B）。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-25/23/19/22/12 均不属 HR-TG 子集{04,06,07,08,09,16,17,26}；改的是 gate 完成判据、非运行期爆炸/数据损坏/安全泄漏类" -->

合并池实收 findings = 12（codex 4 + 广审 2 + 接地 2 + 对抗A 2 + 对抗B 4，去重后见下）。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  dogfood producer 格式时序缺口（对抗B-4,HIGH）             │
│ [需拍板] Q2  spec delta 结构 MODIFIED vs ADDED（接地+对抗B-3,MAJOR）   │
│ [自动决策·已amend] D1  scope-check 漏权威源 workflow.md（3声,BLOCKER） │
│ [自动决策·已amend] D2  T34 重号 Task 段→UNKNOWN（2声,中高）            │
│ [自动决策·已amend] D3  startswith:263 前缀同步放宽+真git测试（中）     │
│ [自动决策·已amend] D4  复选框行锚定+忽略代码块（中）                   │
│ [自动决策·已amend] D5  T32 判别性负例反 vacuous test（中）             │
│ [自动决策·已amend] D6  "三重巧合"→两条件校正（中）                     │
│ [defer→todolist]  broad-F2  producer 指令无单一真相源（minor）         │
└──────────────────────────────────────────────────────────────────────┘
```

### 需拍板

**Q1 —— dogfood producer 格式时序缺口〔对抗B-4，HIGH，高置信〕**

现象：`RUN_PLAN`（生成 superpowers-plan.md）在阶段三链路里排在 task 1.4（改 SKILL/workflow 派发 args）**之前**——本 change 的 plan 必然在 1.4 落地前生成，writing-plans 读到的是**旧裸格式**派发 args。tasks.md 表头"每 task commit MUST 用命名空间格式"是文档句、**无自动传导机制**进 writing-plans，唯一生效路径是**未被记录的人工介入**。故"本 change 自动 dogfood 新格式"不自动成立；无人工介入则本 change 自己的 checkpoint 落裸格式（安全、走 A1 兼容，但 dogfood 自证目标落空 + 与表头 MUST 冲突）。**注**：这修正了 grill Q2 的前提——Q2 重排解析器先行修好了 **consumer/parser** 的自举，但 **producer 格式** 的自举另有此时序洞。

| 选项 | 后果 |
|------|------|
| **A（推荐）self=裸格式** | 本 change 只 dogfood **parser/consumer**（用裸自 checkpoint，走 A1 计入）；**producer 格式由新增真-git 测试验证**、对**下一个 change** 首次端到端生效。删 tasks.md 表头"MUST 命名格式"自证句，收尾报告改"parser 落地+producer 测试验证，next change 首消费"。零人工介入、无冲突。 |
| B 人工预override | RUN_PLAN 前显式人工/SDD 编排者覆盖派发 args 为新格式，把隐性依赖变显式任务项。能 dogfood producer，但引入一个 gate 想消灭的"人工介入"环节。 |

推荐 **A**：producer 正确性靠测试（比活体跑一次更强的保证），self 用裸格式无自证损失且零人工介入；grill Q2 的"解析器先行"仍成立（管 parser 自举），本 Q 只修正 producer 自举的过度承诺。

**Q2 —— spec delta 结构 MODIFIED vs ADDED〔接地 + 对抗B-3，MAJOR，中高置信〕**

现象：本 delta 用 `## ADDED Requirements` 新建两独立顶层需求；但 v1（ship-gate-hardening）先例用 `## MODIFIED Requirements` 把 B1-B4 作为**同一** "阶段三编排台账确定性" 需求的追加 Scenario。后果：① 既有需求 `前置产物缺失点名` Scenario（主 spec:271）仍写"plan 复选框全勾为辅"（全局语义），与新 ADDED「分段绑定」需求（禁全局）**书面直接矛盾**；② 完成判据被拆散在 3 个需求块、主需求正文无交叉引用，读者跨 3 处才拼全貌；③ 背离本项目自建先例。（archive CLI **不报错**——对抗B 已证伪"CLI 崩溃"疑虑。）

| 选项 | 后果 |
|------|------|
| **A（推荐）改用 MODIFIED** | 跟随 v1 先例，MODIFY「阶段三编排台账确定性」需求：追加 T32/T34 Scenario + 同步改 `前置产物缺失点名` 的"全勾为辅"措辞（消矛盾）+ 主需求正文提命名空间。代价：delta 须复现该需求全量正文（16 Scenario）——转写量大但结构正确、消矛盾。 |
| B 保留 ADDED + 交叉引用 | 轻（不复现 16 Scenario），但需在既有 `前置产物缺失点名` Scenario 补一句"复选框语义详见新需求"消矛盾——仍是两处管一机制，治理分裂未根治。 |

推荐 **A**：矛盾必须消（否则归档后主 spec 自相矛盾，误导 verify）；跟随先例、结构最干净。转写量大是一次性成本，可在实现期由 archive 步的中档子代理按代码实况同步（sdflow-done 既有能力）。

### 已 amend（自动决策，改动标 [spec-review-amendment]，可在设计门覆盖）

- **D1〔BLOCKER·3声共识：codex#1+接地+广审F1〕** scope-check 表漏 **bundle 唯一权威源 `workflow.md:74`** + `test_workflow_authority.py:16`（钉死旧 token）+ `ship_gate.py:32` 头注释。**漏改后果**：本仓真实 dogfood 主路径经 workflow.md，不同步改则该路径产的 task tag 恒裸格式 → **T32 对主用路径形同虚设**。→ design scope-check 表补至 **9 点**、tasks 1.4 扩为同批改 3 处 + archive 触发 `sdflow-init update`、proposal Impact 补权威源。
- **D2〔中高·2声：codex#3+对抗B-1c〕** 重号 `### Task N:` 段（plan 手改事故）：`set` 折叠会掩盖"一段全勾一段未勾"假✅ → design ADR-3 + spec + tasks 加"重号→UNKNOWN"，锚 `test_duplicate_task_number_unknown`。
- **D3〔中·对抗A-F1〕** `ship_gate.py:263` `startswith("checkpoint(task")` **必须**随 `TAG_RE` 放宽为 `startswith("checkpoint(")`，否则命名标签被整条 `continue` 跳过→T32 静默失效+吞自己完成号 → 升为 scope-check 独立行 + tasks 要求**真实 git commit fixture**（非字符串 mock）。
- **D4〔中·codex#4〕** 复选框识别 `checkboxes_all` 现为全文子串，会把代码块/散文 `- [x]` 误当完成 → ADR-3 + spec + tasks 改**行锚定 `^\s*-\s+\[[ xX]\]` + 忽略 fenced code block**，锚 `test_fenced_checkbox_not_counted`。
- **D5〔中·codex#2〕** T32 核心 Scenario 原用"同号 task1"无区分力（plan={1} 时计不计 B 都判齐=vacuous）→ 改**判别性负例**：plan={1,2}、A 有 task1、B 有 **task2**（=A 缺的号）→ 期望 done={1} CONTINUE_IMPL（错计 B 则假齐）。spec Scenario + tasks 1.1 同步。
- **D6〔中·对抗A-F2〕** "三重巧合"高估残留难度——任务号顺序编号使"撞号"近乎必然、非独立项 → design/proposal 校正为**两条件（stacking + 裸污染方）**；且若 D1 未修则主路径恒裸、"裸其一"由 A 自满足（G1 修复是残留可枯竭前提）。

---

## 各镜 findings（合并去重后，带裁决）

| # | 来源 | finding | 置信/严重 | 裁决 |
|---|------|---------|----------|------|
| G1 | codex#1·接地·广审F1（3声） | scope-check 漏权威源 workflow.md + test_workflow_authority + ship_gate.py:32 | 高/blocker | **采信→D1 amend** |
| B-4 | 对抗B | dogfood producer 格式时序缺口（RUN_PLAN 早于 1.4） | 高/high | **采信→Q1 需拍板** |
| G2/B-3 | 接地·对抗B（2声） | spec ADDED 违 v1 MODIFIED 先例 + 与既有 Scenario 书面矛盾 | 中高/major | **采信→Q2 需拍板** |
| T34-dup | codex#3·对抗B-1c（2声） | 重号 Task 段 set 折叠→假✅ | 中高/中高 | **采信→D2 amend** |
| A-F1 | 对抗A | startswith:263 未放宽→T32 静默失效 | 高/中 | **采信→D3 amend** |
| cx#4 | codex#4 | 复选框全文子串含代码块伪框 | 中/中 | **采信→D4 amend** |
| cx#2 | codex#2 | T32 Scenario vacuous test | 中/中 | **采信→D5 amend** |
| A-F2 | 对抗A | "三重巧合"高估残留 | 中/中 | **采信→D6 amend** |
| F2 | 广审 | producer 指令无单一真相源 | 中/minor | **defer→todolist** |

## 已裁掉区（反静默压制·可审计，不静默丢）

对抗镜主动证伪、经主 session 复核**确为不成立/已覆盖**，留痕：

- **X1 正则命名组歧义/误匹配**（对抗A refuted）：命名/裸分野严格依赖字面 `:`，贪婪组遇首个 `:` 停；`checkpoint(task2:task1-fix)` 精确解出 `ns=task2,N=1`，无错位。**裁定成立（refuted 正确）**——正则稳健。
- **X2 闭区间窗口×命名空间交互**（对抗A refuted）：`self_subject` 走与窗口内 commit 完全相同代码路径，无独立新增暴露面（A-F1 的风险对它同等适用、非新增）。**裁定成立**。
- **X3 T34 嵌套/前言段/Task10前缀/并集语义**（对抗B 1a/1b/1d/1e refuted）：子串检测与缩进无关、前言段 tasks.md:20 已覆盖、`\d+` 贪婪无前缀歧义、checkpoint∪checkbox 是既有主锚优先语义（用户忘勾框不该判未完成）。**裁定成立**。
- **X4 plan 首提交解析器中间态**（对抗B-2c refuted）：gate 读磁盘 symlink 即时生效、非 git 提交态，文件保存即新 regex 生效——比 design 自述更宽松。**裁定成立**。
- **X5 archive CLI 因 ADDED 崩溃**（对抗B 主动证伪自己 prompt 的疑虑）：ADDED 两标题不与既有重名，CLI 顺利追加不报错。**裁定成立**——G2/B-3 是治理/矛盾问题、非 CLI 崩溃。

> 无低置信项被静默滤除；所有 refuted 均记于此可审计。

---

## 结论

本轮 spec-review **抓出 grill 漏掉的 3 枚硬伤**（grill 死磕了 ADR 逻辑/可达性/parser 自举，漏了契约权威面 G1、producer 时序 B-4、spec 结构 G2）+ 5 枚中等 + 1 defer。**无一枚是"假✅ 穿门"**（对抗镜明确：所有爆点属假阴/churn/治理问题，未破假阳红线），故设计骨架稳。D1-D6 已就地 amend；**Q1（producer 时序）/ Q2（spec 结构）需你在设计门拍板**。

☑ 已过设计 HARD-GATE（拍 Q1/Q2 → 回写 `design-approved` 锚 → writing-plans）

---

## 设计门拍板记录（2026-07-04）

- **Q1 = A**（self 用裸格式）：本 change 只 dogfood parser/consumer，自 checkpoint 用裸格式（A1 兼容）；producer 命名空间格式靠真-git 测试验证、下个 change 首次端到端消费。→ tasks 表头 + design Migration 已改 [spec-review-amendment]。
- **Q2 = A**（改用 MODIFIED）：spec delta 转 `## MODIFIED Requirements`，逐字复现「阶段三编排台账确定性」需求（16 Scenario 保真）+ 追加 6 条 T32/T34 Scenario + 消解「前置产物缺失点名」的"全勾为辅"矛盾 + 主需求正文提命名空间/分段。→ specs delta 已重构，validate 通过（22 Scenario）。
- D1-D6 自动决策 amendment 全部保留；broad-F2 defer→todolist（producer 指令单一源）。

<!-- ship-gate: design-approved -->
