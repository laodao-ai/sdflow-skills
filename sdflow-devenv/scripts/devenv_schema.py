"""`.devenv.json` 的 schema —— 标准库 json，零第三方依赖。

【职责边界，MUST 守】（07 §3.3 · §0.0 闸门 0「形态问」· adr/0021）

    schema  拦「结构」—— 字段在不在 · 枚举合不合法 · 类型对不对
    lint    报「内容」—— 六槽留白 · 不适用没写后果 · blocked_by 敷衍

判据 = 【人看不看得见】：
  - 「lane.status 写成 'verifed'」——长得像正常值，人看不见 ⇒ schema fail-closed 拦。
  - 「e2e 层六个槽全空」——人打开 testing-strategy.md 一眼就看见 ⇒ lint 报 + 渲染显眼，
    MUST NOT 拦（adr/0021：代价可见 > 机械拦截）。

【为什么内容检查 MUST NOT 拦】（07 §2.2 round-3 对抗镜实证）：
拦一个空的 blind_spots，并不会让模型写出好的 blind_spots——只会让它写出【一句话】。
机械层会【奖励空话、惩罚诚实】。skill 是副驾：它的职责是【问到了】，不是【填满了】。
人当场答不上来 ⇒ 原样落 PENDING，这是合法产物。

【封闭枚举纪律】（07 附录 A24）：
只有 layer 是封闭三值（unit/integration/e2e —— 它是核心承诺的骨架）。
【其余一切分类字段 MUST 是自由文本】——source / deps[].note / 泳道形态。
封闭枚举 = 未列举的形态当场罢工 = 一类项目被拒之门外，这正是 A21 的病。

【本文件没有什么】（四条碑文，勿手贱加回来）：
  - 无 make/shell 语法解析 —— A21（无界语法面禁手搓；命令能不能跑，让工具自己判）
  - 无时效 digest —— A23（「验证后文件改没改」由 continue 时问一句 + git 回答）
  - 无文件锁 / CAS —— A23（防一个不会发生的并发；JSON 写坏 = 重跑一次）
  - 无层状态字段 —— A25（层状态是泳道的【投影】，手写即可伪造可漂移）
"""
import json
from pathlib import Path

SCHEMA_VERSION = 1

DEVENV_REL = "openspec/architecture/.devenv.json"

# 唯一的封闭枚举 —— 核心承诺的骨架（07 §2.2）。
# 「层」= 保真度刻度：unit=不穿任何真实外部边界 / integration=穿过部分 / e2e=端到端全穿。
LAYERS = ("unit", "integration", "e2e")

# 每层要【问】的槽。⑤状态不在此列 —— 它从 lanes[] 投影算出（A25）。
CONTENT_SLOTS = ("how", "convention", "process", "tooling", "blind_spots")

LANE_STATUSES = ("planned", "scaffolded", "verified")
EXECUTORS = ("script", "human")
ATTESTORS = ("script", "human")

# verified 的证据 = 一次历史执行的坐标。无时效 digest（A23）。
EVIDENCE_KEYS = ("at_commit", "at_time", "exit", "attested_by")

# 「我还没想好」的合法值（adr/0021）—— 副驾问了、人当场答不上来，如实落它。
# schema 接受；lint 计数并要求渲染横幅 + 收尾报告逐条列出。
PENDING = "⚠️ 待定"

# 层的唯一人写状态。其余三态（planned/scaffolded/verified）从 lanes[] 投影（A25）。
NOT_APPLICABLE = "not-applicable"


class SchemaInvalid(Exception):
    pass


class SchemaTooNew(Exception):
    pass


def _enum(errs, val, allowed, field):
    if val not in allowed:
        errs.append(f"{field} 非法（须 ∈ {allowed}）: {val!r}")


def _str_field(errs, obj, key, field):
    """字段必须存在且为 string。空串 / PENDING 都算存在——内容够不够是 lint 的事。"""
    v = obj.get(key)
    if v is None:
        errs.append(f"{field} 缺失")
    elif not isinstance(v, str):
        errs.append(f"{field} 须为 string，实际是 {type(v).__name__}")


# ---------- layers（三层框架）----------

def validate_layer(name, L):
    """只查结构。六槽的【内容】够不够，归 devenv_lint（只报不拦）。"""
    if not isinstance(L, dict):
        return [f"{name} 层须为 object，实际是 {type(L).__name__}"]
    errs = []

    if L.get("status") == NOT_APPLICABLE:
        # 不适用 ⇒ ①–④、⑥ 槽豁免（否则是逼模型为「不做这件事」编造废话）。
        # 但 reason + consequence MUST 有 —— consequence 正是 ⑥ 在这个状态下的形态。
        _str_field(errs, L, "reason", f"{name}.reason")
        _str_field(errs, L, "consequence", f"{name}.consequence")
        return errs

    # A25：层状态是投影，MUST NOT 手写。唯一例外是 not-applicable（上面已处理）。
    if "status" in L:
        errs.append(
            f"{name}.status 只能是 {NOT_APPLICABLE!r} 或【不写】—— "
            f"planned/scaffolded/verified 是从 lanes[] 投影算出的，MUST NOT 手写（07 A25）"
        )

    for slot in CONTENT_SLOTS:
        _str_field(errs, L, slot, f"{name}.{slot}")

    lane_ids = L.get("lane_ids")
    if lane_ids is None:
        lane_ids = []
    if not isinstance(lane_ids, list):
        errs.append(f"{name}.lane_ids 须为数组，实际是 {type(lane_ids).__name__}")
    else:
        for i in lane_ids:
            if not isinstance(i, str):
                errs.append(f"{name}.lane_ids[] 的元素须为 string，实际是 {type(i).__name__}")
    return errs


def layer_status(layer, lanes):
    """⑤ 状态 —— 从泳道【投影】算出，不是声明（07 §2.2 · A25）。

    这是【结构性保证】而非拦截：层状态无法伪造、无法漂移，因为它压根不存在于数据里。

    🔴 【投影取最弱的那条泳道，不是最强的那条】（07 A29 · mqtt-console 试点实证）：
    「有一条绿 ⇒ 整层报 ✅ 已验证」是【假绿】—— 它是 A25 要杀的那条病，换了个地方长出来。
    试点现场：e2e 层三条泳道，两条 planned（打包冒烟压根没做），标题照报「✅ 已验证」。
    而【标题那一行才是被读的那一行】；下面泳道表里那两个 ○ 救不了它。
    ∴ 全绿才 verified；有绿有非绿 ⇒ partial（如实说「3 条里绿了 1 条」）。
    """
    if isinstance(layer, dict) and layer.get("status") == NOT_APPLICABLE:
        return NOT_APPLICABLE
    ids = set(layer.get("lane_ids") or []) if isinstance(layer, dict) else set()
    mine = [l for l in lanes if isinstance(l, dict) and l.get("id") in ids]
    if not mine:
        return "planned"
    statuses = {l.get("status") for l in mine}
    if statuses == {"verified"}:
        return "verified"
    if "verified" in statuses:
        return "partial"
    if "scaffolded" in statuses:
        return "scaffolded"
    return "planned"


def layer_lane_tally(layer, lanes):
    """(已 verified 数, 该层泳道总数) —— 给 partial 的标题用「3 条里绿了 1 条」。"""
    ids = set(layer.get("lane_ids") or []) if isinstance(layer, dict) else set()
    mine = [l for l in lanes if isinstance(l, dict) and l.get("id") in ids]
    return sum(1 for l in mine if l.get("status") == "verified"), len(mine)


# ---------- lanes ----------

def validate_lane(lane):
    """只查结构与枚举。MUST NOT 有 kind 枚举（A24：封闭枚举 = 一类项目被拒之门外）。"""
    if not isinstance(lane, dict):
        return [f"lane 须为 object，实际是 {type(lane).__name__}"]
    errs = []

    _str_field(errs, lane, "id", "lane.id")
    _enum(errs, lane.get("layer"), LAYERS, "lane.layer")
    status = lane.get("status")
    _enum(errs, status, LANE_STATUSES, "lane.status")

    # source 是【自由文本人读注记】，不是结构化契约（A24）。
    _str_field(errs, lane, "source", "lane.source")

    v = lane.get("verification")
    if not isinstance(v, dict):
        errs.append(f"lane.verification 须为 object，实际是 {type(v).__name__}")
        return errs

    # method 是结构性必需：verify-lane 要拿它去 fork 执行，没有它 B 层的手动不了。
    # （这不是「防漏」—— 是「手需要它才能动」。）
    _str_field(errs, v, "method", "verification.method")
    _enum(errs, v.get("executor"), EXECUTORS, "verification.executor")

    if status == "verified":
        ev = v.get("evidence")
        if not isinstance(ev, dict):
            errs.append("verified MUST 有 evidence（object）—— 证据只能由执行者本人写")
        else:
            for k in EVIDENCE_KEYS:
                if k not in ev:
                    errs.append(f"verified MUST 有 evidence.{k}")
            _enum(errs, ev.get("attested_by"), ATTESTORS, "evidence.attested_by")

    deps = lane.get("deps")
    if deps is None:
        deps = []
    if not isinstance(deps, list):
        errs.append(f"lane.deps 须为数组，实际是 {type(deps).__name__}")
        deps = []
    for d in deps:
        if not isinstance(d, dict):
            errs.append("deps[] 的元素须为 object")
            continue
        if "owned_by" in d:
            errs.append("deps[].owned_by 已删除（07 A16：「运行时派生」的锚不存在）")
        if "kind" in d:
            errs.append(
                "deps[].kind 已删除（07 A24：封闭枚举 = 未列举的依赖形态当场罢工 = "
                "一类项目被拒之门外）—— 用自由文本的 deps[].note"
            )
        _str_field(errs, d, "name", "deps[].name")
    return errs


# ---------- 顶层 ----------

def validate(data):
    if not isinstance(data, dict):
        return [f"顶层须为 object，实际是 {type(data).__name__}"]

    errs = []
    lanes = data.get("lanes")
    if lanes is None:
        lanes = []
    if not isinstance(lanes, list):
        return [f"lanes 须为数组，实际是 {type(lanes).__name__}"]

    ids = [l["id"] for l in lanes if isinstance(l, dict) and isinstance(l.get("id"), str)]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errs.append(f"lane id 重复: {dupes}")
    for lane in lanes:
        prefix = lane.get("id") if isinstance(lane, dict) else "?"
        errs += [f"[lane {prefix}] {e}" for e in validate_lane(lane)]

    layers = data.get("layers")
    if layers is None:
        layers = {}
    if not isinstance(layers, dict):
        return errs + [f"layers 须为 object，实际是 {type(layers).__name__}"]

    known = set(ids)
    for name in LAYERS:
        L = layers.get(name)
        if L is None:
            # 三层【必须都在】—— 核心承诺的结构骨架（「一层都不许留白」）。
            # 注意：层【在】但六个槽全是 PENDING 是【合法】的（人还没想好）——那由 lint 报。
            errs.append(f"三层框架缺 {name} 层 —— 一层都不许留白")
            continue
        errs += [f"[layer {name}] {e}" for e in validate_layer(name, L)]
        for lid in (L.get("lane_ids") or []) if isinstance(L, dict) else []:
            if isinstance(lid, str) and lid not in known:
                errs.append(f"[layer {name}] lane_ids 指向不存在的泳道: {lid!r}")
    return errs


# ---------- IO ----------

def load(root):
    p = Path(root) / DEVENV_REL
    if not p.exists():
        raise SchemaInvalid(f"{DEVENV_REL} 不存在")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaInvalid(f"{DEVENV_REL} JSON 语法错误: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaInvalid(f"{DEVENV_REL} 顶层须为 object，实际是 {type(data).__name__}")

    ver = data.get("schema_version")
    # bool 是 int 的子类 —— isinstance(True, int) 恒真，须显式排除，
    # 否则 schema_version=true 会被静默当成合法版本号接受。
    if isinstance(ver, bool) or not isinstance(ver, int):
        raise SchemaInvalid(
            f"{DEVENV_REL} 的 schema_version 须为整数，实际是 {type(ver).__name__} —— fail-closed"
        )
    if ver > SCHEMA_VERSION:
        raise SchemaTooNew(
            f"{DEVENV_REL} 的 schema_version={ver} 高于本实现已知的 {SCHEMA_VERSION} —— "
            f"skill 版本过旧，请升级。MUST NOT 尽力解析。"
        )
    return data


def save(root, data):
    errs = validate(data)
    if errs:
        raise SchemaInvalid("; ".join(errs))
    data = dict(data)
    data["schema_version"] = SCHEMA_VERSION
    p = Path(root) / DEVENV_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def blank():
    """新起手的空框架 —— 三层都在，六槽全待定。这是合法的起点。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "layers": {
            name: {slot: PENDING for slot in CONTENT_SLOTS} | {"lane_ids": []}
            for name in LAYERS
        },
        "lanes": [],
    }
