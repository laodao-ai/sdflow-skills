## ADDED Requirements

### Requirement: FF-0 未判定路径不对错仓执法且留下非越权审计

FF-0 PreToolUse hook SHALL 仅在 payload `cwd` 可安全作为命令作用仓时执行三分支判定。检测到可能改变工作目录的 shell 结构，或无法从单一创建调用读取唯一合法 change 名时，hook SHALL fail-open，但 SHALL 输出含 `additionalContext` 的 PreToolUse 结果说明“未判定”的具体原因。

该审计结果 MUST NOT 设置 `permissionDecision: allow`，以免把日志行为变成绕过宿主原生权限。实现 MUST NOT 解析 shell 以推断 `cd`、变量展开或实际作用目录。

#### Scenario: 跨仓 cd 调用
- **WHEN** Bash 命令在 payload `cwd` 外通过工作目录切换创建 OpenSpec change
- **THEN** FF-0 SHALL 不以 payload 仓的分支作 deny/allow 判定，并向上下文记录未判定原因

#### Scenario: 动态 change 名
- **WHEN** 创建命令的 change 名包含变量、命令替换或其他未被有界解析器读取的形态
- **THEN** FF-0 SHALL fail-open 并记录未判定原因，MUST NOT 静默放行或尝试展开 shell
