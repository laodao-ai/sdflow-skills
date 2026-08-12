# sdflow-skills

围绕 **OpenSpec 规格驱动流程（spec-driven flow）** 的 Claude Code / Codex 自建 skills 集合，
隶属老刀AI码场自建 skills 体系。提供一条从「铺工作流 → 生成变更 → 设计审 → 代码审 → 收尾归档」
的规格驱动开发（SDD）闭环，外加缺陷 / 待办 / 批次的记录工具。

本仓库同时是这套 spec 工作流 bundle 的 **权威源**（见下方[工作原理](#工作原理)），
既产出工作流资产、又用它管理自身变更（dogfooding）。

> 📖 想系统理解这套体系的**原理、设计思路与实战用法**：见
> [docs/sdflow-guide.html](./docs/sdflow-guide.html)（自包含单文件，浏览器直接打开即可）。

## Quick Start（跑一个变更，从需求到 merge）

```bash
git clone https://github.com/laodao-ai/sdflow-skills.git && cd sdflow-skills && bash setup.sh
```

装完在**你的项目**里，逐条敲（问题模糊先 `opsx:explore`，清晰直接进 `/sdflow-spec`；`/sdflow-spec`
人可直接触发，人示意收敛时模型也会自动 invoke）：

```text
/sdflow-init            # 只做一次：把 spec 工作流 bundle 铺进这个项目
/sdflow-spec            # 阶段一：澄清 → 拷问 → 生成四件套 + decision-memo.md
/clear                  # ↓ 出口序列（G1 的具名例外之一：cache 按模型隔离 + 产/审错档）
                        #   切换到评审档模型
/sdflow-spec-review     # 阶段二：并行多镜设计审 → 一份 spec-review-report.md
                        #   ★ 人在这里过一次报告拍板（全流程唯一人类门）
/sdflow-ship {change}   # 阶段三：实现 → 代码审 → done → merge，一路连续跑
```

阶段一的 project-local schema 由 `sdflow-init` 从 `sdflow-init/assets/schemas/sdflow-spec-driven/`
下发到消费项目。它负责四件套结构、依赖、`skip_specs` 和委派提示；委派只是提示层引流，不能替代
`/sdflow-spec` 的入口规则。CLI 版本门未通过时保持内置 `spec-driven`；迁移必须先补写
在途 change 的 schema，再切换配置。当前不提供 fork 漂移的机械检测或自动 rebase，该边界已记录为
后续 todo。

## Skills 列表

| 分类 | Skill | 说明 |
|------|-------|------|
| 工作流铺设/维护 | `sdflow-init` | 一键把整套 OpenSpec spec 工作流 bundle 铺进任意项目（本仓库是该 bundle 权威源） |
| 工作流铺设/维护 | `sdflow-maintain` | 扫描 openspec 目录状态、对比 INDEX、报告差异并修复 |
| 工作流铺设/维护 | `sdflow-upgrade` | 运行 checkout 一键升级：pull → setup → 版本展示（堵 pull→setup 窗口期） |
| 生成（阶段一） | `sdflow-spec` | 阶段一·产 spec 单一入口：澄清 → 拷问 → 生成三相位一次连续跑，拷问结构性前置于成文；产四件套 + 承重的 `decision-memo.md`（`/clear` 无损）。人可直接触发；人示意收敛（如"开搞"）时模型自动 invoke，但模型不得自主判断"该开 change 了" |
| 评审（主审） | `sdflow-spec-review` | 阶段二·设计审主审：自持广审双镜 + 并行多镜（领域+对抗+接地读码）+ design-voice 跨模型第二意见 → 一份 spec-review-report，供人类门拍板 |
| 评审（主审） | `sdflow-code-review` | 阶段三·代码审主审：并行多镜（领域+对抗+历史）+ 机械引用核 + 二元裁决，能修的自动修 → 一份 code-review-report |
| 编排（阶段三） | `sdflow-ship` | 阶段三编排器：gate 台账（`ship_gate.py`）驱动 实现 → 代码审 → done → merge 一路连续跑 |
| 编排（阶段三） | `sdflow-implement` | tickets 实现管线双模式：出 ticket（tracer-bullet 垂直切片）→ 执行（Blocked-by frontier 受限并行 + 每 ticket 双轴审）；由 /sdflow-ship 按 gate 判定以显式 mode= 参数派发，实现管线唯一 = tickets |
| 收尾 | `sdflow-done` | 闭环：verify（证据锚点）→ hand-off → archive（delta 对码核验同步）→ commit → merge |
| 规划 | `sdflow-architecture` | 系统架构设计编排器：简单需求 → skeleton-ready SAD（openspec/architecture/ 单例）+ 骨架切片建议交棒 |
| 规划 | `sdflow-devenv` | 开发/测试环境副驾：定测试策略（单元/集成/e2e 三层，一层不留白）→ 落脚手架 → 尽可能真跑一遍确认 → 出 `testing-strategy.md` + `environments.md` |
| 规划 | `sdflow-roadmap` | 分阶段 roadmap 规划工作流，直写产出 design/roadmap/task-log 三件套（可选 memo），不经 change 壳 |
| 维护（单仓专用） | `sdflow-upstream-watch` | 追踪四个上游源（gstack / superpowers / matt 套件 / OpenSpec CLI）的 delta，产出人可拍板的三分诊报告；**仅服务本仓（sdflow-skills）自身**，其他项目 cwd 下调用会被机械守卫拒绝 |
| 记录（issues 台账） | `sdflow-issues` | issues 台账单一 skill：bug 池（缺陷记录 + 状态回写 OPEN→VERIFIED→FIXED，B-ID）+ todo 池（改进 / 技术债，T-ID）两池记录，跨池 `issues/INDEX.md` 重建与批次注册表维护，保证 ID 不撞号、总览/详情双写一致 |
| 复盘 | `sdflow-retro` | 只读再生 workflow 成本×价值复盘报告（阶段墙钟×per-镜价值 join），不决策不改动 |

> `sdflow-init`、`sdflow-issues`、`sdflow-retro`、`sdflow-maintain`、`sdflow-implement`、`sdflow-ship`、
> `sdflow-done`、`sdflow-architecture`、`sdflow-devenv` 与 `sdflow-upstream-watch` 为**数据类 skill**
> （带 `scripts/`，多数另有 `tests/`），由脚本保证确定性；其余 5 个
> （`sdflow-spec`、`sdflow-spec-review`、`sdflow-code-review`、`sdflow-roadmap`、`sdflow-upgrade`）
> 为纯 Markdown 编排类。

> **已迁出 skills**：`openspec-upgrade` 与 `embedded-test-sop` 由
> [laodao-skills](https://github.com/laodao-ai/laodao-skills) 维护。更新本仓后运行一次
> `bash setup.sh` 会仅清理仍指向本仓的旧安装项；随后在 laodao-skills 运行
> `bash setup.sh` 完成接管。

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
> | `buglist-recorder` | `sdflow-issues`（bug 池已并入统一台账 skill） |
> | `todolist-recorder` | `sdflow-issues`（todo 池已并入统一台账 skill） |
> | `issues-recorder` | `sdflow-issues` |

## 安装

把仓库 clone 到任意位置（安装用绝对路径 symlink，与仓库存放位置无关），然后运行 `setup.sh`：

```bash
git clone https://github.com/laodao-ai/sdflow-skills.git
cd sdflow-skills
bash setup.sh
```

`setup.sh` 会把每个含 `SKILL.md` 的目录同时装到 **Claude**（`~/.claude/skills/`）和
**Codex**（`~/.codex/skills/`），另铺 `~/.claude/agents/` 下的 agent 定义与 `~/.sdflow/` 下的
全局 canonical workflow + 辅助脚本（四个落点详见下方[工作原理](#工作原理)）。幂等，可反复运行。

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
  `hack/` 不会被当 skill）。共四个落点：
  - `~/.claude/skills/` 与 `~/.codex/skills/` —— 全部 skill；
  - `~/.claude/agents/` —— `sdflow-spec/agents/*.md` 逐文件软链（3 个角色定义 +
    5 个 `sdflow-effort-*` 档位定义）。这是全局命名空间，守卫更严：只接管确认指向本仓的软链；
  - `~/.sdflow/` —— 全局 canonical `workflow`（软链到本仓 `sdflow-init/assets/workflow/`）
    + `hack/` 辅助脚本（**拷贝**而非软链——改 `sdflow-init/assets/hack/` 后必须重跑 `setup.sh`）。
  - **Unix**：绝对路径 symlink —— 改源即时生效，仅新增/删 skill 后才需重跑。
  - **Windows**：复制目录 + 写 `.sdflow-skills` 标记文件用于更新检测（名单内目录的存量 `.laodao-skills` 旧 marker 同样识别为自属并可刷新）。
  - 安全兜底：绝不覆盖非本仓库拥有的同名目录；清理源已删除的孤儿链接。
- **spec 工作流 bundle 的权威源与分发**：`sdflow-init/assets/workflow/` 是这套规则集的**唯一权威源**，
  但规则文件与评审 `tools/` **不进消费仓**——`sdflow-init` 只往消费项目落一份人读手册
  `openspec/workflow/WORKFLOW-GUIDE.md`，评审运行时经 `~/.sdflow/hack/resolve-workflow.sh` 解析到
  全局 canonical `~/.sdflow/workflow/`。因此改权威源后跑一次 `bash setup.sh`（或 `/sdflow-upgrade`）
  即对本机所有消费仓即时生效，无需逐仓 update。
- **dogfooding**：仓库根的 `openspec/`（`changes/specs/issues/config.yaml`）是本仓库自身
  跑这套 OpenSpec 流程的实例；变更走 propose → 设计审 → 代码审 → `sdflow-done` 归档。

### Recorder 存储契约

`sdflow-issues` 的 bug/todo 两池共用**单文件模型**：一个 issue 一个 `.md` 文件（YAML frontmatter 为
唯一权威数据源，12 个扁平字段；body 为自由格式 Markdown，脚本只追加状态变更历史、不反解析）；
`open/` / `closed/` 两目录按终态分层，`INDEX.md` / `CLOSED.md` 是 `reindex` 再生的派生物。并发安全靠
文件名级 `O_CREAT|O_EXCL`（新建同 ID 时后到者 `FileExistsError` 自动重试），不需要仓级快照锁——单一
入口 `issues_v2.py` 详见 `sdflow-issues/SKILL.md`。零依赖 YAML 子集写读（沿用
`openspec/adr/0025-recorder-versioned-frontmatter-overlay-and-snapshot-lock.md` 的零依赖原则，不引入
PyYAML；该 ADR 记录的 overlay/snapshot-lock 架构本身已随本次单文件模型改造替换）。

## 开发

数据类 skill 的测试自包含在各自 `tests/` 下，用 pytest 运行：

```bash
pytest                                                       # 全部
pytest sdflow-issues/tests/                                 # 单个 skill
pytest sdflow-issues/tests/test_issues_v2.py::test_xxx -v   # 单个用例
```

面向 AI 协作者的项目级指令见 [CLAUDE.md](./CLAUDE.md) / [AGENTS.md](./AGENTS.md)。

## 许可

MIT
