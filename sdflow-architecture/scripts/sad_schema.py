#!/usr/bin/env python3
"""sad_schema.py — SAD 格式常量与解析单一源（DEC-1）。

scaffold（写侧）/ lint（读侧）共享本模块；各自只做消费方语义校验，
MUST NOT 另写解析器（adr/0011）。
解析口径：行锚定 + fence-aware 覆盖全部正文扫描（DEC-2）。
节标题锚 v1 中文单语（DEC-12③）。

[shared-yaml-subset-parser] frontmatter 的 YAML **取值**核心委托给外部 yq 二进制
（mikefarah/yq，同 git 的外部二进制先例，见 `_yq()`），MUST NOT `import yaml`（零依赖
不变量）；`TOP_KEYS`/`FACT_KEYS`/`FACT_VALUES` 白名单校验仍在 Python 侧对 yq 解出的
dict 做业务判断。`frontmatter_end` 保留纯文本定界符定位（不委托 yq）——它被
`sad_scaffold.py` 用于**行级原地改写**（如 `_rewrite_top_key`），需要的是"第几行是
闭合定界符"这一位置信息，yq 是值抽取器、不回答位置问题；顺带也充当"闭合性预扫描"
（防 yq 对未闭合 frontmatter 的已知静默接受，见 `_yq()` 上方注释），两个用途共用同一
次定位、不重复实现。
"""
import json
import re
import shutil
import subprocess
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


def frontmatter_end(lines):
    """frontmatter 结束定界行索引（顶格精确，无 strip）——[impl-review-fix] A3：防缩进
    `  ---` 被当结束定界（实测把 facts 块内一行 `  ---` 误判为边界，assumptions_open 读 0）。
    无闭合返回 None。scaffold 用此共享 helper 做**行级原地改写**定位（DEC-1）；
    `parse_frontmatter` 也复用它做闭合性预扫描（见该函数与 `_yq()` 的说明）——两个消费方
    都要的是"第几行是定界符"这一位置信息，不是 YAML 语义值，故本函数保留纯文本扫描，
    不委托 yq（yq 是值抽取器、不回答行位置问题；basis-5：这是有界字面定界符定位，非
    无界 YAML 解析）。"""
    return next((i for i in range(1, len(lines)) if lines[i] == "---"), None)


# ────────────────────────────── yq(mikefarah) subprocess 薄封装 ──────────────────────────
# [shared-yaml-subset-parser] `parse_frontmatter` 的 YAML **取值**核心委托给外部 yq 二进制
# （同 git 的外部二进制先例）。本文件自己内联一份 `_yq()`（各脚本各自内联，不跨脚本
# import，见 sdflow-ship/scripts/ship_gate.py 同名函数的姊妹实现）；因所有调用点都是
# 内存中的 `text`（`parse_frontmatter(text)` 从不接收文件路径——`sad_scaffold.py`/
# `sad_lint.py` 均先自行读文件/`git show` 再把文本传入），采用 ship_gate.py 同款
# `text=` stdin 模式，不新增落临时文件的开销。
#
# 【yq 已知局限，实测确认（本机 yq v4.53.3）】`--front-matter=extract` 对没有第二个 `---`
# 的文件，会把首行 `---` 之后的**全部内容**当同一份 YAML 文档处理，若该内容恰好合法会
# 静默"解析成功"——`parse_frontmatter` 借 `frontmatter_end` 的闭合性预扫描堵住这个口子
# （见下方函数体）。
_yq_bin = None  # 进程内缓存


def _dedupe_object_pairs(pairs):
    """`json.JSONDecoder(object_pairs_hook=...)` 钩子：任一层 JSON 对象内出现重复键 → raise。

    【为什么这能work、而不是又一次手搓解析】yq 对 YAML 顶层/嵌套 mapping 里的重复键采用
    "语义上静默取最后值"，但它吐出的 **JSON 文本**里重复键会被**原样双写**（实测确认：
    `{"sad_status": "draft", "sad_status": "draft"}`，两个键字面都在）。Python `json`
    模块允许把这类"语法合法、语义有歧义"的重复键对喂给一个自定义 hook（该 hook 收到
    **该层全部** (key, value) pair，含重复项）——这是消费 yq 已产出的 JSON 结构化数据，
    不是解析 YAML 语法本身，故不违反 basis-5。之前的手搓实现能在扫描时报
    `duplicate-key: <key>`；此处对齐保留同一失败模式（不同层级/字段名不再逐一分类，
    统一在 `parse_frontmatter` 侧包装为 `SadParseError`）。
    """
    seen = set()
    out = {}
    for k, v in pairs:
        if k in seen:
            raise RuntimeError(f"duplicate-key: {k!r}")
        seen.add(k)
        out[k] = v
    return out


def _yq(expression, file=None, *, text=None, front_matter=False, in_place=False, default=None):
    """yq(mikefarah) subprocess 薄封装（design.md §1 参考实现 + F3 多文档防御 + 重复键检测，
    对齐 ship_gate.py 的 `text=` stdin 支持）。`file`=路径 或 `text`=字符串（走 stdin），二选一。

    [R7/F2] exit≠0 恒 raise RuntimeError（不吞、不因 default 静默）——「键不存在」（exit 0 +
    stdout=null，走 default）与「解析失败」（exit≠0，含 yq 未安装/身份不对/文件不可读/语法
    错误/重复键）是两条不同分支。
    [F6] 身份校验：`--version` 输出须含 `mikefarah`，拒 kislyuk/yq（jq 语法不兼容）。
    [F10] `encoding="utf-8", errors="replace"`——Windows 默认 GBK/cp936 会破坏非 ASCII 内容。
    [F3] 多文档防御：stdout 含一个以上 JSON 值（疑似多文档 YAML）→ raise，不静默只取第一个。
    [R5/F4] frontmatter 模式下、调用方传了非 None 的 `default`（意味着期望 dict 形状）时，
    校验解出的顶层结构须为 dict，非 dict → 视为坏块，返回 default（不静默当作合法标量）。
    """
    global _yq_bin
    if _yq_bin is None:
        yq = shutil.which("yq")
        if not yq:
            raise RuntimeError(
                "yq 未安装。安装方式：\n"
                "  macOS:   brew install yq\n"
                "  Windows: winget install --id MikeFarah.yq\n"
                "  Linux:   snap install yq")
        vr = subprocess.run([yq, "--version"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if "mikefarah" not in vr.stdout:
            raise RuntimeError(
                "检测到的 yq 不是 mikefarah/yq（可能是 kislyuk/yq）。\n"
                "  请卸载后安装正确版本：\n"
                "  macOS:   brew install yq\n"
                "  Windows: winget install --id MikeFarah.yq\n"
                "  Linux:   snap install yq")
        _yq_bin = yq
    cmd = [_yq_bin]
    if front_matter:
        cmd += [f"--front-matter={'process' if in_place else 'extract'}"]
    if in_place:
        cmd.append("-i")
    else:
        cmd += ["-o", "json"]
    cmd.append(expression)
    stdin_input = None
    if text is not None:
        cmd.append("-")
        stdin_input = text
    else:
        cmd.append(str(file))
    r = subprocess.run(cmd, capture_output=True, text=True, input=stdin_input,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"yq failed: {r.stderr.strip()}")
    if in_place:
        return None
    raw = r.stdout.strip()
    if not raw or raw == "null":
        return default
    decoder = json.JSONDecoder(object_pairs_hook=_dedupe_object_pairs)
    parsed, idx = decoder.raw_decode(raw)
    if raw[idx:].strip():
        raise RuntimeError(f"yq 输出多个 JSON 值（疑似多文档 YAML，不支持）: {raw[:200]!r}")
    if front_matter and not in_place and default is not None:
        if not isinstance(parsed, dict):
            return default
    return parsed


def _require_int(key, value):
    """业务层类型校验（yq 已把标量类型化，这里只做 bool≠int 的排除 + 非 int 拒绝）。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise SadParseError(f"bad-type: {key} 须为整数，得到 {value!r}")
    return value


def parse_frontmatter(text):
    """解析首块 frontmatter 为 dict（DEC-1 单一源）。

    [shared-yaml-subset-parser] YAML **语法层**（缩进/冒号/引号/注释剥离/重复键/多文档
    判定）全部委托 `_yq('.', text=text, front_matter=True)`；本函数只做**业务层**判断：
    `TOP_KEYS`/`FACT_KEYS`/`FACT_VALUES` 白名单、必需键、枚举、整数类型。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SadParseError("frontmatter 缺失：首行须为 ---")
    end = frontmatter_end(lines)   # [impl-review-fix] A3 顶格精确 + yq 未闭合静默接受的预扫描
    if end is None:
        raise SadParseError("frontmatter 未闭合：缺结束 ---")
    try:
        fm = _yq(".", text=text, front_matter=True, default={})
    except RuntimeError as e:
        raise SadParseError(f"frontmatter 解析失败: {e}") from e
    if not isinstance(fm, dict):
        raise SadParseError(f"frontmatter 顶层结构非 dict: {fm!r}")

    unknown = [k for k in fm if k not in TOP_KEYS]
    if unknown:
        raise SadParseError(f"out-of-domain: 未知键 {unknown!r}（白名单 {TOP_KEYS}）")
    if "sad_schema" not in fm or "sad_status" not in fm:
        raise SadParseError("frontmatter 缺必需键 sad_schema / sad_status")

    schema_val = _require_int("sad_schema", fm["sad_schema"])
    if fm["sad_status"] not in STATUS_ENUM:
        raise SadParseError(f"out-of-domain: sad_status 须∈{STATUS_ENUM}，得到 {fm['sad_status']!r}")

    facts_raw = fm.get("facts", {})
    if not isinstance(facts_raw, dict):
        raise SadParseError("facts 须为嵌套块，不接受内联标量")
    bad_fact_keys = [k for k in facts_raw if k not in FACT_KEYS]
    if bad_fact_keys:
        raise SadParseError(f"out-of-domain: facts 未知子键 {bad_fact_keys!r}")
    for k, v in facts_raw.items():
        if v not in FACT_VALUES:
            raise SadParseError(f"out-of-domain: facts.{k} 值须∈{FACT_VALUES}，得到 {v!r}")

    assumptions_open = _require_int("assumptions_open", fm.get("assumptions_open", 0))

    return {
        "sad_schema": schema_val,
        "sad_status": fm["sad_status"],
        "facts": facts_raw,   # 缺失键即缺席（消费方按 .get(k, "missing") 兜底，语义不变）
        "assumptions_open": assumptions_open,
    }


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
    """第 5 节（CONTRACT_SECTION）span 内的 (lineno, line) —— 🔴 【含 fence 内的行】。

    【为什么 contract 扫描 MUST NOT 剥 fence】（devenv 试点在真 SAD 上抓到的假绿）：
    `sad-template.md` 明确要求 contract 行写在 fence 内（「contract 行格式示例（fence 内）」），
    而真实 SAD 也确实这么写（mqtt-console：44 条 contract 全在 fence 里）。
    原实现走 `body_lines`（DEC-2，剥 fence）⇒ **在任何真实 SAD 上都抽出 0 条** ⇒
    `_check_contract_invariants` 从来没触发过，`devenv_lint` 的 contract 差集恒空。

    **测试当时是绿的** —— 因为 `tests/conftest.py` 的 fixture 恰好把 contract 行写在 fence 外。
    **producer 说 fence 内，parser 剥 fence，fixture 站在 parser 这边 ⇒ 三方各说各话的假绿。**

    【为什么不必担心误伤】：A6② 的顾虑是「全文扫描会误伤附录/散文里的类比提及」——
    那由 **§5 限定** 挡住（附录不在 §5 的 span 里），**不是**由剥 fence 挡住的。
    §5 之内的 fence，本来就是 contract 该待的地方。

    ⚠️ 其余一切扫描仍走 `body_lines`（剥 fence）—— 本函数是 contract 专用的例外，别扩大。
    """
    lines = text.splitlines()
    out, in_span = [], False
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            in_span = (line.strip() == CONTRACT_SECTION)
            continue
        if in_span:
            out.append((i, line))
    return out


def scan_contract_tags(text):
    """只扫第 5 节 span 内的 contract[...] 标签（[impl-review-fix] A6②：全文扫描会误伤
    附录/散文里的类比提及）。捕获任意载荷，payload 交消费方做枚举校验。返回 [(lineno, payload)]。"""
    out = []
    for ln, line in _section5_body_lines(text):
        out += [(ln, m.group(1)) for m in CONTRACT_RE.finditer(line)]
    return out


CONTRACT_NAME_RE = re.compile(r"contract\[[^\]]*\]\s*([^：:|\n]+)")


def scan_contract_names(text):
    """只扫第 5 节 span 内的 contract 【名字】。返回 [(lineno, name)]。

    行格式（本 skill 是它的 producer，故解析归这里；消费方 MUST NOT 另抄一份正则）：

        - contract[draft] 采集端→上报端接口：语法/语义/质量/所有权/演进
        | … | contract[draft] 采集端→上报端接口 | … |          ← 表格单元格里也合法

    名字 = `contract[<tag>]` 之后、到 `：` / `:` / `|` / 行尾 为止的那一段（strip）。
    语法面有界（固定字面前缀 + 三个终止符），穷举得完 ⇒ 可手写〔基准 5〕。

    【谁在消费】：`sdflow-devenv` 的 `devenv_lint` 拿它跟泳道的 `covers` 并集做差集——
    差集是【拿去问人的，不是拿去拦人的】（那条 contract 还没有泳道覆盖，要建一条吗？）。
    """
    out = []
    for ln, line in _section5_body_lines(text):
        for m in CONTRACT_NAME_RE.finditer(line):
            name = m.group(1).strip()
            if name:
                out.append((ln, name))
    return out


def scan_contract_malformed(text):
    """第 5 节 span 内出现 `contract[` 却无闭合 `]` 的行（[impl-review-fix] A6 fail-closed：
    坏标签不得逃逸枚举校验）。返回 [(lineno, line_stripped)]。"""
    out = []
    for ln, line in _section5_body_lines(text):
        if "contract[" in CONTRACT_RE.sub("", line):
            out.append((ln, line.strip()))
    return out
