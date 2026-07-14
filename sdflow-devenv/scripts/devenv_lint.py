"""devenv lint —— 【只报不拦】。

【它 MUST NOT 做什么】（adr/0021 · 07 §0.0 闸门 0）

  ❌ 因为「待定太多」而 fail-closed 拦住流程
  ❌ 因为「不适用没写后果」而拒绝写出文档
  ❌ 任何形式的「填满了才让走」

【为什么】：skill 是副驾，不是审计官。
  「六槽有没有留白」是【人一眼就能看见】的东西——用户打开 testing-strategy.md，
  十五个格子，空的就是空的。为一个人类零成本可验证的不变量建一道闸机，
  是把「提醒」做成了「拦截」。

  而拦截会【奖励空话、惩罚诚实】：拦一个空的 blind_spots，并不会让模型写出好的
  blind_spots，只会让它写出【一句话】。

【它做什么】：把代价【摆到人眼前】。
  - 数出还有几格待定，渲染成 testing-strategy.md 顶部的横幅
  - 算出 SAD 里哪些 contract 还没有泳道覆盖
  - 挑出敷衍的 blocked_by
  然后【退出码 0，放行】。

退出码：
  0  正常（有 findings 也是 0 —— 只报不拦）
  2  fail-closed：数据坏了（JSON 语法错 / schema 不合法 / 文件不存在）
     ——【这个才拦】。它拦的是「人看不见的」（坏 JSON 渲染不出来，用户只看到空白）。
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import devenv_schema as S  # noqa: E402

# blocked_by 写成这些 == 没写。人看得见，但值得当场点出来。
LAZY = {"", "-", "—", "todo", "TODO", "tbd", "TBD", "待定", "待修复",
        "环境问题", "稍后处理", "n/a", "N/A"}


def _lazy(v):
    return not isinstance(v, str) or v.strip() in LAZY or len(v.strip()) < 6


def pending_slots(data):
    """还有哪些格子是 `⚠️ 待定`。返回 [(layer, slot), …]"""
    out = []
    for name in S.LAYERS:
        L = (data.get("layers") or {}).get(name)
        if not isinstance(L, dict) or L.get("status") == S.NOT_APPLICABLE:
            continue
        for slot in S.CONTENT_SLOTS:
            v = L.get(slot)
            if not isinstance(v, str) or v.strip() in ("", S.PENDING):
                out.append((name, slot))
    return out


def total_slots(data):
    """分母 —— 不适用的层不计入（它的槽是豁免的）。"""
    n = 0
    for name in S.LAYERS:
        L = (data.get("layers") or {}).get(name)
        if isinstance(L, dict) and L.get("status") == S.NOT_APPLICABLE:
            continue
        n += len(S.CONTENT_SLOTS)
    return n


def banner(data):
    """testing-strategy.md 顶部的代价横幅。无待定 ⇒ 返回 None（不渲染横幅）。

    这是 adr/0021 的落点：【代价可见 > 机械拦截】。
    """
    pend = pending_slots(data)
    if not pend:
        return None
    total = total_slots(data)
    by_layer = {}
    for layer, slot in pend:
        by_layer.setdefault(layer, []).append(slot)
    detail = " · ".join(f"{k} 层缺 {', '.join(v)}" for k, v in by_layer.items())
    return (f"⚠️ 本框架 {len(pend)}/{total} 格待定，尚不构成一份可用的测试策略。\n"
            f"   待补：{detail}")


def uncovered_contracts(data, sad_contracts):
    """SAD 里哪些 contract 还没有任何泳道 covers 它。

    机械算差集 —— 但【差集是拿去问人的，不是拿去拦人的】：
    「§5.3 这条 contract 还没有泳道覆盖，要建一条吗？还是明确不覆盖（记后果）？」
    """
    covered = set()
    for lane in data.get("lanes") or []:
        if isinstance(lane, dict):
            covered.update(lane.get("covers") or [])
    return [c for c in sad_contracts if c not in covered]


def lazy_blockers(data):
    """blocked_by 写成「TODO」「环境问题」这种 —— 它没告诉任何人下一步该干嘛。"""
    out = []
    for lane in data.get("lanes") or []:
        if not isinstance(lane, dict) or lane.get("status") != "scaffolded":
            continue
        if _lazy(lane.get("blocked_by")):
            out.append((lane.get("id"), lane.get("blocked_by")))
    return out


def unverified_lanes(data):
    return [(l.get("id"), l.get("status"), l.get("blocked_by"))
            for l in data.get("lanes") or []
            if isinstance(l, dict) and l.get("status") != "verified"]


def report(data, sad_contracts=()):
    """人读报告。返回字符串。【永远不 raise，永远不拦】。"""
    lines = []

    b = banner(data)
    if b:
        lines += [b, ""]
    else:
        lines += ["✅ 三层框架六槽已答满（含「不适用 + 后果」）。", ""]

    lanes = data.get("lanes") or []
    if lanes:
        lines.append("泳道状态：")
        for lane in lanes:
            if not isinstance(lane, dict):
                continue
            st = lane.get("status")
            mark = {"verified": "✅", "scaffolded": "⏸", "planned": "○"}.get(st, "?")
            v = lane.get("verification")
            ev = (v.get("evidence") if isinstance(v, dict) else None) or {}
            if st == "verified":
                who = "" if ev.get("attested_by") == "script" else "（人工确认）"
                tail = f"verified @ {str(ev.get('at_commit'))[:7]} · {ev.get('at_time')}{who}"
            elif st == "scaffolded":
                tail = f"scaffolded —— {lane.get('blocked_by')}"
            else:
                tail = str(st)
            # id 可能缺失/非 str（坏数据）—— 报告 MUST NOT 因此崩掉：
            # 崩了人就什么都看不见，而「看得见」正是 lint 存在的唯一理由。
            lid = lane.get("id")
            lid = lid if isinstance(lid, str) else "<无 id>"
            lines.append(f"   {mark} {lid:<16} {tail}")
        lines.append("")

    lazy = lazy_blockers(data)
    if lazy:
        lines.append("⚠️ 这些 blocked_by 没告诉任何人下一步该干嘛：")
        lines += [f"   {i}: {b!r}" for i, b in lazy]
        lines.append("")

    unc = uncovered_contracts(data, sad_contracts)
    if unc:
        lines.append("⚠️ SAD 里这些 contract 还没有泳道覆盖 —— 要建一条，还是明确不覆盖（记后果）？")
        lines += [f"   {c}" for c in unc]
        lines.append("")

    lines.append("（本报告只呈现，不拦截 —— 见 adr/0021）")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="devenv lint —— 只报不拦")
    ap.add_argument("--root", required=True)
    args = ap.parse_args(argv)

    try:
        data = S.load(args.root)
    except (S.SchemaInvalid, S.SchemaTooNew) as exc:
        # 【这个才 fail-closed】：坏 JSON 是「人看不见的」——
        # 它渲染不出来，用户只会看到一份空白文档，还以为是 skill 没跑。
        print(f"[devenv_lint] FAIL: {exc}", file=sys.stderr)
        return 2

    errs = S.validate(data)
    if errs:
        print("[devenv_lint] FAIL: .devenv.json 不合法：", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    print(report(data))
    return 0   # ← 永远 0。有 15 格待定也是 0。


if __name__ == "__main__":
    sys.exit(main())
