import json, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import devenv_schema as S


def _root(tmp_path):
    (tmp_path / "openspec" / "architecture").mkdir(parents=True)
    return tmp_path


def _lane(**kw):
    base = {
        "id": "mqtt-integration",
        "layer": "integration",
        "kind": "external-dep",
        "status": "scaffolded",
        "verification": {
            "method": "make integration",
            "executor": "script",
            "strength": "真穿过 broker；断言是否有效不由本方法保证",
        },
        "source": {"file": "Makefile", "kind": "make-target",
                   "selector": "integration", "digest": "abc123"},
        "smoke": "internal/smoke_test.go",
        "fixtures": [],
        "env": [],
        "deps": [{"name": "mosquitto", "kind": "host-service"}],
        "covers": [],
        "blocked_by": "本机无 mosquitto — brew install mosquitto 后 /sdflow-devenv continue",
    }
    base.update(kw)
    return base


def test_valid_lane_passes():
    assert S.validate_lane(_lane()) == []


def test_lane_rejects_owned_by():
    """owned_by 已删除（07 附录 A16：运行时派生的锚不存在）"""
    lane = _lane()
    lane["deps"][0]["owned_by"] = "skill"
    errs = S.validate_lane(lane)
    assert any("owned_by" in e for e in errs)


def test_lane_requires_method_and_strength():
    assert any("method" in e for e in S.validate_lane(_lane(verification={"executor": "script", "strength": "x"})))
    assert any("strength" in e for e in S.validate_lane(
        _lane(verification={"method": "m", "executor": "script"})))


def test_human_executor_requires_why_and_steps():
    lane = _lane(verification={"method": "人工烧板", "executor": "human", "strength": "s"})
    errs = S.validate_lane(lane)
    assert any("why_not_scriptable" in e for e in errs)
    assert any("human_steps" in e for e in errs)


def test_scaffolded_requires_blocked_by():
    assert any("blocked_by" in e for e in S.validate_lane(_lane(blocked_by="")))


def test_verified_forbids_blocked_by():
    """绿泳道挂着「本机无 X」= 文档在说谎"""
    lane = _lane(status="verified", blocked_by="本机无 mosquitto")
    lane["verification"]["evidence"] = {"at_commit": "abc", "exit": 0,
                                        "method_digest": "d", "attested_by": "script"}
    assert any("blocked_by" in e for e in S.validate_lane(lane))


def test_verified_requires_evidence():
    lane = _lane(status="verified", blocked_by="")
    assert any("evidence" in e for e in S.validate_lane(lane))


def test_bad_enum_rejected():
    assert S.validate_lane(_lane(layer="acceptance"))
    assert S.validate_lane(_lane(kind="bogus"))
    assert S.validate_lane(_lane(status="green"))


def test_schema_version_missing_fail_closed(tmp_path):
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps({"lanes": []}))
    with pytest.raises(S.SchemaInvalid):
        S.load_lanes(root)


def test_schema_version_future_fail_closed(tmp_path):
    """MUST NOT 尽力解析未来版本"""
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps({"schema_version": 999, "lanes": []}))
    with pytest.raises(S.SchemaTooNew):
        S.load_lanes(root)


def test_roundtrip_no_pyyaml(tmp_path):
    root = _root(tmp_path)
    data = {"schema_version": 1, "lanes": [_lane()]}
    S.save_lanes(root, data)
    assert S.load_lanes(root) == data


def test_duplicate_lane_id_rejected(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": [_lane(), _lane()]})


# ---- 坏输入 fail-closed（JSON 语法 / 顶层类型 / 字段类型）----

def test_load_lanes_malformed_json_fail_closed(tmp_path):
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text("{not valid json,,,")
    with pytest.raises(S.SchemaInvalid):
        S.load_lanes(root)


def test_load_lanes_top_level_not_object_fail_closed(tmp_path):
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps([1, 2, 3]))
    with pytest.raises(S.SchemaInvalid):
        S.load_lanes(root)


def test_load_strategy_top_level_not_object_fail_closed(tmp_path):
    root = _root(tmp_path)
    (root / S.STRATEGY_REL).write_text(json.dumps("just a string"))
    with pytest.raises(S.SchemaInvalid):
        S.load_strategy(root)


def test_save_lanes_lanes_wrong_type_rejected(tmp_path):
    """lanes 是字符串不是数组 —— MUST 落 SchemaInvalid，不是随机 AttributeError"""
    root = _root(tmp_path)
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": "not-a-list"})


def test_save_lanes_element_not_object_rejected(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": ["not-a-dict"]})


def test_validate_lane_rejects_non_dict():
    errs = S.validate_lane("not-a-dict")
    assert errs and any("object" in e for e in errs)


def test_validate_lane_deps_wrong_type_rejected():
    errs = S.validate_lane(_lane(deps="not-a-list"))
    assert any("deps" in e for e in errs)


def test_validate_lane_verification_wrong_type_rejected():
    errs = S.validate_lane(_lane(verification="not-a-dict"))
    assert any("verification" in e for e in errs)


def test_validate_strategy_rejects_non_dict():
    errs = S.validate_strategy(["not", "a", "dict"])
    assert errs and any("object" in e for e in errs)


def test_validate_strategy_layers_wrong_type_rejected():
    st = _strategy()
    st["layers"] = "not-a-dict"
    errs = S.validate_strategy(st)
    assert errs and any("layers" in e for e in errs)


def test_validate_strategy_single_layer_wrong_type_rejected():
    st = _strategy()
    st["layers"]["e2e"] = "not-a-dict"
    errs = S.validate_strategy(st)
    assert any("e2e" in e for e in errs)


# ---- strategy（三层框架）----

def _strategy(**layers):
    base = {
        "schema_version": 1,
        "layers": {
            "unit": {"how": "go test", "convention": "*_test.go 同包",
                     "process": "make unit，提交前", "tooling": "go 工具链",
                     "status": "implemented", "lane_ids": ["hermetic"]},
            "integration": {"how": "真 broker", "convention": "build tag realbroker",
                            "process": "make integration", "tooling": "mosquitto",
                            "status": "manual",
                            "why_not_scriptable": "依赖启停内嵌在 recipe 字面文本，无法插桩",
                            "human_steps": "1. brew services start mosquitto 2. make integration 3. 看到 PASS"},
            "e2e": {"status": "not-applicable",
                    "reason": "本项目是纯库，无可执行入口",
                    "consequence": "集成后的真实使用路径无人验证"},
        },
        "known_blind_spots": [],
    }
    base["layers"].update(layers)
    return base


def test_valid_strategy_passes():
    assert S.validate_strategy(_strategy()) == []


def test_missing_layer_fail_closed():
    st = _strategy()
    del st["layers"]["e2e"]
    assert any("e2e" in e for e in S.validate_strategy(st))


def test_implemented_requires_lane_ids():
    st = _strategy(unit={"how": "x", "convention": "x", "process": "x",
                         "tooling": "x", "status": "implemented"})
    assert any("lane_ids" in e for e in S.validate_strategy(st))


def test_not_applicable_requires_consequence():
    """不写后果，「不适用」就是不需要负责的逃生舱"""
    st = _strategy(e2e={"status": "not-applicable", "reason": "纯库"})
    assert any("consequence" in e for e in S.validate_strategy(st))


def test_not_applicable_requires_reason():
    """not-applicable 只缺 reason —— 现有测试只测了缺 consequence"""
    st = _strategy(e2e={"status": "not-applicable", "consequence": "集成路径无人验证"})
    assert any("reason" in e for e in S.validate_strategy(st))


def test_not_applicable_exempts_four_slots():
    """MUST 豁免 ①-④ —— 否则是逼模型为「不做这件事」编造废话（填表游戏）"""
    st = _strategy(e2e={"status": "not-applicable", "reason": "纯库",
                        "consequence": "集成路径无人验证"})
    assert S.validate_strategy(st) == []


def test_manual_requires_why_and_steps():
    st = _strategy(integration={"how": "x", "convention": "x", "process": "x",
                                "tooling": "x", "status": "manual"})
    errs = S.validate_strategy(st)
    assert any("why_not_scriptable" in e for e in errs)
    assert any("human_steps" in e for e in errs)


def test_placeholder_consequence_rejected():
    for junk in ("无", "没有", "N/A", "TODO", "待定", "  "):
        st = _strategy(e2e={"status": "not-applicable", "reason": "纯库", "consequence": junk})
        assert any("consequence" in e for e in S.validate_strategy(st)), junk


def test_implemented_layer_missing_slots_fail():
    st = _strategy(unit={"status": "implemented", "lane_ids": ["hermetic"]})
    errs = S.validate_strategy(st)
    assert any("how" in e for e in errs)


# ---- 面治：类型前置校验反例（每处坏类型都要有一条反例，喂错类型断言 SchemaInvalid）----

def test_lane_id_missing_or_empty_rejected():
    """lane.id 缺失 / 为空 —— 此前零反例覆盖"""
    assert any("id" in e for e in S.validate_lane(_lane(id="")))
    lane = _lane()
    del lane["id"]
    assert any("id" in e for e in S.validate_lane(lane))


def test_lane_id_wrong_type_rejected():
    for bad in (123, ["a"], {"a": 1}, True):
        errs = S.validate_lane(_lane(id=bad))
        assert any("lane.id" in e for e in errs), bad


def test_lane_blocked_by_wrong_type_rejected():
    """blocked_by 是真值但非 str（123 / list / dict）—— (x or "").strip() 会 AttributeError"""
    for bad in (123, ["a"], {"a": 1}, True):
        errs = S.validate_lane(_lane(blocked_by=bad))
        assert any("blocked_by" in e for e in errs), bad


def test_lane_verification_field_wrong_type_no_crash():
    for field in ("method", "strength", "executor"):
        for bad in (123, ["a"], {"a": 1}):
            v = dict(_lane()["verification"])
            v[field] = bad
            errs = S.validate_lane(_lane(verification=v))
            assert isinstance(errs, list)  # 不崩溃即可，具体文案已由其它用例覆盖


def test_deps_element_wrong_type_rejected():
    """deps[] 的单个元素非 dict —— 现有测试只测了 deps 整体类型错"""
    errs = S.validate_lane(_lane(deps=[{"name": "mosquitto", "kind": "host-service"}, "not-a-dict"]))
    assert any("deps[]" in e for e in errs)


def test_plan_snapshot_rejects_non_dict_lane():
    with pytest.raises(S.SchemaInvalid):
        S.plan_snapshot("not-a-dict")
    with pytest.raises(S.SchemaInvalid):
        S.plan_snapshot(["a", "b"])


def test_plan_snapshot_rejects_non_dict_verification():
    """lane.get("verification") or {} 后直接 .get(k) —— 真值非 dict 会 AttributeError"""
    for bad in (123, "not-a-dict", ["a"]):
        lane = _lane(verification=bad)
        with pytest.raises(S.SchemaInvalid):
            S.plan_snapshot(lane)


def test_schema_version_bool_rejected(tmp_path):
    """schema_version=true 时 isinstance(True, int) 恒真 —— MUST 显式拒绝"""
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps({"schema_version": True, "lanes": []}))
    with pytest.raises(S.SchemaInvalid):
        S.load_lanes(root)


def test_save_lanes_unhashable_id_fail_closed(tmp_path):
    """id 是 list（不可哈希）—— 构建判重 set 时 MUST NOT 裸抛 TypeError: unhashable type"""
    root = _root(tmp_path)
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": [_lane(id=["mqtt", "integration"])]})


def test_save_lanes_mixed_type_duplicate_ids_no_crash(tmp_path):
    """dupes 里混不同不可比较类型（str 与 int 各自重复）—— sorted() MUST NOT 裸抛 TypeError"""
    root = _root(tmp_path)
    lanes = [_lane(id="dup"), _lane(id="dup"), _lane(id=7), _lane(id=7)]
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": lanes})


# ---- CAS 快照 ----

def test_plan_snapshot_covers_executor_and_kind():
    """长跑期间 lane 从 script/pure 改成 human/hardware，只比 status 的 CAS 挡不住"""
    a = _lane()
    b = _lane()
    b["verification"] = dict(b["verification"], executor="human",
                             why_not_scriptable="x", human_steps="y")
    assert S.plan_snapshot(a) != S.plan_snapshot(b)

    c = _lane(kind="hardware")
    assert S.plan_snapshot(a) != S.plan_snapshot(c)


def test_plan_snapshot_stable_under_key_order():
    a = _lane()
    b = {k: a[k] for k in reversed(list(a))}
    assert S.plan_snapshot(a) == S.plan_snapshot(b)
