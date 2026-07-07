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
- **选**：写路径对**总览表 row 字段**（`module` / `summary` / `change` / batch key）做 table-cell-safe 校验——含 ASCII `|` **或**换行即 `_die` 拒绝（复用本仓既有写时校验惯例：`buglist.py:357-361` priority/status 非法即 `_die`）。详细块字段（现象/根因/… prose）**不受此限**（非 `|` 分隔、`|`/换行进块无害）。
- **弃**：①**转义**（`\|` + 三处解析器改按未转义切列 + 反转义）——引入全新转义语义、动三处读路径核心、且是给「未来若结构化就被扔掉的机械」投资；②**替换为全角 `｜`**（U+FF5C）——有损、且悄悄改用户字节。
- **理由**：(a) 现存池**0 行**字段含 `|`（全量扫过），"保留字面 `|`"需求实测=0，escape 唯一优势无处兑现；(b) reject 零解析器改动、0 向后兼容负担、fail-closed 对齐本仓纪律、复用 `_die` 成例；(c) **换行是比 `|` 更狠的兄弟风险**（截断整行 + 产生孤儿行），一并纳入 table-cell-safe；(d) 守的是 CONTEXT.md「**盘面即状态**」——总览表即盘面，列错位/行截断 = 盘面腐蚀；(e) reject 是通往未来「结构化机器状态层」roadmap 的**低成本桥**（零机械投资、不挡重构）。

### D2（T1）reindex problems 回显 stderr；默认 exit 0，`--strict` opt-in enforcement
- **选**：`reindex` 收集子进程 `scan` 的 problems，非空则逐条回显 stderr（带 pool/文件定位）。**默认 exit 0、INDEX 照常重建**（不因一个坏块阻断整池刷新）；**加 `--strict`：problems 非空即 exit 非 0**（opt-in 强制），供非交互 / 收尾门用。
- **弃**：①problems 即 exit 非 0（无默认 lenient）——一个坏块阻断整池刷新，因噎废食；②只 stderr、无 `--strict`——非交互调用（sweep / hook / CI）stderr 常被吞 + exit 0 = 绿，一致性问题**静默蒸发**，违反 CONTEXT.md 反静默元原则（grill D2 实证：reindex 主调用者 `sdflow-done` sweep 恰是非交互）。
- **理由**：默认 lenient 保"不阻断重建"；`--strict` 给非交互场景一个能被机器抓住的 enforcement 杠杆，元原则在交互 / 非交互两种场景都不破。致命错误（无法读文件等）仍走既有非 0 退出，与"数据不一致警示"分层。
- **scope 边界**：`--strict` flag 本身在 G1（issues.py/reindex 同 capability）；**让 `sdflow-done` sweep 调 `reindex --strict`** 触 `sdflow-done/SKILL.md`（行为面 + 别 skill capability）→ 按 fold-vs-defer **记延迟绑定 follow-up、不折进 G1**。

### D3（T4）`batch add --if-exists skip`（**match-or-error 幂等**）+ `batch rename` 末尾 auto-reindex
- **选**：`--if-exists skip` 采**真幂等（match-or-error）**语义——已存在同 key 且本次未带会改条目的人写字段（或带的字段与现有条目**一致**）→ no-op 退出 0；已存在但带了**与现有不一致**的字段（title/优先级/计划）→ 仍 `_die`。`rename` 成功后自动调 `reindex`（成员 tag 已变，INDEX/batches 成员行须同步）。
- **弃**：①`--if-exists skip` **无脑 no-op**——复活现有 `cmd_batch_add` docstring 刻意避开的"隐蔽坑"（静默吞 title/优先级/计划、调用方误以为生效），违反反静默纪律；②rename 后仅 SKILL.md 提示"记得 reindex"——靠人记不可靠，漏 reindex 留 INDEX 陈旧（本 session dogfood 亲历：rename 后手动补跑 reindex）。
- **理由**：match-or-error 是幂等标准语义（同输入→同结果 = 幂等，非"存在即无视输入"），既给 automation 安全重跑、又**不破现有 anti-trap**；auto-reindex 把"rename 必致 INDEX 陈旧"从人纪律降为脚本保证。

### D4（T5）`_find_row_file` **各 recorder 内抽**，跨 recorder 镜像 consolidation 出 scope
- **选**：`buglist.py` / `todolist.py` **各自内部**抽一个模块内 `_find_row_file`，消该 recorder 内 `cmd_set_status` 与 `triage` 的定位 dup（T5 的"4 处"= triage + set-status × 2 recorder，是 **intra-recorder** dup）。
- **接地**：两 recorder 的定位逻辑是**刻意"镜像"**（todolist docstring 明写"镜像 buglist"），结构平行但按 (后缀, 周期) 相异——buglist daily `\d{4}-\d{2}-\d{2}-buglist`、todolist monthly `\d{4}-\d{2}-todolist`，**非逐字节相同**。
- **弃**：把两 recorder 的镜像逻辑合成一个跨模块共享 helper——①超出 T5 的 intra-recorder scope；②三 recorder 刻意无共享 import（issues.py subprocess 调），引入共享是新耦合；③跨 recorder 镜像 consolidation 属更大重构，天然归**结构化 recorder（Path B roadmap）**——届时索引层统一、镜像自然消。
- **理由**：低耦合优先 + 守 T5 实际 scope；镜像 drift 的根治留给 Path B，不在本 change 反应式做。

## Risks / Trade-offs

- **[T2 reject 挡掉合法含 `|`/换行 的字段]** → 实测 0 现存 occurrence、需求罕见；写者遇拒可改写（换措辞或用全角 ｜），且错误**响亮不静默**（写时即 `_die`，胜过转义/替换悄悄改字节）。无解析器改动、无读路径回归面。
- **[T2 向后兼容]** → **不适用**：现存池 0 行裸 `|`（全量扫过），无旧腐蚀数据要容错，原设计为此设想的 fail-safe 解析/迁移**取消**。
- **[T3 守卫测试要枚举各 recorder 终态集常量]** → 测试直接 import 三脚本的 `TERMINAL_STATUSES`/`STATUS_CODES` 做子集断言，常量重命名即测试红（正是目的）。
- **[T4 auto-reindex 扩大 rename 副作用面]** → reindex 已验证幂等，副作用可控；rename 失败时不触发 reindex（先成功后同步）。

## Migration Plan

- **无迁移**：现存池 0 行裸 `|`，reject 是纯写时新守卫，不触碰任何既有数据。
- 回滚：本 change 纯 repo-local 脚本 + 测试，`git revert` 即恢复；无下游/bundle 影响面。

## Open Questions

- ~~T2 批次名是否也守卫~~ **已定**（grill）：batch key 纳入 table-cell-safe reject 范围（批次 key 应是干净 slug，含 `|`/换行本就异常）。
- ~~T5 `cmd_batch_set_status` 是否同 dup~~ **已定**（grill 接地）：`issues.py:cmd_batch_set_status` 操作的是 `batches.md` 条目定位（`_find_batch_entry_range`），与 recorder 的 **dated 文件行定位**是不同结构、不同关注点，**不纳入** `_find_row_file` 抽取。

## 上位关系（去字符串化机器状态层 roadmap）

本 change 走 **Path A（现状 markdown 表 + reject 硬化）**，是刻意的短期务实解。更根的 **Path B（总览行结构化 = YAML frontmatter 索引 + prose 块）** 会让 T2 整个蒸发、删掉 recorder 里大片表解析/双写一致机械——但属范畴不同的大改，**不折进本 change**（fold-vs-defer 循环成本纪律）。B 与 **T65（gate 状态锚迁 frontmatter）同根**「去字符串化机器状态层」，二者合并为一个 roadmap 阶段统一权衡（见 todolist 交叉引用）。D1 选 reject 而非 escape，部分正因它是通往 B 的低成本桥：零机械投资、不挡未来结构化重构。**决策全文见 `openspec/adr/0010-issues-machine-state-markdown-plus-reject-defer-structuring.md`**（markdown+reject 守盘面、结构化延后 roadmap）。
