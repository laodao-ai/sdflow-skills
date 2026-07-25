"""守 Codex efficacy 证据检查器 —— 每条门都要**真的会红**。

【为什么需要这个测试】
本检查器是「Codex efficacy=0 能不能关掉」的唯一机械判定点。**一个恒真的断言在这里
比没有断言更坏**：它会给一份不达标的证据盖上机械章（task5-review.md 的主线发现正是
「宣称有锚、实则假绿」）。∴ 每条门都配一条**反向变异**：把好证据改坏一处 → 必须红。

【与被测对象的关系】
检查器只做结构断言，输入是 JSON（stdlib 解析）⇒ 测试也只造 dict，不造 Markdown。
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_codex_efficacy_evidence as CE  # noqa: E402

SCRIPT = Path(CE.__file__).resolve()


def _site(name="design-voice", **over):
    site = {
        "site": name,
        "host": "codex",
        "runner": "claude",
        "model": "opus",
        "effort": "high",
        "reason_code": "ok",
        "job_id": "3d3695d5",
        "attempt_nonce": "4b85f30b20fcedb5c2de990fe46b9dbc",
        "dispatched_at": "2026-07-25T17:00:24Z",
        "started_at": "2026-07-25T17:00:25Z",
        "terminal_at": "2026-07-25T17:07:45Z",
        "collected_at": "2026-07-25T17:07:50Z",
        "duration_seconds": 440.0,
        "stdout_sha256": "a" * 64,
        "stdout_bytes": 4096,
        "stdout_lines": 60,
        "stderr_bytes": 0,
        "stderr_lines": 0,
    }
    site.update(over)
    return site


def _evidence(**over):
    ev = {
        "schema_version": 1,
        "layer": "spec-review",
        "repo": "zhws_ops_api",
        "change": "2026-07-25-manage-permission-catalog-items",
        "run_id": "20260725T170004Z-szMlwM",
        "host": "codex",
        "declared_sites": ["design-voice"],
        "sites": [_site()],
    }
    ev.update(over)
    return ev


# ── 对照组：好证据必须绿（否则下面所有「变异必红」都无意义）──────────────────

def test_a_good_evidence_passes():
    assert CE.verify(_evidence()) == []


def test_two_site_layer_passes():
    ev = _evidence(declared_sites=["design-voice", "hr-tg"],
                   sites=[_site(),
                          _site("hr-tg", job_id="7c1a9b02",
                                attempt_nonce="b" * 32,
                                terminal_at="2026-07-25T17:02:30Z",
                                collected_at="2026-07-25T17:02:35Z",
                                duration_seconds=125.0)])
    assert CE.verify(ev) == []


# ── G1：全部站点 host=codex / runner=claude / reason_code=ok ─────────────────

@pytest.mark.parametrize("field,bad", [
    ("host", "claude"),
    ("runner", "codex"),
    ("reason_code", "timeout"),
    ("reason_code", "exec-error"),
    ("reason_code", "fallback-unavailable"),
])
def test_g1_rejects_a_site_that_is_not_a_trusted_cross_model_success(field, bad):
    ev = _evidence(sites=[_site(**{field: bad})])
    assert any(field in f for f in CE.verify(ev))


def test_g1_rejects_when_one_of_two_sites_degraded():
    """一个 ok、一个降级 ⇒ 整层不达标（「全部站点」不是「至少一个」）。"""
    ev = _evidence(declared_sites=["design-voice", "hr-tg"],
                   sites=[_site(),
                          _site("hr-tg", reason_code="timeout")])
    assert CE.verify(ev)


def test_g1_rejects_a_missing_declared_site():
    """declared 两个、只落一个证据 ⇒ 红（HAE-09 per-site 完整性）。"""
    ev = _evidence(declared_sites=["design-voice", "hr-tg"], sites=[_site()])
    assert any("declared_sites 与实落证据站点集不等" in f for f in CE.verify(ev))


def test_g1_rejects_an_undeclared_extra_site():
    """反方向也要红：证据里多出一个没 declared 的站点。"""
    ev = _evidence(declared_sites=["design-voice"],
                   sites=[_site(), _site("hr-tg")])
    assert any("declared_sites 与实落证据站点集不等" in f for f in CE.verify(ev))


def test_empty_declared_sites_is_not_green():
    """空集会让 all() 恒真 —— MUST NOT 报绿。"""
    ev = _evidence(declared_sites=[], sites=[_site()])
    assert CE.verify(ev)


def test_empty_sites_is_not_green():
    ev = _evidence(sites=[])
    assert CE.verify(ev)


def test_duplicate_sites_rejected():
    ev = _evidence(declared_sites=["design-voice"], sites=[_site(), _site()])
    assert any("重复站点" in f for f in CE.verify(ev))


def test_top_level_host_must_be_codex():
    """本证据只对 Codex 宿主有意义 —— Claude 宿主的成功不能关这个缺口。"""
    ev = _evidence(host="claude", sites=[_site(host="claude", runner="codex")])
    assert CE.verify(ev)


# ── G2：至少一个自然 >300 秒的 opus+high 成功站点 ────────────────────────────

def test_g2_rejects_when_every_site_is_short():
    ev = _evidence(sites=[_site(terminal_at="2026-07-25T17:04:00Z",
                                collected_at="2026-07-25T17:04:05Z",
                                duration_seconds=215.0)])
    assert any("G2 未达标" in f for f in CE.verify(ev))


def test_g2_boundary_is_strictly_greater_than_300():
    """恰好 300 秒证不出「跨过」旧天花板 ⇒ 红；301 秒 ⇒ 绿。"""
    at_ceiling = _evidence(sites=[_site(terminal_at="2026-07-25T17:05:25Z",
                                        collected_at="2026-07-25T17:05:30Z",
                                        duration_seconds=300.0)])
    assert any("G2 未达标" in f for f in CE.verify(at_ceiling))

    over = _evidence(sites=[_site(terminal_at="2026-07-25T17:05:26Z",
                                  collected_at="2026-07-25T17:05:30Z",
                                  duration_seconds=301.0)])
    assert CE.verify(over) == []


@pytest.mark.parametrize("field,bad", [("model", "sonnet"), ("effort", "medium")])
def test_g2_requires_the_long_site_to_be_strong_model_high_effort(field, bad):
    """>300 秒但不是 opus/high ⇒ 证不出「强模型跨过天花板」。"""
    ev = _evidence(sites=[_site(**{field: bad})])
    assert any("G2 未达标" in f for f in CE.verify(ev))


def test_g2_is_not_satisfied_by_a_degraded_long_site():
    """跑满 900 秒然后 timeout 的站点 MUST NOT 顶替成功证据。"""
    ev = _evidence(sites=[_site(reason_code="timeout",
                                terminal_at="2026-07-25T17:15:25Z",
                                collected_at="2026-07-25T17:15:30Z",
                                duration_seconds=900.0)])
    fails = CE.verify(ev)
    assert any("G2 未达标" in f for f in fails)


# ── G3：字段可机读（时刻 / duration / digest）───────────────────────────────

@pytest.mark.parametrize("bad", [
    "2026-07-25 17:07:45", "2026-07-25T17:07:45+00:00", "1784969329", "", None,
])
def test_g3_rejects_unparseable_timestamps(bad):
    ev = _evidence(sites=[_site(terminal_at=bad)])
    assert any("terminal_at" in f for f in CE.verify(ev))


def test_g3_rejects_out_of_order_timestamps():
    """terminal 早于 started ⇒ 红。"""
    ev = _evidence(sites=[_site(started_at="2026-07-25T17:07:45Z",
                                terminal_at="2026-07-25T17:00:25Z")])
    assert any("次序颠倒" in f for f in CE.verify(ev))


def test_g3_rejects_duration_inconsistent_with_the_timestamps():
    """把 440 秒的跑写成 620 秒 ⇒ 与两端时刻不自洽 ⇒ 红。

    这是「自然耗时」的防伪核心：duration 不是自由字段，它 MUST 由两个时刻夹住。
    """
    ev = _evidence(sites=[_site(duration_seconds=620.0)])
    assert any("不自洽" in f for f in CE.verify(ev))


def test_g3_rejects_a_short_run_relabelled_as_long():
    """把 120 秒的真跑标成 400 秒（时刻没改）⇒ 红，且 G2 不因此达标。"""
    ev = _evidence(sites=[_site(terminal_at="2026-07-25T17:02:25Z",
                                collected_at="2026-07-25T17:02:30Z",
                                duration_seconds=400.0)])
    assert any("不自洽" in f for f in CE.verify(ev))


@pytest.mark.parametrize("bad", [0, -1, "440", None, True])
def test_g3_rejects_bad_duration_types(bad):
    ev = _evidence(sites=[_site(duration_seconds=bad)])
    assert CE.verify(ev)


@pytest.mark.parametrize("bad", ["A" * 64, "a" * 63, "", None, "z" * 64])
def test_g3_rejects_bad_stdout_digest(bad):
    ev = _evidence(sites=[_site(stdout_sha256=bad)])
    assert any("stdout_sha256" in f for f in CE.verify(ev))


def test_g3_rejects_empty_stdout():
    """rc=0 但 stdout 空 —— 不得猜成功（OVBG-02）。"""
    ev = _evidence(sites=[_site(stdout_bytes=0)])
    assert any("stdout_bytes" in f for f in CE.verify(ev))


def test_g3_rejects_zero_stdout_lines():
    ev = _evidence(sites=[_site(stdout_lines=0)])
    assert any("stdout_lines" in f for f in CE.verify(ev))


def test_stderr_counters_may_be_zero_but_must_be_integers():
    assert CE.verify(_evidence(sites=[_site(stderr_bytes=0, stderr_lines=0)])) == []
    assert CE.verify(_evidence(sites=[_site(stderr_bytes="0")]))


# ── 第四条：证据里 MUST NOT 有 context / stderr 正文 ─────────────────────────

def test_extra_site_key_is_rejected():
    """白名单是封闭集合 —— `stderr_text` 这种字段根本没有落脚点。"""
    ev = _evidence(sites=[_site(**{})])
    ev["sites"][0]["stderr_text"] = "panic: something"
    assert any("白名单外的 key" in f for f in CE.verify(ev))


def test_extra_top_level_key_is_rejected():
    ev = _evidence()
    ev["context"] = "……评审 context 正文……"
    assert any("白名单外的 key" in f for f in CE.verify(ev))


def test_missing_site_key_is_rejected():
    ev = _evidence()
    del ev["sites"][0]["stdout_sha256"]
    assert any("缺字段" in f for f in CE.verify(ev))


def test_missing_top_level_key_is_rejected():
    ev = _evidence()
    del ev["run_id"]
    assert any("缺字段" in f for f in CE.verify(ev))


def test_multiline_string_anywhere_is_rejected():
    """换行 = 正文的形状。合法字段里也不许有。"""
    ev = _evidence(sites=[_site(job_id="3d3695d5\nTraceback (most recent call last):")])
    assert any("换行" in f for f in CE.verify(ev))


# 一段「正文尺寸」的绝对字面量。用绝对值而不是 `MAX_STRING_LEN + 1`：后者随常量一起
# 缩放 ⇒ 把上界放到 10**9 时断言依然绿（**恒真锚**）。这里钉死「4096 字符的东西一定
# 是正文，不许进证据」。
PROSE_SIZED = "x" * 4096


def test_overlong_string_anywhere_is_rejected():
    assert any("长度" in f for f in CE.verify(_evidence(change=PROSE_SIZED)))


def test_scalar_guard_reaches_into_lists():
    ev = _evidence(declared_sites=["design-voice", PROSE_SIZED])
    assert any("长度" in f for f in CE.verify(ev))


def test_overlong_boundary_is_at_the_declared_constant():
    """恰好 MAX_STRING_LEN 绿、+1 红 —— 边界落在契约常量上。"""
    assert CE.verify(_evidence(change="x" * CE.MAX_STRING_LEN)) == []
    assert CE.verify(_evidence(change="x" * (CE.MAX_STRING_LEN + 1)))


# ── emit：证据从 collected witness 机械派生，不手抄 ──────────────────────────

def _write_collected(run_dir, site, **over):
    payload = {
        "schema_version": 1, "run_id": "20260725T170004Z-szMlwM",
        "site": site, "host": "codex", "runner": "claude", "model": "opus",
        "effort": "high", "reason_code": "ok", "job_id": "3d3695d5",
        "attempt_nonce": "4b85f30b20fcedb5c2de990fe46b9dbc",
        "dispatched_at": "2026-07-25T17:00:24Z",
        "started_at": "2026-07-25T17:00:25Z",
        "terminal_at": "2026-07-25T17:07:45Z",
        "collected_at": "2026-07-25T17:07:50Z",
        "duration_seconds": 440.0, "stdout_sha256": "a" * 64,
        "stdout_bytes": 4096, "stdout_lines": 60,
        "stderr_bytes": 0, "stderr_lines": 0,
        # collect 真实 payload 里还有这些 —— emit MUST 把它们挡在证据之外
        "stdout_path": str(Path(run_dir) / f"{site}.stdout"),
        "detail": "rc=0 且 stdout 非空",
        "state": "SUCCEEDED", "terminal": True, "ok": True, "rc": 0,
    }
    payload.update(over)
    (Path(run_dir) / f"{site}.collected.json").write_text(
        json.dumps(payload), encoding="utf-8")


def test_emit_drops_non_whitelisted_collect_fields(tmp_path):
    """collect 的 `detail` / `stdout_path` / `state` 一律不进证据。"""
    _write_collected(tmp_path, "design-voice")
    ev = CE.emit(str(tmp_path), "codex", "spec-review", "zhws_ops_api",
                 "some-change", ["design-voice"])
    assert set(ev["sites"][0]) == set(CE.SITE_KEYS)
    assert CE.verify(ev) == []


def test_emit_does_not_invent_missing_fields(tmp_path):
    """collect 里缺 digest ⇒ emit 搬 None ⇒ verify 报红，MUST NOT 兜底成好看的默认值。"""
    _write_collected(tmp_path, "design-voice")
    data = json.loads((tmp_path / "design-voice.collected.json").read_text())
    del data["stdout_sha256"]
    (tmp_path / "design-voice.collected.json").write_text(json.dumps(data))
    ev = CE.emit(str(tmp_path), "codex", "spec-review", "r", "c", ["design-voice"])
    assert ev["sites"][0]["stdout_sha256"] is None
    assert any("stdout_sha256" in f for f in CE.verify(ev))


def test_emit_carries_a_degraded_site_verbatim_so_the_gate_can_red(tmp_path):
    """降级站点的 reason_code 原样搬进证据 ⇒ G1 必红（emit MUST NOT 帮着美化）。"""
    _write_collected(tmp_path, "design-voice", reason_code="timeout")
    ev = CE.emit(str(tmp_path), "codex", "spec-review", "r", "c", ["design-voice"])
    assert ev["sites"][0]["reason_code"] == "timeout"
    assert CE.verify(ev)


def test_emit_fills_host_from_the_cli_because_collect_has_no_such_field(tmp_path):
    """collect payload **没有** `host` —— helper 不知道自己被哪个宿主调用。

    ∴ 它只能来自 `--host` 入参（诚实边界）。这条同时守住「emit 别把 host 留成 None
    让证据永远红」和「别把它偷偷写死成 codex」。
    """
    _write_collected(tmp_path, "design-voice")
    raw = json.loads((tmp_path / "design-voice.collected.json").read_text())
    del raw["host"]
    (tmp_path / "design-voice.collected.json").write_text(json.dumps(raw))

    ev = CE.emit(str(tmp_path), "codex", "spec-review", "r", "c", ["design-voice"])
    assert ev["sites"][0]["host"] == "codex"
    assert CE.verify(ev) == []


def test_emit_with_a_non_codex_host_is_rejected_by_the_gate(tmp_path):
    """Claude 宿主下跑出来的成功 **不能**顶替 Codex efficacy 证据 —— 门必须红。"""
    _write_collected(tmp_path, "design-voice")
    ev = CE.emit(str(tmp_path), "claude", "spec-review", "r", "c", ["design-voice"])
    assert ev["host"] == "claude" and ev["sites"][0]["host"] == "claude"
    assert any("host" in f for f in CE.verify(ev))


def test_emit_fails_loud_when_a_declared_site_has_no_witness(tmp_path):
    """declared 了却没 collected witness ⇒ emit 非零退出，MUST NOT 悄悄少一个站点。"""
    _write_collected(tmp_path, "design-voice")
    with pytest.raises(CE.EvidenceError):
        CE.emit(str(tmp_path), "codex", "spec-review", "r", "c",
                ["design-voice", "hr-tg"])


# ── CLI 契约 ────────────────────────────────────────────────────────────────

def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, encoding="utf-8")


def test_cli_check_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_evidence()), encoding="utf-8")
    assert _run("check", "--evidence", str(good)).returncode == 0

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_evidence(sites=[_site(reason_code="timeout")])),
                   encoding="utf-8")
    r = _run("check", "--evidence", str(bad))
    assert r.returncode == 1
    assert "保留 T162" in r.stderr

    assert _run("check", "--evidence", str(tmp_path / "nope.json")).returncode == 2

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert _run("check", "--evidence", str(broken)).returncode == 2


def test_cli_emit_then_check_roundtrip(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_collected(run_dir, "design-voice")
    out = tmp_path / "evidence.json"
    r = _run("emit", "--run-dir", str(run_dir), "--host", "codex",
             "--layer", "spec-review", "--repo", "zhws_ops_api",
             "--change", "c", "--declared-sites", "design-voice",
             "--out", str(out))
    assert r.returncode == 0, r.stderr
    assert _run("check", "--evidence", str(out)).returncode == 0


def test_cli_emit_rejects_empty_declared_sites(tmp_path):
    r = _run("emit", "--run-dir", str(tmp_path), "--host", "codex",
             "--layer", "spec-review", "--repo", "r", "--change", "c",
             "--declared-sites", " , ", "--out", str(tmp_path / "e.json"))
    assert r.returncode == 2


def test_constants_are_the_only_copy_of_the_thresholds():
    """门限只有一份 —— 改契约就改这里，别在测试里再钉一次语义。"""
    assert CE.MIN_NATURAL_DURATION_SECONDS == 300.0
    assert CE.REQUIRED_HOST == "codex"
    assert CE.REQUIRED_RUNNER == "claude"
    assert CE.REQUIRED_MODEL == "opus"
    assert CE.REQUIRED_EFFORT == "high"
    assert CE.MAX_STRING_LEN == 256
    assert CE.DURATION_CONSISTENCY_TOLERANCE_SECONDS == 1.0


def test_site_key_whitelist_has_no_free_text_field():
    """白名单里 MUST NOT 出现任何能装正文的字段（这是「不含 context/stderr」的定义）。"""
    forbidden = {"detail", "stdout", "stderr", "stdout_text", "stderr_text",
                 "context", "stdout_path", "findings", "output", "log"}
    assert CE.SITE_KEYS & forbidden == frozenset()
    assert CE.TOP_LEVEL_KEYS & forbidden == frozenset()


def test_verify_is_pure(tmp_path):
    """verify MUST NOT 改输入（报告会把同一份 dict 再序列化落盘）。"""
    ev = _evidence()
    snapshot = copy.deepcopy(ev)
    CE.verify(ev)
    assert ev == snapshot
