## 1. T2 字段 `|` 安全（系统性 correctness，先做——最基础 + 最高风险）

- [ ] 1.1 pre-flight：扫现有 `openspec/issues/**` 确认有无既存**未转义裸 `|`** 腐蚀行，记录基线（design 风险「现有池可能已有裸 `|`」的缓解前提）
- [ ] 1.2 写失败测试（TDD）：含 ASCII `|` 字段 write→read 往返逐字节一致——`buglist.py` / `todolist.py` / `issues.py` 三 recorder 各一例
- [ ] 1.3 写失败测试：旧**未转义裸 `|`** 历史行解析 fail-safe（不抛异常、尽力还原、不二次腐蚀）
- [ ] 1.4 实现：写路径把字段值 `|`→`\|` 转义；三处解析器 `strip("|").split("|")`（`buglist.py:293` / `todolist.py:282` / `issues.py:678`）改为**按未转义 `|` 切列** + 读出反转义
- [ ] 1.5 跑三 recorder `tests/` + 全套件回归，确认绿（转义往返 + 旧裸 `|` 容错用例通过）

## 2. T1 reindex 一致性问题回显 stderr

- [ ] 2.1 写失败测试（TDD）：制造表↔块不一致 → `issues.py reindex` 把 problems 逐条回显 stderr（带 pool/文件定位）、exit 0、INDEX 仍重建
- [ ] 2.2 实现：reindex 收集子进程 `scan` 的 problems 非空即回显 stderr；**不因 problems 改 exit code**（致命错误仍走既有非 0 退出，分层）
- [ ] 2.3 跑 `sdflow-issues/tests/` + 相关，确认独立跑 reindex 时不一致不再静默

## 3. T3 终态集跨脚本一致性守卫测试

- [ ] 3.1 加测试：`import` 三脚本常量，断言 `issues.py` 的 `TERMINAL_STATUSES` ⊆ `buglist.py` / `todolist.py` 各自 `STATUS_CODES`（终态码重命名即测试红）
- [ ] 3.2 跑测试确认现状通过（守卫就位；此为纯新增测试、不改生产逻辑）

## 4. T4 batch 操作幂等

- [ ] 4.1 写失败测试（TDD）：`batch add --if-exists skip` 重复调 no-op 退出 0；`batch rename` 后 INDEX/`batches.md` 成员行已自动同步（auto-reindex）
- [ ] 4.2 实现：`batch add` 加 `--if-exists skip`（已存在同 key → no-op exit 0）；`batch rename` 成功后自动调 `reindex`（失败时不触发）
- [ ] 4.3 跑 `sdflow-issues/tests/`，确认幂等 + rename 后无 INDEX 陈旧

## 5. T5 定位逻辑去重 + 分支补测

- [ ] 5.1 抽 `_find_row_file`：`buglist.py` / `todolist.py` **各自模块内**抽 helper，替换 `cmd_set_status` 与 `triage` 的行定位 dup（design D4：不跨 recorder 强行共享）
- [ ] 5.2 核对 `issues.py:cmd_batch_set_status` 是否同 dup（design Open Question）——是则纳入、否则记明不纳入
- [ ] 5.3 补测试：WONTDO 分支 + 0 成员人标 IN_PROGRESS 分支
- [ ] 5.4 跑三 recorder `tests/`，确认去重无行为回归

## 6. 收尾验证

- [ ] 6.1 全套件 `pytest` 全绿（含本 change 全部新增用例）
- [ ] 6.2 T1-T5 逐项 `/sdflow-todolist` set-status DONE（关联 change `issues-pool-hardening` + commit）
- [ ] 6.3 delta spec 对码核验：`specs/spec-workflow/spec.md` 两个 ADDED 需求（T2 字段安全 / T1 reindex 可观测）与实现逐条对齐，无悬空 Scenario
