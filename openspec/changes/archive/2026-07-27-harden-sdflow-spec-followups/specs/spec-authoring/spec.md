## MODIFIED Requirements

### Requirement: SA-01 单一入口三相位管线，拷问前置且为内建默认路径

`sdflow-spec` SHALL 以单一入口驱动「澄清（A）→ 拷问（B）→ 生成（C）」三相位管线。相位 A 可在需求已成熟时由主 session 判断提前收束，但相位 B SHALL 是管线的内建默认路径——任何进入相位 C 的路径 SHALL 先产出非空决策纪要。skill SHALL 声明 `disable-model-invocation: true`，并把“只能人触发”表述限定为**已由当前宿主执行面验证的事实**。

**诚实边界**：本 requirement 提供的是结构性改善，不是机械保证；纪要存在且必填小节非空不能证明发生过对抗拷问。宿主未提供模型可调用的 Skill 接口时，文档 SHALL 记录该验证缺口，MUST NOT 把接口缺席表述成模型调用被拒。

#### Scenario: Codex 无模型调用接口时如实降级声明
- **WHEN** Codex 宿主只能观察到用户显式触发 skill，且本 session 没有可供模型调用的 Skill 接口
- **THEN** `sdflow-spec` SHALL 声明该宿主的模型调用拒绝语义未获正向实证，MUST NOT 宣称“只能人触发”已被机械验证

### Requirement: SA-06 终审兜判断层，并核产物间一致性

相位 C 生成完毕后，主 session SHALL 读回四件套与决策纪要执行终审：核验产物与决策纪要的一致性、design 与 specs 的互相一致性，以及 proposal/design/tasks 未截断。判断性偏差直接修改；措辞与风格差异 SHALL 放过。

被砍候选及其理由的追溯范围 SHALL 是整个 `openspec/changes/<name>/` 目录，包含 `decision-memo.md`。`design.md` 的 Decisions 节仅有指向纪要的一行指针是合法实现，MUST NOT 要求四件套重复被砍候选。

#### Scenario: 被砍候选仅存在于决策纪要
- **WHEN** 某被砍候选和理由可在 `decision-memo.md` 追溯，但四件套均未重复该文本
- **THEN** 终审 SHALL 判为可追溯，MUST NOT 作为判断性偏差

## ADDED Requirements

### Requirement: SA-16 入口常驻契约与按需资料分层

[spec-review-amendment] `sdflow-spec/SKILL.md` SHALL 只承载每次运行必须读取和执行的契约，并以 Python Unicode 字符数不超过 18,000 为机械门。未启用外派协议、详细异常诊断与演进依据 SHALL 置于 versioned reference；入口 SHALL 明确其触发条件和相对路径。机械门 SHALL 以 resident-contract token map 同时验证 frontmatter、Phase 0/A/B/C、C.1 四判、终审、`openspec validate --strict`、两个 checkpoint、出口三步与每个 reference 的加载条件仍在入口；MUST NOT 以空标题、裸链接或只移动文字规避。

#### Scenario: 未启用外派不进入默认入口
- **WHEN** 阶段二外派仍为未启用资产
- **THEN** 其完整协议 SHALL 位于按需 reference，入口只保留状态和加载条件

#### Scenario: 入口超量
- **WHEN** `SKILL.md` 的 Python Unicode 字符数超过 18,000
- **THEN** 回归测试 SHALL 失败

### Requirement: SA-15 T132 的阶段一收敛输入契约按入口分治

[spec-review-amendment] 本 change SHALL 只为 T132 的未来 grill 收敛门定义并订正输入契约，不实现或关闭 T132。分支 A 的候选证据为身份、hash 与必填节有效的 `decision-memo.md` 加 `checkpoint(sdflow-spec-grill)`；分支 B 的候选证据为既有 `checkpoint(grill)` 或未来 gate 明确认可的 `sdflow:grill-done` 锚。规则身份 MUST NOT 使用会漂移的行号；T132 台账 SHALL 保持 OPEN。

#### Scenario: 分支 A 的未来 gate 输入被完整定义
- **WHEN** 本 change 订正 T132/T234 的 A/B 信号描述
- **THEN** [spec-review-amendment] 描述 SHALL 把分支 A 的纪要 + `sdflow-spec-grill` 与分支 B 的 grill 信号分开，且 SHALL 明示 T132 尚未实现、保持 OPEN
