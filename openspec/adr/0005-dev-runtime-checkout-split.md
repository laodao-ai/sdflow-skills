# 开发/运行 checkout 分离：toolkit 自身 dev/release 靠两个物理 clone

laodao-skills 既是 workflow 规则的源、又要 dogfood 自己（用自己的 workflow 开发自己）。若**单一 checkout** 同时承担"编辑规则"和"用规则"，dev/release 缠在一起：`setup` 从半成品仓装、dogfood 会吃到未发布编辑、`openspec/` 开发过程与"作为规则源"互扰。改为**两个物理 clone 分角色**（grill 2026-07-03，读法 X）。

- **开发 checkout**（独立目录的 clone）：编辑 skill / bundle、跑 workflow dogfood 自己；留本地 `openspec/workflow/`（WIP），resolver **local-first** 命中、吃自己**尚未发布**的规则编辑。
- **运行 checkout**（`~/.skills/laodao-skills`）：只 `git pull` 已完成的 skill 并 `setup` 安装；充当全局 **canonical 解析锚点**（`setup` 在此写 `~/.sdflow/` 软链/指针，见 `adr/0003` grill-amendment）；只含**已发布**内容，自己**不** run workflow on 自己。
- **发布边界** = push（开发）→ pull（运行）→ setup。不靠 resolver 逻辑绕，靠 checkout **物理边界**隔。

**明确接受的代价**：改 **skill 本身**（非规则）需在开发 checkout 跑一次 `setup` 才 dogfood 得到（临时把 skills/canonical 指向 dev）；本机开发时 canonical 指 dev 无碍——本机**无外部消费者**（外部消费者在各自机器的运行 checkout）。改**规则**（workflow.md / checklists）则 local-first 自动 dogfood，无需 setup。

## Considered Options

- **两 checkout 分角色（选中）**：dev/release 物理隔；resolver 的 local-first 步天然服务开发 checkout；`openspec/` 在运行 checkout 惰性无害。代价 = 改 skill 要 setup-from-dev。
- **单 checkout + 分支/gitignore 隔 dev-openspec**：一个目录两用；缠、易误从半成品装、dogfood 吃未发布编辑。未选。
- **拆两个 repo（源 repo + 精简发布 repo）**：`~/.skills` clone 发布 repo（无 openspec/changes）。破 openspec 天条"spec 随码" + 造 publish 管线 + 维护两 remote。评估过重，未选。

## Consequences

- resolver（见 `adr/0003`）的 **local-first 步正牌用户 = 开发 checkout**（+ 消费仓显式 pin）；运行 checkout 根本不 run workflow on 自己，故无"源仓吃未发布编辑"之虞。
- **canonical 锚点 = 运行 checkout**；`setup` 应在运行 checkout 跑（发布态）。开发 checkout 跑 `setup` = 知情地临时切到 dev 测 skill 编辑。
- **与 `minimize-repo-footprint` / `adr/0003` 的关系**：本 ADR 定 toolkit **自身** dev/release 拓扑；0003 定**消费仓**部署 footprint。0003 的 resolver local-first 存在，正为本 ADR 的开发 checkout（与消费仓 pin）服务。
- **"移走 openspec"= 移走开发活动，非移文件**（读法 X）：`openspec/` 在运行 checkout 物理存在但 inert——`setup` 只认带 `SKILL.md` 的目录、canonical 只认 bundle 路径，都不碰 `openspec/`。
