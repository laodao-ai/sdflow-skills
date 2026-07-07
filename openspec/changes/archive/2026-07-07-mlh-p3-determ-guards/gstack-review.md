<!-- sdflow:step1-broad-review v1 mode="simulated" -->
# 广审（Step1）— mlh-p3-determ-guards

> mode=simulated：`/autoplan` 未在本会话原生暴露 → 派 fresh-context 冷镜 agent（Engineering Manager 视角）作广审降级替代，非原生 autoplan（不伪装）。findings 纳入 Step3 合并池。

## EM 视角广审 findings（6 条，全采纳）

| # | 严重度 | 发现 | 处置 |
|---|---|---|---|
| F1 | 致命→高 | batch 优先级 lint 无占位符豁免，现存 3 条 `优先级: <待填>` 假阳、破零假阳基线 | ✅ 采纳（D5 扩两字段豁免）|
| F2 | 中→高 | 优先级 `P1 ★` 后缀非括注，D4「容忍括注」措辞二义 | ✅ 采纳（D4 前导 token 后不校验）|
| F3 | 高 | `block_ranges` 有第二处 AST 差异（消费循环签名），只归一 starts AST 仍不等 | ✅ 采纳（D6/Task1.1 列两处）|
| F4 | 中 | PRIORITIES 常量塞进函数-AST 守护集会 TypeError | ✅ 采纳（R4 值相等断言）|
| F5 | 中 | 3.B「写了没人跑」触发可靠性 vs 3.A 自动跑，Success Metrics 未区分 | ✅ 采纳（Metrics 分层）|
| F6 | 低 | helper-删除 scenario 无 test、try/except 吞异常无把关 | ✅ 采纳（Task1.8 属性访问约束）|

**已核实排除**（EM 背书）：模块顶层无副作用（`if __name__` 保护）、AST 契约实测吻合、归一回归非空头支票（todolist 71 测经 subprocess 命中两函数）、Task1/Task3 无文件级冲突。
