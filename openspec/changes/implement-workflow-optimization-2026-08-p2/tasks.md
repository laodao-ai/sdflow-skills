# Tasks — implement-workflow-optimization-2026-08-p2

> Requirement 缩写：R-裁决 =「评审裁决协议为机械前置 + 二元裁决 + 置信降排序」；R-roster =「镜 roster 条件化派发（降采样）」；R-voice =「outside-voice tension 不静默采纳」（MODIFIED）；R-全跑 =「sdflow-code-review 为每次全跑的独立强制主审」（MODIFIED）；R-处置 =「待复评镜处置记录消费与行内注记」；R-快照 =「done 收尾终态快照」。
> 顺序即依赖：裁决面（commit B）→ 重放部署门 → roster 面（commit A）→ 快照 → 集成收尾。migration 步序见 design.md §Migration Plan。

## 1. 裁决协议面（commit B · P0）〔R-裁决 / R-voice / R-全跑〕

- [ ] 1.1 新建 `findings_ref_check.py`（bundle `tools/`，实施定名）：逐条核 路径存在 / file:line 界内 / 单行引文子串；无引文且无证据包 → 机械裁掉；输出遵循信号内诚实（不 emit 裸通过码）；带 pytest（正例 / 三种失败态 / 无引文态 / 输出码形态）〔R-裁决〕
- [ ] 1.2 `sdflow-code-review/SKILL.md` Step3 重写：删 <80 数值滤、删置信封顶 ≤50 条款、删跨模型豁免矩阵条款；接入 1.1 机械前置 + 二元裁决（采纳/裁掉/defer + critique）+ 置信仅排序；「已裁掉」区新增 `[ref-check]` 来源标记；Step2 括注「置信过滤+对抗裁决」改「机械引用核+二元裁决」〔R-裁决 / R-voice / R-全跑〕
- [ ] 1.3 `sdflow-spec-review/SKILL.md` Step3 裁决动作层对齐（同 1.2 三层协议；spec-review 侧核对象含四件套文档）；「拿不准 → 决策登记区」路由保留并与置信数字脱钩〔R-裁决〕
- [ ] 1.4 lens-metric contract：`runner="none"` 成因清单扩 `condition-not-met`，按 §enum 扩展治理升版本；`lens_metric_emit.py` 输入侧兼容（findings JSON 含置信字段时不报错、锚 schema 不动）+ retro 再生冒烟〔R-roster / R-裁决〕
- [ ] 1.5 spec-workflow 主 spec 相关条款联动核查：grep 全仓「置信过滤 / <80 / 豁免」消费点（SKILL / bundle 规则 / spec / 测试），逐处改齐或确认不动（C7 边界：anchor_lint 矩阵保留）〔R-voice〕

## 2. 历史重放部署门（P0）〔R-裁决〕

- [ ] 2.1 重放 harness（一次性，落 `impl-reports/replay/`）：选 3-5 份归档评审报告，`git worktree` checkout `reviewed_sha`，findings 逐条过 1.1 脚本 + 强档二元重裁，与历史裁决对表
- [ ] 2.2 重放报告：误杀率（历史采纳且实修被新协议裁掉）**红线 = 0**，非 0 逐条追查记因；噪声重入率标「参考」（C4 语料限制如实写明）；报告落 `impl-reports/replay/replay-report.md`——**不过门则 1.2/1.3 不得部署下游**

## 3. roster 面（commit A · P1）〔R-roster / R-处置〕

- [ ] 3.1 设计门拍板后的处置表写入 `openspec/retro/mirror-dispositions.yaml`（DD1 schema；13 面镜含降采样条件原文）〔R-处置〕
- [ ] 3.2 两评审 SKILL roster 段落地处置：降采样镜（草案：code-review history、spec-review grounding）加派发条件行；条件跳过轮落锚 `runner="none" findings="0"`（condition-not-met）+ 报告一行说明〔R-roster〕
- [ ] 3.3 `retro_report.py` surfacing 注记：读 dispositions.yaml、命中镜行内注记；错误语义分治（缺失=零注记 / 坏 yaml=fail-loud / 未命中键=告警）；带 pytest（四态各一）〔R-处置〕

## 4. done 终态快照（独立小 commit · P2）〔R-快照〕

- [ ] 4.1 `sdflow-done/SKILL.md` 第三步起手前接线 `token_snapshot.py --step done-final`（archive 前、change 目录原位）；失败显式降级不挡收尾；残余盲区（archive/commit/merge 自身）在契约文档如实声明〔R-快照〕
- [ ] 4.2 token-snapshot 契约/测试同步：`done-final` step 值入契约文档；retro join 对该行可读（冒烟）〔R-快照〕

## 5. 集成与收尾

- [ ] 5.1 bundle 权威源一致性：所有规则改动确认落 `sdflow-init/assets/workflow/`（非仓内副本）；`sync_principles.py --check` 绿；README/INDEX 若涉及则同步
- [ ] 5.2 全仓 pytest 绿 + anchor_lint 全绿（真实锚样本回归）
- [ ] 5.3 dogfood 准备：前瞻窗口判读指标写进 hand-off（漏检→roster、采纳率偏移→裁决；对照基线 code-review ~73% / spec-review ~87-93%）——窗口本身为 roadmap 层残项，不阻塞归档

## 测试覆盖图〔TG-18〕

| code path | 测试类型 |
|---|---|
| `findings_ref_check.py` 三查 + 无引文态 + 输出码 | pytest 单元（1.1） |
| `retro_report.py` 处置注记四态（注记/缺失/坏 yaml/未命中键） | pytest 单元（3.3） |
| `lens_metric_emit.py` 含置信字段输入兼容 | pytest 单元（1.4） |
| 新裁决协议对历史语料行为 | 重放对表（2.1-2.2，一次性） |
| SKILL 条款与锚一致性 | anchor_lint 回归（5.2） |
| roster 条件跳过锚行 | dogfood 首轮真实评审（窗口期） |
| done-final 快照行 | retro join 冒烟（4.2） |
