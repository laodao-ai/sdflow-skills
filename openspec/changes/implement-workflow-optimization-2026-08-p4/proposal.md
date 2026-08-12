# Proposal · implement-workflow-optimization-2026-08-p4

## Why

roadmap `workflow-optimization-2026-08` 阶段 4（成本工程剩余）的前置条件已于 2026-08-12 全部
满足：token 基线累积完毕（p1/p2/p3/rsp 四个 change 全程锚）、阶段 2 观察窗口判读收口（roster
与裁决协议双 PASS，effort 改动不再有归因混杂）。同时窗口判读坐实两条 P1 断链（B25
code-review 报告机械层落盘自 08-07 起静默缺失、B26 defer 入池通道 3/3 断）——与本阶段同属
评审编排面，用户拍板 fold 进本 change（决策纪要 D2）。

## What Changes

- **面 A · effort 分档（T105 + T103）**：`model-tiers.md` 加 effort 第二维机读块（claude
  机队 strong→high / mid→medium / light→low；codex 侧如实 n/a）；`resolve-models.sh` 导出
  `$SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（含 config.yaml per-repo 覆盖，机制与 model 同构）；
  `setup.sh install_agents` 扩面铺 4 个全局 effort-keyed agent 定义
  `sdflow-effort-{low,medium,high,xhigh}`（frontmatter 仅 `effort:`，`model: inherit`）；
  四个编排 SKILL（sdflow-spec-review / sdflow-code-review / sdflow-implement / sdflow-done）
  派发条款接 `subagent_type` 选 effort 档；T103 输出封顶句（回传目标 ≤2k token）进稳定前缀段。
  机制取舍全文见 `openspec/adr/0043`。
- **面 B · dispatch prompt 构造（T98 + T124）**：三段组装序钉死——段① 稳定前缀（通则区块 +
  评审子代理通用契约 + base checklist 全文，由新 hack 脚本 `render-review-prefix.sh` 按固定
  序产出，byte-stable 可测）→ 段② 半稳定（镜角色 + domains 清单/对抗角度）→ 段③ 动态
  （change_dir + diff）。大部头/高频演进规则保持引用 + anchor_lint 不变；「SKILL.md 禁静态
  内联」不变。
- **B25 修复 + 机械门**：诊断并修复 code-review 报告 lens-metric 锚 / 机械引用核落盘缺失的
  直接成因；ship_gate 判 code-review 报告时 `metrics.enabled=true` ⇒ 要求 lens-metric 锚与
  引用核落盘段存在，缺 ⇒ 判「该步进行中，重跑」；spec-review 报告在 design 门同款检查（面治）。
- **B26 修复 + 对账门**：code-review SKILL Step4 defer 改为当场调 recorder add（显式
  `source_change`）、返回 id 写进报告台账；ship_gate 对账 defer 行 id ∧ 池文件存在
  （文件系统判，不走 git ls-files）。
- 08-07 起 6 个 change 的存量缺锚**不回填**（归档件不可手拼，断层如实记档）。

## Capabilities

### New Capabilities

（无——effort 分档并入既有 host-adaptive-execution 能力面，不发明新 capability。）

### Modified Capabilities

- `spec-workflow`: 评审编排 Requirement 变更——dispatch prompt 三段组装序（稳定前缀 =
  脚本输出原文）、镜派发带 effort 档、T103 输出封顶句、code-review defer 当场入池契约。
- `impl-orchestration`: ship_gate 新增两道报告机械层门（B25 lens-metric 锚存在性 +
  B26 defer id 对账）；sdflow-implement 派发接 effort 档。
- `host-adaptive-execution`: 档位解析扩 effort 第二维（`$SDFLOW_EFFORT_*` 导出 + config
  覆盖 + codex 机队 n/a 降级）；install_agents 铺 4 个 effort-keyed 全局 agent 定义。

## 需求优先级（TG-19）

- **P0**：B25/B26 修复 + ship_gate 机械门（正在流血的断链，晚一个 change 就多一个无锚样本）
- **P1**：面 A effort 分档（T105/T103，本阶段主目标）
- **P2**：面 B prompt 构造（T98/T124，收益靠 cc/cr 趋势长期显形）

## 假设列表（TG-22）

- **A1**：frontmatter `effort:` 对 `subagent_type` 派发的子代理全链生效（本仓
  `sdflow-spec/agents/` 三定义为实用先例，但评审镜场景未实测）。失效影响：面 A 的 effort
  维退化为无效声明——实现期首个 ticket 先做最小实测（派一个 effort=low 探针对比输出规模）。
- **A2**：cc/cr 比例趋势可在 change 间对比（同一 token-log 采集口径）。失效影响：面 B 验收
  层 ② 退化为「机械落地 + 质量不退」两层——已声明为方向信号不设硬阈值，可接受。

## 开放问题（TG-21）

- **Q1**：B25 直接成因（emitter 未被调用 vs 调用失败未记录）——实现期修复票内诊断定案，
  修复以机械门为主、成因修复为辅（门在成因不明时也能拦住再犯）。

## Impact

- **栈**：Python（gate/脚本/测试）+ Bash（setup.sh / hack 脚本）+ Markdown（SKILL/bundle
  规则），命中 backend 领域清单（TG-01）；devex 面命中（TG-28：SKILL 派发契约、config
  键扩展、新 hack 脚本均为 developer-facing）。
- **代码面**：`sdflow-init/assets/workflow/model-tiers.md`（bundle 权威源，改动经
  `sdflow-init update` 推下游）、`sdflow-init/assets/hack/resolve-models.sh` +
  `render-review-prefix.sh`（新）、`setup.sh` install_agents、`sdflow-ship/scripts/ship_gate.py`、
  四个编排 SKILL.md、对应 pytest 测试群。
- **下游消费仓**：model-tiers 机读块扩维与 config 覆盖键扩展随下次 `sdflow-init update`
  生效；未 update 的仓行为不变（effort 缺省仅在新 SKILL + 新 resolver 同时就位时生效）。
- **全局命名空间**：`~/.claude/agents/` +4 定义（install_agents 既有守卫/孤儿清理覆盖）。

## Success Metrics

- 机械落地层：全仓 pytest 绿，新增测试覆盖——install_agents 4 定义（假 HOME）、
  resolve-models effort 导出+覆盖、render-review-prefix byte-stable golden、ship_gate
  B25/B26 门「缺省=放行/存在坏=fail-closed」双向、defer id 对账契约。
- 断链止血：本 change 自身的 code-review 报告即含 lens-metric 锚 + 引用核落盘段 + defer
  id 对账（dogfood 自证，gate 强制）。
- 成本方向信号：后续 change 的 cc/cr 比例趋势对照 4-change 基线记档观察（不设硬阈值，
  不阻塞归档）；质量不退沿用 p2 hand-off D4 判读指标随后续窗口累积（事后锚，本 change 内
  显式标注不可核验，随后续 change 判读）。

## Non-Goals

- 不回填 08-07 起 6 个 change 的存量缺锚。
- 不动评审编排大改（T276 条件未触发；Workflow 编排原语不用）。
- 不碰 T101 / 阶段 5（人类门减负）。
- 不给 codex 机队发明 effort 机制（如实 n/a）。
- xhigh/max 进值域不进缺省映射。
- 不改裁决协议与镜 roster（刚过窗口判读，保持稳定避免下窗口归因混杂）。

## Compliance

N/A（本仓开发工作流工具，无合规面）。
