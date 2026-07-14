"""devenv scaffold —— B 层（手）：建造，不是评估。

子命令：
  init         preflight + 模式分流（退出码驱动）
  set-layer    写三层框架的槽（六槽中要问的五个）
  set-lane     写泳道（planned / scaffolded 两态；verified MUST 走 verify-lane）
  verify-lane  ⭐ 亲自 fork 执行 verification.method，拿真实 exit code
  confirm-lane 人工验证后，经人门写入（attested_by: human）
  render       .devenv.json → testing-strategy.md
  inject       opsx-devenv 托管块 → CLAUDE / AGENTS / README / INDEX

【MUST NOT】（07 附录 A21 · A23 · A24 · A26 · adr/0022）
  ❌ 解析 Makefile / shell / 任何语言的语法 —— 无界语法面禁手搓。
     「命令能不能跑」由 verify-lane 真跑一遍，让工具自己判。
  ❌ 猜用户文件里原来有什么 —— 要知道就问人。
  ❌ 删除用户的任何文件 —— 爆炸半径不受控（引用可能在仓外）。
  ❌ 时效 digest / 文件锁 / CAS。
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import devenv_schema as S  # noqa: E402
from devenv_paths import PathEscape, contain  # noqa: E402

ARCH_DIR = "openspec/architecture"
STRATEGY_MD = f"{ARCH_DIR}/testing-strategy.md"
ENV_MD = f"{ARCH_DIR}/environments.md"
LOG_MD = f"{ARCH_DIR}/devenv-log.md"

MARK_START = "<!-- opsx-devenv:start -->"
MARK_END = "<!-- opsx-devenv:end -->"

DEFAULT_TIMEOUT = 300


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _head(root):
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "(no-git)"
    except (OSError, subprocess.SubprocessError):
        return "(no-git)"


def _log(root, line):
    p = Path(root) / LOG_MD
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# devenv-log\n\n> append-only。continue 断点恢复靠它。\n\n",
                     encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- `{_now()}` {line}\n")


# ---------- environments.md：模版骨架（人写区，零机械渲染）----------
#
# 【为什么它没有 JSON 载体】（07 §2.1 · 附录 A27）：
# 这十槽是【长自由文本】（「新人最容易卡在哪一步」「回滚怎么做」「有没有退不回去的东西」）。
# 06 的接地实测：17 个槽里 SAD 真投影只有 2 个，其余是纯人写 —— 而【纯人写区恰恰是全篇
# 最高价值的部分】。把它强行 JSON 化，只会让人写得更烂。
#
# 【但「有模版 + 逐槽问出口」和「有 JSON 载体」是两件事】：
# skill 铺骨架（下面这份）+ 按 references/environments-template.md 逐槽问 + 人填。
# 它是【直写 Markdown】，没有 DO-NOT-EDIT 区块 —— 铺完就归人 own，skill 不再覆盖。
#
# 🔴 【骨架里 S.PENDING 只许出现在槽位上，MUST NOT 出现在说明文字/图例里】：
# lint 的 env_pending 是【数这个字面量出现了几次】（基准 5：语法面只有一个元素 ⇒ 不必解析）。
# 该做法成立的前提是【这个字面量只有一个意思 = 一个未答的槽】—— 维持这个前提是本骨架的责任，
# 不是 lint 的责任（让 lint 去认「这行是图例不是槽」，就是又一个手搓 Markdown 解析器）。
# mqtt-console 试点实证：模型现场自创的出处图例里写了 `[⚠️ 待定] = 还没答案`，
# env_pending 当场恒 +1（报 3/10，真待定只有 2）。故图例改为【指称而不复现】该标记，
# 并把这份图例收进骨架 —— 模型就不会再自己发明一份。
# 守卫：tests/test_lint.py::test_env_pending_counted_but_not_blocking 断言刚铺完 == len(ENV_SLOTS)。

ENV_SLOTS = [
    ("1.1", "前置工具链"),
    ("1.2", "本地依赖服务"),
    ("1.3", "构建 + 本地运行"),
    ("1.4", "构建副产物"),
    ("1.5", "常见坑"),
    ("3.1", "目标平台 + 依赖版本"),
    ("3.2", "配置项清单"),
    ("3.3", "发布流程"),
    ("3.4", "回滚"),
    ("3.5", "架构决策指针"),
]

ENV_SKELETON = f"""# 环境：搭建与发布

> 真相源。**测试怎么跑 → [`testing-strategy.md`](./testing-strategy.md)**（本文档不复述）。
>
> 本文档由 `/sdflow-devenv` 铺骨架、**按 `references/environments-template.md` 逐槽问出来**。
> **此后归你 own** —— skill 不会覆盖它。
>
> **出处标记**（每条内容后的方括号）：`[实测]` 本机真跑过 · `[代码]` 从源码读出 ·
> `[人拍]` 操作者拍板 · `[调研]` 模型查证后给的推荐，人已确认。
> **没答出来的槽，保留 skill 铺下的那个黄底待办标记**（收尾报告会逐条列出）。

## 1. dev —— 怎么在本机跑起来

### 1.1 前置工具链
{S.PENDING}

### 1.2 本地依赖服务
{S.PENDING}

### 1.3 构建 + 本地运行
{S.PENDING}

### 1.4 构建副产物
{S.PENDING}

### 1.5 ⭐ 常见坑
{S.PENDING}

## 2. 测试

测试策略与执行方式 → [`testing-strategy.md`](./testing-strategy.md)

## 3. deploy —— 怎么发出去

### 3.1 目标平台 + 依赖版本
{S.PENDING}

### 3.2 配置项清单
{S.PENDING}

### 3.3 发布流程
{S.PENDING}

### 3.4 ⭐ 回滚
{S.PENDING}

### 3.5 架构决策指针
{S.PENDING}
"""


def _seed_environments(root):
    """铺 environments.md 骨架。已存在 ⇒ 【不碰】（它归人 own）。"""
    p = Path(root) / ENV_MD
    if p.exists():
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(ENV_SKELETON, encoding="utf-8")
    return len(ENV_SLOTS)


# ---------- init：preflight + 模式分流 ----------

def cmd_init(args):
    root = Path(args.root).resolve()

    if not (root / "openspec").is_dir():
        print("[devenv] 无 openspec/ 布局 —— 先跑 /sdflow-init", file=sys.stderr)
        return 3

    sad = (root / ARCH_DIR / "sad.md").exists()
    if not sad:
        # 显式降级，不 fail-closed。MUST NOT 佯装有 SAD。
        print("⚠️  sad.md 缺失 —— 拿不到子系统 contract 清单：", file=sys.stderr)
        print("    · 泳道覆盖对账【失效】", file=sys.stderr)
        print("    · 测试策略只能靠读码猜，【可能漏掉边界】", file=sys.stderr)
        print("    强烈建议先跑 /sdflow-architecture。继续运行中……\n", file=sys.stderr)

    if (root / S.DEVENV_REL).exists():
        if not args.on_exists:
            print("[devenv] 已有本 skill 产物 —— 带 --on-exists continue|replan 重跑",
                  file=sys.stderr)
            return 4
        _log(root, f"重入：mode={args.on_exists}")
        print(f"mode={args.on_exists} · sad={'ok' if sad else 'missing'}")
        return 0

    S.save(root, S.blank())
    n_env = _seed_environments(root)
    _log(root, f"起手：mode=new · sad={'ok' if sad else 'missing'}")
    print(f"mode=new · sad={'ok' if sad else 'missing'}")
    print(f"已建 {S.DEVENV_REL}（三层框架，十五格全待定 —— 这是合法起点）")
    if n_env:
        print(f"已铺 {ENV_MD}（{n_env} 槽全待定 —— 按 references/environments-template.md 逐槽问）")
    return 0


# ---------- set-layer / set-lane ----------

def cmd_set_layer(args):
    root = Path(args.root).resolve()
    data = S.load(root)
    layers = data.setdefault("layers", {})

    if args.not_applicable:
        if not (args.reason and args.consequence):
            print("[devenv] `不适用` MUST 同时给 --reason 和 --consequence —— "
                  "不写后果，它就是一个不需要负责的逃生舱", file=sys.stderr)
            return 1
        layers[args.layer] = {"status": S.NOT_APPLICABLE,
                              "reason": args.reason,
                              "consequence": args.consequence}
    else:
        L = layers.setdefault(args.layer, {s: S.PENDING for s in S.CONTENT_SLOTS})
        L.pop("status", None)          # 层状态是投影，不手写（A25）
        L.setdefault("lane_ids", [])
        for slot in S.CONTENT_SLOTS:
            v = getattr(args, slot)
            if v is not None:
                L[slot] = v

    S.save(root, data)
    _log(root, f"set-layer {args.layer}")
    print(f"✓ {args.layer}")
    return 0


def cmd_set_lane(args):
    root = Path(args.root).resolve()
    data = S.load(root)

    # 🔴 verified MUST 由 verify-lane / confirm-lane 产出 —— 脚本亲自跑，或人门写入。
    # 这【不是防伪】（作为防伪它一文不值：method 设成 `true` 就能击穿）。
    # 它的价值是：脚本顺手就能拿到真实的 exit code，当场告诉操作者「这条跑得起来 / 缺 mosquitto」。
    if args.status == "verified":
        print("[devenv] set-lane 不产出 verified —— 用 verify-lane（脚本跑）"
              "或 confirm-lane（人跑 + 人门）", file=sys.stderr)
        return 5

    for rel in filter(None, [args.smoke]):
        try:
            contain(root, rel)
        except PathEscape as exc:
            print(f"[devenv] 路径越界: {exc}", file=sys.stderr)
            return 2

    lanes = data.setdefault("lanes", [])
    lane = next((l for l in lanes if l.get("id") == args.id), None)
    if lane is None:
        lane = {"id": args.id, "deps": []}
        lanes.append(lane)

    lane["layer"] = args.layer or lane.get("layer")
    lane["status"] = args.status
    lane["source"] = args.source or lane.get("source") or "（待注记）"
    if args.smoke:
        lane["smoke"] = args.smoke
    if args.covers:
        lane["covers"] = args.covers

    v = lane.setdefault("verification", {})
    if args.method:
        v["method"] = args.method
    v.setdefault("executor", args.executor or "script")
    if args.executor:
        v["executor"] = args.executor
    if args.strength:
        v["strength"] = args.strength
    if args.why_not_scriptable:
        v["why_not_scriptable"] = args.why_not_scriptable
    if args.human_steps:
        v["human_steps"] = args.human_steps

    if args.status == "scaffolded":
        if not args.blocked_by:
            print("[devenv] scaffolded MUST 带 --blocked-by（含可辨认的修复指引）—— "
                  "「跑不绿」是合法状态，「跑不绿却不说为什么」不是", file=sys.stderr)
            return 1
        lane["blocked_by"] = args.blocked_by
    else:
        lane.pop("blocked_by", None)

    # 挂进对应层的 lane_ids
    L = data.setdefault("layers", {}).get(lane["layer"])
    if isinstance(L, dict) and L.get("status") != S.NOT_APPLICABLE:
        ids = L.setdefault("lane_ids", [])
        if args.id not in ids:
            ids.append(args.id)

    S.save(root, data)
    _log(root, f"set-lane {args.id} → {args.status}")
    print(f"✓ {args.id} → {args.status}")
    return 0


# ---------- ⭐ verify-lane：真 fork 执行 ----------

def cmd_verify_lane(args):
    """脚本【亲自】fork 执行 verification.method，捕获真实 exit code。

    这是 skill 唯一「产生新事实」的地方。它在【建造】，不在评估。

    🔴 失败不重试、不 debug —— 跑一次，失败就如实记 blocked_by（诊断可以给，修复不做）。
       一旦允许 debug，它会在一条泳道上耗光整个 session。跑不绿本来就是合法状态。
    """
    root = Path(args.root).resolve()
    data = S.load(root)
    lane = next((l for l in data.get("lanes") or [] if l.get("id") == args.id), None)
    if lane is None:
        print(f"[devenv] 无此泳道: {args.id}", file=sys.stderr)
        return 1

    v = lane.get("verification") or {}
    method = v.get("method")
    if not method or not str(method).strip():
        print(f"[devenv] {args.id} 没有 verification.method —— 跑什么？", file=sys.stderr)
        return 1

    if v.get("executor") == "human":
        print(f"[devenv] {args.id} 是 executor: human —— 人跑完后用 confirm-lane",
              file=sys.stderr)
        return 1

    print(f"$ {method}")
    try:
        r = subprocess.run(method, shell=True, cwd=str(root), capture_output=True,
                           text=True, timeout=args.timeout)
        code, out, err = r.returncode, r.stdout, r.stderr
        timed_out = False
    except subprocess.TimeoutExpired:
        code, out, err, timed_out = 124, "", "", True
    except OSError as exc:
        code, out, err, timed_out = 127, "", str(exc), False

    if out:
        print(out[-2000:])
    if err:
        print(err[-2000:], file=sys.stderr)

    # 🔴 A24：skill 若追加过 task 入口，可能与用户已有的重名。
    # GNU make 自己会警告 —— 我们只是【读它已经打出来的那行】。
    # 零额外执行、零解析器。这就是「让工具自己回答」。
    if "overriding recipe for target" in err or "overriding commands for target" in err:
        print("\n🔴 检测到 target 重名 —— 你原来的定义可能已被覆盖（后定义的赢）。"
              "\n   请看上面的 warning，并检查你的构建文件。", file=sys.stderr)

    if code == 0:
        v["evidence"] = {
            "at_commit": _head(root),
            "at_time": _now(),
            "exit": 0,
            "attested_by": "script",
        }
        lane["status"] = "verified"
        lane.pop("blocked_by", None)
        S.save(root, data)
        _log(root, f"verify-lane {args.id} → verified (exit 0)")
        print(f"\n✅ {args.id} → verified @ {v['evidence']['at_commit'][:7]}")
        print("   ⚠️ 它是 `verified-at <sha>`（一次历史执行的记录），"
              "不是「当前状态的绿灯」—— 业务代码一改，这个绿灯就在说谎。")
        return 0

    # 跑红 —— 如实记，不 debug。
    head = (err or out or "").strip().splitlines()
    summary = head[0][:200] if head else f"exit {code}"
    if timed_out:
        summary = (f"超时（{args.timeout}s）—— 未确认是环境问题还是 smoke 本身挂了")
    lane["status"] = "scaffolded"
    lane["blocked_by"] = f"{summary}（exit {code}）"
    lane.get("verification", {}).pop("evidence", None)
    S.save(root, data)
    _log(root, f"verify-lane {args.id} → scaffolded (exit {code})")
    print(f"\n⏸ {args.id} → scaffolded", file=sys.stderr)
    print(f"   blocked_by: {lane['blocked_by']}", file=sys.stderr)
    print("   （skill 的职责是「建 + 验」，不是「调通」——"
          "修好后跑 /sdflow-devenv continue）", file=sys.stderr)
    return 0        # ← 跑红【不是 skill 的失败】。跑不绿是合法状态。


def cmd_confirm_lane(args):
    """人跑完人工验证后，经人门写入。

    🔴 产出的绿【如实标 attested_by: human】—— 人说的，不是脚本验的。
       MUST NOT 声称「脚本保证了执行者本人写入」：agent session 里模型是唯一的命令
       执行者，「人亲自调用」在机械上不可区分（07 A18）。如实标注，不设防伪。
    """
    root = Path(args.root).resolve()
    data = S.load(root)
    lane = next((l for l in data.get("lanes") or [] if l.get("id") == args.id), None)
    if lane is None:
        print(f"[devenv] 无此泳道: {args.id}", file=sys.stderr)
        return 1

    v = lane.setdefault("verification", {})
    if v.get("executor") != "human":
        print(f"[devenv] {args.id} 是 executor: script —— 用 verify-lane 让脚本跑。"
              f"\n（「本机缺个依赖」不是「方法本身没法用程序跑」——把前者标成后者是在撒谎）",
              file=sys.stderr)
        return 1

    v["evidence"] = {
        "at_commit": _head(root),
        "at_time": _now(),
        "exit": 0,
        "attested_by": "human",
        "confirmed_what": args.confirmed_what,
    }
    lane["status"] = "verified"
    lane.pop("blocked_by", None)
    S.save(root, data)
    _log(root, f"confirm-lane {args.id} → verified (human)")
    print(f"✅ {args.id} → verified（**人工确认**，非脚本验证）")
    return 0


# ---------- render ----------

_STATUS_TEXT = {
    "verified": "✅ 已验证",
    "partial": "⚠️ 部分验证",          # ← 全绿才 ✅。有绿有非绿必须如实说（A29）
    "scaffolded": "⏸ 已搭好，未验证",
    "planned": "○ 计划中",
    S.NOT_APPLICABLE: "— 不适用",
}


def _layer_status_text(L, lanes):
    """层状态那一行 —— 【它是整份文档最被人读的一行】，MUST NOT 报得比实情好。"""
    st = S.layer_status(L, lanes)
    if st != "partial":
        return st, _STATUS_TEXT.get(st, st)
    ok, total = S.layer_lane_tally(L, lanes)
    return st, (f"{_STATUS_TEXT['partial']} —— **{total} 条泳道里只跑绿了 {ok} 条**，"
                f"其余 {total - ok} 条见下表（这层**还没有**真正立起来）")

_SLOT_TITLE = {
    "how": "① 本项目怎么实现",
    "convention": "② 测试规范",
    "process": "③ 测试方法与流程",
    "tooling": "④ 需要配备的工具与脚本",
    "blind_spots": "⑥ ⭐ 这层证明了什么 · 看不见什么",
}

_LAYER_TITLE = {
    "unit": "单元层（不穿任何真实外部边界）",
    "integration": "集成层（穿过部分真实边界）",
    "e2e": "e2e 层（端到端穿过全部真实边界）",
}


def render_strategy(data):
    import devenv_lint as LT

    lines = [MARK_START,
             "<!-- 本区块由 devenv_scaffold.py render 从 .devenv.json 生成。DO NOT EDIT。 -->",
             "", "# 测试策略：三层框架", ""]

    b = LT.banner(data)
    if b:
        lines += ["> " + b.replace("\n", "\n> "), ""]

    lanes = data.get("lanes") or []
    for name in S.LAYERS:
        L = (data.get("layers") or {}).get(name) or {}
        st, st_text = _layer_status_text(L, lanes)
        lines += [f"## {_LAYER_TITLE[name]}", "",
                  f"**状态**：{st_text}", ""]

        if st == S.NOT_APPLICABLE:
            lines += [f"**理由**：{L.get('reason')}", "",
                      f"**后果（不做这层，我们因此看不见什么）**：{L.get('consequence')}", ""]
            continue

        for slot in S.CONTENT_SLOTS:
            lines += [f"**{_SLOT_TITLE[slot]}**", "", f"{L.get(slot, S.PENDING)}", ""]

        mine = [l for l in lanes if l.get("id") in (L.get("lane_ids") or [])]
        if mine:
            lines += ["**泳道**", "",
                      "| 泳道 | 命令 | 出处 | 状态 |", "|---|---|---|---|"]
            for l in mine:
                v = l.get("verification") or {}
                ev = v.get("evidence") or {}
                s = l.get("status")
                if s == "verified":
                    who = "" if ev.get("attested_by") == "script" else " · **人工确认**"
                    cell = (f"✅ verified-at `{str(ev.get('at_commit'))[:7]}`"
                            f" · {str(ev.get('at_time'))[:10]}{who}")
                elif s == "scaffolded":
                    cell = f"⏸ {l.get('blocked_by')}"
                else:
                    cell = "○ planned"
                lines.append(f"| `{l.get('id')}` | `{v.get('method','')}` | "
                             f"{l.get('source','')} | {cell} |")
            lines.append("")
            lines += ["> ⚠️ `verified-at <sha>` 是**一次历史执行的记录**，"
                      "**不是「当前状态的绿灯」**——业务代码一改，那个绿灯就在说谎。", ""]

    lines += [MARK_END, ""]
    return "\n".join(lines)


def cmd_render(args):
    root = Path(args.root).resolve()
    data = S.load(root)
    p = root / STRATEGY_MD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_strategy(data), encoding="utf-8")
    _log(root, "render testing-strategy.md")
    print(f"✓ {STRATEGY_MD}")
    return 0


# ---------- inject ----------

def inject_block(text, content):
    """幂等整块替换。注释语法【有界】（`<!-- -->` 数得完）⇒ 可手写（基准 5）。"""
    block = f"{MARK_START}\n{content}\n{MARK_END}"
    if MARK_START in text and MARK_END in text:
        pre = text.split(MARK_START)[0]
        post = text.split(MARK_END, 1)[1]
        return pre + block + post
    sep = "" if text.endswith("\n\n") or not text else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + block + "\n"


def cmd_inject(args):
    root = Path(args.root).resolve()
    content = (f"## 开发/测试环境\n\n"
               f"- 测试策略（三层框架）→ [`{STRATEGY_MD}`](./{STRATEGY_MD})\n"
               f"- 环境搭建 / 部署 → [`{ENV_MD}`](./{ENV_MD})\n"
               f"- 推进一格 → `/sdflow-devenv continue`\n")
    for rel in ("CLAUDE.md", "AGENTS.md", "README.md"):
        p = root / rel
        if not p.exists():
            continue
        p.write_text(inject_block(p.read_text(encoding="utf-8"), content), encoding="utf-8")
        print(f"✓ {rel}")
    _log(root, "inject 入口托管块")
    return 0


# ---------- CLI ----------

def build_parser():
    ap = argparse.ArgumentParser(prog="devenv_scaffold")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--root", required=True)
    p.add_argument("--on-exists", choices=["continue", "replan"])
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("set-layer"); p.add_argument("--root", required=True)
    p.add_argument("--layer", required=True, choices=S.LAYERS)
    for slot in S.CONTENT_SLOTS:
        p.add_argument(f"--{slot.replace('_','-')}", dest=slot)
    p.add_argument("--not-applicable", action="store_true")
    p.add_argument("--reason"); p.add_argument("--consequence")
    p.set_defaults(fn=cmd_set_layer)

    p = sub.add_parser("set-lane"); p.add_argument("--root", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--layer", choices=S.LAYERS)
    p.add_argument("--status", required=True, choices=S.LANE_STATUSES)
    p.add_argument("--method"); p.add_argument("--executor", choices=S.EXECUTORS)
    p.add_argument("--source"); p.add_argument("--smoke")
    p.add_argument("--strength"); p.add_argument("--blocked-by", dest="blocked_by")
    p.add_argument("--why-not-scriptable", dest="why_not_scriptable")
    p.add_argument("--human-steps", dest="human_steps")
    p.add_argument("--covers", nargs="*")
    p.set_defaults(fn=cmd_set_lane)

    p = sub.add_parser("verify-lane"); p.add_argument("--root", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.set_defaults(fn=cmd_verify_lane)

    p = sub.add_parser("confirm-lane"); p.add_argument("--root", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--confirmed-what", dest="confirmed_what", required=True)
    p.set_defaults(fn=cmd_confirm_lane)

    p = sub.add_parser("render"); p.add_argument("--root", required=True)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("inject"); p.add_argument("--root", required=True)
    p.set_defaults(fn=cmd_inject)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (S.SchemaInvalid, S.SchemaTooNew) as exc:
        print(f"[devenv] FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
