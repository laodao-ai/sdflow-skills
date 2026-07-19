# hand-off — fix-mechanical-layer-silent-failures

> 2026-07-19 · 异步人类再入口 + 下个 change 的种子。随归档留档。
> **本文不搬运 verify 的 ✅**——下方每条「完成」的锚点均经编排层复核存在性后才写入。

---

## ✅ 完成了什么

本 change 修的是 `outside-voice.sh`（跨模型第二意见 helper）两处「**`exit 0`，事情没做成**」，
来源是 `async-outside-voice` 那轮 dogfood 的实测现场。

### R1（P0）— 截断产出保证合法 UTF-8

200KB 截断原本按**字节**切，把 CJK 字符腰斩 ⇒ codex 报 `input is not valid UTF-8 (invalid byte at offset 107475)` ⇒ rc=1 降级同族 fallback，**跨模型第二意见静默丢失**（报告照出、锚行照落）。

| 锚点 | 复核 |
|---|---|
| 纯 bash UTF-8 边界回扫（`utf8_head_trim` / `utf8_tail_skip`，只认 UTF-8、不嗅探） | ✅ 在 `outside-voice.sh` |
| 全切点扫描 `test_every_cut_offset_yields_two_valid_utf8_halves`（**头尾两半各自**严格解码，失败 0） | ✅ 在 `test_outside_voice_utf8.py` |
| 变异验证 `test_mutation_constant_zero_backscan_turns_the_scan_red`（回扫恒返 0 ⇒ 扫描必红） | ✅ 承重已证 |
| 非 UTF-8 语料逐切点 golden（锁「MUST NOT 演化成编码嗅探」，非区间断言） | ✅ `test_non_utf8_lead_bytes_follow_utf8_semantics_not_sniffing` |

**🔴 Success Metric 1 在生产路径上兑现了一次（非合成语料）**：本轮 code-review 的 `code-voice` 站点，
context **305,959 字节 > 200KB**，截断真实触发（`OV_TRUNCATED_DROPPED_BYTES=101159`），**codex rc=0 收下了**。
同一场景在本 change 之前必 rc=1。verify 另独立复现一次（260KB 中文 context，rc=0，`OV_UTF8_BACKSCAN_DROPPED=3`，206053 字节 prompt 严格解码通过）。

### R2（P1）— 父被回收时 runner 子进程必死

原本 trap 只清 workdir、**不杀 runner** ⇒ 孤儿 reparent 到 PID 1 跑满内层超时（实测 `42998 1 timeout -k 10 60 sleep 45`）。

| 锚点 | 复核 |
|---|---|
| 后台起 runner + `OV_RUNNER_PID=$!` + `wait`；trap 覆盖 `INT TERM HUP EXIT` | ✅ |
| SIGTERM/INT/HUP 三参数化验尸 `test_runner_subtree_dies_when_parent_is_signalled` | ✅ |
| 退出码无回归（0 / 124 / 其他非零原样透传） | ✅ |
| **组级 KILL 升级**（`kill -KILL -"$PID"`，穿透 `trap '' TERM` 的 runner 子树） | ✅ `test_runner_ignoring_term_dies_under_group_kill_escalation` |
| 自杀风险守卫（目标须是组长 ∧ 组 ≠ 脚本自身组，否则退回单 PID 并打 `OV_GROUP_KILL_DEGRADED=1`） | ✅ 4 条纯函数用例 + 1 条端到端安全用例 |

### 顺带修掉的（代码审揪出，均属本 change 新代码或其自身 design 承诺）

- **M1/M2** 回扫不可用 ⇒ **fail-loud 非零**（锚 `design.md` 失败模式表 F2），含 `od` **部分输出**判失败
- **M3** prompt 生成链写入失败不再被末尾 `echo` 覆盖成 0（磁盘满曾致 exit 1 且 stdout/stderr **全空**）
- **M4** kill 失败不再宣称成功（`OV_KILL_FAILED=1`）
- **M5** `ov_cleanup` 重入加固（入口屏蔽信号 + 原子快照 PID 先清全局）
- **M6** 四条 trap 合并为一次调用（缩小安装窗口）
- **CI**：加 `-rs`（skip 理由逐条可见）+ **macos-latest 泳道** + macOS 装 coreutils
- **bash 3.2 多字节机械门**扫全仓 7 个 `.sh`（`$var` 紧贴非 ASCII ⇒ `set -u` 罢工，实测撞过）

**跨平台闭环**：CI run **29674903570**，`ubuntu-latest` + `macos-latest` 双 job 均 success
（ubuntu 1749 passed/7 skipped；macOS 1752/4）。**macOS 泳道装了 coreutils 后，11 条进程组/生命周期用例才第一次在真 bash 3.2 上跑起来**。

---

## ⏳ 未完成 / 延后

**批次 `fix-mechanical-layer-silent-failures`**（14 项，见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`）。
下面只点名**必须被下一个人看见**的三条，其余在批次里。

### 🔴 B13（P1，安全）— 出境 `secret_scan` 三洞，**两个独立镜判 critical**

**这是本次 hand-off 最该被看见的一条。** runner 持有**整仓只读权限**，读得到 `.env`/密钥并可能原样引用在回传里；
`secret_scan` 的出境侧就是拦这个的最后一道，而它**只挂在成功路径上**：

- 洞(1) **扫描点挂错位置**：rc=124 / rc≠0 / 空消息三条失败分支的 dump 全部绕过出境扫描，而 runner 非零退出/空输出恰恰常见
- 洞(2) **检测器自身 fail-open**：`grep` 在无 `pipefail` 管道首端且吞 stderr ⇒「扫不动」与「扫过了、干净」外部不可区分
- 洞(3) **对象同一性**：扫描与发送是对同一路径的两次独立 open（TOCTOU）

**为什么没在本 change 修**：三洞均为**既有缺口**（非本次引入），且 `proposal.md` 的 Non-Goal 明写「不改出境侧扫描」，
该假设未被证伪；洞(3) 的正解（私有快照）要重写整条 render/exec 通路，fold 进来会撑爆 scope。
**根因已在 B13 逐洞写清**，含一条给修复者的警告：`:684` 那条既有注释「`stderr.log` 非 context 正文，无新增出境面」
**对 `stderr.log` 站得住，但盖不住 `:676` 的 `last-message.md` 与 `:685` 的 `cli.log`**——别被它挡回去。

### 🔴 B14（P1）— 混合信号风暴击穿 trap 机制，**实测 67%**

3 秒内 20–150ms 随机间隔**交替**发 TERM/INT/HUP（现实对应：Ctrl-C 连按、CI 取消与超时同时到），
**15 跑 10 中** helper 被信号默认处置直接终止、`ov_cleanup` 一行没跑、runner 与孙进程双双成孤儿。
对照组：单一信号同频洪泛 **0/10**；慢速多类型 trap 重入但幂等扛住 ⇒ **引爆点是「高频 × 多类型」的交集**。

**⚠️ 这条直接影响 Success Metric 2 的达成度，MUST NOT 在后续文档里被压缩成「Metric 2 达成」**：

| 路径 | 实测 |
|---|---|
| 单信号（TERM/INT/HUP）被回收 | ✅ 达成 |
| runner 主动 `trap '' TERM` 忽略终止信号 | ✅ 达成（本 change 才修好） |
| **高频 × 多类型混合信号风暴** | ❌ **不达成，67% 产孤儿** |

**为什么没修**：修法（外层去抖 / `flock` 单实例互斥取代 bash trap 作回收原语）是**换掉整个回收机制**，
属**设计级决策**，超出代码审权限、也撞 ship「不跨设计门」红线。已登记 `design.md` D2.2 `(d*)` + 概率性回归用例
`test_mixed_high_frequency_signal_storm_can_defeat_trap_mechanism`（不复现时 skip，skip 文案警告勿删）。

### T178（基础设施）— M3 的锁在 CI 无人看守

`test_exec_disk_full_render_meta_gets_unconditional_stderr_diagnostic` 已标 `skipif(CI)`、**本地专属**。
起因：它要物理填满真 ramdisk、恰好卡在「`mktemp` 建得了目录、prompt 写不进去」的字节窗口，
而该窗口位置取决于文件系统块大小/分配粒度/runner 镜像 —— **环境依赖面**。macOS CI 上连挂三轮、每轮换一种失败姿势
（①失败点位不同 ②ramdisk 太满致 `mktemp` 先挂、变异体与修复版不可区分 ③校准过头致失败下移到 runner 阶段），
触 CLAUDE.md 基准⑤ 警号后拍板停止调参。**本机仍真跑且承重**（压测 100 次 = 91 通过/9 诚实 skip/0 失败，变异验证成立）。
长期正解见 T178（可注入 workdir 接缝 + `chmod 500` 让写入以 EACCES 确定性失败），**但它要加第二个测试接缝，
而第一个（`_OV_TEST_LIB_ONLY`）在本 change 里刚咬过一次**——务必配同等 fail-loud 处理。

### 其余延后项（在批次内，不逐条罗列）

`B12` · `T168`–`T177`。其中值得点一句的：
- **T170**：recorder 三份物理复制 parser 的结构性根因 + B11/B12 —— **MUST NOT 只捡 B11/B12 单独修**，那正是三轮评审证否过的路径
- **T175**：两层评审 SKILL 的 async 段漏写「`$SDFLOW_VOICE_RUNNER` 等环境变量 MUST 内联 eval」——本轮 code-voice 首次 dispatch 因此拒跑（harness 每次 Bash 调用是独立 shell）
- **T177**：`buglist.py add` 的必填校验不含「根因」，最贵的那部分分析反而没有机械门守

### 延后的 ≥2 方案决策（T10 台账，附当时选了什么）

- **F2/F3 改 fail-loud 非零**（而非维持降级 + 哨兵）→ **自动选**，判据客观：`design.md:84` F2 已写死「非零」
- **F7 信号风暴登记不修**（而非就地换回收机制）→ **自动选**，判据：修法属设计级、撞 ship 红线
- **磁盘满用例改本地专属**（而非继续调参 / 撤 macOS 泳道）→ **人拍板（方案 B）**，判据：三轮三姿势触基准⑤ 警号

---

## ▶ 下一阶段建议

**roadmap 回填**：本 change 非 roadmap 驱动（`roadmap_writeback_draft.py` exit=3 `NO_ASSOCIATION`），无需回填。

### 建议开的下一个 change（按优先级）

1. **`harden-outside-voice-egress-scan`（对应 B13，最高优先）** —— 安全项，两个独立镜判 critical。
   建议按三洞**分治**（成因各不相同）：先补失败分支的扫描点（改动最小、收益最大），
   再修 `secret_scan` 自身的 fail-open（与本 change 的 `od` bug 同形，修法可直接借鉴），
   最后做私有快照（改动最大，要动整条 render/exec 通路）。
   **建议一并把 B13 根因里那条「安全门三个失效面 = 位置 / 自身可靠性 / 对象同一性」提炼成评审检查表**，
   它对本仓其他机械门同样适用。

2. **`redesign-runner-reaping`（对应 B14）** —— **这是设计级 change，必须走完整 grill + spec-review + 设计门**，
   不要当 bugfix 顺手做。要拍的是「bash trap 还能不能作为回收原语的唯一挂载点」，
   候选：外层监督者去抖 / `flock` 单实例互斥兜底。两者都有新面要评估（去抖会不会吞掉合法连续信号？互斥会不会引入死锁/饿死？）。

3. **`fix-recorder-parser-triplication`（对应 T170 + B11/B12）** —— 结构性根因，
   **MUST NOT 只捡 B11/B12 单独修**。三轮评审已证否那条路径（拓扑虚构错了两次、退出码地基不成立）。

### 该一起清的 defer 项

- 开 (1) 时顺带清 **T176**（`--timeout 0` 未被拒，GNU timeout 语义下 `0` = 禁用超时）——同文件、同类「调用方纪律没落成机械门」
- 开 (2) 时顺带清 **T173**（SIGKILL 兜底那行无测试锁）、**T178**（M3 锁的确定性注入）——都在同一片进程/信号面上
- **T175** 独立且便宜（改两层 SKILL 的 async 段 + 跑字节等值门），可随手做掉，不必等专门的 change

---

## 给下一个人的一句话

这个 change 最值钱的经验不是那两个 bug，是**「治静默失效的 change，自己被同一种病咬了五次」**：
`_OV_TEST_LIB_ONLY` 泄漏致静默 exit 0 → `2>/dev/null` 位置错没生效 → `htrim` 兜底成 0 →
`od` 失败返回字面 `"0"` 骗过守卫 → 磁盘满致 exit 1 且 stderr 全空。
**每一次都是「返回值形态合法、语义却是失败」**。评审时值得专门拿这条当透镜扫一遍：
**这个函数在它失败的时候，返回的东西和它成功时长得一样吗？**
