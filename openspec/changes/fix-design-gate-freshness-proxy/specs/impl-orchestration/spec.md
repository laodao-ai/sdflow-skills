## ADDED Requirements

### Requirement: implementer dispatch 携带信号权威归属声明

`sdflow-implement` 派发 implementer / fix 子代理时，dispatch prompt SHALL 携带一份**信号权威表**，正面声明「完成信号写哪里」与「设计工件不可碰」——子代理跑在 fresh context，看不见 SKILL.md 与 CLAUDE.md，未声明即等同未约束。

声明 SHALL 为正面陈述（列出权威归属），MUST NOT 仅写成禁令清单——禁令只挡列举到的那一种越界，权威表挡的是整个范畴。

本要求的适用面 SHALL 限于本仓自有的 `sdflow-implement`；第三方实现 skill（superpowers `subagent-driven-development`、matt `implement`）不受本要求约束，故本要求 MUST NOT 被当作设计门失鲜问题的唯一防线（机械防线在 `spec-workflow` 的设计门新鲜度内容判据）。

#### Scenario: dispatch prompt 含信号权威表

- **WHEN** `sdflow-implement` 执行模式派发 implementer 或 fix 子代理
- **THEN** prompt MUST 含信号权威表，至少覆盖两行归属：完成信号 = `superpowers-plan.md` 验收复选框 + `checkpoint(<change>:task<N>-<slug>)` 标签；设计工件 = `proposal.md` / `design.md` / `tasks.md` / `specs/`，实现期不修改
- **AND** 该表 MUST 与 `ship_gate.py` 实际消费的完成判据一致（plan 复选框 + checkpoint 标签），MUST NOT 声明 gate 并不读取的信号源

#### Scenario: 权威表缺席不得静默降级

- **WHEN** 因 SKILL 裁剪或模板漂移导致 dispatch prompt 未携带信号权威表
- **THEN** 该缺席 MUST NOT 被当作「已由 gate 兜住所以无所谓」——gate 的监视集分流只消解失鲜误判，不阻止 implementer 写脏设计工件；本要求与 gate 侧要求 SHALL 各自独立成立
