"""`sdflow-spec` 六种故障处置的回归门（`tasks.md` 4.5 / 覆盖图「六种故障处置」那一格）。

【为什么要有本文件】[impl-review-fix] F2
Task 3 的 dogfood 把六种故障**各注入过一次**，夹具跑完即删 ⇒ **没有任何回归会红**。
覆盖图那一格标着「会红 ✅」，而当时它是假绿。本文件把**能机械化的部分**固化成回归；
机械够不着的，如实降级为语义残余（基准 1：诚实边界 = 合法的残余划分，不是弱点）。

【为什么放在 `hack/tests/`】
`sdflow-spec` 是**纯 Markdown 编排类 skill，没有 `scripts/` 也没有 `tests/`**；
它既有的两道机械门就住在 `hack/tests/test_decision_memo_gate.py`（同一 idiom：门的实现
写在测试文件里，因为被守的「产品」是给模型看的指令，不存在第二份可执行实现）。
故障④ 复用那份文件的 `_decision_hash`（**MUST NOT 复刻算法**），放同一目录最省接线。

【六种故障 · 锚的强度分级（本文件的核心诚实声明）】

| # | 故障 | 可执行 producer | 本文件给的锚 | 强度 |
|---|---|---|---|---|
| ① | 工作树脏 | **无**（B.1① 是给模型看的指令） | SKILL.md 指令在场 + design 失败模式表行在场 | 弱 |
| ② | 在其它 feature 分支 | ✅ `ff0-branch-guard.py` | **真跑 hook**（三选一处置）+ **B.1② 判定指令在场** | **强** |
| ③ | 目标分支已存在 | **无**（git 自身行为 + B.1② 指令） | 指令在场 + `git` 真实行为对账 | 中 |
| ④ | 纪要陈旧（身份字段不匹配） | 判 1/2 已有门；判 3/4 算法有单一源 | **四 fixture 真跑判 3/判 4** + **C.1 四判与两条处置指令在场** | **强** |
| ⑤ | CLI 缺失 | **无**（0.1 预检是指令） | 指令在场（三件事逐条）+ 真实 PATH 剥离下的 exit code | 中 |
| ⑥ | `instructions --json` schema 断言不过 | **无**（C.3 §2 是指令） | **真 CLI 载荷 ⊇ 文档声明字段集** + 假 CLI 三种畸形 fail-closed + 处置句在场 | **强** |

🔴 **弱锚守的是「指令还在、没被后续编辑悄悄删掉/弱化」，MUST NOT 被表述成「处置正确会红」。**
「模型收到脏工作树时真的 halt 了没」没有确定性信号，只能靠 dogfood 人核 —— 这条残余不消失。
∴ 覆盖图那一格的真实状态是「②④⑥ 强锚 · ③⑤ 中锚 · ① 弱锚」，而不是齐刷刷的 ✅。

【锚质量纪律（承 `test_canonical_entry_sync.py`）】
- 指令在场锚 MUST 打在**它自称守的那句话**上，且能被定点变异打红（删那句 → 红）。
- 数量类断言一律给**下限**并注明语义，防「正则一个字没匹配上 ⇒ 空转恒绿」。
- **算法锚 MUST 配一条指令在场锚**〔[impl-review-fix fix2] F-A〕。判据只有一条：
  **「它守的那条处置，从 SKILL.md 里删掉，会红吗？」** —— 判 3/判 4 的算法住在本文件里
  （被守的产品是给模型看的指令，不存在第二份可执行实现），故算法锚只证明「**判得出**」，
  证不了「**处置还写在那儿**」；处置句被删 ⇒ 模型不再核身份，而算法用例一条不红。
  ④ 曾是本文件里自评最高的一格，恰恰只有它缺这半边 —— **假绿复发在自评最高处**。
- 指令在场锚的 needle 要么**足够长**、要么**整句连读**：短 needle 会被文档别处的同词满足
  （恒真锚的第二种成因），删掉它自称守的那句仍然绿。
"""
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "sdflow-spec" / "SKILL.md"
DESIGN = REPO / "openspec" / "changes" / "add-sdflow-spec" / "design.md"
HOOK = REPO / "sdflow-init" / "assets" / "hooks" / "ff0-branch-guard.py"
LADDER = REPO / "sdflow-spec" / "references" / "degradation-ladder.md"

_CLI_TIMEOUT_S = 60

# ── 复用既有门文件的算法实现，MUST NOT 复刻 ────────────────────────────────────
# `_decision_hash` 是**真跑 schema 文档里那条 bash 命令**（不是 Python 复刻）⇒ 本文件对
# `decision_hash` 的判据与文档是同一份，结构上不存在漂移面。
# 从文件路径加载（目录名含 `-`，非合法包名），与 test_decision_memo_gate.py 的 idiom 一致。
_GATE_PATH = REPO / "hack" / "tests" / "test_decision_memo_gate.py"
_gate_spec = importlib.util.spec_from_file_location("_memo_gate_for_failure_modes", _GATE_PATH)
_memo_gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_memo_gate)
_decision_hash = _memo_gate._decision_hash
check_decision_memo = _memo_gate.check_decision_memo
REQUIRED_SECTIONS = _memo_gate.REQUIRED_SECTIONS
MEMO_FILENAME = _memo_gate.MEMO_FILENAME
MEMO_SCHEMA_DOC = _memo_gate.MEMO_SCHEMA_DOC

openspec_cli = pytest.mark.skipif(
    shutil.which("openspec") is None,
    reason="openspec CLI 未安装 —— 故障⑥ 的真载荷对账需要真 CLI（MUST NOT 手搓解析器顶替）",
)


def _skill_text():
    return SKILL.read_text(encoding="utf-8")


def _squash(s):
    """压掉全部空白 —— 用于跨行中文散文的在场判定（硬折行位置会变，单行锚会假红）。"""
    return re.sub(r"\s+", "", s)


# ══════════════════════════════════════════════════════════════════════════════
# 故障① 工作树脏 —— 无可执行 producer，**弱锚：指令在场**
# ══════════════════════════════════════════════════════════════════════════════

def test_fault1_dirty_worktree_halt_instruction_is_present():
    """B.1① 的三件事一件不能少：探测命令 · halt 处置 · 「MUST NOT 静默继续」。

    🔴 本用例**不证明**模型真的 halt 了 —— 它只保证这条指令没被后续编辑删掉/弱化。
    """
    squashed = _squash(_skill_text())
    assert "gitstatus--porcelain" in squashed, \
        "B.1① 的探测命令 `git status --porcelain` 不见了 —— 脏树故障连检测都没有了"
    assert "halt并向人说明检测到的条目" in squashed, \
        "B.1① 的处置（halt 并说明条目）不见了 —— 与 design 失败模式表分叉"
    assert "MUSTNOT静默继续" in squashed, \
        "B.1① 的「MUST NOT 静默继续」不见了 —— 这句正是本故障的整个要害"


def test_fault1_design_failure_table_still_lists_it():
    """design 失败模式表那一行还在 —— 两处载体（指令 / 失败模式表）不得单边消失。"""
    squashed = _squash(DESIGN.read_text(encoding="utf-8"))
    assert "工作树不洁进入B收敛" in squashed
    assert "MUSTNOT静默`addA`" in squashed or "MUSTNOT静默`add-A`" in squashed


# ══════════════════════════════════════════════════════════════════════════════
# 故障② 在其它 feature 分支 —— **强锚：真跑 hook**
#
# 三分支判定的完整行为面（deny / 哨兵一次性 / TTL 双边 / detached HEAD fail-open …）
# 由 `sdflow-init/tests/test_ff0_branch_guard.py` 覆盖，**本文件不重复**。
# 这里只补它没断言的那一条：deny 文案 MUST 给出失败模式表写的**三选一**。
# ══════════════════════════════════════════════════════════════════════════════

def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    (r / "openspec").mkdir(parents=True)
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "f.txt").write_text("x", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def _run_hook(repo_dir, command):
    payload = {"tool_name": "Bash", "cwd": str(repo_dir),
               "tool_input": {"command": command}}
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"hook 非零退出：{proc.stderr}"
    if not proc.stdout.strip():
        return False, ""
    d = json.loads(proc.stdout)["hookSpecificOutput"]
    return d["permissionDecision"] == "deny", d["permissionDecisionReason"]


def test_fault2_branch_judgment_instruction_is_present():
    """B.1② 的三分判定表 + 「MUST NOT 沿用弱判据」在 SKILL.md 在场。

    [impl-review-fix fix2] F-A（面治）：hook 只在**模型敲 `openspec new change`** 时才拦；
    B.1② 才是模型自己那一跳的判定。删掉它 ⇒ 只剩 hook 这一层兜底，而 hook 之外的路径
    （人手敲、或先切分支再建目录）全裸奔 —— 下面那条真跑 hook 的用例照样绿。
    """
    squashed = _squash(_skill_text())
    assert "|**其它feature分支**|**halt问人**：从当前切出/回base切出/就地继续|" in squashed, \
        "B.1② 三分判定表的「其它 feature 分支 ⇒ halt 问人（三选一）」那一行不见了"
    assert "MUSTNOT沿用「已在feature分支就跳过」的弱判据" in squashed, \
        "B.1② 的「MUST NOT 沿用弱判据」不见了 —— 第二个 change 会落在前一个 change 的分支上"


def test_fault2_deny_offers_exactly_the_three_documented_choices(repo):
    """失败模式表的处置是「halt 问人（从当前切出 / 回 base 切出 / 就地继续）」——三条都要在文案里。

    只断言 deny 是不够的：文案退化成「不许在这建」而不给出路，人就只能去猜或去改 hook。
    """
    _git(repo, "checkout", "-qb", "feat/add-bar")
    denied, reason = _run_hook(repo, "openspec new change add-foo")
    assert denied, "在别的 change 的 feature 分支上建新 change 必须 halt（FF-0 分支③）"
    squashed = _squash(reason)
    for want, label in (("从当前分支切出", "选项 a"),
                        ("回base再切出", "选项 b"),
                        ("就地继续", "选项 c")):
        assert want in squashed, f"deny 文案缺失{label}（`{want}`）—— 三选一处置退化"
    assert "MUSTNOT自行touch哨兵" in squashed, \
        "deny 文案没说清「c) 只能由人决定」—— 模型会把逃生口当常规做法"


# ══════════════════════════════════════════════════════════════════════════════
# 故障③ 目标分支已存在 —— **中锚：指令在场 + git 真实行为对账**
# ══════════════════════════════════════════════════════════════════════════════

def test_fault3_fallback_instruction_is_present():
    squashed = _squash(_skill_text())
    assert "fallback`gitcheckoutfeat/{change}`" in squashed, \
        "B.1② 的「`checkout -b` 失败 ⇒ fallback `git checkout`」不见了"


def test_fault3_git_really_behaves_as_the_instruction_assumes(repo):
    """指令建立在两条 git 行为上：`checkout -b` 撞名必非零；`checkout` 复用必成功。

    这不是恒真锚 —— 它锚的是**外部依赖的行为**（同 `test_validate_strict_only_covers_delta_specs`
    锚 openspec CLI 行为）。git 哪天改了语义，这条会红并提示回来改指令。
    """
    _git(repo, "checkout", "-qb", "feat/demo")
    _git(repo, "checkout", "-q", "main")
    dup = subprocess.run(["git", "checkout", "-b", "feat/demo"], cwd=repo,
                         capture_output=True, text=True)
    assert dup.returncode != 0, "`git checkout -b` 撞名竟成功 —— fallback 指令的前提没了"
    back = subprocess.run(["git", "checkout", "feat/demo"], cwd=repo,
                          capture_output=True, text=True)
    assert back.returncode == 0, "fallback `git checkout <已存在分支>` 失败"


# ══════════════════════════════════════════════════════════════════════════════
# 故障④ 纪要陈旧 —— **强锚：C.1 判 3 / 判 4 四 fixture 真跑**
#
# 判 1/判 2（存在 + 必填非空）已由 test_decision_memo_gate.py 覆盖，这里直接复用它的
# `check_decision_memo`；判 3（身份字段）/判 4（hash 重算）此前**只活在 SKILL.md 指令里**，
# 本节把它们变成可回归的判据。
#
# ⚠️ 反循环设计：字段名从 **schema 文档**读，hash 由**文档里那条 bash 命令**算 —— 判据的
# 单一源都在被守的文档一侧，改文档即改判据，不是「测试自己守自己」。
# ══════════════════════════════════════════════════════════════════════════════

# C.1 判 3/判 4 消费的 frontmatter 键。语义是**下限**：schema 加字段不红，删/改这四个才红。
IDENTITY_KEYS = ("change", "branch", "generated_at", "decision_hash")


_SHAPE_HEADING = "## 2. 文件形状"


def _documented_frontmatter_keys():
    """从 `decision-memo-schema.md` §2「文件形状」的代码块里抠出 frontmatter 键名（单一源）。"""
    doc = MEMO_SCHEMA_DOC.read_text(encoding="utf-8")
    head = doc.find(_SHAPE_HEADING)
    assert head >= 0, f"schema 文档里找不到小节「{_SHAPE_HEADING}」—— 字段的单一源不见了"
    m = re.search(r"^```markdown\n(.*?)^```", doc[head:], re.S | re.M)
    assert m, f"「{_SHAPE_HEADING}」下找不到 ```markdown 样例块 —— 字段的单一源不见了"
    keys = [k for k in re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", m.group(1), re.M)]
    assert len(keys) >= len(IDENTITY_KEYS), (
        f"样例块里只抠到 {keys} —— 少于 C.1 判 3/判 4 消费的 {list(IDENTITY_KEYS)}")
    return keys


def test_identity_keys_all_come_from_the_schema_doc():
    """反循环锚：本节用的四个键必须真的在 schema 文档里 —— 文档改名即红。"""
    documented = _documented_frontmatter_keys()
    missing = [k for k in IDENTITY_KEYS if k not in documented]
    assert not missing, (
        f"C.1 判 3/判 4 消费的键 {missing} 不在 schema 文档的 frontmatter 里 —— "
        f"文档只声明了 {documented}；指令与 schema 已分叉"
    )


def _frontmatter(text):
    """解析 frontmatter → dict。语法面有界（首行 `---` 到下一行 `---`）⇒ 可手写（基准 5）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def check_memo_identity(memo_path, *, change, branch):
    """C.1 判 3/判 4 → `(verdict, problems)`。

    verdict 三态，**处置各不相同**（schema §3 注解 + SKILL.md C.1 末段）：
      · `"ok"`        → 准入相位 C
      · `"undrafted"` → `generated_at`/`decision_hash` **缺失** = 相位 B 收敛两步没走完
                        ⇒ **退回相位 B 补定稿**，MUST NOT 按「身份不匹配」去问人复用与否
      · `"stale"`     → 身份字段对不上 / hash 重算不符
                        ⇒ **拒绝进 C + 呈现旧 memo 摘要给人确认**，MUST NOT 静默复用
    """
    text = Path(memo_path).read_text(encoding="utf-8")
    fm = _frontmatter(text)

    missing = [k for k in ("generated_at", "decision_hash") if not fm.get(k)]
    if missing:
        return "undrafted", [f"纪要未定稿：frontmatter 缺 {missing} —— 退回相位 B 补定稿"]

    problems = []
    if fm.get("change") != change:
        problems.append(f"判 3 身份不符：memo `change`={fm.get('change')!r}，当前 change={change!r}")
    if fm.get("branch") != branch:
        problems.append(f"判 3 身份不符：memo `branch`={fm.get('branch')!r}，当前分支={branch!r}")
    recomputed = _decision_hash(memo_path)
    if recomputed != fm["decision_hash"]:
        problems.append(
            f"判 4 hash 不符：重算 {recomputed}，frontmatter 记 {fm['decision_hash']} "
            f"—— 定稿之后 memo 被手改过"
        )
    return ("stale" if problems else "ok"), problems


_MEMO_BODY = """# 决策纪要 · demo

## 目标态

一句话目标态。

{decisions}

{constraints}

## 接受的边角

无。
"""


def _write_memo(tmp_path, *, change="demo", branch="feat/demo",
                extra_decision="", finalize=True):
    """造一份 fixture 纪要；`finalize=True` 时补上定稿两字段（`generated_at`/`decision_hash`）。"""
    decision_h, constraint_h = REQUIRED_SECTIONS
    decisions = f"{decision_h}\n\n- D1：做 A，因为 B。{extra_decision}"
    constraints = f"{constraint_h}\n\n- C1：X 必须成立（证据锚 `foo.py:12`）。"
    body = _MEMO_BODY.format(decisions=decisions, constraints=constraints)

    d = tmp_path / "changes" / change
    d.mkdir(parents=True, exist_ok=True)
    memo = d / MEMO_FILENAME
    head = f"---\nschema_version: 1\nchange: {change}\nbranch: {branch}\n---\n\n"
    memo.write_text(head + body, encoding="utf-8")
    if not finalize:
        return d
    # 定稿：先按「frontmatter 之外全文」算 hash，再把两字段写回 frontmatter。
    h = _decision_hash(memo)
    head = (f"---\nschema_version: 1\nchange: {change}\nbranch: {branch}\n"
            f"generated_at: 2026-07-26T21:11:15+08:00\ndecision_hash: {h}\n---\n\n")
    memo.write_text(head + body, encoding="utf-8")
    return d


def test_fault4_fixtureA_intact_memo_is_admitted(tmp_path):
    """A 正常：判 1–判 4 全过 ⇒ 准入相位 C。"""
    d = _write_memo(tmp_path)
    assert check_decision_memo(d) == []
    verdict, problems = check_memo_identity(d / MEMO_FILENAME, change="demo", branch="feat/demo")
    assert (verdict, problems) == ("ok", []), problems


def test_fault4_fixtureB_branch_mismatch_is_stale(tmp_path):
    """B `branch` 改成 `…-OLD`：判 3 红 ⇒ `stale`（拒绝进 C + 呈现旧 memo 摘要）。"""
    d = _write_memo(tmp_path, branch="feat/demo-OLD")
    assert check_decision_memo(d) == [], "判 1/判 2 本就该过 —— 陈旧 memo 在旧判据下是全绿的"
    verdict, problems = check_memo_identity(d / MEMO_FILENAME, change="demo", branch="feat/demo")
    assert verdict == "stale", "身份字段不符却放行 ⇒ 静默复用上一次废弃运行的共识"
    assert any("判 3" in p for p in problems), problems


def test_fault4_fixtureC_edited_after_finalize_is_stale(tmp_path):
    """C 定稿后手改（偷加一条 D5）：判 4 hash 不符 ⇒ `stale`。"""
    d = _write_memo(tmp_path)
    memo = d / MEMO_FILENAME
    memo.write_text(memo.read_text(encoding="utf-8") + "\n- D5：偷加的一条。\n", encoding="utf-8")
    assert check_decision_memo(d) == [], "判 1/判 2 对「定稿后被手改」是瞎的 —— 判 4 才是这条的守卫"
    verdict, problems = check_memo_identity(memo, change="demo", branch="feat/demo")
    assert verdict == "stale"
    assert any("判 4" in p for p in problems), problems


def test_fault4_fixtureD_missing_finalize_fields_is_undrafted_not_stale(tmp_path):
    """D 缺 `generated_at`/`decision_hash`：**处置与 B/C 不同** —— 退回 B 补定稿，不是问人复用与否。

    🔴 这一条是本节的要害：两种 verdict 若被合并成「都判红」，D 的人机交互就错了
    （去问人「复用还是重做」，而正确动作是回相位 B 把收敛两步补完）。
    """
    d = _write_memo(tmp_path, finalize=False)
    verdict, problems = check_memo_identity(d / MEMO_FILENAME, change="demo", branch="feat/demo")
    assert verdict == "undrafted", "未定稿被误判成 stale ⇒ 会去问人复用与否（处置错）"
    assert problems and "退回相位 B" in problems[0]


def test_fault4_three_verdicts_are_distinguishable(tmp_path):
    """三态互不相等 —— 防「全部塌成红/绿两态」这类退化。"""
    ok = check_memo_identity(_write_memo(tmp_path / "a") / MEMO_FILENAME,
                             change="demo", branch="feat/demo")[0]
    stale = check_memo_identity(_write_memo(tmp_path / "b", branch="feat/x") / MEMO_FILENAME,
                                change="demo", branch="feat/demo")[0]
    undrafted = check_memo_identity(_write_memo(tmp_path / "c", finalize=False) / MEMO_FILENAME,
                                    change="demo", branch="feat/demo")[0]
    assert len({ok, stale, undrafted}) == 3, (ok, stale, undrafted)


def test_fault4_dispositions_are_present_in_the_skill():
    """C.1 的**四判 + 两条处置**在 SKILL.md 在场 —— 上面五条算法用例守不到这里。

    🔴 [impl-review-fix fix2] F-A：这是本文件要治的假绿**复发在自评最高的那一格**。
    `check_memo_identity` 住在本测试文件里（`sdflow-spec` 无 `scripts/`，见文件头），
    ⇒ 把 SKILL.md 那句处置整行删掉，判 3/判 4 的算法用例**一条都不会红**：
    模型不再核身份，陈旧纪要静默复用，而覆盖图 4.5 照旧绿。
    算法锚只证明「判得出」，本用例补的是「**处置还写在那儿**」这另一半。
    """
    squashed = _squash(_skill_text())
    # 判 3 / 判 4 的判据本身
    assert "身份字段匹配当前盘面" in squashed, \
        "C.1 判 3（身份字段匹配当前盘面）不见了 —— 陈旧 memo 的唯一识别信号没了"
    assert "`decision_hash`重算后匹配" in squashed and "重算纪要正文" in squashed, \
        "C.1 判 4（decision_hash 重算比对）不见了 —— 定稿后被手改的 memo 无从发现"
    # 处置 A：任一不过 ⇒ 拒绝进入生成
    assert "任一不过⇒**拒绝进入生成，退回相位B**" in squashed, \
        "C.1「任一不过 ⇒ 拒绝进入生成」不见了 —— 四判退化成只报告不阻断"
    # 处置 B：stale（判 3/判 4 红）⇒ 呈摘要给人确认，MUST NOT 静默复用
    assert "身份不符（判3）或hash不符（判4）⇒**呈现旧memo摘要" in squashed, \
        "C.1「身份/hash 不符 ⇒ 呈现旧 memo 摘要给人确认」不见了 —— stale 的处置没了"
    assert "MUSTNOT静默复用" in squashed, \
        "C.1 的「MUST NOT 静默复用」不见了 —— 这句正是故障④ 的整个要害"
    # 处置 C：undrafted（定稿两字段缺失）⇒ 退回 B 补定稿，**与 stale 不同处置**
    assert "**退回B补定稿**，MUSTNOT按「身份不匹配」去问人复用与否" in squashed, \
        "C.1 的 undrafted 分支（退回 B 补定稿）不见了 —— 会去问人复用与否，人机交互错"


# ══════════════════════════════════════════════════════════════════════════════
# 故障⑤/⑥ —— openspec CLI 缺失 / `instructions --json` 载荷畸形
#
# 文档声明的必需字段集从 **SKILL.md C.3 §2** 抠出（单一源），故：
#   · ⑥a 拿它去对**真 CLI** 的载荷 —— CLI schema 漂移（F-13）或文档写错，都会红；
#   · ⑤/⑥b 拿它去跑**假 CLI**（临时 PATH）—— 证明「缺失 / 三种畸形」确实 fail-closed。
# ══════════════════════════════════════════════════════════════════════════════

_TYPES = {"str": str, "list": list, "int": int, "bool": bool}
# 声明字段数的**下限**：防「把 C.3 §2 的字段删剩一个，⑥a 仍然绿」。
MIN_DECLARED_FIELDS = 5


def documented_required_fields():
    """→ {字段名: python 类型}，抠自 SKILL.md C.3 §2 那一句（`name`(type) · … 形态，有界）。"""
    text = _skill_text()
    head = text.find("**最小 schema 断言**")
    assert head >= 0, "SKILL.md C.3 找不到「最小 schema 断言」—— 故障⑥ 的整条要求不见了"
    seg = text[head:head + 400]
    pairs = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`\((str|list|int|bool)\)", seg)
    assert len(pairs) >= MIN_DECLARED_FIELDS, (
        f"C.3 §2 只声明了 {len(pairs)} 个必需字段（下限 {MIN_DECLARED_FIELDS}）：{pairs}"
    )
    return {name: _TYPES[t] for name, t in pairs}


def assert_instructions_schema(raw):
    """SKILL.md C.3 §2+§3 的断言：非法即抛 —— **fail-closed，MUST NOT 重试同一调用**。"""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AssertionError(f"problem: instructions --json 载荷不是合法 JSON / cause: {e}")
    if not isinstance(payload, dict):
        raise AssertionError("problem: instructions --json 载荷不是对象")
    for name, typ in documented_required_fields().items():
        if name not in payload:
            raise AssertionError(f"problem: instructions --json 缺必需字段 `{name}` / "
                                 f"cause: 实有字段={sorted(payload)}")
        if not isinstance(payload[name], typ):
            raise AssertionError(f"problem: 字段 `{name}` 类型不符，期望 {typ.__name__}")
    return payload


def test_declared_field_set_includes_the_confused_deputy_field():
    """`resolvedOutputPath` 是 SA-12 S4 路径净化的入口 —— 它从声明集里掉出去 = 安全面失守。"""
    assert "resolvedOutputPath" in documented_required_fields()


@openspec_cli
def test_fault6_real_cli_payload_carries_every_documented_field(tmp_path):
    """⑥a **强锚**：真 `openspec instructions --json` 的载荷 ⊇ SKILL.md 声明的字段集。

    CLI 换版把字段改名/降级（F-13「版本对、行为变」），或文档把字段写错 —— 都在这里红。
    """
    root = tmp_path / "proj"
    (root / "openspec" / "changes" / "demo" / "specs" / "foo").mkdir(parents=True)
    (root / "openspec" / "config.yaml").write_text(
        "schema: spec-driven\ncontext: |\n  fixture\n", encoding="utf-8")
    (root / "openspec" / "changes" / "demo" / "proposal.md").write_text(
        "# Demo Proposal\n\n## Why\nx\n\n## What Changes\n- a\n\n## Impact\n- specs/foo\n",
        encoding="utf-8")
    out = subprocess.run(
        ["openspec", "instructions", "design", "--change", "demo", "--json"],
        cwd=str(root), capture_output=True, text=True, timeout=_CLI_TIMEOUT_S)
    assert out.returncode == 0, f"CLI 非零退出：{out.stderr}"
    payload = assert_instructions_schema(out.stdout)   # 缺字段/类型不符 ⇒ 这里抛
    assert payload["artifactId"] == "design"


def _fake_openspec(tmp_path, stdout_body, *, exit_code=0):
    """在临时 PATH 里放一个假 `openspec`，返回可直接传给 subprocess 的 env。"""
    binder = tmp_path / "fakebin"
    binder.mkdir(exist_ok=True)
    exe = binder / "openspec"
    exe.write_text("#!/bin/sh\n"
                   'if [ "$1" = "--version" ]; then echo "1.5.0-FAKE"; exit 0; fi\n'
                   f"cat <<'EOF'\n{stdout_body}\nEOF\nexit {exit_code}\n", encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    env = dict(os.environ, PATH=f"{binder}:/usr/bin:/bin")
    return env


@pytest.mark.parametrize("body,label", [
    ('{"artifactId":"design","dependencies":[],"instruction":"x","template":"y"}',
     "缺 resolvedOutputPath"),
    ("not json at all", "不是合法 JSON"),
    ('{"artifactId":"design","dependencies":"NOT-A-LIST","instruction":"x",'
     '"template":"y","resolvedOutputPath":"/tmp/x.md"}', "dependencies 类型不符"),
])
def test_fault6_malformed_payload_fails_closed(tmp_path, body, label):
    """⑥b：三种畸形载荷各跑一次，**全部 fail-closed（抛异常）+ 诊断带 `problem:` 三要素**。

    🔴 [impl-review-fix fix2] F-D：本用例**不**断言「零重试 / 零写入」——那两维是
    **模型行为**（要不要再调一次、要不要落盘），无确定性信号可捕获（基准 1）；
    在这里硬断只会断到本用例自己写的那一次 `subprocess.run` 上，是恒真锚。
    这两维由 `test_fault6_no_retry_instruction_is_present` 的**指令在场锚（弱）**承载。
    """
    env = _fake_openspec(tmp_path, body)
    out = subprocess.run(["openspec", "instructions", "design", "--change", "demo", "--json"],
                         cwd=str(tmp_path), capture_output=True, text=True,
                         env=env, timeout=_CLI_TIMEOUT_S)
    with pytest.raises(AssertionError) as e:
        assert_instructions_schema(out.stdout)
    assert "problem:" in str(e.value), f"{label}：诊断缺 problem 三要素"


def test_fault5_missing_cli_is_detected(tmp_path):
    """⑤ 中锚：PATH 里没有 `openspec` ⇒ 预检命令非零退出（0.1 的检测信号真的存在）。"""
    env = dict(os.environ, PATH="/usr/bin:/bin")
    out = subprocess.run(["env", "openspec", "--version"], capture_output=True,
                         text=True, env=env, timeout=_CLI_TIMEOUT_S)
    assert out.returncode != 0, "剥掉 PATH 后 `openspec --version` 竟成功 —— 检测信号不成立"


def test_fault5_preflight_instruction_is_present():
    """⑤ 的处置指令三件事：fail-closed 中止 · 报实际版本 · 「MUST NOT 手工创建 change 目录顶替」。"""
    squashed = _squash(_skill_text())
    assert "openspecCLI预检" in squashed, "0.1 的 CLI 预检小节不见了"
    # 三件事逐条落锚（[impl-review-fix fix2] F-D 面治：docstring 宣称几条就断言几条）。
    # 「fail-closed 中止」用**整段连读**断，防被 C.3 §2 那处同词满足（假绿的另一种成因）。
    assert "命令不存在或非零退出⇒**fail-closed中止**" in squashed, \
        "0.1 的「命令不存在/非零退出 ⇒ fail-closed 中止」不见了 —— 预检退化成只提示不阻断"
    assert "cause（exitcode/`commandnotfound`原文+实际版本）" in squashed, \
        "0.1 三要素里的「报实际版本」不见了 —— 版本对不上的降级报告将无从复现"
    assert "MUSTNOT手工创建change目录结构顶替" in squashed, \
        "0.1 的「MUST NOT 手工创建 change 目录结构顶替」不见了 —— 这句正是本故障的要害"
    ladder = _squash(LADDER.read_text(encoding="utf-8"))
    assert "唯一failclosed面" in ladder.replace("-", ""), \
        "降级阶梯里「CLI 是唯一 fail-closed 面」的声明不见了"


def test_fault6_no_retry_instruction_is_present():
    """⑥ 断言不过时的处置指令：**fail-closed 中止 + 报实际 CLI 版本 + MUST NOT 重试同一调用**。

    整句连读断言（不是三段散断）：⑥b 的「零重试 / 零写入」两维无确定性信号（F-D），
    全部由这一条**弱锚**承载 —— 处置句在，才有「断言不过就不写、也不再调一次」这回事；
    「fail-closed 中止」若拆开单断，会被 0.1 那处同词满足，锚就空了。
    """
    assert ("任一缺失或类型不符⇒**fail-closed中止**，报**实际CLI版本**+修复命令，"
            "**MUSTNOT重试同一调用**") in _squash(_skill_text()), \
        "C.3 §2 的处置句（fail-closed 中止 / 报实际版本 / MUST NOT 重试）被删或改写了"
