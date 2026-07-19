---
ship-gate:
  verify: PASS
---

# verify-report — harden-repo-root-fail-closed

**结论：PASS** —— 核心交付（`repo_root` 身份校验 fail-closed · 单点解析 · 假绿消除 · cwd 泄漏回归断言）全部落地并有可机验锚点；全仓 `1910 passed / 9 skipped / 3 xfailed / 0 failed`。**存在一条 spec MUST 未达成（R2 Scenario 3，B15），判为「可接受的已知缺口」而非核心缺失——理由与归档硬条件见 §4.1。**

> 本报告独立核对代码与测试，不采信 `impl-reports/` 与 `code-review-report.md` 的措辞。每条 ✅ 附文件:行 / 测试名 / commit。

---

## 1. 独立执行的验证动作（本次 verify 亲自跑的）

| 动作 | 结果 |
|---|---|
| `find . -maxdepth 1 -name '{*'` | **无输出**（Task 0.1/0.2/4.1 闭环） |
| `ast.walk` 统计三份 `repo_root` Call 节点 | `issues.py:2518` / `buglist.py:1795` / `todolist.py:1769` —— **各 1 处，合计 3**（期望值 3，符合 1.2） |
| `pytest sdflow-{issues,buglist,todolist}/tests` | `603 passed / 7 skipped / 3 xfailed` |
| 干净临时目录跑 `pytest <abs>/sdflow-issues/tests/` | `269 passed / 1 xfailed`，**目录条目数 = 0**（Task 4.2 锚，本次亲验） |
| 全仓 `pytest` | `1910 passed / 9 skipped / 3 xfailed / **0 failed**` |
| **变异验证（主防线）**：把 `buglist.py` 步骤⑦ `if common != normcase(top_real)` 改成 `if False` | `test_core_worktree_redirect_is_rejected` + `test_ancestor_check_independently_catches_unsanitized_env` **双双变红** ⇒ 祖先校验的测试锚是真的（已还原，`git diff` 干净） |
| 重跑面治扫描 `grep -rln "show-toplevel" --include="*.py" --include="*.sh"`（排除 `.git/`/`tests/`/`openspec/changes/`） | **命中 8 个文件**，与 proposal:59-62 声明一致（Task 4.7 要求的是「重跑扫描」而非「核对自洽」，此处按要求重跑） |

---

## 2. tasks.md 逐项核对（33 项）

| 任务 | 代码出处 / 锚点 | 状态 |
|---|---|---|
| 0.1 删 4 棵 JSON 命名垃圾树 | commit `318f79f`；本次复跑 `find` 无输出 | ✅ |
| 0.2 确认干净 | 同上，本次亲验 | ✅ |
| 1.1 六步（现为**九步**）身份校验三份同步 | `buglist.py:581-788` / `todolist.py:581-788` / `issues.py:1132-1341`；`try` 仅包 `subprocess.run`（:664-681）、`TimeoutExpired` 单独 raise（:671）、无 `except Exception`、`ascii(...)[:200]` 截断、`discovery_env`/`git_timeout` 为**函数体内局部常量**（:613-618, :663）、raise 消息不含脚本名 | ✅（**实现比 spec 严**，见 §4.3） |
| 1.2 单点解析，Call 节点 19→3 | 本次 `ast.walk` 实测 = 3；commit `7a5c54e`；`test_repo_root_is_resolved_once_per_process_and_only_in_main`（三份各一） | ✅ |
| 1.2b 同步 docstring | `buglist.py:588-608`（已描述 ADR-5 单点解析 + 九步判据 + 回落新契约） | ✅ |
| 1.2c `--root` 默认 `None` | `issues.py:2459` / `buglist.py:1755` / `todolist.py:1728`；`test_root_argparse_default_is_none` | ✅ |
| 1.3 形状负例（非绝对/不存在/空/空白/末尾空格/多行）+ 断言未创建 | `test_shape_negatives_are_rejected`（参数化）· `test_multiline_stdout_is_rejected` · `test_trailing_space_is_preserved_not_stripped`（三份各一） | ✅ |
| 1.3b cwd 不变性**双态**实测 | `test_bad_relative_value_rejected_regardless_of_cwd:240` | ✅ |
| 1.3c cwd 被删除负例 | `test_deleted_process_cwd_yields_controlled_failure:138` + `test_cli_with_deleted_process_cwd_exits_two_without_traceback:709`；实现 `buglist.py:634-642` 捕 `OSError`（比 spec 的 `FileNotFoundError` 更宽，见 §4.3） | ✅ |
| 1.4 `core.worktree` 主防线回归 + 变异确认 | `test_core_worktree_redirect_is_rejected:266`；**本次 verify 亲自做变异确认，删判据即红** | ✅ |
| 1.5 环境重定向（两层防御各自独立） | `test_git_dir_and_work_tree_env_are_sanitized:296` + `test_ancestor_check_independently_catches_unsanitized_env:306` | ✅ |
| 1.6 边缘场景正向回归 + 回落 | `test_linked_worktree_dot_git_is_a_file:413` · `test_submodule_dot_git_is_a_file:424` · `test_symlinked_start_resolves_to_real_root:346` · `test_returns_root_from_nested_subdirectory:338` · `test_falls_back_outside_any_git_repo:439` · `test_bare_repo_falls_back:446` · `test_cli_still_exits_zero_outside_any_git_repo:636` | ✅（`.git/` 内起点**改判 fail-closed** —— `test_inside_dot_git_directory_fails_closed:454`，属实现收紧，见 §4.3-j） |
| 1.7 起点校验（调 git 前拦截、路径未被创建） | `test_missing_start_directory_is_rejected_before_calling_git:107` · `test_file_as_start_is_rejected_before_calling_git:120`；实现 `buglist.py:621-626` | ✅ |
| 1.8 超时 → `ValueError` → exit 2，不回落 | `test_timeout_raises_and_does_not_fall_back:652` + `test_timeout_with_real_hanging_git:674`（真 PATH 注入） | ✅ |
| 1.9 CLI 级契约真跑（exit 2 / 无 Traceback / 含诊断） | `test_cli_bad_root_exits_two_with_diagnostic_on_stderr:762`（子进程真跑，非 AST 扫描） | ✅ |
| 1.10 determinism-guards 三向 AST 等价 | `sdflow-buglist/tests/test_mirror_consistency.py`，全仓跑绿 | ✅ |
| 1.11 跨进程重解析锚定测试 | `test_child_resolving_a_different_root_must_fail_loudly:945`（`xfail(strict=True)`）+ **前提核验用例 `test_child_root_drift_premise_climbs_to_outer:916`（刻意不带 xfail）** | ⚠️ **测试已写且是活锚，但被锚的 MUST 当前不成立** → B15，见 §4.1 |
| 2.1 修假绿（mock 收窄到 scan 调用点） | `sdflow-issues/tests/conftest.py:52 make_dispatch_run` / `scan_only_run`；`test_task4_rename_snapshot.py:154-190` 已改用分派工厂 | ✅ |
| 2.2 变异验证（写入即变红） | commit `29bf7a5` / `eedc585` 报告记录对照实验；**且已固化为机械守**：`test_patch_discipline.py` 门 A（站点必须用分派工厂）+ 门 B（工厂内层必须保留真实透传分支，:229-262） | ✅ |
| 2.3 完整断言集（exit=2 + `scan item[0].id` + 派生字节不变 + cwd 无新增） | `test_task4_rename_snapshot.py:180-190`，四条断言齐备，另有 `assert "仓根" not in diagnostic` 排除「更早关口崩掉」 | ✅ |
| 2.4 暴露的分支当场 fold | CF-1 面级改造：12 个同姿势站点全部改分派（commit `29bf7a5`+`eedc585`），非只修 1 处 | ✅ |
| 3.1 仓根单一份 `conftest.py` | `/conftest.py`（hook wrapper 形式，非 autouse fixture —— 理由见 CF-9b，技术上更优）+ `/pytest.ini`（钉 rootdir，CF-9c 实证缺一即失效） | ✅ |
| 3.2 覆盖面验证（各套件干净目录跑） | commit `a1c10a1`/`a245c7e` 报告；**本次亲验 sdflow-issues 一例 = 0 条目**。⚠️ 票面「12 个 skill」实为 **11**（`sdflow-retro` 无 `tests/`），CF-9e 已登记 | ✅（数字口径 Minor） |
| 3.3 反向验证 fixture 真会红 | `task5-cwd-leak-regression.md:119-161` 四态矩阵（无 ini 时注入泄漏 `1 passed` 假绿 / 有 ini 时 `1 failed`）；一次性验证，未留常驻用例 | ✅（Minor：无常驻回归） |
| 4.1 垃圾树未再生 | 本次 `find` 无输出 | ✅ |
| 4.2 干净临时目录条目数 = 0 | **本次亲验**：`/tmp/vroot` 跑完 `ls -a` 除 `.`/`..` 外空 | ✅ |
| 4.3 CLAUDE.md 登记 `premise-verification.md` 指针 | `CLAUDE.md:137-138`（只写路径 + 内部「规则 N」，未复制规则文本，合既定约定） | ✅ |
| 4.4 同步「运行测试」段 | `CLAUDE.md:74-79`（已改为**两文件**表述 `conftest.py` + `pytest.ini`，含「缺一即失效」） | ✅ |
| 4.5 记 buglist（outside_voice 用例） | **B16**（`2026-07-19-buglist.md:10`，显式带 `change` 字段；描述已按 CF-3 订正为「间歇性、触发条件未定位」，未照抄被证伪的「全量跑必红」） | ✅ |
| 4.6 Windows 泳道覆盖 | `test_task2_windows_local_fs_smoke.py:127-290`：`test_windows_repo_root_positive_regression` · `test_windows_repo_root_rejects_nonexistent_start` · `test_windows_repo_root_rejects_core_worktree_redirect` · `test_windows_commonpath_cross_drive_raises_without_recorder_format` · `test_windows_repo_root_cross_drive_redirect_is_fail_closed`；已挂进 `.github/workflows/windows-recorder-smoke.yml`（该 workflow 正是跑此文件） | ⚠️ **Minor 缺口**：本机 macOS 全 skip（全仓 9 skipped 含之），**从未在真 Windows runner 跑过** |
| 4.7 面治闭环（不限扩展名扫描 + 逐条论证） | **本次亲自重跑扫描 = 8 个文件**，与声明一致；论证落 `task6-surface-closure.md:23-40`；`outside-voice.sh` **有独立论证段**（:37）未套用「只读拼路径」模板。⚠️ proposal Non-Goals 正文只逐条论证了 `init.py` / `ship_gate.py`，三个 shell 脚本的论证在 impl-report 而非 Non-Goals —— CF-9f 已登记须回写 | ✅（回写待办 Minor） |
| 4.8 记 todo（git stdout 无界读取 DoS 面） | **T182**（`2026-07-todolist.md:41`） | ✅ |
| 4.9 全仓跑 pytest 无回归 | **本次亲跑**：`1910 passed / 9 skipped / 3 xfailed / 0 failed` | ✅ |

---

## 3. spec R1–R5 逐 Requirement / Scenario 核对

### R1 — recorder 仓根解析对外部进程输出 fail-closed

| Scenario | 锚点 | 状态 |
|---|---|---|
| git 返回合法仓根 | `test_returns_root_from_nested_subdirectory:338` · `test_nested_inner_repo_resolves_to_inner:603` | ✅ |
| **core.worktree 重定向（主防线）** | `test_core_worktree_redirect_is_rejected:266`；**本次变异确认删⑦即红** | ✅ |
| GIT_DIR / GIT_WORK_TREE 重定向 | `test_git_dir_and_work_tree_env_are_sanitized:296` + `test_ancestor_check_independently_catches_unsanitized_env:306`；实现 `buglist.py:650-656` | ✅ |
| linked worktree 与 submodule | `test_linked_worktree_dot_git_is_a_file:413` · `test_submodule_dot_git_is_a_file:424`；实现用 `os.path.exists`（:769） | ✅ |
| 起点不是既存目录 | `test_missing_start_directory_is_rejected_before_calling_git:107`；实现 `buglist.py:621` 在调 git 前 | ✅ |
| 进程 cwd 在运行期被删除 | `test_deleted_process_cwd_yields_controlled_failure:138` · `test_cli_with_deleted_process_cwd_exits_two_without_traceback:709` · `test_getcwd_permission_error_is_controlled_too:743` | ✅ |
| git 探测超时 | `test_timeout_raises_and_does_not_fall_back:652`；实现 `buglist.py:671-677` | ✅ |
| git 返回非目录字符串 | `test_shape_negatives_are_rejected:182` · `test_multiline_stdout_is_rejected:195` | ✅ |
| 坏值恰好匹配 cwd 下既存目录 | `test_bad_relative_value_rejected_regardless_of_cwd:240`（**仓内/仓外双态**） | ✅ |
| git 返回空输出 | `test_shape_negatives_are_rejected` 参数含空串/纯空白 | ✅ |
| git 命令失败 → 回落 | `test_falls_back_outside_any_git_repo:439` · `test_bare_repo_falls_back:446` · `test_git_refusing_outside_any_repo_still_falls_back:530` | ✅ **但判据已收紧**：非 0 退出**不再整块**回落，改为「上溯一层 `.git` 都找不到才回落」（`buglist.py:698-716`，`test_git_refusing_inside_repo_fails_closed:474`）→ 见 §4.3-h |
| 抛出点在调用方异常出口内 | `test_cli_bad_root_exits_two_with_diagnostic_on_stderr:762`（CLI 真跑，非 AST 猜） | ✅ |

### R2 — 仓根在单次调用内只解析一次

| Scenario | 锚点 | 状态 |
|---|---|---|
| `cmd_*` 不再自行解析 | 本次 `ast.walk` 实测 Call 节点 = 3（三份 `main()` 各一）；`test_repo_root_is_resolved_once_per_process_and_only_in_main:849` | ✅ |
| 锁与写入锚定同一个根 | 由单点解析结构保证；`test_unspecified_root_probes_cwd_while_explicit_root_is_validated:886` | ✅ |
| **子进程解析出不同的根时响亮失败** | `test_child_resolving_a_different_root_must_fail_loudly:945` = `xfail(strict=True)`；`recorder_lock` 在 `validate_recorder_participant` 抛 `RecorderLockError` 时 `except → participant = None` 回落 owner 模式（`issues.py:194` / `buglist.py:207` / `todolist.py:207`）⇒ 子进程在外层根 `makedirs` + rc=0 | ❌ **spec MUST 未达成**（B15）；判为**可接受已知缺口**，见 §4.1 |

### R3 — fail-closed 校验在三份 recorder 间逐字一致

| Scenario | 锚点 | 状态 |
|---|---|---|
| 镜像守护校验 | `sdflow-buglist/tests/test_mirror_consistency.py`（三向 AST 等价），全仓绿 | ✅ |
| 单份漂移被拦截 | 既有 `test_logic_drift_is_caught`（跨 change 通用机制） | ✅ |

### R4 — 测试套件不得在当前工作目录留下副作用

| Scenario | 锚点 | 状态 |
|---|---|---|
| 干净目录跑任一套件 → 条目数 0 | **本次亲验** `/tmp/vroot` + `sdflow-issues/tests`：0 条目 | ✅ |
| 覆盖面为全仓而非仅 recorder | 仓根单一份 `/conftest.py` + `/pytest.ini`（rootdir 钉死，CF-9c 双向变异实证） | ✅ |
| 泄漏被回归断言捕获并报出条目名 | `conftest.py:_check` 抛 `AssertionError` 含条目名；`task5-cwd-leak-regression.md:119-161` 反向验证 | ✅ |

> ⚠️ 口径落差（CF-9a/b）：spec:157-158 仍写「**一切落盘物** MUST 位于 `tmp_path`」，实现口径是 D6 收窄后的「禁止新增 cwd **顶层条目**」；spec:160 + ADR-3 写「autouse fixture」，实现是 hook wrapper。**实现口径更窄但更可靠**（autouse teardown 抛异常会被记成 `1 passed`），须在归档回写。

### R5 — 坏 root 下的 reindex 不得静默通过派生字节校验

| Scenario | 锚点 | 状态 |
|---|---|---|
| 变异验证——写入即变红 | commit `29bf7a5`/`eedc585` 对照实验；固化为 `test_patch_discipline.py` 门 A + 门 B（:214, :223-262） | ✅ |
| 坏 scan 输出被受控拒绝且不误伤派生字节 | `test_task4_rename_snapshot.py:154-190`，四条断言齐（exit 2 / `ERROR: ` 前缀 / `scan item[0].id` / `; cause:` / `; fix:` / 无 Traceback / 字节不变 / cwd 无新增） | ✅ |
| 拒绝理由必须可区分 | 同上 `:181-184`，另含 `assert "仓根" not in diagnostic` | ✅ |

---

## 4. 缺口清单

### 4.1 🔴 唯一的真实 spec 缺口：R2 Scenario 3（B15）—— **判 PASS + 显著标注，附归档硬条件**

**事实**（我独立核实，与登记描述相符）：`recorder_lock` 捕获 `validate_recorder_participant` 抛出的 `RecorderLockError` 后 `participant = None` 回落 owner 模式，于是根分裂的子进程在自己解析出的**外层根**上新建锁、`makedirs`、rc=0 静默成功。spec R2 明写「MUST 以 `RecorderLockError` 失败，MUST NOT 静默写入」——**这条 MUST 当前不成立**。

**我的判断：PASS（可接受的已知缺口），不是 FAIL。** 理由：

1. **R2 的主体已达成**：本 change 的 P0 是「删 16 处二次解析、每进程只解析一次」，AST 实测 19→3 已闭环；Scenario 3 是对**跨进程边界**的兜底期望，spec 自己也把它定位为「由 `validate_recorder_participant` 的 path/token 绑定兜底」的依赖锚。
2. **缺陷不在本 change 的修改面内**：根因在 `recorder_lock` 的 participant 回落协议（锁能力），修法需新增 `SDFLOW_RECORDER_LOCK_ROOT` 下传父进程 realpath，**触及 recorder-lock 的 spec 且与既有契约测试 `test_invalid_participant_env_falls_back_to_owner_or_conflict` 直接冲突** ⇒ 是另一个能力的设计门议题，不是「因为现状少见所以缩水」。
3. **缺口是被本 change 发现并机械锚死的，盘面比起点更诚实**：`xfail(strict=True)` + **独立的前提核验用例（不带 xfail）** 的组合是我见过的高质量锚——前提一烂当场判红，绑定一旦补上 XPASS 强制回来删标记。B15 已登记 P1 且写明修法与爆炸半径（6 处生产调用点）。

**🔴 归档硬条件（MUST，否则主 spec 会宣称一个假保证）**：archive 同步 delta 到 `openspec/specs/` 时，**R2 的 Scenario「子进程解析出不同的根时响亮失败」MUST NOT 原样落进主 spec**。二选一：(a) 该 Scenario 就地标注「⚠️ 当前不成立，已登记 B15 + `xfail(strict=True)` 机械锚」；(b) 移出 ADDED、改由 B15 承接。**MUST NOT 静默同步。**

### 4.2 Minor 缺口（可接受 / 已 deferred，均已登记）

| 缺口 | 登记 | 说明 |
|---|---|---|
| Windows 泳道从未在真 Windows runner 跑过 | tasks 4.6 / design Open Questions | 用例已写、已挂 workflow（`windows-recorder-smoke.yml` 正是跑该文件），本机全 skip。**push 后由真 runner 跑即闭环**；`isabs("C:/…")` / `normcase`+`commonpath` 跨盘符 / SUBST 三条仍未实测 |
| 非仓库 + 不可写目录仍裸 Traceback + rc=1 | **B17**（P2） | `makedirs` 抛 `OSError`，`main()` 只 `except ValueError` 接不住。不在 `repo_root` 面内 |
| `maintain_scan.py::find_repo_root` 是仓根解析的**第四份**实现，三条加固判据全缺 | **B18**（P1） | 我核实：面治扫描按 `show-toplevel` 关键词扫，该文件用别的写法 ⇒ **未被 8 处扫描命中**。这是本次面治的口径盲区，已登记，非静默遗漏 |
| 回落分支返回 lexical `abspath` 可能 != git 实际探测目录 | **T181** | 存量，改需先改 spec |
| git stdout / stderr 无界读入（DoS 面） | **T182 / T185** | 非正确性面，`timeout=30` 已限时间窗 |
| 起点校验 TOCTOU 窗口 | **T183** | |
| outside-voice `$SDFLOW_VOICE_RUNNER` 协议坑 | **T184** | 与本 change 无关，顺手记录 |
| 3.2 票面「12 个 skill」实为 11 | CF-9e | `sdflow-retro` 无 `tests/` |
| 3.3 反向验证为一次性、未留常驻用例 | — | 可接受：常驻「故意泄漏」用例本身会污染 |
| Non-Goals 缺三个 shell 脚本的逐条论证（论证在 impl-report） | CF-9f/g | 归档回写 |

### 4.3 🔴 CF-9 h–k 方向核实：**实现超出 spec，不是偏离 spec**

我逐条对码核实，结论 = **实现比 spec 严，属可接受的收紧，必须回写而非回退**：

| # | spec 原判据 | 实现 | 核实结论 |
|---|---|---|---|
| **h** | spec:34,102 把「git 非 0 退出」**整块**归为回落 | `buglist.py:698-716`：git 失败时先看步骤④上溯到的 `marker_dir`——**找得到 marker ⇒ raise**，一层都找不到才回落 | **收紧且正确**。原口径的枚举（非 git 仓库/git 不可用/bare/`.git` 内）不完备：`safe.directory` dubious ownership、坏 `.git/config` 同样 rc=128 而进程**确实在仓内**，旧口径此时返回起点自身 = fail-open。锚 `test_git_refusing_inside_repo_fails_closed:474` |
| **i** | spec 只要求证明「是 `start` 所属仓库的根」 | 新增步骤⑨「最近根一致」（`buglist.py:776-787`）：git 返回的根 MUST 严格等于上溯到的第一个 marker 目录 | **收紧且必要**。⑦⑧ 只能证明「是**某个**祖先仓的根」——`core.worktree` 指向祖先仓 / PATH 上 fake git 返回外层仓，两条全过。锚 `test_core_worktree_redirect_to_ancestor_repo_is_rejected:544` + `test_fake_git_on_path_returning_outer_repo_is_rejected:574` |
| **j** | spec 把 `.git/` 内起点列为「正常回落」 | 改判 fail-closed（`test_inside_dot_git_directory_fails_closed:454`） | **收紧且正确**。旧行为返回 `.git` 内部路径 ⇒ 下游在 `.git/openspec/issues/` 建树 |
| **k** | spec 写「六步」 | 实现九步（③拆为③④⑤ + 新增⑨） | 纯计数同步，测试 docstring 已就地更新 |

> 另有两处**同向**收紧（本次核实新点出，与 h–k 同类）：① `buglist.py:637` 捕 `OSError` 而非 spec 写的 `FileNotFoundError`（`PermissionError` 同族，锚 `test_getcwd_permission_error_is_controlled_too:743`）；② `buglist.py:732` 用 `os.fsdecode(bytes)` 而非 `text=True`（Windows cp1252 下 `text=True` 会在读管道线程里解码崩、`out.stdout` 变 `None` ⇒ `AttributeError` 逃出 `except ValueError`，锚 `test_undecodable_git_stdout_fails_closed_with_controlled_diagnosis:986`）。**这两条 spec 也未覆盖，建议一并进回写批次（记为 l / m）。**

**⇒ 归档时 h–m MUST 作为「设计实质修订」处理，MUST NOT 折叠进「措辞订正」桶。**

---

## 5. 🔴 复选框回勾建议

### 可以勾 `[x]`（29 项）

`0.1` `0.2` `1.1` `1.2` `1.2b` `1.2c` `1.3` `1.3b` `1.3c` `1.4` `1.5` `1.6` `1.7` `1.8` `1.9` `1.10` `2.1` `2.2` `2.3` `2.4` `3.1` `3.3` `4.1` `4.2` `4.3` `4.4` `4.5` `4.8` `4.9`

### 勾 `[x]` 但 MUST 附说明（3 项）

| 任务 | 附注原文建议 |
|---|---|
| **3.2** | `[x] 3.2 …` + `> ⚠️ 实为 **11** 个套件（10 skill + hack；sdflow-retro 无 tests/），票面「12」沿用 ADR-3 失准基线，见 CF-9e。verify 复验其中 sdflow-issues 一例 = 0 条目。` |
| **4.6** | `[x] 4.6 …` + `> ⚠️ 用例已写并挂进 windows-recorder-smoke.yml，但**从未在真 Windows runner 跑过**（本机 macOS 全 skip）。design Open Questions 三条（isabs("C:/…") / normcase+commonpath 跨盘符与 UNC / realpath 对 SUBST）仍未实测。闭环点 = push 后该 workflow 首次绿。` |
| **4.7** | `[x] 4.7 …` + `> ⚠️ verify 独立重跑扫描确认 8 处；但三个 shell 脚本的逐条论证目前落在 impl-reports/task6-surface-closure.md 而非 proposal Non-Goals 正文（CF-9f/g，归档回写）。另：maintain_scan.py::find_repo_root 是第四份实现，因不含 "show-toplevel" 关键词而**未被本扫描口径命中** ⇒ 已登记 B18，属扫描口径盲区而非遗漏。` |

### 🔴 MUST 保持 `[ ]`（1 项）

| 任务 | 说明原文建议 |
|---|---|
| **1.11** | `[ ] 1.11 …` + `> 🔴 **测试已写、且是高质量活锚**（xfail(strict=True) + 独立的不带 xfail 的前提核验用例 test_child_root_drift_premise_climbs_to_outer），**但被锚的 spec MUST 当前不成立**：recorder_lock 吞掉 RecorderLockError 回落 owner 模式 ⇒ 子进程在外层根静默 makedirs + rc=0。已登记 **B15（P1）**，修法需触 recorder-lock 协议 spec ⇒ 属下一个设计门。**MUST NOT 勾 [x]** —— 勾了就是把一条未达成的 MUST 记成已完成。` |

**盘面诚实度底线**：1.11 保持 `[ ]` + 4.1 的归档硬条件（R2 Scenario 3 不得静默同步进主 spec），二者缺一，本 change 归档后 `openspec/specs/` 就会宣称一个代码里不成立的保证。

---

## 6. 一句话结论

**PASS** —— P0 三块（身份校验 fail-closed / 单点解析 / 假绿消除）全部有可机验锚点且经变异确认，全仓 0 failed；唯一未达成的 spec MUST（R2 Scenario 3 / B15）根因在另一能力的锁协议、已被 strict-xfail 机械锚死并登记，属可接受的已知缺口，但归档时 MUST 按 §4.1 处理其 spec 同步。
