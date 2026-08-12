### Task 1: effort 维解析与导出全链

**Blocked-by:** none
**R-ID:** HAE-1

为 effort 分档建立从机读块到 eval 导出的完整数据通路：在 model-tiers 文档新增独立 `effort-tier-defaults` 机读块（仅 claude 三键 strong→high / mid→medium / light→low），resolver 脚本按有界键路径行锚定提取并导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（与既有六变量同一 eval 契约）；codex/unknown 宿主显式初始化三变量为空串（MUST NOT 复用 model tier 的 unknown 回落路径或 `_resolve_tier` 告警路径）。消费仓 config.yaml `effort-tiers.claude.*` 覆盖按有界键路径解析，值域校验 ∈ {low,medium,high,xhigh,max}，非法值回落缺省 + stderr 告警。resolver 头注释变量清单 6→9。

起手做 A1 最小实测：手工临时放一个 `effort: low` 探针 agent 定义到 `~/.claude/agents/`，派探针子代理对比 token 用量/耗时/输出规模多信号确认 effort 经 subagent_type 生效；结论记入 impl-report；失效 ⇒ 止损按 ADR 0043 备选重估。

- [ ] A1 探针实测通过，effort 经 subagent_type 全链生效（结论记入 impl-report）
- [ ] model-tiers 文档新增 `effort-tier-defaults` 机读块（仅 claude 三键），与上方表格两处不漂移
- [ ] resolver 导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（claude 宿主 high/medium/low；codex/unknown 空串不阻断）
- [ ] config `effort-tiers.claude.*` 覆盖生效 + 非法值回落告警
- [ ] 测试覆盖：三宿主态导出 × 覆盖生效 × 非法值回落 × eval 契约 × codex/unknown 空串无告警噪声

