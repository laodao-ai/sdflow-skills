"""devenv scaffold —— B 层（手）：建造，不是评估。

子命令：
  init         preflight + 模式分流（退出码驱动）
  set-layer    写三层框架的槽（六槽中要问的五个）
  set-lane     写泳道（planned / scaffolded 两态；verified MUST 走 verify-lane）
  verify-lane  ⭐ 亲自 fork 执行 verification.method，拿真实 exit code
  confirm-lane 人工验证后，经人门写入（attested_by: human）
  set-review-docs 配置评审页额外收录的 .md 文档（review.extra_docs，覆盖写）
  render       .devenv.json → testing-strategy.md + devenv-review.md（八节审阅汇总）
  review-page  组装文档清单，调共享评审页生成器（失败只提示，不阻塞）
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
import shlex
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import devenv_schema as S  # noqa: E402
from devenv_paths import PathEscape, contain, git_toplevel_problem  # noqa: E402

ARCH_DIR = "openspec/architecture"
STRATEGY_MD = f"{ARCH_DIR}/testing-strategy.md"
ENV_MD = f"{ARCH_DIR}/environments.md"
LOG_MD = f"{ARCH_DIR}/devenv-log.md"

MARK_START = "<!-- opsx-devenv:start -->"
MARK_END = "<!-- opsx-devenv:end -->"

DEFAULT_TIMEOUT = 300

REVIEW_MD = f"{ARCH_DIR}/devenv-review.md"
REVIEW_HTML = f"{ARCH_DIR}/review/devenv-review.html"
OUTSIDE_VOICE_DIR = f"{ARCH_DIR}/.outside-voice"
INVALIDATED_MARK = "> ⚠️ 已失效"

RUNS_DIR = f"{ARCH_DIR}/.devenv-runs"
LOG_TAIL_LINES = 80
LOG_LINE_MAX = 2000
LOG_TRUNC_MARK = "…（已截断）"
LOG_KEEP = 5
RUNS_GITIGNORE_LINES = ("*", "!.gitignore")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_run(root, *args, timeout=60):
    """→ (returncode, stdout)；git 不可用 → (None, "")。所有 git 调用共用这一个入口。"""
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None, ""
    return r.returncode, r.stdout


def _head(root):
    rc, out = _git_run(root, "rev-parse", "HEAD", timeout=10)
    return out.strip() if rc == 0 else "(no-git)"


# ---------- 失败日志（verify-lane 跑红 / 超时时落盘，不进 git）----------

_SAFE_ID_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")


def _safe_lane_id(lane_id):
    """泳道 id 进文件名前，把 [A-Za-z0-9._-] 以外的字符换成 `_`（字符集有界，不需要 `re`）。"""
    return "".join(c if c in _SAFE_ID_CHARS else "_" for c in str(lane_id))


def _as_text(v):
    """TimeoutExpired 捕获的部分输出可能是 bytes / str / None。"""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return v


def _tail(text):
    # 单行可能是压缩过的 JSON / 进度条，长度不设限会让日志文件膨胀
    lines = [ln if len(ln) <= LOG_LINE_MAX else ln[:LOG_LINE_MAX] + LOG_TRUNC_MARK
             for ln in text.splitlines()[-LOG_TAIL_LINES:]]
    return "\n".join(lines)


def _lane_logs(runs_dir, lane_id):
    """该泳道的失败日志 → [(排序键, 路径)]，按时间从旧到新。

    文件名 = <安全化 id>-<YYYYmmddTHHMMSSffffffZ>[-<序号>].log；旧版秒级时间戳（16 位）
    也认。后缀按固定形状解析，免得 id `a` 把 `a-b-…log` 也当成自己的。
    """
    if not runs_dir.is_dir():
        return []
    prefix = f"{_safe_lane_id(lane_id)}-"
    found = []
    for f in runs_dir.iterdir():
        name = f.name
        if not (name.startswith(prefix) and name.endswith(".log")) or f.is_symlink():
            continue
        stamp, _, seq = name[len(prefix):-4].partition("-")
        if len(stamp) == 16:                      # 旧版：补成微秒位，与新版可比
            stamp = stamp[:15] + "000000Z"
        if not (len(stamp) == 22 and stamp[:8].isdigit() and stamp[8] == "T"
                and stamp[9:21].isdigit() and stamp[21] == "Z"):
            continue
        if seq and not seq.isdigit():
            continue
        found.append(((stamp, int(seq or 1)), f))
    return sorted(found, key=lambda item: item[0])


def _prune_lane_logs(runs_dir, lane_id):
    """同一泳道只留最近 LOG_KEEP 份。只删 _lane_logs 认出的本脚本生成的文件。

    这是本脚本里唯一的删除点（adr/0022 的例外：删的是自己生成、同泳道、文件名严格匹配的日志）。
    删不掉不影响本次结果，下次写日志时再清。
    """
    for _, f in _lane_logs(runs_dir, lane_id)[:-LOG_KEEP]:
        try:
            f.unlink()
        except OSError:
            pass


def _ensure_runs_gitignore(runs_dir):
    """`.devenv-runs/.gitignore` 含 `*` 与 `!.gitignore`；缺哪行补哪行，不动其他内容。"""
    gi = runs_dir / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    have = set(text.splitlines())
    missing = [l for l in RUNS_GITIGNORE_LINES if l not in have]
    if not missing:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    gi.write_text(text + "\n".join(missing) + "\n", encoding="utf-8")


def _write_failure_log(root, lane_id, code, timed_out, out, err):
    """成功 → 返回仓库相对路径；失败 → stderr 告警并返回 None（泳道状态照常记录）。"""
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        runs_dir = contain(root, RUNS_DIR)
        runs_dir.mkdir(parents=True, exist_ok=True)
        _ensure_runs_gitignore(runs_dir)
        head = "超时" if timed_out else f"exit {code}"
        body = (f"# {lane_id} · {stamp} · {head}\n\n"
                f"## stdout（最后 {LOG_TAIL_LINES} 行）\n\n{_tail(out) or '无输出'}\n\n"
                f"## stderr（最后 {LOG_TAIL_LINES} 行）\n\n{_tail(err) or '无输出'}\n")
        # 排他创建：撞名（同泳道同微秒）时加序号，绝不覆盖先写的日志
        for n in range(1, 1000):
            suffix = "" if n == 1 else f"-{n}"
            rel = f"{RUNS_DIR}/{_safe_lane_id(lane_id)}-{stamp}{suffix}.log"
            path = contain(root, rel)
            if path.parent != runs_dir:
                raise PathEscape(f"日志路径不在 {RUNS_DIR}/ 内: {rel}")
            try:
                with open(path, "x", encoding="utf-8") as f:
                    f.write(body)
            except FileExistsError:
                continue
            _prune_lane_logs(runs_dir, lane_id)
            return rel
        raise OSError(f"同一微秒内日志撞名超过 999 次: {stamp}")
    except (OSError, PathEscape, UnicodeDecodeError) as exc:   # [impl-review-fix] P1: 非 UTF-8 的 .gitignore 不得逃出 verify-lane
        print(f"[devenv] 日志写入失败（泳道状态照常记录）: {exc}", file=sys.stderr)
        return None


# 汇总自己的派生文件：不能算进落地物，否则汇总会把自己算进内容。
_REVIEW_DERIVED = (REVIEW_MD, f"{ARCH_DIR}/review", RUNS_DIR)
# devenv 自产路径：本 skill 自己会写，不能算「用户的未提交改动」。
# 派生文件是它的子集，两份清单由同一处定义，免得增删一处漏另一处。
_DEVENV_OWNED = _REVIEW_DERIVED + tuple(f"{ARCH_DIR}/{n}" for n in (
    ".devenv.json", "devenv-log.md", "testing-strategy.md", ".outside-voice"))


def _excludes(paths):
    return [f":(exclude){p}" for p in paths]


def _dirty(root):
    """工作区（排除 devenv 自产路径）有无未提交改动。True / False；无 git 或查询失败 → None。

    交给 git 回答（pathspec 排除），不自己解析 status 输出的路径。
    """
    rc, out = _git_run(root, "status", "--porcelain", "--untracked-files=all",
                       "--", ".", *_excludes(_DEVENV_OWNED), timeout=30)
    if rc != 0:           # None（无 git）或非 0（查询失败）
        return None
    return bool(out.strip())


def _dirty_evidence(root):
    """取 dirty、有未提交改动就警告 → 要并入 evidence 的字段（无 git 时为空 dict）。

    verify-lane 要在命令执行之前调用：命令自己产生的文件不算「执行时的状态」。
    """
    dirty = _dirty(root)
    if dirty:
        print("⚠️  工作区有未提交改动，提交后重跑才有可复现的锚", file=sys.stderr)
    return {} if dirty is None else {"dirty": dirty}


def _new_round(root):
    return {"base_commit": _head(root), "started_at": _now()}


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
# 试点项目试点实证：模型现场自创的出处图例里写了 `[⚠️ 待定] = 还没答案`，
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

def _load_valid(root):
    """读 .devenv.json 并校验整份 schema；不合法 → SchemaInvalid。"""
    data = S.load(root)
    errs = S.validate(data)
    if errs:
        raise S.SchemaInvalid("; ".join(errs))
    return data


def _load_for_replan(root):
    """replan 不要求旧文件合法：读得了就保留内容，损坏则按新建处理。

    schema 版本比本实现新（SchemaTooNew）照常向上抛：那是 skill 过旧，不是文件损坏，
    按新建覆盖会丢掉新版写的内容。
    """
    try:
        return _load_valid(root)
    except S.SchemaInvalid as exc:
        print(f"⚠️  旧 {S.DEVENV_REL} 无法使用（{exc}），按新建处理并重置 round",
              file=sys.stderr)
        return S.blank()

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
        # replan = 新一轮，重置起点；continue = 同一轮续跑，保留已有起点、缺失才补记。
        if args.on_exists == "replan":
            data = _load_for_replan(root)
            data["round"] = _new_round(root)
            S.save(root, data)
        else:
            try:
                data = _load_valid(root)
            except S.SchemaInvalid as exc:
                print(f"[devenv] 问题：{S.DEVENV_REL} 无法读取或不合法\n"
                      f"  原因：{exc}\n"
                      f"  修复：修好该文件；想放弃旧内容重来，改用 --on-exists replan",
                      file=sys.stderr)
                return 2
            if "round" not in data:
                data["round"] = _new_round(root)
                S.save(root, data)
        _log(root, f"重入：mode={args.on_exists}")
        print(f"mode={args.on_exists} · sad={'ok' if sad else 'missing'}")
        return 0

    data = S.blank()
    data["round"] = _new_round(root)
    S.save(root, data)
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

    dirty_ev = _dirty_evidence(root)      # 命令执行之前取
    print(f"$ {method}")
    try:
        command = method
        run_kwargs = {"shell": True}
        if os.name == "nt":
            bash = shutil.which("bash")
            if not bash:
                raise OSError("Git Bash is required to execute verification.method on Windows")
            command = [bash, "-c", method]
            run_kwargs = {}
        r = subprocess.run(command, cwd=str(root), capture_output=True,
                           text=True, timeout=args.timeout, **run_kwargs,
                           encoding="utf-8", errors="replace")
        code, out, err = r.returncode, r.stdout, r.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        code, timed_out = 124, True
        out, err = _as_text(exc.stdout), _as_text(exc.stderr)
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
        v["evidence"].update(dirty_ev)
        lane["status"] = "verified"
        lane.pop("blocked_by", None)
        S.save(root, data)
        _log(root, f"verify-lane {args.id} → verified (exit 0)")
        print(f"\n✅ {args.id} → verified @ {v['evidence']['at_commit'][:7]}")
        print("   ⚠️ 它是 `verified-at <sha>`（一次历史执行的记录），"
              "不是「当前状态的绿灯」—— 业务代码一改，这个绿灯就在说谎。")
        return 0

    # 跑红 —— 如实记，不 debug。
    # stderr 只有空白时要回落到 stdout，不能因为 err 非空串就丢掉 stdout
    head = (err.strip() or out.strip()).splitlines()
    if timed_out:
        summary = f"超时（{args.timeout}s）—— 未确认是环境问题还是 smoke 本身挂了（exit {code}）"
    elif head:
        summary = f"{head[0][:200]}（exit {code}）"
    else:
        summary = f"无输出（exit {code}）"      # 不重复 exit 码
    log_rel = _write_failure_log(root, args.id, code, timed_out, out, err)
    if log_rel:
        summary += f"· 日志：{log_rel}"
    lane["status"] = "scaffolded"
    lane["blocked_by"] = summary
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

    dirty_ev = _dirty_evidence(root)
    v["evidence"] = {
        "at_commit": _head(root),
        "at_time": _now(),
        "exit": 0,
        "attested_by": "human",
        "confirmed_what": args.confirmed_what,
    }
    v["evidence"].update(dirty_ev)
    lane["status"] = "verified"
    lane.pop("blocked_by", None)
    S.save(root, data)
    _log(root, f"confirm-lane {args.id} → verified (human)")
    print(f"✅ {args.id} → verified（**人工确认**，非脚本验证）")
    return 0


# ---------- set-review-docs：评审页额外收录的 .md 文档 ----------

def check_review_doc(root, rel):
    """路径合法 → None；否则返回拒绝原因。

    containment 只防越界；`.md` 限制防止 `.env` 一类私有文件被嵌进提交的评审页。
    评审页生成前会用同一个函数再查一次。
    """
    try:
        p = contain(root, rel)
    except PathEscape as exc:
        return f"路径越界: {exc}"
    if p.suffix != ".md":
        return "只收 .md 文件"
    if ".git" in Path(os.path.relpath(p, Path(root).resolve())).parts:
        return "不收 .git/ 下的文件"
    if not p.is_file():
        return "文件不存在"
    return None


def cmd_set_review_docs(args):
    root = Path(args.root).resolve()
    data = S.load(root)
    bad = [(rel, why) for rel in args.path if (why := check_review_doc(root, rel))]
    if bad:
        for rel, why in bad:
            print(f"[devenv] 拒绝 {rel}: {why}（整条命令未写入）", file=sys.stderr)
        return 2
    if not isinstance(data.get("review"), dict):   # [impl-review-fix] C1: review 为 null/非 dict 时换成新 dict
        data["review"] = {}
    data["review"]["extra_docs"] = list(args.path)
    S.save(root, data)
    _log(root, f"set-review-docs {len(args.path)} 项")
    print(f"✓ review.extra_docs = {args.path}")
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
                    mark = " · **未提交改动**" if ev.get("dirty") is True else ""
                    cell = (f"✅ verified-at `{str(ev.get('at_commit'))[:7]}`"
                            f" · {str(ev.get('at_time'))[:10]}{who}{mark}")
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


# ---------- 审阅汇总 devenv-review.md ----------
#
# 只重新组织已有事实（.devenv.json、run 目录、失败日志、git），不产生新事实，
# 也不读源码里的配置文件。落地物 / issues / 已失效文件都交 git 回答（基准 5）。

_HEX = frozenset("0123456789abcdef")


def _code(text):
    """行内代码：反引号围栏比内容里最长的连续反引号多一个。"""
    text = str(text).replace("\n", " ")
    n = 1
    while "`" * n in text:
        n += 1
    return f"{'`' * n} {text} {'`' * n}" if text.startswith("`") or text.endswith("`") \
        else f"{'`' * n}{text}{'`' * n}"


def _fence(text):
    n = 3
    while "`" * n in text:
        n += 1
    return f"{'`' * n}text\n{text.rstrip()}\n{'`' * n}"


def _oneline(v):
    return str(v).replace("\r", " ").replace("\n", " ")


def _range_base(data):
    """本轮起点 → (base, None)；算不了 → (None, 原因与下一步)。"""
    rnd = data.get("round")
    if not isinstance(rnd, dict) or not rnd.get("base_commit"):
        return None, "本轮起点缺失（.devenv.json 没有 round）；重跑 `init --on-exists continue` 补记"
    base = str(rnd["base_commit"])
    if base == "(no-git)":
        return None, ("本轮起点是 (no-git)（init 时没有 git）；本轮起点不可恢复，"
                      "需要时以 `init --on-exists replan` 开新一轮")
    if not (4 <= len(base) <= 64 and set(base) <= _HEX):
        return None, (f"本轮起点 {_code(base)} 不是提交号；本轮起点不可恢复，"
                      "需要时以 `init --on-exists replan` 开新一轮")
    return base, None


def _unreachable_reason(base):
    return (f"起点 {_code(base[:7])} 在当前历史里不可达（可能 rebase 过）；本轮起点不可恢复，"
            "需要时以 `init --on-exists replan` 开新一轮")


def _landing_lines(root, data):
    base, why = _range_base(data)
    if base is None:
        return [f"无法计算：{why}"]
    rc, stat = _git_run(root, "diff", "--stat=200", f"{base}..HEAD", "--", ".", *_excludes(_REVIEW_DERIVED))
    if rc is None:
        return ["无法计算：git 不可用"]
    if rc != 0:
        return [f"无法计算：{_unreachable_reason(base)}"]
    rc, status = _git_run(root, "status", "--porcelain", "--untracked-files=all",
                          "--", ".", *_excludes(_REVIEW_DERIVED))
    lines = [f"相对本轮起点 {_code(base[:7])} 已提交的改动（`git diff --stat`）：", "",
             _fence(stat) if stat.strip() else "无", "",
             "未提交的改动（`git status --porcelain`）：", ""]
    if rc is None or rc != 0:
        lines.append("无法获取：git status 失败")
    else:
        lines.append(_fence(status) if status.strip() else "无")
    return lines


def _new_issue_paths(root, base):
    """→ (paths, None) 或 (None, 原因)。已提交的新增 + 未跟踪的新文件，去重排序。"""
    rc, added = _git_run(root, "diff", "-z", "--name-status", "--diff-filter=A",
                         base, "--", "openspec/issues/")   # [impl-review-fix] V2: 与工作树比，已 add 未提交的新增也算
    if rc is None:
        return None, "git 不可用"
    if rc != 0:
        return None, _unreachable_reason(base)
    tokens = added.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    paths = set(tokens[1::2])                   # -z 输出：状态、路径交替
    rc, untracked = _git_run(root, "ls-files", "-z", "--others", "--exclude-standard",
                             "--", "openspec/issues/")
    if rc == 0:
        paths.update(p for p in untracked.split("\0") if p)
    return sorted(paths), None


def _issues_lines(root, data):
    base, why = _range_base(data)
    if base is None:
        return [f"无法计算：{why}"]
    paths, why = _new_issue_paths(root, base)
    if paths is None:
        return [f"无法计算：{why}"]
    if not paths:
        return ["本轮没有新增 issue 文件"]
    return [f"- [{p}](<{_rel_arch(p)}>)" for p in paths]


def _first_nonblank_line(path):
    """文件首个非空行（去 BOM、首尾空白）；读不了 → None。只读开头一段。"""
    try:
        with open(path, "rb") as f:
            head = f.read(65536)
    except OSError:
        return None
    for line in head.decode("utf-8", errors="replace").lstrip("﻿").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _invalidated_files(root):
    """首个非空行是「> ⚠️ 已失效」的 .md → [(path, tracked)]；非 git 仓 → None。

    候选 = 已跟踪 + 未跟踪未忽略，交 git 回答；判定只看首个非空行，正文引用不算。
    """
    rc, tracked = _git_run(root, "ls-files", "-z")
    if rc is None or rc != 0:
        return None
    rc, untracked = _git_run(root, "ls-files", "-z", "--others", "--exclude-standard")
    cands = {p: True for p in tracked.split("\0") if p.endswith(".md")}
    if rc == 0:
        cands.update({p: False for p in untracked.split("\0") if p.endswith(".md")})
    out = []
    for rel in sorted(cands):
        full = Path(root) / rel
        if full.is_symlink() or not full.is_file():
            continue
        first = _first_nonblank_line(full)
        if first is not None and first.startswith(INVALIDATED_MARK):
            out.append((rel, cands[rel]))
    return out


def _env_pending_lines(root):
    p = Path(root) / ENV_MD
    if not p.is_file():
        return None
    return [(n, ln.strip()) for n, ln in
            enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1)
            if S.PENDING in ln]


def _latest_lane_log(root, lane_id):
    """该泳道最近一份失败日志的仓库相对路径；没有 → None。"""
    logs = _lane_logs(Path(root) / RUNS_DIR, lane_id)
    return f"{RUNS_DIR}/{logs[-1][1].name}" if logs else None


def _pick_run_dir(root, data):
    """含 disposition.md 且不早于本轮起点的最新 run 目录；没有 → None。"""
    try:
        contain(Path(root).resolve(), OUTSIDE_VOICE_DIR)   # [impl-review-fix] H2: 祖先软链指向仓外 → 不采信
    except PathEscape:
        return None
    base = Path(root) / OUTSIDE_VOICE_DIR
    if not base.is_dir():
        return None
    rnd = data.get("round")
    floor = ""
    if isinstance(rnd, dict) and isinstance(rnd.get("started_at"), str):
        floor = rnd["started_at"].replace("-", "").replace(":", "")   # 与 run 目录名同一时间戳写法
    names = []
    for d in base.iterdir():
        disp = d / "disposition.md"
        if d.is_symlink() or not d.is_dir() or disp.is_symlink() or not disp.is_file():
            continue
        if floor and d.name[:len(floor)] < floor:
            continue
        names.append(d.name)
    return base / max(names) if names else None


def _rel_arch(rel):
    return Path(os.path.relpath(rel, ARCH_DIR)).as_posix()


def render_review(root, data):
    import devenv_lint as LT

    lanes = [l for l in data.get("lanes") or [] if isinstance(l, dict)]
    layers = data.get("layers") or {}
    lines = ["<!-- 本文件由 devenv_scaffold.py render 生成。DO NOT EDIT。 -->", "",
             "# devenv 评审汇总", "",
             "> 只重新组织已有事实，节序即人门议程。", ""]

    # 1. 结论
    lines += ["## 1. 结论", ""]
    for name in S.LAYERS:
        st, text = _layer_status_text(layers.get(name) or {}, lanes)
        lines.append(f"- {_LAYER_TITLE[name]}：{text}")
    tally = {}
    for l in lanes:
        tally[l.get("status")] = tally.get(l.get("status"), 0) + 1
    parts = " · ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda kv: str(kv[0])))
    lines.append(f"- 泳道：共 {len(lanes)} 条" + (f"（{parts}）" if parts else ""))
    pend = LT.pending_slots(data)
    lines.append(f"- 框架待定格：{len(pend)}/{LT.total_slots(data)}")
    env_lines = _env_pending_lines(root)
    lines.append("- environments.md 待定处："
                 + ("尚未铺设" if env_lines is None else str(len(env_lines))))
    b = LT.banner(data)
    if b:
        lines += ["", "> " + b.replace("\n", "\n> ")]
    lines.append("")

    # 2. 需要人拍板的事项
    lines += ["## 2. 需要人拍板的事项", ""]
    lines.append(f"**框架待定格**（{len(pend)}）")
    by_layer = {}
    for layer, slot in pend:
        by_layer.setdefault(layer, []).append(slot)
    lines += [f"- {k} 层：{'、'.join(v)}" for k, v in by_layer.items()] or ["- 无"]
    lines += ["", f"**environments.md 待定处**（{0 if env_lines is None else len(env_lines)}）"]
    lines += ([f"- 第 {n} 行：{t}" for n, t in env_lines]
              if env_lines else ["- 无" if env_lines is not None else "- 尚未铺设"])
    lines += ["", "**未 verified 的泳道**"]
    unverified = [l for l in lanes if l.get("status") != "verified"]
    lines += [f"- {_code(l.get('id'))}：{l.get('status')}" for l in unverified] or ["- 无"]
    lines += ["", "**不适用的层**"]
    na = [(n, layers[n]) for n in S.LAYERS
          if isinstance(layers.get(n), dict) and layers[n].get("status") == S.NOT_APPLICABLE]
    lines += [f"- {n} 层：理由 {_oneline(L.get('reason'))}；后果 {_oneline(L.get('consequence'))}"
              for n, L in na] or ["- 无"]
    lines += ["", "**建议删除的已失效文件**（请自行执行）"]
    stale = _invalidated_files(root)
    if stale is None:
        lines.append("- 无法扫描：不是 git 仓")
    elif not stale:
        lines.append("- 无")
    else:
        lines += [f"- {_code(rel)}：" + _code(("git rm " if tracked else "rm ") + shlex.quote(rel))
                  for rel, tracked in stale]
    lines.append("")

    # 3. 三层框架
    lines += ["## 3. 三层框架", ""]
    for name in S.LAYERS:
        st, _ = _layer_status_text(layers.get(name) or {}, lanes)
        lines.append(f"- [{_LAYER_TITLE[name]}](./testing-strategy.md)：{_STATUS_TEXT.get(st, st)}")
    lines.append("")

    # 4. 泳道与证据
    lines += ["## 4. 泳道与证据", ""]
    if not lanes:
        lines.append("无泳道")
    for l in lanes:
        v = l.get("verification") if isinstance(l.get("verification"), dict) else {}
        ev = v.get("evidence") if isinstance(v.get("evidence"), dict) else {}
        lines.append(f"- {_code(l.get('id'))} · {l.get('layer')} 层 · executor {v.get('executor')}"
                     f" · {_STATUS_TEXT.get(l.get('status'), l.get('status'))}")
        lines.append(f"  - 命令：{_code(v.get('method', ''))}")
        if ev:
            who = " · 人工确认" if ev.get("attested_by") == "human" else ""
            mark = " · 未提交改动" if ev.get("dirty") is True else ""
            lines.append(f"  - 证据：{_code(str(ev.get('at_commit'))[:7])} · {ev.get('at_time')}"
                         f"{who}{mark}")
        if l.get("status") == "scaffolded":
            lines.append(f"  - blocked_by：{_oneline(l.get('blocked_by'))}")
            log = _latest_lane_log(root, l.get("id"))
            if log:        # 只放路径，日志内容可能含敏感信息；日志不进 git，只在本机可打开
                lines.append(f"  - 失败日志（仅本机可打开）：[{_rel_arch(log)}](<{_rel_arch(log)}>)")
    lines.append("")

    # 5. 环境文档
    lines += ["## 5. 环境文档", ""]
    if env_lines is None:
        lines.append("environments.md 尚未铺设")
    else:
        lines.append(f"- [environments.md](./environments.md)：{len(env_lines)} 处待定")
    lines.append("")

    # 6. 落地物清单
    lines += ["## 6. 落地物清单", ""] + _landing_lines(root, data) + [""]

    # 7. 冷审处置
    lines += ["## 7. 冷审处置", ""]
    run_dir = _pick_run_dir(root, data)
    if run_dir is None:
        lines.append("本轮无冷审处置记录")
    else:
        lines.append(f"run 目录：{_code(OUTSIDE_VOICE_DIR + '/' + run_dir.name)}（只在本机存在，不进 git）")
        lenses = sorted(f.name for f in run_dir.glob("lens-*.md") if f.is_file() and not f.is_symlink())
        if lenses:
            lines.append("镜报告：" + "、".join(_code(n) for n in lenses) + "（评审页另页收录）")
        lines.append("")
        text = (run_dir / "disposition.md").read_text(encoding="utf-8", errors="replace")
        lines += [("> " + ln).rstrip() for ln in text.splitlines()]
    lines.append("")

    # 8. 本轮新增 issues
    lines += ["## 8. 本轮新增 issues", ""] + _issues_lines(root, data) + [""]
    return "\n".join(lines)


def cmd_render(args):
    root = Path(args.root).resolve()
    data = S.load(root)
    p = root / STRATEGY_MD
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_strategy(data), encoding="utf-8")
    _log(root, "render testing-strategy.md + devenv-review.md")
    # 日志与策略文档都写完之后再汇总：汇总会读 git 状态，写入顺序固定才能让连跑两次逐字节相同。
    (root / REVIEW_MD).write_text(render_review(root, data), encoding="utf-8")
    print(f"✓ {STRATEGY_MD}")
    print(f"✓ {REVIEW_MD}")
    return 0


# ---------- review-page：调共享评审页生成器 ----------

def _doc_label(rel, used):
    """标签 = 文件名去 .md；重名前缀父目录名（docs-README）；仍重名再加序号。"""
    path = Path(rel)
    label = (path.name[:-3] if path.name.endswith(".md") else path.name).replace("=", "_")
    if label in used:
        label = f"{path.parent.name or 'root'}-{label}"
    base, n = label, 2
    while label in used:
        label, n = f"{base}-{n}", n + 1
    return label


def _review_page_docs(root, data):
    """→ [(标签, 仓库相对路径)]：必有文档在前，可选文档只收存在且合格的。"""
    rels = [REVIEW_MD, STRATEGY_MD]
    if (root / ENV_MD).is_file():
        rels.append(ENV_MD)
    review = data.get("review")
    for rel in (review.get("extra_docs") if isinstance(review, dict) else None) or []:
        why = check_review_doc(root, rel)        # 与 set-review-docs 同一判定，生成前再查一次
        if why:
            print(f"[devenv] 跳过额外文档 {rel}: {why}", file=sys.stderr)
        else:
            rels.append(rel)
    run_dir = _pick_run_dir(root, data)
    if run_dir is not None:
        rels += [f"{OUTSIDE_VOICE_DIR}/{run_dir.name}/{f.name}"
                 for f in sorted(run_dir.glob("lens-*.md")) if f.is_file() and not f.is_symlink()]
    used, docs = set(), []
    for rel in rels:
        label = _doc_label(rel, used)
        used.add(label)
        docs.append((label, rel))
    return docs


def _review_page_unavailable(reason, fix):
    # 生成失败只提示、不阻塞人门（与其他节点一致），所以走 stdout 且退出码 0。
    print(f"评审页未生成：{reason}")
    print(f"修复方法：{fix}")
    return 0


def cmd_review_page(args):
    root = Path(args.root).resolve()
    data = S.load(root)
    home = os.environ.get("SDFLOW_HOME") or os.path.expanduser("~/.sdflow")
    generator = Path(home) / "hack" / "render-review-page.py"
    if not generator.is_file():
        return _review_page_unavailable(f"生成器不存在（{generator}）",
                                        "在运行 checkout 跑 bash setup.sh")
    cmd = [sys.executable, str(generator), "--out", REVIEW_HTML,
           "--title", f"devenv 评审 · {root.name}"]
    for label, rel in _review_page_docs(root, data):
        cmd += ["--doc", f"{label}={rel}"]
    if args.event:
        cmd += ["--event", args.event]
    if args.no_open:
        cmd.append("--no-open")
    try:
        r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=120,
                           encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError) as exc:
        return _review_page_unavailable(f"生成器无法运行（{exc}）", "确认 python3 可用后重跑 review-page")
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        return _review_page_unavailable(
            f"生成器退出码 {r.returncode}",
            "先跑 render 生成 devenv-review.md，按上面的错误信息处理后重跑 review-page")
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

    p = sub.add_parser("set-review-docs"); p.add_argument("--root", required=True)
    p.add_argument("--path", action="append", required=True)
    p.set_defaults(fn=cmd_set_review_docs)

    p = sub.add_parser("render"); p.add_argument("--root", required=True)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("review-page"); p.add_argument("--root", required=True)
    p.add_argument("--event"); p.add_argument("--no-open", action="store_true")
    p.set_defaults(fn=cmd_review_page)

    p = sub.add_parser("inject"); p.add_argument("--root", required=True)
    p.set_defaults(fn=cmd_inject)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    # 路径基准统一为仓顶层：子目录会让 git 输出（相对顶层）与脚本解析（相对 root）错位
    problem = git_toplevel_problem(args.root)
    if problem:
        print(f"[devenv] {problem}", file=sys.stderr)
        return 2
    try:
        return args.fn(args)
    except (S.SchemaInvalid, S.SchemaTooNew) as exc:
        print(f"[devenv] FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
