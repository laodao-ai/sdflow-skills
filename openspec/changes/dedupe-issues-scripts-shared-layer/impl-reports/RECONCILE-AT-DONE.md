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

## R-2〔T5 发现·主 spec delta 同步核验〕：archive 须落地两主 spec 的旧 ref 更新

**文件**：`specs/recorder-root-resolution/spec.md`、`specs/spec-workflow/spec.md`（两份 MODIFIED delta）

T5 的机械引用守卫（`test_downstream_reference_guard.py`）**永久 allowlist 了 `openspec/specs/`**，前提是
「本 change 携 MODIFIED delta，主 spec 在 archive 阶段经 delta-sync 更新」。T5 Spec 轴已核实两 delta 真含
sdflow-issues 更新（recorder delta:37-42 三薄入口路径写为 `sdflow-issues/scripts/`；spec-workflow delta
RENAME-MAP 移除两旧名）、且 delta header 与主 spec 现役 header 逐一匹配 → sync 有对象。

**和解动作（done/archive）**：archive 子代理 delta-sync 后，**MUST 核验** `openspec/specs/recorder-root-resolution/spec.md`
与 `openspec/specs/spec-workflow/spec.md` 中原有的旧 skill 名/脚本路径（recorder 3 处、spec-workflow 4 处）
**已被 delta 替换为 sdflow-issues 目标态**（守卫 allowlist 了 specs/、不会自动抓；这是 delta-sync 正确性的
兜底核验点）。

## A-1〔T4 发现·已闭·无需 done 动作〕：`issues._legacy_block_range` 同名近重复

**结论**：T4 双轴审定级 **Important = T2 单一源遗漏**（逐行相同承重扫描算法，非 AD-7 defer）。
**已在 T4 fix1（commit c77e341）真做掉 dedup**（非 defer）：抽取 core 单一 `_scan_legacy_block_range`
+ `LegacyBlockError` 结构化 sentinel，两 caller 各自格式化错误文案（byte-exact 不变），删 issues 副本，
thinness 守 `ALLOWED_DISTINCT` 清空转正面核验。re-review 通过。**本条无需 done 阶段任何动作。**
