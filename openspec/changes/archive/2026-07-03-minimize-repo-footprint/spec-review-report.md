# spec-review-report — minimize-repo-footprint

> 日期：2026-07-03 · 编排：spec-review skill（主审 = 主 session 强模型）
> 镜面：autoplan 广审（16 findings，CEO✅/Design 跳过/Eng✅/DX✅ + Codex outside voice，详见 [gstack-review.md](./gstack-review.md)）
> ＋对抗镜×3（A1 隐藏假设 7 条 / A2 失败模式 8 条 / A3 时序·自指 6 条，Sonnet fresh context）
> ＋接地镜×1（代码事实核验 21 项，3 处不符，Haiku）。
> **领域镜 = 0**：本 change 为 bash/python 部署工具链，未命中 spec-checklists/domains 任何栈（backend-go/embedded/frontend）——按"只审命中的"跳过，非遗漏。
>
> **评审环境披露**：本次评审的 skill 执行体来自运行 checkout（`~/.skills/laodao-skills @ b248c2d`，旧 remote），
> 规则读自本仓 instance（`openspec/workflow/`，落后于 assets 权威源）。三层来源混杂**正是本 change 要解的缠**，
> 不影响本次评审有效性（评审对象是 change 文档本身），但它实证了 Q1 的紧迫性。

---

## 一、决策登记区

### [需拍板]（设计门勾选）

**Q1 · 运行 checkout 迁移归属 —— 灾难级前置缺口**（A1-P1 / A2-F1·F2 / 用户 session 中亲自指出，三方独立实测确认）

现实：运行 checkout（`~/.skills/laodao-skills` → `laodao-ai/laodao-skills.git`）与开发 checkout（本仓 → `laodao-ai/sdflow-skills.git`）是**历史互不相交的两个 repo**（互相 `git cat-file` 查无对方 commit）。adr/0005 的发布边界 `push→pull→setup` 从设计起点就断裂：canonical 一旦按 tasks 1.1 建链，即**永久冻结在旧仓 b248c2d**，本 change 全部成果无法到达任何消费方（"做完也是死代码"——A2 原话）。change 文档全文无 "sdflow-skills" 字样；此事卡在本 change 与 `extract-sdflow-repo` 之间的真空地带，无人认领。

| 选项 | 内容 | 后果 |
|---|---|---|
| **A（推荐）** | 本 change 新增前置任务：迁移运行 checkout 到 sdflow-skills remote（重 clone 或改 remote + reset），并把"运行 checkout remote = 当前权威 remote"写进 5.1 纪律段与 setup 前置校验提示 | 本 change 自洽可验收；`extract-sdflow-repo` 范围缩小为"拆库收尾"。代价：本 change 范围 +1 个运维任务 |
| B | 归 `extract-sdflow-repo`，本 change 声明其为硬前置并**阻塞等待** | change 边界干净。代价：本 change 完成即闲置，且 extract 尚未 materialize，闲置期不可控 |

> ✅ **拍板（2026-07-03 设计门）**：选 **A**，并细化——运行 checkout 落位 **`~/.skills/sdflow-skills/`**（fresh clone + setup.sh，旧 laodao-skills 保留不删）；另新增 **`sdflow-upgrade`** skill（git pull → setup.sh → 版本/变更展示 → 提示消费仓 update，结构性堵 pull→setup 窗口），已入 tasks §7。

**Q2 · 迁移期显式 pin marker？**（autoplan/Codex 单声部，留人工终审）

ADR 现状 = "留本地规则副本即 pin"（无 marker 文件）。Codex 建议加显式 marker（如 `.workflow-pin`）区分"有意 pin"与"忘了删"。**默认维持 ADR 现状**（副本即声明，少一个状态文件），除非你认为"忘了删 vs 有意留"的区分值得一个 marker——4.2 的陈旧遮蔽告警已把两者都显形，功能上不缺。

> ✅ **拍板（2026-07-03 设计门）**：维持现状，不加 marker。

### [自动决策]（高置信采纳，已回流 amendment，默认接受、可覆盖）

| # | 决策 | 依据 |
|---|---|---|
| D1 | resolver 步① 粒度 = **any-of 即 pin**（三顶层单元任一存在→判本地），部分残留时输出**专门告警**（提示补齐或删净） | A1-P2 / autoplan #5：迁移期必经部分残留态，两种隐式语义各有一种静默失效 |
| D2 | resolver 接口契约先行：`--root`（默认 `git rev-parse --show-toplevel`）、`${SDFLOW_HOME:-$HOME/.sdflow}` env override、退出码表、canonical 命中后最小健全性检查（workflow.md 非空+三单元在）、`--explain` 来源诊断 | autoplan #4·#7 / A1-P3·P4 / A3-F4（override 复用 init.py `CLAUDE_CONFIG_DIR` 先例） |
| D3 | 调用侧 `[ -x ]` 判脚本存在，缺失 = 专属"重跑 setup"文案（与步3"bundle 缺失"降级**区分**，防 pull→setup 窗口期误诊） | autoplan #4·#11 / A2-F3 |
| D4 | 开放问题 4 裁决：告警触发 = **update 内联为主 + opsx-maintain 兜底扫描**；检测范围**含旧版仓内 `hack/checkpoint-commit.sh` 孤儿副本**（对称提示：删=用全局 / 本地 workflow.md 副本仍引用它则勿删） | A3-F5 / A2-F4·F5：双触发点均被动，兜底扫描收窄"常年不 update"敞口 |
| D5 | task 2.3 **只改 assets**（instance 勿手改）；行号引用改锚文本"`[checkpoint]` 约定行"（实测 assets:59/80，"line62"已漂移） | A3-F2 / 接地镜 #3 |
| D6 | 新增 dev dogfood 刷新机制：`opsx-project-init update --dev`（整 bundle 刷本仓 instance），倾向此而非发布前 drift-fail 断言 | A3-F3 / autoplan #3：instance 落后 assets 已是实测事实，同步通道又被 Q1 冻结 |
| D7 | 新增**激活验证任务**：实现完在开发 checkout 跑 `setup.sh` + 真实触发一次评审 skill，确认 resolve-workflow.sh 被真实调用；verify 对此类 ✅ 锚点 = **真实调用输出**（非"文本已改"） | A3-F1：当前拓扑下流水线无法自证，纯文本锚点会造假✅ |
| D8 | 修复部署产物读点缺口：init.py `handle_config` 改读 BUNDLE_SRC（现读消费仓副本，copy_bundle 去规则后必现 FileNotFoundError）；config.template.yaml `@openspec/workflow/...` 引用 + snippets 两文件改全局解析兼容 | autoplan #1·#2（跨模型共识，本 change 最硬的两条实现级缺口） |
| D9 | canonical 建链加**所有权检查**（复用 setup.sh install_into 模式：只接管自属软链/指针，异物停手告警） | autoplan #6 / A2-F8 |
| D10 | 措辞收窄与文档修正：exec 位"根治"限定 git 追踪层（Windows bash 解释器依赖沿现状，入 Non-Goals）；"唯一权威源 5 处"改实核 4 处（CHANGELOG 不存在于本仓）；opsx-ship 从验收范围移出（待其 change 落地后追加读点）；6.1 收窄"只决策落点不实施" | A2-F7 / 接地镜 #1 / A3-F6 / autoplan #13·#16 |

**读点全扫结论（关闭开放问题 3）**：实际规则读点仅 `spec-review/SKILL.md`（3 处）+ `impl-review/SKILL.md`（4 处）；opsx-done / buglist-recorder / todolist-recorder = **0 处**。resolver 改造面比 proposal 预估小（利好）。

### [已裁掉]（反静默压制：连理由归档，设计门可复核）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | CEO 镜："痛点未量化，应降级为 spike"（autoplan 裁） | 动机在 adr/0003 已记（漂移+堆积），机制成本低且可回退；再 spike 是重复决策 |
| X2 | CEO 镜："砍掉 Windows 支持简化"（autoplan 裁） | 双 agent/双平台是 proposal 明载的 stakeholder 约束（TG-20），非可选项 |
| X3 | A2-F5 后半段"用户误删 checkpoint 旧副本致静默失败"独立成险（主审降级，非丢弃） | 前半（孤儿文件+告警盲区）已采进 D4；"误删"链路是推断且被 D4 的对称提示直接覆盖，不再独立计险 |

### 低置信上抛（一行带过，不静默滤除）

- A1-P5：Codex 沙盒/审批档位是否放行读 `~/.sdflow` 未实测 → 并入 D7 激活验证顺带实测一次 Codex 侧。
- A1-P6：Windows 指针文件编码/换行/路径风格 → 已并入 5.3 测试用例（空格/中文/尾随换行）。
- A1-P7 / autoplan #12：全局侧"运行 checkout 长期未 pull"无感知 → 超本 change 范围，记 todolist（T12，hash/日期一次性提示）。

---

## 二、合并 findings 总览（去重后 9 簇）

| 簇 | 来源镜 | 严重度 | 处置 |
|---|---|---|---|
| C1 拓扑断裂：remote 分家、canonical 将钉死旧仓 | A1-P1 / A2-F1·F2 / 用户 | **灾难级** | **Q1 拍板** |
| C2 激活/自证缺失：编辑不生效、假✅ 风险、部分部署窗口 | A3-F1 / A2-F3 / autoplan #11 | 高 | D3·D7（新任务 5.7＋发布纪律句） |
| C3 resolver 契约不完整（粒度/仓根/退出码/健全性/诊断/测试隔离） | autoplan #4·#5·#7 / A1-P2·P3·P4 / A3-F4 | 高 | D1·D2（tasks 3.1 重写） |
| C4 部署产物读点系统性缺口（config/snippets/handle_config） | autoplan #1·#2 | 高 | D8（新任务 2.5/3.4） |
| C5 dogfood/instance 同步断链 | A3-F2·F3 / autoplan #3 / 接地镜 #3 | 中高 | D5·D6（新任务 5.6） |
| C6 运维健壮性（回滚/告警兜底/孤儿/所有权/三副本权威源） | A2-F4·F5·F6·F8 / autoplan #6·#10 | 中高 | D4·D9＋纪律段回滚句（A2-F6） |
| C7 平台与外部 agent 未实测（Codex/Windows） | A1-P5·P6 / A2-F7 / autoplan #15 | 中 | D10＋上抛区 |
| C8 文档失真（5 处约定/行号/opsx-ship/开放问题过时） | 接地镜 #1·#3 / A3-F6 / autoplan #8·#14 | 低 | D5·D10 |
| C9 范围蠕变（6.1 无验收判据） | autoplan #13 | 低 | D10 |

**证伪失败方向**（对抗镜如实申报，佐证机制内核站得住）：dangling symlink 被 `-d` 天然拦截；任务分组顺序无颠倒（缺的是激活步而非排序错）；opsx-done/recorders 读点为 0（自指爆炸半径小于担忧）；多用户 `~/.sdflow` 天然隔离。

## 三、图验证（design-diagrams：只验存在/正确/未过时，不重画）

- TG-12 决策图（design §三）：✓ 存在、经 D1/D2 amendment 后正确。
- TG-14 组件/拓扑图（design §四）：⚠ **已过时**——图中"运行 checkout = ~/.skills/laodao-skills（同 repo 两 clone）"与实测不符（两 remote 分家）。已在 design §四标记过时警示，Q1 拍板后随修。

## 四、回流 amendment 清单（均标 [spec-review-amendment]）

- `tasks.md`：3.1 重写为契约先行；3.2 补 `[ -x ]`/127 文案 + 读点清单钉死；新增 2.5（handle_config）/ 3.4（config+snippets 读点）/ 5.6（update --dev）/ 5.7（激活验证）；2.3 限定 assets+锚文本；4.2 触发点裁决落定；1.1/1.2 加所有权检查；1.3/2.2/6.1 措辞修正；5.2/5.3 加 SDFLOW_HOME 隔离与新用例；顶部加发布纪律句。
- `design.md`：§三补 resolver 契约细则；§四加拓扑图过时警示；§七迁移告警补触发点裁决与孤儿覆盖。
- `specs/spec-workflow/spec.md`：R-MRF-2 补 any-of 粒度 / SDFLOW_HOME / 退出码区分 + 部分残留 Scenario；R-MRF-3 补双触发点与孤儿脚本覆盖。
- `proposal.md`：开放问题 3/4 关闭；Non-Goals 补 Windows 解释器沿现状；Success Metrics 移除 opsx-ship。

## 五、收敛口

**有条件建议进设计门**：amendment 已全部回流；机制内核（分层部署 + resolver 脚本化 + opt-in 迁移）经三面对抗镜未被击穿，被击穿的全是"spec 与现实拓扑的接缝"与"实施时序"，均已收进任务或决策区。**批准前提 = Q1 拍板**（推荐 A：本 change 认领运行 checkout 迁移）+ Q2 确认默认（不加 marker）。Q1 若不决，本 change 实现完即死代码——不建议带着 Q1 未决进阶段三。
