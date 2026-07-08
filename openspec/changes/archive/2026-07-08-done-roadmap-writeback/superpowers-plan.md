# done-roadmap-writeback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 sdflow-done 加 roadmap 回填降摩擦助手——done 收尾读盘面生成 roadmap 回填草稿进 hand-off，机械搬运（定位到 phase）自动化、判断（勾哪几行）留人。

**Architecture:** 机械核 = `sdflow-done/scripts/roadmap_writeback_draft.py`（stdlib-only、确定性、fail-closed、pytest 覆盖）；编排 = `sdflow-done/SKILL.md` 第二步加 §2.2 子步调脚本把草稿写进 hand-off + 第六步摘要抬一行。切分线：定位到 phase（change 名前缀 `implement-{roadmap}-pN` 确定性信号 → 机械）；勾哪几行/价值叙述（判断 → 人）。

**Tech Stack:** Python 3 stdlib（argparse/re/pathlib）+ pytest；Markdown skill 编排。

## Global Constraints

以下为 design.md 领域约束，每个 task 隐含遵守（逐字自 design/spec-review-report）：

- **切分线（P-2）**：定位到 **phase**（change 名前缀 `implement-{roadmap}-pN` 确定性编码 roadmap+phase）= 机械；这个 change 勾该 phase **哪几行** / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred = 判断留人。助手只产**阶段级候选行集**，MUST NOT 产 per-行「建议勾」。
- **时序（P-1）**：草稿机械锚只含步2（hand-off）已实现事实（verify=PASS / tasks 完成态 / change 名 / 分支 / pytest 数[有则取无则 N/A]）；archive 路径（步3，含日期）/ merge（步5）在草稿生成时尚不存在，MUST 留占位「待归档后由人补」，MUST NOT 当盘面预填。
- **格式分形态 fail-loud（P-3）**：探测目标 roadmap 承载形态——复选框式（`- [ ] {id}`）→ 定位该 phase 候选行集；表格/散文式（`| ✅` 无复选框）→ 不产复选框草稿、fail-loud 告知留人工（非静默退现状）。
- **detection fence-aware（P-5）**：marker 检测 MUST fence-aware（跳 code fence/行内 code/缩进码块）+ 行锚定（marker 独占一行、整行匹配）+ 排除 change 自身讨论区——防本 change 8 处产物字面含 marker 串致假阳。
- **坏输入三分（C-9）**：absent（verify-report 缺/无 frontmatter）→ 留人工；malformed（frontmatter 未闭合/重复 verify 键/坏枚举）→ fail-closed 标畸形；verify≠PASS → 不出完成候选。三态各有独立退出码 + 场景。
- **关联优先级（C-6）**：`--roadmap` > marker > change 名前缀；多通道不一致 → warn（反静默，不静默取默认）。
- **不碰 change 产物文件（C1）**：助手 MUST NOT 写 change 的 tasks.md/proposal.md 等产物；只读盘面 + 输出草稿文本（由 SKILL 编排写进 hand-off）。
- **确定性**：脚本 stdlib-only、纯函数核心无墙钟/随机；同盘面输入 → 同骨架输出（archive/merge 为静态占位串、非当前日期）。
- **反静默**：未声明但疑似 roadmap 驱动 SHOULD 提示；定位不到/非复选框格式 fail-loud，不静默。

**载体决策（T10 客观判据）**：机械核实现为 Python 脚本（非纯 done 指令步）——客观判据=C-9 坏输入三分须 pytest 覆盖 + P-5 fence-aware 须可测，只有脚本路径提供自动化测试；对齐本仓 sdflow-issues 数据类 skill 模式。

---

### Task 1: change 名前缀解析 `parse_prefix`

**Files:**
- Create: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Produces: `parse_prefix(change_name: str) -> tuple[str, str] | None` — `implement-{roadmap}-pN-*` → `(roadmap, phase)`；不符前缀返回 None。

- [ ] **Step 1: Write the failing test**

```python
# sdflow-done/tests/test_roadmap_writeback_draft.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import roadmap_writeback_draft as rwd


def test_parse_prefix_real_change_name():
    # 真实归档样本：implement-mechanical-layer-hardening-p4-lens-metric-emit
    assert rwd.parse_prefix(
        "implement-mechanical-layer-hardening-p4-lens-metric-emit"
    ) == ("mechanical-layer-hardening", "4")


def test_parse_prefix_no_suffix():
    assert rwd.parse_prefix("implement-workflow-cost-optimization-p2") == (
        "workflow-cost-optimization",
        "2",
    )


def test_parse_prefix_non_matching_returns_none():
    assert rwd.parse_prefix("done-roadmap-writeback") is None
    assert rwd.parse_prefix("add-user-auth") is None
    assert rwd.parse_prefix("implement-foo") is None  # 无 -pN
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q`
Expected: FAIL（`ModuleNotFoundError` 或 `AttributeError: parse_prefix`）

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""roadmap_writeback_draft.py — sdflow-done roadmap 回填降摩擦助手机械核.

机械搬运（定位到 phase + 盘面读 + 骨架拼），判断（勾哪几行/价值叙述）留人.
切分线: 定位到 phase = 机械（change 名前缀确定性信号）; 勾哪几行 = 判断留人.
stdlib-only, 确定性（无墙钟/随机）, fail-closed.
"""
import re

# change 名前缀 implement-{roadmap}-pN-* ; roadmap 可含横杠, -p\d+ 作定界, 可选尾缀
PREFIX_RE = re.compile(r"^implement-(?P<roadmap>.+)-p(?P<phase>\d+)(?:-.+)?$")


def parse_prefix(change_name):
    """implement-{roadmap}-pN-* → (roadmap, phase); 不符返回 None."""
    m = PREFIX_RE.match(change_name.strip())
    if not m:
        return None
    return (m.group("roadmap"), m.group("phase"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（3 passed, 0 warning）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task1-parse-prefix "change 名前缀 implement-{roadmap}-pN 解析(P-2 确定性信号) + 3 测试"
```

---

### Task 2: fence-aware marker 检测 `detect_markers`（P-5 防自指核心）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Consumes: 无
- Produces: `strip_code_fences(text: str) -> str`；`detect_markers(text: str) -> list[tuple[str, str]]` — 仅返回 fence 外、行锚定（整行匹配）、独占一行的 `<!-- roadmap: {name}#{phase} -->`。

- [ ] **Step 1: Write the failing test**

```python
def test_detect_markers_solo_line():
    text = "前言\n<!-- roadmap: mechanical-layer-hardening#4 -->\n后文"
    assert rwd.detect_markers(text) == [("mechanical-layer-hardening", "4")]


def test_detect_markers_self_ref_defense():
    # P-5: marker 串在行内 code(反引号) / 散文中 → 不误检测（本 change 自身即如此）
    prose = "- change 声明关联：一行 `<!-- roadmap: {name}#{phase} -->`（或 done --roadmap）"
    assert rwd.detect_markers(prose) == []


def test_detect_markers_inside_code_fence_ignored():
    text = "```\n<!-- roadmap: foo#1 -->\n```\n正文"
    assert rwd.detect_markers(text) == []


def test_detect_markers_indented_code_block_ignored():
    text = "正文\n    <!-- roadmap: foo#1 -->\n更多"
    assert rwd.detect_markers(text) == []


def test_detect_markers_placeholder_name_not_matched():
    # 字面占位 {name} 非 [a-z0-9-] → 不匹配
    text = "<!-- roadmap: {name}#{phase} -->"
    assert rwd.detect_markers(text) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k detect_markers`
Expected: FAIL（`AttributeError: detect_markers`）

- [ ] **Step 3: Write minimal implementation**

追加到 `roadmap_writeback_draft.py`：

```python
# marker 整行匹配: <!-- roadmap: {name}#{phase} -->  (name=小写字母数字横杠, phase=数字)
MARKER_RE = re.compile(
    r"^<!--\s*roadmap:\s*(?P<roadmap>[a-z0-9][a-z0-9-]*)#(?P<phase>\d+)\s*-->$"
)


def strip_code_fences(text):
    """去掉 ``` / ~~~ 围栏码块内容, 使其中 marker 不被检测."""
    out = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def detect_markers(text):
    """fence-aware + 行锚定 + 独占一行的 marker 检测(P-5 防自指).
    返回 [(roadmap, phase), ...]; fence 内/缩进码块/行内 code/散文行一律忽略."""
    result = []
    for line in strip_code_fences(text).splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue  # markdown 缩进码块
        stripped = line.strip()
        m = MARKER_RE.match(stripped)  # 整行匹配 → 散文/行内 code 不命中
        if m:
            result.append((m.group("roadmap"), m.group("phase")))
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（8 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task2-fence-aware-marker "fence-aware+行锚定 marker 检测(P-5 消 C-5 自指坑) + 5 测试(含自指防御)"
```

---

### Task 3: 关联解析 + 优先级 `resolve_association`（C-6）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Consumes: `parse_prefix`, `detect_markers`
- Produces: `resolve_association(change_name, proposal_text, tasks_text, flag=None) -> dict | None` — 返回 `{"roadmap","phase","source","warnings":[...]}`（source ∈ prefix/marker/flag）或 None（无关联）。优先级 flag > marker > prefix。

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_prefix_only():
    a = rwd.resolve_association(
        "implement-mechanical-layer-hardening-p4-x", "", "", None
    )
    assert a["roadmap"] == "mechanical-layer-hardening"
    assert a["phase"] == "4"
    assert a["source"] == "prefix"
    assert a["warnings"] == []


def test_resolve_flag_overrides_prefix_with_warning():
    a = rwd.resolve_association(
        "implement-foo-p1-x", "", "", "bar#2"
    )
    assert (a["roadmap"], a["phase"], a["source"]) == ("bar", "2", "flag")
    assert len(a["warnings"]) == 1  # foo#1(prefix) vs bar#2(flag) 不一致 warn


def test_resolve_marker_fallback_when_prefix_absent():
    proposal = "<!-- roadmap: wco#3 -->"
    a = rwd.resolve_association("done-roadmap-writeback", proposal, "", None)
    assert (a["roadmap"], a["phase"], a["source"]) == ("wco", "3", "marker")


def test_resolve_none_when_no_signal():
    assert rwd.resolve_association("done-roadmap-writeback", "散文无 marker", "", None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k resolve`
Expected: FAIL（`AttributeError: resolve_association`）

- [ ] **Step 3: Write minimal implementation**

追加：

```python
FLAG_RE = re.compile(r"^(?P<roadmap>[a-z0-9][a-z0-9-]*)#(?P<phase>\d+)$")


def resolve_association(change_name, proposal_text, tasks_text, flag=None):
    """优先级 flag > marker > prefix; 多通道不一致 warn. 无信号返回 None."""
    candidates = {}  # source -> (roadmap, phase)
    prefix = parse_prefix(change_name)
    if prefix:
        candidates["prefix"] = prefix
    markers = detect_markers(proposal_text) + detect_markers(tasks_text)
    if markers:
        candidates["marker"] = markers[0]
    if flag:
        fm = FLAG_RE.match(flag.strip())
        if fm:
            candidates["flag"] = (fm.group("roadmap"), fm.group("phase"))
    if not candidates:
        return None
    for source in ("flag", "marker", "prefix"):
        if source in candidates:
            chosen_source = source
            break
    chosen = candidates[chosen_source]
    warnings = []
    for source, val in candidates.items():
        if val != chosen:
            warnings.append(
                "关联不一致: %s=%s#%s vs 采纳 %s=%s#%s"
                % (source, val[0], val[1], chosen_source, chosen[0], chosen[1])
            )
    return {
        "roadmap": chosen[0],
        "phase": chosen[1],
        "source": chosen_source,
        "warnings": warnings,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（12 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task3-resolve-association "关联解析+优先级 flag>marker>prefix+不一致 warn(C-6) + 4 测试"
```

---

### Task 4: 盘面读取 + 坏输入三分（P-1 时序 / C-9）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Produces: `read_verify_state(change_dir) -> tuple[str, str|None]` — state ∈ {good, absent, malformed}；good 时第二元 ∈ {PASS, FAIL}。`read_tasks_completion(change_dir) -> tuple[int, int]` — (done, total)。

- [ ] **Step 1: Write the failing test**

```python
def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_verify_state_good_pass(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nship-gate:\n  verify: PASS\n---\n# r\n")
    assert rwd.read_verify_state(tmp_path) == ("good", "PASS")


def test_verify_state_absent_when_missing(tmp_path):
    assert rwd.read_verify_state(tmp_path) == ("absent", None)


def test_verify_state_absent_when_no_frontmatter(tmp_path):
    _write(tmp_path, "verify-report.md", "# 无 frontmatter\nPASS\n")
    assert rwd.read_verify_state(tmp_path) == ("absent", None)


def test_verify_state_malformed_unclosed(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nship-gate:\n  verify: PASS\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_verify_state_malformed_duplicate_key(tmp_path):
    _write(tmp_path, "verify-report.md",
           "---\nverify: PASS\nverify: FAIL\n---\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_verify_state_malformed_bad_enum(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nverify: MAYBE\n---\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_tasks_completion_counts(tmp_path):
    _write(tmp_path, "tasks.md", "- [x] a\n- [x] b\n- [ ] c\n普通行\n")
    assert rwd.read_tasks_completion(tmp_path) == (2, 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k "verify_state or tasks_completion"`
Expected: FAIL（`AttributeError`）

- [ ] **Step 3: Write minimal implementation**

追加（顶部 import 加 `from pathlib import Path`）：

```python
from pathlib import Path  # 若文件顶部尚无, 加到 import re 下方


def read_verify_state(change_dir):
    """读 verify-report.md 的 ship-gate frontmatter verify 字段.
    返回 (state, value): state ∈ {good, absent, malformed}.
    absent=文件缺/无首块 frontmatter; malformed=未闭合/无 verify/重复键/坏枚举."""
    path = Path(change_dir) / "verify-report.md"
    if not path.exists():
        return ("absent", None)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ("absent", None)
    fm, closed = [], False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        fm.append(line)
    if not closed:
        return ("malformed", None)
    vals = [m.group(1) for m in (re.match(r"^\s*verify:\s*(\S+)\s*$", ln) for ln in fm) if m]
    if len(vals) != 1:
        return ("malformed", None)  # 0=无字段, >1=重复键
    if vals[0] not in ("PASS", "FAIL"):
        return ("malformed", None)  # 坏枚举
    return ("good", vals[0])


def read_tasks_completion(change_dir):
    """tasks.md 复选框 (done, total)."""
    path = Path(change_dir) / "tasks.md"
    if not path.exists():
        return (0, 0)
    done = total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("- [x]") or s.startswith("- [X]"):
            done += 1
            total += 1
        elif s.startswith("- [ ]"):
            total += 1
    return (done, total)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（19 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task4-board-read "盘面读取 verify 三态(good/absent/malformed, C-9)+tasks 完成态 + 7 测试"
```

---

### Task 5: roadmap 形态探测 + phase 候选行定位（P-3）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Produces: `probe_format(roadmap_text: str) -> str` — 'checkbox' | 'table-prose'。`locate_phase_rows(roadmap_text: str, phase: str) -> list[str]` — 该 phase（`N.*`）下**未勾** `- [ ]` 候选行，整行原样。

- [ ] **Step 1: Write the failing test**

```python
CHECKBOX_ROADMAP = (
    "- [x] 1.A.1 done item\n"
    "- [ ] 4.A.1 phase4 待办甲\n"
    "- [x] 4.C.1 phase4 已交付\n"
    "- [ ] 4.D.1 phase4 待办乙\n"
    "- [ ] 5.A.1 phase5 待办\n"
)
TABLE_ROADMAP = (
    "| **P1** · x | Leg 1 | — | ✅ 已交付 |\n"
    "| **P2** · y | Leg 2 | P0 | 🔄 |\n"
    "- 脚本：散文 bullet 无复选框\n"
)


def test_probe_format_checkbox():
    assert rwd.probe_format(CHECKBOX_ROADMAP) == "checkbox"


def test_probe_format_table_prose():
    assert rwd.probe_format(TABLE_ROADMAP) == "table-prose"


def test_locate_phase_rows_only_unchecked_of_phase():
    rows = rwd.locate_phase_rows(CHECKBOX_ROADMAP, "4")
    assert rows == ["- [ ] 4.A.1 phase4 待办甲", "- [ ] 4.D.1 phase4 待办乙"]
    # 已勾 4.C.1 不入候选; 别的 phase(1/5) 不入


def test_locate_phase_rows_empty_when_none():
    assert rwd.locate_phase_rows(CHECKBOX_ROADMAP, "9") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k "probe_format or locate_phase"`
Expected: FAIL（`AttributeError`）

- [ ] **Step 3: Write minimal implementation**

追加：

```python
def probe_format(roadmap_text):
    """任一行以 `- [ ]`/`- [x]` 开头 → checkbox; 否则 table-prose(P-3)."""
    for line in roadmap_text.splitlines():
        if re.match(r"^- \[[ xX]\]", line):
            return "checkbox"
    return "table-prose"


def locate_phase_rows(roadmap_text, phase):
    """该 phase(N.*) 下未勾 `- [ ]` 候选行(整行原样); 只 checkbox 式.
    只定位到 phase 行集(机械), 不判勾哪几行(留人)."""
    pat = re.compile(r"^- \[ \] " + re.escape(phase) + r"\.")
    return [ln.rstrip() for ln in roadmap_text.splitlines() if pat.match(ln)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（23 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task5-format-probe "roadmap 形态探测(checkbox/table-prose, P-3)+phase 候选行定位(只定位到 phase 不判勾哪行) + 4 测试"
```

---

### Task 6: 草稿拼装 `assemble_draft`（P-1 占位 / P-4 锚 / 确定性）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Consumes: `resolve_association` 的返回 dict
- Produces: `assemble_draft(assoc, verify_value, tasks_done, tasks_total, change_name, branch, fmt, candidate_rows, pytest_count=None) -> str` — hand-off 回填草稿文本；archive/merge 为静态占位串（确定性、非当前日期）。

- [ ] **Step 1: Write the failing test**

```python
def _assoc(source="prefix", warnings=None):
    return {"roadmap": "mlh", "phase": "4", "source": source, "warnings": warnings or []}


def test_assemble_draft_checkbox_has_mechanical_anchors_and_placeholders():
    out = rwd.assemble_draft(
        _assoc(), "PASS", 5, 5, "implement-mlh-p4-x", "feat/x",
        "checkbox", ["- [ ] 4.A.1 甲"], pytest_count=39
    )
    assert "change: `implement-mlh-p4-x`" in out
    assert "verify: PASS" in out
    assert "5/5" in out
    assert "pytest: 39" in out
    assert "- [ ] 4.A.1 甲" in out  # 候选行集
    # P-1: archive/merge 占位不预填当前日期
    assert "<待归档后由人补>" in out
    assert "<待 merge 后由人补>" in out
    # P-2: 不产 per-行"建议勾"(措辞), 只列候选行集供人判
    assert "建议勾" not in out


def test_assemble_draft_table_prose_fail_loud():
    out = rwd.assemble_draft(
        _assoc(), "PASS", 3, 3, "implement-wco-p2-y", "feat/y",
        "table-prose", [], pytest_count=None
    )
    assert "fail-loud" in out or "非复选框格式" in out
    assert "pytest: N/A" in out


def test_assemble_draft_warnings_surfaced():
    out = rwd.assemble_draft(
        _assoc(source="flag", warnings=["关联不一致: prefix=a#1 vs 采纳 flag=b#2"]),
        "PASS", 1, 1, "c", "b", "checkbox", [], None
    )
    assert "关联不一致" in out


def test_assemble_draft_deterministic():
    args = (_assoc(), "PASS", 2, 2, "c", "b", "checkbox", ["- [ ] 4.A.1 甲"], 10)
    assert rwd.assemble_draft(*args) == rwd.assemble_draft(*args)  # 同输入同输出
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k assemble`
Expected: FAIL（`AttributeError`）

- [ ] **Step 3: Write minimal implementation**

追加：

```python
def assemble_draft(assoc, verify_value, tasks_done, tasks_total, change_name,
                   branch, fmt, candidate_rows, pytest_count=None):
    """拼 hand-off 回填草稿. 机械锚只填步2 已实现事实; archive/merge 静态占位(P-1).
    只列候选行集(机械), 勾哪几行/价值叙述留人(P-2)."""
    roadmap, phase = assoc["roadmap"], assoc["phase"]
    pytest_str = str(pytest_count) if pytest_count is not None else "N/A（纯 Markdown 或未采集）"
    lines = [
        "### ▶ roadmap 回填草稿（%s#%s，关联来源: %s）" % (roadmap, phase, assoc["source"]),
        "",
        "> 助手机械搬运（定位到 phase + 盘面锚），**判断留人**：勾哪几行 / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred。",
    ]
    for w in assoc.get("warnings", []):
        lines.append("> ⚠ %s" % w)
    lines += [
        "",
        "**机械锚（步2 已实现事实）**：",
        "- change: `%s`" % change_name,
        "- verify: %s" % verify_value,
        "- tasks 完成态: %d/%d" % (tasks_done, tasks_total),
        "- 分支: `%s`" % branch,
        "- pytest: %s" % pytest_str,
        "- archive 路径: `<待归档后由人补>`  ◀ P-1 预测值不预填",
        "- merge: `<待 merge 后由人补>`",
        "",
    ]
    if fmt == "checkbox":
        if candidate_rows:
            lines.append("**候选复选框行集（phase %s，请人判断勾哪几行）**：" % phase)
            lines.extend(candidate_rows)
        else:
            lines.append("**候选复选框**：phase %s 下未定位到未勾复选框行——请人工核对。" % phase)
    else:
        lines.append("**⚠ fail-loud**：目标 roadmap 为非复选框格式（表格/散文式），助手不产复选框草稿——复选框/状态回填请人工。")
    lines += [
        "",
        "**task-log 完成总结骨架（价值叙述留人补）**：",
        "- [%s] %s#%s：<一句交付摘要，人补> — verify %s, %d/%d tasks, merge `<待补>`"
        % (change_name, roadmap, phase, verify_value, tasks_done, tasks_total),
        "  - 价值（grill/冷审/defer/耗时）：<人补>",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -W error`
Expected: PASS（27 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task6-assemble-draft "草稿拼装(机械锚+archive/merge占位 P-1, 候选行集不判勾 P-2, fail-loud P-3, 确定性) + 4 测试"
```

---

### Task 7: CLI `main` + 退出码 + dogfood 集成（自指跳过 / 两形态）

**Files:**
- Modify: `sdflow-done/scripts/roadmap_writeback_draft.py`
- Test: `sdflow-done/tests/test_roadmap_writeback_draft.py`

**Interfaces:**
- Consumes: 上述全部函数
- Produces: `main(argv=None) -> int` — 退出码：0=草稿产出、2=change dir 缺、3=无关联(退现状)、4=盘面 absent/roadmap 缺(留人工)、5=malformed(fail-closed)、6=verify≠PASS。草稿 → stdout；诊断 → stderr。

- [ ] **Step 1: Write the failing test**

```python
import subprocess

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "roadmap_writeback_draft.py")


def _run(root, change, extra=None):
    cmd = ["python3", SCRIPT, "--change", change, "--root", str(root), "--branch", "feat/t"]
    if extra:
        cmd += extra
    return subprocess.run(cmd, capture_output=True, text=True)


def _mk_change(root, name, verify="PASS", proposal="", tasks="- [x] a\n- [ ] b\n"):
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True)
    if verify is not None:
        (d / "verify-report.md").write_text(
            "---\nship-gate:\n  verify: %s\n---\n" % verify, encoding="utf-8")
    (d / "proposal.md").write_text(proposal, encoding="utf-8")
    (d / "tasks.md").write_text(tasks, encoding="utf-8")
    return d


def _mk_roadmap(root, name, text):
    d = root / "openspec" / "roadmaps" / name
    d.mkdir(parents=True)
    (d / "roadmap.md").write_text(text, encoding="utf-8")


def test_main_happy_checkbox(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-x")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-x")
    assert r.returncode == 0
    assert "roadmap 回填草稿" in r.stdout
    assert "- [ ] 4.A.1" in r.stdout


def test_main_no_association_returns_3(tmp_path):
    # dogfood 自指: change 名非 implement-* 前缀 + proposal 内 marker 仅在散文/行内 code
    _mk_change(tmp_path, "done-roadmap-writeback",
               proposal="轻量标记 `<!-- roadmap: {name}#{phase} -->` 兜底")
    r = _run(tmp_path, "done-roadmap-writeback")
    assert r.returncode == 3  # 无关联 → 退现状(P-5 fence-aware 未误检测)


def test_main_table_prose_fail_loud_still_exit0(tmp_path):
    _mk_change(tmp_path, "implement-wco-p2-y")
    _mk_roadmap(tmp_path, "wco", TABLE_ROADMAP)
    r = _run(tmp_path, "implement-wco-p2-y")
    assert r.returncode == 0
    assert "fail-loud" in r.stdout or "非复选框格式" in r.stdout


def test_main_malformed_board_returns_5(tmp_path):
    d = _mk_change(tmp_path, "implement-mlh-p4-z", verify=None)
    (d / "verify-report.md").write_text("---\nverify: MAYBE\n---\n", encoding="utf-8")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-z")
    assert r.returncode == 5


def test_main_verify_fail_returns_6(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-w", verify="FAIL")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-w")
    assert r.returncode == 6


def test_main_board_absent_returns_4(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-v", verify=None)  # 无 verify-report
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-v")
    assert r.returncode == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest sdflow-done/tests/test_roadmap_writeback_draft.py -q -k main`
Expected: FAIL（`main` 未定义 / SystemExit）

- [ ] **Step 3: Write minimal implementation**

追加（顶部加 `import argparse`, `import subprocess`, `import sys`）：

```python
def _git_branch(root):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "<unknown>"


def main(argv=None):
    p = argparse.ArgumentParser(description="roadmap 回填降摩擦助手机械核")
    p.add_argument("--change", required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--roadmap", default=None, help="{name}#{phase} 覆写(优先级最高)")
    p.add_argument("--branch", default=None)
    p.add_argument("--pytest-count", type=int, default=None)
    args = p.parse_args(argv)

    root = Path(args.root)
    change_dir = root / "openspec" / "changes" / args.change
    if not change_dir.exists():
        sys.stderr.write("CHANGE_DIR_MISSING %s\n" % change_dir)
        return 2

    proposal = change_dir / "proposal.md"
    tasks = change_dir / "tasks.md"
    proposal_text = proposal.read_text(encoding="utf-8") if proposal.exists() else ""
    tasks_text = tasks.read_text(encoding="utf-8") if tasks.exists() else ""

    assoc = resolve_association(args.change, proposal_text, tasks_text, args.roadmap)
    if assoc is None:
        sys.stderr.write("NO_ASSOCIATION 未声明关联且名前缀不符 → 退现状(不产草稿)\n")
        return 3

    state, verify_value = read_verify_state(change_dir)
    if state == "absent":
        sys.stderr.write("BOARD_ABSENT verify-report 缺/无 frontmatter → 留人工\n")
        return 4
    if state == "malformed":
        sys.stderr.write("BOARD_MALFORMED verify frontmatter 畸形 → fail-closed 留人工\n")
        return 5
    if verify_value != "PASS":
        sys.stderr.write("VERIFY_NOT_PASS verify=%s → 不出完成候选\n" % verify_value)
        return 6

    roadmap_path = root / "openspec" / "roadmaps" / assoc["roadmap"] / "roadmap.md"
    if not roadmap_path.exists():
        sys.stderr.write("ROADMAP_MISSING %s → 留人工\n" % roadmap_path)
        return 4
    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    fmt = probe_format(roadmap_text)
    rows = locate_phase_rows(roadmap_text, assoc["phase"]) if fmt == "checkbox" else []

    tasks_done, tasks_total = read_tasks_completion(change_dir)
    branch = args.branch or _git_branch(root)
    draft = assemble_draft(assoc, verify_value, tasks_done, tasks_total,
                           args.change, branch, fmt, rows, args.pytest_count)
    sys.stdout.write(draft + "\n")
    for w in assoc["warnings"]:
        sys.stderr.write("WARN %s\n" % w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest sdflow-done/tests/ -q -W error`
Expected: PASS（33 passed, 0 warning）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task7-cli-main "CLI main+退出码 0/2/3/4/5/6(坏输入三分 C-9)+dogfood 自指跳过(P-5)+两形态集成 + 6 测试"
```

---

### Task 8: sdflow-done/SKILL.md 编排集成（§2.2 子步 + 第六步摘要 + 设计原则）

**Files:**
- Modify: `sdflow-done/SKILL.md`

**Interfaces:**
- Consumes: `sdflow-done/scripts/roadmap_writeback_draft.py`（脚本路径经 sibling 约定 `~/.claude/skills/sdflow-done/scripts/`）

- [ ] **Step 1: 在第二步 §2.1 sweep 之后加 §2.2 roadmap 回填助手子步**

在 `sdflow-done/SKILL.md` 第 147 行（§2.1 结尾「别为了兜孤儿放宽 `--change` 过滤。」）之后、第 149 行 `---` 之前，插入：

```markdown

### 2.2 roadmap 回填降摩擦助手子步（§2.1 之后、写 hand-off 三段之前）〔done-roadmap-writeback〕

verify 判完之后，跑 roadmap 回填助手机械核生成回填草稿，供人异步确认回填 roadmap（切分线：**定位到 phase 机械、勾哪几行判断留人**）。主 session 直接跑（纯机械脚本）。

**脚本路径**（sibling 约定，同 §2.1）：`~/.claude/skills/sdflow-done/scripts/roadmap_writeback_draft.py`（兜底 `~/.codex/skills/…` 或本仓 `find . -name roadmap_writeback_draft.py`）。

```bash
python3 ~/.claude/skills/sdflow-done/scripts/roadmap_writeback_draft.py \
  --change {change_name} --root . 2>/tmp/rwd_err; echo "exit=$?"; cat /tmp/rwd_err
```

**退出码处置（遵脚本判定，不静默）**：
- `0` → stdout 即回填草稿，**原样贴进 hand-off.md 的「▶ 下一阶段建议」段**（作 roadmap 回填草稿子块）；stderr 有 `WARN 关联不一致` 则一并转述。
- `3`（无关联，退现状）→ change 非 roadmap 驱动，**不产草稿**；若分支名/change 名疑似 roadmap 驱动，hand-off 留一行「未检测到 roadmap 关联标记；若属某 roadmap 请手动回填」（反静默 SHOULD）。
- `4`（盘面 absent / roadmap 缺）/ `5`（frontmatter 畸形 fail-closed）/ `6`（verify≠PASS）→ hand-off 记一行「roadmap 回填草稿未生成：<stderr 原因>，请人工」（**不静默、不伪造**）。
- `2`（change dir 缺）→ 异常，停下核对。

**判断留人**：草稿只列 phase 候选行集 + 机械锚（archive/merge 占位），**勾哪几行 / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred 由人在异步回填时判**——助手 MUST NOT 代判、MUST NOT 直接改 roadmap、MUST NOT 写 change 产物文件（避 C1）。
```

- [ ] **Step 2: 第六步摘要抬一行（P-4 异步闭环可见）**

在第 280 行 `Merge:` 行之后、`Push:` 行之前插入一行（模板内）：

```
  Roadmap: ⚠ 回填草稿待人确认（见 hand-off「▶ 下一阶段建议」）｜— 无关联
```

- [ ] **Step 3: 设计原则区登记（§2.2 + 同位不同性）**

在第 299 行（issues sweep 设计原则条）之后追加一条：

```markdown
- **roadmap 回填助手（§2.2，done-roadmap-writeback）**：verify 之后跑 `roadmap_writeback_draft.py` 生成 roadmap 回填草稿进 hand-off + 第六步摘要抬一行（merge 时点可见）；**与 §2.1 issues sweep 同位不同性**——同为 done 收尾盘面消费，但 sweep 机械终写机器独占文件（INDEX）、roadmap 回填**助人确认**（完成判定含判断，写入语义相反，不诱导复用 sweep 自动落盘）。切分线：定位到 phase=机械（change 名前缀确定性信号）、勾哪几行=判断留人；archive/merge 预测值留占位不预填（P-1）；detection fence-aware 防自指（P-5）；非复选框格式 fail-loud（P-3）。**残差登记**：草稿产出即止、apply 由人异步、不保证（经 /sdflow-ship 全自动链人被支走时尤然）。
```

- [ ] **Step 4: 核验 SKILL.md 一致性 + setup.sh（脚本落链）**

Run:
```bash
grep -n "roadmap_writeback_draft\|### 2.2\|Roadmap:" sdflow-done/SKILL.md
bash setup.sh 2>&1 | tail -3
ls ~/.claude/skills/sdflow-done/scripts/roadmap_writeback_draft.py
```
Expected: §2.2/摘要行/设计原则均命中；setup.sh 幂等成功；脚本经 symlink 可达（sdflow-done 首次有 scripts/，symlink 指向源即时生效）。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh done-roadmap-writeback:task8-skill-integration "sdflow-done/SKILL.md §2.2 回填助手子步+第六步摘要抬行(P-4)+设计原则(同位不同性 C-7)+setup.sh 落链"
```

---

## 测试覆盖图（TG-18）

```
code path                                  测试类型             task
─────────────────────────────────────────  ──────────────────  ────
change 名前缀 implement-{roadmap}-pN 解析    pytest              1
fence-aware marker 检测·防自指(fence/散文)   pytest ★关键        2
关联优先级 flag>marker>prefix·不一致 warn    pytest              3
盘面 verify 三态 good/absent/malformed(C-9)  pytest              4
tasks 完成态计数                            pytest              4
形态探测 checkbox/table-prose(P-3)           pytest              5
phase 候选行定位(只定位不判勾)               pytest              5
草稿机械锚+archive/merge 占位(P-1)+确定性     pytest              6
CLI 退出码 0/2/3/4/5/6(坏输入三分)            pytest(subprocess)  7
dogfood 自指跳过(P-5)+两形态集成             pytest(subprocess)  7
SKILL §2.2 子步+第六步摘要+设计原则          静态核对+setup      8
```

## Self-Review

- **Spec coverage**：R1（回填助手·定位到 phase 机械/勾哪几行判断）→ task1-8；R2（关联解析·前缀主/marker 兜底 fence-aware/漏退现状）→ task1-3,7。P-1 时序→task4/6；P-2 切分线→task1/5/6；P-3 格式→task5/6/7；P-4 闭环→task8；P-5 自指→task2/7；C-6→task3；C-8 pytest 锚→task6（N/A 处理）；C-9 三分→task4/7；C-12 反静默→task8（exit3 SHOULD 提示）；C1 不碰产物→task7/8（只读+stdout）。全覆盖。
- **Placeholder scan**：无 TBD/TODO；每步含完整代码/命令/期望。
- **Type consistency**：`resolve_association` 返回 dict `{roadmap,phase,source,warnings}` 在 task3 定义、task6/7 消费一致；`read_verify_state` 返回 `(state, value)` task4 定义、task7 消费一致；`assemble_draft` 签名 task6 定义、task7 调用参数顺序一致。

---

**执行**：本 plan 由 /sdflow-ship 链自动以 subagent-driven-development 执行——每任务 fresh 子代理 TDD、逐任务 checkpoint（命名空间标签 `done-roadmap-writeback:task<N>-<slug>`）、final whole-branch 终审附 `code-checklists/domains/backend` 额外 lens。无法自动解决记入 buglists/todolists。
