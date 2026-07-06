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
    # [impl-review-fix F5] 措辞诚实化：sev 聚合器根本不消费（render_table 不读取
    # sev 字段，只落锚存证供人工/未来消费者读取）——这里只验证解析层原样保留整串
    # 不腐坏，不存在"子解析健壮性在渲染层校验"这回事。
    a = ANCHOR.replace('sev="致0/高2/中2/低1"', 'sev="高2/致0"')
    assert lma.parse_anchor(a)["sev"] == "高2/致0"


def _write(tmp_path, change, *anchors):
    d = tmp_path / "archive" / change; d.mkdir(parents=True)
    (d / "code-review-report.md").write_text("\n".join(anchors) + "\n", encoding="utf-8")

def _a(lens, findings, 采纳, 独立, site="—", layer="code-review", runner="claude"):
    return (f'<!-- sdflow:lens-metric v1 layer="{layer}" lens="{lens}" runner="{runner}" '
            f'site="{site}" findings="{findings}" 采纳="{采纳}" 裁掉="0" defer="0" '
            f'独立="{独立}" sev="致0/高{采纳}/中0/低0" -->')

def test_aggregate_two_changes(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2), _a("adversarial", 4, 2, 1))
    _write(tmp_path, "c2", _a("domain", 6, 4, 3))
    rows, no_anchor, parse_failed = lma.aggregate(tmp_path / "archive")
    assert len(rows) == 3 and no_anchor == [] and parse_failed == []

def test_no_anchor_report_counted(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    old = tmp_path / "archive" / "old"; old.mkdir(parents=True)
    (old / "code-review-report.md").write_text("旧格式 voice分桶: codex 采纳3/裁掉0\n", encoding="utf-8")
    rows, no_anchor, _ = lma.aggregate(tmp_path / "archive")
    assert "old" in no_anchor  # 显式计无锚样本，不静默跳过

def test_render_table_has_independent_and_flags(tmp_path):
    # 独立列非空 + 出现轮数≥10 标记（构造 domain 出现 10 轮）
    for i in range(10):
        _write(tmp_path, f"c{i}", _a("domain", 5, 3, 2))
    rows, no_anchor, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    assert "独立" in table and "≥10" in table  # 表含独立列 + N≥10 标记
    assert "无锚样本" in table  # 无锚计数呈现
    # 真哨兵：Σ独立=10轮×2=20 真值入表（防独立聚合退化,非仅列名存在）
    assert "| 20 |" in table
    # 补充：Σfindings=10轮×5=50 也真入表（防端到端数值退化）
    assert "| 50 |" in table

def test_out_of_enum_lens_flagged(tmp_path):
    _write(tmp_path, "c1", _a("对抗镜1", 3, 1, 1))  # 未折叠的非法值
    rows, _, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "越域" in table or "invalid" in table.lower()  # 非法 lens 值被标记不静默

def test_out_of_enum_layer_flagged(tmp_path):
    # [impl-review-fix F2] 此前只测非法 lens，未测非法 layer 分支
    _write(tmp_path, "c1", _a("domain", 3, 1, 1, layer="foo-review"))  # 未在 LAYER_ENUM 内
    rows, _, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "越域" in table  # 非法 layer 值同样被标记不静默

def test_no_synthetic_score(tmp_path):
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    rows, _, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, [])
    assert "综合分" not in table and "价值分" not in table  # 描述性多列,无合成分


def test_runner_distinguishes_outside_voice(tmp_path):
    # [impl-review-fix CF-1] 契约键是 (layer,lens,runner,site,轮)——codex 与
    # claude-fallback 是两个不同 runner，同 site 的 outside-voice 不可合并成一行。
    _write(tmp_path, "c1",
           _a("outside-voice", 3, 2, 2, site="code-voice", runner="codex"),
           _a("outside-voice", 4, 1, 1, site="code-voice", runner="claude-fallback"))
    rows, no_anchor, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    lines = [l for l in table.splitlines() if "outside-voice" in l]
    assert len(lines) == 2  # 未被错误合并成一行
    assert any("codex" in l for l in lines) and any("claude-fallback" in l for l in lines)
    # 真哨兵：各自独立的 Σfindings（3 与 4）都完整入表，不是合并后的 7
    assert any("| 3 |" in l for l in lines) and any("| 4 |" in l for l in lines)


def test_bad_encoding_report_does_not_crash_aggregate(tmp_path):
    # [impl-review-fix CF-2] 一个编码坏字节的 archived 报告不应拖垮全仓聚合，
    # 应被单独计入「解析失败」桶，其余 report 照常聚合。
    _write(tmp_path, "c1", _a("domain", 5, 3, 2))
    bad = tmp_path / "archive" / "bad"; bad.mkdir(parents=True)
    (bad / "code-review-report.md").write_bytes(b"\xff\xfe\x00broken non-utf8 bytes")
    rows, no_anchor, parse_failed = lma.aggregate(tmp_path / "archive")  # 不应抛异常
    assert "bad" in parse_failed
    assert len(rows) == 1  # 好文件不受坏文件牵连
    table = lma.render_table(rows, no_anchor, parse_failed)
    assert "解析失败" in table and "bad" in table  # 显式呈现，不静默丢


def test_nested_fence_length_aware_no_leak():
    # [impl-review-fix CF-4] design.md 这类文档常用 4-反引号外层包 3-反引号内层
    # 示范锚。此前的单一 bool 翻转会在内层 3-``` 处误判"已跳出 fence"，把示范锚
    # 当真数据吃进；现按确切反引号长度处理，内层锚不应被漏出。
    text = ("正文\n"
            "````\n"                # 外层开：4 个反引号
            "示例(内层 3-``` 演示锚):\n"
            "```\n"                 # 内层开：3 个反引号（不构成外层闭合，3<4）
            + ANCHOR + "\n"
            "```\n"                 # 内层关：3 个反引号（同样不构成外层闭合）
            "````\n"                # 外层关：4 个反引号，真正闭合
            "正文2\n")
    lines = list(lma._fence_aware_lines(text))
    assert ANCHOR not in lines  # 内层锚不漏出
    assert "正文" in lines and "正文2" in lines  # fence 外内容仍正常产出


def test_illegal_numeric_value_flagged(tmp_path):
    # [impl-review-fix CF-5] "3.0" 是浮点串,不是契约要求的 int——此前 _int 静默
    # 吞成 0（采纳率算错），现须显式标 ⚠数值非法。
    _write(tmp_path, "c1", _a("domain", 5, "3.0", 2))
    rows, no_anchor, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    assert "⚠数值非法" in table


def test_negative_numeric_value_flagged(tmp_path):
    # [impl-review-fix CF-5] 负值同样违反契约 int≥0,此前会被原样求和(采纳率变负)。
    _write(tmp_path, "c2", _a("domain", 5, -1, 2))
    rows, no_anchor, _ = lma.aggregate(tmp_path / "archive")
    table = lma.render_table(rows, no_anchor)
    assert "⚠数值非法" in table

def test_unclosed_fence_swallows_trailing_anchors(tmp_path):
    # 诚实留档：奇数个 ``` （未闭合 fence）会把其后所有行都视为 fence 内，
    # 导致尾部锚被漏计（少计而非误取，方向偏保守，暂可接受）。
    anchor2 = _a("adversarial", 4, 2, 1)
    text = _a("domain", 5, 3, 2) + "\n```\n" + anchor2 + "\n"  # 只开未关
    p = tmp_path / "archive" / "c1"; p.mkdir(parents=True)
    (p / "code-review-report.md").write_text(text, encoding="utf-8")
    rows = lma.parse_report(p / "code-review-report.md")
    assert len(rows) == 1  # 第二个锚因未闭合 fence 被漏计,不是被误取
