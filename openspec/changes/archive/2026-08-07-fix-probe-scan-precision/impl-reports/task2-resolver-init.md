# Task 2 impl report — resolver 两步链 + 停铺 tools/contract + 退役 --dev/full

## 范围

`tasks.md` 第 2 节（resolver 收缩为两步链）+ 第 3 节（停止铺设 tools/contract，退役 `--dev` 与
`full` 模式）。Task 3（`stale_shadow_warnings` 文案改写/判据扩员语义）与 Task 4（ship_gate 腿退役 +
死件清理 + 文档面 sweep）不在本票范围，未触碰。

## 生产代码改动

### `sdflow-init/assets/hack/resolve-workflow.sh`

- 删除步①（本地 pin 判定：`LOCAL`/`has_wf`/`has_spec`/`has_code`/`total` 及 any-of 分支 + 部分残留
  告警）。解析直接从全局 canonical 开始，两步链：① 全局 canonical → ② 显式降级。
- 头部契约注释（`:2` 三步链→两步链、`:5` "本地 pin 或全局 canonical"→"全局 canonical"）同批订正；
  内部步骤编号（原步②→步①、原步③→步②）与注释引用一并顺延。
- `sane()` 扩面：追加 `[ -d "$1/tools" ] && [ -n "$(ls -A "$1/tools")" ]` +
  `[ -s "$1/lens-metric-contract.md" ]` 两条形状级检查——只查目录/文件存在且非空，未枚举任何
  `.py` 成员名（design.md「sane() 扩面决策」A5 明确禁止）。
- 退出码集不变：0（成功）/ 2（bundle 不可达或不完整）/ 64（用法错误）；`--root`/`--explain`/
  `SDFLOW_HOME` 三个入参契约原样保留；`explain()` 的 `source=` 此后只剩 `global-canonical`。

### `sdflow-init/scripts/init.py`

- `copy_bundle(root, include_schema=True)`：签名去掉 `full` 参数。删除 `tools/` 整删重拷、
  `lens-metric-contract.md` 复制、`ignore_tools_tests()`、`LOCAL_TOOL_CACHES` 常量——四者一并
  删除（`ignore_tools_tests`/`LOCAL_TOOL_CACHES` 唯一消费者就是被删的 `full`/`tools` 分支，
  `grep -rn` 全仓确认无其它调用方）。只保留 `WORKFLOW-GUIDE.md` 复制 + `include_schema` 时的
  project-local schema 下发。`os.makedirs(dst, exist_ok=True)` 前置——此前 `openspec/workflow/`
  由 `tools/` 的 `copytree` 隐式创建，删掉后 fresh init 若无此行会在 `copy2(guide_src, ...)`
  处抛 `FileNotFoundError`（`ensure_dirs` 的 `CORE_DIRS` 只有 `changes`/`specs`）——已用
  `TestBundleGuideAndSchemaOnly::test_fresh_init_does_not_raise` 锚住。
- `run(root, mode)`：去掉 `dev` 关键字参数与 toolkit-仓根守卫（`if dev: ...`）；`copy_bundle`
  调用不再传 `full=dev`；`stale_shadow_warnings(root)` 调用去掉 `if not dev:` 豁免，无条件跑
  （--dev 退役后不再存在"刻意铺规则进 workflow/、告警是误报"的场景）。
- `main()`：`--dev` argparse flag **保留**（含 `action="store_true"`），但改为 tombstone——
  `if args.dev: _die("--dev 已退役：源仓 dogfood 同样走全局 canonical，无需本地 instance")`
  在任何文件系统操作之前拦截，比 argparse 的 generic "unrecognized arguments" 更明确。
  `run(...)` 调用点去掉 `dev=args.dev`。

## 测试改动（以 pytest 实跑红名单为准，非 grep 推断）

跑基线 `pytest sdflow-init/tests/ hack/tests/ sdflow-maintain/tests/` 确认改动前 1213 passed /
4 skipped 全绿，然后按生产代码改动逐个刷红名单改写：

- **`sdflow-init/tests/test_resolve_workflow.py`**：全面重写。`make_bundle()` 追加
  `with_tools`/`with_contract` 开关（sane() 扩面反向锚用）；`make_repo()` 简化（不再需要
  `with_rules` 参数——resolver 不再读仓内 openspec/workflow/）；新增 `make_repo_with_full_rule_copy()`
  专供反向锚。新增两个类：
  - `TestLocalCopyIgnored`：D13 核心不变量反向锚（task 2.3）——仓内放全套规则副本（含
    `tools/`）+ 全局 canonical 命中 → 仍解析到全局路径，`--explain` 报 `source=global-canonical`。
    旧实现（保留步①）在此必红（已用 `git stash` 临时回退验证过，见下「反向锚验证」）。
  - `TestSaneExpandedShapeChecks`（task 2.5）：canonical 缺 `tools/`、`tools/` 空、缺
    `lens-metric-contract.md`、`lens-metric-contract.md` 空四种半坏态各断言 `exit 2`；一条
    正向对照（形状齐全仍判健全）防扩面误伤。
  - 删除的旧用例：`test_local_pin_hit`、`test_tools_only_repo_falls_to_global_symlink`、
    `test_partial_residue_pins_and_warns`（本地 pin 判定与部分残留告警随步①一并消失）。
  - 保留用例（`TestEdgeCases`）全部改写 `make_bundle` 调用点补 `tools/`+contract，`explain`
    断言从 `source=local-pin` 改为 `source=global-canonical`。
  - `SDFLOW_HOME` 测试隔离契约（task 2.4）：既有 `test_global_canonical_symlink_hit` /
    `test_pointer_file_fallback` 覆盖，未改语义。
- **`sdflow-init/tests/test_resolve_models.py`**：`make_bundle_repo()` fixture 改造——bundle 从
  `root/openspec/workflow/`（本地 pin 路径）迁到 `tmp_path/sdflow-home/workflow/`，`run_resolve`/
  `eval_resolve` 的 `SDFLOW_HOME` 从指向不存在路径改为指向该假 sdflow-home；fixture 同步补
  `tools/`+`lens-metric-contract.md`（否则全局 canonical 因 sane() 扩面判「不完整」exit 2，
  26 条用例全灭）。语义不变：测的仍是 model-tiers 解析，非 pin 判定。
- **`sdflow-maintain/tests/test_marker_consistency.py`**：删除
  `test_resolve_workflow_bash_markers_match_python`（resolver 内联的第 3 份 `RULE_MARKERS`
  副本随步①消失，守卫失去对象，DRY 正向收益）；同步删无用的 `RW_PATH` 常量与 `re` import。
- **`sdflow-init/tests/test_init.py`**（全面改写以下几处，其余 65 条既有用例未改动）：
  - `TestBundleToolsOnly` → `TestBundleGuideAndSchemaOnly`：文件全集断言（task 3.4）——
    `openspec/workflow/` 下只有 `WORKFLOW-GUIDE.md`；新增 `test_fresh_init_does_not_raise`
    （F15 回归锚）；删除全部 `full=True`/`LOCAL_TOOL_CACHES` 相关用例（6 条，功能已退役）。
  - `TestPinConsumerUpdateInvariant` → `TestCopyBundleLeavesExistingWorkflowFilesAlone`：语义
    收窄为"copy_bundle 不碰既有文件"（不再断言 tools/ 刷新——tools/ 不再部署）。
  - `TestUpdateDev` → `TestUpdateDoesNotDeployRules`：删 `test_dev_update_deploys_full_bundle`，
    保留 plain-update 不铺规则的断言。
  - `TestDevRepoIdentityGuard` → `TestDevTombstone`：新增 3 条用例——`run()` 不再接受 `dev`
    关键字（`TypeError`）、CLI 层 `--dev` fail-loud（`SystemExit(1)` + "--dev 已退役"文案）、
    tombstone 在任何文件系统操作前拦截（不半跑一截）。
  - `TestCopyBundleConvergence` 整体删除（`tools/` 收敛测试，功能退役后无对象）。
- **`sdflow-init/tests/test_init_contract_sync.py`**：整文件删除（`full=False` + contract 断言，
  两者均已退役）。
- **`sdflow-init/tests/test_task5_regression.py:39`**：删除 `tools/anchor_lint.py` 部署断言，
  改为断言 `openspec/workflow` 目录存在但无 `tools/`（tools/ 不再部署，但 dst 仍须
  `os.makedirs` 创建）。

## 反向锚验证（防「删测试凑绿」，task 7.1 要求的一部分）

对 `TestLocalCopyIgnored` 与 `TestSaneExpandedShapeChecks` 两组新增反向锚，临时回退
`resolve-workflow.sh` 到改动前版本（`git stash` 恢复步①/旧 `sane()`）重跑，确认：

- `test_full_local_rule_copy_still_resolves_to_global_canonical`：旧实现命中步①，
  stdout 指向仓内副本而非全局 canonical → **红**（符合预期）。
- `test_missing_tools_dir_exits_2` / `test_missing_contract_exits_2`：旧 `sane()` 不查
  `tools/`/contract，半坏 canonical 仍判健全、`exit 0` → **红**（符合预期）。

验证后 `git stash pop` 恢复新实现，全部转绿。

## 测试结果

```
/usr/bin/python3 -m pytest sdflow-init/tests/ hack/tests/ sdflow-maintain/tests/ -q
1210 passed, 4 skipped in 229.76s
```

（基线为 1213 passed / 4 skipped；净减 3 条，构成：删除 `test_init_contract_sync.py` 1 条 + 删除
`test_resolve_workflow_bash_markers_match_python` 1 条 + `test_init.py` 内新增/删除净减 1 条——
`full=True`/dev 相关旧用例删除多于 tombstone 新增用例。）

另跑仓库其余全部测试（`--ignore=sdflow-init --ignore=hack --ignore=sdflow-maintain`）：
`890 passed, 6 skipped`，全绿，未见我改动波及。

## 真跑验证（非 pytest，手工）

- `bash sdflow-init/assets/hack/resolve-workflow.sh --explain --root .`（本仓，开发 checkout）
  → `source=global-canonical path=/Users/.../.sdflow/workflow`，`exit 0`。
- `eval "$(bash sdflow-init/assets/hack/resolve-models.sh --root .)"` → `HOST=claude
  STRONG=opus MID=sonnet LIGHT=haiku`，档位解析未受影响（resolve-models.sh 内部调用
  resolve-workflow.sh 定位 `model-tiers.md`，两步链改造后依然透明工作）。
- `python3 -c "...import init; init.copy_bundle.__code__.co_varnames..."` 确认新签名
  `copy_bundle(root, include_schema)` / `run(root, mode)`，`LOCAL_TOOL_CACHES` 属性已不存在。

三态真跑（正常仓 / 仓内放规则副本 / `SDFLOW_HOME` 指向空目录）与全链路 `openspec validate` 属
tasks.md 第 7 节（Task 5 "实现验证"票），未在本票执行。

## 文档同步（超出 tasks.md 第 2/3 节字面清单，但直接源于本票改动，遂 fold 做掉）

- `sdflow-code-review/SKILL.md:172(原197)` / `sdflow-spec-review/SKILL.md:147(原172)`："禁止自行
  重实现三步链" → "两步链"（`sdflow:async-branch` marker 区间**之外**，无需两文件字节相同，
  `test_async_branch_parity.py` 41 条用例复跑确认未受影响）。
- `sdflow-init/SKILL.md`「铺设了什么」目录树：从"整套 bundle 副本（含 tools/、checklists/ 等）"
  改为"只铺 WORKFLOW-GUIDE.md + project-local schema"，并订正"退役部署文件清理"一节里已过时的
  "tools/ 整删重拷自动清除"表述（tools/ 已不再部署，无整删重拷动作）。这两处直接描述本票改的
  `copy_bundle` 输出、且是用户会读到的操作指引，留着不改会误导——按四条通则的 fold 原则就地修正；
  该文件其余"铺 28 个文件"等次要措辞未动，留给 Task 4（文档面级订正）统一处理，未扩大范围。

## 未做 / 明确不在本票范围

- `stale_shadow_warnings()` 判据扩员（查 `tools/`+contract 残留）与文案改写、
  `sdflow-maintain/tests/test_maintain_scan.py` 的断言反转 —— Task 3。
- `ship_gate.py` `tools_spec` 腿退役、本仓 `openspec/workflow/` 死件清理（`tools/` 6 个 `.py` +
  `lens-metric-contract.md`）、ADR 状态注记、`0039` 新增、CONTEXT.md 术语补充、`docs/` 面 sweep
  —— Task 4。
- 概念词表全仓 sweep（task 7.6）、`openspec validate --strict`、三态真跑全链路、`setup.sh` 全局
  窗口层真跑评审 skill —— Task 5（实现验证收尾票）。

## 状态

四项 P0 MUST 同批落地项（resolver 删步① / copy_bundle 停铺 tools+contract / 两个 SKILL 删探测段
[Task 1 已完成] / 对应测试）本票范围内三项全部完成且测试绿；`--dev`/`full` 退役 + tombstone 完成；
`sane()` 扩面完成且有正反向锚；退出码集验证不变。
