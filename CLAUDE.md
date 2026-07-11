# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

一个 **Claude Code + Codex 自建 Skills 集合仓库**（源项目 laodao-skills，本仓库建为 sdflow-skills）。
根目录下每个含 `SKILL.md` 的目录就是一个可安装的 skill；`setup.sh` 把它们装进两个 agent 运行时。
内容以 Markdown 为主（skill 指令 + OpenSpec 工作流规则），少数「数据类」skill 附带 Python 脚本 + pytest 测试。

## 常用命令

### 安装 / 更新 skills（本仓库的构建入口）

```bash
bash setup.sh
```

把每个含 `SKILL.md` 的顶层目录同时装到 `~/.claude/skills/` 和 `~/.codex/skills/`。
Unix 用**绝对路径 symlink**（改源即时生效，无需重装）；Windows 用 copy + `.sdflow-skills` marker（名单内目录的存量 `.laodao-skills` 旧 marker 仍识别为自属）。
幂等，可反复运行。改动 skill 源码后一般无需重跑（symlink 场景）；仅在**新增/删除**顶层 skill 后重跑，
以建立新链接、清理源已删除的孤儿链接。**改 `sdflow-init/assets/hack/` 下脚本后也必须重跑 `setup.sh`**
（它们拷贝进 `~/.sdflow/hack/`，非 symlink，不重跑 = 新 SKILL 调旧脚本）。

### 运行测试

没有根级 pytest 配置——测试各 skill **自包含**在 `<skill>/tests/`，用 pytest 直接跑：

```bash
pytest                                                  # 发现并运行全部 test_*.py
pytest sdflow-buglist/tests/                            # 单个 skill
pytest sdflow-buglist/tests/test_buglist.py::test_xxx -v     # 单个用例
```

带脚本+测试的 skill 仅这几个：`sdflow-buglist`、`sdflow-todolist`、`sdflow-issues`、
`sdflow-init`、`sdflow-retro`、`sdflow-maintain`。其余为纯 Markdown 编排类，无自动化测试。

## 架构

### Skill 目录约定

每个 skill 是自包含目录：

- **`SKILL.md`**（必需）— frontmatter（`name` / `description`）+ 指令主体。**唯一被 `setup.sh` 识别为 skill 的标志**；
  `description` 决定触发，改它要顾及触发精度。
- **`scripts/`**（数据类才有）— 确定性 Python 脚本。设计取向是「机械活交脚本、模型只做判断」：
  脚本 owns 某类文件的读写与一致性（ID 不撞号、总览表与详细块双写一致等），别把不变量判断塞回模型。
- **`tests/`** — 脚本的 pytest 测试。改 `scripts/` 必须同步跑对应 `tests/`。
- **`assets/` / `references/`** — 模版与参考资料。

### 两类 skill

1. **编排类（纯 Markdown）**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done` /
   `sdflow-roadmap` / `embedded-test-sop` / `openspec-upgrade` — 靠 SKILL.md 指令驱动主 session 调度子代理，无脚本。
2. **数据类（Markdown + Python）**：`sdflow-buglist` / `sdflow-todolist` / `sdflow-issues` / `sdflow-init` /
   `sdflow-retro` / `sdflow-maintain` — 由 `scripts/` 保证确定性，SKILL.md 负责判断与编排。

### `setup.sh` 安装机制（核心，改动需谨慎）

- 遍历 `REPO_DIR/*/`，**仅含 `SKILL.md` 的目录才安装** → `openspec/`、`docs/`、`hack/` 不会被当 skill。
- 安全兜底：**绝不覆盖非本仓库拥有的同名目录**（只处理自己的 symlink / `.sdflow-skills` marker copy，名单内目录的存量 `.laodao-skills` 旧 marker 同样识别为自属）；
  清理源已删除的孤儿链接（用 `-e` 解析检查，保留有效链接）。
- 读 `REPO_DIR/VERSION` 显示版本（如 `v0.9.0`）。

### OpenSpec 的双重角色（`openspec/`）

本仓库既**产出** OpenSpec 工作流资产、又**用**它管理自身变更（dogfooding）：

- **`sdflow-init/assets/workflow/`** 是这套 spec 工作流 bundle 的**唯一权威源**——铺给其他项目的
  `openspec/workflow/` 都源于此。改规则**先改 assets、再 `sdflow-init update` 推下游**，
  禁止只改某个下游项目的 `openspec/workflow/` 后忘记回灌。
- **`openspec/workflow/`**（仓库根）— **只保留 `tools/`**（review 工具机械，`sdflow-init update` 托管刷新）；
  规则**不在仓内存副本**——`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done` 运行时经
  `~/.sdflow/hack/resolve-workflow.sh` 解析到全局 canonical `~/.sdflow/workflow/`（由 setup.sh
  软链至运行 checkout 的 `sdflow-init/assets/workflow/`）。勿把规则文件重新拷回仓内（会形成 pin 遮蔽全局）。
- **`openspec/{changes,specs,issues,config.yaml}`** — 本仓库自身的 OpenSpec 变更管理，
  流程走 propose → review → done → archive，强制规范见文末托管区块。
- **`openspec/roadmaps/{name}/`** — 项目级 roadmap 文档包（长期真相源，`sdflow-roadmap` 铺设）：
  design/roadmap/task-log 三件套 + 可选 memo，直写落盘、不经 `plan-{topic}` change 壳；比单次 change
  更大的层级，统摄多阶段规划（每阶段 → 一次未来 change）。roadmap 类 wayfinding 落
  `openspec/roadmaps/{name}/footage/`（长讨论考古层；三件套不引用）。现有 `workflow-cost-optimization`
  （评审工作流成本优化三腿四阶段）、`mechanical-layer-hardening`（adr/0006 机械层固化：脚本化 +
  去字符串化两腿六阶段）沿用存量四件套格式（迁移受控延后，Q-C）。
- **`.claude/skills/openspec-*` 与 `.codex/skills/openspec-*`** — openspec CLI（`@fission-ai/openspec`）
  init 时生成的官方 change-workflow skills，随仓库提交，**非本仓库维护的源**，勿在此手改。
- **`openspec/retro/report.md`** — `sdflow-retro` 只读再生的全 change 成本×价值复盘活文档
  （阶段墙钟 join per-镜 lens-metric 锚，只呈现不决策），随仓库提交（tracked，view-only，
  跑 `python3 sdflow-retro/scripts/retro_report.py --root .` 再生覆盖，勿手改）。

### `hack/`

- `checkpoint-commit.sh` — **旧版仓内副本**（checkpoint 已全局化：真相源 = `sdflow-init/assets/hack/checkpoint-commit.sh`，
  由 setup.sh 装到 `~/.sdflow/hack/`，运行时一律调全局路径）。本仓已无规则副本，此文件可删。

### dev/runtime checkout 纪律（adr/0005 + 设计门拍板）

- **运行 checkout** = `~/.skills/sdflow-skills`：只 `git pull` + `setup.sh`，日常一键用 `/sdflow-upgrade`；
  remote 必须 = `laodao-ai/sdflow-skills.git`。
- **开发 checkout** = 本仓：编辑 skill / bundle。本仓不再保留规则副本（规则经全局 canonical 解析），
  故改 **skill、assets/workflow 规则或 assets/hack/ 脚本**都须在开发 checkout 跑一次 `setup.sh`
  才测得到——知情临时指 dev，测完/合并后在运行 checkout 重跑 setup 还原。
- **发布边界** = push（开发）→ pull（运行）→ **立即** setup（pull 与 setup 之间是"新 SKILL 调旧脚本"的窗口期）。
- **反向窗口**：pull 后既有 SKILL 路由（如 ship 链序）即生效（symlink 即时），而新增 skill 的链接须 setup 后才存在——已开 `impl-pipeline: tickets` 的仓在窗口期触发 RUN_PLAN 会调不存在的 sdflow-implement；故 pull 与 setup 之间勿跑阶段三。
- **回滚** = 运行 checkout `git checkout <上一已知良好 commit>` + 重跑 setup.sh。

## 修改本仓库的注意

- 新增/删除顶层 skill 后：更新 README「Skills 列表」保持一致，并重跑 `setup.sh` 建链接 / 清孤儿。
- 数据类 skill 改 `scripts/` → 必跑 `tests/`；纯 Markdown skill 改的是指令与触发。
- 审查顺序（下方托管区块有强制规范）不可颠倒：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。

## 设计/分析基准原则（一致性机械化优先 + 目标态导向）

评估任何设计/change（尤其 grill、spec-review、决策收敛）**一律以此为基准**：

1. **一致性机械化优先**：能用「可固化规则 + 脚本」确定性保证的一致性，**优先机械化**（承 adr/0006(b)「凡机械 prose MUST 脚本化」）；只有**机械真够不着的残余**（无确定性信号者，如「命中哪些 TG」「declared 是否真命中集」，adr/0018）才退到语义规则（模型判断 + 人读注记 + git 审计）。诚实边界 = 合法的残余划分，**不是弱点、不是妥协**。机械/语义切分线判据见 [[mechanical-judgment-split-signal-criterion]]（有无确定性信号）。
2. **目标态导向，不拿现状反驳目标**：开发阶段以**最终目标态**为准。**MUST NOT** 用「现状语料/存量里这种情况很少/没出现」论证「目标不该做 / 该缩水」——迁移中「旧数据还没新形态」是必然，拿它当风险基线会把「目标态才暴露的面」误判为「不存在」，是拿现状给目标松绑。评估问「目标态 producer 会/不会产出该形态」，而非「现存文件里有没有」。见 [[target-state-not-current-snapshot]]。
3. **面治优先于点补**：机械化时把同片一致性面**一次扫全**（spec 已 MUST 却无机械守的漏网格一并补），而非只补当场被点穿的一处，见 [[point-vs-surface-fix]]。
4. **拆分标准 = 一个 change 一个完整阶段结果**（roadmap/change/task 通用）：scope 按「一个完整内聚交付物」定，**不按同批来源/顺手/凑票数**；别把一件事拆散跨多 change、别混不相干功能。执行中撞到**与本次功能相关的 bug/todo → 立即 fold 做掉**（不 defer、不另开）；**唯一合理 defer = 依赖的模块尚不存在 → 留占位 + 记 todo**（非"这条边角现在少见所以妥协"）。**碎片化是"反复对现状提疑问 + 给妥协方案（WARN/grace/flag）"的根因**——一次做完整、锚目标态 fail-closed，这些疑问根本不产生。见 [[change-scope-one-complete-stage-result]] + [[change-fold-vs-defer-cycle-cost]]（一体两面）。

> 反面教训（本条成因）：grill mlh-p4-validators-hardening 时，我曾用「corpus 显示多数 hr-tg 锚是手写 evidence=、无 declared」论证「T136 重算覆盖薄、可不做」——被用户当场纠正为违反本基准（拿现状反驳目标）。正解 = 锚目标态（所有锚走脚本必有 declared=），M1–M4 全机械化，S1（declared 正确性）才留语义。

## 本仓库自身的 OpenSpec 工作流规范

下方为 `sdflow-init` 铺设、`sdflow-maintain` 维护的托管区块（**勿手改区块内部**），
是本仓库做变更时的强制流程，也是上文提到的规则真相源：

<!-- opsx-init:start —— 由 sdflow-init 维护，勿手改本区块 -->
## OpenSpec 工作流（sdflow-init 铺设）

端到端流程见 workflow 规则集 `workflow.md`（真相源；本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。规则集在 `openspec/workflow/`：
`trigger-catalog.md`（触发单一源 TG）· `spec-checklists/`、`code-checklists/`（设计审/代码审）·
`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
质量分层与升级安全见 `openspec/workflow/reference/quality-layering.md`（本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。

**强制操作规范**

- **起手判触发**：收到 `opsx:ff` / `propose` / `explore`，先按 `trigger-catalog.md` 的 TG 判命中，
  据此激活对应的生成约束 / 领域清单 / 画图 / 模版必填槽（深度由触发决定，不分 S/M/L）。
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。
  子 agent 调度期间（subagent-driven-development / sdflow-implement / sdflow-spec-review / sdflow-code-review 运行中）禁 `/clear`。
- **ff 开分支**：`opsx:ff` 若不在 feature 分支，先 `git checkout -b feat/{change}`（FF-0）。
- **INDEX 同步**（仅规则副本 pin 仓/toolkit 源仓适用）：新增/删 `openspec/workflow/` 规则后，同步 `openspec/INDEX.md`。

**配套 skill（workflow 依赖，需先安装）** — 均来自 sdflow-skills（`bash ~/.skills/sdflow-skills/setup.sh` 装到 Claude+Codex）：

| skill | 在流程中的角色 |
|---|---|
| `/sdflow-spec-review` | 设计审**主审**——并行多镜，按 `spec-checklists/domains` + 对抗 + 接地读码 |
| `/sdflow-code-review` | 代码审**主审**——并行多镜，按 `code-checklists/domains` + 对抗 + 置信过滤 |
| `/sdflow-done` | **闭环**——verify → archive（delta 对码核验同步）→ commit → merge |

> 另有两个记录类配套 skill（按需）：`/sdflow-buglist`（缺陷）、`/sdflow-todolist`（改进收集池），
> 同样来自 sdflow-skills，写入 `openspec/issues/buglist|todolist/`。
<!-- opsx-init:end -->
## Agent skills

### Issue tracker

工作项使用本地 Markdown，存放在 `openspec/matt/<feature>/`；外部 PR 不作为 triage 输入。详见 `openspec/matt/issue-tracker.md`。roadmap 类 wayfinding effort 的落盘根为 `openspec/roadmaps/{name}/footage/`（条件分流详见 tracker doc）。

### Triage labels

使用默认的五种 triage 标签：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`。详见 `openspec/matt/triage-labels.md`。

### Domain docs

单一上下文布局：`openspec/CONTEXT.md` 与 `openspec/adr/`。详见 `openspec/matt/domain.md`。
