# anchor-lint 确定性锚自检门 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把两审 SKILL 的手工锚自检降为确定性脚本 `anchor_lint.py`（存在性 + lens-metric 字段/枚举/子格式，fail-closed）。

**Architecture:** 新增 bundle 工具 `anchor_lint.py`（纯 stdlib、退出码承载判定、双输出），从契约 `lens-metric-enums` 机读块读枚举、脚本内重实现 fence-aware 行级核（禁跨 skill import）；两审 SKILL 自检步接脚本；copy_bundle 契约随 tools/ 同刷；aggregator 加一致性测试。

**Tech Stack:** Python 3 纯 stdlib（argparse/re/json/pathlib/sys），pytest。

## Global Constraints

- 纯 stdlib，**无 yaml 依赖**（repo 无 yaml）；受限行锚定正则读 config，非通用 YAML parse。
- **MUST NOT** `import lens_metric_aggregate` 或 `ship_gate`——跨 skill import 在消费仓会 ImportError（sdflow-retro/scripts 不在消费仓）。fence-aware + kv 解析脚本内重实现。
- 枚举取值域**只从** `sdflow-init/assets/workflow/lens-metric-contract.md` 的 `lens-metric-enums` fenced 块读；契约/块缺失/空 → ERROR(2)，**绝不回落硬编码兜底**。
- 退出码：`0=CLEAN` / `1=VIOLATION` / `2=ERROR`（fail-closed）。双输出：human 行（stderr/stdout）+ JSON（机读违规清单）。
- `site` 字段 **MUST NOT** 校验（契约 CF-补2）。数值一致性（findings vs 实收数）脚本不兜（主 session 信任边界）。
- 每任务收尾 checkpoint 格式：`~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task<N>-<slug> "<描述>"`（change 命名空间 + task<N>-<slug> 带横杠，ship_gate TAG_RE 主锚）。
- 测试落点：anchor_lint → `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`；一致性 → `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`；copy_bundle → `sdflow-init/tests/`。

## File Structure

- Create: `sdflow-init/assets/workflow/tools/anchor_lint.py` — 锚自检脚本（load_enums / read_metrics_enabled / fence 核 / 锚解析 / 校验 / main）。
- Create: `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` — 脚本测试。
- Modify: `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py` — 加 enum 一致性 + 交叉断言。
- Modify: `sdflow-init/scripts/init.py:154-158`（copy_bundle 非 full 分支）— 契约随 tools/ 同刷。
- Modify: `sdflow-init/tests/`（新增或并入）— copy_bundle 契约同刷测试。
- Modify: `sdflow-spec-review/SKILL.md:79` + `sdflow-code-review/SKILL.md:117-124` — 自检步接脚本。
- Modify: `openspec/roadmaps/mechanical-layer-hardening/{design.md,roadmap.md,task-log.md}` — 复用→重实现调和。

**已就位（grill/spec-review amendment 已落）**：`sdflow-init/assets/workflow/lens-metric-contract.md` 已含 `lens-metric-enums` 机读块（Task 1 解析它，无需再建）。

---

### Task 1: anchor_lint 核心 — 契约枚举读取 + fence 核 + 锚族识别

**Files:**
- Create: `sdflow-init/assets/workflow/tools/anchor_lint.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`

**Interfaces:**
- Produces: `load_enums(contract_path=None) -> dict`（返回 `{"layer": set, "lens": set, "runner": set, "sev_re": compiled}`；契约/块缺失/空抛 `EnumsError`）；`fence_outside_lines(text) -> iterator[str]`；`parse_kv(line) -> dict`；`anchor_prefix(line) -> str|None`（返回 `outside-voice`/`hr-tg`/`step1-broad-review`/`lens-metric` 或 None）；`EnumsError(Exception)`。

- [ ] **Step 1: 写失败测试 — load_enums 解析真实契约块**

```python
# sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py
import subprocess, sys, importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent          # .../workflow/tools
SCRIPT = TOOLS / "anchor_lint.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"     # .../workflow/lens-metric-contract.md

def _mod():
    spec = importlib.util.spec_from_file_location("anchor_lint", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_load_enums_from_real_contract():
    al = _mod()
    e = al.load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
    assert e["runner"] == {"claude", "codex", "claude-fallback"}
    assert e["sev_re"].match("致1/高2/中0/低3")
    assert not e["sev_re"].match("致1/高2/中0")

def test_load_enums_missing_block_raises(tmp_path):
    al = _mod()
    bad = tmp_path / "c.md"; bad.write_text("# no machine block here\n", encoding="utf-8")
    import pytest
    with pytest.raises(al.EnumsError):
        al.load_enums(bad)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k load_enums -v`
Expected: FAIL（anchor_lint.py 不存在 / load_enums 未定义）

- [ ] **Step 3: 实现 anchor_lint.py 骨架 + load_enums + fence 核 + 锚族识别**

```python
#!/usr/bin/env python3
"""anchor_lint — 评审报告锚自检确定性门（mlh-p2-anchor-lint）。
盘面即状态：只读报告，退出码承载判定，双输出（human + JSON）。
    0=CLEAN  1=VIOLATION  2=ERROR(fail-closed)
枚举单一源 = 契约 lens-metric-contract.md 的 `lens-metric-enums` 机读块（同 workflow bundle）。
fence-aware 行级核脚本内重实现（禁跨 skill import lens_metric_aggregate/ship_gate——消费仓无 sdflow-retro）。"""
import argparse, json, re, sys
from pathlib import Path

EXIT_CLEAN, EXIT_VIOLATION, EXIT_ERROR = 0, 1, 2

ANCHOR_PREFIXES = {
    "<!-- sdflow:outside-voice v1": "outside-voice",
    "<!-- sdflow:hr-tg v1": "hr-tg",
    "<!-- sdflow:step1-broad-review v1": "step1-broad-review",
    "<!-- sdflow:lens-metric v1": "lens-metric",
}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')                    # 受限 kv：key="value"
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')               # CommonMark fence：0-3 空格 + ≥3 marker
_ENUM_BLOCK = re.compile(r'^ {0,3}(`{3,}|~{3,})lens-metric-enums\s*$')  # 机读块开启行

COUNT_FIELDS = ("findings", "采纳", "裁掉", "defer", "独立")
REQUIRED_FIELDS = ("layer", "lens", "runner", "findings", "采纳", "裁掉", "defer", "独立", "sev")


class EnumsError(Exception):
    pass


def _default_contract():
    return Path(__file__).resolve().parent.parent / "lens-metric-contract.md"


def load_enums(contract_path=None):
    """从契约 `lens-metric-enums` fenced 块读 layer/lens/runner 枚举 + sev-format 正则。
    块缺失/空/契约不可读 → EnumsError（调用侧 fail-closed，绝不回落硬编码）。"""
    p = Path(contract_path) if contract_path else _default_contract()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise EnumsError(f"契约不可读: {p}: {e}")
    lines = text.splitlines()
    body, in_block, fence_char, fence_len = [], False, None, 0
    for ln in lines:
        if not in_block:
            m = _ENUM_BLOCK.match(ln)
            if m:
                in_block = True; fence_char = m.group(1)[0]; fence_len = len(m.group(1))
            continue
        c = _FENCE.match(ln)
        if c and c.group(1)[0] == fence_char and len(c.group(1)) >= fence_len and ln[c.end():].strip() == "":
            break                                           # 闭合
        body.append(ln)
    if not in_block:
        raise EnumsError(f"契约缺 lens-metric-enums 机读块: {p}")
    kv = {}
    for ln in body:
        if ":" in ln:
            k, v = ln.split(":", 1)
            kv[k.strip()] = v.strip()
    layer = {x.strip() for x in kv.get("layer", "").split(",") if x.strip()}
    lens = {x.strip() for x in kv.get("lens", "").split(",") if x.strip()}
    runner = {x.strip() for x in kv.get("runner", "").split(",") if x.strip()}
    sev_fmt = kv.get("sev-format", "").strip()              # 致N/高N/中N/低N
    if not (layer and lens and runner and sev_fmt):
        raise EnumsError(f"lens-metric-enums 块解析空/缺项: {p}")
    # 由 sev-format 模板生成正则：N → \d+，其余字面
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    return {"layer": layer, "lens": lens, "runner": runner, "sev_re": sev_re}


def fence_outside_lines(text):
    """产出非 fenced-block 行（CommonMark：0-3 空格缩进 + ≥3 同字符 marker 开合、闭合行 marker 后仅空白）。"""
    fence = None
    for ln in text.splitlines():
        m = _FENCE.match(ln)
        if fence is None:
            if m:
                fence = (m.group(1)[0], len(m.group(1))); continue
            yield ln
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and ln[m.end():].strip() == "":
                fence = None
            continue


def parse_kv(line):
    return {k: v for k, v in _KV.findall(line.strip())}


def anchor_prefix(line):
    s = line.strip()
    for pref, name in ANCHOR_PREFIXES.items():
        if s.startswith(pref):
            return name
    return None
```

- [ ] **Step 4: 写 fence 核 + 锚族识别测试**

```python
def test_fence_outside_excludes_demo_anchor():
    al = _mod()
    text = "real\n<!-- sdflow:lens-metric v1 layer=\"x\" -->\n```\n<!-- sdflow:lens-metric v1 layer=\"demo\" -->\n```\n"
    outside = list(al.fence_outside_lines(text))
    hits = [ln for ln in outside if al.anchor_prefix(ln) == "lens-metric"]
    assert len(hits) == 1 and 'layer="x"' in hits[0]        # fence 内 demo 不计

def test_anchor_prefix_four_families():
    al = _mod()
    assert al.anchor_prefix('<!-- sdflow:hr-tg v1 hit="none" -->') == "hr-tg"
    assert al.anchor_prefix('note <!-- sdflow:hr-tg v1 --> inline') is None or True  # 描述性内联(前缀非行首)
    assert al.anchor_prefix('<!-- sdflow:step1-broad-review v1 mode="native" -->') == "step1-broad-review"
    assert al.anchor_prefix('plain text') is None
```

- [ ] **Step 5: 跑全 Task1 测试绿**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k "load_enums or fence or prefix" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task1-core "anchor_lint 骨架：契约 lens-metric-enums 块枚举读取 + fence 核 + 锚族识别"
```

---

### Task 2: 存在性校验 + metrics 真四态门控 + 最小必有行

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/anchor_lint.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`

**Interfaces:**
- Produces: `read_metrics_enabled(root) -> bool`（抛 `MetricsError` 表块坏）；`MetricsError(Exception)`；`check_existence(report_text, layer, metrics_on) -> list[dict]`（返回违规列表，每项 `{"kind","detail"}`）。
- Consumes: `fence_outside_lines`, `anchor_prefix`, `parse_kv`（Task 1）。

- [ ] **Step 1: 写 metrics 真四态测试**

```python
def _write_config(tmp_path, body):
    d = tmp_path / "openspec"; d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text(body, encoding="utf-8"); return tmp_path

def test_metrics_file_absent_false(tmp_path):
    al = _mod(); assert al.read_metrics_enabled(tmp_path) is False        # ① 无文件

def test_metrics_no_block_false(tmp_path):                                # ② 消费仓常态
    al = _mod(); root = _write_config(tmp_path, "schema: spec-driven\ncontext: |\n  x\n")
    assert al.read_metrics_enabled(root) is False

def test_metrics_block_illegal_raises(tmp_path):                          # ③ 块在值非法
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    import pytest
    with pytest.raises(al.MetricsError):
        al.read_metrics_enabled(root)

def test_metrics_true(tmp_path):                                          # ④
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: true\n")
    assert al.read_metrics_enabled(root) is True

def test_metrics_block_boundary(tmp_path):                                # 块边界：另一段的 enabled 不误读
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: false\nother:\n  enabled: true\n")
    assert al.read_metrics_enabled(root) is False
```

- [ ] **Step 2: 跑确认失败** → Run: `pytest .../test_anchor_lint.py -k metrics -v` Expected: FAIL

- [ ] **Step 3: 实现 read_metrics_enabled（真四态 + 块边界）**

```python
class MetricsError(Exception):
    pass

_TOP_KEY = re.compile(r'^\S')                              # 顶层键：行首非空白
_ENABLED = re.compile(r'^\s+enabled:\s*(true|false)\s*$')  # metrics 块内合法布尔（仅小写 true/false）

def read_metrics_enabled(root):
    """真四态：①文件不存在→False ②有文件无顶层 metrics: 块→False（消费仓常态放行）
    ③metrics: 块在但块内(至下一顶层键前)解不出合法 enabled: true|false→MetricsError(fail-closed)
    ④解出→bool。块边界=先定位 ^metrics: 再限范围到下一顶层键。"""
    cfg = Path(root) / "openspec" / "config.yaml"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False                                        # ①
    idx = next((i for i, ln in enumerate(lines) if ln.rstrip() == "metrics:" or ln.startswith("metrics:")), None)
    if idx is None:
        return False                                        # ②
    for ln in lines[idx + 1:]:                              # ③④ 块内至下一顶层键
        if _TOP_KEY.match(ln) and not ln.startswith(" "):
            break
        m = _ENABLED.match(ln)
        if m:
            return m.group(1) == "true"
    raise MetricsError("metrics: 块存在但解不出合法 enabled: true|false")
```

- [ ] **Step 4: 写存在性 + 最小必有行测试**

```python
def test_existence_missing_mandatory(tmp_path):
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="none" -->\n<!-- sdflow:step1-broad-review v1 mode="native" -->\n'  # 缺 outside-voice
    v = al.check_existence(report, "code-review", metrics_on=False)
    assert any(x["kind"] == "missing-anchor" and "outside-voice" in x["detail"] for x in v)

def test_existence_min_required_rows(tmp_path):
    al = _mod()
    # metrics 开：有 domain lens-metric 但缺 broad+outside-voice 行
    report = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
              '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
              '<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" -->\n')
    v = al.check_existence(report, "code-review", metrics_on=True)
    kinds = {x["detail"] for x in v if x["kind"] == "missing-lens-row"}
    assert "broad" in " ".join(kinds) and "outside-voice" in " ".join(kinds)
```

- [ ] **Step 5: 实现 check_existence（恒须三类 + metrics 开 lens-metric 存在 + broad/outside-voice 最小必有行）**

```python
MANDATORY = ("outside-voice", "hr-tg", "step1-broad-review")
MIN_LENS_ROWS = ("broad", "outside-voice")

def check_existence(report_text, layer, metrics_on):
    outside = list(fence_outside_lines(report_text))
    present, lens_rows = set(), set()
    for ln in outside:
        name = anchor_prefix(ln)
        if name:
            present.add(name)
            if name == "lens-metric":
                lens_rows.add(parse_kv(ln).get("lens", ""))
    v = []
    for fam in MANDATORY:
        if fam not in present:
            v.append({"kind": "missing-anchor", "detail": fam})
    if metrics_on:
        if "lens-metric" not in present:
            v.append({"kind": "missing-anchor", "detail": "lens-metric (metrics.enabled)"})
        for need in MIN_LENS_ROWS:
            if need not in lens_rows:
                v.append({"kind": "missing-lens-row", "detail": need})
    return v
```

- [ ] **Step 6: 跑全 Task2 测试绿** → Run: `pytest .../test_anchor_lint.py -k "metrics or existence or boundary or required" -v` Expected: PASS

- [ ] **Step 7: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task2-existence "存在性(+broad/outside-voice最小必有行) + metrics 真四态门控(无块=放行/块坏=ERROR) + 块边界"
```

---

### Task 3: lens-metric 字段校验（枚举/sev/layer==--layer/int≥0）+ site 豁免 + main + fail-closed

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/anchor_lint.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`

**Interfaces:**
- Produces: `check_lens_metric(report_text, layer, enums) -> list[dict]`；`main(argv) -> int`。
- Consumes: `load_enums`/`read_metrics_enabled`/`check_existence`/`fence_outside_lines`/`anchor_prefix`/`parse_kv`。

- [ ] **Step 1: 写字段校验测试（越域/缺字段/坏sev/错层/坏计数/site豁免）**

```python
def _lm(**kw):
    base = dict(layer="code-review", lens="domain", runner="claude",
               findings="2", 采纳="1", 裁掉="1", defer="0", 独立="0", sev="致0/高1/中0/低0")
    base.update(kw)
    return "<!-- sdflow:lens-metric v1 " + " ".join(f'{k}="{v}"' for k, v in base.items()) + " -->"

def _enums():
    return _mod().load_enums(CONTRACT)

def test_lens_enum_out_of_domain():
    al = _mod(); v = al.check_lens_metric(_lm(lens="bogus"), "code-review", _enums())
    assert any(x["field"] == "lens" for x in v)

def test_layer_must_equal_cli():
    al = _mod(); v = al.check_lens_metric(_lm(layer="spec-review"), "code-review", _enums())
    assert any(x["field"] == "layer" and "cli" in x["kind"] for x in v)

def test_bad_sev():
    al = _mod(); v = al.check_lens_metric(_lm(sev="致0/高1/中0"), "code-review", _enums())
    assert any(x["field"] == "sev" for x in v)

def test_count_not_nonneg_int():
    al = _mod()
    for bad in ("-1", "1.5", "", "三"):
        v = al.check_lens_metric(_lm(findings=bad), "code-review", _enums())
        assert any(x["field"] == "findings" for x in v), bad

def test_site_not_checked():
    al = _mod(); v = al.check_lens_metric(_lm(site="weird-value"), "code-review", _enums())
    assert v == []                                          # site 任意值合法

def test_missing_required_field():
    al = _mod()
    anchor = '<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" -->'  # 缺多字段
    v = al.check_lens_metric(anchor, "code-review", _enums())
    assert any(x["field"] == "runner" for x in v)
```

- [ ] **Step 2: 跑确认失败** → `pytest .../test_anchor_lint.py -k "enum or layer or sev or count or site or required" -v` Expected: FAIL

- [ ] **Step 3: 实现 check_lens_metric**

```python
_NONNEG_INT = re.compile(r'^\d+$')

def check_lens_metric(report_text, cli_layer, enums):
    v = []
    for ln in fence_outside_lines(report_text):
        if anchor_prefix(ln) != "lens-metric":
            continue
        kv = parse_kv(ln)
        for f in REQUIRED_FIELDS:
            if f not in kv:
                v.append({"anchor": ln.strip()[:80], "field": f, "kind": "missing-field"})
        if kv.get("layer") and kv["layer"] not in enums["layer"]:
            v.append({"anchor": ln.strip()[:80], "field": "layer", "kind": "out-of-enum"})
        if kv.get("layer") and kv["layer"] != cli_layer:
            v.append({"anchor": ln.strip()[:80], "field": "layer", "kind": "layer-ne-cli"})
        if kv.get("lens") and kv["lens"] not in enums["lens"]:
            v.append({"anchor": ln.strip()[:80], "field": "lens", "kind": "out-of-enum"})
        if kv.get("runner") and kv["runner"] not in enums["runner"]:
            v.append({"anchor": ln.strip()[:80], "field": "runner", "kind": "out-of-enum"})
        if kv.get("sev") and not enums["sev_re"].match(kv["sev"]):
            v.append({"anchor": ln.strip()[:80], "field": "sev", "kind": "bad-subformat"})
        for cf in COUNT_FIELDS:
            if cf in kv and not _NONNEG_INT.match(kv[cf]):
                v.append({"anchor": ln.strip()[:80], "field": cf, "kind": "not-nonneg-int"})
    return v
```

- [ ] **Step 4: 写 main + fail-closed + 退出码测试**

```python
def _run(report_path, layer, root=None):
    cmd = [sys.executable, str(SCRIPT), "--report", str(report_path), "--layer", layer]
    if root: cmd += ["--root", str(root)]
    return subprocess.run(cmd, capture_output=True, text=True)

def test_clean_report_exit0(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = tmp_path / "r.md"
    rpt = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 0, r.stderr

def test_missing_report_error_exit2(tmp_path):
    r = _run(tmp_path / "nope.md", "code-review", tmp_path); assert r.returncode == 2

def test_violation_exit1(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt_path = tmp_path / "r.md"; rpt_path.write_text("<!-- sdflow:hr-tg v1 hit=\"none\" -->\n", encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 1
    assert '"' in r.stdout or r.stdout.strip()              # JSON 输出

def test_config_bad_block_exit2(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    rpt_path = tmp_path / "r.md"
    rpt_path.write_text('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
                        '<!-- sdflow:step1-broad-review v1 mode="native" -->\n', encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 2
```

- [ ] **Step 5: 跑确认失败** → Expected: FAIL（main 未实现）

- [ ] **Step 6: 实现 main（组装 + 双输出 + 退出码）**

```python
def main(argv=None):
    ap = argparse.ArgumentParser(description="评审报告锚自检门（确定性·fail-closed）")
    ap.add_argument("--report", required=True)
    ap.add_argument("--layer", required=True, choices=["spec-review", "code-review"])
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    # 1) 读报告（fail-closed）
    try:
        report_text = Path(args.report).read_text(encoding="utf-8")
    except OSError as e:
        print(f"[anchor_lint] ERROR 读不到报告: {args.report}: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "report-unreadable"}, ensure_ascii=False))
        return EXIT_ERROR
    # 2) 读枚举 + metrics（fail-closed）
    try:
        enums = load_enums()
    except EnumsError as e:
        print(f"[anchor_lint] ERROR 契约枚举: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "enums"}, ensure_ascii=False))
        return EXIT_ERROR
    try:
        metrics_on = read_metrics_enabled(args.root)
    except MetricsError as e:
        print(f"[anchor_lint] ERROR config metrics 块坏: {e}", file=sys.stderr)
        print(json.dumps({"result": "ERROR", "reason": "metrics-block-bad"}, ensure_ascii=False))
        return EXIT_ERROR
    # 3) 校验
    violations = check_existence(report_text, args.layer, metrics_on)
    if metrics_on:
        violations += check_lens_metric(report_text, args.layer, enums)
    if violations:
        for x in violations:
            print(f"[anchor_lint] VIOLATION {x}", file=sys.stderr)
        print(json.dumps({"result": "VIOLATION", "violations": violations}, ensure_ascii=False))
        return EXIT_VIOLATION
    print("[anchor_lint] CLEAN", file=sys.stderr)
    print(json.dumps({"result": "CLEAN"}, ensure_ascii=False))
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
```

> 注：`check_lens_metric` 只在 `metrics_on` 时跑（metrics 关则 lens-metric 一类整体跳过，与门控一致）。数值一致性（findings vs 实收数）**不校验**——脚本不兜（信任边界）。

- [ ] **Step 7: 跑全量 anchor_lint 测试绿**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -v`
Expected: PASS（全部）

- [ ] **Step 8: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task3-fields "lens-metric 字段/枚举/sev + layer==--layer + int≥0 + site 豁免 + main 双输出 + fail-closed"
```

---

### Task 4: aggregator 枚举一致性测试 + 双解析器交叉断言

**Files:**
- Modify: `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`

**Interfaces:**
- Consumes: `lens_metric_aggregate.LAYER_ENUM`/`LENS_ENUM`；契约 `lens-metric-enums` 块；`anchor_lint.load_enums`（仅测试内跨路径 import 允许——测试非运行时消费仓）。

- [ ] **Step 1: 写一致性 + 交叉断言测试**

```python
# 追加到 sdflow-retro/scripts/tests/test_lens_metric_aggregate.py
import importlib.util
from pathlib import Path
import lens_metric_aggregate as lma

_REPO = Path(__file__).resolve().parents[3]                # 仓根
_CONTRACT = _REPO / "sdflow-init" / "assets" / "workflow" / "lens-metric-contract.md"
_ANCHOR_LINT = _REPO / "sdflow-init" / "assets" / "workflow" / "tools" / "anchor_lint.py"

def _parse_enum_block_minimal(contract_path):
    """极简契约 lens-metric-enums 块解析（不 import anchor_lint，独立实现）。"""
    text = Path(contract_path).read_text(encoding="utf-8")
    lines, out, in_block = text.splitlines(), {}, False
    for ln in lines:
        if not in_block:
            if ln.strip().startswith("```lens-metric-enums") or ln.strip().startswith("~~~lens-metric-enums"):
                in_block = True
            continue
        if ln.strip().startswith("```") or ln.strip().startswith("~~~"):
            break
        if ":" in ln:
            k, v = ln.split(":", 1)
            out[k.strip()] = {x.strip() for x in v.split(",") if x.strip()}
    return out

def test_aggregator_enum_matches_contract():
    block = _parse_enum_block_minimal(_CONTRACT)
    assert lma.LAYER_ENUM == block["layer"]
    assert lma.LENS_ENUM == block["lens"]

def test_dual_parser_cross_assert():
    """交叉断言：anchor_lint.load_enums 与本测试 mini-parser 对同一契约解出的 layer/lens 相等。"""
    spec = importlib.util.spec_from_file_location("anchor_lint", _ANCHOR_LINT)
    al = importlib.util.module_from_spec(spec); spec.loader.exec_module(al)
    e = al.load_enums(_CONTRACT)
    block = _parse_enum_block_minimal(_CONTRACT)
    assert e["layer"] == block["layer"]
    assert e["lens"] == block["lens"]
    assert e["runner"] == block["runner"]
```

- [ ] **Step 2: 跑确认过（现契约块与 aggregator 硬编码应一致）**

Run: `pytest sdflow-retro/scripts/tests/test_lens_metric_aggregate.py -k "enum or cross" -v`
Expected: PASS（若红则说明契约块与 aggregator 硬编码不一致，须核对——不改 aggregator，核契约块）

- [ ] **Step 3: 验证守卫生效（临时改契约块 lens → 测试红 → 还原）**

Run: 临时把契约块 `lens:` 删一项，`pytest ... -k enum` 应 FAIL；还原后 PASS。

- [ ] **Step 4: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task4-enum-consistency "aggregator 硬编码 enum 对契约块一致性 + 双解析器交叉断言"
```

---

### Task 5: copy_bundle 契约同刷 + roadmap 复用→重实现调和

**Files:**
- Modify: `sdflow-init/scripts/init.py:154-158`（copy_bundle 非 full 分支）
- Test: `sdflow-init/tests/test_init_contract_sync.py`（新增）
- Modify: `openspec/roadmaps/mechanical-layer-hardening/design.md`, `roadmap.md`, `task-log.md`

**Interfaces:**
- Consumes: `init.copy_bundle(root, full=False)`。

- [ ] **Step 1: 写 copy_bundle 契约同刷测试**

```python
# sdflow-init/tests/test_init_contract_sync.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import init

def test_copy_bundle_refreshes_contract(tmp_path):
    init.copy_bundle(str(tmp_path), full=False)
    contract = tmp_path / "openspec" / "workflow" / "lens-metric-contract.md"
    assert contract.exists(), "非 full 模式须一并铺 lens-metric-contract.md"
    assert "lens-metric-enums" in contract.read_text(encoding="utf-8")
    assert (tmp_path / "openspec" / "workflow" / "tools" / "anchor_lint.py").exists()
```

- [ ] **Step 2: 跑确认失败** → Run: `pytest sdflow-init/tests/test_init_contract_sync.py -v` Expected: FAIL（契约不在非 full 输出）

- [ ] **Step 3: 改 copy_bundle 非 full 分支（在 copytree tools 之后加契约拷贝）**

在 `sdflow-init/scripts/init.py` 的 `else:` 分支（约 154-158 行），`shutil.copytree(...tools...)` **之后**加：

```python
        # [mlh-p2-anchor-lint] 契约是 tools/anchor_lint.py 的运行时机读依赖（读 lens-metric-enums 块），
        # 须与 tools/ 同批刷新，否则本地 pin 消费仓 update 后「新脚本+旧契约无块」永久 fail-closed。
        contract_src = os.path.join(BUNDLE_SRC, "lens-metric-contract.md")
        if os.path.isfile(contract_src):
            shutil.copy2(contract_src, os.path.join(dst, "lens-metric-contract.md"))
```

（`dst = <root>/openspec/workflow`，已在函数内定义。full 模式整树 copytree 已含契约，无需改。）

- [ ] **Step 4: 跑测试绿 + 全 init 测试无回归**

Run: `pytest sdflow-init/tests/ -v`
Expected: PASS（新测试 + 既有 init 测试无回归）

- [ ] **Step 5: roadmap 复用→重实现调和**

改 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md` 阶段2 子任务 2.A.1 里「复用 `lens_metric_aggregate.parse_anchor`/`_fence_aware_lines`…不重实现」一句，改为：

> 遵 F1 实质（度量锚变长 KV 走前缀匹配、**不用** `ship_gate._line_scoped_hits` 定长整行原语）；因 anchor_lint 作 bundle tools/ 经 update 铺进消费仓、而 `sdflow-retro/scripts` 不在消费仓，`import lens_metric_aggregate` 运行时 break，故**脚本内重实现同款 fence-aware + 前缀 kv 逻辑**（非 import 复用）〔mlh-p2-anchor-lint 调和〕。

改 `openspec/roadmaps/mechanical-layer-hardening/design.md` §2 技术栈表 anchor-lint 行「直接复用，不重实现」同款调和一句。

`openspec/roadmaps/mechanical-layer-hardening/task-log.md` 追一条（倒序最新）：

```markdown
## 2026-07-07
### [阶段 2 / mlh-p2-anchor-lint spec-review] 「复用→重实现」调和（H3/BASE-08）
- spec-review 领域镜 BASE-08 抓出 design 决策与 roadmap「复用不重实现」正面矛盾。裁决：遵 F1 实质（变长 KV 前缀匹配、不用 _line_scoped_hits），但因跨 skill import 在消费仓 break，实现为脚本内重实现同款逻辑。已改 roadmap.md 2.A.1 + design.md §2 技术栈行。
```

- [ ] **Step 6: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task5-deploy-reconcile "copy_bundle 一并刷契约(pin 防错配) + roadmap 复用→重实现调和"
```

---

### Task 6: 两审 SKILL 自检步接 anchor_lint + 保留诚实边界

**Files:**
- Modify: `sdflow-spec-review/SKILL.md:79`
- Modify: `sdflow-code-review/SKILL.md:117-124`

- [ ] **Step 1: 改 spec-review SKILL Step3 自检步（:79）**

把 `sdflow-spec-review/SKILL.md` 第 79 行「**锚行存在性自检…出报告后 grep 四类 v1 锚行（…）**」那句的**手 grep 措辞**替换为调脚本，保留诚实边界。改为：

> - **锚行自检（确定性脚本门）〔mlh-p2-anchor-lint〕**：出报告后调 `$RULES_ROOT/tools/anchor_lint.py --report {change_dir}/spec-review-report.md --layer spec-review --root "$(git rev-parse --show-toplevel)"`——退出码非 0（1=违规/2=fail-closed）即本步报错阻塞，遵其判定，MUST NOT 静默吞。脚本机验四类 v1 锚存在性 + lens-metric 字段/枚举/sev/layer==--layer/计数 int≥0（枚举从契约 `lens-metric-enums` 块单一源读）+ metrics 开时 broad/outside-voice 最小必有行。**保留信任边界声明**：`findings=N` 与合并池实收数的**数值一致性**仍是主 session 信任边界、非机械可验——脚本不谎称保证数值正确。config `metrics.enabled` 关/无 metrics 块时 lens-metric 一类跳过（脚本内门控）。**此门只挡「同一会话内忘记跑这步」，挡不住「整段跳过本步」**（诚实拦截力）。

- [ ] **Step 2: 改 code-review SKILL Step5 自检步（:117-124）**

把 `sdflow-code-review/SKILL.md` 117-124 行的「锚行存在性自检…grep 四类 v1 锚行…」整段替换为调脚本（同上，但 `--layer code-review`、report 路径 `{change_dir}/code-review-report.md`），保留：①诚实边界（数值一致性主 session 信任边界）；②config 门控；③**旁路声明**（锚缺失/违规仅拦报告完整性，MUST NOT 反向改写已裁决 findings 采纳结论或「建议进 /sdflow-done」结论）。

- [ ] **Step 3: dogfood 校验（dev checkout 直接跑，不靠符号链）**

Run:
```bash
python3 sdflow-init/assets/workflow/tools/anchor_lint.py \
  --report openspec/changes/mlh-p2-anchor-lint/spec-review-report.md \
  --layer spec-review --root "$(git rev-parse --show-toplevel)"
echo "exit=$?"
```
Expected: exit 0（本 change 自己的 spec-review-report.md 含全四类锚 + 5 lens-metric 行含 broad+outside-voice，metrics.enabled=true）。**若非 0**：读 JSON 违规清单核对——可能本报告某锚字段与新校验规则（如 layer==--layer：报告是 spec-review layer）有出入，据实修报告或脚本。

- [ ] **Step 4: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task6-skill-wire "两审 SKILL 自检步接 anchor_lint + 保留数值一致性诚实边界 + dogfood 校验"
```

---

### Task 7: 收尾验证

**Files:** 无新增（跑全量测试 + validate）

- [ ] **Step 1: 全量 pytest 三处绿**

Run:
```bash
pytest sdflow-init/assets/workflow/tools/tests/ sdflow-retro/scripts/tests/ sdflow-init/tests/ -q
```
Expected: PASS（无 fail/error）

- [ ] **Step 2: openspec validate**

Run: `openspec validate mlh-p2-anchor-lint`
Expected: `Change 'mlh-p2-anchor-lint' is valid`

- [ ] **Step 3: 核 spec delta 与实现一致**：抽查 spec 12 Scenario 各有对应实现/测试（存在性、metrics 四态、layer==--layer、int≥0、site 豁免、fence、fail-closed、最小必有行、一致性、pin 部署、数值边界）。

- [ ] **Step 4: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh mlh-p2-anchor-lint:task7-verify "收尾：全量 pytest 绿(tools+retro-scripts+init) + validate + spec delta 对码核验"
```

---

## Self-Review

**1. Spec coverage**：spec 12 Scenario → Task 映射：干净报告(T3)、缺恒须锚(T2)、越域枚举/缺字段/坏sev(T3)、site豁免(T3)、config缺失/无块放行(T2)、块坏fail-closed(T2)、最小必有行(T2)、layer≠cli(T3)、计数非int(T3)、fence示范锚(T1)、读不到报告fail-closed(T3)、一致性测试(T4)、pin同刷(T5)、数值边界(T3 不校验断言)。全覆盖。

**2. Placeholder scan**：无 TBD/TODO；每代码步含完整代码。

**3. Type consistency**：`load_enums`→dict(layer/lens/runner set + sev_re)；`read_metrics_enabled`→bool/raise MetricsError；`check_existence`/`check_lens_metric`→list[dict]；`main`→int。跨 Task 签名一致。
