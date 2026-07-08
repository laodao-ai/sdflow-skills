# mlh-p5-parser-cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清结 P5 尾巴——`ship_gate.py` 的 frontmatter 解析把「首行 `---` 无闭合」由 `unterminated` fail-closed 改判 `absent`（弥合 spec 措辞张力、堵 live 硬崩 exit 6），退役 `unterminated` 死类别，并删除 Task6 退役后只剩测试引用的孤儿符号。

**Architecture:** 纯健壮性修复 + 死代码清理，向后兼容。三条腿：①`parse_ship_gate_frontmatter` 的 `end is None` 分支返回值从 `({}, ("frontmatter","unterminated"))` 改为 `({}, None)`；②live 读点上层加一个**独立轻量结构诊断**（不改 parse 签名、不改 verdict/退出码），absent 且首行 `---` 无闭合时给 emit reason 附结构提示；③删死符号 `anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` 并收缩 `ALL_ANCHORS`，外科改写混装测试文件。

**Tech Stack:** Python 3 stdlib（零依赖不变量——`parse_ship_gate_frontmatter` 手写解析，禁 `import yaml`）；pytest。

## Global Constraints

- **零依赖不变量**：`parse_ship_gate_frontmatter` 及全 `ship_gate.py` 仅用 stdlib，MUST NOT `import yaml` 或引入任何三方包。
- **单一解析核心（D4，防漂移）**：live 读点与归档 git-show 文本读共用 `parse_ship_gate_frontmatter`；本 change MUST NOT 改其**返回签名** `(state, error)`——三个调用方 `live_ship_gate_state` / `archived_verify_state` / `anchor_set` 均依赖它。
- **fail-closed / fail-safe 取向（机械层红线，design §决策5）**：判定方向安全——absent 不放行；坏输入 pytest 覆盖断言退出码。
- **adr/0004 红线**：absent 判定后 live MUST NOT 回退 inline、MUST NOT 扫正文当过门锚。
- **candidate② 明确弃用**：MUST NOT 引入「意图探测启发式」（会在本仓「讨论 gate 自身」的报告上精准误崩，重蹈 gate-substring-dogfood 覆辙）。
- **保留边界（MUST NOT 删）**：`ANCHOR_VERIFY_PASS` / `ANCHOR_VERIFY_FAIL`（`archived_verify_state` 真用）、`_line_scoped_hits`（归档 dual-read 现役唯一调用方）。
- **checkpoint 标签格式权威**：`sdflow-ship/scripts/ship_gate.py` 的 `TAG_RE = checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`。每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p5-parser-cleanup:task<N>-<slug> "<描述>"`（命名空间前缀 + `task<N>-` **带横杠**，缺横杠 gate 不匹配、完成集 0/N 卡死）。

---

### Task 1: `end is None` 改判 absent + `unterminated` 死类别退役

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py:314-315`（`parse_ship_gate_frontmatter` 的 `end is None` 分支返回值）
- Modify: `sdflow-ship/scripts/ship_gate.py:295`（docstring 的 `category` 枚举移除 `unterminated`）
- Modify: `sdflow-ship/tests/test_frontmatter_parse.py:26-28`（原 `test_unterminated_is_error` 改断言 absent）
- Test: `sdflow-ship/tests/test_frontmatter_parse.py`（新增无闭合回归）
- Test: `sdflow-ship/tests/test_gate_breaker.py`（`anchor_set` 第三调用方不变量回归）

**Interfaces:**
- Consumes: `parse_ship_gate_frontmatter(text) -> (state: dict, error: tuple|None)`（现有签名，不改）；`anchor_set(text) -> frozenset`（现有）。
- Produces: 无新符号。语义变更：首行 `---` 全文无第二个 `---` 的文本 → `parse_ship_gate_frontmatter` 返回 `({}, None)`（absent），`anchor_set` 对同一文本返回 `frozenset()`。

- [ ] **Step 1: 改写既有 `test_unterminated_is_error` 为 absent 断言（tasks.md 3.2）**

`sdflow-ship/tests/test_frontmatter_parse.py` 第 26-28 行，把：

```python
def test_unterminated_is_error():          # --- 不配对 → 坏
    state, err = P("---\nship-gate:\n  verify: PASS\n")
    assert err is not None and err[1] == "unterminated"
```

改为（**保留输入、改期望**）：

```python
def test_unclosed_frontmatter_is_absent():   # [T74] 首行 --- 无闭合 → absent（首块不成立，非坏）
    state, err = P("---\nship-gate:\n  verify: PASS\n")
    assert state == {} and err is None
```

- [ ] **Step 2: 新增无闭合回归单元测试（tasks.md 3.1a）**

在 `sdflow-ship/tests/test_frontmatter_parse.py` 追加（`P` 是本文件既有的 `parse_ship_gate_frontmatter` 别名）：

```python
def test_unclosed_frontmatter_first_line_only():
    # [T74] 首行 --- + 全文无第二个 --- → 首块不闭合 → absent（走既有无锚语义），非 unterminated 坏
    state, err = P("---\n随便正文，没有闭合横线\nship-gate 也不在块内\n")
    assert state == {} and err is None
```

- [ ] **Step 3: 新增 `anchor_set` 第三调用方不变量回归（tasks.md 3.6，BR-1/TC-1）**

在 `sdflow-ship/tests/test_gate_breaker.py` 追加（本文件已 `from ... anchor_set = _ship_gate.anchor_set`）：

```python
def test_anchor_set_absent_on_unclosed_frontmatter():
    # [T74/BR-1] 钉死「挪格子不改熔断进展判据」：首行 --- 无第二个 --- 改判 absent 后，
    # anchor_set 仍返回空集（与旧 unterminated 行为一致），防未来重构 anchor_set 短路时无声失守。
    assert anchor_set("---\nship-gate:\n  verify: PASS\n") == frozenset()
```

- [ ] **Step 4: 跑三个测试确认失败（红）**

Run: `pytest sdflow-ship/tests/test_frontmatter_parse.py::test_unclosed_frontmatter_is_absent sdflow-ship/tests/test_frontmatter_parse.py::test_unclosed_frontmatter_first_line_only sdflow-ship/tests/test_gate_breaker.py::test_anchor_set_absent_on_unclosed_frontmatter -v`
Expected: FAIL —— 前两者因当前返回 `("frontmatter","unterminated")` 断言 `err is None` 失败；`anchor_set` 因坏 err 走 `frozenset()` 分支实际会通过（该用例是回归护栏，改判后仍须绿）。

- [ ] **Step 5: 落地 `end is None` → absent（tasks.md 1.1）**

`sdflow-ship/scripts/ship_gate.py` 第 314-315 行，把：

```python
    if end is None:
        return {}, ("frontmatter", "unterminated")
```

改为：

```python
    if end is None:
        # [T74] 首行 --- 但全文无第二个 --- → 首块不闭合 → 不构成 frontmatter block，
        # 首行 --- 视作正文/markdown 水平线 → absent（走既有无锚语义），非坏、非 fail-closed。
        # 与「D2 只认文件首块」定义统一：无闭合 --- 不成块。
        return {}, None
```

- [ ] **Step 6: 退役 `unterminated` 死类别的 docstring 枚举（tasks.md 1.2）**

`sdflow-ship/scripts/ship_gate.py` 第 295 行，把：

```python
             category ∈ unterminated|duplicate-key|out-of-domain|bad-type|tab-indent
```

改为：

```python
             category ∈ duplicate-key|out-of-domain|bad-type|tab-indent
```

- [ ] **Step 7: 跑测试确认通过（绿）**

Run: `pytest sdflow-ship/tests/test_frontmatter_parse.py sdflow-ship/tests/test_gate_breaker.py -v`
Expected: PASS —— 全绿（含改写与新增用例）。

- [ ] **Step 8: grep 确认 `unterminated` 无任何产生路径（tasks.md 1.3）**

Run: `grep -rn "unterminated" sdflow-ship/scripts/ship_gate.py`
Expected: 空输出（源码零残留；若有仅剩历史注释亦可，但 Step 5/6 应已清尽）。再确认测试无残留断言：
Run: `grep -rn "unterminated" sdflow-ship/tests/`
Expected: 空输出。

- [ ] **Step 9: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p5-parser-cleanup:task1-parse-absent "首行 --- 无闭合改判 absent + unterminated 死类别退役 + anchor_set 不变量回归"
```

---

### Task 2: live 结构诊断提示 + 归档杂交盲区头注释登记

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（新增 `_unclosed_frontmatter_hint` helper；接入 design/code-review/verify 三读点的 emit reason；头注释登记归档盲区）
- Test: `sdflow-ship/tests/test_frontmatter_live_read.py`（live 三读点结构提示 + 三足对齐集成）
- Test: `sdflow-ship/tests/test_frontmatter_archived.py`（目标态归档 fail-safe 回归）

**Interfaces:**
- Consumes: `parse_ship_gate_frontmatter`（Task 1 已改，absent 语义）；三读点 emit 位——design（L697-700 REFUSE_START）、code-review（L769-771 STEP_IN_PROGRESS）、verify（L812-814 STEP_IN_PROGRESS）。
- Produces: `_unclosed_frontmatter_hint(path: Path) -> str`——首行 `---` 无闭合返回结构提示串（前缀「（结构提示：…）」），否则返回 `""`。**纯诊断**：不改 parse 签名、不改 verdict/退出码、不探测意图。

- [ ] **Step 1: 写 live 三读点结构提示的失败测试（tasks.md 1.5 + 3.1b 三足对齐，TC-2）**

在 `sdflow-ship/tests/test_frontmatter_live_read.py` 追加。该文件已 `from conftest import commit_all, mkchange`、`from test_gate_preflight import run_gate`、`from test_gate_tail import impl_done`。补一个不闭合 frontmatter 常量与三读点断言：

```python
UNCLOSED = "---\nship-gate:\n  design_approved: true\n无闭合横线，正文继续\n"


def test_live_unclosed_design_refuse_with_hint(repo):
    # [T74 1.5/3.1b] 首行 --- 无闭合的 spec-review-report → design 读点 absent → REFUSE_START(3)，
    # 且 emit reason 含结构提示子串（提醒补闭合行）。
    d = mkchange(repo)
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")  # 非嵌入式避 RUN_SOP
    d.joinpath("spec-review-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "未见闭合" in js["reason"]


def test_live_unclosed_code_review_step_in_progress_with_hint(repo):
    # [T74 3.1b] 同形态报告作 code-review-report → STEP_IN_PROGRESS(0)/next=sdflow-code-review，
    # 不 UNKNOWN(6)，reason 含结构提示。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "cr-unclosed")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-code-review"
    assert "未见闭合" in js["reason"]


def test_live_unclosed_verify_step_in_progress_with_hint(repo):
    # [T74 3.1b] 同形态报告作 verify-report → STEP_IN_PROGRESS(0)/next=sdflow-done，
    # **不 UNKNOWN(6)**（坐实无闭合首块不再硬崩），reason 含结构提示。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "verify-unclosed")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-done"
    assert "未见闭合" in js["reason"]
```

- [ ] **Step 2: 跑测试确认失败（红）**

Run: `pytest sdflow-ship/tests/test_frontmatter_live_read.py -k unclosed -v`
Expected: FAIL —— verdict/退出码断言可能已过（Task 1 后 absent 语义生效），但 `assert "未见闭合" in js["reason"]` 失败（提示尚未接入）。

- [ ] **Step 3: 新增 `_unclosed_frontmatter_hint` helper**

在 `sdflow-ship/scripts/ship_gate.py` 的 `live_ship_gate_state` 定义之后（约 L483 后、`TASK_TITLE_RE` 之前）插入：

```python
def _unclosed_frontmatter_hint(path):
    """[T74 1.5/spec-review Q1=A；design ADR-5] live 读点上层**独立轻量结构诊断**：
    报告首行为 '---' 但全文无第二个 '---'（首块不闭合，parse 判 absent）→ 返回结构提示串
    供 emit reason 追加。纯诊断——MUST NOT 改 parse 返回签名、MUST NOT 改 verdict/退出码、
    MUST NOT 探测意图（≠candidate②）。文件不存在 / 首行非 '---' / 已闭合 → 返回 ''（无提示）。
    与 parse 首块判据同口径（去 BOM、strip 后等值、只认第 2 行起首个 '---'），防诊断与解析漂移。"""
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    if any(lines[i].strip() == "---" for i in range(1, len(lines))):
        return ""                            # 已闭合 → 非本诊断场景（坏/有效由 parse 处置）
    return "（结构提示：首行为 `---` 但未见闭合 `---`，已按正文处理；欲声明状态请补闭合行）"
```

- [ ] **Step 4: 接入 design 读点（REFUSE_START）**

`sdflow-ship/scripts/ship_gate.py` 的 design 门 `if not design_ok:` 分支（约 L697-700），把 emit 的 reason 尾部追加提示。改为：

```python
    if not design_ok:
        emit("REFUSE_START", EXIT_REFUSE, None,
             "未过设计门：spec-review-report.md 缺失或无 design-approved 锚行；"
             "先完成设计门；若拍板已发生请人工补锚（显式越权留痕）"
             + _unclosed_frontmatter_hint(report))
```

- [ ] **Step 5: 接入 code-review 读点（STEP_IN_PROGRESS）**

`sdflow-ship/scripts/ship_gate.py` 的 `if cr_state is None:` 分支（约 L769-771），改为：

```python
    if cr_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-code-review",
             "code-review-report.md 在但无锚行 → 该步进行中，重跑"
             + _unclosed_frontmatter_hint(cr))
```

- [ ] **Step 6: 接入 verify 读点（STEP_IN_PROGRESS）**

`sdflow-ship/scripts/ship_gate.py` 的 `if v_state is None:` 分支（约 L812-814），改为：

```python
    if v_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-done",
             "verify-report.md 在但无锚行 → 该步进行中，重跑"
             + _unclosed_frontmatter_hint(vf))
```

- [ ] **Step 7: 头注释登记归档杂交盲区（tasks.md 1.4）**

在 `sdflow-ship/scripts/ship_gate.py` 文件头部的模块 docstring / 已知不覆盖登记区（若无则紧接 shebang+import 后的注释块）追加一段：

```python
# [T74/grill-amendment Q2] 已知不覆盖（登记越权盲区，非正常可达）：
#   「首行 --- 无闭合 × 归档 verify-report 正文独占一行 inline PASS 锚」杂交形态——
#   改判 absent 后 archived_verify_state 会回退 inline 扫到独占行 PASS → 判 pass。
#   但此形态**无 producer 产出**：目标态 producer 写 frontmatter 不写 inline，旧 producer
#   首行恒 '#' 非 '---'。须手工伪造归档才能构造 = 显式越权（git 留痕可审计，adr/0008/0011）。
#   目标态论证：迁移期评估安全锚 producer 契约而非现存语料快照（见 design ADR-4）。
```

- [ ] **Step 8: 写目标态归档 fail-safe 回归（tasks.md 3.5）**

先看 `sdflow-ship/tests/test_frontmatter_archived.py` 的既有 git fixture 口径（`archived_verify_state(root, ref, archive_dir)` 经 `git show` 读归档树）。在其末尾追加两个用例（沿用该文件既有的 `_git` / 建归档目录 + commit 模式；此处给出自足写法）：

```python
def test_archived_unclosed_no_inline_none(tmp_path):
    # [T74 3.5/目标态 fail-safe] 首行 --- 无闭合 + 正文无 inline 锚（模拟 producer 迁后漏闭合）
    # → parse 判 absent → 回退 inline 扫空 → archived_verify_state 判 'none'（不 SHIPPED，方向安全）。
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-08-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n无闭合横线，正文继续\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch-unclosed")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-08-demo") == "none"


def test_archived_unclosed_with_inline_pass_is_registered_blindspot(tmp_path):
    # [T74 3.5/登记盲区] 对照：首行 --- 无闭合 + 正文独占一行 inline PASS 锚 → 回退 inline
    # 扫到独占行 → 判 'pass'。**记录其为已登记越权盲区、非正常可达**（producer 不产此形态）。
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-08-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(
        "---\n无闭合首块\n" + _sg.ANCHOR_VERIFY_PASS + "\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch-hybrid")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-08-demo") == "pass"
```

> 注：若 `test_frontmatter_archived.py` 未定义模块级 `_git` / `_sg`，参照 `test_gate_anchor_scope.py` 顶部的 `_git`（subprocess 包装）与 importlib 加载 `_sg` 口径补上（勿 `import yaml`、勿改动既有用例）。

- [ ] **Step 9: 跑本 Task 相关测试确认通过（绿）**

Run: `pytest sdflow-ship/tests/test_frontmatter_live_read.py sdflow-ship/tests/test_frontmatter_archived.py -v`
Expected: PASS —— live 三读点结构提示 + 目标态归档 fail-safe 全绿。

- [ ] **Step 10: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p5-parser-cleanup:task2-live-hint "live 三读点结构诊断提示 + 归档杂交盲区头注释登记 + 目标态 fail-safe 回归"
```

---

### Task 3: T75 死符号删除 + 外科测试改写 + 收口验证

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（删 `anchors_in` L395-401、`pick_exclusive` L441-457、常量 `ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` L125/128/129，收缩 `ALL_ANCHORS` L130-131）
- Modify: `sdflow-ship/tests/test_gate_anchor_scope.py`（外科删孤儿测 + 改写语料契约，保留守卫测）
- Test（回归护）: `sdflow-ship/tests/test_frontmatter_archived.py`、全量 `sdflow-ship/tests/`

**Interfaces:**
- Consumes: `_line_scoped_hits`（保留）、`archived_verify_state`（保留）、`ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL`（保留）。
- Produces: `ALL_ANCHORS` 收缩为 `[ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL]`（仅 verify 锚）；`anchors_in`/`pick_exclusive`/`ANCHOR_DESIGN`/`ANCHOR_CR_PASS`/`ANCHOR_CR_BLOCKED` 全库不存在。

- [ ] **Step 1: 删前 grep 核实保留符号仅归档路径 + test 在用（tasks.md 2.3 保留边界）**

Run: `grep -rn "ANCHOR_VERIFY_PASS\|ANCHOR_VERIFY_FAIL\|_line_scoped_hits" sdflow-ship/scripts/ship_gate.py`
Expected: `ANCHOR_VERIFY_PASS`/`ANCHOR_VERIFY_FAIL` 出现在 `archived_verify_state`（L202/L205）与 `ALL_ANCHORS`；`_line_scoped_hits` 定义 + `archived_verify_state`/`anchors_in` 调用。确认 `archived_verify_state` 仍真用这两个 verify 锚（保留依据），`anchors_in`/`pick_exclusive` 仅剩定义 + test 引用（可删依据）。

Run: `grep -rn "anchors_in\|pick_exclusive" sdflow-ship/scripts/ship_gate.py`
Expected: 仅出现在各自 `def` 定义 + `_line_scoped_hits` docstring 提及（无运行时 `decide()` 调用点——Task6 已摘除）。

- [ ] **Step 2: 删死函数 `anchors_in` 与 `pick_exclusive`（tasks.md 2.1）**

删除 `sdflow-ship/scripts/ship_gate.py` 中整个 `def anchors_in(path, candidates):` 函数块（约 L395-401，连同其上方注释）与整个 `def pick_exclusive(path, positive, negative, label):` 函数块（约 L441-457）。删后确认 `emit` 函数（原 L430-438）保留、未被误删。

- [ ] **Step 3: 删死常量并收缩 `ALL_ANCHORS`（tasks.md 2.2）**

`sdflow-ship/scripts/ship_gate.py` 第 125-131 行，把：

```python
ANCHOR_DESIGN = "<!-- ship-gate: design-approved -->"
ANCHOR_VERIFY_PASS = "<!-- ship-gate: verify=PASS -->"
ANCHOR_VERIFY_FAIL = "<!-- ship-gate: verify=FAIL -->"
ANCHOR_CR_PASS = "<!-- ship-gate: code-review=pass -->"
ANCHOR_CR_BLOCKED = "<!-- ship-gate: code-review=blocked -->"
ALL_ANCHORS = [ANCHOR_DESIGN, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL,
               ANCHOR_CR_PASS, ANCHOR_CR_BLOCKED]
```

改为（只留归档 dual-read 真用的 verify 锚）：

```python
# [T75] design/code-review inline 锚常量已随 Task6 live inline 读半场退役而删除；
# 仅 verify 锚保留——archived_verify_state 的归档 dual-read 兜底旧 inline 现役唯一在用。
ANCHOR_VERIFY_PASS = "<!-- ship-gate: verify=PASS -->"
ANCHOR_VERIFY_FAIL = "<!-- ship-gate: verify=FAIL -->"
ALL_ANCHORS = [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL]
```

- [ ] **Step 4: 外科删孤儿测试（tasks.md 2.4/2.5 —— 用 anchors_in / pick_exclusive 的用例）**

`sdflow-ship/tests/test_gate_anchor_scope.py` 删除下列**仅测死符号存在性/行为**的用例（勿整文件删）：
- `test_inline_mention_not_hit`（L24-28，用 `anchors_in`）
- `test_fenced_anchor_not_hit`（L31-35，用 `anchors_in`）
- `test_standalone_anchor_hit`（L38-42，用 `anchors_in`）
- `test_conflict_multi_hit`（L45-50，用 `anchors_in`）
- `test_pick_exclusive_unbalanced_unknown`（L84-97，用 `pick_exclusive`）

**保留**（归档现役核心守卫，MUST NOT 波及）：`test_core_descriptive_pass_not_hit`（`_line_scoped_hits`）、`test_archived_descriptive_pass_none` / `test_archived_true_pass_and_conflict` / `test_archived_unbalanced_none`（`archived_verify_state`）、`test_decide_b4_board_refuse_start`、`test_contract_live_frontmatter_corpus_fields`。

- [ ] **Step 5: 外科改写语料契约 `test_contract_archived_corpus_anchor_hits`（tasks.md 2.5，BR-3）**

`sdflow-ship/tests/test_gate_anchor_scope.py` 的 `test_contract_archived_corpus_anchor_hits`（L134-154）中，`ALL_ANCHORS` 收缩为 verify-only 后 L150 用 `_sg.ALL_ANCHORS` 扫语料 + L153 `assert DESIGN in exclusive` 会 AssertionError（gate 从不从归档读 design/CR 锚）。改用局部 verify 锚列表扫语料、去 `DESIGN in exclusive` 断言。把这两行：

```python
        hits, _ = _sg._line_scoped_hits(text, _sg.ALL_ANCHORS)   # fence-aware 独占行判据
```
```python
    assert DESIGN in exclusive, "归档 spec-review 语料无一以独占行承载 design-approved——模板可能已去独占行"
    assert VPASS in exclusive or VFAIL in exclusive, "归档 verify 语料无一以独占行承载 verify=PASS/FAIL"
```

分别改为：

```python
        hits, _ = _sg._line_scoped_hits(text, [VPASS, VFAIL])   # [T75] verify-only 锚，fence-aware 独占行判据
```
```python
    # [T75/BR-3] gate 从不从归档读 design/CR 锚（那些 inline 读半场已退役），故只断言
    # verify 锚以独占行承载；原 `DESIGN in exclusive` 测的是 gate 消费不到的东西，删。
    assert VPASS in exclusive or VFAIL in exclusive, "归档 verify 语料无一以独占行承载 verify=PASS/FAIL"
```

- [ ] **Step 6: 收口 grep —— 死符号零残留（tasks.md 3.4）**

Run: `grep -rn "anchors_in\|pick_exclusive\|ANCHOR_DESIGN\|ANCHOR_CR_PASS\|ANCHOR_CR_BLOCKED" sdflow-ship/scripts/ sdflow-ship/tests/`
Expected: 空输出（源码 + 测试零残留引用）。若命中仅剩 `test_gate_preflight.py` / `test_gate_terminal.py` / `test_frontmatter_live_read.py` 的**历史注释性提及**（非代码调用，如 "pick_exclusive 后不再可达"），须一并把注释里的死符号名订正/移除，确保输出为空。

- [ ] **Step 7: 收口 grep —— 三调用方未误删（tasks.md 3.4，BR-1/adr-0011）**

Run: `grep -n "parse_ship_gate_frontmatter" sdflow-ship/scripts/ship_gate.py`
Expected: 列出定义 + 三个调用方 `live_ship_gate_state`、`archived_verify_state`、`anchor_set` 均在（尤其 `anchor_set` 是活 API，不在删除名单）。

- [ ] **Step 8: 归档 dual-read 不回归 + 全量 pytest（tasks.md 3.3 + 3.4 全绿）**

Run: `pytest sdflow-ship/tests/ -q`
Expected: 全绿，0 warning。特别确认 `test_frontmatter_archived.py`（88 归档兼容用例）+ `test_gate_anchor_scope.py` 改写后的语料契约通过，`ANCHOR_VERIFY_PASS/FAIL` + `_line_scoped_hits` 删除清理未波及、SHIPPED 判定不变。

- [ ] **Step 9: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh mlh-p5-parser-cleanup:task3-dead-symbols "删死符号 anchors_in/pick_exclusive/3 常量 + 收缩 ALL_ANCHORS + 外科改写语料契约 + 收口全绿"
```

---

## 测试覆盖图（TG-18；与 tasks.md 对齐）

```
code path                                          → 测试类型                        → Task
──────────────────────────────────────────────────────────────────────────────────────
parse: 首行 --- 无闭合 → ({}, None)                → 单元回归 (3.1a/3.2)             → 1
anchor_set(第三调用方): 无闭合 → frozenset()       → 熔断不变量回归 (3.6·BR-1/TC-1)  → 1
live 三读点: 无闭合 → design REFUSE_START(3) /       → 集成三足 (3.1b·TC-2)            → 2
            code-review·verify STEP_IN_PROGRESS(0)/不 UNKNOWN + 结构提示子串
archived: 漏闭合 frontmatter(无 inline) → none      → 目标态归档 fail-safe (3.5)      → 2
archived: 漏闭合 + 独占 inline PASS → pass(登记盲区) → 对照 (3.5)                     → 2
死符号删除 → 零残留引用 + 三调用方在                → grep 门 (3.4)                   → 3
test_gate_anchor_scope 语料契约(ALL_ANCHORS 收缩)   → 外科改写不压垮 (2.5·BR-3)       → 3
归档 dual-read inline 兼容(既有 88 用例)            → 全量 pytest 回归护 (3.3)        → 3
──────────────────────────────────────────────────────────────────────────────────────
保留未变（回归护，不测新）: 首块成立后坏 → UNKNOWN(6)、重复键 → UNKNOWN、
                        归档 frontmatter 读、命名空间/复选框完成判据
```

## Self-Review

- **Spec coverage**：tasks.md 全 15 子项（1.1-1.5、2.1-2.5、3.1-3.6）均有对应 Task 步骤——1.1→T1S5、1.2→T1S6、1.3→T1S8、1.4→T2S7、1.5→T2S3-6、2.1→T3S2、2.2→T3S3、2.3→T3S1、2.4→T3S4、2.5→T3S4-5、3.1→T1S2/T2S1、3.2→T1S1、3.3→T3S8、3.4→T3S6-8、3.5→T2S8、3.6→T1S3。
- **Placeholder scan**：每处改代码均给出完整前后对照，无 TBD/TODO。
- **Type consistency**：`parse_ship_gate_frontmatter` 签名 `(state, error)` 全程不变；`_unclosed_frontmatter_hint(path) -> str` 在 T2 定义、T2 三读点消费，命名一致；`ALL_ANCHORS` 收缩后仅 T3S5 的语料契约与 `archived_verify_state` 消费，均已对齐 verify-only。
