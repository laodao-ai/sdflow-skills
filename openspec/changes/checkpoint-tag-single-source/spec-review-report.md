# spec-review 报告 — checkpoint-tag-single-source

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG-18(测试计划)/TG-23(≥2方案)，∩ HR-TG 子集{04,06,07,08,09,16,17,26}=∅" -->

## 命中范围

- **TG**：TG-18（有测试计划）、TG-23（≥2 方案，已记 design D1）；TG-25 弱沾边（多文件契约漂移）不作栈判据。
- **栈/领域**：无栈领域命中（skills 仓自身 docs+test 元改动）→ 未开领域镜。
- **镜阵**：Step1 广审（主 session native + codex outside-voice）+ 2 对抗镜 + 1 接地镜。**HR-TG=none**（不开领域 cross-model）。
- **合并池实收**：广审 3（BR-1~3）+ outside-voice 4（OV-1~4）+ 接地 5（含 3 相符/2 缺陷）+ 对抗A 5（A-1~5）+ 对抗B 5（F1~5）→ 去重后 **4 高 / 6 中 / 2 低**。

## 总裁决：⛔ 设计被实质证伪，不建议按原样进 HARD-GATE

四路独立声音（接地镜 / codex outside-voice / 对抗镜 A / 对抗镜 B）**汇聚**：本 change 的核心主张「加一条 contract 测试把**文档↔解析器双向钉死、任一站漂移即红**」**当前不成立**——parser 侧多种真漂移与 doc 侧裸兼容删除均可静默保绿（对抗镜 A 实证），且 D3 SKILL.md 瘦身自打脸（对抗镜 B）。此非措辞瑕疵，是**方法本身的洞**。spec-review 在此兑现价值：explore 里看似「无 grill 悬念的便宜清理」，冷审下露出四类高危缺陷。

---

## Findings（对抗裁决后，按严重度）

### 高

- **H1 既有测试冲突 + 验收条件不可满足**〔4 声共识：广审BR-1 / 接地F4 / OV-3 / 对抗B-F1〕
  `sdflow-ship/tests/test_workflow_authority.py:23-27` 的 `test_skill_producer_arg_namespaced` 断言 `"<change>:task<N>-<slug>" in SKILL.md`。tasks 2.1 要删该字面 → 该断言必红；tasks 1.3 新增**相反**断言（SKILL.md MUST NOT 含字面）→ 同 suite 两断言互斥；tasks 3.1 声称「确认瘦身**未破**既有断言」**不可满足**，且**无任何 task** 说删/改 `test_skill_producer_arg_namespaced`。裁决：**采信（高）**，四声独立命中、纯代码事实。

- **H2 漏掉第四耦合站 `checkpoint-commit.sh`（真正的 producer）**〔OV-2，接地坐实〕
  `sdflow-init/assets/hack/checkpoint-commit.sh:46/48` 把 `$1` 包成 `checkpoint($step): …`——`checkpoint(` 外壳正是 `TAG_RE` 要解析的一部分。契约真正该焊的是 **producer→parser**（脚本真产的 subject 能否被 gate 认），本 change 只测 doc→parser、放过了唯一真铸造 subject 的站点。裁决：**采信（高）**，这是比 doc↔doc 更本质的链路。

- **H3 parser→doc 方向零锚，「双向」是空文**〔对抗镜 A-2，**实证**〕
  单 happy 实例 `checkpoint(demo:task1-slug)`→断言捕获 `("demo","1")`。实测三种 `TAG_RE` 放松（尾 dash 可选 / 命名空间允许大写 / 编号可空）**全部保绿**——真漂移不红。裁决：**采信（高）**，实证不可辩，需负例矩阵才成立。

- **H4 D3 瘦身自打脸 + 退化路径正是本 change 要防的假✅**〔对抗镜 B-F2 / OV-4〕
  SKILL.md:29 是实际 RUN_PLAN 派发指令，字面**当下就在上下文、自足**；瘦身成「按 workflow.md 引用」后，主 session 派发要么额外读 workflow.md（= design D1 明文否决 include 的**同一个**间接读依赖，自相矛盾），要么派发 args 只剩模糊话→plan commit 步不带确切字面→**gate 主锚 miss→假✅**（本 change 存在的理由）。裁决：**采信（高）**，D3 逻辑自毁。

### 中

- **M1 spec 两条 MUST 互斥**〔对抗镜 A-1〕：spec.md:10「MUST NOT 硬编码期望串」与「doc 改字面即红」不可兼得——机械抓 doc 漂移必须持已知良好串比对（= 被禁的硬编码）。裁决：采信（中）。
- **M2 裸兼容 doc 断言不可证伪**〔对抗镜 A-3，实证〕：`task<N>-` 是 `<change>:task<N>-<slug>` 子串，`assert "task<N>-" in doc` 永真，删裸兼容声明照绿。裁决：采信（中）。
- **M3 delta spec.md 自复制格式字面**〔OV-1〕：spec.md:5 抄了 `checkpoint(<change>:task<N>-<slug>)`，归档后成第四漂移源——本 change 反讽。裁决：采信（中）。
- **M4「step6 tag 契约」是虚构引用锚**〔对抗镜 B-F3〕：workflow.md 无此命名锚（格式在表格行 line 74），引用悬空且无测试守卫。裁决：采信（中）。
- **M5 字面↔语义不可干净分离**〔对抗镜 B-F4〕：字面是句子语法宾语，「裸 `task<N>-` 向后兼容」本身内嵌 token；机械删留残句，关键词检查测不出语义丢失/语病。裁决：采信（中）。
- **M6 脆性中间点缺失**〔对抗镜 A-4〕：workflow.md 已混用 `<change>` 与 `{change}` 记法，统一记法会误红；spec 无 token 契约表定「哪些 token 承重 + 归一化规则」。裁决：采信（中）。

### 低（一行带过，可审计不静默丢）

- **L1**〔接地 F5〕`from ship_gate import TAG_RE` 需自注 sys.path（现测试全走 subprocess/read_text，`scripts/` 不在 path）。实现细节，采信（低）。
- **L2**〔对抗镜 A-5〕「双向钉死」宣称 > 实交付（真机械覆盖仅「作者手写常量↔TAG_RE 捕获结构」单点）。诚实性问题，采信（低）。

## 已裁掉（反静默压制）

- 无。全部 findings 经对抗裁决存活（多带接地/实证背书）；接地镜 Finding1-3（TAG_RE/workflow.md/SKILL.md 文案相符）为**正向核验通过**，非缺陷、不入池。

---

## 决策登记区

```
spec-review-report.md · 决策登记区
┌──────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  设计已实质证伪 → 走哪条路？（三选一，见下，推 B）        │
│ [自动决策] D-a  HR-TG=none，不开领域 cross-model（判据已记锚行）      │
│ [自动决策] D-b  无栈领域命中，不开领域镜（skills 仓元改动）           │
└──────────────────────────────────────────────────────────────────┘
```

### 〔需拍板〕Q1 — 设计证伪后的路径（人类设计门决）

| 选项 | 内容 | 后果 |
|---|---|---|
| **A 推翻重设计（全量修）** | 补负例矩阵(H3)+token 契约表(M6)+解 MUST 互斥(M1)+加 producer 集成测试(H2)+撤 D3 瘦身(H4)+改既有测试(H1)+delta spec 去自复制(M3) | change 从「便宜清理」膨胀成中等设计工作；但把三/四站真钉死 |
| **B 缩到可靠内核（推荐）** ⭐ | **只保留经得起冷审的两件**：① **producer→parser 集成测试**（临时 repo 跑 `checkpoint-commit.sh demo:task1-slug`→读 commit subject→断言 `TAG_RE` 捕获 `("demo","1")` + 负例集）——这才是 H2 指出的**真防漂移网**，一次覆盖 producer/parser 两站；② **`TAG_RE` 负例矩阵**（H3：`checkpoint(task1slug)`/`checkpoint(DEMO:task1-)` 等 MUST NOT match）。**撤销** D3 SKILL.md 瘦身（H4 自毁）、**撤销**「测试读文档正则抽格式」的循环法（A-1/M1）、delta spec 不自复制字面（M3）。既有 `test_workflow_authority.py` 子串断言保留作 doc 侧弱守卫、不动（避 H1 冲突） | scope 收回到真正 sound 的核；放弃 markdown 层 DRY 幻觉；交付一个**实测有效**的防漂移测试 |
| **C WONTDO / 放弃** | 结论：边际 DRY 价值 < 成本，保持现状（既有子串断言 + spec-review G1 兜 doc↔doc） | 不留新代码；把 T36 标 WONTDO 记理由。但会放掉 H2 揭示的 producer↔parser 真缺口（那条其实独立有价值） |

**主审推荐 B**：冷审证明「便宜清理」的原设计不 sound，但 codex 挖出的 **producer→parser 集成测试（H2）是真有价值且独立成立**的内核——它比原方案（doc 正则抽取）更简单、更 sound、覆盖更本质的站点。B 把 scope 收回到这一件真正值得做的事 + 一个负例矩阵，砍掉所有被证伪的部分（瘦身/循环测试/spec 自复制）。若你认为连这个内核都不值，退 C。

---

## 收敛口

⛔ **不建议**按原 design/specs/tasks 进设计 HARD-GATE。请就 **Q1** 拍板：**B（缩到可靠内核，推荐）** / A（全量重设计）/ C（WONTDO）。拍板后：
- 选 **B/A** → 我据裁决重写 design/specs/tasks（标 `[spec-review-amendment]`），再回设计门过修订版；
- 选 **C** → 归档本 change 为 WONTDO + 把 producer↔parser 缺口（H2）单记一条 todolist（它独立有价值）。

> 设计门拍板发生后才写 `<!-- ship-gate: design-approved -->`（当前**故意不写**——设计未获批）。

---

## 拍板记录

- **Q1 → 选 B（缩到可靠内核）**〔用户设计门拍板〕。据此重写 design/specs/tasks（标 `[spec-review-amendment]`）：B 收敛为**纯测试新增、零 doc/skill 改动**——① producer→parser 集成测试（H2）② `TAG_RE` 负例矩阵（H3）；撤 D3 瘦身（H4）、撤循环 doc-抽取（A-1/M1）、delta spec 不自复制字面（M3）；既有 `test_workflow_authority.py` 子串断言保留不动（避 H1、作 doc 侧弱守卫）。修订版须回设计门再过一次。

---

# 复审门 Round 2 — Q1=B 修订版设计审（sdflow-spec-review 编排）

> 本轮 = 上一行"修订版须回设计门再过一次"承诺的复审。触发背景：`/sdflow-ship` 因 gate `anchors_in` 子串误配（第 85 行对锚的**描述性提及**被当真锚，已记 **B4/VERIFIED**）假判"设计已过门"而越门起跑，实现三任务已落地全绿；现补这道设计门复审。**本轮是事后审计而非实现前把关**——拍板须追认覆盖已落地的 task1-3。
>
> 编排：Step1 主 session 原生广审 + codex outside-voice（超时→claude-fallback）；Step2 fan-out 对抗镜×2 + 接地镜×1（fresh context）；Step3 主 session 综合对抗裁决。实现已全绿（sdflow-ship 85/85、仓级 348/348）作接地。

## 镜头与锚（自检）

- Step1 广审锚：见 `gstack-review.md` 首行 `<!-- sdflow:step1-broad-review v1 mode="native" -->`（Round 2 重写）。
- outside-voice：codex exec **exit 124 超时** → claude-fallback 只读回落（同源同 prompt）。锚：

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="timeout" findings="4" truncated="false" -->

- HR-TG 判定：命中 TG-01（工具链）；HR-TG 子集 ∩ 命中集 = **∅**（纯测试新增、零运行时行为/数据路径/安全面，无"运行期爆炸/数据损坏/安全泄漏"）。锚：

<!-- sdflow:hr-tg v1 hit="none" evidence="纯测试新增,零运行时行为/数据/安全面,不满足HR-TG入选判据" -->

- 领域镜：`domains/`（backend-go/backend/embedded*/frontend）**无一命中**（Python 测试 + skills 元变更）→ 不开领域镜（如实记录，非静默跳）。

## 综合结论

**核心内核 sound、已接地验证**：接地镜 16/16 代码事实全符合；三路独立对抗（对抗镜×2 + OV-fallback）经 mutation 模拟共识——4 条负例各为真哨兵（非空断言）、集成测试双层独立断言无假绿、D3「零 doc/skill/ship_gate.py 改动」跨三 commit diff 核实成立、sys.path 注入安全。**无 CRITICAL 技术缺陷**。残差为 1 个中等覆盖缺口 + 2 个中等诚实性/披露项 + 若干低 prose 项。

## 决策登记区

```
┌───────────────────────────────────────────────────────────────────┐
│ [需拍板] Q2  设计门追认 + 是否要求 DF1-DF3 修订后再写锚（见收敛口）    │
│ [需拍板] Q3  DF1 负例覆盖缺口：是否补一条 taskab- 负例 + 修注释        │
│ [自动决策] D-A  核心内核 sound,默认采纳(接地16/16+三路对抗共识)         │
│ [已裁掉] X1  对抗镜#2 对 DF1 的"仅术语瑕疵"判定(裁：低估,见 DF1)        │
└───────────────────────────────────────────────────────────────────┘
```

## Findings（带置信/严重度；低置信一行带过、不静默丢）

### 接地镜（机械读码，弱档）
- **G〔通过·高〕** 7 大事实 16 细项全符合：`ship_gate.py:231` TAG_RE 字面/捕获组、`:526` `__main__` 守卫、import 无副作用；`checkpoint-commit.sh:46` 包裹 `checkpoint($step): $desc` + 无变更静默跳；`conftest.py:8` repo fixture；`test_workflow_authority.py` 既有断言存在；4 条负例当前 TAG_RE 实跑均 None；实现文件断言与 design 一致。

### DF1〔中 · CONFIRMED〕负例矩阵一处真实覆盖缺口 + 第 3 条注释名不副实
- 来源：对抗镜#1 F1（mutation 模拟严谨）；对抗镜#2/OV 判"仅术语瑕疵"→**主 session 裁决：低估，采信对抗镜#1**（见 X1）。
- 实质：`task(\d+)-` 若被放松成 `task([a-z0-9]+)-`（号位允许**字母**，如 `checkpoint(taskab-slug)`），现有 2 正例 + 4 负例**无一翻红** → 该放松类无守卫。第 3 条 `checkpoint(task-1-)` 注释写"号位允许非数字"，但它实际挡的是"带 dash/空号"变体（`task([\w-]+)-`/`task(\d*)-`），**不挡纯字母加宽**——注释与实际防御类不符。
- 严重度：中（触及本 change 核心卖点"负例封住放松即保绿"的一个可复现盲区；design D2 已声明"负例集非穷举"作部分兜底）。
- 建议：补一条 `checkpoint(taskab-slug)`（号位字母）负例；把第 3 条注释改为准确描述（"带 dash/空号变体"）。

### DF2〔中 · CONFIRMED〕D3「既有断言=弱但真实守卫」未披露 M2 空转残留
- 来源：对抗镜#2 F1。`test_workflow_authority.py:19` `assert "task<N>-" in t` 是第 18 行 `"<change>:task<N>-"` 的子串 → 逻辑恒真（M2，Round 1 提出但修订版四份文档均未提及/处理）。design D3/Risks 称这些为"弱但真实的守卫"**偏乐观**——其中一条对"裸兼容语义"零守卫力。
- 建议：design Risks 显式披露 M2（该断言对裸兼容语义无守卫），勿笼统称"弱但真实"。

### DF3〔中 · CONFIRMED〕"spec-review G1 兜底"是自我拆台的类比（方法论双标）
- 来源：对抗镜#2 F2。G1（proposal:6 自述）= 过去一次靠人工评审运气抓到的事故，非可重复机械机制。本 change 立项理由是"producer→parser 不能只靠评审"，却对 doc↔doc 链接受"下次评审人也能像上次一样抓到"作缓解——同设计两条链两把尺子。
- 建议：Risks 改措辞为"doc↔doc 无自动化兜底、依赖人工评审、已知比 producer→parser 弱"，勿用"G1"包装成机制。

### 低置信/低严重（一行带过，可审计）
- **DF4〔低〕** `spec.md:12` Scenario prose 仍复述标签形状（`<当前change>:task<号>-<slug> 形态`）——M3 轻量回声，又一份需人工保持一致的 doc 副本，Risks 未披露。
- **DF5〔低·遣词〕** `spec.md:12` "`<当前change>`" 易被误读为"须用本 change 真实 slug"，而实现用任意占位 `demo`。
- **DF6〔低·可移植〕** 测试造文件名含冒号 `f-demo:task1-slug.txt`（NTFS 非法），Unix 跑绿，Windows CI 会误红（本测试层 Unix 取向，极低概率）。
- **DF7〔低〕** 集成测试仅用单数字任务号 "1"，未覆盖多位数（如 "12"）`group(2)` 边界（非本 change 引入的新缺口）。

## 已裁掉（反静默压制，可审计）
- **X1**：对抗镜#2 与 OV 对 DF1 判"第 3 条负例名不副实但功能等价、仅术语瑕疵、非真实缺口"。**裁决：部分裁掉——采信对抗镜#1**。理由：对抗镜#2/OV 测的是 `task([\w-]+)-`/`task(\d*)-`（带 dash/空号，第 3 条确能挡）；对抗镜#1 测的是 `task([a-z0-9]+)-`（纯字母，第 3 条**挡不住**且无其他负例覆盖）——两者测的是不同放松变体，对抗镜#1 的 `taskab-` 盲区客观存在。故 DF1 保留为"真但窄的覆盖缺口 + 注释不准"，非纯术语。

## 收敛口

**建议**：Q1=B 修订版设计**技术上 sound、已接地验证，可进设计 HARD-GATE**。但因本轮为事后审计，拍板须**追认覆盖已落地的 task1-3**。两个从属决策留人拍板：
- **Q2（追认）**：拍板即追认 task1-3 合法，随后写真 `<!-- ship-gate: design-approved -->` 锚（独立成行，勿依赖 B4 的子串误配）+ 提交 → ship 可从 RUN_CODE_REVIEW 续跑。
- **Q3（是否修订后再写锚）**：DF1（补 `taskab-` 负例 + 修注释）+ DF2/DF3（Risks 诚实披露）均属廉价 `[spec-review-amendment]` 增补。推荐**先应用 DF1-DF3 再写锚**（闭掉唯一真覆盖缺口 + 让 Risks 诚实），DF4-DF7 记 todolist 择机。若认为残差可接受，也可直接追认写锚、把 DF1-DF3 记 todolist。

---

## 拍板记录 · Round 2（Q1=B 修订版复审门）

- **通过 · 先修 DF1-DF3 再追认**〔用户设计门拍板 2026-07-05〕。已应用：
  - **DF1**：`test_producer_parser_contract.py` 补 `checkpoint(taskab-slug)` 负例（挡"号位加宽为字母数字"）+ 修 `checkpoint(task-1-)` 注释为准确的"号位空/含前导符号"（7 passed）。
  - **DF2**：`design.md` Risks 披露 M2——既有 `test_workflow_authority.py:19` `assert "task<N>-" in t` 是同段子串、逻辑恒真、对裸兼容语义零守卫力。
  - **DF3**：`design.md` Risks 更正"G1 兜底"措辞为"doc↔doc 无自动化兜底、纯依赖人工评审"。
  - **DF4-7**：记 todolist `T37/T38/T39/T40`（spec prose M3 轻回声 / 遣词歧义 / 文件名含冒号 Windows / 单数字号覆盖）。
- **追认覆盖 task1-3**：本轮为事后审计（gate B4 子串误配致越门起跑），拍板即追认已落地的 producer→parser 集成测试 / TAG_RE 负例矩阵 / 回归三任务合法。仓级 349 pytest 全绿。
- 真锚写入下方（**独立成行**，勿依赖第 85 行描述性提及；gate B4 待修 / 已记 buglist）：

<!-- ship-gate: design-approved -->

