## MODIFIED Requirements

### Requirement: 触发分工与互相指路（生态路由）〔grill-amendment〕

本 skill 的 description SHALL 聚焦架构词面（架构设计 / 子系统划分 / contract / SAD）并含与 sdflow-roadmap 的分工指路句（本 skill 管空间轴，时间轴规划指向 sdflow-roadmap）；`sdflow-roadmap/SKILL.md` 的 description SHALL 增加一句指路：「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」——消解两 skill 在「新项目起步」入口的现役触发冲突（roadmap 侧 delta 见 `specs/roadmap-planning/spec.md`〔spec-review-amendment〕）。两侧指路句均 SHALL 注明前置条件（消费仓需已 `sdflow-init`）——防绿地新项目被路由后首触即 preflight 拒绝的体验断崖〔spec-review-amendment〕。

**过程轴下游指路（本 change 新增）**：本 skill 的 description SHALL 增加**过程轴分流句**——「建 dev/test 环境 / 定测试策略 → `/sdflow-devenv`」，与既有的时间轴分流句（→ `sdflow-roadmap`）并列，使三轴路由在 description 层完整（空间轴=本 skill · 时间轴=roadmap · 过程轴=devenv）。

**交棒话术改写（本 change 新增）**：skeleton-ready 交棒时的「过程轴文档指路」SHALL 从**「指出不代写 + 给模板路径」**改为**指向下游 skill `/sdflow-devenv`**——过程轴此前无下游、只能给锚与模板路径；`sdflow-devenv` 落地后该空缺已填补，继续只给模板路径会把操作者留在手搓状态。改写后 SHALL 保留「本 skill 不代写过程轴文档」的边界（architecture 仍是**指路者**，MUST NOT 代写 environments/testing-strategy，亦 MUST NOT 将其内容写进 SAD——违 `quality-criteria.md` 边界总则），并 SHALL 继续给出可投影的 SAD 锚（工具链锚=§2 约束 · **依赖形态锚=§3 外边界** · 集成测试点锚=§5 contract · 部署锚=§7 · 配置项锚=§8），供下游 skill 消费。

#### Scenario: 两侧 description 均含分工指路
- **WHEN** 检查两个 skill 的 SKILL.md description 文本
- **THEN** sdflow-architecture 侧含「时间轴规划 → sdflow-roadmap」指路句，sdflow-roadmap 侧含「尚无 SAD 先 /sdflow-architecture」指路句

#### Scenario: description 含过程轴分流句
- **WHEN** 检查 `sdflow-architecture/SKILL.md` 的 description 文本
- **THEN** 其中含「建 dev/test 环境 / 定测试策略 → /sdflow-devenv」分流句，与时间轴分流句并列

#### Scenario: 交棒指向下游 skill 而非模板路径
- **WHEN** SAD 升为 skeleton-ready 并输出过程轴文档指路
- **THEN** 指路内容指向 `/sdflow-devenv`（含前置说明），而非仅给出模板文件路径让操作者自行手搓

#### Scenario: 交棒仍不代写过程轴文档
- **WHEN** SAD 升为 skeleton-ready
- **THEN** skill 给出可投影的 SAD 锚（§2/§3/§5/§7/§8）并指向下游 skill，但 MUST NOT 代写 environments.md 或 testing-strategy.md，亦 MUST NOT 将其内容写入 SAD
