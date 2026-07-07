## ADDED Requirements

### Requirement: 总览表 row 字段 table-cell-safe（写时 reject 守盘面完整性）

issues 池 recorder（`buglist.py` / `todolist.py` / `issues.py`）以 markdown 表存状态总览（「盘面即状态」的盘面），其行按 `|` 切列。recorder SHALL 保证：**任何把字段写入总览管道表 row 的写路径**，字段含 ASCII `|` **或**换行（会致列错位 / 整行截断而腐蚀盘面）时 MUST 拒绝写入（`_die` 报清晰错误，复用既有 priority/status 非法即拒的写时校验惯例），MUST NOT 静默转义或替换。**写路径须全覆盖**〔spec-review-amendment C1〕：不止 `add`——`triage`（写 batch 列）、`rename`（retag 成员的 new_key 列）同样把字段写进管道表，MUST 一并守；`batch add` 写的 `batches.md` batch key MUST 同样拒 `|`/换行（防含腐蚀字符的 key 经 triage/retag 流入管道表）。校验 MUST 施于**各命令入口的原始用户参数**，MUST NOT 施于行拼接 sink（`" | ".join(cells)` 在 split 之后、`|` 已被切走，挂 sink 永不触发 = 假覆盖）。详细块 prose 字段（现象/根因/修复）不受此约束（非 `|` 分隔）；但块专用 `title` 进块头 `## id: title`，其**换行**MUST 一并守（防块头孤儿行）〔C7〕。**batch key 是 slug〔spec-review-amendment OV-2〕**：`batches.md` header `### {key} — {title}` 用 ` — ` 作分隔，故 batch key MUST 过 slug 校验（拒 `|`、换行、` — `、首尾空白），施于 `batch add`/`triage --批次`/`rename new_key` 三处。**自定义 `id`〔OV-3〕**：显式传入的 `id` MUST 符合 ID 语法（`ID_RE`）且不与既有 ID 重复（`parse_table_rows` 按 ID 建 dict、重复即静默丢行），否则 `_die`；`scan` MUST 报告同池重复 ID。此为写时 fail-closed 守卫，非事后解析补救。

#### Scenario: 字段含 `|` 或换行被写时拒绝

- **WHEN** 记录或回写一条 item，其 `summary` / `module` / `change` / batch key 含 ASCII `|` 或换行
- **THEN** recorder 以清晰错误拒绝写入（`_die`），不产生任何列错位 / 行截断的腐蚀盘面，并提示改写

#### Scenario: triage / rename 写路径同样被守（非只 add）

- **WHEN** `triage` 给 item 打一个含 `|`/换行 的批次名，或 `rename` 把批次改成含 `|`/换行 的 new_key
- **THEN** recorder 在这两条写路径同样 `_die` 拒绝（不只 `add`），管道表 `cells[7]` 不被腐蚀

#### Scenario: 详细块 prose 不受 table-cell-safe 约束

- **WHEN** 一条 item 的详细块字段（现象 / 根因 / 修复等 prose）含 `|` 或换行
- **THEN** 正常写入（详细块非 `|` 分隔表、无腐蚀风险），不被拒绝

### Requirement: reindex 一致性问题可观测且不阻断重建

`issues.py reindex` SHALL 把子进程 `scan` 报出的表↔块一致性 problems **回显到 stderr**（逐条带 pool / 文件定位），使独立跑 reindex 时的不一致对用户可见（兑现 D5 承诺）。**默认**：problems 非空 MUST NOT 使 reindex 失败——INDEX SHALL 照常确定性重建、退出码为 0（不因一个坏块阻断整池刷新）。reindex SHALL 提供 **`--strict`** 选项：problems 非空时以**非 0 退出码**结束，供非交互调用 / 收尾门做 enforcement——防非交互场景（sweep / hook / CI）stderr 被吞 + 默认 exit 0 致一致性问题**静默蒸发**（反静默元原则）。**致命错误**（无法读取文件等）无论是否 `--strict` 仍以非 0 退出（与一致性警示分层）。**读侧盘面完整性〔spec-review-amendment OV-1〕**：`scan` MUST 校验总览行 arity（当前 8 列 / 旧格式 7 列之外一律入 `problems`）——否则无块坏行的列错位腐蚀不进 `problems`、reindex 回显与 `--strict` 皆抓不到（T2 写侧防之外须有读侧检测，二者合成完整盘面完整性）。

#### Scenario: problems 回显 stderr 但不阻断 INDEX 重建

- **WHEN** 池中某 dated 文件存在表↔块不一致，运行 `issues.py reindex`
- **THEN** 每条 problem 逐条出现在 stderr（含 pool / 文件定位），INDEX 仍被完整重建，退出码为 0

#### Scenario: 独立跑 reindex 时不一致不再静默

- **WHEN** 不经 `scan`、直接运行 `reindex`，且池中存在表↔块不一致项
- **THEN** 用户从 stderr 看到具体不一致项（而非静默重建、不一致被吞）

#### Scenario: --strict 下 problems 非空即非 0 退出

- **WHEN** 以 `reindex --strict` 运行且池中存在表↔块不一致项
- **THEN** problems 回显 stderr 后以**非 0 退出码**结束（供非交互 / 收尾门 enforcement）；同一不一致下默认（无 `--strict`）仍 exit 0、INDEX 照常重建
