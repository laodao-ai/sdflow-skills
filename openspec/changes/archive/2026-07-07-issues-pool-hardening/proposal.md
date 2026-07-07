## Why

issues 池 recorder（`issues.py` 跨池命令 + `buglist.py` / `todolist.py` per-type recorder）积了一批已识别的健壮性缺口（`batches.md` 批次 `issues-pool-hardening`，成员 T1-T5）：字段含 `｜` 会破 markdown 表的位置解析、读错列 → 静默数据腐蚀（T2，系统性）；独立跑 `reindex` 时表↔块不一致对用户不可见（T1）；终态集跨脚本无守卫、未来改终态码会静默漂移（T3）；`batch` 操作非幂等易误用（T4）；recorder 行定位逻辑 4 处重复、WONTDO / 0 成员分支无测试（T5）。这些同属 issues.py/recorder 一个 capability，是 batch-triage 判据下的「相关合批」（同 cap ∧ 高耦合 ∧ 低增量，AND 门三腿净），一 change 一轮评审清完最省固定循环成本。

## What Changes

- **T2（数据完整性·系统性 correctness）**：recorder 写入前对字段（`module` / `summary` / 批次名等）里的 `｜` 统一转义（或拒绝含 `｜` 的字段），杜绝位置解析读错列的静默腐蚀。
- **T1（可观测性）**：`issues.py reindex` 把子进程 `scan` 报出的 problems 回显到 stderr——独立跑 reindex 时表↔块不一致对用户可见（兑现 D5 承诺）。**本 change 交付的即此 stderr 回显**；另加 `--strict` opt-in flag 作为 T2.5 follow-up 的**预置接口**——本 change 内**无消费者、不产生 enforcement 价值**，不记作"已堵非交互静默蒸发"〔spec-review Q1，见 design D2〕。
- **T3（一致性守卫）**：加终态集跨脚本一致性测试——`issues.py` 的 `TERMINAL_STATUSES` ⊆ 对应 recorder 的 `STATUS_CODES`，防未来改终态码时静默漂移。
- **T4（幂等）**：`batch add` 加 `--if-exists skip` 幂等选项；`batch rename` 后自动 `reindex`（或 SKILL 明示 rename 后须 reindex）。
- **T5（去重 + 测试）**：抽 `_find_row_file` 消除 `triage` 与 `set-status` 的定位逻辑重复（4 处）；补 WONTDO / 0 成员人标 IN_PROGRESS 的分支测试。

## Capabilities

### New Capabilities

（无——recorder / issues 池能力已由 `spec-workflow` 承载，本 change 不新建能力）

### Modified Capabilities

- `spec-workflow`: recorder 债务池需求补两处 spec-level 行为——①**字段内容安全**（含 `｜` 字段须转义/拒绝防列腐蚀，T2）；②**reindex 一致性问题可观测**（子进程 problems 回显 stderr，T1）。T3/T4/T5 是既有需求下的实现健壮化（守卫测试 / 幂等选项 / 去重重构），不改 spec-level 需求，只落 tasks。

## Impact

- **代码**：`sdflow-issues/scripts/issues.py`（reindex problems 回显、`batch --if-exists`、rename auto-reindex、`_find_row_file` 抽取落点之一）、`sdflow-buglist/scripts/buglist.py` + `sdflow-todolist/scripts/todolist.py`（字段 `｜` 转义、`_find_row_file` 去重、终态集常量守卫）。
- **测试（数据类纪律：改 scripts 必跑对应 tests）**：三 recorder 各自 `tests/` 新增 `｜` 转义、终态集守卫、WONTDO / IN_PROGRESS 分支、幂等 batch 用例。
- **无下游 bundle 影响**：recorder 是 repo-local sdflow skills，不经 `resolve-workflow.sh` 下发、不碰 `sdflow-init/assets/workflow/`，故不涉回灌纪律。
- **向后兼容风险**：T2 转义须对既有含 `｜` 数据向后兼容——转义只改存储表示、不改语义；实现前须扫现有池确认无破坏，并定义读路径对旧未转义 `｜` 的容错。
