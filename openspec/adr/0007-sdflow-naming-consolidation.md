# sdflow 品牌收拢：全量 sdflow- 前缀改名 + 三保留名单

本仓 12 个 skill 的命名此前是三个时代的地层堆积：`opsx-*` 家族与官方 `opsx:*` CLI 只差一个标点（长期混淆源）、`spec-review`/`impl-review` 是裸通用词（撞名风险最高且不表归属）、品牌字符串仍是 laodao 遗产（`setup.sh` 输出 `laodao-skills vunknown`、marker `.laodao-skills`、无 `VERSION`）。`minimize-repo-footprint` 交付规则全局解析后，改名传播成本降到历史最低（权威源改一次 + 消费仓 `sdflow-init update` 重注入），消费仓数量也在最少点——explore 2026-07-03 拍板：**全量 `sdflow-` 前缀改名，去掉冗余后缀，三个名字保留不改**（`RENAME-MAP`，9 改 3 留，见 `openspec/changes/sdflow-rebrand/design.md` §三，本仓唯一数据源）：

| 旧名 | 新名 | 旧名 | 新名 |
|---|---|---|---|
| `opsx-project-init` | `sdflow-init` | `spec-review` | `sdflow-spec-review` |
| `opsx-done` | `sdflow-done` | `impl-review` | `sdflow-code-review` |
| `opsx-maintain` | `sdflow-maintain` | `buglist-recorder` | `sdflow-buglist` |
| `opsx-roadmap-planner` | `sdflow-roadmap` | `todolist-recorder` | `sdflow-todolist` |
| | | `issues-recorder` | `sdflow-issues` |

**保留原名**：`embedded-test-sop`（域技能身份，改名会丢失其"嵌入式测试"语义锚点）、`openspec-upgrade`（升级的是外部 `openspec` npm CLI 本体，非 sdflow 自身，域名即语义）、`sdflow-upgrade`（本次命名法的源头 skill，本身已是 `sdflow-` 前缀）。

围绕这一拍板，另有若干需要单列记录的子决策：

- **(a) 机械化约束**〔承 `adr/0006` (b)〕：改名不靠模型逐处手改记忆，全部按 `RENAME-MAP` 驱动（写死确切 `git mv` / sed 命令，等效脚本化，可复核可重放）；收尾验证用**反向法**——全仓 grep 每个旧名，逐名定制 pattern（防止如 `spec-review` ⊂ `sdflow-spec-review` 的子串碰撞误判），命中文件不在白名单（ADR / ROADMAP 历史行 / CONTEXT 术语史 / `changes/archive/` / `.superpowers/` / `openspec/issues/` 债池历史 / `docs/` / `memo-*.md`）即 FAIL；断言时点定在托管区块重注入之后（先断言必假 FAIL，见 design §四 D1）。
- **(b) `impl-review → sdflow-code-review` 是 9 项改名中唯一非纯机械映射**（词根替换 impl→code，其余 8 项均是纯前缀添加/后缀剥离）：`impl-review` 直译为 `sdflow-impl-review` 对外并不直白（"impl"不是常见触发词，用户实际是在说"帮我 review 代码"）；权衡"对外表达直白"与"与设计评审 `spec-review`/`sdflow-spec-review` 的术语连续性（impl vs code 打破对仗）"两个方向后，用户拍板取前者——直白优先于术语工整。
- **(c) `openspec-upgrade` 豁免理由**：它与 CLI 生成的官方 `openspec-*` 家族同前缀，形式上恰属本次要消灭的混淆类，但其职责就是升级 openspec CLI 本体——域名与语义完全对应，贴 `sdflow-` 前缀反而制造"它是 sdflow 自有能力"的误导。评估过「纳入改名」选项（如改 `sdflow-openspec-upgrade`），因语义倒挂未采纳，维持原名。
- **(d) 触发等价约束**：9 个改名 skill 的 `description` 重写产出一份 `openspec/changes/sdflow-rebrand/trigger-map.md`（随 change 留档，不随本 ADR 归档删除）：每行 = 旧触发短语集 → 新 description 中的对应短语 + slash 新名，约束「原触发场景语句全保留」（如"记一下这个 bug"仍触发 `sdflow-buglist`），只换 slash 名与陈旧指称。验证从最初设想的"人工 3 条抽查"升格为**机械断言**（从新旧 description 提取引号内触发短语集，断言旧集 ⊆ 新集∪trigger-map 映射行）——呼应 `adr/0006` (b) 的"prose 协议脚本化优先"，不能自己定的机械化约束却用人工抽查验收。
- **(e) 回滚边界如实收窄**：本机层面（`git revert` 改名提交 + canonical 重跑 `setup.sh`）可逆；但**消费仓侧非全自动**——已执行过 `sdflow-init update` 重注入新名的消费仓，托管区块不会随源仓 revert 自动还原，需在消费仓再手动跑一次 `update` 回注旧名。不做"纯可逆"的过强承诺。
- **(f) 双品牌过渡期**：`laodao-skills` 旧仓保留为 misc grab-bag，不删、不处置其同名旧 skills；旧仓自带的 `update`（"ld-update"）与本仓 `sdflow-upgrade` 两个品牌名并存一段时间，本次不做收敛，评估工作交给 hand-off 异步跟进。
- **(g) `openspec-upgrade` 与 `sdflow-init` 的触发相邻性**：两者 description 在语义上有一定邻近（都涉及"升级/初始化 openspec 相关工具"），评审阶段的迁移镜曾尝试证伪二者互相误触发的风险，未能证实也未能证伪。此为改名前即存在的既有现象，本次改名未放大也未收窄——如实记录，不额外设防。

## Considered Options

- **全量 `sdflow-` 前缀改名 + 三保留名单（选中）**：一次性消除三代命名地层堆积，建立统一品牌前缀；代价 = 9 处斜杠命令肌肉记忆一次性切换（单用户环境，接受）。
- **plugin 冒号命名空间**（如 `sdflow:review`）：形式上更贴近官方 `opsx:*` 的命名法。**双 agent 否决**——Codex 无 plugin 概念，这套 skill 集合本就要在 Claude 与 Codex 两侧同时可用，冒号命名空间在 Codex 侧无落地方式，会造成两侧命名分裂而非收拢。未选。
- **半量改名**（只改风险最高的几个，如 `spec-review`/`impl-review`，其余 `opsx-*` 维持不动）：改动量小、风险面窄，但会制造"改了一半"的品牌分裂状态——12 个 skill 里几个 `sdflow-*`、几个 `opsx-*`、几个裸通用词并存，比改名前的单一地层堆积更难解释给新读者。未选。
- **留旧名 stub/别名**（旧 slash 名保留一个转发到新名的过渡期）：设计门讨论过（评审 DR-6），Codex 一侧曾建议给一版过渡期 stub 以降低旧肌肉记忆的失效冲击。**未采纳**——本仓单用户环境下，旧名失效是"响的"（skill not found，立即可感知）而非静默错误，`RENAME-MAP` 已固定不再变化、无需过渡期，stub 本身也是要长期维护的额外面。设计门 Q2（Non-Goals："不留旧名 stub/别名"）维持 no-stub。

## Consequences

- `RENAME-MAP` 是本次改名唯一数据源：9 个 skill 目录 `git mv`、`setup.sh` 的 `OUR_LEGACY_NAMES`（迁移测试侧另维护对照集合 `OUR_NAMES`）、各 `SKILL.md` 互引、`assets/workflow/workflow.md` 步骤表 prompt、`assets/snippets/` 托管区块模版，均从此表机械派生，任何后续再改名（若发生）须先改这张表。
- `setup.sh` 输出品牌升级为 `sdflow-skills v<VERSION>`（`VERSION` 新建 `0.9.0`）；marker 由 `.laodao-skills` 迁移为 `.sdflow-skills`，兼容识别集合收窄为「目录名 ∈ RENAME-MAP 旧名∪新名∪保留名单」，防止误伤 laodao 旧仓自身 misc skill 的 Windows 拷贝（评审 F8/DR-7）。
- `trigger-map.md` 作为触发等价的评审面与断言输入随 change 留档；后续任何 skill 改名都应比照本次产出同类映射表，而非仅凭人工记忆核对触发短语。
- 三保留名单（`embedded-test-sop` / `openspec-upgrade` / `sdflow-upgrade`）固化为本仓命名规范的显式例外，后续新增 skill 若域名/外部依赖与 `sdflow-` 前缀语义冲突，可参照 (c) 的豁免理由类比裁决，无需每次重新论证。
- 两笔延后事项进 hand-off / todolist：① `laodao-skills` 旧仓 `update` 与 `sdflow-upgrade` 双品牌并存的收敛评估（(f)）；② `openspec-upgrade` 与 `sdflow-init` 触发相邻性的既有风险持续观察，不阻塞本次改名（(g)）。
- 回滚（若需要）遵循 (e) 的边界：本机 `git revert` + canonical 重跑 `setup.sh` 即可复原；已执行过消费仓 `update` 的下游仓库需各自补一次 `update` 回注旧名，非一键全自动。
