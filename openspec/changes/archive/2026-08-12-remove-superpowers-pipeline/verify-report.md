---
ship-gate:
  verify: PASS
  reviewed_sha: 55afb53ae7ad453b9e35627d500105a2f38075a9
---

# Verify Report: remove-superpowers-pipeline

## 核对方法

逐条比对 tasks.md 的 6 张 ticket（含收尾票）与 specs/ 三个 delta（impl-orchestration、spec-workflow、yq-yaml-operations）的每条需求，以代码 grep/read 为证据源，每条 PASS 附机验锚点（测试名 / commit / file:line）。全仓 pytest 在 HEAD 重跑确认。

## 逐需求核对表

### R1 — 阶段三派发直连 sdflow-implement（唯一管线）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| route 子命令与全部路由函数删除 | PASS | `sdflow-implement/scripts/impl_route.py` 无 `_cmd_route`/`read_config_pipeline`/`read_plan_marker`/`resolve_pipeline`/`LEGAL_PIPELINES`/`RouteStop`/`_get_plan_sha` 定义 |
| `_yq` 及仅为其服务的 import 删除 | PASS | `impl_route.py` 无 `_yq` 函数定义（仅 docstring 注释） |
| `test_yq_wrapper_consistency.py` 成员表去 impl_route | PASS | `hack/tests/test_yq_wrapper_consistency.py:61-72` TARGETS 仅 5 条 |
| route/config/marker 测试退役 | PASS | `sdflow-implement/tests/test_impl_route.py:13-16` docstring 确认 |
| 保留半场接口逐字不变 | PASS | `parse_blocked_by`:83, `TopoError`:75, `BLOCKED_BY_RE`:69 定义在 impl_route.py |
| gate sibling-import 回归 | PASS | `test_gate_closing_ticket.py` 8 用例全绿 |
| ship 链序无路由直连派发 | PASS | `sdflow-ship/SKILL.md:167-170` 直连 `sdflow-implement mode=tickets-plan/tickets-exec` |

### R2 — 出 ticket 模式（tickets.md 单名）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| `PLAN_FILENAMES = ("tickets.md",)` | PASS | `ship_gate.py:1346` |
| 遗留旧名兜底 fail-closed | PASS | `ship_gate.py:1347-1370` `LegacyPlanNameFound` + `:1722-1724` emit UNKNOWN |
| 计划文件 frontmatter 含且仅含 `impl-pipeline: tickets` | PASS | `tickets.md:1-3` |
| 收尾票存在（R-ID: all, Blocked-by 全部功能票号） | PASS | `tickets.md:124-133` Task 6, Blocked-by: 1,2,3,4,5, R-ID: all |
| 收尾票 impl-report 证据 schema 齐全 | PASS | `impl-reports/task6-verify.md` 三层各一行、SHA 一致 |

### R3 — 执行模式宿主条件化受限并行（交叉引用换名）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| 保留半场接口不变（parse_blocked_by / TopoError / BLOCKED_BY_RE） | PASS | 同 R1 锚 |
| frontier/topo 测试保留全绿 | PASS | `test_impl_route.py` 35 用例全绿（commit `ff00ea0`） |

### R4 — ticket 文件兼容 ship_gate 既有完成判据契约

| 条目 | 判定 | 证据锚 |
|---|---|---|
| 完成判据窗口锚 `tickets.md` | PASS | `ship_gate.py` `git log --diff-filter=A` 路径为 resolver 返回的 tickets.md |
| 收尾票无条件校验 | PASS | `ship_gate.py:1746-1750` `plan_closing_ticket_check()` 无条件调用 |

### R5 — implementer dispatch 携带信号权威归属声明

| 条目 | 判定 | 证据锚 |
|---|---|---|
| dispatch prompt 含信号权威表 | PASS | `sdflow-implement/SKILL.md` 信号权威表在 dispatch 模板中 |

### R6 — 管线路由 / 试点回退 / 熔断哨兵 REMOVED

| 条目 | 判定 | 证据锚 |
|---|---|---|
| route 子命令物理删除 | PASS | 同 R1 |
| 存量 `impl-pipeline` 键无读取方 | PASS | grep `impl-pipeline` 在 scripts 中无读取（ship_gate 零 config 依赖） |

### R7 — 阶段三过设计门后连续自动跑到 merge（tickets 唯一管线）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| step6-writing-plans.md 删除 | PASS | 文件不存在 |
| 守卫测试名单去 step6 | PASS | `test_checkpoint_slug_coverage.py:82` MIN_CALLSITES 16->15 |
| 六份 bundle 资产收口 | PASS | workflow.md/WORKFLOW-GUIDE.md/ff-generation-constraints.md/config.template.yaml/claude-section.md/quality-layering.md 无 superpowers 运行时引用 |
| 现役视图文档同步 | PASS | workflow-overview/workflow-map/workflow-console/criteria-mechanization-tracker 已清理 |

### R8 — 阶段三编排台账确定性（计划文件名术语）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| gate 契约表 next 字段更新 | PASS | `ship_gate.py:42-48` RUN_PLAN/CONTINUE_IMPL next=sdflow-implement（code-review 自动修复） |

### R9 — 失鲜判定（计划文件名术语）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| 监视集定位经 resolver 使用 tickets.md | PASS | `ship_gate.py` resolver 返回 tickets.md 路径 |

### R10 — impl-pipeline 缺省为 tickets REMOVED

| 条目 | 判定 | 证据锚 |
|---|---|---|
| 本仓 `openspec/config.yaml` 无 `impl-pipeline` 键 | PASS | config.yaml 顶层键仅 schema/context/rules/operations/metrics |

### R11 — yq-yaml-operations delta（impl-pipeline Scenario 删除）

| 条目 | 判定 | 证据锚 |
|---|---|---|
| 主 spec Purpose 去 `impl_route.py` | PASS | `openspec/specs/yq-yaml-operations/spec.md:3-13` 列 5 脚本 |
| `test_yq_wrapper_consistency.py` 成员表去 impl_route | PASS | 同 R1 锚 |

## 全仓测试

```
/usr/bin/python3 -m pytest
2560 passed, 10 skipped in 360.69s
```

SHA: `55afb53ae7ad453b9e35627d500105a2f38075a9`（HEAD，含 code-review 自动修复 2 提交）

10 skipped 为既有条件跳过，非本 change 引入。

## Success Metrics 第三条（ship 直连 e2e）

**事后锚**——由下一真实 change 的 `/sdflow-ship` 首跑承接。本 change 无法自验 ship 链序 e2e（需一个新的 change 走完整阶段三），此为 tasks.md 5.3 显式登记的已知时效缺口，MUST NOT 留白或假绿。

## 缺口清单

无缺口。
