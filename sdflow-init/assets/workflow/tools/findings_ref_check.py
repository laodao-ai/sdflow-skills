#!/usr/bin/env python3
"""findings_ref_check — 评审 findings 引用核验机械前置门（implement-workflow-optimization-2026-08-p2 DD4）。
承 adr/0041 裁决地基改造：三层裁决协议（机械引用核 → 强档二元裁决 → 置信降排序）的第一层。
纯 stdlib、无 subprocess，只吃结构化 JSON——MUST NOT 解析 markdown 散文（design.md DD4）。

三查（对每条 finding 的 `{file, line, quote}` 三元组）：
    ① 引用路径存在（相对 `--root` 解析，绝对路径原样）
    ② `file:line` 落在文件行数内
    ③ 单行引文命中所报行（对该行文本做子串核，MUST NOT 整文件子串核——
       整文件核可被任意合法行号 + 他处文本绕过，spec-review-amendment 明令堵死此形）

三态输出（每条独立 `{id, status, reason?}`）：
    pass         三查全过
    fail         结构化字段在、任一查不过；或「无引文且无证据包」（确认皆缺）→ 机械裁掉
    uncheckable  引用非干净 `path:N` 形态——证据包（`evidence_pack` 在场）/ 设计层引用
                 （有引文但无 file/line）/ 行范围外形态（`line` 非干净正整数，如区间字符串
                 `"12-18"`、list、浮点）——一律不裁，原样直进强档二元裁决

**引文与断言的语义对应不查**——那是强档二元裁决的活（基准 1 切分：有确定性信号的下沉脚本，
语义残余留裁决），本脚本只核「引用是否真实指向所声明的位置」这一层确定性信号。

脚本级不可恢复错误（输入 JSON 畸形 / findings 结构非预期导致内部异常，如列表内混入非
对象条目）⇒ 整批降级：`result="degraded"` + `code="[ref-check-unavailable]"`，`results=[]`
（不吐半截结果、不静默呈现「全部 pass」假象——消费型信号校验器输出诚实，adr/0016 反静默方向；
degraded 与 ok 两态在 JSON 顶层字段值上互斥可辨，调用方读 JSON 即可区分，不依赖退出码）。
单条 finding 内部形态不合预期（如 file/line 缺一角但非「彻底空」）不视为脚本崩溃，
归入 uncheckable（design-reference），不牵连批次其余结果——只有结构层面真正不可辨识的输入
（JSON 语法错误 / 列表条目非对象）才触发整批降级。"""
import argparse, json, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

EXIT_OK, EXIT_DEGRADED = 0, 1
DEGRADE_CODE = "[ref-check-unavailable]"


def _clean_line_number(value):
    """严格判「干净单行形态」：正整数 `int`（非 bool）或纯数字字符串。其余一律非干净
    （浮点、负数、0、区间字符串 `"12-18"`、list/dict 等）→ 返回 None，调用侧归 uncheckable。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 1 else None
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            n = int(s)
            return n if n >= 1 else None
    return None


def classify_finding(finding, root):
    """单条 finding 三态分类。`finding` MUST 为 dict（非 dict 由调用侧 process_batch 自然抛出
    AttributeError，触发整批降级——见模块 docstring「脚本级不可恢复错误」）。"""
    evidence_pack = finding.get("evidence_pack")
    has_evidence = evidence_pack not in (None, "", {}, [])
    quote = finding.get("quote")
    has_quote = isinstance(quote, str) and quote.strip() != ""

    if has_evidence:
        return {"status": "uncheckable", "reason": "evidence-pack"}
    if not has_quote:
        return {"status": "fail", "reason": "no-quote-no-evidence"}

    file_field = finding.get("file")
    has_file = isinstance(file_field, str) and file_field.strip() != ""
    line_raw = finding.get("line")
    line_int = _clean_line_number(line_raw)

    if not has_file or line_int is None:
        # 有引文但拿不到干净 path:N 三元组——区分「给了 line 但形态非干净单行」vs「压根没给 file/line」
        if has_file and line_raw is not None and line_int is None:
            return {"status": "uncheckable", "reason": "line-range-form"}
        return {"status": "uncheckable", "reason": "design-reference"}

    target = Path(root) / file_field
    if not target.is_file():
        return {"status": "fail", "reason": "path-not-found"}
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {"status": "fail", "reason": "file-unreadable"}
    if line_int > len(lines):
        return {"status": "fail", "reason": "line-out-of-bounds"}
    target_line = lines[line_int - 1]
    if quote.strip() in target_line:
        return {"status": "pass"}
    return {"status": "fail", "reason": "quote-mismatch"}


def load_findings(raw_text):
    """解析输入 JSON → findings 列表。顶层可为裸 list，或 `{"findings": [...]}`。
    其余顶层形态（含 `findings` 非 list）视为畸形输入，抛 ValueError（调用侧转整批降级）。"""
    data = json.loads(raw_text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("findings"), list):
        return data["findings"]
    raise ValueError('顶层须为 JSON list，或 {"findings": [...]} 形态')


def process_batch(findings, root):
    """逐条分类。任一条目非 dict ⇒ `.get` 自然抛 AttributeError，向上传播触发整批降级
    （单条彻底不可辨识的条目视为「结构层面不可信」，非可归类的 uncheckable/fail 残余）。"""
    results = []
    for idx, f in enumerate(findings):
        fid = f.get("id") or f"finding-{idx}"
        outcome = classify_finding(f, root)
        outcome["id"] = fid
        results.append(outcome)
    return results


def _emit_ok(results):
    print(f"[findings_ref_check] OK: {len(results)} 条", file=sys.stderr)
    print(json.dumps({"result": "ok", "results": results}, ensure_ascii=False))
    return EXIT_OK


def _emit_degraded(reason):
    print(f"[findings_ref_check] DEGRADED: {reason}", file=sys.stderr)
    print(json.dumps({
        "result": "degraded",
        "code": DEGRADE_CODE,
        "reason": reason,
        "results": [],
    }, ensure_ascii=False))
    return EXIT_DEGRADED


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="findings 引用核验机械前置门（确定性·三态输出·崩溃显式降级）")
    ap.add_argument("--input", required=True, help="findings JSON 文件路径")
    ap.add_argument("--root", default=".", help="finding.file 相对路径解析根目录")
    args = ap.parse_args(argv)

    try:
        raw = Path(args.input).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return _emit_degraded(f"input-unreadable: {e}")

    try:
        findings = load_findings(raw)
    except (json.JSONDecodeError, ValueError) as e:
        return _emit_degraded(f"input-json-malformed: {e}")

    try:
        results = process_batch(findings, Path(args.root))
    except Exception as e:  # 蓄意宽捕：脚本本体崩溃须整批降级，不得让单条畸形条目击穿仍能续算的其余结果
        return _emit_degraded(f"internal-error: {e}")

    return _emit_ok(results)


if __name__ == "__main__":
    sys.exit(main())
