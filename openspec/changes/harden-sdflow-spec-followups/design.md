## Context

`add-sdflow-spec` 归档后，T233–T238、T240–T242 留下源仓行为与叙述不一致。最关键的两处是：FF-0 把 session `cwd` 当成命令实际仓；`SKILL.md` 把常驻流程、未启用外派和故障百科一并注入。

## Goals / Non-Goals

**Goals:**

- 让 FF-0 只在可证明作用仓就是 payload 仓时执行三分支判定，并使未判定可见但不自动授权。
- 将 `sdflow-spec` 的常驻执行契约压到 18,000 Unicode 字符以内，保留按需资料的确定加载路径。
- 订正 Codex、终审追溯和 A/B grill 信号的诚实边界，并关闭已完成的归档台账。

**Non-Goals:**

- 不做 T239 的下游 rollout，不重启外派模式，不解析 shell 语法。

## Decisions

### D1：FF-0 采用“保守识别 + 无决策审计”

只有命令文本不包含任何可能改变工作目录的 shell 结构时，才把 payload `cwd` 作为判定仓。检测到 `cd` 结构、或无法读出唯一合法 change 名时，hook 输出仅含 `hookEventName` 与 `additionalContext` 的 JSON，说明未执行 FF-0 判定；不设置 `permissionDecision`。

这避免了把 `allow` 当作日志而跳过宿主权限，也避免把无界 shell 解析引进守卫。审计记录仍进入调用上下文；实际仓语义继续由 shell 和 review 负责。

### D2：入口薄化但不稀释执行契约

`SKILL.md` 保留四条通则、每轮必经的 Phase 0/B/C、终审、checkpoint、出口序列和“何时读哪个 reference”的指针。未启用的外派协议、详细降级诊断和演进依据移入三个 reference。新增测试以 Python `len()` 验证入口不超过 18,000 Unicode 字符，并锚定必驻标题与引用文件存在。

### D3：宿主和追溯按证据边界改写

Codex 没有本 session 可调用的 Skill 执行面，因而只记录“用户显式触发被接受”，不把接口缺席误写成模型调用被拒。终审以整个 change 目录为追溯边界，`decision-memo.md` 是被砍候选和理由的合法唯一载体。T132 将在实施前把 A/B 的收敛信号分开描述并由门消费。

## Risks / Trade-offs

- [跨仓调用未被强制拦截] → 守卫显式注入未判定原因；不假装知道实际仓。
- [reference 漂移] → 测试检查入口指针、文件存在和必驻章节；按需资料随仓版本化。
- [Codex 宿主接口变更] → 文案不作永久否定；后续出现可调用接口时补正反实测。

## Migration Plan

1. 在 canonical 源仓修改 hook、skill、references、workflow/specs 与测试。
2. 运行受影响测试、全量 pytest、`setup.sh`，验证全局 hook/skill 安装状态。
3. 本 change 不向下游执行 update；T239 保持为独立 rollout 待办。
4. 回滚时还原同一提交；全局安装通过回滚后的 `setup.sh` 刷新。

## Open Questions

无。用户已确认薄入口 + reference 与 18,000 Unicode 字符门。

## Compliance

不新增外部服务、持久化数据或凭据处理；hook 只处理本机 PreToolUse payload。
