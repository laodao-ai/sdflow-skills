"""devenv_schema 的测试。

【本文件测什么 / 不测什么】—— 直接对应 07 §3.3 的职责边界：

    schema  拦「结构」   ← 本文件测的全是这个
    lint    报「内容」   ← 五槽留白 / 不适用没写后果 / blocked_by 敷衍
                          全部【不在这里】，归 test_lint.py，且断言的是「报了几条」不是「拒了」

判据 = 【人看不看得见】：
  - status 写成 'verifed' —— 长得像正常值，人看不见 ⇒ schema fail-closed 拦。
  - e2e 五槽全空 —— 人打开文档一眼就看见 ⇒ lint 报，MUST NOT 拦。

红线测试（防已否机制复活）见文件末尾。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import devenv_schema as S  # noqa: E402


def _evidence(**over):
    ev = {
        "at_commit": "a" * 40,
        "at_time": "2026-07-14T10:23:00Z",
        "exit": 0,
        "attested_by": "script",
    }
    ev.update(over)
    return ev


def _lane(**over):
    lane = {
        "id": "hermetic",
        "layer": "unit",
        "kind": "pure",
        "status": "verified",
        "verification": {
            "method": "go test ./...",
            "executor": "script",
            "strength": "覆盖纯逻辑；不穿过外部依赖",
            "evidence": _evidence(),
        },
        # A21：source 无 digest 字段。A23：evidence 也无任何 digest。
        "source": {"file": "-", "kind": "toolchain", "selector": "go test"},
        "smoke": "internal/console/smoke_test.go",
        "deps": [],
    }
    lane.update(over)
    return lane


def _strategy(**over):
    layers = {
        "unit": {"status": "implemented", "how": "go test", "convention": "_test.go",
                 "process": "make unit", "tooling": "无额外依赖", "lane_ids": ["hermetic"]},
        "integration": {"status": "not-applicable", "reason": "无外部依赖",
                        "consequence": "wire 层回归无自动化护栏"},
        "e2e": {"status": "manual", "how": "playwright", "convention": "e2e/*.spec.ts",
                "process": "人工按清单跑", "tooling": "浏览器",
                "why_not_scriptable": "需人眼判断渲染",
                "human_steps": "打开页面，逐项对照检查清单"},
    }
    data = {"schema_version": 1, "layers": layers}
    data.update(over)
    return data


# ---------- lane：结构与枚举 ----------

def test_valid_lane_passes():
    assert S.validate_lane(_lane()) == []


def test_lane_rejects_non_dict():
    assert S.validate_lane("nope")
    assert S.validate_lane(["a"])


@pytest.mark.parametrize("field,bad", [
    ("layer", "e2ee"),
    ("kind", "pure-ish"),
    ("status", "verifed"),   # 典型 typo：长得像正常值 ⇒ 人看不见 ⇒ 必须拦
])
def test_lane_enum_typo_is_fail_closed(field, bad):
    errs = S.validate_lane(_lane(**{field: bad}))
    assert any(field in e for e in errs), errs


def test_lane_id_must_be_string():
    assert any("lane.id" in e for e in S.validate_lane(_lane(id=123)))
    assert any("lane.id" in e for e in S.validate_lane(_lane(id=None)))


def test_verification_must_be_object():
    assert any("verification" in e for e in S.validate_lane(_lane(verification="go test")))


def test_method_is_structurally_required():
    """method 不是「防漏」检查——verify-lane 要拿它去 fork 执行，没有它 B 层的手动不了。"""
    lane = _lane()
    del lane["verification"]["method"]
    assert any("method" in e for e in S.validate_lane(lane))


def test_executor_enum_enforced():
    lane = _lane()
    lane["verification"]["executor"] = "robot"
    assert any("executor" in e for e in S.validate_lane(lane))


# ---------- lane：verified 的证据（历史执行坐标，无时效锚）----------

@pytest.mark.parametrize("key", S.EVIDENCE_KEYS)
def test_verified_requires_each_evidence_key(key):
    lane = _lane()
    del lane["verification"]["evidence"][key]
    assert any(key in e for e in S.validate_lane(lane))


def test_verified_requires_evidence_object():
    lane = _lane()
    lane["verification"]["evidence"] = "跑过了"
    assert any("evidence" in e for e in S.validate_lane(lane))


def test_attested_by_enum_enforced():
    """两种 verified 在数据里就是两种东西（07 §0.3）：脚本验的 vs 人说的。"""
    lane = _lane()
    lane["verification"]["evidence"] = _evidence(attested_by="probably")
    assert any("attested_by" in e for e in S.validate_lane(lane))


def test_human_attested_verified_is_legal():
    lane = _lane()
    lane["verification"]["executor"] = "human"
    lane["verification"]["evidence"] = _evidence(attested_by="human")
    assert S.validate_lane(lane) == []


def test_exit_zero_is_not_treated_as_missing():
    """回归：exit=0 是最常见的值。若用 `if not ev.get(k)` 判存在，0 会被当成缺失。"""
    lane = _lane()
    lane["verification"]["evidence"] = _evidence(exit=0)
    assert S.validate_lane(lane) == []


def test_planned_lane_needs_no_evidence():
    assert S.validate_lane(_lane(status="planned")) == []


# ---------- lane：deps ----------

def test_deps_kind_enum():
    lane = _lane(deps=[{"name": "mosquitto", "kind": "broker"}])
    assert any("deps[].kind" in e for e in S.validate_lane(lane))


def test_owned_by_stays_dead():
    """A16：deps[].owned_by 是「运行时派生」的假锚——skill 不知道 recipe 内部启了什么。"""
    lane = _lane(deps=[{"name": "mosquitto", "kind": "host-service", "owned_by": "skill"}])
    assert any("owned_by" in e for e in S.validate_lane(lane))


def test_deps_must_be_list():
    assert any("deps" in e for e in S.validate_lane(_lane(deps={"a": 1})))


# ---------- strategy：三层骨架 ----------

def test_valid_strategy_passes():
    assert S.validate_strategy(_strategy()) == []


@pytest.mark.parametrize("missing", S.LAYERS)
def test_missing_layer_is_fail_closed(missing):
    """三层【必须都在】—— 核心承诺的结构骨架。缺一层不是「留白」，是「没这层」。"""
    data = _strategy()
    del data["layers"][missing]
    assert any(missing in e for e in S.validate_strategy(data))


def test_layer_status_enum():
    data = _strategy()
    data["layers"]["unit"]["status"] = "done"
    assert any("unit.status" in e for e in S.validate_strategy(data))


def test_pending_slots_are_legal():
    """⭐ 核心行为反转：`⚠️ 待定` 是【合法】产物（07 §3.1）。

    人当场答不上来（「e2e 我还没想好」）⇒ 原样落 PENDING。schema MUST NOT 拒绝它。
    它由 lint 计数 + 渲染显眼 + 收尾报告逐条列出 ——【报，不拦】。

    旧版在这里 fail-closed（"五槽不许留白"）。那是审计官的做法：
    拦一个空的 strength，并不会让模型写出好的 strength，只会让它写出【一句话】。
    机械层会奖励空话、惩罚诚实（07 §2.2 round-3 对抗镜实证）。
    """
    data = _strategy()
    for slot in ("how", "convention", "process", "tooling"):
        data["layers"]["unit"][slot] = S.PENDING
    assert S.validate_strategy(data) == []


def test_all_pending_strategy_still_passes_schema():
    """极端：三层全待定 —— schema 全过。这不是漏洞，是设计（副驾不拦人）。

    可见性由别处保证：lint 报满屏、渲染显眼、收尾报告逐条列。人一眼就知道这次白跑了。
    """
    data = _strategy()
    for name in S.LAYERS:
        data["layers"][name] = {"status": "manual", "how": S.PENDING,
                                "convention": S.PENDING, "process": S.PENDING,
                                "tooling": S.PENDING, "why_not_scriptable": S.PENDING,
                                "human_steps": S.PENDING}
    assert S.validate_strategy(data) == []


def test_not_applicable_without_consequence_passes_schema():
    """「不适用没写后果」是【内容】问题 ⇒ 归 lint 报，schema 放行。

    这条测试是故意的：它锁死「schema 不做内容检查」这个边界。
    若哪天有人把 consequence 检查加回 schema，这条会红——那正是它存在的意义。
    """
    data = _strategy()
    data["layers"]["integration"] = {"status": "not-applicable", "reason": "无外部依赖"}
    assert S.validate_strategy(data) == []


# ---------- IO ----------

def test_roundtrip(tmp_path):
    S.save_lanes(tmp_path, {"lanes": [_lane()]})
    assert S.load_lanes(tmp_path)["lanes"][0]["id"] == "hermetic"
    S.save_strategy(tmp_path, _strategy())
    assert S.load_strategy(tmp_path)["layers"]["unit"]["status"] == "implemented"


def test_save_rejects_invalid(tmp_path):
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(tmp_path, {"lanes": [_lane(status="verifed")]})


def test_duplicate_lane_ids(tmp_path):
    with pytest.raises(S.SchemaInvalid, match="重复"):
        S.save_lanes(tmp_path, {"lanes": [_lane(), _lane()]})


def test_unhashable_id_does_not_crash_dupe_check(tmp_path):
    """非 string 的 id 由 validate_lane 各自报出，MUST NOT 在判重时 TypeError 崩溃。"""
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(tmp_path, {"lanes": [_lane(id=["a"]), _lane(id={"b": 1})]})


def test_missing_file(tmp_path):
    with pytest.raises(S.SchemaInvalid, match="不存在"):
        S.load_lanes(tmp_path)


def test_bad_json(tmp_path):
    p = tmp_path / S.LANES_REL
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(S.SchemaInvalid, match="JSON 语法错误"):
        S.load_lanes(tmp_path)


def test_schema_too_new(tmp_path):
    S.save_lanes(tmp_path, {"lanes": []})
    p = tmp_path / S.LANES_REL
    p.write_text(p.read_text(encoding="utf-8").replace('"schema_version": 1',
                                                       '"schema_version": 99'),
                 encoding="utf-8")
    with pytest.raises(S.SchemaTooNew):
        S.load_lanes(tmp_path)


def test_schema_version_true_is_not_an_integer(tmp_path):
    """bool 是 int 的子类 —— isinstance(True, int) 恒真。不显式排除就会静默放行。"""
    S.save_lanes(tmp_path, {"lanes": []})
    p = tmp_path / S.LANES_REL
    p.write_text(p.read_text(encoding="utf-8").replace('"schema_version": 1',
                                                       '"schema_version": true'),
                 encoding="utf-8")
    with pytest.raises(S.SchemaInvalid, match="整数"):
        S.load_lanes(tmp_path)


# ---------- 红线：防已否机制复活 ----------

def test_no_resurrected_mechanisms():
    """⭐ 红线：三个被否的机制 MUST NOT 从后门回到 schema 里。

    - make 语法解析（A21）——无界语法面禁手搓；target 能不能跑，让 make 自己判
    - 时效 digest（A23 闸门 0）——该由「continue 时问一句 + git」做的事
    - 文件锁 / CAS（A23 闸门 3）——防一个不会发生的并发

    警号（CLAUDE.md 基准 5）：「每轮 review 都在同一个函数里补一个新的语法分支」
    不是「还差最后一个 case」，是「这个函数本来就不该存在」。

    【断言的是「符号」，不是「文本」】——这个区分是本测试正确性的全部。
    本文件的 docstring、注释、以及【报错文案】都在解释「为什么没有这些机制」
    （例：owned_by 的报错里就写着 "skill 不知道 recipe 内部启动了什么"）。
    扫文本必然命中那些解释，报假阳。要断言的其实是：
        「代码里没有名为 digest / sha256 / recipe … 的【标识符】，也没 import 它们」
    ⇒ 走 AST 收集标识符集合，字符串字面量与注释天然不在其中。

    （这个假阳我踩了三次：devenv_digest 的红线测试（docstring）→ 本测试 v1（注释）
      → 本测试 v2（报错文案）。三次都是「扫文本」。记在这里，别再扫文本。）
    """
    import ast

    src = Path(__file__).resolve().parents[1] / "scripts" / "devenv_schema.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    symbols = set()
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            symbols.add(n.id.lower())
        elif isinstance(n, ast.Attribute):
            symbols.add(n.attr.lower())
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(n.name.lower())
        elif isinstance(n, ast.arg):
            symbols.add(n.arg.lower())
        elif isinstance(n, ast.keyword) and n.arg:
            symbols.add(n.arg.lower())
        elif isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0].lower() for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0].lower())

    # 子串禁词：出现在【任何标识符】里都算复活。
    banned_substrings = {"digest", "sha256", "recipe", "makefile",
                         "atomic_write", "plan_snapshot"}
    # 导入禁词：只查 import 名，MUST NOT 拿去做子串匹配 ——
    # "re" 是 errs / rel / _require_* 的子串，子串匹配会把它们全打成阳性（我刚踩过）。
    banned_imports = {"re", "hashlib", "fcntl", "devenv_lock", "devenv_digest"}

    sym_hits = {b for b in banned_substrings for s in symbols if b in s}
    imp_hits = banned_imports & imports
    assert not (sym_hits | imp_hits), (
        f"schema 里出现了已否机制的痕迹 —— 符号 {sorted(sym_hits)} / 导入 {sorted(imp_hits)}。"
        "见 07 附录 A21（make 解析）· A23（时效 digest / 文件锁）。MUST NOT 从后门复活。"
    )
