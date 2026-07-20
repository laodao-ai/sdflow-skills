# Task 2 · fix2：`tg02_hit` 围栏未闭合改为保守判命中（re-review Important）

修一条，只修一条。上一轮（`fix1`）把 fence 词法收敛到单一源并补全 `~~~` 与任意长游程，
re-review 由此发现 `tg02_hit` 是四个 fence 调用点里**唯一不处理「围栏未闭合」**的，方向 **fail-open**。

## 问题

`sdflow-ship/scripts/ship_gate.py` 的 `tg02_hit`：循环扫头部声明区（开头 → 首个真 `## ` 前），
fence 内的行 `continue` 跳过。但循环跑到 EOF 后**直接 `return False`**——
`fence.inside` 为真（= 围栏未闭合、悬空围栏吞掉了其后的真声明行 `〔TG-02：…〕`）这一情形被**静默吞掉**。

后果：`ship_gate` 约 :962 判 `SKIP_SOP`，**静默跳过 embedded-test-sop 门**——
一份真嵌入式 change 因为 proposal 头部有个没闭合的围栏就绕过了 SOP 要求。

另三处对同一信号都做保守处理，`tg02_hit` 是唯一的例外：

| 调用点 | `fence.inside`(EOF) 的处理 | 方向 |
|---|---|---|
| `_normalize_checkbox_lines` | `return None`（判定不能 ⇒ 不豁免 ⇒ 判失鲜） | fail-safe |
| `_parse_plan` | 返 unbalanced flag ⇒ 调用方 `UNKNOWN` | fail-safe |
| `_line_scoped_hits` | 返 flag ⇒ 归档侧「判定不能」（ADR-5） | fail-safe |
| **`tg02_hit`**（修前） | **吞掉，`return False`** | **fail-open** |

**为什么现在修，而不是「这是存量、留着」**（通则 ③，不拿现状反驳目标）：
该洞对 ` ``` ` 确是存量，但 `fix1` 把围栏开口从**一族扩到两族**（含 `~~~` 与任意长游程）——
**本次修改直接放大了它的触发面**。且 `fix1` 报告写的「行为变化方向一律 fail-safe」这句话，
**对这个调用点根本不成立**。

## 修法

`tg02_hit` 循环结束后补：

```python
if fence.inside:
    return True
```

语义：**围栏未闭合 ⇒ 头部声明区的可见性判定不可信 ⇒ 保守要求跑 SOP**，与另三处「看不清就保守」方向对齐。

**没做的事**（防 scope drift）：`code` 域失鲜判据、BR-7 精确式 subject 豁免逐字未动；
无 `--no-merges` / `--first-parent`；**MUST NOT 扩到 markdown 其它结构**（表格 / 嵌套列表 / 引用块 = 无界面，基准 5）——本次一行都没碰解析器边界。

## 新增用例（3 条，取自复审实测形态）

`sdflow-ship/tests/test_gate_impl_progress.py`：

| 用例 | 形态 |
|---|---|
| `test_tg02_unclosed_backtick_fence_conservative_hit` | 头部未闭合 ` ``` ` 吞掉其后真声明行 |
| `test_tg02_unclosed_tilde_fence_conservative_hit` | 头部未闭合 `~~~` 同理 |
| `test_tg02_long_tilde_run_before_declaration_conservative_hit` | 一行 `~~~~~~~~`（本意作水平分隔线，按 CommonMark 是围栏开启符）出现在声明行之前 |

三例修前实测均 `tg02_hit=False`（本该判命中），修后均 `True`。

## 变异验证（实跑）

删掉 `if fence.inside: return True` 这条保守回落，三条新用例应全红：

```
$ /usr/bin/python3 -m pytest sdflow-ship/tests/ -q -k "unclosed or long_tilde_run"
E       AssertionError: assert False is True
E        +  where False = <function tg02_hit at 0x106cb1430>(...)
FAILED test_gate_impl_progress.py::test_tg02_unclosed_backtick_fence_conservative_hit
FAILED test_gate_impl_progress.py::test_tg02_unclosed_tilde_fence_conservative_hit
FAILED test_gate_impl_progress.py::test_tg02_long_tilde_run_before_declaration_conservative_hit
3 failed, 11 passed, 227 deselected in 1.04s
```

三条全红 ⇒ 均为 load-bearing，不是恰好蒙对。已还原。

## 测试结果

- `/usr/bin/python3 -m pytest sdflow-ship/tests/ -q` — **241 passed**（fix1 的 238 → +3），零 failure
- 仓根 `/usr/bin/python3 -m pytest -q` — **1987 passed, 9 skipped, 3 xfailed**（138.50s），零 failure

**无任何既有用例转红**，未改动任何既有断言以迁就。

> 关于「行为变化」的如实交代：本修法确实让「头部区有未闭合围栏」的 change 从 `SKIP_SOP` 变成
> `RUN_SOP`。**既有用例里没有依赖旧行为的**（已全套件核实），但这是真实的行为变化面——
> 一份 proposal 头部写了个没闭合的围栏，从此会被要求跑 SOP。这正是保守方向该有的样子。

## 顺带订正 fix1 报告的两处措辞（不是新改动，是如实陈述）

`task2-checkbox-exemption-fix1.md` 两处笼统的「fail-safe / 一律保守」已改为**分调用点**表述：

1. 「行为变化方向」节的「一律 fail-safe」——补注：三处 fail-safe，`tg02_hit` 原本 fail-open，本轮修正。
2. 「诚实边界」里「开启符前最多 3 空格缩进未实现，方向更保守」——补注：该结论对前三个调用点成立，
   对 `tg02_hit` 是 **fail-open** 方向（更易认作围栏 ⇒ 更易吞掉声明行）；修完第 1 条后被
   `fence.inside ⇒ True` 兜住，但表述仍须分点写清，不许笼统说「一律保守」。

## 改动清单

- `sdflow-ship/scripts/ship_gate.py` — `tg02_hit` 末尾补 4 行（含注释）保守回落
- `sdflow-ship/tests/test_gate_impl_progress.py` — +3 用例
- `openspec/changes/fix-design-gate-freshness-proxy/impl-reports/task2-checkbox-exemption-fix1.md` — 两处措辞订正
