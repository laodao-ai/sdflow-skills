# Task 3 — 内容豁免与既有 subject 豁免的优先级有唯一解

**R-ID:** SW-1 · **Blocked-by:** Task 2 · **状态:** 完成

## 结论先行

**次序现状已正确，无需改逻辑**——`ship_gate.py::is_stale` 的 design 分支里，subject 精确式判定
（L494 区块）本来就在 `design_watched_subs` / `design_frame_exempt` 之前，∴ **短路发生在读取任何
blob 之前**。Task 3 的实际产出是：

1. **把「已经对但没被钉住」的行为钉成真值表用例**（8 格 + 短路次序 + 反向证）；
2. **把优先级契约写进源码注释**（防止未来有人把 `变体 subject + 纯勾选` 这一格「修」回失鲜）。

没有为了显得有产出而重构。

## 优先级契约（唯一解）

| 通道 | 判据 | 位置 |
|---|---|---|
| **A** subject 精确式（BR-7） | `subject == "checkpoint(impl-review)"` 或以 `"checkpoint(impl-review):"` 起首 | **读取任何 blob 之前**短路豁免 |
| **B** 内容判据（Task 2） | 帧内 design 监视路径集 == `{tasks.md}` 且勾选框归一化后逐行等值 | 通道 A 未命中时求值 |

**BR-7 语义澄清**：BR-7 管的是「**变体不因 subject 获豁免**」，**不是**「变体必然失鲜」。
一个变体 subject、内容却是纯勾选翻转的提交，走通道 B 豁免是正确的——豁免面取自**内容本身**，
被监管方能书写的只有 subject，∴ 伪装 subject 拿不到任何额外豁免面。

## 真值表 8 格（`test_gate_freshness.py` ⑧a）

帧内落在 design 监视集的路径恰为 `{tasks.md}`，另带一份仓库源码（贴 `git add -A` 真实形态）。

| subject \ 内容 | 纯勾选翻转 | 语义改动（标题措辞） |
|---|---|---|
| **精确** `checkpoint(impl-review)[:…]` | 豁免（通道 A 短路） | **豁免**（通道 A 独有格，BR-7 既有语义，本 change 不动） |
| **变体** `checkpoint(impl-review)evil` | **豁免（经通道 B）** ← 判别性最强 | 失鲜 |
| **空 subject** | 豁免（经通道 B） | 失鲜 |
| **普通** `docs: …` | 豁免（经通道 B） | 失鲜 |

对应用例：`test_tt_exact_subject_pure_flip_exempt` / `test_tt_exact_subject_semantic_exempt_by_subject` /
`test_tt_variant_subject_pure_flip_exempt_via_content` / `test_tt_variant_subject_semantic_stale` /
`test_tt_empty_subject_pure_flip_exempt_via_content` / `test_tt_empty_subject_semantic_stale` /
`test_tt_plain_subject_pure_flip_exempt_via_content` / `test_tt_plain_subject_semantic_stale`。

## 既有 BR-7 回归用例：未改宽，且理由更强

按 ticket 关键要求 2 逐条核对了既有用例的**内容**，确认没有一条是「恰好纯勾选、现在会被放行」：

| 既有用例 | 改的文件 | 内容 | 现状 |
|---|---|---|---|
| `test_impl_review_evil_suffix_stale` | `design.md` | `v1` 新写 | 失鲜 ✅ |
| `test_impl_review_fix_variant_stale` | `design.md` | `v1` 新写 | 失鲜 ✅ |
| `test_empty_subject_touch_design_stale` | `design.md` | `v1` 新写 | 失鲜 ✅ |
| `test_interleaved_impl_review_and_normal_stale` | `design.md`（普通帧） | 语义改 | 失鲜 ✅ |
| `test_impl_review_exempt_bare_and_colon` | `design.md` + `tasks.md` | — | 豁免 ✅（通道 A） |

这四条失鲜用例改的都是 `design.md`——**落在通道 B 的适用面之外**（帧内监视路径集 ≠ `{tasks.md}`，
被 `subs - {"tasks.md"}` 那道分支先行拦下）。∴ 通道 B 的加入对它们零影响，断言一字未改。

## 短路次序的证明（⑧b）

- `test_exact_subject_short_circuits_before_any_blob_read`：把 `blob_pair` 替身为「一调用即抛」，
  精确 subject + **语义改动** 的帧仍判 `(False, "fresh")`，且调用记录为空。
- `test_non_exact_subject_does_reach_blob_read`（反向证）：非精确 subject 下 `blob_pair` **必须**
  被调到 1 次——否则上例的绿会退化成「它从来不被调用」的恒真断言。

## 豁免面不由被监管方声明决定（⑧c）

- `test_content_channel_verdict_independent_of_subject`（4 参数）：同一份语义改动配 4 种 subject
  （含两种伪装成豁免形态的变体）⇒ 判定恒为失鲜。
- `test_content_criterion_takes_only_content`：机械锚——`inspect.signature(_tasks_content_exempt)`
  的入参恰为 `["before", "after"]`，无 subject / 无路径 / 无文件存在性。将来有人往判据里塞 subject
  即转红。

## 变异验证（实跑，逐条记录）

| 变异 | 手法 | 转红用例 |
|---|---|---|
| **M1 次序颠倒** | 在 subject 判定**前**插入 `design_watched_subs` + `design_frame_exempt` 求值 | `test_exact_subject_short_circuits_before_any_blob_read`、`test_non_exact_subject_does_reach_blob_read`（2 failed / 8 passed） |
| **M2 删通道 A** | subject 精确式分支整体换成 `pass` | `test_tt_exact_subject_semantic_exempt_by_subject`、`test_exact_subject_short_circuits_...`（2 failed / 13 passed） |
| **M3 删通道 B** | `if subs and not design_frame_exempt(...)` → `if subs:` | 三条 `*_pure_flip_exempt_via_content` + `test_non_exact_subject_does_reach_blob_read`（4 failed / 11 passed） |
| **M4 内容判据恒 True** | `_tasks_content_exempt` 首行插 `return True` | 三条 `*_semantic_stale` + 4 参数 `test_content_channel_verdict_independent_of_subject`（7 failed / 8 passed） |

每次变异后均 `cp` 还原源文件。

> 说明：`test_tt_exact_subject_pure_flip_exempt` 一格在 M1–M4 下都不红——它被两条通道**双重覆盖**
> （精确 subject 且内容纯勾选），这是真值表的合法一格，不是无效断言；其判别力在于「若两条通道
> 同时坏掉」才失守，M2+M3 联合变异即可杀，不单列。

## 代码改动

`sdflow-ship/scripts/ship_gate.py`：仅新增注释区块（+11 行），**逻辑零改动**。写明
① 短路次序是硬要求、MUST NOT 把内容读取挪到它前面；② BR-7 读作「变体不因 subject 获豁免」而非
「变体必然失鲜」；③ 指向 ⑧a / ⑧b 两处用例锚。

## 测试

- `pytest sdflow-ship/tests/` → **256 passed**
- 仓根全套件 `/usr/bin/python3 -m pytest -q` → **2003 passed, 8 skipped, 3 xfailed**（124.90s）
- 无既有用例转红，无断言被改。
