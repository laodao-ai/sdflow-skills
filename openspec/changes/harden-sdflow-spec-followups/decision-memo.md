---
schema_version: 1
change: harden-sdflow-spec-followups
branch: feat/harden-sdflow-spec-followups
generated_at: 2026-07-27T03:23:36Z
decision_hash: 67e299e595d9
---

# 决策纪要 · harden-sdflow-spec-followups

## 目标态

`/sdflow-spec` 与 FF-0 在 Codex/跨仓/异常命令场景如实表达其可验证边界，阶段一入口保持轻量可执行，且 `add-sdflow-spec` 已完成的归档期修正和台账状态一致。

## 承重约束

- **C1 范围只覆盖源仓后续项** — [spec-review-amendment] T232–T238、T240–T242 与 T132 的前置订正纳入本 change；T132 只订正未来 gate 输入并保持 OPEN，T239 的下游 rollout 明确排除。**证据锚**：用户 2026-07-27 明确指示；`openspec/issues/todolist/2026-07-todolist.md:92-102`。
- **C2 FF-0 不得解析 shell 以推断实际仓** — payload `cwd` 与命令实际作用仓不一致时，守卫必须停止判定而非对错仓 deny；不把 `cd`/变量/引号扩展塞进解析器。**证据锚**：T235；`sdflow-init/assets/hooks/ff0-branch-guard.py` 模块边界说明。
- **C3 fail-open 必须留下宿主可见的解释，且不能越权放行** — 对跨仓或读不出 change 名的未判定路径，输出 PreToolUse `additionalContext`，但不输出 `permissionDecision: allow`。**证据锚**：Claude Code Hooks Reference（2026-07-27 实查）：`allow` 会跳过权限提示，`additionalContext` 可在不做决策时加入上下文；T237。
- **C4 Codex 的 `disable-model-invocation` 只可按已验证事实表述** — 本运行仅证明用户显式触发成功；当前 Codex 工具面没有模型可调用的 Skill 执行接口，不能将其当作“模型调用被拒”的正向实证。**证据锚**：本 session 工具清单与用户 `$sdflow-spec` 触发记录；T233。
- **C5 分支 A/B 的 grill 收敛信号必须分治** — A 使用非空且身份一致的 `decision-memo.md` 与 `checkpoint(sdflow-spec-grill)`；B 使用既有 grill checkpoint / `sdflow:grill-done` 锚。**证据锚**：T234；`hack/tests/test_decision_memo_gate.py`。
- **C6 入口默认上下文必须实质缩小，不能只靠改行宽** — 每次执行的状态机、门、命令和出口仍留在 `SKILL.md`；外派（未启用）、异常诊断细节与演进依据按需外置。入口以 Python Unicode 字符计数限制为不超过 18,000。**证据锚**：用户 2026-07-27 明确确认；`sdflow-spec/SKILL.md` 当前为 20,768 字符、600 行。
- **C7 终审追溯范围是整个 change 目录** — 被砍候选及理由在 `decision-memo.md` 中可追溯即合格；`design.md` 的一行指针是合法路径，不要求四件套重复。**证据锚**：T236；`sdflow-spec/references/decision-memo-schema.md:93-105`。

## 拍板决策

- **D1 新 change 统一收口源仓 follow-ups** — 名称采用 `harden-sdflow-spec-followups`；不另开 rollout change。依据：遗留共享 `/sdflow-spec`、FF-0 与台账闭环；**砍掉的候选**：拆为源仓修复与下游 rollout 两个 change，理由：T239 由用户在消费仓自行执行，拆分只增加完整 workflow 成本。
- **D2 入口采用“薄 SKILL + 按需 reference”** — `SKILL.md` ≤ 18,000 Unicode 字符；将未启用外派、异常诊断细节、演进依据拆到受版本管理的 references，并为必驻章节与引用加载条件添加测试。依据：降低每次注入成本且不丢执行契约；**砍掉的候选**：24,000 字符但不拆分，理由：只能防软换行规避，不能减少日常上下文。
- **D3 未判定的 FF-0 调用保留 fail-open，但带单一上下文审计** — [spec-review-amendment] 只有完整匹配单条直接 literal 创建 grammar 才进入 payload cwd 的三分支；其余命中创建字样的形态采用无 `permissionDecision`、统一带 `command-unverifiable` 的 `additionalContext` JSON。依据：正向有界识别不需要对无界 shell 做负向证明、不越权自动批准、使模型和 transcript 都看见守卫未判定；**砍掉的候选**：危险结构黑名单，理由：永远无法证明覆盖所有 cwd 包装；`cwd-ambiguous|change-name-unparseable` 双原因码，理由：没有 hook 外部或跨阶段消费者、权限行为相同，当前内部仅用于选择两段说明，细分已连续产生组合分类反例；返回 `allow`，理由：会跳过宿主原生权限提示。
- **D4 Codex 宿主声明降为“依赖宿主执行语义，当前未作模型调用拒绝实证”** — 同时增加可复现的宿主测试说明/测试夹具，只在接口真正出现时给出正反结论。依据：不能把接口缺席伪装成拒绝证据；**砍掉的候选**：继续写“只能人触发”，理由：当前 Codex 上无可核验支撑。

## 接受的边角

- `additionalContext` 只能记录“守卫未判定”，不能证明命令实际写入了哪个仓；shell 实际语义无界。概率中等、影响被 fail-open 限制；完美解析成本高，故以诚实审计与 review 兜底。
- 当前 Codex 无法直接复现实验性 Skill 调用拒绝；不能在本 change 内凭空制造宿主接口。待宿主暴露可调用接口时补证，不把未知宣称为安全保证。

## 三镜代价

本次无 TG-23 命中。
