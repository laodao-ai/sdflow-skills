# Design: rebuild-sdflow-roadmap-v2

## Context

sdflow-roadmap 现行形态（五阶段：讨论 → 开 `plan-{topic}` change 壳 → 产四件套 → autoplan 三连审 → 归档）在两个真实案例上实测：壳产物 52/55 行 vs 文档包 1333 行；requirements.md 在全部归档中零实施引用（仅 plan change 自身 tasks 勾选项与 1 条导航行）；design.md 被实施 change 引为「整体架构/立论权威源」9 处；脚本侧仅 `roadmap_writeback_draft.py:349` 读 `roadmap.md`、`:276` 产 task-log 完成总结骨架，**零处读 requirements.md**（已 grep 核验）。2026-07-10 探索会（三个接地调研代理 + 主 session 亲验）拍板本次重构方向；wayfinder 侧的落盘约定注入点已亲验为 `openspec/matt/issue-tracker.md:22-31` 单点。

## Goals / Non-Goals

**Goals：**

- 三件套（design/roadmap/task-log）取代四件套，PRD 角色降为 design.md 伸缩头部章
- roadmap 文档包产出去 change 壳，recorder 式直写
- 长讨论由 wayfinder 承载（footage/ 落盘），memo 降级为短档可选
- roadmap.md 近细远雾；review 按野心分档
- 存量两包迁移 + 全仓「四件套」表述同步

**Non-Goals：** 见 proposal.md Non-Goals（5 条，各附可证伪假设）——wayfinder→ff 衔接契约（T126/T127）、wayfinding 机械校验、回填助手改动、recorder 后端可插拔、产品型展开段深化。

## Decisions（决策记录，TG-23）

### D1 · 合并方向：requirements 并入 design（三件套），而非反向或二件套

- **候选**：A 保持四件套；B requirements 并入 design（选中）；C 全并入 roadmap.md（二件套）。
- **理由**：消费侧不对称是决定性证据——design.md 有 9 处归档实质引用（如 `archive/2026-07-07-mlh-p1-issues-sweep/design.md:3`「整体架构/立论权威源」），文件名保留则引用零断链；requirements.md 零实施消费者；C 会把稳定考古层（决策档案）和高频进度层（阶段状态）搅进同一 diff，且 roadmap.md 已是最长活文档。requirements 独有的两块载重内容（验收门槛表、愿景/目标态判据）整块搬入 design 头部，包内节级引用一次修补。
- **三镜与主次**：系统镜——单一源块从 4 处降 ≤2 处，漂移面收窄（mlh-p2 F8 类矛盾的结构性消除）；用户镜——写作与收口更新省一个文件的同步；开发循环镜——一次性文本修补（SKILL.md:4,48,138,182,211,222,265,277,340 + 4 份模板导航块 + 3 处仓级表述，全部已 grep 穷举）。**主判定：系统镜为主**——同步面收窄是实证痛点的直接根治，迁移成本一次性且可穷举。

### D2 · 去 change 壳：recorder 式直写

- **候选**：A 保壳（现状规则 4）；B 直写（选中）。
- **理由**：壳的四项收益逐项落空——归档快照≈0（文档包本就长期留存）、verify 对纯文档近空转（SKILL.md 自认 verify 不查内容质量）、review 处置载体本就在 task-log.md、retro 度量损失已由用户明示不在意。直写先例已立：buglist/todolist/issues 三 recorder 直写 `openspec/issues/`。roadmap 文档包性质 = 长期活文档（issues 池同类），非一次交付即冻结的 change 交付物。
- **软门迁移**：「review 处置完才算完」从 archive 时刻移到 skill 收尾 checklist——两个世界均无机械门（verify 不扫处置小节），载体与强度不变，仅触发时机前移。
- **主判定：用户循环镜为主**——去掉的是纯仪式（开壳/verify/archive 三步），系统性损失经逐项核查为零或已被接受。

### D3 · footage 落盘：tracker doc 条件分流（方案 B）+ 调用语辅助（C 兜底）

- **候选**：A 全局改（Wayfinding 约定整体迁 roadmaps/）；B 条件分流（选中）；C 仅调用时注入路径。
- **理由**：B 用 wayfinder 自己设计的唯一注入点（`openspec/matt/issue-tracker.md` Wayfinding 小节，wayfinder/SKILL.md:25 明示查此处），单文件改动生效；票号 NN 本就 per-effort 作用域（issue-tracker.md:10,27）、frontier 本就只扫本 effort `issues/`（:29）、map 标签在本地 tracker 为「文件名即 map.md」——重定向零机制破坏。A 会迫使非 roadmap 讨论也进 roadmaps/ 污染目录契约；C 违背 wayfinder 设计（后续 work-through session 只带 map 路径调起时读 tracker doc 会得到不一致约定）。C 作辅助：sdflow-roadmap 发起 effort 时在调用语顺带声明 map 路径，双保险但以 tracker doc 为准。
- **主判定：系统镜为主**——注入点唯一性是这个方案成立的结构性理由，其余两案都制造第二真相源或路径不一致。

### D4 · 长讨论引擎：直接依赖 wayfinder（不做「借形不借体」平行实现）

- **候选**：A 直接调用 matt 套件（选中）；B 抄 map/fog-of-war 形态做 sdflow 自有轻量版。
- **理由**：用户已拍板依赖无问题（workflow 本就依赖 grill-with-docs → grilling/domain-modeling 同源）；B 需永久维护一份平行实现，违背单一源纪律。wayfinder 内建自降级（chart 第 2 步无雾即停）天然接住小讨论误入。域文档层已对齐（matt domain.md 与 grill 共用 `openspec/CONTEXT.md` + `openspec/adr/`），衔接零额外工作。
- **主判定：开发循环镜为主**——不养平行实现是长期维护成本的决定项。

### D5 · review 分档：默认 plan-eng-review 单跑

- **候选**：A 默认 autoplan 三连（现状）；B 默认 eng 单跑、野心才三连（选中）。
- **理由**：现状 SKILL.md 已承认「纯技术重构无产品野心 → CEO review 可跳」「简单项目 → 单跑 eng」；本仓两个真实 roadmap 均为工作流型，三连审的 CEO/design 轴基本空转。分档判据可观察（外部用户/变现/获客信号）。风险（单审漏产品盲区）由消费期实施 change 的 spec-review 兜底，成本后移可接受（见 proposal 假设 3）。
- **主判定：用户循环镜为主**——review 是流程中最重的 token/时间项，分档直接砍默认成本至 1/3。

### D6 · memo 降级：footage 取代长档 memo，短档 memo 可选保留

- **理由**：memo 策略表的存在动机（讨论过程对抗 compaction）被 footage 结构性解决——map+tickets 就是持久化的结构化 footage，且有 Decisions-so-far 索引，优于线性 memo。短档讨论（单 session）无跨 session 风险，memo 保留为可选（不写则 design 决策章写厚，现状规则不变）。规则 3「不引用 memo」措辞扩展为「不引用 footage/（含 memo）」——考古层语义统一。

### D7 · 近细远雾：roadmap.md 阶段分层

- **理由**：实证——mlh roadmap.md 六阶段全写满五节（254 行），task-log.md:86 记录 adr/0010 判据中途被目标态复核推翻；远期细节写得越满、推翻时废稿越多。fog-of-war 判据（「能否现在精确表述」而非「能否回答」）来自 wayfinder/SKILL.md:88，已在 matt 调研可借鉴机制表列为第 1 条。补细时机 = 前序阶段全交付、该阶段进入待实施（spec Scenario 已定义）。
- **与回填助手的相容性**：`roadmap_writeback_draft.py` 按 adr/0015 适配现状散文、仅按 `assoc["roadmap"]` 定位 `roadmap.md`（:349）生成草稿供人确认——远期阶段薄写不影响其读点（回填只发生在已实施阶段，那些必然已补全五节）。

## 组件清单与依赖图（BASE-25，TG-14）

| 组件 | 角色 | 本次变更 |
|---|---|---|
| `sdflow-roadmap/SKILL.md` | 规划工作流编排指令 | 主体重写（三件套/直写/分档/footage/近细远雾/收尾 checklist） |
| `sdflow-roadmap/references/` | 模板骨架（5 → 4 个） | 删 requirements-template；design-template 加头部章；余者导航块与注释更新 |
| `openspec/matt/issue-tracker.md` | wayfinder 落盘约定唯一注入点 | Wayfinding 小节条件分流 + 双语标题 |
| CLAUDE.md Agent skills 托管块 | 约定第二锚 | 补 footage 一句 |
| wayfinder / grilling / domain-modeling（外部） | 长讨论引擎 | 零改动，运行时依赖 |
| plan-eng-review / autoplan（外部 gstack） | 内容质量 review | 零改动，调用推荐变化（adr/0002 边界内） |
| `roadmap_writeback_draft.py`（sdflow-done） | 回填草稿助手 | **零改动**（读点已核不含 requirements.md） |
| 存量两 roadmap 包 | 长期真相源实例 | requirements 并入 design + 引用修补 |

```mermaid
flowchart LR
    SK["sdflow-roadmap SKILL.md"] -->|长档路由| WF["wayfinder（外部）"]
    WF -->|查约定| TD["openspec/matt/issue-tracker.md<br/>Wayfinding 小节（唯一注入点）"]
    TD -.第二锚.- CL["CLAUDE.md 托管块"]
    WF -->|落盘| FT["roadmaps/{name}/footage/"]
    SK -->|结晶直写| PKG["roadmaps/{name}/ 三件套"]
    SK -->|分档调用| RV["plan-eng-review / autoplan（外部）"]
    DONE["sdflow-done 回填助手"] -->|只读 roadmap.md/task-log.md| PKG
```

## 序列图：长档端到端（TG-10）

```mermaid
sequenceDiagram
    participant U as 用户
    participant SK as sdflow-roadmap
    participant WF as wayfinder
    participant FT as footage/
    participant PKG as 三件套
    U->>SK: 帮我规划 X（判长档）
    SK->>WF: chart（destination=三件套定稿）
    WF->>FT: map.md + 首批票（查 tracker doc 得根目录）
    loop 逐票（可跨 session）
        U->>WF: work through map
        WF->>FT: 决议评论 + Decisions-so-far 追加
    end
    WF-->>SK: 无票剩余（way is clear）
    SK->>PKG: 结晶直写三件套（不引用 footage）
    SK->>U: review 分档判定 → plan-eng-review（默认）
    SK->>PKG: task-log「Review 处置」逐条标注
    SK->>SK: 收尾 checklist（无未处置 → 完成）
```

## 分档路由决策图（TG-12）

```mermaid
flowchart TD
    S["讨论充分度检查"] -->|已充分| CRYST["直接结晶"]
    S -->|不足| SIZE{"预估规模"}
    SIZE -->|"单 session 收得住"| EXP["/opsx:explore（可选 memo）"]
    SIZE -->|">30 轮 / 跨天 / 跨 clear"| WFC["wayfinder chart"]
    WFC -->|无雾自降级| EXP
    WFC -->|有雾| MAP["footage/ 铺图逐票"]
    EXP --> CRYST
    MAP -->|决策集收敛| CRYST
    CRYST --> REV{"产品/商业野心?"}
    REV -->|否（默认）| ENG["/plan-eng-review"]
    REV -->|是| AP["/autoplan 三连"]
    ENG & AP --> CK["收尾 checklist"]
```

## 失败模式表与可观测性（D-4，TG-08）

外部依赖为 skill 间调用与文件约定，无网络/超时语义；「超时」栏以「不可用判定」代之。全部降级路径显式提示、不静默（反静默铁律）。

| 失败模式 | 判定方式 | 降级路径 | 回滚 |
|---|---|---|---|
| wayfinder 未安装 | 起手 `ls ~/.claude/skills/wayfinder/SKILL.md` 不存在 | 显式告知 + 退回 explore+memo（旧长档策略），流程不阻塞 | — |
| grilling/domain-modeling 未装 | wayfinder 票内调用失败 | 票内降级为普通对话式讨论，票照常 resolve；提示装 matt 套件 | — |
| tracker doc Wayfinding 小节缺失/被覆盖 | wayfinder 起手查不到分流规则 | wayfinder 按默认落 `openspec/matt/<effort>/`——**错位但不丢数据**；skill 起手核对小节在场，缺失即提示恢复（第二锚 CLAUDE.md 供比对） | 手工搬移 map+tickets 至 footage/（纯文件移动） |
| setup-matt-pocock-skills 重跑覆盖定制 | 人在环草稿确认时发现 openspec/matt/ 与草稿不符 | CLAUDE.md 第二锚提示定制在场；覆盖后 git diff 可见、revert 即回 | `git checkout openspec/matt/` |
| 存量迁移中断 | 三件套引用断链（收尾 checklist 项） | checklist 拦截提示补齐 | `git revert`（迁移为纯文本 commit，requirements.md 内容在 git history 永存） |

**可观测性**：分档判定结果（explore/wayfinder/直接结晶）、review 分档判定（eng/autoplan/跳过）、收尾 checklist 结果——三个判定点均要求在对话中显式陈述一行 + task-log.md 留痕（跳过类判定须显著呈现，不埋长消息）。

## 契约文档套件 scope-check 表（BASE-29，TG-25）

「四件套→三件套」牵连的全部文件（grep `requirements`/`四件套` 穷举，行号已核验）：

| 文件 | 受牵连处 | 处置 |
|---|---|---|
| sdflow-roadmap/SKILL.md | :4,48,138,182,211,222,265,267,277,340 | 主体重写覆盖 |
| references/requirements-template.md | 整文件 | 删除 |
| references/design-template.md | :16 导航 | 更新导航 + 增头部章骨架 |
| references/roadmap-template.md | :19 导航 | 更新导航 + 近细远雾注释 |
| references/task-log-template.md | :20,69 导航 | 更新导航 |
| references/memo-template.md | :23,27,117 | 更新为 footage 语境（短档可选定位） |
| CLAUDE.md | :79「四件套」 | 改三件套 + footage 表述；托管块补第二锚句 |
| README.md | :22「四件套」 | 改三件套 |
| docs/sdflow-fable5/02-module-reference.md | :205 | 改三件套 + 去壳表述 |
| openspec/matt/issue-tracker.md | :22-31 Wayfinding 小节 | 条件分流 + 双语标题 |
| 存量 wco 包 | requirements.md 整文件 + design/roadmap/task-log 中 6-7 处节级引用 | 并入 + 修补 |
| 存量 mlh 包 | 同上 | 并入 + 修补 |
| 归档树内历史引用 | `archive/2026-07-07-plan-mechanical-layer-hardening/design.md:6` 等 3 处 | **不回改**（归档不可变），合并文件头加考古注记 |

## Risks / Trade-offs

- **[风险] wayfinding 六操作在本仓未实测**（约定核读过、没跑过）→ 缓解：tasks 含一次最小实测（建一个演练 effort 走 chart→claim→resolve→frontier 全操作）；失败则按 proposal 假设 1 降级 explore+memo，不阻塞其余交付。
- **[风险] 「roadmap 类 effort」判别依赖调用语/人工指认**（无机械信号）→ 缓解：tracker doc 措辞给出双判据（隶属声明 or 由 sdflow-roadmap 发起）；残余风险接受（错落 openspec/matt/ 仅错位不丢失）。
- **[取舍] 巡检面拆两处**（open 票分布 openspec/matt/*/issues/ 与 roadmaps/*/footage/issues/）→ 接受：frontier 查询本就 per-map，跨面巡检非高频动作。
- **[取舍] design.md 变长**（合并后 wco 约 180 行、mlh 约 300 行）→ 接受：仍低于 roadmap.md 现有长度；头部章有固定小节锚便于跳读。
- **[风险] 首个产品型 roadmap 时伸缩段不够用** → proposal 假设 5，按实例补节，不预设计。

## Migration Plan

1. skill 与模板重写（P0）→ dev checkout 跑 `setup.sh`（adr/0005：symlink 场景改 SKILL.md 即时生效，重跑为防新增/删除模板文件产生孤儿）。
2. tracker doc 分流 + CLAUDE.md 第二锚（P0，与 1 同 commit 可）。
3. 存量两包迁移（P2）：每包一次 commit——requirements.md 内容整块并入 design.md 头部章 → 修补包内节级引用（wco：design:62、roadmap:69 等；mlh：roadmap:110、task-log:63,98 等，实施时逐一 grep 复核）→ 删 requirements.md → 合并文件头加考古注记（「2026-07 起 requirements 并入本文件，历史版本见 git」）。
4. 全仓表述同步（P2）。
5. **回滚**：整链纯文本，`git revert` 逐 commit 可逆；requirements.md 历史内容 git 永存。

## Open Questions

见 proposal.md 开放问题表（2 条：effort 判别措辞——本 design D3 已给推荐「隶属声明 or sdflow-roadmap 发起」，最终措辞实施时定稿；产品型 NFR 小节取舍——留占位注释）。

## Compliance（规则/边界合规声明）

- **D-6 边界确认**：roadmap 包结构为 sdflow-roadmap（producer）/ sdflow-done 回填助手（consumer）/ 实施 change 引用（consumer）三方共享契约。本次仅移除 requirements.md（零消费者，grep 核验 `roadmap_writeback_draft.py` 无读点、归档无实施引用）并保留 design.md/roadmap.md/task-log.md 文件名与散文格式——**共享边界未越界**。
- **adr/0015**：遵守——不新增机器锚、不做机读化迁移、回填判断留人；存量迁移属文档合并非机读化。
- **adr/0002**（gstack 复用输出不改内部）：遵守。**adr/0003**（不动全局规则 bundle）：遵守——本次零 assets/workflow 改动。**adr/0005**（dev/runtime 分治）：遵守——见 Migration 1。
- **adr/0013/0014**：已被 0015 supersede 的机械回写骨架不构成约束；0013 保留内核「盘面即真相源」与本设计一致（footage/三件套均落盘）。
- 生成约束：D-1 全部代码事实已先 grep 核验（本文行号均来自本次核验输出）；D-3 见 proposal Non-Goals；D-5 见 proposal Success Metrics。
