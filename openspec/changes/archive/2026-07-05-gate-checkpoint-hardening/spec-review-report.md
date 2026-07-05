## spec-review 报告 — gate-checkpoint-hardening

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG{19,23,25}，均不入 HR-TG 子集{04,06,07,08,09,16,17,26}" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="5" truncated="false" -->

### 命中范围
- 变更性质：workflow bundle 规则/skill/spec delta（gate + checkpoint + 锚 契约硬化），无逻辑代码为主。
- 触发：TG-19（多需求）/ TG-23（ADR-1/ADR-2 两真设计点）/ TG-25（契约文档套件一致性）。HR-TG=none。
- 镜：广审（scope-drift+完成度，simulated）· 领域镜（spec 质量+一致性）· 对抗镜×2（ADR-2 / ADR-1+ADR-3）· 接地镜（9 代码事实）· codex design-voice。
- 合并池：codex 5 + 广审 2 + 领域 7 + 对抗A 4 + 对抗B 5 + 接地 0(全属实) = 去重后 **10 条独立 finding**。

### Findings（按严重度，去重后）

**[致命] SR-1 · ADR-2 熔断触发硬化失效**（对抗A-1/2/3/4 · 领域-F4/F6 · codex-5）
- `HEAD 未移 AND 报告未变 才熔断` → `HEAD 移动` 是 OR 逃逸口。STEP_IN_PROGRESS 重跑 `/sdflow-code-review`（修→commit 循环，几乎必产 commit 但可能仍无锚行）→ HEAD 动了判"有进展"→ **熔断永不触发，T26 要防的无限循环原样复现且更糟**。
- mtime/sha 弱信号（重写同内容/linter touch 即逃逸）；未提交报告无 git sha、内容哈希算法未定义；mtime 跨 checkout 双向不可靠。
- "记 HEAD+mtime 两跨-turn 精确值"比"记一个整数"更易丢，且 `emit()` 不输出 HEAD、判据纯活 SKILL prose 不可 CI 断言——换汤不换药，撞"机械活交脚本"。
- **候选 C（无状态比较 helper）被误否决**：纯比较函数不持久化、快照 in-invocation 作参数传入，不撞 D9（对抗A-3 · 领域-F4 交汇）。
- 置信 高 · 判据来自读码实锤（ship_gate.py:46/243-251/533-535，sdflow-code-review 修复循环设计）

**[高] SR-2 · ADR-1 merge 硬检查：判据留白 + 撞 no-AskUserQuestion + 时序**（领域-F2/F5 · 对抗B-F1/F2 · codex-2）
- "停下问" **撞既有 spec MUST**：Purpose(主spec:4)"阶段三无人类阻塞门连续跑到 merge" + Scenario(主spec:72-74)"全程无 AskUserQuestion"。须定义为 **halt+报告（非交互）**，不得引入阶段三中途 AskUserQuestion（领域-F2）。
- 判据"非-openspec 改动"留白 → 宽则天天误挡逼出 opt-out、窄则漏真风险（对抗B-F1）。
- 时序双路径：tracked dirty 被 commit 步 `git add -u` 先提交掉（codex-2）; untracked 存活到 merge（对抗B-F1）——检查须覆盖 commit 步**之前**(tracked) + merge 前(untracked)，判据须精确（分支生命周期内新产未追踪 + tracked 非-openspec）。对抗B-F2 记录：merge 位时序对(针对 untracked)，问题在判据。
- 置信 高 · 证据 sdflow-done/SKILL.md:221-222/247-248

**[高/中] SR-3 · T37/T38 需 MODIFIED Requirements 块**（广审-1 · 领域-F1 · 对抗B-F4，三镜共识）
- `<当前change>` 在主 spec:517（已归档 Requirement「checkpoint 标签 producer→parser 契约测试」），delta 只有 ADDED、无 MODIFIED → `openspec archive` 只追加不改旧文本，517 行不会被同步；verify 只对 delta 核码会漏判"已完成"。
- 置信 高

**[中] SR-4 · ADR-3 TAG_RE 单源仍留人读串漂移**（对抗B-F3）
- workflow.md:74 仍留完整人读格式串 `<change>:task<N>-<slug>`，贴"非权威"标签≠技术约束；test_producer_parser_contract.py 不比对 workflow.md。TAG_RE 改形状无机制强制同步该行 → spec delta 自己的"MUST NOT 第二份需手工对齐串"被这行违反。
- 置信 中高

**[中] SR-5 · T36 撞既有测试**（codex-3）
- test_workflow_authority.py:23 断言 SKILL 必须含 `<change>:task<N>-<slug>`，与"SKILL 改引用式不复述"冲突；design 没把改测试列进 tasks。

**[中] SR-6 · T43 缺回归测试**（codex-4）
- test_anchor_contract.py 只做子串 `a in text`，坏模板照过；应加逐行 `strip()==anchor` + 无反引号/尾注断言。

**[中] SR-7 · `--help` 缓解引了不存在接口**（codex-1 · 广审-2）
- design:113 "以 checkpoint-commit.sh --help 缓解"，脚本无 --help 分支（dirty 仓跑会真 commit）；且与 proposal Impact"非改"表述不一致。删掉该缓解说法即两全。

**[低] SR-8 · producer 措辞张力**（领域-F3）："producer 铸造" vs "format-agnostic 非源" 表面矛盾，加一句澄清两角色维度。
**[低] SR-9 · 两锚族塞一条 Requirement**（领域-F7）：delta Req1 混 checkpoint 标签 + ship-gate 锚，考虑拆或分段标注。
**[低] SR-10 · code-review 双锚语义尾注不可合并**（对抗B-F5）：pass/blocked 各自尾注语义不同，实现期勿照 verify 合并成共享脚注，各锚配各注。

### 已裁掉 / 抗住（反静默压制，可审计）
- 对抗B-F2：软/硬两层**时序**（merge 前查 untracked）**抗住**——verify 读活工作区能看见 dirty，风险在"看见 ≠ 带进 base"，merge 位卡在该缺口，时序设计对；问题归 SR-2 判据。
- ADR-4 锚族 B 修复本身**抗住**（对抗B-F5 仅实现期措辞细节，归 SR-10）。
- 接地镜 9 条代码事实**全属实**（含 T37/T38 前提成立：主 spec 真含 `<当前change>` 行517 + prose 复述标签形状 372-393），无虚构前提被裁。

### 决策登记区
```
┌────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  ADR-2 重做：熔断判据 HEAD/mtime → 该步锚行集合变化    │  设计门裁
│              (复用 _line_scoped_hits) + 复议候选 C(无状态 helper) │
│ [需拍板] Q2  ADR-1 机制定死：停下问=halt+报告(非 AskUserQuestion) │  设计门裁
│              + 判据精确化(分支内新产 untracked + tracked 非-osp)  │
│              + 检查覆盖 commit 步之前(tracked)+merge 前(untracked)│
│ [自动决策] D1 SR-3 补 ## MODIFIED Requirements 块 + tasks 显式改  │  amendment 已应用
│              spec:517 + verify 锚列该行                            │
│ [自动决策] D2 SR-4 加机械钩子(TAG_RE 旁 checklist / 弱校验 wf.md) │  amendment 入 tasks
│ [自动决策] D3 SR-5 tasks 加更新 test_workflow_authority.py       │  amendment 入 tasks
│ [自动决策] D4 SR-6 tasks 加 T43 逐行 strip()==anchor 回归测试     │  amendment 入 tasks
│ [自动决策] D5 SR-7 删 design --help 缓解说法 + Impact 对齐         │  amendment 已应用
│ [自动决策] D6 SR-8/9/10 措辞澄清/分段/双注(低,实现期带)            │  记录,实现期处理
└────────────────────────────────────────────────────────────────┘
```

### 结论
- **不建议直接进设计 HARD-GATE**——SR-1（致命）+ SR-2（高）是两个真设计点的实质缺陷，需用户就 Q1/Q2 拍板后才算设计收敛。
- 自动决策 D1-D5 已作 `[spec-review-amendment]` 落 design/specs/tasks/proposal；D6 记录留实现期。
- 收敛口：请用户裁 Q1（ADR-2 重做方向）+ Q2（ADR-1 机制），拍板后写 design-approved 锚，方可进阶段三。

### 设计门拍板记录
- 2026-07-05 用户拍板：Q1 = 锚行集合判据 + 无状态 helper；Q2 = merge 缩简版（只 untracked + halt+报告）。全部 amendment 已落 design/specs/tasks/proposal，validate 通过。批准进阶段三。

<!-- ship-gate: design-approved -->
