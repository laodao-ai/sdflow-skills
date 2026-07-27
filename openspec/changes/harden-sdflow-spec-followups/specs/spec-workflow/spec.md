## ADDED Requirements

### Requirement: FF-0 未判定路径不对错仓执法且留下非越权审计

[spec-review-amendment] FF-0 PreToolUse hook SHALL 仅在整条命令完整匹配有限的单条直接 literal 创建 grammar 时，把 payload `cwd` 作为命令作用仓并执行三分支判定；MUST NOT 以“未发现已知危险结构”的黑名单作为安全证明。命令含创建字样但未命中该 grammar，或无法读取唯一合法 change 名时，hook SHALL fail-open，并 SHALL 输出含 `additionalContext` 的 PreToolUse 结果；context SHALL 带有限原因码 `cwd-ambiguous` 或 `change-name-unparseable` 与人类可读说明。

[spec-review-amendment] 该审计结果 MUST NOT 设置任何 `permissionDecision`，以免把日志行为变成绕过宿主原生权限或错仓 deny。实现 MUST NOT 解析 shell 以推断 `cd`、变量展开或实际作用目录。既有“多处有界创建调用必须拆开”的 stacking deny 与直接调用的三分支/ack 行为 SHALL 保持。

#### Scenario: 跨仓 cd 调用
- **WHEN** Bash 命令在 payload `cwd` 外通过工作目录切换创建 OpenSpec change
- **THEN** [spec-review-amendment] FF-0 SHALL 不以 payload 仓的分支作 deny/allow 判定，并向上下文记录 `cwd-ambiguous`

#### Scenario: 动态 change 名
- **WHEN** 创建命令的 change 名包含变量、命令替换或其他未被有界解析器读取的形态
- **THEN** [spec-review-amendment] FF-0 SHALL fail-open 并记录 `change-name-unparseable`，MUST NOT 静默放行或尝试展开 shell

#### Scenario: 直接 literal 调用保持三分支
- **WHEN** 整条命令完整匹配允许的单条直接 literal 创建 grammar
- **THEN** [spec-review-amendment] FF-0 SHALL 在 payload `cwd` 上执行既有 protected/same-change/other-feature + ack 判定

#### Scenario: 包装或散文命中不被错当直接调用
- **WHEN** 创建字样位于 wrapper、复合命令、目录切换或前后散文中
- **THEN** [spec-review-amendment] FF-0 SHALL 输出 `cwd-ambiguous` context 且不设置任何 `permissionDecision`
