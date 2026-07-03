# sdflow-ship Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 阶段三编排层：`/sdflow-ship` 一次调用经确定性台账 `ship_gate.py` 驱动 5.5→9 到 merge 建议，并闭环 T10/T11/T20。

**Architecture:** 新 skill `sdflow-ship/`（SKILL.md 纯编排读者 + `scripts/ship_gate.py` 只读盘面判官 + pytest 全盘面态）；三个既有报告模板补机器锚行；模型档位收拢进 bundle 规则文件 `model-tiers.md`。

**Tech Stack:** Python 3 stdlib（同 recorder 先例，零第三方依赖）、pytest、bash/git、Markdown SKILL 指令。

## Global Constraints

（逐字来自 design.md D1-D9〔含设计门拍板 Q1=B/Q2/Q3=A〕与评审结论，每任务隐含遵守）

1. **盘面即状态**：ship_gate 只读 change 目录产物与 git 历史，**零副作用**；MUST NOT 设可变 state 文件（第二真相源）。
2. **锚行字面集（grep -F 语义，零正则，双向钉死）**：`<!-- ship-gate: design-approved -->` / `<!-- ship-gate: verify=PASS -->` / `<!-- ship-gate: verify=FAIL -->` / `<!-- ship-gate: code-review=pass -->` / `<!-- ship-gate: code-review=blocked -->`——ship_gate.py 头注释与三个 SKILL.md 报告模板 MUST 同组字面，单测断言双向一致。
3. **退出码**：0=可推进（含 SHIPPED/SKIP）/ 3=REFUSE_START / 4=BLOCKED_UPSTREAM / 5=VERIFY_FAIL / **6=UNKNOWN**；同一报告并存冲突锚行 → UNKNOWN 点名冲突行，MUST NOT 猜优先级。
4. **完成判据窗口〔Q2〕**：主锚 = superpowers-plan.md 首次提交 sha 起 `git log <sha>..HEAD --no-merges` 内收集 `checkpoint(task<k>-` 去重任务号集，对 plan `### Task \d+:` 计数 N；标题命中 0 → UNKNOWN；辅 = 复选框全勾；皆不可判 → UNKNOWN。MUST NOT 全历史扫描。
5. **D9 新鲜度按锚分域〔Q1=B〕**：design-approved 仅对其后触及 `openspec/changes/{change}/` 路径的提交失鲜；verify/code-review 对其后触及 `openspec/` 之外路径的提交失鲜（遍历不加 `--first-parent`）；**报告从未提交 = fresh + `freshness=uncommitted`〔Q3=A〕**；产物在但无锚行 = 步进行中。头注释声明已知不覆盖：openspec/workflow/ 规则漂移不触发陈旧、rebase/--amend 可伪造保鲜。
6. **ship 零 git 写操作〔D8〕**：不 commit/merge/push；merge opt-out 原样透传 sdflow-done；SHIPPED 摘要提醒手动 push（toolkit 源仓附 `/sdflow-upgrade` 激活句）。
7. **T10 三级决策协议**：①客观判据可判 → 自动选+记理由；②无 → 对抗镜复核推荐项，通过才选（记录进报告）；③复核不过/无从复核 → defer。MUST NOT 以"有把握"类自评置信为唯一依据。
8. **T11 零内联模型名**：四个编排 SKILL.md（ship/done/spec-review/code-review）**全文**（含派发 prompt 行）不得出现裸模型名；唯一白名单 = 指向规则根 `model-tiers.md` 的引用句；canonical 缺省（强 opus / 中 sonnet / 弱 haiku）只住 model-tiers.md。
9. **测试沙箱**：pytest 一律 tmp_path + `git init` 沙箱仓（配 user.name/user.email），绝不写真实 HOME/真实仓；**窗口污染态必须预埋历史 fixture**（干净仓测不出 C2）。
10. **逐任务 checkpoint〔D1 注入点〕**：每任务最后一步由 implementer 自己执行 `bash ~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "<描述>"`（脚本缺失则 `git add -A && git commit -m "checkpoint(task<N>-<slug>): <描述>"`）。**标签 task<N>- 前缀是 gate 主锚契约，不可省。**
11. **Edit 前必先 Read 目标文件**；只改本任务列出的文件；权威源在 `sdflow-init/assets/workflow/`，本仓 `openspec/workflow/` instance 勿手改（Task 10 经 update --dev 同步）。
12. **每任务完成跑 `python3 -m pytest sdflow-ship/tests/ -q`（Task 8 起加跑全仓 pytest）确认全绿无 warning。**

---

### Task 1: ship_gate.py 骨架 + 锚行解析 + pre-flight

**Files:**
- Create: `sdflow-ship/scripts/ship_gate.py`
- Create: `sdflow-ship/tests/conftest.py`
- Test: `sdflow-ship/tests/test_gate_preflight.py`

**Interfaces:**
- Produces: `run_git(root,*args)->str`、`anchors_in(path,candidates)->list[str]`、`emit(verdict,exit_code,next_step,reason,**extra)`（打印人读行+JSON 后 sys.exit）、常量 `ANCHOR_*`、`EXIT_*`、`main(argv)`；conftest 的 `repo(tmp_path)` fixture（沙箱 git 仓）与 `mkchange(root,name)`、`commit_all(root,msg)` helper。后续任务在 `decide()` 内按注释区块扩展。

- [ ] **Step 1: 写失败测试**（conftest + pre-flight 三态）

`sdflow-ship/tests/conftest.py`：
```python
import subprocess
import pytest

def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git_init = ["init", "-q", "-b", "main"]
    subprocess.run(["git", "-C", str(tmp_path), *_git_init], check=True,
                   capture_output=True, text=True)
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "user.email", "t@t")
    return tmp_path

def commit_all(root, msg):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg, "--allow-empty")

def mkchange(root, name="demo"):
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    return d
```

`sdflow-ship/tests/test_gate_preflight.py`：
```python
import json, subprocess, sys
from pathlib import Path
from conftest import commit_all, mkchange

GATE = Path(__file__).resolve().parents[1] / "scripts" / "ship_gate.py"

def run_gate(root, change="demo"):
    r = subprocess.run([sys.executable, str(GATE), "--change", change,
                        "--root", str(root)], capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    payload = json.loads(lines[-1]) if lines else {}
    return r.returncode, payload, lines[0] if lines else ""

def test_refuse_when_report_missing(repo):
    mkchange(repo); commit_all(repo, "seed")
    code, js, human = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "补锚" in js["reason"]  # exit3 文案含人工补锚指引（D2）

def test_refuse_when_anchor_missing(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# 报告\n结论：通过\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_pass_gate_when_anchor_present(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "# 报告\n<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, human = run_gate(repo)
    assert code == 0 and js["verdict"] != "REFUSE_START"
    assert human.startswith("[ship-gate]")  # D2 首行人读

def test_verify_conflict_anchors_unknown(repo):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n<!-- ship-gate: verify=FAIL -->\n",
        encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "verify" in js["reason"]
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_gate_preflight.py -q`
Expected: FAIL（ship_gate.py 不存在）

- [ ] **Step 3: 最小实现**

`sdflow-ship/scripts/ship_gate.py`（完整创建；头注释 = 契约真相源，Global Constraints 2/3/4/5 逐字进注释）：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ship_gate.py — sdflow-ship 确定性台账（盘面即状态：只读、零副作用）

契约（与三个 SKILL.md 报告模板双向钉死；tests/test_anchor_contract.py 断言两侧同组字面）:

锚行字面集（grep -F 语义，零正则）:
    <!-- ship-gate: design-approved -->        spec-review-report.md（sdflow-spec-review 拍板回写）
    <!-- ship-gate: verify=PASS -->            verify-report.md（sdflow-done verify 模板）
    <!-- ship-gate: verify=FAIL -->
    <!-- ship-gate: code-review=pass -->       code-review-report.md（sdflow-code-review 模板）
    <!-- ship-gate: code-review=blocked -->

退出码: 0=可推进(含 SHIPPED/SKIP) 3=REFUSE_START 4=BLOCKED_UPSTREAM 5=VERIFY_FAIL 6=UNKNOWN

verdict × exit × next 契约表:
    REFUSE_START     3  -                  未过设计门（若拍板已发生请人工补锚——显式越权留痕）
    RUN_SOP          0  embedded-test-sop  TG-02 命中且 {change}-sop.md 缺
    RUN_PLAN         0  writing-plans      superpowers-plan.md 缺
    CONTINUE_IMPL    0  subagent-dev       标签集未齐 N（JSON done_tasks=已完成任务号集，SDD 勿重派）
    RUN_CODE_REVIEW  0  sdflow-code-review code-review-report.md 缺
    BLOCKED_UPSTREAM 4  -                  code-review=blocked
    RUN_VERIFY       0  sdflow-done        verify-report.md 缺
    VERIFY_FAIL      5  -                  verify=FAIL 且未陈旧
    RERUN_STALE      0  <该步 skill>        D9 陈旧结论 → 重跑该步
    STEP_IN_PROGRESS 0  <该步 skill>        产物在但无锚行
    SHIPPED          0  -                  final 全通（hand-off+archive+分支已并）
    UNKNOWN          6  -                  多锚冲突/双通道不可判/标题0/detached HEAD

完成判据窗口〔设计门拍板 Q2〕: superpowers-plan.md 首次提交 sha 起
    `git log <sha>..HEAD --no-merges` 收集 checkpoint(task<k>- 去重任务号集；
    plan `### Task <n>:` 计数 N；齐 N 判完成；标题命中 0 → UNKNOWN。

D9 新鲜度按锚分域〔设计门拍板 Q1=B / Q3=A〕:
    design-approved: 其后触及 openspec/changes/{change}/ 的提交 → 失鲜（改设计须重审）
    verify / code-review: 其后触及 openspec/ 之外路径的提交 → 陈旧
    报告从未提交: fresh（freshness=uncommitted，人机同权）

已知不覆盖（接受并记录）:
    openspec/workflow/ 规则漂移不触发陈旧；rebase/--amend 历史改写可伪造保鲜；
    提交遍历不加 --first-parent（merge 内部提交逐一枚举，不漏检）。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ANCHOR_DESIGN = "<!-- ship-gate: design-approved -->"
ANCHOR_VERIFY_PASS = "<!-- ship-gate: verify=PASS -->"
ANCHOR_VERIFY_FAIL = "<!-- ship-gate: verify=FAIL -->"
ANCHOR_CR_PASS = "<!-- ship-gate: code-review=pass -->"
ANCHOR_CR_BLOCKED = "<!-- ship-gate: code-review=blocked -->"
ALL_ANCHORS = [ANCHOR_DESIGN, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL,
               ANCHOR_CR_PASS, ANCHOR_CR_BLOCKED]

EXIT_OK, EXIT_REFUSE, EXIT_BLOCKED, EXIT_VFAIL, EXIT_UNKNOWN = 0, 3, 4, 5, 6


def run_git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def anchors_in(path, candidates):
    """字面查找（零正则）。文件不存在返回 []。"""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    return [a for a in candidates if a in text]


def emit(verdict, exit_code, next_step, reason, **extra):
    human = f"[ship-gate] {verdict}"
    if next_step:
        human += f" → next={next_step}"
    human += f" — {reason}"
    print(human)
    print(json.dumps({"verdict": verdict, "next": next_step,
                      "reason": reason, **extra}, ensure_ascii=False))
    sys.exit(exit_code)


def pick_exclusive(path, positive, negative, label):
    """互斥锚对解析：两者并存 → UNKNOWN（不猜优先级）。返回 'pos'/'neg'/None。"""
    found = anchors_in(path, [positive, negative])
    if positive in found and negative in found:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             f"{label} 报告并存冲突锚行（{positive} 与 {negative}），请人工裁决删除其一")
    if positive in found:
        return "pos"
    if negative in found:
        return "neg"
    return None


def decide(root, change):
    cdir = root / "openspec" / "changes" / change
    # ── pre-flight：设计门（D7 起跑不越门）─────────────────────────
    report = cdir / "spec-review-report.md"
    if ANCHOR_DESIGN not in anchors_in(report, [ANCHOR_DESIGN]):
        emit("REFUSE_START", EXIT_REFUSE, None,
             "未过设计门：spec-review-report.md 缺失或无 design-approved 锚行；"
             "先完成设计门；若拍板已发生请人工补锚（显式越权留痕）")
    # ── verify 冲突锚早检（多锚冲突 → UNKNOWN，任务3 完整接管步序）──
    vfile = cdir / "verify-report.md"
    if vfile.is_file():
        pick_exclusive(vfile, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL, "verify")
    # 步序判定由后续任务区块填充；当前最小可行：过门即建议进入计划步
    emit("RUN_PLAN", EXIT_OK, "writing-plans", "已过设计门（骨架版：步序判定待任务2-4）")


def main(argv=None):
    p = argparse.ArgumentParser(description="sdflow-ship 盘面判官（只读）")
    p.add_argument("--change", required=True)
    p.add_argument("--root", default=None)
    a = p.parse_args(argv)
    root = Path(a.root) if a.root else Path(
        run_git(Path.cwd(), "rev-parse", "--show-toplevel") or Path.cwd())
    decide(root, a.change)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/test_gate_preflight.py -q`
Expected: 4 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task1-gate-preflight "ship_gate 骨架+锚行解析+pre-flight(exit3/6)+沙箱fixture"
```

---

### Task 2: step 5.5 条件步 + step 6/7 完成判据（窗口主锚）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（decide() 内 RUN_PLAN 骨架行替换为完整步序前半）
- Test: `sdflow-ship/tests/test_gate_impl_progress.py`

**Interfaces:**
- Consumes: Task 1 的 `run_git/emit/anchors_in`。
- Produces: `tg02_hit(cdir)->bool`、`plan_task_count(plan)->int`、`plan_first_sha(root,plan_rel)->str`、`done_task_ids(root,sha)->set[str]`、`checkboxes_all(plan)->bool|None`。

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_gate_impl_progress.py`：
```python
import subprocess, sys, json
from pathlib import Path
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate

PLAN2 = "### Task 1: A\n- [ ] s\n### Task 2: B\n- [ ] s\n"

def approved_change(repo, plan=None, sop=False, tg02=False):
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text(
        "<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    prop = "# p\n〔TG-02：嵌入式〕\n" if tg02 else "# p\n〔TG-01：工具链〕\n"
    (d / "proposal.md").write_text(prop, encoding="utf-8")
    if sop:
        (d / "demo-sop.md").write_text("sop\n", encoding="utf-8")
    if plan is not None:
        (d / "superpowers-plan.md").write_text(plan, encoding="utf-8")
    commit_all(repo, "seed change")
    return d

def test_tg02_hit_sop_missing(repo):
    approved_change(repo, tg02=True)
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_SOP" and js["next"] == "embedded-test-sop"

def test_no_tg02_plan_missing_run_plan(repo):
    approved_change(repo, tg02=False)
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_PLAN" and "SKIP_SOP" in js["reason"]

def test_continue_impl_with_done_set(repo):
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-foo): done A")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == ["1"]

def test_all_tags_present_advances(repo):
    approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-foo): A")
    commit_all(repo, "checkpoint(task2-bar): B")
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_window_excludes_legacy_and_merge(repo):
    # 污染①：plan 提交前 main 已有遗留标签（C2 实证态）
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-legacy): 旧 change 遗留")
    commit_all(repo, "checkpoint(task2-legacy): 旧 change 遗留")
    approved_change(repo, plan=PLAN2)
    # 污染②：merge 带入的外部标签（--no-merges 只滤 merge commit 本身，
    # 分支内普通提交仍在窗口——用 merge commit message 携带标签验证滤除）
    subprocess.run(["git", "-C", str(repo), "merge", "--allow-unrelated-histories",
                    "-s", "ours", "-m", "checkpoint(task2-external): merge携带",
                    "HEAD"], capture_output=True, text=True)
    code, js, _ = run_gate(repo)
    # 窗口内无任何 task 标签 → 0/2 完成，辅通道复选框未全勾 → CONTINUE_IMPL
    assert js["verdict"] == "CONTINUE_IMPL" and js["done_tasks"] == []

def test_plan_zero_titles_unknown(repo):
    approved_change(repo, plan="# 空计划，无任务标题\n")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"

def test_checkbox_fallback_advances(repo):
    plan = "### Task 1: A\n- [x] s\n### Task 2: B\n- [x] s\n"
    approved_change(repo, plan=plan)  # 无标签但复选框全勾（回勾型执行器）
    code, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_gate_impl_progress.py -q`
Expected: FAIL（decide 仍是骨架 RUN_PLAN）

- [ ] **Step 3: 实现**

在 `ship_gate.py` 顶部函数区追加（`decide` 之前）：
```python
import re

TASK_TITLE_RE = re.compile(r"^### Task (\d+):", re.M)   # 计数用；锚行才禁正则
TAG_RE = re.compile(r"checkpoint\(task(\d+)-")


def tg02_hit(cdir):
    p = cdir / "proposal.md"
    return p.is_file() and "TG-02" in p.read_text(encoding="utf-8")  # 字面子串（归档实例为全角括号混用）


def plan_task_count(plan):
    return len(TASK_TITLE_RE.findall(plan.read_text(encoding="utf-8")))


def plan_first_sha(root, plan_rel):
    out = run_git(root, "log", "--diff-filter=A", "--format=%H", "--", plan_rel)
    return out.splitlines()[-1] if out else ""


def done_task_ids(root, sha):
    msgs = run_git(root, "log", f"{sha}..HEAD", "--no-merges", "--format=%s")
    return {m.group(1) for line in msgs.splitlines() if (m := TAG_RE.search(line))}


def checkboxes_all(plan):
    text = plan.read_text(encoding="utf-8")
    unchecked, checked = "- [ ]" in text, "- [x]" in text
    if not unchecked and not checked:
        return None
    return not unchecked
```

`decide()` 中替换骨架行 `emit("RUN_PLAN", ...)` 为：
```python
    # ── step 5.5：条件步（TG-02 字面子串；细判归模型）────────────
    sop_note = ""
    if tg02_hit(cdir):
        if not (cdir / f"{change}-sop.md").is_file():
            emit("RUN_SOP", EXIT_OK, "embedded-test-sop", "TG-02 命中且 sop 产物缺")
    else:
        sop_note = "SKIP_SOP(非嵌入式不触发); "
    # ── step 6/7：plan 与完成判据〔Q2 窗口主锚〕──────────────────
    plan = cdir / "superpowers-plan.md"
    if not plan.is_file():
        emit("RUN_PLAN", EXIT_OK, "writing-plans", sop_note + "superpowers-plan.md 缺")
    n = plan_task_count(plan)
    if n == 0:
        emit("UNKNOWN", EXIT_UNKNOWN, None,
             "plan 无 '### Task <n>:' 标题（上游模板漂移？），完成判据不能")
    sha = plan_first_sha(root, str(plan.relative_to(root)))
    done = done_task_ids(root, sha) if sha else set()
    if len(done) < n:
        boxes = checkboxes_all(plan)
        if boxes is True:
            pass  # 辅通道：复选框全勾（回勾型执行器）
        elif not sha and boxes is None:
            emit("UNKNOWN", EXIT_UNKNOWN, None, "plan 未提交且无复选框，双通道皆不可判")
        else:
            emit("CONTINUE_IMPL", EXIT_OK, "subagent-dev",
                 f"实现进度 {len(done)}/{n}（窗口 {sha[:7] or '-'}..HEAD --no-merges）",
                 done_tasks=sorted(done, key=int))
    # ── step 8/9/final 由任务3 填充；当前推进到 code-review ──────
    emit("RUN_CODE_REVIEW", EXIT_OK, "sdflow-code-review", "实现完成，进入代码审")
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 11 passed, no warnings（含 Task 1 的 4 条回归）

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task2-gate-impl-progress "step5.5 TG + 完成判据窗口主锚(污染fixture/标题0 UNKNOWN/辅通道)"
```

---

### Task 3: step 8/9 + final（分支已并 / SHIPPED / archive 重入）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`
- Test: `sdflow-ship/tests/test_gate_tail.py`

**Interfaces:**
- Consumes: Task 1/2 全部；`pick_exclusive`。
- Produces: `branch_state(root)->str`（"merged"/"pending"/"unknown"）；decide() 尾段完整。

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_gate_tail.py`：
```python
import subprocess
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2

def impl_done(repo):
    d = approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    return d

def test_cr_missing_run_code_review(repo):
    impl_done(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_cr_blocked_exit4(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=blocked -->\n", encoding="utf-8")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 4 and js["verdict"] == "BLOCKED_UPSTREAM"

def test_verify_fail_exit5(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"

def test_full_pass_to_shipped(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    (d / "hand-off.md").write_text("交接\n", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档\n", encoding="utf-8")
    commit_all(repo, "tail")
    code, js, _ = run_gate(repo)   # 沙箱在 main 无 feature 分支 → 视为已并
    assert code == 0 and js["verdict"] == "SHIPPED"

def test_verify_pass_but_no_handoff_run_verify_step(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    commit_all(repo, "tail")
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_VERIFY"  # done 未走完（hand-off/archive 缺）
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_gate_tail.py -q`
Expected: FAIL（decide 在 RUN_CODE_REVIEW 截止）

- [ ] **Step 3: 实现**

函数区追加：
```python
def branch_state(root):
    """已并判定〔spec-review-amendment D6〕。"""
    head = run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if head == "HEAD":
        return "unknown"          # detached HEAD
    for base in ("main", "master"):
        if run_git(root, "rev-parse", "--verify", base):
            if head == base:
                return "merged"   # 已在 base 上（分支已删/已并场景）
            return "merged" if not run_git(root, "log", f"{base}..HEAD",
                                           "--oneline") else "pending"
    return "unknown"
```

`decide()` 尾段替换 `emit("RUN_CODE_REVIEW", ...)` 为：
```python
    # ── step 8：code-review 门 ─────────────────────────────────
    cr = cdir / "code-review-report.md"
    if not cr.is_file():
        emit("RUN_CODE_REVIEW", EXIT_OK, "sdflow-code-review", "实现完成，进入代码审")
    cr_state = pick_exclusive(cr, ANCHOR_CR_PASS, ANCHOR_CR_BLOCKED, "code-review")
    if cr_state == "neg":
        emit("BLOCKED_UPSTREAM", EXIT_BLOCKED, None,
             "code-review 判 blocked：先解 blocker（见报告），gate 不蒙头跑")
    if cr_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-code-review",
             "code-review-report.md 在但无锚行 → 该步进行中，重跑")
    # ── step 9：verify 终门 ────────────────────────────────────
    vf = cdir / "verify-report.md"
    if not vf.is_file():
        emit("RUN_VERIFY", EXIT_OK, "sdflow-done", "进入收尾（verify→hand-off→archive→merge）")
    v_state = pick_exclusive(vf, ANCHOR_VERIFY_PASS, ANCHOR_VERIFY_FAIL, "verify")
    if v_state == "neg":
        emit("VERIFY_FAIL", EXIT_VFAIL, None, "verify FAIL：停并上抛缺口清单（报告内）")
    if v_state is None:
        emit("STEP_IN_PROGRESS", EXIT_OK, "sdflow-done",
             "verify-report.md 在但无锚行 → 该步进行中，重跑")
    # ── final：SHIPPED 判定 ────────────────────────────────────
    handoff = (cdir / "hand-off.md").is_file()
    archived = any((root / "openspec" / "changes" / "archive").glob(f"*-{change}"))
    bstate = branch_state(root)
    if bstate == "unknown":
        emit("UNKNOWN", EXIT_UNKNOWN, None, "detached HEAD，分支态判定不能")
    if handoff and archived and bstate == "merged":
        emit("SHIPPED", EXIT_OK, None,
             "全通：verify PASS + hand-off + 已归档 + 分支已并。"
             "未 push（手动控制）；toolkit 源仓请 push 后新会话 /sdflow-upgrade 激活")
    emit("RUN_VERIFY", EXIT_OK, "sdflow-done",
         f"verify PASS 但收尾未完（hand-off={handoff} archive={archived} branch={bstate}）")
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 16 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task3-gate-tail "step8/9+final(blocked exit4/FAIL exit5/SHIPPED/分支已并/archive glob)"
```

---

### Task 4: D9 新鲜度按锚分域（Q1=B / Q3=A）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`
- Test: `sdflow-ship/tests/test_gate_freshness.py`

**Interfaces:**
- Consumes: 前三任务全部。
- Produces: `report_last_sha(root,rel)->str`、`is_stale(root,rel,scope,change)->tuple[bool,str]`（返回 (stale, freshness)，freshness ∈ fresh/stale/uncommitted）。decide() 在 step8/9/pre-flight 接入。

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_gate_freshness.py`：
```python
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2
from test_gate_tail import impl_done

def tail_ok(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    commit_all(repo, "reports")
    return d

def touch_code(repo, name="src.py"):
    (repo / name).write_text("# code\n", encoding="utf-8")
    commit_all(repo, "code change")

def test_stale_pass_reruns_not_ship(repo):
    tail_ok(repo)
    touch_code(repo)             # 报告后有 openspec/ 外提交
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review"

def test_stale_fail_reruns_not_exit5(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "reports")
    touch_code(repo)             # FAIL 之后修了代码 → 重验不卡死
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"

def test_design_anchor_survives_impl_commits(repo):
    # Q1=B 断言①：实现提交不令 design-approved 失鲜
    approved_change(repo, plan=PLAN2)
    touch_code(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"   # 而非 REFUSE_START（链自锁反例）

def test_design_anchor_stale_on_design_edit(repo):
    # Q1=B 断言②：四件套被改 → design-approved 失鲜
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("# 拍板后又改了设计\n", encoding="utf-8")
    commit_all(repo, "edit design after approval")
    code, js, _ = run_gate(repo)
    assert code == 3 and "重审" in js["reason"]

def test_uncommitted_report_is_fresh(repo):
    # Q3=A：报告从未提交 → fresh + freshness=uncommitted
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True); (arch / "p.md").write_text("a", encoding="utf-8")
    commit_all(repo, "tail")
    # 用未提交的新 verify 报告覆盖（工作区改动不提交）
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n新一轮手写\n", encoding="utf-8")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "SHIPPED"

def test_openspec_only_commits_keep_fresh(repo):
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    commit_all(repo, "handoff only touches openspec")   # 正常尾流不误伤
    _, js, _ = run_gate(repo)
    assert js["verdict"] in ("RUN_VERIFY", "SHIPPED")   # 不得 RERUN_STALE
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_gate_freshness.py -q`
Expected: FAIL（无新鲜度逻辑）

- [ ] **Step 3: 实现**

函数区追加：
```python
def report_last_sha(root, rel):
    return run_git(root, "log", "-1", "--format=%H", "--", rel)


def is_stale(root, rel, scope, change):
    """D9 分域〔Q1=B/Q3=A〕。scope: 'design'|'code'。返回 (stale, freshness)。"""
    sha = report_last_sha(root, rel)
    if not sha:
        return False, "uncommitted"          # Q3=A：人机同权，手写产物合法
    files = run_git(root, "log", f"{sha}..HEAD", "--name-only", "--format=")
    watched = f"openspec/changes/{change}/"
    for f in filter(None, files.splitlines()):
        if scope == "design" and f.startswith(watched):
            return True, "stale"
        if scope == "code" and not f.startswith("openspec/"):
            return True, "stale"
    return False, "fresh"
```

`decide()` 三处接入（Read 后精确替换）：

pre-flight 锚行判定通过之后、verify 冲突早检之前，插入：
```python
    stale, _fr = is_stale(root, str(report.relative_to(root)), "design", change)
    if stale:
        emit("REFUSE_START", EXIT_REFUSE, None,
             "design-approved 之后四件套被改动 → 拍板失鲜，改设计须重审"
             "（重跑 sdflow-spec-review 后重新拍板补锚）")
```

step 8 中 `cr_state == "pos"` 通过后（即 `if cr_state is None:` 块之后）插入：
```python
    stale, cr_fresh = is_stale(root, str(cr.relative_to(root)), "code", change)
    if stale:
        emit("RERUN_STALE", EXIT_OK, "sdflow-code-review",
             "code-review 结论后存在 openspec/ 外提交 → 结论陈旧，重审", freshness=cr_fresh)
```

step 9 中 verify 锚行解析之前（`v_state = pick_exclusive(...)` 之前）插入：
```python
    v_stale, v_fresh = is_stale(root, str(vf.relative_to(root)), "code", change)
```
并把 `v_state == "neg"` 与 `v_state == "pos"` 之后的推进改为先判陈旧：
```python
    if v_stale:
        emit("RERUN_STALE", EXIT_OK, "sdflow-done",
             "verify 结论后存在 openspec/ 外提交 → 结论陈旧（FAIL 修复后重验不卡死 / PASS 不背书新代码）",
             freshness=v_fresh)
    if v_state == "neg":
        emit("VERIFY_FAIL", EXIT_VFAIL, None, "verify FAIL：停并上抛缺口清单（报告内）")
```
（SHIPPED 输出的 JSON 附 `freshness=v_fresh`，供 uncommitted 留痕。）

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 22 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task4-gate-freshness "D9 分域新鲜度(Q1=B链自锁反例/Q3=A uncommitted/陈旧FAIL不卡死/陈旧PASS不放行)"
```

---

### Task 5: 三报告模板锚行 + 双向一致契约测试

**Files:**
- Modify: `sdflow-spec-review/SKILL.md`（第四步·产出节 + 收敛口后加拍板回写协议）
- Modify: `sdflow-done/SKILL.md`（第一步 verify prompt 的报告结构段）
- Modify: `sdflow-code-review/SKILL.md`（报告格式节结论区）
- Test: `sdflow-ship/tests/test_anchor_contract.py`

**Interfaces:**
- Consumes: ship_gate.py 的 `ANCHOR_*` 常量行（文本解析）。

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_anchor_contract.py`：
```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"

PAIRS = [
    ("sdflow-spec-review/SKILL.md", ["<!-- ship-gate: design-approved -->"]),
    ("sdflow-done/SKILL.md", ["<!-- ship-gate: verify=PASS -->",
                              "<!-- ship-gate: verify=FAIL -->"]),
    ("sdflow-code-review/SKILL.md", ["<!-- ship-gate: code-review=pass -->",
                                     "<!-- ship-gate: code-review=blocked -->"]),
]

def test_gate_header_lists_all_anchors():
    text = GATE.read_text(encoding="utf-8")
    for _, anchors in PAIRS:
        for a in anchors:
            assert a in text, f"gate 头注释缺锚行 {a}"

def test_skill_templates_carry_same_literals():
    for rel, anchors in PAIRS:
        text = (REPO / rel).read_text(encoding="utf-8")
        for a in anchors:
            assert a in text, f"{rel} 模板缺锚行 {a}（双向钉死破坏）"
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_anchor_contract.py -q`
Expected: FAIL（三个 SKILL.md 尚无锚行）

- [ ] **Step 3: 实现（先 Read 各 SKILL.md 再 Edit）**

`sdflow-spec-review/SKILL.md` 第四步「收敛口（1.6）」句后追加一段：
```markdown
- **拍板回写协议（ship-gate 锚，D2）**：设计门拍板**发生后**，主 session MUST 立即把下行锚原样写入 `spec-review-report.md`（拍板记录区末尾）——写入者=主 session、触发点=用户批准动作；这是 `/sdflow-ship` pre-flight 的唯一机判依据：

  `<!-- ship-gate: design-approved -->`

  gate exit 3 时若拍板已发生，人工补此锚行 = 显式越权留痕（人机同权）。
```

`sdflow-done/SKILL.md` 第一步 verify prompt 内报告结构列表（"- **结论**：PASS / FAIL"行）之后插一行：
```markdown
   - **结论行下方紧跟机器锚行（ship-gate 契约，模板写死二选一）**：`<!-- ship-gate: verify=PASS -->` 或 `<!-- ship-gate: verify=FAIL -->`——/sdflow-ship 以字面查找机判，勿改写措辞、勿两行并存
```

`sdflow-code-review/SKILL.md` 报告格式的"### 结论"区块内补：
```markdown
  结论区末行为机器锚行（ship-gate 契约，二选一）：
  <!-- ship-gate: code-review=pass -->   （建议进 /sdflow-done）
  <!-- ship-gate: code-review=blocked --> （存在未解 blocker）
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 24 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task5-anchor-templates "三报告模板锚行+双向契约测试(1.4)"
```

---

### Task 6: sdflow-ship/SKILL.md（编排指令全文）

**Files:**
- Create: `sdflow-ship/SKILL.md`
- Test: `sdflow-ship/tests/test_skill_text.py`

**Interfaces:**
- Consumes: ship_gate.py CLI（`python3 <sibling>/scripts/ship_gate.py --change X --root .`）。

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_skill_text.py`：
```python
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"

def text():
    return SKILL.read_text(encoding="utf-8")

def test_gate_discipline_present():
    t = text()
    assert "每步前后" in t and "ship_gate" in t
    assert "MUST" in t and "prose" in t.lower() or "步序" in t

def test_zero_git_and_passthrough():
    t = text()
    assert "不 commit" in t or "零 git" in t
    assert "透传" in t and "push" in t

def test_fuse_and_resume():
    t = text()
    assert "重跑一次仍无锚行" in t and "UNKNOWN" in t     # D5 熔断
    assert "重调" in t and "勿重派" in t                  # D9 resume

def test_trigger_words_scoped():
    t = text()
    assert "/sdflow-ship" in t and "ship 这个 change" in t
    head = t.split("---", 2)[1]   # frontmatter
    assert "发布" not in head      # 避让裸词（D9 撞车）
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_skill_text.py -q`
Expected: FAIL（SKILL.md 不存在）

- [ ] **Step 3: 创建 SKILL.md**

`sdflow-ship/SKILL.md`（完整内容）：
```markdown
---
name: sdflow-ship
description: 阶段三编排器——对已过设计门的 OpenSpec change 一次调用驱动 5.5→9（embedded-test-sop 条件 → writing-plans/subagent-dev → sdflow-code-review → sdflow-done→merge）。触发：「/sdflow-ship」「ship 这个 change」「阶段三跑到 merge」「过完设计门了，跑起来」。不含裸"ship"泛化触发。
---

# sdflow-ship — 阶段三编排器（盘面即状态）

一次调用把已过设计门的 change 从 5.5 驱动到 merge 建议。**meta-orchestrator：chain 现有 skill、不取代**；窄 scope 不越两个人类点（不跨 grill、不跨设计门——过门后才起跑，adr/0004 红线）。

## 铁律

- **每步前后 MUST 调 ship_gate 并遵其判定，禁止以 prose 记忆步序**〔adr/0006(b)〕：
  ```bash
  python3 ~/.claude/skills/sdflow-ship/scripts/ship_gate.py --change {change} --root "$(git rev-parse --show-toplevel)"
  ```
  路径缺失时按 sibling 约定兜底（~/.codex/skills/… 或仓内 sdflow-ship/scripts/），找不到停下问用户。
  步前问"NEXT 是谁 + 前置缺什么"，步后问"产物落了吗 + 门禁结论"。首行人读摘要照抄进对话，JSON 供判定。
- **ship 零 git 写操作〔D8〕**：全程不 commit/merge/push（各子 skill 的 checkpoint 归其自身；ship 无产物故无自身 checkpoint）；**不自动 push**。
- **merge 意图透传**：调用语含"别合并 / 跑到 merge 前停"类 opt-out → **原样转述给 sdflow-done**（git 单向操作只在 done 一处）。
- **决策协议（T10 三级，替换"有把握自动选"）**：阶段三遇 ≥2 方案——①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录写进该步报告）；③复核不过/无从复核 → defer 进 buglist/todolist + hand-off。**MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。**
- 模型档位与缺省见规则根 `model-tiers.md`（经 ~/.sdflow/hack/resolve-workflow.sh 解析；config.yaml 的 model-tiers 段可覆盖映射）。

## 链序（gate 驱动，非记忆）

REFUSE_START(exit3)→停："先过设计门；若拍板已发生请人工补锚（显式越权留痕）" ·
RUN_SOP→跑 embedded-test-sop（TG-18/高风险细判归模型） · RUN_PLAN→superpowers:writing-plans（**派发 args MUST 要求 plan 每任务 commit 步显式用 `checkpoint-commit.sh task<N>-<slug>`，由 implementer 执行**——gate 主锚契约）→ subagent-driven-development 自动执行 · CONTINUE_IMPL→把 JSON `done_tasks` 已完成任务号集传给 SDD dispatch **勿重派** · RUN_CODE_REVIEW→/sdflow-code-review · BLOCKED_UPSTREAM(exit4)→停并原样上抛 blocker 清单 · RUN_VERIFY→/sdflow-done（透传 merge 意图） · VERIFY_FAIL(exit5)→停并原样上抛缺口清单 · RERUN_STALE→重跑 gate 指定步 · STEP_IN_PROGRESS→重跑该步；**同一 invocation 内同一步重跑一次后仍无锚行 → 按 UNKNOWN 停上抛人工，禁无限静默循环**〔熔断〕 · UNKNOWN(exit6)→停并转述 reason · SHIPPED→输出摘要。

## resume / 暂停 / 人机同权〔D9〕

- **停即停、重调即续**：ship 零跨步内存状态，任何时刻中断后重调 `/sdflow-ship {change}`，gate 从盘面推导缺口继续。
- **gate 不辨产者**：期间人工手跑某步（如手跑 /sdflow-code-review）产出的报告同样被认；手改锚行 = 显式越权通道（git 留痕可审计）。
- 实现中断的 resume：gate 输出已完成任务号集 → 传 SDD 勿重派。

## SHIPPED 摘要模板

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/sdflow-ship 完成 — {change}
  链: [sop|SKIP] → plan+impl({n}/{n} 任务) → code-review(pass) → done(verify PASS, merged)
  ⏸ 未 push（手动控制）。toolkit 源仓：push 后新会话跑 /sdflow-upgrade 激活。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 28 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task6-ship-skill "sdflow-ship SKILL.md(gate纪律/零git/透传/T10/熔断/resume/摘要)"
```

---

### Task 7: workflow.md 权威源（入口行 + 决策4 T10 + 步6 标签契约）

**Files:**
- Modify: `sdflow-init/assets/workflow/workflow.md`
- Test: `sdflow-ship/tests/test_workflow_authority.py`

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_workflow_authority.py`：
```python
from pathlib import Path

WF = Path(__file__).resolve().parents[2] / "sdflow-init" / "assets" / "workflow" / "workflow.md"

def test_orchestrator_entry_row():
    t = WF.read_text(encoding="utf-8")
    assert "/sdflow-ship" in t and "5.5" in t

def test_decision4_no_self_confidence():
    t = WF.read_text(encoding="utf-8")
    assert "有把握自动选" not in t
    assert "对抗镜复核" in t

def test_step6_tag_contract():
    t = WF.read_text(encoding="utf-8")
    assert "task<N>-" in t and "checkpoint-commit.sh" in t
    assert "implementer" in t or "实现子代理" in t   # D1 注入点：由 implementer 执行
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_workflow_authority.py -q`
Expected: FAIL

- [ ] **Step 3: 实现（先 Read workflow.md 定位三处再 Edit）**

① 阶段三步骤表标题下方加入口行：
```markdown
> **编排层入口 = `/sdflow-ship {change}`**：一次调用经 ship_gate 确定性台账驱动 5.5→9（下表手动逐步仍为合法 reference 路径）。
```
② 决策 4 原句（含"有把握自动选"）整句替换为：
```markdown
遇 ≥2 方案按三级决策协议〔T10〕：①有客观判据（测试/断言/基准可判）→ 自动选并记理由；②无客观判据 → 派对抗镜复核推荐项，通过方自动选（复核记录进报告）；③复核不过或无从复核 → defer 进 buglist/todolist 由 hand-off 引导清理。禁以自评置信（"有把握"）为唯一依据。
```
③ 步 6 prompt 的"逐任务 checkpoint-commit"句升格为：
```markdown
plan 每任务的 commit 步 MUST 显式写 `bash ~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "<描述>"` 并由 implementer（实现子代理）自己执行——`task<N>-` 标签是 /sdflow-ship gate 完成判据主锚（主 session 事后补跑会因工作区已净而空转）。
```

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q`
Expected: 31 passed, no warnings

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task7-workflow-authority "workflow.md 入口行+决策4 T10+步6标签契约(D1注入点)"
```

---

### Task 8: model-tiers（规则文件 + config 覆盖段 + 四 SKILL 零内联）

**Files:**
- Create: `sdflow-init/assets/workflow/model-tiers.md`
- Modify: `sdflow-init/assets/workflow/config.template.yaml`
- Modify: `sdflow-init/assets/snippets/index-section.md`（规则表加行；先 Read 确认文件名与表格式）
- Modify: `sdflow-ship/SKILL.md`、`sdflow-done/SKILL.md`、`sdflow-spec-review/SKILL.md`、`sdflow-code-review/SKILL.md`（全文裸模型名清零）
- Test: `sdflow-ship/tests/test_model_tiers.py`

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_model_tiers.py`：
```python
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TIERS = REPO / "sdflow-init" / "assets" / "workflow" / "model-tiers.md"
CONFIG = REPO / "sdflow-init" / "assets" / "workflow" / "config.template.yaml"
SKILLS = ["sdflow-ship/SKILL.md", "sdflow-done/SKILL.md",
          "sdflow-spec-review/SKILL.md", "sdflow-code-review/SKILL.md"]
BARE = re.compile(r"\b(opus|sonnet|haiku|Opus|Sonnet|Haiku)\b")

def test_tiers_file_is_truth_source():
    t = TIERS.read_text(encoding="utf-8")
    for kw in ("强档", "中档", "弱档", "opus", "sonnet", "haiku",
               "verify", "对抗裁决", "机队锚定"):
        assert kw in t

def test_config_overlay_section():
    t = CONFIG.read_text(encoding="utf-8")
    assert "model-tiers" in t and "覆盖" in t and "model-tiers.md" in t

def test_skills_zero_inline_model_names():
    for rel in SKILLS:
        for i, line in enumerate((REPO / rel).read_text(encoding="utf-8").splitlines(), 1):
            if "model-tiers.md" in line:      # 引用句白名单
                continue
            assert not BARE.search(line), f"{rel}:{i} 残留裸模型名: {line.strip()}"
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_model_tiers.py -q`
Expected: FAIL

- [ ] **Step 3: 实现**

新建 `sdflow-init/assets/workflow/model-tiers.md`：
```markdown
# model-tiers — 模型档位映射（单一真相源）

> 机队锚定〔adr/0006(c)〕：档位是**相对执行机队**的相对词（机队会换血），不绑具体产品名。
> 消费仓覆盖：`openspec/config.yaml` 的 `model-tiers` 段仅作 per-repo 覆盖映射，缺省勿填。
> 编排 skill 一律以一句引用指向本文件，MUST NOT 内联模型名。

| 档位 | 职责（谁必须用它） | canonical 缺省 |
|---|---|---|
| **强档 strong** | verify 终门 / 对抗裁决（Step3 主审）/ final whole-branch 终审 | opus |
| **中档 mid** | 领域镜·对抗镜（判断/对抗推理）/ 生成 / 实现 / archive 对码 | sonnet |
| **弱档 light** | 纯机械步：接地镜 grep 核验 / 历史镜 / 置信打分 / commit message | haiku |

铁律：带门禁、无人逐条复核的步 MUST NOT 降档（假绿会放不完整的活过关）；
纯机械步可下放弱档（失败可重试、无判断权重）。
```

`config.template.yaml` 末尾追加：
```yaml
# model-tiers（可选覆盖段）——真相源 = 规则根 model-tiers.md（resolver 解析）。
# 此段仅 per-repo 覆盖"档位→模型"映射；缺省请勿填（留空即用 canonical 缺省）。
# model-tiers:
#   strong: <model-id>
#   mid: <model-id>
#   light: <model-id>
```

`snippets/index-section.md` 规则表加一行（匹配现有表格式）：
```markdown
| model-tiers.md | 模型档位映射（强/中/弱职责 + canonical 缺省 + config 覆盖语义） |
```

四个 SKILL.md（先 Read 再逐处 Edit）：把全文所有裸模型名行（sdflow-done 的两处派发行 `model: sonnet`/`model: haiku`、"模型选择"表格、sdflow-spec-review/code-review 的模型建议列与模型选择节、sdflow-ship Task 6 已写的引用句保持）统一改为档位词 + 引用句。规范写法：
- 派发行：`派发 Agent（model: 按规则根 model-tiers.md 中档；config.yaml model-tiers 段可覆盖）`
- 表格列：`强档`/`中档`/`弱档`（表头注一句"档位与缺省见规则根 model-tiers.md"）
- 每文件保留恰好一句白名单引用：`档位与缺省见规则根 \`model-tiers.md\`（resolver 解析；config.yaml model-tiers 段可覆盖映射）`

- [ ] **Step 4: 跑测确认通过 + 全仓回归**

Run: `python3 -m pytest sdflow-ship/tests/ -q && python3 -m pytest -q`
Expected: 全绿无 warning（全仓 233+ 用例不受影响）

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task8-model-tiers "model-tiers.md 真相源+config 覆盖段+snippets 行+四 SKILL 零内联(T11)"
```

---

### Task 9: T20 串行句 + grep 断言留档 assert-log.md

**Files:**
- Modify: `sdflow-spec-review/SKILL.md`（Step2 首句）
- Create: `openspec/changes/sdflow-ship/assert-log.md`
- Test: `sdflow-ship/tests/test_serial_discipline.py`

- [ ] **Step 1: 写失败测试**

`sdflow-ship/tests/test_serial_discipline.py`：
```python
from pathlib import Path

SR = Path(__file__).resolve().parents[2] / "sdflow-spec-review" / "SKILL.md"

def test_step2_serial_must_sentence():
    t = SR.read_text(encoding="utf-8")
    assert "MUST 待 Step1" in t and "checkpoint 完成后才 fan-out" in t
    assert "禁止与 Step1 并行" in t
    assert "增量核对" in t   # 历史并行补救句
```

- [ ] **Step 2: 跑测确认失败**

Run: `python3 -m pytest sdflow-ship/tests/test_serial_discipline.py -q`
Expected: FAIL

- [ ] **Step 3: 实现**

`sdflow-spec-review/SKILL.md`「## 第二步」标题行之后加首句（D6 全文）：
```markdown
> **串行纪律〔T20〕**：**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明。
```

然后跑断言集并留档 `openspec/changes/sdflow-ship/assert-log.md`（记录每条命令 + 实际输出）：
```bash
grep -c "有把握自动选" sdflow-init/assets/workflow/workflow.md          # 期望 0
grep -l "model-tiers.md" sdflow-ship/SKILL.md sdflow-done/SKILL.md \
  sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md               # 期望 4 个文件全列出
grep -c "MUST 待 Step1" sdflow-spec-review/SKILL.md                     # 期望 ≥1
grep -c "ship-gate: design-approved" sdflow-spec-review/SKILL.md        # 期望 ≥1
grep -c "ship-gate: verify" sdflow-done/SKILL.md                        # 期望 ≥2
grep -c "ship-gate: code-review" sdflow-code-review/SKILL.md            # 期望 ≥2
python3 -m pytest -q 2>&1 | tail -2                                     # 全绿无 warning
```
assert-log.md 结构：`# assert-log — sdflow-ship` + 逐条「命令 / 期望 / 实际输出（原样粘贴）/ ✅」。**实际输出必须真实执行粘贴，禁"文本已改"式自证。**

- [ ] **Step 4: 跑测确认通过**

Run: `python3 -m pytest sdflow-ship/tests/ -q && python3 -m pytest -q`
Expected: 全绿无 warning

- [ ] **Step 5: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task9-serial-assertlog "T20 串行句(4.1)+grep 断言留档 assert-log.md(5.2)"
```

---

### Task 10: 文档收尾 + 债务闭环 + instance 同步

**Files:**
- Modify: `README.md`（Skills 列表加 sdflow-ship 行）
- Modify: `openspec/ROADMAP.md`（`opsx-ship-orchestrator` 行更名 `sdflow-ship` + materialize 注记 + 状态推进）
- Modify: `openspec/adr/0004-opsx-ship-stage3-orchestrator.md`（标题下加一行注记："落地名 sdflow-ship，见 adr/0007 命名规范"，不改历史正文）
- 债务闭环 + instance 同步（命令步）

- [ ] **Step 1: 文档三处（先 Read 再 Edit，各一行级改动）**

README「Skills 列表」按现有表格式加：`| sdflow-ship | 阶段三编排器：gate 台账驱动 5.5→9 到 merge 建议 |`（列数随现表）。ROADMAP 找 `opsx-ship-orchestrator` 行改名 + 注记。adr/0004 标题行下加注记行。

- [ ] **Step 2: 债务闭环（T10/T11/T20 → DONE + reindex）**

```bash
EV="change sdflow-ship, $(git rev-parse --short HEAD)"
python3 ~/.claude/skills/todolist-recorder/scripts/todolist.py set-status --id T10 --to DONE --evidence "$EV; sdflow-ship/SKILL.md 决策协议节 + workflow.md 决策4"
python3 ~/.claude/skills/todolist-recorder/scripts/todolist.py set-status --id T11 --to DONE --evidence "$EV; assets/workflow/model-tiers.md + config.template.yaml 覆盖段 + 四 SKILL 引用句"
python3 ~/.claude/skills/todolist-recorder/scripts/todolist.py set-status --id T20 --to DONE --evidence "$EV; sdflow-spec-review/SKILL.md Step2 串行句"
python3 ~/.claude/skills/issues-recorder/scripts/issues.py reindex
```
（路径不存在则按 sibling 兜底：`~/.codex/skills/...` 或仓内 `sdflow-todolist/scripts/todolist.py`、`sdflow-issues/scripts/issues.py`。）

- [ ] **Step 3: instance 同步（权威源 → 本仓 openspec/workflow/）**

```bash
python3 sdflow-init/scripts/init.py update --dev --root .
git status --short   # 确认 openspec/workflow/ 收到 model-tiers.md 与 workflow.md 更新
python3 -m pytest -q # 最终全量回归，全绿无 warning
```

- [ ] **Step 4: checkpoint**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh task10-docs-debt-sync "README/ROADMAP/adr0004 注记+T10/T11/T20 DONE+reindex+update --dev(6.1-6.3)"
```

---

## 测试覆盖图

```
NEW CODEPATHS（ship_gate.py 决策图全分支） → tests/test_gate_*.py 22 例
  pre-flight 3态+冲突锚 / TG-02 两态 / plan 缺·标题0·窗口污染·辅通道·done_tasks
  / cr 缺·blocked·无锚 / verify 缺·FAIL·无锚 / final 3件套·分支态 / D9 六态(Q1×2/Q3/陈旧×2/openspec保鲜)
NEW 契约耦合面 → test_anchor_contract.py（gate 头注释 ↔ 三 SKILL 模板双向）
NEW prose 契约 → test_skill_text.py / test_workflow_authority.py / test_serial_discipline.py / test_model_tiers.py
回归 → 全仓 pytest（recorder/init/roadmap 233+ 例不受影响）
慢/脆点：全部 git 沙箱本地操作，无网络、无时间依赖；merge fixture 用 -s ours 确定性。
```

## Self-Review（已执行）

- Spec 覆盖：R-SS-1→Task1-5；R-SS-2→Task8；R-SS-3→Task6/7；R-SS-4→Task9；tasks.md 6.x→Task10。设计门拍板 Q1=B/Q2/Q3=A 分别落 Task4/Task2/Task4。评审 D1-D12 全部有落点（D1→T7/T6、D2→T5、D3→T1 头注释+T3、D4→T1、D5 熔断→T6、D6→T3、D7→T2、D8→T8、D9→T6 frontmatter、D10→T2、D11→T1 头注释、D12→实现时随手，H4 archive 重入已在 T3 final glob 覆盖）。
- 占位扫描：无 TBD/TODO/"类似 Task N"；所有代码步含完整代码。
- 类型一致：`run_gate` 返回 (code, js, human) 全文件一致；`approved_change`/`impl_done` 跨文件 import 路径一致（tests 同目录平铺）。
