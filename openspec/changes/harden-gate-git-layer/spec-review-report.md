---
ship-gate:
  design_approved: true
---

# spec-review-report — harden-gate-git-layer（第二轮 · 设计重写后）

> **本报告取代第一轮**（针对 `-m`/`--cc` 枚举方案的那版，内容见 git 历史 `6424751`）。
> 评审对象：`646fcc1` 版四件套（录锚 + 比内容 + 限定求值窗口）。

## 锚行区

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-14,TG-17,TG-18,TG-19,TG-22,TG-23" evidence="被保护资产=设计审拍板/代码审放行/verify 通过三个结论的有效性，是 merge 前仅有的质量门；威胁模型表 + 残余面登记构成 TG-17 触发点" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="16" 采纳="16" 裁掉="0" defer="0" 独立="16" sev="致3/高5/中6/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="11" 采纳="11" 裁掉="0" defer="0" 独立="10" sev="致0/高7/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="6" 采纳="5" 裁掉="0" defer="1" 独立="5" sev="致0/高0/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="5" 采纳="1" 裁掉="4" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="1" sev="致0/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="2" 裁掉="0" defer="2" 独立="1" sev="致0/高2/中0/低0" -->

**镜阵**：Step1 广审 3 镜（CEO / eng / DX，`simulated` 降级已标注）+ Step2 fan-out 5 镜
（base 1 + 对抗 3 + 接地 1）+ 跨模型 outside-voice 2 站点（codex `gpt-5.6-sol`，两站点 `rc=0`）。
**领域镜 0 个**：`domains/` 只有 backend/embedded/frontend，本 change（Python stdlib CLI 门禁 + Markdown 编排）
无命中 ⇒ 该位改跑通用 `spec-quality-base.md`（canonical 投影记为 `domain`）。

---

## 🔴 先说结论

**设计方向成立，但四件套 MUST 经一轮实质修订才能进 HARD-GATE。**

- **方向站得住**：CEO 镜独立评估后判定「限定求值窗口」这个取舍**值**——让出的保护面有明文工作流兜底、
  落进既有残余面，换回的复杂度删减是实打实的；且被取消的那套逃生口机制其机械性本来就被高估
  （gate 只能比较 `reviewed_sha` 的值，拦不住谁去写它）。两条更简的替代路（整树 sha、负向 pathspec）
  已实测证伪 ⇒ 现方案已是化简后的下限。
- **但不能就这样过门**：本轮挖出 **4 条致 + 15 条高**，其中两条足以让本 change 的核心承诺落空
  （fixture 结构性不兼容 ⇒ 30+ 处无关测试集体失败；威胁表两个头号安全收益无任何测试任务）。

### 🟢 关于「不能越改越复杂」这条 steer —— 逐条分类过了

| 类别 | 条数 | 是否增加方案复杂度 |
|---|---|---|
| **把已定的决定写对**（补 tasks 子项、补实现指引、修文档断言） | 26 | **否**——不加机制，只是把口径钉死 |
| **减法**（D26：`ls-tree` 比 `path→oid` 映射） | 1 | **负**——git 调用 8–10 次 → 4 次，覆盖面反而更全 |
| **零成本改时序**（窗口右边界、code-review 锚时序） | 2 | **否**——改的是「在哪一刻求值 / 在哪一刻写锚」，判据本身不变 |
| **真的要加东西**（需你拍板） | 3 | **是**——见 Q1/Q2/Q3 |

**⇒ 全部发现里只有 3 条会让方案变复杂，且都上了拍板台。其余是「本来就该这么写」。**

---

## 决策登记区

```
  ┌──────────────────────────────────────────────────────────────┐
  │ [需拍板] Q1  归档终态盲区（2 条致命的同一片面）→ fold 还是另开？  │
  │ [需拍板] Q2  「锚定对象 ≠ 审查对象」一组 → 修哪几条、留哪几条？  │
  │ [需拍板] Q3  回滚不对称 → 登记残余面 还是 加硬约束？            │
  │ [自动决策] D1–D26  采纳，落进四件套修订（不增复杂度）           │
  │ [已裁掉]  X1–X4   接地镜「未实现」误报，附裁掉理由              │
  └──────────────────────────────────────────────────────────────┘
```

### 🔴 Q1（致）— 归档终态盲区：`verify` 之后到 `merge` 之间无任何失鲜检查

**两条独立路径，两个 voice 站点各命中一条，合起来把最后一公里说透了**：

- **V-F1（design-voice）· 已提交路径**：`:1311` 检查 `verify-report` 之后 → `RUN_VERIFY` → `sdflow-done`
  执行 archive + commit + merge → 重跑 gate 时 `cdir` 已不存在 → **D3 短路凭归档 `verify=PASS` 判 `SHIPPED`，
  全程不调 `is_stale`**（主 session 已核实：D3 段内 `is_stale` 出现 **0 次**）。
- **H-F1（hr-tg）· 未提交路径**：gate 只看 committed（`ship_gate.py:90` 起明文），dirty worktree 仅 MAY 软提示；
  而 `sdflow-done` 第四步是**无范围限制的 `git add -u`**（`sdflow-done/SKILL.md:321`）⇒ verify PASS 后改已追踪源码、
  **保持 HEAD 不变**，gate 判 fresh，改动却被一次性收编进最终提交。

**都不需要恶意**——`git add -u` 是收尾的正常动作。**后果**：「verify=PASS 背书了 merge 的内容」这个承诺不成立。

**同片面已有登记**：T179「archive 后无人重跑全套件，gate 判 SHIPPED 时 main 实际是红的」——
「测试没重跑」与「代码改动没重查」是**同一盲区的两半**，本条不是孤例。

> **推荐：fold 进本 change。** 依据——**修法成本已核实为极低，且是纯复用**：
> ① V-F1：`archived_verify_state`（`:207`）已经在做「从 ref 树 `git show` 归档 verify-report →
> `parse_ship_gate_frontmatter`」，**frontmatter 已经解析出来了**，读 `reviewed_sha` 只是多取一个字段；
> 比顶层树的原语本 change 也已经有了 ⇒ 约 1 个 task。
> ② H-F1：`sdflow-done` 已有 merge 前 untracked 硬检查（SR-2，判据「任何 `??` 存在即 halt」），
> 扩到非 `openspec/` 的 tracked dirty 就是同一段落改判据 ⇒ 约 1 个 task。
>
> **代价**：tasks 30 → 约 33。
> **备选**：另开 change（后果：本 change 宣称修好了失鲜判定，而最后一公里敞开；且新 change 要重付一遍
> workflow 循环成本——撞基准 4「撞到与本次功能相关的 bug 立即 fold」）。

### 🔴 Q2（高）— 「锚定对象 ≠ 审查对象」：四条发现是同一个根问题的四个面

| # | 面 | 来源 | 我的推荐 |
|---|---|---|---|
| a | **窗口右边界间隙**：`CONTINUE_IMPL` 条件是 `plan_ids - done` 非空（`:1268`），窗口右边界恰好是「最后一个 task 打勾那一刻」，不是「实现结果被检查过那一刻」。同一提交「改 design.md + 完成最后一个 task」即跨过 | design-voice V-F2 + 主 session 独立命中 | **修**（零成本） |
| b | **code-review 锚时序自锁**：tasks 1.1 说「出报告时」写 `reviewed_sha`，但 `sdflow-code-review` 把修复与报告**同一个 checkpoint** 提交（`SKILL.md:256-257`）⇒ 锚不含修复 ⇒ checkpoint 一落**立刻自失鲜**，每轮有自动修复的代码审都会自锁 | hr-tg H-F2 | **必修**（P0 实现阻断） |
| c | **spec-review 锚定 ≠ 审查对象**：Step3 checkpoint 落 C1（已审内容）→ 人读报告后要求改 → C2（**未经任何镜审查**）→ 拍板 → `reviewed_sha = HEAD = C2` | 对抗镜 B-F1 | **修**（低成本） |
| d | **verify 对着可移动的靶子**：代码审后停止求值 + `opsx:verify` 明文允许「revise design.md to match reality」⇒ design 被改成匹配现实 → verify 拿改写后的 design 核对 → **当然 PASS** | hr-tg H-F4 | **登记残余面**，不修 |

> **推荐 a/b/c 修、d 登记。**
>
> - **a 的修法是零复杂度**：窗口右边界从「最后一个 task 打勾」挪到 **`code-review-report.md` 出现之前**。
>   判据仍是纯盘面、仍全机械（`cr` 文件不存在 = 代码审尚未开始 = 不可能有 `[impl-review-fix]` 合法修订），
>   窗口定义反而更自然。**同时堵住 a 和 c 的大部分。**
> - **b 的修法在本设计下天然可行**：修复先单独 commit → `reviewed_sha` 指它 → 报告单独 commit。
>   因为 code 域比较**排除 `openspec` 条目**，report-only commit 不动非 openspec 顶层条目 ⇒ 不触发失鲜。
>   *（注：design 域天然免疫此问题——其监视集是四件套 + `specs/`，**不含 `spec-review-report.md` 自己**。）*
> - **d 不修的理由**：它是 `opsx:verify` 的流程性质问题（verify 被授权改靶子），不是失鲜判据能解决的。
>   voice 建议的「不可变 approved-design digest」会把刚砍掉的那类机制加回来，与简化方向冲突。
>   **但 design.md 现有的残余面措辞低估了它**——只说「没有门禁记录，只有 git 历史可查」，
>   没说出「verify 会依据改写后的目标判 PASS」这条完整后果链。**MUST 升级措辞。**
>
> **备选（若你要更强保证）**：d 也修，加 approved-design digest。**代价**：新增不可变字段 + 归档前比较，
> 约 +3 tasks，且与「取消补偿机制」的简化方向相悖。

### 🔴 Q3（致）— 回滚不干净：`ship_gate.py` 单文件回滚会打回正常推进中的 change

design.md Migration Plan 把回滚安全性归结为「`reviewed_sha` 对旧 gate 是未知字段」——
**该断言经核实为真**（`:876-877` `if field not in FIELD_ENUMS: continue`，注释写明「非本 schema 字段（外来 metadata），忽略」）。

**但它漏了求值窗口这条核心改动**：旧 gate 在 `:1214` **无条件全阶段求值** design 失鲜。
⇒ 一个 change 在新 gate 下合法推进到代码审/done 期、期间按工作流明文允许修订过四件套，
此时单文件回滚 `ship_gate.py`，旧 gate 会立刻把这些**合法修订**判成「拍板失鲜」→ `REFUSE_START`(exit 3)，
把正常推进中的 change 瞬间打回。这不是「回滚到已知旧缺陷」的正常代价，是**新语义特有、旧语义无对应保护的假阳**。

> **推荐：登记 + 加一条人读约束**（不加代码）。Migration Plan 补一句：
> 「若已有 change 在新 gate 下进入代码审后修订过四件套，回滚 `ship_gate.py` 会使其撞 `REFUSE_START`；
> 回滚前 MUST 人工核验在途 change 的阶段。」**代价**：一句话。
> **备选**：加代码兼容层（后果：为回滚路径养一套双语义，复杂度明显上升，不推荐）。

---

## 自动决策区（D1–D26 · 采纳，落进四件套修订）

### 🔴 致命级

**D1 · 共享 fixture 与新锚模型结构性不兼容**（对抗镜 A-F5，主 session 已完整证实）
`approved_change()`（`test_gate_impl_progress.py:14-28`）把报告 + `proposal.md` + plan 全写完后**一次 `commit_all`**，
且 `repo` fixture 只 `git init`、**无初始提交** ⇒ 那次提交就是根提交
⇒ **不存在先于报告的 HEAD 可填 `reviewed_sha`**（报告与它审查的设计在同一提交里，无法自指出先于自己的锚）——**逻辑必然，非猜测**。
调用点 **44 处**：`test_gate_impl_progress.py` 24 / `test_gate_freshness.py` 13 / `test_gate_namespace.py` 6 / `test_gate_tail.py` 1。
其中 **30 处**（impl_progress + namespace）测的是任务号窗口 / 命名空间隔离等**与失鲜完全无关**的逻辑，
却都要穿过 `:1214`，且落在实现窗口内（不被求值窗口豁免）⇒ fixture 不同步重构，这 30+ 处集体 `UNKNOWN(6)` 失败。
**`tasks.md` 零处提及 fixture 重构。**
→ **新增显式任务**：重构 `approved_change` / `tail_ok` / `impl_done` 为两段提交模型；
MUST NOT 指望 4.13「全套件回归」顺带发现（4.13 是验证步骤，不是设计步骤，到那时返工已发生）。

**D2 · 威胁表两个头号 code 域场景无任何测试任务**（对抗镜 A-F4，主 session 已证实）
design.md 威胁表（`:115-116`）把本 change 要修的头号风险列为「代码审后在 merge 提交里 resolve 出源码改动」
与「`git mv` 把源码迁进 `openspec/`」——**这是 ADR-2「code 域改用 ls-tree 顶层比较」唯一的正面收益证明**。
但 `tasks.md` 对 merge resolve / `git mv` **零处提及**；现存 `test_git_mv_tasks_is_stale_end_to_end` 测的是
**tasks.md（design 域）**，不是 code 域源码外迁。
⇒ **ADR-2 的核心收益，实现完可能从未被验证过。**
→ 4.10 下拆两条显式子项，各自经 `is_stale` 公共入口 + 变异证明。

### 🔴 高

**D3 · `specs/` 子树比较未指定双侧并集枚举**（**三重独立命中**：eng 镜 + design-voice + hr-tg）
只枚举 HEAD 侧 ⇒ 锚有、HEAD 已删的 spec 不出现在枚举里（fail-open）；只枚举锚侧 ⇒ HEAD 新增的被跳过。
→ **采纳并合并 D26 的简化**，一次同时修 bug 且减复杂度。

**D4 · A2「窗口内无合法 churn」被仓内真实历史证伪**（CEO 镜，主 session 全仓重扫 + 时间线逐个核对）
以 `checkpoint(<change>:taskN-*)` ∧ 触碰自身 `design.md`/`proposal.md`/`specs/` 为口径全仓命中 6 个，
逐个核对 `design_approved` 时间线后 **3 个确证反例**（`94c20b79b` 拍板后 **1.6 小时**改 design.md +13/−3；
`55489213a`、`cfb9a670d` 分别 14.9 / 14.6 小时），跨 2 个 change，最近一个在**本 change 起草前一天**；
另 3 个用旧 inline 锚查不到拍板时间、保守不计入。
⇒ **不推翻求值窗口**（这些提交按新设计理应被判失鲜，正是判据要抓的），但推翻「零成本」这个论证。
→ A2 与 ADR-3 措辞 MUST 从「这种情况不存在，所以没有代价」改为
**「存在且不算罕见，我们选择把它拦下、逼回正规流程」**——后者同样支持「不需要逃生口」的结论，且经得起 tasks 5.2 复核。
→ tasks 5.2 执行时 MUST 预先带上这三个反例，不要让实现期子代理从零发现后临场纠结要不要开逃生口。
→ hand-off MUST 登记：「本 change 上线后，历史上出现过的『实现期直接改设计纠偏』模式将被 `REFUSE_START` 拦下，
这是**有意的行为收紧**，不是 bug。」

**D5 · 求值窗口「前移」要拆进 3 个 early-return 分支**（eng 镜 E-F1；CEO F6 同向）
`RUN_SOP`(`:1237`) / `RUN_PLAN`(`:1243`) / `CONTINUE_IMPL`(`:1269`) 分散在三处独立 `emit()`，而 `emit()` 内部
`sys.exit()` 是硬 early-return；现状 design 检查是单一调用点且在三者之前（`:1214`）。
⇒ 挪到三者之后永远到不了，挪到三者之前等于没做窗口限定。
🔴 **实现若走捷径只在 step 7 后加一次检查 ⇒ `RUN_SOP`/`RUN_PLAN` 两条路径完全逃出失鲜检查，方向 fail-open。**
→ tasks 2.5 MUST 拆成显式子项并给实现指引（引 `emit_windowed()` 辅助函数，或先算 tentative verdict 再统一检查）。

**D6 · `reviewed_sha` 与现有 `FIELD_ENUMS` 有限枚举架构不兼容**（eng 镜 E-F2，主 session 已读码证实）
`FIELD_ENUMS` 是三字段有限枚举，`if val not in FIELD_ENUMS[field]` 套不进「任意 40 位 hex」
⇒ 直接加字段的结果是 `out-of-domain`，等价于「**新锚永远读不到**」——**正是 ADR-1 自己点名最该避免的失败模式**。
→ tasks 1.3 MUST 写明：`FIELD_ENUMS` 升级为支持「字段 → 校验函数」，并**显式拆开两层校验**——
语法级（40 位 hex 格式）留在纯文本函数 `parse_ship_gate_frontmatter`（live 读与归档 git-show 文本读共用）；
语义级（commit-object 存在性，如 `git cat-file -e <sha>^{commit}`，确认解析为 commit 而非 blob/tree）
必须在有 `root` 的 `read_reviewed_sha` 里另做一次 git 调用。

**D7 · 退役清单不完整，一整簇 helper 会变悬空引用 / 死代码**（eng 镜 E-F5，主 session 逐符号 grep 证实）
`commit_parents` / `_parent_path_status` / `_plain_content_modification` / `_plain_modification_from_raw` /
`blob_pair` / `design_watched_subs` / `STALE_CATEGORIES` —— **7 项在 tasks/design 中 0 次点名**，
而它们唯一的存在理由就是给帧遍历链条打下手；`design_frame_exempt` 会因所调函数被删而 `NameError`。
→ 组件清单与 tasks 2.6 MUST 扩到完整簇。
✅ **顺带的正面核实（写进实现指引防误删）**：`DESIGN_WATCHED_NAMES`（`:238`）与 `_tasks_content_exempt`
（`:576-595`，签名 `(before_bytes, after_bytes) -> bool`）**可直接复用、无需改动**。

**D8 · ADR-4 用来证成「诊断可退役」的论据本身不成立**（DX 镜 D-F1）
理由是「`git diff <reviewed_sha> HEAD` 一条命令即得」，但三处 stale 的 `emit` 的 `reason`/`extra` 都不含锚值，
四件套通篇也没要求把 `reviewed_sha` 写进 emit ⇒ 撞门者得先开文件抄值。
→ `emit()` 的 `extra` 补 `reviewed_sha`，reason 直接拼出可执行命令。
**不违反 ADR-2/ADR-4 红线**——`reviewed_sha` 是**录下来的常量**，读出来打印零推断成本，与被退役的帧遍历诊断管道性质不同。
✅ **同时确认 ADR-4 的另一半论据成立**：接地镜核实 `:1291`/`:1311` **确实是二元解包丢弃 `trigger`**
⇒「该能力在 code 域从未真正接通过」属实，退役诊断的决定本身没错。

**D9 · `GateIndeterminate` 诊断未强制结构化**（DX 镜 D-F2 + D-F3）
五类失败（git 不在 PATH / 超时 / 锚缺失 / 对象不存在 / 读失败）补救动作**完全不同**，
但 tasks 1.2/3.1/3.4 只说「可读诊断」，spec 四个 Scenario 只锁行为不锁文案。
仓内已有对照先例 `_fail_closed_on_bad(err, label)`（`:956-959`）把 `(field, category)` 结构化后拼进 reason。
→ MUST 要求 `GateIndeterminate` 携带区分五类原因的结构化 payload；`reviewed_sha` 缺失一支单独给针对性措辞
（「该报告产出于本次硬化之前 → 请重跑 sdflow-spec-review 补锚」），**一次写对，不依赖每次有人记得写 hand-off**
（这同时解决 D-F3：tasks 5.3 的迁移提示只写进本 change 的 hand-off，是一次性通知，覆盖不到未来撞门者）。

**D10 · `design_approved` 与 `reviewed_sha` 的原子写入未规定**（对抗镜 B-F2）
tasks 1.1 只说「同批」——是散文措辞，不是硬约束。若拆成两次 Edit 且中断落在中间，
盘面变成「`design_approved: true` 在、`reviewed_sha` 缺」⇒ `design_ok` 判 True 跳过 `REFUSE_START`，
但 `read_reviewed_sha` 抛 `GateIndeterminate` → `UNKNOWN(6)`，**且无任何诊断告诉恢复者缺的是哪个字段**。
→ tasks 补硬约束「MUST 在同一次文件写入中落盘」；该中间态的诊断并入 D9。

**D11 · 人工补锚通道的指引文案未随本 change 更新**（对抗镜 B-F3，主 session 已证实）
`ship_gate.py:1210-1213` 的 `REFUSE_START` 诊断只提 `design_approved`；`tasks.md` 对「补锚 / 越权留痕 / REFUSE_START」**零处**提及。
⇒ 本 change 落地后人工补锚需要**两个**字段，但唯一引导该动作的文本没说，且没告诉人该填哪个 commit
（填错等价于 Q2-c 的信任断裂，且是人工主动引入）。
→ 新增任务：同批更新 `ship_gate.py:1212` 提示文案 + `design.md:227` 及 code-review/done 两处同类文案，
给出「该填哪个 commit」的操作指引。

**D12 · 测试套件 60/115（52%）的命运取决于退役范围，4.12 一句话带过**（对抗镜 A-F3）
34 个直调即将退役的内部 helper；8 个 `tt_*` 就是 BR-7 真值表本体；5 个测 `StaleResult.trigger`/`STALE_CATEGORIES`；
另有 10+ 个 evil-merge / `git mv` 端到端测试——**后者承载的安全承诺在新架构下仍然生效**
（design.md 威胁表第 2 行就点名了 `git mv`），需**重新设计等价用例**而非简单删除。
→ 4.12 MUST 拆成「纯删除清单」与「需重新设计等价用例清单」，后者并入 4.1–4.10 编号体系而非塞进「删除说明」。

**D13 · 4.3 / 4.5 的变异证明不是「可单行删除」的东西**（对抗镜 A-F2）
- 4.3（求值窗口）是**控制流重排**，「删掉窗口」不等于删一行；只把 `if phase in WINDOW` 改成恒 True
  只验证了开关本身，验证不了「阶段判定前移」这个结构改动是否正确落地。
- 4.5（排版提交不移锚）的守卫本体是 ADR-1 的架构决策；新实现里根本没有「反推逻辑」可删，
  唯一「变异」手段是把已退役的 `report_last_sha` **复活**——而这**直接违反 Compliance 的明文 MUST NOT**。
  实现者很可能退化成「改测试 fixture 观察结果变化」，那正是 4.11 明令禁止的形式主义。
→ 4.5 改为「以旧实现为参照物做对比测试」并在 impl-report 说明其证明手段与其余不同源；
4.3 拆成「窗口开关变异」+「前移后判定顺序回归」两部分。

### 🟡 中 / 低

- **D14**（中）· `GIT_*` 清理 MUST 明写 **denylist**（复制 `os.environ` 剔除 `GIT_` 前缀），
  MUST NOT 做 allowlist——后者在 Windows 漏 `SYSTEMROOT`/`COMSPEC` 致子进程启动失败，
  与本仓已踩过的坑同类（本地 macOS 测不出）。测试补「非 `GIT_*` 变量原样透传」方向。（eng E-F4）
- **D15**（中）· 4.6 / 4.9 把多条独立守卫压成一个任务号：4.9 实为 3 helper × 2 异常 + `main()` = 7 组；
  4.6 至少 3 类独立守卫。4.11 的「逐条」在这两处实际是「逐组」，真实变异点位 20+ 组。→ 拆子编号。（对抗 A-F1）
- **D16**（中）· 「MUST 经 `is_stale` 公共入口」与 4.9 冲突：`OSError` 可能发生在 `is_stale` 之外的调用点
  （如 D3 短路分支的 git 调用）。「公共入口」未定义到底指哪一层。→ 明确列举范围，4.9 显式豁免。（对抗 A-F6）
- **D17**（中）· `reviewed_sha` 在 frontmatter 的**挂载位置**无统一模板（嵌套 `ship-gate:` 下 vs 顶层独立键）。
  三处 SKILL 独立编辑，某处写成顶层键则该 producer 的锚永远读不到。→ 给具体 YAML 示例，三处逐字对齐。（对抗 B-F4）
- **D18**（中）· **第二个 frontmatter 消费方未盘点**：`sdflow-done/scripts/roadmap_writeback_draft.py:151-202`
  是独立的 `verify-report.md` frontmatter reader。**已核实对新增字段免疫**（`re.match(r"^\s*verify:\s*(\S+)\s*$")` 只认 `verify:`），
  但组件清单完全没提这个消费方——**基准 3 面治缺口**，且正是 `adr/0011`「MUST grep 列全调用点」要防的
  （讽刺的是本 change 的 ADR 还自评「本轮再次自证其必要」）。→ 组件清单补一行，把隐式假设变显式登记。（对抗 B-F5）
- **D19**（中）· Windows 分发非原子：`setup.sh` Unix 走 `ln -snf`（`:68`，`git pull` 落盘即生效，近乎瞬时一致），
  Windows 走 `cp -r` 逐目录（`:38`/`:53`）；字母序 `sdflow-ship` < `sdflow-spec-review`
  ⇒ 中断会产生「新 gate + 旧 producer」（方向 fail-closed，安全但未登记）。→ Migration Plan 补平台差异说明。（对抗 C-F2）
- **D20**（中）· 消费仓存量规模不可估算：全仓无下游消费仓清单/注册表。
  → hand-off 给消费仓一条**只读自查命令**，列出「本仓有几个 active change 会因 `reviewed_sha` 缺失而 fail-closed」，
  而不是让人逐个撞门才发现代价。（对抗 C-F3）
- **D21**（中）· `sdflow-ship/SKILL.md` 对「失鲜/陈旧/`reviewed_sha`」零命中，tasks 5.1 只要求改
  `ship_gate.py` 头注释。→ 补 `SKILL.md` 链序段说明。
  **不建议**在每次 emit 加运行时提示（逐次加噪声不是本仓风格，参照 T33/T35 软提示惯例）。（DX D-F4）
- **D22**（中）· `_normalize_checkbox_lines` 的**承重程度在新设计下升格**（主 session 独立发现）：
  旧设计里它只是众多判据之一，**新设计里它是 design 域唯一的放行闸门**；
  而它自己就登记着基准 5 警号（T189：「已第 4 轮往同一函数补语法分支」）。
  design.md 登记了 T189 耦合但措辞低估了这个升格。→ 残余面措辞 MUST 升级。**不 fold T189**（独立面，与简化方向冲突）。
- **D23**（中）· **BASE-12 违反**：proposal 自报命中 **TG-23**（≥2 合理方案），但 `三镜 / 主次判定` 全文 grep **零命中**。
  → 至少对 ADR-1、ADR-2 补一句系统镜/用户镜/开发循环镜取舍 + 主次判定（内容其实已隐含在现文字中，只缺显式标签化）。（base 镜）
- **D24**（中）· 🔴 **DOC-1 违反 · 正文残留三处考古层碑文**（base 镜用删除测试逐条论证）：
  - `proposal.md:46`「起草期曾为『后期合法修订』设计过语义分诊 + 重锚协议…已随本条整体取消」
  - `design.md:73`「起草期曾为…一整套补偿机制——语义分诊层 → 重锚协议 → …」（与上条**同一素材第二次复述**，
    且其所在 ADR-3 已有规范的「备选（已否决）」小节承载等价信息 ⇒ 双重违规）
  - `design.md:105`「起草期实证：…」（同一素材第三处，且已在 spec 以规范 Requirement 形式表达）
  - 范围外同源第四处：`CONTEXT.md:289` 术语条目内嵌同一段历史
  → 按 DOC-1 清理进附录或直接删除（ADR 的「备选（已否决）」小节本就是记录被否决方案的规范位置）。
  **自评**：本仓 memory 明确记着我是这条的高发户——「每删一个机制就在正文立碑」。本轮删了一整套补偿机制，立了三块碑。
- **D25**（低）· `sdflow-init update` 对本 change **无效**（`ship_gate.py` 与三个评审 SKILL 都不在
  `sdflow-init/assets/workflow/` bundle 内，只由全局 `setup.sh` / `/sdflow-upgrade` 分发）。
  design/proposal 命令写对了，但 hand-off 未显式复述这条本仓历史高发混淆点。→ tasks 5.3 补一句。（对抗 C-F4）
- **D26**（低 · **减法**）· 🟢 **`ls-tree -r` 比 `path→oid` 映射**（主 session 提出并**实测验证**）：
  `ls-tree -r` 输出为 `mode type oid\tpath`，**天然含 mode 与 type**，正好一次覆盖 hr-tg 要求的
  「存在性、对象类型、mode、内容」四者。实测五格全绿：新增 ✅ / 删除 ✅ / rename（内容不变）✅ / 内容改动 ✅ / **无改动 → fresh 无假阳** ✅。
  → design 域改为两侧各一次 `ls-tree -r <ref> -- proposal.md design.md specs/` 比映射，
  **同时修掉 D3 的三重命中缺陷**；git 调用 **8–10 次 → 4 次**（`tasks.md` 仍需 2 次 `git show` 走 checkbox 归一化）；
  顺带把最坏等待从 ~4–5 分钟压到 ~2 分钟（并入 DX D-F5：ADR-5 应写出这个数量级，**不改 `timeout=30` 本身**——
  其判据「文件系统卡死线，非性能预算」是对的，与 `buglist.py` 先例一致，接地镜已逐字核实该注释原文）。

**其余低优先完备性缺口（base 镜，一并采纳）**：BASE-21 补一句合规声明（「不涉及 PII」）；
BASE-17 把 `CONTEXT.md` 术语条目补进 proposal Impact；BASE-19 补一张「阶段 × 域 × 是否求值」ASCII 图；
接地镜 G：`tasks.md` 覆盖图漏 `4.13`（图 12 项 vs 列表 13 项）。
**BASE-20 / BASE-22 / BASE-29**（利益相关方表 / proposal 混入实现细节 / 契约 scope-check 表）→ **defer**，
理由：本 change 规模下形式收益低于维护成本，且 base 镜自评「可选、非阻塞」。

---

## 已裁掉区（反静默压制 · 原始发现 + 裁掉理由，供人复核裁得对不对）

**X1–X4 · 接地镜的四条「代码未实现」误报**

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | 「`read_reviewed_sha()` 函数完全缺失」 | **本 change 尚在设计审阶段**，该函数正是设计要新增的东西（design.md 组件清单标注为「新增」） |
| X2 | 「三个 git helper 缺 timeout 与异常捕获」 | 同上——这正是 P1 要做的改动 |
| X3 | 「`run_git` 系列缺 env 清理」 | 同上——ADR-6 要做的改动 |
| X4 | 「`main()` 缺顶层异常处理」 | 同上——tasks 3.4 要做的改动 |

> 🔴 **这不是接地镜的错，是我的 prompt 缺陷**：我写了「核对代码事实是否真实存在且一致」，
> **没写「设计要新增的东西当然不存在，不要当缺陷报」**。
> 而这是上一轮 grounding 镜**同一失效模式的第二次复发**（上一轮它的 5 条 findings 也多为
> 「把设计但未实现误报为不符」）——**属于评审工作流自身的可改进点，已如实登记。**
>
> **接地镜的本职部分全部有效且有价值**：组件清单所有符号 ✅ 存在且描述准确；`:1214`/`:1291`/`:1311` 三个行号 ✅ 精确；
> **`:1291`/`:1311` 确实是二元解包丢弃 `trigger`**（⇒ 支撑 ADR-4 的退役决定，见 D8）；
> `buglist.py` timeout 注释、`opsx/verify.md:99` 引文 ✅ 逐字准确；A5/A6 ✅ 属实。
> 它还独立发现了覆盖图漏 `4.13`（已采纳）。

---

## 镜阵效能观察（供 `/sdflow-retro` 聚合，非本轮决策）

| 镜 | findings | 采纳 | 独立 | 备注 |
|---|---|---|---|---|
| adversarial ×3 | 16 | 16 | **16** | 三个角度（验证计划 / producer 侧 / 迁移回滚）**零重叠**，独立率 100%；3 条致命里出了 3 条 |
| broad（CEO/eng/DX） | 11 | 11 | 10 | 出 A2 证伪与 FIELD_ENUMS 不兼容两条关键 |
| domain（base 清单） | 6 | 5 | 5 | DOC-1 三处碑文是它独家 |
| outside-voice ×2 站点 | 7 | 4 | 2 | 两站点**各自独立命中** `specs/` 枚举侧（与 eng 镜构成三重命中）；归档终态盲区是其独家 |
| grounding | 5 | 1 | 1 | 4 条误报（见 X1–X4，prompt 缺陷）；本职核验全对 |

**最强信号**：`specs/` 双侧枚举被 **3 个互不可见的 fresh context 各自命中**（eng 镜 + 两个 voice 站点）。
**对抗镜差异化角度设置有效**：Step1 五个来源全都没碰「验证计划本身」，而对抗镜 A 从那个角度挖出两条致命。

---

## 拍板记录（设计 HARD-GATE）

**设计门已拍板批准，日期 2026-07-21。** 机判锚见本文件头部 frontmatter `ship-gate.design_approved: true`。

三个 `[需拍板]` 项的最终去向：

| # | 最终裁决 | 落点 |
|---|---|---|
| **Q1** | **不做**（用户裁定：verify 检查点到 merge 之间本无其他动作，无须再查） | 无 |
| **Q2** | **a 不改**（用户纠正：code-review 过程中本就可能改代码与文档，`code-review-report.md` 出现之前不是合法右边界；窗口维持原定义，间隙登记为残余面 + 语义层第二道）；**b 修**（→ ADR-7(a)）；**c 降级为流程纪律**（不改 gate，改为「拍板前先跑窄复核」+ ADR-7(b) 二次修订须单独提交）；**d 登记残余面并升级措辞** | design.md ADR-7 / tasks 1.7b |
| **Q3** | **登记 + 人读约束**（Migration Plan 补一句：回滚前 MUST 人工核验在途 change 阶段） | design.md Migration Plan |

窄复核（`edefe35`）已跑，3 条真发现（1 致 2 高）全部返修落盘；机械门（`openspec validate`、通则 sync、覆盖图双向一致、退役簇闭包）全绿。**本记录本身即 ADR-7(b) 的首次实践**：被审四件套已于 `5f54da0` / `edefe35` 单独提交，∴ 此刻写入的锚指向已包含全部批准内容的提交。

### ⚠️ 〔SR-M〕lens-metric 门后重算 —— 本轮**未执行**，诚实登记

锚行区的 6 条 `lens-metric` 仍是 **Step3 的 pre-gate 临时值**。原因：`lens_metric_emit.py` 是**全 roster 一次性确定性归约**，重算需要原始的 45 条 finding hit 集作输入，而**该输入 JSON 从未落盘**（SKILL 只要求「构造 → 调 emitter → 落 stdout」，未要求持久化）。反推一份能复现已知输出的输入即是编造；手改 emitter 产出的锚行则绕过了机械层。∴ 两条路都不走，如实标注。

**若执行，本应发生的 delta（仅两行，供人工复核）**：

| 行 | 字段 | pre-gate | 门后应为 | 触发 |
|---|---|---|---|---|
| `outside-voice / design-voice` | 采纳/裁掉/defer | 2 / 0 / 1 | 2 / **1** / **0** | V-F1（Q1）被裁定不做 |
| `outside-voice / hr-tg` | 采纳/裁掉/defer | 2 / 0 / 2 | **3** / **1** / **0** | H-F1（Q1）裁掉；H-F4（Q2d）采纳为残余面登记 |

**影响面**：`/sdflow-retro` 的采纳率/独立率聚合会把本 change 的两条 outside-voice 行按 pre-gate 值计入（低估采纳率、高估 defer 率）。这正是 SKILL 里已声明的「best-effort、无机械兜底」局限的一次真实兑现——**根因是 emitter 输入不持久化，使 SR-M 在结构上不可执行**，已记 todo。

---

## 收敛口（拍板前的原始建议，保留供审计）

**不建议现在进设计 HARD-GATE。** 建议顺序：

1. 你先拍 **Q1 / Q2 / Q3** 三个问题（每个都已带推荐 + 依据 + 代价 + 备选）。
2. 我按拍板结果 + D1–D26 做一轮四件套修订（**其中 26 条是把已定决定写对、1 条是减法、2 条是零成本改时序**）。
3. 修订后**无需再跑一轮全量多镜**——本轮已把设计面、验证面、producer 面、迁移面各审过一遍；
   修订属于「按已确认结论落文字」。但 **MUST 跑一次窄复核**盯接缝（本仓实证：返修最易在
   「扩枚举不回改派生判据」「解耦函数不解耦输入数据」这类接缝处引入新洞）。
4. 窄复核绿 ⇒ 进 HARD-GATE 拍板 ⇒ 回写 `ship-gate.design_approved` frontmatter + 最终化 lens-metric 锚。
