# impl-notes — matt-workflow-integration（归档材料：4.1 / 4.2 实测结论）

## 4.1 disable-model-invocation harness 语义实测

**结论：阻断。** `disable-model-invocation: true` 会让主 session 的 Skill tool 调用被 harness 直接拒绝。

依据（两次独立实证，2026-07-10/11 同一会话）：
1. 受控探测：主 session `Skill(implement)`（matt `implement` skill 带该旗标）→ harness 返回错误
   `Skill implement cannot be used with Skill tool due to disable-model-invocation`，零副作用。
2. 自然实证：同会话早前 `Skill(grill-with-docs)`（`~/.claude/skills/grill-with-docs/SKILL.md:4` 旗标在场）同款被拒，
   用户手动键入 `/grill-with-docs` 才得以执行。

**处置（按假设表②既定路径）**：sdflow-implement **维持不写**该旗标——其执行完全依赖 ship 主 session 经 Skill tool
inline 加载，写旗标即自毁编排链（对抗镜预判成立）；触发收窄仅靠 description 措辞（已核 SKILL.md frontmatter 无旗标）。

## 4.2 出 ticket → gate → 执行最小演练

演练场：`<scratchpad>/drill-tickets/`（独立 git 仓，不触本仓；阅后即弃，本 notes 为存证）。
盘面：`openspec/config.yaml` 开 `impl-pipeline: tickets`；change `drill-tickets` 四件套 + 手写 `design_approved`
frontmatter（人机同权通道）；ticket plan 按 sdflow-implement 出 ticket 契约（marker 单键 frontmatter + 2 张
`### Task N:` ticket + Blocked-by + 验收复选框）。

逐步判定（全程 gate 零改动、零 UNKNOWN）：

| 步 | 动作 | 判定 | 结果 |
|---|---|---|---|
| ① | route CLI 首跳 | receipt 三值 | `PIPELINE_RECEIPT change=drill-tickets config=tickets marker=tickets pipeline=tickets plan_sha=18ca832` ✓ |
| ② | plan 入库 | B1 窗口锚 | 窗口 `[18ca832, HEAD]` 建立（本演练 plan 随初始 commit 入库，验证了 D3 记载的 add -A 捎带自愈路径；正式流程仍按契约单独 checkpoint） |
| ③ | gate 三道校验 | fence/标题/重号 | `CONTINUE_IMPL done_tasks=[]`（0/2）✓ |
| ④ | 实现 ticket1 提交**不带标签** | 续审语义 | gate 仍 `done_tasks=[]`——「实现提交在、完成标签缺」不计 done，resume 进续审而非重实现 ✓〔F1〕 |
| ⑤ | 双轴审 spot check | 验收逐条 | Spec 轴两项 ✓（Standards 轴纯文本无域清单命中，按 F13 口径记「未覆盖-演练简化」不宣称通过） |
| ⑥ | 补打 `checkpoint(drill-tickets:task1-hello)` + 勾框（双写） | done 归属 | gate `done_tasks=["1"]`（1/2），命名空间标签精确归属 ✓ |
| ⑦ | frontier CLI `--done 1` | 拓扑 next-ready | 输出 `2`（Blocked-by 1 解锁）✓ |

**附带发现（演练价值）**：change 名以 `_` 开头（如 `_drill`）会使 TAG_RE 命名空间组
（`[a-z0-9][a-z0-9-]*`）失配、完成标签整条不计——出 ticket 模式对 change 名的字符集依赖与 openspec
kebab-case 约定一致，无需额外防御，但演练/临时 change 命名须避开下划线前缀。

**结论**：假设表①（tickets 管线本仓未实践过）经最小演练消解——出 ticket 外衣、三道校验、后置双写、
resume 续审、frontier 拓扑全部按契约工作，无需回炉 SKILL.md 措辞。

## 6.1 附记：活文档全量表述同步留 Phase B

docs/ 历史快照不回改；活文档（workflow-map/overview、sdflow-fable5/* 等）中 writing-plans/subagent-dev
的全量表述同步显式留 Phase B（本 change 仅改 workflow.md 权威源的三处行 + README 增行），hand-off 引用本条。
