# Verify Report — mlh-p1-issues-sweep

日期：2026-07-07
Change：mlh-p1-issues-sweep（issues sweep 原子子命令，机械活脚本化 · roadmap 阶段 1）

## 结论：PASS

<!-- ship-gate: verify=PASS -->

冷启独立核验（不信复选框、不信 code-review-report）：ADDED 需求「issues sweep 原子子命令」的 4 个 Scenario 均在 `issues.py cmd_sweep` 有真实现 + 有真断言测试；独立跑 `python3 -m pytest sdflow-issues/tests/ -q` → **102 passed in 9.28s**（自跑确认，非引用报告）。附加的 code-review 修项（problems 透传 / 0 命中不建僵尸批次 / 「非原子」措辞订正）也逐条落地。无核心缺口。

## 逐需求/Scenario 核对表

| 需求/Scenario | 代码出处 文件:行 / 测试名 | 状态 |
|---|---|---|
| 子命令注册 `sweep --change`（必填、`--root` 缺省） | `issues.py:1014-1024`（subparser + `--change required=True`）；`main()` 分发 `args.func` | ✅ |
| 全子步走 subprocess CLI（不直调 cmd_*） | `issues.py:916`（scan）/`933`（triage）/`952`（batch add）/`960`（reindex）均 `subprocess.run` | ✅ |
| ① 入口守卫先于任何写盘（非空 + `_reject_batch_key_unsafe`） | `issues.py:902-909`；`_reject_batch_key_unsafe:324-350`（拒 `\|`/换行/` — `/首尾空白/空） | ✅ |
| **Scenario 1**：`--open-ungrouped` 口径扫全非终态未分批项（含非 OPEN 非终态如 IN_PROGRESS；已在别批次不 clobber） | 口径实现 `buglist.py:659-661` + `todolist.py:624-628`（`status in 非终态集 and not batch`），与 `--change` 过滤叠加（buglist:655-656 / todolist:620-621）；sweep 传 `--open-ungrouped`（`issues.py:918`）。测试 `test_sweep_open_ungrouped`（断言 B2 IN_PROGRESS 被纳入 tag=PROPOSED）。不 clobber 由 `not batch` 过滤保证（已分批项天然被排除） | ✅ |
| **Scenario 2**：幂等重跑退出码 0（`batch add --if-exists skip`） | `issues.py:952-958`（固定带 `--if-exists skip`）；`cmd_batch_add:698-706`（默认撞号 `_die`，`skip` → no-op exit0）。测试 `test_sweep_idempotent`（连跑两次 rc==0、batches/INDEX 字节级无变化、`### chg-y` 计数==1） | ✅ |
| **Scenario 3**：空 change 入口守卫拒（防孤儿误纳） | `issues.py:904-909`（首尾空白/空/unsafe 先于写盘 `_die`）。测试 `test_sweep_rejects_empty_change`（`""`/`"   "`/`"a — b"`/`"a\|b"`/`"a\nb"` 全 rc!=0、孤儿 B1 batch=""、status=OPEN、batches.md 未建）+ `test_sweep_rejects_whitespace_change`（`" chg"`/`"chg "` 拒） | ✅ |
| **Scenario 4**：某项 triage 失败 fail-closed + 重跑收敛 | fail-closed `issues.py:938-943`（查 returncode 非零 `_die`，报 pool/id/已 tag 列表）。测试 `test_sweep_triage_fail_closed`（注入 B2 triage rc=1 → SystemExit≠0、stderr 含 B2/bug/B1、B1 已 tag/B2 未 tag/batches 未建）+ `test_sweep_rerun_converges`（移除注入重跑 rc==0、B1+B2 全收敛 tag=PROPOSED、batches 建成、INDEX 刷新） | ✅ |
| 末步 reindex 也 fail-closed（区别 rename warn-only） | `issues.py:960-965`（reindex rc!=0 → `_die`）。测试 `test_sweep_reindex_fail_closed`（注入含义标注真验证：fake stderr="boom"，断言 err 含 "reindex"（只能来自代码自标注）+ "boom"） | ✅ |
| 附加：scan problems 透传 stderr（不收紧退出码） | `issues.py:928-929`。测试覆盖：scan 失败分支 `test_sweep_scan_fail_closed` | ✅ |
| 附加：reindex 子进程 stderr（内部 `_echo_problems`）透传 | `issues.py:966-970`（成功路径透传 `ri.stderr`） | ✅ |
| 附加：0 命中不建僵尸批次（防 D1 vacuous-truth 空批次累积） | `issues.py:948-950`（`tagged` 为空即 return，不 batch add/reindex）。测试 `test_sweep_zero_items`（`chg-empty` 无匹配 → rc==0、batches.md 未建、未匹配项不受影响） | ✅ |
| 附加：「原子」措辞订正为「非原子、fail-closed、可重跑收敛」 | subparser help `issues.py:1016-1021`；`sdflow-issues/SKILL.md:101,120`；`sdflow-done/SKILL.md:123,133` 均已订正 | ✅ |
| Doc：`sdflow-done/SKILL.md §2.1` 改调 sweep 一行（保留孤儿/显式 --change/D6 串行边界） | `sdflow-done/SKILL.md:109-135`（一行 sweep + 孤儿不归/显式 `--change`/D6 串行/失败语义全声明） | ✅ |
| Doc：`sdflow-issues/SKILL.md` 命令面补 sweep 段 | `sdflow-issues/SKILL.md:101-142`（口径/幂等/空守卫/非原子重跑收敛/D6 串行/孤儿边界） | ✅ |
| 全套件绿 | 独立跑 `pytest sdflow-issues/tests/ -q` → 102 passed（自跑，非引用） | ✅ |

## 缺口清单

### 核心缺口
无。

### Minor（PASS，仅记录）
- **M1（测试覆盖）**：Scenario 1 的「已在别批次的项 MUST NOT 被 clobber」由 `--open-ungrouped` 的 `not batch` 过滤在实现层保证，但 TestSweep 无专门造「已分批项」并断言其 batch tag 不变的用例（`test_sweep_excludes_orphans` 覆盖的是源为空孤儿，非已分批项）。实现正确、不阻断；补一条已分批项不被 clobber 的显式断言可更完整。
