# sdflow-skills

围绕 **OpenSpec 规格驱动流程（spec-driven flow）** 的 Claude Code / Codex 自建 skills 集合，
隶属老刀AI码场自建 skills 体系。提供一条从「铺工作流 → 生成变更 → 设计审 → 代码审 → 收尾归档」
的规格驱动开发（SDD）闭环，外加缺陷 / 待办 / 批次的记录工具与嵌入式测试 SOP 生成。

本仓库同时是这套 spec 工作流 bundle 的 **权威源**（见下方[工作原理](#工作原理)），
既产出工作流资产、又用它管理自身变更（dogfooding）。

## Skills 列表

| 分类 | Skill | 说明 |
|------|-------|------|
| 工作流铺设/维护 | `sdflow-init` | 一键把整套 OpenSpec spec 工作流 bundle 铺进任意项目（本仓库是该 bundle 权威源） |
| 工作流铺设/维护 | `sdflow-maintain` | 扫描 openspec 目录状态、对比 INDEX、报告差异并修复 |
| 工作流铺设/维护 | `openspec-upgrade` | 升级 openspec CLI（`@fission-ai/openspec`）并刷新项目内 openspec skills |
| 工作流铺设/维护 | `sdflow-upgrade` | 运行 checkout 一键升级：pull → setup → 版本展示（堵 pull→setup 窗口期） |
| 评审（主审） | `sdflow-spec-review` | 阶段二·设计审主审：并行多镜（领域+对抗+接地读码）→ 一份 spec-review-report |
| 评审（主审） | `sdflow-code-review` | 阶段三·代码审主审：并行多镜 + 对抗裁决 + 置信过滤 → 一份 code-review-report |
| 编排（阶段三） | `sdflow-ship` | 阶段三编排器：gate 台账驱动 5.5→9 到 merge 建议 |
| 编排（阶段三） | `sdflow-implement` | tickets 实现管线双模式：出 ticket（tracer-bullet 垂直切片）→ 执行（frontier 串行+每 ticket 双轴审）；由 /sdflow-ship 按 config 键/plan marker 条件路由 |
| 收尾 | `sdflow-done` | 闭环：verify（证据锚点）→ hand-off → archive（delta 对码核验同步）→ commit → merge |
| 规划 | `sdflow-roadmap` | 分阶段 roadmap 规划工作流，产出 requirements/design/roadmap/task-log 四件套 |
| 记录（issues 池） | `sdflow-buglist` | 缺陷记录 + 状态回写（OPEN→VERIFIED→FIXED），保证 ID 不撞号、总览/详情双写一致 |
| 记录（issues 池） | `sdflow-todolist` | 改进想法 / 技术债收集池（非缺陷），全局唯一 T-ID |
| 记录（issues 池） | `sdflow-issues` | 跨 buglist+todolist 的 `issues/INDEX.md` 重建与批次注册表维护 |
| 复盘 | `sdflow-retro` | 只读再生 workflow 成本×价值复盘报告（阶段墙钟×per-镜价值 join），不决策不改动 |
| 测试 | `embedded-test-sop` | 为嵌入式固件功能生成手动测试 SOP + 配套日志自动分析规则（log-checks.yaml） |

> 三个 recorder、`sdflow-retro`、`sdflow-init`、`sdflow-maintain` 与 `sdflow-implement` 为**数据类 skill**（带 `scripts/` + `tests/`），
> 由脚本保证确定性；其余（含 `sdflow-roadmap`）为纯 Markdown 编排类。

> **曾用名对照**（改名于 `sdflow-rebrand`，历史 PR / issue / 本地记忆若引用旧名，按此表换算）：
>
> | 旧名 | 新名 |
> |------|------|
> | `opsx-project-init` | `sdflow-init` |
> | `opsx-done` | `sdflow-done` |
> | `opsx-maintain` | `sdflow-maintain` |
> | `opsx-roadmap-planner` | `sdflow-roadmap` |
> | `spec-review` | `sdflow-spec-review` |
> | `impl-review` | `sdflow-code-review` |
> | `buglist-recorder` | `sdflow-buglist` |
> | `todolist-recorder` | `sdflow-todolist` |
> | `issues-recorder` | `sdflow-issues` |

## 安装

把仓库 clone 到任意位置（安装用绝对路径 symlink，与仓库存放位置无关），然后运行 `setup.sh`：

```bash
git clone https://github.com/laodao-ai/sdflow-skills.git
cd sdflow-skills
bash setup.sh
```

`setup.sh` 会把每个含 `SKILL.md` 的目录同时装到 **Claude**（`~/.claude/skills/`）和
**Codex**（`~/.codex/skills/`）。幂等，可反复运行。

## 更新

```bash
cd sdflow-skills
git pull
bash setup.sh
```

`setup.sh`（含 `/sdflow-upgrade`）现也触发退役 hook 自愈——升级工具链即清理存量死 hook（`change-review-stub.py`），不必等某项目跑 `sdflow-init update`。

## 工作原理

- **每个 skill 是一个自包含目录**：`SKILL.md`（frontmatter + 指令，唯一被 `setup.sh` 识别的标志）
  + 可选 `scripts/`（Python/Shell）+ `tests/`（pytest）+ `assets/` / `references/`。
- **安装机制**：`setup.sh` 遍历仓库根下所有目录，仅安装含 `SKILL.md` 的（故 `openspec/`、`docs/`、
  `hack/` 不会被当 skill）。
  - **Unix**：绝对路径 symlink —— 改源即时生效，仅新增/删 skill 后才需重跑。
  - **Windows**：复制目录 + 写 `.sdflow-skills` 标记文件用于更新检测（名单内目录的存量 `.laodao-skills` 旧 marker 同样识别为自属并可刷新）。
  - 安全兜底：绝不覆盖非本仓库拥有的同名目录；清理源已删除的孤儿链接。
- **spec 工作流 bundle 的权威源**：`sdflow-init/assets/workflow/` 是铺给其他项目的
  `openspec/workflow/` 的**唯一来源**。改动这套规则集，一律**先改 assets、再用 `sdflow-init update`
  推到下游**，禁止只改某个下游项目的 `openspec/workflow/` 后忘记回灌。
- **dogfooding**：仓库根的 `openspec/`（`workflow/` 规则 + `changes/specs/issues/config.yaml`）
  是本仓库自身跑这套 OpenSpec 流程的实例；变更走 propose → 设计审 → 代码审 → `sdflow-done` 归档。

## 开发

数据类 skill 的测试自包含在各自 `tests/` 下，用 pytest 运行：

```bash
pytest                                                       # 全部
pytest sdflow-buglist/tests/                                # 单个 skill
pytest sdflow-buglist/tests/test_buglist.py::test_xxx -v    # 单个用例
```

面向 AI 协作者的项目级指令见 [CLAUDE.md](./CLAUDE.md) / [AGENTS.md](./AGENTS.md)。

## 许可

MIT
