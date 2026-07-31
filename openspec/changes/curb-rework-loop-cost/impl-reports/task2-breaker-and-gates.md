# Task 2: 熔断硬上限与出票闸门 — 实现报告

## 范围

在 `sdflow-implement/SKILL.md`（Task 1 已改过版本基础上）落地 R-ID IO-2/IO-3/IO-4 涉及的五项改动。
无脚本、无数据迁移，纯 prose 契约编辑，符合 Global Constraints「本 change 全部交付物是 SKILL.md
prose 契约与配置模板，无 Python 脚本」。

## 逐项落地位置与内容

### 1. 熔断规则 `review-loop-breaker`（`sdflow-implement/SKILL.md` 约 692-717 行）

原「触发」只有单一判据（同指纹连续 2 轮不消解）。改为：

- **判据 (a)**：同指纹连续 2 轮不消解（原判据，措辞保留）。
- **判据 (b)**〔curb-rework-loop-cost · adr/0035〕：同一文件累计被 Critical/Important 命中 ≥3 轮，
  与指纹无关；命中即停，仲裁命题变为「这个门/这段实现本身该不该存在」。附理由段：判据 (b) 存在
  是因为 (a) 的身份键可被「同一根因每轮换语法分支」绕过，并显式写入 **MUST NOT 试图靠改进指纹算法
  替代 (b)**（指纹算法判断"什么是同一根因"本身即模型判断、落在无界语法面——挂钩 CLAUDE.md 基准 5）。
- **subsume 声明**〔R-9〕：(a)(b) 同时命中（第 3 轮）时只派 (b) 的仲裁，MUST NOT 同时派两个不同
  scope 的仲裁。
- **计数窗口**〔R-10〕：显式声明为「全 change 生命周期」，跨全部 ticket 累计，MUST NOT 按单 ticket
  清零。
- **账本持久化**〔R-5〕：新增熔断账本条款——编排层每轮 fix-review 后追加一行到
  `{change_dir}/impl-reports/breaker-ledger.md`，格式 `轮次 | 文件 | 指纹 | 严重度`，git-tracked，
  支持跨 context 压缩后恢复计数与事后审计；同时明确该账本**不构成机械门**（无校验脚本，判定仍由
  编排层自行读取历史行 + 当轮结果比对完成）。
- **(b) 仲裁的 review package 范围**〔R-4〕：显式声明含「该文件 ticket 起点以来的累积 diff」，不受
  第 4 项「fix 轮 review package 只含本轮修复 diff」的增量限定，并注明「(b) 优先于该增量规则」，
  两处互相打了交叉引用（熔断规则节 ↔ 文件交接节）。
- 原有「身份键跨轮稳定」「三级处置归于互斥终态」两条保留不动，位置移到新增内容之后。

### 2. 出票闸门（`sdflow-implement/SKILL.md` 约 271-278 行，出 ticket 模式「产出」小节）

在「每 ticket 含验收标准复选框」之后、「本票声明的 e2e 场景」之前插入新条目：验收标准的语法面
有界性闸门。内容对齐 spec IO-2 Requirement 新增段落：

- 判据：有界语法面（CommonMark fence 变体、自有格式机器锚行）⇒ 可写机械门；无界语法面（通用
  编程语言源码、YAML、make、shell）⇒ MUST NOT 写成机械门，改为「让工具自己回答」（真跑一遍 / 权威
  解析器）或降级为不作判定依据的 best-effort 展示。
- 判据覆盖伪装形态：不仅匹配「扫描/识别/拒绝某形态/指纹」类显式措辞，还匹配「在某格式文件中
  定位/插入/修改某处」（"只动一个键值"背后也是解析）。
- 显式标注「本闸门是指令层约束，MUST NOT 被表述为机械保证」，并挂钩 CLAUDE.md 基准 5（无界语法
  禁手搓）。

### 3. red-before-green 扩展（`sdflow-implement/SKILL.md` 约 533-541 行，implementer dispatch 的
   TDD 循环规则段）

在既有「Red before green / One slice at a time / Refactoring is not part of the loop」三条循环
规则之后追加一段，扩展适用场景到「往既有测试补断言或修改既有断言的期望值/判定逻辑」：

- 要求：补一条断言或修改既有断言时 MUST 先确认它会红——当场破坏被测点、确认失败，再恢复。
- 理由：恒真断言（needle 被别的门满足，或没有用例走到该行）写入时无成本可验，事后 review 才发现，
  届时已需一整轮返工；修改期望值同理。
- 显式声明「实现验证」收尾票的既有 red-before-green 豁免**不受本扩展影响**（该票不写产品代码，
  验收物是证据不是 diff）——对应 ticket 描述里的「收尾票的既有豁免不受影响」要求。

### 4. review package 增量化（`sdflow-implement/SKILL.md` 约 617-623 行，「文件交接〔T125〕」节）

在 review-package 生成脚本代码块之后追加条款：`<before-sha>` 取值按轮次分列——

- 首轮（implementer 首次报 `DONE`/`DONE_WITH_CONCERNS`）：`<before-sha>` = ticket 起点 SHA，范围
  不变。
- fix 轮（第 2 轮起）：`<before-sha>` = 上一轮已审的 `<after-sha>`（"上轮已审 SHA..HEAD"），MUST
  NOT 重新打包自 ticket 起点以来的累积全量 diff，理由与实测证据（单包最大 1,356KB）随 spec 原文
  带入。
- 例外交叉引用：`review-loop-breaker` 判据 (b) 的仲裁 dispatch 不适用本增量限定，(b) 优先于本条
  ——与第 1 项的熔断规则节形成双向引用，避免两处漂移。

### 5. Tests are code 一致性核对（`sdflow-implement/SKILL.md` 约 656-659 行，Standards 轴 dispatch
   prompt 必带清单三条治理规则）

核对现有措辞（"**Tests are code**（本清单同样适用于测试文件——尤其 Duplicated Code〔重复的测试
形状应合并〕与 Speculative Generality〔为想象中的需求预写的测试应删除〕。测试只增不减会让全量
套件单次成本单调上升，这是唯一的遏制点。reviewer MUST NOT 直接删测试，只报 finding 交裁决）"）
与 spec IO-2「Standards 轴的治理规则 SHALL 含『Tests are code』」段逐句比对：Duplicated Code /
Speculative Generality 判据、"测试只增不减…唯一的遏制点"、"reviewer MUST NOT 直接删测试，只报
finding 交裁决" 四个要素均已存在且语义一致（该段已在 d1aa607 落地）。**结论：已一致，未做改动。**

## 未改动范围确认

- 未触碰 `proposal.md` / `design.md` / `specs/` / `tasks.md`。
- 未触碰 `tickets.md`，未勾框、未打完成标签。
- 未引入任何 Python 脚本或解析器（本 change Global Constraints 要求）。
- 零依赖不变量、GC-2 边界锁未涉及。

## 证据

```
git diff --stat sdflow-implement/SKILL.md
 sdflow-implement/SKILL.md | 44 +++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 43 insertions(+), 1 deletion(-)
```

五处编辑均已用 Edit 工具落盘（先 Read 后 Edit），`git diff` 已核验实际改动与本报告描述一致。
