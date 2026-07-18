# Tasks — mlh-p6-recorder-frontmatter

> Requirement IDs：`SW-RI-1` frontmatter/overlay、`SW-RI-2` ID+并发、`SW-RI-3` 单次解析/rename snapshot、`SW-RI-4` reindex 可观测性、`DG-RI-1` 镜像一致性。实现顺序遵 design Migration Plan：dual-reader 先于新 writer，确保任何中间提交与回滚都能读取已产生的新格式。

## 1. Contract Fixtures and Parser TDD

- [x] 1.1 `[SW-RI-1]` 为 bug/todo 建立 canonical、pure-legacy、overlay 三类文档 fixture，覆盖同文件 shadow、新 frontmatter-only item、`|`/换行/Unicode round-trip，并记录升级前 legacy scan baseline；`[grill-amendment]` 加 summary 含 `## fake`/`---`/多行的 fixture，断言 heading 单行投影、逐行 blockquote 与 block identity 不受注入。
- [x] 1.2 `[SW-RI-1][DG-RI-1]` 先写失败测试固定 planned bytes helpers `read_recorder_document` / `parse_recorder_document` / `render_recorder_namespace`、v1 schema、固定字段顺序、JSON duplicate-key 拒绝与 parse→render→parse 等价；`[grill-amendment]` 增加 item permutation golden bytes、semantic ID sort、pool-specific object order、null-only optional、`items: {}`、render→render byte identity，以及共享 envelope 的 BOM/EOL/unknown-content/Unicode 保真 fixture；`[spec-review-amendment]` 把 envelope lexical profile 的接受类（plain ASCII 顶层 key + 缩进 block/quoted/flow value）和拒绝类（quoted/explicit/complex key、sequence/directive/tab/未缩进 continuation/ownership 变体）逐类做 byte golden，不再用笼统 unknown-content 代替 grammar。
- [x] 1.3 `[SW-RI-1][SW-RI-4]` 建坏输入矩阵：未知 schema、pool/path 不符、非法 mode、tab/缩进、重复 namespace/ID/JSON key、缺字段、类型/枚举越域；`[grill-amendment]` 补 change/batch 空串、裸 `items:`、module/summary 纯空白、canonical+legacy 区域、overlay/legacy 区域缺失/重复、namespace 非标准同名拼写、正文伪 frontmatter、编码/EOL/Unicode/boundary 歧义；`[spec-review-amendment]` 补 Arabic-Indic/fullwidth/mixed ID digits 与 scan JSON 缺键/错型/缺 file；逐例断言 non-zero、三段式 `ERROR: problem; cause; fix`、path/ID+field+reason、JSON stdout 无污染、无 legacy fallback、原 bytes/INDEX/batches 不变。
- [x] 1.4 `[SW-RI-1]` 写 merge/block 失败测试：namespace 缺失才走 legacy、overlay 同文件 semantic ID frontmatter 胜、frontmatter-owned 与未 promotion legacy relation 分区、跨文件重复仍 fatal、新格式 prose 不参与当前 status/batch 判定；`[grill-amendment]` 新 block 只认成对 marker，覆盖缺对/错 ID/嵌套/重复/orphan、bug 缺块、todo 无块合法与首次历史建 minimal block；另覆盖 promotion 原位包裹后内部 bytes 不变、后续不回退 heuristic，以及缺块/多块/歧义 bug fail-closed；`[spec-review-amendment]` legacy 候选 block 内预存任一精确 marker 时写前拒绝且原 bytes 不变。

## 2. Dual Reader and Deterministic Frontmatter Writer

- [x] 2.1 `[SW-RI-1][DG-RI-1]` 在 `buglist.py` 与 `todolist.py` 实现严格 bytes frontmatter parser/renderer、document format 判定与 legacy/overlay merge；`[grill-amendment]` 每 dated 文件一次 binary read，scanner 仅在 byte 0/UTF-8 BOM 后识别 envelope，只解释唯一顶层 `sdflow-issues` 子树、其它内容 opaque 保留，禁止 universal-newline text round-trip/二次读取，ambiguous encoding/EOL/boundary fail-closed；此步保持旧 writer，先让全部现有 scan 测试与新 reader 测试通过。
- [x] 2.2 `[SW-RI-1][SW-RI-4]` 把 `cmd_scan` 重构为一次 `parse_recorder_document` 产出 items/blocks/problems/format，保留 legacy 7/8 列 arity、重复 ID 与 prose relation 可观测性；`[grill-amendment]` 同次 parse 计数 legacy 总览区域并互证 mode（mismatch fatal），canonical/overlay block_ranges 改读精确 start/end marker，legacy 才读 heading/`---` heuristic；`[spec-review-amendment]` effective owner 按 semantic key 分区，frontmatter-owned item 不跑 legacy 双写检查，marker ownership/partial-promotion 冲突 fatal。
- [x] 2.3 `[SW-RI-1]` 切换 `ensure_file`/`cmd_add`：新文件写 `mode=canonical`；已有 legacy 文件创建/更新 `mode=overlay`；`[grill-amendment]` 已有共享 envelope 只 splice 唯一 `sdflow-issues` 子树并逐字节保留其余内容；索引只写 frontmatter，CLI/JSON 返回 shape 不变。
- [x] 2.4 `[SW-RI-1]` 切换 `set-status` 与 `triage`：legacy item 先提升完整 overlay，canonical/overlay 原位更新；`[grill-amendment]` promotion 对唯一旧 block 只插外围 marker、内部 bytes 不变，todo 无块建 minimal block，bug 缺块/多块/边界歧义拒绝；`[spec-review-amendment]` 孤立 raw `A007` 仅作 legacy alias，promotion key/marker/result canonicalize 为 `A7`，按 semantic key shadow；候选块预存 marker 写前拒绝；状态历史追加到 end marker 前，后续 mutation 只按 marker 定位；旧表/旧属性表逐字节不变。
- [x] 2.5 `[SW-RI-1]` 新格式 prose block 移除可变 status/batch 副本；`[grill-amendment]` 用成对 ID marker 定界并 escape 用户内容中的精确 marker 独占行，显式 title 仅拒 CR/LF/NUL，缺省 display title 由 summary 连续空白折叠派生，完整 summary 逐物理行加 `> ` 渲染且不反解析；用窄 line-safety helper 或安全逐行 renderer 保住 source/project/date/note 的 Markdown 结构，允许普通详情 prose 自由包含 heading/separator/fence。

## 3. Canonical IDs and Repository Lock

- [x] 3.1 `[SW-RI-2][DG-RI-1]` 实现 canonical ID key/validation：`[grill-amendment]` 新写保留单字母自定义 prefix、统一接受 ASCII `[A-Z][1-9][0-9]*`，默认 B/T；用 ASCII 类/`re.ASCII` 拒绝 Unicode digits，prefix 非单个 ASCII 大写字母拒绝，legacy `A007` vs `A7` 按 `(prefix, decimal)` 语义冲突并报告全部 pool/位置；`[spec-review-amendment]` 覆盖孤立 raw alias promotion 与输出 canonicalization。
- [x] 3.2 `[SW-RI-2][DG-RI-1]` 实现三份一致的 `recorder_lock(root, command)`：`O_CREAT|O_EXCL`、repo/owner metadata + 高熵 token、fail-fast、metadata 初始化窗口保守判 occupied、`finally` identity+token best-effort release、stale/partial-lock 恢复指引；`[spec-review-amendment]` 不泄露 token、不 TTL 自动偷锁，终检前替代锁保留，明确 compare-and-unlink 不可得的终检后 TOCTOU residual；partial metadata 走“停该 repo 全部 recorder→删精确路径→重试”break-glass。
- [x] 3.3 `[SW-RI-2]` 把 bug/todo scan/next-id/add/set-status/triage 与 issues reindex/sweep、`batch lint/add/set-status/rename` 纳入同一 exclusive snapshot lock；`[grill-amendment]` 独立权威读也作 owner；`[spec-review-amendment]` 除纯参数/root 解析外，所有 discovery/stat/open 都在 acquire/participant validation 后；token 可由已验证 participant 仅向同 repo allowlist recorder 子进程原样转发，非 allowlist child env 必须剥离，覆盖 `sweep→reindex→scan`；禁止前后 existence check 或全局无条件 `--no-lock`。
- [x] 3.4 `[SW-RI-2]` 把自动 ID 的 scan max+1、显式 ID 查重和最终写盘放进同一锁区；`[grill-amendment]` 自定义 prefix 的 `next-id`/add 必须扫描 bug+todo 两池 semantic keys，跨 pool 显式冲突失败、自动分配跳到下一全局可用号；`next-id` 保持只读 advisory，并补释放后竞态测试。
- [x] 3.5 `[SW-RI-2]` 加 20 进程并发 add、lock conflict、bytes render/write/chmod/replace fault injection 与 stale lock 测试，断言成功 ID 唯一、失败显式、原 bytes/mode 不变、无正常路径残留 lock/tmp；`[grill-amendment]` 覆盖 reader↔writer 双向 barrier、独立 scan/next-id owner、sweep/read_pool participant 不自锁、缺失/伪造/过期 token、partial metadata、ownership-lost；`[spec-review-amendment]` 加两 namespace 合规 producer 共享 document lock barrier、嵌套 allowlist delegation 与非 allowlist token 剥离，并明确绕锁 producer 是不保证的 residual、不得伪造 fingerprint/CAS 保证。
- [x] 3.6 `[SW-RI-2]` `[grill-amendment]` 收窄只读锁域到 immutable snapshot materialize 完成、输出前释放，测试 blocked stdout 不占锁且输出不再读文件；`[spec-review-amendment]` 新增 canonical `sdflow-init/assets/snippets/runtime-gitignore.txt` 与 `init.py::merge_runtime_gitignore()`，init/update 两路覆盖缺失/已有/重复/用户 bytes，确保 `/openspec/issues/.recorder.lock` 恰好一次，并同步本仓 `.gitignore` dogfood；文档明确 shared document lock/cooperative residual、POSIX/Windows/network FS 与 process-crash/power-loss 边界。

## 4. Cross-Pool Rename, Snapshot Reuse, and Reindex

- [x] 4.1 `[SW-RI-1][DG-RI-1]` 在 `issues.py` 加与两 recorder 等价的 frontmatter/legacy parser、renderer、semantic-ID、relation 与 lock helpers，planned `read_rename_snapshot()` 对两池每 dated 文件一次 binary read 即保留 raw bytes/spans/model/effective items/problems；canonical/overlay 更新 frontmatter、pure legacy 建 overlay，永不 patch legacy table row。
- [x] 4.2 `[SW-RI-3]` 重构 `cmd_batch_rename`：禁止先 `scan --json` 再二次打开 dated files；直接复用 `read_rename_snapshot()`，retag 同步更新 per-file model 与内存 items，并让 `_reindex_core` 接受已验证 updated snapshot，整个 rename per-pool scan=0、每 dated file read/parse=1。
- [x] 4.3 `[SW-RI-3]` 加 subprocess/open call-count 与 bytes-preservation 测试，断言 scan 及整个 batch rename 每 dated 文件 read/parse 各一次、rename 每 pool `scan --json`=0；覆盖 bug+todo 多文件、overlay/legacy 混合、BOM/CRLF/external sibling，并证明 raw span 不经 text round-trip。
- [x] 4.4 `[SW-RI-3][SW-RI-4]` 保留 batch rename 非事务但有 provenance、原命令幂等恢复语义；`[spec-review-amendment]` 首次严格预检后 registry-first 原子写 header new + machine-owned `重命名自: old`，再 retag/reindex；以 registry/provenance × items old/new 状态矩阵覆盖全 old/混合/全 new recovery、无 provenance 的 old-missing 误输、preexisting new orphan、双 key fail-closed；注入 registry/dated/INDEX/batches 各阶段失败，验证未完全收敛一律非零、错误含 stage+原命令，删除写/reindex failure 的 warning-only exit 0；与 retag 无关的 legacy nonfatal problems 仍回显并沿用默认 reindex 成功语义。
- [x] 4.5 `[SW-RI-3][SW-RI-4]` 更新 reindex/rename fatal-nonfatal 分层：frontmatter/ID/consumer JSON 损坏始终非零且不改 INDEX/batches；与 retag 无关、item 仍可判的 legacy arity/block problems 默认回显继续、`--strict` 非零；任何影响 batch 判定或 dated/registry/INDEX/batches 写入的失败不得 warning-only exit 0，派生输出使用同一 updated snapshot。

## 5. Remove Legacy Write Machinery and Rebaseline Guards

- [x] 5.1 `[SW-RI-1]` 删除三脚本 `_reject_cell_unsafe` 与新写路径的表 row render/insert/update、状态双写调用；保留 batch slug 与 Markdown 单行结构的窄校验，不得连带删除已修复的注入守卫。
- [x] 5.2 `[SW-RI-1][DG-RI-1]` 保留 `split_sections`/`parse_table_rows` 仅供 legacy read/overlay promotion，补调用图/monkeypatch 测试证明 canonical/overlay writer 不调用它们。
- [x] 5.3 `[DG-RI-1]` 更新 `test_mirror_consistency.py` 显式 THREE_WAY/TWO_WAY roster，覆盖 text+bytes atomic write、binary frontmatter/lock/canonical-ID helpers及 `[grill-amendment]` Unicode escape/canonical sort+null renderer；`[spec-review-amendment]` 把 issues direct rename snapshot 所需 legacy region/semantic overlay/relation/JSON consumer validator 纳入三向行为 golden/roster，移除 `_reject_cell_unsafe`，加 call-graph 断言 dated writer 不走 text helper，保留 docstring-ignore、missing-helper fail 与 PRIORITIES 独立值断言。
- [x] 5.4 `[SW-RI-1][SW-RI-2][SW-RI-3]` 更新 `README.md`、三个脚本 module docstring、对应 `SKILL.md`、`--help` 与用户错误提示：breaking storage/升级步骤、shared envelope lexical profile、overlay precedence、raw legacy ID→canonical promotion、lock/break-glass、`next-id` advisory、CLI/JSON contract、rename provenance/retry、平台/FS/durability 边界；新增失败统一 stderr `ERROR: problem; cause; fix`，stdout JSON 纯净，不新增 doctor/lock-recover/diagnostic-JSON API。
- [x] 5.5 `[SW-RI-3]` 为 `_scan_pool` 增加严格 consumer validator：bug `bugs/problems`、todo `items/problems` 必须为 list，每 item 必需字段/type/enum/file 完整；坏 JSON/缺键/错型 fail-closed 且不写 INDEX/batches，建立 legacy/canonical/overlay contract fixtures与 partial-install 回归。

## 6. Migration Evidence, ADR, and Reconciliation

- [x] 6.1 `[SW-RI-1][SW-RI-4]` 对仓内全部现存 buglist/todolist 文档跑升级前 baseline vs 新 dual-reader 对账，关键字段逐 item 相等；不得把移动中的 item 总数写成硬编码长期断言。
- [x] 6.2 `[SW-RI-1][SW-RI-2][SW-RI-3][DG-RI-1]` 完成后继 ADR-0025：除 `[grill-amendment]` shared envelope/bytes canonical renderer、same-file overlay+marker、全局 semantic ID、exclusive snapshot lock owner/participant 外，纳入 `[spec-review-amendment]` lexical profile、shared document-lock、raw alias promotion、registry-first rename provenance、平台/TOCTOU/break-glass 边界；声明 supersede `adr/0010` 新写决策，并同步 `openspec/CONTEXT.md` 稳定术语。
- [x] 6.3 `[SW-RI-1][SW-RI-3]` 用真实 recorder 命令 dogfood：在 legacy 2026-07 todolist 文件上将 T85/T66/T67/T146 的变更写成 overlay，确认旧表未改、`scan --json` 当前值正确、`reindex --strict` 收敛；最终状态只在交付闭环时置 DONE。
- [x] 6.4 `[SW-RI-1][SW-RI-3]` 更新 mechanical-layer-hardening roadmap/task-log 与 issues batches/index 的交付记录，确保 T85/T66/T67/T146 全部关联本 change，T2 保持 DONE 且注明根治已兑现。

## 7. Verification

- [x] 7.1 `[SW-RI-1][SW-RI-2][SW-RI-3][SW-RI-4]` 运行 `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error`，确认三 recorder 定向套件全绿且无 warning。
- [x] 7.2 `[DG-RI-1]` 单独运行 mirror consistency 测试并做 source grep：三脚本无 `import yaml`、无跨 recorder import、无 `_reject_cell_unsafe` 活引用、新 writer 无 legacy table mutation。
- [x] 7.3 `[SW-RI-1][SW-RI-2][SW-RI-3][SW-RI-4][DG-RI-1]` 运行全仓 `pytest -W error`、`openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` 与 `git diff --check`，保存命令/计数/结果供 verify-report。
  - 完成说明：全仓 `pytest -W error` → `1619 passed, 2 skipped`（2 skip 为 Windows-only smoke）；`openspec validate ... --strict` valid、`git diff --check` 通过。前置 fold 修复见 7.5——清零 4 个 pre-existing 未关闭文件站点后 warning 归零。
- [x] 7.4 `[SW-RI-1][SW-RI-2][SW-RI-3]` 跑已知 consumer smoke：升级安装后以 legacy/canonical/overlay fixture 执行两 recorder `scan --json`、issues `reindex --strict`、`sweep` dry fixture，并校验 JSON schema/INDEX/batches；在 Windows local-disk runner 跑 acquire/conflict/participant/replace/cleanup + setup copy smoke，记录 network FS 与 power-loss durability 为非承诺而非假绿跳过。
  - 完成说明：consumer smoke 已在定向套件通过；actual Windows local-disk smoke 在 `windows-latest` runner 取得无 skip `2 passed in 20.73s`（run 29568476168，commit `ba004e1`）。收尾途中经真 Windows 暴露并修两处测试层问题（`bash` 解析走 System32 的 WSL launcher、subprocess text 模式未指定 utf-8 致读线程解码崩），非 recorder/setup.sh 代码 bug。

- [x] 7.5 `[SW-RI-1][SW-RI-2][SW-RI-3][SW-RI-4][DG-RI-1]` fold 清零全仓 `-W error` 门下的 4 个 pre-existing 未关闭文件站点：`sdflow-maintain/scripts/maintain_scan.py:184/:244`（裸 `open().read()`，mlh-p4-maintain-scan 引入）、`sdflow-maintain/tests/test_maintain_scan.py:224`（裸 `open(...,"w").write()`，同 change 引入，`-W error` 面治新发现，非「37 全在读」）、`sdflow-architecture/tests/test_sad_scaffold.py:525`（并发 `Popen(PIPE)` 只 `wait()` 不 drain，add-sdflow-architecture 引入），分别用 `with`/`communicate()` 收口；连带修正两 recorder 镜像的 `cmd_triage` docstring 陈旧表格双写描述（对应 T153）。站点以全仓 `-W error` 权威枚举（非正则手搓）。全仓机械守卫（把全仓 `-W error` 常态化为持久 CI 门）超出本 change 内聚范围，另开 hardening change（登记 todolist T155）。

## Test Coverage Diagram（TG-18）

```text
code path / contract                    unit                 integration                 regression
────────────────────────────────────────────────────────────────────────────────────────────────────
strict FM parse/render + bad matrix  ─▶ parser fixtures  ─▶ scan canonical/overlay  ─▶ full legacy corpus
legacy table + overlay shadow        ─▶ merge fixtures   ─▶ set-status/triage       ─▶ T1-T5 scenarios
canonical ID                         ─▶ prefix/ID matrix ─▶ add + cross-pool scan   ─▶ existing custom-ID tests
snapshot lock + atomic write         ─▶ fault injection ─▶ reader/writer + 20 add  ─▶ all snapshot/mutating CLIs
batch rename direct bytes snapshot  ─▶ call counts     ─▶ provenance rename/retry ─▶ reindex/sweep suites
scan JSON consumer contract         ─▶ bad envelopes   ─▶ partial-install failure ─▶ known-consumer smoke
mirror helper parity                 ─▶ AST/value tests ─▶ import isolation        ─▶ full pytest -W error
```

## Requirement Traceability

| Requirement | Tasks |
|---|---|
| `SW-RI-1` | 1.1–1.4, 2.1–2.5, 4.1, 5.1–5.2, 5.4–5.5, 6.1–6.4, 7.1–7.4 |
| `SW-RI-2` | 3.1–3.6, 5.4, 6.2–6.3, 7.1–7.4 |
| `SW-RI-3` | 4.2–4.4, 5.4–5.5, 6.3–6.4, 7.1–7.4 |
| `SW-RI-4` | 1.3, 2.2, 4.4–4.5, 6.1, 7.1, 7.3 |
| `DG-RI-1` | 1.2, 2.1, 3.1–3.2, 4.1, 5.2–5.3, 6.2, 7.2–7.3 |
