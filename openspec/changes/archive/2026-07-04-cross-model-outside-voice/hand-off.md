# hand-off — cross-model-outside-voice（2026-07-04）

## ✅ 完成了什么（锚点已逐条复核，非搬运 verify）

- **共享 codex helper**：`sdflow-init/assets/hack/outside-voice.sh`（preflight 三态含 missing-deps / render-prompt / exec 硬化 `-s read-only --ephemeral --output-last-message` + `-k 10` / version / secret 粗筛含 sk-ant- / 截断留痕）——锚点：`pytest sdflow-init/tests/test_outside_voice.py` **30 passed**（本 session 实跑）；checkpoint task1-3 + 修复波 commit。
- **T25 原生执行**：两 SKILL Step1 改写（原生执行 + 主 session 落盘 + v1 锚行 + 显式降级）——锚点：`sdflow-spec-review/SKILL.md:33-45`、`sdflow-code-review/SKILL.md:58-61`；**本 change 自己的 spec-review 与 code-review 两轮全程原生跑通**（gstack-review.md / code-review-report.md 均带 `mode="native"` 锚行）。
- **两 skill voice 接入 + 协议节 + HR-TG + 锚行 v1 + 分桶**——锚点：code-review-report.md 活体首跑实录（codex hr-tg 成功 3 findings / code-voice 超时→只读 fallback 回落全链验证 / M4 首份分桶 codex 采纳3·fallback 采纳1）。
- **契约套件**：trigger-catalog TG-26 四列 + HR-TG 附录 + 五层升格四处 + design-diagrams 行 + workflow.md 引用 + INDEX 计数（修 TG-25 既有漂移）+ CR-GO-06——锚点：`grep TG-26 ~/.sdflow/workflow/trigger-catalog.md`（本 session 实证 ≥2 处）+ checkpoint task10/11。
- **边界**：C7 权威 grep 零命中（verify 复跑确认）；`.gitignore` 含 `**/.outside-voice/`。
- 全量回归 **307 passed**（修复波后实跑）。

> 纠正 verify 报告一处假红：其 Minor#2 称「CONTEXT.md 不存在、HR-TG 术语未补」——实际 `openspec/CONTEXT.md:87-89` HR-TG 条目**已存在**（task12-closeout 落的），verify 子代理查错了路径。非缺口。

## ⏳ 未完成 / 延后

- **批次 `cross-model-outside-voice`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`，6 成员已分诊 PROPOSED）：
  - **B1**（ship_gate 窗口排他起点漏数 task 锚，已复现）、**B2**（gate 把 [impl-review-fix] 评审补丁误判拍板失鲜，本轮两次触发）——gate 新鲜度/窗口判定的两个真实缺陷，建议合起来开一个 `ship-gate-hardening` 小 change 优先清。
  - **T28**（阶段收尾附下一步完整 prompt）、**T29**（agent/子阶段时长度量，含工作时长 vs 墙钟拆分）——同族「工作流信息显性化」，可与 workflow-metrics-loop 合流。
  - **T30**（helper 健壮性 a-d：**a/b/c 已被本 change 修复波顺手闭掉**〔A1/A2/A5 + B2/B4 测试〕，仅剩 d fake-timeout 时序）、**T31**（voice 层硬化池 ×8：协议节下沉单一源 / **cap-timeout 校准（185KB→300s 超时实证）** / 并发命名 / stdout 落点 / 孤儿进程 / 分隔符 nonce / UTF-8 截断 / setup.sh 原子替换 + codex 沙箱黑盒验证）。
- **延后的自动决策**：无「拿不准」项——T10 复核仅 1 例（timeout 缺失处置选显式报错，客观判据=反静默原则，记录在 code-review-report 台账）。
- **verify Minor**：T25 台账行的 change 列写 `sdflow-ship`（源 change 归属，provenance 正确——T25 是 sdflow-ship 评审发现的，非瑕疵，留档说明即可）；preflight 三态是对 tasks 1.1 二态的超集加固（评审驱动，非偏离）。

## ▶ 下一阶段建议

1. **优先**：`ship-gate-hardening`（B1+B2，编排层可靠性——本轮 ship 两处人工越权都是它造成的，量小收益直接）。
2. **数据驱动**：跑满 10 次评审后按 M4 分桶采纳率执行 Q3/Q5 复评条款（always-on 降采样与 HR-TG 子集校准）——首份样本已在 code-review-report。
3. T31② cap-timeout 校准建议随下一次真实评审顺带实测（降 OV_MAX 或分片），有实证数据再改参。
4. workflow-metrics-loop materialize 时把 T28/T29 并入 scope 评估。
