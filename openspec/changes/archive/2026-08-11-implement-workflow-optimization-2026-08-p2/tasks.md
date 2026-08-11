# Tasks — implement-workflow-optimization-2026-08-p2

> Requirement 缩写：R-裁决 =「评审裁决协议为机械前置 + 二元裁决 + 置信降排序」；R-roster =「镜 roster 条件化派发（降采样）」；R-voice =「outside-voice tension 不静默采纳」（MODIFIED）；R-全跑 =「sdflow-code-review 为每次全跑的独立强制主审」（MODIFIED）；R-处置 =「待复评镜处置记录消费与行内注记」；R-快照 =「done 收尾终态快照」。
> 顺序即依赖：裁决面（commit B）→ 重放部署门 → roster 面（commit A）→ 快照 → 集成收尾。migration 步序见 design.md §Migration Plan。

## 1. 裁决协议面（commit B · P0）〔R-裁决 / R-voice / R-全跑〕

- [x] 1.1 新建 `findings_ref_check.py`（bundle `tools/`，实施定名）：**只吃结构化 JSON 输入**（每条 finding 带 `{file, line, quote}` 或 `evidence_pack` 机读字段，不解析 markdown 散文）〔spec-review-amendment〕；逐条核 路径存在 / file:line 界内 / **引文命中所报行（或行范围）**〔spec-review-amendment〕；输出三态 pass / fail / **uncheckable（非干净 path:N 形态不裁，直进强档裁决）**〔spec-review-amendment〕；无引文且无证据包（结构化字段确认皆缺）→ 机械裁掉；脚本级崩溃 = 显式降级（整批标 `[ref-check-unavailable]` 直进裁决 + 报告显著标注）〔spec-review-amendment〕；输出遵循信号内诚实（不 emit 裸通过码）；带 pytest（正例 / 三种失败态 / 无引文态 / uncheckable 态 / 脚本级崩溃态 / 输出码形态）〔R-裁决〕
- [x] 1.2 `sdflow-code-review/SKILL.md` Step3 重写：删 <80 数值滤、删置信封顶 ≤50 条款、删跨模型豁免矩阵条款；接入 1.1 机械前置 + 二元裁决（采纳/裁掉/defer + critique）+ 置信仅排序；「已裁掉」区新增 `[ref-check]` 来源标记；frontmatter description 中 **Step3** 括注「置信过滤（<80 滤除）+ 对抗裁决」改「机械引用核+二元裁决」（显式删「(<80 滤除)」字样；原任务误标 Step2，spec-review-amendment 更正）；Step2 各镜 prompt 的 findings 输出契约改为强制结构化字段（`{file, line, quote}` / `evidence_pack`，供 1.1 消费）〔spec-review-amendment〕〔R-裁决 / R-voice / R-全跑〕
- [x] 1.3 `sdflow-spec-review/SKILL.md` Step3 裁决动作层对齐（同 1.2 三层协议；spec-review 侧核对象含四件套文档）；「拿不准 → 决策登记区」路由保留并与置信数字脱钩〔R-裁决〕
- [x] 1.4 lens-metric contract + emitter + anchor_lint 合法组合矩阵扩展〔设计门 Q1〕：contract 约束①（普通镜行 `runner==host`）扩一条合法组合「普通镜行 `runner="none"` ∧ `findings=0`」，contract 升版本（枚举域不动、不新增字段）；`lens_metric_emit.py` 非-outside-voice 分支接受 `runner="none" ∧ findings=0`（原 `:147-148` 强制 `runner==host` 加旁路）；`anchor_lint.py` 普通镜行校验（`:809-817`）同步接受该组合；`lens_metric_emit.py` 输入侧兼容（findings JSON 含置信字段时不报错）+ retro 再生冒烟〔R-roster / R-裁决〕
- [x] 1.5 spec-workflow 主 spec 相关条款联动核查：grep 全仓「置信过滤 / <80 / 豁免」消费点（SKILL / bundle 规则 / spec / 测试），逐处改齐或确认不动（C7 边界：anchor_lint 矩阵保留）〔R-voice〕

## 2. 历史重放部署门（P0）〔R-裁决〕

- [x] 2.1 重放 harness（一次性，落 `impl-reports/replay/`）：选 3-5 份归档评审报告，`git worktree` checkout `reviewed_sha`，findings 逐条过 1.1 脚本 + 强档二元重裁，与历史裁决对表
- [x] 2.2 重放报告〔设计门 Q2：三类归因法〕：重裁不一致项逐条归因入三类——①历史误标/口径漂移（剔除分母，重放报告记归因证据）②模型方差（复裁一次，二次仍不一致才计入）③协议缺陷（真误杀）；**红线 = ③类（协议缺陷）= 0**，①②类如实报数不挡部署；噪声重入率标「参考」（C4 语料限制如实写明）；报告落 `impl-reports/replay/replay-report.md`——**③类非 0 则 1.2/1.3 不得部署下游**

## 3. roster 面（commit A · P1）〔R-roster / R-处置〕

- [x] 3.1 设计门拍板后的处置表写入 `openspec/retro/mirror-dispositions.yaml`（DD1 schema；13 面镜含降采样条件原文）〔R-处置〕
- [x] 3.2 两评审 SKILL roster 段落地处置：降采样镜（code-review history；grounding 经设计门 Q3 拍板改保留、从降采样清单移除）加派发条件行，**并给出条件阈值的具体取值与判定命令**（如 `git diff --numstat` 行数阈值 / `--diff-filter=R` rename 检测，随 roster 段落盘，不留「大规模」定性词）〔spec-review-amendment〕；条件跳过轮落锚 `runner="none" findings="0"`〔设计门 Q1：合法组合矩阵扩展，condition-not-met 不进锚字段，成因由 dispositions.yaml condition + 报告散文承载〕+ 报告一行说明〔R-roster〕
- [x] 3.3 `retro_report.py` surfacing 注记：读 dispositions.yaml、命中镜行内注记；错误语义分治（缺失=零注记 / 坏 yaml=fail-loud / 未命中键=告警）；带 pytest（四态各一）〔R-处置〕

## 4. done 终态快照（独立小 commit · P2）〔R-快照〕

- [x] 4.1 `sdflow-done/SKILL.md` 第三步起手前接线 `token_snapshot.py --step done-final`（archive 前、change 目录原位）；失败显式降级不挡收尾；残余盲区（archive/commit/merge 自身）在契约文档如实声明；**补 host 判定：codex/unknown 宿主不走 Claude transcript mtime fallback（现 `token_snapshot.py:40,90` 硬编码 host=claude + 无条件 mtime 兜底会记错 transcript），直接落显式降级行 + 回归测试**〔spec-review-amendment〕〔R-快照〕
- [x] 4.2 token-snapshot 契约/测试同步：`done-final` step 值入契约文档；retro join 对该行可读（冒烟）〔R-快照〕

## 5. 集成与收尾

- [x] 5.1 bundle 权威源一致性：所有规则改动确认落 `sdflow-init/assets/workflow/`（非仓内副本）；`sync_principles.py --check` 绿；README/INDEX 若涉及则同步；`adr/0041` 首段「validator …（弱档…）」括注同步为「机械脚本」（DD4 已升格，防实施者误读）〔spec-review-amendment〕
- [x] 5.2 全仓 pytest 绿 + anchor_lint 全绿（真实锚样本回归）
- [x] 5.3 dogfood 准备：前瞻窗口判读指标写进 hand-off（漏检→roster、采纳率偏移→裁决；对照基线 code-review ~73% / spec-review ~87-93%）——窗口本身为 roadmap 层残项，不阻塞归档

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
