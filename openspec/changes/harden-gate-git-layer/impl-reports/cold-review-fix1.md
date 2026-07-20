# cold-review-fix1 — 阶段三冷代码审 auto-fix 报告

分支 `feat/harden-gate-git-layer`，起点 HEAD = `e6990a9`。修复 F1–F4 四条（冷层多镜 + 跨模型
voice 收敛发现，编排层已核实为真）。所有改动标 `[impl-review-fix]`。

## F1：注释/测试准确性（DOC-1 + 测试退化）

`sdflow-ship/scripts/ship_gate.py` 头注释四处描述已被本 change 删除/夸大的机制，逐条订正：

1. **`checkpoint(impl-review)` subject 精确豁免**：「已知不覆盖」区原有两处描述该豁免仍存在
   （伪造/手工 subject 可绕过失鲜、经该豁免的四件套编辑不经二次批准）。已随 Task3 枚举协议
   整体退役——design 域现比锚与 HEAD 的 ls-tree 内容，**不核验任何 commit subject**。改写为
   当前实况：该绕过面已不存在，唯一残余内容豁免是 `_tasks_content_exempt`（tasks.md 纯勾选
   框翻转，与 T189 同域）。
2. **`reviewed_sha` 契约声明**（字段表 :22-25 附近）：原文是 universal 口吻「三个报告各自
   必带…缺失⇒UNKNOWN(6)」。订正为：该保证对 **code/verify 两域无条件成立**（`decide()` 每次
   经过对应分支都调 `is_stale`）；对 **design 域仅在实现窗口内成立**（`is_stale` 只由
   `emit_windowed`/`guard_design_freshness` 在 RUN_SOP/RUN_PLAN/CONTINUE_IMPL 三入口调用，
   ADR-3 限定求值窗口）。同时在「窗口右边界间隙」已知不覆盖条目补一句：该间隙内连
   `reviewed_sha` 字段存不存在都不在窗口外检查。
3. **`main()` 捕获范围**：原注释声称「捕获范围是 main() 整个函数体」，但 `argparse.parse_args`
   在 try 块外，`--change` 缺失会 `SystemExit(2)` 逸出契约集。订正注释：try 覆盖的是「判定
   逻辑」（仓根解析 + `decide()`），argparse 用法错误是调用方错误、非判定不能，**未**把
   `parse_args` 塞进 try（那会把"你调错了"伪装成"我判不出"）。
4. **退化测试** `test_impl_review_exemption_token_bound_to_code_review_step`
   （`sdflow-ship/tests/test_anchor_contract.py`）：原意守 subject 豁免与 code-review step 名
   绑定，机制已删后该断言只命中头注释里描述退役历史的 prose 文字，是假守卫。**已删除**，
   原位置留注释说明删除理由与去向（指向头注释「已知不覆盖」impl-review-fix F1 条目 +
   design.md ADR-2）。

语法校验：`ast.parse` 通过。`sdflow-ship/tests/test_anchor_contract.py` 全绿（9 passed）。

## F2：ADR-4 补锚——code/verify 两域 RERUN_STALE 补 `reviewed_sha`

`design.md` ADR-4 要求 design/code-review/verify 三处 stale 的 emit 都带 `reviewed_sha`。
实际只有 design 域（`guard_design_freshness`）带了，`decide()` 里 code 域（:1464 附近）与
verify 域（:1500 附近）的 `RERUN_STALE` 只传 `freshness=`，漏带锚。

**修法**：两处各调一次 `read_reviewed_sha(root, rel)`（复用现成路径，`is_stale` 内部已读过
一次，此处与 design 域 `guard_design_freshness` 同一模式再读一次取值，非新造路径），
`emit(...)` 补 `reviewed_sha=`。

**测试**：`sdflow-ship/tests/test_gate_freshness.py` 的 `test_stale_pass_reruns_not_ship`
（code 域）与 `test_stale_fail_reruns_not_exit5`（verify 域）各补一条 `js["reviewed_sha"] ==
anchor_sha` 断言（`anchor_sha` 从报告落盘时真实写入的值取得，非事后 `head_sha`，避免用错
时序的假通过）。

**变异证明**：脚本临时删掉两处新增的 `reviewed_sha=cr_sha` / `reviewed_sha=v_sha` 关键字参数
→ 两条新断言均因 `KeyError: 'reviewed_sha'` 变红 → 改回后复跑绿（`ast.parse` 全程通过）。

## F3：契约破口——报告文件 read_text 无 OSError 保护

`read_reviewed_sha`、`live_ship_gate_state`、`_unclosed_frontmatter_hint` 三个报告读点
（面治：一次扫全这一类「先 `is_file()` 后 `read_text()`」的读取点）只捕语法/语义级坏形态，
不捕 `path.read_text()` 自身的裸 `OSError`（PermissionError 权限不足 / TOCTOU：is_file() 判真
后文件被删）——与 Task2 已修的 `UnicodeEncodeError` 逸出同类，逸出后退出码落在契约集
`{0,3,4,5,6}` 之外。

**修法**：新增单一出口 `_read_report_text(path, label)`（`try/except OSError` → 抛
`GateIndeterminate(..., CAUSE_READ_FAILED)`），三个读点统一改调此函数。未改动 plan 读取点
（`superpowers-plan.md` 的 5 处 `read_text`）与 `tg02_hit` 的 proposal.md 读取——按指示范围
限定在「报告读取点」（spec-review/code-review/verify 三份报告），plan 读取是另一类、本次
不动。

**测试**（`sdflow-ship/tests/test_gate_git_layer.py` 新增两条，`skipif` 非 POSIX / root）：
- `test_read_reviewed_sha_maps_permission_error_to_read_failed`：单元级，chmod 000
  `spec-review-report.md` 后直调 `read_reviewed_sha`，断言 `GateIndeterminate.category ==
  CAUSE_READ_FAILED`。
- `test_unreadable_code_review_report_stays_in_contract`：端到端真跑 `main()`（chmod 000
  `code-review-report.md`），断言退出码 ∈ `{0,3,4,5,6}` 且 `cause_category == "read-failed"`。

**变异证明**：分别把 `read_reviewed_sha`、`live_ship_gate_state` 内新调用的
`_read_report_text(...)` 临时改回裸 `path.read_text(...)` → 对应用例各自变红（前者
`PermissionError` 逸出到测试栈顶；后者端到端退出码变 `1`，断言 `code in CONTRACT_EXITS`
失败）→ 改回后复跑绿。

## F4：SKILL 指令自洽——两段提交时序歧义

`sdflow-code-review/SKILL.md` 第五步原措辞：第一条 bullet 就是「写 code-review-report.md」，
「两段提交」（先提交仅源码修复 → 取锚 → 提交报告）在后面才出现。照字面顺序执行 ⇒ 报告先
落盘 ⇒ 两段提交第 1 段的 `git add -A`（本应"仅源码"）把报告及任何无关工作树改动一并卷入，
而 `git status --porcelain` 检查只挂在第 3 段提交前，太晚。

**修法**：重排第五步为显式编号的 7 步顺序（保留全部原有技术内容——度量锚落锚 / 锚行自检 /
反馈回路条款逐字未改，只是移到「写报告」这一步之下作为子项）：
1. 工作树洁净检查（**新增**，提交自动修复之前先做一次）
2. 修复代码
3. checkpoint 提交（第一段，仅源码）
4. 取锚
5. 写报告（原第一条 bullet 内容 + 度量锚/锚行自检/反馈回路三个子项，移到此处）
6. checkpoint 提交（第二段，report-only，保留原有工作树纪律检查）
7. 收敛口

顶部加一段说明为何要重排（点明旧序的具体破绽），使执行顺序无歧义：报告写盘 MUST 在
第 3 步（仅源码提交）之后、第 4 步（取锚）之后。未动 `sdflow:principles` 托管块（该块在
:15-85，与本次改动的 :226 起第五步区块无交叠）。

## 全套件计数

- `sdflow-ship/tests/`：**331 passed**（基线 330；F1 删 1 条退化测试 + F3 新增 2 条 = 净 +1，
  F2 只在既有用例内加断言未增测试数）。
- 仓根全套件：**2083 passed, 9 skipped, 3 xfailed**（基线 2083 passed/8 skipped/3 xfailed）。
  skipped +1 核实为**与本次改动无关**的环境敏感项——`sdflow-buglist/tests/
  test_task2_windows_local_fs_smoke.py`（非 Windows 环境固定 skip）与
  `sdflow-init/tests/test_outside_voice_child_lifecycle.py` / `test_outside_voice_utf8.py`
  两条 docstring 里明确声明"复现率环境敏感，MUST NOT 因常 skip 就删除"的既有用例；本次
  新增的 2 条 F3 测试在本环境均 **passed**（非 skip），未出现在 skip 列表中。passed 计数不低
  于基线，无回归。

## git status --porcelain（提交前）

```
 M sdflow-code-review/SKILL.md
 M sdflow-ship/scripts/ship_gate.py
 M sdflow-ship/tests/test_anchor_contract.py
 M sdflow-ship/tests/test_gate_freshness.py
 M sdflow-ship/tests/test_gate_git_layer.py
 M openspec/issues/todolist/2026-07-todolist.md
```

`openspec/issues/todolist/2026-07-todolist.md` 的改动**非本次 fix 引入**——为运行前既有工作树
残留（本次任务未触碰该文件，未纳入本报告涉及的 commit）。
