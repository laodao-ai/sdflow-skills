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
