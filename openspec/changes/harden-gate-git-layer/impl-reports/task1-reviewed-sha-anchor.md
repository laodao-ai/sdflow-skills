# Task 1 — 评审锚成为门禁的唯一真相源，缺失即拒绝放行

**R-ID**: R3 ｜ **范围**: tasks 1.1–1.4、1.9、4.1、4.2 ｜ **状态**: DONE_WITH_CONCERNS

## 1. 做了什么

### 1.1 解析器：有限枚举 → 「字段 → 校验函数」（tasks 1.1/1.2）

`FIELD_ENUMS` 容不下「任意 40 位 hex」——直接加字段会让每个真 sha 判 `out-of-domain`（新锚永远读不到）。
新增 `FIELD_VALIDATORS` 作为「本 schema 认识哪些字段」的单一注册表：三个枚举字段由
`_enum_validator(FIELD_ENUMS[f])` 生成，`reviewed_sha` 挂 `_is_full_oid`。`FIELD_ENUMS` 保留为
枚举字段的数据源（producer 模板契约测试仍按它比对定义域）。

**语法级校验落在纯文本函数内**（`_is_full_oid`，`ship_gate.py:829-841`）：完整 40 位**小写** hex；
拒缩写 SHA、`HEAD`、ref 名、大写、39/41 位、非 hex 字符。不依赖 `root`、不调 git ⇒ live 读与
归档 git-show 文本读共用同一核心。

### 1.2 语义级：`read_reviewed_sha(root, rel)`（task 1.3）

`ship_gate.py:246-283`。读报告 frontmatter → `git cat-file -e <sha>^{commit}`。
`^{commit}` 后缀是承重项：它使指向 **blob / tree** 的锚同样落进 `rc≠0`。
四种形态各抛 `GateIndeterminate`，category 各不相同（`anchor-missing` / `anchor-invalid` /
`anchor-unresolvable`），**无任何回退分支**。

### 1.3 `GateIndeterminate` + `main()` 唯一映射点（tasks 3.5/3.6 的本票半场）

`ship_gate.py:159-186` 定义异常与六个 `CAUSE_*` 常量（含 Task 2 将接入的 `git-unavailable` /
`git-timeout` / `read-failed`，先把 category 空间开出来，避免后续票再动映射点）。
`main()` 以 `try/except` 包住 `decide()` **整个函数体**，按 `_INDETERMINATE_ADVICE` 表拼
各自可行动的诊断，JSON 额外带 `cause_category` 供机械消费。

### 1.4 三个 producer 模板落锚（task 1.4）

`sdflow-spec-review/SKILL.md` / `sdflow-done/SKILL.md`（PASS + FAIL 两模板）/
`sdflow-code-review/SKILL.md`（pass + blocked 两模板）各加
`reviewed_sha: 0123456789abcdef0123456789abcdef01234567`，**顶层 `ship-gate:` 的直接子键**，
与 design.md ADR-1 的 YAML 示例逐字一致。三处均补语义句「锚记的是被批准的盘面，不是写报告的时刻」
与「MUST 与结论字段在同一次文件写入中落盘」。

### 1.5 反推锚退役（task 1.9）

删除 `report_last_sha`；`is_stale` 的锚源改为 `read_reviewed_sha`。仓内无调用点残留（机械断言见 §3）。
原「报告从未提交 → `freshness=uncommitted`」分支随之消失（见 §4 决策 D2）。

### 1.6 测试基座：两段 / 三段提交模型（tasks 4.1/4.1b/4.2）

`conftest.py` 新增 `head_sha` / `sg_frontmatter` / `write_report`。
`approved_change` 改为：①四件套落盘提交 → ②可选 `revise=` 二次修订提交 → ③读 HEAD、写携锚报告、单独提交。
`anchor=` 参数可取 `"head"`（默认）/ `"pre-revision"`（表达 ADR-7(b) 自锁）/ `None`（缺锚负例）/ 显式 sha。
`impl_done` / `tail_ok` 经 `approved_change` 继承该模型；44 处调用点全部跑通（§3 全套件）。

## 2. 逐条验收标准的证据锚点

| 验收标准 | 证据 |
|---|---|
| 报告 frontmatter 能承载 40 位 OID 且与结论字段同层 | `test_gate_reviewed_sha.py::test_syntax_layer_accepts_full_lowercase_oid`（同块解出两字段）；`test_anchor_contract.py::test_producer_anchor_is_direct_child_of_ship_gate` |
| 缺失 / 格式非法 / 对象不存在 / 非 commit 四形态各得 UNKNOWN(6)，诊断能分辨 | `test_missing_anchor_is_unknown_and_names_the_field`（category=`anchor-missing`）· `test_syntactically_invalid_anchor_is_unknown`（7 参数）· `test_anchor_object_absent_is_unknown`（category=`anchor-unresolvable`，reason 含「force-push」）· `test_anchor_pointing_at_non_commit_object_is_unknown[blob/tree]`；诊断互异性 `test_indeterminate_reasons_are_mutually_distinguishable` |
| 「结论在、锚缺」中间态同样 UNKNOWN(6) 且点名锚 | `test_missing_anchor_is_unknown_and_names_the_field`（`design_approved: true` 在场，断言 reason 含 `reviewed_sha`） |
| 三模板写出锚字段、与设计示例逐字一致 | `test_anchor_contract.py::test_producer_templates_declare_reviewed_sha_verbatim`（裸行等值 `ADR1_ANCHOR_LINE`） |
| 反推式旧锚退役、无调用点 | `test_inferred_anchor_helper_is_gone`（`hasattr` + 源码 grep `report_last_sha(`）；行为面 `test_touching_the_report_does_not_move_the_anchor` |
| 共享 fixture 支持两段提交、44 处调用点跑通 | `test_fixture_two_stage_model_puts_artifacts_before_report` · `test_fixture_third_stage_models_pre_approval_revision` · `test_fixture_third_stage_can_express_adr7b_selflock`；全套件 `2071 passed, 8 skipped, 3 xfailed`（仓根 `pytest`） |
| 每条新增守卫附变异证明 | §3 全表 |

两个 code 域消费方各自覆盖（Compliance 硬要求）：
`test_code_review_report_missing_anchor_is_unknown` / `test_verify_report_missing_anchor_is_unknown`。

## 3. 变异证明（逐条实做：改源 → 跑全套件 → 记红 → 还原）

口径 = **按守卫计数**。每行都是真的把那行代码删掉/改反后跑出来的，不是「用例存在且为绿」。
基线 = `318 passed`（`sdflow-ship/tests/`）。

| # | 守卫 | 变异手法 | 结果 | 变红用例 |
|---|---|---|---|---|
| G1 | `_is_full_oid` 长度 == 40 | 去掉长度判据 | 3 failed | `test_syntax_layer_lives_in_the_pure_text_parser[0123456 / 39位 / 41位]` |
| G2 | `_is_full_oid` 字符集 ⊆ 小写 hex | 去掉字符集判据 | 2 failed / 316 passed | 同上 `[大写 / g开头]` |
| G3 | `FIELD_VALIDATORS["reviewed_sha"]` 注册 | 删注册行（字段被当外来 metadata 忽略） | **109 failed** / 209 passed | `test_reviewed_sha_registered_in_validators`、`test_producer_anchor_is_direct_child_of_ship_gate` + 全部经锚求值的链路 |
| G4 | `read_reviewed_sha` 缺字段 fail-closed | 换成 `state.get(...,"")` | 4 failed / 314 passed | `test_missing_anchor_is_unknown_and_names_the_field`、`test_semantic_layer_raises_typed_payload[None]`、两个 code 域消费方用例 |
| G5 | `cat-file` 的 `^{commit}` 后缀 | 去掉后缀（只验对象存在） | 2 failed / 316 passed | `test_anchor_pointing_at_non_commit_object_is_unknown[blob]` / `[tree]` |
| G6 | 对象存在性校验整段 | `if rc != 0:` → `if False:` | 4 failed / 314 passed | `test_anchor_object_absent_is_unknown` + blob/tree 两条 + typed payload |
| G7 | `main()` 的 `GateIndeterminate → UNKNOWN(6)` 映射 | 拆掉 try/except | 7 failed / 311 passed | 全部 CLI 层锚用例（退出码逸出契约集 → 变红） |
| G8 | 锚源 = 录锚（反推锚已退役） | **复活** `git log -1 --format=%H -- <report>` 作锚 | 9 failed / 309 passed | 含 `test_touching_the_report_does_not_move_the_anchor` |
| G9 | verify 读点「先定结论、再求失鲜」次序 | 把 `is_stale` 挪回 `v_state` 判定之前 | 5 failed / 313 passed | `test_unclosed_verify_frontmatter_keeps_structural_hint`、`test_verify_report_no_anchor_in_progress` 等 |
| G10 | fixture 两段提交模型 | 删掉第一段 `commit_all` | **122 failed** / 196 passed | `test_fixture_two_stage_model_puts_artifacts_before_report` 起全链 |
| G11 | producer 模板锚字段 | 从 `sdflow-spec-review` 模板删掉锚行 | 2 failed / 316 passed | `test_producer_templates_declare_reviewed_sha_verbatim`、`test_producer_anchor_is_direct_child_of_ship_gate` |

**G8 的手段与其余不同源（tasks 5.5 明文要求登记）**：新实现里没有「反推逻辑」可删——
删掉它就没有锚了。故变异手法改为**以旧实现为参照物**：把 `report_last_sha` 的表达式塞回锚位，
观察 `test_touching_the_report_does_not_move_the_anchor` 变红。这条用例的盘面是「拍板 → 偷改
design.md → 有人给报告补个空行」：旧锚会前移到排版提交、埋掉未审改动判 fresh，新锚推不动。

**G1/G2 的覆盖形状值得记一笔**：这两个变异**只**让 parser 层用例变红，CLI 层的
`test_syntactically_invalid_anchor_is_unknown` 仍绿——因为缩写 SHA / 非法 hex 走到语义层后
`cat-file` 照样失败，仍是 UNKNOWN(6)。这正是 ADR-1 坚持「两层校验 MUST 显式分层」的实证：
端到端结论相同，但**层归属**只有层内用例证得出来。若只写 CLI 用例，语法层被整层删掉都不会变红。

## 4. 遇到的问题与决策

**D1 · `GateIndeterminate` 提前到本票落地**（原挂 tasks 3.5/3.6，属 Task 2）。
理由：本票的四个 fail-closed 形态没有它就落不了地；把映射点先建好且 category 空间一次开全
（含 Task 2 的三类），Task 2 只需在三个 git helper 里 `raise`，不必回头改 `main()`。

**D2 · 退役 `freshness=uncommitted` 语义**（对应既有用例 `test_uncommitted_report_is_fresh`，
属 5.15b「需重新设计等价用例」，非纯删除）。
该语义是**反推锚的产物**：旧实现推不出锚时只好特判。新锚是录下来的常量，与报告是否进过提交无关。
Q3=A「人机同权、手写产物合法」的实质**保住了**——手写报告不被拒，只是同样要落锚。
用例改名为 `test_uncommitted_report_still_evaluated_by_its_own_anchor`，断言未提交报告携有效锚时
正常求值判 `fresh`，且**不**因「没进过提交」被判缺锚。

**D3 · verify 读点次序改为「先定结论、再求失鲜」**（对应既有用例
`test_stale_unclosed_verify_appends_hint`，同属 5.15b）。
起因：`reviewed_sha` 与结论字段**同一次写入落盘**（ADR-1），∴「报告在但无结论」这一合法中间态
本就没有锚可读。若仍先跑 `is_stale`，该态会被判「缺锚 → UNKNOWN(6)」，把正常的
`STEP_IN_PROGRESS` 变成判定不能。改后与 **code-review 读点次序一致**（那边本来就是先定结论）。
原 OV-2 关心的承诺——「未闭合 frontmatter 的结构提示不被吞掉」——由 `STEP_IN_PROGRESS`
分支自带的 `_unclosed_frontmatter_hint` 承载，用例改名为
`test_unclosed_verify_frontmatter_keeps_structural_hint` 并**加强**了断言（新增
`"陈旧" not in reason`——无有效结论的报告不该被称「结论陈旧」，这恰是 OV-2 的本意）。
随之删除 step 9 尾部一处**变成死代码**的重复 `v_state is None` 分支（纯删除）。

**D4 · `_is_full_oid` 只认小写**。三个 producer 的锚一律取自 `git rev-parse`（恒小写），
单一规范形使诊断无歧义；人手写出大写时 fail-closed 且诊断点名规则。方向安全。

**未越界**：1.5/1.6/1.6b/1.7/1.7b/1.8（评审 SKILL 的提交时序与流程纪律）、比内容与求值窗口
（Task 3/4）、code 域顶层条目比较（Task 5）、git 调用层容错（Task 2）均未动。
1.4 中只写了「锚是什么、取值怎么来、须与结论同写」，两段提交时序留给 Task 6。

## 5. Concerns

1. 🔴 **本仓自身的 `harden-gate-git-layer/spec-review-report.md` 缺 `reviewed_sha`** —— 本 change
   一旦生效，对**它自己**跑 gate 会 `UNKNOWN(6) / anchor-missing`（design.md Migration Plan 第 3 条
   已预见：「在途的只有本 change 自己」）。补锚 = 执行**拍板回写**，是编排层/人的动作，且锚必须指向
   「设计门拍板时被批准的那个盘面」（`e249db1 gate(design): …` 前后），implementer 不应自行选定 ⇒
   **未自行写入，显式上抛**。建议编排层在本 change 收尾前补，锚取 `e249db1`（或其父，视拍板时四件套
   落盘位置而定，需人核对 `git log`）。
2. **SHA-256 object-format 仓被判非法**：`_is_full_oid` 按 design.md ADR-1 写死 40 位；
   sha256 仓的 64 位 OID 会走 `anchor-invalid`。方向 fail-closed 安全，但对该形态的仓是硬阻断。
   design 未提及此面，此处显式登记，不自行放宽（放宽属改设计）。
3. **`is_stale` 内部仍是旧的帧枚举实现**，本票只换了锚源。design.md ADR-2 的「比内容」在 Task 3/4
   落地；在那之前，锚正确但比较手段仍是被判定为有缺陷的那一套（不构成回归，属分票推进的中间态）。
