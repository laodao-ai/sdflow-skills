---
impl-pipeline: tickets
---

## Global Constraints

- 新 item 的机器索引只写 versioned frontmatter，不再写 Markdown 总览表；`|`、换行与 Unicode 可无损 round-trip。
- 历史表格零批量改写且永不再写；历史 item 仍可 `set-status`、`triage`、`batch rename` 和 `sweep`。
- frontmatter 坏数据 fail-closed；不存在 namespace 才允许回退 legacy table，namespace 在场但损坏不得回退。
- 自定义 ID 在语义上唯一；所有 recorder 写事务由仓级互斥串行化并保持原子替换。
- `scan` 每文件只读/解析一次；`batch rename` 每池只扫描一次并复用更新后的 snapshot 完成 reindex。
- 保持 recorder 自包含、不建立跨 skill import；用镜像一致性测试兜住共享机械逻辑。
- `sdflow-issues` 本身就是 namespace 前缀：内部保持短键 `schema/pool/mode/items`。reader 不替其它工具校验未知顶层内容；writer 以 byte-level 窄 scanner 定位 recorder 子树并做局部 splice，namespace 之外逐字节保留。重复 namespace、非标准拼写造成的所有权歧义或无法确定 splice 边界时 fail-closed，原文件不变。
- ID 在 bug+todo 两池仓级全局唯一；bug `A1` 与 todo `A1` 冲突。自定义 prefix 的 `next-id`、自动 add 与显式 ID 查重必须在同一 snapshot lock 内读取两池全集，MUST NOT 只扫当前 pool。
- `O_EXCL` 成功即代表锁已占用，即使竞争者恰好读到 owner metadata 尚未写完，也只能报告“owner metadata unavailable/initializing”，MUST NOT 当成 stale 或空锁继续。
- writer 出错时只回退 writer/cleanup 提交，保留 dual-reader，使已经产生的 canonical/overlay 文件仍可读；MUST NOT 直接回退到只认 Markdown 表的版本。
- 不迁 `issues/batches.md`。
- 不批量迁移所有 legacy dated 文件。
- 不改变状态机、优先级/类型枚举、DONE/FIXED 门禁或 sweep 的非原子重跑语义。
- 不修改 `sdflow-init/assets/workflow/`。

### Task 1: 严格 dual-reader 与 canonical frontmatter 合同

**Blocked-by:** none
**R-ID:** SW-RI-1, SW-RI-4, DG-RI-1

从行为级 fixture 和失败矩阵起步，交付可同时读取 canonical、overlay 与 pure-legacy 文档的严格 reader，以及唯一、确定性的 frontmatter renderer。新 reader 必须一次 binary read/parse 完成格式识别、索引合并、block relation 与诊断；坏 namespace 必须在任何旧表 fallback 或写盘前 fail-closed，同时保持旧 writer 可用，建立后续迁移的回滚安全底座。

- [x] canonical、overlay、pure-legacy 三类 fixture 覆盖同文件 shadow、Unicode/多行/管道符 round-trip、共享 envelope byte 保真和 block 注入边界。
- [x] canonical renderer 的字段顺序、semantic ID 排序、null/empty-map、Unicode scalar 与 LF/CRLF/BOM 规则具有 golden bytes，并满足 parse/render 幂等。
- [x] schema、lexical profile、编码/EOL、namespace/ID/JSON 重复、mode/物理结构不一致等坏输入全部 non-zero，诊断可定位且原 bytes 不变。
- [x] scan 对每个 dated 文档只有一次 binary read 和一次 document parse，legacy arity/problem 语义与 CLI/JSON shape 保持兼容。
- [x] dual-reader 的共享机械 helper 在三个自包含 recorder 间由显式 parity/golden 契约守护。

### Task 2: 仓级 semantic ID 与 exclusive snapshot lock

**Blocked-by:** 1
**R-ID:** SW-RI-2, DG-RI-1

交付跨 bug/todo 两池统一的 canonical ID 语义和仓级 exclusive snapshot lock。所有权威读、分配、查重、复合命令 participant 与最终原子替换必须落在同一 cooperative 锁域；冲突、partial metadata、stale lock、token 越权与平台差异都要 fail-loud，且运行时锁不会进入 Git。

- [ ] 新写 ID 仅接受 canonical ASCII spelling，自定义 prefix 兼容，legacy alias promotion 与跨池语义冲突有确定行为。
- [ ] scan/next-id/add/status/triage/reindex/sweep/batch 命令覆盖 owner/participant 锁协议，影响结果的 discovery/read 均发生在锁内。
- [ ] token 只向同 repo allowlist recorder 子进程受控转发，非 allowlist、跨 repo、伪造、过期和越级委派均在业务读写前拒绝。
- [ ] 20 进程并发 add、reader/writer barrier、fault injection、ownership-lost 与 break-glass 场景证明无重复成功 ID、无 lost write、无静默偷锁。
- [ ] init/update 对运行时 lock ignore 的合并幂等、保留用户 bytes，dogfood 仓盘面恰有一条对应 ignore。

### Task 3: 新写 frontmatter、overlay promotion 与 marker prose

**Blocked-by:** 1, 2
**R-ID:** SW-RI-1, SW-RI-2

把所有新建与 mutation 行为切换到 frontmatter：新文件产生 canonical 索引，历史文件按访问建立 overlay，legacy item promotion 原位包裹唯一可判 prose block。新格式 prose 只保留人读内容和追加历史，不再复制可变机器状态；任何旧表、外部 namespace 或 marker 歧义都不得被猜测性改写。

- [ ] add 在新文件写 canonical、在 legacy 文件写 overlay，索引字段允许管道符、换行与 Unicode，CLI/JSON 输出兼容。
- [ ] status/triage 对 legacy item 完整 promotion，旧表、旧属性表和既有 prose bytes 保持不变，后续 mutation 只按 canonical marker 定位。
- [ ] marker 缺对、错 ID、嵌套、重复、预存碰撞及 legacy bug block 歧义均写前拒绝；todo 无块时可确定性创建 minimal block。
- [ ] display title、summary blockquote、用户 marker escape 与 line-safety 行为阻断 Markdown 注入而不重新限制合法多行索引值。
- [ ] 新 writer 已彻底停止写总览表 row 或双写 status/batch，同时 dual-reader 仍能读取所有已产生形态。

### Task 4: 单次 snapshot 的 batch rename 与 fail-closed reindex

**Blocked-by:** 3
**R-ID:** SW-RI-1, SW-RI-3, SW-RI-4, DG-RI-1

交付可恢复的跨池 batch rename：直接构造两池一次性 bytes snapshot，在内存 retag 后复用同一 updated snapshot 生成派生索引；registry provenance 区分首次执行、合法重试与未知 source。consumer 协议漂移、frontmatter/ID fatal 或任何写失败都必须在完全收敛前 non-zero，非致命 legacy problems 继续保持默认可观测语义。

- [ ] rename 每个 dated 文档 read/parse 各一次、每池 recorder scan 调用为零，reindex 不重新读取两池。
- [ ] registry-first provenance 与 old/new item 状态矩阵覆盖首次执行、全 old、混合、全 new retry、orphan、双 key 与未知 source。
- [ ] canonical/overlay/legacy retag 永不 patch 历史表 row，BOM/CRLF/外部 namespace bytes 在自有 span 外保持不变。
- [ ] scan JSON 坏 JSON、缺键、错型、缺 file 或枚举漂移在覆盖 INDEX/batches 前 fail-closed。
- [ ] registry、dated 文档、INDEX 与 batches 各阶段 fault injection 均给出 stage/原命令恢复信息，完全收敛前不得 warning-only success。

### Task 5: 移除 legacy 写半场并完成交付对账

**Blocked-by:** 4
**R-ID:** SW-RI-1, SW-RI-2, SW-RI-3, SW-RI-4, DG-RI-1

收口存储迁移：删除新写侧的表格 cell 拒绝与 row mutation，只保留 legacy read/promotion 半场；更新用户契约、后继 ADR、术语与交付记录，并用真实 recorder 命令 dogfood 活跃历史 item。最终以定向、全仓、严格 OpenSpec 和跨平台 smoke 证据证明新格式、并发安全、snapshot 复用及兼容边界完整闭环。

- [ ] legacy table parser 只剩 read/promotion 调用，新 writer 无表 row mutation、无 `_reject_cell_unsafe` 活引用、无跨 recorder import 或 YAML 依赖。
- [ ] mirror roster、consumer contract、README/SKILL/help/error 文案和 ADR/CONTEXT 明确 shared envelope、lock、rename retry、平台/FS/durability 边界。
- [ ] 全量历史 corpus 的 dual-reader 关键字段与升级前 baseline 逐 item 相等，不把动态 item 总数固化成长期断言。
- [ ] T85/T66/T67/T146 经真实命令写成 overlay，旧表 bytes 不变，scan/reindex strict 与 roadmap/issues 交付记录收敛。
- [ ] recorder 定向套件、mirror consistency、全仓 warnings-as-errors、严格 OpenSpec 校验、diff check、known-consumer smoke 和 Windows local-disk smoke 均留下可审计结果。
