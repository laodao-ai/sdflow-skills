# Task 1 impl-report — 设计门能看见内容，且看不清时一律保守判失鲜

**R-ID:** SW-1 · **文件:** `sdflow-ship/scripts/ship_gate.py` / `sdflow-ship/tests/test_gate_freshness.py`

## 做了什么

给 `is_stale(scope="design")` 装上两项它此前没有的能力，并把「看不清」的方向一律钉死在**判失鲜**一侧：

1. **区分「本帧落在 design 域监视集内的触及路径集」与该提交的完整文件列表**——新增纯函数
   `design_watched_subs(frame_files, base)`。
2. **取到指定提交前后两版 `tasks.md` 的原始字节**——新增 `run_git_bytes`（原始字节读取）
   + `tasks_blob_pair`（前后两版 + 形态资格 + 双侧 rc 检查）+ `commit_parents`（逐 parent）。
3. `git log` format 由 `%x00%s` 扩为 `%x00%H%x1f%s`，让每帧携带自身 sha（无 sha 就取不到 blob）。

**本票不引入任何豁免。** `design_frame_exempt` 的判据入口 `_tasks_content_exempt(before, after)`
在本票恒返回 `False`，因此对外可观察行为与本票之前**逐字一致**——一切情形仍照判失鲜。

## 关键设计选择及理由

| 选择 | 理由 |
|---|---|
| **`cat-file blob` 而非 `show`** 读前后两版 | `show` 的输出受 smudge/textconv 过滤器影响，同一 blob 在不同 config 下可读出不同字节；`cat-file blob` 是 object 原始字节。实测本机全局 `core.autocrlf=input` 会在 **commit 时**清掉 CRLF（那发生在 blob 生成前，读取端无从补救）——但读取端本身必须零转换。 |
| **`run_git_bytes` 全新一条路径，不复用 `run_git`/`run_git_rc`** | 后两者 `text=True` + `errors="replace"` + `.strip()`，四者各自可造假等值（吞首尾空白、吞末尾换行、CRLF↔LF 不可分辨、非 UTF-8 → U+FFFD 后两版趋同）。变异 M12 实证：把读取换回文本路径 ⇒ 两条保真用例转红。 |
| **形态资格闸门**（`_plain_modification_from_raw`） | 新建/删除/改名/复制/类型变更/仅权限位这些形态下，前后两版 blob 字节**可能完全相同**（chmod、regular↔symlink），纯字节等值会把真实的状态位变更读成「没实质改动」。 |
| **把 raw 行解析抽成纯函数** | 首轮变异验证发现 `status == "M"` 与行形校验在 git 驱动的用例下**杀不掉**（被 mode 相等 + 双侧 rc 两道先兜住）——不是「不需要」，是「不可证伪」。抽成纯函数后对合成 raw 行直测，两条分支各自有了红。这是本票唯一一次结构调整，动机即 PV 规则 5 的可证伪性。 |
| **把 Task2 判据抽成 `_tasks_content_exempt` 独立函数** | 同上：Task1 恒 False 会把上游三道保守回落分支全遮住（删掉也没人红）。有了这个替身点，测试可把它 stub 成恒 True，逐条证伪回落分支。Task2 只需实现这一个函数。 |
| **`is_stale` 沿用逐文件 return-True 结构**〔1.1a〕 | 仅 `sub == "tasks.md"` 走单独分支延后到帧末判定；「帧内监视集路径集是否恰为 `{tasks.md}`」由控制流建立，未重构成帧级两遍预扫描。 |
| **`\x1f` 作 sha/subject 分隔符** | subject 可含空格与冒号；`%H` 长度随 sha1/sha256 变，定长切片不安全。 |
| **`--no-renames`** | 让改名分解成 A+D，不依赖仓库级 `diff.renames` config（确定性）。 |

**BR-6 护栏逐字不动**：design 域遍历未引入 `--no-merges` / `--first-parent`；merge 提交下「前版」
相对**每个** parent 各自定义（`commit_parents` 返回全部 parent，`design_frame_exempt` 逐 parent 求值）。
机械守：`test_br6_guard_no_no_merges_or_first_parent_in_design_scope`（扫代码行、跳过注释——
护栏注释本身就写着这两个 flag 名）。

## 每条验收标准的证据锚点

| 验收标准 | 锚点 |
|---|---|
| 能求出「监视集内触及路径集」，与完整文件列表是两个量 | `design_watched_subs` (ship_gate.py:234) · `test_watched_subs_is_not_the_full_file_list`、`test_watched_subs_collects_all_watched_members` |
| 能取到前后两版原始字节，读取保真 | `run_git_bytes` (ship_gate.py:222) · `tasks_blob_pair` (ship_gate.py:290) · `test_blob_pair_returns_raw_bytes_verbatim`（首尾空白 + 末尾换行 + CRLF + `\xff\xfe` 非 UTF-8 逐字节相等）、`test_blob_pair_preserves_crlf_and_trailing_newline_difference` |
| 返回状态显式检查；任一侧失败 ⇒ 判失鲜，不依赖空值相等 | `tasks_blob_pair` 的 `rc_before != 0 or rc_after != 0` · `test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes`（显式断言不得返回 `(True, b"", b"")`）、`test_blob_pair_rc_failure_on_one_side_is_conservative` |
| 前版不存在（该提交中新建）⇒ 判失鲜 | `test_blob_pair_added_in_this_commit_is_conservative`、`test_exempt_conservative_when_added_in_this_commit` |
| 后版不存在（删除 / 迁走）⇒ 判失鲜 | `test_blob_pair_deleted_in_this_commit_is_conservative`、`test_blob_pair_renamed_away_is_conservative` |
| 非普通内容修改（重命名/复制/类型变更/仅权限位）⇒ 判失鲜 | `_plain_modification_from_raw` (ship_gate.py:262) · `test_blob_pair_chmod_only_is_conservative`（含前提校准断言：chmod 确被 git 记录，否则本例失去区分力）、`test_blob_pair_type_change_to_symlink_is_conservative`、`test_raw_line_rejects_non_modification_statuses`、`test_raw_line_rejects_mode_only_change`、`test_raw_line_rejects_malformed_shapes` |
| merge 下前版相对每个 parent 各自定义，未引入 `--no-merges`/`--first-parent` | `commit_parents` (ship_gate.py:250) · `test_commit_parents_enumerates_every_parent_of_a_merge`、`test_exempt_requires_every_parent_of_a_merge`（**判别性构造**：merge 相对 first parent 合格、相对 second parent 不合格，含两条前提校准断言）、`test_br6_guard_no_no_merges_or_first_parent_in_design_scope` |
| 既有全部失鲜用例逐字保持绿，本票不改变任何判定 | 既有 164 条全绿（无一条被改写）· 新增行为不变用例：`test_tasks_only_checkbox_flip_still_stale`、`test_tasks_flip_plus_source_code_still_stale`（`git add -A` 打包形态）、`test_merge_commit_touching_tasks_still_stale`、`test_design_frame_exempt_never_exempts_in_task1` |

## 变异验证实际执行记录

机械执行（脚本逐条改源 → 跑 `test_gate_freshness.py` 全文件 → 还原），**15/15 全部转红**：

| 变异 | 转红用例 |
|---|---|
| M1 删两侧 rc 显式检查 | `test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes`, `..._on_one_side_...` |
| M2 删整个形态闸门 | `..._chmod_only_...`, `..._type_change_to_symlink_...`, `test_exempt_conservative_when_form_disqualified` |
| M3b 只删 mode 相等（留 status==M） | `..._chmod_only_...`, `test_raw_line_rejects_mode_only_change`, `test_exempt_conservative_when_form_disqualified` |
| M4c 只删 status==M（留 mode 相等） | `test_raw_line_rejects_non_modification_statuses` |
| M10 删「以 `:` 起始」行形校验 | `test_raw_line_rejects_malformed_shapes` |
| M10b 删字段数校验 | `test_raw_line_rejects_malformed_shapes` |
| M11 删 rc/空输出回落 | `test_plain_content_modification_false_when_path_untouched` |
| M5 `commit_parents` 只留 first parent | `test_commit_parents_enumerates_every_parent_of_a_merge`, `test_exempt_requires_every_parent_of_a_merge` |
| M5b `commit_parents` 解析失败不回落 None | `test_commit_parents_unresolvable_sha_is_none` |
| M6 `design_watched_subs` 退化为完整文件列表 | `test_watched_subs_is_not_the_full_file_list` |
| M7 exempt 去掉「监视集恰为 {tasks.md}」限定 | `test_exempt_conservative_when_other_watched_path_touched_even_if_content_ok` |
| M7b exempt 去掉根提交 / None parents 回落 | `test_exempt_conservative_on_root_commit`, `..._on_unresolvable_sha` |
| M7c exempt 去掉 pair 不合格回落 | `test_exempt_conservative_when_form_disqualified`, `..._when_added_in_this_commit`, `test_exempt_requires_every_parent_of_a_merge` |
| M8 format 不携带 `%H` | `test_impl_review_exempt_bare_and_colon`, `test_br6_guard_...` |
| M12 读取改走 text 路径（`.strip()` + `errors="replace"`） | `test_blob_pair_returns_raw_bytes_verbatim`, `..._preserves_crlf_...` |

首轮 M4c/M10/M7/M7b/M7c 曾**不转红**（被上游闸门遮蔽 / 被 Task1 恒 False 遮蔽）——这直接驱动了
上表两处结构选择（抽纯函数 + 抽判据函数），而非放宽变异标准。

## 全套件结果

- `pytest sdflow-ship/tests/` — **47 passed**（本文件；全 ship 套件 `sdflow-ship/tests/` 164 → **197 passed**，新增 33 条，无既有用例被改写）
- 仓根 `/usr/bin/python3 -m pytest` 全套件 — **1944 passed, 8 skipped, 3 xfailed**（125.62s），零 failure、零新增 warning
- `python3 -m py_compile sdflow-ship/scripts/ship_gate.py` — 通过

## Concerns

1. **`--no-renames` 这道保障不可证伪。** 移除它没有任何用例转红：路径限定 + 双侧 rc 检查已把改名
   兜在 False 一侧。保留它是为了不依赖仓库级 `diff.renames` config（确定性），但它目前是
   defense-in-depth 而非独立承重——显式登记，不冒充有守。
2. **CRLF 归一化发生在 commit 时，读取端无从补救。** 本机全局 `core.autocrlf=input` 下，CRLF 在
   blob 生成前就被清成 LF，两版 blob 根本不含 CR。这不影响本票的判定方向（保真读取仍是必须的，
   否则 `autocrlf=false` 的消费仓会被吞掉差异），但意味着「CRLF 差异」在部分消费仓天然不可见。
   两条保真用例已显式钉 `core.autocrlf=false`，并在注释里写明前提校准的理由。
3. **`design_frame_exempt` 恒 False 期间，其内部分支只靠 monkeypatch 替身证伪。** 这是 Task1
   「能力先行、判据后接」形态的固有代价。Task2 接上 `_tasks_content_exempt` 后，这些分支会同时
   拿到端到端（`run_gate`）层面的红，届时建议补一轮不带替身的端到端负例。
