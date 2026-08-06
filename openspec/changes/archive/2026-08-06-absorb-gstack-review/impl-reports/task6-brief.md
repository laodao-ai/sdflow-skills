### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task6-<slug>.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

本仓的测试命令是 `/usr/bin/python3 -m pytest`（本机裸 `pytest` 不存在、默认 `python3` 未装
pytest——这是本机环境事实）。仓 `openspec/config.yaml` 若无 `test-suites` 配置，则依仓内既有
约定判定并在报告里写明命令原文与判定依据；确无某层则记「未覆盖（本仓无此层）」+ 判定依据，
**不得 fail-closed 罢工**。

除聚合回归外，本票还承接本 change 的三项收尾：Success Metrics 静态核验、issues 池记录、
以及为紧随其后的 dogfood 打开全局窗口。

**dogfood 分工声明（诚实边界）**：`tasks.md` 6.4 要求本 change 自身跑一次 `/sdflow-code-review`
并核验产出锚。该实跑观测**由本票之后 ship 链序的 code-review 步天然承担**（开窗后它跑的就是
本 change 的新 SKILL），本票只负责**开窗前置**与**待核锚清单的落盘**，不重复跑一次多镜评审。
本票 MUST 在报告里显式写明这一分工与待核锚清单，MUST NOT 声称已完成实跑观测。

**开窗是机器级影响的时间盒操作**：`bash setup.sh` 会把 `~/.sdflow/workflow`、`~/.claude/skills/*`、
`~/.codex/skills/*` 全部翻向本开发树。本票 MUST 在报告里写明还原方式（合并后在运行 checkout
`~/.skills/sdflow-skills` 重跑 `bash setup.sh`），供收尾提示引用。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] `grep -rn "gstack" sdflow-code-review/SKILL.md` 严格归零（贴命令与输出）
- [ ] `openspec validate --strict` 绿（贴输出）
- [ ] issues 池记三条 todo（用开发 checkout 的 `sdflow-issues/scripts`、显式传 `change` 字段）：① python.md domain（Async/Sync 混用条目落点）② spec-review 侧 autoplan 姊妹依赖处置 ③ 仓根 `openspec/workflow/` 孤儿副本清理（`lens-metric-contract.md` / `WORKFLOW-GUIDE.md`）
- [ ] 开发 checkout 跑 `bash setup.sh` 成功，且 `readlink ~/.sdflow/workflow` 确认指向本开发树（贴输出）
- [ ] 报告写明 dogfood 分工声明 + 待核锚清单（`mode="subagent"` 锚 / `scope-audit` 折叠出的 `lens="broad"` 行 / anchor_lint 通过）+ 全局窗口还原方式
