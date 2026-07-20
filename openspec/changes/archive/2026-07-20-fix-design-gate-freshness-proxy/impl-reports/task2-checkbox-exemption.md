# Task 2 impl-report — 纯勾选框翻转不再撞门

**R-ID:** SW-1 · **文件:** `sdflow-ship/scripts/ship_gate.py` / `sdflow-ship/tests/test_gate_freshness.py`

## 做了什么

把 Task 1 留下的占位 `_tasks_content_exempt(before, after)`（恒 `False`）实现掉——这是本 change 的 P0
交付，也是 Task 2 唯一需要动的判据面。上游 `design_frame_exempt` 的编排、`blob_pair` 的读取保真、
`design_watched_subs` 的监视集单一源、BR-6 逐 parent 求值**逐字未动**。

新增两个函数：

| 函数 | 职责 |
|---|---|
| `CHECKBOX_BYTES_RE` | `CHECKBOX_RE`（`^\s*-\s+\[([ xX])\]`）的字节版，口径逐字相同 |
| `_normalize_checkbox_lines(raw)` | 原始字节 → 归一化后的**行列表**；围栏未闭合返回 `None` |
| `_tasks_content_exempt(before, after)` | 两侧归一化 → 行数相等 → **按行号位置对齐**逐行等值 |

**判据形状**（design.md ADR-1 求值口径）：

- **归一化只替换标记本身**：`CHECKBOX_BYTES_RE.match(line)` 命中后，用 `m.start(1)` 定位那**一个**
  字符，`line[:i] + b" " + line[i+1:]`。缩进、标记后空白、行内其余字符逐字节保留。
- **行首锚定**：正则 `^` 锚定 ⇒ 表格单元格、行内反引号、散文字面量、以及同一行**第二个之后**的
  标记一律不动。
- **fence 感知**：`line.lstrip().startswith(b"```")` 翻转 `in_fence`——**复用仓内既有口径**
  （`_line_scoped_hits` / `_parse_plan` 同一行），未另造一套。fence 内的行原样入列。
- **围栏未闭合 ⇒ 返回 `None` ⇒ 调用方判失鲜**：EOF 时 `in_fence` 仍为真，则「哪些行在 fence 内」
  本身不可信，保守方向。
- **切行用 `split(b"\n")` 而非 `splitlines()`**：后者还在 `\r` 处切开，CRLF↔LF 会被抹平。前者把 CR
  留在行尾，行尾差异与末尾换行增删都保持可区分。
- **🔴 位置对齐，禁 LCS**：`len` 不等直接 False，其余 `all(x == y for x, y in zip(nb, na))`。
  MUST NOT 用 `difflib`——LCS 下纯行重排的删除行与插入行逐字节相同，会被判等值而放行。

## 关键实现选择及理由

| 选择 | 理由 |
|---|---|
| **全程在 bytes 上做，不解码** | 判据的输入是 `blob_pair` 的原始字节（Task 1 为此专门建了 `run_git_bytes`）。任何 `.decode()` 都可能在非 UTF-8 tasks.md 上抛异常或替换成 U+FFFD 使两版趋同——那正是 Task 1 花力气堵掉的假等值面，判据端不能从后门放回来。 |
| **`m.start(1)` 单字符替换，而非 `re.sub` 整体重写** | `re.sub` 需要重构造整行，容易顺手规范化空白；单字符切片替换在结构上不可能碰到标记以外的字节。 |
| **归一化统一成 `[ ]`（而非 `[x]`）** | 任意一侧都可以，只要对称。`[X]` 与 `[x]` 同归一 ⇒ 大小写变体也算纯翻转。 |
| **围栏未闭合返回 `None` 而非 `False`** | `None`/行列表两种返回类型让「不可信」与「归一化结果」在类型上就分开，调用方不会把空列表误当合法结果。 |
| **不引入 `difflib` / 不做 markdown 结构解析** | design.md Compliance 明文禁止；且这是基准 5 的典型无界语法面——一旦开始解析 markdown 结构，就进了「每轮 review 补一个新语法分支」的补丁循环。行级等值是有界的。 |

**Non-Goals 遵守**：未做任何内容感知豁免（措辞/注释/格式化一律照判失鲜）；`code` 域逐字未动；
BR-7 精确式 subject 豁免逐字未动（`test_e2e_br7_impl_review_subject_exemption_intact` 机械守，
本票不定义它与内容豁免的优先级——那是 Task 3）。

## 测试

新增 21 条用例（`sdflow-ship/tests/test_gate_freshness.py` 第 ⑦ 节 + 第 ⑥ 节改写），
`E = _sg._tasks_content_exempt` 为单元入口。

### 行为翻转的既有用例（Task 1 的「行为不变」锚，本票按设计翻转）

| 旧名（Task 1 期望失鲜） | 新名（Task 2 期望豁免） |
|---|---|
| `test_design_frame_exempt_never_exempts_in_task1` | `test_design_frame_exempt_true_on_pure_checkbox_flip` |
| `test_tasks_only_checkbox_flip_still_stale` | `test_tasks_only_checkbox_flip_not_stale` |
| `test_tasks_flip_plus_source_code_still_stale` | 🔴 `test_tasks_flip_plus_source_code_not_stale`（主用例） |
| `test_merge_commit_touching_tasks_still_stale` | `test_merge_commit_pure_flip_not_stale` |

### 每条验收标准的证据锚点

| 验收标准 | 锚点 |
|---|---|
| 正例：监视集内只触及 tasks.md、只翻勾选 ⇒ 不失鲜 | `test_tasks_only_checkbox_flip_not_stale`、`test_design_frame_exempt_true_on_pure_checkbox_flip`、`test_content_exempt_forward_flip`、`test_content_exempt_multi_line_partial_flip` |
| 🔴 正例（主用例）：同帧既纯勾选 tasks.md、又改仓库别处源码 ⇒ 不失鲜 | `test_tasks_flip_plus_source_code_not_stale`（`git add -A` 打包形态） |
| 正例：`[x]` 翻回 `[ ]`（反向）⇒ 不失鲜 | `test_content_exempt_reverse_flip_is_symmetric`；大写变体 `test_content_exempt_uppercase_marker` |
| 归一化仅替换标记本身，不触碰缩进/空白/其余字符 | `test_content_exempt_preserves_indent_and_spacing`（**双向断言**：缩进不同 ⇒ False；缩进相同 ⇒ True，排除「有缩进就拒」蒙对） |
| 归一化锚定行首；fence 内不参与 | `test_content_stale_on_fenced_code_block_flip`、`test_content_stale_when_second_marker_on_same_line_flips_back` |
| 负例：fence 内翻转 ⇒ 失鲜 | `test_content_stale_on_fenced_code_block_flip`；围栏未闭合 `test_content_exempt_conservative_on_unbalanced_fence` |
| 负例：表格 / 行内反引号 / 散文字面量 ⇒ 失鲜 | `test_content_stale_on_table_and_inline_code_literals`、`test_content_stale_on_prose_literal_marker` |
| 负例：同行多标记，task marker 与文档字面量反向翻转 ⇒ 失鲜 | 🔴 `test_content_stale_when_second_marker_on_same_line_flips_back`（判别性构造：全行替换下两版会被抹成同一串） |
| 负例：纯行重排（零字符改动）⇒ 失鲜 | 🔴 `test_content_stale_on_pure_line_reorder`（含前提校准断言 `sorted(before.split) == sorted(after.split)`，确证多重集相同、差异纯为顺序） |
| 负例：勾选框 + 同行措辞 ⇒ 失鲜 | `test_content_stale_on_flip_plus_same_line_wording`、端到端 `test_e2e_tasks_wording_change_still_stale` |
| 负例：勾选框 + 新增/删除任务段 ⇒ 失鲜 | `test_content_stale_on_flip_plus_task_section_added`、`..._removed`、`test_content_stale_on_line_count_change_alone` |
| 负例：只改缩进 / 空白 ⇒ 失鲜 | `test_content_stale_on_whitespace_only_change` |
| 负例：CRLF↔LF、末尾换行增删、首尾空白 ⇒ 失鲜 | `test_content_stale_on_crlf_and_trailing_newline_and_edge_whitespace`（四条各自独立断言） |
| 负例：同帧触及 tasks.md（纯勾选）+ design.md ⇒ 失鲜 | `test_e2e_flip_plus_design_edit_still_stale`（端到端 exit 3 / REFUSE_START）+ 既有 `test_design_frame_exempt_false_when_other_watched_path_touched` |
| BR-7 精确式 subject 豁免未被弄坏 | `test_e2e_br7_impl_review_subject_exemption_intact` + 既有 `test_impl_review_exempt_bare_and_colon` / `..._evil_suffix_stale` / `..._fix_variant_stale` 全绿 |

### fixture 修正：`_reanchor`

端到端正例最初**全部红**，理由不是判据错，而是 fixture 的窗口边界：`_seed_tasks` 里**新建**
tasks.md 的那一提交本身落在 design 锚之后的窗口内，而「新建」形态不合格 ⇒ 该帧先于待测的翻转帧
触发失鲜，把用例的通过/失败理由整个换掉。新增 helper `_reanchor(repo, d)`（重提交
`spec-review-report.md`——它不在 design 监视集内）把锚推到 HEAD，让窗口内只剩待测帧。
这是前提校准，不是放宽断言：修正后 M-A/M-B 变异仍能把这几条打红（见下表），说明区分力在。

## 变异验证实际执行记录

逐条**实际执行**（改源 → 跑 `test_gate_freshness.py` → 记录转红用例 → `git checkout` 还原）。
🔴 前置教训：首轮做变异时实现尚未 commit，`git checkout --` 把实现本身一并回滚，导致 M-B 的
观测被污染（unit 用例陪红）。改为**先 commit 实现再变异**后重跑，下表为重跑后的干净结果。

| 变异 | 结果 | 转红用例 |
|---|---|---|
| **M-A** 删内容判据（`_tasks_content_exempt` 恒 `False`） | ✅ 9 failed | `test_design_frame_exempt_true_on_pure_checkbox_flip`, `test_tasks_only_checkbox_flip_not_stale`, `test_tasks_flip_plus_source_code_not_stale`, `test_merge_commit_pure_flip_not_stale`, `test_content_exempt_forward_flip`, `..._reverse_flip_is_symmetric`, `..._uppercase_marker`, `..._multi_line_partial_flip`, `..._preserves_indent_and_spacing` |
| **M-B** 删监视集限定，改按**整 commit 文件列表**求值（`set(frame_files) != {base+"tasks.md"}`） | ✅ 4 failed | 🔴 **`test_tasks_flip_plus_source_code_not_stale`**（ticket 点名的那颗钉子）, `test_design_frame_exempt_true_on_pure_checkbox_flip`, `test_tasks_only_checkbox_flip_not_stale`, `test_merge_commit_pure_flip_not_stale` |
| **M-C** 删 fence 感知（去掉围栏翻转与 in_fence 跳过 + 去掉未闭合回落） | ✅ 2 failed | `test_content_stale_on_fenced_code_block_flip`, `test_content_exempt_conservative_on_unbalanced_fence` |
| **M-D** 删行首锚定（改 `line.replace(b"[x]", b"[ ]")` 全行替换） | ✅ 3 failed | `test_content_stale_on_table_and_inline_code_literals`, `test_content_stale_on_prose_literal_marker`, `test_content_stale_when_second_marker_on_same_line_flips_back` |
| **M-E** 位置对齐改 LCS（🔴 构造敏感，唯一有判别力的形态 = `difflib.SequenceMatcher` 收集非 equal 区块后**比较删除行/插入行多重集**；详见下方订正表） | ✅ 1 failed | `test_content_stale_on_pure_line_reorder`（报错行直呈 `True = E(b'- [ ] a\n- [x] b\n', b'- [x] b\n- [ ] a\n')`——即 LCS 下重排被判等值放行） |

**〔fix1 M3 订正〕M-E 的构造敏感，原描述过弱、易被读成「随便换个 difflib 写法都能转红」。
实测（fix1 轮复跑，两种构造各跑一次全 sdflow-ship 套件）：**

| M-E 构造 | 结果 | 说明 |
|---|---|---|
| `return difflib.SequenceMatcher(None, nb, na).ratio() == 1.0` | ❌ **238 passed，不转红** | ratio() 只是相似度；重排两版 ratio < 1.0 ⇒ 仍返回 False（判失鲜）⇒ 与正确实现同结论，**零区分力** |
| 收集非 equal 区块的**删除行/插入行多重集**并比较：<br>`for tag,i1,i2,j1,j2 in SequenceMatcher(None,nb,na).get_opcodes(): if tag!="equal": dels+=nb[i1:i2]; ins+=na[j1:j2]`<br>`return sorted(dels)==sorted(ins)` | ✅ **1 failed** | 这才复现 LCS 误判机制（「删除行与插入行逐字节相同」）⇒ `test_content_stale_on_pure_line_reorder` 转红，报错行直呈 `True = E(b'- [ ] a\n- [x] b\n', b'- [x] b\n- [ ] a\n')` |

**结论：只有多重集形态对「位置对齐 vs LCS」这道守护有判别力。** 记录在此：不为凑数放宽变异，
构造不对就换构造；也不许拿无区分力的构造冒充「变异已验」。

## 全套件结果

- `pytest sdflow-ship/tests/` — **217 passed**（Task 1 收尾 197 → 本票 +20）
- 仓根 `/usr/bin/python3 -m pytest` 全套件 — **1964 passed, 8 skipped, 3 xfailed**（123.60s），零 failure（Task 1 收尾 1944 → 本票 +20）
- 每次变异还原后均复跑确认回绿

## Concerns

1. **`test_merge_commit_pure_flip_not_stale` 的区分力主要落在 side 分支的普通提交上。**
   `git log --name-only` 对 merge 提交默认不列文件，故 merge 帧的 `subs` 为空、直接跳过；真正被判定的
   是被逐一枚举的 side 提交（BR-6 承诺的「merge 内部提交逐一枚举」正是如此）。**「merge 提交本身
   逐 parent 求值」这条路径在端到端层仍只由 Task 1 的 `test_exempt_requires_every_parent_of_a_merge`
   （带替身）覆盖**，本票未新增不带替身的端到端 merge-frame 用例——显式登记，不冒充有守。
2. **围栏未闭合的保守回落是本票自加的**（ticket 未列）。方向与全篇一致（看不清 ⇒ 失鲜），且有
   `test_content_exempt_conservative_on_unbalanced_fence` + M-C 变异守着；但它扩大了「判失鲜」的
   面，若下游发现 tasks.md 常态带未闭合围栏，会表现为豁免不生效。
3. **判据不看行的语义角色。** 一行若同时是 task marker 又承载设计信息（例如把 `- [ ] 做 A` 改成
   `- [x] 做 A`，而「做 A」这条任务的含义在别处被重定义），判据看不见——这是 design.md Non-Goals
   明确划走的语义面，正解是 `checkpoint(impl-review)` subject 声明式豁免，非本票范围。
