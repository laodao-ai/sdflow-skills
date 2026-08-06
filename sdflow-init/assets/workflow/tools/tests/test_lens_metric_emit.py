import subprocess, sys, json, importlib.util, pytest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "lens_metric_emit.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"

def _mod():
    spec = importlib.util.spec_from_file_location("lens_metric_emit", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_load_enums_real_contract():
    e = _mod().load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain","adversarial","grounding","history","outside-voice","broad"}
    assert e["host"] == {"claude","codex","unknown"}                       # add-codex-host-support
    assert e["runner"] == {"claude","codex","none","unknown"}              # add-codex-host-support
    assert e["sev_levels"] == ("致","高","中","低")
    assert e["sev_re"].match("致1/高2/中0/低3") and not e["sev_re"].match("致1/高2/中0")

def test_load_fold_real_contract():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert fold["对抗镜1"] == "adversarial" and fold["codex"] == "outside-voice"
    assert fold["claude"] == "outside-voice"                  # add-codex-host-support：反向路径新增映射
    assert all(v in e["lens"] for v in fold.values())        # codomain ⊆ lens enum
    assert "domain" not in fold                              # 恒等项不列块

def test_load_enums_missing_block(tmp_path):
    m = _mod(); bad = tmp_path/"c.md"; bad.write_text("# no blocks", encoding="utf-8")
    with pytest.raises(m.EmitError): m.load_enums(bad)

def test_load_block_unclosed_fence_fail_closed(tmp_path):
    m = _mod(); bad = tmp_path/"c.md"
    bad.write_text("```lens-metric-enums\nlayer: spec-review,code-review\n", encoding="utf-8")  # 无闭合围栏
    with pytest.raises(m.EmitError):
        m.load_enums(bad)

def test_load_fold_dup_key_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n对抗镜1: adversarial\n对抗镜1: broad\n```\n", encoding="utf-8")
    with pytest.raises(m.EmitError): m.load_fold(c, e)

def test_load_fold_codomain_out_of_enum_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n某镜: newlens\n```\n", encoding="utf-8")
    with pytest.raises(m.EmitError): m.load_fold(c, e)

# --- fold_hit: 行键升维 (lens,host,runner,site)。host 为调用方 --host 单一源，非 hit 自带 ---

def test_fold_hit_identity_passthrough():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"domain"}, "claude", e, f) == ("domain","claude","claude","—")

def test_fold_hit_nonidentity_map():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"对抗镜2"}, "claude", e, f) == ("adversarial","claude","claude","—")

def test_fold_hit_non_ov_runner_tracks_host_not_hardcoded_claude():
    # add-codex-host-support：非-ov runner 取当前 --host，host=codex 时 runner 同为 codex（非硬编码 claude）
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"domain"}, "codex", e, f) == ("domain","codex","codex","—")

def test_fold_hit_host_unknown_ordinary_runner_unknown():
    # 契约：unknown 仅合法于非-ov 普通镜行 ∧ host=unknown——两者同值
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"broad"}, "unknown", e, f) == ("broad","unknown","unknown","—")

def test_fold_hit_outside_voice_needs_runner_site():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"codex","runner":"codex","site":"hr-tg"}, "claude", e, f) == \
        ("outside-voice","claude","codex","hr-tg")            # host=claude(主审)、runner=codex(跨模型 voice)
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex"}, "claude", e, f)      # 缺 runner/site

def test_fold_hit_ov_runner_none_fail_closed():
    # 复评 Critical fix：hit 级 runner="none" MUST fail-closed（NOT legal）——"none"=无执行只对 roster 行合法，
    # hit 代表实际报出的 finding，蕴含该 voice 真跑过，不可能 runner=none。
    # （此前 test_fold_hit_ov_runner_none_legal 把这条锁成了"合法"，方向锁反了，本次改正断言方向。）
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError):
        m.fold_hit({"raw":"codex","runner":"none","site":"hr-tg"}, "unknown", e, f)

def test_fold_hit_ov_runner_unknown_fail_closed():
    # outside-voice 行 runner 域收紧至 {claude,codex,none}，不取 unknown（矩阵约束，契约「跨模型性」段）
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError):
        m.fold_hit({"raw":"codex","runner":"unknown","site":"hr-tg"}, "unknown", e, f)

def test_fold_hit_unknown_raw_fail_closed_not_broad():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"神秘镜"}, "claude", e, f)     # SR-E 不塞 broad

def test_fold_hit_scope_audit_maps_to_broad():
    # absorb-gstack-review：code-review Step1 自持 scope 审计的原始镜名 scope-audit 折叠到 broad
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"scope-audit"}, "claude", e, f) == ("broad","claude","claude","—")

def test_fold_hit_gstack_adv_no_longer_recognized():
    # absorb-gstack-review：gstack-adv→broad 行已被 scope-audit→broad 替换（不共存），
    # 旧 raw 名 gstack-adv 现应 fail-closed 而非静默折叠——回归防止两者共存
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert "gstack-adv" not in f
    with pytest.raises(m.EmitError):
        m.fold_hit({"raw":"gstack-adv"}, "claude", e, f)

def test_fold_hit_unknown_raw_error_mentions_update_hint():
    # 未知 raw 镜名报错须带可操作指引——这是「SKILL 已更新、消费仓 bundle 未更新」的第一现场，
    # 报错文案须含「若本仓 openspec/workflow/ 为旧版，请先跑 sdflow-init update」
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError) as exc_info:
        m.fold_hit({"raw":"gstack-adv"}, "claude", e, f)
    assert "sdflow-init update" in str(exc_info.value)
    assert "openspec/workflow/" in str(exc_info.value)

def test_fold_hit_site_injection_fail_closed():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex","runner":"codex","site":'a"b'}, "claude", e, f)

def test_fold_hit_raw_unhashable_fail_closed():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError):
        m.fold_hit({"raw":["broad"]}, "claude", e, f)               # raw 非字符串（unhashable）→ 干净 EmitError 非裸 TypeError

def test_fold_hit_ov_site_non_str_fail_closed():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    with pytest.raises(m.EmitError):
        m.fold_hit({"raw":"codex","runner":"codex","site":["x"]}, "claude", e, f)   # site 非字符串 → 先类型后注入拦截

def _ef():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e); return m, e, f

def test_reduce_single_accepted():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"design-voice"}]
    findings = [{"hits":[{"raw":"domain"}], "verdict":"采纳", "sev":"高"}]
    lines = m.reduce(roster, findings, "spec-review", "claude", e, f)
    dom = [l for l in lines if 'lens="domain"' in l][0]
    assert 'host="claude"' in dom and 'findings="1"' in dom and '采纳="1"' in dom and '独立="1"' in dom
    assert 'sev="致0/高1/中0/低0"' in dom
    # 零-finding 行全零
    ov = [l for l in lines if 'lens="outside-voice"' in l][0]
    assert 'host="claude"' in ov and 'runner="codex"' in ov
    assert 'findings="0"' in ov and 'sev="致0/高0/中0/低0"' in ov and 'site="design-voice"' in ov

def test_reduce_scope_audit_raw_folds_to_broad_anchor():
    # absorb-gstack-review：code-review Step1 自持 scope 审计上报 raw="scope-audit"，
    # emitter 归约后 MUST 落在 roster 的 canonical lens="broad" 行（下游 retro 聚合/MIN_LENS_ROWS 零感知）
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"design-voice"}]
    findings = [{"hits":[{"raw":"scope-audit"}], "verdict":"采纳", "sev":"中"}]
    lines = m.reduce(roster, findings, "code-review", "claude", e, f)
    broad = [l for l in lines if 'lens="broad"' in l][0]
    assert 'findings="1"' in broad and '采纳="1"' in broad and '独立="1"' in broad
    assert 'sev="致0/高0/中1/低0"' in broad

def test_reduce_coreport_no_independent():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"},
              {"lens":"broad","runner":"claude","site":"—"}]
    findings = [{"hits":[{"raw":"domain"},{"raw":"codex","runner":"codex","site":"hr-tg"}],
                 "verdict":"采纳","sev":"中"}]
    lines = m.reduce(roster, findings, "spec-review", "claude", e, f)
    for lens in ("domain","outside-voice"):
        row = [l for l in lines if f'lens="{lens}"' in l][0]
        assert '采纳="1"' in row and '独立="0"' in row     # 共抓：各记采纳、均不独立

def test_reduce_same_type_multi_instance_independent():
    m, e, f = _ef()
    roster = [{"lens":"adversarial","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    findings = [{"hits":[{"raw":"对抗镜1"},{"raw":"对抗镜2"}], "verdict":"采纳","sev":"致"}]
    adv = [l for l in m.reduce(roster, findings, "spec-review", "claude", e, f) if 'lens="adversarial"' in l][0]
    assert '采纳="1"' in adv and '独立="1"' in adv and 'sev="致1/高0/中0/低0"' in adv

def _base_roster():
    return [{"lens":"broad","runner":"claude","site":"—"},
            {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]

def test_reduce_empty_hits_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[], "verdict":"采纳","sev":"高"}], "spec-review", "claude", e, f)

def test_reduce_accepted_missing_sev_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"采纳"}], "spec-review", "claude", e, f)

def test_reduce_bad_verdict_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"通过","sev":"高"}], "spec-review", "claude", e, f)

def test_reduce_bad_layer_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [], "review", "claude", e, f)

def test_reduce_finding_lens_not_in_roster_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # C4：domain 不在 roster
        m.reduce(_base_roster(), [{"hits":[{"raw":"domain"}], "verdict":"采纳","sev":"高"}], "spec-review", "claude", e, f)

def test_reduce_roster_missing_mandatory_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # 缺 outside-voice
        m.reduce([{"lens":"broad","runner":"claude","site":"—"}], [], "spec-review", "claude", e, f)

def test_reduce_roster_dup_key_fail_closed():
    m, e, f = _ef()
    r = _base_roster() + [{"lens":"broad","runner":"claude","site":"—"}]
    with pytest.raises(m.EmitError):
        m.reduce(r, [], "spec-review", "claude", e, f)


def test_reduce_roster_site_non_str_fail_closed():
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":123},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "claude", e, f)

def test_reduce_roster_lens_unhashable_fail_closed():
    m, e, f = _ef()
    roster = [{"lens":["broad"],"runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "claude", e, f)

def test_reduce_non_ov_wrong_runner_site_fail_closed():
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"codex","site":"x"},          # 幽灵行：非 ov 却 runner/site 越出强制归约
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "claude", e, f)

def test_reduce_non_ov_runner_ne_host_fail_closed():
    # add-codex-host-support：非-ov 行键 runner 须严格等于 --host；此处 runner="claude" 但 --host="codex"
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "codex", e, f)

def test_reduce_rejected_illegal_sev_fail_closed():
    m, e, f = _ef()
    findings = [{"hits":[{"raw":"broad"}], "verdict":"裁掉", "sev":"严重"}]  # 非法 sev 级，即便非采纳也 fail-closed
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), findings, "spec-review", "claude", e, f)


# --- add-codex-host-support：--host 单一源（缺失/越域受控 fail-closed，MUST NOT 默认 claude）---

def test_reduce_host_out_of_domain_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [], "spec-review", "claude-fallback", e, f)    # 已废弃值

def test_reduce_ov_runner_none_legal_all_zero():
    # D6：outside-voice 行 runner="none"（host-unknown/secret-hit 的无执行轮次）合法且恒全零
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"unknown","site":"—"},
              {"lens":"outside-voice","runner":"none","site":"hr-tg"}]
    lines = m.reduce(roster, [], "spec-review", "unknown", e, f)
    ov = [l for l in lines if 'lens="outside-voice"' in l][0]
    assert 'runner="none"' in ov and 'findings="0"' in ov and '采纳="0"' in ov and '独立="0"' in ov
    assert 'sev="致0/高0/中0/低0"' in ov

def test_reduce_non_ov_runner_none_fail_closed():
    # runner="none" 只对 outside-voice 行合法——非-ov 行必须 runner==host，host 从不取 "none"
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"none","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "claude", e, f)

def test_reduce_ov_roster_runner_unknown_fail_closed():
    # outside-voice roster 行 runner 越出收紧域 {claude,codex,none}（不取 unknown）
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"unknown","site":"—"},
              {"lens":"outside-voice","runner":"unknown","site":"hr-tg"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, [], "spec-review", "unknown", e, f)

def test_reduce_ov_hit_runner_none_fail_closed_not_counted():
    # 复评 Critical repro：roster 有合法 (outside-voice,none,hr-tg) 零执行行 + 一条 hits runner="none" 的
    # verdict=采纳 finding——修前会被 fold_hit 接受、折进该零执行行，把它的 findings/采纳/独立 顶到非零，
    # 破 spec「runner="none" 行恒全零」不变量。修后 MUST fail-closed（NOT 产出 findings="1"）。
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"unknown","site":"—"},
              {"lens":"outside-voice","runner":"none","site":"hr-tg"}]
    findings = [{"hits":[{"raw":"codex","runner":"none","site":"hr-tg"}], "verdict":"采纳","sev":"高"}]
    with pytest.raises(m.EmitError):
        m.reduce(roster, findings, "spec-review", "unknown", e, f)

def test_reduce_host_unknown_ordinary_runner_unknown_emits():
    # codex#1：host=unknown 时普通镜行 runner 如实为 unknown（非崩、非默认 claude）
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"unknown","site":"—"},
              {"lens":"outside-voice","runner":"none","site":"hr-tg"}]
    lines = m.reduce(roster, [], "spec-review", "unknown", e, f)
    broad = [l for l in lines if 'lens="broad"' in l][0]
    assert 'host="unknown"' in broad and 'runner="unknown"' in broad


def _run(inp_path, layer="spec-review", host="claude", extra_args=None):
    args = [sys.executable, str(SCRIPT), "--layer", layer, "--input", str(inp_path)]
    if host is not None:
        args += ["--host", host]
    if extra_args:
        args += extra_args
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_cli_valid_emits(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}], "verdict":"采纳","sev":"高"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 0
    assert r.stdout.count("<!-- sdflow:lens-metric v1") == 2
    assert 'host="claude"' in r.stdout


def test_cli_bad_json_exit1_no_stdout(tmp_path):
    inp = tmp_path/"in.json"; inp.write_text("{not json", encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout and r.stderr.strip()


def test_cli_partial_fail_no_partial_anchor(tmp_path):
    # 第 2 条 finding 坏（采纳缺 sev）→ 全失败、stdout 无任何锚（all-or-nothing）
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"},
                    {"hits":[{"raw":"broad"}],"verdict":"采纳"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout


def test_cli_idempotent_cross_process(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"domain","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"domain"}],"verdict":"采纳","sev":"中"}]}, ensure_ascii=False), encoding="utf-8")
    import os
    env0 = dict(os.environ, PYTHONHASHSEED="0"); env1 = dict(os.environ, PYTHONHASHSEED="1")
    a = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--host","claude","--input",str(inp)],
                       capture_output=True, text=True, env=env0, encoding="utf-8", errors="replace").stdout
    b = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--host","claude","--input",str(inp)],
                       capture_output=True, text=True, env=env1, encoding="utf-8", errors="replace").stdout
    assert a == b and a.count("lens-metric v1") == 3      # 跨 hashseed 字节一致


def test_cli_null_roster_clean_fail(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text('{"roster": null, "findings": []}', encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--host","claude","--input",str(inp)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 1 and r.stdout == "" and "FAIL" in r.stderr and "Traceback" not in r.stderr


def test_cli_non_str_field_clean_fail(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":123}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "Traceback" not in r.stderr and "FAIL" in r.stderr


# --- add-codex-host-support · Scenario「缺 --host 或取值越域则受控 fail-closed（非 argparse 崩）」D4/D12 ---

def test_cli_missing_host_controlled_fail_closed_not_argparse_crash(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp, host=None)                                        # 不传 --host
    assert r.returncode == 1                                        # 受控 fail-closed（EXIT_FAIL），非 argparse exit(2)
    assert r.returncode != 2
    assert r.stdout == "" and "Traceback" not in r.stderr
    assert "host" in r.stderr and "FAIL" in r.stderr                # 可读错误消息报明原因

def test_cli_missing_host_does_not_default_to_claude(tmp_path):
    # MUST NOT 默认填 claude：缺 --host 时即便 roster 恰好是纯 claude 行键，仍须 fail-closed 而非静默按 claude 通过
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp, host=None)
    assert r.returncode == 1 and r.stdout == ""                     # 若默认填 claude 会 exit0 产出锚，此处必须不产出

def test_cli_host_out_of_domain_fail_closed(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp, host="claude-fallback")                           # 已废弃值
    assert r.returncode == 1 and r.stdout == "" and "Traceback" not in r.stderr and "host" in r.stderr

def test_cli_host_unknown_accepted(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"unknown","site":"—"},
                  {"lens":"outside-voice","runner":"none","site":"hr-tg"}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp, host="unknown")
    assert r.returncode == 0 and 'host="unknown"' in r.stdout and 'runner="unknown"' in r.stdout

def test_cli_extras_fail_closed_not_silently_swallowed(tmp_path):
    # D12：parse_known_args 后 if extras: fail-closed——拼错/多余参数不得静默吞
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp, extra_args=["--laye", "spec-review"])              # 拼写错误的多余参数
    assert r.returncode == 1 and r.returncode != 2
    assert r.stdout == "" and "Traceback" not in r.stderr
    assert "laye" in r.stderr or "无法识别" in r.stderr


# --- 产出↔校验/聚合一致性守卫（跨模块单一源；importlib 加载真实模块，非脚本 import） ---

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm); return mm

AL = TOOLS / "anchor_lint.py"
# repo_root/sdflow-retro/scripts/lens_metric_aggregate.py — TOOLS =
# .../sdflow-init/assets/workflow/tools，需 4 层 .parent 才到 repo root
# （brief 草稿写 3 层算错，落到 sdflow-init/sdflow-retro/... 不存在；已按真实目录改正）。
AGG = TOOLS.parent.parent.parent.parent / "sdflow-retro" / "scripts" / "lens_metric_aggregate.py"

def test_emit_then_check_lens_metric_clean(tmp_path):
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    lines = m.reduce(roster, [{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"}], "spec-review", "claude", e, f)
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    report = "\n".join(lines) + "\n"
    assert al.check_lens_metric(report, "spec-review", enums) == []   # 无违规（C5 精确口径）

def test_emit_then_check_lens_metric_clean_host_codex():
    # 面治：host≠claude（codex 宿主自身跑普通镜）+ 反向 outside-voice（runner=claude）同样须过 anchor_lint 无违规
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"codex","site":"—"},
              {"lens":"outside-voice","runner":"claude","site":"hr-tg"}]
    lines = m.reduce(roster, [{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"}], "spec-review", "codex", e, f)
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    report = "\n".join(lines) + "\n"
    assert al.check_lens_metric(report, "spec-review", enums) == []

def test_load_enums_equivalence():
    m = _mod(); al = _load("anchor_lint", AL)
    me, ae = m.load_enums(CONTRACT), al.load_enums(CONTRACT)
    for k in ("layer","lens","host","runner"):        # add-codex-host-support：host 加入逐字段等价守卫（C10 面治）
        assert me[k] == ae[k]
    assert me["sev_re"].pattern == ae["sev_re"].pattern       # C10 逐字段等价

def test_fold_codomain_subset_lens_enum():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert set(fold.values()) <= e["lens"]                   # C3

def test_aggregator_enum_matches_contract():
    m = _mod(); e = m.load_enums(CONTRACT); agg = _load("lens_metric_aggregate", AGG)
    assert agg.LENS_ENUM == e["lens"] and agg.LAYER_ENUM == e["layer"]   # C23

def test_min_lens_rows_matches_anchor_lint():
    m = _mod(); al = _load("anchor_lint", AL)
    assert set(m.MANDATORY_LENS) == set(al.MIN_LENS_ROWS)     # C17 分叉①=B


# --- golden fixture（两审 SKILL 落锚步引用的 schema 样例，emitter 吃它须 exit0 且过 anchor_lint） ---

FIX = TOOLS / "tests" / "fixtures" / "lens_metric_input.json"

def test_golden_fixture_emits_and_lints(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "--layer", "spec-review", "--host", "claude", "--input", str(FIX)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and r.stdout.count("lens-metric v1") >= 2
    assert 'host="claude"' in r.stdout
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    assert al.check_lens_metric(r.stdout + "\n", "spec-review", enums) == []
