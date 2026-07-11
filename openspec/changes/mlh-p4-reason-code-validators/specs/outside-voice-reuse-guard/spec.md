## ADDED Requirements

### Requirement: outside-voice 复用三判归约为单一 reason_code

校验器 SHALL 对 spec-review 复用 codex outside-voice 的三前置（来源 / 新鲜度 / 结构）按序判定，归约出**唯一** reason_code，取值属固定七枚举 `none|file-missing|section-not-found|zero-findings|stale|stale-dirty-tree|simulated-source`〔grill-amendment：新增 `stale-dirty-tree`〕。`none` = 三判全过（可复用），退出码 0；任一不过 = 对应原因码。

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

#### Scenario: 工作树 dirty 时 fail-safe 判陈旧〔grill-amendment〕
- **WHEN** `{change_dir}` 工作树有未提交改动（`git log` 时间不可信、无法确认新鲜）
- **THEN** 输出 `stale-dirty-tree`（保守重跑 outside-voice，非假新鲜复用陈旧审查）

### Requirement: 自跑 git 作新鲜度事实 owner、门控外置〔grill-amendment〕

校验器 SHALL 自跑 `git log -1 --format=%ct -- {change_dir}`（新鲜度）与 `git status --porcelain -- {change_dir}`（dirty 检测）作为「新鲜度事实」的天然 owner，用 git fixture 测；MUST NOT 读 config（门控外置）。〔初版曾要求「不自跑 subprocess、`change_mtime` 由 SKILL 传参」，grill Q3 反转：`git log` 看不到未提交改动的语义 bug 与谁跑 git 无关，且传参是把未测接缝挪进 SKILL prose。此为三校验器中唯一 subprocess 例外。〕

#### Scenario: 新鲜度事实自持可测
- **WHEN** 判新鲜度 / dirty
- **THEN** 脚本自跑 git 取事实（非依赖入参 mtime），行为由 git fixture 可复现测试锁定

### Requirement: 坏输入 fail-closed

校验器 SHALL 对无法判定的坏输入（`step1-broad-review` 锚缺失、mode 非枚举值）以非零退出 + stderr 原因结束，MUST NOT 静默产出某个 reason_code 掩盖损坏。

#### Scenario: 锚缺失非零退出
- **WHEN** `gstack-review.md` 缺 `step1-broad-review` 锚或 mode 值不在 `native|simulated`
- **THEN** 退出码非 0，stderr 打印 `[outside_voice_guard] FAIL: <原因>`（区别于正常的 `simulated-source` 判定）
