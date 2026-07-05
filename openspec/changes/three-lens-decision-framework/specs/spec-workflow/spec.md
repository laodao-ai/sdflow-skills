## MODIFIED Requirements

### Requirement: 评审决策登记进报告，不中途打断

评审编排器 SHALL 把决策点（自动决策与需人拍板）连同选项、推荐、**决策后果**登记进评审报告，MUST NOT 在评审中途以 `AskUserQuestion` 打断，使一遍评审能自主跑到完成。

**决策后果 SHALL 按三镜展开**——系统镜（对系统本身：耦合 / 依赖 / 复杂度 / 可回退性）、用户镜（对最终用户使用：体验 / 可感知行为 / 干扰）、开发循环镜（对后续开发过程循环：心智负担 / 是否靠人 / 流程开销 / 复用性）——并 MUST 附**一句主次判定**（对当前这个决策，三镜哪个更重要、为何据此选定），MUST NOT 只罗列三镜后果而不判主次。触发深度 SHALL 分层：行为层每个决策都按三镜 + 主次分析；书面写入报告的三镜 + 主次 MUST 覆盖命中 TG-23（≥2 合理方案 / 非显然设计）的**方案选择**决策点，琐碎决策（无 ≥2 合理方案）SHALL NOT 被强制写满三镜段（避免样板税）。**「核验不了的事实」类决策点（Q2 事实核验）不属 TG-23，走「待核验证据 / 风险 / 默认处理」登记，不强制三镜**〔CV4：TG-23 定义仅 ≥2 方案，事实核验另类〕。

#### Scenario: sdflow-spec-review 遇到 ≥2 合理方案
- **WHEN** 某评审镜发现一个有 ≥2 合理方案的决策点（命中 TG-23）
- **THEN** 编排器把它写入 spec-review-report.md 决策登记区（选项 + 推荐 + 三面后果 + 主次判定）并继续，不中途弹 AskUserQuestion

#### Scenario: sdflow-code-review 自动选推荐项按三镜记理由
- **WHEN** 阶段三 code-review 按 T10 三级协议在 ≥2 方案中自动选定推荐项（有客观判据自动选 / 无则对抗镜复核 / 复核不过 defer；判据定义引主 spec T10 需求，本需求不重定义）
- **THEN** 记入 code-review-report.md 台账的理由 SHALL 按三镜 + 主次判定组织（与 spec-review 决策登记同口径），MUST NOT 只写一句主观理由

#### Scenario: 琐碎决策不被强制写满三镜
- **WHEN** 某决策点无 ≥2 合理方案（显然设计、单一可行路径）
- **THEN** 编排器 SHALL NOT 强制为其写满三面后果 + 主次判定段（书面三镜门只对命中 TG-23 的决策 MUST），避免样板噪声淹没报告

#### Scenario: 评审/grill 新发现工作走 fold-vs-defer 判据
- **WHEN** 评审 / grill 过程中发现当前 change 未覆盖的新需求或修复
- **THEN** 是否并入当前 change SHALL 按【对当前 change 工作的影响 + workflow 循环固定成本高】判——related + 低影响（紧耦合 / 同 capability / 一致性修复 / blast-radius 小）→ fold 进当前 change，真独立 / 扩容大 / 需自身设计审查 → defer 另开——此判定走三镜（开发循环镜通常主导），MUST NOT 反射式以「change 单一职责」教条拆分（拆 change 有一整轮循环固定成本）；判据成文于 BASE-18

### Requirement: outside-voice tension 不静默采纳

outside voice 与主审分歧（tension）SHALL 中立并陈、标 TENSION：sdflow-spec-review 写入报告决策登记区（选项 + 推荐 + 两方视角 + **三面后果（系统 / 用户 / 开发循环）+ 主次判定**，设计 HARD-GATE 人一次性拍板）；sdflow-code-review 有把握则自动裁决并**按三镜 + 主次记理由**、拿不准则 defer 进 buglist/todolist + hand-off。outside voice 的建议 MUST NOT 被静默自动采纳（不直接改代码/设计而不留痕）。**`runner=codex`** 的 outside-voice findings MUST NOT 经自评置信阈值（<80）预过滤——跨模型自评不可比、异见易被同族标尺误杀——一律直通对抗裁决，被裁掉的连理由落报告「已裁掉」区〔grill-amendment Q4〕；`runner=claude-fallback` 的 findings 属同族产物，照过同族置信滤（豁免理由对其不成立）〔spec-review-amendment〕。

#### Scenario: 设计侧分歧进决策登记区
- **WHEN** codex voice 与 spec-review 主审对同一设计点结论相反
- **THEN** 报告决策登记区新增 TENSION 条目（两方观点 + 推荐 + 三面后果 + 主次判定），不中途 AskUserQuestion

#### Scenario: 代码侧分歧自动裁决或 defer
- **WHEN** codex voice 与 code-review 主审分歧且裁决无客观判据
- **THEN** defer 进 issues 池并写入 hand-off，不静默采纳任一方

#### Scenario: 低自评置信的 codex finding 不被预筛
- **WHEN** 某条 `runner=codex` 的 finding 自评置信低于 Step3 阈值（<80）
- **THEN** 该条仍进入对抗裁决（不被置信滤拦截）；若裁决不成立，连理由落报告「已裁掉」区

#### Scenario: fallback finding 照过同族滤〔spec-review-amendment〕
- **WHEN** 某条 `runner=claude-fallback` 的 finding 自评置信低于阈值
- **THEN** 按同族 findings 常规处理（过滤规则一致），不享受跨模型豁免
