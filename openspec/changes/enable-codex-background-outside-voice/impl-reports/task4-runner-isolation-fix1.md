# Task 4 · fix1 —— 双轴审轮 1 Standards 轴 FAIL 的修复报告

**票**：`task4-runner-isolation`（`enable-codex-background-outside-voice`）
**轮次**：fix1（Spec 轴 PASS / Standards 轴 FAIL：3 Important + 3 Minor）
**基线 commit**：`908b818`
**性质**：**5 条纯陈述订正 + 1 条行为改动（M3）**。行为改动只有一处：`EFFORT_VALUES` 收窄为
`("high",)`，其余全部是注释 / docstring / 报告文字。

> 本轮三条 Important 是**同一个形态**：写下的「契约陈述」被自家代码证伪。
> ∴ 除逐条修复外，另做了一遍**全票契约断言自查**（第三节），又自捕到 5 处同族陈述错误，一并订正。

---

## 一、逐条发现 → 修法 → 锚

### I1（Important）「pid 缺席 ⇒ 退回 `unverifiable`」被消费侧代码证伪

**事实核对**（自己打开代码看的，不是转述）：`probe_subtree` 的 `runner_kind == "absent"`
分支**不返回** unverifiable，而是直落判据 ⑤ —— `outside-voice-job.py:1600-1611`：

```python
    terminal_kind, _, _ = load_witness(run_dir, site, ".terminal.json", job, "terminal_at")
    if terminal_kind == "ok":
        return (SUBTREE_EXITED, "worker pid=%s 已发布 terminal witness 后退出 ⇒ …")
```

而 ⑤ 自己的残余登记里写着「helper 若是被 SIGKILL 打死的，`subprocess.call` 同样返回、
witness 同样发布，而孤儿 runner 仍活着」——**正是 pid 缺席窗口里发生的那件事**。
∴ 真实降级方向是**假 `exited`**（`cleanup --cancel` 解闸同族 fallback、孤儿仍在计费），
不是 fail-closed 的 unverifiable。

**修法（裁定照办：改陈述，不改行为）**——四处陈述全部订正为「缺席 ⇒ 退回 ⑤ 的盘面推断；
helper 正常退出时结论正确，SIGKILL-in-window 时会误判 exited —— 这正是 ④ 要关而缺席时关不满的窄口」：

| # | 位置 | 订正 |
|---|---|---|
| 1 | `outside-voice.sh:30-38`（头部契约 `$SDFLOW_VOICE_RUNNER_PID_FILE` 段） | 删掉「消费方读不到即退回 fail-closed 的 unverifiable，属诚实降级」，改为 ⑤ 的真实路径 + **误判 exited** 明写 |
| 2 | `outside-voice.sh:474-480`（`ov_publish_runner_pid` 时序诚实边界） | 同上；并删掉「方向安全」这句（它正是被证伪的那半句） |
| 3 | `outside-voice-job.py:38-42`（`worker` 子命令契约） | 同上 |
| 4 | `sdflow-init/tests/test_outside_voice.py:715-721`（`test_exec_still_delivers_findings_when_the_pid_sidecar_cannot_be_written` docstring） | 改写为「**因为它不是 fail-closed 降级**，所以这条哨兵是操作者唯一能看见窄口被打开的信号」 |
| 5 | `impl-reports/task4-runner-isolation.md:43`（三条边界表首行） | 原文保留 + `〔fix1 订正〕` 标注，明写「被自家消费侧代码证伪」 |

**行为零改动**（裁定要求）：`git diff` 亲验，这五处全是注释 / docstring / 报告文字。
pid 文件在场时 ④ 压过 ⑤ 的既有行为原样保留。

**锚**：无新锚（纯陈述）。既有 `test_the_published_runner_pid_unblocks_the_subtree_verdict`
仍是 ④ 生效的后果锚；⑤ 的误判窄口**按裁定不修**，故只登记不上锚。

### I2（Important）`outside-voice.sh` 头部注释主语颠倒

`$SDFLOW_VOICE_RUNNER`（`:6`）定义为「当前宿主**之外**的另一个机队」⇒ 走 claude 分支
⟺ 宿主是 **Codex**。原文「Claude 宿主的同步路径走这条缺省」主语反了。

**修**：`outside-voice.sh:16-25` 重写该段，显式点出「⚠ 主语别搞反：走到 claude 分支 ⟺ 宿主是
**Codex**；Codex 宿主的同步路径直调本脚本 exec、没有下发方，走的就是这条缺省」。
交叉核实（`sdflow-code-review/SKILL.md:398` 执行模式矩阵）：`| sync | host=codex |` —— Codex 宿主
确实走同步直调 exec，订正后的陈述成立。

**行为零改动**：按编排层裁定，**三旗覆盖所有 claude 反向调用是照 OVBG-04 原文，不是加宽** ⇒
未加任何分档、未动 argv。

### I3（Important）effort 断言对 codex runner 不成立

`RUNNER_VALUES` 含 `codex`，而 `outside-voice.sh` 的 codex 分支**从不读** `SDFLOW_VOICE_EFFORT`
⇒ `--runner codex` 时 job.json 的 `effort` 仍是装饰。原注释无条件称「真实下发并生效」。

**修**：`outside-voice-job.py:912-917` 把断言**带上主语**——`runner=claude` 时才是生效值；
`runner=codex` 时明写「仍是装饰值，MUST NOT 拿它当『codex 实际生效档位』的证据」。
同族一处（自查发现）：`outside-voice.sh:149-152` 的 `--effort <档位>` 说明也做了同样限定。

### M1（Minor）`probe_subtree` 判据 ④ 的时序描述漏改

`outside-voice-job.py:1550` 仍写「helper 在 spawn runner **前**落盘」，与已订正的 `:36`/`:1496`
打架（首轮报告自述「两处」，实为三处）。

**修**：订正为「spawn runner **后**立即落盘，早于 `wait`；pid 在 `&` 之前不存在，"spawn 前落盘"
在 shell 层不可能」。首轮报告第 4 节标题的「两处」也加了 `〔fix1 订正〕` 注记。

### M2（Minor）契约锚正则看不见裸 `$SDFLOW_VOICE_*`

`test_env_contract_block_registers_every_consumed_variable` 原正则 `\$\{(SDFLOW_VOICE_[A-Z_]+)[:\-}]`
只认花括号形态；脚本里 `"$SDFLOW_VOICE_MODEL"`（`:737`）/ `"$SDFLOW_VOICE_RUNNER"`（`:800`）是**裸**形态。
当前四个变量各自都另有花括号用法故无实漏，但「只以裸形态出现的新变量」会静默逃逸本锚。

**修**：正则改为 `\$\{?(SDFLOW_VOICE_[A-Z_]+)`，docstring 写明口径 MUST 覆盖两种形态。
（预防性改动，当前无红可转绿 —— 如实说明，不假称"修复了一个漏检"。）

### M3（Minor · **唯一的行为改动**）dispatch 侧把 effort 钉死 `high`

spec（OVBG-04）写死 `--effort high`，而实现允许 `dispatch --effort low|medium` 一路下发。
裁定：**dispatch 侧钉死 high**（它是整条链上 effort 的唯一 producer：`build_worker_command`
→ worker → `SDFLOW_VOICE_EFFORT` → `outside-voice.sh` 全程原样透传，没有第二个注入点），
helper 侧 `${SDFLOW_VOICE_EFFORT:-high}` 的透传能力**保留不删**（宿主直调 exec 路径用）。

**修**：`EFFORT_VALUES = ("low","medium","high")` → `("high",)`（一行 + 理由注释），
拒绝文案改为「effort 非法（后台通道按 OVBG-04 钉死 high，MUST NOT 降档）」。
**选了 fail-loud 拒绝而非静默改写成 high**：静默改写会让「调用方以为发了 medium、实际跑了 high」
两边都察觉不到；拒绝则当场暴露调用方 bug。校验点仍是原来那一处 `if args.effort not in EFFORT_VALUES`，
**没有新增分支**。

**TDD（先红后绿，实跑）**：

```
$ /usr/bin/python3 -m pytest sdflow-init/tests/test_outside_voice_job.py -q -k effort   # 实现前
FAILED …::test_dispatch_only_ever_dispatches_effort_high[low]
FAILED …::test_dispatch_only_ever_dispatches_effort_high[medium]
2 failed, 4 passed, 304 deselected
```

（`xhigh` / `""` 两格改前就绿——原枚举已挡掉；真正的缺口正是 `low`/`medium` 这两格，
∴ 这条锚不是"全拒式"空断言。）

**新锚 2 条**（`test_outside_voice_job.py`）：

| 锚 | 证明什么 |
|---|---|
| `test_dispatch_only_ever_dispatches_effort_high[low\|medium\|xhigh\|""]` | 非 high 一律 exit 1 + `state="usage-error"`，且 `_bg_invocations == []`、`.reserve` 不存在 ⇒ **在任何外部派发之前**被拒 |
| `test_dispatch_accepts_effort_high_and_hands_it_down_verbatim` | 正向对照：high 真被 `shlex` 解出的 worker 命令原样携带（证明拒绝不是靠"全拒"实现的） |

**连带订正**（同一片，避免留下互相打架的陈述）：`outside-voice.sh:22-25` 与
`test_outside_voice.py:624` 的「job helper 只放行 3 档」→「只放行 high 一档」；
`test_exec_claude_effort_comes_from_the_dispatched_env` 的 docstring 补一句「本锚锁的是**透传能力**，
MUST NOT 被读成 dispatch 可以下发 medium」——那条金标里的 `medium` 保留（裁定：helper 透传能力不删）。

**版本号未动**（`outside-voice-job.py 0.1.0`）：本文件由本 change 的 Task 1 新增、尚未下发到任何
消费仓，无 skew 面；且无测试锚该字面值。如判需 bump，请下轮明示。

---

## 二、全量测试

```
$ cd /Users/cheneyzhao/Documents/04-sdflow-skills && /usr/bin/python3 -m pytest sdflow-init/tests/ -q
621 passed, 4 skipped in 163.49s
```

```
$ /usr/bin/python3 -m pytest -q
2469 passed, 10 skipped, 3 xfailed in 254.16s (0:04:14)
```

基线（`908b818`）= 2464 passed, 10 skipped, 3 xfailed；本轮新增 2 条 dispatch 锚（其中一条
4 格参数化）⇒ 预期 +5，**实测 +5，无回归、无 skip/xfail 变化**。
（本机 pytest 只在系统 python 里：命令 MUST 写 `/usr/bin/python3 -m pytest`。）

---

## 三、契约断言自查（本票每一句「保证 / 不会发生」× 代码是否兑现）

逐条打开代码核对（`git show 908b818` 全 diff 逐行过），本票落下的断言清单：

| # | 断言（本票写下的） | 代码兑现？ | 处置 |
|---|---|---|---|
| 1 | pid 缺席 ⇒ 消费侧退回 fail-closed 的 `unverifiable` | ❌ **证伪**（落 ⑤，terminal witness 在场即 `exited`） | I1，四处订正 |
| 2 | 该降级「方向安全」 | ❌ **证伪**（假 exited = 解闸 fallback，方向不安全） | I1，删该措辞 |
| 3 | claude 分支缺省档位服务的是「Claude 宿主同步路径」 | ❌ **主语反**（claude 分支 ⟺ Codex 宿主） | I2 |
| 4 | job.json 的 effort 是「真实下发并生效」值 | ❌ **对 `runner=codex` 不成立** | I3 |
| 5 | pid sidecar「spawn 前落盘」（`probe_subtree` ④） | ❌ **shell 层不可能**，且与同文件另两处打架 | M1 |
| 6 | 「订正了**两处** docstring」（首轮报告） | ❌ 实为三处，漏 `probe_subtree` ④ | M1，报告加注 |
| 7 | 后台通道 effort 合法值 = 3 档 | ❌ 与 spec「写死 high」不符 | M3 |
| 8 | **自捕 a**：`cmd_worker` 注释「缺这个信号时组长分支只能 fail-closed 判 unverifiable」 | ❌ 同 I1 形态（缺信号是落 ⑤，不是卡在组长分支） | 已订正（`:919-923`） |
| 9 | **自捕 b**：`read_runner_pid` docstring「文件缺席 ⇒ MUST NOT 当成 runner 已退出」 | ⚠️ 半真 —— 函数自身返回 `"absent"` 无误，但读起来像在承诺判定结果，而 ⑤ 确会判 exited | 已改写为「`"absent"` 本身不构成任何一侧的证据，调用方由此退回 ⑤」（`:1496-1499`） |
| 10 | **自捕 c**：`test_exec_claude_effort_defaults_to_high_without_the_env` docstring「Claude 宿主的同步路径」 | ❌ 同 I2 主语反 | 已订正 |
| 11 | **自捕 d**：`test_exec_writes_no_runner_pid_sidecar_when_the_env_is_absent` docstring「Claude 宿主的同步路径」（用例 env 恰是 `runner=claude`，自相矛盾） | ❌ 同 I2 主语反 | 已订正 |
| 12 | **自捕 e**：`test_helper_writes_no_runner_pid_when_the_worker_did_not_ask_for_one` docstring「同步（Claude 宿主）路径」 | ❌ 同 I2 主语反 | 已订正 |
| 13 | **自捕 f**：`test_the_published_runner_pid_unblocks_the_subtree_verdict` docstring「没有它：verdict 恒 `unverifiable`」 | ⚠️ 只在**本用例刻意删掉 terminal witness** 的形态下成立，孤立读会读成全称命题 | 已加限定 + 点明「有 witness 时是漏放不是卡死」 |
| 14 | `--safe-mode` 关掉 ambient 定制但**不**关四旗/读围栏 | ✅ 真机探针 + 对照组（首轮第三节实测输出） | 保留 |
| 15 | 两条 runner 路径都落 pid sidecar | ✅ `test_exec_publishes_the_runner_pid_sidecar` + `…_on_the_codex_path_too` | 保留 |
| 16 | sidecar 格式 = 纯十进制、权限 0600 | ✅ 两侧各有断言（helper 侧 `stat` + 消费侧 `read_runner_pid` strict `\A\d+\Z`） | 保留 |
| 17 | 「无 terminal witness 的站点恒判 unverifiable」（`ov_publish_runner_pid` 段 + 一条测试 docstring） | ✅ 该句**自带限定**，与 ⑤ 一致 | 保留 |
| 18 | worker 的 stdout/stderr 不入 supervisor transcript | ✅ 真机 canary + 反向变异（首轮第三节） | 保留 |

**结论**：本票原有 18 条断言里，**7 条不成立、2 条表述过宽**（其中 6 条是本轮自查新捕的，
双轴审只点了 3 条 Important + 1 条 Minor）。全部已订正；无一条靠改行为去迁就陈述。

**同源根因**（如实记，不粉饰）：这 9 条集中在两簇——
① **降级方向**（把「我希望它 fail-closed」写成了「它 fail-closed」，共 4 条）；
② **主语**（`runner` 名与 `host` 名反着用，共 4 条）。两簇都属「落笔前没回去打开被引用的那段代码」。
② 尤其便宜可防：`$SDFLOW_VOICE_RUNNER` 的定义就在同一文件第 6 行。

---

## 四、未修项（裁定不修，MUST NOT 顺手做）

| 项 | 理由（照裁定原样执行） |
|---|---|
| ⑤ 的 SIGKILL-in-window 误判 exited 本身 | 裁定「改陈述，不改行为」——pid 文件在场时 ④ 压过 ⑤，缺席只发生在宿主直调路径或 helper 版本 skew，属已登记的诚实降级 |
| `--safe-mode` 对 plugins/skills 未独立探针 | Spec 轴独立裁定为合理简化（`claude --help` 原文把 skills/plugins 与 hooks/memory 归同一 flag，且已实证覆盖两个最高影响类 + 对照组） |
| 哨兵三档只有 `write` 有锚、`${dest}.tmp.$$` 残片 | 影响≈0（gitignored run-dir、无 glob 消费者），已 defer |
| canary 依赖本机 claude≥2.1.169、CI skip | research-preview 下不可避免，已 defer |
| `EFFORT_VALUES` 3 档 vs CLI 5 档的"漂" | 已被 M3 取代：现在是 1 档 vs 5 档，且方向 fail-closed |
| `<site>.runner.pid` 写后不删 | 方向安全（stale ⇒ 判 alive） |
| `openspec/specs/` 主 spec 的「四旗」措辞 | 归 archive 阶段的 delta 同步，实现期 MUST NOT 改 |

**流程纪律**：未勾任何复选框、未打 `task4-` 完成标签、未改 `proposal.md` / `design.md` /
`specs/` / `tasks.md` / `openspec/specs/`（`git status` 亲验：改动仅 4 个源/测试文件 +
本票两份 impl-report）。
