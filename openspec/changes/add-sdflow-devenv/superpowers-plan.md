> # ⚠️ 已失效（2026-07-14）
>
> **本实现计划为 `docs/sad/07` 的旧设计所排——该设计已被 grill 九条决策整体推翻**（附录 **A23–A28**）。
> 其中大部分 Task 是**已死机制**的工期（文件锁 / CAS / 时效 digest / make 解析 / 五槽 / 两文档「方法vs操作」切线），
> 且 **Task 顺序本身就是病灶**——`references/` 排第 6、`SKILL.md` 排第 7，前面五层机械基础设施〔**A28**〕。
>
> **新的构建顺序见 `tasks.md`**（脑 → 手 → 记性）。
> **本文件按 `adr/0022`「整体失效」处置：内容原样保留，不删。**

---

# sdflow-devenv Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建一个 skill，把项目的 dev/test 环境真正建起来——产出一份三层测试策略框架（unit/integration/e2e，一层不留白）+ 可跑的 Makefile/harness/smoke，并**尽可能跑一遍确认**。

**Architecture:** 编排器（非生成器）。两份 JSON 侧文件为机械真相源（`.devenv-lanes.json` 泳道 / `.devenv-strategy.json` 三层框架），两份 Markdown 由脚本渲染。`devenv_scaffold.py` 写、`devenv_lint.py` 读。验证分两通道：`verify-lane`（脚本亲自 fork 执行）/ `confirm-lane`（人门写，标 `attested_by: human`）。

**Tech Stack:** Python 3（**仅标准库**）· pytest · Markdown

---

## Global Constraints

**这些约束对每个 Task 都生效。违反任一条 = 任务不通过。**

1. **机械层只做「防漏」（完整性），不做「防伪」（真实性）。** 写下任何一条"MUST 机械保证 X"之前先问"这个保证的信号从哪来"——答不上来就**不要写这个检查**。禁止再引入任何"证明模型没撒谎"的机制。真相源：`docs/sad/07-devenv-skill-design.md` §0.0。
2. **零第三方依赖。** 只用标准库。`sdflow-ship/tests/test_anchor_contract.py` 有测试断言禁 `import yaml`。**禁止 `pip install` 任何东西。**
3. **改 `scripts/` 必须同步写并跑 `tests/`**（本仓强制纪律）。
4. **⛔ MUST NOT 手搓 GNU make（或任何语言的）解析器**〔round-4 · `07` 附录 **A21** · **本条取代原「digest 规范化按文件类型分治」**〕：
   - **所有 digest = `sha256(文件原始字节)`，一视同仁，零规范化。** 不提取 recipe body，不做空白/注释/缩进处理。
     （原「分治」规则是 recipe 提取的**衍生债**——不提取就不需要 normalize，那个假绿在结构上不可能发生。）
   - **`devenv_digest.py` MUST 零 make 知识**：不解析 recipe，**也不用正则查 target 存在性**（「正则找不到」≠「target
     不存在」⇒ 要么误报罢工、要么恒真假绿，两条路都错）。
   - **「target 存在且能跑」由 `verify-lane` 真 fork 执行保证——make 自己是权威判官**（拼错 → `No rule to make
     target` → `exit≠0` → 进不了 `verified`）；**「target 被删/改名」由 `file_digests` 失配抓**。
   - **一般化规则**：机械层想知道「某个 make/shell/语言构造是什么意思」，**正解是让那个工具自己回答**（真跑一遍 /
     `make -n`），**MUST NOT 手搓解析器去猜**。本 skill 的核心机制就是「尽可能跑一遍确认」——**跑一遍即最强的解析器。**
   - **唯二允许的浅 make 正则**（Task 12，均 **best-effort、均不做机械判定**）：① `append_makefile_target` 的**重名
     检测**（匹配到 → fail-closed 拒绝追加；漏判兜底 = 人门看 diff + make 自己报 `overriding recipe`）② **recipe 展示**
     给人看（失败 → **降级提示，MUST NOT 罢工**）。**这两处的代码 MUST NOT 被复用为任何 digest / 判定基准。**
   > **⚠️ 血的教训**：本约束的前一版（"分治 + selector 重定位"）导致 Task 4 三轮补丁螺旋——脚本 261→562 行、测试
   > 304→753 行，每轮 review 都挖出一个新的 make 语法角落（内联 `;` → `ifeq` 块 → `define` 块 → …）。**无界语法面上
   > 补丁循环不会自己收敛。** 而那 7 个「语法不支持」的 fail-closed 分支，**每一个都是对「不管什么项目都能给一份三层
   > 框架」这条核心承诺的一次背叛**。
5. **数据模型不含 `owned_by`；没有 cleanup ledger。** skill 不主动启停任何依赖服务，也不管理它没有启动过的资源。
6. **`confirm-lane` MUST NOT 声称保证了执行者身份**，产出标 `attested_by: human`。
7. **所有模型提供的路径 MUST 经统一的 `containment` helper**（Task 1）——拒绝绝对路径 / `..` / symlink 祖先 / 仓外 realpath。**禁止各模块自行实现路径校验。**
8. **三层框架落 JSON**，Markdown 从 JSON 渲染。**禁止让 lint 解析自由格式 Markdown。**
9. **checkpoint 格式（gate 主锚，权威 = `sdflow-ship/scripts/ship_gate.py` 的 `TAG_RE`）**：
   ```bash
   ~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task<N>-<slug>" "<message>"
   ```
   **`task<N>` 后面的横杠是强制的**——写成 `task1` 会让 gate 匹配不到、卡在 0/N。

---

## File Structure

```
sdflow-devenv/                          # 新建 skill
├── SKILL.md                            # 五步编排 · 三模式分流 · 两道人门（Task 16）
├── scripts/
│   ├── devenv_paths.py                 # containment helper（Task 1）—— 横切，最先
│   ├── devenv_lock.py                  # 写域锁 + atomic_write(mode) + owner（Task 2）
│   ├── devenv_schema.py                # 两份 JSON schema + schema_version（Task 3）
│   ├── devenv_digest.py                # file_digests：原始字节 sha256，【零 make 知识】（Task 4 · A21）
│   ├── devenv_runner.py                # 子进程执行（allowlist/进程组/超时/孤儿如实报告）（Task 9）
│   ├── devenv_txn.py                   # touched-files 事务 journal（Task 14）
│   ├── devenv_scaffold.py              # CLI 写侧：init/set-lane/verify-lane/confirm-lane/
│   │                                   #   render/inject/log/doctor-gen（Task 5-8, 10-12）
│   └── devenv_lint.py                  # CLI 读侧：诚实检查（Task 13）
├── references/                         # Task 15
│   ├── lane-patterns.md
│   ├── verification-patterns.md        # 含三条负面知识（实验证伪的方法）
│   ├── boundary-rules.md
│   ├── testing-strategy-template.md
│   ├── environments-template.md
│   ├── review-lenses.md
│   ├── exit-codes.md                   # 退出码表（一码一义）
│   └── env-allowlist.md                # 按栈的最小环境 allowlist
└── tests/
    ├── test_paths.py · test_lock.py · test_schema.py · test_digest.py
    ├── test_scaffold.py · test_runner.py · test_verify.py · test_render.py
    ├── test_lint.py · test_txn.py · test_lock_contract.py（跨 skill 锁协议一致性）
    └── fixtures/
        ├── brownfield/                 # 归位模式的 checkin fixture
        └── fence/                      # fence-aware 的固定语料（MUST NOT 用本仓活语料）

# 跨 skill 面治改动（Task 17-19）
sdflow-init/scripts/init.py             # inject() 补锁 + 原子写
sdflow-architecture/scripts/sad_scaffold.py  # 迁共用锁 + 从零加 owner + atomic_write(mode)
sdflow-maintain/scripts/maintain_scan.py     # 新增第五类扫描：devenv 健康度
```

**跨 skill 锁的代码共享问题（已决策，实现时照做）**：三个 skill 各自独立目录、symlink 安装、**无法互相 `import`**。故：**锁协议极简 + 三份各自实现 + 契约测试钉死格式一致**（照本仓 `test_producer_parser_contract` 先例）。锁文件内容格式钉死为单行 JSON：

```json
{"owner": "<uuid4 hex>", "pid": 12345, "ts": 1752400000.0}
```

---

### Task 1: 路径 containment helper（横切基座，最先做）

**Files:**
- Create: `sdflow-devenv/scripts/devenv_paths.py`
- Test: `sdflow-devenv/tests/test_paths.py`

**Interfaces:**
- Produces: `contain(root: Path, rel: str) -> Path` —— 校验通过返回**绝对 resolved 路径**；违规 raise `PathEscape(str)`。`class PathEscape(Exception)`。
- 后续所有 Task 读/写/删/digest **任何模型提供的路径**，都 MUST 先过 `contain()`。

- [ ] **Step 1: 写失败测试**

```python
# sdflow-devenv/tests/test_paths.py
import os, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_paths import contain, PathEscape


def test_accepts_plain_relative(tmp_path):
    (tmp_path / "Makefile").write_text("x\n")
    got = contain(tmp_path, "Makefile")
    assert got == (tmp_path / "Makefile").resolve()


def test_rejects_absolute(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "/etc/passwd")


def test_rejects_dotdot(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "../outside.txt")


def test_rejects_dotdot_in_middle(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "a/../../outside.txt")


def test_rejects_symlink_ancestor(tmp_path):
    outside = tmp_path.parent / "outside_dir"
    outside.mkdir()
    (outside / "loot.txt").write_text("secret\n")
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    # 目标文件本身不是 symlink，但它的【祖先】是 —— 前一版只查目标本身，会漏
    with pytest.raises(PathEscape):
        contain(tmp_path, "link/loot.txt")


def test_rejects_symlink_target_itself(tmp_path):
    outside = tmp_path.parent / "outside2.txt"
    outside.write_text("x\n")
    (tmp_path / "sneaky").symlink_to(outside)
    with pytest.raises(PathEscape):
        contain(tmp_path, "sneaky")


def test_nonexistent_path_ok_if_contained(tmp_path):
    # 写入新文件时目标还不存在 —— 必须允许（否则 skill 写不了新 smoke）
    got = contain(tmp_path, "internal/new_smoke_test.go")
    assert got == (tmp_path / "internal/new_smoke_test.go").resolve()


def test_rejects_empty(tmp_path):
    with pytest.raises(PathEscape):
        contain(tmp_path, "")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-devenv/tests/test_paths.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devenv_paths'`

- [ ] **Step 3: 实现**

```python
# sdflow-devenv/scripts/devenv_paths.py
"""路径 containment —— 所有模型提供的路径的唯一入口。

设计约束（spec: R-PATH）：
  source.file / smoke / fixtures[] / touched-files 清单
  全是【模型填的自由文本】。任何读/写/删/digest 之前 MUST 经此校验。
  注：外部配置文件（compose.yml 等）无独立字段 —— 归入 fixtures[]（见 Task 4 注）。

【为什么要逐级查 symlink 祖先】：前一版只拒绝「目标文件本身是 symlink」，
于是 `link/loot.txt`（父目录是指向仓外的 symlink）畅通无阻。
"""
import os
from pathlib import Path, PurePosixPath


class PathEscape(Exception):
    """路径逃逸出消费仓边界。"""


def contain(root, rel):
    """校验 rel 是 root 之内的安全相对路径，返回 resolved 绝对路径。

    root: Path —— 消费仓根（调用方保证它已 resolve）
    rel:  str  —— 模型提供的相对路径

    raise PathEscape 于：空路径 / 绝对路径 / 含 `..` / symlink 祖先或自身 /
                        最终 realpath 落在 root 之外
    """
    root = Path(root).resolve()

    if not rel or not str(rel).strip():
        raise PathEscape("空路径")

    p = PurePosixPath(str(rel).replace(os.sep, "/"))

    if p.is_absolute():
        raise PathEscape(f"拒绝绝对路径: {rel}")
    if any(part == ".." for part in p.parts):
        raise PathEscape(f"拒绝含 `..` 的路径: {rel}")

    # 逐级 lstat：任一层（含目标自身）是 symlink 即拒绝。
    # 注意用 lstat 不用 exists —— 不存在的路径是合法的（写新文件），
    # 但【存在且是 symlink】就必须拒。
    cur = root
    for part in p.parts:
        cur = cur / part
        if cur.is_symlink():
            raise PathEscape(f"拒绝 symlink（自身或祖先）: {cur.relative_to(root)}")

    # 最终 realpath 必须仍在 root 内（防 symlink 之外的逃逸路径，如挂载点）
    final = Path(os.path.realpath(str(cur)))
    try:
        final.relative_to(root)
    except ValueError:
        raise PathEscape(f"路径解析后落在消费仓之外: {rel} -> {final}")

    return cur.resolve()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-devenv/tests/test_paths.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task1-containment" "路径 containment helper：拒绝绝对路径/../symlink 祖先/仓外 realpath（R-PATH）"
```

---

### Task 2: 写域锁 + atomic_write(mode) + owner

**Files:**
- Create: `sdflow-devenv/scripts/devenv_lock.py`
- Test: `sdflow-devenv/tests/test_lock.py`

**Interfaces:**
- Produces:
  - `LOCK_REL = "openspec/.sdflow-write.lock"`（**三 skill 共用的锁名**）
  - `write_lock(root: Path)` —— contextmanager，包裹整个读-改-写序列
  - `atomic_write(path: Path, text: str, mode: int = 0o644)` —— **mode 参数是必需的**（`sad_scaffold` 硬编码 `0o644` ⇒ 生成的 doctor 脚本落盘即不可执行）
  - `LockBusy(Exception)` / `LockStale(Exception)`
- 锁文件内容格式（**契约，三 skill 必须一致**）：单行 JSON `{"owner": "<uuid4 hex>", "pid": <int>, "ts": <float>}`

- [ ] **Step 1: 写失败测试**

```python
# sdflow-devenv/tests/test_lock.py
import json, os, sys, time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_lock import write_lock, atomic_write, LOCK_REL, LockBusy


def _mkroot(tmp_path):
    (tmp_path / "openspec").mkdir()
    return tmp_path


def test_lock_file_format_is_contract(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        raw = (root / LOCK_REL).read_text()
        rec = json.loads(raw)
        assert set(rec) == {"owner", "pid", "ts"}
        assert isinstance(rec["owner"], str) and len(rec["owner"]) == 32
        assert rec["pid"] == os.getpid()
        assert isinstance(rec["ts"], float)


def test_lock_released_on_exit(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        assert (root / LOCK_REL).exists()
    assert not (root / LOCK_REL).exists()


def test_lock_released_on_exception(tmp_path):
    root = _mkroot(tmp_path)
    with pytest.raises(ValueError):
        with write_lock(root):
            raise ValueError("boom")
    assert not (root / LOCK_REL).exists()


def test_second_acquire_busy(tmp_path):
    root = _mkroot(tmp_path)
    with write_lock(root):
        with pytest.raises(LockBusy):
            with write_lock(root, retries=1, interval=0.01):
                pass


def test_does_not_delete_foreign_lock(tmp_path):
    """A 释放时 MUST NOT 删掉 B 的锁 —— owner 不符就不删。"""
    root = _mkroot(tmp_path)
    lp = root / LOCK_REL
    try:
        with write_lock(root):
            # 模拟：锁被别人抢走并改写（owner 变了）
            lp.write_text(json.dumps({"owner": "f" * 32, "pid": 99999, "ts": time.time()}))
    except Exception:
        pass
    # 别人的锁必须还在
    assert lp.exists()
    assert json.loads(lp.read_text())["owner"] == "f" * 32


def test_atomic_write_mode_755(tmp_path):
    p = tmp_path / "doctor.sh"
    atomic_write(p, "#!/bin/sh\necho ok\n", mode=0o755)
    assert p.read_text().startswith("#!/bin/sh")
    assert oct(p.stat().st_mode)[-3:] == "755"


def test_atomic_write_default_644(tmp_path):
    p = tmp_path / "notes.md"
    atomic_write(p, "hi\n")
    assert oct(p.stat().st_mode)[-3:] == "644"


def test_atomic_write_preserves_existing_mode(tmp_path):
    p = tmp_path / "existing.sh"
    p.write_text("old\n")
    os.chmod(p, 0o700)
    atomic_write(p, "new\n")          # 不传 mode ⇒ 保留原 mode
    assert p.read_text() == "new\n"
    assert oct(p.stat().st_mode)[-3:] == "700"


def test_atomic_write_leaves_no_tmp_on_success(tmp_path):
    p = tmp_path / "x.md"
    atomic_write(p, "x\n")
    leftovers = [f for f in tmp_path.iterdir() if ".tmp-" in f.name]
    assert leftovers == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-devenv/tests/test_lock.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devenv_lock'`

- [ ] **Step 3: 实现**

```python
# sdflow-devenv/scripts/devenv_lock.py
"""openspec/ 写域锁 + 原子写。

【三 skill 共用同一把锁】（spec: R-CONC）：devenv / sdflow-init / sdflow-architecture
写入面重叠（都注入 CLAUDE/AGENTS/README/INDEX）。各发一把锁 = 互斥性不可组合。
锁文件内容格式是【跨 skill 契约】—— 改它要同步改另外两个 skill + 契约测试。

【锁 MUST 短持有】：LOCK_STALE_SEC 是为亚秒级操作调的；验证可跑数分钟。
锁若跨验证持有 ⇒ 并发 session 把活锁判成残留锁 ⇒ 提示删锁 ⇒ 两 session 同写。
"""
import contextlib
import json
import os
import tempfile
import time
import uuid
from pathlib import Path

LOCK_REL = "openspec/.sdflow-write.lock"
LOCK_RETRIES = 20
LOCK_INTERVAL = 0.1
LOCK_STALE_SEC = 120


class LockBusy(Exception):
    """锁被占且未陈旧。"""


class LockStale(Exception):
    """锁疑似残留（mtime 超阈值）——提示人工删，不自动夺。"""


@contextlib.contextmanager
def write_lock(root, retries=LOCK_RETRIES, interval=LOCK_INTERVAL):
    root = Path(root)
    lockp = root / LOCK_REL
    lockp.parent.mkdir(parents=True, exist_ok=True)
    me = uuid.uuid4().hex
    rec = json.dumps({"owner": me, "pid": os.getpid(), "ts": time.time()})

    acquired = False
    for _ in range(retries):
        try:
            fd = os.open(str(lockp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(rec)
            acquired = True
            break
        except FileExistsError:
            try:
                age = time.time() - lockp.stat().st_mtime
            except OSError:
                age = 0.0
            if age > LOCK_STALE_SEC:
                raise LockStale(
                    f"锁 mtime 超 {LOCK_STALE_SEC}s，疑似残留；"
                    f"若确认无并发进程，删除 {lockp} 后重试"
                )
            time.sleep(interval)
    if not acquired:
        raise LockBusy(f"另一 sdflow 写操作进行中；若确认无并发进程，删除 {lockp} 后重试")

    try:
        yield
    finally:
        # MUST NOT 删他人的锁：释放前核对 owner
        with contextlib.suppress(Exception):
            cur = json.loads(lockp.read_text(encoding="utf-8"))
            if cur.get("owner") == me:
                lockp.unlink()


def atomic_write(path, text, mode=None):
    """mkstemp 唯一 tmp 名 + os.replace。

    mode=None 且文件已存在 ⇒ 保留原 mode（不擅自改用户的权限位）
    mode=None 且文件不存在 ⇒ 0o644
    显式传 mode ⇒ 用它（脚本类落地物传 0o755）
    """
    path = Path(path)
    d = path.parent
    d.mkdir(parents=True, exist_ok=True)

    if mode is None:
        try:
            mode = path.stat().st_mode & 0o777
        except OSError:
            mode = 0o644

    fd, tmpname = tempfile.mkstemp(dir=str(d), prefix=path.name + ".", suffix=".tmp-devenv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmpname, mode)      # mkstemp 默认 0600
        os.replace(tmpname, str(path))
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmpname)
        raise
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-devenv/tests/test_lock.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task2-lock" "写域锁（三 skill 共用锁名 + owner 核对）+ atomic_write(mode)（R-CONC）"
```

---

### Task 3: 两份 JSON schema + schema_version 消费行为

**Files:**
- Create: `sdflow-devenv/scripts/devenv_schema.py`
- Test: `sdflow-devenv/tests/test_schema.py`

**Interfaces:**
- Consumes: `devenv_paths.contain`（Task 1）· `devenv_lock.atomic_write`（Task 2）
- Produces:
  - `SCHEMA_VERSION = 1`
  - `LANES_REL = "openspec/architecture/.devenv-lanes.json"` · `STRATEGY_REL = "openspec/architecture/.devenv-strategy.json"`
  - `load_lanes(root) -> dict` / `save_lanes(root, data)` / `load_strategy(root) -> dict` / `save_strategy(root, data)`
  - `validate_lane(lane: dict) -> list[str]`（返回错误列表，空 = 合法）· `validate_strategy(data) -> list[str]`
  - `class SchemaTooNew(Exception)` / `class SchemaInvalid(Exception)`
  - `LAYERS = ("unit", "integration", "e2e")` · `SLOTS = ("how", "convention", "process", "tooling", "status")`
  - `plan_snapshot(lane) -> str` —— CAS 快照 digest：`sha256(json.dumps({status,executor,kind,method,source,smoke,fixtures,env,deps}, sort_keys=True, ensure_ascii=False))`

- [ ] **Step 1: 写失败测试**

```python
# sdflow-devenv/tests/test_schema.py
import json, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import devenv_schema as S


def _root(tmp_path):
    (tmp_path / "openspec" / "architecture").mkdir(parents=True)
    return tmp_path


def _lane(**kw):
    base = {
        "id": "mqtt-integration",
        "layer": "integration",
        "kind": "external-dep",
        "status": "scaffolded",
        "verification": {
            "method": "make integration",
            "executor": "script",
            "strength": "真穿过 broker；断言是否有效不由本方法保证",
        },
        "source": {"file": "Makefile", "kind": "make-target",
                   "selector": "integration"},          # 无 digest〔A21〕
        "smoke": "internal/smoke_test.go",
        "fixtures": [],
        "env": [],
        "deps": [{"name": "mosquitto", "kind": "host-service"}],
        "covers": [],
        "blocked_by": "本机无 mosquitto — brew install mosquitto 后 /sdflow-devenv continue",
    }
    base.update(kw)
    return base


def test_valid_lane_passes():
    assert S.validate_lane(_lane()) == []


def test_lane_rejects_owned_by():
    """owned_by 已删除（07 附录 A16：运行时派生的锚不存在）"""
    lane = _lane()
    lane["deps"][0]["owned_by"] = "skill"
    errs = S.validate_lane(lane)
    assert any("owned_by" in e for e in errs)


def test_lane_requires_method_and_strength():
    assert any("method" in e for e in S.validate_lane(_lane(verification={"executor": "script", "strength": "x"})))
    assert any("strength" in e for e in S.validate_lane(
        _lane(verification={"method": "m", "executor": "script"})))


def test_human_executor_requires_why_and_steps():
    lane = _lane(verification={"method": "人工烧板", "executor": "human", "strength": "s"})
    errs = S.validate_lane(lane)
    assert any("why_not_scriptable" in e for e in errs)
    assert any("human_steps" in e for e in errs)


def test_scaffolded_requires_blocked_by():
    assert any("blocked_by" in e for e in S.validate_lane(_lane(blocked_by="")))


def test_verified_forbids_blocked_by():
    """绿泳道挂着「本机无 X」= 文档在说谎"""
    lane = _lane(status="verified", blocked_by="本机无 mosquitto")
    lane["verification"]["evidence"] = {"at_commit": "abc", "exit": 0,
                                        "file_digests": {"Makefile": "d"},
                                        "attested_by": "script"}
    assert any("blocked_by" in e for e in S.validate_lane(lane))


def test_verified_requires_evidence():
    lane = _lane(status="verified", blocked_by="")
    assert any("evidence" in e for e in S.validate_lane(lane))


def test_bad_enum_rejected():
    assert S.validate_lane(_lane(layer="acceptance"))
    assert S.validate_lane(_lane(kind="bogus"))
    assert S.validate_lane(_lane(status="green"))


def test_schema_version_missing_fail_closed(tmp_path):
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps({"lanes": []}))
    with pytest.raises(S.SchemaInvalid):
        S.load_lanes(root)


def test_schema_version_future_fail_closed(tmp_path):
    """MUST NOT 尽力解析未来版本"""
    root = _root(tmp_path)
    (root / S.LANES_REL).write_text(json.dumps({"schema_version": 999, "lanes": []}))
    with pytest.raises(S.SchemaTooNew):
        S.load_lanes(root)


def test_roundtrip_no_pyyaml(tmp_path):
    root = _root(tmp_path)
    data = {"schema_version": 1, "lanes": [_lane()]}
    S.save_lanes(root, data)
    assert S.load_lanes(root) == data


def test_duplicate_lane_id_rejected(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(S.SchemaInvalid):
        S.save_lanes(root, {"schema_version": 1, "lanes": [_lane(), _lane()]})


# ---- strategy（三层框架）----

def _strategy(**layers):
    base = {
        "schema_version": 1,
        "layers": {
            "unit": {"how": "go test", "convention": "*_test.go 同包",
                     "process": "make unit，提交前", "tooling": "go 工具链",
                     "status": "implemented", "lane_ids": ["hermetic"]},
            "integration": {"how": "真 broker", "convention": "build tag realbroker",
                            "process": "make integration", "tooling": "mosquitto",
                            "status": "manual",
                            "why_not_scriptable": "依赖启停内嵌在 recipe 字面文本，无法插桩",
                            "human_steps": "1. brew services start mosquitto 2. make integration 3. 看到 PASS"},
            "e2e": {"status": "not-applicable",
                    "reason": "本项目是纯库，无可执行入口",
                    "consequence": "集成后的真实使用路径无人验证"},
        },
        "known_blind_spots": [],
    }
    base["layers"].update(layers)
    return base


def test_valid_strategy_passes():
    assert S.validate_strategy(_strategy()) == []


def test_missing_layer_fail_closed():
    st = _strategy()
    del st["layers"]["e2e"]
    assert any("e2e" in e for e in S.validate_strategy(st))


def test_implemented_requires_lane_ids():
    st = _strategy(unit={"how": "x", "convention": "x", "process": "x",
                         "tooling": "x", "status": "implemented"})
    assert any("lane_ids" in e for e in S.validate_strategy(st))


def test_not_applicable_requires_consequence():
    """不写后果，「不适用」就是不需要负责的逃生舱"""
    st = _strategy(e2e={"status": "not-applicable", "reason": "纯库"})
    assert any("consequence" in e for e in S.validate_strategy(st))


def test_not_applicable_exempts_four_slots():
    """MUST 豁免 ①-④ —— 否则是逼模型为「不做这件事」编造废话（填表游戏）"""
    st = _strategy(e2e={"status": "not-applicable", "reason": "纯库",
                        "consequence": "集成路径无人验证"})
    assert S.validate_strategy(st) == []


def test_manual_requires_why_and_steps():
    st = _strategy(integration={"how": "x", "convention": "x", "process": "x",
                                "tooling": "x", "status": "manual"})
    errs = S.validate_strategy(st)
    assert any("why_not_scriptable" in e for e in errs)
    assert any("human_steps" in e for e in errs)


def test_placeholder_consequence_rejected():
    for junk in ("无", "没有", "N/A", "TODO", "待定", "  "):
        st = _strategy(e2e={"status": "not-applicable", "reason": "纯库", "consequence": junk})
        assert any("consequence" in e for e in S.validate_strategy(st)), junk


def test_implemented_layer_missing_slots_fail():
    st = _strategy(unit={"status": "implemented", "lane_ids": ["hermetic"]})
    errs = S.validate_strategy(st)
    assert any("how" in e for e in errs)


# ---- CAS 快照 ----

def test_plan_snapshot_covers_executor_and_kind():
    """长跑期间 lane 从 script/pure 改成 human/hardware，只比 status 的 CAS 挡不住"""
    a = _lane()
    b = _lane()
    b["verification"] = dict(b["verification"], executor="human",
                             why_not_scriptable="x", human_steps="y")
    assert S.plan_snapshot(a) != S.plan_snapshot(b)

    c = _lane(kind="hardware")
    assert S.plan_snapshot(a) != S.plan_snapshot(c)


def test_plan_snapshot_stable_under_key_order():
    a = _lane()
    b = {k: a[k] for k in reversed(list(a))}
    assert S.plan_snapshot(a) == S.plan_snapshot(b)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-devenv/tests/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devenv_schema'`

- [ ] **Step 3: 实现**

```python
# sdflow-devenv/scripts/devenv_schema.py
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


# ---------- lanes ----------

def validate_lane(lane):
    errs = []
    if not lane.get("id"):
        errs.append("lane.id 缺失")
    if lane.get("layer") not in LAYERS:
        errs.append(f"lane.layer 非法（须 ∈ {LAYERS}）: {lane.get('layer')!r}")
    if lane.get("kind") not in LANE_KINDS:
        errs.append(f"lane.kind 非法（须 ∈ {LANE_KINDS}）: {lane.get('kind')!r}")
    status = lane.get("status")
    if status not in STATUSES:
        errs.append(f"lane.status 非法（须 ∈ {STATUSES}）: {status!r}")

    v = lane.get("verification") or {}
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

    blocked = (lane.get("blocked_by") or "").strip()
    if status == "scaffolded" and not blocked:
        errs.append("scaffolded MUST 带非空 blocked_by")
    if status == "scaffolded" and blocked.lower() in PLACEHOLDERS:
        errs.append(f"blocked_by 敷衍（{blocked!r}）—— MUST 含可辨认的修复指引")
    if status == "verified":
        if blocked:
            errs.append("verified 泳道 MUST NOT 残留 blocked_by（绿泳道挂着「本机无 X」= 文档在说谎）")
        ev = v.get("evidence") or {}
        # A21：file_digests + method_at_verify 取代 method_digest
        for k in ("at_commit", "file_digests", "method_at_verify", "attested_by"):
            if not ev.get(k):
                errs.append(f"verified MUST 有 evidence.{k}")
        fd = ev.get("file_digests")
        if fd is not None and not isinstance(fd, dict):
            errs.append("evidence.file_digests MUST 是 {rel_path: sha256} 映射")
        # A21 面治补口：method 字符串本身也要有时效锚（file_digests 只认文件）
        if ev.get("method_at_verify") and ev["method_at_verify"] != v.get("method"):
            errs.append(
                f"验证方法已改动（{ev['method_at_verify']!r} → {v.get('method')!r}），需重验"
            )

    for d in lane.get("deps") or []:
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
    """
    v = lane.get("verification") or {}
    snap = {k: lane.get(k) for k in SNAPSHOT_KEYS}
    snap.update({k: v.get(k) for k in SNAPSHOT_VERIF_KEYS})
    blob = json.dumps(snap, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------- strategy（测试三层框架）----------

def validate_strategy(data):
    errs = []
    layers = data.get("layers") or {}
    for name in LAYERS:
        L = layers.get(name)
        if not L:
            errs.append(f"三层框架缺 {name} 层 —— 一层都不许留白")
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

        for slot in ("how", "convention", "process", "tooling"):
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
    data = json.loads(p.read_text(encoding="utf-8"))
    ver = data.get("schema_version")
    if ver is None:
        raise SchemaInvalid(f"{rel} 缺 schema_version —— fail-closed")
    if not isinstance(ver, int):
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
        errs = []
        ids = [l.get("id") for l in d.get("lanes") or []]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            errs.append(f"lane id 重复: {sorted(dupes)}")
        for lane in d.get("lanes") or []:
            errs += [f"[{lane.get('id')}] {e}" for e in validate_lane(lane)]
        return errs
    _save(root, LANES_REL, data, _v)


def load_strategy(root):
    return _load(root, STRATEGY_REL)


def save_strategy(root, data):
    _save(root, STRATEGY_REL, data, validate_strategy)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-devenv/tests/test_schema.py -v`
Expected: 21 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task3-schema" "两份 JSON schema：lanes（无 owned_by）+ strategy（三层五槽，not-applicable 豁免①-④）+ schema_version fail-closed + CAS 快照覆盖 executor/kind（R-DATA/R-STRAT）"
```

---

### Task 4: 出处锚 —— `file_digests`（原始字节，零规范化，**零 make 知识**）

> **⚠️ 本 Task 在 round-4 被整体重写（`07` 附录 A21）。前一版要求「digest 按文件类型分治 + 按 selector 用 parser 重定位 make target 提取 recipe」——那条路已被否决。**
>
> **前一版的下场（务必读）**：三轮补丁螺旋，`devenv_digest.py` 261→562 行、`test_digest.py` 304→753 行，每一轮 review 都挖出一个新的 GNU make 语法角落（内联 `;` recipe → `ifeq` 块 → 行首注释 → `define` 块 → 双冒号 → 一行多 target → target-specific 变量）。最终留下 **7 个「Makefile 语法不支持」的 fail-closed 罢工分支**。
>
> **为什么这是致命的**：核心承诺是「**不管什么项目**，都能给用户一份三层测试与验证的框架」。而 `ifeq`、双冒号、一行多 target 在真实 Makefile 里**常见且合理**。**每一个罢工分支 = 一类项目被拒之门外 = 对核心承诺的一次背叛。** 为了防一个 §0.0 已宣告不存在的攻击者（"操作者偷改 recipe 还不重跑"）而写的东西，最终攻击的是目标本身。
>
> **无界语法面上，补丁循环不会自己收敛——这本身就是「该删掉它」的信号。**

**本 Task 现在极其简单。如果你写出了超过 ~60 行的 `devenv_digest.py`，你走错路了，停下来重读上面。**

- Files:
  - Create: `sdflow-devenv/scripts/devenv_digest.py`
  - Test: `sdflow-devenv/tests/test_digest.py`

- [ ] **Step 1: 写测试（TDD）**

**API（全部：3 个函数，零 make 知识）**：

```
file_digest(root, rel) -> str
    sha256(文件原始字节)。经 contain() 校验路径。所有文件类型一视同仁，零规范化。

lane_file_digests(root, lane) -> dict[str, str]
    {rel_path: sha256} —— 覆盖 source.file(非 "-") + smoke + fixtures[]。
    这就是 evidence.file_digests 的内容。

stale_files(root, lane) -> list[str]
    对比 lane.verification.evidence.file_digests 与当前磁盘，返回失配的文件列表（排序）。
    空列表 = 未失配。lint 用它报「验证证据已过期：<file> 已改动，请重跑」。
```

> **没有 `find_make_target`。没有 `digest_make_recipe`。没有 `method_digest`。没有 `normalize()`。**
> **没有任何 make 语法知识。** 这个模块不知道 Makefile 是什么，它只知道字节。

```python
# sdflow-devenv/tests/test_digest.py
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from devenv_digest import file_digest, lane_file_digests, stale_files
from devenv_paths import PathEscape


# ── 复杂 Makefile 语料：A21 的核心回归守卫 ──────────────────────────
# 前一版的 parser 在这份语料上有 7 种罢工姿势。现在它必须【全部正常工作】。
COMPLEX_MAKEFILE = """\
SHELL := /bin/bash
MQTT_PORT ?= 1883

ifeq ($(CI),true)
integration: deps           # ← ifeq 包裹的 target（前一版：静默截断 → 假绿）
\tgo test -tags=integration ./...
else
integration: deps
\tMQTT_PORT=$(MQTT_PORT) go test -tags=integration ./...
endif

lint vet:: fmt              # ← 一行多 target + 双冒号（前一版：MakefileUnsupported）
\tgo vet ./...

integration: EXTRA := -v    # ← target-specific 变量（前一版：误判为重复定义）

define run_smoke            # ← define 块（前一版：吞掉后续 target）
\t@echo running
endef

deps: ; @echo deps          # ← 内联 ; recipe（前一版：算出空 digest → 假绿）

long: \\
\tdeps                      # ← 续行（前一版：截断）
\t@echo long
"""


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _lane(**kw):
    lane = {
        "id": "integration",
        "source": {"file": "Makefile", "kind": "make-target", "selector": "integration"},
        "smoke": "smoke_test.go",
        "fixtures": [],
        "verification": {"evidence": {}},
    }
    lane.update(kw)
    return lane


# ── file_digest：原始字节，零规范化 ────────────────────────────────

def test_file_digest_is_raw_bytes(tmp_path):
    (tmp_path / "Makefile").write_bytes(COMPLEX_MAKEFILE.encode())
    assert file_digest(tmp_path, "Makefile") == _sha(COMPLEX_MAKEFILE.encode())


def test_file_digest_no_normalization_at_all(tmp_path):
    """A21 核心：所有类型一视同仁，零规范化。
    这一条同时保证了旧「分治」规则想保证的东西（YAML 缩进即语义），
    且【在结构上不可能踩错】—— 因为根本不存在 normalize()。"""
    p = tmp_path / "compose.yml"
    p.write_text("services:\n  broker:\n    image: eclipse-mosquitto\n")
    d1 = file_digest(tmp_path, "compose.yml")
    p.write_text("services:\n    broker:\n        image: eclipse-mosquitto\n")  # 缩进变 = 语义变
    d2 = file_digest(tmp_path, "compose.yml")
    assert d1 != d2, "YAML 缩进变化必须被捕获"


def test_file_digest_tab_vs_spaces_differ(tmp_path):
    """tab 有语法意义。原始字节天然区分它 —— 无需任何「保留 tab」的特殊规则。"""
    p = tmp_path / "Makefile"
    p.write_text("t:\n\tgo test\n")
    d_tab = file_digest(tmp_path, "Makefile")
    p.write_text("t:\n    go test\n")
    assert d_tab != file_digest(tmp_path, "Makefile")


def test_file_digest_comment_change_detected(tmp_path):
    """改注释也算改动 —— 允许多报，刻意如此（防漏宁可多报）。"""
    p = tmp_path / "Makefile"
    p.write_text("t:\n\tgo test  # fast\n")
    d1 = file_digest(tmp_path, "Makefile")
    p.write_text("t:\n\tgo test  # slow\n")
    assert d1 != file_digest(tmp_path, "Makefile")


def test_file_digest_goes_through_containment(tmp_path):
    with pytest.raises(PathEscape):
        file_digest(tmp_path, "../../etc/passwd")


# ── ⭐ A21 回归守卫：复杂 Makefile MUST NOT 罢工 ────────────────────

def test_complex_makefile_never_raises(tmp_path):
    """核心承诺「不管什么项目」的守卫。
    前一版的 parser 在这份语料上有 7 种 MakefileUnsupported 罢工姿势。
    现在：digest 是整文件字节 —— 语法再复杂也【不可能】罢工。"""
    (tmp_path / "Makefile").write_bytes(COMPLEX_MAKEFILE.encode())
    (tmp_path / "smoke_test.go").write_text("package x\n")
    d = lane_file_digests(tmp_path, _lane())          # MUST NOT raise
    assert d["Makefile"] == _sha(COMPLEX_MAKEFILE.encode())


def test_no_make_parsing_symbols_exist():
    """A21 契约测试：这个模块【MUST 零 make 知识】。
    若未来有人再把 parser 加回来，这条当场红。"""
    import devenv_digest as m
    banned = ("find_make_target", "digest_make_recipe", "method_digest",
              "normalize", "MakefileUnsupported", "_COND_RE", "_DEFINE_RE")
    for name in banned:
        assert not hasattr(m, name), (
            f"{name} 不该存在 —— A21：devenv_digest MUST 零 make 知识。"
            f"「target 能不能跑」由 verify-lane 真跑一遍让 make 自己判。"
        )
    src = Path(m.__file__).read_text(encoding="utf-8")
    assert "recipe" not in src.lower(), "MUST NOT 提取/理解 recipe"


# ── lane_file_digests：覆盖面 ─────────────────────────────────────

def test_lane_file_digests_covers_source_smoke_fixtures(tmp_path):
    (tmp_path / "Makefile").write_text("integration:\n\tgo test\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    (tmp_path / "fixture.json").write_text("{}\n")
    d = lane_file_digests(tmp_path, _lane(fixtures=["fixture.json"]))
    assert set(d) == {"Makefile", "smoke_test.go", "fixture.json"}


def test_lane_file_digests_skips_toolchain_source(tmp_path):
    """source.file == "-"（toolchain 类，如 `go test ./...`）→ 不进 digest。"""
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane(source={"file": "-", "kind": "toolchain", "selector": "go test"})
    assert set(lane_file_digests(tmp_path, lane)) == {"smoke_test.go"}


def test_lane_file_digests_paths_are_contained(tmp_path):
    lane = _lane(fixtures=["../../etc/passwd"])
    with pytest.raises(PathEscape):
        lane_file_digests(tmp_path, lane)


# ── stale_files：失配检测（lint 的判据）───────────────────────────

def test_stale_files_empty_when_unchanged(tmp_path):
    (tmp_path / "Makefile").write_text("integration:\n\tgo test\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(tmp_path, lane)
    assert stale_files(tmp_path, lane) == []


def test_stale_files_detects_changed_smoke(tmp_path):
    (tmp_path / "Makefile").write_text("integration:\n\tgo test\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(tmp_path, lane)
    (tmp_path / "smoke_test.go").write_text("package x\nfunc TestFoo(t *testing.T) {}\n")
    assert stale_files(tmp_path, lane) == ["smoke_test.go"]


def test_stale_files_line_shift_IS_detected(tmp_path):
    """「行还在、内容变了」+ 行号位移 —— 整文件字节，两者都抓。
    对比旧「行号锚」：它对任何 ≥N 行的文件恒真 = 设计好的假绿。"""
    p = tmp_path / "Makefile"
    p.write_text("integration:\n\tgo test\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(tmp_path, lane)
    p.write_text("VAR := 1\nVAR2 := 2\nVAR3 := 3\nintegration:\n\tgo test\n")  # 顶部插三行
    assert stale_files(tmp_path, lane) == ["Makefile"]


def test_stale_files_allows_overreport_on_unrelated_target(tmp_path):
    """【刻意的多报】改了 Makefile 里【别的】target 也会报。
    多报代价 = 重跑一次 smoke；消除多报代价 = 300 行 make 解析器。
    方向反了 —— 防漏宁可多报〔A21〕。"""
    p = tmp_path / "Makefile"
    p.write_text("integration:\n\tgo test\n\nlint:\n\tgo vet\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(tmp_path, lane)
    p.write_text("integration:\n\tgo test\n\nlint:\n\tgo vet ./...\n")   # 只改了 lint
    assert stale_files(tmp_path, lane) == ["Makefile"], "多报是刻意的，不是 bug"


def test_stale_files_reports_deleted_file(tmp_path):
    """文件被删 —— MUST 报失配，MUST NOT 抛异常（lint 要能继续跑完其他检查）。"""
    (tmp_path / "Makefile").write_text("integration:\n\tgo test\n")
    (tmp_path / "smoke_test.go").write_text("package x\n")
    lane = _lane()
    lane["verification"]["evidence"]["file_digests"] = lane_file_digests(tmp_path, lane)
    (tmp_path / "smoke_test.go").unlink()
    assert stale_files(tmp_path, lane) == ["smoke_test.go"]


def test_stale_files_no_evidence_means_no_digests(tmp_path):
    """planned 泳道（还没验证过）—— 无 file_digests ⇒ 无从比对 ⇒ 空。
    spec：planned 不核验命令出处。"""
    assert stale_files(tmp_path, _lane()) == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest sdflow-devenv/tests/test_digest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'devenv_digest'`

- [ ] **Step 3: 实现**

```python
# sdflow-devenv/scripts/devenv_digest.py
"""出处锚与验证证据的时效锚。

【A21 · 本模块 MUST 零 make 知识】

digest 一律 = sha256(文件原始字节)，所有文件类型一视同仁，零规范化。

MUST NOT 在这里加：
  - GNU make 解析（提取 recipe body / 按 selector 重定位 target）
  - 「target 存在性」正则
  - 任何 normalize()

【为什么】GNU make 的语法面无界（ifeq / define / 双冒号 / 模式规则 / 续行 /
内联 ; / target-specific 变量 …）。手搓解析器必然带一堆「语法不支持」的罢工
分支，而它罢工一次就击穿本 skill 的核心承诺 ——「不管什么项目，都能给用户一份
三层测试与验证的框架」。前一版就是这么长到 562 行、留下 7 个罢工分支的。

「target 存在且能跑」谁来保证？
  - selector 拼错 / target 不存在
        → verify-lane 真 fork 跑 `make <selector>`
        → make 报 "No rule to make target" → exit != 0
        → 泳道进不了 verified。
        【make 自己解释自己的语法 —— 100% 覆盖，零解析器，零维护。】
  - target 后来被删 / 改名
        → Makefile 字节变了 → file_digests 失配 → lint 报「已改动，请重跑」。

一般化规则：机械层想知道「某个 make/shell/语言构造是什么意思」，正解是让那个
工具自己回答（真跑一遍 / make -n），MUST NOT 手搓解析器去猜。本 skill 的核心
机制恰好就是「尽可能跑一遍确认」—— 跑一遍，就是最强的解析器。

【时效锚的诚实边界】file_digests 覆盖 source.file + smoke + 显式声明的
fixtures[]，【不覆盖被测实现】（覆盖它需要跨语言 import 图静态分析，零依赖做
不到 —— A19）。故 verified 是 `verified-at <sha>`：一次历史执行的记录，不是
「当前状态的绿灯」。业务代码一改，那个绿灯就在说谎。

【失配 = 提醒，不是抓贼】允许多报：改了 Makefile 里【别的】target 也会触发。
刻意如此 —— 多报的代价是重跑一次 smoke，消除多报的代价是 300 行解析器。
防漏宁可多报。
"""

import hashlib

from devenv_paths import contain

__all__ = ["file_digest", "lane_file_digests", "stale_files"]


def file_digest(root, rel):
    """sha256(文件原始字节)。零规范化 —— 所有文件类型一视同仁。

    零规范化不只是「够用」，它比按类型分治【严格更强且不可能踩错】：
    分治规则（Makefile 剥空白保 tab / YAML 原始字节）之所以存在，纯粹是因为要
    提取 recipe body 才会引入缩进噪声。不提取 recipe ⇒ 无噪声 ⇒ 无需 normalize
    ⇒「一个通用 normalize() 把两份缩进不同、语义不同的 YAML 算出同一 digest」
    这个假绿【在结构上不可能发生】。
    """
    return hashlib.sha256(contain(root, rel).read_bytes()).hexdigest()


def _tracked_paths(lane):
    """本泳道时效锚覆盖的文件清单（相对路径，去重排序）。"""
    paths = set()

    source = lane.get("source") or {}
    f = source.get("file")
    if f and f != "-":              # "-" = toolchain 类（如 `go test ./...`），无出处文件
        paths.add(f)

    smoke = lane.get("smoke")
    if smoke:
        paths.add(smoke)

    paths.update(lane.get("fixtures") or [])
    return sorted(paths)


def lane_file_digests(root, lane):
    """{rel_path: sha256} —— 写进 evidence.file_digests 的内容。

    只在【执行者本人】产出证据时调用（verify-lane / confirm-lane）。
    """
    return {rel: file_digest(root, rel) for rel in _tracked_paths(lane)}


def stale_files(root, lane):
    """返回失配的文件清单（排序）。空 = 未失配。

    lint 用它报「验证证据已过期：<file> 已改动，请重跑」。
    文件被删 → 算失配（MUST NOT 抛异常，lint 要能跑完其余检查）。
    """
    recorded = ((lane.get("verification") or {}).get("evidence") or {}).get("file_digests") or {}
    if not recorded:
        return []                   # planned 泳道：没验证过，无从比对（spec：planned 不核验出处）

    stale = []
    for rel, want in sorted(recorded.items()):
        try:
            got = file_digest(root, rel)
        except FileNotFoundError:
            stale.append(rel)       # 被删了 = 失配
            continue
        if got != want:
            stale.append(rel)
    return stale
```

> **注意 `contain()` 抛 `PathEscape` 时不吞**——路径逃逸是安全问题，MUST 冒泡到调用方（区别于 `FileNotFoundError`，那是正常的「文件没了」）。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest sdflow-devenv/tests/test_digest.py -v`
Expected: 15 passed

**特别确认这两条通过——它们是 A21 的红线**：
- `test_complex_makefile_never_raises` —— 核心承诺「不管什么项目」的守卫
- `test_no_make_parsing_symbols_exist` —— 防止 parser 从后门爬回来

- [ ] **Step 5: 清理旧实现（若从 round-3 版本迁移）**

前一版的 `devenv_digest.py`（562 行）与 `test_digest.py`（753 行）**整体作废**。
本 Task 的产物应是 **~60 行脚本 + ~180 行测试**。**若你手上还留着 `find_make_target` / `digest_make_recipe` / `method_digest` / `MakefileUnsupported`，删掉它们**——`test_no_make_parsing_symbols_exist` 会替你把关。

- [ ] **Step 6: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task4-digest" "fix(devenv)!: A21 —— 删掉手搓 GNU make 解析器（562→~60 行）。digest 一律原始字节零规范化；「target 能不能跑」由 verify-lane 真跑一遍让 make 自己判。7 个「语法不支持」罢工分支归零 —— 它们每一个都是对「不管什么项目」这条核心承诺的背叛（R-DATA）"
```

---

### Task 5: 跨 skill 锁契约测试（先立契约，再改另外两个 skill）

> **为什么现在做**：Task 17/18 要改 `init.py` 和 `sad_scaffold.py` 的锁。**先把契约测试写出来**，那两个 Task 才有客观判据（否则"三 skill 共用一把锁"只是一句口号）。

**Files:**
- Create: `sdflow-devenv/tests/test_lock_contract.py`

**Interfaces:**
- Consumes: `devenv_lock.LOCK_REL`（Task 2）
- 契约：三个 skill 的锁实现 MUST 使用**同一个锁文件路径**，且**锁文件内容为单行 JSON 含 `owner`/`pid`/`ts` 三键**

- [ ] **Step 1: 写测试（此时 init/sad_scaffold 尚未改，故预期 FAIL —— 这正是 Task 17/18 的验收判据）**

```python
# sdflow-devenv/tests/test_lock_contract.py
"""跨 skill 锁协议契约 —— 三个 skill 无法互相 import（各自独立目录、symlink 安装），
故用【契约测试】钉死格式一致（照本仓 test_producer_parser_contract 先例）。

改锁协议 MUST 同步改三处 + 本测试。
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sdflow-devenv" / "scripts"))
from devenv_lock import LOCK_REL

CANONICAL_LOCK = "openspec/.sdflow-write.lock"

SKILL_SCRIPTS = {
    "devenv": REPO / "sdflow-devenv" / "scripts" / "devenv_lock.py",
    "init": REPO / "sdflow-init" / "scripts" / "init.py",
    "architecture": REPO / "sdflow-architecture" / "scripts" / "sad_scaffold.py",
}


def test_devenv_uses_canonical_lock_name():
    assert LOCK_REL == CANONICAL_LOCK


@pytest.mark.parametrize("skill", sorted(SKILL_SCRIPTS))
def test_all_three_skills_reference_canonical_lock(skill):
    """三 skill MUST 共用同一把锁 —— 各发一把锁 = 互斥性不可组合。

    devenv 注入 CLAUDE.md 时，另一 session 跑 /sdflow-init update 覆写同一文件
    ⇒ devenv 的整块注入被静默吃掉。
    """
    src = SKILL_SCRIPTS[skill].read_text(encoding="utf-8")
    assert CANONICAL_LOCK in src, (
        f"{skill} 未使用共用锁 {CANONICAL_LOCK}；"
        f"若它仍用自己的锁名（如 .sad-scaffold.lock），互斥性不可组合"
    )


@pytest.mark.parametrize("skill", sorted(SKILL_SCRIPTS))
def test_all_three_skills_record_owner(skill):
    """锁文件 MUST 记 owner —— 释放前核对，MUST NOT 删他人的锁。

    注：sad_scaffold 现在【根本没写入过 owner 信息】（_acquire_lock 只 os.open 空文件），
    所以这是【从零加机制】，不是「补核对」。
    """
    src = SKILL_SCRIPTS[skill].read_text(encoding="utf-8")
    assert re.search(r'["\']owner["\']', src), f"{skill} 的锁未记 owner"
    assert "uuid" in src, f"{skill} 的锁未生成 uuid owner"


@pytest.mark.parametrize("skill", sorted(SKILL_SCRIPTS))
def test_all_three_skills_verify_owner_before_release(skill):
    src = SKILL_SCRIPTS[skill].read_text(encoding="utf-8")
    # 释放路径附近必须出现 owner 比对（宽松匹配：不同实现写法不同）
    assert re.search(r'owner.*==|==.*owner|get\(["\']owner["\']\)', src), \
        f"{skill} 释放锁前未核对 owner —— 可能删掉他人的锁"


def test_no_stale_private_locks_remain():
    """确认旧的私有锁名已被清除（sad_scaffold 的 .sad-scaffold.lock）"""
    src = SKILL_SCRIPTS["architecture"].read_text(encoding="utf-8")
    assert ".sad-scaffold.lock" not in src, \
        "sad_scaffold 仍持有私有锁名 —— Task 18 未完成"
```

- [ ] **Step 2: 跑测试，确认 devenv 通过、另两个 skill FAIL（这是预期的）**

Run: `pytest sdflow-devenv/tests/test_lock_contract.py -v`
Expected:
- `test_devenv_uses_canonical_lock_name` PASS
- `test_all_three_skills_*[init]` / `[architecture]` **FAIL**（它们还没改）
- `test_no_stale_private_locks_remain` **FAIL**

**这些 FAIL 是 Task 17/18 的验收判据，此时 MUST NOT 去改另外两个 skill 来"修绿"** —— 它们有自己的 Task。用 `-k devenv` 确认本 Task 交付物本身是绿的：

Run: `pytest sdflow-devenv/tests/test_lock_contract.py -v -k "devenv or canonical"`
Expected: 1 passed

- [ ] **Step 3: 标记预期失败（让 Task 1-16 期间的全量 pytest 不被这三条卡住）**

在 `test_lock_contract.py` 顶部加：

```python
# Task 17/18 完成前，init / architecture 两条契约必然 FAIL —— 它们是那两个 Task 的验收判据。
# 完成 Task 18 后【MUST 删掉这个 xfail 标记】，让契约真正生效。
pytestmark = pytest.mark.xfail(
    reason="Task 17/18（init.py 补锁 · sad_scaffold 迁锁）尚未完成；完成后 MUST 删除此标记",
    strict=False,
)
```

- [ ] **Step 4: 跑全量确认不阻塞**

Run: `pytest sdflow-devenv/tests/ -v`
Expected: 全部 pass 或 xfail，**无 FAIL**

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task5-lock-contract" "跨 skill 锁协议契约测试（三 skill 共用锁名 + owner 记录/核对）；init/architecture 暂 xfail，为 task17/18 的验收判据（R-CONC）"
```

---

### Task 6: `devenv_scaffold.py` CLI 骨架 —— init / set-lane / log（含 CAS）

**Files:**
- Create: `sdflow-devenv/scripts/devenv_scaffold.py` · `sdflow-devenv/references/exit-codes.md`
- Test: `sdflow-devenv/tests/test_scaffold.py`

**Interfaces:**
- Consumes: `devenv_paths` · `devenv_lock` · `devenv_schema`（Task 1–3）
- Produces: CLI `python3 devenv_scaffold.py <subcmd> --root <path> ...`
- **退出码表（一码一义，写进 `references/exit-codes.md`，实现期照抄不留现场发明空间）**：

| code | 含义 | 调用方该做什么 |
|---|---|---|
| 0 | 成功 | — |
| 2 | 坏输入 / schema 非法 / 路径逃逸 | 停下报错 |
| 3 | 无 `openspec/` 布局 | 转述「先跑 /sdflow-init」 |
| 4 | `environments.md` 已存在（需 `--on-exists continue\|replan`） | 问操作者 |
| 5 | **非法调用**（`set-lane --status verified`） | **停下报 bug** |
| 6 | **CAS 冲突**（lane 在长跑期间被改） | **重读后重跑验证** |
| 7 | **锁被占** | **退避重试** |
| 8 | schema_version 过新 | 提示升级 skill |
| 9 | lane 不存在 | 停下报错 |

> **6 与 7 MUST NOT 共用同一码** —— 前者应重读重跑，后者应退避重试，**处置完全相反**。

- [ ] **Step 1: 写失败测试（要点）**

```python
# sdflow-devenv/tests/test_scaffold.py —— 核心断言
def test_init_no_openspec_exit3(tmp_path):
    assert run(["init", "--root", str(tmp_path)]).returncode == 3

def test_init_sad_missing_degrades_loudly(tmp_path):
    """MUST NOT 佯装有 SAD —— 响亮告警 + frontmatter 留痕 sad: missing"""
    mkrepo(tmp_path)                       # 有 openspec/ 无 sad.md
    r = run(["init", "--root", str(tmp_path)])
    assert r.returncode == 0
    assert "sad" in r.stderr.lower() and "missing" in r.stderr.lower()
    assert "sad: missing" in (tmp_path / "openspec/architecture/environments.md").read_text()

def test_init_exists_exit4(tmp_path):
    mkrepo_with_env(tmp_path)
    assert run(["init", "--root", str(tmp_path)]).returncode == 4

def test_set_lane_verified_refused_exit5(tmp_path):
    """verified MUST NOT 由模型传入 —— set-lane 只管 planned/scaffolded"""
    r = run(["set-lane", "--root", str(tmp_path), "--id", "x", "--status", "verified"])
    assert r.returncode == 5
    assert "verify-lane" in r.stderr and "confirm-lane" in r.stderr

def test_set_lane_scaffolded_requires_blocked_by(tmp_path):
    assert run(["set-lane", ..., "--status", "scaffolded"]).returncode == 2

def test_cas_conflict_exit6(tmp_path):
    """快照覆盖 executor/kind —— 只比 status 挡不住"""
    lane = seed_lane(tmp_path, executor="script", kind="pure")
    snap = plan_snapshot(lane)
    mutate_lane(tmp_path, executor="human")     # 另一 session 改了 executor，status 未变
    r = run(["set-lane", ..., "--expect-snapshot", snap])
    assert r.returncode == 6

def test_log_rejects_newline(tmp_path):
    assert run(["log", "--root", str(tmp_path), "--line", "a\nb"]).returncode == 2

def test_only_patches_one_lane(tmp_path):
    """回写 MUST 只 patch 那一条 lane，MUST NOT 用内存快照覆写整份"""
```

- [ ] **Step 2: 跑测试确认失败** — `pytest sdflow-devenv/tests/test_scaffold.py -v`

- [ ] **Step 3: 实现要点**

```python
# devenv_scaffold.py —— 关键片段
EXIT_OK, EXIT_BADINPUT, EXIT_NO_OPENSPEC, EXIT_EXISTS = 0, 2, 3, 4
EXIT_ILLEGAL, EXIT_CAS, EXIT_LOCKED, EXIT_TOO_NEW, EXIT_NO_LANE = 5, 6, 7, 8, 9

def cmd_set_lane(args):
    if args.status == "verified":
        die(EXIT_ILLEGAL,
            "verified 只能由 verify-lane（script 通道）或 confirm-lane（human 通道）产出。\n"
            "理由：若无脚本亲自执行，数据流只能是「模型跑 → 模型读 exit code → 模型调 set-lane」\n"
            "⇒ 脚本对「到底跑没跑」零独立证据 ⇒ 退化为「模型自称，脚本盖章」。")
    with write_lock(root):                       # 短持有：只包这次读-改-写
        data = load_lanes(root)
        lane = find_lane(data, args.id) or die(EXIT_NO_LANE, f"lane 不存在: {args.id}")
        if args.expect_snapshot and plan_snapshot(lane) != args.expect_snapshot:
            die(EXIT_CAS, "lane 的 verification plan 在此期间被改动（executor/kind/method/...）；"
                          "请重读后重跑验证")
        patch_one_lane(data, args.id, updates)   # 只 patch 这一条
        save_lanes(root, data)
```

`init` 的三模式分流：无 `openspec/` → exit 3 · `environments.md` 已存在 → exit 4（要 `--on-exists`）· 检出存量 Makefile/测试 → 提示归位模式 · `sad.md` 缺失 → **stderr 响亮告警 + `sad: missing` 留痕，继续**（MUST NOT fail-closed——会把没做过 SAD 的存量项目全挡在门外）。

- [ ] **Step 4: 跑测试确认通过** — Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task6-scaffold-cli" "scaffold CLI：init 三模式分流 · set-lane 拒 verified(exit5) · CAS 覆盖 verification plan(exit6) · 退出码表一码一义（R-PF/R-EXEC/R-CONC）"
```

---

### Task 7: `devenv_runner.py` —— 子进程执行（allowlist / 进程组 / 超时 / 孤儿如实报告）

**Files:**
- Create: `sdflow-devenv/scripts/devenv_runner.py` · `sdflow-devenv/references/env-allowlist.md`
- Test: `sdflow-devenv/tests/test_runner.py`

**Interfaces:**
- Produces: `run(cmd: str, root: Path, extra_env: list[str], timeout: int = 300) -> RunResult`
  `RunResult = namedtuple("RunResult", "exit_code output_tail timed_out orphan_warning duration")`

**⚠️ 两条设计红线：**
1. **最小环境 allowlist 是主护栏**（不是"事后打码"）——子进程**MUST NOT 继承 agent 的完整环境**。被执行的 recipe 或其下游脚本可把凭证**写进文件、发往网络**，**事后打码管不着这些**。
2. **孤儿资源如实告知，MUST NOT 假装能回收**——recipe 内部起的 Docker 容器**不属于子进程组**，杀进程树杀不到它。**没有 cleanup ledger**（那个机制的锚不存在：skill 不知道 recipe 内部创建了什么）。

- [ ] **Step 1: 写失败测试（要点）**

```python
def test_env_allowlist_excludes_secrets(tmp_path, monkeypatch):
    """子进程 MUST NOT 继承 agent 的完整环境"""
    monkeypatch.setenv("MY_SECRET_TOKEN", "s3cr3t")
    r = run("env", tmp_path, extra_env=[])
    assert "MY_SECRET_TOKEN" not in r.output_tail
    assert "s3cr3t" not in r.output_tail

def test_env_allowlist_includes_toolchain_basics(tmp_path):
    r = run("env", tmp_path, extra_env=[])
    for k in ("PATH", "HOME", "SHELL", "TMPDIR", "LANG"):
        assert k in r.output_tail

def test_lane_declared_env_passed_through(tmp_path, monkeypatch):
    monkeypatch.setenv("GOPROXY", "https://proxy.example")
    r = run("env", tmp_path, extra_env=["GOPROXY"])
    assert "https://proxy.example" in r.output_tail

def test_timeout_kills_process_tree(tmp_path):
    """子进程起孙进程，超时后【整棵树】都要死"""
    script = tmp_path / "spawn.sh"
    script.write_text("#!/bin/sh\nsleep 300 &\necho $! > child.pid\nsleep 300\n")
    script.chmod(0o755)
    r = run("./spawn.sh", tmp_path, extra_env=[], timeout=1)
    assert r.timed_out
    child_pid = int((tmp_path / "child.pid").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)          # 孙进程必须也死了

def test_timeout_reports_orphan_warning_honestly(tmp_path):
    """MUST NOT 声称已清理 —— recipe 内部起的容器杀不到"""
    r = run("sleep 300", tmp_path, extra_env=[], timeout=1)
    assert r.timed_out
    assert "孤儿资源" in r.orphan_warning
    assert "请检查" in r.orphan_warning
    assert "已清理" not in r.orphan_warning     # 绝不能撒谎

def test_output_truncated_and_masked(tmp_path):
    r = run("echo 'AMQP_URL=amqp://u:p@h'", tmp_path, extra_env=[])
    assert "p@h" not in r.output_tail          # best-effort 打码
```

- [ ] **Step 2: 确认失败**

- [ ] **Step 3: 实现要点**

```python
BASE_ALLOWLIST = ("PATH", "HOME", "SHELL", "TMPDIR", "LANG", "LC_ALL", "TERM", "USER")
SECRET_RE = re.compile(r'(?i)(token|secret|password|passwd|api[_-]?key|:\/\/[^:]+:)([^\s@"\']+)')

def run(cmd, root, extra_env, timeout=300):
    env = {k: os.environ[k] for k in BASE_ALLOWLIST if k in os.environ}
    for k in extra_env or []:                      # lane 显式声明的（无独立信号 ⇒ 过人门）
        if k in os.environ:
            env[k] = os.environ[k]

    if os.name != "posix":
        raise PlatformUnsupported(
            "非 POSIX 平台的进程树杀灭未经实测 —— 不做无证据的执行。该泳道请走 executor: human。"
        )   # ADR-11：MUST NOT 写一段从未在该平台执行过的代码并声称它能杀进程树

    proc = subprocess.Popen(cmd, shell=True, cwd=str(root), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, start_new_session=True)   # POSIX-only
    try:
        out, _ = proc.communicate(timeout=timeout)
        timed_out, orphan = False, ""
    except subprocess.TimeoutExpired:
        _kill_tree(proc.pid)                        # TERM 整组 → 宽限 → KILL 整组
        out, _ = proc.communicate()
        timed_out = True
        orphan = ("本次验证超时被中止。**可能留下孤儿资源**（recipe 内部起的容器/端口占用不属于"
                  "子进程组，skill 杀不到），**请检查**。")
    return RunResult(proc.returncode, _mask(_tail(out)), timed_out, orphan, ...)

def _kill_tree(pid):
    pgid = os.getpgid(pid)
    os.killpg(pgid, signal.SIGTERM)
    time.sleep(2)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGKILL)
```

`references/env-allowlist.md` 写按栈的推荐追加集（**标「实例，非规格」**）：Go → `GOPATH`/`GOCACHE`/`GOMODCACHE`/`GOPROXY`/`GOFLAGS` · Docker → `DOCKER_HOST`/`DOCKER_CONFIG` · 网络 → `SSL_CERT_FILE`/`HTTPS_PROXY`。

- [ ] **Step 4: 跑测试** — Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task7-runner" "runner：最小环境 allowlist(主护栏) + 独立进程组 + 超时杀进程树 + 孤儿资源如实告知(MUST NOT 假装能回收) + 非 POSIX refuse（R-BOUND）"
```

---

### Task 8: `verify-lane`（script 通道）+ `confirm-lane`（human 通道）

**Files:**
- Modify: `sdflow-devenv/scripts/devenv_scaffold.py`
- Test: `sdflow-devenv/tests/test_verify.py`

**Interfaces:**
- Consumes: `devenv_runner.run`（Task 7）· `devenv_digest.lane_file_digests`（Task 4）· `plan_snapshot`（Task 3）

**⚠️ 设计红线 1：`confirm-lane` MUST NOT 声称保证了执行者身份。**

**⚠️ 设计红线 2〔A21〕：`verify-lane` 是「target 存不存在、能不能跑」的唯一判官——因为它让 make 自己回答。**

> `selector` 拼错 / target 不存在 → `make <selector>` 报 `No rule to make target` → `exit≠0` → **泳道进不了 `verified`**，如实落 `scaffolded` + `blocked_by`。
> **MUST NOT** 在 verify 之前加一道「静态检查 target 是否存在」的正则——它在「找不到」方向没有确定性信号（`ifeq` 包裹 / `define` 内 / 一行多 target 都会漏判），加了只会**在复杂 Makefile 上误报罢工**，把 A21 杀掉的病请回来。**真跑一遍，就是最强的解析器。**

> 在 agent session 里，**模型是唯一的命令执行者**——人只在对话里回答「同意/否决」，从无「人亲自开终端敲命令」的通道。"模型 MUST NOT 代替操作者调用"这句话**按字面永远为假**。**且本就不必防**（总则：使用者就是那个人自己）。
> ⇒ **如实标 `attested_by: human`，渲染时与脚本验证的绿可区分。**

- [ ] **Step 1: 写失败测试（要点）**

```python
def test_verify_lane_forks_and_records_real_exit(tmp_path):
    """脚本【亲自 fork 执行】—— 不问「你跑过吗」"""
    seed_lane(tmp_path, method="exit 0", executor="script")
    r = run_cli(["verify-lane", "--root", str(tmp_path), "--id", "x"])
    lane = load_lane(tmp_path, "x")
    assert lane["status"] == "verified"
    ev = lane["verification"]["evidence"]
    assert ev["exit"] == 0
    assert ev["attested_by"] == "script"
    assert len(ev["at_commit"]) >= 7
    assert ev["file_digests"]                  # {rel: sha256}〔A21〕

def test_verify_lane_missing_make_target_stays_scaffolded(tmp_path):
    """⭐ A21：「target 不存在」由 make 自己抓 —— 不是靠静态解析。
    make 报 `No rule to make target` → exit≠0 → 进不了 verified。"""
    (tmp_path / "Makefile").write_text("integration:\n\t@true\n")
    seed_lane(tmp_path, method="make integraton", executor="script")   # 拼错
    run_cli(["verify-lane", "--root", str(tmp_path), "--id", "x"])
    lane = load_lane(tmp_path, "x")
    assert lane["status"] == "scaffolded"
    assert lane["blocked_by"]

def test_verify_lane_red_stays_scaffolded(tmp_path):
    seed_lane(tmp_path, method="exit 1", executor="script")
    run_cli(["verify-lane", ...])
    lane = load_lane(tmp_path, "x")
    assert lane["status"] == "scaffolded"
    assert lane["blocked_by"]                    # 必须写清卡在哪

def test_verify_lane_refuses_human_executor(tmp_path):
    seed_lane(tmp_path, executor="human")
    assert run_cli(["verify-lane", ...]).returncode == 5

def test_verify_lane_refuses_hardware(tmp_path):
    """kind: hardware ⇒ refuse ⇒ 走 human 通道（不是「无法 verified」）"""
    seed_lane(tmp_path, kind="hardware", executor="script")
    r = run_cli(["verify-lane", ...])
    assert r.returncode == 5
    assert "embedded-test-sop" in r.stderr

def test_confirm_lane_marks_human_attested(tmp_path):
    """MUST NOT 声称脚本保证了执行者身份"""
    seed_lane(tmp_path, executor="human", why="真硬件", steps="1.烧板 2.看灯")
    run_cli(["confirm-lane", "--root", str(tmp_path), "--id", "x",
             "--confirmed-what", "已烧板并观察到 LED 按预期闪烁"])
    lane = load_lane(tmp_path, "x")
    assert lane["status"] == "verified"
    ev = lane["verification"]["evidence"]
    assert ev["attested_by"] == "human"          # ← 如实标注
    assert ev["confirmed_what"] == "已烧板并观察到 LED 按预期闪烁"

def test_confirm_lane_refuses_script_executor(tmp_path):
    """script 通道的泳道必须真跑，不能走人工确认绕过"""
    seed_lane(tmp_path, executor="script")
    assert run_cli(["confirm-lane", ...]).returncode == 5

def test_cas_snapshot_taken_before_long_run(tmp_path):
    """长跑期间 lane 被改 executor ⇒ 回写必须被拒（exit 6）"""

def test_verified_clears_blocked_by(tmp_path):
    """绿泳道上挂着「本机无 mosquitto」= 文档在说谎"""
```

- [ ] **Step 2: 确认失败**

- [ ] **Step 3: 实现要点**

```python
def cmd_verify_lane(args):
    with write_lock(root):
        lane = load_and_find(root, args.id)
    if lane["verification"]["executor"] != "script":
        die(EXIT_ILLEGAL, "executor=human 的泳道请走 confirm-lane（人跑完后经人门确认）")
    if lane["kind"] == "hardware":
        die(EXIT_ILLEGAL, "kind=hardware ⇒ 脚本不执行烧板命令。请走 executor: human，"
                          "验证方法指向 embedded-test-sop。")

    snap = plan_snapshot(lane)                    # ← 长跑前拍快照
    res = runner.run(lane["verification"]["method"], root,
                     lane.get("env"), timeout=args.timeout)   # ← 锁【不】持有

    with write_lock(root):                        # ← 回写时才重新持锁
        data = load_lanes(root)
        cur = find_lane(data, args.id)
        if plan_snapshot(cur) != snap:
            die(EXIT_CAS, "lane 在验证期间被改动，本次执行证据作废；请重读后重跑")
        if res.exit_code == 0 and not res.timed_out:
            cur["status"] = "verified"
            cur["blocked_by"] = ""                # 绿泳道 MUST NOT 残留 blocked_by
            cur["verification"]["evidence"] = {
                "at": now_iso(),
                "at_commit": head_sha(root),          # 给人读的坐标，【不作机械比对基准】
                "exit": 0, "output_digest": sha(res.output_tail),
                "file_digests": lane_file_digests(root, cur),      # 时效锚：文件〔A21〕
                "method_at_verify": cur["verification"]["method"], # 时效锚：命令字符串〔A21 面治补口〕
                "attested_by": "script",
            }
        else:
            cur["status"] = "scaffolded"
            cur["blocked_by"] = compose_blocked_by(res)   # 差什么 + 怎么修 + 怎么 continue
                                                          # 超时时含 res.orphan_warning
        patch_one_lane(data, args.id, cur)
        save_lanes(root, data)


def cmd_confirm_lane(args):
    """human 通道。

    【诚实边界】脚本【无法】区分调用者是人门还是模型 —— agent session 里模型是唯一的
    命令执行者。故本命令【不设防伪】，只如实标注 attested_by: human，让读者知道
    这条绿是【人说的】，不是脚本验的。渲染时与脚本验证的绿可区分。
    """
    if lane["verification"]["executor"] != "human":
        die(EXIT_ILLEGAL, "executor=script 的泳道 MUST 走 verify-lane（脚本亲自执行）")
    if not args.confirmed_what.strip():
        die(EXIT_BADINPUT, "confirm-lane MUST 写明人确认了什么")
    ...evidence = {..., "confirmed_what": args.confirmed_what, "attested_by": "human"}
```

- [ ] **Step 4: 跑测试** — Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task8-verify-confirm" "两条验证通道：verify-lane 脚本亲自 fork(证据 attested_by=script) · confirm-lane 人门写(attested_by=human，如实标注不设防伪) · CAS 跨长跑 · hardware/human refuse（R-EXEC）"
```

---

### Task 9: touched-files 事务 journal（③-pre 否决的回退）

**Files:**
- Create: `sdflow-devenv/scripts/devenv_txn.py`
- Test: `sdflow-devenv/tests/test_txn.py`

**⚠️ 前一版的两个致命缺陷（MUST 修）：**
1. **清单只记 digest 不记内容** ⇒「恢复原内容」**根本做不到**（digest 不是内容）
2. **清单不持久** ⇒ session 在「写落地物 → ③-pre」之间崩溃，留下一堆**未经批准的文件**，下次运行无从复原

**Interfaces:**
- Produces: `begin(root, paths) -> None`（**写入任何落地物之前**原子落盘）· `rollback(root)` · `commit(root)` · `pending(root) -> dict | None`

- [ ] **Step 1: 写失败测试（要点）**

```python
def test_journal_records_original_CONTENT_not_digest(tmp_path):
    """digest 恢复不了文件"""
    (tmp_path / "Makefile").write_text("old content\n")
    txn.begin(tmp_path, ["Makefile", "new_smoke.go"])
    j = json.loads((tmp_path / ".devenv-txn.json").read_text())
    entry = next(e for e in j["files"] if e["path"] == "Makefile")
    assert entry["existed"] is True
    assert entry["content"] == "old content\n"      # ← 原【内容】，不是 digest
    assert entry["mode"]
    new_entry = next(e for e in j["files"] if e["path"] == "new_smoke.go")
    assert new_entry["existed"] is False

def test_rollback_restores_modified_and_deletes_new(tmp_path):
    (tmp_path / "Makefile").write_text("old\n")
    txn.begin(tmp_path, ["Makefile", "new_smoke.go"])
    (tmp_path / "Makefile").write_text("MODEL WROTE THIS\n")
    (tmp_path / "new_smoke.go").write_text("package x\n")
    txn.rollback(tmp_path)
    assert (tmp_path / "Makefile").read_text() == "old\n"      # 复原
    assert not (tmp_path / "new_smoke.go").exists()            # 精确删除

def test_rollback_never_touches_unrelated_untracked(tmp_path):
    """MUST NOT 用无路径限定的 git clean —— 会误删操作者未 git add 的其他文件"""
    (tmp_path / "my_wip_notes.txt").write_text("我的草稿\n")   # 操作者自己的 untracked 文件
    txn.begin(tmp_path, ["new_smoke.go"])
    (tmp_path / "new_smoke.go").write_text("x\n")
    txn.rollback(tmp_path)
    assert (tmp_path / "my_wip_notes.txt").exists()            # ← 绝不能被删

def test_pending_detected_after_crash(tmp_path):
    """崩溃后下次启动 MUST 检测到未完成 journal"""
    txn.begin(tmp_path, ["Makefile"])
    assert txn.pending(tmp_path) is not None

def test_commit_clears_journal(tmp_path):
    txn.begin(tmp_path, ["Makefile"])
    txn.commit(tmp_path)
    assert txn.pending(tmp_path) is None

def test_rollback_refuses_if_file_changed_after_write(tmp_path):
    """人门期间人手改了 —— 拒绝盲删，留人裁决"""

def test_paths_go_through_containment(tmp_path):
    with pytest.raises(PathEscape):
        txn.begin(tmp_path, ["../../etc/passwd"])
```

- [ ] **Step 2: 确认失败**

- [ ] **Step 3: 实现要点**

```python
TXN_REL = "openspec/architecture/.devenv-txn.json"

def begin(root, rel_paths):
    """写入任何落地物【之前】原子落盘。记原【完整内容】。"""
    files = []
    for rel in rel_paths:
        p = contain(root, rel)                    # ← 全部经 containment
        if p.exists():
            files.append({"path": rel, "existed": True,
                          "content": p.read_text(encoding="utf-8"),   # ← 内容，非 digest
                          "mode": p.stat().st_mode & 0o777})
        else:
            files.append({"path": rel, "existed": False})
    atomic_write(Path(root) / TXN_REL,
                 json.dumps({"began_at": now_iso(), "files": files},
                            indent=2, ensure_ascii=False) + "\n")

def rollback(root):
    j = pending(root) or return
    for e in j["files"]:
        p = contain(root, e["path"])              # ← 再次经 containment
        if e["existed"]:
            atomic_write(p, e["content"], mode=e["mode"])     # 用【原内容】复原
        elif p.exists():
            p.unlink()                            # 精确删除本次新写的
            # MUST NOT git clean —— 会误删操作者未 git add 的其他文件
    (Path(root) / TXN_REL).unlink()
```

- [ ] **Step 4: 跑测试** — Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task9-txn-journal" "touched-files 事务 journal：写前原子落盘、记【原完整内容】(非 digest)、否决时精确回退、崩溃后可检测；MUST NOT git clean（R-TXN）"
```

---

### Task 10: `render` —— 两份 JSON → 两份 Markdown（诚实渲染）

**Files:** Modify `devenv_scaffold.py` · Create `references/{environments,testing-strategy}-template.md` · Test `tests/test_render.py`

**⚠️ 渲染 MUST 携带诚实信息**（round-3 对抗镜 F4）：三个月后另一个人打开 `environments.md`，若只看到「泳道 X：verified ✓」，当初那句「这个方法只证明命令耦合了依赖，不证明断言有效」**已经蒸发**。

- [ ] **Step 1: 测试要点**

```python
def test_verified_rendered_with_commit_anchor(tmp_path):
    """verified 是【历史执行记录】，不是当前状态的绿灯 —— file_digests 不覆盖被测实现"""
    md = render_environments(tmp_path)
    assert "verified-at abc1234" in md
    assert "✅ verified\n" not in md          # MUST NOT 呈现为无条件的绿

def test_human_attested_distinguishable(tmp_path):
    md = render_environments(tmp_path)
    assert "已确认（人工验证）" in md
    # 与脚本验证的绿在视觉上可区分

def test_strength_rendered_into_doc(tmp_path):
    """盲区披露 MUST 落进文档，MUST NOT 只在人门口头说"""
    md = render_environments(tmp_path)
    assert "不证明断言有效" in md

def test_do_not_edit_banner(tmp_path):
    assert "DO NOT EDIT" in render_environments(tmp_path)

def test_strategy_renders_three_layers(tmp_path):
    md = render_testing_strategy(tmp_path)
    for layer in ("单元测试", "集成测试", "端到端"):
        assert layer in md
    assert "不适用" in md and "后果" in md    # not-applicable 的后果必须可见
    assert "人工" in md and "用户按" in md    # manual 的步骤必须可见

def test_line_numbers_are_generated_not_stored(tmp_path):
    """行号仅在 render 时动态生成供阅读，不作真相"""
```

- [ ] **Step 2-4: 实现 + 跑测试** — Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task10-render" "render 诚实渲染：verified-at <sha>(非无条件绿) · human-attested 可区分 · strength 盲区落进文档 · 三层框架从 JSON 渲染（R-DOC）"
```

---

### Task 11: `devenv_lint.py` —— 只查诚实（防漏），不查质量（防伪）

**Files:** Create `sdflow-devenv/scripts/devenv_lint.py` · Test `tests/test_lint.py`

**九条检查（每一条都是「防漏」，无一条试图判断「质量」）：**
① `verification.method`/`strength` 非空 ② 状态与证据匹配（`verified` ⇒ evidence 齐全 ∧ **`file_digests` 未失配**（`stale_files()` 返回空）∧ `blocked_by` 为空；`scaffolded` ⇒ `blocked_by` 非空且含修复指引）③ **三层框架完整性**（读 JSON，**非解析 Markdown**）④ **三态强制附带项** ⑤ 命令出处一致性——**只查 `file_digests` 未失配**（**非行号**；**MUST NOT 对 `source` 做任何 make 语法解析：既不提取 recipe，也不用正则查 target 存在性**〔A21〕——「能不能跑」由 `verify-lane` 真跑一遍让 make 自己判）⑥ 指针不悬空 ⑦ 删源残留引用（**排除 `.devenv-backup/`**）⑧ 路径 containment ⑨ 入口复述检测

- [ ] **Step 1: 测试要点**

```python
def test_lint_catches_line_still_there_content_changed(tmp_path):
    """原规格下这不是坏输入 ⇒ 测了也测不到真问题"""
    seed_verified_lane(tmp_path)
    bump_makefile_recipe(tmp_path)               # 行还在，内容变了
    assert lint(tmp_path).failed
    assert "验证证据已过期" in lint(tmp_path).report

def test_lint_catches_missing_layer(tmp_path):
    del_strategy_layer(tmp_path, "e2e")
    assert "缺 e2e 层" in lint(tmp_path).report

def test_lint_catches_na_without_consequence(tmp_path):
    set_layer(tmp_path, "e2e", status="not-applicable", reason="纯库")  # 无 consequence
    assert "consequence" in lint(tmp_path).report

def test_lint_catches_implemented_pointing_at_planned_lane(tmp_path):
    """挂靠一条 planned 空壳泳道 —— 前一版只堵「完全没有泳道」，不堵这个"""
    seed_lane(tmp_path, id="e2e-smoke", status="planned")
    set_layer(tmp_path, "e2e", status="implemented", lane_ids=["e2e-smoke"])
    assert "status ∈ {scaffolded, verified}" in lint(tmp_path).report

def test_lint_catches_blocked_by_todo(tmp_path):
    seed_lane(tmp_path, status="scaffolded", blocked_by="TODO")
    assert lint(tmp_path).failed

def test_lint_catches_verified_with_blocked_by(tmp_path):
    """绿泳道挂着「本机无 X」= 文档在说谎"""

def test_lint_pass_code_is_honest(tmp_path):
    assert "structure-ok-SEMANTICS-UNCHECKED" in lint(tmp_path).report

def test_lint_does_NOT_judge_method_quality(tmp_path):
    """总则：机械层不判断验证方法有没有效 —— 那归人门与冷审"""
    seed_lane(tmp_path, method="echo ok", strength="这个方法什么也证明不了")
    assert not lint(tmp_path).failed          # lint MUST NOT 因方法弱而报错
```

- [ ] **Step 2-4: 实现 + 跑测试** — Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task11-lint" "devenv_lint 九条：只查诚实(防漏)不查质量(防伪) · 三层框架读 JSON 非解析 Markdown · digest 非行号 · 诚实通过码（R-LINT）"
```

---

### Task 12: `append_makefile_target` + `doctor-gen` + `inject`（fence-aware）+ recipe 展示

**Files:** Modify `devenv_scaffold.py` · Create `tests/fixtures/fence/*.md` · Test `tests/test_scaffold.py`（追加）

**⚠️ `inject` MUST 为 fence-aware**：**MUST NOT 照抄 `init.py`** —— 其 `:49-52` 注释明示判据尚非 fence-aware，会命中代码块内演示的 marker，fence-aware 版本已 defer。**照抄将继承该缺陷**，而消费仓的 README 很可能在代码块里演示 marker（本仓自身即是）。

> **为什么 fence-aware 是安全的、而 make parser 不是**（免得你把 A21 误读成「一切解析都禁」）：**CommonMark 的 fence 语法面是有界的**——` ``` ` / `~~~` / 四 backtick / 缩进 fence，**穷举得完**。GNU make 的语法面**无界**。**有界 ⇒ 可穷举 ⇒ 可正确；无界 ⇒ 补丁循环永不收敛。** 这就是判据。

---

**⚠️⚠️ 本 Task 是 A21 唯一允许出现 make 正则的地方。两处，边界钉死：**

| 用途 | 性质 | 找不到时怎么办 | 兜底 |
|---|---|---|---|
| **① 重名检测**（`append_makefile_target`） | best-effort，**只在「确定存在」方向 fail** | **照常追加**（漏判） | ③-pre **人门看 diff** + **make 自己会报 `overriding recipe for target`**。skill 是**追加者**——最坏后果是多一条定义，**不删不改人的东西** |
| **② recipe 展示**（给人看，跑之前呈现 `rm -rf` 之类） | best-effort，**纯展示，零判定** | **降级**为「无法自动展开，请查看 `<file>` 的 `<selector>` target」 | 人自己看原文 |

**两条硬约束（违反 = A21 从后门复活）**：

1. **这两处的代码 MUST NOT 被复用为任何 digest / 机械判定的基准。** `file_digests` 只认整文件原始字节（Task 4），**MUST NOT** 调用这里的任何函数。
2. **MUST NOT 为提高精度而扩充 make 语法覆盖。** 想要权威展开，正解是**调 `make` 自己**（`make -n <target>`，并如实标注它会执行 `$(shell ...)` 的边界）——**MUST NOT 手搓**。

> **判据（记住这一条就够）**：**机械保证的东西必须正确**（∴ 无界语法面 = 死路）；**给人看的辅助允许 best-effort + 降级**。前者的失败是**罢工**（击穿「不管什么项目」），后者的失败只是**少显示一段文字**。

- [ ] **Step 1: 测试要点**

```python
def test_inject_ignores_marker_inside_fence(tmp_path):
    """fixture 必须是 checkin 的【固定语料】，MUST NOT 拿本仓活语料当 fixture"""
    md = load_fixture("fence/marker_in_code_block.md")
    out = inject(md, "opsx-devenv", "NEW")
    assert md.count("<!-- opsx-devenv:start -->") == out.count("<!-- opsx-devenv:start -->") - 1
    # fence 内的演示 marker 没有被劫持

@pytest.mark.parametrize("variant", ["backtick3", "tilde3", "backtick4", "indented"])
def test_inject_handles_all_commonmark_fence_variants(variant):
    ...

def test_inject_orphan_marker_fail_closed():
    with pytest.raises(InjectError) as e:
        inject(load_fixture("fence/orphan_start.md"), "opsx-devenv", "X")
    assert "位置" in str(e.value)               # fail-closed 报位置

def test_inject_never_writes_opsx_init_block():
    """整块替换 ⇒ 共用 marker 会使两个 skill 互相覆盖"""

def test_append_makefile_target_name_collision_fail_closed(tmp_path):
    """脚本【只判名字碰撞】，语义符不符归模型+人 —— MUST NOT 假装机械判断了语义"""
    r = append_target(tmp_path, "integration", "\tgo test\n")
    assert r.returncode == 2
    assert "名字" in r.stderr
    assert "语义" not in r.stderr or "归人" in r.stderr

def test_append_makefile_target_complex_syntax_never_raises(tmp_path):
    """⭐ A21：重名检测是 best-effort。在复杂 Makefile 上【漏判可以，罢工不行】。
    漏判的兜底 = 人门看 diff + make 自己报 `overriding recipe for target`。"""
    (tmp_path / "Makefile").write_text(COMPLEX_MAKEFILE)   # ifeq/define/双冒号/一行多 target
    r = append_target(tmp_path, "brand-new", "\t@true\n")  # MUST NOT raise / MUST NOT exit≠0,2
    assert r.returncode in (0, 2)                          # 0=追加了 2=判定重名；【不允许「语法不支持」】
    assert "语法" not in r.stderr and "不支持" not in r.stderr

def test_recipe_preview_degrades_never_raises(tmp_path):
    """⭐ A21：recipe 展示是【纯展示】。提取不了就【降级】，MUST NOT 罢工。"""
    (tmp_path / "Makefile").write_text(COMPLEX_MAKEFILE)
    out = recipe_preview(tmp_path, "Makefile", "integration")   # ifeq 包裹的 target
    assert out is None or isinstance(out, str)                  # 提取到 → str；提不到 → None
    # 调用方据此渲染「无法自动展开，请查看 Makefile 的 integration target」

def test_recipe_preview_not_reused_as_digest_basis():
    """⭐ A21 契约：展示代码 MUST NOT 渗回 digest 路径。"""
    import devenv_digest as d
    src = Path(d.__file__).read_text(encoding="utf-8")
    assert "recipe_preview" not in src and "devenv_scaffold" not in src

def test_append_makefile_target_no_trailing_newline(tmp_path):
def test_append_makefile_target_uses_tab(tmp_path):
def test_doctor_gen_is_executable(tmp_path):
    """0o755 —— 原 sad_scaffold 硬编码 0644 ⇒ 落盘即不可执行"""
    assert oct((tmp_path / "hack/doctor.sh").stat().st_mode)[-3:] == "755"
def test_doctor_gen_does_not_install(tmp_path):
    """MUST NOT 替操作者安装系统依赖"""
    body = (tmp_path / "hack/doctor.sh").read_text()
    assert "brew install" not in body or "# 请手动执行" in body
```

- [ ] **Step 2-4: 实现 + 跑测试** — Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task12-append-inject" "append_makefile_target(只判名字碰撞) + doctor-gen(0o755，不替人装依赖) + inject fence-aware(不照抄 init.py 的已知缺陷)（R-APPEND/R-MARKER）"
```

---

### Task 13: `references/` 七份（含三条负面知识）

**Files:** Create `references/{lane-patterns,verification-patterns,boundary-rules,review-lenses}.md`（`exit-codes.md`/`env-allowlist.md`/两份 template 已在前置 Task 建）

**⚠️ `verification-patterns.md` MUST 含四条负面知识**（这是三轮评审 + 一次接地实验 + **一次实现期返工**唯一买到的东西，**让下一次的模型站在已知盲区之上**）：

1. **negative control 在真实项目上常常抽不动** —— mqtt-console 的 `Makefile:11-14` 把连接参数与依赖启停**打包进同一条 recipe 的字面文本**（`MQTT_PORT=1883` 是 shell 前缀赋值）⇒ 对任何外部覆盖免疫 ⇒ 隔离式无注入点 · 停服务接不上 · 改 Makefile 被禁止。**三条路全堵死。而这种写法常见且合理。**
2. **轮询式连接观测：瞬时连接漏检率 100%**（`lsof` 轮询进程组，5/5 全漏，现场实验证伪）—— **采样抓不住瞬时事件，方法本身错，不是参数没调好。**
3. **`assert True` 类语义恒真，任何外部插桩都堵不住** —— proxy 计数（零漏检）能证明"跟依赖说过话"，**但不能证明"断言有效"**。要堵只有变异测试（太重）⇒ **机械层堵不死，归冷审 vacuous 镜。**
4. **⭐ MUST NOT 手搓无界语法的解析器**〔A21，**实现期用三轮返工买到的**〕—— 曾要求「lint 用 parser 按 selector 重定位 make target、提取 recipe body 做 digest」。GNU make 的语法面**无界**（`ifeq` / `define` / 双冒号 / 模式规则 / 续行 / 内联 `;` / target-specific 变量…），**每轮 review 都挖出一个新角落**（脚本 261→562 行、测试 304→753 行），最终留下 **7 个「语法不支持」的罢工分支**——**而每个罢工分支都是对「不管什么项目都能给一份三层框架」这条核心承诺的一次背叛。**
   - **判据（有界 vs 无界）**：CommonMark 的 fence 变体**可穷举** ⇒ 手写 fence-aware 解析**是安全的**（Task 12 的 `inject` 就该这么做）。GNU make / shell / 通用编程语言的语法面**无界** ⇒ **补丁循环永不收敛**。**能不能穷举，就是能不能手搓的分界线。**
   - **正解**：**想知道某个 make / shell / 语言构造是什么意思，就让那个工具自己回答**——真跑一遍（`verify-lane` 的做法：target 不存在 ⇒ make 自己报 `No rule to make target` ⇒ `exit≠0`）或调 `make -n`。**本 skill 的核心机制恰好就是「尽可能跑一遍确认」——跑一遍，就是最强的解析器。**
   - **警号**：**当你发现「每轮 review 都在同一个函数里补一个新的语法分支」，那不是"还差最后一个 case"，那是"这个函数本来就不该存在"。**

`review-lenses.md` 冷审镜单 MUST 含：覆盖镜 · **验证方法镜**（`strength` 有无夸大 · `why_not_scriptable` 是否成立）· **分类镜**（`kind`/`layer`/`covers`/`fixtures`/`env` 是否属实——**这些无独立信号却是机械层的输入，必须有一镜专查**）· **vacuous 镜**（唯一防线）· 诚实镜（含 `human-attested` 的 `confirmed_what` 是否具体）· 删源镜

- [ ] **Step 1-4:** 写 4 份 Markdown（无代码，无测试）；`lane-patterns.md` 按**依赖形态四问**分格（**非按语言**），**只固化「问什么」不固化「答什么」**，实例标「非规格」

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task13-references" "references 七份：verification-patterns 含三条接地实验的负面知识 · review-lenses 含验证方法镜/分类镜/vacuous 镜 · lane-patterns 只固化问什么"
```

---

### Task 14: `SKILL.md` 编排（五步 · 三模式 · 两道人门）

**Files:** Create `sdflow-devenv/SKILL.md`

**关键内容：**
- frontmatter `description`：含与 `sdflow-init` 的**分流判据句**（装流程规则 → init；建项目 dev/test 环境 → devenv）+ 两条前置声明
- **③-pre 人门（执行任何验证之前）**：① 新写落地物 diff 全文（**仅登记的既有 target 只展示登记映射**，MUST NOT 要求人重读他自己写的代码）② 验证方法逐条确认（含 `strength`）③ **声明清单过目**（`kind`/`layer`/`executor`/`fixtures`/`env`——**全部无独立信号**）④ 命令（recipe 展开）。**②③ 表格化一次性呈现**（"逐条" = 清单里逐行列出，**不是**逐条打断式提问）
- **④ 人门（执行后 + 冷审后）**：① 泳道复核 ② 未 verified 逐条确认 ③ 三层框架的 `不适用` 槽逐条确认 ④ `executor: human` → `confirm-lane` ⑤ **删源清单单独拎出**（不可逆，不与常规议程同级）
- **人门呈现 SHALL 用人话**：`executor`/`kind`/`layer` 先翻译成后果描述再呈现
- 收尾：**逐条列出**未 verified 泳道 + **整体判定 + 下一步怎么调用**

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task14-skill-md" "SKILL.md 五步编排：③-pre 人门在执行之前(含无信号声明清单) · ④ 人门(删源单独拎出) · 批量呈现 · 收尾给整体判定与下一步（R-GATE/R-TRIG）"
```

---

### Task 15: 面治腿 2 —— `sdflow-init/scripts/init.py` 的 `inject()` 补锁 + 原子写

**Files:** Modify `sdflow-init/scripts/init.py:91-128` · Test `sdflow-init/tests/test_init_lock.py`

**现状（已核实）**：`inject()` 末尾是**裸 `open(path, "w")` 全量覆写**（`:126-127`），**无锁、无原子写** ⇒ devenv 注入 ‖ `/sdflow-init update` 覆写同一文件 ⇒ **devenv 的整块注入被静默吃掉**。
（注：该文件的 `fcntl` **只用于 `settings.json`**，与 `inject()` 无关——别混淆。）

- [ ] **Step 1: 测试** — 两进程并发注入不丢块 · 锁文件用共用锁名 · 锁记 owner 且释放前核对
- [ ] **Step 2-4: 实现** — 在 `init.py` 内实现与 `devenv_lock` **格式一致**的锁（三 skill 无法互相 import，故各自实现 + 契约测试钉死）；`inject()` 的写入改为 `mkstemp` + `os.replace`
- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task15-init-lock" "面治腿2：init.py 的 inject() 补写域锁 + 原子写（原为裸 open(w) 全量覆写，会静默吃掉 devenv 的注入）（R-CONC）"
```

---

### Task 16: 面治腿 3 —— `sad_scaffold.py` 迁共用锁 + **从零加 owner** + `atomic_write(mode)`

**Files:** Modify `sdflow-architecture/scripts/sad_scaffold.py:38,64-85,112-140` · Test `sdflow-architecture/tests/test_sad_lock.py`

**现状（已核实，三条都要改）**：
1. `LOCK_REL = "openspec/.sad-scaffold.lock"`（`:38`）—— **另一把锁**，与 devenv 互斥不了
2. `_acquire_lock` **根本没写入过 owner 信息**（只 `os.open` 建空文件），`_release_lock` 直接 `unlink` —— **是从零加机制，不是「补核对」**
3. `atomic_write(path, text)` **无 mode 参数**，`os.chmod(tmpname, 0o644)` 硬编码（`:78`）—— 复用它写 doctor 脚本会**落盘即不可执行**

- [ ] **Step 1: 测试** — 迁到共用锁名 · owner 记录 + 释放前核对（A 不删 B 的锁）· `atomic_write(mode=0o755)` 生效 · 覆盖既有文件保留原 mode · **`sdflow-architecture` 原有 68 个测试全绿**（回归）
- [ ] **Step 2-4: 实现**
- [ ] **Step 5: 删掉 `test_lock_contract.py` 的 `xfail` 标记，让契约真正生效**

```bash
pytest sdflow-devenv/tests/test_lock_contract.py -v     # 现在必须【全绿】，无 xfail
pytest sdflow-architecture/tests/ -v                     # 回归：原 68 测试全绿
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task16-sad-lock" "面治腿3：sad_scaffold 迁共用锁 + 从零加 owner(原本没写入过) + atomic_write 加 mode 参数(原硬编码 0644 ⇒ doctor 脚本落盘即不可执行)；锁契约测试转全绿（R-CONC）"
```

---

### Task 17: `sdflow-maintain` 新增 devenv 健康度扫描（`devenv_lint` 的唯一触发点）

**Files:** Modify `sdflow-maintain/scripts/maintain_scan.py`（`run_scan` `:249-257` 硬编码四类管线 → 加第五类）· `sdflow-maintain/SKILL.md` · Test `sdflow-maintain/tests/test_devenv_scan.py`

> **dogfood 自指坑**：本 change 把「无门禁——检查无任何自动触发点」列为**立项理由之一**，而前一版的 `devenv_lint` **自己也没有任何触发点**。**没有触发点的 lint = 没有 lint。**
> **诚实边界**：maintain 是**人主动跑**的 ⇒ 这是「更响的提醒」而非硬门禁，**MUST NOT 佯装硬拦截**。

- [ ] **Step 1: 测试** — 检出 `environments.md` → 调 `devenv_lint` · **报告原样透传诚实后缀**（MUST NOT 二次渲染成「verified = ✓」）· 无 `environments.md` → 跳过（非报错）· `devenv_lint` 不可用 → **显式提示，MUST NOT 静默略过**
- [ ] **Step 2-4: 实现**（**注意：maintain 现为四类硬编码扫描、无插件挂点 ⇒ 这是新增代码**）
- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task17-maintain-scan" "sdflow-maintain 新增第五类扫描：devenv 健康度(devenv_lint 的唯一触发点) · 原样透传诚实后缀不二次渲染（M-1）"
```

---

### Task 18: 仓级集成 —— 双向分流句 · README · CLAUDE.md · setup.sh

**Files:** Modify `sdflow-devenv/SKILL.md` · `sdflow-init/SKILL.md` · `sdflow-architecture/SKILL.md` · `README.md` · `CLAUDE.md`

- [ ] **Step 1: 双向触发分流**（**词面碰撞是双向的，只补一边不解决路由**）
  - `sdflow-devenv` description：「装流程规则 → `/sdflow-init`；建项目 dev/test 环境 → `/sdflow-devenv`」
  - **`sdflow-init` description 加反向排除句**：「不管理项目的 dev/test 运行环境 / 依赖 / CI —— 那部分 → `/sdflow-devenv`」
- [ ] **Step 2: `sdflow-architecture` 交棒话术**改为**指向 `/sdflow-devenv`**（保留「不代写」边界 + 继续给 SAD 锚）
- [ ] **Step 3: README「Skills 列表」+ CLAUDE.md「两类 skill」分类**（devenv 归数据类）
- [ ] **Step 4: 跑 `bash setup.sh` 验证双宿主装载 + 全量回归**

```bash
bash setup.sh
pytest sdflow-devenv/tests/ sdflow-architecture/tests/ sdflow-init/tests/ sdflow-maintain/tests/ -v
```
Expected: 全绿，**无 xfail**

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh "add-sdflow-devenv:task18-integration" "仓级集成：双向分流句(init 侧反向排除) · architecture 交棒指向 devenv · README/CLAUDE 更新 · setup.sh 双宿主装载验证（R-TRIG/A-1）"
```

---

## Self-Review

**Spec coverage（21 条 Requirement → Task 映射）：**

| Requirement | Task |
|---|---|
| R-PATH（路径 containment） | 1 |
| R-CONC（并发/原子写/CAS/退出码） | 2, 5, 6, 15, 16 |
| R-DATA（两份 JSON + digest 锚） | 3, 4 |
| R-STRAT（测试三层框架） | 3, 10, 11 |
| R-PF（preflight 三模式） | 6 |
| R-EXEC（执行者分工） | 6, 8 |
| R-BOUND（执行边界/不伤害） | 7, 12 |
| R-VERIFY（验证方法） | 8, 13 |
| R-TRISTATE（泳道三态） | 6, 11 |
| R-TXN（事务 journal） | 9 |
| R-DOC（文档渲染） | 10 |
| R-LINT（机械 lint） | 11 |
| R-APPEND（落地物追加） | 12 |
| R-MARKER（fence-aware inject） | 12 |
| R-GATE（冷审与人门） | 14 |
| R-LANE（泳道设计） | 13, 14 |
| R-FACT（事实采集） | 14 |
| R-RELOC / R-DELGUARD（归位/删源） | 14（SKILL.md 编排）+ 9（txn）+ 1（containment） |
| R-MAINT（lint 触发点） | 17 |
| R-TRIG（触发分工） | 18 |
| M-1（maintain-scan） | 17 |
| A-1（architecture-design） | 18 |

**⚠️ 覆盖缺口（如实登记）**：R-RELOC / R-DELGUARD（归位模式的素材盘点、判归属、搬运表、删源护栏、backup manifest）**没有独立的编码 Task** —— 它们主要是 **SKILL.md 的编排纪律**（模型行为），其机械部分（containment / txn journal / `git status` 前置 / 逐文件校验）已分散在 Task 1/9。**实现 Task 14（SKILL.md）时 MUST 完整写出这两条的编排纪律**，并在 `tests/fixtures/brownfield/` 建 checkin fixture 供 SM-2 回归。

**不进 plan 的（如实登记）：**
- `tasks.md` 第 12 组（**首个真实试点**）—— 实现完成后由操作者用真实项目跑的**验收兼路线证伪**，不是编码任务。**它检验假设 A-8（模型能否为三层各自提出像样的验证方法）——整条路线的地基，至今零实证。**
- **无自动化覆盖（诚实登记）**：模型提的验证方法**是否有效** · `kind`/`layer`/`covers`/`fixtures`/`env` 声明**是否属实** · **`assert True` 类 vacuous** · **`human-attested` 的真实性**（agent session 架构边界，**且本就不必防**）—— 全部归**人门 + 冷审**，机械层**MUST NOT 佯装能守**。
