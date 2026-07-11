## ADDED Requirements

### Requirement: outside-voice 复用三判归约为单一 reason_code

校验器 SHALL 对 spec-review 复用 codex outside-voice 的三前置（来源 / 新鲜度 / 结构）按序判定，归约出**唯一** reason_code，取值属固定六枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source`。`none` = 三判全过（可复用），退出码 0；任一不过 = 对应原因码。

#### Scenario: mode=simulated 判无效
- **WHEN** `gstack-review.md` 的 `step1-broad-review` 锚 `mode="simulated"`
- **THEN** 输出 `simulated-source`，退出码非 0（不可复用）

#### Scenario: 产物陈旧
- **WHEN** 产物 mtime 早于传入的 `change_mtime`（`{change_dir}` 最新改动 epoch 秒）
- **THEN** 输出 `stale`

#### Scenario: codex 段不可解析
- **WHEN** `gstack-review.md` 存在但解析不出 codex findings 段
- **THEN** 输出 `section-not-found`（best-effort parse 失败 fail-closed 到此码，不崩溃）

#### Scenario: codex findings 为 0 条
- **WHEN** codex 段可解析但 findings 计数为 0
- **THEN** 输出 `zero-findings`

#### Scenario: 文件缺失
- **WHEN** `gstack-review.md` 路径不存在
- **THEN** 输出 `file-missing`

#### Scenario: 三判全过可复用
- **WHEN** mode=native 且产物不陈旧且 codex 段可解析且 findings>0
- **THEN** 输出 `none`，退出码 0

### Requirement: 输入契约门控外置、不自跑 subprocess

校验器 SHALL 只接收已备齐的原始事实作入参（`gstack-review.md` 路径 + `change_mtime`），MUST NOT 自行调用 `git` 或任何 subprocess，MUST NOT 读 config——保持 stdlib-only 纯函数可测。

#### Scenario: 无 subprocess 调用
- **WHEN** 校验器执行任意判定路径
- **THEN** 进程不 fork / exec 子进程；`change_mtime` 取自入参而非脚本内 `git log`

### Requirement: 坏输入 fail-closed

校验器 SHALL 对无法判定的坏输入（`step1-broad-review` 锚缺失、mode 非枚举值）以非零退出 + stderr 原因结束，MUST NOT 静默产出某个 reason_code 掩盖损坏。

#### Scenario: 锚缺失非零退出
- **WHEN** `gstack-review.md` 缺 `step1-broad-review` 锚或 mode 值不在 `native|simulated`
- **THEN** 退出码非 0，stderr 打印 `[outside_voice_guard] FAIL: <原因>`（区别于正常的 `simulated-source` 判定）
