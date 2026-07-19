# impl-report — task3-cross-platform-fix2

根治 change `fix-mechanical-layer-silent-failures` 遗留的最后一条残余：`outside-voice.sh`
`ov_cleanup()`（:406-445，行号为修复后）的 KILL 兜底升级只杀 `timeout` 单 PID，
runner 若 `trap '' TERM` 忽略终止信号则子树逃逸成孤儿（design.md D2 残余表原第 (d) 条，
`task3-cross-platform-fix1.md` 记录的 F-新2）。分支 `feat/fix-mechanical-layer-silent-failures`。

## 根因回顾（承接 F-新2，未重新推导）

`OV_RUNNER_PID` 记的是 `timeout` 自身的 PID。`ov_cleanup` 先对该 PID 发 TERM（`timeout`
会转发给子进程组，runner 未忽略时子树同灭），但若 runner 主动 `trap '' TERM` 不为所动，
`ov_cleanup` 只宽限约 1s 就直接对 `$OV_RUNNER_PID`（即 `timeout` 本身）发 SIGKILL——
SIGKILL 不可捕获，`timeout` 瞬间死亡，**来不及**跑到它自己那条「向子进程组转发 KILL」
的 `-k 10` 升级逻辑，runner 与其孙进程 reparent 到 PID 1 继续存活。

## 修法：组级 KILL（已实测验证，非推测）

**关键机制事实**（本轮手工探针实测，macOS + homebrew coreutils GNU `timeout`）：GNU
`timeout` 会 `setpgid` 把自己放进【独立进程组】，且该组的 PGID **恒等于** `timeout`
自己的 PID、**不等于**脚本自身的 PGID：

```
$ ./probe.sh
script pid=2199 pgid=2194
timeout pid=2203 pgid=2203
./probe.sh: line 9:  2203 Killed: 9               timeout -k 10 20 sleep 15
timeout dead
```

针对「runner 忽略 TERM」的真实场景（假 runner `trap '' TERM` + 背景孙进程 `sleep 300`），
组级 `kill -KILL -"$tpid"` 一次性带走全部三层：

```
timeout pid=2420, pgid=2420
$ kill -TERM 2420; sleep 1; kill -KILL -2420
2420 dead
2423 dead   (runner 本体)
2443 dead   (runner 的孙进程)
```

∴ 把 `ov_cleanup` 的 KILL 升级步（原 :364 单行）从「杀单个 PID」改成「守卫通过时杀负号
进程组」，SIGKILL 直接打穿整棵子树，不再依赖 `timeout` 来不及跑完的组内转发。

## 自杀风险守卫（本次修复的核心风险点，已加双重条件 + 测试锁死）

`kill -KILL -"$PID"` **MUST NOT 无条件发**——新增 `_ov_pgid_of`（纯取值，`ps -o pgid=`
失败/非数字一律输出空串）与 `_ov_group_kill_decision`（纯判定函数，`$1`=目标PID
`$2`=目标PGID `$3`=脚本自身PGID → `"group"` | `"single:<reason>"`）：

- **守卫①**：目标必须是【组长本身】（`目标PGID == 目标PID`）——否则该 PGID 大概率就是
  脚本自己所在的组（子进程默认继承父 pgid，除非自己 `setpgid`），组信号会打到脚本自己。
- **守卫②**：该 PGID 不能等于脚本自身的 PGID——双重确认，防守卫①在 PID 复用巧合下失手。
- 任一不满足（含 PGID 取不到）一律退回既有单 PID `kill -KILL "$PID"`，且 stderr 打印
  `OV_GROUP_KILL_DEGRADED=1 reason=<pgid-unavailable|not-leader|own-group> pid=... target_pgid=... own_pgid=...`
  （结构化字段，MUST NOT 含 context 正文，同 `OV_UTF8_BACKSCAN_UNAVAILABLE=1` 规格）——
  这是本次修复自己新引入的、刻意的诚实退化边界（与 (a)(b)(c) 那类不可消除时序窗口性质不同）。

## 面治扫描（基准③）：脚本内是否还有其他「记 PID=杀单个 PID≠杀子树」的同形实例

`grep -n "kill \|OV_RUNNER_PID\|PID="` 全量核对：脚本里唯一的 `kill -KILL`/`kill -TERM`
落点就是 `ov_cleanup` 内这一处（另有一处 `kill -0` 仅用于存活探测，不是终止动作）。TERM
阶段的单 PID kill 不受影响（`timeout` 自身会正常转发，已由既有
`test_runner_subtree_dies_when_parent_is_signalled` 覆盖）。**未发现第二个实例** ——
本次残余在脚本内是孤立的一处，不构成面。

## 变更文件

- `sdflow-init/assets/hack/outside-voice.sh`：
  - 新增 `_ov_pgid_of` / `_ov_group_kill_decision`（`resolve_timeout_bin()` 之后）。
  - `ov_cleanup()` 的 KILL 升级步改为守卫判定后二选一（组级 / 单 PID + 降级哨兵）。
  - 头部契约注释（exec 段、R2 子进程生命周期段）同步说明修法与残余(d)已治、
    `OV_GROUP_KILL_DEGRADED=1` 字段。
  - `OV_VERSION` `1.4.1` → **`1.4.2`**。
- `openspec/changes/fix-mechanical-layer-silent-failures/design.md`：
  - 新增 `### D2.1 — 组级 KILL 升级：治愈残余(d)` 小节（根因/修法/实测/守卫/守卫自身的
    诚实边界）。
  - D2 诚实边界残余表由 4 行（a-d）收回 3 行（a-c）——(d) 不再是残余，且**保留** (a)(b)(c)
    三条真·残余，未因治好 (d) 顺手声称孤儿问题已彻底根治。
  - 失败模式表 F8：状态由「残余(d)：子树存活」改为「已治〔D2.1〕」。
  - Risks/Trade-offs：拆成 3 残余的无缓解条目 + 组级 KILL 守卫退化路径的缓解条目。
- `sdflow-init/tests/test_outside_voice_child_lifecycle.py`：
  - `test_runner_ignoring_term_survives_kill_escalation_documented_residual` **翻转重命名**为
    `test_runner_ignoring_term_dies_under_group_kill_escalation`——断言从"子树存活"改为
    "子树已灭（runner + 孙进程均死，且真 GNU timeout 场景下不应触发降级）"。
  - `test_term_ignoring_residual_is_documented_in_design`（机械锁"仍是残余"）**替换**为
    `test_group_kill_fix_is_documented_in_design_without_overclaiming`（机械锁"已治 + 仍保留
    (a)(b)(c) + 无越界断言"）。
  - `test_mutation_no_op_cleanup_leaves_an_orphan`：mutation 的 `.replace()` 链新增一条，
    同时摘除组级 KILL 与单 PID KILL 两条 literal——否则旧写法只摘单 PID 分支，真 GNU
    timeout 场景下走的是组级分支，变异体仍会灭掉子树，测试会失去承重力。
  - 新增 6 条自杀风险测试：4 条纯函数单测（`_ov_group_kill_decision` 的 group / not-leader /
    own-group / pgid-unavailable 四态）+ 1 条 `_ov_pgid_of` 真实取值测试 + 1 条端到端安全
    集成测试（`test_group_kill_guard_degrades_instead_of_self_harm_when_timeout_shares_own_group`，
    用不 setpgid 的假 `timeout` 构造"目标组==脚本自己的组"真实场景，`start_new_session=True`
    隔离运行防守卫万一有 bug 时殃及本次 pytest 会话）。
- `sdflow-init/tests/test_outside_voice.py`：version golden `1.4.1` → `1.4.2`。

## 变异验证（承重证明，已实跑）

把 `ov_cleanup` 的守卫判定 + 二选一 KILL 逻辑手工回退成修复前的单行
`kill -KILL "$OV_RUNNER_PID" 2>/dev/null`（精确还原 F-新2 报告里的原病），重跑
`test_outside_voice_child_lifecycle.py`：

```
FAILED test_runner_ignoring_term_dies_under_group_kill_escalation[system:/bin/bash]
  AssertionError: 残余(d)复发：runner 忽略 TERM 后 PID=40193 仍存活——组级 KILL 升级失效
FAILED test_group_kill_guard_degrades_instead_of_self_harm_when_timeout_shares_own_group[system:/bin/bash]
  AssertionError: 守卫未按预期降级 —— rc=143
  err='...outside-voice: runner PID=40576 未响应 TERM，已 SIGKILL 兜底\n'
    （无 OV_GROUP_KILL_DEGRADED=1 —— 因为回退版根本没有守卫逻辑，不会打这行）
2 failed, 16 passed in 19.59s
```

两条直接验证本次修复的新增/改名测试全部转红，其余 16 条（含既有的
`test_mutation_no_op_cleanup_leaves_an_orphan` 自身的内部变异）不受影响——证明这两条
测试确实由本次修复承重，不是巧合绿。随后已用 `/tmp/outside-voice.sh.fixed.bak` 覆盖还原
（`diff` 确认逐字节一致），重跑确认全绿（`18 passed`）。

手工探针留下的孤儿进程（本次交互式验证的副作用，非生产测试路径产生）已用
`kill -9` 手动清理，`ps aux` 复核干净。

## 全量验证

```
$ bash -n sdflow-init/assets/hack/outside-voice.sh && /bin/bash -n sdflow-init/assets/hack/outside-voice.sh
bash5 syntax OK
bash3.2 syntax OK

$ /usr/bin/python3 -m pytest -q
1743 passed, 2 skipped in 94.57s

$ python3 hack/check_async_branch_parity.py
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ bash setup.sh   # 刷新 ~/.sdflow/hack/outside-voice.sh
    ✓ hack/outside-voice.sh @ /Users/cheneyzhao/.sdflow   (mode: symlink (Unix))
[sync_principles] ✅ 20 个投放面全部与真相源一致
[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致
[async-branch-parity] ✅ 2 处 async host 调度段逐字节一致

$ ~/.sdflow/hack/outside-voice.sh version
outside-voice.sh 1.4.2
```

## 诚实边界（未变，逐条核对未越界）

- **(a)(b)(c) 三条残余原样保留**——D2.1 只治 (d)，未触碰这三条 shell 层不可消除的时序
  窗口。`test_sigkill_residue_is_documented_not_claimed_solved` 继续把守脚本注释不越界，
  未改动该测试。
- **组级 KILL 守卫自身有诚实边界**：仅覆盖「真实 GNU-like `timeout`（会 `setpgid` 且组
  PGID==自身PID）」这类实现；非 GNU / 未 `setpgid` 的 `timeout`（如某些 busybox 变体）会
  触发 `reason=not-leader` 降级，此时仍退回旧的单 PID 行为——(d) 在这一交集场景下未变化，
  design.md D2.1 与 Risks 段已如实登记，未声称覆盖所有 `timeout` 实现。
- **Linux 侧本轮未实测**——沿用 D1 既有的 A1 分工（CI 泳道 `mechanical-gates.yml`
  ubuntu-latest 判定），未声称"macOS 绿=全平台绿"。

## Non-Goals 核对

未改 recorder 侧代码；未做 R7；未改锚行字段与 `anchor_lint` 合法组合矩阵；**未触碰任何
async/backgrounding 相关内容**（本次改动全部在 `ov_cleanup` 的信号投递目标 + 两个新增纯
函数 + 文档/版本号，`check_async_branch_parity.py` 复核通过，两层 SKILL 的 async 字节等值
marker 段未被触及）。

## 状态

`DONE` —— 修复已落地、面治扫描确认无第二个同形实例、design.md 已回改为"已治"且未越界
声称、两个既有测试已按要求翻转/替换、四条守卫单测 + 一条真实取值测试 + 一条端到端安全
集成测试全部新增、变异验证已实跑证明测试承重、全套件与 parity 门均绿、`setup.sh` 已刷新
运行 checkout。未发现需要 orchestrator 特别关注的遗留问题——本次改动虽然也改了
`design.md`（会触发 `ship_gate` 设计门失鲜，同 fix1 的先例），但已知情，无需额外提示。
