# Spec Review Report · implement-workflow-optimization-2026-08-p4

- 评审对象：`openspec/changes/implement-workflow-optimization-2026-08-p4/` 四件套（proposal / design / specs×3 / tasks）+ decision-memo + adr/0043
- 镜子审的盘面：`bdd5ef423d4d87d7aa5b426039020607e5bdba4f`（`git rev-parse HEAD`，checkpoint「相位 C 生成四件套 + 终审」）
- 评审档：主 session 强档（opus）协调；镜 fan-out 中档（sonnet）× 7 + 弱档（haiku）接地镜 × 1 + 跨模型 design-voice（codex · gpt-5.6-sol）
- 日期：2026-08-12

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-01,TG-14,TG-18,TG-19,TG-21,TG-22,TG-23,TG-25,TG-28" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->

## 执行摘要

单批 dispatch 9 路（strategy / plan-eng / backend / devex / 对抗 ×3〔高风险档：ship_gate 门禁 + 全局命名空间〕/ 接地 / design-voice）全部按时收齐，无降级。合并去重后 **23 条 canonical findings**：机械引用核 21 pass + 2 uncheckable（证据包）+ 0 fail；对抗裁决 **采纳 21 / defer 1 / 裁掉 1**。三面 Critical：

1. **M1 · install_agents 多源扩容未设计**（6 镜收敛，独家深挖 = manifest 覆写数据丢失面）
2. **M2 · defer 台账行机读判据未定义**（3 镜收敛，假阳 + 假阴双向失效）
3. **M9 · dogfood 自证时序不成立**（对抗镜 C 独家，机器实测验证）

两个 ≥2 方案点进「需拍板」（Q1 `max` 值域处置、Q2 install_agents 扩容方案），其余采纳项均为方向无分歧的自动决策，已按 `[spec-review-amendment]` 回流四件套。

## 决策登记区

### 需拍板（人工设计门勾选）

**Q1 · `max` 进值域但无 agent 定义 —— 派发断链（M3，voice + devex 双路收敛，High）**
`host-adaptive-execution` delta 值域 ∈ {low,medium,high,xhigh,max}，但只铺 4 个定义（无 `sdflow-effort-max`）；派发规则把非空值直接拼 `subagent_type: sdflow-effort-<值>` ⇒ 消费仓覆盖 `max` 时请求不存在的 agent 定义，且**不走空值回落**（值非空）——介于「非法回落」与「空值回落」之间的未覆盖第三态，无任何错误文案。
- **选项 A（推荐）**：值域收窄为 {low,medium,high,xhigh}，`max` 判非法回落 + 告警。依据：与 D5「xhigh/max 不进缺省映射」精神一致、零新增机制、逃生口仍有 xhigh。
- **选项 B**：补第 5 个 `sdflow-effort-max` 定义 + 安装测试。
- 三面后果：系统镜——A 少一个全局命名空间名额与一份定义资产，B 多一个但值域完整；用户镜——A 下配 `max` 的消费仓收到告警回落（可感知、无断链），B 无感；开发循环镜——A 改一行值域 + 一条负例测试，B 多一份定义 + 测试扩面。**主次判定**：系统镜为主——p4 是成本工程，B 属加宽；A 的唯一代价是「未来真想要 max」时再开一条小 change，可接受。

**Q2 · install_agents 扩容方案 + 源目录名（M1，6 镜收敛，Critical）**
`install_agents()` 四处硬编码 `sdflow-spec/agents`（`setup.sh:297/363/420/451`），且 `AGENTS_MANIFEST=".sdflow-agents"` 单文件**覆盖写**（`setup.sh:386-396`）——若对第二源目录再调一遍现函数，后一次 manifest 整体冲掉前一次 ⇒ 既有 3 定义从 manifest 消失、退役检测/孤儿清理对其永久失效（违反本 delta 自己的「源目录删除后孤儿清理」Scenario）。组件清单「源目录名实施定」把架构决策悬空到实现期，而 CLAUDE.md 把这段守卫标为 🔴 最敏感段。
- **选项 A（推荐）**：`install_agents()` 泛化为遍历源目录列表（`sdflow-spec/agents` + 新目录），所有权判据参数化为 `*/<src-rel>/"$name"` 形状，manifest 改为**跨源 union 后一次性覆写**；孤儿清理同步参数化。依据：保住单 manifest 的既有清理逻辑与测试骨架，改动集中一个函数族。
- **选项 B**：新独立函数 + 独立 manifest 文件（如 `.sdflow-effort-agents`），两套互不覆盖。依据：隔离彻底、不碰既有守卫；代价：skipped[] 文案/守卫逻辑双份漂移面（devex DX4）。
- **源目录名（附属拍板）**：推荐新建独立目录（如 `sdflow-agents/agents/` 或 `sdflow-effort/agents/`）——依据：memo D5 明确三个既有角色定义不动，effort 值键定义与 spec 角色键定义混放同目录语义混杂；代价：多一个顶层目录（无 SKILL.md，不会被 install_into 误认）。
- 三面后果：系统镜——A 单一 manifest 单一逻辑，B 双份平行结构；用户镜——皆无感；开发循环镜——A 须动 🔴 守卫段（`hack/tests/test_install_agents.py` 扩双源矩阵），B 测试独立但翻倍。**主次判定**：系统镜为主——manifest 覆写是数据丢失级失效，A 从根上消除「两份清单」这个失效面本身。

### 自动决策（高置信采纳，已回流 amendment，默认接受可覆盖）

| # | 决策 | 依据 |
|---|---|---|
| D1 | ship_gate B25 门 config 读取机制钉死：复用 `_yq()` 非 frontmatter file 模式；**config.yaml 文件不存在 = 缺省放行**；`metrics:` 在但 `enabled` 键缺失 = 放行；仅解析失败（yq 非零退出）= fail-closed（M8） | `_yq()` 对缺文件会裸 `raise`（`ship_gate.py:264`），不钉死则「文件缺失」误落 fail-closed；与 `anchor_lint._metrics_enabled` 四态对齐 |
| D2 | defer 台账行机读 schema 钉死：台账 = 表格行，id 列为独立单元格且**单元格全部内容 = 单个 id**（防描述列旧票号误抓假通过）；现有聚合摘要句（`SKILL.md:659` 含 "defer" 字面无 id）改写移出检测范围（M2） | 假阳（摘要句恒红）+ 假阴（T105 等真实旧票号误抓）双向失效，[[gate-substring-detection-dogfood]] 同族 |
| D3 | 机械引用核落盘段定义结构化锚 `sdflow:ref-check`（status/checked/pass/fail/uncheckable 计数），gate 检测锚而非段标题/散文（M5） | 「标题存在」形同虚设 vs 「[ref-check] 行存在」误伤零裁掉报告——两头都不可判，只有专用锚可机读 |
| D4 | B26 门对账升级：id 存在 ∧ 池文件存在 ∧ 池文件 frontmatter `change == 当前 change`（M6） | 不核 source_change 则误抄任意既有 id 即假绿；池文件已有该字段，成本一行 |
| D5 | 四个编排 SKILL 的 tier-resolution unset 清单同步扩含 `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（M4） | 旧 resolver + 同 shell 残留脏值 ⇒ 空值回落被击穿；与既有 V1 清脏条款同因 |
| D6 | 两道新门 verdict **字面复用 `STEP_IN_PROGRESS`**，不新增 verdict 名（M11） | sdflow-ship 熔断按 verdict 字面分治（`SKILL.md:170`），新名绕开熔断 = 无限重跑 |
| D7 | tasks 新增 4.0：自审（code-review/verify）前在 dev checkout 开全局窗口 `bash setup.sh`（时间盒），完毕后运行 checkout 还原（M9） | 机器实测 `~/.claude/skills/sdflow-ship` 软链运行 checkout ⇒ 不开窗口则自审跑旧 gate，「dogfood 自证」为空话且可能产出第 7 个缺锚样本 |
| D8 | tasks 2.1 探针方法论细化：定义手工临时放置 `~/.claude/agents/`（不经 install_agents，验证完删除）；生效信号用 token 用量/耗时 + 输出规模多信号，不以单一「规模」判；备选指针改 `adr/0043` Considered Options（M10 + M20） | 输出规模对 effort 是弱代理信号（假阴/假阳皆易）；memo K1 无「备选」内容，字面指引扑空 |
| D9 | scope-check 表补两行：`anchor_lint._metrics_enabled` ↔ ship_gate 新读取点（孪生实现一致性）；`init.py lint_config` ↔ `effort-tiers` 新键（M7 + M8 附属） | 两处独立演进静默漂移；新 config 键不进 lint = 错拼静默放行 |
| D10 | resolver effort 分支防呆：MUST NOT 复用 model tier 的 unknown 回落缺省逻辑（effort 语义相反：空串）；codex/unknown 分支显式初始化空串（`set -u` 下漏初始化 = 整个 resolver 中止殃及 model 导出）；不复用 `_resolve_tier` 告警路径（codex 侧恒告警违反自身 Scenario）（M13 + M14） | `resolve-models.sh:215`（unknown 回落 claude 缺省）与新 Scenario 语义相反，复制黏贴高危 |
| D11 | proposal 补 TG-24 定性成本小节；tasks 4.3 补 T98/T103/T105/T124 set-status；design 补 B26 最小序列图（recorder 失败分支）；`_parse_model_tiers_block` 引用修正为 `_model_tiers_from_dict`；门文案四子分支 cause 区分句 + render-prefix fail-loud 含 fix 指引句（M15/M16/M17/M18/M19/M21） | 各低成本一处，逐条见 findings 表 |
| D12 | design 门 metrics 检查补转换态提示：消费仓 `metrics.enabled` 在报告写就后翻 true 的场景，gate 失败文案提示「重跑 spec-review 或按既有人工补锚指引处置」（M12，低概率轻防御） | 通则④五问：概率低、影响中、完美成本高（时间锚定语义）⇒ 只加文案不加机制 |

### 低置信上抛（一行带过，不静默滤）

- **M22（DX5，低置信）**：4 个 SKILL 的 `description` frontmatter 本次是否受改动影响未在设计文本记录，按 devex 判表为 UNVERIFIABLE——若确认未改，design 一句话记录即可消解；defer 至实现期顺手确认。

### 已裁掉（反静默压制，可审计）

- **X1 · 接地镜 #17**「bundle `config.template.yaml` 无 `effort-tiers` 段落点」——**裁掉理由**：这正是本 change tasks 2.6 要新增的内容（目标态产物），拿现状快照核目标态清单属误报（通则③反向应用——现状缺失不构成设计缺陷）。接地镜其余 21 项核验全数一致或已单列（M21）。

（机械引用核 0 fail ⇒ 本轮无 `[ref-check]` 机械裁掉项。）

## 合并 findings 总表（23 条）

| ID | 问题（一句） | 命中镜 | 严重度 | 置信 | 裁决 |
|---|---|---|---|---|---|
| M1 | install_agents 单源硬编码 ×4 + manifest 覆盖写，第二源目录扩容未设计，孤儿清理/退役检测击穿 | strategy·plan-eng·backend·devex·对抗A·对抗B | Critical | 高 | 采纳 → **Q2** |
| M2 | defer 台账行机读判据未定义：摘要句子串假阳 + 描述列旧票号假阴 | backend·对抗A·对抗B | Critical | 高 | 采纳 → D2 |
| M3 | `max` 合法值无对应 agent 定义，派发断链无文案 | voice·devex | High | 高 | 采纳 → **Q1** |
| M4 | SKILL tier-resolution unset 清单不含 `SDFLOW_EFFORT_*`，脏值击穿空值回落 | voice（独家） | High | 高 | 采纳 → D5 |
| M5 | 「机械引用核落盘段」无机器可判格式契约 | voice·backend | High | 高 | 采纳 → D3 |
| M6 | B26 门不核 source_change，任意既有 id 假绿 | voice（独家） | Medium→High | 高 | 采纳 → D4 |
| M7 | `effort-tiers` 未接 `init.py lint_config`，错拼静默放行 | voice（独家） | Medium | 高 | 采纳 → D9 |
| M8 | ship_gate 读 config.yaml 机制留白（缺文件分支 / `_yq` raise / anchor_lint 孪生实现无一致性锚） | plan-eng·backend·对抗A·对抗B | High | 高 | 采纳 → D1+D9 |
| M9 | dogfood 自证时序不成立：自审跑运行 checkout 旧 gate（机器实测） | 对抗C（独家） | Critical | 高 | 采纳 → D7 |
| M10 | A1 探针「输出规模」信号效度弱 + 探针资产路径歧义（2.1 与 2.4 互绕） | 对抗A·对抗C | High | 中 | 采纳 → D8 |
| M11 | 新失败态不字面复用 STEP_IN_PROGRESS 则绕开熔断 → 无限重跑 | 对抗B（独家） | Medium | 中 | 采纳 → D6 |
| M12 | design 门用当前 config 回看旧报告，metrics 翻开后卡已批准设计 | 对抗B（独家） | Low | 中 | 采纳 → D12 |
| M13 | effort unknown 回落语义与 model tier 既有分支相反，复制黏贴高危 | backend（独家） | Medium | 中 | 采纳 → D10 |
| M14 | 复用 `_resolve_tier` 告警路径则 codex 侧恒噪声；`set -u` 漏初始化中止整个 resolver | 对抗B（独家） | Medium | 中高 | 采纳 → D10 |
| M15 | tasks 4.3 遗漏 T98/T103/T105/T124 状态回填（p3 有先例） | strategy（独家） | Medium | 高 | 采纳 → D11 |
| M16 | BASE-26 成本估算全篇缺失（成本工程 change 反而没有成本小节，p2 有先例） | strategy（独家） | Medium | 中 | 采纳 → D11 |
| M17 | B26 回路跨 3+ 组件无序列图（TG-10；design 自认时序风险点） | plan-eng（独家） | Medium | 中 | 采纳 → D11 |
| M18 | 两门四种失败根因共用单一文案，低于 `cause_category` 既有诊断精度线 | devex（独家） | Medium | 中 | 采纳 → D11 |
| M19 | render-prefix fail-loud 文案仅要求「说明缺失源」，未锁 fix 指引质量线 | devex（独家） | Low | 中 | 采纳 → D11 |
| M20 | tasks 2.1「按 memo K1 备选重估」扑空（备选实在 adr/0043 Considered Options） | 对抗C（独家） | Low | 高 | 采纳 → D8 |
| M21 | design 引用 `init.py::_parse_model_tiers_block`，实际函数名 `_model_tiers_from_dict` | grounding（独家） | Low | 高 | 采纳 → D11 |
| M22 | DX-05 SKILL description 影响未记录（UNVERIFIABLE） | devex | Low | 低 | defer（上抛一行） |
| M23 | config.template 无 effort-tiers 落点 | grounding | Low | 高 | 裁掉 → X1 |

已核对镜自报「放过的面」：对抗镜三面共放过 12 个查证面（`model: inherit` 与 `model` 参数并用机制自洽、B26 id 生成确定性、任务时序无环、P0 独立可交付、fence-aware 复用无新假阳面等），与采纳集无矛盾。

## 各机制核验（design-diagrams / 图）

- 依赖图（TG-14）：存在（design.md）且与组件清单一致，未过时 ✅
- 测试覆盖图（TG-18）：存在（tasks.md）✅
- 序列图（TG-10，B26 回路跨 SKILL/recorder/gate 3 组件）：**缺失** → M17，amendment 已补最小时序描述
- v_old/v_new、状态机图等：对应 TG 未命中，不适用

## 诚实边界声明

- 能力探针：host=claude 免探恒 available；`mirrors=`/`mode=` 为主 session 自报，anchor_lint 只核锚行文法自洽，非机械保证。
- `findings=N` 与合并池实收数的数值一致性、lens-metric 分类正确性 / roster 完备性 / findings 誊写准确，均为主 session 信任边界（emitter 只保证确定性归约）。
- 本轮无 hr-tg voice（HR-TG∩=∅，`hr_tg_intersect.py` 判定见锚行）；design-voice 全量 context 4924 字节未截断。

## 评审价值度量（lens-metric）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="6" sev="致3/高2/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="3" sev="致1/高1/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="9" 采纳="8" 裁掉="0" defer="1" 独立="3" sev="致2/高3/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="3" sev="致0/高3/中2/低0" -->

（拍板前草稿值；per〔SR-M〕，设计门拍板回写时如需拍板项改向将原地最终化。）

## 收敛口（1.6）

**建议：修订后进设计 HARD-GATE。** 21 条采纳 findings 的 amendment 已回流四件套（标 `[spec-review-amendment]`）；Q1/Q2 两个拍板点不阻塞阅读但**须在批准前勾选**（Q2 属 Critical 面——install_agents 扩容方案不定，任务 2.4 无法开工）。拍板流程提醒：本报告审的是 `bdd5ef4` 盘面，amendment 构成拍板前修订 ⇒ 按 ADR-7(b)，amendment 已单独 checkpoint 落盘，拍板回写 `reviewed_sha` 时取该 checkpoint 的 sha（含 amendment 的盘面）；若拍板时再改四件套（如 Q1/Q2 选非推荐项），MUST 先单独 checkpoint 再回写锚。
