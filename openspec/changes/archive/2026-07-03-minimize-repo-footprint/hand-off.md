# hand-off — minimize-repo-footprint

> 2026-07-03 · verify PASS 之后 / archive 之前产出 · 异步人类再入口 + 下个 change 种子

## ✅ 完成了什么（锚点已独立复核，非搬运 verify ✅）

- **运行 checkout 迁移**（Q1=A）：`~/.skills/sdflow-skills` 就位、软链全切（activation-log.md Task1 段 readlink 原始输出，复核在场）。
- **resolver 脚本化**：`~/.sdflow/hack/resolve-workflow.sh` 三步链 + 契约守护（cwd/--root/SDFLOW_HOME/sane 非空/退出码 0-2-64），18 个脚本单测（`opsx-project-init/tests/test_resolve_workflow.py`，61 全绿套件内，复核测试文件在场）。
- **激活验证三重真实调用**：本仓 local-pin / 临时消费仓 global-canonical / 新 init 仓规则数 0 + **Codex CLI 侧实测通过** + **经 /impl-review 第零步协议真实触发**（activation-log.md 各段原始输出，复核 `source=` 行在场）。
- **部署分层**：copy_bundle 只 tools/（+`--dev` 整刷，带源仓身份校验）、handle_config 读 BUNDLE_SRC、checkpoint/hack 全局装（setup.sh `install_sdflow`，`test_setup_sdflow.py` 在场）。
- **迁移反静默**：陈旧遮蔽告警（update+init 双模式 + opsx-maintain 兜底 + checkpoint 孤儿对称提示），绝不自动删（`TestStaleShadowWarnings` 在场）。
- **读点改造**：spec-review 3 处 + impl-review 4 处改调 resolver；config/snippets 全局解析措辞；`sdflow-upgrade` skill 新增（`sdflow-upgrade/SKILL.md` 在场）。
- 评审链：spec-review（5 镜，Q1/Q2 设计门拍板）→ subagent-dev 11 任务双审 → 终审 READY-TO-MERGE → impl-review（5 镜，10 findings 全修 `[impl-review-fix]` @ `935eb42`）。

## ⏳ 未完成 / 延后

- **批次 `minimize-repo-footprint`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）：13 项 PROPOSED（T6–T18）。要点：T14 Windows 指针所有权检查（tasks 1.2 对账注的部分完成项）、T13 测试断言补强、T18 skills 链接管可见化、T9/T10/T11 属 workflow 机制债（随 opsx-ship 落）。
- **自动选推荐的 2 项裁决**（impl-review，记理由于 code-review-report.md）：多 checkout 接管走"可见化不阻断"（X1）；tools/ 收敛走"清后拷"。如不认可可在清理 change 翻案。
- verify Minor 缺口 = 上述 T 号全集，无核心缺失。

## ▶ 下一阶段建议

1. **合并后立即**：`git push` → 在运行 checkout跑 `/sdflow-upgrade`（pull + setup）——把 `~/.claude/skills/*` 与 `~/.sdflow/*` 从"临时指 dev"还原到运行 checkout（activation-log Task10 承诺项，**勿漏**）。
2. **下个 change = `opsx-ship-orchestrator`**（ROADMAP 建议序）：materialize 时写死 adr/0006 约束(b)（确定性步序台账）；顺带认领 T10（自动选推荐判据）+ T11（档位映射进 config）。
3. **清理 change 候选**：批次 `minimize-repo-footprint` 的 T13/T14/T15/T16/T18（均为小修，适合一个半天的收尾 change）；T6（Codex-hook 空档）可并入。
4. Phase C（cross-model outside voice）与 `workflow-metrics-loop` 随后；本 change 的五镜报告正是 metrics-loop 的第一批数据样本。
