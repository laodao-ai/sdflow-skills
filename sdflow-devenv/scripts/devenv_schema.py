"""两份 JSON 侧文件的 schema —— 标准库 json，零第三方依赖。

【职责边界，MUST 守】（07 §3.3 · §0.0 闸门 0「形态问」）

    schema  拦「结构」—— 字段在不在 · 枚举合不合法 · 类型对不对
    lint    报「内容」—— 五槽留白 · 不适用没写后果 · blocked_by 敷衍

判据 = 【人看不看得见】：
  - 「lane.status 写成 'verifed'」——人看不见（它长得像个正常值），⇒ schema fail-closed 拦。
  - 「e2e 层五个槽全空」——人打开 testing-strategy.md 一眼就看见，⇒ lint 报 + 渲染显眼 +
    收尾报告逐条列，MUST NOT 拦。

【为什么内容检查 MUST NOT 拦】（07 §2.2 round-3 对抗镜实证）：
拦一个空的 strength，并不会让模型写出好的 strength——只会让它写出【一句话】。
机械层会【奖励空话、惩罚诚实】。而 skill 是副驾，它的职责是【问到了】，不是【填满了】：
人当场答不上来 ⇒ 原样落 PENDING，这是合法产物（07 §3.1）。

【为什么落 JSON 而非 frontmatter】：嵌套 lanes[]（列表 × 中文自由文本 × 带冒号的值）
没有可用的解析/序列化方案——目标环境无 PyYAML，而唯一先例 sad_schema.parse_frontmatter
是手搓的扁平标量解析器。

【本文件没有什么】（三条碑文，勿手贱加回来）：
  - 无 atomic_write / 文件锁 / CAS —— devenv_lock 已删（07 A23 闸门 3：防一个不会发生的
    并发；JSON 写坏的后果是「重跑一次」，真代码的护栏是 git）。
  - 无 file_digests / method_at_verify 时效锚 —— devenv_digest 已删（07 A23 闸门 0：
    「上次验证后文件改没改」该由 continue 时问一句 + git 回答，不该由 410 行 sha256 拦）。
  - 无 make 语法解析 —— 07 A21（无界语法面禁手搓；target 能不能跑，让 make 自己判）。
"""
import json
from pathlib import Path

SCHEMA_VERSION = 1

LANES_REL = "openspec/architecture/.devenv-lanes.json"
STRATEGY_REL = "openspec/architecture/.devenv-strategy.json"

LAYERS = ("unit", "integration", "e2e")
SLOTS = ("how", "convention", "process", "tooling", "status")

LANE_KINDS = ("external-dep", "ui", "lang-bridge", "hardware", "pure")
STATUSES = ("planned", "scaffolded", "verified")
EXECUTORS = ("script", "human")
DEP_KINDS = ("compose", "host-service", "port", "toolchain", "testcontainer")
LAYER_STATUSES = ("implemented", "not-applicable", "manual")

# 「我还没想好」的合法值（07 §3.1）—— 副驾问了、人当场答不上来，如实落它。
# schema 接受；lint 计数并要求渲染显眼 + 收尾报告逐条列出。
PENDING = "⚠️ 待定"

# verified 的证据 = 一次历史执行的坐标。无时效 digest（A23）。
EVIDENCE_KEYS = ("at_commit", "at_time", "exit", "attested_by")
ATTESTORS = ("script", "human")


class SchemaInvalid(Exception):
    pass


class SchemaTooNew(Exception):
    pass


def _enum(errs, val, allowed, field):
    if val not in allowed:
        errs.append(f"{field} 非法（须 ∈ {allowed}）: {val!r}")


def _str_field(errs, obj, key, field):
    """字段必须存在且为 string。空串/PENDING 都算存在——内容够不够是 lint 的事。"""
    v = obj.get(key)
    if v is None:
        errs.append(f"{field} 缺失")
    elif not isinstance(v, str):
        errs.append(f"{field} 须为 string，实际是 {type(v).__name__}")


# ---------- lanes ----------

def validate_lane(lane):
    """只查结构与枚举。内容完整性归 devenv_lint（只报不拦）。"""
    if not isinstance(lane, dict):
        return [f"lane 须为 object，实际是 {type(lane).__name__}"]
    errs = []

    _str_field(errs, lane, "id", "lane.id")
    _enum(errs, lane.get("layer"), LAYERS, "lane.layer")
    _enum(errs, lane.get("kind"), LANE_KINDS, "lane.kind")
    status = lane.get("status")
    _enum(errs, status, STATUSES, "lane.status")

    v = lane.get("verification")
    if not isinstance(v, dict):
        errs.append(f"lane.verification 须为 object，实际是 {type(v).__name__}")
        return errs

    # method 是结构性必需：verify-lane 要拿它去 fork 执行，没有它这条泳道跑不了。
    # （这不是「防漏」——是「B 层的手需要它才能动」。）
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
            errs.append("deps[].owned_by 已删除（07 A16：「运行时派生」的锚不存在——"
                        "skill 不知道 recipe 内部启动了什么）")
        _enum(errs, d.get("kind"), DEP_KINDS, "deps[].kind")
    return errs


# ---------- strategy（测试三层框架）----------

def validate_strategy(data):
    """只查三层齐不齐 + status 枚举。五槽留白归 devenv_lint（只报不拦）。"""
    if not isinstance(data, dict):
        return [f"strategy 顶层须为 object，实际是 {type(data).__name__}"]
    layers = data.get("layers")
    if layers is None:
        layers = {}
    if not isinstance(layers, dict):
        return [f"layers 须为 object，实际是 {type(layers).__name__}"]

    errs = []
    for name in LAYERS:
        L = layers.get(name)
        if L is None:
            # 三层【必须都在】—— 这是核心承诺的结构骨架（07 §2.2「一层都不许留白」）。
            # 注意：层【在】但五个槽全是 PENDING 是【合法】的（人还没想好）——那由 lint 报。
            errs.append(f"三层框架缺 {name} 层 —— 一层都不许留白")
            continue
        if not isinstance(L, dict):
            errs.append(f"{name} 层须为 object，实际是 {type(L).__name__}")
            continue
        _enum(errs, L.get("status"), LAYER_STATUSES, f"{name}.status")
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
    # bool 是 int 的子类 —— isinstance(True, int) 恒真，须显式排除，
    # 否则 schema_version=true 会被静默当成合法版本号接受。
    if isinstance(ver, bool) or not isinstance(ver, int):
        raise SchemaInvalid(
            f"{rel} 的 schema_version 须为整数，实际是 {type(ver).__name__} —— fail-closed"
        )
    if ver > SCHEMA_VERSION:
        raise SchemaTooNew(
            f"{rel} 的 schema_version={ver} 高于本实现已知的 {SCHEMA_VERSION} —— "
            f"skill 版本过旧，请升级。MUST NOT 尽力解析。"
        )
    return data


def _save(root, rel, data, validate):
    errs = validate(data)
    if errs:
        raise SchemaInvalid("; ".join(errs))
    data = dict(data)
    data["schema_version"] = SCHEMA_VERSION
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_lanes(root):
    return _load(root, LANES_REL)


def save_lanes(root, data):
    def _v(d):
        if not isinstance(d, dict):
            return [f"lanes 文件顶层须为 object，实际是 {type(d).__name__}"]
        lanes = d.get("lanes")
        if lanes is None:
            lanes = []
        if not isinstance(lanes, list):
            return [f"lanes 须为数组，实际是 {type(lanes).__name__}"]

        errs = []
        # id 只在【都是 string】时才判重（非 string 的 id 由 validate_lane 各自报出，
        # 不在这里因 unhashable 而崩溃）。
        ids = [l["id"] for l in lanes
               if isinstance(l, dict) and isinstance(l.get("id"), str)]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            errs.append(f"lane id 重复: {dupes}")
        for lane in lanes:
            prefix = lane.get("id") if isinstance(lane, dict) else "?"
            errs += [f"[{prefix}] {e}" for e in validate_lane(lane)]
        return errs

    _save(root, LANES_REL, data, _v)


def load_strategy(root):
    return _load(root, STRATEGY_REL)


def save_strategy(root, data):
    _save(root, STRATEGY_REL, data, validate_strategy)
