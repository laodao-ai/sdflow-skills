# gate-anchor-line-scoped 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `ship_gate.py` 的三处子串检测（`anchors_in`、`archived_verify_state`、`tg02_hit`）从裸 `x in text` 收紧为行级/声明式匹配，堵住「描述性提及被误判为真锚/真触发」的假阳（B4 + dogfood tg02），并为互斥锚对补未闭合 fence 保守判定。

**Architecture:** 抽一个文本级核心 `_line_scoped_hits(text, candidates) -> (hits, unbalanced)`（逐行 `strip()` 等值 + fence 翻转跳过，复用既有 `_parse_plan` 的 `line.lstrip().startswith("```")` 惯例）。`anchors_in` 读文件后调核心（单锚调用方只取 hits）；互斥锚对调用方 `pick_exclusive`/`archived_verify_state` 直接调核心并消费 `unbalanced`（真→保守 UNKNOWN/none）。`tg02_hit` 独立改为声明式 `〔TG-02` 匹配。

**Tech Stack:** 纯 Python 3（标准库 re/pathlib/subprocess）+ pytest。单文件 gate 脚本 `sdflow-ship/scripts/ship_gate.py`，测试 `sdflow-ship/tests/`。

## Global Constraints

- 每任务 commit 步 MUST 用命名空间格式：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task<N>-<slug> "<msg>"`（gate 完成判据主锚；`<change>`=gate-anchor-line-scoped）。
- 定位脚本/文件 MUST 用仓根相对或 `Path(__file__).resolve().parents[N]`，MUST NOT 硬编码绝对路径。
- 保「字面查找（非正则）」：行级用 `str.strip() ==` 等值，fence 用 `str.startswith`，MUST NOT 给锚检测引入正则。
- `anchors_in(path, candidates)` 对外仍返回 **list**（`X in anchors_in(...)` 的既有调用方 :408/:478 不得破）；`unbalanced` 只经核心 `_line_scoped_hits` 或直接调用方获取。
- 退出码语义、锚字面集（`ANCHOR_*` 常量）、JSON 字段不变。
- 仓级 pytest 基线 **350** 不回归（`pytest` 全绿）。
- 单元测试导入 ship_gate 用 importlib 按路径加载（同 `test_producer_parser_contract.py`，无副作用——`__main__` 守卫）。集成测试用既有 `conftest.py` 的 `repo`/`commit_all`/`mkchange` fixture 与 `run_gate`。

---

### Task 1: `_line_scoped_hits` 核心 + `anchors_in` 行锚定（ADR-1/2/4）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（`anchors_in` :198-203 改写 + 上方新增 `_line_scoped_hits`）
- Create: `sdflow-ship/tests/test_gate_anchor_scope.py`

**Interfaces:**
- Produces: `_line_scoped_hits(text: str, candidates: list[str]) -> tuple[list[str], bool]`（hits 按 candidates 原序去重；bool = EOF 时 in_fence 未闭合）；`anchors_in(path, candidates) -> list[str]`（行为收紧、签名不变）。

- [ ] **Step 1: 写失败测试（新文件 header + 4 例）**

```python
# sdflow-ship/tests/test_gate_anchor_scope.py
"""锚检测行锚定 + fence-aware（B4）：anchors_in / _line_scoped_hits。"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)   # __main__ 守卫，加载无副作用

DESIGN = "<!-- ship-gate: design-approved -->"
VPASS = "<!-- ship-gate: verify=PASS -->"
VFAIL = "<!-- ship-gate: verify=FAIL -->"


def test_inline_mention_not_hit(tmp_path):
    # B4 活体复现：锚内联在描述句中（行内反引号），非独占一行 → 不命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_fenced_anchor_not_hit(tmp_path):
    # 锚独占一行但在 ``` 代码块内作文档示例 → 不命中（ADR-2）
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论区\n```\n{DESIGN}\n```\n正文无真锚\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_standalone_anchor_hit(tmp_path):
    # 独占一行的真锚（前后可有空白）→ 命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论\n\n   {DESIGN}   \n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == [DESIGN]


def test_conflict_multi_hit(tmp_path):
    # PASS 与 FAIL 各独占一行并存 → 两者皆命中（保 ADR-3 多命中）
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    got = _sg.anchors_in(f, [VPASS, VFAIL])
    assert VPASS in got and VFAIL in got
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -v`
Expected: `test_inline_mention_not_hit` / `test_fenced_anchor_not_hit` FAIL（旧子串会命中描述性提及）；后两例可能已过。

- [ ] **Step 3: 实现 `_line_scoped_hits` + 改写 `anchors_in`**

在 `ship_gate.py` 把 `anchors_in`（当前 :198-203）替换为：

```python
def _line_scoped_hits(text, candidates):
    """文本级行锚定核心（零正则）：候选须独占一行（strip 后等值），忽略 fenced code block。
    返回 (hits[按 candidates 原序去重], unbalanced[EOF 时围栏未闭合])。
    anchors_in（读文件）与 pick_exclusive/archived_verify_state（互斥锚对）共用〔ADR-4/5〕。
    fence 翻转口径同 _parse_plan（line.lstrip().startswith("```")）。"""
    cand = set(candidates)
    hit = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = line.strip()
        if s in cand:
            hit.add(s)
    return [a for a in candidates if a in hit], in_fence


def anchors_in(path, candidates):
    """行级字面查找（零正则）：机判锚 MUST 独占一行（strip 后等值）、忽略 ``` 代码块——
    描述性提及/文档示例不触发〔B4/ADR-1/2〕。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")  # 非 UTF-8 防崩
    return _line_scoped_hits(text, candidates)[0]
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -v`
Expected: 4 例 PASS。

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_gate_anchor_scope.py
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task1-line-scoped-core "抽 _line_scoped_hits 核心 + anchors_in 行锚定+fence-aware"
```

---

### Task 2: `archived_verify_state` 折入共用核心（ADR-4）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（`archived_verify_state` :134-146）
- Test: `sdflow-ship/tests/test_gate_anchor_scope.py`（增）

**Interfaces:**
- Consumes: `_line_scoped_hits`（Task 1）。
- Produces: `archived_verify_state(root, ref, archive_dir) -> "conflict"|"pass"|"none"`（三态不变，检测维从子串→行级）。

- [ ] **Step 1: 写失败测试（核心单元 + git fixture 端到端）**

```python
# 追加到 test_gate_anchor_scope.py
import subprocess

def _git(root, *a):
    subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True)


def test_core_descriptive_pass_not_hit():
    # 核心单元：描述性提及 PASS 的文本 → hits 不含 PASS
    text = f"归档说明：曾写过 `{VPASS}` 但后撤。\n```\n{VPASS}\n```\n"
    hits, unbalanced = _sg._line_scoped_hits(text, [VPASS, VFAIL])
    assert VPASS not in hits


def test_archived_descriptive_pass_none(tmp_path):
    # 端到端：git fixture，归档 verify-report 仅描述性提及 PASS（无真锚）→ archived_verify_state 判 none
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"结论待定；模板锚示例：`{VPASS}`。\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "arch")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"


def test_archived_true_pass_and_conflict(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "pass")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "pass"
    (d / "verify-report.md").write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "conflict")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "conflict"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -k archived -v`
Expected: `test_archived_descriptive_pass_none` FAIL（旧裸子串判 pass）。

- [ ] **Step 3: 实现 `archived_verify_state` 折入核心**

把 `archived_verify_state` 的判定两行替换（保留 rc!=0 早返 + 三态分派）：

```python
    rc, out = run_git_rc(root, "show",
                         f"{ref}:openspec/changes/archive/{archive_dir}/verify-report.md")
    if rc != 0:
        return "none"
    hits, _ = _line_scoped_hits(out, [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL])  # [ADR-4] 行级，非子串
    has_pass, has_fail = ANCHOR_VERIFY_PASS in hits, ANCHOR_VERIFY_FAIL in hits
    if has_pass and has_fail:
        return "conflict"
    return "pass" if has_pass else "none"
```

（unbalanced 信号 Task 3 才消费，此处先 `_` 忽略。）

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -k "archived or core" -v`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_gate_anchor_scope.py
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task2-archived-fold "archived_verify_state 折入 _line_scoped_hits 共用核心"
```

---

### Task 3: 未闭合 fence → 互斥锚对保守判定（ADR-5 · OV-2）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（`pick_exclusive` :217-227、`archived_verify_state` unbalanced 分支）
- Test: `sdflow-ship/tests/test_gate_anchor_scope.py`（增）

**Interfaces:**
- Consumes: `_line_scoped_hits`（返回 `(hits, unbalanced)`）、`emit`、`EXIT_UNKNOWN`。
- Produces: `pick_exclusive` 遇 unbalanced → emit UNKNOWN；`archived_verify_state` 遇 unbalanced → "none"。

- [ ] **Step 1: 写失败测试**

```python
# 追加到 test_gate_anchor_scope.py
import pytest

def test_pick_exclusive_unbalanced_unknown(tmp_path):
    # 正锚在 fence 外 + 未闭合 ``` + 负锚在内被吞 → 不得判 pass，须 UNKNOWN
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")   # ``` 未闭合
    with pytest.raises(SystemExit) as e:
        _sg.pick_exclusive(f, VPASS, VFAIL, "verify")
    assert e.value.code == _sg.EXIT_UNKNOWN


def test_archived_unbalanced_none(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-07-05-demo"
    d.mkdir(parents=True)
    (d / "verify-report.md").write_text(f"{VPASS}\n```\n{VFAIL}\n", encoding="utf-8")
    _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-q", "-m", "unb")
    assert _sg.archived_verify_state(tmp_path, "main", "2026-07-05-demo") == "none"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -k unbalanced -v`
Expected: 两例 FAIL（当前吞 FAIL → 判 pass）。

- [ ] **Step 3: 实现 unbalanced 消费**

`pick_exclusive` 改为自读文件 + 消费 unbalanced：

```python
def pick_exclusive(path, positive, negative, label):
    """互斥锚对解析：两者并存 / 未闭合 fence → UNKNOWN（不猜）。返回 'pos'/'neg'/None。"""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    found, unbalanced = _line_scoped_hits(text, [positive, negative])
    if unbalanced:   # [ADR-5] 未闭合 fence 可吞负锚 → 保守不判 pass
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告含未闭合 fence（``` 悬空），无法可靠判定互斥锚，请人工修复围栏后重试")
    if positive in found and negative in found:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告并存冲突锚行（{positive} 与 {negative}），请人工裁决删除其一")
    if positive in found:
        return "pos"
    if negative in found:
        return "neg"
    return None
```

`archived_verify_state` 把 Task 2 的 `hits, _ = ...` 改为消费 unbalanced：

```python
    hits, unbalanced = _line_scoped_hits(out, [ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL])
    if unbalanced:   # [ADR-5] 保守：未闭合 fence 不判 SHIPPED
        return "none"
    has_pass, has_fail = ANCHOR_VERIFY_PASS in hits, ANCHOR_VERIFY_FAIL in hits
```

- [ ] **Step 4: 跑测试确认通过 + pick_exclusive 平衡回归**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -v`
Expected: 全 PASS。

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_gate_anchor_scope.py
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task3-unbalanced-fence "未闭合 fence → pick_exclusive/archived 保守判定(ADR-5)"
```

---

### Task 4: `tg02_hit` 声明式匹配（ADR-6 · dogfood）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（`tg02_hit` :234-237）
- Test: `sdflow-ship/tests/test_gate_impl_progress.py`（增；若既有 tg02 fixture 用裸 `TG-02` 须同步改）

**Interfaces:**
- Produces: `tg02_hit(cdir) -> bool`（匹配声明式 `〔TG-02`，非裸子串）。

- [ ] **Step 1: 写失败测试**

```python
# 追加到 test_gate_impl_progress.py（沿用其既有 import 惯例载 ship_gate 为 _sg / 或 importlib）
def test_tg02_descriptive_mention_not_hit(tmp_path):
    from conftest import mkchange
    d = mkchange(tmp_path, "demo")
    # 描述性提及 / 代码引用 / 否定句，无 〔TG-02 声明
    d.joinpath("proposal.md").write_text(
        '讨论 `\"TG-02\" in` 检测；技术栈 TG-01/02/03 均不命中。\n', encoding="utf-8")
    assert _sg.tg02_hit(d) is False


def test_tg02_declaration_hit(tmp_path):
    from conftest import mkchange
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text("〔TG-02：嵌入式固件变更〕\n", encoding="utf-8")
    assert _sg.tg02_hit(d) is True
```

> 若 `test_gate_impl_progress.py` 无 `_sg`/ship_gate 载入，按 Task 1 的 importlib 头补一份；`mkchange` 来自 conftest。

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-ship/tests/test_gate_impl_progress.py -k tg02 -v`
Expected: `test_tg02_descriptive_mention_not_hit` FAIL（旧裸子串命中 `"TG-02"`）。

- [ ] **Step 3: 实现声明式匹配**

```python
def tg02_hit(cdir):
    p = cdir / "proposal.md"
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8", errors="replace")  # 非 UTF-8 防崩
    # [ADR-6] 声明式匹配（全角括号头注 〔TG-NN：，ff 强制格式），非裸子串——
    # 描述性提及/代码引用/否定句(TG-01/02/03)不触发假 RUN_SOP（dogfood B4 类）
    return "〔TG-02" in text
```

- [ ] **Step 4: 跑测试确认通过 + 既有 tg02 回归**

Run: `pytest sdflow-ship/tests/test_gate_impl_progress.py -v`
Expected: 全 PASS。若既有 tg02/RUN_SOP 用例用裸 `TG-02` 造 proposal 而变红 → 把其 fixture 改为 `〔TG-02：` 声明形（真嵌入式盘面），再跑绿。

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_gate_impl_progress.py
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task4-tg02-declaration "tg02_hit 声明式 〔TG-02 匹配(ADR-6)"
```

---

### Task 5: 端到端 B4 + 头注释契约 + 契约测试（§3）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（头注释契约表 :5-60 区）
- Test: `sdflow-ship/tests/test_gate_anchor_scope.py`（端到端 + 契约样本）

**Interfaces:**
- Consumes: `run_gate`（`test_gate_preflight`）、`conftest` 的 `mkchange`/`commit_all`。

- [ ] **Step 1: 写端到端 + 契约测试**

```python
# 追加到 test_gate_anchor_scope.py
import sys, json
GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"

def _run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change, "--root", str(root)],
                       capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    return r.returncode, (json.loads(lines[-1]) if lines else {})


def test_decide_b4_board_refuse_start(tmp_path):
    # B4 盘面：spec-review-report 仅描述性提及 design-approved（无独占锚）→ REFUSE_START
    from conftest import mkchange, commit_all
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "t"); _git(tmp_path, "config", "user.email", "t@t")
    d = mkchange(tmp_path, "demo")
    d.joinpath("proposal.md").write_text("〔TG-25：契约〕\n", encoding="utf-8")   # 非嵌入式，避免 RUN_SOP
    d.joinpath("spec-review-report.md").write_text(
        f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    commit_all(tmp_path, "seed")
    code, js = _run_gate(tmp_path)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_contract_archived_corpus_anchor_hits():
    # 契约：归档真实报告语料的独占锚行 → _line_scoped_hits 命中（防模板假设静默失效）
    # 样本源 = 归档 corpus（实证 15/15 独占顶格），非 SKILL 展示块
    archive = REPO / "openspec" / "changes" / "archive"
    samples = list(archive.glob("*/spec-review-report.md")) + \
              list(archive.glob("*/verify-report.md")) + \
              list(archive.glob("*/code-review-report.md"))
    assert samples, "无归档报告语料"
    for f in samples:
        text = f.read_text(encoding="utf-8", errors="replace")
        for anc in _sg.ALL_ANCHORS:
            if anc in text:   # 该报告含此锚（子串层）
                hits, _ = _sg._line_scoped_hits(text, [anc])
                assert anc in hits, f"{f.name} 的真锚 {anc} 行级判据下漏检——模板锚未独占一行?"
```

- [ ] **Step 2: 跑测试确认（B4 先红或已绿视实现）**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -k "b4 or contract" -v`
Expected: `test_decide_b4_board_refuse_start` PASS（Task1 已修 anchors_in）；`test_contract_archived_corpus_anchor_hits` PASS。

- [ ] **Step 3: 更新头注释契约表**

在 `ship_gate.py` 头注释「已知不覆盖」区补：①机判锚 MUST 独占一行（行级等值 + 忽略 ``` 代码块），两处解析点（anchors_in / archived_verify_state）共用 `_line_scoped_hits`；②互斥锚对遇未闭合 fence → 保守 UNKNOWN/none（ADR-5）；③tg02 声明式 `〔TG-02` 匹配（ADR-6）；④多行 HTML 注释内嵌锚不解析（人为构造，显式越权同权级）；⑤`~~~`/带语言标签围栏误判不特判（安全侧假阴）。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-ship/tests/test_gate_anchor_scope.py -v`
Expected: 全 PASS。

- [ ] **Step 5: Commit**

```bash
git add sdflow-ship/scripts/ship_gate.py sdflow-ship/tests/test_gate_anchor_scope.py
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task5-e2e-contract "端到端 B4 REFUSE_START + 契约样本(归档 corpus) + 头注释"
```

---

### Task 6: 全量回归 + 收敛（§4）

**Files:**
- Test: 无新增；跑全量。
- Modify: buglist（B4 → FIXED）。

- [ ] **Step 1: 跑 ship 测试套 + 仓级全量**

Run: `pytest sdflow-ship/tests/ -q && pytest -q`
Expected: `sdflow-ship/tests/` 全绿；仓级基线 350 + 本 change 新增用例，**0 failed**。若某既有用例因锚/tg02 收紧变红 → 按 Task 3/4 的回归条款核对 fixture（真锚独占 / `〔TG-02` 声明），非削弱断言。

- [ ] **Step 2: 跑 gate 确认 tg02 假 RUN_SOP 已消**

Run: `python3 sdflow-ship/scripts/ship_gate.py --change gate-anchor-line-scoped --root "$(git rev-parse --show-toplevel)"`
Expected: **不再** RUN_SOP（tg02_hit 声明式后本 change proposal 无 `〔TG-02` → SKIP）；应为 RUN_CODE_REVIEW 或 RUN_VERIFY 等推进态（视完成判据）。

- [ ] **Step 3: buglist B4 → FIXED**

```bash
python3 ~/.claude/skills/sdflow-buglist/scripts/buglist.py set-status --id B4 --to FIXED \
  --evidence "gate-anchor-line-scoped; test_gate_anchor_scope.py::test_inline_mention_not_hit + anchors_in 行锚定"
```

> 注：B4 记录在 main 分支的 buglist（feat 落后）。若 feat 上 `set-status` 撞号/找不到 B4，改在收尾（sdflow-done）后于 main 处理，或 hand-off 记明。实现者遇此**停下报告**，不强改。

- [ ] **Step 4: Commit**

```bash
git add -A
bash ~/.sdflow/hack/checkpoint-commit.sh gate-anchor-line-scoped:task6-regression "全量回归绿 + gate tg02 假阳消 + B4→FIXED"
```

---

## Self-Review 结论

- **Spec 覆盖**：ADR-1/2 → Task1；ADR-4 → Task2；ADR-5 → Task3；ADR-6 → Task4；spec delta 两条 B4 Scenario + SHIPPED-path + unbalanced Scenario + tg02 Scenario → Task1/2/3/4/5；契约测试 → Task5；回归 → Task6。无 spec 需求缺 task。
- **类型一致**：`_line_scoped_hits` 全程返回 `(list, bool)`；`anchors_in` 返回 `list`（Task1 定义，Task5 契约测试消费 `[0]`）；`archived_verify_state` 三态 str；`tg02_hit` bool——各 Task 引用一致。
- **无占位符**：每步含实际代码/命令；已知残差（B4 跨分支 set-status）显式标「停下报告」而非 TODO。
