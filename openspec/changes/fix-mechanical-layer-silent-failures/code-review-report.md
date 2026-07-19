---
ship-gate:
  code_review: pass
---

# code-review 报告 — fix-mechanical-layer-silent-failures

**结论（人读）**：建议进 `/sdflow-done`。六条必修已落地 + 变异验证；两条 defer 进 buglist（B13/B14），hand-off 须点名 B13 的凭证泄漏面。

## 命中范围

- **栈**：POSIX shell / bash 3.2 + pytest。**⚠️ F13 降级**：`code-checklists/domains/` 下只有 `backend.md` / `backend-go.md` / `embedded*.md`，**无 shell/bash 清单** ⇒ 领域清单未覆盖，本轮以 `code-review-base.md` CR-01~09 为主清单 + `backend.md` 通用条目 + 仓内 `CLAUDE.md` 五条基准 + `adr/0018`。**MUST NOT 读作「按领域清单通过」。**
- **diff base**：`f4d0e6d4`（`merge-base origin/main HEAD`）。
- **trivial_shape**：`NOT_EXEMPT`（`logic-line:.github/workflows/mechanical-gates.yml`）⇒ 照常 fan-out。
- **HR-TG**：命中 4 条 ⇒ 按高风险开 3 个对抗镜 + 单开 `hr-tg` 领域专属跨模型。

<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-17,TG-26" declared="TG-08,TG-09,TG-17,TG-18,TG-19,TG-22,TG-26" evidence="trap 与 OV_RUNNER_PID 跨信号上下文共享可变状态（TG-26）；secret_scan 边界与 stderr 绕过出境扫描（TG-17）；runner 多状态生命周期（TG-09）；新增依赖 ps -o pgid= 与 GNU timeout setpgid 行为（TG-08）" -->

## Step1 — scope-drift + 完成度（⚠️ 降级执行）

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

🔴 **诚实登记**：**未原生执行 gstack `/review`**。本段由主 session 直接做 scope-drift 与完成度审计，
**不冒充 native**。降级理由：本轮编排在 ship 链序内 inline 运行，未调用 gstack skill；
该层的 findings 因此可能少于原生执行（`broad` 镜 lens-metric 锚 findings=0 反映的是这个事实，不是「审过且干净」）。

**scope-drift 审计结论：无夹带。** 非 openspec 改动面 = `outside-voice.sh` + 其 4 个测试文件 + `mechanical-gates.yml`，与声明范围吻合，无不相关功能。两处超出 ticket 字面但有据：

| 超出项 | 依据 |
|---|---|
| 多字节机械门扫**全仓 7 个 `.sh`**（非仅 `assets/hack/`） | 基准③ 面治——该坑与文件在哪个目录无关，只与「有没有 `$var` 紧贴非 ASCII」有关 |
| CI 加 `-rs` + **macOS 矩阵泳道** | 直接服务本 change 的假设 A1（跨平台一致）；`-rs` 见下 F11，macOS 泳道见 F11 |

`openspec/CONTEXT.md` / `adr/0018` 的改动全部标 `[grill-amendment]`，属设计期产物，非实现期夹带。

**完成度**：R1 **达成且生产路径实证**；R2 **部分达成**（见下）。

## 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

`host=claude` ⇒ 免探针，恒 available。第三镜为**历史镜**，`mirrors=` 按跨层固定三 token 词表借用 `grounding` 记该镜跑过（镜的精确身份由 lens-metric 的 `lens="history"` 承载，二者不互相替代）。

## outside-voice（跨模型第二意见）

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->

两站点均 rc=0 ⇒ 合法组合矩阵判**跨模型**（`host=claude, runner=codex, reason_code="ok"`）⇒ 其 findings 跳过 <80 数值滤、直通对抗裁决。

**首次 dispatch 失败并重派（如实登记）**：首轮 run-id `20260719T023731Z-zYF0SL` 的 `code-voice` 得 rc=1，
原因是 helper 读不到 `$SDFLOW_VOICE_RUNNER` ⇒ 判 `host=unknown` 拒跑。**根因是 harness 每次 Bash 调用是独立 shell**，
第零步 `eval` 出的环境变量在 dispatch 那次调用里并不存在。两层评审 SKILL 的 async 段对 `$HELPER` 与 run-id
都写了「MUST 代入字面值、MUST NOT 用 shell 变量」，**唯独漏了 `$SDFLOW_VOICE_RUNNER` 这组**。
按 per-run 不可变纪律换新 run-id `20260719T023848Z-Yj4tIl`、把 `eval` 内联进同一次调用后成功。
⇒ 已记 todolist（SKILL 契约缺口，非本 change 代码缺陷）。

**`truncated="true"` 的额外意义**：`code-voice` 的 context 为 **305,959 字节 > 200KB 上限**，
截断真实触发（`OV_TRUNCATED_DROPPED_BYTES=101159`），而 codex **rc=0 收下了**。
**同一场景在本 change 之前是 rc=1 `input is not valid UTF-8 (invalid byte at offset 107475)`**
⇒ **Success Metric 1 在生产路径上当场兑现了一次**（非合成语料、非实验室条件）。

## Findings（置信 ≥80；跨模型 voice 项豁免数值滤）

| # | 严重度 | 问题 | 证据 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| F1 | 致 | **磁盘写满时 `exec` 静默失败、零诊断**：`render_prompt` 子壳内 `head`/`printf`/`tail`/`echo` 全部写失败，最终 **exit 1 且 stdout/stderr 均 0 字节**（2MB ramdisk 实测，两次独立复现）。兜底的 `cat render.meta >&2` 在写入本身失败时形同虚设 | `outside-voice.sh` `render_prompt`/`do_exec` | 对抗B + code-voice | **已修 M3**〔impl-review-fix〕 |
| F2 | 高 | **回扫不可用未 fail-loud**：`case "$htrim" in ''\|*[!0-9]*)` 命中后打哨兵即**继续按字节切、exit 0** ⇒ prompt 带非法 UTF-8 出门、B9 原病复发。**与 `design.md` 失败模式表 F2「fail-loud，退出码非零」直接冲突** | `design.md:84` vs `render_prompt` | code-voice | **已修 M1**〔impl-review-fix〕 |
| F3 | 高 | **`od` 部分输出被当完整结果**：`_ov_bytes_at` 是 `od\|tr\|grep`，管道退出码只反映末端 `grep`；process substitution 又丢 producer 返回码；守卫只检查「**完全为空**」⇒ 吐一半再失败 ⇒ 数组非空 ⇒ 判成功 | `_ov_bytes_at` / `utf8_head_trim` / `utf8_tail_skip` | code-voice | **已修 M2**〔impl-review-fix〕 |
| F4 | 高 | **`ov_cleanup` 可被不同信号重入**：三个 trap 全程激活、清理内含 ~1s 等待循环、`OV_RUNNER_PID` 到最后才清空 ⇒ 第二种信号嵌套进入，对同一或已复用 PID 再发组级 KILL | `ov_cleanup` | hr-tg voice | **已修 M5**〔impl-review-fix〕 |
| F5 | 中 | **kill 失败却宣称成功**：组级与单 PID `kill -KILL` 均吞错误、忽略返回码，随后**无条件**打印「已 SIGKILL 兜底」并清空 PID ⇒ 制造假成功证据（违反 adr/0018） | `ov_cleanup` | code-voice + hr-tg voice（**两镜独立**） | **已修 M4**〔impl-review-fix〕 |
| F6 | 低 | **trap 安装窗口**：`OV_WORKDIR` 赋值后、四条 `trap` 逐条装完前收信号 ⇒ 走 shell 默认处置，**连 EXIT trap 都不触发**，workdir 泄漏 | `do_exec` | 对抗B | **已修 M6**（合并为一次 trap 调用）〔impl-review-fix〕 |
| F7 | 致 | 🔴 **高频×多类型混合信号风暴可整体击穿 trap 机制**：3s 内 20–150ms 随机间隔交替发 TERM/INT/HUP，**15 跑 10 中（67%）** helper 被信号默认处置直接终止、stderr 无任何 `ov_cleanup` 痕迹、runner 与孙进程双双成孤儿。对照组：单一信号同频洪泛 **0/10**；慢速多类型 trap 重入但幂等扛住 ⇒ **引爆点是「高频 × 多类型」的交集** | 对抗A（实测） | 对抗A | **登记不修**（见下 T10 台账）→ `design.md` D2.2 `(d*)` + **B14** |
| F8 | 致 | **失败通道绕过出境 `secret_scan`**：rc≠0 分支 `head -3 last-message.md`、空消息分支 `tail -5 cli.log` + `tail -5 stderr.log` 全部未扫描直出（`secret_scan` 仅在 rc=0 成功路径跑）。**现有测试甚至锁定了原始 stderr 转发行为** | `do_exec`；`test_outside_voice.py:249`/`:623` | hr-tg voice + 对抗B（**两镜独立判 critical**） | **defer → B13**（既有缺口 + proposal Non-Goal「不改出境侧扫描」） |
| F9 | 高 | **`secret_scan` 自身 fail-open**：`grep` 在无 `pipefail` 的管道首端且吞错误 ⇒ `grep` 不可用 / IO 失败 / 权限竞态均表现为空结果 ⇒ 函数返回成功、context 继续出境 | `secret_scan` | hr-tg voice | **defer → B13** |
| F10 | 高 | **扫描对象与发送对象非同一快照（换文件 TOCTOU）**：context 在 `secret_scan` 后又被 `wc`/`head`/`tail`/`cat` 重新打开；`do_exec` 预扫同样不封闭该窗口 | `render_prompt` | hr-tg voice | **defer → B13**；另**已在 design 补边界**（原声明「先扫整个文件 ⇒ 不缩小覆盖面」需加此限定） |
| F11 | 中 | **CI 只有 ubuntu 泳道 ⇒ 真实 bash 3.2 运行时行为从未被跑过**，仅被静态正则代理覆盖；且 `timeout` 缺失分支在 ubuntu 上恒 skip。静态门的存在会制造「已机械覆盖」的错觉 | `mechanical-gates.yml`；本机 1743/2 vs CI 1740/5 的差值对比 | 对抗C | **已修**：加 `macos-latest` 矩阵泳道〔impl-review-fix〕 |

## 已裁掉（反静默压制，可审计）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | **领域镜判 CR-01「无 Critical/Important」并给通过**，理由是「取字节失败时输出空串而非误导性 `0`，符合 adr/0018」 | **与 code-voice F2/F3 正面冲突，采信 voice。** 领域镜验证了**修复存在**，但未回答两件事：① `design.md:84` F2 明写要求**非零退出**，而实现是「哨兵 + 继续送非法字节」；② 空串守卫只挡「完全为空」，挡不住 `od` 吐一半。编排层独立读码复核，确认 voice 成立。**记为 TENSION：这是框架内视角的盲区**——镜子问「代码有没有做它说要做的事」，voice 问「这事做到目标态没有」 |

## 修复 / defer 台账

- **自动修 7 项**〔impl-review-fix〕：M1–M6 + macOS CI 泳道。全部含**承重测试锁 + 变异验证**（回退修复 ⇒ 断言转红，实际输出见 `code-review-fix1.md`）。
- **defer 3 项**：F8/F9/F10 → **B13**（P1，出境安全三洞）；F7 → **B14**（P1，信号风暴）；`--timeout 0` 未被拒（GNU timeout 语义下 `0` = **禁用**超时，不在本 diff 范围）→ todolist。
- **T10 复核（无客观判据的 ≥2 方案，各附三镜 + 主次）**：

  `T10复核: F2/F3 改为 fail-loud 非零（而非维持降级+哨兵） | 对抗镜结论 通过 | 系统镜：design.md:84 F2 已白纸黑字写死「非零」，属客观判据（实为 T10 第①级，无需对抗复核，此处补记）；用户镜：拿不准字节就不发 > 发出去被拒收，后者浪费一整轮跨模型评审；开发循环镜：fail-closed 使故障在第一现场暴露，不再顺流到 runner 侧表现为「codex 拒收」这种误导性症状。主次：以系统镜为主——文档化契约优先于实现现状。`

  `T10复核: F7 登记不修（而非就地换回收机制） | 对抗镜结论 通过 | 系统镜：修法（外层去抖 / flock 单实例互斥取代 bash trap）是换掉整个回收原语，属设计级决策，超出代码审权限，且 ship 红线为不跨设计门；用户镜：67% 复现率不允许被描述为「极少见」，故必须显著登记而非静默放过；开发循环镜：登记 + 回归用例 + buglist 三重留痕，使后续 change 接得住，且防「少见可不修」的误判。主次：以系统镜为主——权限边界是硬约束，不是偏好。`

## R2 完成度的诚实结论

**Success Metric 2「孤儿 runner 进程数 = 0」**：

| 路径 | 实测 |
|---|---|
| 单信号（TERM / INT / HUP 各自）被回收 | ✅ **达成**，`ps` 验尸为空 |
| runner 主动 `trap '' TERM` 忽略终止信号 | ✅ **达成**（D2.1 组级 KILL 升级，本轮前为不达成） |
| **高频 × 多类型混合信号风暴** | ❌ **不达成**，实测 67% 产生孤儿 |

**MUST NOT** 把前两行的达成读作 Metric 2 整体达成。第三行是真实缺口，已登记 D2.2 `(d*)` + B14 + 回归用例。

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="5" 采纳="4" 裁掉="0" defer="1" 独立="3" sev="致2/高0/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="0" 裁掉="1" defer="1" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="2" sev="致1/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="5" 采纳="2" 裁掉="0" defer="3" 独立="1" sev="致0/高1/中1/低0" -->

> 数值一致性（findings/采纳/独立 是否与合并池实收数吻合）**是主 session 信任边界、非机械可验**；emitter 只保证「给定输入的确定性归约」。
> 本报告不做聚合、不做复评判断——跨 change 归档后由 `/sdflow-retro` 按 per-(层,镜) 采纳率 + 独立率双列复评。

**本轮值得下一次复评注意的一条**：`domain` 镜 findings=2 / 采纳=0 / **独立=0**，且其唯一的通过结论被 voice 推翻（X1）；
而两个 `outside-voice` 站点独立 = 2 + 1、`adversarial` 独立 = 3。**冷跨模型层与对抗层在本轮是承重的，框架内领域镜不是。**
单轮样本不足以据此砍镜（判据要求出现轮数 ≥10），仅登记。

## 结论

- ☑ 建议进 `/sdflow-done`
- ☑ defer 残差已入 buglist（**B13** 出境安全三洞 · **B14** 信号风暴击穿 trap）与 todolist（`--timeout 0`、SKILL async 段环境变量契约缺口），hand-off 会引用
- 🔴 **hand-off MUST 点名 B13**：它是真实凭证泄漏面，两个独立镜判 critical，仅因属既有缺口 + proposal 明写 Non-Goal 而未 fold
