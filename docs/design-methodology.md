# sdflow 设计/分析方法论（结构层的「怎么想」姊妹篇）

> **定位**：[`workflow-map.md`](workflow-map.md) 是**结构层（what）**——阶段×脚本门×frontmatter 锚×分发链，一张表看全工作流「长什么样」。本文是**方法层（how）**——在这套结构里**怎么定 scope、怎么机械化、怎么决策**，结构层从不覆盖这层。
>
> **真相源纪律**：三条基准的权威定义在**项目 `CLAUDE.md`「设计/分析基准原则」节** + 自动记忆（`mechanize-first-target-state-baseline` / `change-scope-one-complete-stage-result`）+ `adr/0019`。本文**引用不复制**（narrative + 案例），基准措辞以 CLAUDE.md 为准。
>
> 立于 2026-07-11（grill/spec-review `harden-hr-tg-anchor-consistency` 时确立）。

---

## 1. 三条基准（引用 CLAUDE.md，此处只给一句话锚 + 为什么重要）

| 基准 | 一句话 | 权威源 |
|---|---|---|
| **① 机械化优先 + 目标态导向** | 能用「固化规则 + 脚本」确定性保证的一致性**优先机械化**；机械真够不着的残余（无确定性信号）才用语义规则兜。以**目标态**为准，**MUST NOT** 用「现状语料少/没出现」反驳目标该做 | CLAUDE.md · memory `mechanize-first-target-state-baseline` |
| **② 一个 change = 一个完整阶段结果** | scope 按「一个完整内聚交付物」定，不按同批来源/顺手/凑票数；**别拆碎、别混做**；执行中撞到的相关 bug/todo **立即 fold**，唯一合理 defer = 依赖的模块尚不存在 → 占位 + todo | CLAUDE.md · memory `change-scope-one-complete-stage-result` |
| **③ 面治优先于点补** | 机械化时把同片一致性面**一次扫全**，非只补当场被点穿的一处 | memory `point-vs-surface-fix` |

**为什么这层重要（结构层看不见的坑）**：
- **碎片化是"反复现状妥协"的根因**——把一件事拆成多个 defer fragment，逐个捡起来时每个都触发「对现状提问 → 给 WARN/grace/flag 妥协」。一次做完整、fail-closed，妥协根本不产生。
- **诚实边界 = 合法残余划分，非弱点**——别把「有一格不可机械」当成「整个机械化不值得做」的理由。
- **冷层承重**——热层（生成/grill）会自我说服，机械/语义边界的真漏洞常由冷独立层（对抗镜/codex 跨模型）抓（见案例）。

---

## 2. 案例：hr-tg 锚一致性机械化（三基准怎么落地）

`harden-hr-tg-anchor-consistency` 是三基准的首个完整落地样本。

### 2.1 目标态 vs 现状（基准①）
- **踩坑**：grill 时曾用「corpus 多数 hr-tg 锚是手写 `evidence=`、无 `declared=` → 重算覆盖薄、可不做」论证降级——**违基准①**（拿现状反驳目标）。
- **正解**：锚**目标态**（所有锚经脚本产出、必有 `declared=`），把 hr-tg 锚一致性拆成机械层全做：
  - **M1** `declared=` 硬必填 · **M2** `hit = declared∩HR-TG` 重算 · **M3** tg-set/成员严格解析 · **M4** `hit≠none ⟹ evidence=` 在场 · **M-new** declared/hit 的 TG 存在于 catalog 全集
  - 唯一语义残余 **S1**：`declared` 是否=真命中集（「命中哪些 TG」无确定性信号）→ 留模型 + evidence 人读 + git 审计（诚实边界，非弱点）。

### 2.2 零妥协（基准① + 碎片化根治）
把三个 fragment 视角的妥协**全删**（一次做完整就不产生）：`--trigger-catalog` 未传 → **fail-closed**（非 WARN 降级）；删 `--allow-legacy` 迁移旁路；删 declared grace。

### 2.3 一个完整内聚交付物（基准②）
- **剥出**：T139（outside_voice_guard 双锚）是**另一个 capability** → 剥出另开完整 change（todolist）；T137（config）非本功能 → 剔。
- **立即 fold**：grill/spec-review 撞到的**相关**发现（M-new + 冷层 15 条 F1–F16）**立即做掉、不 defer**——因为都是同片 hr-tg 一致性的更多确定性维度。
- **管线随 scope**：收窄后自然 ~2 内聚片 → 跌破 tickets 3–6 下限 → 走 superpowers、不再当 tickets 样本。**scope 定管线，非反向凑票绑 scope。**

### 2.4 冷层承重实证（面治 + 冷独立）
5 源冷审（广审+对抗×2+接地+codex）揪出 15 条"机械化还没做完整"，全 fold：
- **F1**（`declared="none"` 应为 `""`）= 热层（我）**引入的 spec bug**，codex 独家抓；
- **F2**（跨消费者重复键：lint 末值胜 vs retro 取首）/ **F3**（M2/M-new「非 import」双份重实现无跨文件一致性兜底）= 热层 grill + 广审**漏的面级问题**，对抗镜/codex 交叉抓。
- 印证：面治不是一次到位的，冷独立层才是"面"级漏洞的真防线（memory `cold-code-review-load-bearing`）。

---

## 3. 对 workflow-map.md 的 delta（本次处理/暴露的结构层过时项）

workflow-map.md 接地自 `mlh-p5-parser-cleanup`（mlh-p4 之前），已在多处过时；本次工作暴露/处理：

| workflow-map 条目 | 过时/变化 | 去向 |
|---|---|---|
| §3.2 hr-tg 锚 = `hit`+`evidence`（2 字段） | drift：应为 `hit`+`declared`+`evidence`（declared canonical） | 本 change F12 fold 补 map §3.2 |
| §4 anchor_lint 输入/检查 | 加必需 `--trigger-catalog` + M1/M2/M4/M-new | F12 fold 补 map §4 行 |
| §4「14 脚本」清单 | 缺 5 个 mlh-p4 后脚本：`hr_tg_intersect` / `outside_voice_guard` / `review_disposition_check` / `lens_metric_emit` / `maintain_scan` | **map 需一次广度刷新**（超本 change scope，另记） |
| §6 两条分发链 | skew 速率不对称风险未展开 | 本 change design Risks（F11）已展开 |

> **注**：map 的广度刷新（补 5 脚本）是**独立的一件事**（基准②：不混做）——不 fold 进 hr-tg change，另记 todo。

---

## 4. 挂起的独立事项（各自另开完整 change，不混）

| 项 | 内容 | 状态 |
|---|---|---|
| **T139** | outside_voice_guard 双 step1 锚一致性 | todolist，另开完整 change |
| **T141** | 把「拆分标准」融入 workflow 三处触发（roadmap / ff-change-spec / 执行发现） | todolist，hr-tg 收尾后单开 |
| **T137** | config `impl-pipeline:tickets` 全局翻键 blast radius | 待用户裁（全局切换 vs 仅 pilot） |
| **map 刷新** | workflow-map.md 补 5 个 mlh-p4 后脚本 + hr-tg schema 回灌 | 建议随下次 map 维护 |

---

*方法层立于 harden-hr-tg-anchor-consistency（grill + 5 源 spec-review）。基准权威源见 CLAUDE.md「设计/分析基准原则」+ 自动记忆 + adr/0019。本文 narrative + 案例，引用不复制。*
