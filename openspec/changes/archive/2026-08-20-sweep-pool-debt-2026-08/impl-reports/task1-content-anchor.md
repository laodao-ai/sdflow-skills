# Task 1 impl-report · ship_gate 内容锚（sweep-pool-debt-2026-08）

## 做了什么

**核心机制（`sdflow-ship/scripts/ship_gate.py`）**：

- 新增内容指纹单一源：`_manifest_bytes_from_entries` / `fingerprint_entries` /
  `_manifest_entries_from_bytes`——`{path→(mode,type,oid)}` → 按原始 path 字节序排序的规范
  字节流 → sha256 digest。design 域（`change_base`+`design_pathspecs`+`ls_tree_map`）与 code
  域（顶层条目排除 `openspec`）都复用同一份 `fingerprint_entries`，`is_stale`/`anchor_writeback.py`
  物理同源。
- `read_reviewed_sha` 重写为薄封装，实际实现移到新函数 `_read_anchor(root, rel)`：live 读点
  要求 `reviewed_sha`（64-hex）+ `reviewed_manifest`（base64）双字段齐全、互证（sha256(解码
  manifest) == reviewed_sha），任一环节失败按 `CAUSE_ANCHOR_MISSING`/`CAUSE_ANCHOR_INVALID`
  分流 `GateIndeterminate`。**锚不再被当 git ref 解析**——原 `cat-file -e <sha>^{commit}` 语义级
  校验与 `CAUSE_ANCHOR_UNRESOLVABLE` 分类整体删除（诊断六类→五类）。
- `is_stale` 重写：design/code 两分支均退化为「HEAD 侧重算 manifest digest vs 锚 digest 等值」，
  不再把锚值喂给 `ls_tree_map` 当 ref 解析。
- `DESIGN_WATCHED_NAMES` 从 `("proposal.md","design.md","tasks.md")` 收窄为
  `("proposal.md","design.md")`——`tasks.md` 移出监视集（D2）。
- 纯勾选框翻转豁免层整体退役并物理删除：`_normalize_checkbox_lines` / `_tasks_content_exempt` /
  `indent_columns` / `is_indented_code_line` / `CHECKBOX_BYTES_RE` / `read_blob_bytes`
  （连带 is_stale 内 ~140 行豁免分支）。**`HtmlCommentTracker` 保留**——它是与 `FenceTracker`
  同族的跨子系统共享单一源（`hack/tests/test_decision_memo_gate.py` 复用），误删会击穿另一
  子系统，已实测发现并修复（见「票外发现」）。
- `FIELD_VALIDATORS["reviewed_sha"]` 放宽为「40 或 64 位小写 hex」纯语法校验（DT-1 校验分层，
  容归档 34 份存量报告自然通过解析）；新增 `FIELD_VALIDATORS["reviewed_manifest"]`（单行 base64
  语法校验，含空字符串合法——对应零字节监视域的合法编码，非典型场景但语义自洽）。
- `guard_design_freshness` 诊断重写：不再拼 `git diff <sha> HEAD` 命令（sha 已不可解析），改为
  对锚 manifest 与 HEAD 侧枚举求差集、逐路径配 `git log -1` 点名最近改动提交。
- `_fail_closed_on_bad`：`reviewed_manifest` 语法坏时与 `reviewed_sha` 同走 `CAUSE_ANCHOR_INVALID`
  专属诊断（原实现只特判 `reviewed_sha`，实测证实 `reviewed_manifest` 坏会退化成无
  `cause_category` 的通用 UNKNOWN——已修，见「票外发现」不适用，此为本票内直接发现并修复）。

**新增 `sdflow-ship/scripts/anchor_writeback.py`**：`import ship_gate` 复用 `fingerprint_entries`；
`--change`/`--report`/`--domain {design,code}`/`--set field=value`（可重复）/`--allow-dirty`；
监视域枚举失败或为空 fail-loud；脏树守卫（`git status --porcelain`，design 域用正向 pathspec、
code 域整仓扫描后 Python 侧排除 `openspec/` 前缀）；原子替换写入（tmp 文件 + `Path.replace`）；
4 行 reconfigure 前导。已用 scratchpad 脚本端到端 smoke 测试 design/code 两域的正常写入、脏树拒写、
`--allow-dirty` 越权路径。

**测试迁移**（`sdflow-ship/tests/`，实际触达 13 个文件——比 brief 估计的 11 略多，因
`test_gate_tail.py` 与 `test_gate_closing_ticket.py` 也各有一处内联 `head_sha(repo)` 锚构造需同步）：
`conftest.py`（新增 `fingerprint`/`write_anchored_report` 复用生产 `fingerprint_entries`，
`sg_frontmatter`/`write_report` 新增 `manifest` 参数）、`test_anchor_contract.py`（整体重写：
从「SKILL.md 字面 frontmatter 模板逐字比对」改为「SKILL.md 是否正确指示调用
`anchor_writeback.py`」）、`test_gate_freshness.py`（整体重写：删除 ~260 行勾选框豁免测试簇 +
tasks.md 专属测试，新增 manifest round-trip / 差异化 / 退役覆盖测试）、
`test_gate_reviewed_sha.py`（整体重写：BAD_SYNTAX 保留、语义级测试改为 64-hex+互证判据、
删除 git-object-resolution 相关测试）、`test_gate_impl_progress.py`（`approved_change` 补
`design.md` 种子文件 + 内容指纹锚）、`test_gate_git_layer.py`（五类诊断更新）、
`test_gate_tail.py`/`test_gate_closing_ticket.py`/`test_gate_preflight.py`/
`test_gate_report_anchors.py`/`test_gate_tools_leg_retirement.py`/`test_plan_resolver.py`/
`test_frontmatter_live_read.py`（锚构造改用 `fingerprint()`/`write_anchored_report`）。

**三产出方 SKILL.md 回写步骤改调脚本**：`sdflow-spec-review/SKILL.md`（拍板回写协议段整体
重写为调 `anchor_writeback.py --domain design`）、`sdflow-code-review/SKILL.md`（Step5 落锚步
改调脚本 `--domain code`，报告格式段模板改为脚本调用示范 + 输出形态占位；**新建**
「impl-review 尾流修订重锚协议」独立小节）、`sdflow-done/SKILL.md`（verify-report 落锚步改调
脚本 `--domain code`，1.1 机械校验条款同步改 64-hex+manifest 判据）。三处均明确
「MUST NOT 手写/手抄锚值」。

**新增 ADR** `openspec/adr/0044-content-fingerprint-anchor-retires-commit-sha-and-tasks-checkbox-exemption.md`；
`adr/0026` 头部加 superseded-by 指针（决策 1/2 被取代、决策 3 求值窗口未受影响仍有效）。

**全仓 `reviewed_sha` 消费面收口**：`grep -rln reviewed_sha`（不加 --include，排除 `/archive/`）
实测 30 个命中文件。逐一核验：`sdflow-ship/` 下 13 个测试文件 + `scripts/ship_gate.py` +
`scripts/anchor_writeback.py` 已按新格式迁移；三产出方 SKILL.md 已迁移；
`docs/workflow-skills/sdflow-spec-review.md` 修正「40 位 OID」为「64 位 hex + reviewed_manifest」
表述；`docs/windows-pytest-remediation-inventory.md` 只是文件清单表格行（提及测试文件名，非
语义断言，未改）；`openspec/adr/0026`/`0044`（本次新写/改动，符合目标态）；
`openspec/specs/spec-workflow/spec.md`（仓库主 spec 树，本 change 尚未归档同步，保持现状，
留待 `sdflow-done` archive 步骤同步 delta，非本票职责）；
`openspec/specs/openspec-170-followup/spec.md`（提及 ADR-7(b) 时序纪律概念，未断言具体格式，
未改）；`openspec/changes/sweep-pool-debt-2026-08/*`（proposal/design/tasks/tickets/
decision-memo/impl-reports——本 change 自身的规划文档，描述的正是目标态，无需改）；
`openspec/issues/{INDEX,CLOSED}.md` 与 `openspec/issues/{open,closed}/todo/{T189,T193,T262,T292}.md`
（issues 池的历史记录/待办条目，非本票职责——T292 恰是本 change 的源 todo，标记完成属 pool
纪律由编排/recorder 处置，非实现票自行越权）；`openspec/upstream/reports/*`（历史快照，
DOC-1 归档豁免）。

**收尾**：用 `anchor_writeback.py` 重锚本 change 自身 `spec-review-report.md`（40-hex→64-hex+
manifest，`design_approved: true` 结论字段原样保留），随后实跑 `ship_gate.py --change
sweep-pool-debt-2026-08` 确认输出 `CONTINUE_IMPL`（非 `REFUSE_START`）——design 域 CURRENT。

## 测试

- `sdflow-ship/tests/` 单独跑：**328 passed**。
- 全仓 `pytest -q`（含 `hack/tests/`）：**2573 passed, 10 skipped, 0 failed**（385s）——覆盖了
  票外发现的 `HtmlCommentTracker` 跨子系统消费。

## 票外发现（非本票验收范围，如实记录）

1. **`HtmlCommentTracker` 误删又恢复**：初次删除勾选框豁免整簇时，把与 `FenceTracker` 同族、
   被 `hack/tests/test_decision_memo_gate.py` 复用的通用 HTML 注释状态机一并删了；全仓 pytest
   在 collection 阶段报 `AttributeError` 当场抓住，已恢复该类（保留在 `ship_gate.py`，作为
   跨子系统共享单一源，不再被 `_normalize_checkbox_lines` 消费但仍是模块公开符号）。
2. **`reviewed_manifest` 语法坏时诊断分类缺口**：`_fail_closed_on_bad` 原实现只对
   `field == "reviewed_sha"` 特判走 `CAUSE_ANCHOR_INVALID` 专属诊断，`reviewed_manifest` 坏时会
   退化成无 `cause_category` 的通用 UNKNOWN（本票开发过程中由新增测试
   `test_manifest_not_valid_base64_is_unknown` 抓到并当场修复，已计入本票交付，非遗留缺口）。

## Global Constraints 逐条核对

- DT-1（校验分层）：`FIELD_VALIDATORS["reviewed_sha"]` 40|64 位放行，`archived_verify_state`
  只消费 `verify` 结论——`test_verify_pass_active_present_run_verify` 等既有归档回归测试全绿，
  归档 34 份 40-hex 报告未受影响（本票未新增归档 fixture 测试，因归档回归属既有 test_gate_terminal.py
  覆盖范围，未在本票改动面内触碰）。
- DT-2（等值判定只走 digest + manifest 诊断 + 字节保真）：`is_stale` 两分支均纯 digest 比较；
  `test_manifest_round_trip_stable_for_tab_and_non_ascii_paths` 覆盖 Tab/CRLF/非 ASCII 路径
  round-trip。
- DT-3（同批写入 + 脏树守卫）：`anchor_writeback.py` 的 `--set` 与锚同批落盘；脏树守卫已
  smoke 测试正反两路径。
- 枚举失败 fail-closed：既有 `test_ls_tree_read_failure_is_indeterminate_not_fresh` /
  `test_ls_tree_unparsable_output_is_indeterminate` 覆盖，未改动该判据本身（仍走
  `GateIndeterminate`）。
- DT-7（impl-review 豁免通道改造）：gate 端 subject 豁免代码本就已在更早 change 物理删除
  （`grep -n subject|BR-7 ship_gate.py` 核实无残留豁免通道，仅剩 `_tag_task_id` 等完成标签
  机制，与本次豁免退役无关）；`sdflow-code-review/SKILL.md` 新建重锚协议段。
- Compliance（DOC-1/premise-verification/基准 5）：本报告与代码改动未新增任何 Markdown/语法
  解析——`anchor_writeback.py` 的 frontmatter 块切分复用 `parse_ship_gate_frontmatter` 同一
  「只认首块」识别口径（`_split_frontmatter_block` 只做块边界切分，取值仍交 `ship_gate` 单一源）。
