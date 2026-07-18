## ADDED Requirements

### Requirement: sweep 的失配信号接进退出码，反静默成功

`issues.py sweep` 的 `problems`（盘面两套投影失配的诊断项）**SHALL** 参与退出码判定：`problems` 非空时 **MUST** 非零退出，**MUST NOT** 仅回显 stderr 后以 0 退出。

**红线取 `problems` 非空，MUST NOT 取 `tagged == 0`**——后者单独是合法幂等态（重跑时本就无未分诊项），拿它当红线会把正常重跑判红；而 `problems` 非空是「读到的盘面与预期投影失配」的**唯一确定性信号**，把它排除在退出码之外，等于把唯一告警降级成日志（承 `adr/0018` 机械校验器输出诚实性）。

**MAY** 提供显式逃生口（如 `--allow-problems`）供知情放行，缺省 **MUST** 为严格。

#### Scenario: 失配时非零退出

- **WHEN** `sweep` 执行过程中产生非空 `problems`
- **THEN** 命令非零退出，stderr 保留全部 problems 明细，调用方（`/sdflow-done` §2.1）据此停下而非静默继续

#### Scenario: 干净盘面上重跑不误红

- **WHEN** 盘面无失配、且本 change 的待分诊项已在上一次运行中全部 tag 完（`tagged == 0`、`problems` 为空）
- **THEN** 命令以 0 退出（幂等重跑不被判红）

#### Scenario: 逃生口须显式

- **WHEN** 调用方未传逃生口开关且 `problems` 非空
- **THEN** 命令非零退出；**仅当**显式传入逃生口时才以 0 退出，且 stderr 仍完整记录被放行的 problems
