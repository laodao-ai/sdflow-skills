---
name: sdflow-architecture
description: >
  架构设计（SAD）编排器——为**一个系统**产出/维护「系统架构设计文档」（SAD）：事实三问采集 → 子系统划分
  与 contract 定义 → 挂产物拍板 → 冷走查 + 人门 → skeleton-ready 交棒骨架 change。本 skill 管**空间轴**
  （一个系统当下怎么切成子系统、子系统间 contract 怎么定）。触发词面：「设计架构 / 划分子系统 / 定 contract /
  做一份 SAD / 系统架构设计 / 这个系统该怎么拆模块 / 架构评审」。**不触发**：单次 change 的 spec/design（走
  /opsx:ff）、纯代码实现、bug 修复。**时间轴规划（分阶段 roadmap / 阶段排期 / 里程碑）→ 用 /sdflow-roadmap**
  （本 skill 不排期，只定一个系统当下的空间结构）。**前置条件**：消费仓需已 `sdflow-init`——无 `openspec/`
  布局时首触即 preflight fail-closed 并指引先跑 /sdflow-init。Trigger with /sdflow-architecture。
---

# sdflow-architecture — 架构设计（SAD）五步编排器

把一个系统的架构设计做成一条**可门禁、可留痕、fail-closed** 的五步流水线，产出/维护消费仓
`openspec/architecture/sad.md`（项目级单例 live 文档）。机械活（脚手架/状态机/结构 lint/分家写入）全部交
`scripts/` 两脚本（`sad_scaffold.py` 写、`sad_lint.py` 读），**模型只做判断与编排**——提问、跑拆分规则集、
挂产物拍板、派冷走查、过人门。

**产出形态 = recorder 式直写**：SAD 直写 `openspec/architecture/`，**MUST NOT 以 openspec change 壳承载
生成过程**（先例：sdflow-roadmap 规则 4）——质量门内建（lint + 冷走查 + 升档 + 人门），第一个 change 壳是
人拍板后开的**骨架 change**（步骤 ⑤ 交棒物），不是本 skill 自己开。

## 路径与调用约定（先读）

本 SKILL 出现的每条命令都用下列变量，运行前先在会话里定死其字面值：

```
REPO="$(git rev-parse --show-toplevel)"     # 消费仓根（分家/SAD 落位都在其 openspec/ 下）
SKILL_DIR=<本 SKILL.md 所在目录>            # 安装后 = ~/.claude/skills/sdflow-architecture（Codex 宿主为
                                            #   ~/.codex/skills/sdflow-architecture）；经 symlink 指向源仓 checkout
SAD="$REPO/openspec/architecture/sad.md"    # SAD 单例
```

- 自带脚本一律 `python3 "$SKILL_DIR/scripts/<脚本>" <子命令> --root "$REPO" …`——**脚本在 skill 目录，`--root`
  是消费仓根，两者不同**，别把 `--root` 指到 skill 目录。（生态先例：`sdflow-retro` 同样脚本在 skill 目录、
  `--root` 指消费仓。）
- 退出码约定（照抄脚本、勿臆造）：`sad_scaffold.py` 0=ok / 2=坏输入 / 3=无 openspec 布局 / 4=单例已存在 /
  5=迁移拒绝（表外迁移或锁 draft 前置未过）；`sad_lint.py` 0=全过 / 1=有违规 / 2=坏输入。
- **references（按名引用，不复述其内容）**：`references/intake-questionnaire.md`（①三问）·
  `references/decomposition-rules.md`（②R1–R11 + AP1–AP4）· `references/review-lenses.md`（④走查/升档信号表）·
  `references/quality-criteria.md`（S 编号真相源，人门清单源）· `references/sad-template.md`（十节骨架，scaffold
  写入）· `references/checklists/`（R1 外部依赖典型集 / R4 变化类别表 / 横切模板 / 质量属性候选库）。

## 信任边界（两条原文级声明，每次跑到相关步都显式陈述一行）

- **「lint 通过 = 结构性通过 ≠ 内容已审」**——`sad_lint.py` v1 只断言结构（十节存在性 / 假设集合对账 /
  排序 / frontmatter 枚举 / 组合不变式 / 建议节分支），通过码 `structure-ok-SEMANTICS-UNCHECKED` 的尾缀即诚实
  提醒：绿不代表内容对，内容质量由冷走查 + 升档 + 人门守。
- **「facts=answered = 已记录回答 ≠ 质量已核（复核在人门议程）」**——`set-fact <key>=answered` 只表示
  「已记录到人的回答」，不表示回答真实充分；回答质量核验固定列入人门议程第 1 条「三问回答复核」。

（同款信任边界还覆盖：候选真实性（是否凑数）、假设推测依据是否成立——均无确定性信号，归人门 + 冷走查复核。）

## 模型档位（一行）

主 session（提问/规则集判断/拍板编排/裁决）与**冷走查子代理均用强档**，无可下放弱档的步——机械活已全部
脚本化（scaffold/lint 零模型），带门禁的判断步弱档 = 假绿放行。档位与缺省见规则根 `model-tiers.md`（经
`~/.sdflow/hack/resolve-workflow.sh` 解析；DEC-12①）。

---

## 起手 A：preflight + 单例分流（二次触发编排入口）

**每次触发先跑 `init`**——它内建两级 preflight 与单例分流：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" init --root "$REPO"
```

按退出码分流：

- **exit 3（无 `openspec/` 布局）**：**原样转述** stderr 的 preflight 指引（先在运行 checkout 跑
  `bash ~/.skills/sdflow-skills/setup.sh`，再在消费仓会话执行 `/sdflow-init`，装完回来重跑本命令）——
  MUST NOT 自造半套布局、MUST NOT 静默继续。（有 `openspec/` 但缺 `adr/`/`CONTEXT.md` 时脚本会打印「首次
  创建 …」并最小初始化，属正常，照实转述即可。）
- **exit 4（`sad.md` 已存在）**：**显式向操作者区分 continue / replan 后**带 `--on-exists` 重跑，MUST NOT
  静默覆盖：
  - **continue（增量续写）**：`init --root "$REPO" --on-exists continue`。续写前**先读
    `openspec/architecture/sad-log.md` 定位断点**——找最后的 `step=N reached` 行与其后的**候选摘要快照**行，
    据此判断从哪一步接着跑（候选只活在断掉的对话里，不读 sad-log 会丢）。
  - **replan（重规划，旧内容归 git 历史）**：`init --root "$REPO" --on-exists replan --reason "<非空重规划原因>"`
    （脚本会用模板重置 sad.md 并 append 一条 `replan: <原因>` 留痕）。
  - **判据（供操作者选，不代决）**：只补未定内容、不推翻既有决策 → continue；推翻既有事实/分解决策 → replan。
- **exit 0（全新）**：脚本已建 `sad.md` + `sad-log.md` 并 append `init` 留痕，进步骤 ①。

**一仓多系统**：操作者声明消费仓是「一仓多系统」时，**显式提示**「v1 仅支持单系统单例（演进路径
`openspec/architecture/{system}/` 已预留，v1 未启用）」并留痕（`log --line "多系统声明：按 v1 单例处理"`），
MUST NOT 硬造多系统目录布局。

> **回写与回落（既定后续动作，不经 continue/replan 分流）**——见文末「状态迁移速查」，此处不重复。

---

## 步骤 ① 事实三问采集

读 `references/intake-questionnaire.md`，向操作者提**事实类三问**（价值类问题 MUST NOT 进首轮）：
① 一句话定位（是什么/给谁用/解决什么）· ② 外部系统清单 + 文档指针 · ③ 硬约束（栈/平台/部署形态/存量/合规）。
按该文件的「追问提示」逐问追问；答不出「还有哪些外部系统」时提示 `references/checklists/external-deps-typical.md`
协助枚举。

**时序纪律（加粗强制）**：**MUST 实际向操作者提问并获得人的回答之后，才允许调 `set-fact` 记录；MUST NOT 预填、
MUST NOT 替操作者臆测答案。** 记录：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" set-fact --root "$REPO" --fact positioning=answered
python3 "$SKILL_DIR/scripts/sad_scaffold.py" set-fact --root "$REPO" --fact external_systems=answered
python3 "$SKILL_DIR/scripts/sad_scaffold.py" set-fact --root "$REPO" --fact hard_constraints=answered
```

（key 三选一：`positioning` / `external_systems` / `hard_constraints`；value ∈ `answered|missing`。）

**允许「不知道」**：任一问操作者明确答不出 → 对应 fact **保持 `missing`**（不调 set-fact，或显式
`--fact <key>=missing` 留待补痕）——这是合法的非阻塞状态，**锁 `draft`**（不许升 skeleton-ready），但不阻塞
继续采集与产草稿。此处复述信任边界：**facts=answered = 已记录回答 ≠ 质量已核（复核在人门议程）**。

三问处置完，留痕步骤到位 + 事实快照：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "step=1 reached | facts: positioning=answered external_systems=answered hard_constraints=missing"
```

---

## 步骤 ② 规则集跑候选（R1–R11 + AP 自检前置）

按 `references/decomposition-rules.md` 的判据流水线执行：R1 原料提取 → R2 语义聚类 → R3 物理边界先行 →
R4–R7 四判据精修（变化率/单写者/context 预算/依赖形状）→ R8 冲突仲裁序 → R9 粒度带（3–7）与终止 →
R10 拆分做全景（后期子系统 `planned` 占位）→ R11 留痕 schema。

**AP 自检 MUST 先于候选交人**（AI 自由分解默认高发 AP1 entity-service / AP2 流程式 / AP3 技术分层 /
AP4 God-hub）。任一候选命中 AP → 按修正动作重新聚类，并留三行结构化痕（交人门快速核验「真改了还是嘴上改」）：

```
before: <自检前候选切法一句话，含命中 AP 的子系统名/职责>
after:  <修正后切法一句话>
触发 AP 编号: AP<n>
```

**候选数由仲裁分歧驱动**（不定配额）：

- R8 出现**真实判据分歧**（如语言边界 vs 变化率打架、hub 拆不拆）→ 每个分歧点产出一对**真实**候选（整体
  通常收敛 2–3 个方案）；**整体方案数上限 3**——超出按分歧维度归并后再呈现（防拍板面爆炸）。
- 四判据**无分歧** → 允许单方案直出，但 **MUST 显式陈述一行**「判据无分歧，单方案直出」（跳过类判定显著
  呈现），并留痕：`log --root "$REPO" --line "判据无分歧，单方案直出"`。
- **MUST NOT 构造明显劣化的对照方案凑数**（稻草人让拍板变表演，比单方案更糟）。**信任边界**：候选真实性
  （是否凑数）无确定性信号，归人门与冷走查复核——脚本不查、模型不自证。

**分解判据落 ADR**：子系统分解的判据、被否切法、显式接受的疑点（hub / 横跨变化）→ 消费仓 `openspec/adr/`
下的**第一条分解 ADR**，经 `adr-new` 机械分配编号（见「分家指令」节）。

留痕步骤到位 + **候选摘要快照**（continue 断点恢复靠它）：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "step=2 reached | 候选快照：方案A=<一句话> / 方案B=<一句话>（分歧点：语言边界 vs 变化率）"
```

---

## 步骤 ③ 挂产物拍板（一轮打包呈现）

价值类问题在此步**挂具体产物以选择题形态**问（「A/B 切法选哪个」而非「描述你的质量取舍」）：

- **一轮打包呈现**：全部选择题分组，用**单条消息**摊给操作者，不逐条弹窗打断。
- **数值溯源二态穷尽**：操作者拍的数值标 `〔人拍〕`；操作者**不否决即采纳推荐**的数值标 `〔推荐待校准〕`
  （AI 给出域惯例推荐值，待后续校准/否决）。数值不许裸写无标记。
- **假设显影**：任何 AI 推测/编造/占位内容一律标 `[假设-N]`（含推测依据），并在 SAD《附录：假设清单》
  登记同编号行（内联标记 ↔ 附录行**双向锚**：编号集合双向相等、双侧不重号）——一份「看起来完整」却带一堆
  未确认假设的 SAD 是 draft 不是成品。

拍板后：把定稿方案写入 SAD 正文（第 1/2/3/4/5/7/8/9 节 + 附录假设清单，按 `references/sad-template.md` 骨架，
每节「有内容 或 显式 `N/A — <理由>`」），并留痕候选快照 + 步骤到位：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "step=3 reached | 拍板快照：采纳方案A（子系统：采集端/上报端/…），关键数值：重连补发窗口5s〔人拍〕"
```

---

## 步骤 ④ 冷走查 + 升档判定 + 人门

### 4.1 冷走查（默认档，每次必跑）

**走查 MUST 由 fresh 子代理执行**——派一个 fresh-context 子代理（Agent 工具），让它读
`references/review-lenses.md`，对 SAD 做**场景×子系统×contract 覆盖矩阵**走查。**禁止生成 session 自查**
（自证偏差）。矩阵产出**内嵌 SAD 第 6 节正文**（DEC-11），**MUST NOT 生成独立走查报告文件**；发现的洞
转成正文修订或 `[假设-N]` 条目。

走查留痕 **MUST 带执行者字段**（供审计区分冷走查与自查）：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "走查 轮次=1 洞数=2 执行者=fresh-subagent:<子代理标识>"
```

**走查失败重派一次**（子代理无矩阵产出）→ 再失败 **显式报告缺口**，**MUST NOT 无走查静默过人门**。

**Codex 宿主降级分支**：若运行宿主无 fresh 子代理 fan-out 原语（如 Codex CLI 宿主——setup.sh 双宿主分发
无 opt-out），SHALL **显式降级**：走查由主 session 执行，并 **MUST 响亮留痕**
`walkthrough=self-review-degraded` + 建议操作者换有子代理原语的宿主复跑，**MUST NOT 佯装冷走查**：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "走查 轮次=1 洞数=N walkthrough=self-review-degraded 执行者=main-session（宿主无 fresh 子代理原语，建议换宿主复跑）"
```

### 4.2 升档判定（信号表，显式一行 + 留痕）

按 `references/review-lenses.md`「走查与评审分档」信号表判是否升档，命中任一即升：① 骨架验证慢/贵（硬件
依赖/外部审批链/分布式部署，无法一个 change 打通）② 不可逆决策面大（落盘 schema/对外发布 API/多进程拓扑）
③ 不可控外部 contract 多 ④ 操作者显式要求。**判定 SHALL 显式陈述一行并留痕，未命中也写**：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" log --root "$REPO" --line "升档判定：未命中升档信号，走默认档冷走查"
# 或： --line "升档判定：命中信号②不可逆决策面大（落盘 schema）→ 升档多镜"
```

**排除项**：假设计数高 ≠ 升档信号（假设多 = 缺事实，回步骤 ① 补采集，多镜审不出事实缺失）。

### 4.3 升档形态（自编排镜阵，MUST NOT 整体调 sdflow-spec-review）

升档 = 本 skill **按 `review-lenses.md` 自编排镜阵 fan-out fresh 子代理**（S2 走查镜 / S3 分解正当性镜 /
S4 对抗找缝镜 / S6 一致性镜 / S7 考虑面完整性镜 / S8 目标态镜 / S9 风险对位镜 / S10 切片自足性镜 /
S11 演进可维护性镜，按命中风险取镜）。**MUST NOT 整体调用 `/sdflow-spec-review`**——它锚定 change 四件套，
硬套则领域段空转、产物语义错配。

**outside voice 镜**：升档且 wrapper 可用时，**至少一面镜用跨模型**，放 prior 依赖最强镜位（S4 对抗找缝 /
S8 目标态）。调用经 `~/.sdflow/hack/outside-voice.sh`（**契约单一源 = 脚本头注释，此处只给分支决策，不转述
接口细节**）：

```
HELPER=~/.sdflow/hack/outside-voice.sh
[ -x "$HELPER" ] 不成立（不可执行/不存在）           → 显式降级 Claude 镜（与 preflight 非 ready 同一降级出口，不静默）
preflight：仅精确匹配 "ready" 走 codex               → 其余（not_installed/missing-deps/畸形/非零）显式降级 Claude 镜
exec --context-file <f>：
  exit 0    → stdout findings 进镜阵合并池
  exit 124  → 超时：显式降级 Claude 镜（不静默）
  exit 1    → exec-error：显式降级 Claude 镜（不静默，stderr 摘要写正文）
  exit 3    → secret-hit：拒发本镜、不 fallback、报人工核查
```

**升档前 MUST 提示操作者确认消费仓无敏感明文**——codex read-only 沙箱防写不防读、不防出境；wrapper 的 secret
扫描只覆盖显式喂入的 context 文件，仓内其他敏感文件不在其保护面。降级一律**显式提示不静默**，并留痕
`log --line "升档镜阵：outside-voice reason_code=<…> → 降级 Claude 镜"`。

### 4.4 人门（固定议程，位置钉死 = 走查洞处置后、scaffold 迁移前）

走查/镜阵产出的洞处置完，进人门，**固定三条议程逐条过**：

1. **三问回答复核**——核验 facts 三问回答是否真实充分（facts=answered 只是已记录，质量在此复核）。
2. **假设逐条处置**——每条 `[假设-N]` 由操作者「显式接受 或 标待校准」，处置经 scaffold 落盘（发生在操作者
   逐条确认之后）：
   ```
   python3 "$SKILL_DIR/scripts/sad_scaffold.py" set-assumption --root "$REPO" --assumption 1=接受
   python3 "$SKILL_DIR/scripts/sad_scaffold.py" set-assumption --root "$REPO" --assumption 2=待校准
   ```
   （处置 ∈ `接受|待校准`；`未处置` 不可经本把手写入。存在未处置假设 → 后续迁移会被锁 draft。）
3. **走查洞处置确认**——逐洞确认已转成正文修订或假设条目、无遗留。

---

## 步骤 ⑤ 交棒（skeleton-ready）

### 5.1 撰写「骨架切片建议」内容到临时文件

模型撰写切片建议内容到一个**临时文件**（供 `--slice-file` 机械插入 SAD），MUST 含：

- **穿越点：引用第 5 节条目、MUST NOT 复述**——每个子系统一行，格式钉死
  `- 穿越点[<子系统名>]：<引用/一句话>`（`<子系统名>` 须与第 5 节 `### 5.x 名称` 集**完全一致、不重复**，
  否则 scaffold 前置复检 fail-closed）。
- **骨架 DoD 文案**（原文级）：「每条 L1 contract 被一次真实调用穿过 + 部署链路走通」。
- **建议 change 名**（如 `skeleton-<system>`）。
- **消费语义声明**：「**建议非契约**；本 skill **不代开骨架 change**，工作流扳机归操作者」。

示例临时文件内容：

```
- 穿越点[采集端]：见 §5.1 对外 contract「采集端→上报端接口」，骨架期以一次真实上报穿过
- 穿越点[上报端]：见 §5.2 对外 contract「上报端→云接口」
骨架 DoD：每条 L1 contract 被一次真实调用穿过 + 部署链路走通
建议 change 名：skeleton-<system>
（建议非契约；不代开骨架 change，工作流扳机归操作者。）
```

### 5.2 迁移 + lint + 收尾

先过人门（4.4）后，机械迁移（scaffold 复检 facts 三问齐 + 假设对账过 + 穿越点集 == 子系统集）：

```
python3 "$SKILL_DIR/scripts/sad_scaffold.py" transition --root "$REPO" --to skeleton-ready --slice-file <临时文件>
python3 "$SKILL_DIR/scripts/sad_lint.py" --root "$REPO"
```

lint 通过码 `structure-ok-SEMANTICS-UNCHECKED`——复述信任边界：**lint 通过 = 结构性通过 ≠ 内容已审**。

**对话收尾行（原文级，交棒不得只埋在文件里）**：

```
SAD 已 skeleton-ready · 建议骨架 change：<名> · 下游：/opsx:ff <名> · 软提示：git add openspec/architecture/ 纳入版本控制
```

---

## 分家指令（ADR / 术语单一真相源；SAD 只引用不复述）

分家写入**全部机械化**，SAD 本体只索引/引用，**MUST NOT 复述**其内容（复述必双写发散）：

- **ADR → `openspec/adr/`**（不可变 + supersession 链），编号由 scaffold 机械分配：
  ```
  python3 "$SKILL_DIR/scripts/sad_scaffold.py" adr-new --root "$REPO" --title "<决策一句话>" --slug "<kebab-slug>"
  ```
  扫描既有文件名最大数字前缀 +1；**编号模式无法识别 → fail-closed**（脚本非零退出），此时人工核对后用
  `--number <N>` 越过扫描。第一条分解 ADR（步骤 ② 判据）即经此产出。
- **术语 → `openspec/CONTEXT.md`**（生态既有 home），并入 `## Language` 段末尾：
  ```
  python3 "$SKILL_DIR/scripts/sad_scaffold.py" context-add --root "$REPO" --term "<术语>" --definition "<定义>"
  ```
  同名术语**不覆盖**——**冲突 fail-closed 显式报告，留人裁决**（脚本非零退出并指出冲突行）。

---

## 状态迁移速查（合法迁移表；表外一律拒绝）

状态迁移**只由 `sad_scaffold.py transition` 执行**，模型/人不得手改 frontmatter 跳级。

| 迁移 | 命令 | 备注 |
|---|---|---|
| draft → skeleton-ready | `transition --to skeleton-ready --slice-file <f>` | 复检 facts 齐 + 假设对账 + 穿越点集==子系统集；插入建议节（步骤 ⑤） |
| skeleton-ready → validated | `transition --to validated --dod-confirmed` | **骨架落地后 continue 回写入口**（既定后续动作，**不经 continue/replan 分流**）；scaffold 自动**移除**建议节 |
| skeleton-ready → draft（回落） | `transition --to draft --reason "<原因>"` | 事实答案被推翻；回落原因入 sad-log，建议节一并移除 |
| validated → draft（回落） | `transition --to draft --reason "<原因>"` | 骨架否决 contract 大面积 / 事实推翻；回落原因入 sad-log |

**骨架落地后的回写编排**：骨架 change 落地、DoD 达成后，操作者以 **continue 回写入口**重触发本 skill →
`init --on-exists continue` → 直接跑上表 `transition --to validated --dod-confirmed`。这是**既定后续动作**，
**不属「重新触发生成」、不经 continue/replan 确认分流**（REQ-9 显式排除，消除同一单例双入口门禁不一致）。

---

## 全流程留痕总则

关键判定 SHALL 追加进 `openspec/architecture/sad-log.md`（append-only，`sad_scaffold.py` 负责追加，
MUST NOT 改写既有行）：单方案声明 / 升档判定（含未命中）/ 降级提示 / 状态迁移与回落原因 / 走查轮次与洞数 /
**`step=N reached` 步骤到位 / 候选摘要快照 / 走查执行者字段**——后三者是 continue 断点恢复的凭据（候选只活在
对话里则 session 断即丢）。`transition` / `set-fact` / `set-assumption` / `init` 会自动 append 各自留痕；SKILL
自身的判定留痕用 `log --line "<…>"` 显式追加。
