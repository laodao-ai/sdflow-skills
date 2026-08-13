# Design · add-frontend-checklists

## Context

动机见 `proposal.md - Why`。现状与约束：

- spec 侧 `frontend.md` 现有 FE-01~05（交互状态 + 视觉品味），形制 = `extends: base` 头注 + 单表（ID/规则/触发条件/检查点）+ 尾注；code 侧无 frontend domain。
- 两侧 README 各有：架构图、选用规则（TG 映射）、ID 约定表、领域注册表；扩展约定五步（「只写本层新增、extends 声明父层、每条给触发条件/检查点/防什么失效、注册表登记、不改 base/父层」）**仅 spec 侧 README 成节（`README.md:82-88`）——code 侧 README 现无该节**（注册表后即尾注，68 行），随本 change task 2.3 补齐 [spec-review-amendment：原句「两侧各有扩展约定」经实读证伪，voice 发现]。
- `trigger-catalog.md` TG-03 领域列现为 `frontend`；分层链既有记法 = `backend`(+`backend-go`)。
- 条目内容 = 已拍板 26 条（`decision-memo.md` + `research/absorption-candidates.md`，含逐条检查点全文与来源）。

## Goals / Non-Goals

**Goals（设计级）**：4 文件形制与既有逐点一致；接线面一次收全（承重约束 4 的消费面清单）；备选内容不进部署面。
**Non-Goals**：见 proposal；另加设计级边界——不为 checklist 内容建任何机械校验（domain 文件无脚本/测试面，与既有 domains 一致）。

## Decisions

决策纪要见 `decision-memo.md`（承重约束 7 条 + 拍板决策 8 条）。以下为设计级技术选择：

| # | 决策 | 选择 | 理由（为何不是另一个） |
|---|---|---|---|
| D1 | React 条目放哪 | 独立 `frontend-react.md` delta 层，不并入 `frontend.md` | 沿 base+delta 架构（backend→backend-go 先例）；非 React 前端项目（Vue/原生）不被 React 噪音稀释——README 选用规则「不涉及的领域不要叠」的前提是领域可分层。[spec-review-amendment 主次判定：三镜中**用户镜**（清单消费者=评审镜与非 React 项目读者，不被无关条目稀释）主导；系统镜代价=多一个文件与一行注册（近零）；开发循环镜=沿先例零新心智 |
| D2 | ID 前缀 | spec 侧 `REACT-`、code 侧 `CR-REACT-` | 沿 `GO-`/`CR-GO-` 先例（子层用栈短名，不用 `FE-R-` 复合式）；`REACT-`/`CR-REACT-` 经 grep 确认未被占用 |
| D3 | specs 处理 | `skip_specs: true` | 见 proposal Capabilities：spec 层不枚举 domain 文件，devex 先例同构 |
| D4 | B6 归属 | 独立成条 CR-FE-06（人拍板），检查点内注「CR-04 的前端特化」 | 前端泄漏形态（window listener/observer × SPA 无整页刷新）足够特化；code-frontend 是新文件不占旧号 |
| D5 | 机械层前置注记 | 文件头 blockquote 一行，不逐条内注 | 一处声明管全文件；逐条注会把「lint 边界」复述 N 遍（漂移面 ×N） |
| D6 | [仅RSC] 标记 | 条目规则名后缀 `[仅RSC]` + 触发条件列写「项目实际启用 React Server Components（如 Next.js App Router / 显式 RSC 配置）——非仅『使用支持 RSC 的框架』或仅 SSR/Pages Router」[spec-review-amendment 措辞细化，防对 Pages Router 项目误触发 / 对 App Router 项目按框架名漏判] | 触发条件列是既有语义位；仅名称标记不带条件会让选用者无判据 |
| D7 | 备选文档位置 | `openspec/changes/<name>/research/`，**不进** `assets/workflow/` | assets 是部署面权威源——放那里会把未采纳内容铺进全局 canonical 广播给所有消费仓；change 附件归档随行、留痕不部署。[spec-review-amendment 主次判定：**系统镜**主导（部署面纯净性不可回退地广播，错放代价 = 全消费仓吃到未采纳内容）；用户镜/开发循环镜代价≈0（查阅路径仅多一跳） |

## 结构与接线图

```
sdflow-init/assets/workflow/
├── trigger-catalog.md          [改] TG-03: `frontend`(+`frontend-react`)
├── checklists-guide.html       [改] 覆盖表失鲜修正（P1）
├── spec-checklists/
│   ├── README.md               [改] 架构图 + ID 表(REACT-) + 注册表 +1 行
│   └── domains/
│       ├── frontend.md         [改] +FE-06~13（8 条）+ 机械层前置注记
│       └── frontend-react.md   [新] REACT-01~03 · extends frontend
└── code-checklists/
    ├── README.md               [改] 架构图 + 选用规则 L33 接实 + ID 表 + 注册表 +2 行
    └── domains/
        ├── frontend.md         [新] CR-FE-01~08 · extends base
        └── frontend-react.md   [新] CR-REACT-01~07 · extends frontend

openspec/INDEX.md               [改] L23-24 括注（P1）
openspec/changes/add-frontend-checklists/research/   [新] 候选表+备选冻结区（不部署）

[spec-review-amendment] 评审补入的接线面：
├── code-checklists/domains/backend.md   [改] L11 CR-BE-02 IOU 句 → 交叉引用 CR-FE-01
├── sdflow-spec-review/SKILL.md          [改] L223 栈枚举 +frontend-react
├── sdflow-init/SKILL.md                 [改] L195 栈枚举 +frontend-react
├── sdflow-init/assets/workflow/config.template.yaml  [改] L24 栈枚举 +frontend-react
└── code-checklists/README.md            [改] 追加「如何新增一个领域（扩展约定）」节（复制 spec 侧五步、改 ID 示例——该侧原无此节）
```

选用链（目标态）：命中 TG-03 → spec 审读 `base+frontend(+frontend-react)`；code 审读 `code-review-base+frontend(+frontend-react)`；react delta 叠加条件 = 变更实际涉及 React 栈（同 backend-go 语义）。

## Risks / Trade-offs

- [26 条一次落盘，个别检查点措辞失真（尤其 8 条〔未核实〕）] → 落盘时逐条对照 `research/absorption-candidates.md` 原文；阶段二 spec-review 领域镜按候选表核对；单条措辞可低成本 amend（非难逆转）。
- [checklists-guide.html 手工编辑破坏页面结构/导航] → 只动覆盖相关表格与文案区块，不动脚本与样式；改后做标签配对与目录锚点自检。
- [frontend.md 增至 13 条后表格变长，偏离既有 15-25 行文件形制] → 13 行表 + 头尾注 ≈ 24 行，仍在带内；不拆表。

## Migration Plan

无部署动作：`assets/workflow/` 即权威源，改动随常规 push → 运行 checkout `git pull` + `setup.sh`（canonical 为 symlink，规则即时生效）；消费仓无规则副本（adr/0039 后），无需逐仓 update。回滚 = `git revert` 本 change 提交（纯 Markdown，无状态迁移）。

## Compliance

遵守：README 扩展约定四步（纯增量、不改 base/父层）；ID 不复用不重排（README:53）；DOC-1 正文即最终态（新条目不带演进史）；premise-verification（承重约束逐条带锚，见 decision-memo）。无豁免项。

## Open Questions

无。
