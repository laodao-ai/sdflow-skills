### Task 3: 守卫脚本退役与矩阵 golden 迁移 — 实现报告

**范围**：`openspec/changes/absorb-gstack-autoplan/tasks.md` 任务组 3（3.1/3.2）。

## 做了什么

1. **矩阵全笛卡尔 golden 先迁移**（在 guard 删除之前完成，`sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`）：
   - 新增 `_matrix_oracle(host, runner, reason_code, findings)`：独立于 `classify_combo` 分支顺序的矩阵定义 oracle（四类各写成互斥谓词 + 显式互斥断言，非照抄生产实现的 if/elif 结构），供 golden 测试核验 `anchor_lint.classify_combo` 是否符合 `host-adaptive-execution` spec.md 记录的矩阵定义。
   - 新增 `test_matrix_full_cartesian_golden_conforms_to_definition`：对 `host×runner×reason_code×findings` 全笛卡尔积（枚举域来自 `enums["host"]`/`["runner"]`/`["reason_code"]`（真实契约机读块）+ mutation：`bogus-host`/`bogus-runner`/`bogus-reason`/`None`，findings 域 `[0, 1, 5, None]`）逐条断言 `classify_combo` 输出与 oracle 一致，并断言 `categories_seen == {cross-model, same-family, no-exec, self-review, illegal}`（防测试域退化成只测部分分支）。
   - 迁移前原 `test_outside_voice_guard.py::test_matrix_cross_tool_golden_full_cartesian` 是**两工具互比**（`anchor_lint.classify_combo` vs `outside_voice_guard.classify_combo`）；迁移后是**单工具自测**（`anchor_lint.classify_combo` vs 独立 oracle）——与 host-adaptive-execution spec.md 「矩阵实现收敛为 anchor_lint 单一本地实现...防漂移 golden SHALL 收敛为 anchor_lint 单工具自测」的要求一致。
   - 迁移前先跑 `pytest -k matrix` 确认新用例绿（18 passed），再执行删除，未出现「先删后测」的覆盖面丢失窗口。

2. **删除守卫脚本及其测试**：
   - `git rm sdflow-init/assets/workflow/tools/outside_voice_guard.py`（215 行）
   - `git rm sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py`（436 行，44 个测试函数）
   - 全部 44 个测试中，唯一具备独立覆盖价值、且被 spec 明确要求保留的是 Step 5 矩阵全笛卡尔 golden（已迁移）；其余测试（`classify`/`parse_mode`/`source_max_mtime`/`parse_codex_findings`/CLI 契约等）覆盖的是 guard 自身的 `gstack-review.md` 读取 + 复用判定工作流——该工作流随 task 2.3（Step1 autoplan 原生执行/gstack-review.md 落盘/guard 调用/checkpoint 四环节整体删除）已失去存在依据，MUST NOT 迁移（迁移会把已退役工作流的测试面伪装成"仍活"）。

3. **清理 `anchor_lint.py` 两处因 guard 删除而失真的注释**（`classify_combo` 所在模块头部注释 + docstring 末句）：原文声称"outside_voice_guard 各自重实现，golden 守一致"——guard 删除后这句话对当前代码库为假，已改写为过去时框架（"absorb-gstack-autoplan 前曾…该复用路径退役后收敛为本文件单一实现，golden 改为单工具自测"）。判断依据：这两处注释直接描述 `classify_combo` 的协作对象，若不同步会让读者对着已不存在的文件抓瞎；范围判据（fold-vs-defer）——低成本、与本任务直接相关（我正是这次删除的执行者），故当场 fold 而非另开。

## 未改动 / 明确排除的范围

- `lens-metric-contract.md` 的 outside_voice_guard 相关散文——task 1（已在更早的 commit 完成）已改写为"退役而并入 absorb-gstack-autoplan"的正确措辞，读码确认无需再动。
- `sdflow-spec-review/SKILL.md` :297 的 `outside_voice_guard.py` 提法——上下文是"旧「outside-voice 复用守卫」...整体退役"的历史性描述（task 2 已完成），措辞已正确，未改动。
- `test_review_disposition_check.py` :100 的 `outside_voice_guard` 字符串——是测试夹具里的示例 commit message 文本（用于测试 Markdown 解析行为），非代码依赖，未改动。
- `openspec/INDEX.md`、`openspec/CONTEXT.md`、`openspec/specs/outside-voice-reuse-guard/spec.md`（主 spec REMOVED delta 同步）——分属 task 4.3 / 归档阶段 delta 同步，不在本任务范围。
- `guard=` 字段解析——全局约束要求 anchor_lint MUST NOT 解析该字段；核验 `anchor_lint.py` 现状本就未解析 `guard=`（:555 注释明确"MUST NOT 解析 guard="），无需改动。

## 验证

- `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -k matrix`：18 passed（含新迁移的全笛卡尔 golden）。
- 全仓 `/usr/bin/python3 -m pytest -q`：**2444 passed, 10 skipped, 1 failed**。
  - 失败用例：`sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`——与本任务（outside-voice-**reuse-guard**）无关的另一模块（async outside-voice **job** supervisor），依赖真实 `claude` CLI 的 `--bg --exec` 时序探针，对照组本身未采到 canary（环境时序问题）。**在我改动前的基线跑（同一 worktree、改动前状态）已同样失败**，测试计数 2487 passed / 1 failed，与改动后 2444 passed（2487 − 44 删除 + 1 迁移新增 = 2444）精确吻合，证明该失败与本次守卫脚本退役/矩阵迁移无关，是预先存在的环境相关 flake。
  - `grep -rn "outside_voice_guard" --include="*.py" --include="*.sh" .`：仅剩 3 处非代码引用命中（`anchor_lint.py` 的两行历史性注释 + `test_review_disposition_check.py` 的字符串夹具），均已在上节说明，无残留调用。

## Checklist（供门禁核对，未勾选——由执行模式在双轴审后补打）

- [x] 矩阵全笛卡尔 golden 已迁移到 anchor_lint 测试（含 mutation/边界）
- [x] outside_voice_guard.py + tests 已删除
- [x] 全仓 pytest 绿（guard 残留引用归零；1 个不相关预存 flake 已核实非本任务引入）
