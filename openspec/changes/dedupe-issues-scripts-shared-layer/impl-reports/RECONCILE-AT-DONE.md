# done/archive 阶段待和解项（实现期发现，现在改 specs 会触设计失鲜门）

> 这些是**已批准设计与 spec-delta 文本之间的内部不一致**，实现期由 implementer 上抛、编排层裁决为
> 「done 阶段和解」——因为 CONTINUE_IMPL 窗口内改 `specs/` 会触发 `ship_gate` 设计失鲜 REFUSE_START。
> 正解 = 代码审期 / done 期修订四件套以匹配落地现实（流程明文允许 "revise to match reality"，
> 且 RUN_CODE_REVIEW 起不再检查 design 域失鲜）。**archive 子代理 verifies each delta against
> actual code**——本表是其必须消解的清单。

## R-1〔T4 发现·DG-M1 R6〕：determinism-guards spec delta 两 Scenario 自相矛盾

**文件**：`specs/determinism-guards/spec.md`

- `:32-35` Scenario「direct↔scan golden 不再宣称抓 rule 遗漏」：THEN 守「同源两 code-path 接线正确」，
  **MUST NOT 宣称「任一方漏 rule → 失败」（同源自比、tautology）**。← 这条符合 AD-4/R6，正确。
- `:42-46` Scenario「direct snapshot 与 scan 语义漂移」：THEN「…任一方漏掉 lexical/marker/overlay/ID
  rule 时测试失败」。← **与上条直接矛盾**：仍宣称抓 rule 遗漏。

**落地现实**（T4 代码）：golden 已按 R6 降级为接线守，**不**宣称抓 rule 遗漏（单一 core 是 rule 单一源，
同源自比 = tautology）。∴ `:42-46` 的「漏 rule 时测试失败」是陈旧宣称。

**和解动作（done/archive）**：把 `:42-46` Scenario 的 THEN 改为与 R6 一致——守「同源两 code-path 经
semantic key 等价（接线/投影正确）」，删「任一方漏掉…rule 时测试失败」的 rule-完整性宣称（真 rule-完整性
须外部 golden fixture，非 core 自比 core，AD-4/R6 已声明）。使两 Scenario 一致。

## A-1〔T4 发现·已闭·无需 done 动作〕：`issues._legacy_block_range` 同名近重复

**结论**：T4 双轴审定级 **Important = T2 单一源遗漏**（逐行相同承重扫描算法，非 AD-7 defer）。
**已在 T4 fix1（commit c77e341）真做掉 dedup**（非 defer）：抽取 core 单一 `_scan_legacy_block_range`
+ `LegacyBlockError` 结构化 sentinel，两 caller 各自格式化错误文案（byte-exact 不变），删 issues 副本，
thinness 守 `ALLOWED_DISTINCT` 清空转正面核验。re-review 通过。**本条无需 done 阶段任何动作。**
