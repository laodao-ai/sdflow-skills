# add-sdflow-architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建 `sdflow-architecture` skill（系统架构设计编排器）：输入简单需求 → 产出 skeleton-ready SAD（消费仓 `openspec/architecture/sad.md` 项目级单例）+ 内嵌「骨架切片建议」节交棒。

**Architecture:** 五组件——SKILL.md 五步流程编排 + references 六件（模版/规则集/判据/镜单/问卷/清单库）+ scripts 三件（`sad_schema.py` 格式与解析单一源、`sad_scaffold.py` 脚手架+状态机+分家写入、`sad_lint.py` v1 结构断言）+ tests。机械层独占状态迁移与格式一致性（DEC-1/2/3/4），语义残余归冷走查与人门。

**Tech Stack:** Python 3 stdlib（argparse/re/pathlib/datetime）、pytest；Markdown skill 指令；setup.sh symlink 分发。

## Global Constraints

以下逐字级硬约束，每个任务的要求隐式包含本节：

- **checkpoint 格式（ship_gate TAG_RE）**：每任务结尾 MUST 跑 `bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task<N>-<slug>" "<一句话>"`——slug 含横杠且非空（如 `task1-sad-schema`）；写成 `task<N>` 无尾横杠会让 gate 完成数卡 0/N。
- **实现期 MUST NOT 修改 change 四件套**（`openspec/changes/add-sdflow-architecture/{proposal,design,tasks}.md` 与 `specs/`——含勾选 tasks.md 复选框，勾选留到 done 的 archive 阶段），否则 ship_gate 设计门失鲜 REFUSE_START。新增文件（如 impl-verify-notes.md）允许。
- **子代理先 Read 再 Edit**（Edit 工具要求目标文件先 Read 过，否则报 "Error editing file"）。
- **纯 stdlib**：三脚本无第三方依赖、无 subprocess、不读 config；坏输入 fail-closed 非零退出。
- **解析一律行锚定 + fence-aware，覆盖全部正文扫描**（DEC-2）——`[假设-N]` 实扫 / 节标题锚 / N/A 行 / 假设清单表全走 `sad_schema.body_lines()`，MUST NOT naive 全文正则（模版自带 fence 内标记示例，非 fence 感知必自指假阳）。
- **解析函数只在 `sad_schema.py`**（DEC-1）：scaffold/lint 只 import 消费，MUST NOT 各写解析器。
- **文件写入一律原子写 temp+rename**（DEC-8）；`sad-log.md` append-only（追加后既有字节逐字节不变）。
- **状态迁移只由 `sad_scaffold.py` 执行**（DEC-4），合法迁移以 design 显式迁移表为准，表外拒绝 + stderr。
- **lint 输出诚实**（DEC-5）：通过码 `structure-ok-SEMANTICS-UNCHECKED`；坏输入 fail-closed（exit 2 + stderr `[sad_lint] FAIL:`），与正常 reason_code 判定（exit 1）物理区分；每个 reason_code 携带一行 next-step 提示。
- **节标题锚 v1 中文单语**（DEC-12③）；lint 假设计数以正文实扫为准，frontmatter `assumptions_open` 仅展示缓存（DEC-12②）。
- **MUST NOT 触碰** `openspec/workflow/` 与 `sdflow-init/assets/`（本 change 不涉 workflow bundle）。
- 引用蓝本 `docs/sad/02-sad-skill-design.md` 时**只读转写**，MUST NOT 修改该文件（已冻结考古层）。

---

## File Structure

| 文件 | 责任 | 动作 |
|---|---|---|
| `sdflow-architecture/scripts/sad_schema.py` | 格式常量 + 解析函数单一源（DEC-1/2） | Create |
| `sdflow-architecture/scripts/sad_scaffold.py` | init/preflight/状态机/facts/假设处置/分家写入/sad-log | Create |
| `sdflow-architecture/scripts/sad_lint.py` | v1 结构断言 + reason_code + next-step | Create |
| `sdflow-architecture/tests/conftest.py` | 合法 SAD fixture 构造器 | Create |
| `sdflow-architecture/tests/test_sad_schema.py` | 常量/正则/解析正负路径 | Create |
| `sdflow-architecture/tests/test_sad_scaffold.py` | 建骨架/原子写/preflight/迁移表/对账/单例 | Create |
| `sdflow-architecture/tests/test_sad_lint.py` | 每类断言正负≥2 + fail-closed | Create |
| `sdflow-architecture/references/sad-template.md` | 十节骨架 + frontmatter + 标记示例 | Create |
| `sdflow-architecture/references/{decomposition-rules,quality-criteria,review-lenses,intake-questionnaire}.md` | 蓝本定稿转写 | Create |
| `sdflow-architecture/references/checklists/`（4 件） | 横切模板/质量属性库/外部依赖集/R4 变化类别 | Create |
| `sdflow-architecture/SKILL.md` | 五步流程编排 | Create |
| `sdflow-roadmap/SKILL.md` | description 加指路句（roadmap-planning delta） | Modify（仅 frontmatter description） |
| `README.md` | Skills 列表新增条目 | Modify |

**机械文本形态锁定（三方共享契约，全部锚入 sad_schema.py，模版逐字一致）**：

- 十节标题锚：`## 1. 目标与质量属性` / `## 2. 约束` / `## 3. 外边界` / `## 4. 架构策略与 ADR 索引` / `## 5. 子系统分解与 contract` / `## 6. 运行场景` / `## 7. 部署` / `## 8. 横切概念` / `## 9. 风险登记` / `## 10. 词汇表引用`
- 暂态节：`## 骨架切片建议`；附录：`## 附录：假设清单`
- 子系统标题：`### 5.<i> <名称>`；contract 行：`- contract[planned|draft|validated|frozen] <名>：<五层主干>`
- 穿越点行（建议节内）：`- 穿越点[<子系统名>]：<引用 §5 条目>`
- 假设内联：`[假设-N]`；清单表行：`| 假设-N | <位置> | <内容> | <依据> | 接受/待校准/未处置 |`（编号列**无方括号**，与内联正则物理区分）
- N/A 行：`N/A — <非空理由>`；质量属性全序：第 1 节 `1.`…`N.` 连续有序列表

---

### Task 1: sad_schema.py（常量 + 解析核心）+ 单元测试

**R-ID:** REQ-5/6/10 · **tasks.md:** §1.1

**Files:**
- Create: `sdflow-architecture/scripts/sad_schema.py`
- Create: `sdflow-architecture/tests/conftest.py`、`sdflow-architecture/tests/test_sad_schema.py`

**Interfaces（后续任务全部依赖，签名逐字）:**
- `SAD_SCHEMA_VERSION=1` · `STATUS_ENUM` · `CONTRACT_ENUM` · `FACT_KEYS` · `FACT_VALUES` · `DISPOSITIONS=("接受","待校准","未处置")` · `SECTION_ANCHORS`（10 元组，上表逐字） · `SLICE_ANCHOR` · `APPENDIX_ANCHOR` · `REASON_NEXT_STEP: dict[str,str]` · `PASS_CODE="structure-ok-SEMANTICS-UNCHECKED"`
- `class SadParseError(Exception)` — 坏输入 fail-closed 面
- `body_lines(text) -> list[(lineno,line)]` — fence-aware 行流（``` 开合行自身与栏内行均剔除）
- `parse_frontmatter(text) -> dict` — 返回 `{"sad_schema":int,"sad_status":str,"facts":dict,"assumptions_open":int}`；坏形态 raise SadParseError
- `scan_sections(text) -> dict[anchor,{"present":bool,"body":[(lineno,line)]}]`
- `scan_assumptions(text) -> (inline_ids:list[int], rows:list[(int,str)])` — 内联编号按出现序含重复；rows=(编号,处置)含重复
- `check_assumptions(text) -> list[(code,detail)]` — 对账共用核心（scaffold 锁 draft 复检与 lint 同用）
- `scan_subsystems(text) -> list[str]`、`scan_pierce_refs(text) -> list[str]`、`scan_contract_tags(text) -> list[(lineno,tag)]`

- [ ] **Step 1: 写失败测试（fence-aware + frontmatter 坏形态 + 对账）**

`conftest.py`（合法 SAD 构造器，全部测试复用）：

```python
import textwrap

def make_sad(status="draft", schema=1, facts=None, cache=0, assumptions=(),
             slice_section=False, subsystems=("采集端",), extra=""):
    """构造结构合法的 SAD 文本。assumptions=[(编号,处置)]，同时产内联与表行。"""
    facts = facts or {"positioning": "missing", "external_systems": "missing",
                      "hard_constraints": "missing"}
    fm = ["---", f"sad_schema: {schema}", f"sad_status: {status}", "facts:"]
    fm += [f"  {k}: {v}" for k, v in facts.items()]
    fm += [f"assumptions_open: {cache}", "---", ""]
    body = ["# SAD", ""]
    inline = " ".join(f"[假设-{n}]" for n, _ in assumptions) or "无假设。"
    sections = {
        "## 1. 目标与质量属性": "1. 可靠性\n2. 可维护性",
        "## 2. 约束": f"栈已定〔人拍〕 {inline}",
        "## 3. 外边界": "N/A — 单机无外部系统",
        "## 4. 架构策略与 ADR 索引": "见 openspec/adr/",
        "## 5. 子系统分解与 contract": "\n".join(
            f"### 5.{i+1} {s}\n- contract[draft] {s}接口：语法/语义/错误语义主干"
            for i, s in enumerate(subsystems)),
        "## 6. 运行场景": "场景A：启动→采集→上报",
        "## 7. 部署": "单机 binary",
        "## 8. 横切概念": "N/A — v1 无横切面",
        "## 9. 风险登记": "无已知风险",
        "## 10. 词汇表引用": "见 openspec/CONTEXT.md",
    }
    for anchor, content in sections.items():
        body += [anchor, "", content, ""]
    if slice_section:
        body += ["## 骨架切片建议", ""]
        body += [f"- 穿越点[{s}]：§5 contract 条目" for s in subsystems]
        body += ["- 骨架 DoD：每条 L1 contract 被一次真实调用穿过 + 部署链路走通",
                 "- 建议 change 名：skeleton-demo", ""]
    body += ["## 附录：假设清单", "", "| 编号 | 位置 | 内容 | 依据 | 处置 |",
             "|---|---|---|---|---|"]
    body += [f"| 假设-{n} | §2 | 某推测 | 类比 | {d} |" for n, d in assumptions]
    return "\n".join(fm + body) + ("\n" + extra if extra else "") + "\n"
```

`test_sad_schema.py` 关键用例（全部先写、先跑确认 import 失败）：

```python
import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad

def test_body_lines_skips_fences():
    text = "a\n```\n[假设-9]\n## 1. 目标与质量属性\n```\nb\n"
    lines = [l for _, l in S.body_lines(text)]
    assert lines == ["a", "b"]          # fence 内标记/节锚不进行流

def test_parse_frontmatter_ok():
    fm = S.parse_frontmatter(make_sad(facts={"positioning": "answered",
        "external_systems": "answered", "hard_constraints": "missing"}))
    assert fm["sad_status"] == "draft" and fm["facts"]["hard_constraints"] == "missing"

@pytest.mark.parametrize("mutate,label", [
    (lambda t: t.replace("sad_status: draft", "sad_status: draft\nsad_status: draft"), "duplicate-key"),
    (lambda t: t.replace("assumptions_open", "unknown_key"), "out-of-domain"),
    (lambda t: t.replace("sad_schema: 1", "sad_schema: one"), "bad-type"),
    (lambda t: t.replace("  positioning", "\tpositioning"), "tab-indent"),
    (lambda t: t.replace("facts:\n  positioning: missing\n", "facts: inline\n  positioning: missing\n"), "facts-inline"),
    (lambda t: t.replace("sad_status: draft", "sad_status: approved"), "enum-invalid"),
    (lambda t: t.replace("  positioning: missing", "  color: red"), "facts-unknown-subkey"),
], ids=lambda x: x if isinstance(x, str) else "")
def test_parse_frontmatter_bad_forms_fail_closed(mutate, label):
    with pytest.raises(S.SadParseError):
        S.parse_frontmatter(mutate(make_sad()))

def test_facts_key_missing_means_missing_not_crash():
    text = make_sad().replace("  hard_constraints: missing\n", "")
    fm = S.parse_frontmatter(text)
    assert fm["facts"].get("hard_constraints", "missing") == "missing"

def test_scan_assumptions_and_check():
    ok = make_sad(assumptions=[(1, "接受"), (2, "待校准")], cache=0)
    assert S.check_assumptions(ok) == []
    dup = make_sad(assumptions=[(1, "接受")],
                   extra="[假设-1] 重号内联\n")           # 内联两个1，表一行 → 集合仍相等但重号
    codes = [c for c, _ in S.check_assumptions(dup)]
    assert "assumption-set-mismatch" in codes
    unresolved = make_sad(assumptions=[(1, "未处置")])
    codes = [c for c, _ in S.check_assumptions(unresolved)]
    assert "assumption-unresolved" in codes

def test_scan_subsystems_and_pierce():
    t = make_sad(subsystems=("采集端", "上报端"), slice_section=True, status="skeleton-ready")
    assert S.scan_subsystems(t) == ["采集端", "上报端"]
    assert S.scan_pierce_refs(t) == ["采集端", "上报端"]

def test_every_reason_code_has_next_step():
    for code in ("missing-section", "na-without-reason", "assumption-set-mismatch",
                 "assumption-unresolved", "assumption-cache-mismatch",
                 "quality-attr-order-broken", "schema-version-mismatch",
                 "contract-invariant-violation", "slice-section-missing",
                 "slice-section-stale", "slice-pierce-set-mismatch"):
        assert S.REASON_NEXT_STEP[code].strip()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-architecture/tests/test_sad_schema.py -v`
Expected: FAIL（`ModuleNotFoundError: sad_schema`）

- [ ] **Step 3: 实现 sad_schema.py**

```python
#!/usr/bin/env python3
"""sad_schema.py — SAD 格式常量与解析单一源（DEC-1）。

scaffold（写侧）/ lint（读侧）共享本模块；各自只做消费方语义校验，
MUST NOT 另写解析器（adr/0011）。纯 stdlib。
解析口径：行锚定 + fence-aware 覆盖全部正文扫描（DEC-2）。
节标题锚 v1 中文单语（DEC-12③）。
"""
import re

SAD_SCHEMA_VERSION = 1
SAD_REL_PATH = "openspec/architecture/sad.md"
LOG_REL_PATH = "openspec/architecture/sad-log.md"

STATUS_ENUM = ("draft", "skeleton-ready", "validated")      # 文档级无 frozen
CONTRACT_ENUM = ("planned", "draft", "validated", "frozen")
FACT_KEYS = ("positioning", "external_systems", "hard_constraints")
FACT_VALUES = ("answered", "missing")
DISPOSITIONS = ("接受", "待校准", "未处置")
TOP_KEYS = ("sad_schema", "sad_status", "facts", "assumptions_open")

SECTION_ANCHORS = (
    "## 1. 目标与质量属性", "## 2. 约束", "## 3. 外边界",
    "## 4. 架构策略与 ADR 索引", "## 5. 子系统分解与 contract",
    "## 6. 运行场景", "## 7. 部署", "## 8. 横切概念",
    "## 9. 风险登记", "## 10. 词汇表引用",
)
SLICE_ANCHOR = "## 骨架切片建议"
APPENDIX_ANCHOR = "## 附录：假设清单"

ASSUMPTION_RE = re.compile(r"\[假设-(\d+)\]")
NA_RE = re.compile(r"^N/A\s*—\s*\S")
ORDERED_RE = re.compile(r"^(\d+)\.\s+\S")
SUBSYS_RE = re.compile(r"^###\s+5\.\d+\s+(.+?)\s*$")
CONTRACT_RE = re.compile(r"contract\[([a-z]+)\]")
PIERCE_RE = re.compile(r"^-\s*穿越点\[(.+?)\]：")
APPENDIX_ROW_RE = re.compile(r"^\|\s*假设-(\d+)\s*\|(?:[^|]*\|){3}\s*([^|\s]+)\s*\|\s*$")

PASS_CODE = "structure-ok-SEMANTICS-UNCHECKED"
REASON_NEXT_STEP = {
    "missing-section": "补该节内容，或写显式 `N/A — <理由>` 行；节标题须逐字用 SECTION_ANCHORS",
    "na-without-reason": "把裸 N/A 改为 `N/A — <非空理由>`",
    "assumption-set-mismatch": "对齐正文 [假设-N] 与附录清单的编号集合（双向相等、双侧无重号）",
    "assumption-unresolved": "人门逐条处置后跑 `sad_scaffold.py set-assumption --assumption <N>=接受|待校准`",
    "assumption-cache-mismatch": "以正文为准；任一 scaffold 写命令会刷新 assumptions_open 缓存",
    "quality-attr-order-broken": "第 1 节质量属性写成 `1.`…`N.` 连续有序列表（全序，无并列无重号）",
    "schema-version-mismatch": "SAD 的 sad_schema 与脚本支持版本不符——升级 SAD 或更新 skill（重跑 setup.sh）后再 lint",
    "contract-invariant-violation": "组合不变式：draft/skeleton-ready ⇒ contract∈{planned,draft}；validated ⇒ 非 planned 全∈{validated,frozen}",
    "slice-section-missing": "skeleton-ready 须含「骨架切片建议」节——经 `sad_scaffold.py transition --to skeleton-ready --slice-file <f>` 写入",
    "slice-section-stale": "validated 不应残留「骨架切片建议」节——`transition --to validated` 会移除，勿手工恢复",
    "slice-pierce-set-mismatch": "建议节 穿越点[子系统] 集合须与第 5 节 `### 5.x` 子系统集完全一致",
}


class SadParseError(Exception):
    """坏输入（fail-closed 面）：frontmatter 损坏/枚举非法/文件形态坏。"""


def body_lines(text):
    out, in_fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


def _to_int(key, raw):
    if not re.fullmatch(r"-?\d+", raw.strip()):
        raise SadParseError(f"bad-type: {key} 须为整数，得到 {raw!r}")
    return int(raw)


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SadParseError("frontmatter 缺失：首行须为 ---")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise SadParseError("frontmatter 未闭合：缺结束 ---")
    fm, facts, in_facts = {}, {}, False
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if raw.startswith("\t") or (raw != raw.lstrip() and "\t" in raw[:len(raw) - len(raw.lstrip())]):
            raise SadParseError(f"tab-indent: frontmatter 禁用 tab 缩进: {raw!r}")
        if raw.startswith("  ") and in_facts:
            k, _, v = raw.strip().partition(":")
            k, v = k.strip(), v.strip()
            if k not in FACT_KEYS:
                raise SadParseError(f"out-of-domain: facts 未知子键 {k!r}")
            if k in facts:
                raise SadParseError(f"duplicate-key: facts.{k}")
            if v not in FACT_VALUES:
                raise SadParseError(f"out-of-domain: facts.{k} 值须∈{FACT_VALUES}，得到 {v!r}")
            facts[k] = v
            continue
        in_facts = False
        k, sep, v = raw.partition(":")
        k, v = k.strip(), v.strip()
        if not sep or raw != raw.lstrip():
            raise SadParseError(f"frontmatter 不可解析行: {raw!r}")
        if k not in TOP_KEYS:
            raise SadParseError(f"out-of-domain: 未知键 {k!r}（白名单 {TOP_KEYS}）")
        if k in fm or (k == "facts" and facts):
            raise SadParseError(f"duplicate-key: {k}")
        if k == "facts":
            if v:
                raise SadParseError("facts 须为嵌套块，不接受内联标量")
            in_facts = True
            fm["facts"] = facts
            continue
        fm[k] = v
    if "sad_schema" not in fm or "sad_status" not in fm:
        raise SadParseError("frontmatter 缺必需键 sad_schema / sad_status")
    fm["sad_schema"] = _to_int("sad_schema", fm["sad_schema"])
    if fm["sad_status"] not in STATUS_ENUM:
        raise SadParseError(f"out-of-domain: sad_status 须∈{STATUS_ENUM}，得到 {fm['sad_status']!r}")
    fm["assumptions_open"] = _to_int("assumptions_open", fm.get("assumptions_open", "0"))
    fm.setdefault("facts", facts)   # 缺失 ≡ 全 missing（锁 draft 方向，不崩溃）
    return fm


def _section_spans(text):
    """返回 [(heading_line, [body (lineno,line)...])]，按 `## ` 顶级切分（fence-aware）。"""
    spans, cur, cur_body = [], None, []
    for ln, line in body_lines(text):
        if line.startswith("## "):
            if cur is not None:
                spans.append((cur, cur_body))
            cur, cur_body = line.strip(), []
        elif cur is not None:
            cur_body.append((ln, line))
    if cur is not None:
        spans.append((cur, cur_body))
    return spans


def scan_sections(text):
    spans = dict(_section_spans(text))
    return {a: {"present": a in spans, "body": spans.get(a, [])} for a in SECTION_ANCHORS}


def scan_assumptions(text):
    inline, rows = [], []
    appendix_bodies = [b for h, b in _section_spans(text) if h == APPENDIX_ANCHOR]
    appendix_lns = {ln for b in appendix_bodies for ln, _ in b}
    for ln, line in body_lines(text):
        if ln in appendix_lns:
            m = APPENDIX_ROW_RE.match(line)
            if m:
                rows.append((int(m.group(1)), m.group(2)))
            continue
        inline += [int(n) for n in ASSUMPTION_RE.findall(line)]
    return inline, rows


def check_assumptions(text):
    """集合双向相等 + 双侧无重号 + 处置合法且无未处置（DEC-3；共用核心）。"""
    inline, rows = scan_assumptions(text)
    v = []
    if len(inline) != len(set(inline)) or len([n for n, _ in rows]) != len({n for n, _ in rows}):
        v.append(("assumption-set-mismatch", f"重号：内联{sorted(inline)} 表{sorted(n for n, _ in rows)}"))
    elif set(inline) != {n for n, _ in rows}:
        v.append(("assumption-set-mismatch", f"集合不等：内联{sorted(set(inline))} 表{sorted({n for n, _ in rows})}"))
    for n, d in rows:
        if d not in DISPOSITIONS or d == "未处置":
            v.append(("assumption-unresolved", f"假设-{n} 处置={d}"))
    return v


def scan_subsystems(text):
    return [SUBSYS_RE.match(l).group(1) for _, l in body_lines(text) if SUBSYS_RE.match(l)]


def scan_pierce_refs(text):
    slice_bodies = [b for h, b in _section_spans(text) if h == SLICE_ANCHOR]
    return [PIERCE_RE.match(l).group(1) for b in slice_bodies for _, l in b if PIERCE_RE.match(l)]


def scan_contract_tags(text):
    out = []
    for ln, line in body_lines(text):
        out += [(ln, t) for t in CONTRACT_RE.findall(line)]
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-architecture/tests/test_sad_schema.py -v`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task1-sad-schema" "sad_schema 常量+fence-aware解析核心+坏形态fail-closed+对账共用核心"
```

---

### Task 2: references/sad-template.md + 模版↔schema 一致性测试

**R-ID:** REQ-2/5/6/12 · **tasks.md:** §3.1

**Files:**
- Create: `sdflow-architecture/references/sad-template.md`
- Modify: `sdflow-architecture/tests/test_sad_schema.py`（追加一致性用例）

**Interfaces:**
- Produces: 模版文件（Task 3 scaffold init 逐字节拷入消费仓；节标题与 sad_schema.SECTION_ANCHORS 逐字一致）

- [ ] **Step 1: 写失败测试（模版存在 + 锚一致 + 自指安全）**

```python
TEMPLATE = pathlib.Path(__file__).parent.parent / "references" / "sad-template.md"

def test_template_contains_all_anchors_verbatim():
    text = TEMPLATE.read_text(encoding="utf-8")
    lines = [l for _, l in S.body_lines(text)]
    for anchor in S.SECTION_ANCHORS + (S.APPENDIX_ANCHOR,):
        assert anchor in lines, anchor

def test_template_marker_examples_fenced():
    """模版内 [假设-N]/穿越点 示例必须都在 fence 内——正文实扫零命中（自指安全）。"""
    text = TEMPLATE.read_text(encoding="utf-8")
    inline, rows = S.scan_assumptions(text)
    assert inline == [] and rows == []
    assert S.scan_pierce_refs(text) == []

def test_template_frontmatter_parses_as_fresh_draft():
    fm = S.parse_frontmatter(TEMPLATE.read_text(encoding="utf-8"))
    assert fm["sad_status"] == "draft" and fm["sad_schema"] == S.SAD_SCHEMA_VERSION
    assert all(fm["facts"][k] == "missing" for k in S.FACT_KEYS)
```

- [ ] **Step 2: 跑测试确认失败**（模版不存在）

- [ ] **Step 3: 写模版**。结构要求（内容转写自 `docs/sad/02-sad-skill-design.md` §2 L63–93 十节推导，只读）：

1. frontmatter 逐字：`---` / `sad_schema: 1` / `sad_status: draft` / `facts:` + 三子键全 `missing` / `assumptions_open: 0` / `---`
2. `# 系统架构设计（SAD）` 标题 + 一段「本文档由 /sdflow-architecture 维护；状态迁移只经 sad_scaffold.py」
3. 十节标题逐字 = SECTION_ANCHORS；每节含 HTML 注释槽位说明（深度分层：低风险节一句话或 `N/A — 理由` 合法 + 留痕），关键节额外要求：
   - §1：质量属性**全序**有序列表示例（fence 内）+ 数值溯源标记说明 `〔人拍〕`/`〔推荐待校准〕`
   - §5：`### 5.<i> 名称` 子块骨架 + contract 行格式示例（fence 内展示 `- contract[draft] X接口：语法/语义/质量/所有权/演进`）+ 注意事项槽 + contract 五层与成熟度一句话说明
   - §6：走查矩阵槽（场景×子系统×contract 表头，DEC-11 内嵌不外发）
   - §10：`见 openspec/CONTEXT.md`（SAD 只引用不复述）
4. `## 附录：假设清单`：表头 `| 编号 | 位置 | 内容 | 依据 | 处置 |` + 行格式示例（fence 内）+ 「[假设-N] 内联标记 ↔ 本表双向锚」说明
5. **全部标记示例（`[假设-N]`、穿越点行、contract 行、N/A 行）一律放 ``` fence 内**——Step 1 的自指安全测试逐条验证

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-architecture/tests/test_sad_schema.py -v` → 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task2-sad-template" "sad-template 十节骨架+frontmatter+fence内标记示例+锚一致性测试"
```

---

### Task 3: sad_scaffold.py 核心（init/preflight 两级/原子写/单例分流/log 追加）

**R-ID:** REQ-9/12 · **tasks.md:** §1.2, §1.4（单例）, §1.5（部分）

**Files:**
- Create: `sdflow-architecture/scripts/sad_scaffold.py`
- Create: `sdflow-architecture/tests/test_sad_scaffold.py`

**Interfaces:**
- CLI：`sad_scaffold.py <sub> --root <消费仓根> …`；exit 码约定 `0=ok / 2=坏输入 / 3=preflight无布局 / 4=单例冲突 / 5=迁移拒绝`
- Produces（Task 4/5 复用）：`atomic_write(path, text)`、`append_log(root, line)`（行格式 `- {UTC时间} | {line}`）、`load_sad(root) -> (path, text)`、`_die(code, msg)`（stderr `[sad_scaffold] FAIL: …`）
- 模版定位：`Path(__file__).resolve().parent.parent / "references" / "sad-template.md"`（symlink 安装下成立）

- [ ] **Step 1: 写失败测试**

```python
import subprocess, sys, pathlib
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_scaffold.py"

def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args,
                          capture_output=True, text=True, cwd=cwd)

def make_repo(tmp_path, with_openspec=True):
    if with_openspec:
        (tmp_path / "openspec" / "changes").mkdir(parents=True)
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
    return tmp_path

def test_preflight_no_openspec_fail_closed(tmp_path):
    r = run(["init", "--root", str(make_repo(tmp_path, with_openspec=False))], tmp_path)
    assert r.returncode == 3 and "sdflow-init" in r.stderr   # 指引含完整入口，不自造布局
    assert not (tmp_path / "openspec").exists()

def test_preflight_level2_first_create(tmp_path):
    repo = make_repo(tmp_path)
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 0 and "首次创建" in (r.stdout + r.stderr)
    assert (repo / "openspec" / "adr").is_dir()
    assert "## Language" in (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    sad = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "sad_status: draft" in sad
    log = (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")
    assert "init" in log

def test_singleton_no_silent_overwrite(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    marked = repo / "openspec" / "architecture" / "sad.md"
    marked.write_text(marked.read_text(encoding="utf-8") + "\n定制内容\n", encoding="utf-8")
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 4 and "continue" in r.stderr and "replan" in r.stderr
    assert "定制内容" in marked.read_text(encoding="utf-8")      # 未被覆盖
    r2 = run(["init", "--root", str(repo), "--on-exists", "continue"], tmp_path)
    assert r2.returncode == 0 and "定制内容" in marked.read_text(encoding="utf-8")
    r3 = run(["init", "--root", str(repo), "--on-exists", "replan", "--reason", "方向推翻"], tmp_path)
    assert r3.returncode == 0 and "定制内容" not in marked.read_text(encoding="utf-8")
    assert "replan" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_log_append_only_bytes(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    logp = repo / "openspec" / "architecture" / "sad-log.md"
    before = logp.read_bytes()
    r = run(["log", "--root", str(repo), "--line", "step=2 reached"], tmp_path)
    assert r.returncode == 0
    after = logp.read_bytes()
    assert after[:len(before)] == before and b"step=2 reached" in after

def test_atomic_no_temp_residue(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    assert not list((repo / "openspec" / "architecture").glob("*.tmp*"))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-architecture/tests/test_sad_scaffold.py -v` → FAIL（脚本不存在）

- [ ] **Step 3: 实现核心**。要点（argparse subparsers；`sys.path.insert(0, str(Path(__file__).parent)); import sad_schema`）：

```python
def atomic_write(path, text):
    tmp = path.with_name(path.name + ".tmp-scaffold")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)                      # DEC-8：temp+rename，中断只留 temp

def append_log(root, line):
    logp = root / "openspec" / "architecture" / "sad-log.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(logp, "a", encoding="utf-8") as f:   # append-only：不读不改既有行
        f.write(f"- {ts} | {line}\n")

def preflight(root, out):
    if not (root / "openspec").is_dir():
        _die(3, "消费仓无 openspec/ 布局——先运行 /sdflow-init 铺设 OpenSpec 工作流"
                "（安装：bash ~/.skills/sdflow-skills/setup.sh，然后在消费仓会话执行 /sdflow-init；"
                "装完回来重跑本命令）。MUST NOT 自造半套布局。")
    for rel, kind in (("openspec/adr", "dir"), ("openspec/CONTEXT.md", "file")):
        p = root / rel
        if not p.exists():
            out.append(f"首次创建 {rel}")
            p.mkdir(parents=True) if kind == "dir" else atomic_write(p, "# Context\n\n## Language\n")
    (root / "openspec" / "architecture").mkdir(exist_ok=True)
```

`init`：preflight → sad.md 存在且无 `--on-exists` → `_die(4, "…SAD 已存在：--on-exists continue（增量续写）或 replan（重规划，旧内容归 git 历史）…")`；`continue` → 不动文件只打印续跑提示；`replan` → 要求 `--reason` 非空，模版覆写 + log `replan: {reason}`；全新 → 模版拷入 + sad-log.md 建头 `# sad-log（append-only 判定留痕）\n` + log `init`。
`log` 子命令：`--line` 直通 `append_log`（SKILL 用于 单方案声明/升档判定/降级提示/step=N/候选快照/走查执行者 留痕）。

- [ ] **Step 4: 跑测试确认通过** → `pytest sdflow-architecture/tests/test_sad_scaffold.py -v` 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task3-scaffold-core" "scaffold init+preflight两级+原子写+单例continue/replan分流+sad-log append-only"
```

---

### Task 4: scaffold 状态机（迁移表/锁 draft 复检/facts/假设处置/建议节写入与移除）

**R-ID:** REQ-1/5/6/8/12 · **tasks.md:** §1.3, §1.4（对账回写）

**Files:**
- Modify: `sdflow-architecture/scripts/sad_scaffold.py`
- Modify: `sdflow-architecture/tests/test_sad_scaffold.py`

**Interfaces:**
- `set-fact --fact <key>=<answered|missing>`（key∈FACT_KEYS；SKILL 时序纪律：实际提问后才允许记录）
- `set-assumption --assumption <N>=<接受|待校准>`（改附录表行处置格；行不存在 → exit 2）
- `transition --to <目标态> [--reason <r>] [--slice-file <f>] [--dod-confirmed]`
- 迁移表（design 逐字）：`draft→skeleton-ready`（前置：facts 三键全 answered + `sad_schema.check_assumptions` 空 + `--slice-file` 给出且穿越点集==§5 子系统集）；`skeleton-ready→draft`（`--reason` 必填；移除建议节）；`skeleton-ready→validated`（`--dod-confirmed` 必填；移除建议节）；`validated→draft`（`--reason` 必填）。**表外一律 exit 5 + stderr**。
- 每次写命令后重算 `assumptions_open` 缓存（= 表中处置为「未处置」的行数）并回写 frontmatter；迁移/回落/处置各追加 log 行。

- [ ] **Step 1: 写失败测试**（复用 conftest.make_sad 直写 sad.md 构造前态）：

```python
def seed(repo, **kw):
    from conftest import make_sad
    p = repo / "openspec" / "architecture" / "sad.md"
    p.write_text(make_sad(**kw), encoding="utf-8")
    return p

ANSWERED = {"positioning": "answered", "external_systems": "answered", "hard_constraints": "answered"}

def test_missing_fact_locks_draft(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts={**ANSWERED, "external_systems": "missing"})
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "external_systems" in r.stderr   # 指明缺失问项

def test_unresolved_assumption_locks_draft(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受"), (2, "未处置")])
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "假设-2" in r.stderr

def test_happy_path_to_skeleton_ready_inserts_slice(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0)
    slice_f = tmp_path / "s.md"
    slice_f.write_text("- 穿越点[采集端]：§5.1 contract 条目\n- 骨架 DoD：…\n- 建议 change 名：skeleton-x\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "sad_status: skeleton-ready" in text and "## 骨架切片建议" in text
    assert "skeleton-ready" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_pierce_set_mismatch_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, subsystems=("采集端", "上报端"))
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "上报端" in r.stderr

def test_out_of_table_transition_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)                       # draft
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 5 and "迁移表" in r.stderr # draft→validated 表外

def test_validated_removes_slice_and_fallback_logs_reason(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True)
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "## 骨架切片建议" not in text and "sad_status: validated" in text
    r2 = run(["transition", "--root", str(repo), "--to", "draft", "--reason", "contract 大面积否决"], tmp_path)
    assert r2.returncode == 0
    assert "contract 大面积否决" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_set_fact_and_set_assumption_update_cache(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, assumptions=[(1, "未处置")], cache=1)
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r.returncode == 0
    r = run(["set-assumption", "--root", str(repo), "--assumption", "1=接受"], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "positioning: answered" in text and "assumptions_open: 0" in text and "| 接受 |" in text
    r = run(["set-assumption", "--root", str(repo), "--assumption", "9=接受"], tmp_path)
    assert r.returncode == 2                          # 行不存在 fail-closed
```

- [ ] **Step 2: 跑测试确认失败**

- [ ] **Step 3: 实现**。核心（迁移表数据驱动，前置复检**只调 sad_schema 共用核心**，不看缓存）：

```python
def _precheck_skeleton(fm, text, args, subsys):
    missing = [k for k in sad_schema.FACT_KEYS if fm["facts"].get(k, "missing") != "answered"]
    if missing:
        _die(5, f"事实三问未齐（缺 {','.join(missing)}）——锁 draft（fail-closed）。"
                f"人实际作答后跑 set-fact 记录。")
    v = sad_schema.check_assumptions(text)            # 正文实扫，缓存 MUST NOT 参与门禁
    if v:
        _die(5, "假设对账未过：" + "; ".join(f"{c}({d})" for c, d in v))
    if not args.slice_file:
        _die(5, "缺 --slice-file（骨架切片建议内容，模型撰写、scaffold 机械插入）")
    pierce = [m.group(1) for l in pathlib.Path(args.slice_file).read_text(encoding="utf-8").splitlines()
              if (m := sad_schema.PIERCE_RE.match(l))]
    if set(pierce) != set(subsys) or len(pierce) != len(set(pierce)):
        _die(5, f"穿越点集≠第5节子系统集：穿越点{sorted(set(pierce))} vs 子系统{sorted(set(subsys))}")

TRANSITIONS = {
    ("draft", "skeleton-ready"):    "precheck+insert_slice",
    ("skeleton-ready", "draft"):    "reason+remove_slice",
    ("skeleton-ready", "validated"): "dod+remove_slice",
    ("validated", "draft"):         "reason",
}
```

`transition` 主体：load → parse_frontmatter →`(cur, to)` 不在表 → `_die(5, f"表外迁移 {cur}→{to}——合法迁移表见 design 状态机节")`；按动作串执行：`reason` 缺 → exit 2；`insert_slice` = 在 `APPENDIX_ANCHOR` 行前插 `## 骨架切片建议\n\n{slice内容}\n`（无附录则文末）；`remove_slice` = 删 SLICE_ANCHOR 起至下一 `## ` 行前；frontmatter `sad_status:` 行重写；原子写 + log 行（`transition draft→skeleton-ready` / `fallback …: {reason}` / `validated：骨架 DoD 已确认`）。
`set-fact`/`set-assumption`：解析 `k=v`（枚举校验，非法 exit 2）；set-assumption 定位 `APPENDIX_ROW_RE` 匹配且编号相等的行，重写末格；每次写后 `assumptions_open` 重算回写 + log 行。

- [ ] **Step 4: 跑测试确认通过**（全文件回归含 Task 3 用例）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task4-scaffold-statemachine" "状态机迁移表+锁draft正文实扫复检+facts/假设处置把手+建议节插拔+缓存重算"
```

---

### Task 5: scaffold 分家机械化（adr-new + context-add）

**R-ID:** REQ-9 · **tasks.md:** §1.6

**Files:**
- Modify: `sdflow-architecture/scripts/sad_scaffold.py`、`sdflow-architecture/tests/test_sad_scaffold.py`

**Interfaces:**
- `adr-new --root R --title <标题> --slug <ascii-kebab> [--number N]` → 建 `openspec/adr/NNNN-<slug>.md`，stdout 打印路径
- `context-add --root R --term <术语> --definition <一段定义>` → 追加 `## Language` 末尾；同名冲突 exit 2 显式报告不覆盖

- [ ] **Step 1: 写失败测试**

```python
def test_adr_new_max_plus_one(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "adr" / "0007-x.md").write_text("x", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "分解判据", "--slug", "decomposition"], tmp_path)
    assert r.returncode == 0
    assert (repo / "openspec" / "adr" / "0008-decomposition.md").exists()

def test_adr_new_unrecognized_pattern_fail_closed(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "adr" / "notes.md").write_text("x", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 2 and "notes.md" in r.stderr          # 留人工，--number 可越
    r2 = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t", "--number", "12"], tmp_path)
    assert r2.returncode == 0 and (repo / "openspec" / "adr" / "0012-t.md").exists()

def test_context_add_append_and_conflict(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    r = run(["context-add", "--root", str(repo), "--term", "SAD", "--definition", "系统架构设计文档"], tmp_path)
    assert r.returncode == 0
    ctx = (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    assert "**SAD**" in ctx
    r2 = run(["context-add", "--root", str(repo), "--term", "SAD", "--definition", "另一定义"], tmp_path)
    assert r2.returncode == 2 and "已存在" in r2.stderr
    assert "另一定义" not in (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: 跑确认失败** → **Step 3: 实现**：

`adr-new`：扫 `openspec/adr/*.md`（忽略 `README.md`），全部须 `^(\d{4})-` 前缀，任一不匹配且未给 `--number` → `_die(2, f"无法识别编号模式（{bad}）——人工指定 --number")`；`--slug` 须 `fullmatch [a-z0-9][a-z0-9-]*`；内容骨架 = `# ADR NNNN: {title}\n\n- Status: Proposed\n- Date: {UTC日期}\n\n## Context\n\n## Decision\n\n## Consequences\n`（原子写 + log 行 `adr-new NNNN-{slug}`）。
`context-add`：读 CONTEXT.md；行锚定检查 `**{term}**` 开头行已存在 → exit 2 报告现有定义位置；无 `## Language` 段 → 追加该段；条目格式 `\n**{term}**:\n{definition}\n`，插到 `## Language` 段末（下一 `## ` 前）；原子写 + log 行。

- [ ] **Step 4: 全文件回归通过** → **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task5-scaffold-split" "分家机械化 adr-new编号max+1 fail-closed+context-add同名不覆盖冲突显式"
```

---

### Task 6: sad_lint.py（v1 全断言 + 输出诚实）

**R-ID:** REQ-2/5/6/8/10 · **tasks.md:** §2.1–2.5

**Files:**
- Create: `sdflow-architecture/scripts/sad_lint.py`
- Create: `sdflow-architecture/tests/test_sad_lint.py`

**Interfaces:**
- CLI：`sad_lint.py --root <消费仓根>`（定位 `openspec/architecture/sad.md`）或 `--sad <直接路径>`
- exit：`0` 全过（stdout 首行 `structure-ok-SEMANTICS-UNCHECKED`，另输出 `假设计数: N`）/ `1` 违规（每条 `[sad_lint] {code}: {detail}` + `  next-step: {提示}`，**独立收集全量输出**，不首错即停）/ `2` 坏输入（stderr `[sad_lint] FAIL: {原因}`，stdout 无判定）

- [ ] **Step 1: 写失败测试**（每类断言正负≥2——SM-2 锚；关键用例）：

```python
import subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_lint.py"

def lint(tmp_path, text):
    p = tmp_path / "sad.md"; p.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--sad", str(p)],
                          capture_output=True, text=True)

def test_pass_honest_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=0))
    assert r.returncode == 0 and r.stdout.splitlines()[0] == S.PASS_CODE
    assert "假设计数: 1" in r.stdout

def test_missing_section_reason_code(tmp_path):
    text = make_sad().replace("## 8. 横切概念\n\nN/A — v1 无横切面\n\n", "")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "missing-section" in r.stdout and "8" in r.stdout
    assert "next-step:" in r.stdout

def test_na_without_reason(tmp_path):
    r = lint(tmp_path, make_sad().replace("N/A — v1 无横切面", "N/A"))
    assert r.returncode == 1 and "na-without-reason" in r.stdout

def test_duplicate_number_set_reconciliation(tmp_path):
    # 正文两个[假设-1] + 表 假设-1/假设-2 → 计数2==2 但集合对账拦截（REQ-5 场景逐字）
    text = make_sad(assumptions=[(1, "接受"), (2, "接受")], cache=0)
    text = text.replace("[假设-1] [假设-2]", "[假设-1] [假设-1]")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "assumption-set-mismatch" in r.stdout

def test_cache_mismatch_independent_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=5))
    assert r.returncode == 1 and "assumption-cache-mismatch" in r.stdout

def test_quality_attr_order(tmp_path):
    r = lint(tmp_path, make_sad().replace("1. 可靠性\n2. 可维护性", "- 可靠性\n- 可维护性"))
    assert r.returncode == 1 and "quality-attr-order-broken" in r.stdout
    r2 = lint(tmp_path, make_sad().replace("2. 可维护性", "3. 可维护性"))  # 跳号
    assert r2.returncode == 1 and "quality-attr-order-broken" in r2.stdout

def test_schema_version_mismatch_not_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad(schema=0))
    assert r.returncode == 1 and "schema-version-mismatch" in r.stdout   # 独立码+指引
    assert "FAIL" not in r.stderr                                        # 不与损坏共用出口

def test_contract_invariant(tmp_path):
    bad = make_sad(status="validated").replace("contract[draft]", "contract[draft]")  # validated 下 draft contract
    r = lint(tmp_path, bad)
    assert r.returncode == 1 and "contract-invariant-violation" in r.stdout
    ok = make_sad(status="validated").replace("contract[draft]", "contract[validated]")
    assert lint(tmp_path, ok).returncode == 0

def test_slice_branch_assertions(tmp_path):
    r = lint(tmp_path, make_sad(status="skeleton-ready", slice_section=False,
                                facts={"positioning": "answered", "external_systems": "answered",
                                       "hard_constraints": "answered"})
             .replace("contract[draft]", "contract[draft]"))
    assert r.returncode == 1 and "slice-section-missing" in r.stdout
    r2 = lint(tmp_path, make_sad(status="validated", slice_section=True)
              .replace("contract[draft]", "contract[validated]"))
    assert r2.returncode == 1 and "slice-section-stale" in r2.stdout

def test_bad_input_fail_closed(tmp_path):
    r = lint(tmp_path, "no frontmatter at all\n")
    assert r.returncode == 2 and r.stderr.startswith("[sad_lint] FAIL:") and S.PASS_CODE not in r.stdout
    r2 = subprocess.run([sys.executable, str(SCRIPT), "--sad", str(tmp_path / "nope.md")],
                        capture_output=True, text=True)
    assert r2.returncode == 2 and "[sad_lint] FAIL:" in r2.stderr

def test_enum_invalid_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad().replace("sad_status: draft", "sad_status: approved"))
    assert r.returncode == 2 and "approved" in r.stderr      # REQ-6 场景：stderr 区别于 reason_code

def test_crlf_bom_tolerated(tmp_path):
    text = "﻿" + make_sad(assumptions=[(1, "接受")], cache=0).replace("\n", "\r\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0

def test_fence_inside_markers_not_counted(tmp_path):
    text = make_sad(extra="```\n[假设-7]\n## 11. 假节\n```\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0        # fence 内标记/节锚不计
```

- [ ] **Step 2: 跑确认失败** → **Step 3: 实现**：

主体（读文件 → BOM/CRLF 归一 `text.lstrip("﻿").replace("\r\n","\n")` → try parse_frontmatter，SadParseError → stderr `[sad_lint] FAIL: {e}` exit 2 → 逐检查独立收集 `violations: list[(code, detail)]`）：

1. `fm["sad_schema"] != SAD_SCHEMA_VERSION` → schema-version-mismatch（detail 含两版本号；**不 return，继续其余检查**）
2. `scan_sections`：每锚 absent → missing-section；present 但 body 全空行 → missing-section；body 非空但全部行既非内容判定——取 body 首个非空行，若 `N/A` 开头且不匹配 NA_RE → na-without-reason
3. `check_assumptions(text)` 直接并入；`len(scan_assumptions(text)[0])`（内联去重后计数）≠ `fm["assumptions_open"]` → assumption-cache-mismatch（以「表中未处置行数」为缓存语义：重算 = `sum(1 for _, d in rows if d == "未处置")`，与 scaffold 重算口径一致——detail 里写明实扫值/缓存值）
4. §1 body 的 ORDERED_RE 序列：若该节非 N/A——收集编号序列，须非空且 == `[1..N]` 严格连续，否则 quality-attr-order-broken
5. `scan_contract_tags`：tag 不在 CONTRACT_ENUM → contract-invariant-violation（detail 未知标签）；status ∈ {draft, skeleton-ready} 且 tag ∈ {validated, frozen} → 违规；status == validated 且 tag == draft → 违规（planned 豁免）
6. slice 分支：status==skeleton-ready → SLICE_ANCHOR 不在节谱 → slice-section-missing；在则 `set(scan_pierce_refs) != set(scan_subsystems)` → slice-pierce-set-mismatch；status==validated 且 SLICE_ANCHOR 存在 → slice-section-stale
7. 输出：violations 空 → print PASS_CODE + `假设计数: {n}` exit 0；否则逐条 `[sad_lint] {code}: {detail}` + `  next-step: {REASON_NEXT_STEP[code]}`，最后 `假设计数: {n}`，exit 1

- [ ] **Step 4: 跑全部三个测试文件回归** → 全 PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task6-sad-lint" "lint v1全断言:十节/集合对账/缓存mismatch/全序/版本独立码/组合不变式/建议节分支+输出诚实"
```

---

### Task 7: references 其余五件（蓝本定稿转写）

**R-ID:** REQ-1/3/4/7/10 · **tasks.md:** §3.2–3.6

**Files:**
- Create: `sdflow-architecture/references/decomposition-rules.md`、`quality-criteria.md`、`review-lenses.md`、`intake-questionnaire.md`、`checklists/{cross-cutting-template,quality-attribute-candidates,external-deps-typical,change-categories}.md`

转写源 = `docs/sad/02-sad-skill-design.md`（**只读**，冻结考古层；转写后 references/ 为真相源）。逐件要求：

- [ ] **Step 1: `decomposition-rules.md`** ← 蓝本 §5.1（L213–259）+ §5.2（L261–268）逐条转写 R1–R11 + AP1–AP4。补三处定稿增量：①两轴正交提醒（R 轴=怎么切空间 / AP 轴=什么形态不许出现）②AP 自检留痕含**修正前/后切法对比结构化字段**（`before:` / `after:` / `触发 AP 编号:` 三行格式）③R9 带宽（3–7）之外需记 ADR 理由一句。文头声明「真相源=本文件；蓝本 docs/sad/02 已冻结」。
- [ ] **Step 2: `quality-criteria.md`** ← 蓝本 §3.1（L98–113）S1–S11 全文 + §3.2（L114–132）机械化拆解表。**真相源标记**：文头注明「S 编号被 review-lenses.md 与 sad_lint.py 注释引用——增删改 S 条目须按 design scope-check 表同步核对」。
- [ ] **Step 3: `review-lenses.md`** ← 蓝本 §3.3 组件清单 + §5.4（L275–289）走查与升档分档。内容 = 语义残余镜单（每条带 S 编号引用）+ 升档信号表（骨架验证慢贵/不可逆决策面大/不可控外部 contract 多/操作者显式要求）+ BASE-29 scope-check 人工核对清单 v1（自 design「协议文档套件 scope-check 表」转写四行）。
- [ ] **Step 4: `intake-questionnaire.md`** ← 蓝本 §5.3（L269–274）。三问全文（一句话定位 / 外部系统清单**含文档指针追问**〔X3 微采纳：引导证据指针〕/ 硬约束五分项：栈-平台-部署形态-存量-合规）+ 各问追问提示 + 「价值类问题 MUST NOT 进首轮」声明 + 允许「不知道」（缺答锁 draft 非阻塞采集）。
- [ ] **Step 5: `checklists/` 四件**（P2 允许薄，各 ≤40 行）：`cross-cutting-template.md`（横切概念常见面：错误语义/日志/配置/时间/持久化/安全）、`quality-attribute-candidates.md`（可靠性/性能/可维护性/可移植性/安全/成本 各一行判别问句）、`external-deps-typical.md`(云服务/DB/消息/固件外设/第三方 API 典型集)、`change-categories.md`（R4 预期变化类别：需求面/规模面/技术栈面/组织面）。
- [ ] **Step 6: 核对**：grep 确认 review-lenses 每条镜位都有 `S\d+` 引用；decomposition-rules 含 R1–R11、AP1–AP4 全部编号无缺号。

Run: `grep -c "^### R" sdflow-architecture/references/decomposition-rules.md` → 11；`grep -c "^### AP" …` → 4；`grep -o "S[0-9]*" sdflow-architecture/references/review-lenses.md | sort -u` 覆盖语义残余条目。

- [ ] **Step 7: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task7-references" "references五件定稿转写:R1-R11+AP1-4/S1-S11真相源/镜单+升档信号/三问问卷/清单库四件"
```

---

### Task 8: SKILL.md 五步流程编排

**R-ID:** REQ-1/3/4/5/7/8/10/11 · **tasks.md:** §4.1–4.5, §4.7

**Files:**
- Create: `sdflow-architecture/SKILL.md`

结构与硬性内容（逐项落，缺一即本任务不过）：

- [ ] **Step 1: frontmatter**：`name: sdflow-architecture`；description 聚焦架构词面（架构设计/子系统划分/contract/SAD）+ 触发与不触发场景 + 指路句「时间轴规划（roadmap/阶段排期）→ /sdflow-roadmap」+ 前置条件「消费仓需已 sdflow-init」（REQ-11 本侧）。
- [ ] **Step 2: 五步主体**，每步含调用的脚本命令全文：
  - **①事实三问采集**：读 `references/intake-questionnaire.md` 提问；**加粗时序声明：实际提问并获人回答后才允许 `sad_scaffold.py set-fact` 记录，MUST NOT 预填**；先跑 `python3 {skill}/scripts/sad_scaffold.py init --root <仓根>`（preflight 两级文案由脚本输出；二次触发 exit 4 → 向操作者显式区分 continue/replan 后带 `--on-exists` 重跑；**continue 时先读 sad-log 定位断点**——`step=N reached` 行 + 候选快照行）
  - **②规则集跑候选**：按 `references/decomposition-rules.md` R1–R11；**AP1–AP4 自检先于交人**（留痕 before/after/触发编号）；候选数分歧驱动——无分歧 MUST 显式一行「判据无分歧，单方案直出」并 `sad_scaffold.py log` 留痕；上限 3 超出按分歧维度归并；MUST NOT 造稻草人凑数（信任边界：真实性归人门+冷走查）
  - **③挂产物拍板**：**一轮打包呈现**（分组单条消息）；数值项不否决即采纳推荐并标 `〔推荐待校准〕`；人拍数值标 `〔人拍〕`；AI 推测一律 `[假设-N]` + 附录清单行；拍板后写 SAD 正文 + `log` 候选快照行
  - **④冷走查 + 人门**：走查 MUST fresh 子代理（读 `references/review-lenses.md`；**禁生成 session 自查**）；产出场景×子系统×contract 矩阵**内嵌 SAD 第 6 节**；留痕行带**执行者字段**（子代理标识 / self-review-degraded）；**Codex 宿主降级分支**：无 fresh 子代理原语 → 主 session 走查 + `log` 记 `walkthrough=self-review-degraded` + 建议换宿主复跑，MUST NOT 佯装冷走查；**升档判定**按镜单信号表显式一行留痕；升档 → 自编排镜阵 fan-out（MUST NOT 整体调 sdflow-spec-review），outside voice 镜经 `~/.sdflow/hack/outside-voice.sh`（preflight 仅 `ready` 走 codex；不可执行/不存在/非 ready/超时 124/exec-error 1 → 显式降级 Claude 镜不静默；secret-hit 3 → 拒发报人工；升档前提示操作者确认消费仓无敏感明文——read-only 防写不防读不防出境）；**人门固定议程（位置=走查洞处置后、迁移前）**：三问回答复核 / 假设逐条处置（处置经 `set-assumption` 落）/ 走查洞处置确认
  - **⑤交棒**：模型撰写切片建议内容（穿越点**引用** §5 条目不复述 + 骨架 DoD 文案「每条 L1 contract 被一次真实调用穿过 + 部署链路走通」+ 建议 change 名 + 「建议非契约/不代开 change」声明）→ `transition --to skeleton-ready --slice-file <f>` → `sad_lint.py --root <仓根>` → **对话收尾行**：`SAD 已 skeleton-ready · 建议骨架 change：<名> · 下游：/opsx:ff <名> · 软提示：git add openspec/architecture/ 纳入版本控制`
- [ ] **Step 3: 信任边界声明行 ×2**（原文级）：「lint 通过 = 结构性通过 ≠ 内容已审」「facts=answered = 已记录回答 ≠ 质量已核（复核在人门议程）」
- [ ] **Step 4: 二次触发编排**：continue/replan 分流确认文案；**骨架落地后 continue 回写入口**：`transition --to validated --dod-confirmed`（既定后续动作，不经 continue/replan 分流——REQ-9 显式排除）+ 建议节由 scaffold 移除
- [ ] **Step 5: 分家指令**：ADR 经 `sad_scaffold.py adr-new`（编号无法识别时 fail-closed 留人工 `--number`）；术语经 `context-add`（冲突显式报告留人裁决）；SAD 只引用不复述
- [ ] **Step 6: 模型档位一行**：主 session 与冷走查子代理均强档、无弱档步（机械已脚本化），引 model-tiers.md（DEC-12①）
- [ ] **Step 7: 自查**：对照 specs/architecture-design/spec.md REQ-1/3/4/5/7/8/10/11 逐条 grep SKILL.md 确认每条 SHALL/MUST 有对应指令行；缺则补。

- [ ] **Step 8: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task8-skill-md" "SKILL.md五步编排:三问时序纪律/AP自检/打包拍板/冷走查+宿主降级+人门议程/交棒收尾行+信任边界x2"
```

---

### Task 9: sdflow-roadmap 指路句（roadmap-planning delta）

**R-ID:** roadmap-planning ADDED REQ · **tasks.md:** §4.6

**Files:**
- Modify: `sdflow-roadmap/SKILL.md`（仅 frontmatter description）

- [ ] **Step 1: Read `sdflow-roadmap/SKILL.md`**，定位 frontmatter `description:` 现文本。
- [ ] **Step 2: 在 description 末尾追加**（一句，不动既有触发词面）：`新项目起步尚无架构设计（SAD）时，先 /sdflow-architecture（消费仓需已 sdflow-init）。`
- [ ] **Step 3: 验证**：`grep -c "sdflow-architecture" sdflow-roadmap/SKILL.md` ≥1 且 `grep "需已 sdflow-init" sdflow-roadmap/SKILL.md` 命中（delta Scenario 逐字判据：含「先 `/sdflow-architecture`」+ 前置条件）。
- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task9-roadmap-pointer" "sdflow-roadmap description加SAD指路句+sdflow-init前置条件(roadmap-planning delta)"
```

---

### Task 10: 收尾（README/setup/端到端演练/SM 核对/todolist 登记）

**R-ID:** REQ 全量核对 · **tasks.md:** §5.1–5.4

**Files:**
- Modify: `README.md`（Skills 列表）
- Create: `openspec/changes/add-sdflow-architecture/impl-verify-notes.md`（SM 留痕；**非四件套**，允许新增）

- [ ] **Step 1: README Skills 列表**新增行（Read 现表对齐既有格式）：`sdflow-architecture`——系统架构设计编排器：简单需求 → skeleton-ready SAD（openspec/architecture/ 单例）+ 骨架切片建议交棒。
- [ ] **Step 2: 开发 checkout 跑 `bash setup.sh`**，验证 symlink：`ls -l ~/.claude/skills/sdflow-architecture ~/.codex/skills/sdflow-architecture`（adr/0005：不跑 setup 测不到）。
- [ ] **Step 3: 全套 pytest**：`pytest sdflow-architecture/tests/ -v` 全绿；再跑仓级 `pytest` 确认无回归。
- [ ] **Step 4: 端到端演练**（SM-1 锚），脚本逐条跑并存 transcript：

```bash
E2E=$(mktemp -d); mkdir -p "$E2E/openspec/changes" "$E2E/openspec/specs"
S=sdflow-architecture/scripts
python3 $S/sad_scaffold.py init --root "$E2E"
python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact positioning=answered
python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact external_systems=answered
python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact hard_constraints=answered
# 手工填 §1 全序/§5 一个子系统+contract[draft]/一处[假设-1]+附录行(未处置)——模拟五步①-③产物
python3 $S/sad_scaffold.py set-assumption --root "$E2E" --assumption 1=接受
printf -- '- 穿越点[<§5子系统名>]：§5.1 contract 条目\n- 骨架 DoD：每条 L1 contract 被一次真实调用穿过 + 部署链路走通\n- 建议 change 名：skeleton-demo\n' > "$E2E/slice.md"
python3 $S/sad_scaffold.py transition --root "$E2E" --to skeleton-ready --slice-file "$E2E/slice.md"
python3 $S/sad_lint.py --root "$E2E"; echo "LINT_EXIT=$?"        # 须 =0 且首行 structure-ok-SEMANTICS-UNCHECKED
python3 $S/sad_scaffold.py init --root "$E2E"; echo "SECOND_EXIT=$?"  # 须 =4：continue/replan 提示文案观察
```

- [ ] **Step 5: 写 `impl-verify-notes.md`**：Read proposal.md「Success Metrics」节，SM-1/2/3 逐条贴证据（SM-1：演练产物路径 + LINT_EXIT=0 输出原文；SM-2：`pytest --collect-only -q | tail -1` 用例数 + 每类断言正负≥2 对照表；SM-3：按 proposal 原文核对；SM-4：`试点未启动——设计门 Q1=c 暂缓提名，占位豁免`）+ 演练 transcript + 二次触发提示文案观察记录。
- [ ] **Step 6: todolist 登记两条 defer 工件**（tasks.md §5.4；显式传 change 防误挂）：

```bash
echo '{"module":"sdflow-architecture","summary":"frozen-diff lint：frozen contract 有 diff 无新 ADR 关联报错（需 git 对比，超 v1 纯文件断言）","type":"功能增强","change":"add-sdflow-architecture","motivation":"design 状态机节目标态遗留"}' | python3 sdflow-todolist/scripts/todolist.py add
echo '{"module":"sdflow-architecture","summary":"sad_schema 常量单向生成 JSON schema 工件（跨语言消费方出现时触发）","type":"基础设施","change":"add-sdflow-architecture","motivation":"DEC-1 被否备选的证伪条件登记"}' | python3 sdflow-todolist/scripts/todolist.py add
```

- [ ] **Step 7: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-architecture:task10-closeout" "README条目+setup.sh symlink验证+端到端演练lint0+SM1-4核对留痕+todolist两条defer登记"
```

---

## Self-Review 记录

- **Spec 覆盖**：REQ-1（T4 锁 draft + T8 ①④时序/人门）/ REQ-2（T2 模版 + T6 节断言）/ REQ-3（T7 规则集 + T8 ② AP 前置）/ REQ-4（T8 ②③）/ REQ-5（T1 对账核心 + T4 处置把手 + T6 断言三件）/ REQ-6（T1 schema + T4 迁移表 + T6 版本/不变式/枚举）/ REQ-7（T7 镜单 + T8 ④）/ REQ-8（T4 slice 插拔 + T6 分支断言 + T8 ⑤）/ REQ-9（T3 preflight/单例 + T5 分家 + T8 回写入口）/ REQ-10（T6 输出诚实 + T1 next-step 映射）/ REQ-11（T8 description + T9 roadmap 侧）/ REQ-12（T3 log + T4/T5 各写点 + T8 留痕指令）。roadmap-planning delta → T9。
- **类型/命名一致性**：穿越点/contract/附录行/节锚文本形态在「机械文本形态锁定」区一次定义，T1 常量、T2 模版、T4 校验、T6 断言、T8 指令、T10 演练全部引用同一形态；scaffold exit 码约定（0/2/3/4/5）在 T3 Interfaces 定义，T4/T5 测试沿用。
- **无placeholder 核查**：转写类步骤（T7/T8）均带精确源定位（文件+行号/节号）与验收 grep；代码类步骤全部含可执行代码或逐字段实现指令。
