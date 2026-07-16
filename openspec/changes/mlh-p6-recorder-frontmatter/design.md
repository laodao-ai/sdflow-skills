# Design: mlh-p6-recorder-frontmatter

## Context

`sdflow-buglist/scripts/buglist.py` 与 `sdflow-todolist/scripts/todolist.py` 当前把每条 item 的八个索引字段写入 dated Markdown 表，再把详情写入 prose 块；`sdflow-issues/scripts/issues.py` 通过两个 recorder 的 `scan --json` 聚合数据，并在 `batch rename` 时直接改 dated 文件表格。三个脚本均已使用 `tempfile.mkstemp` + `os.replace` 的 `atomic_write`，但没有跨进程互斥；`next_id()` 的“扫描 max+1”与后续写盘之间存在竞态。

现有 `parse_table_rows()` 按 `|` 位置切列，`_reject_cell_unsafe()` 因而必须拒绝索引字段中的 `|` 与换行。`scan` 还要同时维护行 arity、重复 ID、表↔块与状态双写一致性检查。`issues.py::cmd_batch_rename()` 先 `read_pool()`，写完后 `_reindex_core()` 再读一次两池，形成 T66 的重复工作。

本设计落实 mechanical-layer-hardening P6 与 T85，并 fold T66、T67、T146。已核实仓内 recorder 消费者通过 CLI/JSON 接口读取；除三个 recorder 及其测试外，没有另一个生产脚本直接解析 dated 文件总览表。存量文档仍含大量未终态 item，因此“历史表冻结只读”不能等同于“历史 item 永远不可变”。

**Stakeholders（TG-20）**：仓库 owner 对存储兼容策略有决策权；recorder CLI 使用者与消费仓维护者有知情权；`sdflow-done`/`issues.py sweep` 等调用方依赖 CLI/JSON 稳定性，无需配合改调用方式。

## Goals / Non-Goals

**Goals:**

- 新 item 的机器索引只写 versioned frontmatter，不再写 Markdown 总览表；`|`、换行与 Unicode 可无损 round-trip。
- 历史表格零批量改写且永不再写；历史 item 仍可 `set-status`、`triage`、`batch rename` 和 `sweep`。
- frontmatter 坏数据 fail-closed；不存在 namespace 才允许回退 legacy table，namespace 在场但损坏不得回退。
- 自定义 ID 在语义上唯一；所有 recorder 写事务由仓级互斥串行化并保持原子替换。
- `scan` 每文件只读/解析一次；`batch rename` 每池只扫描一次并复用更新后的 snapshot 完成 reindex。
- 保持 recorder 自包含、不建立跨 skill import；用镜像一致性测试兜住共享机械逻辑。

**Non-Goals:**

- 不迁 `issues/batches.md`。可证伪假设：其 header/人写字段 grammar 与 item 索引腐蚀面正交；若未来出现两次同类结构腐蚀，再单开 T72 类 change。
- 不批量迁移所有 legacy dated 文件。可证伪假设：按访问建立 overlay 足以覆盖活跃历史 item；若实现后一次常规 sweep 需提升超过 100 个 legacy item，重新评估一次性迁移成本。
- 不实现 T123 的可插拔 tracker backend。可证伪假设：当前唯一持久层仍是本地 Git 文档；出现第二个真实 backend 消费方时再抽象。
- 不改变状态机、优先级/类型枚举、DONE/FIXED 门禁或 sweep 的非原子重跑语义。可证伪假设：现有业务语义能完整映射到新索引；若映射测试发现字段缺失，先扩 schema，不顺手改状态机。
- 不修改 `sdflow-init/assets/workflow/`。可证伪假设：三个 recorder 均由顶层 skill 自身安装运行；若实现搜索发现 bundle 副本，必须改权威源并重开影响面核对。

## Component Inventory（TG-13/14）

| Component | 职责 | 技术/部署 | 本 change |
|---|---|---|---|
| `buglist.py` | bug item add/read/update/triage/scan | stdlib Python；skill symlink/复制 | 新格式 producer + legacy/overlay consumer + lock；`[grill-amendment]` dated 文件 bytes pipeline |
| `todolist.py` | todo item add/read/update/triage/scan | stdlib Python；skill symlink/复制 | 同上，保留 todo 独立枚举/轻量块语义 |
| `issues.py` | 两池聚合、reindex、sweep、batch registry/rename | stdlib Python；子进程消费 recorder CLI | 复用 snapshot；直接 retag 时写 frontmatter/overlay；同一仓锁；dated 文件 bytes splice |
| dated Markdown 文件 | Git 中的 item 盘面 | YAML-subset frontmatter + Markdown prose | 新文件 canonical；旧文件可增加 overlay，旧表不改 |
| `issues/INDEX.md` / `batches.md` | 生成索引 / 半手批次注册表 | Markdown | 输出语义不变；输入 snapshot 改由 dual-read 得到 |
| mirror consistency tests | 防三个自包含副本逻辑漂移 | pytest + AST 等价 | 更新 helper roster，覆盖 parser/renderer/lock |
| `sdflow-init` runtime ignore `[grill-amendment]` | 消费仓忽略短生命周期 lock | canonical asset + init/update merge | 新增 `.recorder.lock` 幂等 ignore，保留用户 `.gitignore` bytes |

## Data Model and Lifecycle（TG-05）

### Frontmatter v1

使用 YAML-compatible 的严格子集：外层是固定缩进键，`items` 下每个 ID 的值是**单行 JSON object**。JSON 是 YAML 1.2 flow mapping 的合法子集，可直接用 stdlib `json` 完成字符串转义、重复键检查和 round-trip，无需 `PyYAML`。

```yaml
---
sdflow-issues:
  schema: 1
  pool: todo
  mode: overlay
  items:
    T85: {"module":"roadmap mechanical-layer-hardening / recorder","summary":"支持 | 与\n换行","type":"基础设施","status":"PROPOSED","time":"2026-07-08 15:55","change":null,"batch":"mlh-p4-target-state"}
---
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `schema` | integer | v1 仅允许 `1`；未知版本 fail-closed |
| `pool` | enum | `bug` / `todo`，必须与 recorder/路径一致 |
| `mode` | enum | `canonical` / `overlay`；`[grill-amendment]` 必须与 legacy 总览区域物理形态互证 |
| `items` | map<ID, object> | ID 键在文件内唯一，固定缩进，一 item 一物理行 |
| `module` | string | 非空 |
| `summary` | string | 非空；允许 `|`、换行、Unicode scalar values，由 JSON 转义；孤立 surrogate 非法 |
| `priority` | enum | bug 专属，值域沿用 `PRIORITIES` |
| `type` | enum | todo 专属，值域沿用 `TYPE_TAGS` |
| `status` | enum | 按 pool 沿用 `STATUS_CODES` |
| `time` | string | 保持现有 CLI 输出值，不在本 change 重定义时间格式 |
| `change` | string/null | provenance；非空时不可由 triage 改写 |
| `batch` | string/null | 可变 triage 归属；仍受 batch slug 契约 |

`[grill-amendment]` v1 canonical renderer 只有一种输出：顶层顺序固定 `schema,pool,mode,items`；item 按 semantic ID `(ASCII prefix, decimal integer)` 排序；bug object 顺序固定 `module,summary,priority,status,time,change,batch`，todo 固定 `module,summary,type,status,time,change,batch`，字段不得省略。`change/batch` 无值只写 JSON `null`，writer 把输入空串规范化为 null，reader 拒绝 frontmatter 中这两字段的 `""`。`module/summary` 至少含一个非-whitespace Unicode scalar，但保留原始前后空白/code points。空 map 唯一写作 `items: {}`，裸 `items:` 非法。reader 可接受 item 任意物理顺序；writer mutation 在自有 namespace 内按 canonical form 重排。parse→render→parse 语义等价，render→render byte-identical。

**物理格式规则** `[grill-amendment]`：frontmatter envelope 只有在 opener `---` 位于 byte 0，或紧随 UTF-8 BOM 时才成立；opener/closer 必须各自独占一行，不扫描正文寻找“第一个像 frontmatter 的 block”。该 envelope 由多个工具共享；recorder 只拥有唯一、无引号的顶层 `sdflow-issues:` namespace 及其完整子树，`schema/pool/mode/items` 不展开成多个带前缀的顶层键，也不提升为多工具共管的 `sdflow:` 父树。reader 只严格校验 recorder 子树，把其它顶层条目视为外部所有的 opaque 内容；writer 以 UTF-8 bytes 定位并只插入或替换 recorder 子树，必须逐字节保留 envelope 中其余键、注释、空行、顺序、标量样式、BOM、原有 EOL 与正文。namespace 缺失时按 legacy 文件处理；namespace 在场但重复，或 envelope 边界无法被窄 scanner 无歧义定位，整文件 fatal 且不得写盘；recorder 子树的缩进/tab/JSON/字段/枚举/版本任一非法同样 fatal，MUST NOT 回退 legacy 表。writer 固定 recorder 子树字段顺序、紧凑 JSON，并在写前从内存对象重新校验。

`[grill-amendment]` canonical string domain 是 Unicode scalar values：任何字段中的孤立 UTF-16 surrogate `U+D800..U+DFFF` 必须在 render/write 前按 ID+field fail-closed。JSON renderer 保持 `ensure_ascii=False` 以便普通 Unicode 人读，但把 YAML line-break code points U+0085/U+2028/U+2029 定向输出为 `\u0085`/`\u2028`/`\u2029`；stdlib JSON 继续转义 CR/LF/tab/C0。parser 拒绝 recorder 子树里的 raw NEL/LS/PS，接受 escaped form 并还原原 code point。不得做 NFC/NFKC normalization，parse→render→parse 保持原始 code points。

`[grill-amendment]` 已有 envelope 中新渲染的 recorder 子树沿用 opener 的 LF 或 CRLF；替换时只允许自有子树内部规范化。legacy 文件没有 envelope 时，在 BOM 后或 byte 0 插入，新 envelope 沿用正文首个可识别 LF/CRLF，无 EOL 时使用 LF；新建 canonical 文件固定 UTF-8、无 BOM、LF。UTF-16 BOM、非法 UTF-8、lone CR、opener/closer 缺失换行或 EOL 无法安全判定均 fail-closed，原 bytes 不变。

### Lifecycle

1. **Create**：目标 dated 文件不存在时，建立 `mode: canonical` 空索引；`add` 在锁内分配 ID、插入索引，并按 pool/payload 语义追加 prose 块（bug 必有，todo 轻量项可无）。目标文件是 legacy 时，建立/更新 `mode: overlay`，新 item 只进 frontmatter，不加表行。
2. **Read**：`[grill-amendment]` 先验证 format invariant：canonical 必须不存在 recorder legacy 状态总览区域；overlay 必须恰有一个该区域；namespace 缺失的 legacy 也必须恰有一个该区域。mode 与物理形态 mismatch fatal，MUST NOT 通过 enum 手改隐藏 items。通过后 canonical 只读 frontmatter；纯 legacy 只读表；overlay 读 frontmatter + legacy 表并合并，同文件同 ID 时 frontmatter 显式 shadow legacy snapshot。overlay 区域内坏 row 仍进入既有 arity/problems 分层，区域本身缺失/重复则不是普通 problem。
3. **Update**：canonical/overlay item 原位更新 frontmatter。更新纯 legacy item 时，先从表行构造完整 v1 item 写入 overlay；`[grill-amendment]` 若存在唯一且边界可判的 legacy prose block，只在其前后插入同 ID start/end marker，块内 bytes 不变，再执行状态/批次变更并把历史追加到 end marker 前。legacy todo 无 block 时创建 marker-framed minimal block；legacy bug 缺块、同 ID 多块或边界有歧义时 mutation fail-closed。历史表行与旧属性表不改，后者视为 snapshot，不再参与状态一致性判定；promotion 完成后该 item 永久只按 marker 定位。
4. **Aggregate**：`scan --json` 输出 shape 不变；`issues.py` 只消费合并后的 canonical snapshot。
5. **Archive/Delete**：本 change 不新增删除动作；Git 历史继续承担审计与回滚。终态 item 仍留原文件，INDEX 只生成摘要。

### ID semantics

- `[grill-amendment]` 新写 ID 统一允许 `[A-Z][1-9]\d*`；bug 默认 prefix=`B`、todo 默认 prefix=`T`，公开的单字母自定义 `--prefix` 保持兼容。prefix 只接受一个 ASCII 大写字母，小写、多字母、空串均在业务读取/写盘前拒绝。
- ID semantic key 是 `(uppercase prefix, decimal integer)`，不包含 pool；legacy reader 可读取既有 `[A-Z]\d+` 语料并计算该 key，`A007` 与 `A7` 视为冲突并 fail-closed 报出两个位置，不静默挑一个。
- ID 在 bug+todo 两池仓级全局唯一；bug `A1` 与 todo `A1` 冲突。自定义 prefix 的 `next-id`、自动 add 与显式 ID 查重必须在同一 snapshot lock 内读取两池全集，MUST NOT 只扫当前 pool。
- 新写与显式 ID 必须是 canonical spelling；`next-id` 只作建议展示，不保留号码，真正分配/查重必须在 `add` 新锁事务内完成。

## Design Diagrams

### C4 Context + Container（TG-13）

```text
Context
┌──────────────┐      CLI / JSON       ┌───────────────────────────┐
│ 人 / sdflow  │ ────────────────────▶ │ sdflow recorder subsystem │
│ orchestrator │ ◀──────────────────── │ (local Python skills)      │
└──────────────┘   result / diagnostics └─────────────┬─────────────┘
                                                     │ atomic local writes
                                                     ▼
                                        ┌─────────────────────────┐
                                        │ Git-tracked openspec/   │
                                        │ issues docs + indexes   │
                                        └─────────────────────────┘

Container
┌──────────────────────────────────────────────────────────────────────┐
│ target repository                                                   │
│  ┌────────────┐  ┌─────────────┐  subprocess JSON  ┌─────────────┐ │
│  │ buglist.py │  │todolist.py  │ ◀───────────────▶ │ issues.py   │ │
│  └─────┬──────┘  └──────┬──────┘                   └──────┬──────┘ │
│        └──────────┬──────┴──────── same repo lock ─────────┘        │
│                   ▼                                                  │
│       openspec/issues/{buglist,todolist}/*.md                        │
│       openspec/issues/{INDEX.md,batches.md,.recorder.lock}           │
└──────────────────────────────────────────────────────────────────────┘
```

### Component / Dependency Diagram

```text
buglist.py / todolist.py / issues.py (self-contained copies)
        │
        ├── recorder_lock(root) ── O_CREAT|O_EXCL ── .recorder.lock
        ├── read_recorder_document(path) ──▶ raw bytes (read once)
        ├── parse_recorder_document(raw) ──▶ model + byte spans + EOL
        ├── render_recorder_namespace(model, EOL) ──▶ bytes
        ├── parse_table_rows(...)              ← legacy read only
        ├── atomic_write_bytes(path, bytes) ── dated files
        └── atomic_write(path, text) ── generated INDEX/batches
                      │
                      ▼
              parsed recorder document
           ┌──────────┼───────────┐
           ▼          ▼           ▼
       canonical    overlay      legacy
       FM only    FM > table    table only
           └──────────┬───────────┘
                      ▼
             stable scan JSON snapshot
                      ▼
             issues.py reindex / batch

AST mirror test compares shared helper behavior; runtime imports remain absent.
```

`[grill-amendment]` dated recorder 文件的存储 API 边界固定为 bytes：单次 binary read 后在 raw bytes 上定位 envelope/namespace/marker spans，仅对自有 span decode/validate/render；不得先 universal-newline text-read，再为 splice 二次 binary-read。`atomic_write_bytes` 复用现有同目录唯一 temp、目标 mode bits（新文件 0644）、`os.replace` 与异常清理语义。完全生成的 INDEX/batches 继续使用 text `atomic_write`。内容保真不扩张为 inode/mtime/xattr/ACL 保真；replace 后这些 metadata 不在契约内。

### Read Data Flow（TG-11）

```text
read file once
    │
    ├─ byte-0 envelope absent / namespace absent ──────────▶ legacy table parse
    │
    ├─ namespace valid, mode=canonical ────────────────────▶ frontmatter items
    │
    ├─ namespace valid, mode=overlay ─▶ legacy rows + FM items ─▶ FM shadows same ID
    │
    └─ namespace present but invalid ──────────────────────▶ fatal non-zero
                                                              (no fallback)
                           │
                           ▼
          validate IDs + enums + block relations once
                           │
                           ▼
                 scan --json stable shape
                           │
                           ▼
              reindex / sweep / batch rename
```

### Concurrent Write Sequence（TG-10/TG-26）

```text
Writer A                 .recorder.lock              Writer B
   │ O_CREAT|O_EXCL ─────────▶│                         │
   │◀──────── acquired ───────│                         │
   │                          │◀──── O_CREAT|O_EXCL ───│
   │ read + validate +        │──── EEXIST + owner ───▶│ fail non-zero
   │ allocate ID + render     │                         │
   │ mkstemp + os.replace     │                         │
   │ unlink lock in finally ─▶│                         │
   │◀──────── released ───────│                         │

Crash before replace: old target intact; lock file remains observable and blocks writes.
Operator verifies owner is gone, then removes the documented lock path and retries.
```

## Decisions

### D1 — Strict YAML-subset + JSON item values; no PyYAML

**Decision**：实现 planned bytes helpers `read_recorder_document()` / `parse_recorder_document()` / `render_recorder_namespace()`，只支持上文 v1 子集；JSON object 由 stdlib `json` 解析并用 `object_pairs_hook` 拒绝重复键。三个 skill 均不得 `import yaml`。`[grill-amendment]` 三份 helper 共享同一 Unicode scalar validation 与 NEL/LS/PS 定向 escape，纳入 AST parity；不能把 UTF-8 encode failure 当字段校验。

`[grill-amendment]` renderer 采用 semantic ID 排序、pool-specific fixed object order、null-only optional emptiness；reader 不因 item 物理乱序失败，但下一次合法 mutation 会只在 recorder namespace 内 canonicalize。选择唯一渲染而非保留插入顺序，是为了让三份自包含实现与 fixture 有 byte-level 唯一期望值；代价是首次修改手工乱序 namespace 时该子树会整体重排。

| Candidate | 系统镜 | 用户镜 | 开发循环镜 |
|---|---|---|---|
| **严格子集 + JSON（选定）** | 零依赖、错误域有界、字符串无损 | frontmatter 可读，坏数据明确点位 | 三份实现可用 AST 守卫，测试矩阵有限 |
| `yaml.safe_load` | 完整 YAML，但消费仓缺库会启动即崩 | 写法自由 | 依赖部署与重复键 loader 定制增加维护 |
| 自定义转义 Markdown 表 | 保留脆弱列模型 | GitHub 表渲染最好 | 三读写器永久背转义/反转义，目标未达 |

**主次判定**：系统镜最重要——recorder 在未知消费仓裸 Python 环境运行，零依赖与 fail-closed 高于允许任意 YAML 语法。当前方案代价是只接受一个文档化子集，手工写其它合法 YAML 也会被拒绝。

#### D1a — Shared frontmatter envelope; recorder owns one prefixed namespace `[grill-amendment]`

**Decision**：把文件起点（可在 UTF-8 BOM 后）的 frontmatter block 视为共享 envelope；recorder 的唯一写权限边界是顶层 `sdflow-issues` 子树。`sdflow-issues` 本身就是 namespace 前缀：内部保持短键 `schema/pool/mode/items`。reader 不替其它工具校验未知顶层内容；writer 以 byte-level 窄 scanner 定位 recorder 子树并做局部 splice，namespace 之外逐字节保留。重复 namespace、非标准拼写造成的所有权歧义或无法确定 splice 边界时 fail-closed，原文件不变。`[grill-amendment]` 正文中的 `---` 永不被提升为 envelope；BOM 与既有 EOL 属外部 bytes，不因 recorder mutation 被规范化。

| Candidate | 所有权边界 | 组合性 | 代价 |
|---|---|---|---|
| **单一顶层 `sdflow-issues` 子树（选定）** | 一棵子树，清晰可验 | 可与 `ship-gate` 等 namespace 共存 | 需窄 scanner、局部 splice 与保真 fixture |
| 展平为 `sdflow-issues-schema` 等多键 | 所有权散落在多个顶层键 | 顶层污染，缺键/版本判断分散 | 写入与冲突矩阵更大 |
| 共用 `sdflow:` 父树再放 `issues:` | 多工具共同改写 `sdflow` 子树 | 表面整齐，实际把冲突下移一层 | 每个工具都需解析并保留兄弟子树 |
| recorder 独占整个 frontmatter | 最简单 | 排斥其它 metadata producer | 会为一次 recorder mutation 删除或拒绝无关元数据 |

**主次判定**：目标态会有多个 metadata producer，所有权清晰与无损组合优先于 renderer 简单。代价由 fail-closed scanner 和 byte-preservation 测试承担，MUST NOT 通过接管整个 envelope 转嫁给其它工具。

### D2 — Legacy table frozen; mutable items promoted into same-file overlay

**Decision**：旧表永不再写。对旧 item 的任何 mutation 都把其完整当前索引提升进同文件 `mode: overlay`；frontmatter 对同文件同 ID 优先。新 item 落到已存在 legacy dated 文件时也写 overlay。legacy 表与旧属性表成为只读 snapshot，状态历史 prose 继续 append。`[grill-amendment]` promotion 同时把可唯一定位的旧 prose block 原位套入 marker，内部 bytes 不重渲染；无块 todo 新建 minimal marker block，坏/歧义 bug block 拒绝 mutation。

`[grill-amendment]` `mode` 是 writer 产生、reader 互证的迁移状态，不是用户输入：新文件由 writer 设 canonical，检测到唯一 legacy 总览区域的既有文件才设 overlay。canonical+legacy 区域、overlay+区域缺失/重复都 fatal，不自动改 mode、不自动删表。

| Candidate | 系统镜 | 用户镜 | 开发循环镜 |
|---|---|---|---|
| **同文件 overlay（选定）** | 单文件仍是完整盘面；无永久旧 writer | 不批量改历史，旧 item 可闭环 | dual-read 合并规则明确，可逐项 dogfood |
| 首次 mutation 懒迁整文件 | 单一新格式最干净 | 一次状态变更会重写整篇历史 | converter/大 diff/回滚成本高 |
| 永久保留 legacy writer | 兼容最直接，但两套 writer 永久存在 | 文档形态不变 | T85 根治失败，T66/T2 机械继续维护 |
| 跨文件 sidecar overlay | 历史文件零字节变化 | 需跨文件追真相 | 引入第二盘面与 join 漂移 |

**主次判定**：用户镜与系统镜共同主导——既要历史表不被改写，也要未终态 item 可操作；同文件 overlay 是唯一同时满足两条的方案。代价是 overlay 文件短期包含“旧 snapshot + 新 canonical”两层，必须靠显式 `mode` 与 shadow 规则消歧。

### D3 — One repository-wide fail-fast lock

**Decision** `[grill-amendment]`：planned helper `recorder_lock(root, command)` 用 `O_CREAT|O_EXCL` 获取 `openspec/issues/.recorder.lock`，它是仓级 **exclusive snapshot lock**，不是仅保护 writer。顶层权威 snapshot/read-modify-write CLI 是 lock **owner**；只读命令从第一次业务文件读取持有到全部输入已读取、解析、校验并固化成不再访问文件的内存 snapshot，随后先释放、再格式化/打印，MUST NOT 因慢 stdout 延长锁；mutation 从第一次业务读取持有到最后一次 `os.replace` 完成。范围至少包含 bug/todo `scan`、`next-id`、add/set-status/triage，以及 issues 的 reindex/sweep、batch query/mutation/rename。owner 生成高熵 capability token，锁文件记录 PID、命令、开始时间与 token；复合命令启动的 scan 或 mutating 子进程通过专用环境变量继承 token，校验它与当前锁文件一致后作为 **participant** 加入同一锁域，不重复 acquire、不得 release。锁冲突立即非零退出，不等待、不自动偷锁；错误信息打印 owner 与安全恢复步骤但不得泄露 token。`next-id` 持锁只保证计算时 snapshot 一致，释放后仍是 advisory、绝不构成 reservation。

`O_EXCL` 成功即代表锁已占用，即使竞争者恰好读到 owner metadata 尚未写完，也只能报告“owner metadata unavailable/initializing”，MUST NOT 当成 stale 或空锁继续。owner 用已打开的独占 FD 写完整 metadata 并按需 `fsync`；退出 `finally` 释放前重新读取并核对 token，只能 unlink 自己仍拥有的锁。若锁文件被人工删除并被另一 writer 重建，旧 owner 必须保留新锁并报告 ownership lost。

`[grill-amendment]` 该锁是 cooperative boundary：只约束采用 recorder 协议的 CLI，不能阻止编辑器、手工脚本或 Git 绕过锁修改文件，文档与错误提示不得宣称 OS 级强制隔离。为避免运行中 lock 被 dirty-tree/checkpoint 收入版本，`sdflow-init` SHALL 新增 canonical runtime-ignore snippet，并在 init/update 时幂等合并根 `.gitignore` 的 `/openspec/issues/.recorder.lock`；本仓同步 dogfood 该条目。当前仓内尚无此 canonical ignore 资产，故本 change 必须显式新增，不能假设已有生成规则。

| Candidate | 系统镜 | 用户镜 | 开发循环镜 |
|---|---|---|---|
| **仓级 O_EXCL fail-fast（选定）** | 跨三个进程/多文件写统一串行，跨平台 | 冲突立刻可见，不假装成功 | stdlib、与 T146 指定范式一致 |
| per-file lock | 并行度高，但 ID 与 batch rename 仍跨文件竞态 | 可能部分成功 | 锁顺序/死锁面扩大 |
| `fcntl` advisory lock | 自动随进程释放 | 体验好 | Windows 不可用，破跨平台 |
| 无锁 + 仅原子替换 | 不会半文件，但会 lost update/重复 ID | 静默丢写 | 无法达成 T146 |

#### D3a — Composite commands and authoritative reads share one snapshot lock `[grill-amendment]`

| Candidate | 跨子步隔离 | 自包含边界 | 失败面 |
|---|---|---|---|
| **父命令/独立读 owner + token participant（选定）** | snapshot materialize 或 mutation 完成前无 writer 插入 | 保留 subprocess CLI 解耦 | 读读也串行；需 token 校验、传递与 ownership-lost 测试 |
| 每个子命令独立 acquire/release | 子命令内安全，子步间可被插入 | 保留现状调用形态 | sweep/rename snapshot 可被并发 writer 撕裂 |
| 父命令持锁，子命令照常抢锁 | 无 | 保留现状调用形态 | fail-fast 自锁，复合命令必败 |
| 改为跨 skill 进程内 core 调用 | 可共享父锁 | 破坏 recorder skill 自包含 | 运行时耦合或复制 mutation core |

**主次判定**：目标态要求成功的仓级 snapshot 对应一个没有 writer 穿越的时点，而 `sweep` 必须继续跨三个自包含脚本编排；统一 exclusive lock + token participant 是同时满足两者的最小协议。只在 reader 前后检查 lock 存在 ABA 窗口，不能替代 acquire。token 是锁所有权 capability，不是安全边界或用户 API，只能由 owner 注入其直接子进程。

**主次判定**：系统镜主导——正确性优先于极低频 writer 并行吞吐。当前方案代价是 crash 后可能留下 stale lock；不自动按 TTL 删除，避免误杀仍在运行的慢操作。

### D4 — Parse once and pass updated snapshot through batch rename

`parse_recorder_document()` 每文件一次读取即产出 `items + blocks + problems + format`；`cmd_scan` 不再分别重复 split/arity/row parse。`cmd_batch_rename()` 只调用一次 `read_pool()`，retag 时同步修改这份内存 items，随后调用接受 `items` 参数的 reindex 核心，禁止再次扫描两池。多文件 rename 不声称跨文件事务，但 `[grill-amendment]` 必须把 dated files、batch key、INDEX 与 batches 派生状态全部收敛才可 exit 0；任一写入/reindex 失败均非零，并提示以原 `batch rename old new` 重试。

rename 重试在持锁 snapshot 上按盘面识别阶段，不引入 journal：

| Registry state | Item state | Action |
|---|---|---|
| `old` 存在、`new` 不存在 | 全 old 或 old/new 混合 | retag 仍为 old 的 item，改 registry，再 reindex |
| `old` 不存在、`new` 存在 | 无 old item | 视为 rename 主写已完成，补跑 reindex 后成功 |
| `old` 与 `new` 都存在 | 任意 | fatal；禁止把 retry 偷换成 batch merge |
| `old` 不存在、`new` 存在 | 仍有 old item | fatal；不符合本命令的正常写序，报告冲突盘面 |
| `old` 与 `new` 都不存在 | 任意 | fatal；source batch 不存在 |

不做自动 rollback：跨多个 dated files 与两个派生文件的补偿写也会失败，反而产生第二恢复协议。盘面已足以区分正常阶段，故不增加 transaction journal/stale-journal 真相源。

### D5 — Prose is descriptive, index is the only mutable machine state

新格式 prose 块不再复制 `status/batch` 等可变索引字段。`[grill-amendment]` canonical/overlay 新 block 由独占行 `<!-- sdflow-issue-block:start id={ID} -->` 与 `<!-- sdflow-issue-block:end id={ID} -->` 成对定界；marker 必须同 ID、不可嵌套、每 ID 至多一块。新格式 parser 只按 marker 定位，heading 冒号后的 display title 只供人扫读，不参与 block identity、机器状态或一致性判断；旧 heading/`---` heuristic 只用于 legacy block。精确匹配 marker grammar 的独占行是保留机器语法，renderer 对用户 prose 中的同形行做 HTML escaping，正文里的其它 `---`、`## B12:` 与 code fence 都是普通内容。

显式 `title` 进入单行 heading，须拒绝 CR/LF/NUL；未提供 `title` 时，从 canonical `summary` 确定性派生 display title，将连续空白折叠成一个 ASCII space。完整 `summary` 由 frontmatter 保存原值，并在新建 prose 中以每个物理行都加 `> ` 前缀的 blockquote 展示；promotion 包裹既有 block 时不补写该投影，避免改写历史 prose。写入其它 Markdown 单行语法位的文件头 `source/project`、历史行 `date/note` 仍须经新的窄 line-safety helper 校验或逐行安全渲染，MUST NOT 继续借用 table-cell 守卫。legacy 块内属性表不再作为 overlay item 的一致性来源；`set-status` 只更新 frontmatter 并在 marker block 内 append 历史行。bug 新 item 始终建 marker block；todo 轻量 item 可无 block，首次需要追加历史时建立 marker-framed minimal block。这样删除表↔块状态双写与新 prose 的 heading heuristic，而不删除人读的摘要、分析、根因、证据和变更历史。

新 block 的展示骨架为：

```markdown
<!-- sdflow-issue-block:start id=T85 -->
## T85: 支持管道符与多行摘要

> **摘要**
> 支持 `|`
> 与多行内容

<!-- sdflow-issue-block:end id=T85 -->
```

blockquote 是 canonical summary 的人读投影，不是第二真相源；reader 不从它反解析 summary，后续 mutation 也不为同步 summary 而重写 prose。marker 只负责块边界，不把 prose 提升为机器状态。

### D6 — Self-contained copies with mechanized parity

遵守跨 skill 自包含边界：三个脚本不互相 import 内部 helper。`atomic_write`、`repo_root`、planned `recorder_lock`、frontmatter parser/renderer 等真共享逻辑纳入 AST 等价守卫；`parse_table_rows` 作为 bug/todo legacy 读半场保留，不得用于新写。实现完成时按真实函数 inventory 更新测试 roster，删除 `_reject_cell_unsafe` 的强制存在断言。

## NFRs（TG-16/TG-26）

| NFR | Target | Verification |
|---|---|---|
| 文件解析次数 | 单次 `scan` 每 dated 文件 read=1、document parse=1 | mock/open call-count tests |
| rename 池扫描 | 一次 `batch rename` 每 pool 的 `scan --json` 调用 ≤1 | subprocess call-count test |
| ID 并发唯一性 | 20 个并发 `add` 尝试后：成功记录 ID 全唯一、失败均为显式 lock conflict、0 lost write | multiprocessing/subprocess stress test |
| snapshot 隔离 `[grill-amendment]` | 成功的独立 scan/next-id 不与 writer 重叠；复合命令 participant 读共享 owner 时点 | reader-vs-writer barrier + participant tests |
| lock 可运维性 `[grill-amendment]` | 只读锁不覆盖输出；运行时 lock 永不进入 Git；错误不夸大 cooperative 边界 | blocked-stdout test + init/update ignore idempotence |
| 原子性 | 任意 render/replace 前注入异常时原文件逐字节不变，0 半写目标；dated bytes write 保留既有 mode bits | fault-injection + mode tests |
| I/O 次数 `[grill-amendment]` | dated 文件一次 binary read；0 次 text reread/全文件 decode→encode | open mode/call-count tests |
| 确定性渲染 `[grill-amendment]` | 同一 model 的 render→render byte-identical；items semantic sort、字段/null canonical | golden bytes + permutation tests |
| 兼容性 | 当前全部历史 fixture dual-read 后关键字段与 legacy-only parser baseline 逐项相等 | corpus snapshot comparison |
| 错误可见性 | namespace 在场的每类坏输入均 non-zero + stderr 含 path/reason；0 silent fallback | negative matrix tests |

## Failure Modes and Observability（TG-15）

| Failure | Handling | User-visible evidence |
|---|---|---|
| namespace 在场但 schema/缩进/JSON/枚举错误 | fatal，不回退表、不写盘 | stderr：文件、行/ID、reason；exit non-zero |
| mode 与 legacy 总览区域 mismatch `[grill-amendment]` | fatal，不按 mode 隐藏/猜测 items | stderr：文件、声明 mode、区域计数；exit non-zero |
| overlay 与表同 ID | 合法 shadow，仅限同文件且 mode=overlay | `scan --json` 返回 frontmatter 当前值 |
| 同 ID 跨文件/跨 pool 或 canonical spelling 冲突 | fatal，禁止 reindex/写入 | stderr 列出两处位置、pool 与 canonical key |
| 新 marker 缺失/孤儿/重复/错配/嵌套 `[grill-amendment]` | bug 缺块或任一坏 marker 计入 `problems`；todo 无 block 合法 | 默认可见，`--strict` 非零；不回退 heading heuristic |
| lock 已存在 | 写命令在读盘前失败 | stderr 打印 lock path、PID/command/time 与恢复指引 |
| 进程 crash 留 stale lock | 后续写 fail-fast，不自动删除 | lock 文件本身 + 明确人工核验/删除指引 |
| temp write/replace 失败 | 原文件保持不变；异常上抛 | non-zero + target path；finally 清临时文件 |
| batch rename 中途跨文件或 reindex 失败 `[grill-amendment]` | 已改文件保留，锁释放；原命令按 registry+items 阶段盘面恢复 | stderr 点名失败位置并提示重跑，命令非零；完全收敛前不得 exit 0 |

## Migration Plan

1. 先用失败测试固定 v1 parser/renderer、legacy/canonical/overlay merge、坏 namespace fail-closed；加入 dual-reader，但保留旧 writer。
2. 加仓级 lock 与 canonical ID 校验，覆盖全部 mutating entry；此时存储输出仍可保持旧格式。
3. 切换 `add`/`set-status`/`triage` 到 frontmatter writer：新文件 canonical，已有 legacy 文件 overlay；CLI/JSON 输出不变。
4. 切换 `issues.py batch rename` 到 overlay/canonical retag，并让 reindex 复用 updated snapshot，闭合 T66。
5. 删除新写侧 `_reject_cell_unsafe`、表行 renderer/insert/update 与新格式状态双写；保留 `parse_table_rows` 仅作 legacy read，更新 mirror roster/docstrings/tests。
6. Dogfood：在本 change 收尾时用新 writer 把 T85/T66/T67/T146 的状态更新写成当前 legacy todolist 文件的 overlay，跑 `scan --json`、`reindex --strict` 与全量 pytest。
7. 更新 roadmap/task-log/issues 状态与后继 ADR，明确 `adr/0010` 的 reject+defer 已由本 change 兑现并 supersede。

**Rollback**：提交顺序必须让 dual-reader 先于 writer。writer 出错时只回退 writer/cleanup 提交，保留 dual-reader，使已经产生的 canonical/overlay 文件仍可读；MUST NOT 直接回退到只认 Markdown 表的版本。数据恢复使用 Git revert/checkout 具体文件，禁止自动批量降级为表格（字段可能已含 `|`/换行，降级会再次腐蚀）。

## Open Questions

无阻塞开放问题：proposal OQ1→D2、OQ2→数据模型/D1、OQ3→D3、OQ4→D1 均已收敛。实现中若发现仓外 consumer 直接解析 Markdown 表，按 proposal A1 作为兼容性 blocker 登记并回到设计门，不静默加双写。

## Compliance

- **D-1**：本文现有函数/路径/API 均已从三个脚本与 specs 核验；planned helper 明确标为 planned，不冒充现存代码。
- **D-3**：所有 Non-Goals 均附可证伪假设。
- **D-6 / adr/0016**：共享 schema 跨三个 skill，但运行时保持自包含；一致性靠测试机械守，不建立跨 skill import。
- **adr/0006**：机械解析、锁、ID 与 merge 全部脚本化；坏输入 fail-closed 且有可观察 reason，不押模型遵守 prose。
- **adr/0010**：本 change 正式兑现其 defer 的 Path B，并以目标态 A supersede “Markdown 表 + reject”作为新写契约；历史 read 半场保留，不篡改旧数据。
- **adr/0025 `[grill-amendment]`**：集中记录本 change 的 shared envelope/bytes、overlay+marker、semantic ID、snapshot lock 与 retry recovery 决策；ship 前 Proposed，交付后升 Accepted。
- **adr/0011**：parser/merge 语义按 canonical、overlay、legacy 及三个调用脚本分别测试，任何共享核心语义变化不得只论证一个 consumer。
- **adr/0008**：正确性不依赖“用户不会并发/不会手改”的纪律；锁与 strict parser 提供防御纵深。
- **数据/安全**：只处理仓内既有 issue 元数据，不引入 PII、凭证、网络传输或第三方服务；数据不出仓，法规合规 N/A。
- **bundle 边界**：不触 `sdflow-init/assets/workflow/`，不需要 `sdflow-init update`；顶层 skill 源码经现有 symlink 安装即时生效。
