### Task 1: 路由切除与保留半场回归

**Blocked-by:** none
**R-ID:** R1, R6

从 `sdflow-implement/scripts/impl_route.py` 切除全部路由函数与 `route` 子命令：删除 `_cmd_route` / route subparser / `read_config_pipeline` / `read_plan_marker` / `resolve_pipeline` / `LEGAL_PIPELINES` / `_PIPELINE_KEY_RE` / `RouteStop` / `_get_plan_sha`、`_yq` 及仅为其服务的 import；文件头注释从「管线路由三跳」改写为 tickets 调度 helper 自述。

同步测试：`test_impl_route.py` 的 route/config/marker 参照系用例退役（断言目标态已不存在的行为），frontier / task-text / 拓扑用例保留并全绿。`test_yq_wrapper_consistency.py` 成员表去 impl_route 条目（`_yq` 随路由删除退出消费面）。

核验保留半场接口逐字不变：`parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE` 签名与行为零改动，gate sibling-import 回归绿（`test_gate_closing_ticket.py` 保留用例通过）。

- [ ] `impl_route.py` 路由函数与 `route` 子命令已删除，文件头注释已改写
- [ ] `_yq` 及仅为其服务的 import 已删除
- [ ] `test_impl_route.py` 路由相关用例已退役，保留半场用例全绿
- [ ] `test_yq_wrapper_consistency.py` 成员表已去 impl_route 条目
- [ ] 保留半场接口（`parse_blocked_by` / `TopoError` / `BLOCKED_BY_RE`）签名与行为零改动
- [ ] `test_gate_closing_ticket.py` 保留用例（gate sibling-import）通过

