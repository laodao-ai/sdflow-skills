# verify-report — mlh-p3-determ-guards

- 日期：2026-07-07
- change：mlh-p3-determ-guards
- 方式：冷启动，自 grep 代码 + 实跑测试/命令核验，不信任复选框与历史报告

## 结论：PASS

<!-- ship-gate: verify=PASS -->

全量测试 `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/` → **396 passed**。四个核心承诺均有可机验证据锚点，无核心缺口。

## 逐需求核对表

| 需求/任务 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| ① 镜像一致性测试：剥 docstring 后 AST 等价 3向+2向 | `sdflow-buglist/tests/test_mirror_consistency.py:40` `_ast_no_doc`（剥首个 docstring Expr）；`test_three_way_mirror_consistency`(THREE_WAY 3) + `test_two_way_mirror_consistency`(TWO_WAY 14) 均绿 | ✅ |
| ①a TWO_WAY 经 code-review F5 扩至 14（原 8 + 6） | `test_mirror_consistency.py:78-84` 列出 14 项（含 `_id_sort_key`/`validate_doc_paths`/`all_ids`/`next_id`/`_die`/`_load_json`）；注释 F5 说明 | ✅ |
| ①b 逻辑分叉证伪 | `test_logic_drift_is_caught`（helper_a `1+1` vs helper_b `1+2` → AST 不等）绿 | ✅ |
| ①c helper 删除证伪（getattr 无 try/except 吞 AttributeError） | `test_helper_deletion_is_not_silently_swallowed`（`pytest.raises(AttributeError)`）；比对函数用裸 `getattr(m,name)` 无 try/except（:91-93,:110-111） | ✅ |
| ①d docstring 分化放行 | `test_docstring_diff_ok` 绿 | ✅ |
| ①e PRIORITIES 值断言（独立 `==` 非 getsource） | `test_priorities_constant_consistency`：`assert BUG.PRIORITIES == ISS.PRIORITIES`（:162）；`buglist.py:57` 与 `issues.py:444` 均 `["P0".."P4"]` | ✅ |
| ② config-lint fail-closed 非零 + reason | `init.py:295` `lint_config` / `:351` `cmd_config_lint`（reason→stderr, return 1）；真实数据实跑 `[config-lint] CLEAN exit=0`；坏结构手跑 `缺顶层 schema/rules exit=1` | ✅ |
| ②a config-lint 作 mode 第 4 值（无 add_subparsers） | `init.py:687` `choices=[...,"config-lint"]` + `:696` 早分支 return；`TestConfigLintCliSmoke.test_existing_modes_still_run` 绿 | ✅ |
| ②b 不 import yaml（手写 stdlib 扫描） | grep `^import yaml` → NONE；`_find_top_level_block`/`_second_level_keys` 行级扫描（:314-346） | ✅ |
| ②c 顶层块缺失条件化放行（防 mlh-p2 假阳） | `init.py:327,335` `if block is not None`；`test_no_model_tiers_block_passes` / `test_no_metrics_block_passes_consumer_style_fixture` 绿 | ✅ |
| ②d F1（config 缺失→非零非 fail-open） | `lint_config:302-310` except (OSError,UnicodeDecodeError)→reason；`TestConfigLintMissingFile` 绿 | ✅ |
| ②e F2（two-way except UnicodeDecodeError） | `init.py:309`；`test_non_utf8_config_yaml_clean_reason_nonzero` 绿 | ✅ |
| ③ batch lint fail-closed | `issues.py:772` `cmd_batch_lint`（problems→stderr, `sys.exit(1)`）；真实数据实跑 `19 条全部通过 exit=0` | ✅ |
| ③a 占位符豁免 + 前导 token 后缀不校验（P1 ★ 过） | `issues.py:758,764` `!= BATCH_PLACEHOLDER` 豁免；`_lint_priority_field:728` 只取前导 token；`test_bare_star_suffix...`/`test_placeholder_*_exempt` 绿 | ✅ |
| ③b F1（缺 batches.md→非零非 fail-open） | `issues.py:790-791` `if not os.path.exists → _die`；`TestBatchLintMissingBatchesMdFailsClosed` 绿 + 手跑 `batches.md 不存在 exit=1` | ✅ |
| ③c F2（batches.md 非 UTF-8 干净非零） | `issues.py:501` `except (OSError, UnicodeDecodeError)`；`TestBatchLintNonUtf8...` 绿 | ✅ |
| ③d F3（正则 `^(P[0-4](?!\d)|—)` 拒 P10/P40） | `issues.py:707` `_BATCH_PRIORITY_PREFIX_RE`；`test_two_digit_p10/p40_is_rejected` 绿 + 手跑 P10 exit=1 | ✅ |
| ③e PRIORITIES 声明（值断言守漂移，非跨 import） | `issues.py:444` `PRIORITIES = ["P0".."P4"]` | ✅ |
| ④ 归一零行为改动（split_sections/block_ranges 两处） | todolist 侧归一 → `test_two_way_mirror_consistency` 含 `split_sections`/`block_ranges` 且 AST 等价通过；`pytest sdflow-todolist/tests/` 零回归（含在 396 passed） | ✅ |
| ⑤ 现存真实数据零假阳 | 实跑 `config-lint` exit=0（CLEAN）、`batch lint` exit=0（19 条全过）；`test_real_repo_config_yaml_passes` / `test_real_batches_md_all_entries_pass` 绿 | ✅ |
| ⑥ 守卫不越权、不破 D4（无跨 recorder import） | `test_mirror_consistency.py:28` importlib 独立加载，无 import 包；batch lint 只读不覆写 | ✅ |
| checkpoint 提交留痕（task1-4 命名空间+横杠 TAG） | git log：`caa950c`(task1) `043f3a7`(task2) `7ff7a98`(task3) `e917de9`(task4) | ✅ |
| openspec validate | `openspec validate mlh-p3-determ-guards` → is valid | ✅ |

## 缺口清单

### 核心缺口（FAIL）
- 无。四条核心承诺（镜像一致性守卫真守漂移、config-lint/batch-lint fail-closed 真非零、归一零回归、现存数据零假阳）均有实跑/测试锚点，含全部 code-review 修复（F1/F2/F3/F5）。

### Minor 缺口
- 无。tasks.md 全部复选框（1.1–4.6）均可对应到代码/测试/commit 锚点，无遗留 defer（T70-73 不在本 change 范围内）。

## 结论
PASS — 396 tests 全绿；4 大承诺 + 全部 code-review 修复均可机验；真实 config.yaml / batches.md 跑 lint exit=0（零假阳）；坏输入手验非零退出；openspec validate 通过。
