# issues-pool-hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 硬化 issues 池三 recorder（buglist/todolist/issues）的盘面完整性、可观测性与操作幂等（T1-T5 + spec-review OV-1/2/3）。

**Architecture:** 三 recorder（`sdflow-{buglist,todolist,issues}/scripts/*.py`）刻意无共享 import（issues.py subprocess 调两 recorder）。本 change 在**各 recorder 内**加写时 fail-closed 守卫（table-cell-safe reject 挂各命令**入口原始参数**、非 `" | ".join(cells)` sink）+ scan 读侧 arity 检测 + reindex 可观测 + batch 幂等，不引入跨 recorder 共享模块。

**Tech Stack:** Python 3（stdlib only：argparse/re/subprocess/json/pathlib）、pytest。

## Global Constraints

- **数据类纪律**：改任一 `scripts/*.py` 后 MUST 跑对应 recorder 测试（`pytest sdflow-buglist/tests/test_buglist.py` / `…todolist…` / `…issues…`）。
- **TDD**：每任务先写失败测试 → 跑证失败 → 最小实现 → 跑证通过 → commit。
- **checkpoint 格式**：每任务收尾 commit 步 MUST 用 `~/.sdflow/hack/checkpoint-commit.sh task<N> "<描述>"`（`task<N>` 是 ship_gate 追踪主锚，务必带任务号）。
- **守卫落点铁律（C1 BLOCKER）**：table-cell-safe 校验 MUST 挂各命令**入口的原始用户参数**，MUST NOT 挂 `" | ".join(cells)` 行拼接 sink（sink 在 `strip("|").split("|")` 之后、`|` 已被切走 → 挂那里永不 fire = 假覆盖）。
- **D2 --strict 诚实**：`--strict` 本 change **无消费者**（预置接口），MUST NOT 记作"已堵非交互静默蒸发"。
- 现存池 **0 行**字段含 `|`（存量），故无迁移；reject 是纯新写时守卫。

---

### Task 1: T2 table-cell-safe 守卫 helper + cmd_add 覆盖（三 recorder）

**Files:**
- Modify: `sdflow-buglist/scripts/buglist.py`（加 `_reject_cell_unsafe`；`cmd_add` 入口校验）
- Modify: `sdflow-todolist/scripts/todolist.py`（同款）
- Modify: `sdflow-issues/scripts/issues.py`（同款 helper，供后续任务复用）
- Test: `sdflow-buglist/tests/test_buglist.py`、`sdflow-todolist/tests/test_todolist.py`

**Interfaces:**
- Produces: `_reject_cell_unsafe(value: str, field: str) -> None`（含 `|` 或 `\n` 即调 `_die(f"字段 {field} 含非法字符（| 或换行）会破总览表：{value!r}")`），三 recorder 各有一份（无跨模块共享，D4）。

- [ ] **Step 1: 写失败测试（buglist）**

```python
# sdflow-buglist/tests/test_buglist.py 新增
def test_add_rejects_pipe_in_summary(tmp_path, monkeypatch):
    # summary 含 ASCII | → cmd_add 应 _die（SystemExit），不写出腐蚀行
    import buglist  # 见文件顶部既有 import 方式；若用 runpy/子进程，照既有测试风格
    # 用既有测试里调 add 的同款 helper（子进程或直接调 cmd_add），断言 rc!=0 且池文件未新增坏行
    ...
def test_add_rejects_newline_in_module(tmp_path):
    # module 含 \n → _die
    ...
```

> 实现者：照 `test_buglist.py` 既有测试的调用风格（子进程跑 `buglist.py add` 喂 JSON，或直接 `cmd_add(args)`）。断言：退出非 0 / `SystemExit`，且当日文件行数未增。

- [ ] **Step 2: 跑测试证失败**

Run: `pytest sdflow-buglist/tests/test_buglist.py -k "rejects_pipe or rejects_newline" -v`
Expected: FAIL（当前 cmd_add 无守卫，坏行被写入）

- [ ] **Step 3: 实现守卫 helper + cmd_add 入口校验（buglist，todolist 镜像，issues 加同款 helper）**

在 `buglist.py`（`_die` 定义之后）加：

```python
def _reject_cell_unsafe(value, field):
    """总览管道表字段 fail-closed 守卫：含 ASCII | 或换行即拒（防列错位/行截断腐蚀盘面）。
    MUST 用于各命令入口的原始用户参数，勿用于 " | ".join(cells) 行拼接 sink。"""
    if value is None:
        return
    if "|" in str(value) or "\n" in str(value) or "\r" in str(value):
        _die(f"字段 {field} 含非法字符（| 或换行），会破坏总览表列对齐：{value!r}")
```

在 `cmd_add`（buglist.py:353）**读入 data 后、拼 row 之前**，对进 row 的字段逐一校验：

```python
    for _f in ("module", "summary", "change"):
        _reject_cell_unsafe(data.get(_f), _f)
    _reject_cell_unsafe(data.get("batch"), "batch")
    _reject_cell_unsafe(time_str, "time")       # --time 自由文本也进 row
```

todolist.py `cmd_add` 镜像（字段名相同：module/summary/change/batch/time）。issues.py 只加 `_reject_cell_unsafe` helper（供 Task 2/3 复用），本步不改其命令。

- [ ] **Step 4: 跑测试证通过 + 回归**

Run: `pytest sdflow-buglist/tests/test_buglist.py sdflow-todolist/tests/test_todolist.py -v`
Expected: 新用例 PASS，既有用例全绿。

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task1 "T2 table-cell-safe 守卫 helper + cmd_add 入口校验（三 recorder）"
```

---

### Task 2: T2 补全 triage / rename 写路径（C1 BLOCKER 完成）

**Files:**
- Modify: `sdflow-buglist/scripts/buglist.py`（`cmd_triage`:477，`cells[7]=batch` 前校验 `batch`）
- Modify: `sdflow-todolist/scripts/todolist.py`（`cmd_triage`，同）
- Modify: `sdflow-issues/scripts/issues.py`（`_retag_items_in_dated_files`:681，`cells[7]=new_key` 前校验 `new_key`）
- Test: 三 recorder tests

**Interfaces:** Consumes Task 1 的 `_reject_cell_unsafe`。

- [ ] **Step 1: 写失败测试**

三处各一：`triage` 打含 `|` 的批次名 → `_die`；`rename` new_key 含 `|`/换行 → `_die`（issues）。

```python
# test_buglist.py
def test_triage_rejects_pipe_in_batch(tmp_path):
    # 先 add 一条 OPEN，再 triage --批次 "evil|key" → 退出非 0，cells[7] 未被腐蚀
    ...
# test_issues.py
def test_batch_rename_rejects_pipe_in_new_key(tmp_path):
    # 已有批次 + 成员，rename old "a|b" → _die
    ...
```

- [ ] **Step 2: 跑证失败** — `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -k "triage_rejects or rename_rejects" -v` → FAIL

- [ ] **Step 3: 实现**

`buglist.py cmd_triage`（`cells[7] = batch` 之前）加 `_reject_cell_unsafe(batch, "batch")`；todolist 镜像。
`issues.py _retag_items_in_dated_files`（`cells[7] = new_key` 之前）加 `_reject_cell_unsafe(new_key, "new_key")`。

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -v` → 全绿

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task2 "T2 补全 triage/rename 写路径守卫（C1 BLOCKER：真·管道表 batch-key 写入全覆盖）"
```

---

### Task 3: OV-2 batch key slug 校验（拒 ` — ` / 首尾空白）

**Files:**
- Modify: `sdflow-issues/scripts/issues.py`（加 `_reject_batch_key_unsafe`；`cmd_batch_add`:574、`cmd_batch_rename` new_key、以及 triage 传入的 `--批次` 若经 issues 则同）
- Test: `sdflow-issues/tests/test_issues.py`

**Interfaces:** Produces `_reject_batch_key_unsafe(key)`（在 `_reject_cell_unsafe` 基础上再拒 ` — ` 子串、首尾空白）。

- [ ] **Step 1: 写失败测试**

```python
def test_batch_add_rejects_emdash_delimiter_in_key(tmp_path):
    # batch add "a — b" → _die（否则 header "### a — b — title" 解析把 key 切成 "a"）
    ...
def test_batch_add_rejects_leading_trailing_space(tmp_path):
    ...
```

- [ ] **Step 2: 跑证失败** — `pytest sdflow-issues/tests/test_issues.py -k "emdash or leading_trailing" -v` → FAIL

- [ ] **Step 3: 实现**

```python
def _reject_batch_key_unsafe(key):
    _reject_cell_unsafe(key, "batch key")
    if " — " in key or key != key.strip():
        _die(f"batch key 非法（含 ' — ' 分隔符或首尾空白），会破坏 batches.md header 解析：{key!r}")
```

`cmd_batch_add`（写 `### {key} — {title}` 之前）+ `cmd_batch_rename`（用 new_key 之前）调之；`--title` 加 `_reject_cell_unsafe(title, "title")`（拒换行）。triage 的 `--批次` 值经 recorder 时已在 Task 2 校验 `|`/换行，此处 issues 侧 batch add/rename 补 slug 严格性。

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-issues/tests/test_issues.py -v` → 全绿

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task3 "OV-2 batch key slug 校验（拒 ' — ' 分隔符/首尾空白 + title 拒换行）"
```

---

### Task 4: OV-3 自定义 id 语法 + 查重 + scan 报重复 ID

**Files:**
- Modify: `sdflow-buglist/scripts/buglist.py`（`cmd_add` 显式 id 校验；`cmd_scan` 报重复 ID）
- Modify: `sdflow-todolist/scripts/todolist.py`（镜像）
- Test: 两 recorder tests

**Interfaces:** Consumes `ID_RE`(buglist:59 `\b([A-Z])(\d+)\b`)、`all_ids(root, prefix)`(buglist:243)。

- [ ] **Step 1: 写失败测试**

```python
def test_add_rejects_malformed_explicit_id(tmp_path):
    # data["id"]="bad id" → _die（非 [A-Z]\d+）
    ...
def test_add_rejects_duplicate_explicit_id(tmp_path):
    # 先 add 得 B1，再 add data["id"]="B1" → _die（防 parse_table_rows 按 ID dict 静默丢行）
    ...
```

- [ ] **Step 2: 跑证失败** — `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ -k "malformed_explicit or duplicate_explicit" -v` → FAIL

- [ ] **Step 3: 实现**

`cmd_add` 里 `bid = data.get("id") or next_id(...)` 之后，若 `data.get("id")` 显式传入：

```python
    if data.get("id"):
        if not re.fullmatch(r"[A-Z]+\d+", bid):
            _die(f"显式 id 语法非法（应形如 B12）：{bid!r}")
        if bid in all_ids(root):
            _die(f"显式 id 与既有重复（会静默丢行）：{bid}")
```

`cmd_scan` 末尾（既有 problems 汇总处）：检测同池重复 ID 并加入 `problems`（`all_ids` 前的原始扫描里若同一 ID 出现 >1 次）。

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ -v` → 全绿

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task4 "OV-3 自定义 id 语法(fullmatch)+查重 + scan 报重复 ID"
```

---

### Task 5: T1 reindex problems 回显 stderr + `--strict` + OV-1 scan 行 arity 检测

**Files:**
- Modify: `sdflow-issues/scripts/issues.py`（`_scan_pool`:133 返回 problems；`cmd_reindex`:296 回显 stderr + `--strict`；argparse 加 `--strict`）
- Modify: `sdflow-todolist/scripts/todolist.py` + `sdflow-buglist/scripts/buglist.py`（`cmd_scan` 加行 arity 校验入 problems）
- Test: `sdflow-issues/tests/test_issues.py`、todolist/buglist tests

**Interfaces:** `_scan_pool` 现丢弃 `data["problems"]`（issues.py:141-144）——改为返回 `(items, problems)`；`read_pool` 调用点 `cmd_batch_rename`(issues.py:712) 同步适配。

- [ ] **Step 1: 写失败测试**

```python
# test_issues.py
def test_reindex_echoes_problems_to_stderr_exit0(tmp_path):
    # 制造表↔块不一致 → reindex：stderr 含该 problem、exit 0、INDEX 仍重建
    ...
def test_reindex_strict_exits_nonzero_on_problems(tmp_path):
    # 同不一致 + --strict → exit!=0（默认无 --strict 仍 exit 0）
    ...
# test_todolist.py（OV-1 读侧）
def test_scan_flags_arity_corrupted_row(tmp_path):
    # 无块坏行：summary 直接手写含裸 | 致 8→9 列 → scan problems 含 arity 报告
    ...
```

- [ ] **Step 2: 跑证失败** — 相关 `-k` → FAIL（reindex 现丢 problems、无 --strict、scan 不验 arity）

- [ ] **Step 3: 实现**

(a) `cmd_scan`（buglist/todolist）：解析每数据行时，`len(cells)` 非 8（旧格式 7）即 append 一条 `problems`（`f"{ID} 行 arity 异常：{len(cells)} 列（应 8/7）"`）。
(b) `_scan_pool`（issues.py）：改为收集并返回子进程 `scan --json` 的 `problems`。
(c) `cmd_reindex`：重建 INDEX 后，若聚合 problems 非空 → 逐条 `print(p, file=sys.stderr)`；`args.strict and problems` → `sys.exit(1)`；否则 exit 0。argparse `reindex` 子命令加 `--strict` (`action="store_true")`。致命错误（读文件失败）仍走既有非 0。
(d) `cmd_batch_rename` 的 `read_pool` 调用点适配新返回签名（取 items）。

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-issues/tests/ sdflow-todolist/tests/ sdflow-buglist/tests/ -v` → 全绿

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task5 "T1 reindex problems 回显 stderr + --strict(预置接口) + OV-1 scan 行 arity 检测"
```

---

### Task 6: T3 终态集跨脚本一致性守卫测试

**Files:**
- Test only: `sdflow-issues/tests/test_issues.py`（纯新增测试，不改生产逻辑，除非发现现状已不一致）

**Interfaces:** Consumes `issues.TERMINAL_STATUSES`（per-pool dict）、`buglist.STATUS_CODES`、`todolist.STATUS_CODES`；recorder 内联字面量 buglist `cmd_scan`(:579)/`cmd_triage`(:507) 的 `{FIXED,WONTFIX}`。

- [ ] **Step 1: 写测试（守卫）**

```python
def test_terminal_sets_subset_and_inline_consistency():
    import issues, importlib.util
    # (a) 按 pool dict 索引：issues.TERMINAL_STATUSES["bug"] ⊆ set(buglist.STATUS_CODES)，todo 同
    assert issues.TERMINAL_STATUSES["bug"] <= set(buglist.STATUS_CODES)
    assert issues.TERMINAL_STATUSES["todo"] <= set(todolist.STATUS_CODES)
    # (b) recorder 内联终态字面量 == issues.TERMINAL_STATUSES[pool]
    #     buglist 内联 {"FIXED","WONTFIX"} 应等于 issues.TERMINAL_STATUSES["bug"]
    assert {"FIXED","WONTFIX"} == issues.TERMINAL_STATUSES["bug"]
    assert {"DONE","WONTDO"} == issues.TERMINAL_STATUSES["todo"]
```

> 若三 recorder 无法直接 import（路径），用既有测试的 import 机制（importlib.util.spec_from_file_location）。

- [ ] **Step 2: 跑测试** — `pytest sdflow-issues/tests/test_issues.py -k terminal_sets -v` → 现状应 PASS（守卫就位）；若红说明已漂移、先对齐常量再绿。

- [ ] **Step 3: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task6 "T3 终态集跨脚本+内联字面量一致性守卫测试（按 pool dict 索引）"
```

---

### Task 7: T4 `batch add --if-exists skip`（skip-with-warn）+ rename auto-reindex（失败吞-warn）

**Files:**
- Modify: `sdflow-issues/scripts/issues.py`（`cmd_batch_add` 加 `--if-exists`；`cmd_batch_rename` 末尾 auto-reindex；argparse）
- Test: `sdflow-issues/tests/test_issues.py`

- [ ] **Step 1: 写失败测试**

```python
def test_batch_add_if_exists_skip_warns_and_noops(tmp_path):
    # add key 两次，第二次 --if-exists skip → exit 0 + stderr 含"已存在""忽略"，条目未变
    ...
def test_batch_add_if_exists_skip_ignores_fields_no_die(tmp_path):
    # add key，再 add key --优先级 P1 --if-exists skip → exit 0（不比较字段、不 _die）+ warn
    ...
def test_batch_rename_auto_reindex_refreshes_index(tmp_path):
    # rename 后 INDEX.md 已含 new_key 成员（自动 reindex）
    ...
def test_batch_rename_reindex_failure_warns_but_rename_exit0(tmp_path, monkeypatch):
    # monkeypatch reindex 抛异常 → rename 仍 exit 0 + stderr 含"INDEX 未刷新"
    ...
```

- [ ] **Step 2: 跑证失败** — `-k "if_exists or auto_reindex or reindex_failure"` → FAIL

- [ ] **Step 3: 实现**

`cmd_batch_add` argparse 加 `--if-exists` (`choices=["skip"]`, default None)。撞 key 分支改为：

```python
    if _batch_entry_exists(lines, args.key):
        if getattr(args, "if_exists", None) == "skip":
            print(f"batch key 已存在，--if-exists skip：no-op，字段参数被忽略：{args.key}", file=sys.stderr)
            return   # exit 0，不比较字段、不解析人写行
        _die(f"批次 key 已存在：{args.key}（…既有文案…）")
```

`cmd_batch_rename` 成功写盘后：

```python
    try:
        _reindex_inline(root)   # 或调既有 reindex 逻辑
    except Exception as e:
        print(f"rename 已生效，但 INDEX 未刷新（请手动 reindex）：{e}", file=sys.stderr)
    # rename 本体 exit 0（不因 reindex 失败反噬）
```

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-issues/tests/test_issues.py -v` → 全绿

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task7 "T4 batch add --if-exists skip=skip-with-warn + rename auto-reindex(失败吞-warn+exit0)"
```

---

### Task 8: T5 `_find_row_file` 各 recorder 内抽 + 分支补测

**Files:**
- Modify: `sdflow-buglist/scripts/buglist.py`（抽 `_find_row_file`，`cmd_set_status`/`cmd_triage` 复用）
- Modify: `sdflow-todolist/scripts/todolist.py`（镜像）
- Test: 两 recorder tests（WONTDO / 0 成员 IN_PROGRESS 分支）

- [ ] **Step 1: 写测试（分支补测 + 去重后行为不变）**

```python
def test_set_status_wontdo_branch(tmp_path): ...   # todolist WONTDO
def test_batch_set_status_zero_member_in_progress(tmp_path): ...  # 0 成员人标 IN_PROGRESS
```

- [ ] **Step 2: 跑证失败/现状** — 分支测试 → 若现状已覆盖则记明；去重是重构，重构后既有测试须仍绿

- [ ] **Step 3: 实现 `_find_row_file` 抽取**

buglist：把 `cmd_set_status` 与 `cmd_triage` 里"定位含某 ID 行的 dated 文件 + 行号"的重复逻辑抽成 `_find_row_file(root, item_id) -> (path, lines, line_idx, sec)`，两处调用之。todolist 镜像（各自内抽、不跨 recorder 共享，D4）。

- [ ] **Step 4: 跑证通过 + 回归** — `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ -v` → 全绿（去重无行为回归）

- [ ] **Step 5: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task8 "T5 _find_row_file 各 recorder 内抽 + WONTDO/0成员IN_PROGRESS 分支补测"
```

---

### Task 9: doc-sync（rename 契约变更同步三 recorder SKILL.md）

**Files:**
- Modify: `sdflow-issues/SKILL.md`（rename 段补"末尾自动 reindex" + 订正 :90-91"无副作用"过时措辞）
- Modify: `sdflow-buglist/SKILL.md:182`、`sdflow-todolist/SKILL.md:191-192`（补"（含 auto-reindex）"）

- [ ] **Step 1: 改 SKILL.md 文案**

按 Task 7 落地的 rename auto-reindex 行为，同步三处 SKILL.md（纯文档，无测试）。删除/订正 `sdflow-issues/SKILL.md` 中"rename 不该有副作用"的过时句。

- [ ] **Step 2: Commit**

```bash
~/.sdflow/hack/checkpoint-commit.sh task9 "doc-sync：三 recorder SKILL.md rename 段同步 auto-reindex（订正无副作用过时措辞）"
```

---

### Task 10: 收尾验证

**Files:** 无（验证 + 状态回写）

- [ ] **Step 1: 全套件绿** — `pytest` （仓根，全量）→ 0 failed

- [ ] **Step 2: 诚实核验** — 确认 proposal/adr **未**把 D2"堵非交互静默蒸发"记成本 change 达成（`--strict` 无消费者）

- [ ] **Step 3: delta 对码核验** — `specs/spec-workflow/spec.md` 两 ADDED 需求（T2/T1）与实现逐条对齐，无悬空 Scenario

- [ ] **Step 4: Commit（若有验证性微调）**

```bash
~/.sdflow/hack/checkpoint-commit.sh task10 "收尾验证：全套件绿 + 诚实核验 + delta 对码"
```

> T1-T5 标 DONE、follow-up（T2.5 sweep 用 --strict + roadmap 去字符串化机器状态层）交 `/sdflow-done` 的 hand-off/sweep 处理，不在本 plan。

---

## Self-Review

- **Spec 覆盖**：T2(Task1-4 含 C1/OV-2/OV-3) · T1(Task5 含 OV-1) · T3(Task6) · T4(Task7) · T5(Task8) · doc-sync(Task9,C8) · 收尾(Task10)。spec delta 两 ADDED 需求（T2 table-cell-safe / T1 reindex 可观测+scan arity）均有对应任务。
- **无 placeholder**：守卫 helper、skip-with-warn、scan arity、id 校验均给了真实代码骨架 + 精确函数/行号锚。测试骨架标注了"照既有 test 风格"（实现者读既有 test_*.py 即知调用机制）。
- **类型一致**：`_reject_cell_unsafe(value, field)` / `_reject_batch_key_unsafe(key)` 命名跨任务一致；`_scan_pool` 返回签名变更（Task5）已标同步调用点 `cmd_batch_rename`。
