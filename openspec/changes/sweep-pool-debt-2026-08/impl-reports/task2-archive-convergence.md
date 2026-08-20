# Task 2 impl-report — 归档面收敛 + CI 机械门（archive-validation）

## 执行序（DT-6，已照原序）

1. 本地全量收敛（桶B 14 / 桶A 2 / 桶C 1）→ 2. 本地 `openspec validate --archived` 0 failed →
3. 改 CI（pin 1.5.0→1.9.0 + 新增 `validate --archived` 步）→ 4. 定点破坏自证。

## 结果

- `openspec validate --archived`：起手 **17 failed**（78 items）→ 收尾 **0 failed（78 passed）**。
- 本机 `/usr/bin/python3 -m pytest -q`（仓根 rootdir）：**2620 passed, 10 skipped**，无 failed。
- 定点破坏自证：临时把 `remove-superpowers-pipeline/tasks.md` 1.1 改回 `- [ ]`，
  `openspec validate --archived` 当场判该 change 红（`1 incomplete task (20/21 completed)`）；
  验证门真能红后已还原为 `- [x]`，复核回到 0 failed。

## 17 个 change 的逐条处置（对照 git log / verify-report / issues 池核验）

**桶B（14 个，逐条对照回填）**

| change | 处置 | 依据 |
|---|---|---|
| issues-pool-batch-mgmt | 补勾 6.2 | `openspec/specs/spec-workflow/spec.md` 现含该 change 的两条 Requirement |
| streamline-workflow-automation | 4.4 改无复选框说明段；9.1-9.3 改无复选框登记段 | 4.4 用户显式跳过；9.1-9.3 是外部消费仓事项，本仓无法观测其完成状态 |
| plan-workflow-cost-optimization | 补勾 5.1 | change 现位于 archive/，归档动作显然已完成 |
| done-roadmap-writeback | 4.1 改无复选框说明段 | 条件未触发（原注记已确认，未新增证据） |
| matt-workflow-integration | 补勾 6.3 | 现场 `readlink ~/.claude/skills/sdflow-ship` 核验指回运行 checkout |
| rebuild-sdflow-roadmap-v2 | 5.1-5.3 改无复选框说明段 | T129 现仍 PROPOSED/open，前置条件未满足 |
| add-sdflow-devenv | 补勾「试点结论回灌」；`/sdflow-code-review` 项改无复选框说明段 | commit `fb165c3` 已回灌 mqtt-console 结论至 `verification-patterns.md`；后者用户明示跳过 |
| add-codex-host-support | 0.1/0.2/0.3/10.1 改无复选框说明段 | headless/codex exec/spawned subagent 三形态迄今未验；10.1 要求 `runner="claude"`，实测恒 `runner="codex"`；T162 仍 OPEN |
| harden-repo-root-fail-closed | 1.11 改无复选框说明段 | B15 已于 2026-08-03 关闭为 WONTFIX，MUST 永久不成立 |
| add-sdflow-spec | 补勾 8.2 | T239 已关闭 DONE（canonical bundle 已推下游） |
| enable-codex-background-outside-voice | 6.1/6.2 改无复选框说明段 | T225/T226 已于 2026-08-04 关闭 WONTDO，T162 仍 OPEN |
| fix-windows-encoding-crash | 7.1 改无复选框说明段 | 本机 pytest 现全绿，但 `windows-recorder-smoke.yml` 的 `windows-full-pytest` job 持续红（缺 yq，无关本 change，见「票外发现」） |
| align-sdflow-spec-with-openspec-schema | 3.8/5.6 改无复选框说明段；5.7 改无复选框说明段 | 3.8 表述缺口未见后续补写；5.6 历史执行留痕缺失无法回溯；5.7 同 fix-windows-encoding-crash 的 CI 现状 |
| refactor-roadmap-internalize-deps | 补勾 4.5 | 现场 readlink 核验同 matt-workflow-integration |

**桶A（2 个 tickets 管线 change，收尾对账回填）**

| change | 起手 | 收尾 | 依据 |
|---|---|---|---|
| remove-superpowers-pipeline | 0/21 | 21/21 | `verify-report.md` 30 条 PASS/0 FAIL；本地对多条逐一 grep 核验（`PLAN_FILENAMES`、`impl_route.py` 无路由函数、adr/0033 supersede 指针等） |
| sdflow-init-readwrite-paths | 0/12 | 12/12 | `verify-report.md` 结论 PASS；`_atomic_write_settings`/`_detect_duplicate_top_keys`/`ensure_global_hooks` 均在现行代码 + 对应测试；T64/T149/T6 均已 DONE |

**桶C（1 个，改写为作废说明段）**

| change | 处置 | 依据 |
|---|---|---|
| scoped-test-per-task | tasks.md 全文改写为无复选框作废说明段 | 无 hand-off/verify-report（从未执行）；核心 Requirement「阶段三 subagent-dev 派发…」的派发点已随 `remove-superpowers-pipeline` 移除 `subagent-driven-development` 而消失，目标载体不复存在 |

## CI 改动

`.github/workflows/mechanical-gates.yml`：
- `Install openspec CLI` 步 pin 1.5.0 → 1.9.0（同步更新其上方注释）。
- 新增 `Gate — 归档面校验（openspec validate --archived）`步，`if` 条件与既有 openspec 泳道相同
  （仅 `ubuntu-latest` × `python 3.12`，唯一装了 CLI 的泳道）。
- 「三道门」注释改「四道门」（新增一道后计数同步）。

## 票外发现（[has-off-ticket-finding]）

`.github/workflows/windows-recorder-smoke.yml` 的 `windows-full-pytest` job（3.12 与 3.14 两档）
**自 2026-08-12 起持续 failure**（`gh run list` 近 20 次运行全部红，含本轮 HEAD 前一次运行）。
根因：该 runner 未安装 `yq`，`anchor_lint.py` 的 `_metrics_enabled()` 走 `_yq()` 时抛
`MetricsError: yq 未安装`（`mechanical-gates.yml` 早已给自己的泳道装了 yq v4.53.3，但
`windows-recorder-smoke.yml` 是独立 workflow，未装）。与 `fix-windows-encoding-crash` /
`align-sdflow-spec-with-openspec-schema` 两个已归档 change 的编码/schema 修复本身无关，
且晚于两者的归档时间才出现（首次红在 2026-08-12），判定为**独立缺口，超出本 ticket
（archive-validation 归档面收敛）范围**——未在本轮修复，仅如实记录并建议后续单开 todo
（`windows-recorder-smoke.yml` 装 yq 或改用 `_metrics_enabled()` 的等价降级路径）。

## 验收复选框对照

- [x] 桶B 14 个 change：逐条对照 git log / 实现 commit 回填漏勾复选框
- [x] 桶A 2 个 tickets 管线 change：对照 git log 逐条回填
- [x] 桶C scoped-test-per-task：tasks.md 改写为无勾选框作废说明段
- [x] 本地 `openspec validate --archived` 全量 0 failed
- [x] `.github/workflows/mechanical-gates.yml`：pin 1.9.0 + 新增 `validate --archived` 步 + 注释同步
- [x] 定点破坏自证：临时未勾复选框确认真红后还原
