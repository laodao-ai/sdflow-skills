---
name: opsx:maintain
description: 扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。
license: MIT
compatibility: 需要 openspec 目录结构（openspec/specs/、openspec/rules/、openspec/INDEX.md）。
metadata:
  author: opsx
  version: "1.0"
---

扫描 openspec 目录，对比 INDEX.md，报告差异，经确认后修复。

**触发时机**：归档变更后、手动增删 spec 后、合并上游更新后。

**步骤**

1. **扫描文件系统**

   扫描 `openspec/specs/` 下所有 `spec.md` 文件和 `openspec/rules/` 下所有 `.md` 文件，收集当前存在的 spec 和 rule 列表。

   对于 specs：从目录名提取名称（如 `openspec/specs/cache/spec.md` → `cache`）
   对于 rules：从文件名提取名称（如 `openspec/rules/database.md` → `database`）

2. **解析 INDEX.md**

   读取 `openspec/INDEX.md`，解析所有 markdown 表格行，提取已列出的 spec 和 rule 名称。

   解析范围：
   - 「设计强制规范」段落中的 rules 表格
   - 各主题分组中的 specs 表格
   - 「代码路径速查」表格中引用的所有名称

3. **对比并生成报告**

   对比扫描结果与 INDEX.md 已列条目，按以下类别报告差异：

   - **新增未索引**：文件系统中存在但 INDEX.md 中未列出的 spec/rule
   - **已删未清理**：INDEX.md 中列出但文件系统中不存在的 spec/rule
   - **代码路径缺失**：新增的 spec/rule 在代码路径速查表中没有对应映射

   如果无差异，输出 "INDEX.md 与文件系统一致，无需更新" 并结束。

   额外检查（仅报告，不修复）：
   - 扫描根 CLAUDE.md 和子目录 CLAUDE.md，检查是否引用了已删除的 spec 或 rule 路径
   - 如果发现过时引用，在报告中标注 "CLAUDE.md 中可能存在过时引用：xxx"

4. **询问用户是否修复**

   显示报告后，使用 AskUserQuestion tool 询问用户是否执行修复。

   **如果用户确认**：
   - 新增未索引的条目：添加到 INDEX.md 对应主题分组表格
     - 对于新 spec：根据 spec 文件内容推断所属主题分组，无法推断时询问用户
     - 对于新 rule：添加到「设计强制规范」表格
   - 已删未清理的条目：从 INDEX.md 所有表格中移除
   - 代码路径缺失的映射：根据 spec 内容推断代码路径，添加到速查表
   - 修复后显示变更摘要："已更新 INDEX.md：+N -M"

   **如果用户拒绝**：输出 "跳过修复" 并结束。

**护栏**

- **禁止修改 CLAUDE.md** — 不管是根目录还是子目录的 CLAUDE.md，都只报告不修改
- **只修改 INDEX.md** — 修复范围严格限定在 `openspec/INDEX.md` 一个文件
- **所有修改必须经用户确认** — 不自动修复，先报告再询问
