"""F3 跨文件一致性 golden 测试（Task 6）。

背景：hr_tg_intersect.py（emit 侧）与 anchor_lint.py（lint 侧）各自本地重实现了 trigger-catalog
解析（HR-TG 子集 + 全集 + hit 重算），遵仓内「非 import」约定（adr/0002）。两份独立重实现存在
漂移风险——本文件是唯一的机械兜底：喂同一份 catalog，分别调用两侧真实生产代码，断言产出一致。

三条断言线：
  1) test_load_hr_tg_subset_matches_across_tools —— 两侧独立 parse 出的 HR-TG 子集 / 全集逐字相等
     （drift 若发生在 load_hr_tg_subset/load_all_tg_set 本身，最先在此暴露）。
  2) test_emit_hit_matches_lint_recompute（主 golden，参数化多组 tg-set）—— 用 hr_tg_intersect 的
     intersect() 算出 emit hit，据此构造一条「模拟真实落盘」的 hr-tg 锚串，直接喂给 anchor_lint 的
     真实生产校验函数 check_hr_tg()（而非在本测试里重抄一份 M2 公式）；若 anchor_lint 独立重算的
     hit 与 emit hit 不一致，check_hr_tg 会产出 hit-declared-mismatch violation —— 断言 violations
     为空，即两侧口径吻合。这是最接近生产链路的比较方式：hr_tg_intersect 出锚 → anchor_lint 验锚，
     真实场景就是这条链路，比在测试里独立复刻 M2 公式更能捕获两侧代码本身的漂移。
     诚实边界：断言 2 走的是 check_hr_tg() 内部通道——它在比较前会用自己的 key
     `sorted(set(actual), key=lambda x: int(x[3:]))` 对 hit 重排，这意味着锚串 hit= 字面顺序在比较
     前已被丢弃、按 lint 侧自己的 key 重新排过一次；故断言 2 只验证「hit 的集合成分」一致，
     验不出「emit 侧写入 hit= 的字面顺序是否为 brief 接口明令的数值序」——若 emit 侧排序 key 漂移成
     字典序，断言 2 仍会通过（沙箱复现：`hit="TG-26,TG-04,TG-16"` 乱序字面串直接喂 check_hr_tg()，
     violations == []）。断言 3 补此缺口。
  3) test_emit_hit_numeric_order_not_lexicographic —— 直接验证 hr_tg_intersect.intersect() 返回的
     hits/declared 字面顺序为数值序（int(t[3:]) 为 key），不经 check_hr_tg（会重排、盖住顺序漂移）。
     用跨位数 token（TG-6 与 TG-16）构造字典序≠数值序的分叉输入，使断言在排序 key 漂移时真会 FAIL。
     lint 侧顺序诚实边界：check_hr_tg() 内部 actual_sorted 是函数局部变量，未对外暴露，故本文件无法
     独立取出 lint 侧「重算后的有序 hit」来做同等的逐元素同序断言；lint 侧的顺序契约只能通过其内部
     re-sort 后与 expect_hits（同样重排过）比较来保证在场，不经锚串字面传递，这是本文件的诚实边界
     （非空缺——lint 侧本就不需要保序，因为它不回写 hit=，只读入比较）。

若本文件任一用例 FAIL：说明 hr_tg_intersect.py 与 anchor_lint.py 的解析口径已产生真实漂移，
须回 Task 2/4 对齐两侧实现——MUST NOT 为让本测试变绿而回头改任一侧生产代码掩盖问题。
"""
import importlib.util
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent          # .../workflow/tools
HI_SCRIPT = TOOLS / "hr_tg_intersect.py"
AL_SCRIPT = TOOLS / "anchor_lint.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _hi():
    return _load("hr_tg_intersect", HI_SCRIPT)


def _al():
    return _load("anchor_lint", AL_SCRIPT)


# --- 共用最小 trigger-catalog（触发词目录全集表段 + HR-TG 段），emit 侧与 lint 侧喂同一份数据 ---
# 8 个真实 HR-TG 成员（仅夹具用，非从任一脚本复制——脚本 MUST 各自从单一源读）。
REAL_MEMBERS = "TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26"

_ALL_TG_TABLE = (
    "## 三、触发词目录\n\n"
    "| ID | 触发 |\n|---|---|\n"
    + "".join(f"| TG-{n:02d} | x |\n" for n in (1, 4, 6, 7, 8, 9, 16, 17, 19, 26, 99))
    + "\n"
)


def _shared_catalog(tmp_path):
    body = (
        "# 触发目录\n\n"
        f"{_ALL_TG_TABLE}"
        "## 七、HR-TG 子集（评审 cross-model 层单一源）\n\n"
        "> 高风险触发子集——命中任一 → 单开领域 cross-model。\n"
        f"> 成员：**{REAL_MEMBERS}**\n"
    )
    p = tmp_path / "trigger-catalog.md"
    p.write_text(body, encoding="utf-8")
    return p


# --- 断言线 1：两侧独立 parse 出的 HR-TG 子集 / 全集逐字相等 ---

def test_load_hr_tg_subset_matches_across_tools(tmp_path):
    hi, al = _hi(), _al()
    cat = _shared_catalog(tmp_path)
    assert hi.load_hr_tg_subset(cat) == al.load_hr_tg_subset(cat)
    assert hi.load_all_tg_set(cat) == al.load_all_tg_set(cat)


# --- 断言线 2（主 golden）：emit 侧 intersect 出的 hit，喂给 lint 侧真实 check_hr_tg 重算须零违规 ---
# tg_set 覆盖：命中(TG-04,TG-16 均 HR-TG) / 不命中(TG-19 在全集但非 HR-TG) / 空集 / 混合(命中+不命中)。

@pytest.mark.parametrize("tg_set", ["TG-04,TG-16", "TG-19", "", "TG-04,TG-19,TG-26"])
def test_emit_hit_matches_lint_recompute(tmp_path, tg_set):
    hi, al = _hi(), _al()
    cat = _shared_catalog(tmp_path)

    # emit 侧：hr_tg_intersect 独立 parse + intersect（生产代码原样调用，非重抄逻辑）
    hi_subset = hi.load_hr_tg_subset(cat)
    emit_hits, declared = hi.intersect(hi.parse_tg_set(tg_set), hi_subset)

    # 构造一条「模拟真实落盘」的 hr-tg 锚串（用 emit 侧算出的 hit/declared），喂给 anchor_lint
    hit_field = f'"{",".join(emit_hits)}"' if emit_hits else '"none"'
    declared_field = f'"{",".join(declared)}"'
    evidence = ' evidence="x"' if emit_hits else ""     # M4：hit 非空须 evidence 在场
    anchor_line = f'<!-- sdflow:hr-tg v1 hit={hit_field} declared={declared_field}{evidence} -->'
    report_text = f"# 报告\n\n{anchor_line}\n"

    # lint 侧：anchor_lint 独立 parse catalog + 调用真实生产校验函数 check_hr_tg（含 M2 重算）
    al_hr_tg_subset = al.load_hr_tg_subset(cat)
    al_all_tg_set = al.load_all_tg_set(cat)
    violations = al.check_hr_tg(report_text, al_hr_tg_subset, al_all_tg_set)

    assert violations == [], (
        f"emit hit 与 lint 独立重算不一致（跨文件漂移）: tg_set={tg_set!r} "
        f"emit_hits={emit_hits} declared={declared} violations={violations}"
    )


# --- 断言线 3：emit 侧 intersect() 输出严格数值序（不经 check_hr_tg，避免其内部重排丢序） ---
# 现有 _shared_catalog 全 2 位补零书写（TG-04 ... TG-26），字典序恰好 == 数值序，无法暴露排序 key
# 漂移；本 fixture 故意用跨位数 token（TG-6 / TG-16）令两种序在此分叉。

_CROSS_DIGIT_ALL_TG_TABLE = (
    "## 三、触发词目录\n\n"
    "| ID | 触发 |\n|---|---|\n"
    "| TG-6 | x |\n"
    "| TG-16 | x |\n"
    "\n"
)


def _cross_digit_catalog(tmp_path):
    """跨位数 fixture：TG-6（1 位）与 TG-16（2 位）同为 HR-TG 成员。
    裸字典序（sorted 不传 key）："TG-16" < "TG-6"（首位 '1' < '6'）→ ["TG-16", "TG-6"]。
    数值序（int(t[3:]) 为 key，brief 接口明令）：6 < 16 → ["TG-6", "TG-16"]。
    两者分叉，故能让 test_emit_hit_numeric_order_not_lexicographic 在排序 key 漂移时真 FAIL。
    """
    body = (
        "# 触发目录\n\n"
        f"{_CROSS_DIGIT_ALL_TG_TABLE}"
        "## 七、HR-TG 子集（评审 cross-model 层单一源）\n\n"
        "> 高风险触发子集——命中任一 → 单开领域 cross-model。\n"
        "> 成员：**TG-6, TG-16**\n"
    )
    p = tmp_path / "trigger-catalog-cross-digit.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_emit_hit_numeric_order_not_lexicographic(tmp_path):
    """F3 补（Important 修复）：直接断言 hr_tg_intersect.intersect() 的 hits/declared 字面顺序为
    数值序，不经 check_hr_tg（其内部 `sorted(set(actual), key=lambda x: int(x[3:]))` 会用自己的
    key 重排 hit，比较前即丢弃锚串字面顺序——若只经它断言，emit 侧排序 key 即便漂移成字典序也测
    不出来，见文件头 docstring 断言线 2 的诚实边界说明）。

    喂 tg_set="TG-16,TG-6"（跨位数、乱序输入，命中 _cross_digit_catalog 的两个 HR-TG 成员）：
      - 若 hr_tg_intersect._sort_key 仍为 `int(t[3:])`（数值序，契约正确）→ hits == ["TG-6","TG-16"]。
      - 若排序 key 漂移成裸字典序（如误改成 `sorted(set(...))` 不传 key）→ hits == ["TG-16","TG-6"]，
        本断言 FAIL。
    空跑证据（验过、未落盘改动）：把本机 hr_tg_intersect.py 的 `_dedup_sorted` 临时改成
    `return sorted(set(tokens))`（去掉 key=_sort_key，模拟字典序漂移）重跑本用例 → AssertionError:
    hits == ['TG-16', 'TG-6'] != ['TG-6', 'TG-16']，证明本断言确实能暴露该类漂移；改回后复跑转绿。
    """
    hi = _hi()
    cat = _cross_digit_catalog(tmp_path)
    hr_tg_subset = hi.load_hr_tg_subset(cat)

    hits, declared = hi.intersect(hi.parse_tg_set("TG-16,TG-6"), hr_tg_subset)

    assert hits == ["TG-6", "TG-16"], (
        f"emit 侧 hit 应为数值序，实得 {hits!r}（若为 ['TG-16','TG-6'] 即字典序漂移，未按数值排序）"
    )
    assert declared == ["TG-6", "TG-16"], (
        f"emit 侧 declared 同样须数值序，实得 {declared!r}"
    )
