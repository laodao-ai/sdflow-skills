# Tasks — mlh-p6-recorder-frontmatter

> Requirement IDs：`SW-RI-1` frontmatter/overlay、`SW-RI-2` ID+并发、`SW-RI-3` 单次解析/rename snapshot、`SW-RI-4` reindex 可观测性、`DG-RI-1` 镜像一致性。实现顺序遵 design Migration Plan：dual-reader 先于新 writer，确保任何中间提交与回滚都能读取已产生的新格式。

## 1. Contract Fixtures and Parser TDD

- [ ] 1.1 `[SW-RI-1]` 为 bug/todo 建立 canonical、pure-legacy、overlay 三类文档 fixture，覆盖同文件 shadow、新 frontmatter-only item、`|`/换行/Unicode round-trip，并记录升级前 legacy scan baseline；`[grill-amendment]` 加 summary 含 `## fake`/`---`/多行的 fixture，断言 heading 单行投影、逐行 blockquote 与 block identity 不受注入。
- [ ] 1.2 `[SW-RI-1][DG-RI-1]` 先写失败测试固定 planned bytes helpers `read_recorder_document` / `parse_recorder_document` / `render_recorder_namespace`、v1 schema、固定字段顺序、JSON duplicate-key 拒绝与 parse→render→parse 等价；`[grill-amendment]` 增加 item permutation golden bytes、semantic ID sort、pool-specific object order、null-only optional、`items: {}`、render→render byte identity，以及共享 envelope 的 BOM/EOL/unknown-content/Unicode 保真 fixture。
- [ ] 1.3 `[SW-RI-1][SW-RI-4]` 建坏输入矩阵：未知 schema、pool/path 不符、非法 mode、tab/缩进、重复 namespace/ID/JSON key、缺字段、类型/枚举越域；`[grill-amendment]` 补 change/batch 空串、裸 `items:`、module/summary 纯空白、canonical+legacy 区域、overlay/legacy 区域缺失/重复、namespace 非标准同名拼写、正文伪 frontmatter、编码/EOL/Unicode/boundary 歧义；逐例断言 non-zero、path/ID+field+reason、无 legacy fallback、原 bytes 不变。
- [ ] 1.4 `[SW-RI-1]` 写 merge/block 失败测试：namespace 缺失才走 legacy、overlay 同文件同 ID frontmatter 胜、跨文件重复仍 fatal、新格式 prose 不参与当前 status/batch 判定；`[grill-amendment]` 新 block 只认成对 marker，覆盖缺对/错 ID/嵌套/重复/orphan、bug 缺块、todo 无块合法与首次历史建 minimal block；另覆盖 promotion 原位包裹后内部 bytes 不变、后续不回退 heuristic，以及缺块/多块/歧义 bug fail-closed。

## 2. Dual Reader and Deterministic Frontmatter Writer

- [ ] 2.1 `[SW-RI-1][DG-RI-1]` 在 `buglist.py` 与 `todolist.py` 实现严格 bytes frontmatter parser/renderer、document format 判定与 legacy/overlay merge；`[grill-amendment]` 每 dated 文件一次 binary read，scanner 仅在 byte 0/UTF-8 BOM 后识别 envelope，只解释唯一顶层 `sdflow-issues` 子树、其它内容 opaque 保留，禁止 universal-newline text round-trip/二次读取，ambiguous encoding/EOL/boundary fail-closed；此步保持旧 writer，先让全部现有 scan 测试与新 reader 测试通过。
- [ ] 2.2 `[SW-RI-1][SW-RI-4]` 把 `cmd_scan` 重构为一次 `parse_recorder_document` 产出 items/blocks/problems/format，保留 legacy 7/8 列 arity、重复 ID 与 prose relation 可观测性；`[grill-amendment]` 同次 parse 计数 legacy 总览区域并互证 mode（mismatch fatal），canonical/overlay block_ranges 改读精确 start/end marker，legacy 才读 heading/`---` heuristic。
- [ ] 2.3 `[SW-RI-1]` 切换 `ensure_file`/`cmd_add`：新文件写 `mode=canonical`；已有 legacy 文件创建/更新 `mode=overlay`；`[grill-amendment]` 已有共享 envelope 只 splice 唯一 `sdflow-issues` 子树并逐字节保留其余内容；索引只写 frontmatter，CLI/JSON 返回 shape 不变。
- [ ] 2.4 `[SW-RI-1]` 切换 `set-status` 与 `triage`：legacy item 先提升完整 overlay，canonical/overlay 原位更新；`[grill-amendment]` promotion 对唯一旧 block 只插外围 marker、内部 bytes 不变，todo 无块建 minimal block，bug 缺块/多块/边界歧义拒绝；状态历史追加到 end marker 前，后续 mutation 只按 marker 定位；旧表/旧属性表逐字节不变。
- [ ] 2.5 `[SW-RI-1]` 新格式 prose block 移除可变 status/batch 副本；`[grill-amendment]` 用成对 ID marker 定界并 escape 用户内容中的精确 marker 独占行，显式 title 仅拒 CR/LF/NUL，缺省 display title 由 summary 连续空白折叠派生，完整 summary 逐物理行加 `> ` 渲染且不反解析；用窄 line-safety helper 或安全逐行 renderer 保住 source/project/date/note 的 Markdown 结构，允许普通详情 prose 自由包含 heading/separator/fence。

## 3. Canonical IDs and Repository Lock

- [ ] 3.1 `[SW-RI-2][DG-RI-1]` 实现 canonical ID key/validation：`[grill-amendment]` 新写保留单字母自定义 prefix、统一接受 `[A-Z][1-9]\d*`，默认 B/T；prefix 非单个 ASCII 大写字母拒绝，legacy `A007` vs `A7` 按 `(prefix, decimal)` 语义冲突并报告全部 pool/位置。
- [ ] 3.2 `[SW-RI-2][DG-RI-1]` 实现三份一致的 `recorder_lock(root, command)`：`O_CREAT|O_EXCL`、owner metadata + 高熵 token、fail-fast、metadata 初始化窗口保守判 occupied、`finally` token-safe release、stale-lock 恢复指引；`[grill-amendment]` 不得泄露 token、不得 TTL 自动偷锁、不得误删人工替换后由另一 owner 新建的锁。
- [ ] 3.3 `[SW-RI-2]` 把 bug/todo scan/next-id/add/set-status/triage 与 issues reindex/sweep、batch query/add/set-status/rename 纳入同一 exclusive snapshot lock；`[grill-amendment]` 独立权威读也作 owner，复合命令用专用环境变量把 token 传给直接 scan/mutating 子进程，子进程校验后作 participant 且不 acquire/release；禁止用前后 lock existence check 或全局无条件 `--no-lock` 代替 acquire。
- [ ] 3.4 `[SW-RI-2]` 把自动 ID 的 scan max+1、显式 ID 查重和最终写盘放进同一锁区；`[grill-amendment]` 自定义 prefix 的 `next-id`/add 必须扫描 bug+todo 两池 semantic keys，跨 pool 显式冲突失败、自动分配跳到下一全局可用号；`next-id` 保持只读 advisory，并补释放后竞态测试。
- [ ] 3.5 `[SW-RI-2]` 加 20 进程并发 add、lock conflict、bytes render/write/chmod/replace fault injection 与 stale lock 测试，断言成功 ID 唯一、失败显式、原 bytes/mode 不变、无正常路径残留 lock/tmp；`[grill-amendment]` 覆盖 reader↔writer 双向 barrier、独立 scan/next-id owner、sweep/read_pool participant 不自锁、外部 writer 全程被挡、缺失/伪造/过期 token、partial metadata、ownership-lost 不误删替代锁。
- [ ] 3.6 `[SW-RI-2]` `[grill-amendment]` 收窄只读锁域到 immutable snapshot materialize 完成、输出前释放，测试 blocked stdout 不占锁且输出不再读文件；在 `sdflow-init/assets/` 新增 canonical runtime-ignore snippet 与 init/update 幂等合并逻辑，保留用户 `.gitignore` bytes、确保 `/openspec/issues/.recorder.lock` 恰好一次，并同步本仓 `.gitignore` dogfood；文档明确 lock 仅为 cooperative boundary。

## 4. Cross-Pool Rename, Snapshot Reuse, and Reindex

- [ ] 4.1 `[SW-RI-1][DG-RI-1]` 在 `issues.py` 加与两 recorder 等价的 frontmatter parser/renderer/lock helpers，使 `_retag_items_in_dated_files` 对 canonical/overlay 更新 frontmatter、对 pure legacy 建 overlay，永不 patch legacy table row。
- [ ] 4.2 `[SW-RI-3]` 重构 `cmd_batch_rename`：每 pool 仅一次 `scan --json`，retag 同步更新内存 items，并允许 `_reindex_core` 接受已验证 snapshot，消除 rename 后第二轮 `read_pool`。
- [ ] 4.3 `[SW-RI-3]` 加 subprocess/open call-count 测试，断言 scan 每 dated 文件 read/parse 各一次、batch rename 每 pool scan≤1；覆盖 bug+todo 多文件与 overlay/legacy 混合输入。
- [ ] 4.4 `[SW-RI-3][SW-RI-4]` 保留 batch rename 非事务但阶段可识别、原命令幂等恢复语义；`[grill-amendment]` 以 registry old/new × items old/new 状态矩阵覆盖继续 retag、主写已完成后补 reindex、双 key/反常残留 fail-closed；注入 dated file/batch key/INDEX/batches 各阶段失败，验证未完全收敛一律非零、错误定位与二次执行收敛，删除 reindex warn-only exit 0 路径。
- [ ] 4.5 `[SW-RI-4]` 更新 reindex fatal/nonfatal 分层：frontmatter/ID 损坏始终非零且不改 INDEX/batches；legacy arity/block problems 默认回显继续、`--strict` 非零；INDEX 与 batches 使用同一 snapshot。

## 5. Remove Legacy Write Machinery and Rebaseline Guards

- [ ] 5.1 `[SW-RI-1]` 删除三脚本 `_reject_cell_unsafe` 与新写路径的表 row render/insert/update、状态双写调用；保留 batch slug 与 Markdown 单行结构的窄校验，不得连带删除已修复的注入守卫。
- [ ] 5.2 `[SW-RI-1][DG-RI-1]` 保留 `split_sections`/`parse_table_rows` 仅供 legacy read/overlay promotion，补调用图/monkeypatch 测试证明 canonical/overlay writer 不调用它们。
- [ ] 5.3 `[DG-RI-1]` 更新 `test_mirror_consistency.py` 显式 THREE_WAY/TWO_WAY roster，覆盖 text+bytes atomic write、binary frontmatter/lock/canonical-ID helpers及 `[grill-amendment]` Unicode escape/canonical sort+null renderer，移除 `_reject_cell_unsafe`，加 call-graph 断言 dated writer 不走 text helper，保留 docstring-ignore、missing-helper fail 与 PRIORITIES 独立值断言。
- [ ] 5.4 `[SW-RI-1][SW-RI-2][SW-RI-3]` 更新三个脚本 module docstring、对应 `SKILL.md` 与用户错误提示：新盘面、overlay precedence、canonical ID、lock 冲突/恢复、`next-id` advisory、CLI/JSON 稳定接口。

## 6. Migration Evidence, ADR, and Reconciliation

- [ ] 6.1 `[SW-RI-1][SW-RI-4]` 对仓内全部现存 buglist/todolist 文档跑升级前 baseline vs 新 dual-reader 对账，关键字段逐 item 相等；不得把移动中的 item 总数写成硬编码长期断言。
- [ ] 6.2 `[SW-RI-1][SW-RI-2][SW-RI-3][DG-RI-1]` 新增后继 ADR，记录 `[grill-amendment]` shared envelope/bytes canonical renderer、same-file overlay+marker、全局 semantic ID、exclusive snapshot lock owner/participant 与 rename 阶段恢复，并声明 supersede `adr/0010` 的“Markdown 表 + reject/defer”新写决策；同步 `openspec/CONTEXT.md` 稳定术语。
- [ ] 6.3 `[SW-RI-1][SW-RI-3]` 用真实 recorder 命令 dogfood：在 legacy 2026-07 todolist 文件上将 T85/T66/T67/T146 的变更写成 overlay，确认旧表未改、`scan --json` 当前值正确、`reindex --strict` 收敛；最终状态只在交付闭环时置 DONE。
- [ ] 6.4 `[SW-RI-1][SW-RI-3]` 更新 mechanical-layer-hardening roadmap/task-log 与 issues batches/index 的交付记录，确保 T85/T66/T67/T146 全部关联本 change，T2 保持 DONE 且注明根治已兑现。

## 7. Verification

- [ ] 7.1 `[SW-RI-1][SW-RI-2][SW-RI-3][SW-RI-4]` 运行 `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error`，确认三 recorder 定向套件全绿且无 warning。
- [ ] 7.2 `[DG-RI-1]` 单独运行 mirror consistency 测试并做 source grep：三脚本无 `import yaml`、无跨 recorder import、无 `_reject_cell_unsafe` 活引用、新 writer 无 legacy table mutation。
- [ ] 7.3 `[SW-RI-1][SW-RI-2][SW-RI-3][SW-RI-4][DG-RI-1]` 运行全仓 `pytest -W error`、`openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` 与 `git diff --check`，保存命令/计数/结果供 verify-report。

## Test Coverage Diagram（TG-18）

```text
code path / contract                    unit                 integration                 regression
────────────────────────────────────────────────────────────────────────────────────────────────────
strict FM parse/render + bad matrix  ─▶ parser fixtures  ─▶ scan canonical/overlay  ─▶ full legacy corpus
legacy table + overlay shadow        ─▶ merge fixtures   ─▶ set-status/triage       ─▶ T1-T5 scenarios
canonical ID                         ─▶ prefix/ID matrix ─▶ add + cross-pool scan   ─▶ existing custom-ID tests
snapshot lock + atomic write         ─▶ fault injection ─▶ reader/writer + 20 add  ─▶ all snapshot/mutating CLIs
batch rename snapshot reuse          ─▶ call counts     ─▶ mixed-pool rename/retry ─▶ reindex/sweep suites
mirror helper parity                 ─▶ AST/value tests ─▶ import isolation        ─▶ full pytest -W error
```

## Requirement Traceability

| Requirement | Tasks |
|---|---|
| `SW-RI-1` | 1.1–1.4, 2.1–2.5, 4.1, 5.1–5.2, 5.4, 6.1–6.4, 7.1–7.3 |
| `SW-RI-2` | 3.1–3.6, 5.4, 6.2–6.3, 7.1–7.3 |
| `SW-RI-3` | 4.2–4.4, 5.4, 6.3–6.4, 7.1–7.3 |
| `SW-RI-4` | 1.3, 2.2, 4.4–4.5, 6.1, 7.1, 7.3 |
| `DG-RI-1` | 1.2, 2.1, 3.1–3.2, 4.1, 5.2–5.3, 6.2, 7.2–7.3 |
