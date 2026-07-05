---
name: sdflow-maintain
description: 扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。Trigger with /sdflow-maintain。
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
   - **workflow bundle 陈旧遮蔽兜底扫描**：检查 `openspec/workflow/` 下是否残留规则文件本体（`workflow.md` /
     `spec-checklists/` / `code-checklists/` 任一存在），及仓根 `hack/checkpoint-commit.sh` 孤儿副本。
     发现 workflow 规则文件本体，输出与 `sdflow-init update` 同款告警："遮蔽全局且不再被刷新：删=跟全局 /
     留=显式 pin"；发现 checkpoint 孤儿副本，对称提示："删=用全局 ~/.sdflow/hack/ / 本地 workflow.md 副本
     （pin）仍引用它则勿删"。**只报告绝不删**。

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

5. **lens-metric 度量 surfacing 检查（机械收尾步，独立于 INDEX 差异，防死列 SR-A）**

   本步与上面 INDEX 修复流程无关、无条件跑在**每次维护会话最后**（无论步骤 4 是否有修复）。

   - **config 门控**：读 `openspec/config.yaml` 的 `metrics.enabled`——缺省或 `false` → 跳过本步（不执行、不提示）。
   - 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示"resolve-workflow.sh 未安装——先在运行
     checkout（`~/.skills/sdflow-skills`）跑 `bash setup.sh`"并跳过本步；否则
     `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 →
     原样转发脚本 stderr 告警并跳过本步（绝不静默，也不阻塞整个 `/sdflow-maintain`）；成功 → 聚合器路径 =
     `$RULES_ROOT/tools/lens_metric_aggregate.py`（本仓源仓可直接是 `sdflow-init/assets/workflow/tools/` 下的同一份）。
   - 跑 `python3 <聚合器路径> --root "$(git rev-parse --show-toplevel)"`（只读，不写任何文件，见聚合器契约
     `sdflow-init/assets/workflow/lens-metric-contract.md`）。
   - 扫描输出多列表的 `flag` 列，把命中 `≥10待复评`（**出现轮数 ≥10 的镜**）的每一行单独摘出，在**本次维护
     报告的最后**用独立、显眼的区块呈现——**MUST NOT** 与上方 INDEX 差异报告混排、**MUST NOT** 折叠进长段落
     或被前面内容淹没（呼应 grill-not-skippable：待办判定不能埋在长消息里）：

     ```
     ⚠️ 度量待复评（N 项，出现轮数≥10）——只提示不判断、不自动砍，人读表后自行决定保留/降采样/收紧触发/淘汰：
       - {layer}/{lens}({site}) 出现轮数={轮} 采纳率={..} 独立率={..}
       …
     ```

   - 无命中（表格为空或全部 <10 轮）→ 同样输出一行「度量表：无 ≥10 待复评项」，不省略（防止用户以为本步没跑）。
   - **只提示不判断、不自动砍**：本步 MUST NOT 建议或执行降采样/淘汰/收紧触发——决策交人（消费见
     `sdflow-code-review/SKILL.md` 反馈条款）。聚合器本身零新持久态（view-only、可重生），本步同样**不新增任何
     "已复评"登记文件**——每次维护重新聚合、重新呈现是预期行为（幂等重复提示，代价远低于死列风险）。

**护栏**

- **禁止修改 CLAUDE.md** — 不管是根目录还是子目录的 CLAUDE.md，都只报告不修改
- **只修改 INDEX.md** — 修复范围严格限定在 `openspec/INDEX.md` 一个文件
- **所有修改必须经用户确认** — 不自动修复，先报告再询问
- **步骤 5（lens-metric surfacing）只读不写** — 不产生任何文件改动、不算作"修复"，不受上面「只修改
  INDEX.md」的例外覆盖；只提示不判断，砍镜/降采样决策一律交人
