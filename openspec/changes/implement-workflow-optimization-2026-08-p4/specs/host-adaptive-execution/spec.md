# host-adaptive-execution · delta（implement-workflow-optimization-2026-08-p4）

## ADDED Requirements

### Requirement: 档位解析扩 effort 第二维（claude 机队），空值即回落

档位解析 SHALL 在 model 维之外提供 effort 维：`model-tiers.md` 新增独立机读块
`effort-tier-defaults`，键路径仅含 `claude.{strong,mid,light}`（值域 ∈
{low,medium,high,xhigh,max}；codex 机队**不写键即 n/a**，MUST NOT 引入空值语义）；
resolver SHALL 按有界键路径行锚定提取并导出 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`
（与既有六变量同一 eval 契约）。消费仓 MAY 经 `openspec/config.yaml` 的
`effort-tiers.claude.{strong,mid,light}` 段覆盖，解析复用 model-tiers 段的有界键路径
口径；非法值 SHALL 忽略覆盖回落缺省并告警。缺省映射 strong→high / mid→medium /
light→low；带门禁、无人逐条复核的步 MUST NOT 低于 high（「不降档」铁律的 effort 延伸）。

#### Scenario: claude 宿主导出 effort 三变量

- **WHEN** claude 宿主上 eval resolver 输出
- **THEN** `SDFLOW_EFFORT_STRONG/MID/LIGHT` 分别为 high/medium/low（无覆盖时），
  且与既有 `SDFLOW_TIER_*` 同批导出、可安全 eval

#### Scenario: codex / unknown 宿主 effort 为空且不阻断

- **WHEN** codex 或 unknown 宿主上 eval resolver 输出
- **THEN** `SDFLOW_EFFORT_*` 为空串，resolver 退出码不因此非零；消费方按「空值回落」
  行为处置（见派发侧 Requirement），无告警噪声阻断

#### Scenario: config 覆盖生效与非法值回落

- **WHEN** 消费仓 config.yaml 含 `effort-tiers.claude.mid: xhigh`
- **THEN** `SDFLOW_EFFORT_MID` 导出 xhigh
- **WHEN** 覆盖值不在值域（如 `turbo`）
- **THEN** 忽略该覆盖、回落缺省 medium，stderr 告警一行

### Requirement: effort-keyed 全局 agent 定义经 install_agents 铺设

工具链 SHALL 提供 4 个全局 agent 定义 `sdflow-effort-{low,medium,high,xhigh}`
（frontmatter 仅 `name`/`description`（含「仅由 sdflow 编排 SKILL 派发选用」排他声明）/
`model: inherit`/`effort: <值>`），由 `setup.sh` install_agents 铺至 `~/.claude/agents/`，
沿用既有所有权守卫（只接管 readlink 命中自有源的软链）、孤儿清理与失败降级
（外部命令失败 SHALL 降级 `skipped[]` + 汇总，MUST NOT 中止整个 setup）。Windows 沿用
既有「不铺、报 skipped」路径。

#### Scenario: 铺设幂等且不覆盖他人定义

- **WHEN** `~/.claude/agents/sdflow-effort-low.md` 已存在且非本仓软链
- **THEN** setup 跳过该文件并记入 skipped 汇总，MUST NOT 覆盖

#### Scenario: 源目录删除后孤儿清理

- **WHEN** effort agent 定义源目录整体删除后重跑 setup
- **THEN** 悬空软链被清理，全局名册无残留
