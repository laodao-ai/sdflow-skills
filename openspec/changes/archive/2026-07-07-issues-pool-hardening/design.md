## Context

issues 池 recorder 三脚本（`buglist.py` / `todolist.py` per-type + `issues.py` 跨池）用 markdown 表存状态总览。三者的行解析**全是 naive `line.strip().strip("|").split("|")`**（`buglist.py:293` / `todolist.py:282` / `issues.py:678`）——字段值里只要有一个 ASCII `|` 就多切一列、后续列全错位（静默数据腐蚀，T2）。`issues.py` 不 import 两 recorder 模块（subprocess 调用），三者**无共享代码模块**；`_find_row_file` 目前**不存在**，T5 要新抽（现 dup 在 `buglist.py`/`todolist.py` 各自的 `cmd_set_status` + triage 行定位）。本 change 是 issues.py/recorder 一个 capability 的健壮化合批，不碰 `assets/workflow/` bundle、不下发下游。

## Goals / Non-Goals

**Goals:**
- 消除字段 `|` 致列错位的静默腐蚀（T2）——写路径安全化 + 解析器按未转义 `|` 切列 + 读路径对旧裸 `|` 容错。
- reindex 一致性问题可观测（T1）、终态集漂移有守卫（T3）、batch 操作幂等（T4）、定位逻辑去重 + 分支补测（T5）。
- 严格 scope = T1-T5，不扩张到其它 recorder 面。

**Non-Goals:**
- 不重构表存储格式（不换 CSV/JSON——markdown 人读表是既定契约）。
- 不把三 recorder 合并成一个共享框架（跨模块大重构超出 scope；T5 只去局部 dup）。
- 不碰 bundle / workflow 规则 / 下游回灌。

## Decisions

### D1（T2）总览表 row 字段**写时 reject**——table-cell-safe 守卫（`|` + 换行）
- **选**：写路径对进入**总览管道表 row** 的字段做 table-cell-safe 校验——含 ASCII `|` **或**换行即 `_die` 拒绝（复用既有写时校验惯例：`buglist.py:359-363` priority/status 非法即 `_die`〔spec-review-amendment C10 订正行号〕）。
- **〔spec-review-amendment C1·BLOCKER〕守卫落点 = 各命令入口的原始用户参数，非 `" | ".join(cells)` sink**：sink 在 parse 之后（`|` 已被 `strip("|").split("|")` 切走）→ 挂 sink 永不 fire = **假覆盖**。须逐入口守：`cmd_add`（`module`/`summary`/`change`/`batch`，另含也进 row 的 `time`/自定义 `id`〔C6〕）+ `cmd_triage`（`cells[7]=batch`，buglist:513 / todolist:489）+ `_retag_items_in_dated_files`（`cells[7]=new_key`，issues:681）。**澄清面**：`batch add` 写的是 `batches.md` 的 `### key — title`/`状态:` 行（非 `|` 管道表），那里守的是 **batch key 干净**（防含 `|`/换行的 key 经 triage/retag 流进管道表 `cells[7]`）——与管道表列腐蚀是**两个面**，都要守；`cmd_set_status` 用户输入（status 已校验、evidence 进 append-only prose）**不进 cell、无需表格守卫**。
- **弃**：①转义（`\|` + 改三处解析器）——引入转义语义、动读路径核心、且是给"未来结构化会扔"的机械投资；②替换全角 `｜`——有损、悄改字节。
- **理由**：(a)〔spec-review-amendment C9 措辞降级〕现存池**存量 0 行**含 `|`（全量扫过），"保留字面 `|`"**未来罕见但非零**（本仓 pipe 相关 bug summary 可能含 `|`）——但错误响亮、可改写或用全角 ｜，escape 的无损优势不抵其解析器代价；(b) reject 零解析器改动、fail-closed、复用 `_die`；(c) **换行是比 `|` 更狠兄弟风险**（截行）一并纳入；(d) 守「**盘面即状态**」；(e) reject 是通往结构化 roadmap 的低成本桥。
- **〔spec-review-amendment C7〕详细块 scope 精确化**：详细块**prose 字段**（现象/根因/修复）不受限；但 `BLOCK_TMPL` 内含一张 `| 属性 | 值 |` 子表（`| 模块 | {module} |` 等，buglist:336）——`module`/`summary` 守卫对它**也 load-bearing**（已在守卫集，侥幸覆盖）；块专用 `title`（不在守卫集）含换行→块头 `## id: title` 孤儿行，故 **`title` 的换行也须纳入守卫**。
- **〔spec-review-amendment OV-2（cross-model）〕batch key 是 slug 校验、非只 `|`/换行**：`batches.md` header `### {key} — {title}`（issues:343）用 ` — ` 作分隔——key 含 ` — ` 会被切坏（key 变 `a`、`_find_batch_entry_range` 找不到）。故 batch key MUST 过 **slug 校验**（拒 `|`、换行、` — `、首尾空白），复用到 `batch add` / `triage --批次` / `rename new_key` 三处；`--title` 亦拒换行。
- **〔spec-review-amendment OV-3（cross-model）〕自定义 `id` 除 table-cell-safe 还须 语法 + 查重**：`parse_table_rows` 按 ID 建 dict → **重复 ID 静默丢一行**；非 `[A-Z]\d+` 的 id 破 `block_ranges`。故显式 `data["id"]` MUST `ID_RE.fullmatch` 且不在 `all_ids(root)`（重复即 `_die`）；`scan` 顺带报告同池重复 ID，防存量坏盘面继续静默。

### D2（T1）reindex problems 回显 stderr；默认 exit 0，`--strict` opt-in enforcement
- **选**：`reindex` 收集子进程 `scan` 的 problems，非空则逐条回显 stderr（带 pool/文件定位）。**默认 exit 0、INDEX 照常重建**（不因一个坏块阻断整池刷新）；**加 `--strict`：problems 非空即 exit 非 0**（opt-in 强制），供非交互 / 收尾门用。
- **弃**：①problems 即 exit 非 0（无默认 lenient）——一个坏块阻断整池刷新，因噎废食；②只 stderr、无 `--strict`——非交互调用（sweep / hook / CI）stderr 常被吞 + exit 0 = 绿，一致性问题**静默蒸发**，违反 CONTEXT.md 反静默元原则（grill D2 实证：reindex 主调用者 `sdflow-done` sweep 恰是非交互）。
- **理由**：默认 lenient 保"不阻断重建"；`--strict` 给非交互场景一个能被机器抓住的 enforcement 杠杆，元原则在交互 / 非交互两种场景都不破。致命错误（无法读文件等）仍走既有非 0 退出，与"数据不一致警示"分层。
- **scope 边界**：`--strict` flag 本身在 G1（issues.py/reindex 同 capability）；**让 `sdflow-done` sweep 调 `reindex --strict`** 触 `sdflow-done/SKILL.md`（行为面 + 别 skill capability）→ 按 fold-vs-defer **记延迟绑定 follow-up、不折进 G1**。
- **〔spec-review-amendment Q1·诚实降级（冷镜 B1）〕`--strict` 在本 change 内是零消费者的预置接口**：本 change ship 后无任何非交互调用者传 `--strict`（唯一够格者 sweep 的 wiring 已 defer 到 T2.5）。故 **D2 在本 change 内实际交付的只有 T1 stderr 回显**（立即有效）；`--strict` 是**为 T2.5 follow-up 预置的接口**（保留是为 follow-up 只需 wire+检查、不重做整个 flag），**本 change 内不产生 enforcement 价值**。**MUST NOT** 在 proposal/adr/verify 里把"堵住非交互静默蒸发"记成本 change 已达成的收益——那要等 T2.5 wire sweep 才落地。
- **〔spec-review-amendment OV-1（cross-model）·fold〕`scan` 加行 arity 检测——补上盘面完整性的读侧**：`scan` 现只要求 `len(cells)>=5` 就按固定列位读（todolist:279），无块坏行里 summary 含裸 `|` 会**列错位但不进 `problems`** → 即便 `--strict` 也抓不到这类腐蚀。故 `scan` MUST 校验行 arity（当前 8 列、旧格式 7 列之外一律入 `problems`）——这样 T2 写侧防（reject）+ 读侧 scan 检测凑成**完整盘面完整性**，且 arity 进 problems 后 **T1 的 stderr 回显当场就报出腐蚀**（不必等 --strict 消费者）。补一个 todolist 无块坏行用例，确保读侧检测生效。

### D3（T4）`batch add --if-exists skip`（**skip-with-warn**〔spec-review Q2〕）+ `batch rename` auto-reindex（**钉死失败语义**〔Q3〕）
- **选（Q2=B skip-with-warn，替换 grill 的 match-or-error）**：`--if-exists skip` 遇已存在同 key → **no-op 退出 0 + stderr 警告"key 已存在，字段参数被忽略"**。**不做字段比较、不碰 placeholder 逻辑、不解析人写行、无死胡同**。skip 是 opt-in，忽略字段是其**声明语义**（区别于"默认 no-op"那种隐蔽坑）；反静默由 warn 满足（字段没生效对用户可见）。要改字段走编辑或未来 update 命令。
- **弃 match-or-error（grill 原案，冷镜 B2 否掉）**：match"一致"是语义黑洞——`getattr(args,"优先级") or PLACEHOLDER`（issues:589）把"未传"与占位符塌缩；title/优先级/计划 是架构明文"**绝不解析的人写行**"（issues:27/458）无解析器；placeholder `<待填>` vs 补填 `--优先级 P1` 会 `_die` 制造 **UX 死胡同**（无 update 路径逼手改 batches.md）。skip-with-warn 绕开全部。
- **选（Q3=A auto-reindex 失败语义）**：`rename` 成功后自动调 `reindex`；**auto-reindex 异常吞掉只 warn**（"rename 已生效，INDEX 未刷新，请手动 reindex"）、**rename 本体 exit 0**（写盘已成功，不让 reindex 失败反噬成"rename 失败"假象、也不留 INDEX 陈旧的静默态）。design 显式**承认** rename 触发 `sync_batches_md` 遍历全库条目的**固有副作用面**（可能顺带同步无关批次状态 / 追加 ⚠️）——这是 reindex 的性质，接受并文档化（见 C8 doc-sync）。
- **理由**：skip-with-warn 最简、零架构冲突、达幂等又避 B2 黑洞；auto-reindex 失败吞-warn 保证"rename 生效但 INDEX 陈旧"可见，不留 D3 本要防的静默陈旧。

### D4（T5）`_find_row_file` **各 recorder 内抽**，跨 recorder 镜像 consolidation 出 scope
- **选**：`buglist.py` / `todolist.py` **各自内部**抽一个模块内 `_find_row_file`，消该 recorder 内 `cmd_set_status` 与 `triage` 的定位 dup（T5 的"4 处"= triage + set-status × 2 recorder，是 **intra-recorder** dup）。
- **接地**：两 recorder 的定位逻辑是**刻意"镜像"**（todolist docstring 明写"镜像 buglist"），结构平行但按 (后缀, 周期) 相异——buglist daily `\d{4}-\d{2}-\d{2}-buglist`、todolist monthly `\d{4}-\d{2}-todolist`，**非逐字节相同**。
- **弃**：把两 recorder 的镜像逻辑合成一个跨模块共享 helper——①超出 T5 的 intra-recorder scope；②三 recorder 刻意无共享 import（issues.py subprocess 调），引入共享是新耦合；③跨 recorder 镜像 consolidation 属更大重构，天然归**结构化 recorder（Path B roadmap）**——届时索引层统一、镜像自然消。
- **理由**：低耦合优先 + 守 T5 实际 scope；镜像 drift 的根治留给 Path B，不在本 change 反应式做。

## Risks / Trade-offs

- **[T2 reject 挡掉合法含 `|`/换行 的字段]** → 实测 0 现存 occurrence、需求罕见；写者遇拒可改写（换措辞或用全角 ｜），且错误**响亮不静默**（写时即 `_die`，胜过转义/替换悄悄改字节）。无解析器改动、无读路径回归面。
- **[T2 向后兼容]** → **不适用**：现存池 0 行裸 `|`（全量扫过），无旧腐蚀数据要容错，原设计为此设想的 fail-safe 解析/迁移**取消**。
- **[T3 守卫弱于自述目标〔spec-review-amendment C5〕]** → ⊆ 断言只抓"issues.py 改终态码"，**抓不到 recorder 内联字面量漂移**（buglist:507/579 三处硬编码 `{FIXED,WONTFIX}`）。守卫须**并断 recorder 内联终态集 == `issues.py.TERMINAL_STATUSES[pool]`**（按 pool dict 索引、非扁平 set——接地镜提醒），或让 recorder 从单一常量派生消掉内联。
- **[T4 auto-reindex〔spec-review-amendment Q3〕]** → 失败语义已钉死（异常吞-warn、rename exit 0，见 D3）；rename 触发全库 batches.md 同步的副作用面**已接受并文档化**（reindex 固有性质）；rename 写盘前失败仍不触发 reindex。
- **[rename 契约变更须同步 SKILL.md〔spec-review-amendment C8〕]** → auto-reindex 使 `sdflow-issues/SKILL.md:90-91`"rename 无副作用"成事实错误 → tasks 补 doc-sync 任务（三 recorder SKILL.md rename 段补"含 auto-reindex"、订正"无副作用"措辞）。

## Migration Plan

- **无迁移**：现存池 0 行裸 `|`，reject 是纯写时新守卫，不触碰任何既有数据。
- 回滚：本 change 纯 repo-local 脚本 + 测试，`git revert` 即恢复；无下游/bundle 影响面。

## Open Questions

- ~~T2 批次名是否也守卫~~ **已定**（grill）：batch key 纳入 table-cell-safe reject 范围（批次 key 应是干净 slug，含 `|`/换行本就异常）。
- ~~T5 `cmd_batch_set_status` 是否同 dup~~ **已定**（grill 接地）：`issues.py:cmd_batch_set_status` 操作的是 `batches.md` 条目定位（`_find_batch_entry_range`），与 recorder 的 **dated 文件行定位**是不同结构、不同关注点，**不纳入** `_find_row_file` 抽取。

## 上位关系（去字符串化机器状态层 roadmap）

本 change 走 **Path A（现状 markdown 表 + reject 硬化）**，是刻意的短期务实解。更根的 **Path B（总览行结构化 = YAML frontmatter 索引 + prose 块）** 会让 T2 整个蒸发、删掉 recorder 里大片表解析/双写一致机械——但属范畴不同的大改，**不折进本 change**（fold-vs-defer 循环成本纪律）。B 与 **T65（gate 状态锚迁 frontmatter）同根**「去字符串化机器状态层」，二者合并为一个 roadmap 阶段统一权衡（见 todolist 交叉引用）。D1 选 reject 而非 escape，部分正因它是通往 B 的低成本桥：零机械投资、不挡未来结构化重构。**决策全文见 `openspec/adr/0010-issues-machine-state-markdown-plus-reject-defer-structuring.md`**（markdown+reject 守盘面、结构化延后 roadmap）。
