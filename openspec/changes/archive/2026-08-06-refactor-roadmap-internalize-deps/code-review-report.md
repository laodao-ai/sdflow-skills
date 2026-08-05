---
ship-gate:
  code_review: pass
  reviewed_sha: 8761cf433a1d5352d991d2fe7c7680fa5beb791d
---

## code-review 报告 — refactor-roadmap-internalize-deps

### 命中范围

- **栈**：Markdown skill 指令层 + workflow bundle 模板（**非代码栈**）
- **清单**：CR-01~09 base（语义类比迁移）+ 仓内文档化标准（CLAUDE.md 基准 1–5 / DOC-1 / premise-verification）
- 🔴 **领域清单未覆盖**：`code-checklists/domains/` 下只有 `backend.md` / `backend-go.md` / `embedded.md` /
  `embedded-esp32.md` / `embedded-ml307c.md` 五份，**无 Markdown 指令层清单** ⇒ 按 F13 显式降级，
  **MUST NOT 表述为「领域清单通过」**。领域镜报告开头已如实复述该降级声明。
- **diff base**：`f464e9bff970b291a5fe1aa5a983720ba696b5c0`（`git merge-base main HEAD`）
- **trivial_shape**：`NOT_EXEMPT`（`non-doc-markdown:AGENTS.md`）⇒ 照常 fan-out
- **HR-TG∩**：`TG-08, TG-09`（非空 ⇒ 已开领域专属 cross-model voice）

<!-- sdflow:hr-tg v1 hit="TG-08,TG-09" declared="TG-08,TG-09,TG-12,TG-14,TG-18,TG-25" evidence="design.md 分别以〔TG-08 · BASE-06〕标注失败模式表、〔TG-08 · BASE-11〕标注可观测性、〔TG-09 · BASE-19〕标注包与相位状态机——三处均为本 change 的承重设计面" -->

### Step1：scope-drift + 完成度审计

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

🔴 **如实降级声明（MUST NOT 读作原生）**：本步**未经 gstack `/review` 的 Skill 机制原生执行**，
而是由主 session 直接完成其两项实质职责（scope-drift + 计划完成度）。降级原因 = 编排层对本轮
context 预算的取舍，**不是** gstack/review 不可用（该 skill 在本机可用）。锚行按 SKILL 契约标
`mode="simulated"`，**MUST NOT 伪装 native**。

**scope-drift = 零**：24 个生产面改动逐一对照 `tasks.md` §1–§5，全部可追溯到具体任务号。
唯三例外 `openspec/issues/open/{bug/B24,todo/T265,todo/T266}.md` 是本轮评审 defer 的正常产物
（评审台账），非顺手多改。

**完成度**：`tasks.md` §1–§5 点名的文件全部有对应改动；§6 验证项由 Task 5 / Task 6 承担。
未执行的两项均为**依赖后续阶段**的 hand-off，非缺口：`4.5`（合并后在运行 checkout 重跑 `setup.sh`）、
`6.9`（archive 后重扫提升进主 spec 的结果）。

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,history" -->

`host=claude` ⇒ 免探针、恒可用。本轮实派：领域镜 ×1、对抗镜 ×2（合并为 canonical `adversarial`）、
历史镜 ×1，另加两个跨模型 outside-voice 站点。

### outside-voice

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

两站点均 async·harness 分支（后台能力探针过 + 主 session 已确证），内层 `--timeout 900`
（config 的 `outside-voice.async-timeout-seconds` 被注释掉 ⇒ 缺键 ⇒ 回落默认）。终态取自
`{run-dir}/<site>.rc` sidecar（**非** stdout 推断），两站点 rc 均为 `0`。
`host=claude` ∧ `runner=codex` ∧ `reason_code=ok` ⇒ 矩阵判**跨模型**，其 findings 豁免 <80 数值滤、
直通对抗裁决。run-id = `20260805T174223Z-aT1r4i`。

🔴 **context 范围偏离（显式声明，非疏漏）**：SKILL 规定 `site=code-voice` 的 context = 全量
`git diff $DIFF_BASE..HEAD`。本轮实测全量 **886,848 字节**，远超 helper 截断阈值（保头尾各 100KB、
丢中段）——照全量喂会让**核心实现整段丢失**、voice 只读到 impl-reports。故收敛为**生产面 diff**
（全量减 `openspec/changes/` 下的过程件），**191,641 字节**、24 文件，核心 `sdflow-roadmap/SKILL.md`
完整在内。偏离已写进 context 文件头部，voice 知情。

### Findings（置信 ≥80）

| # | 严重度 | 问题 | 证据 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| F1 | **Critical** | 「产出模式」节明写「直接生成路径**可不产出** memo」，而收尾 checklist **无条件** SHALL 把 memo 的 `状态：DRAFT` 改为 `FINAL` ⇒ 该路径走到收尾时指令**无法满足**（agent 只能报错卡住 / 凭空造 memo / 静默跳过） | `SKILL.md:415`（旧行号）vs `SKILL.md:517`（旧行号） | code-voice + hr-tg voice（两站点独立收敛） | ✅ 已修 `[impl-review-fix]` |
| F2 | Important | 相位 B 起手三步第 3 步**无条件**「落盘草稿 memo.md」，而 continue/replan 的既有 memo 承载承重结论 / `## 未决项` / `[确认]` 全局写入记录 ⇒ **覆盖即永久丢失**；且 `FINAL → DRAFT` 的重入转换无条款。**同一未分支表述在模板侧复现**（第二处） | `SKILL.md:344-350` + `references/memo-template.md:8-9` | code-voice + hr-tg voice + **领域镜**（三源收敛，领域镜独家补出模板侧第二处） | ✅ 已修（两处） |
| F3 | Important | `workflow-history.md` A4 把 matt 移除归因为「前提消解：无 wayfinder 调用点」——**正是 SR-33 明确订正掉的因果表述**；ADR 0037 `:26-29` 明文「删它与 roadmap 重构**无因果关系**」 | `workflow-history.md` A4 段 vs `adr/0037-*.md:26-29` | code-voice 独家 | ✅ 已修 |
| F4 | Important | gate-0 五项**全文无通过阈值定义**。spec `:21` 用「gate-0 任一项未通过」隐含全过=过，但 **skill 是独立分发单元、spec 不随 skill 走** ⇒ 只读 SKILL.md 的 agent 无判据；而阈值直接决定走三态路由哪一支（两支交互成本差异巨大） | `SKILL.md:293-303`（旧行号），全文 grep 无阈值陈述 | 对抗镜 A 独家 | ✅ 已修 |
| F5 | Minor | 七维裁剪表只有「技术重构」「新产品/新项目」两行，无兜底行；而 `:309` 自列的「内部工具 / 基础设施 / 博客文档工程」在表里查不到对应行 | `SKILL.md:354-361`（旧行号） | 对抗镜 A 独家 | ✅ 已修（fold，成本极低） |
| F6 | Minor | 直接生成路径（第①态）中途发现关键判据缺失时，**无「回退相位 B」的转换定义**（design 状态机图对该路径只有单向边，SKILL.md 正文同样沉默） | design.md 状态机图 + `SKILL.md` 全文 grep | 对抗镜 A 独家 | ⏸ defer → `T266` |

> **F1 的来源值得记一笔**：它**是本 change 代码审前一阶段（Task 1 双轴审）修 FIX-1 时引入的**——
> 补「收尾置 FINAL」条款时未考虑直接生成路径根本没有 memo。两个**独立的跨模型 voice** 同时撞到它。
> 这是「返工在接缝处引入新洞」的又一实例，也是冷层独立审查不可替代的直接证据。

> **F3 的来源同样值得记**：Task 3 审的是 ADR（论证正确）、Task 4 审的是 bundle（自身格式正确），
> **没有任何一票跨这两个文件比对** ⇒ 逐票双轴审对这类**跨文件一致性**结构性不可见，只有冷层全 diff 抓得到。

### 已裁掉（反静默压制，可审计）

| # | 原始发现 | 来源 | 裁掉理由 |
|---|---|---|---|
| X1 | 「无状态行的旧格式 memo 一律判 DRAFT，破坏已完成存量包兼容性」 | code-voice | **实现符合设计**：spec `:43` 明文「无状态行的旧格式 memo 视为未定稿，按 DRAFT 处置」。这是设计阶段已拍板的语义，非实现自作主张。对该设计本身的异议超出阶段三代码审边界（改它须另开 change 走设计门）。 |
| X2 | 「B 起手建目录成功、memo 写失败的空包失败态无可见条款」 | hr-tg voice | **设计已明确接受**：design.md 失败模式表第 1 行原文「目录建成、草稿 memo 写失败 → 呈现为『已存在的空包』，走 continue/replan 分支 → **接受**（见 decision-memo「接受的边角」）」。voice 要求的「显式条款」正是被判定为不需要的那部分。 |
| X3 | 「直接生成路径 + review 失败后中断 ⇒ 包无人认领」 | code-voice | **与 F1 同根因**（无 memo ⇒ 第零步对该路径失明），而该根因已被 design Risks 显式接受（「完美成本 = 给直接生成路径也强制建 memo，与 D6 轻量意图冲突…如实声明，不称已覆盖」）。**但 voice 指出的表现面比 design 举的例子更宽**（design 只写了「C 相位写到一半中断」，未写「生成完成 + review 失败 + 中断」）⇒ 该更宽表现已并入 F1 修法的说明段落显式记载，供未来重议 D6 时有完整信息。 |
| X4–X7 | 历史镜的 4 条 findings（SR-1「无消费方前提被证伪」/ SR-2「memo 等价性未验证」致命 / SR-4「footage 演练是恒真锚」/ SR-7「6 处保留节残留」+ 结论「不应进 HARD-GATE」） | 历史镜 | **全部把 `spec-review-report.md` 里已修复的历史 findings 当成当前仍存在的问题**。逐条核实：SR-1 已在 ADR 0037 订正（领域镜独立核实断言为真）；SR-2 已处理（`## 未决项` + 承接边界如实声明，`SKILL.md:389` 有条款）；SR-4 已由 Task 5 构造 fixture 解决；SR-7 已由 Task 1 的 1.10 修 + Task 5 的 6.6 逐句核对。另含**事实错误**一处：称「tasks 6.1 词表不含 `footage`」——词表明确含 `footage`（SR-7 正是为此扩的）。「不应进 HARD-GATE」的结论亦不成立：设计门早已通过，本轮是阶段三。<br>**根因**：契约把历史镜定为**弱档「机械」**（读 blame / 读历史），但它实际做了大量**判断**并判错；其机械部分（改写史 2 次、无相关 revert）是准确的。 |
| X8 | 对抗镜 B 全部 | 对抗镜 B | `refuted=true` ——它扎实核实了 `.py` 硬编码断言零命中、`sdflow-init/assets/snippets/` 干净、`adr/0013:25` 的旧行号属合法历史引用，未找到已知三条之外的悬空活引用。**无 finding 是合格结论**，非漏审。 |

> **<80 置信滤除**：本轮无。跨模型 voice 的 7 条按矩阵判 cross-model 直通裁决（豁免数值滤）；
> 同族镜的 8 条均在裁决层处置（采纳 3 / 裁掉 5），无一条因数值置信被滤掉。

### 修复 / defer 台账

- **自动修 5 项** `[impl-review-fix]`（F1–F5），落在 commit `8761cf4`，改 4 文件 +37/−4：
  - `sdflow-roadmap/SKILL.md`：收尾 FINAL 条件化 / 起手三步按 create·continue·replan 分列 / gate-0 阈值 / 裁剪表兜底行
  - `sdflow-roadmap/references/memo-template.md`：使用方法节加 create-only 限定（F2 第二处）
  - `sdflow-init/assets/workflow/workflow-history.md`：A4 改「同批（非同因）移除」+ git log 时序证据 + 指向 ADR
- **自动选 0 项需 strong 复核**：F1–F5 的修法**均有客观判据**（spec 原文 / ADR 原文 / design 已接受声明 /
  同文档内既有先例——如「放弃清理」节早已对 create vs continue·replan 分列，F2 直接沿用该先例）
  ⇒ 按 `T10-choice` 第①档自动选，无需派 strong 对抗镜复核。
- **defer 1 项**：F6 → `openspec/issues/open/todo/T266.md`（显式带 `source_change`）
- **本轮之前已 defer**（双轴审阶段，此处仅登记不重复处置）：`B24`（测试口径受 worktree 污染 + 硬编码阈值 189<200）、`T265`（跨文件行号引用脆弱耦合）

**复审（Step5 第 4 步，硬上限 1 轮）**：已跑，范围限定本轮修复 diff（`HEAD~1..HEAD`），判定
**PASS**。它逐条追了 F1 修法的三条候选反例（走拷问路径的包 / 存量四件套包 / 缺件包）均不成立，
唯一残余是「人手删除已存在的 memo」——非目标态 producer 会产出的形态，且新条款已用「D6 已在设计
阶段权衡并接受」「MUST NOT 表述为已覆盖」显式承认诚实边界，未 overclaim。**未触发第二轮**，
无残差 defer。

### 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="0" defer="1" 独立="2" sev="致0/高1/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="0" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="4" 采纳="0" 裁掉="4" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="4" 采纳="3" 裁掉="1" defer="0" 独立="1" sev="致1/高2/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="0" sev="致1/高1/中0/低0" -->

以上六行由 `lens_metric_emit.py --layer code-review --host claude` 产出（exit 0）后原样落入，**未手拼**。
**残余信任边界（如实声明）**：分类正确性、roster 完备性、findings JSON 誊写准确性仍是主 session 的
信任边界，emitter 只保证「给定输入的确定性归约」。

> **本轮跨模型 voice 的产出占比值得记录**（供 `/sdflow-retro` 的 per-(层,镜) 采纳率+独立率双列复评）：
> 6 条采纳中 **3 条**由跨模型 voice 首报（F1/F2/F3），其中 F1、F3 是**同族镜全漏**的；
> 同族的 domain/adversarial/history/broad 四镜合计独立贡献 2 条（F4、F5，均出自对抗镜 A）。
> 历史镜 findings=4 采纳=0（全部因把已修历史问题当现存问题而裁掉）。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 issues 池：`T266`（本轮）+ `B24` / `T265`（双轴审阶段），hand-off 会引用
- **三项 hand-off 待 `sdflow-done` 承接**：
  1. `tasks.md` 6.2 的 baseline 失败清单应回填第 2 条（`test_subprocess_encoding_contract.py`
     ——实测 merge-base 与 HEAD 两侧同红，属漏记非回归；实现期 MUST NOT 改 `tasks.md`，它在
     `ship_gate` 的 design 域失鲜监视集内）
  2. `tasks.md` 6.9：archive 后对提升进主 spec 的结果重跑词表扫描 + 逐 Requirement 与 SKILL.md 对码
  3. `tasks.md` 4.5：合并后在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` / `/sdflow-upgrade` 还原
