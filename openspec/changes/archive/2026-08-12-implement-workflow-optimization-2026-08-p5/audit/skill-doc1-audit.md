# DOC-1 考古层审计（15 个 SKILL.md）

范围：`find . -maxdepth 2 -name SKILL.md` 实测的全部 15 个顶层 skill（含 `sdflow-devenv`、
`sdflow-upstream-watch`）。判据：DOC-1 删除测试——「只有读过上一版的人才需要的句子，不属于正文」。
每 skill 一节，含删/迁/留三计数 + 边界个案注记。`sdflow:principles` 托管块全程未触碰。

行数以本次审计起手时 `wc -l` 实测为准（与简报数字略有自然漂移，7 大/8 小分组不变）。

---

## 7 个超 500 行 SKILL（重点清理）

### sdflow-implement（821 行）

- **删**：0
- **迁**：0
- **留**：0（无改动）

审计结论：文中出现的历史提及（「裁剪边界声明（防未来好心加回）」节、附录 A/B 出处说明、「链路里此前
没有任何一步执行『全部票完成后的聚合回归』」等）均是解释**当前设计为何如此**的 why 注记，服务于任何
读者（尤其防止未来误加回已砍机制：warm final whole-branch review / progress ledger / task-brief
抽取层 / matt 语义源目录起手检查），不满足「只有读过上一版才需要」的删除测试。零改动，留档说明。

### sdflow-code-review（771→约 760 行）

- **删**：2 处（跨模型 finding 豁免条款的旧版细节说明；lens-metric 锚系统性跳过事件的完整诊断叙事）
- **迁**：2 处 → `sdflow-code-review/references/evolution-notes.md`（新建）
  - §1 度量锚曾被系统性跳过的诊断（B25）——原「历史注记」整段（六轮归档 100% 缺锚的具体诊断过程）
  - §2 跨模型 finding 豁免条款随数值置信滤一并废止的历史沿革
- **留**：正文替换处均改为一句话现状陈述 + 指向 references 的指针

边界个案：`## 与官方 code-review 的分工（弃用为独立 step）` 节保留——它是**当前**行为的名称消歧表
（区分本 skill 与 Claude Code 内置 `/code-review`），不是历史叙事，过删除测试。`"T10" 保留为历史
别名` 类简短命名注记（≤10 字）保留，因它解释为何正文其他处仍出现 "T10-choice" 措辞，属当前可见
文本的必要脚注。

### sdflow-roadmap（715→约 713 行）

- **删**：0
- **迁**：0（原判定点②历史回填改为就地精简，无独立段落值得外迁）
- **改写**：2 处
  - `## 判定留痕总则` 尾句：删「原判定点②（review 按商业化信号分档）已退役……」的沿革叙述，
    改写为当前状态一句话（review 恒跑不分档、不占用判定点序号）
  - `## 未决项` 小节定义：删除对已移除的 "wayfinder frontier" 系统（`Blocked-by` 依赖图 /
    `claimed` 并发语义）的具名回指，改为直接陈述当前小节是什么 + 不是什么，边界声明本身保留
    （它对读者仍有效——防止误解本小节为票据系统）

边界个案：「存量 footage 冻结」「存量四件套包兼容模式」「缺件存量包兼容模式」三节全部保留——
这些不是"讲历史"，是**当前必须遵守的 MUST/SHALL 兼容行为**（对真实存在于本仓与消费仓的旧格式包，
续跑时不得报错/不得强推迁移），删除测试判负：任何跑这个 skill 遇到旧格式包的人都需要这些内容，
不限于"读过上一版的人"。

### sdflow-spec-review（610→约 600 行）

- **删**：0
- **迁**：3 处 → `sdflow-spec-review/references/evolution-notes.md`（新建）
  - §1 单批全并行 dispatch 取代两段串行的完整沿革（DD1/T20，含旧「串行纪律」的具体运作方式）
  - §2 design-voice 复用守卫退役的沿革（DD3，`outside_voice_guard.py` 的具体判定机制）
  - §3 数值置信滤退役对齐说明（与 sdflow-code-review 同期）
- **留**：正文四处改写为一句话现状 + 指针，保留 DD1/DD3 编号供交叉引用

边界个案：与 sdflow-code-review 完全同构的模式（两个评审编排器共用 outside-voice 协议与
lens-metric 契约，历史沿革也高度相似）——两份 evolution-notes.md 未合并为一份，因两个 skill
是独立分发单元（各自 symlink），合并会破坏 skill 自包含性。

### sdflow-done（567→约 555 行）

- **删**：1 处（首段「核心改进（v3，基于实战）」changelog 摘要——内容与正文各步骤逐条重复）
- **迁**：2 处 → `sdflow-done/references/evolution-notes.md`（新建）
  - §1 v3 改进摘要（历史存档，正文已固化对应指令）
  - §2 首次执行踩坑速记（原「附：实战踩坑速记」表格，六条全部与正文其他节文字重复，含一条
    100% 逐字重复——"blockquote 在 MUST 前"在 §3 fallback「坑（手动同步必看）」已有完整表述）
- **留**：正文各步骤指令原样保留（它们是被迁移内容的权威落点，不受影响）

边界个案：`附：实战踩坑速记` 整节标题即含「来自首次执行」的历史框定语，是本次审计里最清晰的
changelog-style 独立段落——过删除测试的判据最直接：六条踩坑没有一条包含正文其他处没有的操作
指令，纯粹是"事后复盘留痕"。

### sdflow-architecture（562→约 548 行）

- **删**：10 处（`<!-- [impl-review-fix] Cx：... -->` HTML 内联审校注释，逐条记录某轮代码审
  对某处措辞的修订理由，如"原抽象占位改字面路径""补时序纪律双句""与 B 波某内部函数行为同步"）
- **迁**：0（这些注释是纯 review-diff 编辑说明，无正文操作语义，不值得外迁保存）
- **留**：2 处注释中携带真实操作语义的片段并入正文（adr-new 只机械化编号扫描、
  Context/Decision/Consequences 三节仍需模型手写——原 C3①内容）
- **新建** `sdflow-architecture/references/evolution-notes.md`：记录本次清理动作本身（供审计
  回溯"为什么这些注释消失了"），仅一节

边界个案：这批 HTML 注释是**本次审计发现的最典型 DOC-1 违规形态**——它们是 markdown 渲染时
不可见的诊断性文字，专门记录"本版与上一版的措辞差异及理由"，教科书式符合"只有比对过版本差异
的审校者才需要"的删除测试判据。与 code-review/spec-review/done 三份的"历史沿革段落"不同，这批
注释无实质设计依据内容，故选择直接删除而非外迁保存。

### sdflow-spec（528→530 行，含尾部指针，净零实质改动）

- **删**：0
- **迁**：0
- **留**：0（已合规，零改动）

审计结论：该 skill **已经是本次清理要推广的目标形态**——`references/{delegation-protocol,
degradation-ladder,evolution-notes,decision-memo-schema,adr-and-glossary-templates}.md` 早已
存在，SKILL.md 正文顶部即有「按需资料路由（默认不加载）」小节，指向 evolution-notes.md 的用途
声明与末尾指针格式，与本次为其余 6 个大文件新建的模式完全一致。抽查未发现残留 HTML 诊断注释或
changelog 段落。判定：零改动，留档说明——本文件在设计上即是其余 6 份大文件参照的范式来源。

---

## 8 个 ≤500 行 SKILL

### sdflow-devenv（464 行）

- **删**：0 / **迁**：0 / **留**：0（无改动）

零改动结论：全文均为当前操作指令（五步流程、五条红线、三模式），无版本对比、无 changelog 段落、
无 impl-review-fix 内联注释。

### sdflow-issues（345→约 344 行）

- **删**：1 处（`migrate` 历史迁移工具节中"本仓已迁移完成（287 个 issue 全部迁移，v1 数据文件/
  脚本已删除）"的具体历史数字与完成状态叙述）
- **迁**：0
- **留**：该节功能性说明保留（`migrate` 命令本身对其它仍在 v1 格式的仓库依然有效，属当前可用
  工具，非纯历史）

边界个案：本节判定介于"纯历史"与"当前工具文档"之间——`migrate` 命令代码路径仍存在且供其他仓
使用，故不整节删除；但"287 个 issue""本仓已迁移完成"这类仅描述本仓自身历史状态、对任何读者
（含首次接触本 skill 的人）均无操作价值的具体数字，判定为考古层，予以删除。

### sdflow-upstream-watch（335→约 334 行）

- **删**：1 处（`<!-- [impl-review-fix] 缓存路径按源分别列出，不用不存在的 <source>.git 模板 -->`
  HTML 内联审校注释）
- **迁**：0 / **留**：0

### sdflow-init（251 行）

- **删**：0 / **迁**：0 / **留**：0（无改动）

零改动结论：「退役 hook 反注册（自愈）」「退役部署文件清理（自愈）」两节点名具体已退役项
（`change-review-stub.py`、`serve.sh`+`review.html`）——这些不是讲历史，是**当前每次 init/update
运行都会执行的活跃自愈机制**的操作数据（`RETIRED_HOOKS`/`RETIRED_DEPLOY_FILES` 名单内容），任何
跑本 skill 的人都需要知道会清理什么，不限于"读过上一版的人"，过删除测试判负（不删）。

### sdflow-retro（249 行）

- **删**：0 / **迁**：0 / **留**：0（无改动）

零改动结论：全文围绕"脚本做什么、模型做什么判断"的当前行为说明，无历史叙事段落。

### sdflow-maintain（225→约 224 行）

- **删**：1 处（步骤 4 末尾的裸引用标签 `[impl-review-fix CF-3]`——无内容的纯引用标签，不解释
  任何东西，对读者零信息量）
- **迁**：0 / **留**：0

### sdflow-ship（193→约 191 行）

- **删**：2 处（两条 `<!-- [impl-review-fix] 裁决项10：... -->` HTML 内联审校注释，分别说明
  "兜底路径由省略号改写为显式三处路径"与"merge 意图转述由自由措辞改为归一化固定词表"两处措辞
  修订的理由）
- **迁**：0 / **留**：0

边界个案：`"T10" 保留为历史别名` 这类简短命名注记（`## 铁律` 节「决策协议」条目内）保留——它
解释为何本文与其他 skill 里仍多处出现字面 "T10-choice" 措辞，是当前可见文本的必要脚注，非纯历史。

### sdflow-upgrade（183 行）

- **删**：0 / **迁**：0 / **留**：0（无改动）

零改动结论：纯操作步骤（pull → setup → 展示版本 → 提示 → 陈旧提醒），无历史对比段落。

---

## 汇总

| skill | 行数（审计前） | 删 | 迁 | 留 | 结论 |
|---|---|---|---|---|---|
| sdflow-implement | 821 | 0 | 0 | 0 | 零改动 |
| sdflow-code-review | 771 | 2 | 2 | 改写4处 | 已清理 |
| sdflow-roadmap | 715 | 0 | 0 | 改写2处 | 已清理 |
| sdflow-spec-review | 610 | 0 | 3 | 改写4处 | 已清理 |
| sdflow-done | 567 | 1 | 2 | 0 | 已清理 |
| sdflow-architecture | 562 | 10 | 0 | 并入正文2处 | 已清理 |
| sdflow-spec | 528 | 0 | 0 | 0 | 已合规（范式来源） |
| sdflow-devenv | 464 | 0 | 0 | 0 | 零改动 |
| sdflow-issues | 345 | 1 | 0 | 0 | 已清理 |
| sdflow-upstream-watch | 335 | 1 | 0 | 0 | 已清理 |
| sdflow-init | 251 | 0 | 0 | 0 | 零改动 |
| sdflow-retro | 249 | 0 | 0 | 0 | 零改动 |
| sdflow-maintain | 225 | 1 | 0 | 0 | 已清理 |
| sdflow-ship | 193 | 2 | 0 | 0 | 已清理 |
| sdflow-upgrade | 183 | 0 | 0 | 0 | 零改动 |

**考古层关键词命中总计**：个位数级别的独立段落违规（sdflow-done「实战踩坑速记」+
「v3 改进摘要」、sdflow-code-review 两处历史沿革、sdflow-spec-review 三处历史沿革）+
双位数的 HTML 内联审校注释违规（主要集中于 sdflow-architecture 10 处，另 sdflow-ship 2 处、
sdflow-upstream-watch 1 处、sdflow-maintain 1 处裸标签）。**符合简报预期**（「考古层关键词命中
预期为个位数……大文件体量主要来自当前有效指令」）——七个大文件里六个的正文密度确认为当前有效
指令，唯一大幅清理的 sdflow-architecture 也并非"考古层撑体量"，而是审校注释这一独立、可清晰界定
的类别。

**「零改动」结论涉及 6 个 skill**（implement / spec / devenv / init / retro / upgrade），均已
在对应小节留档说明理由，符合任务简报「零改动结论同样合法」的要求。
