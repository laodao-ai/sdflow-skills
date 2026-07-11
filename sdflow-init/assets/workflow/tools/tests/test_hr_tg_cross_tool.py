"""F3 跨文件一致性 golden 测试（Task 6）。

背景：hr_tg_intersect.py（emit 侧）与 anchor_lint.py（lint 侧）各自本地重实现了 trigger-catalog
解析（HR-TG 子集 + 全集 + hit 重算），遵仓内「非 import」约定（adr/0002）。两份独立重实现存在
漂移风险——本文件是唯一的机械兜底：喂同一份 catalog，分别调用两侧真实生产代码，断言产出一致。

两条断言线：
  1) test_load_hr_tg_subset_matches_across_tools —— 两侧独立 parse 出的 HR-TG 子集 / 全集逐字相等
     （drift 若发生在 load_hr_tg_subset/load_all_tg_set 本身，最先在此暴露）。
  2) test_emit_hit_matches_lint_recompute（主 golden，参数化多组 tg-set）—— 用 hr_tg_intersect 的
     intersect() 算出 emit hit，据此构造一条「模拟真实落盘」的 hr-tg 锚串，直接喂给 anchor_lint 的
     真实生产校验函数 check_hr_tg()（而非在本测试里重抄一份 M2 公式）；若 anchor_lint 独立重算的
     hit 与 emit hit 不一致，check_hr_tg 会产出 hit-declared-mismatch violation —— 断言 violations
     为空，即两侧口径吻合。这是最接近生产链路的比较方式：hr_tg_intersect 出锚 → anchor_lint 验锚，
     真实场景就是这条链路，比在测试里独立复刻 M2 公式更能捕获两侧代码本身的漂移。

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
