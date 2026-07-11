#!/usr/bin/env python3
"""review_disposition_check — 确定性 roadmap Review 处置小节校验器（mlh-p4·T82）。
读一份 roadmap task-log，fence/结构感知地断言 `## Review 处置` 小节存在且非空（非仅脚手架注释/空白），
归约出唯一 reason_code(三枚举)：section-missing | section-empty | section-ok-DISPOSITION-UNCHECKED。
纯 stdlib、无 subprocess、门控外置（不读 config）；文件缺失/不可读 fail-closed all-or-nothing。

设计边界（design.md D4 / spec RDC）：
- MUST NOT naive-grep 那个「已处置」的否定词子串——收尾声明句「本小节无『…』条目」含该子串却恰是合规态；
  本脚本根本不匹配该子串，靠「小节存在 + 去注释后非空」的结构判定绕开自指陷阱（memory gate-substring-detection-dogfood）。
- MUST NOT 断言逐条已处置（格式三实例不统一、无字面 token、机械不可达）——归模型；
  输出码尾缀 -DISPOSITION-UNCHECKED 显式点明逐条未核（adr/0018 输出诚实，防 present 被误读为已核=假绿）。
- fence 感知：`## Review 处置` 若仅出现在 code fence 内（示例文本）不算小节存在；
  小节体的「非空」判定去除 HTML 注释 / 水平分隔线 / 空白后再看是否有实体内容。
承 4.C lens_metric_emit 形态（EmitError + EXIT_OK/EXIT_FAIL、跨模块口径重实现不 import）。"""
import argparse, re, sys
from pathlib import Path

EXIT_OK, EXIT_FAIL = 0, 1
REASON_OK = "section-ok-DISPOSITION-UNCHECKED"   # 存在+非空达成；逐条处置显式未核
REASON_MISSING = "section-missing"
REASON_EMPTY = "section-empty"

SECTION_TITLE = "Review 处置"                      # 模版 task-log-template.md:62 规定的 level-2 标题
_FENCE_RE = re.compile(r'^ {0,3}(`{3,}|~{3,})')  # code fence 起止（fence-aware，含缩进容忍）
_H2_RE = re.compile(r'^##[ \t]+(.+?)[ \t]*$')    # level-2 标题（`### ` 不匹配：第三字符非空白）
_H12_RE = re.compile(r'^#{1,2}[ \t]')            # level-1/2 标题（小节边界；level-3 不算边界=属小节内）
_THEMATIC_RE = re.compile(r'^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$')  # 水平分隔线 --- / *** / ___
_HTML_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)              # HTML 注释（非贪婪；结构定位用：标题行行首是否落注释内）
_HTML_COMMENT_GREEDY_RE = re.compile(r'<!--.*-->', re.DOTALL)        # HTML 注释（贪婪；空判用：注释体含 --> 记号的模版例整体视作注释，见 _has_entity_content）


class EmitError(Exception):
    """坏输入 fail-closed（task-log 文件缺失 / 非普通文件 / 解码失败）。"""
    pass


def _annotate_lines(lines):
    """逐行标注 (line, is_live, in_fence)：is_live = 不在 code fence 内、且不在 HTML 注释内的行；
    in_fence = 该行属 code fence（含起止行）。
    fence 用 ``` / ~~~ 成对跟踪；HTML 注释按 <!-- ... --> 跨行跟踪（fence 内不解释注释）。
    用于「结构定位」（标题/边界识别，看 is_live）与「空判」（fence 体计为内容，看 in_fence）——单一逐行态，
    fence 内的伪标题、注释里的伪标题均非 live，不被当作小节。"""
    out = []
    in_fence, fence_char, fence_len = False, None, 0
    in_comment = False
    for ln in lines:
        if in_fence:
            m = _FENCE_RE.match(ln)
            if (m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len
                    and ln[m.end():].strip() == ""):
                in_fence = False
            out.append((ln, False, True))                 # fence 内（含起止行）非 live、in_fence
            continue
        if in_comment:
            if "-->" in ln:
                in_comment = False
            out.append((ln, False, False))                # 注释内非 live
            continue
        m = _FENCE_RE.match(ln)
        if m:
            in_fence, fence_char, fence_len = True, m.group(1)[0], len(m.group(1))
            out.append((ln, False, True))                 # fence 起始行非 live、in_fence
            continue
        # 移除本行内成对注释后若仍留悬空 <!-- → 进入跨行注释态（本行仍算 live，标题在 <!-- 前才有意义）
        if "<!--" in _HTML_COMMENT_RE.sub("", ln):
            in_comment = True
        out.append((ln, True, False))
    return out


def find_section_body(text):
    """结构感知定位 `## Review 处置` level-2 小节，返回小节体行列表；无该 live 小节 → None。
    小节体 = 标题行之后到下一个 live level-1/2 标题之前的所有原始行（fence 内伪标题不作边界）。"""
    annotated = _annotate_lines(text.splitlines())
    start = None
    for i, (ln, live, _fence) in enumerate(annotated):
        if not live:
            continue
        m = _H2_RE.match(ln)
        if m and m.group(1).strip() == SECTION_TITLE:
            start = i
            break
    if start is None:
        return None
    body = []
    for ln, live, _fence in annotated[start + 1:]:
        if live and _H12_RE.match(ln):                    # 下一 level-1/2 标题 = 小节结束
            break
        body.append(ln)
    return body


def _has_entity_content(body_lines):
    """小节体去除 HTML 注释后，是否残留实体内容（非空白、非水平分隔线）。
    与 find_section_body 共用 _annotate_lines 的 fence/注释逐行态（统一注释模型，杜绝两套漂移）：
    ① fence 内真实代码内容计为实体内容（不剔 fence 体，看 in_fence）；
    ② 非 fence 行拼回后去 HTML 注释——用**贪婪** _HTML_COMMENT_GREEDY_RE：模版脚手架注释体常含 `-->` 记号
       （如示例「例 F1 --> 采纳」），非贪婪会在首个 `-->` 早闭、把残余脚手架文字当实体内容 → 假绿；
       gate 语义下「空」是 fail-closed 安全侧（判空=退出非零逼人补真实处置，判非空=放行=假绿有害），
       故整段 `<!-- … -->` 视作注释、偏判空。剔水平分隔线/空白后仍有实体行 → 非空。"""
    annotated = _annotate_lines(body_lines)
    for ln, _live, in_fence in annotated:                 # ① fence 体真实内容 → 实体内容
        if in_fence and ln.strip():
            return True
    nonfence = "\n".join(ln for ln, _live, in_fence in annotated if not in_fence)
    stripped = _HTML_COMMENT_GREEDY_RE.sub("", nonfence)  # ② 贪婪去注释（含 --> 记号的脚手架整体剔除）
    for ln in stripped.splitlines():
        if not ln.strip():
            continue
        if _THEMATIC_RE.match(ln):
            continue
        return True
    return False


def classify(text):
    """三前置 → 唯一 reason_code：小节缺失 / 仅脚手架空 / 存在且非空（逐条未核）。"""
    body = find_section_body(text)
    if body is None:
        return REASON_MISSING
    if not _has_entity_content(body):
        return REASON_EMPTY
    return REASON_OK


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="roadmap Review 处置小节校验器（确定性·纯 stdlib·fail-closed·门控外置）")
    ap.add_argument("--task-log", required=True, help="roadmap task-log.md 路径")
    args = ap.parse_args(argv)
    path = Path(args.task_log)
    try:
        if not path.exists():
            raise EmitError(f"task-log 不存在: {path}")
        if not path.is_file():
            raise EmitError(f"task-log 非普通文件: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise EmitError(f"task-log 不可读: {e}")
        code = classify(text)
    except EmitError as e:
        print(f"[review_disposition_check] FAIL: {e}", file=sys.stderr)  # 坏输入：stderr FAIL、无 stdout
        return EXIT_FAIL
    print(code)                                                          # reason_code 落 stdout（含 missing/empty）
    return EXIT_OK if code == REASON_OK else EXIT_FAIL                   # OK exit0；其余非零（stdout 载码，区别于 stderr FAIL）


if __name__ == "__main__":
    sys.exit(main())
