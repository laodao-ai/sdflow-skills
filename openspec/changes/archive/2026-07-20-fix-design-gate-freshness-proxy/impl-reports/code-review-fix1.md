# code-review fix1 —— 设计门 fail-open 一批（F1–F5）

冷层代码审（5 镜 + 2 跨模型 voice）挖出的 fail-open 缺陷修复。方向铁律：**任何「看不清 / 判不了」一律判失鲜**。

改动文件：
- `sdflow-ship/scripts/ship_gate.py`（F1/F2/F3/F5）
- `sdflow-implement/scripts/impl_route.py`（F4）
- `sdflow-ship/tests/test_gate_freshness.py`、`sdflow-implement/tests/test_impl_route.py`（新增用例）
- `sdflow-ship/tests/fixtures/tickets_plan_nested_fence.md`（新增判别性 fixture）

代码注释一律标 `[impl-review-fix]`（F1–F4 各带条目号）。

---

## F1（致命）帧枚举面 —— 三洞同根，一次扫全

**根**：`is_stale` 的 design 分支用 `git log {sha}..HEAD --name-only` 枚举每帧触及路径。这个协议同时有三个洞，且都在**触及豁免判据之前**就让整帧被 `if not subs: continue` 静默跳过。

| 洞 | 机理 | 后果 |
|---|---|---|
| F1-a | `--name-only` 不带 `-m/--cc` 时对 merge commit **不输出任何文件** | evil-merge（改动只存在于 merge 自身 resolve 出的树）判 fresh；且 Task1 的逐 parent 校验成为生产路径死代码 |
| F1-b | 默认开 rename 检测，`git mv` 只输出目标路径 | 源 `tasks.md` 逃出监视集 → 判 fresh，**直接违反本 change 的 delta spec** |
| F1-c | 文本行协议承载文件名（按行切 + C-quote） | 含 Tab / 换行的路径逃出 `startswith(base)` |

**修法（面治，不逐点补）**：把「分帧」与「帧内触及路径」拆成两跳。

1. 分帧：`git log {sha}..HEAD --format=%H%x1f%s`（只取 sha + subject，subject 保证单行）。
2. 路径：新增 `frame_touched_paths(root, sha)` → `git diff-tree -m -r --raw --no-renames -z --no-commit-id --root <sha>`。
   - `-m` merge 输出**相对每个 parent** 的 diff（补 a）
   - `--no-renames` 改名分解 A+D，源路径与目标路径**都**进枚举（补 b）
   - `-z` NUL 分隔的原始路径，零引号零转义（补 c）
   - `--root` 根提交也能枚举（否则又一处空集静默跳过）
   - 读不到 / 输出形态不是 `:meta\0path\0…` ⇒ 返回 `None` ⇒ 调用方保守判失鲜

**为什么不能塞进同一次 `git log`**：`-z` 的 NUL 与 `--format` 的帧分隔符会互相污染（旧协议正是用 `%x00` 分帧）。拆两跳后各自协议无歧义，代价是窗口内每帧一次 `diff-tree`（窗口 = 设计审报告提交之后的提交，量级小）。

**BR-6 护栏**：未加 `--no-merges` / `--first-parent`。`-m` 是**多输出** merge 的 per-parent diff，不删任何提交、不改变遍历的提交集合，与 BR-6「merge 内部提交逐一枚举不漏检」方向一致。这条区分已逐字写进 `frame_touched_paths` 的 docstring，防后人误读为违规。

### 连带修复：per-parent 四态（unchanged ≠ unfit）

F1-a 修好后 merge 帧**第一次**被真正枚举出来，立刻暴露旧的二值 `_plain_content_modification`：它把 "unchanged"（该 parent 侧此路径无改动）和 "unfit"/"error" 一起折叠成 `False`。于是**普通 merge**（side 改了 tasks.md、main 没改）相对 side-parent 为「无改动」→ 被误判 `shape-unfit` → **假失鲜**。

⇒ 拆出 `_parent_path_status()` 四态：`unchanged` / `plain` / `unfit` / `error`。`unchanged` 跳过该 parent（该侧没有引入任何设计改动，与豁免无关），`unfit`/`error` 照旧保守。`_plain_content_modification` 保留为它的 bool 视图（单一源），既有直调用例不动。

> 该假失鲜是**唯一**一条既有用例转红（`test_merge_commit_pure_flip_not_stale`，assert code==0）。它不是被证伪的假绿，也没有改断言——断言逐字未动，改的是代码。同时该用例的注释「本例并没有验到 merge 帧逐 parent 求值（--name-only 对 merge 恒空 ⇒ 直接跳过）」随本次修复而**不再成立**，已订正为「普通 merge 的逐 parent 求值不产生假失鲜」的钉子。

### Task1 逐 parent 校验现已生产可达

`test_merge_frame_pure_flip_is_exempt_end_to_end` 走 `run_gate` 端到端、不打任何替身：merge 提交自身做纯勾选框翻转、对**每个** parent 都成立 ⇒ `CONTINUE_IMPL`。与 `test_evil_merge_*` 成对，证明「豁免在 merge 上真能生效」而非「见 merge 就一刀切」。

---

## F2（高）帧枚举失败被当成 fresh

枚举那一步仍走 `run_git`（非零退出返空串）⇒ `git log` 失败 ⇒ 零帧 ⇒ `return (False,"fresh")`。Task1 只把 blob 读取换成了 `run_git_rc`，枚举这一半漏了。

**修法**：枚举改用 `run_git_rc` 显式判 returncode，失败 ⇒ 判失鲜，分类原因 `frame-enum-failed`（新增进 `STALE_CATEGORIES`，与既有四条同源登记）。`frame_touched_paths` 返回 `None` 走同一分类。

`report_last_sha` 失败落 `uncommitted`（人机同权）**未动**，按指示只修枚举这一条。

---

## F3（高）归一化漏了 CommonMark 缩进代码块 + HTML 注释块

`_normalize_checkbox_lines` 认 ` ``` ` 与 `~~~` 两族围栏，但**四空格缩进代码块**与**多行 HTML 注释块**内的 `- [ ] → - [x]` 仍被归一化 ⇒ 误判豁免（fail-open）。这是同一个有界面的第三、四支。

**修法**（两者都是有界词法，可手写；见 CLAUDE.md 基准 5）：

- 缩进代码块：新增 `indent_columns()` / `is_indented_code_line()`，判据 = **行首缩进 ≥4 列**（tab 按 4 列制表位展开）。这是 CommonMark 缩进代码块的**必要条件 = 超集**——精确判定依赖段落连续性与列表上下文（**无界**，禁手搓），故取超集，方向恒 fail-closed。
  - **代价（显式登记）**：缩进 ≥4 列的**真嵌套任务项**翻转也判失鲜（假失鲜，保守方向，接受）。本仓 tasks.md 的嵌套项惯用 2 空格，实际不触。
  - MUST NOT 为消掉这类假失鲜而引入列表上下文推断——那正是无界解析面。
- HTML 注释块：新增 `HtmlCommentTracker`（`<!--` / `-->` 配对，HTML 里 `<!--` 不嵌套 ⇒ 有界）。`feed()` 返回**该行行首**是否已在注释内（行锚定复选框只需要行首状态）。误判「在注释内」只会少归一化 ⇒ 多判失鲜，方向同样 fail-closed。

**优先级固定**：fence > comment/indent。围栏内的 `<!--` 不开注释、围栏内缩进行不另判（`test_fence_wins_over_comment_and_indent` 锁死）。

**未扩散**：两道闸门只加在 `_normalize_checkbox_lines`（豁免面）。MUST NOT 顺手推到 `_parse_plan` / `tg02_hit` / `_line_scoped_hits`——那三处的安全方向各不相同，改动须各自论证。已写进文件头「已知不覆盖」。

---

## F4（高）单一源没同步到姊妹解析器

`impl_route.parse_blocked_by` 头注释明写「口径与 `ship_gate._parse_plan` 一致（`line.lstrip().startswith("```")`）」——但 gate 已收敛进 `FenceTracker`（同种 + 长度 ≥ 开启符 + 尾部校验），手抄副本没跟上，**那句注释是假的**。

**修法**：`impl_route` 直接 import `ship_gate.FenceTracker`（单一源），删掉手抄副本。

**定位方式与理由（判据）**：`Path(__file__).resolve().parents[2] / "sdflow-ship" / "scripts"`。两种安装形态都成立——symlink 安装时 `resolve()` 落回仓内；Windows copy 安装时两个 skill 目录在 `~/.claude/skills/` 下互为兄弟。**没有**抽第三个共享模块：它没有 `SKILL.md`，`setup.sh` 不装它 ⇒ 两种形态下反而都找不到。

**fail-closed**：引不到 ⇒ `parse_blocked_by` 直接 `TopoError`，MUST NOT 回退手抄副本（口径漂移正是本条要根治的病）。

**「gate 零改动铁律」**：本次改的是 impl_route 单向**读** gate 的纯词法函数，不改 gate 任何判定、不产生反向依赖。文件头已把该铁律的措辞从「不读、不改」订正为「**不改**」并说明例外。

**判别性 fixture**（新增 `sdflow-ship/tests/fixtures/tickets_plan_nested_fence.md`）：外层 ` ````markdown ` 内嵌 ` ```text ` 示例块。实测口径分叉：

```
NEW gate  ids ['1','2']  boxes {'1':[True],'2':[False]}
NEW route ids {1, 2}
OLD 手抄口径 ids [1, 2, 9]  boxes 4      ← 内层 ``` 提前关掉外层，多认一个伪 Task 9 + 2 个伪复选框
```

两边各一条回归用例（gate 侧 `test_nested_example_fence_hides_pseudo_task_and_checkboxes`，route 侧 `test_nested_example_fence_agrees_with_gate_cross_script`）+ 一条单一源机械守（`test_fence_lexer_is_the_single_source_from_ship_gate`：`ir._FenceTracker is sg.FenceTracker`）。

---

## F5（高）文件头契约未同步

`ship_gate.py` 文件头 D9 新鲜度契约只写了 subject 精确式豁免。已补：

- 「例外一〔B2/BR-7〕subject 精确式」+「例外二〔内容判据〕纯勾选框翻转」并列，例外二写全边界：只 `tasks.md`、只勾选框、只普通内容修改、归一化排除 fence/缩进代码块/HTML 注释、merge 须每个 parent 成立、任何看不清一律回落失鲜；并记帧枚举协议与 F2。
- 「已知不覆盖」区：
  - 原「evil-merge 因 `--name-only` 不产 merge diff 而漏检」标注**已修**，并显式登记**code 域仍走 `--name-only`**（本轮判据逐字不动）⇒ code 域的 evil-merge 漏检**依旧存在**，待后续。
  - 新增 F3 超集闸门条目（含「真嵌套任务项假失鲜」这一代价、以及 MUST NOT 推到另三个 fence 调用点）。

---

## 变异验证（每道新守护删掉 ⇒ 对应用例转红）

全部实跑，输出如下。

### M1 —— F1 枚举协议回退到 `--name-only`
```
FAILED test_gate_freshness.py::test_evil_merge_design_edit_is_stale            (F1-a)
FAILED test_gate_freshness.py::test_evil_merge_tasks_semantic_edit_is_stale    (F1-a)
FAILED test_gate_freshness.py::test_merge_frame_is_actually_enumerated         (F1-a)
FAILED test_gate_freshness.py::test_git_mv_tasks_is_stale_end_to_end           (F1-b)
FAILED test_gate_freshness.py::test_frame_paths_include_rename_source          (F1-b)
FAILED test_gate_freshness.py::test_spec_path_with_tab_is_stale                (F1-c)
FAILED test_gate_freshness.py::test_frame_paths_preserve_tab_unquoted          (F1-c)
7 failed, 276 passed in 23.94s
```
三个子洞各自被独立用例钉住，无一靠其它用例连带。

### M2 —— F2 枚举失败不再判失鲜
```
FAILED test_gate_freshness.py::test_stale_when_commit_enumeration_fails
FAILED test_gate_freshness.py::test_stale_when_frame_path_enumeration_fails
2 failed, 348 passed in 23.94s
```

### M3 —— F3 缩进 + HTML 注释闸门删除
```
FAILED test_gate_freshness.py::test_content_stale_on_indented_code_block_flip
FAILED test_gate_freshness.py::test_content_stale_on_tab_indented_code_block_flip
FAILED test_gate_freshness.py::test_content_stale_on_html_comment_block_flip
3 failed, 347 passed in 23.93s
```

### M4 —— per-parent `unchanged` 折回 `shape-unfit`（旧二值口径）
```
FAILED test_gate_freshness.py::test_merge_commit_pure_flip_not_stale
1 failed, 349 passed in 23.63s
```

### M5 —— impl_route 退回手抄围栏口径
```
FAILED test_impl_route.py::test_nested_example_fence_agrees_with_gate_cross_script
E  Extra items in the right set: 9        ← 伪 Task 9 复活
1 failed, 349 passed in 24.65s
```

---

## 新增用例清单

**`sdflow-ship/tests/test_gate_freshness.py`**（新增一节，全部走 `is_stale` / `run_gate` 端到端，不打替身）

| 用例 | 守什么 |
|---|---|
| `test_evil_merge_design_edit_is_stale` | F1-a：merge 自身 resolve 出未批准 design.md ⇒ REFUSE_START |
| `test_evil_merge_tasks_semantic_edit_is_stale` | F1-a 的 tasks.md 分支（语义改动）⇒ content-changed |
| `test_merge_frame_pure_flip_is_exempt_end_to_end` | 反向证：merge 纯勾选翻转对每 parent 成立 ⇒ 不失鲜（Task1 逐 parent 生产可达证据） |
| `test_merge_frame_is_actually_enumerated` | 机械守协议：merge 触及路径非空；对照旧 `--name-only` 恒空 |
| `test_git_mv_tasks_is_stale_end_to_end` | F1-b：`git mv tasks.md` ⇒ 失鲜（补上既有用例只直调 `blob_pair` 的假绿） |
| `test_frame_paths_include_rename_source` | 机械守：源路径与目标路径都在枚举里 |
| `test_spec_path_with_tab_is_stale` | F1-c：`specs/` 下 Tab 文件名 ⇒ 失鲜 |
| `test_frame_paths_preserve_tab_unquoted` | 机械守 `-z`：路径原样、无 C-quote |
| `test_stale_when_commit_enumeration_fails` | F2：`git log` 失败 ⇒ 失鲜 |
| `test_stale_when_frame_path_enumeration_fails` | F2：`diff-tree` 失败 ⇒ 失鲜 |
| `test_frame_touched_paths_returns_none_on_git_failure` | 坏 sha ⇒ None（不当空集） |
| `test_frame_enum_failed_is_registered_category` | 分类枚举与判定分支同源 |
| `test_content_stale_on_indented_code_block_flip` | F3：四空格缩进代码块 |
| `test_content_stale_on_tab_indented_code_block_flip` | F3：tab 制表位展开 |
| `test_content_stale_on_html_comment_block_flip` | F3：多行 HTML 注释块 |
| `test_normalize_still_works_outside_indent_and_comment` | 判别性反向证：浅缩进 / 注释块外照常豁免（非「见就全拒」） |
| `test_html_comment_tracker_reports_line_start_state` | 注释状态机行首语义 |
| `test_indent_columns_tab_stop` | 制表位口径 |
| `test_fence_wins_over_comment_and_indent` | 三者优先级固定 |
| `test_nested_example_fence_hides_pseudo_task_and_checkboxes` | F4 gate 侧回归 |

**`sdflow-implement/tests/test_impl_route.py`**

| 用例 | 守什么 |
|---|---|
| `test_fence_lexer_is_the_single_source_from_ship_gate` | 机械守 `ir._FenceTracker is sg.FenceTracker`（手抄副本回来即红） |
| `test_nested_example_fence_agrees_with_gate_cross_script` | 两解析器对同一 plan 的段落边界一致 |

**新增 fixture**：`sdflow-ship/tests/fixtures/tickets_plan_nested_fence.md`

---

## 未修 / 显式登记

1. **`code` 域的 evil-merge 漏检**：按约束「`code` 域失鲜判据逐字不动」，`is_stale` 的 `scope == "code"` 分支仍走 `git log --name-only`，故 F1-a 在 code 域**依旧存在**。已写进文件头「已知不覆盖」。若要一并治，是下一票（判据面不同，须独立论证 `-m` 对 code 域「触及 openspec/ 之外路径」语义的影响）。
2. **换行文件名用例**：只做了 Tab（同一个协议面：文本行协议 + C-quote）。换行文件名在本地 git / 文件系统上构造不便，且与 Tab 共用同一条 `-z` 修复路径，判别性不增。已在用例注释里说明。
3. **F3 的假失鲜代价**：缩进 ≥4 列的真嵌套任务项翻转会判失鲜。方向保守、显式登记，MUST NOT 用列表上下文推断去消（无界面）。
4. **BR-7 精确式 subject 豁免**逐字未动（已登记的接受取舍，本轮不动）。

---

## 收尾

- `python3 -m pytest sdflow-ship/tests/ sdflow-implement/tests/ -q` ⇒ **350 passed**
- 仓根全套件 `/usr/bin/python3 -m pytest -q`（rootdir 钉在仓根，`pytest.ini` / `conftest.py` 未动）⇒ **2036 passed, 8 skipped, 3 xfailed**
- 顺带消除 `ship_gate.py:3` 的 `DeprecationWarning: invalid escape sequence \s`（文件头新增文字改引 `CHECKBOX_RE_PATTERN` 常量名，不再内嵌正则字面量）
