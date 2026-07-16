# 0025 · recorder 机器索引迁入 versioned frontmatter：共享 namespace、same-file overlay、marker prose 与仓级 snapshot lock

> 状态：**Proposed**（2026-07-16，`mlh-p6-recorder-frontmatter` grill 收敛时立）`[grill-amendment]`——待该 change ship 后升 Accepted。
> 关联：`openspec/changes/mlh-p6-recorder-frontmatter/{proposal,design,tasks}.md` · `adr/0010`（本 ADR supersede 其新写决策）· CONTEXT「共享 frontmatter envelope」「canonical recorder render」「marker-framed prose block」「锁 owner / participant」。

## Context

bug/todo recorder 现把 `ID/module/summary/priority|type/status/time/change/batch` 写进 Markdown 总览表，再把详情写进 prose block。机器读侧按 `|` 位置切列，写侧因而必须拒绝合法的 ASCII `|` 与换行；状态又在表与属性块双写。ADR-0010 当时有意选择“写时 reject、结构化延后”，把它作为低成本桥，而不是永久目标。

mechanical-layer-hardening P6 现在兑现该 defer。目标态不仅要“换一种序列化”，还要同时守住：

- 历史 Git 文档不批量重写，但未终态 item 仍可 mutation；
- recorder 与其它 metadata producer 可共用一个 Markdown frontmatter；
- 任意合法 prose 不再参与机器边界；
- 三个自包含脚本不建立运行时 import，却不能各写一套漂移语义；
- ID 分配、多文件 batch mutation 与权威 scan 在并发下不产生 lost update 或混合 snapshot；
- 中断后的多文件 rename 能由同一命令按盘面继续，而不是 warning-only 假成功。

## Decision

### 1. 机器索引使用唯一顶层 `sdflow-issues` namespace

dated Markdown 文件在 byte 0（允许前置 UTF-8 BOM）的 frontmatter 是共享 envelope。recorder 只拥有唯一、无引号的顶层 `sdflow-issues` 子树；内部 v1 固定为 `schema/pool/mode/items`，item value 是单行 JSON object。

- reader 只严格校验 recorder 子树；其它顶层 namespace 按 opaque bytes 处理。
- writer 以单次 binary read + byte spans 只 splice 自有子树，namespace 外 BOM/EOL/注释/顺序/正文逐字节保留。
- dated 文件使用 `atomic_write_bytes`；完全生成的 INDEX/batches 继续使用 text `atomic_write`。
- UTF-16 BOM、非法 UTF-8、lone CR、边界歧义、重复/同名变体 namespace 均 fail-closed。
- Unicode string 只允许 scalar values；NEL/LS/PS 定向 JSON escape，孤立 surrogate 前置拒绝，不做 normalization。
- renderer 使用 semantic ID 排序、pool-specific fixed object order、null-only optional emptiness；render→render byte-identical。

不采用展平的 `sdflow-issues-*` 多键，也不建立多工具共管的 `sdflow:` 父树：前者把所有权散到多个顶层键，后者只是把共享 envelope 的冲突下移一层。

### 2. legacy 表冻结，活跃 item 以 same-file overlay 渐进迁移

新文件写 `mode=canonical`；已有 legacy 总览区域的文件写 `mode=overlay`。旧表与旧属性表永不再写，frontmatter 对同文件同 semantic ID shadow legacy snapshot。更新 pure-legacy item 时，把完整当前索引提升进同文件 overlay；不建 sidecar、不批量迁移整篇历史。

`mode` 不是可信行为开关，而是与物理形态互证的迁移声明：canonical 必须无 legacy 总览区域，overlay 必须恰有一个；mismatch fatal，不能靠改 enum 隐藏 items。

新 prose block 使用成对 `sdflow-issue-block:start/end id=...` marker 定界，heading 只展示。legacy item 首次 promotion 时，对唯一可判旧 block 只在外围套 marker，内部 bytes 不重渲染；随后永久按 marker 定位。自由 prose 中的 heading、`---` 与 fence 不再是边界。

### 3. ID 保留自定义 prefix，但升级为两池全局语义唯一

新写 canonical spelling 为 `[A-Z][1-9]\d*`，bug/todo 默认 B/T，公开的单字母自定义 `--prefix` 保持兼容。semantic key 是 `(uppercase prefix, decimal integer)`，不含 pool；`A007`/`A7` 同号异形，bug `A7`/todo `A7` 跨池重复。

`next-id`、自动 add 与显式 ID 查重在同一 snapshot lock 内读取两池全集。`next-id` 释放锁后仍只是 advisory，不构成 reservation。

### 4. `.recorder.lock` 是 cooperative exclusive snapshot lock

顶层权威读或 mutation 以 `O_CREAT|O_EXCL` 创建 `openspec/issues/.recorder.lock`，生成高熵 token 并成为 owner；复合命令的 scan/mutating 子进程凭继承 token 校验后作为 participant，不重复 acquire、不得 release。

- 独立 scan/next-id 也 acquire，避免成功返回多文件 writer 的中间态。
- 只读锁持有到 immutable snapshot materialize，输出前释放；mutation 持有到最后一次 replace。
- owner release 前核对 token，不能误删人工替换后另一 owner 的锁。
- metadata 尚未写完仍视为 occupied；不等待、不按 TTL 自动偷 stale lock。
- lock 只约束遵守协议的 CLI，不宣称阻止编辑器、手工脚本或 Git 绕过。
- `sdflow-init` 新增 canonical runtime-ignore snippet，幂等写入 `/openspec/issues/.recorder.lock`，避免 checkpoint/dirty-tree 污染。

### 5. batch rename 非事务，但必须阶段可识别、同命令恢复

rename 不增加 journal 或跨文件 rollback。它在锁内从 registry old/new 与 items old/new 的 canonical 盘面识别阶段：部分 item 已改时继续；old 已消失、new 已存在且无 old item 时补跑 reindex；双 key 或反常残留 fail-closed。

成功边界覆盖 dated files、batch key、INDEX 与 batches 派生状态。任一步未收敛都 non-zero，并提示重跑原命令；禁止 reindex 失败后 warning-only exit 0。

## Consequences

### 收益

- `|`、换行与 Unicode 不再受 Markdown 表列模型限制，机器索引只有一个可版本化真相源。
- 历史表零批量改写，活跃历史 item 又能逐项迁入目标格式。
- 新 prose 的机器边界不再依赖用户 Markdown；表↔属性状态双写退出目标态。
- 成功 scan 对应无 cooperative writer 穿越的仓级时点；并发 add 不重复、不覆盖。
- 同一 semantic model 有唯一 renderer bytes，三份自包含实现可由 AST/golden fixture 机械守护。
- rename 的“可重跑”成为可测试状态机，而非操作建议。

### 代价与边界

- strict YAML-subset 不是任意 YAML；合法但不在子集内的手写形态会被拒绝。
- 首次 mutation 会 canonicalize 整棵 recorder namespace，并可能给旧 block 加外围 marker。
- exclusive snapshot lock 让读读也串行；被 kill 的短读也可能留下 stale lock并扩大人工恢复面。
- byte-preservation 只覆盖内容与既有 mode bits，不覆盖 inode/mtime/xattr/ACL。
- cooperative lock 不能防外部不守协议写入；后续 parser/validation只能尽量 fail-loud。
- 三份 helper 继续物理复制，维护成本由 AST parity、golden bytes 与 call-graph 测试承担。

## Supersession

本 ADR **supersede ADR-0010 的“Markdown 表 + table-cell reject 作为新写契约、结构化继续 defer”决策**：该桥接任务已完成，新的 recorder item 不再写总览表，也不再因索引字段含 `|`/换行而拒绝。

ADR-0010 对历史背景与迁移前止血措施的记录仍有效；legacy 表的 read/arity 检查继续保留，`batches.md` slug 与 Markdown 单行语法位的窄 line-safety 也不随 `_reject_cell_unsafe` 一并删除。

## Rejected Alternatives

- **PyYAML/full YAML**：消费仓裸 Python 环境不保证依赖，重复键与 loader 行为还需额外定制。
- **继续 Markdown 表 escape/reject**：永久保留脆弱列语义，无法删除双写与 parser 机械。
- **整文件懒迁或批量迁移**：一次 mutation 重写大量历史，diff/回滚成本过高。
- **sidecar overlay**：引入第二盘面与跨文件 join 漂移。
- **heading/`---` 继续作新 block 边界**：任意合法 prose 都可能改变机器结构。
- **per-file lock / unlocked reader**：ID、batch rename 与仓级 snapshot 仍有竞态或中间态。
- **shared/exclusive RW lock**：stdlib 跨平台复杂度不值本地低频并行读收益。
- **transaction journal / 自动 rollback**：新增 stale journal 或补偿失败的第二恢复协议；现有盘面已足以判阶段。
- **删除自定义 prefix**：公开 CLI breaking，与本 change 的接口兼容目标冲突。
