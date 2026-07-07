# issues 池机器状态用 markdown 表 + 写时 reject 守盘面完整性；结构化索引刻意延后（去字符串化机器状态层 roadmap）

issues 池 recorder（`buglist.py` / `todolist.py` / `issues.py`）把每条 debt 的**索引行**（ID/module/summary/priority/status/time/change/batch）存进 markdown 状态总览表——即「盘面即状态」的盘面——用 naive `strip("|").split("|")` 按位置切列。这让"字段值含 ASCII `|` 或换行"能致列错位/整行截断而**静默腐蚀盘面**（issues-pool-hardening 的 T2）。面对这一类，我们**刻意选"守"而非"重构"**：写路径对总览行字段做 **table-cell-safe 校验、含 `|`/换行即 `_die` 拒绝**（reject），保留 markdown 表格式不动；把"索引层结构化（YAML frontmatter 索引 + prose 块）"这个根治**延后**到一个独立 roadmap（「去字符串化机器状态层」，与 gate 状态锚迁 frontmatter 的 T65 同根、同阶段）。理由：markdown 表的人读/`git diff`/grep/GitHub 渲染优点是真的，结构化是范畴不同的大迁移；而 reject 是通往未来结构化的**低成本桥**——零机械投资、不挡重构。

## Considered Options

- **写时 reject + 延后结构化（选中）**：复用本仓既有 `_die` 写时校验惯例（priority/status 非法即拒），零解析器改动、fail-closed、对齐反静默纪律。实证支撑：全量扫过现存池**0 行**字段含 `|`——"保留字面 `|`"需求量=0，YAGNI。代价：真需要字面 `|` 的字段被拒（须改写或用全角 ｜），但响亮不静默、且需求罕见。
- **转义 `\|` + 三处解析器改按未转义切列**：未选——为一个**从未触发**（0 occurrence）的潜在腐蚀，引入全新转义/反转义语义 + 动三处读路径核心，且这套机械在未来结构化后会被整个扔掉（投资打水漂）。
- **替换为全角 `｜`（U+FF5C）**：未选——无损前提不成立（无法还原原 ASCII 管道），且悄悄改用户字节，违反反静默。
- **现在就结构化索引层（Path B）**：未选（本轮）——收益真（腐蚀类蒸发 + 删 recorder 里 ~40 处/文件表解析与双写一致机械 + 化解表↔块一致复杂度），但属大迁移；对小 dogfood 仓，reject 已极小代价堵死腐蚀，结构化 ROI 待"recorder 持续出 bug 或想在数据上建工具"时再兑现。归 roadmap 统一权衡。

## Consequences

- **issues-pool-hardening 落地本 ADR**：T2 实现为总览行字段写时 table-cell-safe reject（`|` + 换行），scope 钉死总览表 row 字段，详细块 prose 不受限。
- **与 D2（--strict）同系反静默**：同一 change 里 reindex 加 `--strict` opt-in enforcement，堵"非交互调用 stderr 被吞 + exit 0"的静默蒸发——reject（写时挡腐蚀）与 --strict（收尾抓不一致）是盘面完整性的两道写/读侧守卫。
- **roadmap「去字符串化机器状态层」**：Path B（recorder 索引结构化）+ T65（gate 状态锚迁 frontmatter）合为两阶段；本 change 的 reject 是其低成本前置桥，不与之冲突。
- **与 adr/0006、0008、0009 同哲学**：workflow「不押上游理想假设」——此处不押"字段永远干净"，写时守盘面。
- **CONTEXT.md**：无新术语（本决策是设计选择非领域词汇）；「盘面即状态」外延澄清——盘面不必是 markdown 表，结构化 YAML 亦是合法盘面，故延后结构化不违背该原则。
