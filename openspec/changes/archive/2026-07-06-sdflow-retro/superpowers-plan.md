# sdflow-retro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建数据类 skill `sdflow-retro`，一条命令从 git 历史（成本/时间维）+ 归档评审报告的 lens-metric 锚（价值维）只读再生「全项目 change 成本×价值复盘」到 `openspec/retro/report.md`。

**Architecture:** 主脚本 `retro_report.py` owns 机械活（change 边界检测靠提交路径不靠 tag、阶段墙钟、hr-tg 双列、join 镜价值）；吸收现有 `lens_metric_aggregate.py`（git mv 进 skill scripts/）做镜价值聚合。SKILL.md 只判断+编排调脚本。`sdflow-maintain` 步骤 5 塌成薄指针（策略 B）。报告 view-only 再生、tracked 活文档。

**Tech Stack:** Python 3（标准库 only：subprocess/pathlib/re/tempfile/os；无第三方依赖，承本仓数据类脚本口径）；pytest 自测。

## Global Constraints

以下为 design.md 领域约束，**每个任务的要求隐含包含本节**，取值逐字自 design：

- **零改 ship_gate tag 契约**：change 归属靠 `git log -- openspec/changes/<name>/`（pre-archive 路径，**非 `--follow`**），**不靠** checkpoint tag；MUST NOT 改 `checkpoint-commit.sh` tag 格式（会踩 `ship_gate.py:200` 精确豁免 `== "checkpoint(impl-review)"` + 命名空间任务标签契约）。
- **D-A / D8 — done 靠 path-rename**：done/归档阶段靠"提交把 change dir `git mv` 进 `archive/`"的路径 rename 事件（R 状态/删旧建新）判定，**不靠 subject 前缀**（实测 14/15 归档提交是 `chore(openspec)`/`feat(...)` 非 `checkpoint(done-archive)`）。
- **D-B / D9 — seed/0-1 边界守卫**：①剔除 seed-mass 提交（一提交碰 **≥3** change dir，如创世 `db3c824`）②pre-archive 路径 0 提交 → 兜底查 archive 路径 ③恰好 0/1 提交 → 显式守卫（墙钟不可算、标"边界不可解析"计入顶部 K 计数、不崩）。
- **D-C — 阶段词表最长前缀匹配**：`impl-review` 优先于 `review`；`-fix/-gate/-autoplan/-rewrite` 归并主族；补 `design-gate`（归 spec-review 段）/`writing-plans`/`model-baseline`（归 impl）/`final-review`（归 code-review）词条；映射不出 → "unknown 阶段"桶（计入总墙钟、报告标注）。additive 约定，MUST NOT 改 tag 格式。
- **D-D / D11 — 价值维双源双报告**：per-change join 扫 **active `changes/*/` + archive 两处**、聚合 `spec-review-report.md` **与** `code-review-report.md` **两份**报告的锚，按 `layer`（spec-review/code-review）分归属。MUST NOT 只扫 archive（有锚的活动 change 会被误标"无锚"）、MUST NOT 只取一份（漏一半锚）。
- **D-E / D10 — hr-tg 双列**：读 spec-review + code-review 各自 `hr-tg` 锚 hit → `spec_hr_tg`/`code_hr_tg` **两列**；不做语义分桶，只客观 flag（单列会 none 覆盖命中）。
- **D3 — 不做语义 change 类型分桶**：只报客观列（总墙钟/Σfindings/code-rev 占比%）+ hr-tg 客观 flag。
- **D6 — 不加 token 估算列**（无 harness 数据，估算误导；同 adr/0009 诚实口径）。
- **D-G / D12 — surfacing 机械契约**：N≥10 待复评镜在报告顶部**独立 `⚠️ 待复评` 区块 + 固定前缀标记**（位置/标记可机验），MUST NOT 仅用"显著"形容词（不可机验 = 死列风险自我复现，grill-not-skippable 教训）。
- **D-H / D13 — 原子写**：report.md 写盘沿用 buglist/todolist 原子写口径（同目录 tempfile → `os.replace`；覆盖保原权限；无残留 tmp；replace 失败原文件不变）。retro_report.py **自带一份** `atomic_write`（按本仓纪律，scripts 自包含、不跨 skill import）。
- **D5 / D7 — 报告形态**：view-only 再生（锚/git 历史为 state 真相源，零新持久可变 state）；tracked 活文档；**含进行中 change**（活动 `changes/*/`，标 `in-progress`，价值维未落锚则标"无度量锚"）。
- **F5 / G2 铁律（级联善后）**：`sdflow-init/scripts/init.py` 的 `copy_bundle` **仅移出聚合器源文件**，`copytree(tools/)` + `ignore_patterns("tests")` 通用排除 **MUST 保留**（它非聚合器专属，还护 `trivial_shape.py` 部署 + `test_trivial_shape.py` 排除；照字面"删排除"会重演 CF-6 消费仓 pytest 污染）。`test_init.py` 断言**改指 `trivial_shape.py`/`test_trivial_shape.py`（非删）**，保 tests-exclusion 覆盖。
- **G1 — 布局钉死**：脚本与 tests/ 均在 `sdflow-retro/scripts/` 下（`scripts/lens_metric_aggregate.py` + `scripts/tests/test_*.py`）→ 移入后 test 的 `Path(__file__).resolve().parents[1]` 仍解析到 `scripts/`，无需改路径代码。
- **F3 — 绝对 skill 路径**：SKILL 调脚本用绝对 skill 路径 `~/.claude/skills/sdflow-retro/scripts/…`（禁 cwd 相对——cwd=消费仓根≠skill 目录；两运行时磁盘皆在）。
- **git 硬化**：`git log` 调用带 `core.quotePath=false`，`subprocess` 输出 `errors="replace"`（承 `trivial_shape.py` 口径），畸形输出不崩。
- **每任务 commit 步**MUST 由 implementer 子代理自己执行：`bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task<N>-<slug> "<描述>"`（`sdflow-retro:task<N>-` 命名空间标签是 /sdflow-ship gate 完成判据主锚）。
- **每任务完成跑对应 pytest 确认零 warning、零回归**（含 `test_init.py` + ship_gate 测试 + `test_trivial_shape.py`）。

---

### Task 1: git mv 聚合器进 skill scripts/ + 保持绿

把 `lens_metric_aggregate.py` + 其 tests 从 bundle 迁进新 skill，作为一切的地基。因 G1 布局钉死，`parents[1]` 移后仍成立，无需改路径代码。

**Files:**
- Move: `sdflow-init/assets/workflow/tools/lens_metric_aggregate.py` → `sdflow-retro/scripts/lens_metric_aggregate.py`
- Move: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py` → `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`
- Create: `sdflow-retro/scripts/tests/__init__.py`（空文件，确保 pytest 收集）

**Interfaces:**
- Produces: `sdflow-retro/scripts/lens_metric_aggregate.py`（聚合器；被 retro_report.py 与 SKILL 消费）

- [ ] **Step 1: git mv 两文件（保持 tests/ 在 scripts/ 下）**

```bash
mkdir -p sdflow-retro/scripts/tests
git mv sdflow-init/assets/workflow/tools/lens_metric_aggregate.py sdflow-retro/scripts/lens_metric_aggregate.py
git mv sdflow-init/assets/workflow/tools/tests/test_lens_metric_aggregate.py sdflow-retro/scripts/tests/test_lens_metric_aggregate.py
touch sdflow-retro/scripts/tests/__init__.py
```

- [ ] **Step 2: 确认 parents[1] 无需改（验证布局）**

Run: `grep -n "parents\[1\]" sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`
Expected: 输出 `_p = Path(__file__).resolve().parents[1] / "lens_metric_aggregate.py"`——parents[0]=tests, parents[1]=scripts，解析到 `scripts/lens_metric_aggregate.py`，**正确，不改**。

- [ ] **Step 3: 跑迁移后聚合器测试**

Run: `pytest sdflow-retro/scripts/tests/test_lens_metric_aggregate.py -q`
Expected: PASS（全部原有用例，与迁移前同数量绿）

- [ ] **Step 4: 确认 bundle tools/ 仍有 trivial_shape + tests/（不受影响）**

Run: `ls sdflow-init/assets/workflow/tools/trivial_shape.py sdflow-init/assets/workflow/tools/tests/test_trivial_shape.py`
Expected: 两文件仍在（tests-exclusion 覆盖对象还在，Task 12 re-point 依赖它）

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task1-mv-aggregator "git mv lens_metric_aggregate.py + tests 进 sdflow-retro/scripts/；parents[1] 布局保持；聚合器测试绿"
```

---

### Task 2: retro_report.py — change 发现

扫活动 + 归档目录，剥日期前缀取 change 名。这是流水线第一段。

**Files:**
- Create: `sdflow-retro/scripts/retro_report.py`
- Create: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Produces: `discover_changes(root: str) -> dict[str, dict]`——返回 `{name: {"active": bool, "active_dir": str|None, "archive_dir": str|None}}`。`active_dir` = `openspec/changes/<name>`（存在则）；`archive_dir` = `openspec/changes/archive/<date>-<name>`（存在则，剥 `YYYY-MM-DD-` 前缀取 name）。同名同时活动+归档 → 两字段都填。

- [ ] **Step 1: 写失败测试**

```python
# sdflow-retro/scripts/tests/test_retro_report.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import retro_report as R


def _mk(root, rel):
    p = root / rel
    p.mkdir(parents=True, exist_ok=True)
    return p


def test_discover_active_and_archive(tmp_path):
    _mk(tmp_path, "openspec/changes/foo")                      # 活动
    _mk(tmp_path, "openspec/changes/archive/2026-07-02-bar")   # 归档
    _mk(tmp_path, "openspec/changes/archive/2026-07-05-foo")   # foo 也有归档
    got = R.discover_changes(str(tmp_path))
    assert set(got) == {"foo", "bar"}
    assert got["foo"]["active"] is True
    assert got["foo"]["archive_dir"].endswith("2026-07-05-foo")
    assert got["bar"]["active"] is False
    assert got["bar"]["archive_dir"].endswith("2026-07-02-bar")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py::test_discover_active_and_archive -v`
Expected: FAIL（`retro_report` 无 `discover_changes` 或 ImportError）

- [ ] **Step 3: 写最小实现**

```python
# sdflow-retro/scripts/retro_report.py 顶部
import os
import re
import tempfile

_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")


def discover_changes(root):
    changes_dir = os.path.join(root, "openspec", "changes")
    archive_dir = os.path.join(changes_dir, "archive")
    out = {}
    if os.path.isdir(changes_dir):
        for name in os.listdir(changes_dir):
            p = os.path.join(changes_dir, name)
            if name == "archive" or not os.path.isdir(p):
                continue
            out.setdefault(name, {"active": False, "active_dir": None, "archive_dir": None})
            out[name]["active"] = True
            out[name]["active_dir"] = p
    if os.path.isdir(archive_dir):
        for entry in os.listdir(archive_dir):
            p = os.path.join(archive_dir, entry)
            if not os.path.isdir(p):
                continue
            m = _DATE_PREFIX.match(entry)
            name = m.group(1) if m else entry
            out.setdefault(name, {"active": False, "active_dir": None, "archive_dir": None})
            out[name]["archive_dir"] = p
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py::test_discover_active_and_archive -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task2-discover "retro_report.discover_changes：扫 active+archive、剥日期前缀取 change 名"
```

---

### Task 3: 边界检测 — git log per change + seed-mass 剔除 + 0/1 守卫 + archive 兜底（D9）

用真实归档语料 fixture 测——冷镜实测证 seed change/0 提交才是真 case。

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Consumes: `discover_changes`
- Produces: `git_commits_for_path(root, relpath) -> list[dict]`（每条 `{"sha","ts":int,"subject"}`，按时间升序；`git log --format=%H%x00%ct%x00%s -- <relpath>`，带 `-c core.quotePath=false`，`errors="replace"`，**无 `--follow`**）。
- Produces: `commit_change_dir_count(root, sha) -> int`（该提交碰了几个 `openspec/changes/<name>/` 顶层 change dir，用 `git show --name-only`；用于 seed-mass 判定 ≥3）。
- Produces: `boundary_for_change(root, name, info, seed_shas: set) -> dict`——返回 `{"commits":[...], "unresolved":bool, "note":str}`。逻辑：先 `git_commits_for_path(active_dir)`；剔除 `seed_shas`（seed-mass）；若剩 0 条 → 兜底 `git_commits_for_path(archive_dir)`（同样剔 seed-mass）；剩 0 或 1 条 → `unresolved=True`，note 记原因。

- [ ] **Step 1: 写失败测试（真实仓 fixture + 单元）**

```python
import subprocess

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, errors="replace").stdout


def _init_repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _commit(root, files: dict, msg):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


def test_seed_mass_excluded_and_0_1_guard(tmp_path):
    root = _init_repo(tmp_path)
    # 创世 mass 提交碰 3 个 change dir → seed-mass
    _commit(root, {
        "openspec/changes/archive/2026-07-02-seedA/proposal.md": "x",
        "openspec/changes/archive/2026-07-02-seedB/proposal.md": "y",
        "openspec/changes/archive/2026-07-02-seedC/proposal.md": "z",
    }, "chore:初始化")
    changes = R.discover_changes(str(root))
    seed = R.seed_mass_shas(str(root), threshold=3)
    b = R.boundary_for_change(str(root), "seedA", changes["seedA"], seed)
    # seedA 的 pre-archive 路径 0 提交（创世只碰 archive 路径），兜底 archive 后剔 seed-mass → 仍 0/1
    assert b["unresolved"] is True
    assert "边界不可解析" in b["note"]


def test_normal_change_boundary(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    changes = R.discover_changes(str(root))
    seed = R.seed_mass_shas(str(root), threshold=3)
    b = R.boundary_for_change(str(root), "foo", changes["foo"], seed)
    assert b["unresolved"] is False
    assert len(b["commits"]) == 2
    assert b["commits"][0]["subject"] == "checkpoint(ff)"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "seed_mass or normal_change_boundary" -v`
Expected: FAIL（无 `seed_mass_shas`/`boundary_for_change`）

- [ ] **Step 3: 写实现**

```python
def _run_git(root, *args):
    return subprocess.run(
        ["git", "-C", root, "-c", "core.quotePath=false", *args],
        capture_output=True, text=True, errors="replace").stdout


def git_commits_for_path(root, relpath):
    out = _run_git(root, "log", "--format=%H%x00%ct%x00%s", "--", relpath)
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x00")
        if len(parts) != 3:
            continue
        sha, ts, subject = parts
        try:
            commits.append({"sha": sha, "ts": int(ts), "subject": subject})
        except ValueError:
            continue
    commits.reverse()  # git log 默认逆序 → 升序
    return commits


def commit_change_dir_count(root, sha):
    out = _run_git(root, "show", "--name-only", "--format=", sha)
    dirs = set()
    for f in out.splitlines():
        m = re.match(r"openspec/changes/(?:archive/\d{4}-\d{2}-\d{2}-)?([^/]+)/", f)
        if m:
            dirs.add(m.group(1))
    return len(dirs)


def seed_mass_shas(root, threshold=3):
    out = _run_git(root, "log", "--format=%H")
    seed = set()
    for sha in out.split():
        if commit_change_dir_count(root, sha) >= threshold:
            seed.add(sha)
    return seed


def boundary_for_change(root, name, info, seed_shas):
    def _fetch(relpath):
        if not relpath:
            return []
        rel = os.path.relpath(relpath, root)
        cs = git_commits_for_path(root, rel)
        return [c for c in cs if c["sha"] not in seed_shas]
    commits = _fetch(info.get("active_dir"))
    if len(commits) == 0:
        commits = _fetch(info.get("archive_dir"))
    if len(commits) <= 1:
        return {"commits": commits, "unresolved": True,
                "note": f"边界不可解析（提交数={len(commits)}，seed/单步 change）"}
    return {"commits": commits, "unresolved": False, "note": ""}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "seed_mass or normal_change_boundary" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task3-boundary "边界检测：git log 路径归属 + seed-mass≥3 剔除 + 0/1 守卫 + archive 兜底（D9），真实 git fixture 测"
```

---

### Task 4: 阶段词表映射（最长前缀 D-C）+ done 靠 path-rename（D8）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Produces: `map_stage(subject: str) -> str`——从 checkpoint 前缀映射阶段。词表（最长前缀优先）：`ff→ff`；`grill→grill`；`spec-review*`/`design-gate→spec-review`；`writing-plans`/`model-baseline`/`task<N>*`/`*-impl→impl`；`impl-review*`/`final-review*`/`sdd-final-review→code-review`（`-fix/-gate/-autoplan/-rewrite` 归并主族）；`propose`/`plan*`/`roadmap*`/`issues`/`*-cross-review→other`；不命中→`unknown`。**注：`impl-review` 必须优先于 `review` 判断（最长前缀）。**
- Produces: `is_archive_rename(root, sha, name) -> bool`——该提交是否把 `changes/<name>/` `git mv` 进 `archive/`（`git show --name-status --format= <sha>`，检 R 状态源在 `changes/<name>/`、目标在 `archive/`；或删 `changes/<name>/` 同时建 `archive/**-<name>/`）。

- [ ] **Step 1: 写失败测试**

```python
def test_map_stage_longest_prefix(tmp_path):
    assert R.map_stage("checkpoint(impl-review)") == "code-review"
    assert R.map_stage("checkpoint(impl-review-fix)") == "code-review"
    assert R.map_stage("checkpoint(spec-review-autoplan)") == "spec-review"
    assert R.map_stage("checkpoint(spec-review-gate)") == "spec-review"
    assert R.map_stage("checkpoint(design-gate)") == "spec-review"
    assert R.map_stage("checkpoint(writing-plans)") == "impl"
    assert R.map_stage("checkpoint(model-baseline)") == "impl"
    assert R.map_stage("checkpoint(sdflow-retro:task3-boundary)") == "impl"
    assert R.map_stage("checkpoint(final-review)") == "code-review"
    assert R.map_stage("checkpoint(ff)") == "ff"
    assert R.map_stage("checkpoint(grill)") == "grill"
    assert R.map_stage("feat(x): 随手") == "unknown"


def test_archive_rename_detects_done(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    # 用 git mv 模拟归档
    (root / "openspec/changes/archive/2026-07-06-foo").mkdir(parents=True)
    _git(root, "mv", "openspec/changes/foo/proposal.md",
         "openspec/changes/archive/2026-07-06-foo/proposal.md")
    _git(root, "add", "-A"); _git(root, "commit", "-q", "-m", "chore(openspec): archive foo")
    sha = _git(root, "rev-parse", "HEAD").strip()
    assert R.is_archive_rename(str(root), sha, "foo") is True
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "map_stage or archive_rename" -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# 最长前缀词表：按前缀长度降序尝试匹配 checkpoint(<inner>)
_STAGE_RULES = [
    ("impl-review", "code-review"),
    ("final-review", "code-review"),
    ("sdd-final-review", "code-review"),
    ("spec-review", "spec-review"),
    ("design-gate", "spec-review"),
    ("writing-plans", "impl"),
    ("model-baseline", "impl"),
    ("grill", "grill"),
    ("ff", "ff"),
    ("propose", "other"),
    ("plan", "other"),
    ("roadmap", "other"),
    ("issues", "other"),
]
_CKPT_RE = re.compile(r"^checkpoint\(([^)]*)\)")


def map_stage(subject):
    m = _CKPT_RE.match(subject.strip())
    if not m:
        return "unknown"
    inner = m.group(1)
    # 命名空间任务标签 <change>:task<N>-... → impl
    tail = inner.split(":", 1)[1] if ":" in inner else inner
    if re.match(r"task\d+", tail) or tail.endswith("-impl"):
        return "impl"
    # 最长前缀匹配：规则按前缀长度降序
    for prefix, stage in sorted(_STAGE_RULES, key=lambda r: -len(r[0])):
        if inner.startswith(prefix):
            return stage
    if inner.endswith("-cross-review"):
        return "other"
    return "unknown"


def is_archive_rename(root, sha, name):
    out = _run_git(root, "show", "--name-status", "--format=", sha)
    moved_out = False
    into_archive = False
    for line in out.splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        status = cols[0]
        paths = cols[1:]
        if status.startswith("R") and len(paths) == 2:
            src, dst = paths
            if f"changes/{name}/" in src and "changes/archive/" in dst and dst.rstrip("/").find(name) != -1:
                return True
        if status == "D" and any(f"changes/{name}/" in p and "/archive/" not in p for p in paths):
            moved_out = True
        if status == "A" and any(f"changes/archive/" in p and name in p for p in paths):
            into_archive = True
    return moved_out and into_archive
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "map_stage or archive_rename" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task4-stage "阶段词表最长前缀映射（impl-review>review，补 design-gate/writing-plans/model-baseline/final-review）+ done 靠 path-rename（D8）"
```

---

### Task 5: 阶段墙钟 Δ（相邻 ts 差 + 负 Δ 钳 0）+ 含人时间标注（E, adr/0009）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Consumes: `boundary_for_change`（commits 升序）、`map_stage`、`is_archive_rename`
- Produces: `stage_walltimes(root, name, commits) -> dict`——返回 `{"stages": {stage: minutes}, "total_min": float, "n_ckpt": int, "reorder_suspected": bool}`。相邻 commit ts 差累加到**前一个** commit 映射的阶段；done 阶段由 `is_archive_rename` 命中的提交贡献；Δ<0 → 钳 0 且 `reorder_suspected=True`。

- [ ] **Step 1: 写失败测试**

```python
def test_stage_walltimes_and_negative_clamp(tmp_path):
    commits = [
        {"sha": "a", "ts": 1000, "subject": "checkpoint(ff)"},
        {"sha": "b", "ts": 1600, "subject": "checkpoint(grill)"},       # ff→grill: 600s=10min 归 ff
        {"sha": "c", "ts": 1500, "subject": "checkpoint(spec-review)"}, # 负 Δ → 钳 0 归 grill
    ]
    got = R.stage_walltimes(str(tmp_path), "foo", commits)
    assert got["stages"]["ff"] == 10.0
    assert got["stages"].get("grill", 0) == 0.0
    assert got["reorder_suspected"] is True
    assert got["n_ckpt"] == 3
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k stage_walltimes -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
def stage_walltimes(root, name, commits):
    stages = {}
    reorder = False
    for i in range(len(commits) - 1):
        cur, nxt = commits[i], commits[i + 1]
        delta_s = nxt["ts"] - cur["ts"]
        if delta_s < 0:
            delta_s = 0
            reorder = True
        if is_archive_rename(root, cur["sha"], name):
            stage = "done"
        else:
            stage = map_stage(cur["subject"])
        stages[stage] = stages.get(stage, 0.0) + delta_s / 60.0
    # 末提交若是 archive rename，单独记 done（无后继 Δ，仅标记存在）
    if commits and is_archive_rename(root, commits[-1]["sha"], name):
        stages.setdefault("done", 0.0)
    total = sum(stages.values())
    return {"stages": stages, "total_min": round(total, 1),
            "n_ckpt": len(commits), "reorder_suspected": reorder}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k stage_walltimes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task5-walltime "阶段墙钟相邻 Δ + 负 Δ 钳 0/reorder-suspected（E）+ done Δ 归 path-rename；含人时间口径"
```

---

### Task 6: join 镜价值 — active+archive 双源 + spec+code 双报告分 layer（D11）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Consumes: `discover_changes` 的 `active_dir`/`archive_dir`；复用 `lens_metric_aggregate.py` 的锚解析（import 同目录模块或复用其 fence-aware 解析函数）。
- Produces: `lens_value_for_change(info) -> dict`——扫该 change 的 active_dir + archive_dir 两处的 `spec-review-report.md` 与 `code-review-report.md`，解析 `lens-metric` 锚，按 `layer` 分归属；返回 `{"has_anchor":bool, "by_layer":{"spec-review":{...}, "code-review":{...}}, "sum_findings":int, "accept_rate":float|None, "sum_independent":int}`。无锚 → `has_anchor=False`。

- [ ] **Step 1: 写失败测试**

```python
ANCHOR = ('<!-- sdflow:lens-metric v1 layer="{layer}" lens="domain" runner="claude" '
          'site="—" findings="{f}" 采纳="{a}" 裁掉="0" defer="0" 独立="{ind}" '
          'sev="致0/高1/中0/低0" -->')


def test_lens_value_active_change_has_anchor(tmp_path):
    d = tmp_path / "openspec/changes/live"
    d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(
        ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n")
    (d / "code-review-report.md").write_text(
        ANCHOR.format(layer="code-review", f=4, a=3, ind=2) + "\n")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["has_anchor"] is True
    assert v["sum_findings"] == 13
    assert "spec-review" in v["by_layer"] and "code-review" in v["by_layer"]


def test_lens_value_no_anchor(tmp_path):
    d = tmp_path / "openspec/changes/bare"; d.mkdir(parents=True)
    (d / "proposal.md").write_text("no anchor here")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["has_anchor"] is False
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k lens_value -v`
Expected: FAIL

- [ ] **Step 3: 写实现（复用聚合器锚解析）**

```python
# 顶部 import 同目录聚合器
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_metric_aggregate as LMA   # 复用其 fence-aware 锚解析

_REPORT_NAMES = ("spec-review-report.md", "code-review-report.md")


def lens_value_for_change(info):
    anchors = []
    for base in (info.get("active_dir"), info.get("archive_dir")):
        if not base:
            continue
        for rn in _REPORT_NAMES:
            fp = os.path.join(base, rn)
            if os.path.isfile(fp):
                text = open(fp, encoding="utf-8", errors="replace").read()
                anchors.extend(LMA.parse_lens_anchors(text))  # 见下方备注
    by_layer = {}
    sum_f = sum_a = sum_ind = 0
    for a in anchors:
        layer = a.get("layer", "unknown")
        by_layer.setdefault(layer, {"findings": 0, "采纳": 0, "独立": 0})
        by_layer[layer]["findings"] += int(a.get("findings", 0))
        by_layer[layer]["采纳"] += int(a.get("采纳", 0))
        by_layer[layer]["独立"] += int(a.get("独立", 0))
        sum_f += int(a.get("findings", 0))
        sum_a += int(a.get("采纳", 0))
        sum_ind += int(a.get("独立", 0))
    rate = round(sum_a / sum_f, 2) if sum_f else None
    return {"has_anchor": bool(anchors), "by_layer": by_layer,
            "sum_findings": sum_f, "accept_rate": rate, "sum_independent": sum_ind}
```

> **备注（实现子代理必读）**：先 `grep -n "def " sdflow-retro/scripts/lens_metric_aggregate.py` 确认锚解析函数真实名（可能非 `parse_lens_anchors`）。若聚合器未暴露单锚解析函数、只有整表聚合入口，则在 retro_report.py 内**复用其 fence-aware 行级纪律重实现**一个 `parse_lens_anchors(text) -> list[dict]`（跳 fenced block、锚独占行前缀匹配、受限 kv 解析、禁裸 split/substring——与 spec.md「字段提取解析器是净新路径」要求一致），MUST NOT import ship_gate。测试用上面 fixture 校验字段提取正确。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k lens_value -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task6-join "join 镜价值：active+archive 双源 + spec+code 双报告按 layer 分归属（D11）；无锚标注不阻塞"
```

---

### Task 7: hr-tg 双列（D10）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Produces: `hr_tg_flags(info) -> dict`——返回 `{"spec_hr_tg":str, "code_hr_tg":str}`。从 spec-review-report.md 的 `sdflow:hr-tg` 锚读 `hit` → `spec_hr_tg`；从 code-review-report.md 读 → `code_hr_tg`；缺则 `"—"`。**两列独立，单列会 none 覆盖命中。**

- [ ] **Step 1: 写失败测试**

```python
HRTG = '<!-- sdflow:hr-tg v1 hit="{hit}" evidence="x" -->'

def test_hr_tg_two_columns(tmp_path):
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(HRTG.format(hit="none") + "\n")
    (d / "code-review-report.md").write_text(HRTG.format(hit="TG-06") + "\n")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    f = R.hr_tg_flags(info)
    assert f["spec_hr_tg"] == "none"
    assert f["code_hr_tg"] == "TG-06"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k hr_tg -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
_HRTG_RE = re.compile(r'<!--\s*sdflow:hr-tg\s+v1\s+hit="([^"]*)"')


def _read_hr_hit(base, report_name):
    if not base:
        return "—"
    fp = os.path.join(base, report_name)
    if not os.path.isfile(fp):
        return "—"
    for line in open(fp, encoding="utf-8", errors="replace"):
        m = _HRTG_RE.search(line)
        if m:
            return m.group(1)
    return "—"


def hr_tg_flags(info):
    def pick(rn):
        for base in (info.get("active_dir"), info.get("archive_dir")):
            hit = _read_hr_hit(base, rn)
            if hit != "—":
                return hit
        return "—"
    return {"spec_hr_tg": pick("spec-review-report.md"),
            "code_hr_tg": pick("code-review-report.md")}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k hr_tg -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task7-hrtg "hr-tg 双列 spec_hr_tg/code_hr_tg 各归位（D10）"
```

---

### Task 8: 报告合成 — per-change 行 + 顶部覆盖计数 + 聚合（schema）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Consumes: 前述所有 per-change 函数
- Produces: `build_report(root) -> str`——返回完整 markdown。顶部覆盖计数「覆盖 N change / 有真锚 M / 边界不可解析 K」；per-change 表（change | 总墙钟 | 各阶段 Δ | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | in-progress 标记）；聚合①阶段占比 ②成本双峰（总墙钟 vs code-review 占比）③per-镜价值表（内嵌聚合器输出）。

- [ ] **Step 1: 写失败测试（用真实本仓验证覆盖计数显性）**

```python
def test_build_report_coverage_counts(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    d = root / "openspec/changes/foo"
    (d / "spec-review-report.md").write_text(ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n")
    md = R.build_report(str(root))
    assert "覆盖" in md and "有真锚" in md and "边界不可解析" in md
    assert "foo" in md
    assert "in-progress" in md  # foo 是活动 change
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k build_report -v`
Expected: FAIL

- [ ] **Step 3: 写实现**（组装前述函数；顶部计数 N/M/K；per-change 行；聚合段。完整拼装 markdown 字符串，in-progress 标记来自 `info["active"]`。code-review 占比 = `stages.get("code-review",0)/total`。M = 有真锚 change 数，K = unresolved 数。）

```python
def build_report(root):
    changes = discover_changes(root)
    seed = seed_mass_shas(root)
    rows, M, K = [], 0, 0
    for name, info in sorted(changes.items()):
        b = boundary_for_change(root, name, info, seed)
        wt = stage_walltimes(root, name, b["commits"]) if not b["unresolved"] else \
            {"stages": {}, "total_min": 0.0, "n_ckpt": len(b["commits"]), "reorder_suspected": False}
        val = lens_value_for_change(info)
        hr = hr_tg_flags(info)
        if val["has_anchor"]:
            M += 1
        if b["unresolved"]:
            K += 1
        rows.append((name, info, b, wt, val, hr))
    N = len(changes)
    lines = ["# 全项目 change 成本×价值复盘（view-only 再生）", "",
             f"> 覆盖 {N} change / 有真锚 {M} / 边界不可解析 {K}",
             "> 阶段墙钟为「阶段级 elapsed（含人读/拍板/生成时间）」口径（adr/0009），非纯 agent 耗时。", ""]
    # ... surfacing 区块（Task 10 插入）、per-change 表、聚合①②③
    lines.append("| change | 总墙钟(min) | #ckpt | spec_hr_tg | code_hr_tg | Σfindings | 采纳率 | 独立Σ | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for name, info, b, wt, val, hr in rows:
        status = "in-progress" if info["active"] and not info["archive_dir"] else "archived"
        note = "（边界不可解析）" if b["unresolved"] else ""
        rate = "无度量锚" if not val["has_anchor"] else f'{val["accept_rate"]}'
        lines.append(f'| {name} | {wt["total_min"]}{note} | {wt["n_ckpt"]} | '
                     f'{hr["spec_hr_tg"]} | {hr["code_hr_tg"]} | '
                     f'{val["sum_findings"] if val["has_anchor"] else "—"} | {rate} | '
                     f'{val["sum_independent"] if val["has_anchor"] else "—"} | {status} |')
    # 聚合①阶段占比、②双峰（总墙钟 x, code-review 占比 y）、③per-镜价值表（调 lens_metric_aggregate 汇总 active+archive）
    return "\n".join(lines) + "\n"
```

> 聚合③ per-镜价值表：调 `lens_metric_aggregate` 的整表聚合入口（先 grep 其函数名），传 archive 根，把输出表内嵌。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k build_report -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task8-report "报告合成：顶部覆盖计数 N/有真锚 M/K 显性 + per-change 表（hr-tg 双列/in-progress）+ 聚合段"
```

---

### Task 9: 原子写（D13）+ 幂等 + CLI 入口

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Produces: `atomic_write(path, text)`（自带一份，同 buglist 口径）；`main(argv)`——`retro_report.py --root <root>` 再生 `openspec/retro/report.md`。
- Produces: 幂等——源无变化二次运行产出等价报告。

- [ ] **Step 1: 写失败测试**

```python
def test_atomic_write_preserves_on_replace_and_no_tmp(tmp_path):
    target = tmp_path / "openspec/retro/report.md"
    R.atomic_write(str(target), "hello")
    assert target.read_text() == "hello"
    # 无残留 tmp
    assert not any(p.suffix == ".tmp" for p in (tmp_path / "openspec/retro").iterdir())


def test_report_idempotent(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    a = R.build_report(str(root))
    b = R.build_report(str(root))
    assert a == b
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "atomic_write or idempotent" -v`
Expected: FAIL

- [ ] **Step 3: 写实现**（复制 buglist 的 `atomic_write` 全实现——见下；加 `main`）

```python
def atomic_write(path, text):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            mode = os.stat(path).st_mode & 0o777
        except FileNotFoundError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    md = build_report(root)
    out = os.path.join(root, "openspec", "retro", "report.md")
    atomic_write(out, md)
    print(f"[sdflow-retro] 复盘报告已再生 → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k "atomic_write or idempotent" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task9-atomic "原子写 helper（D13，同 buglist 口径）+ 幂等验证 + CLI main --root"
```

---

### Task 10: N≥10 待复评镜 surfacing 机械契约（D12）

**Files:**
- Modify: `sdflow-retro/scripts/retro_report.py`
- Modify: `sdflow-retro/scripts/tests/test_retro_report.py`

**Interfaces:**
- Produces: `surfacing_block(root) -> str`——从 lens_metric_aggregate 输出识别「出现轮数≥10」的镜，在报告**顶部独立区块**输出，**固定前缀标记** `⚠️ 待复评:`（可机验）。无命中 → 输出固定行 `⚠️ 待复评: 无（所有镜出现轮数<10）`（不省略，防死列）。

- [ ] **Step 1: 写失败测试**

```python
def test_surfacing_block_fixed_prefix(tmp_path):
    # 无命中也必须有固定前缀行（可机验）
    block = R.surfacing_block(str(tmp_path))
    assert block.strip().startswith("⚠️ 待复评:")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k surfacing -v`
Expected: FAIL

- [ ] **Step 3: 写实现**（调聚合器拿 per-镜出现轮数，≥10 的列进区块；`build_report` 顶部插入 `surfacing_block` 结果，紧接覆盖计数之后）

```python
def surfacing_block(root):
    archive = os.path.join(root, "openspec", "changes", "archive")
    flagged = []
    try:
        # 复用聚合器整表聚合（函数名先 grep 确认）
        table = LMA.aggregate(archive)  # 返回 per-镜行，含 出现轮数/flag
        for row in table:
            if row.get("出现轮数", 0) >= 10:
                flagged.append(row)
    except Exception:
        pass
    if not flagged:
        return "⚠️ 待复评: 无（所有镜出现轮数<10）"
    lines = ["⚠️ 待复评: 以下镜出现轮数≥10、只提示不判断不自动砍——人读后自行决定保留/降采样/淘汰:"]
    for r in flagged:
        lines.append(f"  - {r.get('lens','?')}（出现轮数 {r.get('出现轮数')}）")
    return "\n".join(lines)
```

> 然后在 `build_report` 顶部计数行之后插入 `lines.append(surfacing_block(root))`。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-retro/scripts/tests/test_retro_report.py -k surfacing -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task10-surfacing "N≥10 待复评镜机械契约：报告顶部独立区块 + 固定前缀标记（D12，可机验非形容词）"
```

---

### Task 11: SKILL.md 编排

**Files:**
- Create: `sdflow-retro/SKILL.md`

**Interfaces:**
- Produces: 可安装 skill（`SKILL.md` 是 setup.sh 唯一识别标志）；frontmatter `name: sdflow-retro` + `description`（锚定「openspec change / 评审工作流 / 成本×价值 / 镜价值 复盘」限定词，与运行时同名 gstack `retro` 及 maintain 区隔）。

- [ ] **Step 1: 写 SKILL.md**（frontmatter + 编排主体：判断→调 `~/.claude/skills/sdflow-retro/scripts/retro_report.py --root <仓根>`（绝对 skill 路径，F3）→ 呈现待复评。数据类 skill 约定：机械活交脚本、SKILL 只判断编排。缺 python3/脚本时降级提示。）

- [ ] **Step 2: 校验 frontmatter 合法 + description 含限定词**

Run: `head -5 sdflow-retro/SKILL.md`
Expected: 有 `name: sdflow-retro` 与含「复盘/评审工作流/成本×价值」的 description。

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task11-skill "SKILL.md 编排：绝对 skill 路径调脚本（F3）+ description 限定词锚定触发精度"
```

---

### Task 12: 级联善后 — maintain 瘦身 + init.py + test_init re-point + prose 指针 + INDEX

聚合器迁移后的所有下游同步。**F5/G2 铁律：init.py 排除逻辑保留、test_init 改指 trivial_shape 非删。**

**Files:**
- Modify: `sdflow-maintain/SKILL.md`（步骤 5 → 薄指针）
- Modify: `sdflow-init/scripts/init.py`（仅同步注释，`copy_bundle` 逻辑不动）
- Modify: `sdflow-init/tests/test_init.py`（断言改指 trivial_shape）
- Modify: `sdflow-code-review/SKILL.md`、`sdflow-spec-review/SKILL.md`、`docs/workflow-skills/sdflow-code-review.md`（prose 指针）
- Modify: `openspec/INDEX.md`

- [ ] **Step 1: test_init 改指 trivial_shape（先改测试，验证仍绿）**

`sdflow-init/tests/test_init.py`：
- `test_tools_tests_not_deployed_to_consumer`：`assert (tools_dst / "lens_metric_aggregate.py").is_file()` → `assert (tools_dst / "trivial_shape.py").is_file()`（docstring 里 `test_lens_metric_aggregate.py` 举例改 `test_trivial_shape.py`）
- `test_full_flag_still_includes_tools_tests`：`assert (wf / "tools" / "tests" / "test_lens_metric_aggregate.py").is_file()` → `assert (wf / "tools" / "tests" / "test_trivial_shape.py").is_file()`

- [ ] **Step 2: 跑 test_init 确认绿**

Run: `pytest sdflow-init/tests/test_init.py -q`
Expected: PASS（tests-exclusion 覆盖用 trivial_shape 保住）

- [ ] **Step 3: init.py 注释同步**——把 `copy_bundle` docstring 里"那是聚合器脚本（lens_metric_aggregate.py）的内部 pytest"改为通用表述（如"那是 tools/ 脚本的内部 pytest，如 test_trivial_shape.py"），别暗示 tests 排除只为聚合器。`copytree`+`ignore_patterns("tests")` 逻辑**一行不改**。

- [ ] **Step 4: maintain 步骤 5 → 薄指针**——`sdflow-maintain/SKILL.md` 步骤 5（77-91 行区）内联聚合 surfacing 塌成薄指针：归档后显著提示「跑 `/sdflow-retro` 看完整复盘（含 N≥10 待复评镜）」，不内联聚合逻辑、不丢归档后自动提醒 cadence。核对 maintain description 若提聚合则同步回归纯 INDEX.md 本职。

- [ ] **Step 5: prose 指针改指 retro**——grep 并改：
```bash
grep -rn "tools/lens_metric_aggregate.py\|/sdflow-maintain.*聚合\|由 \`/sdflow-maintain\`" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md docs/workflow-skills/sdflow-code-review.md
```
把「由 /sdflow-maintain 收尾步触发（跑 tools/lens_metric_aggregate.py…）」改为「由 /sdflow-retro 聚合（跑 sdflow-retro/scripts/lens_metric_aggregate.py…）」；聚合器路径 `tools/lens_metric_aggregate.py` → `sdflow-retro/scripts/lens_metric_aggregate.py`。覆盖 code-review:131-132+179、spec-review:104-105+120、docs 中 maintain 引用。

- [ ] **Step 6: INDEX.md**——`openspec/INDEX.md` `workflow-metrics` 条目聚合器路径 `lens_metric_aggregate.py` 更新为 `sdflow-retro/scripts/`；新增 retro/ 策展条目（`openspec/retro/report.md` 全 change 复盘活文档）。

- [ ] **Step 7: 跑受影响测试全绿**

Run: `pytest sdflow-init/tests/ sdflow-retro/scripts/tests/ -q`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task12-cascade "级联善后：maintain 薄指针 + init.py 注释同步（逻辑不动 F5/G2）+ test_init 改指 trivial_shape + 4处 prose 指针 + INDEX retro 条目"
```

---

### Task 13: 部署 + dogfood + 全量零回归

**Files:**
- Modify: `setup.sh`（无需改，验证识别新 skill）；`README.md`、`CLAUDE.md`（新增 skill + `openspec/retro/` 角色）
- Create: `openspec/retro/report.md`（dogfood 产物）

- [ ] **Step 1: setup.sh 装新 skill**

Run: `bash setup.sh 2>&1 | grep -i retro`
Expected: `sdflow-retro` 被识别安装（含 SKILL.md → 建链接到 `~/.claude/skills/` 与 `~/.codex/skills/`）

- [ ] **Step 2: 全量 pytest 零回归**

Run: `pytest -q`
Expected: PASS（含 `test_init.py` tests-exclusion 改断言后绿 + `test_lens_metric_aggregate.py` 迁移后绿 + `test_retro_report.py` 全绿 + `test_trivial_shape.py` 未受影响 + ship_gate 测试仍绿——本 change 不改 tag）

- [ ] **Step 3: dogfood 对本仓再生报告**

Run: `python3 sdflow-retro/scripts/retro_report.py --root "$(git rev-parse --show-toplevel)"`
Expected: 生成 `openspec/retro/report.md`；人工核对——本 change sdflow-retro 自身进复盘标 in-progress；seed change（2026-07-02）标"边界不可解析"或 archive 兜底；归档提交是 chore/feat 的 change 的 done 阶段靠 path-rename 命中；顶部"有真锚 M"显示实测约 2-3（防 N=2 当趋势）。

- [ ] **Step 4: README + CLAUDE.md 同步**——README「Skills 列表」加 `sdflow-retro`；CLAUDE.md 数据类 skill 清单加 `sdflow-retro` + `openspec/retro/` 目录角色（全 change 复盘活文档）。

- [ ] **Step 5: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-retro:task13-deploy "部署：setup.sh 装 skill + 全量 pytest 零回归 + dogfood 首份 openspec/retro/report.md + README/CLAUDE.md 同步"
```

---

## 测试覆盖图（retro_report.py，TG-18 数据类必测）

```
  [+] change 边界检测
    ├── [★★★] 活动/归档 change 各归属正确（路径不靠 tag）        → Task 2/3
    ├── [★★★] seed change pre-archive 0 提交 → archive 兜底/仍 0-1 标不可解析（D9）→ Task 3
    ├── [★★★] seed-mass 提交(碰≥3 dir)被剔除，不污染墙钟起点（D9）→ Task 3
    ├── [★★★] done 靠 path-rename（归档提交是 chore/feat 也命中 done）（D8）→ Task 4
    ├── [★★] 前缀映射不出→unknown 桶；最长前缀（impl-review 不被 review 吞）（D-C）→ Task 4
    └── [★★] change 无提交历史/恰 1 提交 → 不崩                   → Task 3
  [+] 阶段墙钟
    ├── [★★★] 相邻 Δ 正确 + 含人时间口径标注                     → Task 5
    └── [★★] Δ<0（ts 非单调）钳 0 + reorder-suspected（E）        → Task 5
  [+] 镜价值 join
    ├── [★★★] 一 change 两份报告(spec+code)锚正确合并、分 layer（D11）→ Task 6
    ├── [★★★] active change 已有锚 → 挂上（非误标无锚）（D11）    → Task 6
    ├── [★★★] 无锚 change 标"无度量锚"不阻塞                      → Task 6
    └── [★★] hr-tg 双列 spec/code 各归位（单列 none 不覆盖命中）（D10）→ Task 7
  [+] 报告合成
    ├── [★★★] 覆盖计数正确（N/有真锚 M/K）                        → Task 8
    ├── [★★★] 原子写（无残留 tmp / replace 失败原文件不变）（D13）→ Task 9
    ├── [★★★] 幂等：二次运行等价（无漂移）                        → Task 9
    └── [★★★] N≥10 surfacing 固定前缀可机验（D12）               → Task 10
```

## Self-Review

- **Spec coverage**：spec.md 四条 ADDED 需求（只读再生全项目 / 边界靠路径 / 时间维阶段级含人时间 / 缺口显性 fail-safe）→ Task 2-10 覆盖；workflow-metrics 两条 MODIFIED（surfacing 正主迁 retro / 聚合器移 scripts）→ Task 1+11+12 覆盖。全部 D1-D13 有对应任务。
- **Placeholder scan**：join 的锚解析函数名与 surfacing 的聚合入口名标注了"先 grep 确认真实名"——非占位符，是对既有模块的显式接口核对指令（聚合器是迁入的既有代码，函数名以现码为准）。
- **Type consistency**：`boundary_for_change` 产 `{"commits","unresolved","note"}` → `stage_walltimes` 消费 commits；`lens_value_for_change` 产 `has_anchor/sum_findings/accept_rate/sum_independent/by_layer` → `build_report` 逐字段消费；`hr_tg_flags` 产 `spec_hr_tg/code_hr_tg` → 表列一致。

## Execution Handoff

计划已保存到 `openspec/changes/sdflow-retro/superpowers-plan.md`。按 /sdflow-ship 链序，下一步是 **subagent-driven-development** 逐任务执行（fresh 子代理 per task + 两阶段 review），final whole-branch 终审 dispatch 把 `code-checklists/domains/`（dev-tooling/python 数据类 skill）作额外 review lens 附给 reviewer。
