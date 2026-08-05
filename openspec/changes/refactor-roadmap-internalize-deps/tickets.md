---
impl-pipeline: tickets
---

## Global Constraints

> 以下为 `design.md` 的 MUST / MUST NOT / SHALL 类硬约束与 Compliance 条款**逐字摘录**（非转述），
> 作为每个 implementer / reviewer 子代理的共享注意力透镜。

**约束（design.md · Context）：**

> SKILL.md 重写 MUST 保留 `sdflow:principles` 托管块原样（`sync_principles.py --check`
> 是 setup.sh 门禁）；「考古层」在 DOC-1 语境另有语义，改名仅限 roadmap 语境（C5）；
> bundle 文件改动受 dev checkout 纪律约束（改后重跑 setup.sh，经 `sdflow-init update` 推下游）。

**Goals（design.md · Goals / Non-Goals）：**

> - 所有被删机制在 spec delta 中成对处理（删机制 = 删/改对应 Requirement + Scenario），
>   不留悬空 SHALL。
> - 存量兼容零告警刷屏：requirements.md 兼容模式与 footage 冻结共用同一条款结构（至多一行提示）。

**Non-Goals（design.md · Goals / Non-Goals，proposal Non-Goals 之外）：**

> - 不为 memo 设计机械核验门（D4 已拍板轻量化，无 hash/schema 断言脚本）。
> - 不设计存量 footage → memo 的自动转录工具（冻结即可，手工转录是重入时的例外路径）。

**分叉表第 2 行（design.md · 与 sdflow-spec 的实际分叉表）：**

> | 2 | memo 机械层 | frontmatter + `decision_hash`（身份 + 状态双职责） | 仅 `状态：DRAFT/FINAL` 一行状态位，无身份核验 | ✅ 有意（D4），**但状态位不可再砍**（SR-2） |

**诚实边界（design.md · 可观测性）：**

> **诚实边界**：以上三者**全部由执行 agent 自己写**，无任何机械捕获路径（本 skill 无脚本）。
> ⇒ 「判定有没有真做」在事后不可机械核验，只能靠留痕行是否在场做弱推断。这是**合法的残余划分**，
> MUST NOT 被表述为「有可观测性保证」。

**scope-check 表引言（design.md · 契约文档套件 scope-check 表）：**

> BASE-29 强调：**未列入**（清单里根本没有该文件）比**未完成**更危险——下次升级仍不会被想起。
> 故本表枚举**全套**，包括不改的，且不改必须给理由。

**Risks / Trade-offs（design.md，逐条）：**

> - **[同串双语义误替换]**「考古层」（DOC-1 语境）被连带改名 → 改名操作按 C5 范围限定逐文件做，
>   完成后 grep `考古层` 核对：`openspec/rules/`、BASE-30、T169、CLAUDE.md:183-184 必须原样。
> - **[SKILL.md 重写破坏托管块]** principles 区块被动 → 重写以「区块外全重写、区块内零字节不动」
>   执行，收尾跑 `python3 hack/sync_principles.py --check`（setup.sh 门禁同款）。
> - **[bundle 窗口期]** assets/workflow 改动后未重跑 setup.sh ⇒ 全局 canonical 陈旧 →
>   实施任务显式含「dev checkout 跑 `bash setup.sh`」步骤（CLAUDE.md 纪律）。
> - **[存量包续跑回归]** 冻结条款写漏某接触点（如 checklist ③ 未覆盖 footage/）→ 以
>   `issues-triage-2026-08` 包做一次续跑演练（Success Metrics 第 5 条）。
> - **[直接生成路径的半成品无人认领]** gate-0 过 ∧ 无商业化信号的路径允许 memo 不存在，而重入探测
>   只扫未定稿 memo ⇒ C 相位写到一半中断留下的残包不被任何机制发现（见失败模式表）。
>   **接受**：概率低（C 相位是连续写盘、无人类往返）、影响可逆（残包可见、可手删）、
>   完美成本 = 给直接生成路径也强制建 memo（与 D6「直接生成」的轻量意图冲突）。如实声明，不称已覆盖。
> - **[七维 B 相位的摩擦增量未量化〔SR-40〕]** 新增七维拷问对「gate-0 未过」的请求是净增交互轮次，
>   四件套未给出任何量化或体感评估。**接受**：目标态本就要求把 office-hours 的验证能力内化，
>   摩擦是该能力的成本而非缺陷；但收尾时应回看一次实际轮次，若显著超预期则调裁剪基准。
> - **[术语改名遗漏]** 「野心/结晶」残留 → 收尾 grep 不带 `--include` 全量扫（含 .py/.sh/.yml），
>   历史文档（docs/、archive/）白名单排除。

**Compliance（design.md · Compliance）：**

> - 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文正文只写目标态，演进过程在
>   decision-memo（本 change 的过程件）。
> - 遵守 `openspec/rules/premise-verification.md`：承重断言均有 C1–C10 证据锚。
> - 遵守 CLAUDE.md 设计基准 1–5：无新增机械门（基准 1 的残余划分——收尾 checklist ① 的
>   既有脚本门不动）；目标态导向（C6 三态路由不照 handoff 缩水）；无手搓解析器。
> - 无豁免项。

**R-ID 词表**（本 change delta spec 的 Requirement 缩写）：

| 缩写 | Requirement（`specs/roadmap-planning/spec.md`） |
|---|---|
| A1 | ADDED · 讨论层三态路由 |
| A2 | ADDED · B 相位拷问与增量落盘 |
| A3 | ADDED · 历史存档引用边界与存量 footage 冻结 |
| A4 | ADDED · review 按商业化信号分档 |
| M1 | MODIFIED · 三件套直写产出 |
| M2 | MODIFIED · 收尾 checklist 软门 |
| M3 | MODIFIED · roadmap.md 近细远雾分层 |
| R1 | REMOVED · 讨论层按规模分档路由 |
| R2 | REMOVED · footage 落盘位置与引用边界 |
| R3 | REMOVED · review 按项目野心分档 |

**本 change 的通用执行纪律**（每票适用）：

- 逐条实施依据在 `tasks.md`（任务号见各票验收标准），需求依据在
  `specs/roadmap-planning/spec.md`，决策全文在 `decision-memo.md`（D1–D14 / C1–C10）。
  **这三份是设计阶段已定稿的工件，实现期不是它们的作者**——发现设计有问题走 `NEEDS_CONTEXT` /
  `BLOCKED` 上抛编排层。
- 本 change **不改任何 `.py`**（`tasks.md` 测试覆盖图已声明）；若某票的实施必须改 Python，
  先 `NEEDS_CONTEXT` 上抛，不自行扩范围。
- 本仓测试入口 = `/usr/bin/python3 -m pytest`（裸 `pytest` 命令不存在、默认 `python3` 未装 pytest）。

### Task 1: sdflow-roadmap 讨论层三相位重写

**Blocked-by:** none
**R-ID:** A1, A2, A3, A4, M1, M2, M3, R1, R2, R3

操作者调用 `/sdflow-roadmap` 后所经历的流程，从「三分支路由（explore / wayfinder 长档 /
office-hours 前置验证）」变为一条线性的三相位协议：**第零步重入探测 → 相位 A（澄清 + gate-0 +
商业化信号检查 → 三态路由）→ 相位 B（起手三步 / 七维拷问与裁剪 / 术语·ADR 提议制 / 增量落盘 /
停止条件 / 放弃清理）→ 相位 C（三件套直写）→ review 分档 → 收尾 checklist 四项**。

行为上可观察的结果：

- wayfinder 长档路径与 office-hours 前置验证分支在指令中**不再存在**；其验证能力被七维拷问吸收，
  其跨会话铺图能力被 memo 增量落盘 + 未决项小节承接（承接边界如实写明：只承接 frontier 的**清单**
  职能，**不承接** `Blocked-by` 依赖图与 `claimed` 并发语义）。
- footage 落盘、map 再入、tracker preflight、基线记录不再是产出路径；「footage」在本 skill 语境下
  改称「历史存档」，存量 footage 包续跑时至多得到一行冻结提示。
- 三个判定点（路由 / review 分档 / 收尾）各有显式留痕陈述行。
- `sdflow:principles` 托管块**零字节未动**。

依据：`tasks.md` §1（1.1–1.11）逐条 + §6.6「保留」节逐句核对。**1.2（第零步：重入探测）MUST 先于
1.3 / 1.4 完成**，且必须是**独立 `##` 标题、物理位置在相位 A 之前**——SR-36 要防的失效模式正是
「埋在长节子项里被线性执行的 agent 跳过」。

- [x] 第零步节以独立 `##` 标题存在且物理位置在相位 A 之前（1.2）
- [x] frontmatter description 去 wayfinder/footage 且保留「先 `/sdflow-architecture`」指路句（1.1）
- [x] 三相位总览 + 三态路由节写就，入口含第零步分支、判定点①留痕含本次选入维度子集（1.3）
- [x] 相位 B 节写就：起手三步 / 七维裁剪表（词表内联）/ 提议制（`[提议]`·`[确认]` 前缀 + 目标路径 + 条目名 + 版本锚）/ 增量落盘 / 停止条件三态 / 重入协议 / 放弃清理分 create 与 continue·replan 两路（1.4）
- [x] memo `## 未决项` 小节的条款写就：含再触发条件、随包长期存在、承接边界如实声明（1.4 🔴）
- [x] 相位 C 生成节写就：三件套直写、「结晶」→「生成」全文改、生命周期判定时点前移、近细远雾术语改（1.5）
- [x] 历史存档节写就：定义、规则 3 改写、存量 footage 冻结一行提示、陷阱 3 改写（1.6）
- [x] review 分档节（含 `未审待恢复` 阻塞收尾）+ 收尾 checklist 四项（③ 覆盖历史存档、④ 版本锚对账 + 未决项闭环 + 诚实边界）+ 判定点②③留痕（1.7）
- [x] wayfinder 全部机械已删：三分支路由节 / footage 节 / map 再入 / tracker preflight / 基线记录 / 原 checklist ④ / 陷阱 7；路由对照表重写为三态版（1.8）
- [x] `sdflow:principles` 托管块零字节未动，`python3 hack/sync_principles.py --check` 退出码 0（1.9）
- [x] 「保留」节内嵌的 7 处待删机制逐处处置完毕（1.10 的 7 个子弹逐条）
- [x] 「实战案例：博客 v2 重建」显式处置（留或删都在实现记录里写一句），连同规则 1 与陷阱 4 里指向它的括注旁证（1.11）
- [x] 「保留」节逐句核对完成：命名规范 / 下游阶段实施 / 参考模板 / 硬性规则 1·5 / 常见陷阱 1 / CLAUDE.md 配合，无指向已删机制的残留引用（6.6）

### Task 2: references 模板对齐新相位协议

**Blocked-by:** none
**R-ID:** A2, M3

`sdflow-roadmap` 的参考模板与新相位协议一致：memo 模板成为相位 B 纪要的载体（而非可选补充），
三件套模板的术语与新词表一致，长流程范式文档中的 wayfinder 段落降为历史注记。

行为上可观察的结果：按模板起草的 memo 自带 `状态：DRAFT / FINAL` 一行状态位（第零步重入探测唯一
可读的判据）、承重结论 / 拍板决策 / `## 未决项` / 全局写入记录四类小节；三件套模板中不再出现
「产品/商业野心信号」「结晶」「考古层」等旧术语。

依据：`tasks.md` §2（2.1–2.3）。

🔴 `状态：DRAFT / FINAL` 行现已存在于模板中，**MUST 保留**——它是「定稿标记」判据的唯一实现载体
（SR-2），删掉即让第零步重入探测失去全部判据。

- [x] memo 模板含包名 + 日期 + `状态：DRAFT / FINAL` 一行状态位（保留既有行，不新造格式）（2.1）
- [x] memo 模板正文小节 = 承重结论 / 拍板决策 / `## 未决项`（附再触发条件）/ `[提议]`·`[确认]` 全局写入记录（含目标路径 + 条目名 + 版本锚）（2.1）
- [x] memo 模板含历史存档定位声明（2.1）
- [x] design / roadmap / task-log 三模板术语改到位（商业化信号 ×2、生成、历史存档），结构未动（2.2）
- [x] `long-flow-skill-paradigm.md` 的 wayfinder / footage 段落已改为历史注记（2.3）

### Task 3: matt 套件移除与治理面收口

**Blocked-by:** none
**R-ID:** none（治理类，无对应 spec 行为）

`openspec/matt/` 套件及其在项目指令文件中的三个托管区块从本仓消失；本次决策与术语变更在治理面
（ADR / CONTEXT 词条 / INDEX 摘要 / 外部依赖清单 / 活文档 / issue 池）留下一致的记录。

行为上可观察的结果：新 session 读 `CLAUDE.md` / `AGENTS.md` 时不再看到 Issue tracker / Triage
labels / Domain docs 三节，也不再被指向 `openspec/matt/`；查 `openspec/CONTEXT.md` 能查到「历史存档」
与「商业化信号」词条；`docs/external-dependencies.md` 不再声明对 wayfinder / grilling /
domain-modeling 的依赖。

依据：`tasks.md` §3（3.1–3.2）+ §5（5.1–5.7）。

🔴 ADR 的论证 **MUST 按订正后的 D2 写**（历史遗留死配置、独立可删、与本 change 无因果，同批做是
fold 判据），**MUST NOT** 沿用「因本次改动才孤立」的旧因果〔SR-1 / SR-33〕；权衡要写两条（内化
分界线 + 能力承接边界）。
🔴 T134 关闭用 **`WONTDO` + `--reason`**——`OBSOLETE` 不是合法状态码；且须用**本仓**
`sdflow-issues/scripts/`，勿用全局 symlink 旧版（旧 writer 撞号）。

- [x] `openspec/matt/` 整目录（4 文件）已删除（3.1）
- [x] `CLAUDE.md` 与 `AGENTS.md` 的 matt 三区块已删、roadmaps 目录描述行去 footage 措辞，两文件同步（3.2）
- [x] 新增 ADR `0037-`（4 位零填充 + kebab-case，小节结构从现有 ADR 归纳），含两条权衡，matt 论证按订正后 D2（5.1）
- [x] `openspec/CONTEXT.md` 三处词条到位：历史存档（含「结晶」→「生成」）/ 新增商业化信号 / ticket 词条改历史存档语境（5.2）
- [x] T134 已关 `WONTDO` 且带 `--reason`，用本仓脚本执行（5.3）
- [x] `docs/external-dependencies.md` 删 §5 且同步 §8 依赖图，gstack review 节保留（5.4）
- [x] `openspec/INDEX.md:52` roadmap-planning 摘要行整句重写为新结构（三态路由 / 历史存档 / checklist 四项）（5.5）
- [x] `docs/sdflow-fable5/02-module-reference.md` §4.6 已按新结构更新（5.6）
- [x] `docs/drafts/roadmap-refactor-handoff.md` 已删除（5.7）

### Task 4: workflow bundle 同步与安装链路生效

**Blocked-by:** 1, 2, 3
**R-ID:** R2

工作流规则 bundle 与本次讨论层重构对齐：`wayfinder-resolved:` 前缀规则保留但标为 legacy（消费仓
存量 footage 仍可能被溯源）、演进史留下一条移除记录、消费仓 config 生成模版中指向已不存在章节的
陈旧引用被订正；改动经安装链路生效到全局 canonical。

行为上可观察的结果：新下游仓由 `sdflow-init` 生成的 `config.yaml` 不再引用不存在的
「wayfinder→ff 衔接契约」章节；本机 `~/.sdflow/workflow/` 解析到的规则即改动后版本。

依据：`tasks.md` §4（4.1–4.5）。

🔴 **本票在主工作树串行执行**（`Blocked-by` 覆盖全部并行票 ⇒ `next_ready` 只返回它一个）——
`setup.sh` 建的是**绝对路径 symlink**，在临时 worktree 中执行会把全局 skill 链接指向随后即被删除的
路径。若发现自己不在主工作树，`BLOCKED` 上抛，MUST NOT 就地跑 `setup.sh`。
🔴 4.4 的**验收动作 = 单独跑 `python3 hack/sync_principles.py --check` 看 exit code**——`setup.sh`
里那一处是 `if ! …; then echo "⚠️…"; fi`，**不是 fail-closed 门**，警告会淹没在大段输出里。
🔴 4.5 是**合并后**才能执行的 hand-off 项（运行 checkout `~/.skills/sdflow-skills` 重跑 `setup.sh`
/ `/sdflow-upgrade`）——本票**不执行**它，只在实现记录中写明它待 hand-off 承接。

- [ ] `ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀规则保留且加 legacy 标注（4.1）
- [ ] `workflow-history.md` 追加一条 wayfinder 路径移除记录（4.2）
- [ ] `config.template.yaml` 的 `:41` / `:51` 两行陈旧章节引用已订正（4.3）
- [ ] dev checkout 跑过 `bash setup.sh`，且**单独**跑 `python3 hack/sync_principles.py --check` 退出码为 0（4.4）
- [ ] 4.5（合并后运行 checkout 还原）已在实现记录中写明为 hand-off 项，未在本票执行（4.5）

### Task 5: 残留扫描与存量包兼容演练

**Blocked-by:** 1, 2, 3, 4
**R-ID:** A3, M1, M2

被删机制与被改术语在全仓不留残留引用；存量 roadmap 包（含带 footage 的、以及缺件的单文件包）在新
协议下续跑不报错、不被迁移、不阻塞收尾。

行为上可观察的结果：拿一个带 `footage/map.md` 与一张 `open` 状态票的存量包走续跑 / 重入 / 收尾三条
路径，得到的是「至多一行冻结提示」而非报错或迁移动作；拿真实的单文件包
`issues-triage-2026-08/` 走 continue 判定，收尾 ② 对缺失文件判「不适用」而非「不通过」。

依据：`tasks.md` §6 的 6.1 / 6.4 / 6.5 / 6.8。

🔴 6.1 **不是机械 pass/fail**——全量 grep（**不带 `--include`**）实测全仓命中约 103 个文件，
命中需按 `tasks.md` 6.1 的**规则化白名单**（① 考古层 DOC-1/BASE-30 语境 ② `wayfinder-resolved:`
前缀规则 ③ `openspec/issues/` 历史决策 ④ 存量活跃 roadmap 包 ⑤ `.claude/settings.local.json`
⑥ archive/本 change 目录/演进史 ⑦ `docs/` 不再整体白名单）逐条人工过滤。
🔴 6.4 的演练对象 **MUST 是构造出来的 fixture**——全仓实测无任何 `footage/` 目录，直接拿存量包演练
是恒真锚，证不到任何冻结分支。演练后删除临时包。
🔴 6.8 是**逐格核对**，MUST NOT 以「读起来没问题」代替；任一格在 SKILL.md 里找不到明确答案 = 该格
未覆盖，须补写后再收尾。

- [ ] 全量 grep 残留扫描（不带 `--include`，词表见 6.1）跑过，命中逐条过滤，非白名单残留为零（6.1）
- [ ] 构造 footage fixture 包，跑续跑 / 重入 / 收尾三条路径：不报错、不迁移文件、不新增票、未决票不阻塞收尾、至多一行冻结提示；演练后临时包已删除（6.4）
- [ ] 真实单文件包 `issues-triage-2026-08/` 走 continue 判定：不报错、收尾 ② 对缺失文件判「不适用」（6.5）
- [ ] 终审场景核对清单 6×3 逐格核对完成，每格在新 SKILL.md 中有明确答案（6.8）

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1, 2, 3, 4, 5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的聚合测试套件（单元 + 集成 + e2e）并收集证据，证据落
`impl-reports/task6-<slug>.md`，每层一行 `<层> | <命令原文> | <退出码> | <SHA>`；未覆盖层写
`<层> | — | 未覆盖 | <判定依据>`。

契约与已知边界：

- `openspec/config.yaml` **无 `test-suites` 键**（实测），命令来源走优先级 ②：依仓内既有约定判定，
  并在报告里写明命令原文与判定依据。本仓 `CLAUDE.md` 与实测结论：单元层 =
  `/usr/bin/python3 -m pytest`（裸 `pytest` 不存在、默认 `python3` 未装 pytest）。
  某层仓内确无 ⇒ 记「未覆盖（本仓无此层）」+ 判定依据，**MUST NOT fail-closed 罢工**。
- 🔴 **pytest 判据是「相对 merge-base 无新增失败」，不是「全仓绿」**〔SR-18〕。当前 baseline
  **已有 1 个先于本分支存在的失败**——
  `hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`
  （断言 `SA-14` 存在于 `openspec/specs/spec-authoring/spec.md`，实测 grep 0 命中），与本 change
  无关，**不在本 change 修复范围**（要修另开 change）。全仓 2461 用例、本机 >280s，需后台跑或加长
  timeout。
- 本票**豁免 red-before-green**（不写产品代码，验收物是证据不是 diff）；主证据锚 = 本票
  impl-report 文件 + 其内 SHA 三元组，**不依赖本票产生 commit**。
- 判「通过」的证据行 MUST 锚**同一个最终 SHA**（最后一次修复之后的 `git rev-parse HEAD`）。
- 触发回归时的产品代码修复由编排层回派到对应功能票范围，本票只重跑套件收集证据。
- 🔴 `tasks.md` 6.9（archive 后对提升进主 spec 的结果重扫词表 + 逐 Requirement 与 SKILL.md 对码）
  依赖 archive 步，**本票不执行**——在报告中写明它由 `sdflow-done` 的 archive 步承接。

- [ ] 单元测试证据齐全，判据为「相对 merge-base 无新增失败」并附 baseline 已知失败的复核结论
- [ ] 集成测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖（本仓无此层）」+ 判定依据）
- [ ] `python3 hack/sync_principles.py --check` 单独跑，退出码 0（6.3）
- [ ] `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过（6.7）
- [ ] 所有判「通过」的证据行锚同一个最终 SHA
- [ ] 6.9 与 4.5 两项 hand-off 承接已在报告中写明
