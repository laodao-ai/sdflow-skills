# Task 1 · 双轴审第 2 轮返修（fix2）：锚守卫遍历范畴取错

**范围**：`sdflow-ship/tests/test_anchor_contract.py` 一个文件，两个用例。无产品代码改动。

## 发现（re-review · Important）

上一轮（fix1）把锚守卫从「每文件一次存在性」改成逐条遍历，方向对，但**遍历的范畴取错**：
循环的是硬编码的 `PRODUCER_FRONTMATTER.value_lines`（5 条已知枚举值），而不是
`_extract_frontmatter_blocks` 从真实字节抽出的**全部块**。粒度只降到「每枚举值」，没降到「每块」。

**变异实证（re-review 的 M3）**：往 `sdflow-spec-review/SKILL.md` 插入一个
`design_approved: false` 的**无锚**结论块 → 全仓 318 passed，零红。而 `FIELD_ENUMS[design_approved]`
含 `(True, False)`，`false` 是**合法的目标态取值** ⇒ 将来 producer 补负面模板时，会原样重演
fix1 刚修掉的那个 bug（「新增结论块无人守」正是那个 bug 本身）。

同片面的第二处 = fix1 自己上抛的 Concern 2：`test_producer_anchor_is_direct_child_of_ship_gate`
用 `if ADR1_ANCHOR_LINE in b` 过滤块，与守卫循环耦合——**漏锚的块会被过滤掉，于是两个用例都不管它**，
覆盖面随守卫放宽而静默缩小。re-review 判定「不是将来的事，今天就漏」，一并修。

## 修法

### 1. `test_producer_templates_declare_reviewed_sha_verbatim` — 反转循环 + 叠加

两层检查**互补，缺一不可**：

- **(A) 全块遍历**：`for block in blocks: assert ADR1_ANCHOR_LINE in block_lines`
  —— **任何**块都不许漏锚，覆盖将来新增的结论块（含 `design_approved: false`）。
- **(B) value_lines 存在性**（保留）：5 个已知结论块必须都在场，防某块被整体删掉而静默缩面。
  (A) 对空集/缺块无话可说，(B) 才守得住。

同时补 `assert blocks`，防 `_extract_frontmatter_blocks` 整体失效导致 (A) 空转。

### 2. `test_producer_anchor_is_direct_child_of_ship_gate` — 去掉含锚过滤

`blocks = [b for b in ... if ADR1_ANCHOR_LINE in b]` → `blocks = _extract_frontmatter_blocks(text)`，
与 (A) 同范畴。已核实三个 producer 文件里每个块都含本文件对应的结论字段
（spec-review 1 块 / done 2 块 / code-review 2 块），故 `field in state` 断言对全块遍历成立。

## 变异验证

| # | 变异 | 结果 |
|---|---|---|
| M3（re-review 原样复现） | `sdflow-spec-review/SKILL.md` 插入无锚的 `design_approved: false` 块 | **红**（修前绿） |
| M4（新增） | 删掉 `sdflow-done/SKILL.md` 整个 `verify: FAIL` 块 | **红** |

**M3 红的证据**（2 failed, 8 passed）：

```
FAILED test_producer_templates_declare_reviewed_sha_verbatim
  AssertionError: sdflow-spec-review/SKILL.md 存在缺锚字段裸行 'reviewed_sha: 0123...4567' 的 ship-gate 模板块
FAILED test_producer_anchor_is_direct_child_of_ship_gate
  AssertionError: sdflow-spec-review/SKILL.md 锚字段未被解析出（挂载层级错？须是顶层 ship-gate: 的直接子键）
  assert 'reviewed_sha' in {'design_approved': False}
```

两个用例**双双**变红 ⇒ 修法 2（去过滤）确实让第二个用例重新覆盖到了漏锚块。

**M4 红的证据**（3 failed, 7 passed，其中 (B) 分支）：

```
FAILED test_producer_templates_declare_reviewed_sha_verbatim
  assert any(value_line in b for b in blocks)
  AssertionError: sdflow-done/SKILL.md 未找到声明 'verify: FAIL' 的 frontmatter 模板块
```

⇒ 叠加的 (B) 存在性检查仍然承重，没有被 (A) 取代。

两次变异均已恢复原状（`git status --porcelain` 见下）。

## 测试基线

- `pytest sdflow-ship/tests/ -q` → **318 passed**（= 基线）
- 仓根全套件 `pytest -q` → **2070 passed, 9 skipped, 3 xfailed**（总数 2082 = 基线总数，0 failed）

**与基线 2071/8 的 1 例差异已定位，非本轮引入**：`-rs` 复跑锁定第 9 条 skip =
`sdflow-init/tests/test_outside_voice_utf8.py::test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic`，
skip 原因是「变异体这一次独立的 ramdisk 上，在走到 M3 差异化代码之前就撞见 shell/coreutils 自己的
满盘原生诊断（`No space left on device`）——本次未能建立可区分 M3 修复点的前提」。这是该用例
**自身文档化的环境依赖诚实 skip**（其注释记载本机压测 100 次 = 91 通过 / 9 诚实 skip / 0 失败），
逐轮抛硬币，与本轮改动无因果关系——本轮只动 `sdflow-ship/tests/test_anchor_contract.py`，
而 `sdflow-ship/tests/` 前后均为 318 passed。**0 failed，无回归。**

## git status --porcelain（收尾）

```
 M openspec/issues/todolist/2026-07-todolist.md
 M sdflow-ship/tests/test_anchor_contract.py
?? openspec/changes/harden-gate-git-layer/impl-reports/task1-fix1-review-package.diff
?? openspec/changes/harden-gate-git-layer/impl-reports/task1-review-package.diff
?? openspec/changes/harden-gate-git-layer/impl-reports/task1-reviewed-sha-anchor-fix2.md
```

本轮只动 `sdflow-ship/tests/test_anchor_contract.py` + 新增本报告；其余为前序轮次遗留。
未改 proposal/design/specs/tasks，未勾 `superpowers-plan.md`，未打 `task1-` 完成标签。
