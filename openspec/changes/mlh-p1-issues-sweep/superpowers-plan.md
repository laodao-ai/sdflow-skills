# issues.py sweep 原子子命令 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 `issues.py` 加 `sweep --change X` 原子子命令，把 sdflow-done §2.1 的手跑 4 步 issues 分诊循环固化为一次确定性、fail-closed、可重跑收敛的操作。

**Architecture:** sweep 是既有原语的确定性拼装，**全部子步走 subprocess CLI**（不直调 cmd_* 函数）：入口守卫 change → `scan --open-ungrouped` 扫两池 → 逐项 `triage`（查 returncode）→ `batch add --if-exists skip` → `reindex`。非原子、fail-closed、部分失败重跑收敛。

**Tech Stack:** Python 3 + argparse + subprocess + pytest。改 `sdflow-issues/scripts/issues.py` + `sdflow-issues/tests/test_issues.py` + 2 个 SKILL.md。

## Global Constraints

- **数据类纪律**：改 `scripts/` MUST 跑 `pytest sdflow-issues/tests/`（每任务收尾必绿）。
- **TDD**：每个行为先写失败测试 → 实现 → 跑绿。
- **全子步 subprocess CLI**：sweep 调 scan/triage/batch add/reindex 一律用完整 CLI subprocess（带全参数），**不直调 cmd_***（避 `getattr(args,"优先级")` 无默认→AttributeError，及 `_scan_pool` 硬编码无过滤）。
- **扫描口径 `--open-ungrouped`**（设计门 Q1=A）：`scan --change X --open-ungrouped --json` = 源==X ∧ 非终态 ∧ 批次空。**MUST NOT 用 `--status OPEN`**。
- **`batch add` MUST 带 `--if-exists skip`**（默认是 `_die` 报错，不带则幂等重跑破产）。
- **入口守卫先于任何写盘**：`args.change` 非空（strip 后）+ 过 `_reject_batch_key_unsafe`（拒 `|`/换行/` — `/首尾空白）。防空 change 误纳孤儿（致命）。
- **逐项 triage 查 returncode**：非零即中止 + stderr 报明失败点位（第 i 项/pool/已 tag 的 id 列表）。fail-closed。
- **非原子 + 重跑收敛**：措辞/语义对齐 `cmd_batch_rename` D6；末步 reindex 失败也 fail-closed（区别于 rename 的 warn-only）。
- **checkpoint 格式**：每任务收尾 commit 步 MUST 用 `~/.sdflow/hack/checkpoint-commit.sh task<N>-<slug> "..."`（**task 号后紧跟横杠**，否则 ship_gate TAG_RE 不匹配、gate 卡 0/N）。

---

### Task 1: `issues.py sweep` 子命令 + 测试（TDD）

**Files:**
- Modify: `sdflow-issues/scripts/issues.py`（加 `cmd_sweep` + `main()` 注册 subparser）
- Test: `sdflow-issues/tests/test_issues.py`（加 sweep 用例组）

**Interfaces:**
- Consumes（既有原语，均已核验存在）：`_reject_batch_key_unsafe(key)`(issues.py:324) · `repo_root`/`atomic_write` · buglist.py/todolist.py 的 `scan --change X --open-ungrouped --json`（输出键 `bugs`/`items`，每项含 `id`）与 `triage --id --批次`（幂等：已 PROPOSED/终态 no-op）· `issues.py batch add X --if-exists skip`（issues.py:906，choices=["skip"]）· `issues.py reindex`。
- Produces：`cmd_sweep(args)` + `sweep` subparser（`--change` required、`--root` 缺省）。

- [ ] **Step 1: 写失败测试 `test_sweep_open_ungrouped`**

```python
def test_sweep_open_ungrouped(tmp_path):
    root = _init_repo(tmp_path)  # 复用本测试文件既有的仓初始化 helper
    # 造 源==X ∧ 批次空 的 bug（OPEN）+ todo（OPEN），另造一个 IN_PROGRESS bug（非终态非 OPEN）
    _add_bug(root, id="B1", change="chg-x", status="OPEN")
    _add_bug(root, id="B2", change="chg-x", status="IN_PROGRESS")
    _add_todo(root, id="T1", change="chg-x", status="OPEN")
    rc = _run_issues(root, "sweep", "--change", "chg-x")
    assert rc == 0
    # 全部非终态未分批项进批次 chg-x（含非 OPEN 的 B2）
    for iid in ("B1", "B2", "T1"):
        assert _batch_of(root, iid) == "chg-x"
        assert _status_of(root, iid) == "PROPOSED"
    assert _batch_entry_exists(root, "chg-x")      # batches.md 有 PLANNED 条目
    assert _index_lists(root, "chg-x")             # INDEX.md 刷新
```

- [ ] **Step 2: 跑测试确认 FAIL**

Run: `pytest sdflow-issues/tests/test_issues.py::test_sweep_open_ungrouped -v`
Expected: FAIL（`sweep` 子命令不存在 / argparse 报错）

- [ ] **Step 3: 实现 `cmd_sweep` + 注册 subparser**

在 `issues.py` 加（要点，非逐字）：
```python
def cmd_sweep(args):
    root = repo_root(args.root)
    change = (args.change or "").strip()
    if not change:
        _die("sweep --change 不可为空（防空 change 误纳孤儿）")
    _reject_batch_key_unsafe(change)              # 拒 |/换行/ — /首尾空白，先于任何写盘
    tagged = []                                   # 已成功 tag 的 id（失败报点位用）
    for script, pool, idkey in ((BUGLIST_SCRIPT,"bug","bugs"), (TODOLIST_SCRIPT,"todo","items")):
        proc = subprocess.run([sys.executable, script, "--root", root, "scan",
                               "--change", change, "--open-ungrouped", "--json"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            _die(f"sweep: {pool} scan 失败 (rc={proc.returncode}): {proc.stderr.strip()}")
        items = json.loads(proc.stdout).get(idkey, [])
        for it in items:
            iid = it["id"]
            tp = subprocess.run([sys.executable, script, "--root", root, "triage",
                                 "--id", iid, "--批次", change], capture_output=True, text=True)
            if tp.returncode != 0:
                _die(f"sweep: triage 失败于 {pool} 第 {iid} 项 (rc={tp.returncode}); "
                     f"已 tag={tagged}: {tp.stderr.strip()}")
            tagged.append(iid)
    # batch add（MUST --if-exists skip）
    ba = subprocess.run([sys.executable, __file__, "--root", root, "batch", "add",
                         change, "--if-exists", "skip"], capture_output=True, text=True)
    if ba.returncode != 0:
        _die(f"sweep: batch add 失败 (rc={ba.returncode}): {ba.stderr.strip()}")
    ri = subprocess.run([sys.executable, __file__, "--root", root, "reindex"],
                        capture_output=True, text=True)
    if ri.returncode != 0:
        _die(f"sweep: reindex 失败 (rc={ri.returncode}): {ri.stderr.strip()}")
    print(f"sweep {change}: tagged {len(tagged)} 项 {tagged}")
```
在 `main()` 注册：`sw = sub.add_parser("sweep", help="原子分诊本 change 未分批非终态项入批次"); sw.add_argument("--change", required=True); sw.add_argument("--root", default="."); sw.set_defaults(func=cmd_sweep)`。
（核实 `batch add` 子命令的 `--if-exists` 实参名与 subparser 定义一致；核实 `sys`/`json`/`subprocess` 已 import。）

- [ ] **Step 4: 跑测试确认 PASS** — `pytest ...::test_sweep_open_ungrouped -v` → PASS

- [ ] **Step 5: 幂等测试 `test_sweep_idempotent`** — 同 change 连跑两次，第二次 rc==0、triage no-op、batch add skip no-op、盘面无净变化。写→跑→PASS。

- [ ] **Step 6: 空 change 守卫 `test_sweep_rejects_empty_change`** — 造一个源为空的孤儿 OPEN 项；`sweep --change ""`（及 `"  "`/`"a — b"`/`"a|b"`/含换行）→ rc!=0 且 dated 文件无改动、孤儿未进任何批次。写→跑→PASS。

- [ ] **Step 7: 孤儿排除 `test_sweep_excludes_orphans`** — 合法非空 change 下池含源为空孤儿，sweep 后孤儿未进批次 X。写→跑→PASS。

- [ ] **Step 8: triage 失败 fail-closed `test_sweep_triage_fail_closed`** — 注入某项 triage 非零（喂不存在 id / monkeypatch subprocess.run 对 triage 返 rc=1），断言 sweep rc!=0 + stderr 含失败点位（pool/id/已 tag 列表）。写→跑→PASS。

- [ ] **Step 9: 部分失败重跑收敛 `test_sweep_rerun_converges`** — 注入第 k 项失败 → 前 k-1 已 tag；移除注入后重跑 sweep → 全部 tag + batches.md 建 + INDEX 刷新，已 tag 项未被重复 triage（batch 空过滤排除）。写→跑→PASS。

- [ ] **Step 10: reindex 致命 fail-closed `test_sweep_reindex_fail_closed`** — reindex 步致命错误 → sweep rc!=0（末步也 fail-closed，区别 rename warn-only）。写→跑→PASS。

- [ ] **Step 11: 全套件绿** — Run: `pytest sdflow-issues/tests/` → all pass。

- [ ] **Step 12: checkpoint**

```bash
~/.sdflow/hack/checkpoint-commit.sh task1-sweep "issues.py sweep 原子子命令 + 守卫/幂等/孤儿/fail-closed/收敛测试"
```

---

### Task 2: SKILL 文档同步

**Files:**
- Modify: `sdflow-done/SKILL.md`（§2.1 sweep 子步）
- Modify: `sdflow-issues/SKILL.md`（命令面「共享」段）

**Interfaces:** Consumes Task 1 的 `issues.py sweep --change X` CLI。

- [ ] **Step 1: `sdflow-done/SKILL.md` §2.1** — 把手写 4 步循环（scan 两池 → 逐项 triage → batch add → reindex）替换为一行：
  `python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . sweep --change {change_name}`
  保留边界声明：「孤儿项(源="")不归本 sweep，交 `scan --open-ungrouped` 兜底」+「显式传 --change 不靠 detect_change 猜」(D4) +「调用方 MUST 串行、勿与手动 triage 交叉」(D6)。

- [ ] **Step 2: `sdflow-issues/SKILL.md`** — 命令面「共享」段（reindex/batch 附近）补 `sweep --change X` 文档：`--open-ungrouped` 口径（非终态∧批次空）、`--if-exists skip` 幂等、空 change 守卫、非原子 fail-closed 重跑收敛、D6 串行边界。

- [ ] **Step 3: checkpoint**

```bash
~/.sdflow/hack/checkpoint-commit.sh task2-docsync "sdflow-done §2.1 + sdflow-issues 命令面同步 sweep"
```

---

## Self-Review
- **Spec coverage**：spec-workflow「issues sweep 原子子命令」4 场景 → 全部有测试（open-ungrouped 口径=Step1.1、幂等 exit0=1.5、空 change 守卫=1.6、triage 失败 fail-closed+收敛=1.8/1.9）。✓
- **Placeholder scan**：无 TBD/TODO；测试/实现均给具体代码骨架。✓
- **Type consistency**：`cmd_sweep`/subparser 名一致；subprocess CLI 参数名与既有子命令定义对齐（实现时核 `--if-exists`/`--open-ungrouped` 实参名）。✓
- **checkpoint 格式**：`task1-sweep`/`task2-docsync` 均含横杠（TAG_RE 匹配）。✓
