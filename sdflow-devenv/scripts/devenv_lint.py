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

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
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


ENV_MD = "openspec/architecture/environments.md"
SAD_MD = "openspec/architecture/sad.md"


def sad_contracts(root):
    """SAD §5 声明了哪些 contract。→ [name…]；无 SAD ⇒ None（≠ 空集，见下）。

    【单一源】：contract 行格式的 owner 是 `sdflow-architecture`（它是 SAD 的 producer）。
    这里【import 它的 scan_contract_names】，MUST NOT 在本文件另抄一份正则 —— 抄一份就是
    一个新的漂移面：它改了行格式，我们静默算出空集，而空集长得跟「全都覆盖了」一模一样。

    【None vs []】：
      None = 【算不了】（无 SAD / 装不到 sad_schema）⇒ 调用方 MUST 响亮说「对账失效」
      []   = 【算过了，SAD 里就没有 contract】
    把这两者混成一个空列表，就是「佯装算过」——正是 spec §无 SAD 时响亮降级 要防的。
    """
    p = Path(root) / SAD_MD
    if not p.exists():
        return None
    sib = Path(__file__).resolve().parents[2] / "sdflow-architecture" / "scripts"
    if str(sib) not in sys.path:
        sys.path.insert(0, str(sib))
    try:
        import sad_schema
    except ImportError:
        return None                      # 未装 sdflow-architecture ⇒ 算不了，不佯装
    text = p.read_text(encoding="utf-8")
    seen, out = set(), []
    for _, name in sad_schema.scan_contract_names(text):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def env_pending(root):
    """environments.md 里还有几个 `⚠️ 待定`。

    【为什么这不是「解析 Markdown」】（基准 5：有界可手写 / 无界禁手搓）：
    我们【数一个固定字符串出现了几次】—— 不切章节、不判层级、不认结构。
    这个「语法面」只有一个元素（PENDING 这个字面量），穷举得完 ⇒ 合法。

    ⚠️ MUST NOT 演化成「找到 §1.5 这一节、切出它的内容、判断非空」——
    那就是又一个手搓 Markdown 解析器（07 A20），会在 fence / 嵌套 / 变体标题上罢工。
    要更细的粒度，就问人，别猜。
    """
    p = Path(root) / ENV_MD
    if not p.exists():
        return None                       # 没铺过 ⇒ 不报（不是「没填」，是「还没到那一步」）
    return p.read_text(encoding="utf-8").count(S.PENDING)


def report(data, sad=(), root=None):
    """人读报告。返回字符串。【永远不 raise，永远不拦】。"""
    lines = []

    b = banner(data)
    if b:
        lines += [b, ""]
    else:
        lines += ["✅ 三层框架六槽已答满（含「不适用 + 后果」）。", ""]

    if root is not None:
        n = env_pending(root)
        if n:
            lines += [f"⚠️ environments.md 还有 {n}/10 槽待定 —— "
                      f"按 references/environments-template.md 逐槽问出来。",
                      "   （最贵的三槽：常见坑 · 回滚 · 构建副产物 —— "
                      "模型答不出来，只能问人，所以最容易被静默略过）", ""]
        elif n == 0:
            lines += ["✅ environments.md 十槽已答满。", ""]

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

    # SAD 差集。None = 【算不了】（无 SAD / 未装 sdflow-architecture）—— MUST 响亮说，
    # MUST NOT 静默当成「没有未覆盖的 contract」（那两者渲染出来长得一模一样）。
    if sad is None:
        lines += ["⚠️ **泳道覆盖对账失效** —— 读不到 SAD（`openspec/architecture/sad.md` 不存在，"
                  "或未装 `sdflow-architecture`）。",
                  "   测试策略只能靠读码猜，**可能漏掉边界**。建议先跑 `/sdflow-architecture`。", ""]
    else:
        unc = uncovered_contracts(data, sad)
        if unc:
            lines.append("⚠️ SAD 里这些 contract 还没有泳道覆盖 —— 要建一条，还是明确不覆盖（记后果）？")
            lines += [f"   {c}" for c in unc]
            lines.append("")
        elif sad:
            lines += [f"✅ SAD 的 {len(sad)} 条 contract 都有泳道覆盖（`covers` 声明；"
                      f"**真穿过了没有** 要靠冷审的覆盖镜问）。", ""]

    lines.append("（本报告只呈现，不拦截 —— 见 adr/0021）")
    return "\n".join(lines)


def render(root):
    """load + validate + report ——【外部调用方的唯一入口】。→ (ok: bool, text: str)

    【为什么要有这个函数】：`sdflow-maintain` 要把 lint 的结果【原样并入】它的扫描报告
    （spec `maintain-scan`）。让它自己去 load+validate+report，就是把这三步复制一份 ⇒ 必漂。
    ∴ 这里出一个函数，`main()` 和 maintain 【都调它】。

    ok=False ⇒ text 是错误说明（坏 JSON / schema 不合法）——那是唯一 fail-closed 的情形。
    """
    try:
        data = S.load(root)
    except (S.SchemaInvalid, S.SchemaTooNew) as exc:
        # 【这个才 fail-closed】：坏 JSON 是「人看不见的」——
        # 它渲染不出来，用户只会看到一份空白文档，还以为是 skill 没跑。
        return False, f"{exc}"

    errs = S.validate(data)
    if errs:
        return False, ".devenv.json 不合法：\n" + "\n".join(f"  - {e}" for e in errs)

    return True, report(data, sad=sad_contracts(root), root=root)


def main(argv=None):
    ap = argparse.ArgumentParser(description="devenv lint —— 只报不拦")
    ap.add_argument("--root", required=True)
    args = ap.parse_args(argv)

    ok, text = render(args.root)
    if not ok:
        print(f"[devenv_lint] FAIL: {text}", file=sys.stderr)
        return 2

    print(text)
    return 0   # ← 永远 0。有 15 格待定也是 0。


if __name__ == "__main__":
    sys.exit(main())
