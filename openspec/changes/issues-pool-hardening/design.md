## Context

issues 池 recorder 三脚本（`buglist.py` / `todolist.py` per-type + `issues.py` 跨池）用 markdown 表存状态总览。三者的行解析**全是 naive `line.strip().strip("|").split("|")`**（`buglist.py:293` / `todolist.py:282` / `issues.py:678`）——字段值里只要有一个 ASCII `|` 就多切一列、后续列全错位（静默数据腐蚀，T2）。`issues.py` 不 import 两 recorder 模块（subprocess 调用），三者**无共享代码模块**；`_find_row_file` 目前**不存在**，T5 要新抽（现 dup 在 `buglist.py`/`todolist.py` 各自的 `cmd_set_status` + triage 行定位）。本 change 是 issues.py/recorder 一个 capability 的健壮化合批，不碰 `assets/workflow/` bundle、不下发下游。

## Goals / Non-Goals

**Goals:**
- 消除字段 `|` 致列错位的静默腐蚀（T2）——写路径安全化 + 解析器按未转义 `|` 切列 + 读路径对旧裸 `|` 容错。
- reindex 一致性问题可观测（T1）、终态集漂移有守卫（T3）、batch 操作幂等（T4）、定位逻辑去重 + 分支补测（T5）。
- 严格 scope = T1-T5，不扩张到其它 recorder 面。

**Non-Goals:**
- 不重构表存储格式（不换 CSV/JSON——markdown 人读表是既定契约）。
- 不把三 recorder 合并成一个共享框架（跨模块大重构超出 scope；T5 只去局部 dup）。
- 不碰 bundle / workflow 规则 / 下游回灌。

## Decisions

### D1（T2）字段 `|` 用**转义**（`\|`），解析器改按未转义 `|` 切列
- **选**：写路径把字段值里的 ASCII `|` 转义为 `\|`；三处解析器从 `split("|")` 改为**按未转义 `|` 切列**（`\|` 不作分隔符），读出后反转义还原。
- **弃**：①**拒绝**含 `|` 的字段（fail-closed）——丢数据、挡掉合法含管道的描述（如命令行 `a | b`），用户敌对；②**替换为全角 `｜`**（U+FF5C）——无需改解析器但**有损**（无法还原原文 ASCII 管道），对"记录真实命令/日志"的债务字段不可接受。
- **理由**：转义是 markdown 标准（`\|` 渲染即 `|`），无损可逆；解析器改动虽牵动三处读路径，但那正是位置解析正确性的根，值得一次修对。

### D2（T1）reindex problems 回显 stderr，但**不因 problems 变红**
- **选**：`reindex` 收集子进程 `scan` 报出的 problems，非空则逐条回显 stderr（带 pool/文件定位），**exit code 保持 0、INDEX 照常重建**。
- **弃**：problems 非空即 exit 非 0——会让"某个块坏了"阻断整池 INDEX 刷新，因噎废食。
- **理由**：一致性问题要**可见**（兑现 D5 承诺）但不该阻断重建；致命错误（无法读文件等）仍走既有非 0 退出，与"数据不一致警示"分层。

### D3（T4）`batch add --if-exists skip` 幂等 + `batch rename` 末尾 auto-reindex
- **选**：`--if-exists skip` → 已存在同 key 时 no-op 退出 0（非报错）；`rename` 成功后自动调 `reindex`（成员 tag 已变，INDEX/batches 成员行须同步）。
- **弃**：rename 后仅在 SKILL.md 提示"记得 reindex"——靠人记不可靠，漏 reindex 留 INDEX 陈旧。
- **理由**：幂等选项让脚本可安全重跑（CI/自动化）；auto-reindex 把"rename 必致 INDEX 陈旧"从人纪律降为脚本保证。

### D4（T5）`_find_row_file` **各 recorder 内抽**，不强行跨模块共享
- **选**：在 `buglist.py` / `todolist.py` **各自内部**抽一个模块内 `_find_row_file` helper，消 `cmd_set_status` 与 `triage` 的定位 dup。
- **弃**：抽到一个新的跨 recorder 共享模块并让三脚本 import——现三者刻意无共享依赖（issues.py subprocess 调），引入共享 import 是新耦合，收益（消 4 处 dup）不抵架构代价。
- **理由**：低耦合优先；若实现时发现两 recorder 的定位逻辑**逐字节相同**且未来会同步演化，可再议提共享——但默认各自抽。

## Risks / Trade-offs

- **[T2 解析器改动牵动三处所有读路径]** → 全套件回归 + 新增**转义往返测试**（write→read 幂等：含 `|` 字段存取还原一致）；三 recorder 各测一遍。
- **[T2 向后兼容：现有池可能已有裸 `|` 腐蚀行]** → 实现前扫现有池确认；读路径对**旧裸 `|`** fail-safe（尽力解析、不 crash、不再二次腐蚀），加专门容错测试。
- **[T3 守卫测试要枚举各 recorder 终态集常量]** → 测试直接 import 三脚本的 `TERMINAL_STATUSES`/`STATUS_CODES` 做子集断言，常量重命名即测试红（正是目的）。
- **[T4 auto-reindex 扩大 rename 副作用面]** → reindex 已验证幂等，副作用可控；rename 失败时不触发 reindex（先成功后同步）。

## Migration Plan

- 无 schema/目录迁移。T2 落地后若扫到现有裸 `|` 数据：读路径容错即可覆盖（不强制一次性迁移）；若选一次性转义现有数据，作为独立幂等步、可回滚（git）。
- 回滚：本 change 纯 repo-local 脚本 + 测试，`git revert` 即恢复；无下游/bundle 影响面。

## Open Questions

- T2：是否需要对**批次名**（`batches.md` 的 key、进 `|` 表列）同样施加 `|` 转义/拒绝？倾向拒绝（批次 key 应是干净 slug，含 `|` 本就异常）——待 spec/实现时定。
- T5：`issues.py` 的 `cmd_batch_set_status` 是否也共享同一 dup？接地看它是独立路径（`issues.py:611`），暂不纳入 `_find_row_file` 抽取，待实现核对。
