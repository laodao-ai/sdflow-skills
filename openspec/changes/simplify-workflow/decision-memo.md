---
schema_version: "1.0"
change: simplify-workflow
branch: feat/simplify-workflow
generated_at: "2026-08-05T16:00:00+08:00"
decision_hash: "866dc3335cf0"
---

## 目标态

合并 sdflow 工作流双轨为唯一线性路径（explore→sdflow-spec→clear→spec-review→HARD-GATE→clear→sdflow-ship），删除旧入口/wayfinder/embedded-test-sop，解除 sdflow-spec 手动触发限制，impl-pipeline 缺省翻为 tickets。

## 承重约束

### C1: 解除 sdflow-spec 手动限制不削弱拷问质量

- **约束**：`disable-model-invocation` 只控制触发方式，不控制拷问过程。相位 B 的人机对话协议（一次一问、承重约束逐条站稳、停止信号需证据锚）不因触发方式改变而改变。人仍在拷问中做决策。
- **证据锚**：sdflow-spec/SKILL.md 相位 B 协议（B.1~B.8）不受 frontmatter `disable-model-invocation` 影响；HARD-GATE 是真正的人类门。
- **边界**：解除的是「是否开 change」的触发权，不是「拷问可省」的豁免。

### C2: 旧三步删除后无覆盖真空

- **约束**：旧三步的三种例外情形（wayfinder 跨会话 / 用户要分步 / 环境不可用）在新流程中均有覆盖：wayfinder 已决策删除，跨会话由 explore 承载；分步需求由 sdflow-spec 三相位内建；Codex 宿主 sdflow-spec 已支持。
- **证据锚**：sdflow-spec/SKILL.md §0.2 已处理 `SDFLOW_HOST=codex`；opsx:explore 无 `disable-model-invocation` 限制，可跨 session 反复进入。
- **边界**：旧入口（opsx:ff、grill-with-docs、opsx:explore）作为 skill 不删除（两个是 CLI 生成物，一个在仓外），只从 workflow 流程文档中移除。

## 拍板决策

### D1: impl-pipeline 缺省翻转，下游默默跟随

- **决策**：`impl-pipeline` 缺省从 superpowers 翻为 tickets。15 个无显式键的下游项目静默翻转，不做迁移兜底。
- **依据**：15 个受影响项目无在途 change；tickets 管线是 superpowers 的超集（更结构化），不存在功能退化；已有 3 个项目显式 `impl-pipeline: tickets` 不受影响。
- **风险**：可接受。真正跑阶段三时如需旧管线，显式加 `impl-pipeline: superpowers` 即可。

### D2: 删除 sunset 条件，回退靠 git revert

- **决策**：CLAUDE.md 的「旧入口 sunset 条件」段落整段删除。不再有「观察窗 → 三档阈值 → 达标/不达标」的回退路径。
- **依据**：新流程是直接合并（不经 sunset 观察窗）。回退方式 = `git revert` 本 change + 重跑 `setup.sh`——workflow bundle 是 git 管理的，原子可回退，比 sunset 条件更简单更可靠。

### D3: embedded-test-sop 彻底删除（skill + gate 逻辑 + 流程引用）

- **决策**：删除 `embedded-test-sop/` skill 目录 + ship_gate.py 的 RUN_SOP verdict/tg02_hit 检测（17 处）+ 相关测试（21 处）+ workflow bundle 引用 + prompts/step5_5。不保留为手动 fallback。
- **依据**：用户明确要求彻底删除。嵌入式项目需要时可自行建立测试 SOP，不需要 workflow 自动化触发。

### D4: workflow.md G1 分析保留进附录，正文简化为一条规则

- **决策**：G1（/clear 纪律）的详细分析（为什么阶段内部不用、为什么交界处用、各处理由）移入 workflow.md 附录。正文精简为：「阶段内部不用 /clear（评审独立性由 fresh 子代理提供）。两处阶段交界 SHALL /clear：阶段一→二（cache 隔离 + 产/审错档）、阶段二→三（盘面纪律 + 产物自足性 + 去作者偏置）。」
- **依据**：DOC-1（正文即最终态，演进史/分析进附录）。简化后分支 A/B 不再共存，辩护性文字的前提已不存在，但分析本身作为设计推导仍有参考价值。

### D5: explore → sdflow-spec 自动衔接：人示意即触发

- **决策**：explore 中人示意收敛（如"开搞"、"做吧"、"开 change"）→ 模型自动 invoke `/sdflow-spec`。不需要精确的斜杠命令，自然语言信号即可。模型不自主判断「该开 change 了」。
- **实现**：① 机械层 = 删 `sdflow-spec/SKILL.md` 的 `disable-model-invocation: true`；② 规则层 = workflow 文档 + `claude-section.md` 写明触发条件。
- **诚实边界**：规则层是指令约束，非机械门（模型自报遵守，无脚本可验）。与现有 workflow 规则同性质，没有退化。

## 三镜代价

本次无 TG-23 命中。
