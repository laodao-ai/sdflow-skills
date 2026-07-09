## ADDED Requirements

### Requirement: specs/rules ↔ INDEX 双向 set-diff

`maintain_scan.py` SHALL 扫描 `openspec/specs/` 下所有 `spec.md` 与 `openspec/rules/` 下所有 `.md`（`openspec/rules/` 为**可选**目录，缺失时按空集处理、非错误——见「坏输入 fail-closed」），解析 `INDEX.md` **sdflow-init 托管块之外**的已列表格条目，产出双向 set-diff 只读报告，分两类：**新增未索引**（文件系统存在、INDEX 未列）与 **已删未清理**（INDEX 列出、文件系统不存在）。脚本 MUST NOT 修改任何文件。〔grill-amendment：rules/ 可选 + 托管块排除〕

解析 INDEX 时 MUST 排除 `<!-- opsx-init:rules:start -->` 至 `<!-- opsx-init:rules:end -->` 托管块——该块索引 workflow bundle（`openspec/workflow/*.md`），归 sdflow-init（`update` 刷新），非本能力的 set-diff 对象。

#### Scenario: 文件系统有新 spec 未进 INDEX
- **WHEN** `openspec/specs/foo/spec.md` 存在但 `INDEX.md` 未列 `foo`
- **THEN** 报告在「新增未索引」类下列出 `foo`（spec 类），退出码 0（有差异不算错误）
- **AND** `INDEX.md` 与文件系统内容保持不变（脚本零写）

#### Scenario: INDEX 列了已删除的 rule
- **WHEN** `INDEX.md` 托管块之外列出 rule `bar` 但 `openspec/rules/bar.md` 不存在
- **THEN** 报告在「已删未清理」类下列出 `bar`（rule 类）

#### Scenario: 完全一致
- **WHEN** specs/rules 集合与 INDEX 托管块之外已列条目完全一致
- **THEN** 报告输出「一致，无差异」标记，退出码 0

#### Scenario: 不误纳 sdflow-init 托管块条目
- **WHEN** `INDEX.md` 的 `opsx-init:rules` 托管块内列出 workflow bundle 条目（如 `trigger-catalog`），而 `openspec/rules/trigger-catalog.md` 不存在
- **THEN** 报告 MUST NOT 把托管块内条目当「已删未清理」——托管块被整段跳过，不产生该误报

### Requirement: CLAUDE.md 过时引用扫描

`maintain_scan.py` SHALL 扫描根 `CLAUDE.md` 与各子目录 `CLAUDE.md`，报告其中引用了**已从文件系统删除**的 spec/rule 路径的位置（文件 + 行号），仅报告不修复。

#### Scenario: CLAUDE.md 引用已删 spec
- **WHEN** 某 `CLAUDE.md` 含指向 `openspec/specs/gone/` 的引用，但该 spec 已删
- **THEN** 报告「过时引用」小节列出该 `CLAUDE.md` 路径 + 行号 + 被引的已删条目名

#### Scenario: 无过时引用
- **WHEN** 所有 CLAUDE.md 引用的 spec/rule 路径均存在
- **THEN** 报告「过时引用」小节为空/标记无

### Requirement: workflow bundle 陈旧遮蔽兜底扫描

`maintain_scan.py` SHALL 检查 `openspec/workflow/` 下是否残留规则文件本体（判据 = `RULE_MARKERS`：`workflow.md` / `spec-checklists` / `code-checklists` 任一存在，及仓根 `hack/checkpoint-commit.sh` 孤儿副本），命中则报告为「陈旧遮蔽」告警——因规则真相源应为全局 canonical，仓内残留规则副本会 pin 遮蔽全局。仅报告不删除。judgement（是否删/pin）留人。此为 sdflow-init `stale_shadow_warnings` 的**周期性兜底消费者**（init 的检查只在 init/update 动作时跑）。〔grill-amendment〕

#### Scenario: workflow 下残留规则正文
- **WHEN** `openspec/workflow/workflow.md`（规则本体）存在
- **THEN** 报告「陈旧遮蔽」小节列出该残留文件，提示可能 pin 遮蔽全局 canonical

#### Scenario: workflow 仅剩 tools
- **WHEN** `openspec/workflow/` 下只有 `tools/`，无规则正文
- **THEN** 「陈旧遮蔽」小节为空/标记无

### Requirement: 跨脚本共享判据一致性守卫

maintain_scan 与 sdflow-init 共享两组判据常量（`RULE_MARKERS` 陈旧遮蔽判据、`MARK_IDX` 托管块 marker）。canonical 定义留 `sdflow-init/scripts/init.py`；maintain_scan 保自包含副本（跨 skill import 破自包含且运行时脆）。为堵漂移（T17），pytest MUST 机验两处相等——不等即 fail。此为 T17 的真闭合（机验同步，非物理单一源）。〔grill-amendment〕

#### Scenario: RULE_MARKERS 与 init 不一致
- **WHEN** `maintain_scan.RULE_MARKERS != init.RULE_MARKERS`（有人只改了一处）
- **THEN** 一致性守卫 pytest 失败（非零），CI/手动跑测即暴露漂移

#### Scenario: 托管块 marker 与 init 不一致
- **WHEN** maintain_scan 用的 `opsx-init:rules` marker 字符串 != `init.MARK_IDX`
- **THEN** 一致性守卫 pytest 失败，防边界判据漂移致误纳/误跳托管块

### Requirement: 坏输入 fail-closed——重锚防假『一致』

`maintain_scan.py` MUST 在**解析不可信**时 fail-closed——响亮报错（stderr）+ 非零退出码，绝不带半信半疑的解析结果输出「一致」（该红报绿 = 假绿同构）。fail-closed 判据锚在**「防假一致」方向**，非机械纠结「空 vs 畸形」：结构骨架可信但读到 0 条 = 合法响亮态（报全新），不 fail。〔grill-amendment：重锚方向 + rules/ 可选〕

#### Scenario: INDEX.md 缺失
- **WHEN** `openspec/INDEX.md` 不存在
- **THEN** 脚本非零退出并在 stderr 说明缺失，不输出「一致」误判

#### Scenario: INDEX 结构不可信（防假一致）
- **WHEN** `INDEX.md` 存在但预期分节骨架整个缺失、或 `opsx-init:rules` 托管 marker 不配对、或表格行畸形到解析器无法确信读全
- **THEN** 脚本非零退出并报错「INDEX 结构不可信，拒绝输出一致」，绝不在此状态下判「无差异」

#### Scenario: INDEX 读到 0 条 spec 条目（合法响亮态）
- **WHEN** `INDEX.md` 结构完好但托管块之外无任何 spec 条目
- **THEN** 脚本退出 0，报告响亮列出全部 specs 为「新增未索引」（人可自纠），**不** fail-closed

#### Scenario: specs/ 目录缺失（fatal）
- **WHEN** `openspec/specs/` 目录不存在
- **THEN** 脚本非零退出并报错

#### Scenario: rules/ 目录缺失（可选，合法）
- **WHEN** `openspec/rules/` 目录不存在（可选目录，消费仓按需加）
- **THEN** 脚本按空集处理 rules 半场、退出 0（非错误），不与 specs 半场结果混淆

### Requirement: 只读且可观测

`maintain_scan.py` SHALL 只读运行——不创建、修改、删除任何文件；输出的差异报告 MUST 可观测（人可读、结构分类清晰），供 SKILL.md 步骤 4 由模型据此判断是否修复。判断（新 spec 归哪主题分组、是否修复 INDEX）留给模型，脚本不做。

#### Scenario: 运行后工作树无变更
- **WHEN** 在任意状态的仓库跑 `maintain_scan.py`
- **THEN** `git status` 显示脚本未产生任何文件变更（纯读）

#### Scenario: 报告分类可读
- **WHEN** 存在多类差异（新增未索引 + 已删未清理 + 过时引用 + 陈旧遮蔽）
- **THEN** 报告按四类分节呈现，每类列出具体条目，无需模型再手扫文件系统即可判断修复
