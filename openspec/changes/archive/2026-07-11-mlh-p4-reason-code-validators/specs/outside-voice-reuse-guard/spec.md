## ADDED Requirements

### Requirement: outside-voice 复用三判归约为单一 reason_code

校验器 SHALL 对 spec-review 复用 codex outside-voice 的三前置（来源 / 新鲜度 / 结构）按序判定，归约出**唯一** reason_code，取值属固定六枚举 `none|file-missing|section-not-found|zero-findings|stale|simulated-source`〔spec-review Q-C：撤销 grill 的 `stale-dirty-tree`，回 6 码〕。`none` = 三判全过（可复用），退出码 0；任一不过 = 对应原因码。

#### Scenario: mode=simulated 判无效
- **WHEN** `gstack-review.md` 的 `step1-broad-review` 锚 `mode="simulated"`
- **THEN** 输出 `simulated-source`，退出码非 0

#### Scenario: 产物早于源文件（陈旧）〔spec-review Q-C〕
- **WHEN** 产物 `gstack-review.md` 的 fs-mtime 早于源文件（proposal/design/tasks/specs）最大 fs-mtime（**排除评审产物自身**：gstack-review.md / spec-review-report.md / .outside-voice/）
- **THEN** 输出 `stale`（fail-safe 重跑，非假新鲜复用陈旧审查）

#### Scenario: codex 段不可解析
- **WHEN** `gstack-review.md` 存在但解析不出 codex findings 段
- **THEN** 输出 `section-not-found`（best-effort parse 失败 fail-closed 到此码）

#### Scenario: codex findings 为 0 条
- **WHEN** codex 段可解析但 findings 计数为 0
- **THEN** 输出 `zero-findings`

#### Scenario: 文件缺失
- **WHEN** `gstack-review.md` 路径不存在
- **THEN** 输出 `file-missing`

#### Scenario: 三判全过可复用
- **WHEN** mode=native 且产物不早于源文件 且 codex 段可解析 且 findings>0
- **THEN** 输出 `none`，退出码 0

### Requirement: 新鲜度用源文件 fs-mtime 直比、纯 stdlib、门控外置〔spec-review Q-C·撤销 grill Q3〕

校验器 SHALL 用 `os.stat` 比较产物 fs-mtime 与源文件最大 fs-mtime 判新鲜度，MUST NOT 调 subprocess / git，MUST NOT 读 config——纯 stdlib、纯函数可测。〔grill Q3 曾反转为「自跑 git + `git status --porcelain` 全目录 dirty」，但全目录 dirty 含评审产物自身 → 守卫恒判 stale → 双 codex（冷镜 F1 揭穿反噬）；fs-mtime 源文件直比既根治「git-log 看不到未提交」之坑、又无需 git。〕

#### Scenario: 纯 stdlib 无 subprocess
- **WHEN** 校验器执行任意判定路径
- **THEN** 进程不 fork / exec 子进程；新鲜度用 fs-mtime 直比、不调 git

### Requirement: 坏输入 fail-closed

校验器 SHALL 对无法判定的坏输入（`step1-broad-review` 锚缺失、mode 非枚举值）以非零退出 + stderr 原因结束，MUST NOT 静默产出某个 reason_code 掩盖损坏。

#### Scenario: 锚缺失非零退出
- **WHEN** `gstack-review.md` 缺 `step1-broad-review` 锚或 mode 值不在 `native|simulated`
- **THEN** 退出码非 0，stderr 打印 `[outside_voice_guard] FAIL: <原因>`（区别于正常的 `simulated-source` 判定）
