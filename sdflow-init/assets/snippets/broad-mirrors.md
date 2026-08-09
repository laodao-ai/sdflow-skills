<!-- sdflow:broad-mirror-def:start —— 真相源 sdflow-init/assets/snippets/broad-mirrors.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
**广审镜（strategy / plan-eng）— base R 项自持双镜，恒跑、不受 TG 命中门控**

评审对象路径由调用方 SKILL 各自声明（例：spec-review 场景 = `{change_dir}` 下 proposal/design/specs/tasks
四件套；roadmap 场景 = `design.md` + `roadmap.md` + `task-log.md` 三件套整体 plan）——本区块只定义两镜
各自的**职责范围**与**prompt 契约**，评审对象由各自调用方 SKILL 在紧邻本区块处补一句声明，不在此重复。

| 镜 | 数量 | R 项范围（`spec-checklists/spec-quality-base.md`） | 建议档位 |
|----|------|------|-----------|
| **strategy 镜** | 1 | 计划级：BASE-01/08/09/10/12/13/14/18/22/26/27/30（完整性/外部一致性/清晰度/范围-YAGNI/ADR 三镜决策/不在范围内声明/显式假设列表/分解检查-fold-vs-defer/需求无实现细节混入/外部服务成本估算/时序可执行性/正文即最终态）+ **默认规则：未列明的既有或未来新增 base R 项归本镜** | 中档（判断） |
| **plan-eng 镜** | 1 | 工程级：BASE-05/06/16/17/19/25/28（可行性/错误处理完备性/NFR 数字化/需求可追踪性-全链/图表完备性/组件清单/安全与数据保护） | 中档（判断） |

> 两镜划分实现/复评时须以 `spec-checklists/spec-quality-base.md` 当时的 R 项全集核对一次划分完整性——
> 新增 base R 项若未来被显式列入某一镜，以列入为准；未列入前一律按默认规则落 strategy 镜。

**两镜各自 prompt 契约（MUST 含，不 AskUserQuestion）**：

1. 评审对象路径（调用方 SKILL 在本区块外声明的具体路径/文件集）。
2. **四条通则原文整段复制**（`sdflow:principles` 从 start 到 end，不转述、不摘要——见各 SKILL 传播纪律）。
3. 本镜职责清单（上表对应行的 R 项范围）。
4. 返回结构化 findings 列表（每条：问题 / 证据 file:line / 置信度(高/中/低) / 严重度 / 建议）。
5. 不 AskUserQuestion。

**plan-eng 镜防重叠语义补句（MUST 含）**：文件归属线（base 归广审镜、domains/ 归领域镜）不足以消解话题层
残余重叠——plan-eng 镜 prompt MUST 另含一句「栈特定错误处理/重试熔断（domains 的 BE-04/BE-08 类条目）由
领域镜负责，本镜只审跨领域/架构级错误路径」。
<!-- sdflow:broad-mirror-def:end -->
