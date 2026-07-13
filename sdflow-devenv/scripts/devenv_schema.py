"""两份 JSON 侧文件的 schema —— 标准库 json，零第三方依赖。

【为什么不放 frontmatter】：嵌套 lanes[]（含列表 × 中文自由文本 × 带冒号的值）没有
可用的解析/序列化方案 —— 目标环境无 PyYAML，而唯一先例 sad_schema.parse_frontmatter
是手搓的扁平标量解析器。

【为什么三层框架也落 JSON】：若让 lint 去解析自由格式 Markdown，就是又一个手搓解析器
（本仓前科：parse_frontmatter / inject 非 fence-aware / ship_gate 子串检测假阳）。
"""
import hashlib
import json
from pathlib import Path

from devenv_lock import atomic_write

SCHEMA_VERSION = 1

LANES_REL = "openspec/architecture/.devenv-lanes.json"
STRATEGY_REL = "openspec/architecture/.devenv-strategy.json"

LAYERS = ("unit", "integration", "e2e")
SLOTS = ("how", "convention", "process", "tooling", "status")
# 内容槽 = SLOTS 去掉 status（status 走独立的枚举校验，不参与「五槽不许留白」判空）。
# 派生自 SLOTS，单一源防漂移——不要在 validate_strategy 里另起一份硬编码列表。
_CONTENT_SLOTS = tuple(s for s in SLOTS if s != "status")

LANE_KINDS = ("external-dep", "ui", "lang-bridge", "hardware", "pure")
STATUSES = ("planned", "scaffolded", "verified")
EXECUTORS = ("script", "human")
DEP_KINDS = ("compose", "host-service", "port", "toolchain", "testcontainer")
LAYER_STATUSES = ("implemented", "not-applicable", "manual")

# 反敷衍启发式（诚实边界：挡得住敷衍，挡不住「写得像模像样但没用」——后者归人门）
PLACEHOLDERS = {"", "无", "没有", "n/a", "na", "todo", "待定", "tbd", "-", "—"}

# CAS 快照覆盖【整个不可变的 verification plan】，不只 status
SNAPSHOT_KEYS = ("status", "kind", "source", "smoke", "fixtures", "env", "deps")
SNAPSHOT_VERIF_KEYS = ("method", "executor")


class SchemaInvalid(Exception):
    pass


class SchemaTooNew(Exception):
    pass


def _is_placeholder(v):
    return not isinstance(v, str) or v.strip().lower() in PLACEHOLDERS


# ---------- 类型断言 helper ----------
#
# 契约：所有坏输入一律落进 SchemaInvalid，fail-closed。JSON 里任意字段都可能是
# 模型自由填的任意类型（str/int/list/dict/bool/None）——下面这组 helper 在类型
# 不符时统一 raise SchemaInvalid，消息里带字段名 + 期望类型 + 实际类型（给模型看，
# 让它能据此改正），取代散落各处「拿到值就直接做类型相关操作」的裸写法。

def _type_name(v):
    return type(v).__name__


def _require_str(v, field):
    if not isinstance(v, str):
        raise SchemaInvalid(f"{field} 须为 string，实际是 {_type_name(v)}")
    return v


def _require_dict(v, field):
    if not isinstance(v, dict):
        raise SchemaInvalid(f"{field} 须为 object，实际是 {_type_name(v)}")
    return v


def _require_list(v, field):
    if not isinstance(v, list):
        raise SchemaInvalid(f"{field} 须为数组，实际是 {_type_name(v)}")
    return v


def _require_int(v, field):
    # bool 是 int 的子类 —— isinstance(True, int) 恒真，须显式排除，否则
    # schema_version=true 会被静默当作合法版本号接受。
    if isinstance(v, bool) or not isinstance(v, int):
        raise SchemaInvalid(f"{field} 须为整数，实际是 {_type_name(v)}")
    return v


def _require_hashable_id(v, field):
    if not _hashable(v):
        raise SchemaInvalid(f"{field} 须为可哈希类型（string/number），实际是 {_type_name(v)}")
    return v


def _hashable(v):
    try:
        hash(v)
        return True
    except TypeError:
        return False


def _checked(errs, fn, *args):
    """在 errs 累积式校验函数（validate_lane/validate_strategy）里复用 _require_*：
    类型不符时把 helper 抛出的消息并入 errs、返回 None，而不是让异常打断整个校验
    （这些函数的既有契约是「返回错误列表」，直接调用方——包括测试——依赖这一点）。
    """
    try:
        return fn(*args)
    except SchemaInvalid as exc:
        errs.append(str(exc))
        return None


# ---------- lanes ----------

def validate_lane(lane):
    if not isinstance(lane, dict):
        return [f"lane 须为 object，实际是 {type(lane).__name__}"]
    errs = []
    lid = lane.get("id")
    if not lid:
        errs.append("lane.id 缺失")
    else:
        _checked(errs, _require_str, lid, "lane.id")
    if lane.get("layer") not in LAYERS:
        errs.append(f"lane.layer 非法（须 ∈ {LAYERS}）: {lane.get('layer')!r}")
    if lane.get("kind") not in LANE_KINDS:
        errs.append(f"lane.kind 非法（须 ∈ {LANE_KINDS}）: {lane.get('kind')!r}")
    status = lane.get("status")
    if status not in STATUSES:
        errs.append(f"lane.status 非法（须 ∈ {STATUSES}）: {status!r}")

    v = lane.get("verification")
    if v is None:
        v = {}
    elif not isinstance(v, dict):
        errs.append(f"lane.verification 须为 object，实际是 {type(v).__name__}")
        v = {}
    if _is_placeholder(v.get("method")):
        errs.append("verification.method 为空 —— 不允许存在「不知道怎么验」的泳道（人工测试也是方法）")
    if _is_placeholder(v.get("strength")):
        errs.append("verification.strength 为空 —— 模型 MUST 自陈该方法证明了什么、盲区是什么")
    ex = v.get("executor")
    if ex not in EXECUTORS:
        errs.append(f"verification.executor 非法（须 ∈ {EXECUTORS}）: {ex!r}")
    if ex == "human":
        if _is_placeholder(v.get("why_not_scriptable")):
            errs.append("executor=human MUST 写 why_not_scriptable（为什么程序跑不了）")
        if _is_placeholder(v.get("human_steps")):
            errs.append("executor=human MUST 写 human_steps（用户按什么方式来做）")

    raw_blocked = lane.get("blocked_by")
    if raw_blocked is None:
        blocked = ""
    else:
        checked_blocked = _checked(errs, _require_str, raw_blocked, "lane.blocked_by")
        blocked = checked_blocked.strip() if checked_blocked is not None else ""
    if status == "scaffolded" and not blocked:
        errs.append("scaffolded MUST 带非空 blocked_by")
    if status == "scaffolded" and blocked.lower() in PLACEHOLDERS:
        errs.append(f"blocked_by 敷衍（{blocked!r}）—— MUST 含可辨认的修复指引")
    if status == "verified":
        if blocked:
            errs.append("verified 泳道 MUST NOT 残留 blocked_by（绿泳道挂着「本机无 X」= 文档在说谎）")
        ev = v.get("evidence")
        if not isinstance(ev, dict):
            ev = {}
        for k in ("at_commit", "method_digest", "attested_by"):
            if not ev.get(k):
                errs.append(f"verified MUST 有 evidence.{k}")

    deps = lane.get("deps")
    if deps is not None and not isinstance(deps, list):
        errs.append(f"lane.deps 须为数组，实际是 {type(deps).__name__}")
        deps = []
    for d in deps or []:
        if not isinstance(d, dict):
            errs.append("deps[] 的元素须为 object")
            continue
        if "owned_by" in d:
            errs.append("deps[].owned_by 已删除（07 附录 A16：「运行时派生」的锚不存在——"
                        "skill 不知道 recipe 内部启动了什么）")
        if d.get("kind") not in DEP_KINDS:
            errs.append(f"deps[].kind 非法: {d.get('kind')!r}")
    return errs


def plan_snapshot(lane):
    """CAS 快照 —— 覆盖整个不可变的 verification plan。

    仅比对 status 不够：verify-lane 在无锁状态下读了这些字段去跑数分钟，期间另一
    session 可改它们而保持 status 不变（它自己的 CAS 照样通过）⇒ 旧验证回写成功。
    尤其 executor 与 kind：lane 从 script/pure 被改成 human/hardware，旧脚本仍能
    通过只比 status 的 CAS 回写。

    fail-closed：lane / lane.verification 若非预期类型直接 raise SchemaInvalid——
    这是计算函数（非 errs 累积式校验器），类型不符没有「继续算」的意义。
    """
    _require_dict(lane, "lane")
    raw_v = lane.get("verification")
    v = {} if raw_v is None else _require_dict(raw_v, "lane.verification")
    snap = {k: lane.get(k) for k in SNAPSHOT_KEYS}
    snap.update({k: v.get(k) for k in SNAPSHOT_VERIF_KEYS})
    blob = json.dumps(snap, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------- strategy（测试三层框架）----------

def validate_strategy(data):
    if not isinstance(data, dict):
        return [f"strategy 顶层须为 object，实际是 {type(data).__name__}"]
    errs = []
    layers = data.get("layers")
    if layers is None:
        layers = {}
    elif not isinstance(layers, dict):
        return [f"layers 须为 object，实际是 {type(layers).__name__}"]
    for name in LAYERS:
        L = layers.get(name)
        if not L:
            errs.append(f"三层框架缺 {name} 层 —— 一层都不许留白")
            continue
        if not isinstance(L, dict):
            errs.append(f"{name} 层须为 object，实际是 {type(L).__name__}")
            continue
        st = L.get("status")
        if st not in LAYER_STATUSES:
            errs.append(f"{name}.status 非法（须 ∈ {LAYER_STATUSES}）: {st!r}")
            continue

        if st == "not-applicable":
            # ①-④ 槽豁免（否则是逼模型为「不做这件事」编造废话 = 填表游戏）
            if _is_placeholder(L.get("reason")):
                errs.append(f"{name}: not-applicable MUST 有 reason")
            if _is_placeholder(L.get("consequence")):
                errs.append(f"{name}: not-applicable MUST 有 consequence —— "
                            f"不写后果，「不适用」就是一个不需要负责的逃生舱")
            continue

        for slot in _CONTENT_SLOTS:
            if _is_placeholder(L.get(slot)):
                errs.append(f"{name}.{slot} 为空 —— 五槽不许留白")

        if st == "implemented":
            if not L.get("lane_ids"):
                errs.append(f"{name}: implemented MUST 有 lane_ids —— "
                            f"声称已实现却没有泳道 = 文档在说谎")
        elif st == "manual":
            if _is_placeholder(L.get("why_not_scriptable")):
                errs.append(f"{name}: manual MUST 有 why_not_scriptable")
            if _is_placeholder(L.get("human_steps")):
                errs.append(f"{name}: manual MUST 有 human_steps —— "
                            f"「人工」不是「这层没人管」的同义词")
    return errs


# ---------- IO ----------

def _load(root, rel):
    p = Path(root) / rel
    if not p.exists():
        raise SchemaInvalid(f"{rel} 不存在")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaInvalid(f"{rel} JSON 语法错误: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaInvalid(f"{rel} 顶层须为 object，实际是 {type(data).__name__}")
    ver = data.get("schema_version")
    if ver is None:
        raise SchemaInvalid(f"{rel} 缺 schema_version —— fail-closed")
    # bool 是 int 子类：isinstance(True, int) 恒真，须显式排除，否则
    # schema_version=true 会被静默当作合法的版本 1 接受。
    if isinstance(ver, bool) or not isinstance(ver, int):
        raise SchemaInvalid(f"{rel} schema_version 非整数: {ver!r}")
    if ver > SCHEMA_VERSION:
        raise SchemaTooNew(
            f"{rel} 的 schema_version={ver} 高于本实现已知的 {SCHEMA_VERSION} —— "
            f"skill 版本过旧，请升级。MUST NOT 尽力解析。"
        )
    # ver < SCHEMA_VERSION：v1 阶段无需处理（当前只有 v1）。后续版本演进 MUST 在引入
    # 该版本的 change 里显式定义策略（fail-closed 要求迁移 / migrate 子命令 / 只读兼容）。
    return data


def _save(root, rel, data, validate):
    errs = validate(data)
    if errs:
        raise SchemaInvalid("; ".join(errs))
    data = dict(data)
    data["schema_version"] = SCHEMA_VERSION
    atomic_write(Path(root) / rel, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_lanes(root):
    return _load(root, LANES_REL)


def save_lanes(root, data):
    def _v(d):
        if not isinstance(d, dict):
            return [f"lanes 文件顶层须为 object，实际是 {type(d).__name__}"]
        lanes = d.get("lanes")
        if lanes is None:
            lanes = []
        elif not isinstance(lanes, list):
            return [f"lanes 须为数组，实际是 {type(lanes).__name__}"]

        errs = []
        ids = [l.get("id") if isinstance(l, dict) else None for l in lanes]
        # id 可能是 list/dict 等不可哈希类型（模型误结构化）——不可哈希的排除出重复检测
        # 集合（{...} 需要哈希每个元素才能判重，混入不可哈希值会直接 TypeError）；
        # 该类 id 自身的类型错误由下面逐 lane 的 validate_lane 单独报出，不在此处失控崩溃。
        hashable_ids = []
        for i in ids:
            if i is None:
                continue
            try:
                hashable_ids.append(_require_hashable_id(i, "lane.id"))
            except SchemaInvalid:
                continue
        dupes = {i for i in hashable_ids if hashable_ids.count(i) > 1}
        if dupes:
            # key=str：dupes 里可能混着不同可比较类型（如 str 与 int 各自重复），
            # sorted() 默认比较在跨类型时会直接 TypeError —— 用 str 统一排序键规避。
            errs.append(f"lane id 重复: {sorted(dupes, key=str)}")
        for lane in lanes:
            prefix = lane.get("id") if isinstance(lane, dict) else "?"
            errs += [f"[{prefix}] {e}" for e in validate_lane(lane)]
        return errs
    _save(root, LANES_REL, data, _v)


def load_strategy(root):
    return _load(root, STRATEGY_REL)


def save_strategy(root, data):
    _save(root, STRATEGY_REL, data, validate_strategy)
