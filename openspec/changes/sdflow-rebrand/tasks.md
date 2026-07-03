# Tasks: sdflow-rebrand

> 决策真相源 = [proposal.md](./proposal.md) + [design.md](./design.md)（§三 RENAME-MAP 唯一数据源 / §四 D1-D6）。
> 全部未勾（ff 生成，实现在阶段三）。需求 ID 见 [specs/spec-workflow/spec.md](./specs/spec-workflow/spec.md)：**R-SR-1** 命名与品牌一致性（ADDED）· **R-SR-2** 安装器品牌与 marker 兼容（ADDED）· 两条 MODIFIED（bundle 权威源 / resolver）为名称随动。
> 机队锚定〔adr/0006〕：改名活全部 RENAME-MAP 驱动 + 白名单反向断言收尾（D1），不靠模型逐处记忆。

## 1. 改名执行（RENAME-MAP 驱动）〔R-SR-1〕

- [ ] 1.1 `git mv` ×9（一次提交保 rename 检测）：opsx-project-init→sdflow-init、opsx-done→sdflow-done、opsx-maintain→sdflow-maintain、opsx-roadmap-planner→sdflow-roadmap、spec-review→sdflow-spec-review、impl-review→sdflow-code-review、buglist-recorder→sdflow-buglist、todolist-recorder→sdflow-todolist、issues-recorder→sdflow-issues
- [ ] 1.2 功能性文本 sweep（RENAME-MAP × 引用面，design §三 ①②⑤）：`assets/workflow/workflow.md` 步骤表 prompt、`assets/snippets/claude-section.md`+`index-section.md`（配套 skill 表+安装句）、12 个 SKILL.md 互相点名、`setup.sh`/`scripts/init.py` 提示文案、`README.md` 列表、`CLAUDE.md` 正文（托管区块勿手改，走 5.4 update --dev 重注入）
- [ ] 1.3 sibling 硬编码换新〔D4，只换字面不抽象〕：`sdflow-issues/scripts/issues.py` :64-65 目录名 join（`sdflow-buglist`/`sdflow-todolist`）+ 三 recorder/issues tests 中的路径与目录名引用修正
- [ ] 1.4 `sdflow-done/SKILL.md` §2.1 固定脚本路径三行换新名（`~/.claude/skills/sdflow-{buglist,todolist,issues}/scripts/*.py`）+ 兜底 find 提示句同步

## 2. 触发词重写（用户显式要求）〔R-SR-1，D2〕

- [ ] 2.1 9 个改名 SKILL.md 的 frontmatter description 重写：换 slash 新名与自称；**原触发场景语句集全保留**（触发等价约束）；旧名指称清零
- [ ] 2.2 产出 `trigger-map.md`（存 change 目录随档）：每 skill 一节——旧触发短语集 → 新 description 对应短语 + slash 新名；等价性可逐行核对（spec-review 评审面）

## 3. 品牌收拢〔R-SR-2〕

- [ ] 3.1 新建 `VERSION` = `0.9.0`（D6）；`setup.sh` 摘要输出改 `sdflow-skills v${VERSION}`（缺文件仍显式 vunknown）
- [ ] 3.2 marker：`setup.sh` 新写 `.sdflow-skills`；所有权判定**永久兼容** `.laodao-skills`（识别为自属可刷新，D3）；对应注释更新
- [ ] 3.3 品牌叙述清扫：snippets/README/CLAUDE.md 正文中"来自 laodao-skills"类表述 → sdflow-skills（`bash ~/.skills/sdflow-skills/setup.sh` 安装句已对）；laodao 旧仓处置 = 不动（Non-Goals，写进 hand-off 提醒即可）

## 4. 测试与断言〔R-SR-1/R-SR-2〕

- [ ] 4.1 新增测试：**跨改名孤儿清理**（假 HOME 预置旧名链指向本仓旧路径 → setup 重跑 → 新名链在、旧名链被 cleanup_orphans 收走）；**存量 `.laodao-skills` marker 兼容**（预置带旧 marker 的拷贝 → 重跑 → 被识别自属并刷新换新 marker）；setup 版本行断言 `sdflow-skills v0.9.0`
- [ ] 4.2 存量测试路径修正后全量 `python3 -m pytest -q` 全绿无 warning（改名后 sdflow-init/tests 等路径随 git mv 自动跟随，内部引用 1.3 已修）
- [ ] 4.3 **白名单反向断言**（D1，独立验收步）：对 9 个旧名逐一全仓 grep，命中文件必须全部落在白名单（`openspec/adr/` / `openspec/ROADMAP.md` 历史行 / `openspec/CONTEXT.md` / `openspec/changes/archive/` / `.superpowers/` / 本 change 目录自身）——白名单外任一命中即 FAIL 并修复；断言命令与结果留档进 change 目录

## 5. 激活与文档收尾

- [ ] 5.1 落 `adr/0007-sdflow-naming-consolidation.md`：全量 sdflow- 前缀 + 去后缀 + 三保留决策；已评估未选 = plugin 冒号命名空间（Codex 无 plugin，双 agent 否决）、半量改名（品牌分裂）；触发等价约束
- [ ] 5.2 ROADMAP：`extract-sdflow-repo` 行更名 `sdflow-rebrand`（rescope/supersede 注记，状态推进）
- [ ] 5.3 本机激活：`bash setup.sh` 重跑 → `~/.claude/skills` 与 `~/.codex/skills` 双侧 readlink 抽查新名、旧名链清零（真实输出留档 activation-log.md）；触发抽查 3 条真实语句（如"记一下这个 bug"→ sdflow-buglist）
- [ ] 5.4 `python3 sdflow-init/scripts/init.py update --dev --root .` 同步本仓 instance 与托管区块（CLAUDE/AGENTS/INDEX 重注入新名）；`diff -q` instance vs assets 为零
- [ ] 5.5 hand-off 提醒项预置：消费仓须跑一次 `sdflow-init update` 重注入托管区块；本 session 内旧 slash 名已失效（新会话生效）
