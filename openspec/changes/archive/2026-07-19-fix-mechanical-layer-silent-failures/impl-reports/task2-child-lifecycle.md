# Task 2 — 父进程被回收时 runner 子进程必死（R2）

改动文件：
- `sdflow-init/assets/hack/outside-voice.sh`（bundle 唯一权威源；仓内仅此一份，未改任何下游副本）
- `sdflow-init/tests/test_outside_voice_child_lifecycle.py`（**新增**，9 个用例）
- `sdflow-init/tests/test_outside_voice.py`（**fold 修一个既有测试脚手架泄漏**，见 §5）

未动：recorder 侧任何代码 · 锚行字段与 `anchor_lint` 合法组合矩阵 · 两层 SKILL 的
`sdflow:async-branch` 字节等值 marker 段（`test_async_branch_parity` 26 passed，Non-Goal 守卫仍绿）。

## 0. 一句话

runner 改**后台启动 + 记 PID + `wait` 取码**，清理函数先 `kill -TERM`、宽限 ~1s 后 `kill -KILL`
兜底再删 workdir，trap 覆盖 `INT/TERM/HUP/EXIT`。三个可捕获信号下 runner 子树（含孙进程）
实测全灭；退出码 `0/124/其他非零` 三条路径均有**变异验证过**的机械锁。
**SIGKILL 残余按 D2 显式登记，未声称根治。** 全套件 **1721 passed / 2 skipped**，跑完**零残留进程**。

---

## 1. 病根的更正（与直觉相反，design 已实测，此处复核确认）

不是「trap 没跑」。bash 的 EXIT trap 在 SIGTERM 下**确实执行**（workdir 被清了就是证据）。
病根是 **trap 里没有子 PID 可杀**——runner 以**前台** `timeout ...` 运行，父死后它 reparent 到
PID 1，继续跑满内层超时、继续烧 API 调用额度。

∴ 修法必须让子进程**可寻址**：后台化拿到 `$!`。

**未走的备选**（design 已证伪，本轮未重新怀疑）：`setsid` + `kill -- -PGID` —— `setsid` 在
macOS(Darwin 25) 不存在；且 GNU timeout 自建进程组并转发信号，自管进程组收益为零。
本轮的 `test_runner_subtree_dies_when_parent_is_signalled` **把「杀 timeout 连带杀孙进程」这条前提
本身也断言了**（孙进程 PID 单独验尸）——该前提若在某平台不成立，测试当场红，而不是静默退化。

## 2. 实现要点

| 点 | 做法 | 为什么 |
|---|---|---|
| 状态存放 | 全局 `OV_WORKDIR` / `OV_RUNNER_PID` | `do_exec` 的 `local` 在 EXIT trap 触发时（函数已返回）不可见；原 trap 把 `$workdir` 展进字符串可行，但清理函数还要读 PID ⇒ 生命周期状态一律放全局 |
| trap | `EXIT` + `INT/TERM/HUP`，信号 trap 里显式 `exit 128+signum` | 不 `exit` 的话 bash 在 handler 返回后会继续往下跑 |
| 幂等 | `ov_cleanup` 结尾清空两个全局 | 信号 trap 的 `exit` 会**再触发 EXIT trap**，不清空就会对已回收的 PID 二次开火 |
| 收尸后清零 | `wait` 返回后立刻 `OV_RUNNER_PID=""` | 防 EXIT trap 对一个**已被系统复用**的 PID 开火（真实误杀风险） |
| 退出码 | `wait "$pid"; rc=$?` 原样透传 | 脚本只有 `set -u`、**无 `set -e`** ⇒ 非零返回不会误中止 |
| stdin | 保留显式 `< "$workdir/prompt.md"` | 后台任务在无 job control 的壳里 stdin 默认 `/dev/null`，不显式给就读不到 prompt |

## 3. 🔴 途中撞到的真 bug：bash 3.2 变量名不是 multibyte-aware

第一版写 `echo "... 收到 $src，终止 runner ..."`，macOS 自带 **bash 3.2** 扫变量名时把全角逗号
的首字节 `0xEF` 吞进标识符 ⇒ `set -u` 下当场 `src\xef: unbound variable` **罢工**，清理逻辑
整个不执行（测试红 + 留下一地孤儿，见 §5 的第一次实跑）。

修法：`${src}` / `${OV_RUNNER_PID}` 加花括号，并在源码就地写明**这是语义性的、不是风格**——
凡「`$变量` 紧跟 CJK 标点」一律 MUST 用 `${}`。

> 这一条是本轮唯一一个**不在设计预期内**的发现。它没被 Task 1 撞到纯属运气：既有代码里
> `$变量` 后面恰好都跟着 ASCII 或空白。**全文已 grep 复查**（`\$[A-Za-z_]\w*[^\x00-\x7F]`），
> 命中的两处均在注释里，无第二个活的实例。

## 4. 测试与变异验证（跑过的才写）

新增 `test_outside_voice_child_lifecycle.py`，接缝 = 真 `timeout`/`gtimeout` + PATH 前置假 runner，
假 runner 把 (自身 PID, 孙 PID) 落盘，外部发信号后**按 PID 验尸**（不依赖进程名匹配 / ps 输出格式）。
无真 timeout 的机器上 `skipif` 跳过（假 stub 自己也 background，验不出进程组级联）。

| 用例 | 断言 | 变异验证 |
|---|---|---|
| `test_runner_subtree_dies_when_parent_is_signalled[TERM/INT/HUP]` | runner + 孙进程均不存活 | ⭐ `test_mutation_no_op_cleanup_leaves_an_orphan`：摘掉 `kill -TERM`/`kill -KILL` 的变异体**确实留下孤儿** ⇒ 验尸断言由 helper 清理逻辑承重，不是「测试环境恰好把整个 pgid 收了」 |
| `test_cleanup_logs_the_terminated_runner_pid_without_context_body` | stderr 命中 `收到 TERM，终止 runner 子进程 PID=<n>`；`CONTEXT_PROBE` 与正文均不出现 | 同上变异体下该行消失 |
| `test_exit_code_zero_passthrough_after_backgrounding` | rc=0 且最终消息原样出 stdout | — |
| `test_exit_code_124_timeout_passthrough_after_backgrounding` | rc=124 | ⭐ 把 `rc=$?` 变异成 `rc=0` ⇒ **转红**（实跑确认） |
| `test_other_nonzero_exit_code_still_maps_to_one` | rc=1 且半成品不进 stdout | ⭐ 同一变异 ⇒ **转红**（实跑确认）。为此特意让假 runner **写了**最终消息**又**非零退出——否则 rc 丢失后仍会因「输出为空」落到 exit 1，测不出东西 |
| `test_sigkill_residue_is_documented_not_claimed_solved` | 源码登记 SIGKILL 残余 + 全文无「已根治/已消除孤儿/彻底解决」类越界断言 | 构造性承重 |

**变异验证均为实跑**：变异 → 跑 → 观察转红 → 从副本还原 → 复跑确认绿。工作树无残留变异体。

## 5. Fold：既有测试脚手架的孤儿泄漏（`test_outside_voice.py`）

**发现路径**：本票的验尸纪律顺手照出来的——全量套件跑完**每轮稳定留 12 个 `sleep 300` 孤儿**，
而单跑本票文件留 0 个。排查后确认**与本次改动无关，是既有泄漏**：

`_write_fake_timeout` 的看门狗写成 `(sleep "$sec"; kill -9 "$pid") &`，收尾的
`kill -9 "$sleep_pid"` 只杀掉**子壳**，里面那个 `sleep $sec` reparent 到 PID 1 活满 `$sec` 秒
——而 `--timeout` 缺省正是 **300**。

**为什么 fold 而不 defer**（CLAUDE.md 基准 4）：与本票主题同源（父被杀后遗留孤儿子进程）、
改动 ~10 行、零风险，且它每跑一次全量测试就污染一次开发机。
**修法**：看门狗改**短 sleep 轮询**（命令一结束轮询自然退出；被强杀时最多残留一个 0.1s 的 sleep）。

修后：全量套件跑完 **0 残留进程**（已 `ps` 复核）。

## 6. 🔴 诚实边界 —— SIGKILL 残余（MUST NOT 声称根治）

**helper 进程自身被 SIGKILL(-9) 时 trap 根本不会执行**，runner 子进程**仍会存活并 reparent 到
PID 1**。这是 shell 层无解的残余，**不是本实现的疏漏，也没有被本票消除**。

本票只保证**两类路径**：可捕获信号（INT/TERM/HUP）+ 正常退出。要覆盖 SIGKILL，须由调用方
在更外层（进程组 / cgroup / 容器）回收——**本票不做，也未声称做到**。

登记位置（三处，均实跑或机械守）：
1. 文件头 `exec` 契约块的「🔪 子进程生命周期」段（含 `MUST NOT 声称根治` 标注）；
2. `ov_cleanup` 上方的实现注释；
3. `test_sigkill_residue_is_documented_not_claimed_solved` **机械守**登记不被后续改动抹掉，
   并禁止「已根治 / 已消除孤儿 / 彻底解决 / 完全避免孤儿」等越界措辞。

## 7. 契约影响：`OV_TRUNCATED` 不再声称是 stderr「末行」

ticket 提示要求「`OV_TRUNCATED` 必须仍是 stderr 末行」。**核查后更正这个前提**：

- 两层 SKILL.md 的原文是「**truncated 取 helper stderr 的 `OV_TRUNCATED`**」——是**子串命中**，
  没有「末行」约束；
- 且**既有代码本就不满足末行**：失败分支（124 / 非零 / 空输出）的 runner stderr 转发本来就排在
  `OV_TRUNCATED` 之后。「末行」在改动前已不成立。

本票新增的清理痕迹只在**信号回收路径**出现，不含 `OV_TRUNCATED` 子串 ⇒ **对既有解析零影响**。
已把这一点写进文件头契约块（「调用方按子串命中取 `OV_TRUNCATED`，不假定它是 stderr 末行」），
消除这个流传中的错误前提。

## 8. 验证记录

```
/usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_child_lifecycle.py -q
  → 9 passed；跑完 ps 复核零残留进程

/usr/bin/python3 -m pytest -q
  → 1721 passed, 2 skipped in 90.77s；跑完 ps 复核零残留进程

/usr/bin/python3 -m pytest hack/tests/test_async_branch_parity.py -q
  → 26 passed（Non-Goal 守卫：两层 SKILL marker 段未被触碰）
```

按实现期纪律：**未提交**，改动留工作树；无 `task<N>-` 标签；临时变异副本已清理
（`git status` 仅 1 改 1 增 1 改，无未跟踪 debris）。
