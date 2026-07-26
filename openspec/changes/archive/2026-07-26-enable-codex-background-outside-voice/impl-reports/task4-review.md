# Task 4 双轴审存档 — runner 隔离加固与出境面封堵

**票**：Task 4（R-ID: OVBG-04，兼落 OVBG-05 的子树核验信号）
**轮次**：轮 1（`908b818`）Spec PASS / Standards FAIL → fix1（`e1b8bc4`）→ 轮 2 双 PASS

## 领域清单覆盖声明（Standards 轴，两轮均原样重述）

本 change 的 `proposal.md` 明确声明「不命中 backend、frontend、embedded 技术栈领域清单」，而
`code-checklists/domains/` 下只有 `backend*.md` / `embedded*.md` —— 故**领域清单未覆盖**，
Standards 轴以 `code-review-base.md` + 仓内 `CLAUDE.md` 基准 + Fowler code smell 为标准源。
**这是诚实降级，不是「全覆盖通过」。**

## 本票的主线发现：**契约陈述与代码行为不符**（与 Task 3 Critical 1 同种）

轮 1 的三条 Important 有同一个形态 —— **把「我希望它 fail-closed」写成「它 fail-closed」**：

| # | 陈述 | 代码实际 |
|---|---|---|
| I1 | 「pid 落盘缺席 ⇒ 消费方退回 fail-closed 的 `unverifiable`（**不是**误判 exited）」 | `runner_kind=="absent"` **直落判据 ⑤**，terminal witness 在场即 `SUBTREE_EXITED` ⇒ 真实降级方向是**假 exited**（解闸 fallback、孤儿仍在计费）。而 ⑤ 的残余注释原文就写着「helper 被 SIGKILL ⇒ witness 照发、孤儿 runner 仍活着」——**正是本函数注释点名的那个窗口** |
| I3 | 「job.json 里记的 effort 是**真实下发并生效**的值，不是装饰」 | `RUNNER_VALUES` 含 `codex`，而 **codex 分支从不消费 `SDFLOW_VOICE_EFFORT`** ⇒ `--runner codex` 时仍是装饰 |
| I2 | 「缺省 high……**Claude 宿主**的同步路径走这条缺省」 | `SDFLOW_VOICE_RUNNER` = **宿主之外**的机队 ⇒ claude 分支 ⟺ **Codex 宿主**，主语颠倒 |

### 🔴 编排层驳回 Standards 轴的一条判断

Standards 轴在 I2 上附带断言「三旗加在**所有** claude 反向调用上 = 未声明的加宽（OVBG-04 把三旗
界定给 background worker）」。**这条读错了主语，已驳回。** OVBG-04 原文：

> background worker **SHALL** 原样复用 `outside-voice.sh exec` 的四旗（…）、共享 FRAME、入境/出境
> secret scan 与 200KB 截断。**Claude 反向 runner** **SHALL** 使用 `resolve-models.sh` 解析出的
> Claude `strong` 模型（…），**并显式传 `--effort high --safe-mode --no-session-persistence`**；
> 显式 read-fence 与四旗仍须生效。

三旗那句主语是「**Claude 反向 runner**」，不是 background worker ⇒ 覆盖所有 claude 反向调用是
**照 spec 原文**，非加宽。本轮**只修注释、未动行为**。
**评审子代理也会错，报告不能照单全收。**

## fix 轮的额外收获：自查捕到的比双轴审点出的还多

fix prompt 里加了一条要求——「**本票每一句『契约 / 保证 / 不会发生』的断言，代码真的兑现了吗？**」
结果：本票 **18 条契约断言里 7 条不成立、2 条表述过宽**，而双轴审只点了其中 4 条。
两簇根因：① **降级方向美化**（4 条）；② **runner/host 主语反用**（4 条，含两条测试 docstring
与自己的 env 设置自相矛盾）。

Standards 轴轮 2 抽查 4 条订正**均属实**，并特别核实了订正类修复最易走歪的一点：
**无一条靠改行为迁就陈述**。

## 轮 2 复审（双 PASS）

**Standards 轴**（三重反向变异，唯一命名 scratchpad）：
① 还原 `EFFORT_VALUES=("low","medium","high")` ⇒ **仅 `low`/`medium` 红**、`xhigh`/`""` 绿 ——
锚精确命中真实缺口，**非全拒式空断言**；② `EFFORT_VALUES=()` ⇒ 正向对照锚红 —— 拒绝不是靠全拒实现；
③ 改成静默改写 high ⇒ **4 格全红** —— 「fail-loud 而非静默改写」这个选择**本身有锚**。
拒绝点早于 `build_worker_command`/reserve/bg，`_bg_invocations==[]` + 无 `.reserve` 双断言，
且 MUT-C 证明这两条断言真有判别力。
I1 订正后四处措辞与实际行为**逐字吻合**，「方向安全」「诚实降级」两句美化措辞已删净（全仓 grep 无残留）。

**Spec 轴**：6 条验收标准未被改坏（真机 safe-mode 探针 + canary 均**实跑未 skip**）；
`EFFORT_VALUES` 收窄不触真机探针路径（探针走 `_replay_production_argv`，从 shell 侧抓 argv、不经 dispatch）。

### 三条前序票硬交接全部兑现

- **A · runner pid sidecar**：两条 runner 路径均落盘，内容 == 假 timeout 自报的 pid（**不是「是个数字」**），
  0600，`umask 077` 子壳 + `mv -f` 原子，env 缺席零文件。跨文件 e2e 锚 + 「删 terminal witness 逼走 ④」
  的后果锚均真跑通过；scratchpad 副本删掉两处调用 ⇒ 3 条转红。
- **B · `SDFLOW_VOICE_EFFORT`**：真落 `--effort` argv + 头部 env 契约块登记，并加了**机械锚**把
  「代码里读了它」与「契约里写了它」绑死（防再次出现 Task 1 那种「已下发、零消费者、却已写进
  job.json 当事实」的无主变量）。
- **C · canary 口径**：实测 `claude logs` **只回显捕获的 stdout、不回显命令串** ⇒ 对照组是真捕获
  而非命令回声，判别力成立；roster `name` 含绝对路径已显式声明为不判红。

## 编排层裁决

- **`EFFORT_VALUES` 收窄为 `("high",)`**（Spec 轴 Minor → 本轮行为改动）：Spec 轴引 OVBG-04 原文
  「并**显式传 `--effort high`**」+ Scenario 断言 argv「包含 strong model、**high effort**」判为
  **正解**——把 spec 的字面量变成机械门，没新增能力（不加宽），helper 侧透传与直调 exec 缺省
  不受影响（不缩水）。**fail-loud 优于静默改写**：静默改写会造出「job.json 记 medium、实际跑 high」
  的第二份不一致真相，正是 OVBG-02 要杀的形态。
- **`outside-voice-job.py` 版本不 bump**（fix 上抛的待拍板项）。依据（Spec 轴给出、编排层采纳）：
  ① `VERSION` 字符串全仓零消费者、零测试锚（仅 `version` 子命令打印）；② 同代一致性由
  `compute_manifest`/`verify_manifest` 的**内容哈希**保证，与该字符串无关；③ 该文件本 change 新增、
  尚未下发消费仓，无下游据版本号做兼容判断。对照 `outside-voice.sh` **必须**升（已下发 +
  `test_version` 锚死字面值）——两者处境不同，不必对齐。
- **Minor defer**：**T219**（`cmd_worker` 自身不校验 effort，钉死只在 dispatch 一层；当前 dispatch
  是唯一 producer ⇒ 登记备查非缺口）· **T220**（`probe_subtree` 相关 docstring 两处同族漏网，
  **含跨票交接锚、描述误导**）。
- **不修（已裁定）**：`--safe-mode` 对 plugins/skills 未独立探针（Spec 轴查本机 `claude --help` 确认
  plugins/skills 属同一 flag 的上游契约，已覆盖两个最高影响类且带对照组 ⇒ **合理简化，未把标准做窄**）·
  哨兵三档只一档有锚 + tmp 残片（影响≈0）· canary 依赖本机 claude、CI skip 无常驻门（research-preview
  下不可避免）· `EFFORT_VALUES` 3 档 vs CLI 5 档（已随收窄消解）· `<site>.runner.pid` 写后不删
  （方向安全）· `openspec/specs/` 主 spec 仍写「四旗」（归 **archive 阶段的 delta 同步**，
  实现期 MUST NOT 改 —— **done 阶段务必核对**）。

## 🔴 跨票交接（Task 5 / Task 6 MUST 消费）

1. **`probe_subtree` 相关 docstring 有两处已知不准（T220）** —— 后续票 **MUST NOT 据 docstring 推理
   子树判定行为，以代码为准**。
2. **`setup.sh` 的 `capability-manifest.json` 仍未写**（Task 1 起就交接、至今未落）⇒
   **真实安装态 preflight 仍会红**。`write_manifest()` 已作为单一计算源就位，**Task 5 必须落它**。
3. **`openspec/specs/host-adaptive-execution/spec.md` 与 `spec-workflow/spec.md` 仍只写「四旗」** ——
   本 change 的 delta（OVBG-04）已含三面隔离旗，主 spec 由 **archive 阶段的 delta 同步**统一更新。
   **done 阶段核对项。**
4. **Task 3 的 C1 仍然成立**：`unknown_cost=true` 现在覆盖**每一个** LOST 站点 ⇒ **Task 5 的 SKILL
   分支必须显式处理它**（命中即禁自动同族 fallback，改提示跑 `cleanup --cancel`），
   否则费用抑制被旧的「LOST ⇒ fallback」写法绕过。
5. **Task 2 的交接仍在**：helper 对越界 `--timeout` fail-closed，而既有 SKILL 对越界 config 回落 900
   ⇒ **Task 5 MUST 保留 SKILL 侧 clamp**。

## 记录：报告数字与本机不可复现

fix 报告 §二 记「621 passed, 4 skipped」，Standards 轴实跑为 **622 passed, 3 skipped**
（差 1 = 真机 `claude` canary 那格在 fix 运行时被 skip、在评审侧实跑通过）。非缺陷，记录在案。

实跑：`pytest sdflow-init/tests/ -q` → **622 passed, 3 skipped**；全量 **2469 passed / 10 skipped / 3 xfailed**。
