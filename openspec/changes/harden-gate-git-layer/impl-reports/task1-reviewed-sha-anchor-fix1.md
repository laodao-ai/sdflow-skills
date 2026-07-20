# Task 1 返修报告 · 第 1 轮双轴审（fix1）

基线 HEAD = `4d16f41`。首轮报告 = `task1-reviewed-sha-anchor.md`（未覆盖，本文件只记本轮返修）。
三条 Important 全部修完，每条附变异证明。

---

## F1（Standards）`CAUSE_ANCHOR_INVALID` 在生产路径不可达

### 判定：确认成立

三个 live 读点（`ship_gate.py:1311/1336/1382`）都先经 `live_ship_gate_state`。坏 frontmatter 在
`_fail_closed_on_bad` 就 `emit` 了通用 UNKNOWN 并 `sys.exit`，控制流根本走不到 `read_reviewed_sha`。
∴ `read_reviewed_sha:295` 的 `CAUSE_ANCHOR_INVALID` 分支在生产路径上是死代码，撞门者拿到的是
「frontmatter 坏（字段=reviewed_sha 类别=out-of-domain）」——**无 `cause_category`、无「订正为完整
commit OID」指引**，Compliance「五类失败原因各给可行动诊断」在 anchor-invalid 这一类上未兑现。

### 修法：选 (a)（推荐路线），未遇阻碍

`sdflow-ship/scripts/ship_gate.py` `_fail_closed_on_bad`：当出错字段 == `reviewed_sha` 时改抛
`GateIndeterminate(..., CAUSE_ANCHOR_INVALID)`，其余字段维持原 `emit` 不变。

**为什么在 `_fail_closed_on_bad` 而不是调用点分流**：三个读点若各自判一次，就是三份等价逻辑三处漂移；
`_fail_closed_on_bad` 是坏 frontmatter 的唯一收敛点，分流放这里只有一处。

**为什么抛而不是就地 `emit`**：`ship_gate.py:167` 的既有硬约束——「唯一映射点在 `main()`，抛出方
MUST NOT 自行 emit/exit」。抛出后由 `main()` 的 `except GateIndeterminate` 统一转
UNKNOWN(6) + `cause_category` + `_INDETERMINATE_ADVICE[anchor-invalid]`，退出码映射不散。

**代价**：`read_reviewed_sha` 里的 `err is not None` 分支仍保留（现覆盖「同块内**其它**字段坏」这一
理论形态，实际同样已被 live 层拦截）。它现在是防御性冗余而非承重代码——**没有把它删掉**，因为
`read_reviewed_sha` 是公共入口、被测试直调，删掉会让 `test_semantic_layer_raises_typed_payload`
的 anchor-invalid 参数失去落点，且未来若出现不经 live 层的读点会静默失去校验。此点登记在 Concerns。

**未选 (b) 的理由**：(b) 是让 Compliance 明写的承诺缩水，且 (a) 无实现阻碍。

### 变异证明

把 `_fail_closed_on_bad` 的新分支整段撤掉（`git stash push` 该文件），跑
`test_gate_reviewed_sha.py`：

```
7 failed, 25 passed
E  KeyError: 'cause_category'
FAILED test_syntactically_invalid_anchor_is_unknown[0123456] … [g123456789ab]（7 个参数全红）
```

改回后：`318 passed`（sdflow-ship 全套件）。

---

## F2（Standards）CLI 用例断言过弱

### 修法

`sdflow-ship/tests/test_gate_reviewed_sha.py:77` `test_syntactically_invalid_anchor_is_unknown`
在 `code == 6` 之外补两条：

- `js["cause_category"] == "anchor-invalid"` —— 与 missing / unresolvable 两组对齐；
- `"40 位小写 hex" in js["reason"]` —— 钉住该类**专属可行动措辞**（对齐
  `test_anchor_object_absent_is_unknown` 断 `"force-push"` 的既有口径）。多加这条是因为只断
  `cause_category` 仍允许 advice 表退化成一句通用话。

7 个 BAD_SYNTAX 参数各覆盖一次。

### 变异证明（含评审方预期的那个红）

**这条的红就是 F1 的证据**：断言写好、F1 未修时，7 个参数全部 `KeyError: 'cause_category'`
（输出见上 F1 节）——即生产路径确实没有走 anchor-invalid 专属诊断。F1 修好后 7 个全绿。

---

## F3（Spec）模板锚守卫粒度不足

### 判定：确认成立，且已复现评审方的变异

原 `test_producer_templates_declare_reviewed_sha_verbatim` 是**每文件一次存在性检查**
（`ADR1_ANCHOR_LINE in lines`）。5 个结论模板块中 `verify: FAIL`、`code_review: blocked`
两块删掉锚行仍全绿——**正是 FAIL / blocked 两个负面半场无机械守**。

后果不是纸面的：负面结论块缺 `reviewed_sha`，producer 照模板落盘就写不出锚，reader 侧
`anchor-missing` → UNKNOWN(6)，负面半场整条路走不通。

### 修法

改为遍历 `_extract_frontmatter_blocks(text)`，按 `PRODUCER_FRONTMATTER` 的 `value_lines`
**逐块**定位（每个结论值一组块），断言块内含 `ADR1_ANCHOR_LINE`。粒度从「文件」降到「结论模板块」，
5 块全覆盖。

### 顺带 Minor（面治）：`ADR1_ANCHOR_LINE` 改为从 design.md 抽取

原为硬编码字符串 ⇒「逐字对齐 design.md ADR-1」这句承诺的单一源没被钉住：ADR-1 改了示例值/字段名，
本文件不会变红，三个模板照旧对齐着一份已不存在的规格。

新增 `_adr1_anchor_line()`：定位 `### ADR-1` 节 → 节内以 `reviewed_sha:` 起首的裸行 → 断言恰好一条。
解析面有界（Markdown 章节标题），符合基准 5「有界才手写」。

**`_design_md_path()` 兼容归档态**：active `openspec/changes/{change}/design.md` 找不到时回落
`openspec/changes/archive/*{change}*/design.md`，两处都无则 `AssertionError`（不 skip、不静默）。
——写死 active 路径正是本仓刚踩过的坑（commit `434e0e9`：archive 后机械门 FileNotFoundError 崩掉）。

### 变异证明（4 组，逐条实做）

| # | 变异 | 结果 |
|---|---|---|
| M1 | 删 `sdflow-done/SKILL.md` **`verify: FAIL`** 块的锚行（评审方原变异） | ❌ 变红 `1 failed, 9 passed` |
| M2 | 删 `sdflow-code-review/SKILL.md` **`code_review: blocked`** 块的锚行（评审方原变异） | ❌ 变红 `1 failed, 9 passed` |
| M3 | 删 `sdflow-done/SKILL.md` `verify: PASS` 块的锚行（正面半场未回归） | ❌ 变红 `1 failed, 9 passed` |
| M4 | 改 design.md ADR-1 示例值为 `aaaa…`（单一源漂移） | ❌ 变红 `2 failed, 8 passed` |

M1/M2 在修改前均为 `318 passed` 全绿——变异前后对照成立，非「用例存在且为绿」。

**归档态实证**（不是推理）：把整个 change 目录 `mv` 到
`openspec/changes/archive/2026-07-21-harden-gate-git-layer/`，跑 `test_anchor_contract.py` →
`10 passed`；移回后同样 `10 passed`。若回落分支失效，`_adr1_anchor_line()` 在 import 期即
AssertionError、整文件收集失败，绿不了 —— 故这 10 绿是回落真走通的证据。

---

## 全套件

仓根 `pytest`：**2071 passed, 8 skipped, 3 xfailed**（= 基线，无退化）。
sdflow-ship 子套件：`318 passed`。

---

## 残留 Concerns

1. **`read_reviewed_sha` 的 `err is not None` 分支现为防御性冗余**（F1 修法的已知代价，见上）。
   它不再是 anchor-invalid 的生产路径，但仍是 `read_reviewed_sha` 作为公共入口的自洽校验。
   若后续评审认为「不可达代码一律清除」优先，可另开一票删除并同步改
   `test_semantic_layer_raises_typed_payload` 的参数集——本轮**不做**，因为删除会降低
   非 live 读点未来接入时的安全性。
2. **`test_producer_anchor_is_direct_child_of_ship_gate` 仍按 `ADR1_ANCHOR_LINE in b` 过滤块**
   （只审含锚的块）。F3 修完后「所有结论块必含锚」已被机械守住，故该过滤不再形成盲区；
   但两处逻辑存在耦合——若将来 F3 的守卫被放宽，这里会跟着静默缩小覆盖面。已在此登记。
3. **未改任何设计文档**（`proposal.md` / `design.md` / `specs/` / `tasks.md` 一字未动），
   F1 选 (a) 也不需要往 design 登记「已知不覆盖」。
