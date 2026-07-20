# Task 2 修复轮 fix1 — 双轴审 FAIL 的 2 Important + 4 Minor 全修

上游：`98dc7c5`（Task 2 实现）+ `9015c1e`（首轮报告）。本轮**不覆盖**首轮报告，只在其 M-E 行做订正（M3）。
改动严格限于 ticket 列出的条目：`code` 域失鲜判据、BR-7 精确式 subject 豁免**逐字未动**；
未引入 `--no-merges` / `--first-parent`；归一化仍只认行首复选框标记这一个词法。

---

## Important-1 — `~~~` 围栏漏识 ⇒ 假阳放行（**面治**）

### 病灶

仓内 fence 追踪惯用法 `line.lstrip().startswith("```")` 被**手抄 4 处**，全部只认 ``` ：

| 调用点 | 旧口径失效方向 |
|---|---|
| `_normalize_checkbox_lines`（勾选框豁免） | **fail-open** — `~~~` 块内实质改动被当块外纯勾选翻转 ⇒ 放行未批准的设计改动 |
| `_line_scoped_hits`（归档 verify 锚读） | **假 SHIPPED** — `~~~` 块内的示例锚被当真锚计入 |
| `_parse_plan`（plan 复选框/Task 标题） | **假 ✅** — `~~~` 块内伪 `[x]` 计入完成、伪 `### Task N:` 误判重号 |
| `tg02_hit`（TG-02 头部声明区） | 假 RUN_SOP — `~~~` 块内示例声明串被计入 |

复现（修前）：`_tasks_content_exempt(b"~~~\n- [ ] s\n~~~\n", b"~~~\n- [x] s\n~~~\n")` → **True**（放行）。

### 修法（单一源 + CommonMark 有界词法）

`ship_gate.py` 新增**唯一**围栏识别源，四处调用点全部改调它，无一保留手抄：

- `fence_delim(line: str) -> (char, count, tail) | None`
- `fence_delim_bytes(line: bytes)` — **只做形态转换**（`decode("latin-1")` 字节保序、零信息损失）后委派给
  `fence_delim`。**不是手抄副本，是同一份实现的两个入口** ⇒ 结构上不可能口径分叉；
  另有 `test_fence_delim_bytes_delegates_to_str_single_source` 机械守这条委派关系。
- `FenceTracker` — 逐行状态机，`feed(line)` 返回「本行是否是围栏行本身」，`inside` 表示块内，EOF 时
  `inside` 即 unbalanced。

口径按 CommonMark **有界**词法写全（CLAUDE.md 基准 5 明列 fence 变体为「有界 ⇒ 可手写解析」正面例子）：
开启符 = 行首（去 ASCII 空白）连续 **≥3** 个同种 `` ` `` 或 `~`；闭合符须**同种** + 长度 **≥** 开启符 +
其后只余空白。故 ``` 关不掉 `~~~`（反之亦然）、三 backtick 关不掉四 backtick 开的块、带 info string 的行
不能当闭合符。**MUST NOT 由此扩到 markdown 其它结构**（表格 / 嵌套列表 / 引用块 = 无界面）——已在
模块头注释与 helper 注释两处写死这条边界。

模块头注释里那条「`~~~` 围栏不特判、方向=安全侧假阴」的旧承诺已删改为新口径（该承诺本身在勾选框
豁免落地后已**不成立**——它的失效方向变成了 fail-open；ticket 通则 ③：不拿「现有口径本来就这样」辩护）。

### 行为变化方向

更多东西被认作「在围栏内」⇒ 归档读更易 `none`/`unbalanced`、plan 解析更易 `UNKNOWN`、豁免更易判失鲜。

> 🔴 **本节原写「一律 fail-safe」，该表述不准确**（由 re-review 指出，`fix2` 一并修正）。**须分调用点看**：
> `_normalize_checkbox_lines` / `_parse_plan` / `_line_scoped_hits` 三处把 `fence.inside`(EOF) 作为
> unbalanced 上报给调用方做保守处理，**方向确为 fail-safe**；但 `tg02_hit` 当时**直接吞掉返 `False`**，
> 「更易认作围栏」在该点意味着**更易吞掉头部声明行 ⇒ 更易 `SKIP_SOP`**，**方向是 fail-open**。
> 本次扩口径（`~~~` 与任意长游程）**放大了**这个既有洞。修法见
> `task2-checkbox-exemption-fix2.md`（`tg02_hit` 循环后补 `if fence.inside: return True`）。

**既有 217 条 sdflow-ship 用例、仓根全套件零转红**（见下）。

### 每个调用点各自举证（不只测一处）

| 调用点 | 新增用例（文件） |
|---|---|
| `_normalize_checkbox_lines` / `_tasks_content_exempt` | `test_gate_freshness.py`：`test_content_stale_on_tilde_fenced_code_block_flip`（🔴 Important-1 复现钉）、`..._four_backtick_fenced_flip`、`..._tilde_fence_with_info_string`、`test_content_exempt_conservative_on_unbalanced_tilde_fence`、`..._when_cross_type_fence_cannot_close`、`..._when_shorter_fence_cannot_close`、`test_normalize_still_works_outside_tilde_fence`（反向证：不是「见 ~ 就全拒」蒙对的） |
| `_line_scoped_hits` | `test_gate_anchor_scope.py`：`test_line_scoped_tilde_fence_hides_anchor`、`..._four_backtick_fence_hides_anchor`、`..._tilde_fence_not_closed_by_backticks`、`..._short_fence_cannot_close_longer_one`、`..._info_string_line_is_not_a_closer`、`test_fence_delim_bytes_delegates_to_str_single_source` |
| `_parse_plan` + `tg02_hit` | `test_gate_impl_progress.py`：`test_t34_tilde_fenced_checkbox_not_counted`、`..._tilde_task_header_in_fence_not_counted`、`test_t34_unclosed_tilde_fence_unknown`、`test_t34_backtick_cannot_close_tilde_fence`、`test_tg02_tilde_fenced_example_in_header_not_hit`、`test_tg02_tilde_fenced_heading_in_header_still_hits` |

---

## Important-2 — `CHECKBOX_BYTES_RE` 手抄副本无机械守 + 注释不准确

- **改为单一源派生**：新增 `CHECKBOX_RE_PATTERN = r"^\s*-\s+\[([ xX])\]"`；
  `CHECKBOX_BYTES_RE = re.compile(CHECKBOX_RE_PATTERN.encode())`、`CHECKBOX_RE = re.compile(CHECKBOX_RE_PATTERN)`。
- **机械守**：`test_checkbox_re_bytes_derived_from_single_source` 断言
  `CHECKBOX_BYTES_RE.pattern == CHECKBOX_RE.pattern.encode()` 且 `CHECKBOX_RE.pattern == CHECKBOX_RE_PATTERN`。
- **注释订正**（删掉不准确的「口径逐字相同」）：写清 `\s` 在 str 模式认 Unicode 空白（NBSP U+00A0）、
  bytes 模式**只认 ASCII**（tab 认、NBSP 不认）；差异方向 = bytes 侧**少归一化** ⇒ NBSP 缩进的复选框行
  翻转不被豁免 ⇒ 判失鲜 ⇒ **保守，可接受**。该差异由
  `test_checkbox_str_vs_bytes_nbsp_divergence_is_conservative` 机械锚住（含 tab 对照 + 端到端 `E(...) is False`）。

---

## Minor

- **M1**（`test_gate_freshness.py` 三条端到端正例）：`verdict != "REFUSE_START"` → **`code == 0 and verdict == "CONTINUE_IMPL"`**
  （实测真值）。旧弱断言下 `UNKNOWN(6)`（门崩了）也满足，会被读成「门放行了」。
  涉及 `test_tasks_only_checkbox_flip_not_stale`、`test_tasks_flip_plus_source_code_not_stale`、`test_merge_commit_pure_flip_not_stale`。
- **M2**（`test_merge_commit_pure_flip_not_stale` 注释名不副实）：注释改为说实话——该用例**没有**验到
  「merge 帧逐 parent 求值」（merge 提交自身不改 tasks.md ⇒ 其帧 `subs` 为空被直接跳过，真正被求值的是
  side 分支上那个单 parent 普通提交）；逐 parent 的判别性用例是 `test_exempt_requires_every_parent_of_a_merge`。
  保留本例的理由（守 merge 拓扑不致端到端误判失鲜）也一并写进注释。**只改注释，未改断言语义**
  （断言按 M1 强化为确切值）。
- **M3**（首轮报告 M-E 变异描述过弱）：在 `task2-checkbox-exemption.md` 加订正表，**两种构造各实跑一次**：
  `ratio() == 1.0` → **238 passed，零区分力**；收集非 equal 区块比较**删除行/插入行多重集** → **1 failed**
  （`test_content_stale_on_pure_line_reorder`）。结论写死：只有多重集形态对这道守护有判别力。

---

## 变异验证（全部实跑，输出如实记录）

基线：`/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` → **238 passed**。

| # | 变异 | 结果 | 转红用例 |
|---|---|---|---|
| **M1** | 删 `~~~` 支持（`_FENCE_CHARS = ("`",)`） | ✅ **10 failed, 228 passed** | `test_line_scoped_tilde_fence_hides_anchor`, `test_line_scoped_tilde_fence_not_closed_by_backticks`, `test_content_stale_on_tilde_fenced_code_block_flip`, `test_content_stale_on_tilde_fence_with_info_string`, `test_content_exempt_conservative_on_unbalanced_tilde_fence`, `test_t34_tilde_fenced_checkbox_not_counted`, `test_t34_tilde_task_header_in_fence_not_counted`, `test_t34_unclosed_tilde_fence_unknown`, `test_tg02_tilde_fenced_example_in_header_not_hit`, `test_tg02_tilde_fenced_heading_in_header_still_hits` —— **三个调用点各自独立转红**（freshness / anchor-scope / impl-progress 三个文件都在内） |
| **M2** | 闭合符不校验同种/长度/尾部（`if ch == och and n >= on and not tail.strip():` → `if True:`） | ✅ **6 failed, 232 passed** | `test_line_scoped_tilde_fence_not_closed_by_backticks`, `test_line_scoped_short_fence_cannot_close_longer_one`, `test_line_scoped_info_string_line_is_not_a_closer`, `test_content_exempt_conservative_when_cross_type_fence_cannot_close`, `test_content_exempt_conservative_when_shorter_fence_cannot_close`, `test_t34_backtick_cannot_close_tilde_fence` |
| **M3** | `CHECKBOX_BYTES_RE` 改回手抄副本并微漂口径（`-\s*\[` 代替 `-\s+\[`） | ✅ **1 failed, 237 passed** | `test_checkbox_re_bytes_derived_from_single_source` |
| **M4** | 位置对齐改 LCS（多重集形态，见 M3 订正表） | ✅ **1 failed, 237 passed** | `test_content_stale_on_pure_line_reorder` |
| **M4′** | 同上但用 `ratio() == 1.0` | ❌ **238 passed（零区分力）** | —— 反面对照，已写入首轮报告订正表 |

每次变异后均 `cp /tmp/sg.bak` 还原并复跑确认回到 238 passed。

## 全套件结果

- `/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` — **238 passed**（首轮 217 → 本轮 +21）
- 仓根 `/usr/bin/python3 -m pytest -q` — **1985 passed, 8 skipped, 3 xfailed**（125.04s），零 failure
  （首轮 1964 → +21）。**无任何既有用例转红**，未改动任何既有断言以迁就（M1 是**加强**断言，不是放宽）。

## 残留 / 诚实边界

- 本轮把 fence 词法收敛到 CommonMark 的**有界**子集（fence 类型 + 长度 + 尾部空白）。CommonMark 里
  「开启符前最多 3 空格缩进」这条**未实现**——沿用仓内既有的「无限量 ASCII 空白 lstrip」，且与四个
  调用点修前行为一致。刻意不动，避免把有界修补扩成 markdown 结构解析。
  **该差异的方向须分调用点写**（原文笼统写「更保守 / fail-safe」，不准确，由 re-review 指出）：
  「更容易认作围栏」在 `_normalize_checkbox_lines` / `_parse_plan` / `_line_scoped_hits` 三处
  = 更易 unbalanced/UNKNOWN/隐藏锚 ⇒ **确为 fail-safe**；但在 `tg02_hit` 处
  = **更易吞掉头部声明行 ⇒ 更易 `SKIP_SOP`，方向是 fail-open**。
  该风险自 `fix2` 起被 `tg02_hit` 末尾的 `if fence.inside: return True` 兜住
  （吞掉声明行的前提是围栏未闭合，此时一律保守判命中），但**表述本身不许笼统说「一律保守」**。
- `_line_scoped_hits` 对 `~~~` 块的处理是**隐藏锚**（更易判 `none`），归档侧从「假 SHIPPED」翻成
  「判定不能」——符合 ADR-5「宁可判定不能也不假阳」。
