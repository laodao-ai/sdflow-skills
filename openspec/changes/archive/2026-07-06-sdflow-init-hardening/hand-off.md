# hand-off — sdflow-init-hardening

> 2026-07-06 · 轻量健壮性清理批 · verify PASS · code-review pass（冷主审四源收敛扩至 6 fold 修）

## ✅ 完成了什么（每条附机验锚点，已复核锚点存在性）

`sdflow-init/scripts/init.py` + `setup.sh` 健壮性硬化，`sdflow-init` 铺设行为契约不变、无 spec delta：

| 项 | 内容 | 锚点 |
|---|---|---|
| **T49** | settings.json 并发 lost-update 收窗：`_deregister` 用 `_acquire_settings_lock`（独立 lockfile `fcntl.flock LOCK_EX`）串行化读-改-写-replace 临界区，拆 `_deregister_hook_in_settings_locked` | `init.py:_acquire_settings_lock/_deregister_hook_in_settings_locked`；`test_deregister_blocks_while_external_lock_held` |
| **T22** | 读侧 `open().read()`/`json.load(open())` 统一 `with open()`（清 -W error 19 Unraisable） | 静态守卫 `test_no_bare_open_read_or_json_load_open_in_source` |
| **T21** | `_find_marker_line` 逐行 offset 累加（非 text.index，防内嵌 token 锚错位）；多块 collapse **已回退**（见下 F-A） | `init.py:_find_all_marker_lines`；`test_find_marker_line_not_misanchored_by_inline_token` |
| **T48** | `setup.sh` 逐候选迭代 `for _cand in python3 python` + `version_info >= (3,6)` 校验（不喂 py2 致 f-string 解析崩）；init.py 头文档注释 | `setup.sh` probe；`test_setup_probe_rejects_non_py36` |
| **F-A** | 回退 T21 naive collapse（本仓 marker-示例满仓场景会 fence 劫持注入/吞用户内容，实证 F1/F3） | `init.py:inject`（first-start..first-end）；`test_inject_single_block_replace_unchanged` |
| **F-B** | `ensure_global_hook` 畸形 settings 崩溃守卫（`_register_hook_in_settings_locked` isinstance+`_hook_command`，对齐 CR-F1） | `init.py:_register_hook_in_settings_locked`；`test_malformed_settings_does_not_crash` |
| **F-C** | register 路径锁+原子写对称硬化（抽共享 `_atomic_write_settings`，register 与 deregister 同口径） | `init.py:_atomic_write_settings/ensure_global_hook`；`test_register_acquires_exclusive_lock/test_register_write_atomic_no_tmp_residue` |
| **F-D** | `_release_settings_lock` swallow OSError（retire-hooks CLI fail-safe） | `init.py:_release_settings_lock`（`except OSError: pass`） |
| **F-E** | init.py 头 T48 注释与 fcntl import 间加空行 | `init.py` 头 |
| **F-F** | setup.sh 候选迭代 fallback（python3 旧版→合格 python） | `test_setup_probe_falls_back_to_valid_candidate` |

**测试**：`-W error` 全量 sdflow-init 119 passed 零 warning；全仓 479 passed / 1 pre-existing（B5，main 亦红，非本 change）。

## ⏳ 未完成 / 延后 → 批次 `sdflow-init-hardening`（见 `openspec/issues/batches.md` + INDEX）

冷 code-review defer 2 项（已 triage 进批次，PROPOSED）：

- **T63** — inject 多块收敛须 **fence-aware + start/end 配对校验**。本轮回退了 naive collapse（只保 offset misanchor 修 + 单块替换）：naive collapse 在本仓（满是 marker 示例的 workflow-doc 仓）会 ① 命中 ``` 代码块内演示的 marker → 劫持注入（同 MEMORY `gate-substring-detection-dogfood` 类）② 孤儿 start 跨吞用户内容（静默数据丢失）③ 反序 end 残留。正确实现须复用本仓 fence-aware 行级解析 + 配对校验，是完整 change 的活、不塞进轻量批。**注：F1/F2 是 inject 的 pre-existing 脆弱面，本轮未新引入，但已文档化。**
- **T64** — `_atomic_write_settings` 的 tmp 改 `tempfile.mkstemp` 唯一名：POSIX 持锁路径已无碍，但 best-effort 无锁降级路径（Windows/fcntl 缺失）下并发写同名 tmp 可交错撕裂。低优先。

**≥2 方案决策留痕（T10）**：F-A「回退 vs 就地做安全 collapse」→ 有客观判据（回退后既有+新测试全绿且不引入数据丢失面），自动选**回退+defer 正确实现**（安全优先于功能完整；fence-aware 实现留完整 change）。

**批内既有 4 项**：T21/T22/T48/T49 是本批的原始输入，本 change 已全部实现（应随归档标 DONE）。

## ▶ 下一阶段建议

1. **T63（fence-aware inject）宜作独立小 change**——它撞上 MEMORY 已记的 fence-aware 主题，值得一次聚焦设计（复用 ship_gate/lens_metric 的 fence 解析），非大扫除批。优先级中（inject 畸形态触发概率低，但触发即数据丢失/劫持）。
2. **T64** 低优先，可随任意后续 init.py 触碰批次顺带清，或并入 T63 那次 change。
3. 本 change 完成后运行 checkout 跑 `/sdflow-upgrade` 激活（setup.sh/init.py 改动对新安装/update 生效）。
