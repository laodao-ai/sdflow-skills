"""devenv_lint 的测试。

【本文件的核心断言，只有一条】：

    lint 【永远退出 0】—— 哪怕十五个格子全是待定。

它拦的唯一东西是【坏 JSON】（人看不见：渲染不出来，用户只看到空白文档）。
「六槽留白」人一眼看得见 ⇒ 报，不拦（adr/0021：代价可见 > 机械拦截）。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import devenv_lint as L  # noqa: E402
import devenv_schema as S  # noqa: E402


def _lane(**over):
    lane = {
        "id": "hermetic",
        "layer": "unit",
        "status": "verified",
        "verification": {
            "method": "go test ./...",
            "executor": "script",
            "evidence": {"at_commit": "a" * 40, "at_time": "2026-07-14T10:23:00Z",
                         "exit": 0, "attested_by": "script"},
        },
        "source": "直接 go test",
        "deps": [],
    }
    lane.update(over)
    return lane


def _full():
    """六槽答满、一条泳道跑绿的数据。"""
    d = S.blank()
    for name in S.LAYERS:
        for slot in S.CONTENT_SLOTS:
            d["layers"][name][slot] = f"{name} 的 {slot} 已答"
    d["layers"]["unit"]["lane_ids"] = ["hermetic"]
    d["lanes"] = [_lane()]
    return d


# ---------- ⭐ 核心：只报不拦 ----------

def test_exit_zero_even_when_everything_is_pending(tmp_path, capsys):
    """⭐ 全待定 → 退出 0。

    这不是漏洞，是设计（adr/0021）。一个偷懒的运行技术上完全合规——
    但它【一眼就能看出是废纸】：横幅写着 15/15 待定。
    """
    S.save(tmp_path, S.blank())
    assert L.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "15/15 格待定" in out
    assert "尚不构成一份可用的测试策略" in out


def test_exit_zero_when_complete(tmp_path, capsys):
    S.save(tmp_path, _full())
    assert L.main(["--root", str(tmp_path)]) == 0
    assert "✅" in capsys.readouterr().out


def test_exit_zero_with_lazy_blockers(tmp_path, capsys):
    """敷衍的 blocked_by → 报出来，但【不拦】。"""
    d = _full()
    d["lanes"] = [_lane(id="x", status="scaffolded", blocked_by="TODO")]
    d["layers"]["unit"]["lane_ids"] = ["x"]
    del d["lanes"][0]["verification"]["evidence"]
    S.save(tmp_path, d)
    assert L.main(["--root", str(tmp_path)]) == 0
    assert "没告诉任何人下一步该干嘛" in capsys.readouterr().out


# ---------- 唯一 fail-closed：坏数据（人看不见）----------

def test_bad_json_is_fail_closed(tmp_path, capsys):
    """坏 JSON 渲染不出来，用户只会看到空白文档，还以为 skill 没跑 ⇒ 必须拦。"""
    p = tmp_path / S.DEVENV_REL
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    assert L.main(["--root", str(tmp_path)]) == 2
    assert "FAIL" in capsys.readouterr().err


def test_missing_file_is_fail_closed(tmp_path):
    assert L.main(["--root", str(tmp_path)]) == 2


def test_invalid_schema_is_fail_closed(tmp_path, capsys):
    """schema 不合法（如 status 拼错）⇒ 拦。人看不见 'verifed' 和 'verified' 的差别。"""
    import json
    d = _full()
    d["lanes"][0]["status"] = "verifed"
    p = tmp_path / S.DEVENV_REL
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert L.main(["--root", str(tmp_path)]) == 2
    assert "不合法" in capsys.readouterr().err


# ---------- 代价横幅（adr/0021 的落点）----------

def test_banner_none_when_complete():
    assert L.banner(_full()) is None


def test_banner_counts_pending():
    d = _full()
    d["layers"]["e2e"]["blind_spots"] = S.PENDING
    d["layers"]["e2e"]["how"] = S.PENDING
    b = L.banner(d)
    assert "2/15 格待定" in b
    assert "e2e 层缺 how, blind_spots" in b


def test_not_applicable_layer_is_out_of_the_denominator():
    """不适用的层，其六槽是豁免的 ⇒ 不该计入分母，否则永远「有待定」。"""
    d = _full()
    d["layers"]["e2e"] = {"status": S.NOT_APPLICABLE, "reason": "库无部署形态",
                          "consequence": "使用者用错 API 我们看不见"}
    assert L.total_slots(d) == 10          # unit 5 + integration 5
    assert L.banner(d) is None              # 其余全答满 ⇒ 无横幅


def test_pending_in_not_applicable_layer_is_not_counted():
    d = S.blank()
    d["layers"]["e2e"] = {"status": S.NOT_APPLICABLE, "reason": "r", "consequence": "c"}
    pend = L.pending_slots(d)
    assert all(layer != "e2e" for layer, _ in pend)
    assert len(pend) == 10                  # unit 5 + integration 5


# ---------- covers 差集：算出来是为了【问】，不是为了【拦】 ----------

def test_uncovered_contracts_listed_but_not_blocking(tmp_path, capsys):
    d = _full()
    d["lanes"][0]["covers"] = ["§5.2 消息运行时"]
    S.save(tmp_path, d)
    got = L.uncovered_contracts(d, ["§5.2 消息运行时", "§5.3 持久化"])
    assert got == ["§5.3 持久化"]
    # 而它出现在报告里，退出码仍是 0
    assert "§5.3 持久化" in L.report(d, ["§5.2 消息运行时", "§5.3 持久化"])
    assert L.main(["--root", str(tmp_path)]) == 0


# ---------- 报告呈现 ----------

def test_report_shows_verified_with_commit_anchor():
    """`verified` MUST 带 commit 锚 + 日期 —— MUST NOT 呈现为无条件的绿。"""
    r = L.report(_full())
    assert "aaaaaaa" in r          # at_commit[:7]
    assert "2026-07-14" in r


def test_report_marks_human_attested():
    """两种 verified 在文档里 MUST 可区分：脚本验的 vs 人说的。"""
    d = _full()
    d["lanes"][0]["verification"]["executor"] = "human"
    d["lanes"][0]["verification"]["evidence"]["attested_by"] = "human"
    assert "人工确认" in L.report(d)


def test_report_never_raises_on_weird_data():
    """报告是给人看的，MUST NOT 因为数据奇怪就崩 —— 崩了人就什么都看不到。"""
    L.report({"layers": {}, "lanes": [None, "x", {}]})


# ---------- environments.md 的待定计数 ----------

def test_env_pending_counted_but_not_blocking(tmp_path, capsys):
    """environments.md 的十槽也进代价横幅 —— 但同样【只报不拦】。"""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import devenv_scaffold as F
    (tmp_path / "openspec").mkdir()
    F.main(["init", "--root", str(tmp_path)])
    assert L.env_pending(tmp_path) == 10
    assert L.main(["--root", str(tmp_path)]) == 0        # ← 不拦
    out = capsys.readouterr().out
    assert "environments.md 还有 10/10 槽待定" in out
    assert "常见坑 · 回滚 · 构建副产物" in out             # 点名最贵的三槽


def test_env_pending_none_when_not_seeded(tmp_path):
    """没铺过 ⇒ 不报（不是「没填」，是「还没到那一步」）。"""
    assert L.env_pending(tmp_path) is None


def test_env_pending_counts_only_a_fixed_string(tmp_path):
    """⭐ 它【数一个固定字符串】，不切章节、不判结构（基准 5：语法面只有一个元素）。

    MUST NOT 演化成「找到 §1.5 这一节、切出内容、判断非空」——
    那是又一个手搓 Markdown 解析器（07 A20），会在 fence / 嵌套 / 变体标题上罢工。
    """
    p = tmp_path / L.ENV_MD
    p.parent.mkdir(parents=True)
    # 故意用最刁钻的 markdown：fence 里、嵌套列表里、奇怪标题下
    p.write_text(f"""# X
```
{S.PENDING}
```
- 嵌套
  - {S.PENDING}
##### 六级标题
{S.PENDING}
""", encoding="utf-8")
    assert L.env_pending(tmp_path) == 3     # 数得准，且不可能罢工
