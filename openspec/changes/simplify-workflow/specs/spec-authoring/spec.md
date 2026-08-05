## Purpose

同步 spec-authoring 能力，删除双轨入口合并后失去前提的约束。[spec-review-amendment]

## MODIFIED Requirements

### Requirement: SA-01 单一入口三相位管线，拷问前置且为内建默认路径

修改：删除「skill SHALL 声明 `disable-model-invocation: true`」要求。新规则：模型 SHALL 在人示意收敛时自动 invoke `/sdflow-spec`，MUST NOT 自主判断"该开 change 了"。相位 B 的拷问协议不因触发方式改变而改变。

修改：删除「把"只能人触发"表述限定为已由当前宿主执行面验证的事实」——触发方式已改为自动，该条款失去基础。

保留不变：相位 B SHALL 是管线内建默认路径；任何进入相位 C 的路径 SHALL 先产出非空决策纪要。诚实边界声明保留不变。

#### Scenario: 模型在人示意时自动触发

- **WHEN** 用户在 explore 中表达收敛信号或描述需求且需要开 change
- **THEN** 模型自动 invoke `/sdflow-spec`，无需手动敲斜杠命令

## REMOVED Requirements

### Requirement: SA-14 四入口选择规则

本 Requirement 整段移除。双轨合并后不再有"四个入口"，选择规则失去前提。入口规则由 spec-workflow 的「阶段一入口为唯一线性路径」替代。

#### Scenario: 本 Requirement 不再存在

- **WHEN** archive 执行
- **THEN** 主 spec 中本 Requirement 被删除
