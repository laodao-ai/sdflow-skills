---
schema_version: 1
change: implement-workflow-optimization-2026-08-p4
branch: feat/implement-workflow-optimization-2026-08-p4
generated_at: 2026-08-12T10:36:00+08:00
decision_hash: 2f759713a19f
---

# 决策纪要 · implement-workflow-optimization-2026-08-p4

> 相位 B 拷问纪要（增量落盘）。背景：roadmap `openspec/roadmaps/workflow-optimization-2026-08/`
> 阶段 4（成本工程剩余）；探索期结论与验收三层草案见同 roadmap `task-log.md` 2026-08-12 条目。

## 目标态

评审/实现/收尾编排的每次子代理派发按 model-tiers「档位 × effort」二维表构造、以三段组装序
（稳定前缀脚本产出 → 半稳定 → 动态）拼 dispatch prompt；code-review 报告机械层落盘（lens-metric
锚 + 引用核）与 defer 入池通道恢复，并由 ship_gate 机械门守住不再静默断链。

## 承重约束

- **K1 · effort 原语的真实可用形态 = agent 定义 frontmatter，非 per-call 参数**。
  证据锚：本 session Agent 工具 schema 的参数集仅含 `model`（无 `effort`）；
  `sdflow-spec/agents/sdflow-local-researcher.md:9-10`（`model: inherit` + `effort: low`，
  同目录三定义均带 effort 字段，宿主正式支持）。⇒ 调研文档
  `docs/workflow-optimization-research-2026-08.md:144-146`「per-call effort」的说法**半错**，
  面 A 若要真分档，机制只能走 agent 定义（subagent_type）或退化为 prompt 层弱形态。
- **K2 · B25 是执行漂移不是工具坏死**。证据锚：emitter 实存
  `~/.sdflow/workflow/tools/lens_metric_emit.py`；两评审 SKILL 调用条款同路径同机制
  （`sdflow-spec-review/SKILL.md:356`、`sdflow-code-review/SKILL.md:454`，均
  `$RULES_ROOT/tools/lens_metric_emit.py`）；而 08-07 起 6 个 change 的报告
  spec 侧锚数 5-6、code 侧恒 0（archive 逐份 grep 实测）。同工具同路径、单侧持续缺失
  ⇒ 修复主体 = 机械门（报告消费处 fail-closed），散文条款已证明守不住。
- **K3 · defer 通道无机械信号**。证据锚：p3 code-review defer D1/D2 标「待入 todolist」、
  rsp 标「已入 todolist」，池内 grep 均无对应条目（2026-08-12 窗口判读实测，B26）；
  SKILL defer 条款为纯散文 MUST，报告台账与池文件之间无 id 对账。

## 拍板决策

- **D1 · 面 A effort 分档机制与缺省映射**（2026-08-12 人拍板）：
  - **机制 = 方案 A**：`setup.sh install_agents` 扩面，铺 3 个通用档位 agent 定义
    （`sdflow-tier-strong/mid/light`，`model: inherit` + effort 按档映射），编排 SKILL
    派镜 `subagent_type` 按档选、`model` 参数照旧走 `$SDFLOW_TIER_*`。依据：K1（frontmatter
    effort 是唯一原生真分档路径）；install_agents 守卫/孤儿清理/测试机制已存在。
    Codex 宿主无对应物 ⇒ effort 派发 codex 侧如实降级不带（不缩 Claude 侧目标）。
  - **值域 = Claude Code 原生枚举** {low, medium, high, xhigh}（合法值另含 max），
    人明确指示「参考 claude code 的」。
  - **缺省映射**：strong→high（铁律 effort 延伸：门禁步 MUST NOT 低于 high；不升 xhigh——
    p4 是成本工程，升档=加宽）；mid→medium；light→low（low 保留：light 档职责定义
    「纯机械/可重试/无判断权重」排除低推理深度风险面；本仓 `sdflow-spec/agents/` 三定义
    effort: low 实用先例；档位表静态按步定性，无动态路由误分类面）。
  - **xhigh/max 处置**：进值域、不进缺省映射，留 per-repo 覆盖逃生口（config.yaml
    model-tiers 段既有覆盖机制顺带管 effort）。

- **D2 · B25/B26 机械门挂 ship_gate**（2026-08-12 人拍板，一簇四件）：
  - 判据：两 bug 失效模式同为「捕获环节由被监管方（评审 session）把持」——SKILL 自调的
    emitter/anchor_lint 都不构成机械门（既有结论 [[signal-exists-not-equal-mechanical-capture]]）；
    唯一外部消费点 = ship_gate（已读两报告 frontmatter，`ship_gate.py:1783-1800`，
    有 fence-aware 行锚定设施）。
  - **B25 门**：ship_gate 判 code-review 报告时 `metrics.enabled=true` ⇒ 要求 ≥1 行
    `sdflow:lens-metric layer="code-review"` 锚 + 机械引用核落盘段；缺 ⇒ 判「该步进行中，
    重跑」+ 修复指引。`metrics.enabled` 缺省/false ⇒ 跳过（消费仓语义不变，与 SKILL 门控同口径）。
  - **B26 门**：SKILL Step4 defer 改为当场调 recorder add（显式 `source_change`）、
    返回 id 写进报告台账行；ship_gate 对账 defer 行匹配 `T\d+|B\d+` ∧
    `openspec/issues/open/**/<id>.md` **文件系统存在**（不走 git ls-files，
    [[tracked-file-guard-blind-to-uncommitted]] 前科）。
  - **面治扩 spec 侧**：ship_gate 读 design 门时对 spec-review 报告加同款 lens-metric
    存在性检查（现在行为正常但同无守）。
  - **不回填**：08-07 起 6 个 change 缺锚不回填（归档报告不可手拼、改归档件破坏
    reviewed_sha 审计链）；retro 聚合③ code 侧断层如实记档。通则④边角。
  - 代价主次：系统镜为主——gate 新增 config 读取须「缺省=放行 / 存在坏=fail-closed」双向
    测试（[[dogfood-blind-spot-source-config]]）；fence 假阳沿用既有 fence-aware 口径
    （[[gate-substring-detection-dogfood]]）。

- **D1-r · D1 实现层修正：agent 定义按 effort 值键，不按档位键**（2026-08-12 人确认）：
  铺 `sdflow-effort-low/medium/high/xhigh` 四个定义（frontmatter 仅 `effort:`，
  `model: inherit`）；派发 `subagent_type` 选 effort、`model` 参数照旧传 `$SDFLOW_TIER_*`。
  依据：effort 烘在 tier 定义里则 per-repo 覆盖穿不过全局 frontmatter；解耦后覆盖走
  `resolve-models.sh` 导出 `$SDFLOW_EFFORT_<TIER>`，与 model 覆盖机制同构。
  代价：全局命名空间 4 名额（vs 3）。

- **D3 · 面 B 形态：三段组装序 + T124 分界套用 + 段①脚本化**（2026-08-12 人拍板）：
  - **三段组装序**（T98）：段① 稳定前缀（跨轮跨镜 byte-stable）= 通则区块 + 评审子代理
    通用契约（结构化 findings schema / 引文纪律 / **T103 输出封顶句「回传目标 ≤2k token，
    超出按严重度截优先」** / 不问人）+ `code-review-base.md` 全文（**所有镜统一带**——
    对抗/历史镜多付 22 行换整段 byte-stable，通则④判值）；段② 半稳定（per-镜，change 内
    稳定）= 镜角色 + `domains/<栈>` 全文（领域镜）/ 对抗角度 / 历史镜指令；段③ 动态 =
    change_dir + `DIFF_BASE..HEAD` + diff。spec-review 侧同构（`spec-quality-base.md`
    68 行照贴）。
  - **分界不动的一侧**：大部头/高频演进（trigger-catalog、lens-metric-contract）保持
    引用 + anchor_lint；「SKILL.md 禁静态内联」不变（运行时读入贴 prompt ≠ 规则文本写死
    进 SKILL 源文件，后者才是拷贝漂移面）。T124 2026-07-10 拍板原判据照抄。
  - **段① 机械化**：cat 级脚本（如 `render-review-prefix.sh --layer <layer>`）按固定序
    输出段①；SKILL 条款改「段① = 脚本输出原文」。依据：组装序有确定性信号（基准 1）；
    收益 = byte-stable 可测试断言 + cc/cr 趋势归因干净。
  - 尺寸证据锚：`code-review-base.md` 22 行、`domains/*` ≤20 行、`spec-quality-base.md`
    68 行（wc -l 实测）；通则区块 8876 字节（skill-principles.md）。

- **D4 · 覆盖面与验收三层**（2026-08-12 人拍板）：
  - **覆盖面（面治）**：effort 派发接入全部按档位表派子代理的编排器——`sdflow-spec-review` /
    `sdflow-code-review` / `sdflow-implement` / `sdflow-done`（三步子代理）；`model-tiers.md`
    加 effort 第二维机读块（claude 机队；codex 侧如实标 n/a）；`resolve-models.sh` 导出
    `$SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（含 config 覆盖路径）。`sdflow-spec/agents/`
    三既有定义不动（按角色键成立、未启用资产）。
  - **验收三层**：① 机械落地全 pytest——install_agents 假 HOME 测 4 定义、resolve-models
    effort 导出+覆盖、render-review-prefix byte-stable golden、ship_gate B25/B26 门
    「缺省=放行/存在坏=fail-closed」双向、defer id 对账契约；② cc/cr 比例趋势对照现有
    4 change 基线——方向信号**不设硬阈值**（[[variable-quantity-generous-tunable-default-not-spike]]），
    记档观察；③ 质量不退沿用 p2 hand-off D4 判读指标，随后续 3-change 窗口自然累积，
    **不阻塞本 change 归档**（p2 先例）。
  - token 基线证据锚：p1 out 161k/cc 852k/cr 52.5M · p2 out 856k/cc 2.4M/cr 104.2M ·
    p3 out 941k/cc 2.5M/cr 107.3M（retro report.md tokens 列）+ rsp token-log 15 行。

- **D5 · Non-goals**（2026-08-12 人拍板）：不回填 08-07 起 6 change 缺锚（见 D2）；
  不动评审编排大改（T276 条件未触发，Workflow 原语不用）；不碰 T101/阶段 5；不给 codex
  侧发明 effort 机制（如实 n/a）；xhigh/max 不进缺省映射；**不改裁决协议与 roster**
  （刚过窗口判读，保持稳定，避免下个观察窗口归因混杂）。

- **D6 · ADR**（2026-08-12 人确认）：为 D1/D1-r 立一条 ADR「effort 分档经全局
  effort-keyed agent 定义」（真实权衡：frontmatter vs per-call 不存在 vs prompt 弱形态；
  effort 键 vs tier 键；半难逆转：全局命名空间资产）。D2 的 gate 扩展走 spec delta，
  不单开 ADR。落 `openspec/adr/0043`。

## 接受的边角

- **08-07 起 6 个 change 的 code-review 锚不回填** — 概率：已发生（存量既成）；影响：
  retro 聚合③ code 侧断层约一个月，判读可用报告正文人工回算兜底；完美成本：改归档件 +
  手拼锚（双违规）。**为何接受**：修复成本违反两条硬约束（MUST NOT 手拼、归档件
  reviewed_sha 审计链），断层如实记档即可。
- **段① 稳定前缀在规则 bundle 更新时缓存整段失效** — 概率：规则改动低频；影响：单轮
  cache_creation 一次性升高后回落；完美成本：per-文件分段缓存无宿主原语。**为何接受**：
  低频 × 一次性，且正是「稳定前缀」定义的题中之义。
- **codex 宿主无 per-agent effort 对应物** — 概率：确定；影响：codex 机队只享 model
  分档不享 effort 分档；完美成本：给 codex 发明机制 = 自建（04 提案时代已判过成本过高）。
  **为何接受**：如实 n/a 降级，不缩 Claude 侧目标（D5）。
- **change 名含「p4」而阶段边界可能随实施微调** — 名字略偏的目录风险；openspec 无
  rename，接受（删分支即净）。

## 三镜代价

D1（effort 落地机制，三候选，命中 TG-23）：**系统镜**——全局 `~/.claude/agents/`
命名空间 +4 名额（守卫/孤儿清理/测试机制已有，回滚 = 删目录重跑 setup）；**用户镜**——
无感知变化（评审报告形态不变）；**开发循环镜**——SKILL 派发段多 subagent_type 维度，
覆盖机制与 model 同构不加新心智。**主次判定**：系统镜为主——全局命名空间是本仓唯一
标 🔴 的共享面，D1-r 的 effort 键分解正是为把该面的语义钉到最简。
其余决策（D2 gate 挂点、D3 组装序）未命中 TG-23，代价随各决策条目内注。
