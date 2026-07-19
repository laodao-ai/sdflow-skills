# Task 4 双轴审 fix1 —— argv 分派 helper 面级上提 + 假绿防回归机械守

基线 HEAD = `29bf7a5`（全套件 1864 passed / 3 skipped / 3 xfailed）。
本次只动 `sdflow-issues/tests/` 下的文件，未碰 `scripts/`、未碰 change 四件套、未在仓根建 `conftest.py`。

---

## I1（基准 3 · 面治）argv 分派逻辑 7 份手抄 → 单一源

### 站点实测清单与逐处处置

扫描口径：`grep -n 'setattr(.*"run"' sdflow-issues/tests/*.py`，全目录 **16 个** `subprocess.run` 补桩站点（不止 prompt 估计的 7 处 —— 面治要求扫全目录，故把 `test_repo_root_identity_issues.py` 的 4 处一并纳入判定面）。

| 文件 | 原行号 | 所在 def | 原形态 | 处置 |
|---|---|---|---|---|
| `test_issues.py` | 341 | `test_falls_back_to_abspath_when_git_command_raises` | 整体替换 `boom` | **保持不动**（故意且正确：被测对象就是 `repo_root` 的 git 失败回落分支，劫持 git 是断言本体）→ 进白名单 |
| `test_issues.py` | 408–417 | `test_read_pool_raises_runtime_error_when_subprocess_exits_nonzero` | 手抄 `real_run` + `if "scan" in cmd` | → `scan_only_run(...)` fixture |
| `test_issues.py` | 1605–1617 | `test_sweep_scan_fail_closed` | 手抄，判据 `"scan" in cmd` | → `dispatch_run(argv_contains("scan"), …)` |
| `test_issues.py` | 1638–1650 | `test_sweep_batch_add_fail_closed` | 手抄，`"batch" and "add"` | → `dispatch_run(argv_contains("batch", "add"), …)` |
| `test_issues.py` | 1670–1682 | `test_sweep_triage_fail_closed` | 手抄，`"triage" and "B2"` | → `dispatch_run(argv_contains("triage", "B2"), …)` |
| `test_issues.py` | 1705–1717 | `test_sweep_rerun_converges` | 手抄，`"triage" and "B2"` | → 同上 |
| `test_issues.py` | 1749–1761 | `test_sweep_reindex_fail_closed` | 手抄，`"reindex" in cmd` | → `dispatch_run(argv_contains("reindex"), …)` |
| `test_task4_rename_snapshot.py` | 25–50 | 模块级 `_is_recorder_scan` / `_scan_only_run` | 本地 helper 定义 | **上提到 `conftest.py`**，本地定义删除、留一行指针注释 |
| `test_task4_rename_snapshot.py` | 167 / 195 / 253 / 304 | 4 个用例 | `_scan_only_run(...)` | → `scan_only_run(...)` fixture（各自签名加 fixture 形参） |
| `test_task4_rename_snapshot.py` | 810 | `test_batch_rename_uses_direct_snapshot_zero_recorder_scans…` | `observe_run` | **保持不动**（全量透传的观察器，只记 argv 不返回替身，无劫持面）→ 进白名单 |
| `test_repo_root_identity_issues.py` | 83 / 93 / 485 / 518 | `_fake_git_stdout` / `_forbid_subprocess` / `test_timeout_raises_and_does_not_fall_back` / `test_timeout_with_real_hanging_git` | 整体替换 | **保持不动**（被测对象即 `repo_root` 对 git 的调用/超时行为，劫持是断言本体；518 那处本就是全量透传只压 timeout）→ 进白名单 |

**净结果**：6 处手抄补桩 + 1 份本地 helper → 收敛到 `sdflow-issues/tests/conftest.py` 一个源；6 处保持不动的均**显式登记 + 写明理由**，不靠模式碰巧漏掉。

### 新建 `sdflow-issues/tests/conftest.py`

- `make_dispatch_run(predicate, handler)` —— 底层工厂，构造时捕获 `real_run = issues_mod.subprocess.run`，替身签名 `(command, *args, **kwargs)` **全透传**（**Minor S3** 一并修掉：原 `test_issues.py` 写的是 `fake_run(cmd, **kwargs)`，吞掉位置参数，将来以位置方式传 `capture_output` 会 `TypeError`）。
- `is_recorder_scan(command)` / `argv_contains(*tokens)` —— 判据。
- fixtures：`dispatch_run` / `scan_only_run` / `argv_contains`（工厂型 fixture，避免 `import conftest` 的 sys.path 脆性）。
- 模块 docstring 收录假绿机理（原 `_scan_only_run` 的 docstring 原文承接）。
- 顶部明确注明**只服务 `sdflow-issues/tests/`，与 Task 5 的仓根 conftest 无关**。

---

## I2（基准 1 · 机械化优先）假绿防回归：散文 → `ast` 机械守

新增 `sdflow-issues/tests/test_patch_discipline.py`（7 个用例）。**用 `ast`，零正则、零 grep**（基准 5）。

### 判据设计

**门 A（站点形态）** —— AST 找 `monkeypatch.setattr(<expr>, "run", <value>)` 且 `<expr>` 属性链末段为 `subprocess` 的调用；要求 `<value>` 是对 `dispatch_run` / `scan_only_run` / `make_dispatch_run` 的 `ast.Call`，否则该站点的 `(文件名, 词法最内层 def 名)` MUST 命中 `INTENTIONAL_WHOLESALE_PATCHES` 白名单，且白名单值（理由字符串）非空。**新增站点默认红** —— 这是「显式登记豁免」而非「模式碰巧漏掉」，符合 prompt 要求。

**门 B（工厂本体）** —— 解析 `conftest.py` 的 `make_dispatch_run`：MUST 有 `real_run = …` 捕获；内层 `run` MUST 含 `ast.If`（条件分派）；`run` 的**尾语句** MUST 是 `return real_run(command, *args, **kwargs)`（`ast.Starred` + `keyword(arg=None)` 双查，顺带机械锁死 S3 的全透传签名）。

**为什么必须有门 B**：门 A 只看调用形状。把工厂内部改成无条件返回替身，**所有站点的调用形状一字不变**，假绿全面回归而门 A 全绿。门 B 正是 prompt 指定的那个变异（「把 `_scan_only_run` 改回整体替换形态」）的接住点。

**自检用例** `test_patch_sites_exist_at_all`：断言扫描器确实找到 ≥10 个站点 —— 否则「零违规」可能只是选择器写错了（防守护自身假绿）。

### 诚实的能力边界声明

**守得住**：① 站点回退成裸 lambda / 局部 `fake_run`；② 新增未登记的补桩站点；③ 工厂本体被「简化」成无条件返回替身（透传分支消失）；④ 工厂替身签名被改成写死关键字（S3 回归）。

**守不住**（如实登记，不假装全覆盖）：
- **判据函数本身写错**：如 `argv_contains()` 传空 tokens ⇒ `all([])` 恒真 ⇒ 语义上等价整体替换。这是**语义**正确性、无确定性信号（基准 1 的合法残余），留给用例自身断言与评审。
- **绕开 `monkeypatch.setattr` 的补桩路径**：直接赋 `issues_mod.subprocess.run = …`、`unittest.mock.patch`。目前本目录**零使用**（已核实），门 A 不覆盖；新引入这类路径需扩门。这是我按基准 5 的取舍——不为一个当前不存在的形态去堆分支。
- **白名单条目的理由是否仍然成立**：人读注记，非机械信号。
- 覆盖面**仅 `sdflow-issues/tests/`**（本次 scope）。

### 变异确认（PV 规则 5）—— 两次实际输出

**M1：把 `conftest.make_dispatch_run` 改回整体替换形态**（删 `real_run` 捕获、内层 `run` 无条件 `return handler(command)`）

```
=== MUTATION M1: 工厂改回整体替换 ===
>       assert captures_real_run, "make_dispatch_run MUST 先捕获真实 subprocess.run 为 real_run"
E       AssertionError: make_dispatch_run MUST 先捕获真实 subprocess.run 为 real_run
E       assert False
sdflow-issues/tests/test_patch_discipline.py:158: AssertionError
FAILED test_patch_discipline.py::test_gate_b_dispatch_factory_keeps_conditional_passthrough
1 failed, 6 passed in 0.07s
```

同一变异下顺带跑了 `test_task4_rename_snapshot.py`：`4 failed, 87 passed` —— 即 Task 4 加固过的 4 个 CLI 诊断用例能自己察觉，但**其余用例（如 `test_reindex_consumer_drift_preserves_existing_index_and_batches`）仍全绿**，正是「用例断言分辨不出的那部分假绿」。这恰好量化了门 B 的增量价值：它接住的是用例自身接不住的那一半。

**M2：把单个站点回退成局部整体替换**（`test_sweep_reindex_fail_closed` 改回 `def fake_run(cmd, **kwargs): return _FakeFailProc()`）

```
=== MUTATION M2: 单站点回退成局部整体替换 ===
E       AssertionError: 整体替换 subprocess.run 会连带劫持被测函数之外的子进程（含 repo_root 的 git 探测），
        用例退化为假绿。请改用 conftest 的 dispatch_run / scan_only_run，或把该站点显式登记进
        INTENTIONAL_WHOLESALE_PATCHES 并写明理由。违规站点：test_issues.py:1749 (in test_sweep_reindex_fail_closed)
E       assert not ['test_issues.py:1749 (in test_sweep_reindex_fail_closed)']
FAILED test_patch_discipline.py::test_gate_a_…_dispatch_factory[test_issues.py]
1 failed, 6 passed in 0.07s
```

**两次变异均已还原**，还原后 `test_patch_discipline.py` = `7 passed`。

---

## 全套件结果

```
/usr/bin/python3 -m pytest -q -p no:cacheprovider
1871 passed, 3 skipped, 3 xfailed in 116.59s
```

- **0 failed** ✅
- 1864 → **1871**（+7 = 新增 `test_patch_discipline.py` 的 7 个用例），无用例丢失
- `3 skipped` / **`3 xfailed` 原样保留** ✅（3 个 `xfail(strict=True)` 锚未被触碰）
- 三份 AST 镜像：`sdflow-buglist/tests/test_mirror_consistency.py` = `7 passed` ✅
- 仓根无 `{` 开头目录 ✅（`ls -d '{'*` → no matches）
