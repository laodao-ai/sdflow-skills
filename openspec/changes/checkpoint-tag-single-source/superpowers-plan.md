# checkpoint 标签 producer→parser 绑定测试 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 checkpoint 标签的 producer→parser 链加机械绑定测试——焊死 `checkpoint-commit.sh` 真产的 commit subject 能被 `ship_gate.py` 的 `TAG_RE` 正确识别，并补 `TAG_RE` 负例矩阵防"放松即静默保绿"。

**Architecture:** 纯测试新增，零运行时改动。在 `sdflow-ship/tests/` 新增一个测试文件：①集成测试在临时 git repo 里调**真实** `sdflow-init/assets/hack/checkpoint-commit.sh`，读回 commit subject，喂给 `import` 来的 `TAG_RE` 断言 match + 捕获组；②负例矩阵断言一组畸形 subject `TAG_RE.match(...) is None`。不改 `ship_gate.py`/`workflow.md`/`SKILL.md`/任何既有测试断言。

**Tech Stack:** Python 3 / pytest；`subprocess` 调 git 与 bash 脚本；`sys.path` 注入后 `from ship_gate import TAG_RE`。

## Global Constraints

- 只在 `sdflow-ship/tests/` **新增**测试文件，**不改** `ship_gate.py`、`workflow.md`、`SKILL.md`、任何既有测试断言（design D3）。
- 定位脚本/scripts 目录用**仓根相对路径 / `parents[N]`**，勿硬编码绝对路径（tasks 1.2）。照既有约定：`REPO = Path(__file__).resolve().parents[2]`。
- 每个任务 commit 步 MUST 用命名空间格式（ship gate 完成判据主锚）：
  `bash ~/.sdflow/hack/checkpoint-commit.sh checkpoint-tag-single-source:task<N>-<slug> "<msg>"`
- `TAG_RE` 现值（被测锚点，逐字不动）：`checkpoint\((?:([a-z0-9][a-z0-9-]*):)?task(\d+)-`
- 负例矩阵 MUST 覆盖三类放松：**空号 / 大写命名空间 / 无尾 dash**（design D2）。

---

### Task 1: producer→parser 集成测试（命名空间 + 裸格式）

**Files:**
- Create: `sdflow-ship/tests/test_producer_parser_contract.py`
- Reference (不改): `sdflow-init/assets/hack/checkpoint-commit.sh`（producer）、`sdflow-ship/scripts/ship_gate.py`（`TAG_RE` parser）
- Fixture: 复用 `sdflow-ship/tests/conftest.py` 的 `repo`（已 `git init` + 配 user）

**Interfaces:**
- Consumes: conftest `repo` fixture（返回一个已初始化的 tmp git repo 路径）
- Produces: 模块级 `TAG_RE`（import 自 `ship_gate`）、`SCRIPT`（producer 脚本绝对路径，由 `REPO` 推导）、helper `run_producer(repo, step)`（造一个文件变更 → 调脚本 → 返回 `git log -1 --format=%s` 的 subject）。Task 2 复用同文件的 `TAG_RE`。

- [ ] **Step 1: Write the failing test（文件头 + import + 集成两例）**

创建 `sdflow-ship/tests/test_producer_parser_contract.py`：

```python
"""producer→parser 契约：checkpoint-commit.sh 真产的 subject ↔ ship_gate.TAG_RE。
锚的是脚本真吐的字节 ↔ gate 真跑的正则（design D1），非文档占位符。"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "checkpoint-commit.sh"

# D4：scripts 不在 sys.path，注入后 import。ship_gate.py 有 __main__ 守卫，import 无副作用。
sys.path.insert(0, str(REPO / "sdflow-ship" / "scripts"))
from ship_gate import TAG_RE  # noqa: E402


def run_producer(repo, step):
    """在 repo 里造一处变更 → 调真实脚本 → 返回最后一个 commit 的 subject。"""
    (repo / f"f-{step}.txt").write_text(step, encoding="utf-8")  # 制造非空 porcelain
    subprocess.run(["bash", str(SCRIPT), step, "msg"], cwd=repo, check=True,
                   capture_output=True, text=True)
    out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%s"],
                         check=True, capture_output=True, text=True)
    return out.stdout.strip()


def test_namespaced_subject_matches_and_captures(repo):
    subject = run_producer(repo, "demo:task1-slug")
    assert subject == "checkpoint(demo:task1-slug): msg"
    m = TAG_RE.match(subject)
    assert m is not None
    assert (m.group(1), m.group(2)) == ("demo", "1")


def test_bare_subject_matches_with_null_namespace(repo):
    subject = run_producer(repo, "task1-slug")
    assert subject == "checkpoint(task1-slug): msg"
    m = TAG_RE.match(subject)
    assert m is not None
    assert m.group(1) is None
    assert m.group(2) == "1"
```

- [ ] **Step 2: Run tests to verify behavior**

Run: `cd "$(git rev-parse --show-toplevel)" && pytest sdflow-ship/tests/test_producer_parser_contract.py -v`
Expected: 两例 PASS（这是回归钉，`TAG_RE` 与脚本当前已一致，应直接绿；若 red 说明测试写法有误——按报错修 helper/断言，勿改 `ship_gate.py` 或脚本）。

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh checkpoint-tag-single-source:task1-producer-parser "producer→parser 集成测试(命名空间+裸格式)"
```

---

### Task 2: TAG_RE 负例矩阵

**Files:**
- Modify: `sdflow-ship/tests/test_producer_parser_contract.py`（在 Task 1 文件末尾追加）

**Interfaces:**
- Consumes: Task 1 已 import 的模块级 `TAG_RE`
- Produces: 参数化负例测试 `test_tag_re_rejects_relaxations`

- [ ] **Step 1: Write the failing test（追加负例矩阵）**

在 `sdflow-ship/tests/test_producer_parser_contract.py` 末尾追加。每条注明"该挡住的放松类"（design D2 表），使后人放松 `TAG_RE` 时知道红在哪：

```python
# design D2 负例矩阵：每条 MUST NOT match，封住"TAG_RE 被放松后 happy 例仍绿"的漏报。
NEGATIVE_CASES = [
    ("checkpoint(task1slug)",   "尾 dash 变可选（丢 task1/task12 边界锚）"),
    ("checkpoint(DEMO:task1-)", "命名空间允许大写（破 kebab 锁）"),
    ("checkpoint(task-1-)",     "号位允许非数字"),
    ("checkpoint(:task1-)",     "空命名空间"),
]


@pytest.mark.parametrize("subject,relaxation", NEGATIVE_CASES,
                         ids=[c[0] for c in NEGATIVE_CASES])
def test_tag_re_rejects_relaxations(subject, relaxation):
    assert TAG_RE.match(subject) is None, \
        f"负例 {subject!r} 竟被 match——{relaxation} 类放松未被挡住"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd "$(git rev-parse --show-toplevel)" && pytest sdflow-ship/tests/test_producer_parser_contract.py -v`
Expected: 4 条负例全 PASS（当前 `TAG_RE` 已能拒绝这四类）。
> 注：`checkpoint(:task1-)` 空命名空间——`TAG_RE` 的 `[a-z0-9][a-z0-9-]*` 要求至少一字符，故 `match` 从位置 0 会失败（`:task` 前无合法 ns 且可选组不匹配空 `:`），断言 `is None` 成立。若此条意外 match，说明理解有误——记录实际行为、按真实语义调整该条负例（不改 `TAG_RE`），其余三类（空号/大写 ns/无尾 dash）为硬要求 MUST 保留。

- [ ] **Step 3: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh checkpoint-tag-single-source:task2-negative-matrix "TAG_RE 负例矩阵(空号/大写ns/无尾dash)"
```

---

### Task 3: 回归确认

**Files:**
- 无新增/修改（仅运行验证 + 回填 tasks.md 复选框）
- Verify: `sdflow-ship/tests/`（含既有 `test_workflow_authority.py` 断言不变）、仓级 `pytest`

**Interfaces:**
- Consumes: Task 1+2 落地的新测试文件

- [ ] **Step 1: sdflow-ship/tests 全绿（含既有断言不变）**

Run: `cd "$(git rev-parse --show-toplevel)" && pytest sdflow-ship/tests/ -v`
Expected: 全 PASS，**含 `test_workflow_authority.py` 全部断言**（本 change 不改 SKILL.md/workflow.md，既有断言必须仍绿；若某条红说明误动了文档，回退该改动）。

- [ ] **Step 2: 仓级 pytest 无回归**

Run: `cd "$(git rev-parse --show-toplevel)" && pytest`
Expected: 全 PASS，新增用例数增加、零既有用例回归。
> 本 change 无 `assets/` 权威源改动，无需 `sdflow-init update`；仅加测试文件，无需重跑 `setup.sh`。

- [ ] **Step 3: 回填 tasks.md 复选框**

将 `openspec/changes/checkpoint-tag-single-source/tasks.md` 中已完成的 1.1/1.2/1.3/2.1/2.2/3.1/3.2 勾选为 `[x]`（本 change 无源码/文档改动，逐条据实回填）。

- [ ] **Step 4: Commit**

```bash
bash ~/.sdflow/hack/checkpoint-commit.sh checkpoint-tag-single-source:task3-regression-green "回归确认全绿 + 回填 tasks 复选框"
```

---

## Self-Review

**1. Spec coverage：**
- tasks 1.1（import TAG_RE / sys.path 注入）→ Task 1 Step 1（`sys.path.insert` + `from ship_gate import TAG_RE`）✓
- tasks 1.2（命名空间集成用例，仓根相对定位脚本）→ Task 1 `test_namespaced_subject_matches_and_captures` + `SCRIPT` 由 `REPO` 推导 ✓
- tasks 1.3（裸格式集成用例，group(1) is None）→ Task 1 `test_bare_subject_matches_with_null_namespace` ✓
- tasks 2.1/2.2（负例矩阵，空号/大写 ns/无尾 dash + 空 ns，逐条注放松类）→ Task 2 `NEGATIVE_CASES` 表 ✓
- tasks 3.1（sdflow-ship/tests 全绿含 authority 不变）→ Task 3 Step 1 ✓
- tasks 3.2（仓级 pytest 无回归、无需 update/setup）→ Task 3 Step 2 ✓
- design D1（真实脚本调用集成）✓ D2（负例矩阵三类）✓ D3（既有测试/文档不动）✓ D4（sys.path 注入 import）✓
- 无 gap。

**2. Placeholder scan：** 无 TBD/TODO/"handle edge cases"；每个 code step 含完整可运行代码与确切命令+预期。✓

**3. Type consistency：** `run_producer(repo, step)` 签名一致贯穿；`TAG_RE.match(...).group(1)/group(2)` 用法与 `ship_gate.py:231` 捕获组语义一致（组1=命名空间可空、组2=任务号）；`REPO`/`SCRIPT`/`NEGATIVE_CASES` 命名前后一致。✓
