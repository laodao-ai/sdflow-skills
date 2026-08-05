---
schema_version: 1
change: refactor-roadmap-internalize-deps
branch: feat/refactor-roadmap-internalize-deps
generated_at: 2026-08-05T21:32:39+08:00
decision_hash: f49d3d813188
---

# 决策纪要 · refactor-roadmap-internalize-deps

## 目标态

`sdflow-roadmap` 重构为与 sdflow-spec 同构的三相位结构（A 澄清 → B 七维拷问按信号裁剪 +
memo 增量落盘 → C 生成三件套），消除 wayfinder / grilling / domain-modeling / office-hours /
matt tracker 五个外部依赖并整体移除 `openspec/matt/`，review 层外部依赖原样保留。

## 承重约束

- **C1 · matt 无其他运行时消费方**：全仓 grep，`sdflow-implement` 的 matt 引用全是出处注释
  （SKILL.md:228/459/561-562/788/797-798、impl_route.py:5/420/431），无代码读
  `openspec/matt/` 路径；活消费方仅 sdflow-roadmap wayfinder preflight（本次删）+
  CLAUDE.md/AGENTS.md matt 区块 + roadmap-planning spec（本次改）。⇒ D2 可行。
- **C2 · roadmap-planning spec 是最大牵连面**：`openspec/specs/roadmap-planning/spec.md`
  （176 行）至少 4 个 Requirement 锚定被删机制——讨论层路由（:49-81）、footage 落盘与引用
  边界（:83-110）、review 分档（:112-129）、收尾 checklist（:131-148）。delta 必须覆盖。
- **C3 · 存量 footage 真实存在**：`openspec/roadmaps/issues-triage-2026-08/` + archive 下
  wco/mlh 两包含 footage 引用 ⇒ 兼容冻结条款必须有（D7）。
- **C4 ·「历史记录」被 task-log 语境占用**：现 SKILL.md:252-253 replan 条款明文
  「保留既有 task-log.md 的历史记录」⇒ D8 弃「历史记录」选「历史存档」。
- **C5 ·「考古层」同串双语义**：DOC-1 语境（rules/doc-authoring.md:63-66、BASE-30、T169、
  CLAUDE.md:183-184）指文档正文演进史，与 roadmap 语境不同概念 ⇒ 禁全局替换（D8 范围限定）。
- **C6 · gate-0 与需求真实性两关独立**：现 SKILL.md:277 + spec:51 明文「五项全过不能免除
  野心信号检查」⇒ D6 三态路由，照 handoff 二路径图实现即静默缩水。
- **C7 · office-hours 六问结构核实**：Q1-Q6 在 office-hours/SKILL.md:1096-1155，自带按
  项目阶段裁剪路由表（:1089-1092，`Pure engineering/infra → Q2, Q4 only`）⇒ 七维吸收映射
  成立；handoff 漏列 Q3（绝望具体度），吸收时补入维度①的追问弹药。
- **C8 · bundle 牵连仅一处规则 + 一处史录**：`ff-generation-constraints.md:46-47`
  （`wayfinder-resolved:` 前缀禁混用）+ `workflow-history.md:27-32`（A3 演进史）⇒ D10。
- **C9 · review 层降级路径已焊**：现 SKILL.md:449「未审待恢复」不静默条款 ⇒ D1 保留外部
  依赖不新增风险。
- **C10 · 增量落盘同构先例**：sdflow-spec B.4（B 轮数无上界，一次性落盘 = 收敛前中断全损）
  ⇒ D4/D9 的结构论据；wayfinder「map 先建、票增量 resolve」本质同模式。

## 拍板决策

### D1：review 层保留外部依赖原样（人已拍板 2026-08-05）

`/plan-eng-review`（默认档）+ `/autoplan`（野心信号档）继续作为外部依赖，不内化、不简化，
既有降级路径（未审待恢复、不静默）原样保留。
依据：① review 价值在独立冷视角，内化进同 session = 产者自审；② 拆分标准——讨论层内化
已是完整内聚交付物，review 层是另一个能力面；③ gstack 是用户长期维护的自建套件，非脆弱三方。

### D2：openspec/matt/ 整体移除（人已拍板 2026-08-05）

roadmap 重构后本仓再无 matt 套件的活消费方（sdflow-implement 的 matt 引用全是出处注释，
无运行时依赖）。移除 `openspec/matt/` 目录 + CLAUDE.md / AGENTS.md 的 matt 区块
（Issue tracker / Triage labels / Domain docs）。
牵连：T134（domain-modeling 读 matt/domain.md）前提变化，随本 change 处置。

### D3：change 名 = refactor-roadmap-internalize-deps（人已确认 2026-08-05）

### D4：memo.md = 轻量决策纪要，不搬 schema+hash 机械层（人已拍板 2026-08-05）

包根 `memo.md` 升格为相位 B 的唯一决策载体（角色对齐 sdflow-spec 的 decision-memo），
但保持轻量：头部只记包名 + 日期，无 frontmatter/decision_hash 机械核验。
规则 3 原样保留——三件套仍不引用 memo（三件套自足是长期真相源的核心属性）。
依据：hash 层在 sdflow-spec 是为 C.1 机械门服务；roadmap 无 ship gate、无 CLI 载荷消费 memo，
且下游有 review 层 + 收尾 checklist 两道兜底。跨 session 续错包的残余风险由
create/continue/replan 显式确认挡住（五问判：低概率小影响，完美成本过高）。

### D5：术语改名——「结晶」→「生成」、「野心信号」→「商业化信号」（人已拍板 2026-08-05）

- **相位 C 命名「生成」**：与 sdflow-spec 三相位名对齐（A 澄清 / B 拷问 / C 生成）；
  「结晶」是比喻词、不自明。消费面（SKILL.md / spec / memo-template / CONTEXT.md footage 词条）
  全在本次重写范围内，额外成本≈0；`docs/` 历史文档不追改。
- **「产品/商业野心信号」→「商业化信号」**（人定名，否决了我推荐的「产品化信号」）：
  词表不变（外部用户、变现、获客、用户画像未定、"要不要做这个产品"）。
  消费面无 .py/.sh 脚本硬编码（已 grep 全仓核过），SKILL.md / roadmap-template ×2 /
  spec / INDEX.md 一行，除 INDEX 外全在重写范围内。
- **「相位 A/B/C」保留不换**（人两轮探讨后确认 2026-08-05）：候选「阶段」撞管线阶段一/二/三 +
  roadmap 产物阶段（双重占用）、「步骤」撞微观动作层（步骤套步骤）、「环节」可行但需全仓
  统一换（30+ 文件 + 6 个 .py 测试锚，属独立 change）。生成期 MUST NOT 改此词。

### D6：gate-0 通过路径保留商业化信号检查——三态路由（人已拍板 2026-08-05）

```
gate-0 通过 ∧ 无商业化信号 → 直接生成
gate-0 通过 ∧ 商业化信号命中 → Phase B（裁剪到维度①，startup 味逼问）→ 生成
gate-0 未通过 → Phase B（按信号七维裁剪）→ 生成
```

依据：gate-0 验讨论充分度、不验需求真实性，两关独立（现行 spec 明文）；office-hours
内化后检查执行体 = B 维度①单维拷问，保留的结构成本归零，砍掉 = 静默缩水。
handoff 的「二路径」图据此修正为三态。

### D7：收尾 checklist 五项 → 四项 + 存量 footage 冻结（人已拍板 2026-08-05）

- ①（Review 处置，含机械脚本门）②（三件套引用完整）③（历史存档未被引用）原样保留；
  ③ 的「历史存档」覆盖包根 memo.md 与存量 footage/。
- ④（wayfinder 闭环）整项删除——检查对象不复存在。
- ⑤ 简化为「memo 对账」：B 相位写 CONTEXT.md/adr 走提议制 + 人确认（同 sdflow-spec B.6/B.7），
  确认写入均在 memo 留痕 ⇒ 收尾逐条对照 memo 写入记录与三件套终稿，废弃 git 基线 diff 机制。
  诚实边界：绕过提议制手改 CONTEXT.md 的场景查不到（指令层约束固有边界，如实声明）。
- 存量 footage 冻结为合法历史形态（对齐 requirements.md 兼容先例）：续跑不报错、不强推迁移、
  不新增票、不要求闭环，未决票视为历史遗留；至多一行提示。

### D8：「考古层」（roadmap 语境）→「历史存档」（人已拍板 2026-08-05）

memo.md + 存量 footage/ 的统称改为「历史存档」。候选「历史记录」被否：该词已被 task-log
语境占用（replan 条款「保留既有 task-log.md 的历史记录」），同文件一词两义。
行文纪律：「归档」继续专指 roadmaps/archive/ 与 map 归档等目录动作。
🔴 范围限定：DOC-1/BASE-30/T169 语境的「考古层」（文档正文演进史残留）是另一概念，**不改**——
同串双语义，禁止全局替换。CONTEXT.md footage 词条随 wayfinder 移除重写为「历史存档」定义。

### D9：B 起手即建包目录 + 草稿 memo，放弃即删目录（人已拍板 2026-08-05）

- B 起手四步：判定进 B → 定 `{name}` → 判同名包 create/continue/replan（**判定前移到 B 起手**）
  → 建 `openspec/roadmaps/{name}/` + 落草稿 memo.md。
- 重入协议：新 session 探测 `openspec/roadmaps/*/memo.md` 存在且无定稿标记 ⇒ 呈现包 +
  memo 摘要，问人「继续 B 还是新开」（与 sdflow-spec 0.3 同构）。
- 直接生成路径（gate-0 过 ∧ 无商业化信号）：维持生成时建目录，memo 可不存在。
- 拷问中途放弃 ⇒ **删包目录**（与 sdflow-spec「删分支即净」对齐；未定稿 memo 无保留价值）；
  continue/replan 场景放弃时只删本次新增内容，不动既有文件。
- 中断损失窗口 = 两次落盘之间，如实声明，不称零损失。

### D10：bundle 牵连处置（自决 2026-08-05，已向人声明无异议）

`ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀禁混用规则**保留 + 加 legacy
标注**（消费仓存量 footage 仍可能被溯源，不能删）；`workflow-history.md` 追加一条
wayfinder 路径移除的演进记录。bundle 改动后按 dev checkout 纪律跑 setup.sh。

### D11：T134 随本 change 关 OBSOLETE（自决 2026-08-05，已向人声明无异议）

前提消解：重构后本仓工作流无 domain-modeling 调用点，matt/domain.md 随 D2 删除。
实现期以 sdflow-issues set-status 处置并附 evidence。

### D12：explore 移出讨论层内部路由（自决 2026-08-05）

现行「分支 A = /opsx:explore」不再是 skill 内部分支；对齐 sdflow-spec 模式——想法尚未
成形时**先 explore 再 /sdflow-roadmap**（上游可选步，SKILL.md 入口处一句指路即可）。
讨论层内部只剩三态路由（D6）。

### D13：杂项处置（自决 2026-08-05）

- 七维拷问的商业化信号词表**内联 SKILL.md**（skill 是独立分发单元，不引仓内文件）。
- 模板：memo-template.md 重写为 B 相位纪要模板（轻量，头部包名+日期）；design/roadmap
  模板改术语；long-flow-skill-paradigm.md 的 wayfinder 段落改为历史注记。
- `docs/workflow-skills/matt-pocock-workflow.md`、`setup-matt-pocock-skills.md` 等 docs/
  历史文档**不追改**（非规则源）；`docs/external-dependencies.md` **必须更新**（活文档，
  删 wayfinder/grilling/domain-modeling 依赖节）；handoff 草稿实现后删除。
- 判定留痕总则三判定点保留、随新结构重编号（①三态路由 ②review 分档 ③收尾 checklist 四项）。

### D14：ADR 一条 + CONTEXT.md 词条两处，实现期落（人已确认 2026-08-05）

- ADR：「sdflow-roadmap 讨论层内化与 matt 套件移除」——三条件全中（难逆转 / 缺上下文会
  意外（存量 footage 无产出机制）/ 真实权衡（内化分界线：讨论过程是内在职责、冷审价值恰在
  外部性 ⇒ 讨论层内化、review 层留外））。
- CONTEXT.md：① footage 词条重写为「历史存档」定义；② 新增「商业化信号」词条。
- 时机均放实现期（进 tasks.md），避免全局共享文件领先实际形态。

## 接受的边角

- **B 中断损失窗口**：两次 memo 落盘之间的讨论内容中断即丢——概率中、影响小（重问一轮即可）、
  完美成本高（逐句落盘不现实）；与 sdflow-spec 同口径，如实声明不称零损失。
- **memo 无机械身份核验**（D4 的代价）：跨 session 续错包的极端场景靠 create/continue/replan
  显式确认挡——概率低、影响可逆（生成前有人门）、完美成本 = 搬整套 hash 机械层。
- **⑤ 简化后的盲区**（D7 诚实边界）：绕过提议制手改 CONTEXT.md/adr 的写入收尾门查不到——
  属指令层约束固有边界，原 git 基线机制也只覆盖长档路径，非本次新增缺口。
- **拷问中途放弃未删目录**：残留半途包由下次重入探测呈现给人处置，不设自动清扫。

## 三镜代价

D1（review 层保留外部依赖 vs 内化）为本次唯一实质方案选择：
- **系统镜**：仓库继续保留 `/plan-eng-review` + `/autoplan` 两个 gstack 依赖（降级路径已焊，
  失效不静默）；耦合面不变、无新增。
- **用户镜**：新机器未装 gstack 时 review 走「未审待恢复」提示，多一步安装动作。
- **开发循环镜**：本次 change scope 收敛为一个完整内聚交付物（讨论层内化），不膨胀；
  冷审独立性不因内化受损。
- **主次判定**：开发循环镜为主——scope 内聚是一次做完的前提；系统镜代价可接受。
