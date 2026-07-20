# Task 6 — 面治扫描与全套件收敛（SW-1）

**结论先行**：面治扫描**未发现需在本 change 内处理的新豁免形态** ⇒ 本票**零代码改动**，是登记票。
变异矩阵 9 条全部**复跑核实**（非誊抄），全部转红。全套件 **2014 passed / 8 skipped / 3 xfailed，
零 failure、零 warning**。

---

## 1. 面治扫描（design 域监视集全体成员）

**监视集**（`ship_gate.py:222` + `design_watched_subs`）：`proposal.md` · `design.md` · `tasks.md` ·
`specs/` 前缀。

**扫描问题**（逐成员 × 逐形态）：除已豁免的勾选框翻转外，是否还存在**其他「零设计信息量」的改动
形态**——即改了它但**不可能**让 implementer 做出任何不同的事？

**两道闸门**（承 CLAUDE.md 基准 1 + 基准 5）：
① **确定性信号闸门** — 该形态有无可机械判定的信号？无 ⇒ 出局（语义面不开补丁循环）。
② **零信息量闸门** — 目标态下该形态是否**真的**不改变 implementer 读到的内容？

**判据锚目标态，不锚现状语料**（通则③）：下表每一格问的是「**目标态 producer 会不会产出这个形态**」，
不是「现存 change 目录里出现过没有」。

### 1.1 目标态 producer 枚举（扫描的事实底座）

先核实「谁会在设计门窗口 `[design-approved 锚提交, HEAD]` 内写这四个成员」——这决定了哪些形态
**在目标态下真会发生**：

| producer | 写哪个成员 | 形态 |
|---|---|---|
| `sdflow-done` 步 0.3「tasks.md 复选框对账」（SKILL.md:118） | `tasks.md` | 勾选框翻转 —— **已由 ADR-1 豁免** |
| `checkpoint(impl-review)` 协议下的评审后修订 | 任意成员 | 任意 —— **已由 BR-7 subject 通道豁免** |
| implementer 子代理 | **无** —— Task5 信号权威表正面声明「设计阶段已定稿，实现期不是它们的作者」 | — |
| **任何脚本 / 格式化器 / 生成器** | **无** | — |

最后一行是**实测核实**，不是推断：`sdflow-*/scripts/*.py` 全量 grep 写入点，**无一** 写入
`openspec/changes/{change}/` 下的 `proposal.md` / `design.md` / `tasks.md` / `specs/`；唯一触及
`tasks.md` 的脚本是 `sdflow-done/scripts/roadmap_writeback_draft.py:206`，它**只读**复选框计数。
仓内亦无 markdown formatter / pre-commit hook / lint 自动改写（`.github/workflows/` 两个 workflow
均不改写四件套，无 `.pre-commit-config.yaml`、无 `.husky`）。

> **∴ 目标态下，四件套的机械churn源为零**——一切改动都来自「有人（人或 agent）编辑了它」。
> 这是下表 F3/F4/F7 判「拒」的决定性依据，而非「现存语料里没见过」。

### 1.2 逐形态判定表

| # | 候选形态 | 闸门① 确定性信号 | 闸门② 真零信息量 | 判定 |
|---|---|---|---|---|
| **F1** | **勾选框翻转 @ `tasks.md`** | ✅ 行级归一化后逐行等值，有界 | ✅ 已证（A2：完成判据只读 `superpowers-plan.md` 分段复选框 + `checkpoint(<change>:task<N>-<slug>)` 标签） | **✅ 已豁免（ADR-1，Task2 落地）** |
| **F2** | **勾选框翻转 @ `proposal.md` / `design.md` / `specs/`** | ✅ 同上，信号一样有界 | ❌ **未被证明** | **拒** |
| **F3** | 注释 / 措辞 / 错别字 | ❌ | ❌ | **拒（Non-Goal，已拍板）** |
| **F4** | 纯空白 / 缩进 / 行尾空格 | ✅ 字节可比 | ❌ | **拒** |
| **F5** | EOL（CRLF↔LF）/ 文件末尾换行增删 | ✅ 有界（CR/LF/CRLF 三种，数得完） | ⚠️ 语义上确为零，但**目标态无 producer** | **拒** |
| **F6** | 纯行重排（段落 / 任务顺序调换） | ✅ 可判定 | ❌ | **拒（且已是正向决策）** |
| **F7** | 新建 / 删除 / 改名 / 复制 / 类型变更 / 仅权限位 | ✅ `git diff --raw` status + mode | ❌ | **非候选（已一律判失鲜，方向正确）** |
| **F8** | 生成式内容（TOC / 索引 / 自动回填） | — | — | **目标态 producer 不存在 ⇒ 无此形态**；登记为 watch item |

### 1.3 逐条判据（表格「拒」的理由，逐条落档）

**F2（勾选框 @ 其余三成员）—— 本轮扫描里最接近采纳线的一条，仍拒。**
A2 证明的是「**gate 的完成判据**不读 `tasks.md`」。这条证明**不可迁移**到 `proposal.md` /
`design.md` / `specs/`：这三者的内容**就是 implementer 的施工图**，其上任何一行的改动都可能改变
施工结果——包括一个勾选框（例如 `specs/` 里以复选框形式列出的验收项，勾与不勾对应「该项是否在本次
交付范围内」）。豁免它等于把 ADR-1「豁免面精确等于已证零信息量的那个集合——**不多一寸**」直接
破掉。
**目标态补强**：四件套模版本就不含完成度复选框；且实现期 implementer 按 Task5 权威表 MUST NOT
写设计工件 ⇒ 目标态下无 producer 产出这个形态。
（现状语料佐证、**不作判据**：`openspec/changes/` 活跃 + archive 全量扫，`design.md` / `proposal.md`
/ `specs/**` 无一含行首 task-list 复选框。）

**F4（纯空白 / 缩进）—— 闸门②硬性不过。**
CommonMark 里空白**承载语义**：缩进决定列表嵌套层级与缩进代码块归属，**行尾两个空格 = 硬换行**。
「哪一类空白是无义的」这个问题无法在不解析 markdown 结构的前提下回答——而 design.md Compliance
**明令** 「MUST NOT 解析 markdown 结构」。强行做即基准 5 的无界语法面补丁循环。

**F5（EOL / 末尾换行）—— 闸门②语义上过，但目标态 producer 不存在，且代价方向不对。**
三条依次收敛：
1. **目标态无 producer**（§1.1 实测）：管线里没有任何东西会单独改写行终止符。EOL 变化只会**伴随
   「有人编辑了这个文件」一起出现**——而那一刻文件里另有实质差异，照判失鲜正是对的。
2. **豁免它要在字节比较上再加一维归一化**，而这维正是 **Task1 刻意关掉的假等值面**：`run_git_bytes`
   存在的全部理由就是不走 `text=True` + `errors="replace"` + `.strip()` 那条路（四者各自可造假
   等值，其中一条逐字就是「CRLF↔LF 不可分辨」）。加回 EOL 归一化 = 从后门重开 Task1 焊死的洞。
3. **代价方向是 fail-closed**：误报的后果 = 重跑一次设计门，而非放行未批准内容。与 ADR-1「代价
   （显式接受）」同一条逻辑。

**F6（纯行重排）—— 不是漏网，是已做出的正向决策。**
`_tasks_content_exempt` **按行号位置对齐**（`zip`），并在 docstring 里明令 MUST NOT 用 LCS/difflib
——理由逐字：LCS 下纯行重排的删除行与插入行逐字节相同，会被判等值而放行。任务顺序调换是**真实的
设计改动**（执行次序变了）。守护锚：`test_content_stale_on_pure_line_reorder`（变异 M-E 复跑转红，见 §2）。

**F7（非普通内容修改形态）—— 已由 Task1 形态闸门一律判失鲜，方向正确。**
`_plain_modification_from_raw` 要求 `status == "M"` 且 `src_mode == dst_mode`。理由逐字：此类形态下
前后两版 blob 字节**可能完全相同**（chmod、regular↔symlink），拿字节等值当「没实质改动」会放行真实的
状态位变更。∴ 这是**反向**候选（该判失鲜而不是该豁免），不属本次扫描要找的东西。

**F8（生成式内容）—— 目标态下不存在，登记为 watch item。**
§1.1 已实测：无脚本写入四件套。**若将来引入**任何回写四件套的机械 producer（如自动回填 spec 索引），
它会产出一个新的、有确定性信号的零信息量形态 ⇒ **须另开 change 重评本表**，MUST NOT 在那时顺手扩
`_tasks_content_exempt`（那正是基准 5 警号说的「每轮 review 补一个新分支」）。

### 1.4 扫描结论

**已扫全 4 个成员 × 8 类形态，无新形态需在本 change 内处理。** 豁免面维持 ADR-1 划定的
「`tasks.md` × 勾选框翻转」一格，不多一寸。本票零代码改动。

> **落档位置说明**：ticket 允许「有则落进 `design.md` 的取舍登记」。本次结论为「无新形态」，
> 且 `design.md` 本身在 design 域监视集内——实现期改它会触发设计门失鲜（同 Task4 不改 `specs/`
> 的理由）。∴ 结论落在本报告，**未改 `design.md`**。F8 watch item 若日后转为实需，随那次 change
> 一并入 `design.md` 取舍登记。

---

## 2. 变异矩阵（**复跑核实**，非誊抄）

**方法**：脚本逐条改源 → 跑 `sdflow-ship/tests/test_gate_freshness.py`（Task5 那条跑
`sdflow-implement/tests/`）→ 记录 FAILED 名单 → 还原源文件。**9 条全部实际执行**（ticket 要求
≥5 条实跑）。还原后 `git status --porcelain` 空。

| 守护（来源票） | 变异手法 | 结果 | 转红用例（节选） |
|---|---|---|---|
| 内容判据本体（T2 M-A） | `_tasks_content_exempt` 首行 `return False` | **14 failed** | `test_design_frame_exempt_true_on_pure_checkbox_flip`、`test_tasks_only_checkbox_flip_not_stale`、`test_content_exempt_forward_flip` … |
| 监视集限定 vs 整 commit 文件列表（T2 M-B） | 改按 `set(frame_files) != {base+"tasks.md"}` 求值 | **11 failed** | 🔴 `test_tasks_flip_plus_source_code_not_stale`（`git add -A` 打包形态的那颗钉子）、3 条 `test_stale_trigger_category_*` |
| fence 未闭合保守回落（T2 M-C，**本轮细化**） | 删 `if fence.inside: return None` | **2 failed** | `test_content_exempt_conservative_when_cross_type_fence_cannot_close`、`..._when_shorter_fence_cannot_close` |
| 行首锚定（T2 M-D） | 改全行 `line.replace(b"[x]", b"[ ]")` | **4 failed** | `test_content_stale_on_table_and_inline_code_literals`、`..._on_prose_literal_marker`、`..._second_marker_on_same_line_flips_back`、`test_checkbox_str_vs_bytes_nbsp_divergence_is_conservative` |
| 位置对齐 vs LCS（T2 M-E） | difflib 删除行/插入行**多重集**比较 | **1 failed** | `test_content_stale_on_pure_line_reorder` |
| blob 双侧 rc 显式检查（T1 M1） | 删 `if rc_before != 0 or rc_after != 0` | **3 failed** | `test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes`、`..._on_one_side_...`、`test_stale_trigger_category_blob_unreadable` |
| 通道 A：subject 精确式豁免（T3 M2） | 精确式分支整体换 `pass` | **4 failed** | `test_impl_review_exempt_bare_and_colon`、`test_e2e_br7_impl_review_subject_exemption_intact`、`test_tt_exact_subject_semantic_exempt_by_subject`、`test_exact_subject_short_circuits_before_any_blob_read` |
| 默认处置只推重跑设计门（T4 ③） | 指引里混入 `checkpoint(impl-review)` | **1 failed** | `test_default_disposition_recommends_rerun_design_gate_only` |
| dispatch 信号权威表在场（T5 变异1） | 删 SKILL.md 必含槽内整个权威表块 | **2 failed** | `test_dispatch_carries_signal_authority_table`、`test_authority_table_matches_gate_consumed_criteria` |

**9/9 全部转红，无一条无区分力。**

### 2.1 与前序报告记录的核对（一处需订正，非缺陷）

- **转红条数普遍多于前序记录**（M-A 9→14、M-B 4→11、M-D 3→4）：属**正常超集**——Task3/Task4 在
  Task2 之后又新增了真值表 8 格与 4 条分类诊断用例，它们同样依赖这些守护。不是记录错误。
- 🔴 **一处归因订正**：`task2-checkbox-exemption.md` 把
  `test_content_exempt_conservative_on_unbalanced_fence` 记为 M-C 的转红用例。**本轮细化复跑证伪
  该归因**：M-C 在 Task2 报告里是**合并变异**（同时删 fence 追踪 + 删未闭合回落）；本轮把变异**收窄
  到只删未闭合回落**后，该用例**不转红**——因为它的构造
  `E(b"```\n- [ ] s\n", b"```\n- [x] s\n")` 在「块内行不归一化」这条**另一道**守护下就已经判不等值了，
  对「未闭合回落」这一分支**没有区分力**。
  **不构成缺口**：该分支由 fix1 轮新增的 `..._when_cross_type_fence_cannot_close` /
  `..._when_shorter_fence_cannot_close` 两条**实际杀掉**（本轮实测）。仅归因记录不精确，在此订正。

---

## 3. 全套件

```
/usr/bin/python3 -m pytest -q      （仓根，pytest.ini + conftest.py 未改）
→ 2014 passed, 8 skipped, 3 xfailed in 126.89s
```

- **零 failure、零 warning**（无 warnings summary 段）。
- skip 数 8 与 Task4/Task5 报告记的 9 差 1：来自本机环境依赖的磁盘满用例（`skipif` 本地专属，
  见 commit `91bc707`），**与本 change 无关**，非新增 skip。
- 每次变异还原后 `git status --porcelain` 为空，工作树干净。

---

## 4. hand-off：生效条件（显著声明）

> 🔴 **本修复不会自动到达消费仓。** 分发路径 = 本仓 push → 运行 checkout
> （`~/.skills/sdflow-skills`）`git pull` → **`bash setup.sh`**（软链 + `~/.sdflow/` canonical 刷新）。
> 一键入口 = **`/sdflow-upgrade`**。
>
> **在消费仓跑 `/sdflow-upgrade` 之前，那里的 `/sdflow-ship` 仍会在每次勾 `tasks.md` 后撞
> `REFUSE_START`** —— 症状与修复前逐字相同，极易被误判为「没修好」。
>
> 另注 pull→setup 的**窗口期纪律**（CLAUDE.md dev/runtime checkout 纪律）：pull 与 setup 之间
> 勿跑阶段三。

**`proposal.md` Impact 段已有此声明**（`proposal.md:48`：「分发：经 `setup.sh` 软链到
`~/.claude/skills` / `~/.codex/skills`，消费仓跑 `/sdflow-upgrade` 后生效」）—— **已确认在场，未补写**。

---

## 5. 遗留 / 交棒

1. ~~**Task4 已登记的 spec 冲突仍未解**~~ 〔impl-review-fix：**本条系过时误述，已订正**〕
   本票原文称 `specs/spec-workflow/spec.md` 的 `Scenario: 失鲜 REFUSE_START 须携带触发点与处置指引`
   「仍写着 MUST 提 `checkpoint(impl-review)` 通道」——**该冲突早在 commit `e2d7f80` 已修复**
   （经 `checkpoint(impl-review)` 声明通道提交，正是该豁免的正确用法：事前、受控、用在会触发
   失鲜的那个提交自身上）。当前 spec:138 写的是「默认处置指引 MUST 只推荐重跑设计门一条；
   `checkpoint(impl-review)` MUST NOT 出现在默认处置指引中」，与实现一致。
   `tasks.md:16` 的同类残留亦已于 `d02b03d` 一并清除，四件套已全文复扫、零违规。

   **本条误述的成因值得记一笔**：本票照抄了 `task4-stale-diagnostics.md` 尾部**当时**的登记，
   未核当前盘面——正是本 change 反复踩的「自述不可当证据」面。**交棒给 done 时 MUST NOT
   把本条当作待处理项。**
2. **F8 watch item**：将来若引入任何回写四件套的机械 producer，须**另开 change 重评 §1.2 全表**，
   MUST NOT 顺手扩 `_tasks_content_exempt`。
3. `task2-checkbox-exemption.md` Concern 1（不带替身的端到端 merge-frame 用例缺口）本票未动——
   它是显式登记的已知边界，不在 SW-1 面治范围（那是覆盖度问题，不是豁免形态问题）。
