> Requirement 追溯：**[R1]** = `host-adaptive-execution` / 「outside-voice exec 的 dispatch 模式宿主自适应」；**[R2]** = 「async dispatch 不改变锚契约与诚实降级」。

## 1. spec-review SKILL：host-adaptive async 分支

- [ ] 1.1 `sdflow-spec-review/SKILL.md` 的「outside-voice helper 调用协议」节（line 263），exec 步加 `$SDFLOW_HOST` 分支：`claude` = `run_in_background` dispatch（@Step1 design-voice / @Step2 hr-tg 各 context 就绪即派）+ Step3 collect；`codex` = 同步现状（外层 ≥330s）。**[R1]**
- [ ] 1.2 dispatch 时 SHALL 显式记「站点↔task_id」映射（**按实际 dispatch 过的站点**——design-voice 前置门控于 reuse-guard、hr-tg 条件于 HR-TG∩≠∅，故后台 voice 数不定 0/1/2；见 design 并发节），collect 时按站点逐一取（防 model-driven 记账漏收）。**[R1]**
- [ ] 1.3 补 `run_in_background` 能力自探：不可用 → 降级回同步 + 报告显式标注，MUST NOT 假装 async 成功。**[R1]**

## 2. code-review SKILL：同款分支（scope-check 逐字对齐）

- [ ] 2.1 `sdflow-code-review/SKILL.md` 的「outside-voice helper 调用协议」节（line 261）加与 §1 逐字对齐的 host 分支 + 站点↔task_id 记账 + 自探降级。**[R1]**
- [ ] 2.2 **机械等值门**（ADR-5，替代人工 scope-check）：① 两 SKILL 的 async host 调度段用 `<!-- sdflow:async-branch:start/end -->` marker 圈定——段内**只写站点无关的 host 调度逻辑**（claude=run_in_background dispatch/collect、codex=同步、自探降级、collect 轮询到终止按 exit-code 分支），**站点枚举/context 构造留 marker 外**，∴ 两段可字节相同；② 写 `hack/check_async_branch_parity.py`（沿用 `sync_principles.py` idiom）断言两段字节相同、坏则非零退出；③ 挂进 `setup.sh` + `hack/tests/`；④ 首次跑确认绿。**[R1]**

## 3. 锚契约与诚实降级守护

- [ ] 3.1 两 SKILL 写入 collect 语义：Step3 轮询到 voice 终止（≤`--timeout` 天花板 = 脚本自杀点），exit124→既有同族 fallback、锚 `reason_code="timeout"`，MUST NOT 假绿、MUST NOT 落零锚。**[R2]**
- [ ] 3.2 diff 核 `outside-voice.sh` / `anchor_lint` 合法组合矩阵 / 出境安全三件套**零改动**（四旗承重墙、secret_scan、FRAME、200KB 截断逐字不变）。**[R2]**
- [ ] 3.3 collect 天花板可配：SKILL exec 传 `--timeout <值>`，默认 **900s**；per-repo 覆盖走 config.yaml 键——读取路径（resolve-* 导出 vs SKILL 直读 config）impl 定，**默认值 fail-safe 恒生效**（config 缺失/读失败 → 900s，MUST NOT fail-closed）。**[R1]**

## 4. 验证（测试覆盖）— TG-18

**测试覆盖图（code path → 测试类型）**：

| code path | 测试类型 | 依据 |
|---|---|---|
| SKILL async 分支编排（Markdown） | 手动 smoke（编排类无单测） | R1 |
| 锚契约 / anchor_lint 矩阵不变 | 机械回归（既有全笛卡尔 golden） | R2 |
| run_in_background 不可用降级 | 模拟 smoke | R1 |

- [ ] 4.1 smoke：Claude 宿主跑一次真实评审，观察 voice 锚 `reason_code="ok"`（非 `timeout`）、主 session 无 ≥330s 单次阻塞 Bash 调用。**[R1]**
- [ ] 4.2 回归：跑 `anchor_lint` 的 host×runner×reason_code×findings 全笛卡尔 golden，确认与 change 前逐条一致。**[R2]**
- [ ] 4.3 降级路径：模拟/构造 `run_in_background` 不可用，确认降级回同步 + 报告标注、不假绿。**[R1]**
- [ ] 4.4 〔grill 降级〕Open Q2 已由读码解（ADR-6：ship line 96/101 → code-review 主 session inline，run_in_background 同 A1 上下文）；本项改为**验证 §1.3/2.1 自探降级分支本身可跑**（构造 run_in_background 不可用场景 → 确认降级回同步 + 报告标注），不再需要「ship 路径实测」。**[R1]**

## 5. 收尾（scope 外记账，不在本 change 实现）

- [ ] 5.1 记 Codex-方向 efficacy=0 todo：Codex 宿主长跨模型 voice 架构性无法离开关键路径；等 codex `deferred_executor` 稳定 / 或建外部 claude daemon 再议。（sdflow-todolist）
- [ ] 5.2 记 DRY **全抽取** todo：机械等值门（本 change §2.2）已守漂移；长期把 async 段抽单一源注入两 SKILL（超本 change scope，另立 change）。（sdflow-todolist）
