"""devenv_schema 的测试。

【本文件测什么 / 不测什么】—— 直接对应 07 §3.3 的职责边界：

    schema  拦「结构」   ← 本文件测的全是这个
    lint    报「内容」   ← 六槽留白 / 不适用没写后果 / blocked_by 敷衍
                          全部【不在这里】，归 test_lint.py，且断言的是「报了几条」不是「拒了」

判据 = 【人看不看得见】：
  - status 写成 'verifed' —— 长得像正常值，人看不见 ⇒ schema fail-closed 拦。
  - e2e 六槽全空 —— 人打开文档一眼就看见 ⇒ lint 报，MUST NOT 拦（adr/0021）。

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
        "status": "verified",
        "verification": {
            "method": "go test ./...",
            "executor": "script",
            "strength": "覆盖纯逻辑；不穿过任何外部依赖",
            "evidence": _evidence(),
        },
        # A24：source 是自由文本人读注记，不是结构化契约。
        "source": "直接 go test（本项目无 task runner）",
        "smoke": "internal/console/smoke_test.go",
        "deps": [],
    }
    lane.update(over)
    return lane


def _layer(**over):
    L = {s: "已答" for s in S.CONTENT_SLOTS}
    L["lane_ids"] = []
    L.update(over)
    return L


def _data(**over):
    d = {
        "schema_version": 1,
        "layers": {
            "unit": _layer(lane_ids=["hermetic"]),
            "integration": _layer(),
            "e2e": {
                "status": S.NOT_APPLICABLE,
                "reason": "本项目是一个库，没有端到端的部署形态",
                "consequence": "库的使用者若把 API 用错，我们看不见",
            },
        },
        "lanes": [_lane()],
    }
    d.update(over)
    return d


# ---------- lane：结构与枚举 ----------

def test_valid_data_passes():
    assert S.validate(_data()) == []


@pytest.mark.parametrize("field,bad", [
    ("layer", "e2ee"),
    ("status", "verifed"),   # 典型 typo：长得像正常值 ⇒ 人看不见 ⇒ 必须拦
])
def test_lane_enum_typo_is_fail_closed(field, bad):
    errs = S.validate_lane(_lane(**{field: bad}))
    assert any(field in e for e in errs), errs


def test_lane_id_must_be_string():
    assert any("lane.id" in e for e in S.validate_lane(_lane(id=123)))


def test_source_is_free_text_not_a_struct():
    """A24：source 是人读注记。结构化的 {file,kind,selector} 会被拒（类型不对）。"""
    errs = S.validate_lane(_lane(source={"file": "Makefile", "kind": "make-target"}))
    assert any("source" in e for e in errs)
    # 任意自由文本都合法 —— 包括「没有 task runner」这种
    assert S.validate_lane(_lane(source="直接 pytest，本项目没有 Makefile")) == []


def test_method_is_structurally_required():
    """method 不是「防漏」检查——verify-lane 要拿它去 fork 执行，没有它手动不了。"""
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


def test_attested_by_enum_enforced():
    """两种 verified 在数据里就是两种东西：脚本验的 vs 人说的。"""
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


# ---------- lane：deps 无封闭枚举（A24）----------

def test_deps_kind_is_dead():
    """A24：封闭枚举 = 未列举的依赖形态当场罢工 = 一类项目被拒之门外。"""
    lane = _lane(deps=[{"name": "JTAG probe", "kind": "hardware"}])
    assert any("kind" in e for e in S.validate_lane(lane))


def test_deps_accepts_any_dependency_shape():
    """核心承诺「不管什么项目」：一个 JTAG 探针、一个 SIM 卡、一个许可证服务器——全合法。"""
    lane = _lane(deps=[
        {"name": "mosquitto", "note": "本机服务，brew install mosquitto"},
        {"name": "JTAG probe", "note": "接上 ESP-Prog，插 USB"},
        {"name": "厂商许可证服务器", "note": "公司内网 VPN 才通"},
    ])
    assert S.validate_lane(lane) == []


def test_owned_by_stays_dead():
    """A16：deps[].owned_by 是「运行时派生」的假锚。"""
    lane = _lane(deps=[{"name": "mosquitto", "owned_by": "skill"}])
    assert any("owned_by" in e for e in S.validate_lane(lane))


# ---------- layers：三层骨架 + 六槽 ----------

@pytest.mark.parametrize("missing", S.LAYERS)
def test_missing_layer_is_fail_closed(missing):
    """三层【必须都在】—— 核心承诺的结构骨架。缺一层不是「留白」，是「没这层」。"""
    d = _data()
    del d["layers"][missing]
    assert any(missing in e for e in S.validate(d))


def test_pending_slots_are_legal():
    """⭐ 核心：`⚠️ 待定` 是【合法】产物（adr/0021）。

    人当场答不上来（「e2e 我还没想好」）⇒ 原样落 PENDING。schema MUST NOT 拒绝它。
    它由 lint 计数 + 渲染横幅 + 收尾报告逐条列出 ——【报，不拦】。

    审计官的做法是在这里 fail-closed。那不会让模型写出好的 blind_spots，
    只会让它写出【一句话】—— 机械层会奖励空话、惩罚诚实。
    """
    d = _data()
    for slot in S.CONTENT_SLOTS:
        d["layers"]["unit"][slot] = S.PENDING
    assert S.validate(d) == []


def test_blank_framework_passes_schema():
    """极端：全新起手，三层十五格全待定 —— schema 全过。这不是漏洞，是设计。

    可见性由别处保证：lint 报满屏、渲染横幅、收尾报告逐条列。
    人一眼就知道这次白跑了。
    """
    assert S.validate(S.blank()) == []


def test_not_applicable_needs_reason_and_consequence():
    """`不适用` 是唯一需要人拍的层状态，MUST 带理由 + 后果。

    不写后果，`不适用` 就是一个不需要负责的逃生舱；写了后果，它才是一个被知情接受的取舍。
    （这一条【是】结构检查：consequence 字段在不在，人看不见。内容好不好才归 lint。）
    """
    d = _data()
    d["layers"]["e2e"] = {"status": S.NOT_APPLICABLE, "reason": "没时间"}
    assert any("consequence" in e for e in S.validate(d))


def test_not_applicable_exempts_the_six_slots():
    """不适用 ⇒ ①–④、⑥ 槽豁免（否则是逼模型为「不做这件事」编造废话）。"""
    d = _data()
    d["layers"]["integration"] = {
        "status": S.NOT_APPLICABLE,
        "reason": "本项目无外部有状态依赖",
        "consequence": "wire 层回归无自动化护栏",
    }
    assert S.validate(d) == []


# ---------- 层状态：投影，MUST NOT 手写（A25）----------

def test_handwritten_layer_status_is_rejected():
    """⭐ A25：层状态是【投影】，手写即可伪造、可漂移。

    「已实现」这个词曾经允许一个【从未跑绿】的层自称已实现（其定义只要求泳道 ≥ scaffolded）。
    现在它压根没有手写的入口。
    """
    d = _data()
    d["layers"]["unit"]["status"] = "verified"
    errs = S.validate(d)
    assert any("MUST NOT 手写" in e for e in errs), errs


@pytest.mark.parametrize("lane_statuses,want", [
    ([], "planned"),                                  # 零泳道
    (["planned"], "planned"),
    (["planned", "planned"], "planned"),
    (["scaffolded"], "scaffolded"),
    (["planned", "scaffolded"], "scaffolded"),
    (["verified"], "verified"),
    (["verified", "verified"], "verified"),           # 全绿 ⇒ 才是绿
    # ⭐ 投影取【最弱的那条泳道】，不是最强的那条 —— 见下面的回归测试
    (["planned", "scaffolded", "verified"], "partial"),
    (["planned", "verified"], "partial"),
    (["scaffolded", "verified"], "partial"),
])
def test_layer_status_projection(lane_statuses, want):
    lanes = [_lane(id=f"l{i}", status=st) for i, st in enumerate(lane_statuses)]
    layer = _layer(lane_ids=[l["id"] for l in lanes])
    assert S.layer_status(layer, lanes) == want


def test_one_green_lane_does_not_make_the_layer_green():
    """⭐ 回归 A29（mqtt-console 试点实证）：「有一条绿 ⇒ 整层 ✅ 已验证」是【假绿】。

    这条病【曾经被写进本文件的断言里】——原 parametrize 有一行
    `(["planned","scaffolded","verified"], "verified")  # 多泳道：有一条绿就算绿`。
    也就是说：A25 杀掉了「手写层状态」，假绿就换到【投影规则】里长出来了，
    而我把它当成正确行为固化进了测试。**杀掉一个机制不等于杀掉它的病。**

    试点现场：e2e 层三条泳道 —— wails-live-e2e 绿、packaged-app-boot 与
    packaged-app-visual 都是 planned（打包冒烟压根没做，而那正是「能不能交付」的唯一证据），
    标题照报「✅ 已验证」。而【标题那一行才是被读的那一行】。
    """
    lanes = [_lane(id="live", status="verified"),
             _lane(id="pkg-boot", status="planned"),
             _lane(id="pkg-visual", status="planned")]
    layer = _layer(lane_ids=["live", "pkg-boot", "pkg-visual"])

    assert S.layer_status(layer, lanes) == "partial"
    assert S.layer_lane_tally(layer, lanes) == (1, 3)   # 「3 条里绿了 1 条」


def test_not_applicable_layer_projects_to_itself():
    L = {"status": S.NOT_APPLICABLE, "reason": "r", "consequence": "c"}
    assert S.layer_status(L, []) == S.NOT_APPLICABLE


def test_scaffolded_layer_is_not_called_implemented():
    """回归 A25：一个层的唯一泳道从未跑绿 ⇒ 它 MUST NOT 呈现为「已实现」。

    投影出来的是 `scaffolded`（渲染成「已搭好，未验证」）—— 这句话是真的。
    """
    lanes = [_lane(id="x", status="scaffolded", blocked_by="本机无 mosquitto")]
    layer = _layer(lane_ids=["x"])
    assert S.layer_status(layer, lanes) == "scaffolded"


# ---------- 交叉引用 ----------

def test_lane_ids_must_point_at_real_lanes():
    d = _data()
    d["layers"]["integration"]["lane_ids"] = ["ghost"]
    assert any("ghost" in e for e in S.validate(d))


def test_duplicate_lane_ids():
    d = _data(lanes=[_lane(), _lane()])
    assert any("重复" in e for e in S.validate(d))


# ---------- IO ----------

def test_roundtrip(tmp_path):
    S.save(tmp_path, _data())
    got = S.load(tmp_path)
    assert got["lanes"][0]["id"] == "hermetic"
    assert got["layers"]["e2e"]["status"] == S.NOT_APPLICABLE


def test_save_rejects_invalid(tmp_path):
    with pytest.raises(S.SchemaInvalid):
        S.save(tmp_path, _data(lanes=[_lane(status="verifed")]))


def test_missing_file(tmp_path):
    with pytest.raises(S.SchemaInvalid, match="不存在"):
        S.load(tmp_path)


def test_bad_json(tmp_path):
    p = tmp_path / S.DEVENV_REL
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(S.SchemaInvalid, match="JSON 语法错误"):
        S.load(tmp_path)


def test_schema_too_new(tmp_path):
    S.save(tmp_path, S.blank())
    p = tmp_path / S.DEVENV_REL
    p.write_text(p.read_text(encoding="utf-8").replace('"schema_version": 1',
                                                       '"schema_version": 99'),
                 encoding="utf-8")
    with pytest.raises(S.SchemaTooNew):
        S.load(tmp_path)


def test_schema_version_true_is_not_an_integer(tmp_path):
    """bool 是 int 的子类 —— isinstance(True, int) 恒真。不显式排除就会静默放行。"""
    S.save(tmp_path, S.blank())
    p = tmp_path / S.DEVENV_REL
    p.write_text(p.read_text(encoding="utf-8").replace('"schema_version": 1',
                                                       '"schema_version": true'),
                 encoding="utf-8")
    with pytest.raises(S.SchemaInvalid, match="整数"):
        S.load(tmp_path)


# ---------- 红线：防已否机制复活 ----------

def test_no_resurrected_mechanisms():
    """⭐ 红线：四个被否的机制 MUST NOT 从后门回到 schema 里。

    - make/shell 语法解析（A21）——无界语法面禁手搓；命令能不能跑，让工具自己判
    - 时效 digest（A23 闸门 0）——该由「continue 时问一句 + git」做的事
    - 文件锁 / CAS（A23 闸门 3）——防一个不会发生的并发
    - 层状态字段（A25）——层状态是投影，不是声明

    【断言的是「符号」，不是「文本」】—— 这个区分是本测试正确性的全部。
    本文件的 docstring、注释、报错文案都在解释「为什么没有这些机制」，扫文本必然假阳。
    （这个坑踩过三次：docstring → 注释 → 报错文案。三次都是「扫文本」。别再扫文本。）
    """
    import ast

    src = Path(__file__).resolve().parents[1] / "scripts" / "devenv_schema.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    symbols, imports = set(), set()
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

    banned_substrings = {"digest", "sha256", "recipe", "makefile",
                         "atomic_write", "plan_snapshot"}
    # 导入禁词：只查 import 名，MUST NOT 拿去做子串匹配 ——
    # "re" 是 errs / require 的子串，子串匹配会把它们全打成阳性。
    banned_imports = {"re", "hashlib", "fcntl", "devenv_lock", "devenv_digest"}

    sym_hits = {b for b in banned_substrings for s in symbols if b in s}
    imp_hits = banned_imports & imports
    assert not (sym_hits | imp_hits), (
        f"schema 里出现了已否机制的痕迹 —— 符号 {sorted(sym_hits)} / 导入 {sorted(imp_hits)}。"
        "见 07 附录 A21（make 解析）· A23（时效 digest / 文件锁）· A25（层状态字段）。"
    )


def test_layer_has_no_closed_status_enum():
    """A25 红线：schema 里 MUST NOT 有 planned/scaffolded/verified 的【层】状态枚举。

    LANE_STATUSES 是给泳道的（合法）。层没有自己的状态枚举 —— 它只有 NOT_APPLICABLE。
    """
    assert S.NOT_APPLICABLE == "not-applicable"
    assert not hasattr(S, "LAYER_STATUSES"), (
        "层状态枚举已废除（A25）—— 层状态是从 lanes[] 投影算出的"
    )


def test_only_layer_is_a_closed_enum():
    """A24 红线：除 layer（核心承诺的骨架）外，MUST NOT 有其他分类字段的封闭枚举。"""
    assert S.LAYERS == ("unit", "integration", "e2e")
    for dead in ("LANE_KINDS", "DEP_KINDS", "SOURCE_KINDS"):
        assert not hasattr(S, dead), (
            f"{dead} 已废除（A24）—— 封闭枚举 = 未列举的形态当场罢工 = 一类项目被拒之门外"
        )
