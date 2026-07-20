# Task 2 · git 调用失败一律落在退出码契约内，且带可行动诊断

**R-ID**: R5 ｜ **范围**: tasks 3.1–3.6 + 测试 5.8 / 5.9a / 5.9b / 5.9c ｜ **产物**:
`sdflow-ship/scripts/ship_gate.py`、`sdflow-ship/tests/test_gate_git_layer.py`（新增，27 用例）

## 做了什么

三个 git helper（`run_git` / `run_git_rc` / `run_git_bytes`）此前是三处**裸 `subprocess.run`**：
无 timeout、无异常捕获、不清 env。`OSError`（git 不在 PATH / 不可执行 / 权限不足）与
`TimeoutExpired`（文件系统挂起）会直接逸出，落成 Python 默认退出码 **1** —— **契约集 `{0,3,4,5,6}` 之外**，
`/sdflow-ship` 链序对它没有处置路径。

改动四件：

1. **单出口 `_git_run(root, args, text)`**（`ship_gate.py:232`）——三个 helper 唯一的 subprocess 出口，
   统一 `timeout` + env 清理 + 环境级失败映射。三个 helper 只剩各自的语义壳
   （text/strip vs 原始字节）。
2. **`GIT_TIMEOUT_SECONDS = 30`**（`:212`）——ADR-5 取值理由（对齐 `buglist.py::repo_root`：
   纯本地元数据查询，30s 是**文件系统卡死判定线、不是性能预算**；聚合上界数量级 ≈ 2 分钟）
   写在常量注释里。
3. **`_git_env()`**（`:215`）——`os.environ.copy()` 后剔除 `GIT_` **前缀全集**，其余原样透传（denylist）。
4. **`main()` 的 try 覆盖整个函数体**（`:1554`）——**仓根解析（`rev-parse --show-toplevel`）
   本身就是一次 git 调用**，Task 1 时它落在 try 之外。

**顺带**：`_GIT_HARDEN` 的注释按 tasks 3.4 改写为「中和一切能改变判定输入的外部可控态」，
显式点出 config 面（`-c`）与环境面（`_git_env`）两半。

## 逐条验收标准 → 证据锚点

| 验收标准 | 证据 |
|---|---|
| 三个 helper 各自在 `OSError` 下得到受控结果（三组独立验证） | `test_oserror_is_controlled_per_helper[run_git\|run_git_rc\|run_git_bytes]`；另有 `test_permission_error_is_controlled_per_helper[×3]` 覆盖 `PermissionError`（OSError 另一子类）。**真实手段构造**（PATH 里没有 git / git 不可执行），非打桩 |
| 三个 helper 各自在超时下得到受控结果（三组独立验证），上界取值理由写在注释里 | `test_timeout_is_controlled_per_helper[×3]`（注入，跨平台）+ `test_real_hang_times_out_per_helper[×3]`（真实 fake-git 挂起，POSIX）+ `test_timeout_bound_is_the_shared_constant[×3]`（断言传进 subprocess 的 timeout 就是那个常量）。理由注释 `ship_gate.py:206-212` |
| 顶层入口映射 `UNKNOWN(6)`，五类诊断彼此可区分 | `test_main_maps_git_unavailable_to_unknown`、`test_main_maps_git_unavailable_during_repo_root_resolution`、`test_main_maps_timeout_to_unknown`（均经 `main()` 公共入口，断 `cause_category`）；`test_five_causes_give_distinguishable_advice`（六类两两不同，且逐条断各自专属措辞） |
| 已知会扭曲判定的 git 环境变量被剔除后结论与干净环境一致；非 `GIT_` 前缀原样透传 | `test_verdict_is_identical_under_polluted_git_env[fresh\|stale]`（端到端跑脚本，污染集 = `GIT_ICASE_PATHSPECS` / `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` / `GIT_CONFIG_GLOBAL` / `GIT_LITERAL_PATHSPECS` + 仓 config `diff.ignoreSubmodules=all`）；`test_git_prefixed_vars_are_stripped_from_subprocess_env`；透传半场 `test_non_git_prefixed_vars_pass_through`（**行为级**探针：`XDG_CONFIG_HOME` 真的被 git 读到）+ `test_env_is_a_denylist_not_an_allowlist`（剔除面**恰好等于** `GIT_` 前缀集） |
| 退出码始终落在契约集内 | `test_exit_code_stays_in_contract_under_git_failures`（真跑脚本，断 `code in {0,3,4,5,6}`） |
| 每条新增守卫各附一次变异证明 | 下节，8/8 全红 |

**额外一条守卫**（非验收项，属基准 3 面治）：`test_all_git_calls_go_through_the_single_hardened_entry`
——加固靠单出口保证，新增裸 `subprocess.run` 调用点 = 一条没被加固的通路，机械守住（源码中
`subprocess.run(` 恰好出现 1 次）。

## 变异证明（8 条，逐条实测）

跑法：把守卫改坏 → 跑对应用例 → 记录变红 → 还原。**MUST NOT 以「用例存在且为绿」充当证明。**

| # | 变异 | 结果 |
|---|---|---|
| M1 | 删 `_git_run` 的 `except OSError` 子句 | **8 failed** — `test_oserror_is_controlled_per_helper[×3]`、`test_permission_error_is_controlled_per_helper[×3]`、`test_main_maps_git_unavailable_to_unknown`、`test_exit_code_stays_in_contract_under_git_failures`（报错：`FileNotFoundError: No such file or directory: 'git'` 直接逸出） |
| M2 | 删 `except subprocess.TimeoutExpired` 子句 | **7 failed** — `test_timeout_is_controlled_per_helper[×3]`、`test_real_hang_times_out_per_helper[×3]`、`test_main_maps_timeout_to_unknown` |
| M3 | 从 kwargs 里删 `"timeout": GIT_TIMEOUT_SECONDS`（回到无限等待） | **6 failed** — `test_timeout_bound_is_the_shared_constant[×3]`、`test_real_hang_times_out_per_helper[×3]`。⚠ 该轮耗时 61s（真实 fake-git 睡满 20s×3），正是「无上界」的直接观测 |
| M4 | 从 kwargs 里删 `"env": _git_env()`（不清 `GIT_*`） | **3 failed** — `test_git_prefixed_vars_are_stripped_from_subprocess_env`、`test_verdict_is_identical_under_polluted_git_env[fresh\|stale]` |
| M5 | `_git_env` 由 denylist 改成 allowlist（只留 `PATH`/`HOME`） | **2 failed** — `test_non_git_prefixed_vars_pass_through`、`test_env_is_a_denylist_not_an_allowlist` |
| M6 | 仓根解析挪回 `try` 之外（= Task 1 的原形态） | **1 failed** — `test_main_maps_git_unavailable_during_repo_root_resolution` |
| M7 | 超时文案回到硬编码 `>30s`（T194 原形态） | **1 failed** — `test_timeout_advice_interpolates_the_constant` |
| M8 | 在 `run_git` 里恢复一处裸 `subprocess.run`（绕过单出口） | **2 failed** — `test_all_git_calls_go_through_the_single_hardened_entry`、`test_oserror_is_controlled_per_helper[run_git]`（**只有 `run_git` 那一组红** ⇒ 证明三组是真独立、不是共用一条断言） |

还原后已复跑：`sdflow-ship/tests/` **345 passed**；仓根全套件 **2097 passed, 9 skipped, 3 xfailed**
（基线 2070 + 本票新增 27）。

## 关于「守卫计数」

tasks 5.14 的括注按「三处各自复制加固」估作 7 组独立守卫。本实现走**单出口**（`_git_run`），
守卫在源码上不是 7 份而是 4 处（OSError 子句 / Timeout 子句 / timeout 参数 / env 参数）
＋ main 的 try 边界 ＋ 文案插值 ＋ 单出口约束 = **8 条变异**，逐条实测。
**三处复制的方案被否**：三份拷贝必然漂移（`_GIT_HARDEN` 历史上正是靠单点注入才没漏），
且「新增 git 调用点忘了加固」这条失效模式在单出口下不存在——M8 就是把它机械焊住的那条守卫。
覆盖强度不减：**每个 helper 仍各有独立用例**（M8 证明了这三组不共用断言）。

## T194 的处置

T194（`ship_gate.py` 的 UNKNOWN advice 串硬编码 `>30s`，与本票引入的 timeout 常量天然漂移）
**已消**：`_INDETERMINATE_ADVICE[CAUSE_GIT_TIMEOUT]` 改为 f-string 插值 `GIT_TIMEOUT_SECONDS`
（`:1535`），并加机械守 `test_timeout_advice_interpolates_the_constant`
（断源码里不再有 `>30s` 字面量 + 文案确实随常量走）；变异 M7 证明该守卫承重。
按 ticket 要求**未改动 todolist 状态**，交编排层处置。

## 遇到的问题与决策

1. **fixture 顺序踩过一次真坑**：起初把「让 git 消失」写成 pytest fixture，它在 setup 阶段抢先生效
   ⇒ `approved_change` 建仓当场 `FileNotFoundError`——用例是红的，但**红在建仓、不在被测面**
   （典型的「红得不对」）。改为普通函数、在盘面建好之后显式调用。教训写进测试文件注释。
2. **构造 `PermissionError` 需要 PATH 里只留 shadow 目录**：POSIX 的 exec 搜索会**跳过不可执行项
   继续往后找**，把 shadow 目录追加在真 PATH 前面时找到的仍是真 git（实测），构造不出该异常。
3. **fake-git 里的 `sleep` 必须走绝对路径**：shadow 目录若成为唯一 PATH，`sleep` 会
   command-not-found 而秒退，用例照样「不抛异常」但原因与被测面无关（实测踩过，已固化进注释）。
4. **`run_git_bytes` 的「MUST NOT 复用 run_git/run_git_rc」如何解读**：该约束（来自
   `fix-design-gate-freshness-proxy`）针对的是**文本层语义**（text/errors/strip 四者各自可造假等值），
   不是 subprocess 调用本身。共用 `_git_run` 时本函数仍走 `text=False` 拿原始字节，语义无损。
   已在该函数 docstring 里显式登记这一读法，防后续维护者误判为违规。
5. **跨平台**：`chmod` 权限位与 `#!/bin/sh` fake git 仅 POSIX 成立 ⇒ 两组「真实手段」用例
   `skipif(os.name != "posix")`；但**同一守卫另有跨平台的注入式用例覆盖**（`test_timeout_is_controlled_per_helper`
   / `test_oserror_is_controlled_per_helper` 用 PATH 清空，Windows 同样成立）⇒ Windows runner 上守卫不失守。

## Concerns

- **`diff.ignoreSubmodules=all` 只在 5.8 的端到端一致性用例里被覆盖，未单独立守**：本票不改
  config 面（`_GIT_HARDEN` 的 `-c` 注入），且 ADR-2 的新判定路径已不调 `diff`
  ⇒ 该 config 的直接利用面随 Task 3/4 落地而消失。此处只保证「它在也不改变结论」。
- **`CAUSE_READ_FAILED` 的生产触发点尚未接入**（design 组件表标 Task3/4）：本票只验它的
  诊断文案与其余四类可区分，未验它在真实读失败路径上被抛出——那属 Task 3/4 的覆盖面。
