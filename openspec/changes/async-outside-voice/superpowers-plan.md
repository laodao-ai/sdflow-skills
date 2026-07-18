---
impl-pipeline: tickets
---

## Global Constraints

以下条款**逐字**摘自本 change `design.md`，是每个 implementer / reviewer 子代理的共享注意力透镜。

**Non-Goals（设计硬边界）**

- 不改 `outside-voice.sh`（脚本本体 / 四旗承重墙 / 出境安全三件套）。
- 不解 Codex 宿主方向的 efficacy=0（架构性无解，另立项）。
- 不改锚行契约 / `anchor_lint` 合法组合矩阵。

**ADR-3 — 天花板 / barrier / 退出码**

- **天花板（F-B 执行模式矩阵）**：`--timeout` 是 caller flag（脚本不改）。**仅 `$SDFLOW_HOST=claude` 的 async 分支**用 config 默认 **900s**。**Codex 同步分支 + claude 自探失败降级同步分支**保留 **300s 内层 / 外层 ≥330s**。始终机械满足 **外层 ≥ 内层+30s**。
- **collect 是通知驱动（F-A，非「轮询」）**：dispatch 记 `站点↔task_id`；完成通知**异步到达**（可能早于 Step3）→ 主 session 接住即暂存该站点结果；Step3 是 **barrier**：每个「实际 dispatch 过的站点」结果 MUST 已在手（已 collect）或已按退出码降级，**MUST NOT** 单次长 sleep 等待、MUST NOT 自造轮询循环。
- **正向 barrier 语义〔seam-review-amendment G3〕**：Step3 时某 dispatch 站点若**尚无终态退出码**（仍 RUNNING），MUST **让出轮次、等该后台任务的完成/超时通知**——这既非长 sleep 也非轮询循环（通知由 harness 推送）。**`reason_code="timeout"` 只允许由实际观测到的 `exit 124` 产生**：MUST NOT 在未收到该站点终态通知前落 `timeout`。
- **退出码结构化传输（F-D）**：按 helper 退出码分支（`0`=ok / `124`=timeout / `1`=exec-error / `3`=secret-hit / **`2`=用法错·context 不可读→并入 exec-error**，reason_code 枚举不新增）。退出码 MUST 由**可信结构化 envelope** 取得，**MUST NOT** 从 voice 正文推断。
- **「取末行」不自保证 ⇒ envelope 三条 MUST 同时成立〔G2〕**：① wrapper **强制前置换行 + 唯一哨兵**：`printf '\n<<<SDFLOW_EXEC_EXIT>>>%s\n' "$rc"`——用 `printf '\n…'` 而非 `echo`；② parse **整行锚定**：`^<<<SDFLOW_EXEC_EXIT>>>([0-9]+)$`；③ **多重匹配即篡改**：扫到 **0 行或 ≥2 行 → `exec-error`**。
- **未知/丢失退出码 / task lookup 失败 → 保守 `exec-error` 降级**，MUST NOT 读作 `ok`。

**ADR-4** — async/sync 分支读 Step0 export 的 `$SDFLOW_HOST`，MUST NOT 各自重判宿主（防信号跨调用点漂移）。

**ADR-5 — 机械等值门**

- 两处 async **host 调度段**（站点无关逻辑）用 `<!-- sdflow:async-branch:start/end -->` marker 圈定，加 `hack/check_async_branch_parity.py` 断言两段**字节相同**、挂进 `setup.sh` + `hack/tests/`。
- collect 通知/退出码逻辑（站点无关）进 marker；站点枚举 / context 构造 / reuse-guard 门控留 marker 外。

**并发与 per-site 完整性**

- **新增面 = 主 session 记账「站点↔task_id」映射**——SKILL 指令 MUST 显式列该映射；**且 dispatch 时把 task_id 追加落盘**（写该站点 context 目录 manifest，F-I）。
- **declared = 该层「恒有锚站点」∪「条件站点（条件成立时）」**：spec-review = `{design-voice}` ∪ `{hr-tg | HR-TG∩≠∅}`；code-review = `{code-voice}` ∪ `{hr-tg | HR-TG∩≠∅}`。**MUST NOT 定义为「应 dispatch 的站点集」**。∴ 公式**唯一动态输入 = HR-TG∩**；**MUST NOT 解析 `guard=`**——该字段语义**站点相关**。⇒ 两层 declared 站点集**不同** ∴ 该计算 MUST 留在等值门 marker **外**。
- **实现约束**：**MUST 复用 `anchor_lint.py` 的 `fence_outside_lines` 口径**，**MUST NOT 另起裸 grep 解析路径**。∴ **优先实现为 `anchor_lint` 附加校验、而非独立脚本**。
- **诚实边界**：该核**读锚的 `site=` 字段**做 per-层站点期望比对，**不修改** host/runner/reason_code 合法组合矩阵。

**孤儿/泄漏与安全**

- ① **context 用 per-run 不可变路径** `.outside-voice/<run-id>/<site>-context.md`〔G5：**父目录 MUST 仍在 `.outside-voice/` 下**——`.gitignore:19` 的 `**/.outside-voice/` 递归覆盖该层级；落到该目录外则 checkpoint 的 `git add -A` 会把全量 diff / 敏感 context 永久入库〕。
- **缓解**：collect **只取结构化状态 + exit0 的 stdout findings**，MUST NOT 把后台文件原始 stderr 当 findings 采信。
- config `--timeout` 值 MUST 校验**正整数 + harness 上界**，0/负/非整/越界/读失败 → 回落默认（fail-safe 恒生效，MUST NOT fail-closed、MUST NOT 用 `--timeout 0`）。

**Compliance** — 不碰 `sdflow:principles` 托管块、不碰 `outside-voice.sh` 契约、不碰 `anchor_lint` 矩阵。DOC-1（正文即最终态）。设计基准：机械化优先 · 目标态导向 · 无界不手搓。

### Task 1: per-run 不可变 context 路径与 dispatch manifest

**Blocked-by:** none
**R-ID:** R1

两个评审流程写 outside-voice context 时，不再落到「固定命名、下轮覆盖」的路径，而是落到与本次运行一一对应、后续轮次不会重写的位置；该位置仍处在 `.outside-voice/` 之下，从而继续被既有 gitignore 条款递归覆盖、不会被 checkpoint 的全量 add 卷入版本库。同一站点的入境扫描与渲染由此恒对同一份快照，跨会话 TOCTOU 窗关闭。同时，每次实际派发都会在该运行目录留下一条可事后查阅的派发记录（站点与后台任务标识），使「是否真派发过某站点」不再依赖会话记忆。

本票是后续 async 编排的地基（dispatch 需要稳定的 per-run context 与落盘证据），故先行。

- [x] 两层评审流程的 context 构造均改为 per-run 不可变路径，且父目录仍在 `.outside-voice/` 下
- [x] 现行「固定命名、下轮覆盖」的构造说明已被完全取代，仓内无残留旧口径
- [x] dispatch 发生时，站点与后台任务标识被追加落盘到该运行目录的 manifest
- [x] 该路径确认被既有 gitignore 递归覆盖（实测：新建该路径下文件后 `git status` 不出现）

### Task 2: spec-review 层 host-adaptive async dispatch/collect

**Blocked-by:** 1
**R-ID:** R1, R2

在 Claude 宿主下，spec-review 的 outside-voice 调用离开关键路径：context 就绪即后台派发，主 session 继续跑 fan-out 镜与其余评审工作；到 Step3 以 barrier 形式收口——每个实际派发过的站点结果要么已在手，要么已按结构化退出码降级。收口靠 harness 的完成通知驱动，不轮询、不长 sleep；站点若仍无终态退出码，让出轮次等通知，绝不提前落 timeout。退出码经不可伪造的哨兵 envelope 取得，而非从 voice 正文推断。Codex 宿主与「后台能力自探失败」两条路径保持同步现状与原有超时口径。超时天花板可按仓覆盖，非法值一律回落默认而非罢工。

- [ ] Claude 宿主路径 voice 后台派发、主 session 无 ≥330s 单次阻塞调用
- [ ] 站点↔后台任务标识映射在指令中显式列出，collect 按站点逐一取
- [ ] Step3 barrier 语义落定：RUNNING 站点让出轮次等通知，timeout 只由实测 exit 124 产生
- [ ] 退出码走哨兵 envelope 三条（强制前置换行 / 整行锚定 / 0 或 ≥2 行判 exec-error）
- [ ] 退出码 0/124/1/2/3 与未知·丢失码各自的降级去向与 reason_code 对应无遗漏，未知码不读作 ok
- [ ] 后台能力自探存在；不可用即降级同步并在报告显式标注，不假装 async 成功
- [ ] async 分支天花板默认 900s、同步与降级分支 300s，外层恒 ≥ 内层+30s
- [ ] 天花板可经仓配置覆盖，正整数与上界校验齐备，非法值回落默认而非 fail-closed

### Task 3: code-review 层同款分支 + 机械等值门

**Blocked-by:** 2
**R-ID:** R1

code-review 层获得与 spec-review 逐字对齐的 host 分支、站点记账与自探降级。两层的 host 调度段（站点无关部分）被 marker 圈定，并由一个新增的机械校验断言两段字节相同——漂移当场红，而非靠人工比对。该校验挂进安装脚本与仓内测试套件，日常跑得到。站点枚举、context 构造、reuse-guard 门控与 declared-sites 计算留在圈外，因为两层这些部分本就应当不同。

- [ ] code-review 层分支与 spec-review 逐字对齐（站点无关部分）
- [ ] 两层 async host 调度段被 marker 成对圈定，圈内仅站点无关逻辑
- [ ] 新增等值校验断言两段字节相同，不同则非零退出
- [ ] 该校验挂进安装脚本与仓内测试套件
- [ ] 首次跑确认绿

### Task 4: declared-sites per-site 完整性机械核

**Blocked-by:** 3
**R-ID:** R2

两层评审报告落一个「本层应有锚的站点集」声明，并由机械核比对它与报告中实落的 outside-voice 锚站点集是否相等，不等即红。这补上既有家族级门的 per-site 盲区——并发两站点漏收一个不再被判 CLEAN。站点集按「应有锚」定义而非「应派发」（复用态未派仍落锚、code-voice 恒在），唯一动态输入是 HR-TG 交集；guard 字段语义站点相关，不作解析依据。实现复用既有围栏剔除口径、不另起裸 grep 路径，否则报告正文里的模版锚会自指假阳，也会形成围栏口径二源。

- [ ] 两层报告均落 declared-sites 集，按「应有锚站点集」定义
- [ ] 机械核比对 declared 与实落锚站点集，不等即非零退出
- [ ] 实现复用既有 fence 剔除口径，无新增裸 grep 解析路径
- [ ] 含模版/示例锚的报告正文不产生自指假阳（含本 change 自身报告）
- [ ] 合法组合矩阵未被修改（矩阵回归绿）

### Task 5: 零改动核验、实证 smoke 与收尾记账

**Blocked-by:** 4
**R-ID:** R1, R2

对承重墙做零改动核验，并用真实跑动而非推理来证明本 change 达成了目标：跑一次真实评审确认 voice 锚是 ok 而非 timeout、主 session 无长阻塞、每站点的派发/终态/落锚三时刻单调（这是 barrier 未早退的唯一实证信号）；构造后台能力不可用与 voice 非零退出两种场景，确认降级诚实、外层超时实参足够、错误路径的原始 stderr 不被当作 findings 采信。最后把两项超出本 change 范围的长期项记入待办池。

- [ ] 核 outside-voice 脚本、合法组合矩阵、出境安全三件套零改动（diff 为空）
- [ ] 锚契约全笛卡尔回归与 change 前逐条一致
- [ ] 真实评审 smoke：voice 锚 reason_code 为 ok，非 timeout
- [ ] smoke 记录每站点派发/终态通知/落锚三时刻并确认单调
- [ ] smoke 记录 fan-out 墙钟与 voice 完成时刻，校准「重叠非叠加」
- [ ] 降级 smoke：后台能力不可用时回落同步、报告标注、外层超时实参 ≥330000ms、voice 正常完成
- [ ] 错误路径 smoke：voice 非零退出时 collect 只取结构化状态，不采信后台文件原始 stderr
- [ ] harness 后台输出文件的 TTL/权限/清理归属已实测记录，未定项显式登记
- [ ] Codex 方向 efficacy=0 与 DRY 全抽取两项记入待办池
