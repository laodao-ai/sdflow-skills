---
ship-gate:
  verify: PASS
  reviewed_sha: d344061ab1c37df4b36208b67c7f812096ba6192
---

# Verify Report -- shared-yaml-subset-parser

- **日期**: 2026-08-01
- **Change**: shared-yaml-subset-parser
- **结论**: **PASS**

## 逐需求核对表

| 需求 | 描述 | 代码出处 | 状态 |
|---|---|---|---|
| R1 | yq 依赖检测（mikefarah/kislyuk 区分、版本门、安装指引） | `setup.sh:498-576`（`check_dependencies()`，含 `_YQ_MIN_VERSION="4.16.0"` 版本比较、`grep -q "mikefarah"` 身份校验、三平台指引） | PASS |
| R2 | 统一依赖预检（python3/git/yq/openspec/pytest） | `setup.sh:498-585`（五项逐一检测，缺失不中止，汇总输出） | PASS |
| R3 | config.yaml 读操作改为 yq | `init.py:741`（`_yq(".", cfg_path)`）、`init.py:293`（`_yq("[.artifacts[].template]", ...)`）、`init.py:641`（`_yq(".", marker)`）、`impl_route.py:192`（`_yq('."impl-pipeline"', ...)`）、`anchor_lint.py:193`（`_yq(".metrics.enabled", ...)`） | PASS |
| R4 | config.yaml 写操作改为 yq | init.py `_set_schema_key` 刻意保留字节级正则（yq header-preprocess bug 实测证据见 task4-init-yq.md 偏离 1），无 yq 写调用点存在，R13 注入面不成立 | PASS（偏离已记录） |
| R5 | Markdown frontmatter 读操作改为 yq | `ship_gate.py:1122`（`_yq('."ship-gate"', text=text, front_matter=True)`）、`impl_route.py:255`（`_yq('."impl-pipeline"', p, front_matter=True)`）、`roadmap_writeback_draft.py:285`（`_yq(".ship-gate.verify", path, front_matter=True)`）、`sad_schema.py:244`（`_yq(".", text=text, front_matter=True)`） | PASS |
| R6 | 业务逻辑与 YAML 解析分离 | `ship_gate.py:1120-1133`（预扫描后 yq 取值 + FIELD_VALIDATORS Python 侧校验）、`init.py:386-389`（fleet/tier 键验证在 Python dict 上）、`sad_schema.py:244-260`（TOP_KEYS/FACT_KEYS 白名单 Python 侧校验）、`impl_route.py:257-264`（非法值 raise RouteStop） | PASS |
| R7 | yq 不可用/失败时 fail-loud | 7 份 `_yq()` 均含 `shutil.which` 检测 + `sys.exit(1)`/`raise RuntimeError`、`mikefarah` 身份校验（进程内缓存 `_yq_bin`）、非零退出恒 raise（不因 default 静默） | PASS |
| R8 | ADR 记录 | `openspec/adr/0036-yq-replaces-hand-rolled-yaml.md` 含 Context/Decision/Consequences 三节 | PASS |
| R9 | 零依赖声明更新 | `init.py:383-389` 更新为「零依赖不变量收窄为不 import 解析库，代价见 adr/0036」 | PASS |
| R10 | 删除手搓 YAML 解析代码 | 6 个函数零命中（`_strip_inline_comment`/`_find_top_level_block`/`_second_level_keys`/`_parse_model_tiers_block`/`_extract_scalar`/`read_metrics_enabled`）。5 处命中均为合理保留：`_schema_from_config`/`_set_schema_key`（yq bug 刻意保留，task4-init-yq.md 偏离 1）、`_marker_schema`/`read_verify_state`（入口名保留但内部已改用 `_yq()`）、`frontmatter_end`（行位置定位，非 YAML 解析） | PASS（偏离已记录） |
| R11 | ship_gate.py 保留 duplicate-key/tab-indent 预扫描 | `ship_gate.py:1028-1120`（原始文本预扫描在 yq 之前执行，含 duplicate-key 计数和 tab-indent 检测） | PASS |
| R12 | 7 份 `_yq()` 一致性 golden test | `hack/tests/test_yq_wrapper_consistency.py`（TARGETS 字典覆盖 7 个文件、`assert len(paths) == 7`、13 条 CORE_PATTERNS 正则结构断言 + 3 个 fail-loud 专项测试） | PASS |
| R13 | yq 写操作值传递安全 | 全仓无 `_yq(..., in_place=True)` 调用。唯一写操作 `_set_schema_key` 不经 yq/shell（纯 Python 正则替换），无注入面 | PASS（注入面不成立） |

## Tasks 核对

| Task | 描述 | 状态 |
|---|---|---|
| 1 | 依赖预检系统 | PASS -- `setup.sh:498-585` |
| 2 | init.py YAML 改为 yq | PASS -- `init.py:421+` `_yq()` 封装 + 消费点迁移（`_schema_from_config`/`_set_schema_key` 偏离已记录） |
| 3 | impl_route.py YAML 改为 yq | PASS -- `impl_route.py:62+` `_yq()` + `:192`/`:255` 调用点 |
| 4 | ship_gate.py frontmatter 改为 yq | PASS -- `ship_gate.py:211+` `_yq()` + R11 预扫描 + `:1122` yq 取值 |
| 5 | anchor_lint.py YAML 改为 yq | PASS -- `anchor_lint.py:20+` `_yq()` + `:193` 调用点，bundle 副本同步 |
| 6 | roadmap_writeback + sad_schema 改为 yq | PASS -- `roadmap_writeback_draft.py:36+`/`sad_schema.py:158+` `_yq()` + 消费点迁移 |
| 7 | ADR + 收尾 | PASS -- ADR 0036 存在，手搓函数 grep 验证通过 |
| 8 | CI + golden test + 测试修订 | PASS -- `mechanical-gates.yml` 钉 yq v4.53.3，golden test 覆盖 7 份 |

## Tickets 轨聚合覆盖（task6-verification.md）

| 层 | 命令 | 退出码 | SHA |
|---|---|---|---|
| unit | `python -m pytest -q` | 0 | 64e5761 |

- 2579 passed, 82 skipped, 3 xfailed
- 2 failed 均为既有红测（`git stash -u` 复跑确认改动前即红），非本 change 引入：
  1. `test_scaffold.py::test_verify_lane_surfaces_make_overriding_warning` -- sdflow-devenv 相关
  2. `test_hack_shell_multibyte_guard.py::test_no_unbraced_variable_before_non_ascii[setup.sh]` -- bash 变量格式静态检测

## 缺口清单

### Minor 缺口

1. **R10 spec scenario 的 grep 命令字面不满足**：spec.md 列出的 grep 模式在目标脚本中命中 5 处函数名（`_schema_from_config`/`_set_schema_key`/`_marker_schema`/`frontmatter_end`/`read_verify_state`），但每一处都有充分的保留理由且在 impl-report 中已记录：2 处因 yq bug 刻意不迁（有界语法面）、2 处入口名保留但内部已改用 yq、1 处是行位置定位非 YAML 解析。**Spec scenario 的字面 grep 要求与实际合理偏离之间存在文本矛盾，但功能目标（消除手搓 YAML 解析器）已达成。**

2. **task6 报告 SHA 为 `64e5761`**（Task 5 收尾时的 checkpoint），后续又有两个 chore commit（`c0f40ed`、`8a8d9af` 标记验收复选框），当前 HEAD 为 `d344061`。这三个 commit 仅改 tasks.md 复选框，不涉及代码变更，覆盖仍有效。

### 核心缺口

无。

## 结论

**PASS** -- 全部 13 条需求均已实现或有充分记录的合理偏离。7 个脚本的 YAML 解析核心已统一委托 yq，业务逻辑保留在 Python 侧。CI 钉版本、golden test 守一致性、fail-loud 全覆盖。2579 项测试通过，0 本 change 回归。
