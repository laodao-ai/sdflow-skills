# lens-metric 计数确定性 emitter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增确定性脚本 `lens_metric_emit.py`，把 lens-metric 锚计数从主 session 手数下沉为「对结构化 findings + 行键 roster 的机械归约」。

**Architecture:** 纯 stdlib bundle tool。读契约 `lens-metric-enums`（枚举）+ `lens-metric-fold`（折叠）两机读块 → 逐 finding.hit 折叠成行键 `(lens,runner,site)` → 归属/独立/sev-rollup → 为 roster 每行键 emit 一行合规锚。坏输入 fail-closed + all-or-nothing（全校验过才产任何锚）。门控外置（不读 config）。

**Tech Stack:** Python 3（stdlib：argparse/json/re/pathlib）。测试 pytest。

## Global Constraints

- 脚本落 `sdflow-init/assets/workflow/tools/lens_metric_emit.py`（bundle 权威源）；测试落 sibling `sdflow-init/assets/workflow/tools/tests/`。
- **禁 import**：`yaml`、`lens_metric_aggregate`、`ship_gate`、`anchor_lint`（消费仓无 sdflow-retro/sdflow-ship；同 anchor_lint 重实现 fence/enums 读取）。
- **禁读 config**：门控归 SKILL 层（ADR-10），emitter 被调即视 metrics-on。
- 枚举单一源 = 契约 `lens-metric-enums` 块；折叠单一源 = 契约 `lens-metric-fold` 块；`verdict`/`sev` 级 = 本地常量豁免 / 从 `sev-format` 模板解析（ADR-11/C15），MUST NOT 复制枚举清单。
- 行键 = `(lens, runner, site)`，与锚唯一键对齐（ADR-8）；layer 单一源 = `--layer`（ADR-9，无 per-finding layer）。
- 锚形（逐字）：`<!-- sdflow:lens-metric v1 layer="…" lens="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->`
- **每任务 commit 步 MUST 由 implementer 显式执行**（gate 主锚契约，权威=ship_gate.py TAG_RE）：
  `~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task<N>-<desc> "<说明>"`
  命名空间前缀 = 完整 change 名，`task<N>-<desc>` 的 `-` 必需。

---

### Task 1: 契约 fold 块 + 机读块读取器（load_enums / load_fold）

**Files:**
- Modify: `sdflow-init/assets/workflow/lens-metric-contract.md`（在 `## 折叠表` 后加 `lens-metric-fold` 机读块）
- Create: `sdflow-init/assets/workflow/tools/lens_metric_emit.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py`

**Interfaces:**
- Produces: `EmitError`(Exception) · `load_enums(contract_path) -> {"layer":set,"lens":set,"runner":set,"sev_re":re,"sev_levels":tuple}` · `load_fold(contract_path, enums) -> dict[str,str]`

- [ ] **Step 1: 契约加 `lens-metric-fold` 机读块**

在 `sdflow-init/assets/workflow/lens-metric-contract.md` 的 `## 折叠表（canonical 投影）` 段**之后**插入（**只列非恒等**映射；恒等由 `raw∈lens_enum` pass-through 承载、不列本块）：

```markdown
## 机读折叠（消费脚本单一源·勿在脚本内复制）〔mlh-p4-lens-metric-emit〕
> 折叠单一源。格式同 `lens-metric-enums`：fence info-string 恒为 `lens-metric-fold`；每行 `原始镜名: canonical-lens`。**只列非恒等映射**——恒等（raw 已 ∈ lens enum，如 domain/grounding/history/broad）由 emitter `raw∈lens_enum` pass-through 承载、不列本块（ADR-7）。canonical 值 MUST ∈ `lens-metric-enums` 的 lens 域（emitter `load_fold` 读入即自校验）。
```lens-metric-fold
对抗镜1: adversarial
对抗镜2: adversarial
对抗镜3: adversarial
领域镜: domain
历史镜: history
接地镜: grounding
完整性镜: grounding
完整性接地镜: grounding
codex: outside-voice
claude-fallback: outside-voice
autoplan-ceo: broad
autoplan-design: broad
autoplan-eng: broad
autoplan-dx: broad
gstack-adv: broad
```
```

（注意：上方 markdown 内层 ```lens-metric-fold …``` 是要写进契约的真实 fenced 块。）

- [ ] **Step 2: 写失败测试（load_enums / load_fold 从真实契约读 + 缺块 fail-closed + 重复键/越域 fail-closed）**

写入 `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py`：

```python
import subprocess, sys, json, importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "lens_metric_emit.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"

def _mod():
    spec = importlib.util.spec_from_file_location("lens_metric_emit", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_load_enums_real_contract():
    e = _mod().load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain","adversarial","grounding","history","outside-voice","broad"}
    assert e["runner"] == {"claude","codex","claude-fallback"}
    assert e["sev_levels"] == ("致","高","中","低")
    assert e["sev_re"].match("致1/高2/中0/低3") and not e["sev_re"].match("致1/高2/中0")

def test_load_fold_real_contract():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert fold["对抗镜1"] == "adversarial" and fold["codex"] == "outside-voice"
    assert all(v in e["lens"] for v in fold.values())        # codomain ⊆ lens enum
    assert "domain" not in fold                              # 恒等项不列块

def test_load_enums_missing_block(tmp_path):
    m = _mod(); bad = tmp_path/"c.md"; bad.write_text("# no blocks", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_enums(bad)

def test_load_fold_dup_key_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n对抗镜1: adversarial\n对抗镜1: broad\n```\n", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_fold(c, e)

def test_load_fold_codomain_out_of_enum_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n某镜: newlens\n```\n", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_fold(c, e)
```

- [ ] **Step 3: 运行测试确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -v`
Expected: FAIL（`lens_metric_emit.py` 不存在 / 无 load_enums）

- [ ] **Step 4: 实现 load_enums / load_fold（含块读取器）**

写入 `sdflow-init/assets/workflow/tools/lens_metric_emit.py`：

```python
#!/usr/bin/env python3
"""lens_metric_emit — 确定性 lens-metric 锚 emitter（mlh-p4）。
吃 行键 roster + 结构化 findings，按契约折叠/归属/独立/sev-rollup 归约出合规锚行。
门控外置（不读 config）；坏输入 fail-closed all-or-nothing；禁 import yaml/aggregator/ship_gate/anchor_lint。"""
import argparse, json, re, sys
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1
VERDICTS = ("采纳", "裁掉", "defer")            # 本地常量豁免（ADR-11：输入独有、不写进锚、不与 anchor_lint 共享）
MANDATORY_LENS = ("broad", "outside-voice")     # 一致性测试守 == anchor_lint.MIN_LENS_ROWS（分叉①=B）
_SITE_BAD = re.compile(r'["\n\r]|-->|=')        # site 注入字符（C7）
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')


class EmitError(Exception):
    pass


def _read_block_pairs(text, info_string):
    """fence-aware 读 fenced 块内 `k: v` 行为 (k,v) 对列表（重实现同 anchor_lint 口径，不 import）。"""
    open_re = re.compile(r'^ {0,3}(`{3,}|~{3,})' + re.escape(info_string) + r'\s*$')
    body, in_block, fc, fl = [], False, None, 0
    for ln in text.splitlines():
        if not in_block:
            m = open_re.match(ln)
            if m:
                in_block = True; fc = m.group(1)[0]; fl = len(m.group(1))
            continue
        c = _FENCE.match(ln)
        if c and c.group(1)[0] == fc and len(c.group(1)) >= fl and ln[c.end():].strip() == "":
            break
        body.append(ln)
    if not in_block:
        raise EmitError(f"契约缺 {info_string} 机读块")
    pairs = []
    for ln in body:
        if ":" in ln:
            k, v = ln.split(":", 1)
            pairs.append((k.strip(), v.strip()))
    return pairs


def load_enums(contract_path):
    try:
        text = Path(contract_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise EmitError(f"契约不可读: {e}")
    kv = dict(_read_block_pairs(text, "lens-metric-enums"))
    def _set(k): return {x.strip() for x in kv.get(k, "").split(",") if x.strip()}
    layer, lens, runner = _set("layer"), _set("lens"), _set("runner")
    sev_fmt = kv.get("sev-format", "").strip()
    if not (layer and lens and runner and sev_fmt):
        raise EmitError("lens-metric-enums 块解析空/缺项")
    sev_re = re.compile("^" + re.escape(sev_fmt).replace("N", r"\d+") + "$")
    sev_levels = tuple(re.findall(r'([^N/]+)N', sev_fmt))   # 致N/高N/中N/低N → ('致','高','中','低')
    return {"layer": layer, "lens": lens, "runner": runner, "sev_re": sev_re, "sev_levels": sev_levels}


def load_fold(contract_path, enums):
    text = Path(contract_path).read_text(encoding="utf-8")
    fold_map = {}
    for raw, canon in _read_block_pairs(text, "lens-metric-fold"):
        if raw in fold_map:
            raise EmitError(f"lens-metric-fold 重复 raw 键: {raw}")
        if canon not in enums["lens"]:
            raise EmitError(f"lens-metric-fold codomain 越 lens-enum: {raw}→{canon}")  # C3 自校验
        fold_map[raw] = canon
    return fold_map
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -v`
Expected: PASS（5 个 test）

- [ ] **Step 6: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task1-contract-fold-readers "契约加 lens-metric-fold 块 + load_enums/load_fold（codomain 自校验+重复键 fail-closed）"
```

---

### Task 2: 折叠 hit → 行键（fold pass-through + outside-voice runner/site + site 消毒）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/lens_metric_emit.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py`

**Interfaces:**
- Consumes: `load_enums`, `load_fold`
- Produces: `fold_hit(hit, enums, fold_map) -> (lens, runner, site)`

- [ ] **Step 1: 写失败测试**

追加到测试文件：

```python
def test_fold_hit_identity_passthrough():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"domain"}, e, f) == ("domain","claude","—")

def test_fold_hit_nonidentity_map():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"对抗镜2"}, e, f) == ("adversarial","claude","—")

def test_fold_hit_outside_voice_needs_runner_site():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"codex","runner":"codex","site":"hr-tg"}, e, f) == ("outside-voice","codex","hr-tg")
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex"}, e, f)      # 缺 runner/site

def test_fold_hit_unknown_raw_fail_closed_not_broad():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"神秘镜"}, e, f)     # SR-E 不塞 broad

def test_fold_hit_site_injection_fail_closed():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex","runner":"codex","site":'a"b'}, e, f)
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k fold_hit -v`
Expected: FAIL（fold_hit 未定义）

- [ ] **Step 3: 实现 fold_hit**

追加到 `lens_metric_emit.py`：

```python
def fold_hit(hit, enums, fold_map):
    """一个 hit → 行键 (lens, runner, site)。恒等 pass-through；未知 raw fail-closed（不塞 broad）。"""
    if not isinstance(hit, dict) or "raw" not in hit:
        raise EmitError(f"hit 缺 raw: {hit!r}")
    raw = hit["raw"]
    if raw in enums["lens"]:
        canon = raw                                  # 恒等 pass-through（ADR-7）
    elif raw in fold_map:
        canon = fold_map[raw]
    else:
        raise EmitError(f"未知 raw 镜名无折叠映射: {raw}")  # SR-E 不静默塞 broad
    if canon == "outside-voice":
        runner, site = hit.get("runner"), hit.get("site")
        if runner is None or site is None:
            raise EmitError(f"outside-voice hit 缺 runner/site: {hit!r}")
    else:
        runner, site = "claude", "—"
    if runner not in enums["runner"]:
        raise EmitError(f"runner 越域: {runner}")
    if isinstance(site, str) and _SITE_BAD.search(site):
        raise EmitError(f"site 含非法字符（注入）: {site!r}")  # C7
    return (canon, runner, site)
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k fold_hit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task2-fold-hit "fold_hit：恒等 pass-through + ov runner/site 必填 + 未知 raw/site 注入 fail-closed"
```

---

### Task 3: 归约核心 reduce（归属 + 独立 + sev rollup + 不变量）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/lens_metric_emit.py`
- Test: 同上

**Interfaces:**
- Consumes: `fold_hit`, `load_enums`
- Produces: `reduce(roster, findings, layer, enums, fold_map) -> list[str]`（锚行列表；任一坏 → EmitError，产任何锚前全校验=all-or-nothing）

- [ ] **Step 1: 写失败测试（归约计数 + 共抓不独立 + 同类型多实例独立 + sev rollup）**

```python
def _ef():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e); return m, e, f

def test_reduce_single_accepted():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"design-voice"}]
    findings = [{"hits":[{"raw":"domain"}], "verdict":"采纳", "sev":"高"}]
    lines = m.reduce(roster, findings, "spec-review", e, f)
    dom = [l for l in lines if 'lens="domain"' in l][0]
    assert 'findings="1"' in dom and '采纳="1"' in dom and '独立="1"' in dom
    assert 'sev="致0/高1/中0/低0"' in dom
    # 零-finding 行全零
    ov = [l for l in lines if 'lens="outside-voice"' in l][0]
    assert 'findings="0"' in ov and 'sev="致0/高0/中0/低0"' in ov and 'site="design-voice"' in ov

def test_reduce_coreport_no_independent():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"},
              {"lens":"broad","runner":"claude","site":"—"}]
    findings = [{"hits":[{"raw":"domain"},{"raw":"codex","runner":"codex","site":"hr-tg"}],
                 "verdict":"采纳","sev":"中"}]
    lines = m.reduce(roster, findings, "spec-review", e, f)
    for lens in ("domain","outside-voice"):
        row = [l for l in lines if f'lens="{lens}"' in l][0]
        assert '采纳="1"' in row and '独立="0"' in row     # 共抓：各记采纳、均不独立

def test_reduce_same_type_multi_instance_independent():
    m, e, f = _ef()
    roster = [{"lens":"adversarial","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    findings = [{"hits":[{"raw":"对抗镜1"},{"raw":"对抗镜2"}], "verdict":"采纳","sev":"致"}]
    adv = [l for l in m.reduce(roster, findings, "spec-review", e, f) if 'lens="adversarial"' in l][0]
    assert '采纳="1"' in adv and '独立="1"' in adv and 'sev="致1/高0/中0/低0"' in adv
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k reduce -v`
Expected: FAIL（reduce 未定义）

- [ ] **Step 3: 实现 reduce（暂含 roster 校验 + MIN_LENS_ROWS + C4，后续 Task 4/5 补坏输入分支）**

追加到 `lens_metric_emit.py`：

```python
def reduce(roster, findings, layer, enums, fold_map):
    """全校验通过才产锚（all-or-nothing）：返回锚行 list；任一坏 → EmitError。"""
    if layer not in enums["layer"]:
        raise EmitError(f"--layer 越域: {layer}")
    # 1) roster → 行键（去重 + 越域 + site 消毒 + MIN_LENS_ROWS）
    roster_keys, seen = [], set()
    for it in roster:
        if not isinstance(it, dict) or not {"lens","runner","site"} <= set(it):
            raise EmitError(f"roster 项缺字段: {it!r}")
        if it["lens"] not in enums["lens"]:
            raise EmitError(f"roster lens 越域: {it['lens']}")
        if it["runner"] not in enums["runner"]:
            raise EmitError(f"roster runner 越域: {it['runner']}")
        if _SITE_BAD.search(it["site"]):
            raise EmitError(f"roster site 注入: {it['site']!r}")
        key = (it["lens"], it["runner"], it["site"])
        if key in seen:
            raise EmitError(f"roster 重复行键: {key}")
        seen.add(key); roster_keys.append(key)
    roster_lenses = {k[0] for k in roster_keys}
    for need in MANDATORY_LENS:                          # 被调即视 metrics-on
        if need not in roster_lenses:
            raise EmitError(f"roster 缺强制行 lens={need}（MIN_LENS_ROWS）")
    # 2) 累加器
    counts = {k: {"findings":0,"采纳":0,"裁掉":0,"defer":0,"独立":0,
                  "sev":{lv:0 for lv in enums["sev_levels"]}} for k in roster_keys}
    # 3) 逐 finding
    for fd in findings:
        if not isinstance(fd, dict) or "hits" not in fd or "verdict" not in fd:
            raise EmitError(f"finding 缺 hits/verdict: {fd!r}")
        hits = fd["hits"]
        if not isinstance(hits, list) or not hits:
            raise EmitError(f"finding hits 空/非数组: {fd!r}")           # C11
        verdict = fd["verdict"]
        if verdict not in VERDICTS:
            raise EmitError(f"verdict 越域: {verdict}")
        sev = fd.get("sev")
        if verdict == "采纳" and (not sev or sev not in enums["sev_levels"]):
            raise EmitError(f"采纳 finding 缺/非法 sev: {fd!r}")         # C12
        keyset = {fold_hit(h, enums, fold_map) for h in hits}
        for k in keyset:
            if k not in counts:
                raise EmitError(f"finding 命中行 {k} 不在 roster")       # C4 反方向
        for k in keyset:
            counts[k]["findings"] += 1
            counts[k][verdict] += 1
            if verdict == "采纳":
                counts[k]["sev"][sev] += 1
        if len(keyset) == 1 and verdict == "采纳":
            counts[next(iter(keyset))]["独立"] += 1
    # 4) sev 不变量：Σsev == 采纳
    for k, c in counts.items():
        if sum(c["sev"].values()) != c["采纳"]:
            raise EmitError(f"sev rollup 不变量破: {k} Σsev≠采纳")
    # 5) emit（确定序 = 行键排序）
    lines = []
    for k in sorted(roster_keys):
        c = counts[k]
        sev_str = "/".join(f"{lv}{c['sev'][lv]}" for lv in enums["sev_levels"])
        lines.append(
            f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{k[0]}" runner="{k[1]}" '
            f'site="{k[2]}" findings="{c["findings"]}" 采纳="{c["采纳"]}" 裁掉="{c["裁掉"]}" '
            f'defer="{c["defer"]}" 独立="{c["独立"]}" sev="{sev_str}" -->'
        )
    return lines
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k reduce -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task3-reduce-core "reduce 归约核心：行键归属/独立/sev-rollup + 零行 + MIN_LENS_ROWS + C4 + Σsev 不变量"
```

---

### Task 4: 坏输入 fail-closed 穷举（present-but-empty / 越域 / 采纳缺 sev / C4 / all-or-nothing）

**Files:**
- Test: 同上（reduce 已实现分支，本任务补测试锁定坏路径）

**Interfaces:**
- Consumes: `reduce`

- [ ] **Step 1: 写失败测试（穷举坏输入均 EmitError）**

```python
import pytest

def _base_roster():
    return [{"lens":"broad","runner":"claude","site":"—"},
            {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]

def test_reduce_empty_hits_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[], "verdict":"采纳","sev":"高"}], "spec-review", e, f)

def test_reduce_accepted_missing_sev_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"采纳"}], "spec-review", e, f)

def test_reduce_bad_verdict_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"通过","sev":"高"}], "spec-review", e, f)

def test_reduce_bad_layer_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [], "review", e, f)

def test_reduce_finding_lens_not_in_roster_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # C4：domain 不在 roster
        m.reduce(_base_roster(), [{"hits":[{"raw":"domain"}], "verdict":"采纳","sev":"高"}], "spec-review", e, f)

def test_reduce_roster_missing_mandatory_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # 缺 outside-voice
        m.reduce([{"lens":"broad","runner":"claude","site":"—"}], [], "spec-review", e, f)

def test_reduce_roster_dup_key_fail_closed():
    m, e, f = _ef()
    r = _base_roster() + [{"lens":"broad","runner":"claude","site":"—"}]
    with pytest.raises(m.EmitError):
        m.reduce(r, [], "spec-review", e, f)
```

- [ ] **Step 2: 运行确认全绿（reduce Task 3 已含分支）**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k "reduce and (fail_closed or mandatory or dup)" -v`
Expected: PASS（若某条红，回 Task 3 reduce 补对应分支）

- [ ] **Step 3: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task4-fail-closed-exhaustive "坏输入穷举测试锁定：空 hits/采纳缺 sev/越域/C4/缺强制行/重复键均 fail-closed"
```

---

### Task 5: CLI main + all-or-nothing stdout + 确定性/幂等

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/lens_metric_emit.py`
- Test: 同上

**Interfaces:**
- Consumes: `load_enums`, `load_fold`, `reduce`
- Produces: `main(argv=None) -> int`（exit 0 产锚到 stdout；坏输入 exit 1、stdout 无锚）

- [ ] **Step 1: 写失败测试（subprocess CLI：合法产锚 / 坏输入 exit1 空 stdout / 幂等跨进程）**

```python
def _run(inp_path, layer="spec-review"):
    return subprocess.run([sys.executable, str(SCRIPT), "--layer", layer, "--input", str(inp_path)],
                          capture_output=True, text=True)

def test_cli_valid_emits(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}], "verdict":"采纳","sev":"高"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 0
    assert r.stdout.count("<!-- sdflow:lens-metric v1") == 2

def test_cli_bad_json_exit1_no_stdout(tmp_path):
    inp = tmp_path/"in.json"; inp.write_text("{not json", encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout and r.stderr.strip()

def test_cli_partial_fail_no_partial_anchor(tmp_path):
    # 第 2 条 finding 坏（采纳缺 sev）→ 全失败、stdout 无任何锚（all-or-nothing）
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"},
                    {"hits":[{"raw":"broad"}],"verdict":"采纳"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout

def test_cli_idempotent_cross_process(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"domain","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"domain"}],"verdict":"采纳","sev":"中"}]}, ensure_ascii=False), encoding="utf-8")
    import os
    env0 = dict(os.environ, PYTHONHASHSEED="0"); env1 = dict(os.environ, PYTHONHASHSEED="1")
    a = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(inp)],
                       capture_output=True, text=True, env=env0).stdout
    b = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(inp)],
                       capture_output=True, text=True, env=env1).stdout
    assert a == b and a.count("lens-metric v1") == 3      # 跨 hashseed 字节一致
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k cli -v`
Expected: FAIL（main/CLI 未定义）

- [ ] **Step 3: 实现 main**

追加到 `lens_metric_emit.py`：

```python
def main(argv=None):
    ap = argparse.ArgumentParser(description="lens-metric 锚 emitter（确定性·fail-closed·门控外置）")
    ap.add_argument("--layer", required=True, choices=["spec-review", "code-review"])
    ap.add_argument("--input", required=True)
    ap.add_argument("--contract", default=None)
    args = ap.parse_args(argv)
    contract = args.contract or str(Path(__file__).resolve().parent.parent / "lens-metric-contract.md")
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        enums = load_enums(contract)
        fold_map = load_fold(contract, enums)
        if not isinstance(data, dict) or "roster" not in data or "findings" not in data:
            raise EmitError("输入缺 roster/findings 顶层键")
        lines = reduce(data["roster"], data["findings"], args.layer, enums, fold_map)  # all-or-nothing
    except (EmitError, json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        print(f"[lens_metric_emit] FAIL: {e}", file=sys.stderr)
        return EXIT_FAIL
    print("\n".join(lines))                                # 仅全校验过才输出（无部分锚）
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 运行确认通过**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k cli -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task5-cli-main "CLI main：--layer/--input，all-or-nothing stdout，跨 PYTHONHASHSEED 幂等"
```

---

### Task 6: 产出↔校验/聚合一致性（emit-then-check_lens_metric / 三方 enum 守卫 / 等价性 / MIN_LENS_ROWS）

**Files:**
- Test: 同上

**Interfaces:**
- Consumes: emitter 全部 + `anchor_lint`（测试内 importlib 加载，非脚本 import）+ `lens_metric_aggregate`

- [ ] **Step 1: 写测试（构造保证过 check_lens_metric + 单一源三方一致）**

```python
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm); return mm

AL = TOOLS / "anchor_lint.py"
AGG = TOOLS.parent.parent.parent / "sdflow-retro" / "scripts" / "lens_metric_aggregate.py"

def test_emit_then_check_lens_metric_clean(tmp_path):
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    lines = m.reduce(roster, [{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"}], "spec-review", e, f)
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    report = "\n".join(lines) + "\n"
    assert al.check_lens_metric(report, "spec-review", enums) == []   # 无违规（C5 精确口径）

def test_load_enums_equivalence():
    m = _mod(); al = _load("anchor_lint", AL)
    me, ae = m.load_enums(CONTRACT), al.load_enums(CONTRACT)
    for k in ("layer","lens","runner"):
        assert me[k] == ae[k]
    assert me["sev_re"].pattern == ae["sev_re"].pattern       # C10 逐字段等价

def test_fold_codomain_subset_lens_enum():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert set(fold.values()) <= e["lens"]                   # C3

def test_aggregator_enum_matches_contract():
    m = _mod(); e = m.load_enums(CONTRACT); agg = _load("lens_metric_aggregate", AGG)
    assert agg.LENS_ENUM == e["lens"] and agg.LAYER_ENUM == e["layer"]   # C23

def test_min_lens_rows_matches_anchor_lint():
    m = _mod(); al = _load("anchor_lint", AL)
    assert set(m.MANDATORY_LENS) == set(al.MIN_LENS_ROWS)     # C17 分叉①=B
```

- [ ] **Step 2: 运行确认通过（全部为真实一致性断言）**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k "equivalence or codomain or aggregator or min_lens or check_lens" -v`
Expected: PASS（若 aggregator/anchor_lint 与契约漂移则红——正是守卫目的）

- [ ] **Step 3: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task6-consistency-guards "一致性守卫：emit→check_lens_metric 净、load_enums 等价、fold codomain⊆lens、aggregator enum==契约、MIN_LENS_ROWS 一致"
```

---

### Task 7: golden fixture + 两审 SKILL 落锚步接 emitter + 契约注记

**Files:**
- Create: `sdflow-init/assets/workflow/tools/tests/fixtures/lens_metric_input.json`（golden 输入）
- Modify: `sdflow-spec-review/SKILL.md`（Step3/Step4 落锚步）
- Modify: `sdflow-code-review/SKILL.md`（Step3-5 落锚步）
- Modify: `sdflow-init/assets/workflow/lens-metric-contract.md`（归属规则 prose 注记）
- Test: 同上

**Interfaces:**
- Consumes: emitter CLI

- [ ] **Step 1: 写 golden fixture 测试**

```python
FIX = TOOLS / "tests" / "fixtures" / "lens_metric_input.json"
def test_golden_fixture_emits_and_lints(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(FIX)],
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.count("lens-metric v1") >= 2
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    assert al.check_lens_metric(r.stdout + "\n", "spec-review", enums) == []
```

- [ ] **Step 2: 运行确认失败（fixture 不存在）**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k golden -v`
Expected: FAIL

- [ ] **Step 3: 建 golden fixture**

`sdflow-init/assets/workflow/tools/tests/fixtures/lens_metric_input.json`：

```json
{
  "roster": [
    {"lens":"broad","runner":"claude","site":"—"},
    {"lens":"domain","runner":"claude","site":"—"},
    {"lens":"adversarial","runner":"claude","site":"—"},
    {"lens":"grounding","runner":"claude","site":"—"},
    {"lens":"outside-voice","runner":"codex","site":"design-voice"},
    {"lens":"outside-voice","runner":"codex","site":"hr-tg"}
  ],
  "findings": [
    {"hits":[{"raw":"领域镜"},{"raw":"codex","runner":"codex","site":"hr-tg"}],"verdict":"采纳","sev":"高"},
    {"hits":[{"raw":"对抗镜1"},{"raw":"对抗镜2"}],"verdict":"采纳","sev":"中"},
    {"hits":[{"raw":"完整性镜"}],"verdict":"裁掉","sev":"低"}
  ]
}
```

- [ ] **Step 4: 改两审 SKILL 落锚步 + 契约注记**

在 `sdflow-spec-review/SKILL.md` Step3/Step4 落锚步、`sdflow-code-review/SKILL.md` Step3-5 落锚步，把「手折叠+手数+手写锚」改为：

> 构造 `{roster:[{lens,runner,site}…本轮跑过的每个行键], findings:[{hits:[{raw,runner?,site?}…],verdict,sev}…]}`（schema 见 `lens-metric-emit` 能力 + golden fixture `tools/tests/fixtures/lens_metric_input.json`）→ **metrics 关时不调 emitter**；开时 `python3 $RULES_ROOT/tools/lens_metric_emit.py --layer <L> --input <f>` → **exit 0 才**把 stdout 落进报告度量锚段 → 再跑 `anchor_lint` 自检。**保留**残余信任边界声明（分类正确性 + roster 完备性 + JSON 誊写仍是主 session 边界）。

在 `sdflow-init/assets/workflow/lens-metric-contract.md` 的 `## 归属规则（钉死）` 段补一句：

> 〔mlh-p4〕计数由 `lens_metric_emit.py` 从结构化 findings + 行键 roster 确定性归约产出（非手数）；「独立在折叠后计」精化为「折叠到**行键 `(lens,runner,site)`** 后计」。

- [ ] **Step 5: 运行确认通过 + 契约同步下游**

Run: `pytest sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -k golden -v`
Expected: PASS

Run: `python3 ~/.sdflow/workflow/tools/anchor_lint.py --report /dev/null --layer spec-review --root "$(git rev-parse --show-toplevel)" 2>&1 | head -1` （确认 anchor_lint 仍能 load_enums——契约新增 fold 块不破坏 enums 块解析）

- [ ] **Step 6: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task7-skill-fixture-contract "golden fixture + 两审 SKILL 落锚步接 emitter（门控关不调/exit0 才落）+ 契约归属注记"
```

---

### Task 8: 全量绿 + dogfood 端到端 + 验收对账

**Files:**
- Test: 全套
- Modify: （如需）`sdflow-init/tests/test_init_contract_sync.py`（若契约 sync 测试断言块数）

**Interfaces:** 无新增

- [ ] **Step 1: 全量 pytest + -W error**

Run: `pytest sdflow-init/ -q && pytest -W error sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py -q`
Expected: PASS（0 warning）

- [ ] **Step 2: dogfood setup + 契约 sync 一致性**

Run: `bash setup.sh 2>&1 | tail -3`
Expected: 成功（bundle symlink 生效，新 tool 可被两审 SKILL 调到）

Run: `python3 ~/.sdflow/workflow/tools/lens_metric_emit.py --layer spec-review --input sdflow-init/assets/workflow/tools/tests/fixtures/lens_metric_input.json | head -2`
Expected: 输出合规 lens-metric 锚行（经全局 symlink 路径调到）

若 `test_init_contract_sync.py` 因契约新增 `lens-metric-fold` 块失败（断言块数/内容），同步更新其期望值。

- [ ] **Step 3: 验收对账（specs Scenario ↔ 测试锚点）**

逐条核对（写入 commit message 或对话，无代码改动则跳过）：
- lens-metric-emit R1（归约/共抓/同类型独立/零行/C4/强制行）↔ Task 3-4 test
- lens-metric-emit R2（越域/空 hits/采纳缺 sev/site 注入/all-or-nothing/重复键/单一源读取）↔ Task 4-5 test
- lens-metric-emit R3（emit→check_lens_metric/load_enums 等价/残余边界）↔ Task 6 test
- workflow-metrics MODIFIED（计数机械化/残余边界）↔ Task 3+6 test
- 区分机械测试锚点 vs 文档保留锚点（残余边界声明类 = SKILL/契约 prose，非 pytest）

- [ ] **Step 4: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh implement-mechanical-layer-hardening-p4-lens-metric-emit:task8-green-dogfood-verify "全量 pytest 绿 + dogfood setup 端到端 + 验收对账 specs↔测试"
```

---

## Self-Review

**Spec coverage**：
- lens-metric-emit R1（行键归约/折叠 pass-through/独立/零行/C4/强制行）→ Task 2/3/4 ✓
- lens-metric-emit R2（坏输入穷举/all-or-nothing/单一源读取）→ Task 1/4/5 ✓
- lens-metric-emit R3（check_lens_metric/load_enums 等价/残余边界诚实声明）→ Task 6 + Task 7 SKILL prose ✓
- workflow-metrics MODIFIED（emitter 归约/归属键=行键/门控外置）→ Task 3/5/7 ✓
- 单一源（fold codomain/aggregator/MIN_LENS_ROWS）→ Task 1/6 ✓

**Placeholder scan**：无 TBD/TODO；每步含实际代码与命令。

**Type consistency**：`fold_hit`/`reduce`/`load_enums`/`load_fold`/`main` 签名跨任务一致；行键三元组 `(lens,runner,site)` 全程一致；`enums["sev_levels"]` 元组序驱动 sev 输出。

**注意**：契约 `lens-metric-fold` 块的 canonical 值 pass-through 使「lens enum 每值可被 fold 命中」自动满足（恒等），故 C3 守卫的实质断言 = `fold_codomain ⊆ lens_enum`（Task 1 load_fold 自校验 + Task 6 test），反向为平凡真、不单列。
