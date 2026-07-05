<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# 广审（gstack-amendment）— workflow-metrics-loop

> mode=**simulated**：autoplan（gstack）为代码 plan 广审设计，不适配 OpenSpec 设计文档，故派 fresh-context 子代理模拟 CEO/工程/设计完整性/DX 四视角广审（非原生 autoplan）。侧信道佐证：子代理 usage 运行痕迹（100k tokens / 21 tool_uses / 256s），逐文件读了四件套 + 交叉核 SKILL/ship_gate。findings 纳入 Step3 合并池。

## 四视角 findings（进合并池）

- **F-CEO-1 [高]** 回路空转：Success Metrics 只验机械动作（锚落/表出），无「人真看表真裁决」；surfacing 非自动、无 hook，「每 N change」的 N 退化成「按需」= 没人开的仪表盘 → 与立项理由（现状无人验证）同失败模式重演。→ **采信**（对抗镜2-3 同证），SR-A 修。
- **F-CEO-2 [低]** ROI 未量化但可接受（P0/P1/P2 分层把风险切小）。→ 接受。
- **F-ENG-1 [高]** 「findings 与合并池实收数一致」自检机制未设计——存在性检测做不了数值核对，容易被简化成只查字段存在。→ **采信**，SR-B（诚实降级为信任边界）。
- **F-ENG-2 [中]** 度量锚硬阻塞挂旁路观测系统，阶段三无人类门、记账疏漏硬打断流水线。→ **部分采信/降级**：与现有 R1/R3/R5 锚自检硬阻塞一致，且阻塞是「报告完整性」本步可补；消费仓侧的过重问题并入 Q2（opt-out）。
- **F-ENG-3 [低]** Success Metric #2 本 change 合并前无真实数据验证。→ **采信**（对抗镜2-2 同证），SR-H reword。
- **F-DES-1 [中]** `sev` 子格式 `致N/高N/中N/低N` 未定义完整、反例矩阵未测。→ **采信**，SR-I。
- **F-DES-2 [低]** 步骤号措辞：报告落盘在 Step4/5 非 Step3。→ 采信（并入 SR-M 时序澄清）。
- **F-DES-3 [低]** `broad` findings 计数口径未定义。→ **采信**，SR-L（去重后计入）。
- **F-DX-1 [中]** 消费仓无条件 SHALL 落锚+阻塞、无 opt-out。→ **采信**（对抗镜2-4 同证）→ 决策门 Q2。
- **F-DX-2 [低]** 两 SKILL 锚行自检清单变长，后续做统一抽象。→ 记，非本 change。

**总体判断**：接地诚实度高（ADR-3 砍 dur_s、ADR-2 独立敏感声明），P0/P1/P2 分层稳；但 F-CEO-1（回路空转）+ F-ENG-1（数值自检机制）两条不收敛不宜直接进实现——已由 SR-A/SR-B 修。
