# verify 报告 — sdflow-init-hardening

- 日期：2026-07-06
- change：sdflow-init-hardening（sdflow-init 健壮性清理批 T21/T22/T48/T49 + 6 项冷 code-review fold 修）
- 校验方式：Do-Not-Trust 冷核 —— 逐条对 `init.py` / `setup.sh` / 测试的真实代码锚点，不信复选框/报告措辞。无 specs delta（纯健壮性硬化，铺设行为契约不变）。

## 结论：PASS

<!-- ship-gate: verify=PASS -->

四项 tasks（T21/T22/T48/T49）+ 6 项 code-review fold 修（F-A~F-F）全部在代码中落地，各有可机验锚点；`python3 -W error -m pytest sdflow-init/tests/ -q` → **119 passed 零 warning**。2 项 defer（T63/T64）已入 todolist、非本 change scope。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试） | 状态 |
|---|---|---|
| **T49** deregister 用 flock(LOCK_EX) 独立 lockfile 串行化临界区 | `init.py:335-353` `_acquire_settings_lock`（`os.open(settings+".lock")` + `fcntl.flock(fd, LOCK_EX)`）；`init.py:388-402` `_deregister_hook_in_settings` 调 acquire/release | ✅ |
| **T49** 拆 `_deregister_hook_in_settings_locked` | `init.py:405-439` 临界区实现（读-改-`_atomic_write_settings`） | ✅ |
| **T49** 测试证串行化（外部持锁则阻塞） | `test_init_hardening.py:32` `test_deregister_blocks_while_external_lock_held`（passed） | ✅ |
| **T22** 读侧无裸 `open().read()`/`json.load(open())` | 全文读侧均 `with open() as f:`（`init.py:103,131,208,252,256,283,408`）；静态守卫 `test_init_hardening.py:72` `test_no_bare_open_read_or_json_load_open_in_source`（passed） | ✅ |
| **T21** `_find_marker_line` 逐行 offset 累加（非 text.index） | `init.py:47-66` `_find_all_marker_lines`（`off += len(line)` 累加）→ `_find_marker_line` 取首个；`test_init_hardening.py:89` inline-token 不错位（passed） | ✅ |
| **T21** collapse 已回退（inject 用 first-start..first-end，非 last-end） | `init.py:105-106` s_loc/e_loc 均 `_find_marker_line`（=首个）；`init.py:113-115` pre=`text[:s_loc[0]]`/post=`text[e_loc[1]:]`；无 `ends[-1]` | ✅ |
| **T48** setup.sh 逐候选迭代 + 3.6+ 校验 | `setup.sh:169-174` `for _cand in python3 python` + `version_info >= (3, 6)`；`test_init_hardening.py:120/145/168` 三测（passed） | ✅ |
| **T48** init.py 头文档注释（需 3.6+，调用侧把关） | `init.py:27-29` 注释块 | ✅ |
| **F-A** inject collapse 回退（非 `ends[-1]`） | 同 T21 collapse 回退锚；`init.py:108-112` 注释声明多块只收敛首块、fence-aware defer→T63 | ✅ |
| **F-B** register isinstance 守卫 + `_hook_command`（畸形不崩） | `init.py:275-313` `_register_hook_in_settings_locked`（`isinstance(data,dict)` L287、`isinstance(entry,dict)` L302、`_hook_command(h)` L304）；`test_init_hardening.py:182` `test_malformed_settings_does_not_crash`（passed） | ✅ |
| **F-C** `ensure_global_hook` 走 acquire/release + `_atomic_write_settings`（tmp+os.replace） | `init.py:266-272` acquire→`_register_hook_in_settings_locked`→release；`init.py:372-385` `_atomic_write_settings`（tmp + `os.replace`）；`test_init_hardening.py:196/219` 持锁+原子（passed） | ✅ |
| **F-C** register 与 deregister 共享 `_atomic_write_settings` | register `init.py:311` + deregister `init.py:437` 同调 `_atomic_write_settings` | ✅ |
| **F-D** `_release_settings_lock` swallow OSError | `init.py:356-369`（`except OSError: pass`，`os.close` 在 finally） | ✅ |
| **F-E** init.py 头 T48 注释与 fcntl import 间有空行 | `init.py:29` 注释末 → `init.py:30` 空行 → `init.py:31` `try: import fcntl` | ✅ |
| **F-F** setup.sh 候选迭代（非只校验 python3） | `setup.sh:169` `for _cand in python3 python`；`test_init_hardening.py:145` `test_setup_probe_falls_back_to_valid_candidate`（passed） | ✅ |
| 全量测试绿 | `python3 -W error -m pytest sdflow-init/tests/ -q` → **119 passed 零 warning** | ✅ |
| defer T63/T64 入 todolist、非本 scope | code-review-report.md「修复/defer 台账」；tasks 5.2 记录 | ✅（超范围，不阻断） |

## 缺口清单

无核心功能缺口。

- 已知 pre-existing B5（`sdflow-ship/tests/test_gate_anchor_scope.py::test_contract_archived_corpus_anchor_hits`，main 亦红）与本 change 无关，未纳入 FAIL 判据；本 change 定向测试集 `sdflow-init/tests/` 全绿。
- T63（inject 多块 fence-aware + start/end 配对收敛）、T64（`_atomic_write_settings` tmp 唯一名 tempfile 化）为报告显式 defer 项，已入 todolist 批次 `sdflow-init-hardening`，不属本轻量批 scope，非缺口。

PASS —— T21/T22/T48/T49 四项 + F-A~F-F 六项 fold 修全部代码落地并有测试锚点，`-W error` 119 passed 零 warning。
