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
