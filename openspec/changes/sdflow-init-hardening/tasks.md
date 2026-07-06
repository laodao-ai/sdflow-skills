# Tasks — sdflow-init 健壮性清理批（T21/T22/T48/T49）

轻量清理：每项 TDD（先写反证哨兵测试 FAIL → 修 → 测过），逐项 checkpoint。跳 grill/spec-review/设计门（无新设计决策，flock/版本守卫/`with open()` 均标准解），保 cold code-review。测试落 `sdflow-init/tests/`。

## 1. T49 — settings.json 并发 lost-update 收窗（`init.py:_deregister_hook_in_settings`，主·数据丢失面）

- [x] 1.1 写反证测试 `test_deregister_concurrent_no_lost_update`：两「进程」（子进程 / 注入 barrier 的线程）各 deregister 不同 hook，断言两次 deregister 都存活（无静默覆盖）——修前 FAIL（一次被覆盖）
- [x] 1.2 加 `test_deregister_acquires_exclusive_lock`：spy `fcntl.flock`，断言临界区取 `LOCK_EX`（POSIX 分支）——修前 FAIL（从不加锁）
- [x] 1.3 `_deregister_hook_in_settings` 用 `fcntl.flock` 在独立 lockfile（`<settings>.lock`）上串行化整个读-改-写-`os.replace` 临界区；`fcntl` import 失败（Windows）→ best-effort 无锁降级 + 注释声明局限；返回契约不变
- [x] 1.4 跑 `test_init.py` + 相关 test 全绿（既有 retire_hooks / deregister 单进程用例不回归）
- [x] 1.5 checkpoint `bash ~/.sdflow/hack/checkpoint-commit.sh sdflow-init-hardening:task1-t49-flock "T49 settings.json 并发 lost-update flock 收窗"`

## 2. T22 — `open().read()` 统一 `with open()`（`init.py`）

- [x] 2.1 写反证测试 `test_no_unraisable_resource_warning`：`-W error::ResourceWarning`（或断言无裸 `open(...).read()` 残留）下跑 init 主路径零 `PytestUnraisableExceptionWarning`——修前 FAIL
- [x] 2.2 把 `init.py` 内所有 `open(path).read()` / `json.load(open(path))`（读侧：38/81/103/179/222/223/233/294 等）改 `with open() as f:`；写侧已 `with`，不动
- [x] 2.3 `python3 -W error::ResourceWarning -m pytest sdflow-init/tests/` 全绿零 warning
- [x] 2.4 checkpoint `... sdflow-init-hardening:task2-t22-with-open "T22 open().read() 统一 with open() 清 Unraisable"`

## 3. T21 — inject 畸形态加固（`init.py:inject`/`_find_marker_line`）

- [x] 3.1 写反证测试：① `test_inject_multiple_stale_blocks_all_replaced`（多个重复旧 marker 区块全部收敛，非只修首个）② `test_find_marker_line_inline_token_not_misanchored`（行内嵌入相同 marker 文本时锚定到真 marker 行、不错位）——修前 FAIL
- [x] 3.2 `_find_marker_line` 改逐行精确匹配 marker 行（非 `text.index` 子串）；`inject` 检测并处理多重复块
- [x] 3.3 跑 `test_init.py` 全绿（既有幂等 inject / 单块替换用例不回归）
- [x] 3.4 checkpoint `... sdflow-init-hardening:task3-t21-inject-malformed "T21 inject 多重复块+内嵌marker锚定加固"`

## 4. T48 — setup.sh python 探测版本校验（真修点在调用侧）

> 诚实 scope 修正：init.py 内 `sys.version_info` 守卫**无效**（整模块编译先于任何语句，f-string 解析崩来不及被守卫拦）——真修点是 setup.sh 探测端校验，见 proposal。

- [x] 4.1 写反证测试 `test_setup_probe_rejects_non_py36`（fake py2 `python` 在 PATH、无 python3 → probe 版本校验非零 → 跳过不喂 init.py）+ `test_setup_sh_has_version_check`（绑真 setup.sh 含 `version_info >= (3` 校验构造，防漂移）——修前 FAIL
- [x] 4.2 `setup.sh` 探测块：选定 `$_py` 后加 `"$_py" -c 'import sys; sys.exit(0 if sys.version_info >= (3,6) else 1)'` 校验，非 py3.6+ → 清空 `$_py` + 清晰非致命提示（复用 fail-safe 尾式）；init.py 头补一句「需 3.6+，由 setup.sh 调用侧把关」文档注释（非功能守卫）
- [x] 4.3 跑 `sdflow-init/tests/` 全绿（含既有 A5/A6 probe 测不回归）
- [x] 4.4 checkpoint `... sdflow-init-hardening:task4-t48-setup-version-check "T48 setup.sh python 探测加 3.6+ 校验"`

## 5. 收尾

- [x] 5.1 全量 `pytest sdflow-init/tests/` 绿 + 全仓 `pytest` 无新增回归（已知 pre-existing B5 除外）
- [x] 5.2 `/sdflow-code-review`（cold，load-bearing；T49/T21 触逻辑面必跑多镜）→ pass。冷主审 6 镜四源收敛揪出 T21 collapse 不安全(回退)+T49 半边(register 未硬化)+ensure_global_hook 崩溃面 → 6 fold 修 + 2 defer(T63/T64)。见 code-review-report.md
- [ ] 5.3 `/sdflow-done`（verify→hand-off→archive→commit→merge main）
