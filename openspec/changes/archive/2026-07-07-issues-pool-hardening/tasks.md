## 1. T2 总览管道表 row 字段 table-cell-safe（写时 reject，系统性 correctness，先做）〔spec-review C1·BLOCKER〕

- [x] 1.1 写失败测试（TDD）：**逐入口原始参数**校验含 ASCII `|` 或换行 → `_die`——`cmd_add`(module/summary/change/batch + 也进 row 的 time/自定义 id)、**`cmd_triage`(批次名→cells[7], buglist:513/todolist:489)**、**`cmd_batch_rename`(new_key→cells[7], issues:681)**、`batch add`(batches.md key)。三 recorder 各覆盖，**含 triage/rename 两条 add 之外的真·管道表写路径**
- [x] 1.2 写测试：详细块 **prose 字段**（现象/根因/修复）含 `|`/换行正常写入不被拒；但**块专用 `title` 含换行须被守**（防 `## id: title` 块头孤儿行，C7）
- [x] 1.3 实现：table-cell-safe helper 施于**各命令入口的原始用户参数**，**MUST NOT 挂 `" | ".join(cells)` sink**（sink 在 split 后、`|` 已切走、挂那里永不 fire = 假覆盖）；无解析器改动。落点=cmd_add / cmd_triage / _retag_items_in_dated_files / batch add(key) / title(换行)；set-status 用户输入不进 cell、无需守
- [x] 1.4 〔OV-2〕batch key **slug 校验**（拒 `|`/换行/` — `/首尾空白，因 `batches.md` header 用 ` — ` 分隔）——`batch add`/`triage --批次`/`rename new_key` 三处复用；`--title` 拒换行。写失败测试 + 实现
- [x] 1.5 〔OV-3〕自定义 `id` 校验：显式 `data["id"]` MUST `ID_RE.fullmatch` 且不在 `all_ids(root)`（重复即 `_die`，防 `parse_table_rows` 按 ID dict 静默丢行）；`scan` 报告同池重复 ID。写失败测试 + 实现
- [x] 1.6 跑三 recorder `tests/` + 全套件回归，确认绿

## 2. T1 reindex 一致性问题回显 stderr + `--strict` enforcement

- [x] 2.1 写失败测试（TDD）：制造表↔块不一致 → 默认 `reindex` 把 problems 逐条回显 stderr（带 pool/文件定位）、exit 0、INDEX 仍重建
- [x] 2.2 写失败测试：`reindex --strict` 遇 problems 非空 → 回显 stderr 后 **exit 非 0**（同一不一致下默认无 `--strict` 仍 exit 0）
- [x] 2.3 实现：reindex 收集子进程 `scan` problems 非空即回显 stderr；默认不改 exit code；加 `--strict` 使 problems 非空 exit 非 0（致命错误无论是否 strict 仍走既有非 0，分层）
- [x] 2.4 〔OV-1·fold〕`scan` 加**行 arity 校验**：总览行非 8 列（旧 7 列）即入 `problems`——补无块坏行用例（summary 含裸 `|` 列错位），确认进 `problems` → reindex stderr 当场回显（读侧盘面完整性，不必等 --strict 消费者）
- [x] 2.5 跑 `sdflow-issues/tests/`，确认默认 lenient + `--strict` enforcement + scan arity 检测三路
- [x] 2.6 [**延迟绑定 follow-up，不在本 change**] 记 todo：`sdflow-done` sweep 步调 `reindex --strict`（触 `sdflow-done/SKILL.md` 行为面 + 别 capability，单开/搭便车）

## 3. T3 终态集跨脚本一致性守卫测试〔spec-review C5 强化〕

- [x] 3.1 加测试：`import` 三脚本常量，断言 (a) `issues.py.TERMINAL_STATUSES[pool]` ⊆ 对应 recorder `STATUS_CODES`（**按 pool dict 索引**、非扁平 set——接地镜提醒）；(b) **recorder 内联终态字面量 == `issues.py.TERMINAL_STATUSES[pool]`**——buglist `cmd_scan`(:579)/`cmd_triage`(:507) 硬编码的 `{FIXED,WONTFIX}`、todolist 对应处，防"改了 issues.py 但内联没跟"的漂移（⊆ 抓不到这向量）
- [x] 3.2 跑测试确认现状通过（纯新增测试、不改生产逻辑；若内联与常量已不一致须先对齐）

## 4. T4 batch add --if-exists skip（skip-with-warn）+ rename auto-reindex〔spec-review Q2/Q3〕

- [x] 4.1 写失败测试（TDD）：`batch add key --if-exists skip` 遇已存在 key → **no-op exit 0 + stderr 警告"key 已存在，字段参数被忽略"**（**不比较字段、不 `_die`、不碰 placeholder/人写行**）；`batch rename` 后 INDEX/`batches.md` 成员行已自动同步
- [x] 4.2 写失败测试：`rename` 后 auto-reindex **异常路径** → 吞掉只 warn（"rename 已生效、INDEX 未刷新、请手动 reindex"）、**rename 本体 exit 0**（不反噬成 rename 失败假象、不留静默陈旧）
- [x] 4.3 实现：`--if-exists skip`=skip-with-warn（零字段比较）；`rename` 成功后 auto-reindex，reindex 异常吞-warn + exit 0；rename 写盘前失败仍不触发 reindex
- [x] 4.4 跑 `sdflow-issues/tests/`，确认 skip-with-warn + rename auto-reindex 失败语义两路

## 5. T5 定位逻辑去重 + 分支补测

- [x] 5.1 抽 `_find_row_file`：`buglist.py` / `todolist.py` **各自模块内**抽 helper，替换 `cmd_set_status` 与 `triage` 的行定位 dup（design D4：不跨 recorder 强行共享）
- [x] 5.2 核对 `issues.py:cmd_batch_set_status` 是否同 dup（design Open Question）——是则纳入、否则记明不纳入
- [x] 5.3 补测试：WONTDO 分支 + 0 成员人标 IN_PROGRESS 分支
- [x] 5.4 跑三 recorder `tests/`，确认去重无行为回归

## 6. 文档同步（rename 契约变更）〔spec-review C8〕

- [x] 6.1 D3 auto-reindex 落地后同步三 recorder SKILL.md 的 rename 段：`sdflow-issues/SKILL.md`（rename 段补"末尾自动 reindex" + **订正 :90-91"rename 无副作用"过时措辞**）、`sdflow-buglist/SKILL.md:182` / `sdflow-todolist/SKILL.md:191-192`（补"（含 auto-reindex）"）

## 7. 收尾验证

- [x] 7.1 全套件 `pytest` 全绿（含本 change 全部新增用例）
- [x] 7.2 T1-T5 逐项 `/sdflow-todolist` set-status DONE（关联 change `issues-pool-hardening` + commit）
- [x] 7.3 delta spec 对码核验：`specs/spec-workflow/spec.md` 两个 ADDED 需求（T2 字段安全 / T1 reindex 可观测）与实现逐条对齐，无悬空 Scenario
- [x] 7.4 诚实核验：proposal/adr **未**把 D2"堵非交互静默蒸发"记成本 change 已达成（`--strict` 无 in-change 消费者，见 Q1 降级叙事）
