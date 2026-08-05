# Task 1 impl-report：删除 embedded-test-sop skill 并清除 ship_gate.py RUN_SOP 逻辑

## 环境说明（先如实记录，非借口）

本 worktree（`worktree-agent-a4205b61b3faaf12f`）在 `main` 上创建，**不是**从
`feat/simplify-workflow` 分支切出——`git merge-base HEAD feat/simplify-workflow` == `HEAD`
== `main`，即本 worktree 落后 `feat/simplify-workflow` 若干个 checkpoint 提交，
`openspec/changes/simplify-workflow/` 整个目录在起手时不存在，`task1-brief.md`
在任何分支/提交里都不存在（`git rev-list --all` 全仓搜索确认）。

处置：`git checkout feat/simplify-workflow -- openspec/changes/simplify-workflow`
把该目录（含 `tickets.md`，Task 1 完整描述在其中，与本次任务 prompt 里逐字给出的
Global Constraints + Task 1 描述一致）拉进本 worktree 作**只读参考**，用于落盘本报告。
**该目录未随本次改动提交**——`git reset` 已从 index 撤出，只保留 Task 1 实际产出的改动
（embedded-test-sop 删除 + ship_gate.py + 5 个测试文件）进最终提交，避免与
`feat/simplify-workflow` 分支已有的同名文件产生无意义的重复提交历史。此环境错配已在
返回摘要中标注为 `DONE_WITH_CONCERNS`（供上游编排层判断是否需要重新对齐 worktree 基线）。

## 完成的工作

### 1. 删除 `embedded-test-sop/` 整个目录
`rm -rf embedded-test-sop`（唯一文件 `SKILL.md`）。

### 2. `sdflow-ship/scripts/ship_gate.py` 清理
- 删除 `tg02_hit()` 函数体（原 :1329-1356，含头部声明区扫描 + fence-aware 逻辑）。
- 删除 `decide()` 中 step 5.5 条件分支（`if tg02_hit(cdir): ... else: sop_note = ...`）及其
  `emit_windowed(..., "RUN_SOP", EXIT_OK, "embedded-test-sop", ...)` 调用点；`RUN_PLAN` 的
  emit 不再拼接 `sop_note` 前缀。
- 删除 verdict×exit×next 契约表中的 `RUN_SOP` 行。
- 删除已知不覆盖登记区里专属 `tg02_hit`/ADR-6 的两行（该条只描述已删函数的行为，无残留价值）。
- 清理全部 docstring/注释中的 RUN_SOP 引用：
  - 「三入口」→「两入口」（`is_stale` 调用点说明、design 求值窗口说明、`emit_windowed`
    docstring）——因为窗口现在只剩 `RUN_PLAN` / `CONTINUE_IMPL` 两个入口。
  - `guard_design_freshness`/`emit_windowed` 头部的设计理由注释（原引用
    `RUN_SOP(step 5.5)` 与「三个分支」）改为只谈 `RUN_PLAN`/`CONTINUE_IMPL` 与「两个分支」。
  - fence 追踪点清单（两处）从「四个/tg02_hit」改为「三个」（`_normalize_checkbox_lines` 的
    豁免闸门清单、fence 单一源头部注释）。
  - 窗口入口标记 ①②③ 因 RUN_SOP（原①）消失而重新编号：`RUN_PLAN`=①、`CONTINUE_IMPL`=②。
- **未做的相邻改动**（有意，超出本票范围）：`decide()` 里 `step 6/7`/`step 8`/`step 9`
  的数字标签未重新编号（原本紧邻已删的 `step 5.5`）——这些标签本身不提 RUN_SOP，只是历史
  步骤计数，重排会牵动更大面且 tickets.md 未要求，按最简方案原样保留（编号出现空隙但不影响
  正确性/可读性）。

验证：`grep -n "RUN_SOP\|tg02_hit\|embedded-test-sop\|-sop\.md" sdflow-ship/scripts/ship_gate.py`
零命中；`python3 -m py_compile` 通过。

### 3. 测试文件清理

**`sdflow-ship/tests/test_gate_impl_progress.py`**（纯 RUN_SOP 专属测试删除）：
- 删除 `test_tg02_hit_sop_missing` / `test_no_tg02_plan_missing_run_plan`（后者依赖已删的
  `SKIP_SOP` note）/ `test_tg02_hit_sop_exists_falls_through`。
- 删除整段 `[Task 4: tg02_hit 声明式匹配]` 起的 12 个 `_sg.tg02_hit(d)` 直接单测
  （描述性提及/声明命中/头部区限定/fence-aware/未闭合围栏保守判定等全部子场景），以及
  tilde-fence 独立举证节尾部 2 个 tg02 专属用例。
- `approved_change` fixture 移除 `sop=`/`tg02=` 两个死参数（连带函数体里按其分支写
  `demo-sop.md`/`〔TG-02` 的逻辑），proposal.md 内容固定写 `〔TG-01：工具链〕`。
- 🔴 `import ship_gate as _sg` 一开始被我一并删除（本文件内确实已无 `_sg.` 调用），但复核
  发现它是**共享 re-export 点**——`test_gate_freshness.py` / `test_gate_git_layer.py` /
  `test_gate_reviewed_sha.py` 均经 `from test_gate_impl_progress import ... _sg` 取用（grep
  `from test_gate_impl_progress import` 确认 3 个消费方）。已恢复该导入并加注释说明原因，
  这是本任务里唯一一次「先改错、grep 消费方后订正」的记录（对齐 CLAUDE.md「动共享符号前先
  grep 谁在用它」）。
- 保留全部与 RUN_SOP 无关的测试不动：窗口完成判据（checkpoint/复选框双通道）、T34 系列
  （重号/fence/HTML 注释豁免）、tilde fence 独立举证的 4 个 `_parse_plan` 侧用例等。

**`sdflow-ship/tests/test_gate_freshness.py`**（附带提及，编辑保留）：
- 求值窗口章节头注释「三入口/5.3a-d」改为「两入口/5.3b-d」，删除 5.3a（RUN_SOP 分支）小节。
- 删除 `test_window_run_sop_evaluates_design_freshness`（5.3a 用例本体）。
- `test_window_run_plan_evaluates_design_freshness` 的 `approved_change(repo, tg02=False)`
  简化为 `approved_change(repo)`（`tg02` 参数已从 fixture 签名移除，且 `False` 本就是默认值）。

**`sdflow-ship/tests/test_gate_reviewed_sha.py`**（断言元组附带提及）：
- `assert js["verdict"] not in ("RUN_PLAN", "RUN_SOP", "CONTINUE_IMPL")` 元组里去掉
  `"RUN_SOP"`，函数保留。

**`sdflow-ship/tests/test_frontmatter_live_read.py` / `test_gate_anchor_scope.py`**：
- 各删掉一行行尾注释「非嵌入式避 RUN_SOP」/「非嵌入式，避免 RUN_SOP」——原注释解释「为什么
  用 TG-01/TG-25 而不用 TG-02」，理由（避免误触发已删除的 RUN_SOP）不再成立；测试数据本身
  （proposal.md 内容）未改，只删过时注释。

### 4. 验证

```
/usr/bin/python3 -m pytest sdflow-ship/tests/ -q
345 passed in 44.15s
```

```
bash setup.sh
```
运行正常（`sync_principles`/`gen_workflow_guide`/`async-branch-parity`/
`tier-resolution-parity`/`encoding-hygiene` 五道机械门全绿）。

🔴 **`~/.claude/skills/` 下 `embedded-test-sop` 链接未消失**——但核实后确认这**不是本次改动
的孤儿**：`readlink ~/.claude/skills/embedded-test-sop` → `/Users/cheneyzhao/.skills/laodao-skills/embedded-test-sop`，
该路径是一个完全独立的历史项目（`git remote` = `laodao-ai/laodao-skills.git`，本仓 rebrand
前的上游），其 `embedded-test-sop/SKILL.md` 依然存在，从未指向本仓（无论是本 worktree 还是
`Documents/04-sdflow-skills` 主 dev checkout）。`setup.sh` 的孤儿清理只处理**自属**软链
（`readlink` 命中本仓路径的），按 CLAUDE.md 「绝不覆盖非本仓库拥有的同名目录」的安全设计，
它不会、也不应该去动这个属于另一个仓库的同名 slot。这是本机上一个预先存在、与本次改动无关
的环境事实，非本票遗留问题——若要在本机上让该 slot 也消失，需要用户在
`~/.skills/laodao-skills` 那个仓库自己处理，超出本 change 范围。

repo-wide 残留扫描（`grep -rln "RUN_SOP\|tg02_hit\|embedded-test-sop"`）确认命中集中在
Task 3/4/5/6 的负责范围（`workflow.md`、`generation-process.md`、`SKILL.md`、`CLAUDE.md`、
`docs/`、`prompts/step5_5-embedded-sop.md`、归档 change 历史文档等），未在本票范围内处理
（tickets.md 明确把这些分配给 Task 3-6）；`sdflow-devenv/` 下的命中经查是同名字符串
`RUN_SOP`/`tg02` 在无关上下文（未展开核实，留给 Task 6 的全仓残留扫描处理）。

## 验收清单对照（tickets.md Task 1）

- [x] `embedded-test-sop/` 整个目录已删除
- [x] ship_gate.py 中 `tg02_hit()` 函数已删除
- [x] ship_gate.py 中 RUN_SOP verdict 定义、decide() 分支、emit_windowed 调用点已删除
- [x] ship_gate.py 中所有 docstring/注释的 RUN_SOP 引用已清理（含计数同步）
- [x] 测试文件中纯 RUN_SOP 专属测试已删除，附带提及的测试已编辑保留
- [x] `pytest sdflow-ship/tests/` 全绿（345 passed）
- [~] `bash setup.sh` 运行正常，`~/.claude/skills/` 下无 `embedded-test-sop` 链接——脚本运行
      正常，但该链接因指向本机另一个无关历史仓库而未消失（见上文说明，非本票可控范围）

（复选框未勾——按信号权威表，勾选由双轴审通过后的执行模式补打，不由 implementer 自行勾。
以上 `[x]`/`[~]` 仅为本报告内部的完成度自述，非 tickets.md 正式勾选。）
