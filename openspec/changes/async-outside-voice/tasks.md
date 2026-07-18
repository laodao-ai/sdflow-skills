> Requirement 追溯：**[R1]** = `host-adaptive-execution` / 「outside-voice exec 的 dispatch 模式宿主自适应」；**[R2]** = 「async dispatch 不改变锚契约与诚实降级」。

## 1. spec-review SKILL：host-adaptive async 分支

- [ ] 1.1 `sdflow-spec-review/SKILL.md`「outside-voice helper 调用协议」节（line 263），exec 步加 `$SDFLOW_HOST` 分支：`claude` async = `run_in_background` dispatch（@Step1 design-voice / @Step2 hr-tg 各 context 就绪即派，**内层 --timeout 900s、外层不设 ≥330s**）+ **通知驱动 collect@Step3 barrier**（完成推送异步到达即暂存，非轮询、非单次长 sleep，F-A）；`codex` sync + `claude` 自探失败降级 sync = 同步现状（**内层 300s、外层 ≥330s**）。始终外层 ≥ 内层+30s（F-B 矩阵、ADR-3）。**[R1]**
- [ ] 1.2 dispatch 时 SHALL 显式记「站点↔task_id」映射（**按实际 dispatch 过的站点**——design-voice 前置门控于 reuse-guard、hr-tg 条件于 HR-TG∩≠∅，故后台 voice 数不定 0/1/2；见 design 并发节），collect 时按站点逐一取（防 model-driven 记账漏收）。**[R1]**
- [ ] 1.3 补 `run_in_background` 能力自探：不可用 → 降级回同步 + 报告显式标注，MUST NOT 假装 async 成功。**[R1]**

## 2. code-review SKILL：同款分支（scope-check 逐字对齐）

- [ ] 2.1 `sdflow-code-review/SKILL.md` 的「outside-voice helper 调用协议」节（line 261）加与 §1 逐字对齐的 host 分支 + 站点↔task_id 记账 + 自探降级。**[R1]**
- [ ] 2.2 **机械等值门**（ADR-5，替代人工 scope-check）：① 两 SKILL 的 async host 调度段用 `<!-- sdflow:async-branch:start/end -->` marker 圈定——段内**只写站点无关的 host 调度逻辑**（claude=run_in_background dispatch、codex=同步、自探降级、**通知驱动 collect barrier 按结构化退出码分支**——含 exit2→exec-error、未知/丢失码→exec-error，F-A/F-D；**RUNNING 让出轮次 + `timeout` 只由实测 exit124 产生**（G3）；**哨兵 envelope 三条**（前置换行/整行锚定/0·≥2 行即 exec-error，G2）），**站点枚举/context 构造/reuse-guard 门控/`declared-sites` 计算留 marker 外**〔G1：两层的应有锚站点集不同（design-voice vs code-voice），放进 marker 会令等值门永红〕，∴ 两段可字节相同（领域镜已核当前即字节同、除 site= 行，F-O 可行）；② 写 `hack/check_async_branch_parity.py`（沿用 `sync_principles.py` idiom）断言两段字节相同、坏则非零退出；③ 挂进 `setup.sh` + `hack/tests/`；④ 首次跑确认绿。**[R1]**

## 3. 锚契约与诚实降级守护

- [ ] 3.1 两 SKILL 写 collect 语义（**通知驱动 barrier、非轮询**，F-A）：完成推送异步到达即暂存该站点；Step3 每 dispatch 站点结果 MUST 在手或按**结构化退出码**降级（0=ok / 124=timeout / 1·2·未知/丢失=exec-error / 3=secret-hit）；**站点仍 RUNNING（无终态码）MUST 让出轮次等终态通知，`timeout` 只允许由实测 `exit 124` 产生**〔G3——早退假 timeout 逃过 per-site 站点集核，本条是唯一防线〕；退出码走**哨兵 envelope 三条**〔G2〕：① wrapper `printf '\n<<<SDFLOW_EXEC_EXIT>>>%s\n' "$rc"`（**强制前置换行**——`outside-voice.sh:247` 逐字节透传且不保尾换行，朴素 `echo` 会与正文末行粘连）② parse **整行锚定** `^<<<SDFLOW_EXEC_EXIT>>>([0-9]+)$` ③ **0 行或 ≥2 行 → `exec-error`**（≥2 行 = voice 注入的确定性信号）；**MUST NOT 从 voice 正文推断**（F-D）；MUST NOT 单次长 sleep、MUST NOT 假绿、MUST NOT 落零锚。**[R2]**
- [ ] 3.2 diff 核 `outside-voice.sh` / `anchor_lint` 合法组合矩阵 / 出境安全三件套**零改动**（四旗承重墙、secret_scan、FRAME、200KB 截断逐字不变）。**[R2]**
- [ ] 3.3 天花板可配 + 校验（F-B/F-N/F-F）：**async 分支** exec 传 `--timeout` 默认 **900s**、**sync/降级分支** 默认 **300s**（外层各自 ≥内层+30s）；per-repo 覆盖走 **config.yaml 键、SKILL 直读**（沿 `metrics.enabled` 先例 spec-review L179 / code-review L206，**不走 resolver**——两 SKILL 同法否则等值门红）；值 MUST 校验**正整数 + harness 上界**，0/负/非整/越界/读失败 → 回落默认（fail-safe 恒生效，MUST NOT fail-closed、MUST NOT 用 `--timeout 0`）。**[R1]**
- [ ] 3.4 context 用 **per-run 不可变路径** `.outside-voice/<run-id>/<site>-context.md`（弃固定名+下轮覆盖）闭 HV1 跨会话 TOCTOU（scan/render 恒对同一快照）；**父目录 MUST 仍在 `.outside-voice/` 下**〔G5——`.gitignore:19` 的 `**/.outside-voice/` 递归覆盖该层级；落到目录外 = checkpoint `git add -A` 把全量 diff/敏感 context 永久入库，正是该条款要防的〕；**MUST 同步改写两 SKILL 现行 context 构造行**（`sdflow-spec-review/SKILL.md:272` / `sdflow-code-review/SKILL.md:271` 的「固定命名、下轮覆盖」）——该行**不在 §1/§2 的改动范围内**，须在此显式列为改动点〔G5 scope 补〕；dispatch 时 task_id 追加落盘该目录 manifest（F-I 审计证据，「是否真派发」脱离纯记忆）。**[R1]**
- [ ] 3.5 **per-site 完整性机械核**（F-C·Q3 fold·基准①）：报告落 `declared-sites` 集 = 该层「**应有锚**站点集」——spec-review `{design-voice}` ∪ `{hr-tg | HR-TG∩≠∅}`、code-review `{code-voice}` ∪ `{hr-tg | HR-TG∩≠∅}`〔G1：**MUST NOT** 定义为「应 dispatch 集」——复用态 `design-voice` 未派却落锚（归档实证 44 条）、`code-voice` 是 always，按 dispatch 定义必假红；**MUST NOT 解析 `guard=`**（语义站点相关：design-voice 上 none=复用未派、hr-tg 上 none=填充值已派）；∴ 唯一动态输入 = HR-TG∩；两层站点集不同 ⇒ 该计算留等值门 marker **外**〕；加机械核「declared == 实落 `sdflow:outside-voice` 锚站点集」不等即红（承 hr-tg `declared=` 先例 adr/0018；补 `anchor_lint.py:154/595` 家族级门的 per-site 盲区 → 并发 2 站点漏收不再判 CLEAN）。**实现 MUST 复用 `anchor_lint.py` 的 `fence_outside_lines` 口径、MUST NOT 另起裸 grep**〔G4：报告正文含模版/示例锚（本 change 报告自身即是）→ 裸 grep 自指假阳，且形成 fence 口径二源〕∴ **优先实现为 `anchor_lint` 附加校验、而非独立脚本**；该核**不修改**合法组合矩阵。**[R2]**

## 4. 验证（测试覆盖）— TG-18

**测试覆盖图（code path → 测试类型）**：

| code path | 测试类型 | 依据 |
|---|---|---|
| SKILL async 分支编排（Markdown） | 手动 smoke（编排类无单测） | R1 |
| 锚契约 / anchor_lint 矩阵不变 | 机械回归（既有全笛卡尔 golden） | R2 |
| run_in_background 不可用降级 | 模拟 smoke | R1 |

- [ ] 4.1 smoke（F-J 加严）：Claude 宿主跑一次真实评审——① voice 锚 `reason_code="ok"`（非 timeout）；② 主 session 无 ≥330s 单次阻塞 Bash 调用 **且 collect 不靠轮询循环/长 sleep**（约束调用次数）；③ **刻意构造 voice 时长逼近 900s 场景**（压真实负载验后台过 600000ms 上限存活——A1 方向已由 660s 边界 spike 证，此处压真载非侥幸 <600s）；④ 记录 Step2 fan-out 墙钟 vs voice 完成时刻（校准「重叠非叠加」）；⑤ **每站点记「dispatch 时刻 / 终态通知时刻 / 落锚时刻」三者，MUST 单调（落锚不早于终态通知）**〔G3 可核验锚——这是「barrier 未早退」的**唯一实证信号**，per-site 站点集核抓不到它（早退产生的假 timeout 站点仍在集合内）〕。**[R1]**
- [ ] 4.2 回归：跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden，确认与 change 前逐条一致。**[R2]**
- [ ] 4.3 降级路径：模拟/构造 `run_in_background` 不可用，确认降级回同步 + 报告标注、不假绿；**并断言该次同步 exec 的外层超时实参 ≥330000ms、voice 正常完成而非 ~120s 被杀**〔G7：外层超时由调用方逐调用设、helper 作被调方无法机械强制（SKILL:276 自承）∴ 该失效模式**无门可守**，只能靠本条 smoke 断言抓〕。**[R1]**
- [ ] 4.4 〔grill 降级〕Open Q2 已由读码解（ADR-6：ship line 96/101 → code-review 主 session inline，run_in_background 同 A1 上下文）；本项改为**验证 §1.3/2.1 自探降级分支本身可跑**（构造 run_in_background 不可用场景 → 确认降级回同步 + 报告标注），不再需要「ship 路径实测」。**[R1]**
- [ ] 4.5 安全错误路径（DV4/HV2/F-L）：构造 voice `exit≠0`（timeout/exec-error），核 collect **只取 exit0 stdout findings + 结构化状态、不把后台文件原始 stderr 当 findings 采信**；核 harness 后台输出文件 TTL/权限/清理归属（记实测捕获语义，残余则显式登记）。**[R2]**

## 5. 收尾（scope 外记账，不在本 change 实现）

- [ ] 5.1 记 Codex-方向 efficacy=0 todo：Codex 宿主长跨模型 voice 架构性无法离开关键路径；等 codex `deferred_executor` 稳定 / 或建外部 claude daemon 再议。（sdflow-todolist）
- [ ] 5.2 记 DRY **全抽取** todo：机械等值门（本 change §2.2）已守漂移；长期把 async 段抽单一源注入两 SKILL（超本 change scope，另立 change）。（sdflow-todolist）
