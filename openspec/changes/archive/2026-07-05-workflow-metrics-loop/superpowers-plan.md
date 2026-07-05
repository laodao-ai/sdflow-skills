# workflow-metrics-loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给评审系统（spec-review/code-review 各镜）加结构化度量锚 `sdflow:lens-metric v1` + 只读跨 change 聚合器 + per-镜数据驱动反馈（人决），让「哪镜值不值得留」可被数据审视。

**Architecture:** 生产者（两 SKILL 在 Step3 落锚）→ 锚散在归档 review 报告（盘面即状态）→ 只读聚合器 grep archive 出多列表（可重生 view，零持久态）→ /sdflow-maintain 机械 surfacing N≥10 → 人复评。纯**价值**度量（成本另立 T29）；config 门控（源仓 on / 消费仓 off）。

**Tech Stack:** Markdown（bundle 规则 + 两 SKILL.md 编排指令）+ 单个只读 Python 聚合脚本（stdlib only，含 pytest）+ config.yaml 开关。

## Global Constraints

- 每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。
- 锚契约字段（逐字）：`layer`∈{spec-review,code-review} · `lens`∈{domain,adversarial,grounding,history,outside-voice,broad} · `runner`∈{claude,codex,claude-fallback} · `site`∈{code-voice,hr-tg,design-voice,—}（可选，仅 outside-voice） · `findings`/`采纳`/`裁掉`/`defer`/`独立`=int≥0 · `sev`=`致N/高N/中N/低N`（定序、零写0、分隔恒`/`）。锚形：`<!-- sdflow:lens-metric v1 layer="..." lens="..." runner="..." site="..." findings="..." 采纳="..." 裁掉="..." defer="..." 独立="..." sev="..." -->`。
- 聚合器 MUST：净新字段提取解析器、脚本内重实现 fence-aware 行级核（`line.lstrip().startswith("```")` 翻转 in_fence）、锚独占行前缀匹配、禁裸 `split`/substring、**禁跨 skill import `ship_gate`**、不写任何持久文件、不产合成价值分。
- 契约权威源落 `sdflow-init/assets/workflow/`（bundle）；改 assets 后须 `bash setup.sh` 才让全局 canonical 生效。
- 度量落锚受 config `metrics.enabled` 门控：源仓 openspec/config.yaml 默认 `true`，bundle config.template.yaml（推消费仓）默认 `false`；关闭时不落锚、缺锚不阻塞。

---

### Task 1: lens-metric 锚契约权威规范（bundle 源）

**Files:**
- Create: `sdflow-init/assets/workflow/lens-metric-contract.md`

**Interfaces:**
- Produces: 契约单一源（字段/取值域/归属规则/sev 子格式/site 消歧/enum 扩展治理/config 门控/示范锚 fence MUST）——两 SKILL 与聚合器均**引用**此文件，不复制字段清单。

- [ ] **Step 1: 写契约规范文件**

写入 `sdflow-init/assets/workflow/lens-metric-contract.md`，逐字含（照 Global Constraints 的字段表 + design.md「锚契约」节 + 归属规则）：
```markdown
# lens-metric v1 锚契约（评审价值度量单一权威源）

## 锚形（一行一 (layer,lens,runner,site,轮)）
<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->

## 字段与取值域
- layer ∈ {spec-review, code-review}
- lens  ∈ {domain, adversarial, grounding, history, outside-voice, broad}（canonical 投影；折叠表见 §折叠）
- runner∈ {claude, codex, claude-fallback}
- site  ∈ {code-voice, hr-tg, design-voice, —}（可选消歧，仅 outside-voice，不进 lens enum；非 outside-voice 用 —）
- findings/采纳/裁掉/defer/独立 = int≥0
- sev = 致N/高N/中N/低N（四级定序、零也写 0、分隔符恒 /；仅采纳项计入）

## 归属规则（钉死）
findings/采纳/裁掉/defer 按「哪些镜报过该 finding」归属，共抓则每命中镜各记一次；
独立 仅在「唯一报过 ∧ 被采纳」时 +1；独立在折叠到 lens 类型之后计。
数值跨源一致性 = 主 session 信任边界（自做去重又写锚、自核无独立性），非机械门。

## 折叠表（canonical 投影）
领域镜→domain · 对抗镜1/2/3→adversarial · 接地镜/完整性镜→grounding · 历史镜→history ·
codex(任何 site)/claude-fallback→outside-voice · autoplan(CEO/Eng/DX/design)+gstack-adv→broad

## enum 扩展治理
新增镜类型（enum 未列）MUST 先升版本号至 v2 + 更新折叠表，MUST NOT 静默塞入 broad。

## config 门控
度量落锚受 config.yaml `metrics.enabled` 门控：源仓默认 true / 消费仓默认 false；关闭时不落锚、缺锚不阻塞。

## 示范锚 fence（防聚合器自指误取）
review 报告中如需示范/引用锚语法，MUST 包在 ``` fence 内。
```

- [ ] **Step 2: 机械核对**

Run: `grep -c 'sdflow:lens-metric v1' sdflow-init/assets/workflow/lens-metric-contract.md`
Expected: ≥1（锚形示例在）。再 `grep -q 'metrics.enabled' sdflow-init/assets/workflow/lens-metric-contract.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task1-contract "lens-metric v1 契约权威规范(字段/site/sev/折叠/enum治理/config门控/fence MUST)"
```

---

### Task 2: config.yaml 度量开关（源仓 on / 消费仓 off）

**Files:**
- Modify: `openspec/config.yaml`（源仓，加 `metrics.enabled: true`）
- Modify: `sdflow-init/assets/workflow/config.template.yaml`（推消费仓，加 `metrics.enabled: false` + 注释）

**Interfaces:**
- Produces: `metrics.enabled` 布尔键，两 SKILL 落锚前读它。

- [ ] **Step 1: 源仓 config 加开关**

在 `openspec/config.yaml` 末尾追加（顶层键）：
```yaml
# 评审价值度量（lens-metric）开关：源仓 dogfood 高频，默认开
metrics:
  enabled: true
```

- [ ] **Step 2: bundle 模版加开关（消费仓默认关）**

在 `sdflow-init/assets/workflow/config.template.yaml` 末尾追加：
```yaml
# 评审价值度量（lens-metric）开关：低频消费仓默认关（避免零收益期背记账+硬阻塞）；
# 高频仓可改 true 开启。契约见 lens-metric-contract.md。
metrics:
  enabled: false
```

- [ ] **Step 3: 机械核对**

Run: `grep -A1 '^metrics:' openspec/config.yaml sdflow-init/assets/workflow/config.template.yaml`
Expected: 源仓 `enabled: true`，模版 `enabled: false`。

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task2-config "config 度量开关: 源仓 on / 消费仓模版 off"
```

---

### Task 3: 聚合器 fence-aware 行级解析核（Python, TDD）

**Files:**
- Create: `sdflow-init/assets/workflow/tools/lens_metric_aggregate.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py`

**Interfaces:**
- Produces: `_fence_aware_lines(text)->Iterator[str]`、`parse_anchor(line)->dict|None`、`parse_report(path)->list[dict]`。
- Consumes: 无（stdlib only：`re`, `pathlib`, `argparse`, `sys`, `collections`）。

- [ ] **Step 1: Write the failing tests（解析层）**

写 `tests/test_lens_metric_aggregate.py`：
```python
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "lens_metric_aggregate.py"
_spec = importlib.util.spec_from_file_location("lma", _p)
lma = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(lma)

ANCHOR = ('<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" '
          'runner="claude" site="—" findings="5" 采纳="3" 裁掉="1" defer="1" '
          '独立="2" sev="致0/高2/中2/低1" -->')

def test_parse_valid_anchor():
    f = lma.parse_anchor(ANCHOR)
    assert f["layer"] == "code-review" and f["lens"] == "domain"
    assert f["findings"] == "5" and f["采纳"] == "3" and f["独立"] == "2"
    assert f["sev"] == "致0/高2/中2/低1" and f["site"] == "—"

def test_non_anchor_line_returns_none():
    assert lma.parse_anchor("普通一行文字，含 lens-metric 字样但非锚") is None
    assert lma.parse_anchor("- 列表项 sdflow:lens-metric v1 内联提及") is None  # 非行首前缀

def test_fence_block_lines_skipped():
    text = "正文\n```\n" + ANCHOR + "\n```\n正文2\n"
    lines = list(lma._fence_aware_lines(text))
    assert ANCHOR not in lines  # fence 内不产出

def test_anchor_outside_fence_yielded():
    text = "正文\n" + ANCHOR + "\n"
    assert ANCHOR in list(lma._fence_aware_lines(text))

def test_parse_report_only_non_fenced(tmp_path):
    p = tmp_path / "x-review-report.md"
    p.write_text("真锚:\n" + ANCHOR + "\n示例(fence 内不取):\n```\n" + ANCHOR + "\n```\n", encoding="utf-8")
    rows = lma.parse_report(p)
    assert len(rows) == 1  # 只取 fence 外那一行

def test_malformed_anchor_does_not_corrupt(tmp_path):
    # 措辞漂移/裸 substring 陷阱：缺引号、字段名漂移都不应抛异常或误取半行
    bad = '<!-- sdflow:lens-metric v1 layer=code-review lens=domain -->'  # 无引号
    p = tmp_path / "y-review-report.md"; p.write_text(bad + "\n", encoding="utf-8")
    rows = lma.parse_report(p)
    assert rows == [] or all("layer" not in r or r.get("layer") for r in rows)  # 不腐坏

def test_sev_subformat_robust():
    # sev 省级/乱序/多空格 仍作为整串取回（子解析健壮性在渲染层校验，这里只保不腐坏）
    a = ANCHOR.replace('sev="致0/高2/中2/低1"', 'sev="高2/致0"')
    assert lma.parse_anchor(a)["sev"] == "高2/致0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py -q`
Expected: FAIL（`lens_metric_aggregate.py` 不存在 / 函数未定义）

- [ ] **Step 3: 实现解析核**

写 `sdflow-init/assets/workflow/tools/lens_metric_aggregate.py`：
```python
#!/usr/bin/env python3
"""lens-metric 只读聚合器（盘面即状态·view-only）。
扫 archive/**/*-review-report.md 的 sdflow:lens-metric v1 锚 → 多列可排序表。
净新字段提取解析器；脚本内重实现 fence-aware 行级核（禁裸 split/substring、
禁跨 skill import ship_gate）。不写任何持久文件、不产合成价值分。契约见
sdflow-init/assets/workflow/lens-metric-contract.md。"""
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

ANCHOR_PREFIX = "<!-- sdflow:lens-metric v1"
LAYER_ENUM = {"spec-review", "code-review"}
LENS_ENUM = {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
_KV = re.compile(r'([^\s=]+)="([^"]*)"')  # 受限 kv：key="value"，禁裸 split


def _fence_aware_lines(text):
    """产出非 fenced-block 行。fence 翻转口径同 ship_gate._line_scoped_hits：
    line.lstrip().startswith('```')（本脚本内重实现，不跨 skill import）。"""
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield line


def parse_anchor(line):
    """从一行提取 lens-metric 字段 dict；非锚行返回 None。
    锚须独占行前缀（strip 后 startswith ANCHOR_PREFIX）——非行首匹配不误取。"""
    s = line.strip()
    if not s.startswith(ANCHOR_PREFIX):
        return None
    fields = {k: v for k, v in _KV.findall(s)}
    return fields or None


def parse_report(path):
    text = Path(path).read_text(encoding="utf-8")
    rows = []
    for line in _fence_aware_lines(text):
        f = parse_anchor(line)
        if f:
            rows.append(f)
    return rows
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py -q`
Expected: PASS（7 passed）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task3-parser "聚合器 fence-aware 行级解析核(净新字段提取,禁裸split/跨import) + 反例矩阵"
```

---

### Task 4: 聚合成表 + 独立列 + 无锚样本计数 + N≥10 flag（Python, TDD）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/lens_metric_aggregate.py`（加 `aggregate`/`render_table`/`main`）
- Test: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py`（加聚合用例）

**Interfaces:**
- Consumes: Task 3 的 `parse_report`。
- Produces: `aggregate(archive_root)->(rows:list[dict], no_anchor:list[str])`、`render_table(rows, no_anchor)->str`、`main()`。

- [ ] **Step 1: Write the failing tests（聚合层）**

追加到测试文件：
```python
def _write(tmp_path, change, *anchors):
    d = tmp_path / "archive" / change; d.mkdir(parents=True)
    (d / "code-review-report.md").write_text("\n".join(anchors) + "\n", encoding="utf-8")

def _a(lens, findings, 采纳, 独立, site="—", layer="code-review"):
    return (f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{lens}" runner="claude" '
            f'site="{site}" findings="{findings}" 采纳="{采纳}" 裁掉="0" defer="0" '
            f'独立="{独立}" sev="致0/高{采纳}/中0/低0" -->')

def test_aggregate_two_changes(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2), _a("adversarial", 4, 2, 1))
    _write(tmp_path, "c2", _a("domain", 6, 4, 3))
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    assert len(rows) == 3 and no_anchor == []

def test_no_anchor_report_counted(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    old = tmp_path / "archive" / "old"; old.mkdir(parents=True)
    (old / "code-review-report.md").write_text("旧格式 voice分桶: codex 采纳3/裁掉0\n", encoding="utf-8")
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    assert "old" in no_anchor  # 显式计无锚样本，不静默跳过

def test_render_table_has_independent_and_flags(tmp_path):
    # 独立列非空 + 出现轮数≥10 标记（构造 domain 出现 10 轮）
    for i in range(10):
        _write(tmp_path, f"c{i}", _a("domain", 5, 3, 2))
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    assert "独立" in table and "≥10" in table  # 表含独立列 + N≥10 标记
    assert "无锚样本" in table  # 无锚计数呈现

def test_out_of_enum_lens_flagged(tmp_path):
    _write(tmp_path, "c1", _a("对抗镜1", 3, 1, 1))  # 未折叠的非法值
    rows, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "越域" in table or "invalid" in table.lower()  # 非法 lens 值被标记不静默

def test_no_synthetic_score(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    rows, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "综合分" not in table and "价值分" not in table  # 描述性多列,无合成分
```

- [ ] **Step 2: Run to verify fail**

Run: `python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py -q`
Expected: FAIL（`aggregate`/`render_table` 未定义）

- [ ] **Step 3: 实现聚合 + 渲染 + main**

追加到 `lens_metric_aggregate.py`：
```python
def aggregate(archive_root):
    """扫 archive/**/*-review-report.md；返回 (锚行 rows, 无锚 change 名 list)。"""
    rows, no_anchor = [], []
    for report in sorted(Path(archive_root).glob("**/*-review-report.md")):
        rr = parse_report(report)
        if rr:
            for f in rr:
                f["_change"] = report.parent.name
            rows.extend(rr)
        else:
            no_anchor.append(report.parent.name)
    return rows, no_anchor


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def render_table(rows, no_anchor):
    """多列可排序描述性表（无合成分）。按 (layer,lens,site) 分组：
    出现轮数 · Σfindings · Σ采纳 · Σ裁掉 · Σdefer · Σ独立 · 采纳率 · 独立率 · flag。"""
    grp = defaultdict(lambda: dict(轮=0, f=0, 采纳=0, 裁掉=0, defer=0, 独立=0, bad=False))
    for r in rows:
        lens = r.get("lens", "")
        bad = (r.get("layer") not in LAYER_ENUM) or (lens not in LENS_ENUM)
        key = (r.get("layer", "?"), lens or "?", r.get("site", "—"))
        g = grp[key]
        g["轮"] += 1
        g["f"] += _int(r.get("findings"))
        g["采纳"] += _int(r.get("采纳"))
        g["裁掉"] += _int(r.get("裁掉"))
        g["defer"] += _int(r.get("defer"))
        g["独立"] += _int(r.get("独立"))
        g["bad"] = g["bad"] or bad
    hdr = "| layer | lens | site | 出现轮数 | Σfindings | Σ采纳 | Σ裁掉 | Σdefer | Σ独立 | 采纳率 | 独立率 | flag |"
    sep = "|" + "---|" * 12
    lines = [hdr, sep]
    for (layer, lens, site), g in sorted(grp.items()):
        denom = g["采纳"] + g["裁掉"] + g["defer"]
        采纳率 = f"{g['采纳']/denom:.0%}" if denom else "—"
        独立率 = f"{g['独立']/g['f']:.0%}" if g["f"] else "—"
        flags = []
        if g["轮"] >= 10:
            flags.append("≥10待复评")
        if g["bad"]:
            flags.append("⚠越域")
        lines.append(f"| {layer} | {lens} | {site} | {g['轮']} | {g['f']} | {g['采纳']} | "
                     f"{g['裁掉']} | {g['defer']} | {g['独立']} | {采纳率} | {独立率} | {' '.join(flags) or '—'} |")
    lines.append("")
    lines.append(f"> 无锚样本 {len(no_anchor)} 份（旧格式,不纳入）: {', '.join(no_anchor) or '无'}")
    lines.append("> 独立率跨轮不保证同口径（dedup 合并尺度可能漂移），复评时校验最近几轮尺度一致。")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="lens-metric 只读聚合器（view-only）")
    ap.add_argument("--root", default=".", help="仓根（含 openspec/changes/archive）")
    args = ap.parse_args(argv)
    archive = Path(args.root) / "openspec" / "changes" / "archive"
    rows, no_anchor = aggregate(archive)
    print(render_table(rows, no_anchor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py -q`
Expected: PASS（全部 passed，≈13 项）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task4-aggregate "聚合成表(多列可排序/独立列/N≥10 flag/无锚计数/越域标记/无合成分) + 端到端测试"
```

---

### Task 5: sdflow-code-review SKILL 落锚 + voice分桶吸收 + 自检扩枚举 + site + config 门控

**Files:**
- Modify: `sdflow-code-review/SKILL.md`（Step2半/裁决分桶/报告格式台账/第五步自检）

**Interfaces:**
- Consumes: `lens-metric-contract.md`（引用，不复制字段）。

- [ ] **Step 1: 改报告格式台账——voice分桶 prose → lens-metric 锚**

在 `sdflow-code-review/SKILL.md` 报告格式区，把 `voice分桶: codex 采纳x/裁掉y/defer z` 一行替换为「每镜落一行 `lens-metric` 锚」指令，逐字要求：Step3 裁决后为 `domain/adversarial/history/outside-voice(含 site=code-voice|hr-tg)/broad(gstack)` 各落一行锚；字段/取值域**引用** `@openspec/workflow/lens-metric-contract.md`（勿复制清单）；outside-voice 同轮 code-voice+hr-tg 各独立一行以 `site` 区分。

- [ ] **Step 2: 加 config 门控 + 独立导出 + 自检指令**

在同区加：①落锚**前**读 config `metrics.enabled`（缺省/false → 不落锚、跳过自检，仅本仓 dogfood 默认 on）；②Step3 去重时记每条命中镜集合→折叠到 canonical lens 后导出 `独立`（唯一报过∧被采纳 +1）；③第五步锚存在性自检**扩一类**：缺必填字段 **或** `layer/lens/runner/sev` 取值越域/子格式错 → 报错阻塞；数值一致性是主 session 信任边界（非机械门）；④旁路声明：锚有无 MUST NOT 改 findings 判定。

- [ ] **Step 3: 机械核对**

Run: `grep -c 'voice分桶:' sdflow-code-review/SKILL.md`
Expected: `0`（prose 指令已被锚取代；若台账示例保留「voice分桶」历史词，确认其在锚吸收说明的上下文而非活指令）
Run: `grep -q 'lens-metric-contract' sdflow-code-review/SKILL.md && grep -q 'metrics.enabled' sdflow-code-review/SKILL.md && echo OK`
Expected: `OK`（引用契约 + config 门控就位）

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task5-codereview "code-review SKILL 落锚+voice分桶吸收+独立导出+自检扩枚举+site+config门控"
```

---

### Task 6: sdflow-spec-review SKILL 落锚 + 设计门拍板回写最终化 + site + config 门控

**Files:**
- Modify: `sdflow-spec-review/SKILL.md`（Step3 裁决/第四步产出/拍板回写协议）

- [ ] **Step 1: 加落锚指令**

在 `sdflow-spec-review/SKILL.md` 第四步产出区加：Step3 裁决后为 `domain/adversarial/grounding/outside-voice(含 site=design-voice|hr-tg)/broad(autoplan)` 各落一行 `lens-metric` 锚；字段引用 `@openspec/workflow/lens-metric-contract.md`；config `metrics.enabled` 门控（同 code-review）；独立导出同口径。

- [ ] **Step 2: 加拍板回写最终化指令〔SR-M〕**

在「拍板回写协议（ship-gate 锚）」段加：spec-review 的 `采纳/裁掉/defer` 因中置信项设计门可翻改，其 `lens-metric` 锚 MUST 在**拍板回写时**（与 `<!-- ship-gate: design-approved -->` 同步写入）最终确定/重算，反映门后最终裁决，MUST NOT 用 Step3 pre-gate 临时裁决充当最终采纳率。

- [ ] **Step 3: 机械核对**

Run: `grep -q 'lens-metric-contract' sdflow-spec-review/SKILL.md && grep -q '拍板回写' sdflow-spec-review/SKILL.md && grep -q 'metrics.enabled' sdflow-spec-review/SKILL.md && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task6-specreview "spec-review SKILL 落锚+设计门拍板回写最终化(SR-M)+site+config门控"
```

---

### Task 7: /sdflow-maintain surfacing hook（防死列，SR-A）+ 反馈判据泛化

**Files:**
- Modify: `sdflow-maintain/SKILL.md`（加机械收尾检查步）
- Modify: `sdflow-code-review/SKILL.md`（复评条款：10 次采纳率 → per-镜 采纳率+独立率双列）

- [ ] **Step 1: maintain 加 surfacing 检查步**

在 `sdflow-maintain/SKILL.md` 收尾段加机械步：跑 `python3 @openspec/workflow/tools/lens_metric_aggregate.py --root "$(git rev-parse --show-toplevel)"`，对 `出现轮数≥10 且未复评` 的镜在维护收尾**显著**提示（只提示不判断、不自动砍）；MUST NOT 埋进长报告。config `metrics.enabled=false` 时跳过。

- [ ] **Step 2: 反馈条款泛化**

把 code-review SKILL 里「累计 10 次后按采纳率复评降采样 HR-only」条款从仅 outside-voice 泛化到 per-(层,镜)，判据升为**采纳率 + 独立率双列**；surfacing 由 maintain 机械触发（Step 1）；砍/降采样人决，MUST NOT 自动。

- [ ] **Step 3: 机械核对**

Run: `grep -q 'lens_metric_aggregate' sdflow-maintain/SKILL.md && grep -q '≥10\|出现轮数' sdflow-maintain/SKILL.md && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task7-surfacing "maintain surfacing hook(N≥10 显著提示,防死列 SR-A) + 反馈判据泛化 per-镜双列"
```

---

### Task 8: grill 层留档 deferred item（SR grill 边界）

**Files:**
- Modify: `openspec/issues/todolist/2026-07-todolist.md`（新增 grill amendment-survival deferred item）

- [ ] **Step 1: 写 deferred item**

用 `/sdflow-todolist`（或直接编辑）加一条 todo：「grill amendment-下游存活率 度量」——明写口径未定义（`[grill-amendment]` 无 ID/无 ground truth 链接）、需自己的 explore、非本 change；裸数 amendment 条数是误导指标不采；归 workflow-metrics-loop 伞下与 T29 并列；关联 change=workflow-metrics-loop。跑 `issues.py reindex` 刷新 INDEX。

- [ ] **Step 2: 机械核对**

Run: `grep -q 'grill' openspec/issues/todolist/2026-07-todolist.md && grep -q '存活率\|amendment.*存活\|口径未定义' openspec/issues/todolist/2026-07-todolist.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task8-grill-defer "grill amendment-存活率度量 独立 deferred item 留档(口径未定义,需explore)"
```

---

### Task 9: delta 复核 + 部署（setup.sh）

**Files:**
- Verify: `openspec/changes/workflow-metrics-loop/specs/**`（对码复核）
- Run: `bash setup.sh`

- [ ] **Step 1: delta 对码复核**

Read `specs/workflow-metrics/spec.md` + `specs/spec-workflow/spec.md`，逐需求核与已落代码/契约/SKILL 实况一致（锚字段、site、config 门控、自检扩枚举、pre-gate 回写、surfacing）；不符则以实况改 spec。

- [ ] **Step 2: validate**

Run: `openspec validate workflow-metrics-loop`
Expected: `Change 'workflow-metrics-loop' is valid`

- [ ] **Step 3: 部署（全局 canonical 生效）**

Run: `bash setup.sh`
Expected: 成功（`~/.sdflow/workflow` canonical 指向本开发 checkout 的 `sdflow-init/assets/workflow/`，新契约 + tools 聚合器可解析到）。核对：`ls ~/.sdflow/workflow/lens-metric-contract.md ~/.sdflow/workflow/tools/lens_metric_aggregate.py`

- [ ] **Step 4: 全量 pytest 零回归**

Run: `python3 -m pytest -q`
Expected: 全绿（既有 + 新增 lens_metric 测试）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh workflow-metrics-loop:task9-deploy "delta 对码复核一致 + validate valid + setup.sh 部署 canonical + 全量 pytest 零回归"
```

---

## Self-Review

**Spec coverage（对 specs 逐需求核）**：
- 度量锚契约 sdflow:lens-metric v1 → Task 1（契约）+ Task 5/6（生产者落锚）✓
- 独立贡献去重导出 → Task 5/6 Step 2 ✓
- 只读聚合 view + fence-aware + 无锚计数 + 无合成分 → Task 3/4 ✓
- 数据驱动反馈 + surfacing → Task 7 ✓
- grill 留档边界 → Task 8 ✓
- site 消歧（SR-D/Q1）→ Task 1 契约 + Task 5/6 落锚 ✓
- config 门控（SR-G/Q2）→ Task 2 + Task 5/6/7 ✓
- 自检扩枚举+sev（SR-C/I）→ Task 1 契约 + Task 5 自检 + Task 3/4 测试 ✓
- pre-gate 回写（SR-M）→ Task 6 ✓
- enum 治理（SR-E）/ 示范锚 fence（SR-N）→ Task 1 契约 ✓
- Success Metric = fixture（SR-H）→ Task 3/4 pytest 即验收，真实归档=部署后观察 ✓
- 部署 setup.sh → Task 9 ✓

**Placeholder scan**：无 TBD/TODO；聚合器代码完整给出；机械核对步给了确切 grep 命令与期望。

**Type consistency**：`parse_anchor`/`parse_report`/`aggregate`/`render_table`/`main` 签名跨 Task 3→4 一致；字段名（layer/lens/runner/site/findings/采纳/裁掉/defer/独立/sev）跨契约/代码/测试逐字一致。

**任务边界**：Task 3（解析核）与 Task 4（聚合渲染）分开——reviewer 可独立否决解析而通过渲染；两 SKILL 分 Task 5/6（可各自审）；config/契约/maintain/留档各自独立可测。
