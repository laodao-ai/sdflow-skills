# Tasks: minimize-repo-footprint

> 决策真相源 = [`adr/0003`](../../adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md)（+ grill-amendment）+ [`adr/0005`](../../adr/0005-dev-runtime-checkout-split.md) + [design.md](./design.md)。
> 全部未勾（explore/propose + 一轮 grill 收敛，实现在阶段三）。
> 需求 ID 见 [specs/spec-workflow/spec.md](./specs/spec-workflow/spec.md)：**R-MRF-1** 分层部署 · **R-MRF-2** resolver · **R-MRF-3** 迁移。
> grill 2026-07-03 后：**撤销"提根"**、canonical 改软链(Unix)/指针(Windows)、checkpoint 归 `~/.sdflow/hack/`。Codex-hook 空档已单记 todolist（超本 change 范围）。
> model-baseline 重审（explore 2026-07-03，`adr/0006`）后：**resolver 脚本化**——三步链由 `~/.sdflow/hack/resolve-workflow.sh` 确定性执行，SKILL.md 只调用（§3 已按此改写）。

## 1. canonical 全局位（不提根）〔R-MRF-1，grill-amendment〕

> 撤销"提根"：bundle 留 `opsx-project-init/assets/workflow/`，canonical 间接层藏住布局。

- [ ] 1.1 `setup.sh` 建 canonical（Unix）：软链 `~/.sdflow/workflow` → 运行 checkout 的 `opsx-project-init/assets/workflow`；幂等、agent 中立〔R-MRF-1〕
- [ ] 1.2 `setup.sh` 建 canonical（Windows）：写指针文件 `~/.sdflow/workflow-path`（内容 = bundle 绝对路径，取自 `$REPO_DIR`）〔R-MRF-1〕
- [ ] 1.3 确认 bundle 仍在 `assets/workflow`、"唯一权威源"5 处约定（SKILL.md×4/init.py/config.yaml/CHANGELOG）不动〔R-MRF-1〕

## 2. 部署分层：init.py 改造（R-MRF-1）

- [ ] 2.1 `copy_bundle` 去掉规则部分——只部署 `tools/` 子树到消费仓 `openspec/workflow/tools/`，规则文件不再复制〔R-MRF-1〕
- [ ] 2.2 `checkpoint-commit.sh` 改**全局装到 `~/.sdflow/hack/`**（agent 中立 canonical 根，**非** `~/.claude/hooks`——bash 工具非 Claude 事件 hook），不再进消费仓 `hack/`；拷贝 + chmod 一次设好 exec 位〔R-MRF-1，grill-amendment〕
- [ ] 2.3 `workflow.md` line62 `[checkpoint]` 单点约定改指 `~/.sdflow/hack/checkpoint-commit.sh`（步骤表简写不含硬路径，只改此一处）〔R-MRF-1，grill-amendment〕
- [ ] 2.4 `serve.sh` / 根 `review.html` 复制逻辑保持（tools 最小副本模型不变）〔R-MRF-1〕

## 3. 规则解析 resolver（R-MRF-2）〔model-baseline-amendment / adr/0006：resolver = 全局脚本，非 SKILL.md prose 协议〕

> 机队锚定：执行模型 = opus/sonnet/gpt-5.5。三步链交模型逐条照做会静默跳步，故确定性脚本化，skill 只调用。

- [ ] 3.1 新增 `resolve-workflow.sh`：确定性实现三步链——①查仓内**规则文件本体**（`workflow.md`/`spec-checklists/`/`code-checklists/`，**不查** `openspec/workflow/` 目录，tools/ 使其恒存在）→ ②canonical 回落链（试 `~/.sdflow/workflow/` 目录 → 否则读 `~/.sdflow/workflow-path` 指针；平台判断在脚本内）→ ③全局也缺 = **非零退出 + stderr 固定告警文案**（反静默守卫措辞）。stdout = 规则根路径。随 `setup.sh` 装到 `~/.sdflow/hack/`（同 checkpoint，exec 位一次设好）〔R-MRF-2〕
- [ ] 3.2 各 skill 规则读点改为**调用脚本、用其 stdout 路径**——先扫全读点清单（spec-review/impl-review 已知；opsx-done/recorders/opsx-ship 逐个扫，见 proposal 开放问题3）；SKILL.md 统一一句话："跑 `~/.sdflow/hack/resolve-workflow.sh`，用输出路径读规则；非零退出 → 显式降级通用评审 + 转发脚本告警文案"〔R-MRF-2〕
- [ ] 3.3 调用方守卫：skill MUST NOT 静默吞脚本非零退出码、MUST NOT 在指令内自行重实现三步链（防 prose 协议回潮）〔R-MRF-2〕

## 4. 迁移：opt-in 删 + 陈旧遮蔽告警（R-MRF-3）

- [ ] 4.1 `opsx-project-init update` 停止复制规则（只刷 tools/）〔R-MRF-3〕
- [ ] 4.2 检测消费仓残留旧规则文件 → 告警（反静默守卫·陈旧遮蔽变体）"遮蔽全局且不再更新，删=跟全局/留=pin"，**绝不自动删**（触发点 update 内联 or opsx-maintain，见 proposal 开放问题4）〔R-MRF-3〕

## 5. dev/runtime 纪律 + 测试与文档

- [ ] 5.1 写 dev/runtime checkout 纪律段（`adr/0005`）：开发 checkout local-first dogfood 规则；改 skill 需 setup-from-dev；setup 只在运行 checkout 跑〔R-MRF-2〕
- [ ] 5.2 `opsx-project-init/tests/` 跟部署模型改：init 后消费仓 `openspec/workflow/` 只含 tools/、规则数=0；checkpoint 不再进消费仓 hack/〔R-MRF-1〕
- [ ] 5.3 resolver **脚本单测**（从"模型行为测试"变普通单测，可测性提升〔adr/0006〕）：本地命中 / 全局软链命中 / 全局指针命中 / 全局缺 = 非零退出 + 告警文案断言〔R-MRF-2〕
- [ ] 5.4 迁移测试：残留旧规则触发告警、不被删；留旧副本仍 local-first 命中〔R-MRF-3〕
- [ ] 5.5 更新 `INDEX.md` / `CLAUDE.md` 托管区块措辞（若涉及规则落点描述）；ROADMAP 状态推进〔R-MRF-1〕

## 6. 与 issues 层交集收口

- [ ] 6.1 定 `issues.py`（共享 issues 层脚本）物理落点：随本 change 脚本全局化一并定（归档 B design §五留的交集）〔R-MRF-1〕
