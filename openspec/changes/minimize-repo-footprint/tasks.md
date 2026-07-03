# Tasks: minimize-repo-footprint

> 决策真相源 = [`adr/0003`](../../adr/0003-deploy-footprint-global-rules-minimal-repo-copy.md)（+ grill-amendment）+ [`adr/0005`](../../adr/0005-dev-runtime-checkout-split.md) + [design.md](./design.md)。
> 全部未勾（explore/propose + 一轮 grill 收敛，实现在阶段三）。
> 需求 ID 见 [specs/spec-workflow/spec.md](./specs/spec-workflow/spec.md)：**R-MRF-1** 分层部署 · **R-MRF-2** resolver · **R-MRF-3** 迁移。
> grill 2026-07-03 后：**撤销"提根"**、canonical 改软链(Unix)/指针(Windows)、checkpoint 归 `~/.sdflow/hack/`。Codex-hook 空档已单记 todolist（超本 change 范围）。
> model-baseline 重审（explore 2026-07-03，`adr/0006`）后：**resolver 脚本化**——三步链由 `~/.sdflow/hack/resolve-workflow.sh` 确定性执行，SKILL.md 只调用（§3 已按此改写）。
> spec-review 2026-07-03 后〔spec-review-amendment，详见 [spec-review-report.md](./spec-review-report.md)〕：新增 0/2.5/3.4/5.6/5.7，重写 3.1，裁决 4.2 触发点。
> **设计门拍板（2026-07-03）**：**Q1 = A**——运行 checkout 落位 `~/.skills/sdflow-skills/`（0.1 生效），并新增 `sdflow-upgrade` skill（§7）；**Q2 = 维持现状**（留副本即 pin，不加 marker）。
>
> **发布纪律（贯穿）**〔spec-review-amendment / autoplan #11〕：运行 checkout `git pull` 后**必须立即重跑 `setup.sh`**（symlink 生效的 SKILL.md 与拷贝生效的 `~/.sdflow/hack/` 脚本更新节奏不同步，窗口期靠 3.2 的 127 专属文案兜底显形）。

## 0. 前置：拓扑接缝〔spec-review-amendment · 设计门拍板 Q1=A〕

- [ ] 0.1 迁移运行 checkout：fresh clone `laodao-ai/sdflow-skills.git` → **`~/.skills/sdflow-skills/`**，在其中执行 `bash setup.sh`（重指全部 skill 软链）；验证 remote 正确、`~/.claude/skills/*` 与 `~/.codex/skills/*` 软链已指向新 checkout。注意：setup.sh 所有权检查可能把"指向旧仓 laodao-skills 的同名软链"视为非自属——须确认能接管或给出人工清理提示；旧 `~/.skills/laodao-skills` **保留不删**（misc 仓，处置归 `extract-sdflow-repo`）。**未迁移前禁止执行 1.1/1.2**（canonical 会钉死旧仓 b248c2d）〔R-MRF-1〕

## 1. canonical 全局位（不提根）〔R-MRF-1，grill-amendment〕

> 撤销"提根"：bundle 留 `opsx-project-init/assets/workflow/`，canonical 间接层藏住布局。

- [ ] 1.1 `setup.sh` 建 canonical（Unix）：软链 `~/.sdflow/workflow` → 运行 checkout 的 `opsx-project-init/assets/workflow`；幂等、agent 中立；**加所有权检查**（复用 `install_into` 模式：只接管自属软链，`~/.sdflow` 下遇非本工具产物停手告警，不静默 `ln -snf` 覆盖）〔R-MRF-1，spec-review-amendment D9〕
- [ ] 1.2 `setup.sh` 建 canonical（Windows）：写指针文件 `~/.sdflow/workflow-path`（内容 = bundle 绝对路径，取自 `$REPO_DIR`；**显式约定：单行、无尾随 `\r`、POSIX 风格路径（Git-Bash 语境）**）；同 1.1 所有权检查〔R-MRF-1，spec-review-amendment〕
- [ ] 1.3 确认 bundle 仍在 `assets/workflow`、"唯一权威源"约定不动——**实核 4 处**（opsx-project-init/SKILL.md 2-3 处 + init.py 1 处；CHANGELOG 不存在于本仓，原"5 处"清单已修正）〔R-MRF-1，接地镜核验〕

## 2. 部署分层：init.py 改造（R-MRF-1）

- [ ] 2.1 `copy_bundle` 去掉规则部分——只部署 `tools/` 子树到消费仓 `openspec/workflow/tools/`，规则文件不再复制〔R-MRF-1〕
- [ ] 2.2 `checkpoint-commit.sh` 改**全局装到 `~/.sdflow/hack/`**（agent 中立 canonical 根，**非** `~/.claude/hooks`），不再进消费仓 `hack/`；拷贝 + chmod 一次设好——**根治范围限 git exec 位追踪丢失**（Windows bash 解释器依赖沿现状，见 proposal Non-Goals）；**权威源钉死 = `opsx-project-init/assets/hack/`**（三副本中仓根 `hack/` 为本仓 dogfood 实例、`~/.sdflow/hack/` 为部署产物）〔R-MRF-1，grill-amendment + spec-review-amendment D10〕
- [ ] 2.3 `[checkpoint]` 单点约定改指 `~/.sdflow/hack/checkpoint-commit.sh`——**只改 `opsx-project-init/assets/workflow/workflow.md`（权威源），本仓 instance 勿手改**（同步走 5.6）；定位用锚文本"`[checkpoint]` = 步末调…约定行"（实测 assets:59/80，行号引用已漂移，弃"line62"）〔R-MRF-1，spec-review-amendment D5〕
- [ ] 2.4 `serve.sh` / 根 `review.html` 复制逻辑保持（tools 最小副本模型不变）〔R-MRF-1〕
- [ ] 2.5 `init.py handle_config` 改读 **BUNDLE_SRC**（现从消费仓副本读 config.template.yaml（init.py:168），copy_bundle 去规则后新 init 仓**必现 FileNotFoundError**）+ 回归测试〔R-MRF-1，spec-review-amendment D8 / autoplan #2 跨模型共识〕

## 3. 规则解析 resolver（R-MRF-2）〔model-baseline-amendment / adr/0006：resolver = 全局脚本，非 SKILL.md prose 协议〕

> 机队锚定：执行模型 = opus/sonnet/gpt-5.5。三步链交模型逐条照做会静默跳步，故确定性脚本化，skill 只调用。

- [ ] 3.1 **接口契约先行**〔spec-review-amendment D1/D2〕，再实现 `resolve-workflow.sh`：
  - 入参：`--root <仓根>`（缺省 `git rev-parse --show-toplevel`，防 cwd 非仓根误判）；`--explain` 输出来源诊断行（本地 pin / 全局软链 / 全局指针 + 解析到的路径）
  - env：`${SDFLOW_HOME:-$HOME/.sdflow}`（测试隔离，复用 init.py `CLAUDE_CONFIG_DIR` 先例）
  - 三步链：①仓内查**规则文件本体**（`workflow.md`/`spec-checklists/`/`code-checklists/`，**any-of 即 pin**；部分残留 → 仍判本地 + stderr **部分残留专门告警**（提示补齐或删净））→ ②canonical 回落链（试 `$SDFLOW_HOME/workflow/` 目录 → 否则读 `$SDFLOW_HOME/workflow-path`；命中后做**最小健全性检查**：workflow.md 非空 + 三顶层单元在，不过检同缺失处理）→ ③全局缺 = **退出码 2 + stderr 固定告警文案**（反静默守卫措辞）
  - stdout = 规则根路径；退出码表写进脚本头注释；随 `setup.sh` 装到 `~/.sdflow/hack/`（同 checkpoint，exec 位一次设好）〔R-MRF-2〕
- [ ] 3.2 skill 规则读点改为**调用脚本、用其 stdout 路径**——读点清单已实扫钉死〔关闭 proposal 开放问题 3〕：`spec-review/SKILL.md` 3 处 + `impl-review/SKILL.md` 4 处；opsx-done / buglist-recorder / todolist-recorder = **0 处不改**；opsx-ship 待其 change 落地后追加（移出本次验收）。SKILL.md 统一措辞："先 `[ -x ~/.sdflow/hack/resolve-workflow.sh ]`——**脚本缺失 → 专属文案『先重跑 setup.sh』**（与步③ bundle 缺失降级**区分**，防 pull→setup 窗口期误诊）；跑脚本、用输出路径读规则；退出码 2 → 显式降级通用评审 + 转发脚本告警文案"〔R-MRF-2，spec-review-amendment D3〕
- [ ] 3.3 调用方守卫：skill MUST NOT 静默吞脚本非零退出码、MUST NOT 在指令内自行重实现三步链（防 prose 协议回潮）〔R-MRF-2〕
- [ ] 3.4 **部署产物读点修复**〔spec-review-amendment D8 / autoplan #1〕：`config.template.yaml` 的 `@openspec/workflow/...` 引用、`snippets/index-section.md`、`snippets/claude-section.md` 三处改为全局解析兼容措辞（新 init 仓无规则副本时不悬空，防 opsx:ff 生成期规则注入**静默蒸发**）〔R-MRF-2〕

## 4. 迁移：opt-in 删 + 陈旧遮蔽告警（R-MRF-3）

- [ ] 4.1 `opsx-project-init update` 停止复制规则（只刷 tools/）〔R-MRF-3〕
- [ ] 4.2 陈旧遮蔽告警，触发点已裁决〔spec-review-amendment D4，关闭 proposal 开放问题 4〕：**update 内联为主 + `opsx-maintain` 兜底扫描**（覆盖常年不 update 的仓）；检测范围 = 残留旧规则文件 **+ 旧版仓内 `hack/checkpoint-commit.sh` 孤儿副本**（对称提示："删=用全局 `~/.sdflow/hack/` / 本地 workflow.md 副本仍引用它则勿删"）；措辞对齐反静默守卫；**绝不自动删**〔R-MRF-3〕

## 5. dev/runtime 纪律 + 测试与文档

- [ ] 5.1 写 dev/runtime checkout 纪律段（`adr/0005`）：开发 checkout local-first dogfood 规则；改 skill 需 setup-from-dev；setup 只在运行 checkout 跑；**+ 运行 checkout remote 必须 = 当前权威 remote（Q1）**；**+ 回滚操作句：全局规则推坏 = 运行 checkout `git checkout <上一已知良好 commit>` + 重跑 setup.sh**〔R-MRF-2，spec-review-amendment / A2-F6〕
- [ ] 5.2 `opsx-project-init/tests/` 跟部署模型改：init 后消费仓 `openspec/workflow/` 只含 tools/、规则数=0；checkpoint 不再进消费仓 hack/；**测试一律经 `SDFLOW_HOME` 重定向 tmp_path，绝不写真实 `$HOME`**〔R-MRF-1，spec-review-amendment D2〕
- [ ] 5.3 resolver **脚本单测**（从"模型行为测试"变普通单测〔adr/0006〕，`SDFLOW_HOME` 隔离）：本地命中 / **部分残留（any-of pin + 专门告警）** / 全局软链命中 / 全局指针命中 / 全局缺 = 退出码 2 + 告警文案断言 / 健全性不过检 / **指针文件含空格·中文·尾随换行** / 非仓根 cwd + `--root`〔R-MRF-2，spec-review-amendment〕
- [ ] 5.4 迁移测试：残留旧规则触发告警、不被删；留旧副本仍 local-first 命中；**孤儿 checkpoint 副本告警**〔R-MRF-3〕
- [ ] 5.5 文档**必改清单**〔spec-review-amendment D10〕：CLAUDE.md"改动 skill 源码后一般无需重跑"句加例外（**hack/ 两脚本走拷贝，改后必须重跑 setup.sh**）；INDEX.md / CLAUDE.md 托管区块措辞；ROADMAP 状态推进〔R-MRF-1〕
- [ ] 5.6 **dev dogfood 刷新机制**〔spec-review-amendment D6 / A3-F3〕：`opsx-project-init update --dev`（整 bundle 刷新本仓 instance `openspec/workflow/`）——instance 已实测落后 assets，且旧同步通道被 Q1 拓扑冻结；本 change 收尾前跑一次，消除 dogfood 悖论〔R-MRF-2〕
- [ ] 5.7 **激活验证**〔spec-review-amendment D7 / A3-F1〕：实现完成后在开发 checkout 跑 `bash setup.sh`（知情临时指 dev）→ 真实触发一次 `/spec-review` 或 `/impl-review` → 确认 `resolve-workflow.sh` 被**真实调用**（`--explain` 输出为证）；顺带实测一次 **Codex CLI 侧**调用（A1-P5 沙盒假设）。**verify 对"读点已改"类 ✅ 的证据锚点 = 真实调用输出，禁用"文本已改"**〔R-MRF-2〕

## 6. 与 issues 层交集收口

- [ ] 6.1 定 `issues.py`（共享 issues 层脚本）物理落点——**只做落点决策并记录，不在本 change 实施迁移**（收窄范围，验收判据 = 决策写进 design/ADR）〔R-MRF-1，spec-review-amendment D10〕

## 7. sdflow-upgrade skill〔设计门拍板新增 2026-07-03〕

- [ ] 7.1 新建顶层 skill `sdflow-upgrade`（纯 Markdown 编排类，参照既有 `update`/ld-update 形态）：对 `~/.skills/sdflow-skills/` 执行升级三连——`git pull` → `bash setup.sh`（canonical + `~/.sdflow/hack/` 同步刷新，**结构性堵死 pull→setup 窗口期**）→ 显示版本与最新变更；提示消费仓按需跑 `opsx-project-init update`；含回滚一句（`git checkout <last-good>` + 重跑 setup，呼应 5.1 纪律段）〔R-MRF-1〕
- [ ] 7.2 收尾同步：README「Skills 列表」加行 + 重跑 setup.sh 建新链（新增顶层 skill 约定）；旧 `update`（ld-update）skill **不动**（laodao 侧遗产，处置归 `extract-sdflow-repo`）〔R-MRF-1〕
