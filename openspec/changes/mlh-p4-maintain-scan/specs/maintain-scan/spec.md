## ADDED Requirements

### Requirement: specs/rules ↔ INDEX 双向 set-diff

`maintain_scan.py` SHALL 扫描 `openspec/specs/` 下所有 `spec.md` 与 `openspec/rules/` 下所有 `.md`，解析 `INDEX.md` 已列出的表格条目，产出双向 set-diff 只读报告，分两类：**新增未索引**（文件系统存在、INDEX 未列）与 **已删未清理**（INDEX 列出、文件系统不存在）。脚本 MUST NOT 修改任何文件。

#### Scenario: 文件系统有新 spec 未进 INDEX
- **WHEN** `openspec/specs/foo/spec.md` 存在但 `INDEX.md` 未列 `foo`
- **THEN** 报告在「新增未索引」类下列出 `foo`（spec 类），退出码 0（有差异不算错误）
- **AND** `INDEX.md` 与文件系统内容保持不变（脚本零写）

#### Scenario: INDEX 列了已删除的 rule
- **WHEN** `INDEX.md` 列出 rule `bar` 但 `openspec/rules/bar.md` 不存在
- **THEN** 报告在「已删未清理」类下列出 `bar`（rule 类）

#### Scenario: 完全一致
- **WHEN** specs/rules 集合与 INDEX 已列条目完全一致
- **THEN** 报告输出「一致，无差异」标记，退出码 0

### Requirement: CLAUDE.md 过时引用扫描

`maintain_scan.py` SHALL 扫描根 `CLAUDE.md` 与各子目录 `CLAUDE.md`，报告其中引用了**已从文件系统删除**的 spec/rule 路径的位置（文件 + 行号），仅报告不修复。

#### Scenario: CLAUDE.md 引用已删 spec
- **WHEN** 某 `CLAUDE.md` 含指向 `openspec/specs/gone/` 的引用，但该 spec 已删
- **THEN** 报告「过时引用」小节列出该 `CLAUDE.md` 路径 + 行号 + 被引的已删条目名

#### Scenario: 无过时引用
- **WHEN** 所有 CLAUDE.md 引用的 spec/rule 路径均存在
- **THEN** 报告「过时引用」小节为空/标记无

### Requirement: workflow bundle 陈旧遮蔽兜底扫描

`maintain_scan.py` SHALL 检查 `openspec/workflow/` 下是否残留规则文件本体（如 `workflow.md` 等规则正文，而非仅 `tools/`），命中则报告为「陈旧遮蔽」告警——因规则真相源应为全局 canonical，仓内残留规则副本会 pin 遮蔽全局。仅报告不删除。

#### Scenario: workflow 下残留规则正文
- **WHEN** `openspec/workflow/workflow.md`（规则本体）存在
- **THEN** 报告「陈旧遮蔽」小节列出该残留文件，提示可能 pin 遮蔽全局 canonical

#### Scenario: workflow 仅剩 tools
- **WHEN** `openspec/workflow/` 下只有 `tools/`，无规则正文
- **THEN** 「陈旧遮蔽」小节为空/标记无

### Requirement: 坏输入 fail-closed

`maintain_scan.py` MUST 在无法可靠完成扫描的坏输入下 fail-closed——响亮报错（stderr）+ 非零退出码，绝不静默把「解析失败」当作「无差异」。

#### Scenario: INDEX.md 缺失
- **WHEN** `openspec/INDEX.md` 不存在
- **THEN** 脚本非零退出并在 stderr 说明缺失，不输出「一致」误判

#### Scenario: INDEX.md 表格畸形不可解析
- **WHEN** `INDEX.md` 存在但表格结构畸形无法解析出条目
- **THEN** 脚本非零退出并报错，不把畸形静默当作「空 INDEX → 全部新增」

#### Scenario: specs/rules 目录缺失
- **WHEN** `openspec/specs/` 或 `openspec/rules/` 目录不存在
- **THEN** 脚本非零退出并报错（区分「目录缺失」与「目录存在但空」）

### Requirement: 只读且可观测

`maintain_scan.py` SHALL 只读运行——不创建、修改、删除任何文件；输出的差异报告 MUST 可观测（人可读、结构分类清晰），供 SKILL.md 步骤 4 由模型据此判断是否修复。判断（新 spec 归哪主题分组、是否修复 INDEX）留给模型，脚本不做。

#### Scenario: 运行后工作树无变更
- **WHEN** 在任意状态的仓库跑 `maintain_scan.py`
- **THEN** `git status` 显示脚本未产生任何文件变更（纯读）

#### Scenario: 报告分类可读
- **WHEN** 存在多类差异（新增未索引 + 已删未清理 + 过时引用 + 陈旧遮蔽）
- **THEN** 报告按四类分节呈现，每类列出具体条目，无需模型再手扫文件系统即可判断修复
