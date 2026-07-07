# Verify Report — issues-pool-hardening

日期：2026-07-07
Change：issues-pool-hardening

## 结论：PASS
<!-- ship-gate: verify=PASS -->

冷启动、不信任复选框，逐条对码 + 对测核验。全套件 `python3 -m pytest -q` → **552 passed**。7 组 tasks + 2 条 ADDED spec 需求均有可机验证据锚点，无核心功能缺失。诚实核验通过：`--strict` 本 change 无非交互消费者，proposal/design/adr/spec-review 一致将其记为「预置接口/待 T2.5」，未虚记为已达成。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试名 / commit） | 状态 |
|---|---|---|
| **T2.1/1.3 cmd_add 入口守卫** module/summary/change/batch/time/title/source | buglist.py:404-415、todolist.py:366-377（守原始参数、在 `ensure_file` 落盘前；非 join sink） | ✅ |
| **T2 cmd_triage(batch) 守卫** | buglist.py:546（`_reject_cell_unsafe(batch)` 在写 cells[7] 之前）、todolist.py:522 | ✅ |
| **T2 rename retag(new_key) 守卫** | issues.py:780 `_retag_items_in_dated_files` 入口 `_reject_cell_unsafe(new_key)` | ✅ |
| **T2 set_status(evidence/reason/date/month) 守卫** | buglist.py:468-470、todolist.py:449-451 | ✅ |
| **T2 batch_add(优先级/计划/title/key) 守卫** | issues.py:688-695（key 走 `_reject_batch_key_unsafe`，title/优先级/计划 走 cell 守卫） | ✅ |
| **T2 helper 语义**（含 `\|`/`\n`/`\r` 即 `_die`；None 放行） | buglist.py:699-705、todolist.py:658、issues.py:312-321（三脚本逐字同款） | ✅ |
| **1.4 OV-2 batch key slug 校验**（拒 `\|`/换行/` — `/空/首尾空白） | issues.py:324-350 `_reject_batch_key_unsafe`；空/纯空白单独拒(343)、` — `+首尾空白(346) | ✅ |
| **1.5 OV-3 自定义 id 校验** `re.fullmatch([A-Z]\d+)` + all_ids 查重 | buglist.py:394-398、todolist.py 对应（单字母前缀正则，isinstance 防 TypeError；commit 7015491 收单字母前缀） | ✅ |
| **OV-3 scan 报同池/跨文件重复 ID** | buglist.py:573-649（全池 dup_locations，跨文件 dup 单列，commit 54105d5 FIX-2） | ✅ |
| **T1.1/2.3 reindex problems 回显 stderr、默认 exit 0、INDEX 仍重建** | issues.py:407-417 `_echo_problems`；`_reindex_core`:353 收集 problems | ✅ |
| **T1.2 `--strict` problems 非空 exit≠0**（仅 strict+problems 时） | issues.py:418-419 `if strict and problems: sys.exit(1)`；argparse:891 | ✅ |
| **_echo_problems 复用于 cmd_reindex + rename auto-reindex** | issues.py:417（reindex）、879（rename else 分支） | ✅ |
| **2.4 OV-1 scan 行 arity 校验**（`len not in (7,8)` 入 problems） | buglist.py:605-608、todolist.py 对应（commit 32ca4ff） | ✅ |
| **T3.1 终态集 ⊆ + 内联字面量 == 守卫测试** | test_issues.py:198-204（subset+literal）、206-226（≥2 内联覆盖）、228-242（cmd_scan 严格 == 抠取，commit 931c45d） | ✅ |
| **T4 `--if-exists skip`=skip-with-warn**（no-op+warn+exit0、不比较字段） | issues.py:698-705（print stderr + `return`，零字段比较） | ✅ |
| **T4 rename auto-reindex + 失败吞-warn+exit0** | issues.py:866-879（`try _reindex_core / except → warn`，rename 本体 print 在 862 已完成） | ✅ |
| **T5.1 `_find_row_file` 各 recorder 内抽** | buglist.py:317（用于 472 set_status + 539 triage）、todolist.py:302（453/515） | ✅ |
| **T5.2 cmd_batch_set_status 是否纳入** | design.md:64「不纳入」（`_find_batch_entry_range` 定位 batches.md 条目，异结构）——已记明 | ✅ |
| **T5.3 WONTDO/0成员 IN_PROGRESS 分支补测** | test_todolist.py:688-699（WONTDO 门禁）、triage 终态不倒回:649-655 | ✅ |
| **6.1 doc-sync 三 SKILL.md rename 段** | sdflow-issues/SKILL.md:95-98（补 auto-reindex + 订正「无副作用」措辞）、buglist:183、todolist:193 | ✅ |
| **7.1 全套件绿** | `pytest -q` → 552 passed | ✅ |
| **spec ADDED#1 table-cell-safe** 全写路径 + slug + id + prose 豁免 | 见上 T2 各行；prose 不守（cmd_add 只守 title/source，现象/根因/修复未挂守卫） | ✅ |
| **spec ADDED#2 reindex 可观测 + strict + arity** | 见上 T1 各行 | ✅ |
| **7.4 诚实核验**：`--strict` 无 in-change 消费者，未记作已达成 | grep 确认非测试调用者仅 argparse 定义；adr/0010:15、proposal.md:8、design.md:33、spec-review-report Q1 均标「预置接口/无 enforcement 价值/MUST NOT 记作已达成」 | ✅ |

## 缺口清单

**核心 FAIL：无。**

**Minor / deferred（不影响 PASS）：**
- T2.6 / T2.5 follow-up：`sdflow-done` sweep 调 `reindex --strict` 明确 defer 出本 change（tasks.md:17 标注、hand-off 承接）。`--strict` 当前为死代码/预置接口——这是**有意的诚实降级**（spec-review Q1=B），非缺陷。
- 诚实性：全部 6+ 处文档（adr/proposal/design/spec-review/superpowers-plan/design-voice-context）口径一致，无一处把「堵非交互静默蒸发」记成已兑现。诚实性 gate 通过。

## PASS
