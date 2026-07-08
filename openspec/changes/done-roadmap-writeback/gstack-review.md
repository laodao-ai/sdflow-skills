<!-- sdflow:step1-broad-review v1 mode="simulated" -->
# 广审留档（Step1 · simulated）— done-roadmap-writeback（第三轮·最小核）

> **mode="simulated"**：autoplan 原生流程是 gstack plan 文件专用（preamble 跑 gstack session 机制、操作对象=plan file），不适配本 OpenSpec change dir；故由 fresh-context 子代理模拟其 CEO/design/eng/DX 四镜 + 6 决策原则广审。**MUST NOT 伪装原生**。侧信道佐证：codex outside-voice 本轮 exit 1 = usage limit（恢复 1:34 AM）→ 回落 claude-fallback（design-voice 锚 runner="claude-fallback" reason_code="exec-error"）。findings 已并入 spec-review-report.md（第三轮）合并池。

## 广审四镜 findings（simulated · CEO/design/eng/DX）

- **B-F1 [eng·高]** D-2/D-4/spec Scenario 1 时序自相矛盾：草稿钉在 hand-off 步（done 第二步，archive 前），但盘面清单要 archive 路径（第三步）+ merge（第五步）——hand-off 时两块盘面尚未发生。接地核对 `sdflow-done/SKILL.md`：verify=PASS/tasks 完成态/pytest 数在 hand-off 时**已就位**，archive 路径是**可预测公式**（非已存在）、merge 只有 step0.1 捕获的**意图**。→ 盘面成熟度分裂，措辞须区分"事实 vs 预测/意图"。
- **B-F2 [design/eng·高]** 关联标记 `<!-- roadmap: {name} -->` 只带 roadmap **名**，但复选框在 phase/子任务粒度（实证 `roadmap.md` `- [x] 1.A.1`，混无 id 验收标准行 + 占位行）。task 1.2「定位关联子任务」在只给名时无法机械确定勾哪个 → 大量退"留人工"，侵蚀"省定位复选框行"的核心承诺。
- **B-F3 [DX·中]** 双通道 marker vs `--roadmap` 并存且 name 不一致时无优先级裁决。→ 定 precedence + 不一致 warn。
- **B-F4 [design·中]** "与 §2.1 sweep 对称"框架误导：sweep 机械终写、本 change 助人确认，**写入语义相反**。实现者可能被"对称"诱导复用 sweep 自动落盘 → 滑回机械改 roadmap（正是 C1/C2 要消的）。→ 降为"同位不同性"。
- **B-F5 [CEO·低]** 最省替代未显式排除：纯 hand-off 模板 + 回填 checklist 提示（零脚本零新逻辑）应设为默认基线；脚本仅当盘面读取/定位确需确定性时再加。
- **B-F6 [eng·低]** "验证数字(pytest 数)"盘面来源未指明（verify-report 未强制含计数）。→ 指定单一来源（verify-report 取，缺则留人工，勿重跑）。

**广审结论**：建议进设计门，但需先修 B-F1/B-F2 两高（均可澄清、不需重构）。核心方向经三轮收敛已稳、无致命。

## outside-voice（design-voice · claude-fallback，reason_code=exec-error）findings

codex exit 1（usage limit）→ 回落只读 Claude 子代理（同源同 prompt）。找"漏了什么"，剔除与已列重复：

- **OV-F1 [HIGH]** 异步回填**无闭环/无追踪** → feature 自身目标被打败：hand-off 随 archive 冻结进归档，merge 后 `/clear` 无人再被提醒；经 `/sdflow-ship` 跑时人被显式支走（阶段三无人类门），异步提示被执行概率趋零 → 产一堆没人 apply 的草稿。建议给可追踪落点（如 todolist 一条 `roadmap 回填待确认`）或显式登记"产草稿即止、不保证 apply"残差。
- **OV-F2 [HIGH]** archive 路径含**归档日期** `{date}-{change}`，hand-off 时不可知且会漂（本 session 实测日期从 07-08 跳 07-09；跨零点/异步拖到次日则预填日期段直接错）。加重 B-F1。
- **OV-F3 [MEDIUM]** 两存量 roadmap 格式**实测分裂**：`mechanical-layer-hardening` 用 `- [ ] 1.A.1`（grep 54 处）；`workflow-cost-optimization` 用 `| **P1** … | ✅` 表 + 散文 bullet（`grep '^- \['` 零命中、无复选框无 id）。定位算法对后者**整条落空**，"漏=现状"退化是半数存量 roadmap 常态、非边界个案。→ 先收敛格式（前置）或定位显式支持两格式并对不支持者 fail-loud。
- **OV-F4 [MEDIUM]** change↔roadmap 阶段**非 1:1**：一阶段跨多 change、一 change 只交付阶段一部分、task-log 含非 change 项（实证 wco task-log 有 `[explore]`/`[阶段4] 回填` 条目）；助手勾复选框 + 预填 task-log 骨架的插入位置（task-log **倒序需 prepend**）+ 归属阶段无定义 → 模型自由裁量滑回代判。
- **OV-F5 [MEDIUM]** `--roadmap` flag 经 `/sdflow-ship` 编排**不透传**（ship 只归一化 merge 意图，通篇无 roadmap 透传）→ ship 下 flag 通道事实失效，只 in-file marker 存活。→ marker 定为主通道，flag 仅直调 done 覆写；或补 ship 透传。
- **OV-F6 [MEDIUM]** 草稿 done 时算、人异步 apply，其间 roadmap 可能被另一 change 归档/改版/手改重编号 → apply 时无重校验会双勾/错位。→ 草稿注明快照 commit，apply 要求对当前 roadmap 重核目标行存在性。
- **OV-F7 [MEDIUM→LOW]** marker 由谁/何时/写哪个 change 文件未定义 → 采纳 chicken-egg（漏 marker 恰是本 feature 想消的摩擦来源）。→ 让 sdflow-roadmap 建阶段 change 时自动落 marker（源头确定性建立），手工声明降兜底。

**OV 整体判断**：最小核消掉了机械回写风险，但把复杂度推给**异步闭环**（OV-F1）与**关联/定位的现状假设**（OV-F3/F4）——这两处才是实现期会爆的地方，且当前 design 对它们的论证薄于对"弃什么"的论证。
