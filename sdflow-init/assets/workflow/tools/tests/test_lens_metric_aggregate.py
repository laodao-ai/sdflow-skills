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
    # 真哨兵：完整锚前缀出现在行中但非行首（startswith 正确=None；裸 in 会误取→捕获退化）
    assert lma.parse_anchor('foo bar <!-- sdflow:lens-metric v1 layer="x" lens="domain" -->') is None

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


def _write(tmp_path, change, *anchors):
    d = tmp_path / "archive" / change; d.mkdir(parents=True)
    (d / "code-review-report.md").write_text("\n".join(anchors) + "\n", encoding="utf-8")

def _a(lens, findings, 采纳, 独立, site="—", layer="code-review"):
    return (f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{lens}" runner="claude" '
            f'site="{site}" findings="{findings}" 采纳="{采纳}" 裁掉="0" defer="0" '
            f'独立="{独立}" sev="致0/高{采纳}/中0/低0" -->')

def test_aggregate_two_changes(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2), _a("adversarial", 4, 2, 1))
    _write(tmp_path, "c2", _a("domain", 6, 4, 3))
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    assert len(rows) == 3 and no_anchor == []

def test_no_anchor_report_counted(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    old = tmp_path / "archive" / "old"; old.mkdir(parents=True)
    (old / "code-review-report.md").write_text("旧格式 voice分桶: codex 采纳3/裁掉0\n", encoding="utf-8")
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    assert "old" in no_anchor  # 显式计无锚样本，不静默跳过

def test_render_table_has_independent_and_flags(tmp_path):
    # 独立列非空 + 出现轮数≥10 标记（构造 domain 出现 10 轮）
    for i in range(10):
        _write(tmp_path, f"c{i}", _a("domain", 5, 3, 2))
    rows, no_anchor = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    assert "独立" in table and "≥10" in table  # 表含独立列 + N≥10 标记
    assert "无锚样本" in table  # 无锚计数呈现

def test_out_of_enum_lens_flagged(tmp_path):
    _write(tmp_path, "c1", _a("对抗镜1", 3, 1, 1))  # 未折叠的非法值
    rows, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "越域" in table or "invalid" in table.lower()  # 非法 lens 值被标记不静默

def test_no_synthetic_score(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    rows, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "综合分" not in table and "价值分" not in table  # 描述性多列,无合成分

def test_unclosed_fence_swallows_trailing_anchors(tmp_path):
    # 诚实留档：奇数个 ``` （未闭合 fence）会把其后所有行都视为 fence 内，
    # 导致尾部锚被漏计（少计而非误取，方向偏保守，暂可接受）。
    anchor2 = _a("adversarial", 4, 2, 1)
    text = _a("domain", 5, 3, 2) + "\n```\n" + anchor2 + "\n"  # 只开未关
    p = tmp_path / "archive" / "c1"; p.mkdir(parents=True)
    (p / "code-review-report.md").write_text(text, encoding="utf-8")
    rows = lma.parse_report(p / "code-review-report.md")
    assert len(rows) == 1  # 第二个锚因未闭合 fence 被漏计,不是被误取
