# Task 6 impl-report — 行为等价留存测试 + 覆盖判据零回归门 + setup.sh 验证 + 显式 defer

**R-ID:** SC-R3 · R5 · AD-6 · AD-7 ｜ 收口票。全套件绿：`2137 passed, 8 skipped, 3 xfailed`（`/usr/bin/python3 -m pytest -q` 仓根）。

## 6.1 CLI 逐命令行为等价**留存** param 化 harness

新文件 `sdflow-issues/tests/test_task6_cli_equivalence_harness.py`——持久 param 化契约（**非一次性 smoke**），
遍历三薄入口注册的**全部 argparse subcommand**，每命令跑真实 CLI 子进程断言三面：**stdout（JSON envelope / token / 文本）+ 落盘字节 + 退出码**。
共 16 个 param case（core 命令两池各跑）：

| subcommand | 池 | stdout 断言 | 落盘断言 |
|---|---|---|---|
| `core:next-id` | bug·todo | token `^[A-Z][0-9]+$` | 无（只读） |
| `core:add` | bug·todo | JSON `id` | dated 文件字节含 id |
| `core:scan --json` | bug·todo | JSON envelope key（`bugs`/`items`）+`problems` | 无（只读） |
| `core:set-status` | bug·todo | JSON `new`==目标态 | dated 文件字节含新态 |
| `core:triage` | bug·todo | JSON `batch` | dated 文件字节含批次 |
| `issues:reindex` | — | exit0 | INDEX.md 字节含 `DO NOT EDIT` banner |
| `issues:sweep` | — | 文本 `tagged 1` | batches.md 落盘 |
| `issues:batch:add` | — | JSON `key` | batches.md 字节含 key |
| `issues:batch:set-status` | — | JSON `new_status` | batches.md 字节含新态 |
| `issues:batch:rename` | — | JSON `new_key`+`items_changed` | batches.md 字节含新 key |
| `issues:batch:lint` | — | 文本 `通过` | 无（只读） |

前置数据一律经真实 `add`/`triage` CLI producer 造（避 fixture 格式漂移）。harness 导出 `COVERED_SUBCOMMANDS` 供覆盖门核对。

## 6.2 覆盖判据零回归门（**非 `≥N` 魔数**）

新文件 `sdflow-issues/tests/test_task6_coverage_gate.py`——留存门，4 个 assert：

**门 1 · 零回归 node 门（逐 node 比对，非计数）**：读冻结 `node-id-manifest.baseline.txt`（2093 node），
allowlist = 7 个 `test_mirror_consistency.py`。三合一把旧两 skill 的 tests+scripts 整体并入 `sdflow-issues`，
故 baseline 旧路径 node 经 **RENAME-MAP** 重定位后须命中当前 collection：
- `sdflow-{buglist,todolist}/tests/` → `sdflow-issues/tests/`（测试文件搬家）
- `sdflow-{buglist,todolist}/scripts/` → `sdflow-issues/scripts/`（**param 括号内被测脚本路径**，如 `test_...[sdflow-buglist/scripts/buglist.py]`——migration 实况，实现期此门 RED 一次抓到我初版只重定位文件前缀、漏了 param 内脚本路径；已核实 baseline 旧名**仅**以这两类路径出现、无 legacy-name 数据 param，全串替换精确不误伤）。
消失 node 只允许是 7 个 allowlist；其它消失=回归=红。新增 node 允许。
- 反向门：7 个 allowlist node 确已消失（旧路径与重定位后都不在 current）——防 mirror 测试残留=守法未切换。
- 基线完整性门：baseline ≥2000 node 且含 7 allowlist——防基线被误改削弱门。

**门 2 · 全 argparse subcommand 触达门**：让 argparse **自己**枚举 subcommand（CLAUDE.md 基准 5，非手搓名单）：
core 经 `build_parser` 的 subparser choices（`{add,next-id,scan,set-status,triage}`）；issues.py 经 invalid-choice
让 argparse 在 usage 行吐 `{reindex,batch,sweep}` / `batch {add,set-status,rename,lint}`。枚举出 11 个 canonical label，
断言 ⊆ 6.1 harness 的 `COVERED_SUBCOMMANDS`（枚举与 harness 交叉锁死，缺一即红）。

**门 3 · 无 FAILED/无重构 skip**：门 1/2 用 `pytest --collect-only`（让 pytest 自答）对账；8 skip 全 pre-existing
（7×`test_task2_windows_local_fs_smoke` 需真 Windows 磁盘 + 1×outside-voice 环境敏感复现），非重构导致。

## 6.3 setup.sh 验证（temp-HOME，**非真实环境 mutation**）

编排层裁定不 mutate 真实 `~/.claude|.codex/skills`（真实部署留合并后 `/sdflow-upgrade`）。两路核验：

1. **既有机械门**：`sdflow-init/tests/test_setup_sdflow.py::test_rename_scenario_old_links_cleaned_new_links_made`
   在 tmp HOME 里 subprocess 跑 setup.sh，断言建 `sdflow-issues` 链 + `sdflow-buglist`/`sdflow-todolist` orphan 清理——`11 passed`（T5.6 已接线，本票确认绿）。
2. **额外端到端 demo**（temp HOME，跑完即弃）：预置指向已删旧目录的 dangling 链 → `HOME=<tmp> bash setup.sh` → 结果：
   - `.claude/skills/sdflow-issues` 与 `.codex/skills/sdflow-issues` 符号链接建立（→ 仓内 `sdflow-issues`）；
   - setup 输出 `cleaned orphans (2): ✗ sdflow-buglist  ✗ sdflow-todolist`；旧链 AFTER 已消失（orphan reclaimed）。
   - 真实环境未触碰。

## 7 显式 defer todo（dev 脚本记，显式带 `change` 字段）

经 `sdflow-issues/scripts/todolist.py add`（开发版）记两条，均 `change=dedupe-issues-scripts-shared-layer`（scan 查重：T141/T164 无关，无撞号）：
- **T208**〔AD-7/R10〕：`sdflow_issues_core` god-module 拆 cohesive 子模块（recorder/document/locking/ledger/policies）+ issues 内部消自调用子进程（subprocess spawn → 进程内 import）。
- **T209**〔AD-6/R7〕：`move --to-pool` 跨池搬运命令（误判落错池的机械恢复：换前缀+粒度文件+schema+保 provenance）。

## 契约合规

未勾任何复选框、未打 `task6-` 标签、未改 proposal/design/specs/tasks。改动仅：2 个新测试文件 + todolist ledger（T208/T209）。
