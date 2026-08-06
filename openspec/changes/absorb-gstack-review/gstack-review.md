<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="26" truncated="false" -->

# gstack-review · absorb-gstack-review（Step1 广审 · autoplan 原生执行）

**mode="native" 侧信道佐证**：autoplan 经 Skill 机制原生进主 session 执行；三次真实 `codex exec`
（session id `019fd515-e949…` / `019fd522-4e46…` / `019fd531-1d7a…`，模型 gpt-5.6-terra，read-only
沙箱，token 用量 90,922 / 139,153 / 90,352）+ 三个前台 Claude 子代理（CEO/Eng/DX，sonnet）。
restore point：`~/.gstack/projects/laodao-ai-sdflow-skills/feat-absorb-gstack-review-autoplan-restore-20260806-111158.md`。

- 评审对象：四件套 @ commit 3d28ded（盘面 = 纯 spec 产物，564 行新增，无实现 diff）
- Scope 检测：UI scope = no（Design 相位跳过）；DX scope = yes（AI agent 为首要用户）
- Mode（autoplan override 自动决策）：**SELECTIVE EXPANSION**（feature enhancement 缺省档）
- 相位：CEO → Eng → DX，各相位 Claude 独立子代理 + Codex voice 双声，均真实完成（degradation matrix：无降级）

## Step 0 主 session 分析（CEO 相位）

**0A premise challenge**：三条承重前提——① gstack 依赖真实存在且行为不受控（已由接地镜/CEO 子代理
读码证实：SKILL.md gstack native 执行 + AskUserQuestion 门冲突为真）；② 五类 checklist 缺口真实
（CR-01~09 无 shell 注入/枚举完备性，backend 无 DB 竞态条目，无 llm.md——证实）；③「plan 发现残废 ⇒
Step1 最想要的能力恰是废态」——**此前提未经归档报告回测**（CEO 子代理抽档实测：多数轮 clean、但有两次
真实历史捕获——「残废」结论方向对、幅度未量化）。前提①②站稳，③部分站稳 → 登记设计门。
**0B existing-code leverage**：改动全部落在既有单一源机制上（fold 块 / HR-TG 成员行 / MANDATORY 元组 /
needle），无平行重建；hr_tg_intersect 动态 parse「零代码改动」claim 证实。
**0C dream state**：CURRENT（Step1 外挂第三方、语义漂移）→ THIS PLAN（Step1 自持、意图源锚四件套）→
12-MONTH IDEAL（全链路零第三方运行时依赖 + 数据驱动镜优化）。方向一致；spec-review 侧姊妹依赖仍留（记 todo）。
**0C-bis alternatives**：A =本方案（吸收 + 自持，M 档）；B =最小适配器（仅移除 gstack 调用、不吸收
checklist，S 档）；C = provider-neutral 评审证据协议（Codex CEO 提出，XL 档）。memo D1-D3 已人拍板 A；
B/C 作为张力登记设计门（见 spec-review-report 决策区），不在本层重开。
**0E temporal**：实现期将撞的决策点 = 探针时序归位（HOUR1）、五态落盘格式（HOUR2-3）、skew 探测信号
扩展（HOUR4-5）、dogfood 全局窗口（HOUR6+）——全部已被下方 findings 显式化。

## CEO 11 节（主 session 逐节结论，无发现节附「查了什么」）

1 架构：消费点依赖图与实仓一致（接地镜逐条核过）；探针时序矛盾 → 见 ENG-1。2 错误/rescue：两条
fail-closed 路径（emitter 未知 raw / lint 未知 token）存在但**报错不含修法指引** → 见 DX-1。3 安全：
无新攻击面（Step1 子代理只读 + 四条通则传播已覆盖）；CR-LLM 内容本身是防御资产。4 数据流/交互边缘：
五态词汇 PARTIAL/NOT DONE 判据缺失 + finding 类型枚举漏 CHANGED → DX-4。5 代码质量：`_FANOUT_MIRRORS`
单常量双职拆分陷阱 → ENG-3。6 测试：mode 新枚举无 golden 锁定 + dogfood 跑在旧 checkout 的窗口风险 →
ENG-2/ENG-6。7 性能：每轮 +1 中档 dispatch，memo 三镜已记，无新发现（查：无循环放大点）。8 可观测：
raw 名直接替换抹掉新旧 Step1 可比性 → CEO-3。9 部署/回滚：双向 skew 面只分析了窄向 → DX-1/DX-2；
回滚路径（revert + setup）成立。10 长期轨迹：checklist 吸收无维护策略/来源映射 → CEO-6；可逆性 4/5。
11 设计/UX：SKIPPED（无 UI scope）。

## 双声 findings（全量，进 Step3 合并池）

### CLAUDE SUBAGENT (CEO — strategic independence)

- CEO-C1｜Step1「残废」claim 未回测归档报告（实况 = 多数 clean + 两次真实捕获），价值幅度未量化｜中
- CEO-C2｜五态完成度审计与 sdflow-done verify 门的职责重叠未做成本论证｜中
- CEO-C3｜anchor_lint mirrors 改动需把单一共享常量拆成两个永久不同的集合，design/tasks 未点破｜中
- CEO-C4｜spec-review 侧同源 gstack 依赖 defer 无优先级信号｜低
- CEO-C5｜新 checklist 措辞本身无复评检查点（只有 TG-27 命中率有 Q5）｜低

### CODEX SAYS (CEO — strategy challenge) 〔runner=codex · reason_code=ok〕

- CEO-X1｜「依赖移除」与「未证明的质量升级」混装一个 change；checklist/TG-27/引文纪律无历史漏检/误报数据支撑｜高（战略）
- CEO-X2｜Step1 替代非能力等价：四件套一致性检查 ≠ 广义 PR 审查（奖励「按计划完成」，抓不到计划本身错）｜高
- CEO-X3｜NOT DONE/UNVERIFIABLE 作 informational finding 无后果模型（可被裁掉/defer 吞掉）｜高
- CEO-X4｜自持化 = 显性第三方依赖换成难观测宿主行为依赖（自报锚无机械验证却同等可信入度量）｜中
- CEO-X5｜`gstack-adv→scope-audit→broad` 抹掉新旧审计器可比性；broad 还混 autoplan 与 scope-audit｜高
- CEO-X6｜code-review 去 gstack 但 spec-review/roadmap 仍依赖 = 混合依赖，非独立性；应有仓库级依赖战略｜中
- CEO-X7｜checklist 吸收无维护战略（上游演进、无来源映射/复查节奏 → 静态规则债）｜中
- CEO-X8｜TG-27 按栈切分概念错误：本质是「不可信输入跨信任边界」；XSS 塞 backend 同病｜高
- CEO-X9｜引文纪律会压制依赖链/时序/缺失性问题（无单一触发行的 bug 类）｜高
- CEO-X10｜外部竞争风险未处理（官方 code review 产品化吞没本地 checklist 体系）；建议 provider-neutral
  Review Evidence Protocol + 20-30 归档 change shadow evaluation，P0 只做无 gstack 适配器｜战略建议

### CEO DUAL VOICES — CONSENSUS TABLE

| 维度 | Claude | Codex | Consensus |
|---|---|---|---|
| 1 Premises valid? | 已证实(带校准缺口) | 部分(质量升级前提无证) | DISAGREE |
| 2 Right problem? | 是 | 该拆两件事 | DISAGREE |
| 3 Scope calibration? | 合理 | P0/P1 应按证据分立 | DISAGREE |
| 4 Alternatives explored? | 缺口(姊妹依赖无优先级) | 缺口(provider-neutral 未考虑) | CONFIRMED(不足) |
| 5 Competitive risks? | 提及上游演进 | 完全未处理 | CONFIRMED(未充分处理) |
| 6 6-month trajectory? | 可(缺复评点) | 度量可比性丢失/规则债 | DISAGREE |

**PHASE 1 complete.** Codex 10 concerns · Claude subagent 5 issues · Consensus 2/6 confirmed-concern, 4 disagreements → 设计门。

## Eng 相位（Phase 2 Design 跳过：无 UI scope）

主 session Step0 scope challenge：复杂度检查命中（>8 文件），但 autoplan override 不砍 scope（P2）；
拆分判据（CLAUDE.md 基准 4「一个 change 一个完整阶段结果」）本身支持现 scope——与 CEO-X1 张力登记设计门。

### CLAUDE SUBAGENT (eng — independent review)

- ENG-1｜**HIGH**｜能力探针时序未解决：Step1 dispatch（Step0 后、Step2 前）需要 `subagents=` 值，而探针
  定义在 Step2 内部；anchor_lint 强制每轮恰一条 fanout-capability 锚（anchor_lint.py:732-734）⇒ Step1
  自跑探针=双锚被拦 / 静默重排=违背设计 / 复用=时序倒挂。修法：探针统一挪 Step0（与 tier-resolution 同位），
  tasks.md 补显式任务｜design.md:47-50
- ENG-2｜MEDIUM｜dogfood(6.4) 会打在运行 checkout 旧代码上（实测 ~/.sdflow/workflow 与 skills symlink
  均指运行 checkout）：tasks 未写「先开发 checkout `bash setup.sh` 开全局窗口、测完还原」前置步 ⇒ 假绿风险
- ENG-3｜MEDIUM｜`_FANOUT_MIRRORS`(anchor_lint.py:674) 单常量同时供合法性检查(:694)与 dead-fanout 计数(:765)：
  naive 实现直接加 broad 会污染计数集；tasks 2.2 应点破「需拆两个常量」（golden 2.3 能抓但费一轮返工）
- ENG-4｜LOW｜openspec/workflow/ 仓根残留 lens-metric-contract.md / WORKFLOW-GUIDE.md 孤儿副本（非 pin、
  功能死件），grep 假阳来源；建议清理或显式记为存量债
- ENG-5｜LOW｜TG-27 domain 只有 code-checklists 侧无 spec-checklists 侧（有 frontend 反向先例）；建议
  catalog 行或 design 一句注明 code-review-only
- ENG-6｜LOW｜test_anchor_lint golden 全部硬编码 mode="native"，无 mode="subagent" 用例锁定「lint 不校验
  mode 值」不变量（C1 依赖的事实今天为真但无回归守护）
- （复核通过项：C1/C5 消费点 claim 逐条读码证实；retro 聚合器只吃 canonical lens 不受 raw 名影响；
  outside_voice_guard 真的只作用于 gstack-review.md）

### CODEX SAYS (eng — architecture challenge) 〔runner=codex · reason_code=ok〕

- ENG-X1｜阻塞｜探针顺序自相矛盾（同 ENG-1，独立收敛）+ host=unknown 情形下 Step1 恒跑如何满足未定义
- ENG-X2｜阻塞｜Step1 审 `DIFF_BASE..HEAD` 是自动修复**前**的盘面；Step4 auto-fix 后不再有 scope 审计
  ⇒ 报告锚定修复后 SHA 但 scope-drift 没看过它。修法：final-SHA 复跑或记录初审 SHA + 修复 diff 等价审计
- ENG-X3｜阻塞｜五态审计无可审计落盘物（DONE/CHANGED 无逐项证据表、无 task ID/审计 SHA），且与 verify
  终审关系未钉死（NOT DONE 可能被置信过滤裁掉后仍 pass）
- ENG-X4｜高｜pre-emit 引文纪律误杀缺失/链路/时序类 finding；且措辞疑似波及 Step1 的任务证据。修法：
  「可复核证据包」（允许跨文件路径/缺失对照/命令输出），并明确只约束 Step2
- ENG-X5｜高｜度量不可比（同 CEO-X5）：要么升契约版本保 origin 维度，要么明确宣布放弃跨代比较
- ENG-X6｜高｜质量替代未证明（同 CEO-X1）：建议历史 change 回放基线
- ENG-X7｜高｜TG-27→llm.md 消费规则未写进 SKILL 领域选择段 ⇒ llm.md 可能成孤儿；XSS 例证
  （dangerouslySetInnerHTML/v-html）属前端而注册表无 frontend domain ⇒ 「已吸收」名不副实
- ENG-X8｜重要｜维护/验证不足：应机械断言 scope-audit 可 fold、gstack-adv 被拒、TG-27 真选中 llm.md

### ENG DUAL VOICES — CONSENSUS TABLE

| 维度 | Claude | Codex | Consensus |
|---|---|---|---|
| 1 Architecture sound? | 探针时序 HIGH | 探针时序阻塞 | CONFIRMED(坏) |
| 2 Test coverage? | 缺 mode golden/窗口前置 | 缺 fold/TG-27 断言 | CONFIRMED(不足) |
| 3 Performance? | 无实质 | 无实质 | CONFIRMED(无问题) |
| 4 Security? | 无新面 | 未另立 | CONFIRMED(无新面) |
| 5 Error paths? | fail-closed 存在 | 报错不可操作 | DISAGREE→由 DX 相位裁定 |
| 6 Deployment risk? | dogfood 窗口 | 双向 skew 无握手 | CONFIRMED(欠分析) |

**PHASE 3 complete.** Codex 8 concerns · Claude subagent 6 findings · Consensus 5/6 confirmed(其中 3 项为负向确认), 1 disagreement。

## DX 相位（Phase 3.5）

### CLAUDE SUBAGENT (DX — independent review)

- DX-1｜**CRITICAL**｜mirrors 新 token `broad` × 消费仓未 update 的本地 pin anchor_lint（always-on、
  不受 metrics 门控）⇒ 新 SKILL 全局瞬时生效后，**每个未 update 消费仓的每轮 code-review 在末步
  `mirrors-unknown-token` 硬失败**，整轮 fan-out + voice 成本报废；报错为裸 dict repr 无「跑
  `sdflow-init update`」指引；SKILL.md:204 已有同类 skew 探测先例但本 change 未把新信号
  （fold 块 scope-audit 行 / broad token）加进探测。修法 = tasks 补 2.5：skew 探测追加第三信号 + 同款
  fail-loud 文案（面治，成本低）
- DX-2｜HIGH｜TG-27 措辞例证「锚行 parse」正中本仓自身工具链（anchor_lint/emitter/guard 全是解析 LLM
  自报锚）⇒ 本仓高频假阳、污染 Q5 复评样本。修法：删「锚行 parse」例证或加排除句
  （自报控制面锚 ≠ 外部不可信 LLM 产出）
- DX-3｜MEDIUM-HIGH｜Step1 dispatch 时序与降级判据先后矛盾（同 ENG-1，第三次独立收敛）⇒ 中档模型执行分叉
- DX-4｜MEDIUM｜五态判定纪律只钉三态：PARTIAL/NOT DONE 无判据（碰过文件做一半算哪态？）；finding 类型
  枚举 `SCOPE-CREEP/NOT-DONE/PARTIAL/UNVERIFIABLE` 漏 CHANGED ⇒ 报告结构轮间不一致
- DX-5｜MEDIUM｜docs/workflow-console.html:390-526 多处 gstack 叙述未列入 P2 范围（workflow-map.html 实测
  无 gstack 字样无需改）；正是 rename-string-consumers 跨文件类型旧坑
- DX-6｜LOW｜_FANOUT_MIRRORS 拆分陷阱（同 ENG-3）
- DX-7｜LOW｜README「选用规则」示例块（TG-01/02/03 三行）未要求同步 TG-27 行
- DX-8｜LOW/observation｜docs/workflow-skills/gstack-review.md 去留是显式留白，建议设计门现在拍板省实现期临场判断

### CODEX SAYS (DX — developer experience challenge) 〔runner=codex · reason_code=ok〕

- DX-X1｜Blocker｜新 SKILL × 旧消费仓 bundle 必坏且不可诊断（同 DX-1，独立收敛；emitter 与 lint 双报错
  均无升级指引）
- DX-X2｜Blocker｜旧 SKILL × 新 bundle 同样必坏：旧 SKILL 发 gstack-adv、新 contract 已删映射，且此向
  无任何升级线索；「直接替换不共存」制造双向窗口而无版本握手
- DX-X3｜Blocker｜探针→Step1→判 Step2→汇总 mirrors→写唯一锚的顺序未写死（同 ENG-1/DX-3，第四次收敛）
- DX-X4｜Blocker｜五态审计非可审计产物 + 未绑定最终 reviewed SHA（同 ENG-X2/X3 收敛）
- DX-X5｜Major｜mode 与 finding type 均纯 prose 无 schema（任意拼写可过 lint；emitter 输入 schema 未承接）
- DX-X6｜Major｜raw 名替换抹掉可比性（同 CEO-X5/ENG-X5，第三次收敛）
- DX-X7｜Major｜引文门压非局部 finding，与 CR-11「必须读 diff 外代码」自相矛盾（同 ENG-X4 收敛）
- DX-X8｜Major｜消费仓发现路径缺失：无兼容版本/update 后验/stale 诊断；init.py update 不知全局 SKILL 版本
- DX-X9｜TG-27 未回应 trust-boundary 切分（同 CEO-X8 收敛）

### DX DUAL VOICES — CONSENSUS TABLE

| 维度 | Claude | Codex | Consensus |
|---|---|---|---|
| 1 升级路径安全? | CRITICAL(单向) | Blocker(双向) | CONFIRMED(坏) |
| 2 命名/ID 可猜? | 无冲突 | 无异议 | CONFIRMED(好) |
| 3 报错可操作? | 不及格 | 双工具均无指引 | CONFIRMED(坏) |
| 4 文档完备? | 漏 console.html | 漏消费仓视角 | CONFIRMED(缺口) |
| 5 升级后可发现? | 弱 | 缺失 | CONFIRMED(坏) |
| 6 指令 crisp(中档模型)? | 时序+五态分叉 | 同 + schema 缺失 | CONFIRMED(坏) |

**PHASE 3.5 complete.** Codex 9 concerns · Claude subagent 8 findings · Consensus 6/6 confirmed（4 项为负向确认）。

## Cross-Phase Themes（≥2 相位独立命中 = 高置信信号）

1. **探针/dispatch 时序矛盾**：4 声独立命中（ENG-1 / ENG-X1 / DX-3 / DX-X3）
2. **双向 bundle skew 无探测无指引**：3 声（DX-1 / DX-X1 / DX-X2；ENG-2 相邻）
3. **度量可比性丢失**：3 声（CEO-X5 / ENG-X5 / DX-X6）
4. **引文纪律误杀非局部 finding + 与 CR-11 矛盾**：3 声（CEO-X9 / ENG-X4 / DX-X7）
5. **五态审计落盘物/判据/与 verify 关系不完整**：4 声（CEO-X3 / ENG-X3 / DX-4 / DX-X4-X5）
6. **TG-27 切分与消费规则**：4 声（CEO-X8 / ENG-X7 / DX-2 / DX-X9）
7. **质量替代无实证**：3 声（CEO-C1 / CEO-X1 / ENG-X6）

## Decision Audit Trail（autoplan 自动决策）

| # | Phase | Decision | Classification | Principle | Rationale |
|---|---|---|---|---|---|
| 1 | 0 | UI scope=no / DX scope=yes | Mechanical | — | 无 UI 面；AI agent 为首要用户 |
| 2 | 0 | Mode=SELECTIVE EXPANSION | Mechanical | autoplan override | feature enhancement 缺省 |
| 3 | 1 | 双声均跑（codex ready） | Mechanical | P6 | preflight 绿 |
| 4 | 1 | 前提①② 接受、③ 标注待补证 | Taste→设计门 | P6 | 读码证实 vs 回测缺失 |
| 5 | 1-3.5 | 全部 scope 变更建议（B/C 替代、拆 change）不自动采纳 | User Challenge→设计门 | 主权条款 | memo D1-D3 已人拍板 |
| 6 | 3.5 | gstack-review.md 不改四件套（review-only） | Mechanical | autoplan 铁律 | 改动权归 spec-review Step4 |

**User Challenge 登记（永不自动决）**：Codex CEO/Eng/DX 一致建议「拆 change：P0 仅依赖移除、
P1 质量增强按证据分立（或 provider-neutral 协议 + shadow evaluation）」——与用户已拍板的 memo
D1-D3（吸收方案、直接替换、TG-27 收 HR）方向相反。用户原方向为缺省；此挑战连同后果登记进
spec-review-report 决策区 TENSION 条目，设计门一次拍板。
