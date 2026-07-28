### Task 3: 计划文件名共享 resolver（机械核心，双存在 fail-closed）

**Blocked-by:** none
**R-ID:** R-tickets（出 ticket 模式产出 tracer-bullet ticket）, R-stage3（阶段三过设计门后连续自动跑到 merge）

**交付的行为**：gate 与 route helper 经**同一份**共享 resolver 定位计划文件——按序探测新名与旧名，命中其一即用之，两者同时存在 **fail-closed 判 UNKNOWN**（不猜），都不存在判 RUN_PLAN。文件名只用于定位，**MUST NOT 参与轨道路由判定**（路由权威仍是 config 键 + frontmatter marker）。同时把「在途 plan 不可改名」这条正确性要求钉上机械用例。

工作清单权威见 `tasks.md` §5.1、§5.2、§5.3、§5.10 与 §5.7 的**新增用例**部分；决策依据见 `adr/0033`（本票不写 ADR，见 Task 4）。

要点提醒：resolver 是单一源，两处 import 同一份，**MUST NOT 手抄第二份**；`impl_route.py` docstring 里指向 archive 归档文件的两处实路径**不改**（它们指的是真实存在的历史文件）。

- [ ] resolver 落地并被 gate 与 route helper 共同 import（无第二份手抄）
- [ ] 双存在 ⇒ fail-closed UNKNOWN，提示人工删除其一
- [ ] 仅旧名存在 ⇒ 照常识别（在途/他轨向后兼容）；两名皆无 ⇒ RUN_PLAN
- [ ] `[e2e]` 改名窗口用例：造「改名前有 task1 checkpoint、改名后跑 gate」的 fixture，断言 gate **不会**漏数 task1（或断言该场景被显式拒绝）——`plan_first_sha` 用 `--diff-filter=A`，不跟随重命名
- [ ] 既有 gate / route 测试全绿（本票不改测试里的文件名字面量，那属 Task 4）

---

