# token-snapshot-anchor Delta Specification

## Purpose

checkpoint 级 token 快照锚：在每次 checkpoint 提交时机械采集当前会话的 token 用量累计值，落为 change 目录内的只追加 JSONL 锚文件，为 retro 的 per-change token 维提供机械数据源；采集失败一律显式降级为无锚行，MUST NOT 伪造计数、MUST NOT 影响 checkpoint 主功能。

## ADDED Requirements

### Requirement: checkpoint 快照采集与同 commit 入库

checkpoint 过场提交 SHALL 在暂存（`git add -A`）之前采集一次 token 快照：定位当前会话 transcript（优先宿主注入的 session 身份环境变量精确命中，缺席则以本仓 transcript 目录内 mtime 最新文件回退），累加全部 assistant message 的 usage 四计数（input / output / cache_read / cache_creation）与 message 数，向 `openspec/changes/<change>/token-log.jsonl` 追加一行 `anchor=true` 快照（含 schema 版本、时间戳、step、session 标识、host、累计 usage），使快照随同一个 checkpoint commit 入库。`<change>` 由当前分支名 `feat/<change>` 解析且对应 change 目录存在时才写。

#### Scenario: 正常采集随 commit 入库

- **WHEN** 在 `feat/<change>` 分支（`openspec/changes/<change>/` 存在）上执行 checkpoint，且当前会话 transcript 可读
- **THEN** 该 checkpoint commit 包含 `openspec/changes/<change>/token-log.jsonl` 的一行新增 `anchor=true` 记录，其 usage 四计数为该 session 自启动以来的累计值（非区间差），`step` 等于 checkpoint 的 step 参数

#### Scenario: 无 change 落点静默跳过

- **WHEN** 在保护分支或分支名无法解析出存在的 change 目录时执行 checkpoint
- **THEN** 不写任何快照文件，checkpoint 其余行为与快照机制引入前逐字节一致

### Requirement: 采集失败显式降级且不挡 checkpoint

快照采集的任何失败（transcript 缺失、解析失败、无 transcript 宿主如 Codex）SHALL 降级为一行 `anchor=false` 记录并携带机器可判的 `reason` 枚举值（至少含 `no-transcript` / `parse-error`），MUST NOT 伪造或估算计数；采集组件整体缺席或崩溃时，checkpoint 主功能（判空跳过 / add / commit）SHALL 不受任何影响。

#### Scenario: 无 transcript 宿主写无锚行

- **WHEN** 在无本会话 transcript 的环境（如 Codex 宿主）中于活动 change 分支执行 checkpoint
- **THEN** token-log.jsonl 追加一行 `anchor=false` 且 `reason="no-transcript"` 的记录，无 usage 字段，checkpoint 提交正常完成

#### Scenario: 采集组件缺席时 checkpoint 照常

- **WHEN** 快照 helper 脚本不存在或执行崩溃（非零退出）
- **THEN** checkpoint 提交照常完成，退出码与提交内容不受 helper 影响（仅少一行快照）

### Requirement: 锚文件只追加、写侧无状态

token-log.jsonl SHALL 为只追加文件：每行自含 schema 版本号，usage 为 session 累计值，写侧 MUST NOT 读取或改写既有行、MUST NOT 维护任何区间差分状态（差分由读侧按 session 分组计算）。归档时该文件随 change 目录整体迁移冻结，读侧只读。

#### Scenario: 多次 checkpoint 各自独立追加

- **WHEN** 同一 change 在同一 session 内连续执行多次 checkpoint
- **THEN** token-log.jsonl 逐次各追加一行，先前行字节不变，各行 usage 单调不减（同 session 累计值）
