# Proposal: sdflow-rebrand

> 承 `minimize-repo-footprint`（已归档）与 ROADMAP 的 `extract-sdflow-repo`（暂名）——拆库半已发生（repo 已迁 `laodao-ai/sdflow-skills`、misc skills 留守 laodao-skills），本 change 把其剩余 scope 落地为「**sdflow 品牌收拢**」。决策出处 = explore 2026-07-03（命名方案对比 + 三项具体命名拍板）+ `adr/0003` grill ⑤（sdflow 命名派生）。

## Why

12 个 skill 的命名是三个时代的地层堆积：`opsx-*` 家族与官方 `opsx:*` CLI 只差一个标点（长期混淆源）、`spec-review`/`impl-review` 是裸通用词（撞名风险最高且不表归属）、品牌字符串仍是 laodao 遗产（setup 输出 `laodao-skills vunknown`、marker `.laodao-skills`、无 VERSION）。上一 change 刚交付规则全局解析——改名传播成本降到历史最低（权威源改一次 + 消费仓 update 重注入），消费仓数量也在最少点；拖到 Phase C / 消费仓铺开后成本单调上升。**现在是改名的最佳窗口。**

## What Changes

- **①全量改名 9 个 skill 目录**（**BREAKING**：斜杠命令名变化，旧名即刻失效、不留 stub）：

  | 旧名 | 新名 | 旧名 | 新名 |
  |---|---|---|---|
  | opsx-project-init | `sdflow-init` | spec-review | `sdflow-spec-review` |
  | opsx-done | `sdflow-done` | impl-review | `sdflow-code-review` |
  | opsx-maintain | `sdflow-maintain` | buglist-recorder | `sdflow-buglist` |
  | opsx-roadmap-planner | `sdflow-roadmap` | todolist-recorder | `sdflow-todolist` |
  | | | issues-recorder | `sdflow-issues` |

  **保留原名**：`embedded-test-sop`（域技能身份）、`openspec-upgrade`（升级外部 openspec CLI，非 sdflow 本体）、`sdflow-upgrade`（命名法源头）。
- **②触发词/description 全面重写**（用户显式要求）：各改名 SKILL.md 的 frontmatter description 随新名重写——斜杠命令新名、中文触发短语同步更新、**触发精度不得回退**（原有触发场景全保留，仅换名与净化表述）。
- **③品牌字符串清扫 + 旧仓处置**：setup.sh 输出改 `sdflow-skills` + 补 `VERSION` 文件；marker `.laodao-skills` → `.sdflow-skills`（**含存量 marker 迁移兼容**：识别旧 marker 为自属，勿把老 Windows copy 判为异物）；snippets/README/CLAUDE.md 中"来自 laodao-skills"类表述；laodao 旧仓**保留为 misc 不删**；旧名软链由 setup.sh 孤儿清理收走（**跨改名场景需测试锚定**：cleanup_orphans 以 REPO_NAME 匹配，改的是 skill 目录名非仓名，dangling 旧链应被清）。
- **功能性引用面四类同步**（explore 已扫）：workflow.md 权威源步骤表 prompt、assets/snippets 托管区块、`opsx-done`→`sdflow-done` 的 sibling 脚本路径（`~/.claude/skills/{新名}/scripts/*.py`）、各 SKILL.md 互相点名。**文档性引用不改**（ADR/ROADMAP 历史行/CONTEXT 术语史/archive——历史记录保持原名）。
- 落 `adr/0007`（命名方案决策：全量 sdflow- 前缀 + 去后缀；已评估未选：plugin 冒号命名空间（Codex 无 plugin，双 agent 否决）、半量改名（品牌分裂））。
- ROADMAP：`extract-sdflow-repo` 行更名 `sdflow-rebrand` 并注明 rescope/supersede。

## Capabilities

### New Capabilities

（无——纯命名/品牌收拢，不引入新行为能力。）

### Modified Capabilities

- `spec-workflow`：①既有需求文本中的 skill 名随改名更新（如 resolver 需求点名的 spec-review/impl-review、部署需求中的 opsx-project-init）；②ADD 一条「skill 命名与品牌一致性」需求（sdflow- 前缀规范、保留名单、marker 迁移兼容、孤儿链清理承诺）。

## Impact

- **代码**：9 个目录 `git mv`；各 SKILL.md（description 重写 + 互引改名）；`setup.sh`（品牌输出/VERSION/marker 名 + 存量 marker 兼容）；`opsx-done`→`sdflow-done` SKILL.md §2.1 sibling 脚本路径；assets/snippets 两文件 + assets/workflow/workflow.md 步骤表；README Skills 列表；`opsx-project-init`→`sdflow-init` 的 scripts/init.py 内提示文案（"安装配套 skill"句）；测试文件中引用路径。〔TG-01：bash+python 工具链，无领域清单命中〕
- **机械化约束**〔adr/0006〕：改名由**映射表驱动**（一个 rename-map 数据 + 脚本/批量命令执行 + **grep 断言清单**收尾验证），不靠模型逐处手改记忆；断言 = 全仓（除 ADR/CONTEXT/ROADMAP 历史行/archive/`.superpowers`）无旧名残留的白名单式检查。
- **消费仓迁移**：托管区块换名经 `sdflow-init update` 重注入；本机 `~/.claude/skills`/`~/.codex/skills` 旧链经 setup.sh 孤儿清理；`~/.sdflow` canonical 不受影响（路径无 skill 名）。
- **已知代价**：斜杠命令肌肉记忆一次性切换（单用户，接受）；历史文档中旧名与现名并存（有 adr/0007 与 CONTEXT 术语衔接）。

## Success Metrics

- `ls */SKILL.md` 呈现 12 个目录 = 9 新名 + 3 保留名；`bash setup.sh` 后 `~/.claude/skills` 与 `~/.codex/skills` 只有新名链，旧名链被孤儿清理收走（测试锚定）。
- grep 断言清单全绿：功能性文件（SKILL.md×12 / setup.sh / init.py / assets/snippets / assets/workflow/workflow.md / README）中零旧名残留（白名单：ADR/CONTEXT/ROADMAP 历史行/archive）。
- 全部既有测试通过（改名后路径引用修正），且新增：跨改名孤儿清理测试、存量 `.laodao-skills` marker 兼容测试。
- 触发验证：新 description 在 skill 列表加载后，原触发场景语句（如"记一下这个 bug""帮我 review 设计"）仍指向正确 skill（人工抽查 + description 对照表）。
- setup.sh 输出 `sdflow-skills v<VERSION>`；消费仓跑一次 `sdflow-init update` 后托管区块引用全为新名。

## Non-Goals

- 不动 `opsx:*` 官方 CLI skills（openspec 包资产）与 superpowers/gstack 外部引用。
- 不删 laodao-skills 旧仓、不处置其 misc skills（留守现状）。
- 不留旧名 stub/别名（单用户环境，干脆切换）。
- 不改 ADR/ROADMAP 历史行/CONTEXT 术语史/archive 中的旧名（历史记录）。
- 不借机重构任何 skill 的行为逻辑——**纯改名/文案，行为零变化**（description 重写以触发等价为界）。

## Stakeholders & External Dependencies（TG-20）

- **消费仓**：托管区块中的 skill 名将过时 → 经 `sdflow-init update` 重注入；未 update 的仓引用旧名会失灵（旧链已清）——update 提示中注明。
- **双 agent**：Claude 与 Codex 两侧 skills 目录同步换链（setup.sh 一次覆盖两处）。
- **laodao-skills 旧仓**：不动；其同名旧 skills 若仍被旧链引用，本次 setup 后链已重指/清理。
- **openspec CLI**：`opsx:*` 官方 skills 不受影响；本仓 `.claude/skills/openspec-*`（CLI 生成）不在改名范围。

## Open Questions（TG-21）

1. `VERSION` 起始版号（建议 `0.9.0`——rebrand 后、metrics-loop/Phase C 前的基线；低风险，实现期定即可）。
2. 存量 `.laodao-skills` marker 兼容窗口多长（建议：永久识别为自属——一行判断的成本，换绝不误伤；实现期定）。

## Compliance

无跨产品共享数据模型（D-6 N/A）、无 DB 迁移（D-2 N/A）、无外部计费（TG-24 N/A）；迁移守"绝不自动删非自属产物"红线（孤儿清理仅收自属 dangling 链，marker 兼容防误伤）。
