# impl-report — task3-cross-platform-fix1

修复 change `fix-mechanical-layer-silent-failures` 在 Task 3（跨平台）期间暴露的高危缺陷 F-新1，
并补齐 F-新2 的测试缺口。分支 `feat/fix-mechanical-layer-silent-failures`。

## F-新1（高危，已修复）：`_ov_bytes_at` 失败被静默当成「无需回扫」

### 根因确认

`sdflow-init/assets/hack/outside-voice.sh` 的 `utf8_head_trim()` / `utf8_tail_skip()` 在依赖
`od`（经 `_ov_bytes_at`）取字节失败时，旧实现落回 `echo 0`——与「回扫算出来的合法结论就是 0」
（如"末 4 字节全是 continuation"、"纯 ASCII 无需回扫"）**完全同形**。`render_prompt()` 里唯一的
失败判据是 `case "$htrim" in ''|*[!0-9]*) ... backscan_ok=false ;; esac`，而 "0" 既非空串也非
非数字，永远接不住这条路径 ⇒ `OV_UTF8_BACKSCAN_UNAVAILABLE=1` 哨兵行**从未有机会触发**，
是一段死代码。

### 面治扫描（基准③，不止补被点穿的一处）

系统扫了本脚本内**全部** `2>/dev/null` 及命令替换失败可能被吞的位置（`grep -n '2>/dev/null'
outside-voice.sh` 全量核对），结论：

| 位置 | 是否属于"静默空输出=合法结论"这一形态 | 处置 |
|---|---|---|
| `utf8_head_trim` 内 `_ov_bytes_at`（od）失败 | ✅ 是（F-新1 主体） | **已修** |
| `utf8_tail_skip` 内 `_ov_bytes_at`（od）失败 | ✅ 是（同一函数家族的对称分支） | **已修** |
| `utf8_tail_skip` 内 `wc -c` 失败 | ✅ 是——**同一函数里的第二个实例**，旧代码同样 `echo 0` 且注释明确写着"拿不到大小就回退 0（不动）" | **已修**（与上面同一次改动收口） |
| `render_prompt` 自己的 `wc -c`（:274） | 否——本就 fail-loud `exit 2`，不存在"静默默认值" | 无需改 |
| `secret_scan` 里 `grep -nE ... \| head \| cut \| tr \| sed`（:147） | **形态相似但更复杂**：`grep` 失败（非"无匹配"，如正则/环境异常）时管道后半段同样产出空 `lines`，与"未命中"同形。**未修**——理由见下 | **已排查，判定超出本次范围，见下** |
| `resolve_timeout_bin` 的 `command -v` 兜底 | 否——空值本身就被调用方 fail-loud 判空 | 无需改 |
| `repo_root=$(git rev-parse ...) \|\| repo_root="$PWD"` | 否——这是文档化的正常降级（"不在 git 仓则用 PWD"），不是"取不到又假装合法" | 无需改 |
| `cp last-message.md cli.log 2>/dev/null \|\| : > cli.log`（claude 分支） | 否——`cli.log` 只用于失败诊断展示，不作为任何正确性判据输入 | 无需改 |

**`secret_scan` 的 grep 为何未修**：要把"grep 真错误"和"grep 无匹配"分开，需要捕获 grep 自身的
退出码——但当前写法把它塞进 `$(...)` 命令替换里的多段管道，`$?`/`PIPESTATUS` 在这种写法下
拿到的是管道**最后一个**命令（`sed`）的退出码，不是 `grep` 的；要正确捕获须重构成
`PIPESTATUS[0]`（且要求整条管道跑在调用方 shell 里、不能再套进 `$(...)`子壳），是一次**行为变更
而非同形小补丁**，触及安全关键的密钥扫描路径。这超出了"F-新1 面治：找同一形态的其他实例"的
授权范围（该授权是找**同形**残留，不是借机重构一个不同复杂度的安全函数）。**建议**：后续单独
开一个 change/buglist 项处理，不在本次顺手改。

### 修复内容

`sdflow-init/assets/hack/outside-voice.sh`：

- `utf8_head_trim()`：`_ov_bytes_at` 读到的 `bytes` 数组为空时（cnt 在此处恒 >0，正常情况下不可能
  为空数组，为空即代表 od 失败）输出**空串**而非 `0`，交由 `render_prompt` 已有的 case 守卫接住。
- `utf8_tail_skip()`：新增 `got` 计数器，`_ov_bytes_at` 未读到任何字节（`got=0`，cnt 恒 ≥1）时
  同样输出空串；`wc -c` 失败分支也从 `echo 0` 改为 `echo ""`（同一函数内的第二处同形病灶）。
- `render_prompt()` 内 S3 段落补充注释：说明该 case 守卫此前是死分支，现在才是活路径。
- 头部契约注释新增说明该行为差异；`OV_VERSION` 1.4.0 → **1.4.1**（纯内部实现修复，
  stdout/stderr 格式与 exit code 契约不变，仅让已文档化的 `OV_UTF8_BACKSCAN_UNAVAILABLE=1`
  信号第一次真正可达）。

### 测试

`sdflow-init/tests/test_outside_voice_utf8.py` 新增/改：

1. `test_head_trim_reports_failure_not_zero_when_byte_read_fails` —— 覆盖 `_ov_bytes_at` 失败，
   `utf8_head_trim` 输出必须是空串（不 mock 函数本身，只让其依赖失败，走真实分支）。
2. `test_tail_skip_reports_failure_not_zero_when_byte_read_fails` —— 同上，`utf8_tail_skip` 的
   对称分支（`wc` 成功、`_ov_bytes_at` 失败）。
3. `test_render_prompt_real_od_failure_reports_backscan_unavailable` —— ⭐端到端、PATH shim 让
   **真实 `od` 命令**失败（不 mock 任何 outside-voice.sh 内部函数），断言
   `OV_UTF8_BACKSCAN_UNAVAILABLE=1` 真的打印。这是比既有
   `test_backscan_fallback_emits_visible_marker`（该测试 mock 掉两个函数本身，只验证
   `render_prompt` 守卫逻辑，从未验证过函数在真故障下的真实输出）更强的证据。
4. `test_tail_skip_unreadable_file_does_not_pollute_stderr_contract`（既有 S1 测试）：其
   `wc` 失败分支的 stdout 断言从 `"0"` 更新为 `""`——旧断言其实锁死的正是本次要修的 bug
   （chmod 000 触发的 wc 失败，旧实现恰好也 `echo 0`），必须随修复同步更新，否则该测试会与
   修复语义矛盾。

### 变异验证（承重证明，已实跑）

把上面四处修复手工回退（`bytes`/`got` 空判空分支去掉、`wc` 失败分支 `echo ""` 换回 `echo 0`），
重跑同一批测试：

```
FAILED test_outside_voice_utf8.py::test_tail_skip_unreadable_file_does_not_pollute_stderr_contract
  AssertionError: 取字节失败时不得输出'0'... assert '0' == ''
FAILED test_outside_voice_utf8.py::test_head_trim_reports_failure_not_zero_when_byte_read_fails
FAILED test_outside_voice_utf8.py::test_tail_skip_reports_failure_not_zero_when_byte_read_fails
FAILED test_outside_voice_utf8.py::test_render_prompt_real_od_failure_reports_backscan_unavailable
  AssertionError: 真实 od 失败没有被识别为失败（F-新1 复发）:
  'OV_TRUNCATED_DROPPED_BYTES=128\nOV_UTF8_BACKSCAN_DROPPED=0\nOV_TRUNCATED=true\n'
4 failed, 95 passed in 21.21s
```

四条新增/改动测试全部转红，其余 95 条不受影响 —— 证明测试确实由本次修复承重，不是巧合绿。
随后已还原修复（`cp /tmp/outside-voice.sh.fixed.bak` 覆盖回正确版本），重跑确认全绿
（`111 passed`，见下方全量结果）。

## F-新2（测试缺口，已补 + 发现真实残余）

### 缺口

`test_outside_voice_child_lifecycle.py::test_runner_subtree_dies_when_parent_is_signalled` 用的
假 runner 从不忽略 TERM，因此"runner 主动忽略 SIGTERM 时，`ov_cleanup` 的 KILL 兜底 /
`timeout -k` 升级能不能真的灭掉整棵子树"这条路径此前从未被验证过。

### 实跑结果：子树【存活】——真实残余，非推测

新增假 runner（`trap '' TERM`）+ 手工探针双重验证，结论一致：**runner 及其孙进程在
`ov_cleanup` 完成 TERM→KILL 升级后仍然存活**，reparent 到 PID 1。

根因：`OV_RUNNER_PID` 记的是 **`timeout` 自身**的 PID，不是 runner 的 PID。`ov_cleanup` 先对
该 PID 发 TERM——`timeout` 会转发给子进程组，但 runner 若忽略 TERM 则不为所动；`timeout` 自己
的 `-k 10` 组级升级窗口长达 10s，而 `ov_cleanup` 只宽限约 1s 就直接对 `$OV_RUNNER_PID`
（即 `timeout` 本身）发 SIGKILL——SIGKILL 不可捕获，`timeout` 瞬间被杀死，**来不及**跑到它
自己那条"向子进程组转发 KILL"的升级逻辑。手工探针实测（macOS）：

```
runner_pid=55916 grandchild_pid=55926
runner alive?      yes
grandchild alive?  yes
  PID  PPID  PGID COMMAND
55916     1 55915 bash .../codex exec ...
55926 55916 55915 sleep 300
```

（PPID=1 印证已 reparent 到 init/launchd。）

### 处置（按指令：MUST NOT 假装没事，登记而非静默接受，不在本次修复该根因）

- **`design.md` 已改**——D2 诚实边界残余表新增第 **(d)** 条（原 3 条→4 条），失败模式表新增
  **F8**，Risks/Trade-offs 段同步引用。**⚠ 已改 design.md，需再次补锚（人门/design_approved
  frontmatter 或 ship-gate 视 change 状态可能需要重新走一次锚点确认）——请 orchestrator 注意。**
- **`test_outside_voice_child_lifecycle.py` 新增两个测试**：
  1. `test_runner_ignoring_term_survives_kill_escalation_documented_residual` —— 锁定该残余的
     真实行为（子树存活），测试结束后自行 `SIGKILL` 清理，不污染开发机/CI。
  2. `test_term_ignoring_residual_is_documented_in_design` —— 机械锁 `design.md` 确实含第
     (d) 条描述，且全文无"已根治/已消除"等越界断言（与既有
     `test_sigkill_residue_is_documented_not_claimed_solved` 同形，那条锁脚本注释，这条锁
     design.md）。

**本次不修复该根因**（改变 `ov_cleanup` 的信号投递目标为进程组，或调整宽限期与 `timeout -k`
窗口的关系）——这是"补测试缺口"任务的明确边界，修复根因超出本次授权范围，已在
design.md 与测试文档串里留好后续 change 的入口。

## 变更文件清单

- `sdflow-init/assets/hack/outside-voice.sh` —— F-新1 修复；`OV_VERSION` 1.4.0→1.4.1；契约注释同步
- `openspec/changes/fix-mechanical-layer-silent-failures/design.md` —— D2 残余表补第 (d) 条 + F8 + Risks 引用（因 F-新2 实测为真才改，按指令执行）
- `sdflow-init/tests/test_outside_voice.py` —— version golden 1.4.0→1.4.1
- `sdflow-init/tests/test_outside_voice_utf8.py` —— 新增 3 条 F-新1 测试 + 更新 1 条既有测试的过期断言
- `sdflow-init/tests/test_outside_voice_child_lifecycle.py` —— 新增 2 条 F-新2 测试

## 全量验证

```
$ /usr/bin/python3 -m pytest -q
1737 passed, 2 skipped in 100.38s

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ bash setup.sh   # 刷新 ~/.sdflow/hack/outside-voice.sh（cp 非 symlink，dev checkout 纪律 adr/0005）
$ ~/.sdflow/hack/outside-voice.sh version
outside-voice.sh 1.4.1
```

## 给 orchestrator 的显著提示

🔴 **本次修复改动了 `design.md`**（F-新2 分支判定为"子树存活"，按指令必须登记）。这会触发
`ship_gate` 设计门失鲜（本仓 `CLAUDE.md` 已知行为：改 change 四件套触发 REFUSE_START）。
若此 change 已过设计门，需要重新走一次锚点确认；若尚未过设计门，此改动会随下一轮设计审
自然纳入，无需特别处理。请据此判断是否需要补锚。

## 状态

`DONE_WITH_CONCERNS` —— 两项任务均已完成、测试全绿、变异验证已实跑；「concern」仅指上面
显著标注的 design.md 改动触发的锚点/门禁问题，需 orchestrator 确认后续动作，不代表代码或
测试本身有未解决的问题。另：`secret_scan` 的 grep 静默失败同形态候选已排查但判定超出本次
授权范围，建议后续单独立项（buglist/todolist）处理，见上文说明。
