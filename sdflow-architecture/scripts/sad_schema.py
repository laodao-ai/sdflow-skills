#!/usr/bin/env python3
"""sad_schema.py — SAD 格式常量与解析单一源（DEC-1）。

scaffold（写侧）/ lint（读侧）共享本模块；各自只做消费方语义校验，
MUST NOT 另写解析器（adr/0011）。纯 stdlib。
解析口径：行锚定 + fence-aware 覆盖全部正文扫描（DEC-2）。
节标题锚 v1 中文单语（DEC-12③）。
"""
import re
import unicodedata

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
CONTRACT_SECTION = "## 5. 子系统分解与 contract"   # == SECTION_ANCHORS[4]；contract 标签只在此节合法

ASSUMPTION_RE = re.compile(r"\[假设-(\d+)\]")
NA_RE = re.compile(r"^N/A\s*—\s*\S")
ORDERED_RE = re.compile(r"^(\d+)\.\s+\S")
SUBSYS_RE = re.compile(r"^###\s+5\.\d+\s+(.+?)\s*$")
# [impl-review-fix] A6①：捕获任意载荷（原 `[a-z]+` 漏放 contract[Validated]/contract[draft-v2]/contract[]），
# 交消费方做枚举校验；未闭合 `contract[` 由 scan_contract_malformed 单独 fail-closed。
CONTRACT_RE = re.compile(r"contract\[([^\]]*)\]")
PIERCE_RE = re.compile(r"^-\s*穿越点\[(.+?)\]：")
APPENDIX_ROW_RE = re.compile(r"^\|\s*假设-(\d+)\s*\|(?:[^|]*\|){3}\s*([^|\s]+)\s*\|\s*$")
# [impl-review-fix] A1：CommonMark fence 开启行——lstrip 后 ≥3 个同字符（` 或 ~）。
FENCE_RE = re.compile(r"^([`~])\1{2,}")

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
    "malformed-appendix-row": "附录数据行畸形——按 detail 行号排查：全角空格 U+3000 是否混入处置格？`|` 分隔列数是否为 5 列？改回半角并对齐列数",
    "duplicate-section": "同一结构锚（节标题 / 骨架切片建议 / 附录）在 fence 外只能出现一次——删除重复的影子节，保留唯一真节",
    "duplicate-subsystem": "第 5 节 `### 5.x` 子系统名、切片穿越点各自 MUST NOT 重名——重命名折叠的同名项，别让一条穿越点满足两个子系统",
    "facts-status-invariant": "先 `sad_scaffold.py transition --to draft --reason <理由>` 回落，或 `set-fact <k>=answered` 补答后重升——skeleton-ready/validated 要求 facts 三键全 answered",
}


class SadParseError(Exception):
    """坏输入（fail-closed 面）：frontmatter 损坏/枚举非法/文件形态坏。"""


def body_lines(text):
    """fence 外正文行 [(lineno, line)]（DEC-2）。CommonMark 语义子集（A1）：
    开启行 = lstrip 后 ≥3 个同字符（` 或 ~）；关闭 = 同 fence 字符、run 长度 ≥ 开启长度、
    且除 fence 字符外仅余尾随空白的行——故 ```` 内的 ``` 不提前关、~~~ 内的 ``` 不算关。
    到 EOF 仍在 fence 内（未闭合）→ fail-closed raise。
    """
    out = []
    fence_char, fence_len = None, 0
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if fence_char is None:
            m = FENCE_RE.match(stripped)
            if m:
                fence_char = m.group(1)
                fence_len = len(stripped) - len(stripped.lstrip(fence_char))
                continue
            out.append((i, line))
        elif stripped[:1] == fence_char:
            run = len(stripped) - len(stripped.lstrip(fence_char))
            if run >= fence_len and stripped.rstrip() == fence_char * run:
                fence_char, fence_len = None, 0
            # 否则：fence 内更短/带尾随内容的同字符行不闭合，也不计入正文
    if fence_char is not None:
        # [impl-review-fix] A1 未闭合 fence fail-closed：实测未闭合 fence 可把整段
        # （含未处置假设 / 影子节）藏进 fence 假象骗过锁 draft 门禁，故 EOF 仍在 fence 内即判坏输入。
        raise SadParseError(f"未闭合 fence：到 EOF 仍在 {fence_char!r} fence 内（fail-closed）")
    return out


def _to_int(key, raw):
    if not re.fullmatch(r"-?\d+", raw.strip()):
        raise SadParseError(f"bad-type: {key} 须为整数，得到 {raw!r}")
    return int(raw)


def frontmatter_end(lines):
    """frontmatter 结束定界行索引（顶格精确，无 strip）——[impl-review-fix] A3：防缩进
    `  ---` 被当结束定界（实测把 facts 块内一行 `  ---` 误判为边界，assumptions_open 读 0）。
    无闭合返回 None。scaffold 下一波用此共享 helper 替换其 `_frontmatter_end` 复刻（DEC-1）。"""
    return next((i for i in range(1, len(lines)) if lines[i] == "---"), None)


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SadParseError("frontmatter 缺失：首行须为 ---")
    end = frontmatter_end(lines)   # [impl-review-fix] A3 顶格精确
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


def _appendix_line_set(text):
    """附录节 span 覆盖的原始行号集合（fence-aware，A2/共用）。"""
    bodies = [b for h, b in _section_spans(text) if h == APPENDIX_ANCHOR]
    return {ln for b in bodies for ln, _ in b}


def scan_assumptions(text):
    inline, rows = [], []
    appendix_lns = _appendix_line_set(text)
    for ln, line in body_lines(text):
        if ln in appendix_lns:
            m = APPENDIX_ROW_RE.match(line)
            if m:
                rows.append((int(m.group(1)), m.group(2)))
                continue
        inline += [int(n) for n in ASSUMPTION_RE.findall(line)]
    return inline, rows


def _looks_like_data_row(stripped):
    """strip 后形如表数据行：以 `|` 开头且含 ≥4 个 `|`，排除表头 `| 编号 |` 与分隔行 `|---|`。"""
    if not stripped.startswith("|") or stripped.count("|") < 4:
        return False
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    if cells and all(c and set(c) <= set("-:") for c in cells):
        return False   # 分隔行（单元格仅由 - : 组成）
    if cells and cells[0] == "编号":
        return False   # 表头行
    return True


def scan_malformed_appendix_rows(text):
    """附录 span 内形如表数据行、却不匹配 APPENDIX_ROW_RE 的行（[impl-review-fix] A2 fail-closed：
    全角空格 U+3000 等畸形会让行从 rows/inline 双侧蒸发骗过 assumption-unresolved，须显式报出）。
    返回 [(lineno, line_stripped)]。"""
    appendix_lns = _appendix_line_set(text)
    out = []
    for ln, line in body_lines(text):
        if ln in appendix_lns and not APPENDIX_ROW_RE.match(line) and _looks_like_data_row(line.strip()):
            out.append((ln, line.strip()))
    return out


def check_assumptions(text):
    """集合双向相等 + 双侧无重号 + 处置合法且无未处置 + 附录无畸形行（DEC-3；共用核心）。"""
    inline, rows = scan_assumptions(text)
    v = []
    if len(inline) != len(set(inline)) or len([n for n, _ in rows]) != len({n for n, _ in rows}):
        v.append(("assumption-set-mismatch", f"重号：内联{sorted(inline)} 表{sorted(n for n, _ in rows)}"))
    elif set(inline) != {n for n, _ in rows}:
        v.append(("assumption-set-mismatch", f"集合不等：内联{sorted(set(inline))} 表{sorted({n for n, _ in rows})}"))
    for n, d in rows:
        if d not in DISPOSITIONS or d == "未处置":
            v.append(("assumption-unresolved", f"假设-{n} 处置={d}"))
    # [impl-review-fix] A2 畸形行并入共享核心 → scaffold precheck 门禁自动继承
    for ln, raw in scan_malformed_appendix_rows(text):
        v.append(("malformed-appendix-row", f"附录第 {ln} 行畸形（检查全角空格 U+3000 / 列数）：{raw!r}"))
    return v


def scan_subsystems(text):
    # [impl-review-fix] A8 NFC 归一：NFD 同形名会「看着一样却报不一致」，集比对前统一形态。
    return [unicodedata.normalize("NFC", SUBSYS_RE.match(l).group(1))
            for _, l in body_lines(text) if SUBSYS_RE.match(l)]


def scan_pierce_refs(text):
    slice_bodies = [b for h, b in _section_spans(text) if h == SLICE_ANCHOR]
    # [impl-review-fix] A8 NFC 归一（与 scan_subsystems 同口径，集比对才诚实）。
    return [unicodedata.normalize("NFC", PIERCE_RE.match(l).group(1))
            for b in slice_bodies for _, l in b if PIERCE_RE.match(l)]


def duplicate_anchors(text):
    """结构锚（十节 + 骨架切片 + 附录）在 fence 外出现 ≥2 次的清单（[impl-review-fix] A4
    fail-closed：dict last-wins 让影子节顶替真节绕过检查）。返回 [(anchor, count)]。"""
    targets = set(SECTION_ANCHORS) | {SLICE_ANCHOR, APPENDIX_ANCHOR}
    counts = {}
    for _, line in body_lines(text):
        s = line.strip()
        if s in targets:
            counts[s] = counts.get(s, 0) + 1
    return [(a, c) for a, c in counts.items() if c >= 2]


def _section5_body_lines(text):
    """第 5 节（CONTRACT_SECTION）span 内的 (lineno, line)（fence-aware）。"""
    return [(ln, line) for h, b in _section_spans(text) if h == CONTRACT_SECTION
            for ln, line in b]


def scan_contract_tags(text):
    """只扫第 5 节 span 内的 contract[...] 标签（[impl-review-fix] A6②：全文扫描会误伤
    附录/散文里的类比提及）。捕获任意载荷，payload 交消费方做枚举校验。返回 [(lineno, payload)]。"""
    out = []
    for ln, line in _section5_body_lines(text):
        out += [(ln, m.group(1)) for m in CONTRACT_RE.finditer(line)]
    return out


def scan_contract_malformed(text):
    """第 5 节 span 内出现 `contract[` 却无闭合 `]` 的行（[impl-review-fix] A6 fail-closed：
    坏标签不得逃逸枚举校验）。返回 [(lineno, line_stripped)]。"""
    out = []
    for ln, line in _section5_body_lines(text):
        if "contract[" in CONTRACT_RE.sub("", line):
            out.append((ln, line.strip()))
    return out
