# effort 分档经全局 effort-keyed agent 定义落地

编排 skill（sdflow-spec-review / sdflow-code-review / sdflow-implement / sdflow-done）的子代理
派发在 model 档位之外增加 effort 第二维（T105/T103，用户 2026-08-12 拍板）：落地机制 =
`setup.sh install_agents` 铺 4 个全局 agent 定义 `sdflow-effort-{low,medium,high,xhigh}`
（frontmatter 仅 `effort:` 一项，`model: inherit`），派发时 `subagent_type` 选 effort 档、
`model` 参数照旧传 `$SDFLOW_TIER_*`。缺省映射 strong→high / mid→medium / light→low，单一源
在 `model-tiers.md` 第二维机读块，`resolve-models.sh` 导出 `$SDFLOW_EFFORT_{STRONG,MID,LIGHT}`
（config.yaml model-tiers 段可 per-repo 覆盖，机制与 model 覆盖同构）。铁律延伸：门禁步
MUST NOT 低于 high；xhigh/max 进值域不进缺省（p4 是成本工程，升档=加宽目标）。
Codex 机队无 per-agent effort 对应物 ⇒ 如实 n/a，派发不带（不缩 Claude 侧目标的诚实降级）。

## Considered Options

- **effort-keyed 全局 agent 定义（选中）**：宿主对 effort 的原生支持面只有 agent 定义
  frontmatter（Agent 派发的 per-call 参数仅 `model`，无 `effort`——调研文档「per-call
  effort」的说法经 schema 实证为半错）；按 effort 值键（而非按档位键）铺定义，使 per-repo
  覆盖能穿透——effort 若烘在 tier 定义里，config 想让 mid 跑 high 就得改全局 frontmatter。
  代价：全局 `~/.claude/agents/` 命名空间 +4 名额（install_agents 守卫 / 孤儿清理 / 假 HOME
  测试机制已就位，回滚 = 删 `sdflow-*/agents/` 源目录后重跑 setup）。
- **tier-keyed agent 定义**：3 名额略省，但 effort 与 model 耦死在同一定义里，per-repo
  effort 覆盖无通路，否决。
- **prompt 层弱形态**（输出封顶句 + 「简化推理」指示）：零新资产，但 effort 分档名不副实，
  是拿「per-call 参数不存在」的现状缩水 T105 目标（通则③），仅其中的输出封顶句作为 T103
  形态保留（进 dispatch prompt 稳定前缀段）。
- **Workflow 编排原语**（`agent()` 有 `opts.effort`）：属 T276 登记的「评审编排大改」条件
  触发项，Codex 宿主无对应物、双路径双维护，条件未触发不动。

## Consequences

- `~/.claude/agents/` 全局命名空间新增 4 个定义，与 `sdflow-spec/agents/` 三个既有定义
  （按角色键、未启用资产）并存互不影响；install_agents 的所有权守卫（只接管 readlink 命中
  自有源的软链）与孤儿清理对新定义同样生效。
- `model-tiers.md` 机读块从 6 键（2 机队 × 3 档）扩为含 effort 维；消费方仍按有界键路径
  行锚定提取，MUST NOT 长成通用解析器（基准 5）。
- 四个编排 SKILL 的派发条款增加 subagent_type 选择维度；Codex 宿主派发路径不变。
- Windows 宿主沿用 install_agents 既有「不铺、报 skipped」路径，effort 派发在该宿主
  自动缺席（subagent_type 不存在时按各 SKILL 的降级条款处置）。
