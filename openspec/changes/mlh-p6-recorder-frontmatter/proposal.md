# mlh-p6-recorder-frontmatter

> **触发判定（TG）**：TG-05（recorder 索引数据对象变更）· **TG-06 HR**（`buglist.py` / `todolist.py` / `issues.py` 共享存储契约）· TG-10（三组件协作）· TG-11（写入→扫描→聚合管道）· TG-13/14/15（存储架构与读写 codepath 重构）· **TG-16 HR**（T66 性能要求）· TG-18（测试计划）· TG-19（多需求）· TG-20（消费仓影响）· TG-21（开放问题）· TG-23（迁移方案选择）· **TG-26 HR**（并发分配 ID 与写盘）。
>
> **HR-TG 命中 `{TG-06, TG-16, TG-26}`**：设计审须覆盖共享 schema、性能基线与并发写入时序。

## Why

issues recorder 把 `ID/module/summary/priority/status/time/change/batch` 作为 Markdown 总览表的位置列存储，迫使写侧拒绝 `|`/换行、读侧依赖切列和表↔正文双写一致性；这些守卫只能阻止部分腐蚀，不能修复脆弱的数据基底。mechanical-layer-hardening 的 P6 端态 A 已拍板，且前置阶段均已交付，现在应把新记录迁到结构化索引，同时保留历史数据可读和既有 CLI 行为。

## What Changes

- **BREAKING（存储格式；CLI/JSON shape 兼容）**：新建 recorder 文档不再写 Markdown 状态总览表，改为带版本标识的 YAML frontmatter 索引 + Markdown prose 详情块；`[grill-amendment]` 新 block 以成对 ID marker 定界，legacy item 首次 promotion 时只在既有 block 外围套 marker、内部 bytes 不变；`[spec-review-amendment]` 孤立 legacy raw ID（如 `A007`）首次 mutation 后会以 canonical ID（`A7`）出现在成功 JSON/后续 scan，属于值 canonicalization 而非 envelope shape 变化，须在升级说明显式告知。
- `buglist.py`、`todolist.py`、`issues.py` 统一支持新格式，并对历史 Markdown 表执行 fail-closed dual-read；不批量改写存量文件。
- 删除新写侧 `_reject_cell_unsafe`、`_render_item_table` 和表格双写半场，使 `|`、换行等合法内容可由 YAML 正常承载；同步更新 recorder 镜像 helper 一致性守卫。
- **Fold T66**：扫描时每份池数据只解析一次；`[spec-review-amendment]` `batch rename` 以 `issues.py` direct raw-bytes snapshot 做整次命令每 dated 文件 read/parse=1，不先 scan JSON 再二次打开。
- **Fold T67**：自定义 ID 按语义规范化校验，拒绝 `A007`/`A7` 等同号异形并存；`[grill-amendment]` 保留公开的单字母自定义 `--prefix`，但分配/查重升级为锁内跨 bug+todo 两池全局唯一。
- **Fold T146**：为 ID 分配与 recorder 写盘建立仓级互斥和原子替换，避免并发 `max+1` 撞号或覆盖；`[spec-review-amendment]` mutation 同一 dated document 的合规 sibling producer 也须加入该 lock 域。
- 保持 T1/T3/T4/T5 已交付行为：reindex 问题可观测、终态集跨脚本一致、batch 操作幂等、item 定位与状态流转不回归；T2 的拒绝式止血由结构化存储根治取代。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`：把 recorder 的 Markdown 表写入、字段拒绝和表格 arity 契约改为 frontmatter 新写、历史 dual-read、语义 ID 唯一、并发安全及单次扫描契约，同时保留 reindex/sweep/triage/status 的外部行为。
- `determinism-guards`：按目标态重定 recorder 镜像 helper 拓扑；删除已退役 helper 的强制存在断言，并守护新增或继续共享的 frontmatter、ID、锁与原子写 helper 不漂移。

## Impact

- **主要代码**：`sdflow-buglist/scripts/buglist.py`、`sdflow-todolist/scripts/todolist.py`、`sdflow-issues/scripts/issues.py` 及三者测试；`sdflow-buglist/tests/test_mirror_consistency.py`。`[grill-amendment]` dated 文件采用专用 single-read bytes pipeline/atomic helper，INDEX/batches 保留 text pipeline；`[spec-review-amendment]` batch rename 由 `issues.py` direct bytes snapshot 读取一次并以 `batches.md` machine-owned `重命名自:` provenance 恢复；runtime ignore 真相源固定 `sdflow-init/assets/snippets/runtime-gitignore.txt`，init/update 幂等合并并同步本仓 `.gitignore` dogfood。
- **规范**：修改 `spec-workflow` 与 `determinism-guards`；roadmap P6 与 todolist T85/T66/T67/T146 形成追溯关系。
- **消费方**：所有使用 recorder CLI 的仓库；历史 dated 文件不批量迁移，新旧格式在读侧共存。直接解析 Markdown 表的非契约脚本需改用 recorder JSON/CLI 输出。
- **技术栈（TG-01/02/03）**：Python CLI + Markdown/YAML 文档，不命中 backend、embedded、frontend 领域清单。
- **外部依赖**：无外部服务；YAML 解析是否引入库或采用受限自包含解析器留 design 决策。

## Success Metrics

1. 新格式记录的索引字段包含 `|`、换行及 Unicode 时可写入并逐字段 round-trip，且不再依赖 table-cell reject。`[grill-amendment]` 普通 Unicode 保持人读，NEL/LS/PS 定向 escape、孤立 surrogate 前置拒绝且不做 normalization；renderer 按 semantic ID/fixed object order/null canonical form 产生唯一 bytes；多行 summary 以单行 display title + 逐行 blockquote 呈现；canonical/overlay prose 以成对 ID marker 定界，任意自由文本中的 heading/separator/fence 不能制造伪 block，旧 heuristic 仅留 legacy read。
2. 全部现存历史 buglist/todolist 语料经 dual-read 后，ID、状态、change、batch 与变更前扫描结果一致；坏 frontmatter 非零退出且给出文件定位，不静默回退成合法数据。`[grill-amendment]` 仅文件起点（可带 UTF-8 BOM）的 frontmatter 作为共享 envelope，recorder mutation 以 byte-level splice 只改唯一顶层 `sdflow-issues` 子树，namespace 外 BOM/EOL/正文逐字节不变；mode 与 legacy 总览区域必须互证，重复、编码、mode mismatch 或边界歧义时拒绝写盘。
3. 显式同号异形与 Unicode-digit ID 100% 被拒，自定义 prefix ID 在两池全局唯一；并发执行 ID 分配与写入的压力测试无重复 ID、无丢写、无残留锁或半写文件。`[grill-amendment]` 独立权威读也 acquire 同一 exclusive snapshot lock；`sweep` 等复合命令由父进程 owner 持锁，scan/mutating 子进程凭 token 作为 participant 加入，既不自锁、不开放子步间并发插入窗口，也不成功返回跨 writer 的混合 snapshot。`[spec-review-amendment]` 同 dated document 的合规 metadata producers 共用该 document lock；绕锁 producer 明确在 lost-update 保证外，不伪造 CAS 承诺；只读命令在输出前释放，partial lock 有明确 break-glass，init/update 幂等 ignore runtime lock。
4. 单次 `scan` 对每个 dated 文件至多解析一次；`batch rename` 由 `issues.py` direct snapshot 使整个命令每 dated file read/parse=1、per-pool `scan --json`=0，覆盖 T66 的两处重复工作。`[spec-review-amendment]` rename 先 registry-first 写 `重命名自:` provenance，再 retag/reindex；只有 dated files、batch key、INDEX 与 batches 全部收敛才成功，无匹配 provenance 的 old-missing 盘面不得误报 retry success。
5. recorder 三套定向测试、镜像一致性测试及全仓 `pytest` 全绿，T1/T3/T4/T5 既有场景无回归。

## 需求优先级（TG-19）

- **P0**：frontmatter 新写、历史 dual-read、坏数据 fail-closed、既有 CLI/JSON 行为兼容。
- **P0**：语义 ID 唯一与仓级并发锁，避免新格式落地后继续制造撞号或覆盖。
- **P1**：T66 单次解析/单次读池优化、镜像 helper 守卫更新。
- **P2**：迁移诊断与错误提示的可读性增强，不扩大为通用 tracker 抽象。

## 利益相关方与外部依赖（TG-20）

- **直接使用方**：`sdflow-buglist`、`sdflow-todolist`、`sdflow-issues` 的调用者，以及依赖 `scan --json`、`reindex`、`sweep` 的 `sdflow-done` 等编排器。
- **消费仓维护者**：存量文件保持原样；升级后新写格式变化，但 CLI/JSON 是稳定接口。
- **仓库维护者**：需在实现与归档时同步 T85/T66/T67/T146 状态，并确认既有未终态历史 item 仍可操作。
- 无第三方 API、云服务或跨团队发布依赖。

## 开放问题（TG-21）

| ID | 问题 | 负责人 | 截止 |
|---|---|---|---|
| OQ1 | “历史表冻结只读”条件下，仍未终态的历史 item 如何继续 `set-status`/`triage`/`sweep`：按文件懒迁移、结构化 overlay，还是保留受限 legacy 写路径？方案必须同时满足“不批量改历史”和“既有 item 可闭环”。 | design | specs/design 定稿前 |
| OQ2 | frontmatter schema 的版本键、每文件索引形态、字段枚举及重复键/坏 YAML判定如何定义？ | design | specs/design 定稿前 |
| OQ3 | 仓级锁的路径、超时/陈旧锁恢复及 CLI 并发失败语义如何与 `atomic_write` 组合？ | design | design review 前 |
| OQ4 | YAML 解析采用受限 stdlib 实现还是显式依赖；选择须覆盖重复键、tab、类型、BOM 和错误定位。 | design | design review 前 |

## Assumptions

- **A1** recorder CLI/JSON 而非 Markdown 表形态是稳定接口。若存在下游直接切表脚本，存储格式变更会破坏它；design 前须仓内搜索并在已知消费仓抽样验证。
- **A2** 不批量迁移历史文件可以满足审计与成本边界。若 OQ1 证明未终态历史 item 无法在此约束下闭环，须由人重新拍板该约束，而不是静默保留两套永久写路径。
- **A3** 三个 recorder 继续保持自包含、不互相 import。若共享 schema 无法在测试守卫下可靠同步，需另立边界决策，不在实现期临时抽公共运行时模块。

## Non-Goals

- 不批量重写历史 buglist/todolist 文档，也不重排或美化其 prose。
- 不把 `batches.md` 注册表迁到 frontmatter；T72 的批次人写字段完整性另行处理。
- `[spec-review-amendment]` 不承诺 NFS/SMB/FUSE 等 network/userspace filesystem 的 lock/replace 等价语义，也不实现完整 file+directory fsync 的 power-loss durability；POSIX local FS 是自动门，Windows local FS 只按明确 smoke contract 验收。
- `[spec-review-amendment]` 不新增 `doctor`、自动 `lock recover`、TTL 偷锁或 diagnostic JSON API；现有 scan/reindex 与 fix-directed stderr 承担诊断，partial lock 走显式人工 break-glass。
- 不实现 T123 的可插拔 tracker 后端，不引入数据库或远程 issue service。
- 不改变 bug/todo 状态机、优先级业务语义、batch 分诊策略或 `sdflow-done` sweep 流程。
- 不修改 `sdflow-init/assets/workflow/` bundle；本 change 改 recorder skills 与本仓 specs。

## Compliance

不涉及凭证、敏感数据、外部计费或法规合规，业务合规为 N/A。共享 frontmatter schema 属 TG-06 跨模块契约：design 必须指定单一 schema、逐消费方兼容语义与 fail-closed 行为，同时保持 recorder 自包含、以一致性测试防镜像漂移；并发面按 TG-26 明确锁所有权、原子写和失败恢复。目标态以“未来字段腐蚀结构上不可能”为验收基准，不以现有拒绝守卫暂时有效为缩 scope 理由。
