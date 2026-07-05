# gate-anchor-line-scoped — Proposal

〔TG-25：契约套件（锚检测负例）〕〔TG-23：≥2 方案（锚检测方式）〕〔TG-22：未验证前提（锚行独占一行）〕〔TG-18：测试计划〕〔TG-12：决策逻辑（门禁判定）〕 — 技术栈 TG-01/02/03 **均不命中**（元仓 Python gate 脚本，非后端服务/嵌入式/前端）〔spec-review-amendment BR-1〕；HR-TG 子集命中 = none

## Why

`ship_gate.py` 的 `anchors_in()`（`:198-203`）用**纯子串** `a in text` 判断 `<!-- ship-gate: design-approved -->` 等机判锚是否存在。子串匹配会把报告正文里对锚的**描述性提及**误判为真锚——哪怕前后文明说「未获批 / 故意不写」。

**活体复现（本仓 · 元 bug）**：`checkpoint-tag-single-source` 的 `spec-review-report.md` 第 85 行是一句描述句（形如「拍板发生后才写 \`<!-- ship-gate: design-approved -->\`（当前故意不写——设计未获批）」），无任何独占一行的锚（`grep -n "^<!-- ship-gate: design-approved -->"` 空），但 `grep -c "ship-gate: design-approved"` = 1。gate 首跑即凭这句子串命中判「设计已批」→ 返回 `RUN_PLAN`，让该 change 在设计门**实际未过**（报告明写「修订版须回设计门再过一次」）时越过 adr/0004 红线起跑。已记 buglist **B4（P1）**。

这是门禁自身的正确性缺陷，且**不止一处**〔grill 证伪初稿「anchors_in 唯一入口」〕：①`anchors_in`（`:198`）服务设计门 / verify / code-review 锚检测；②`archived_verify_state`（`:143`）**另用裸子串** `ANCHOR_VERIFY_PASS in out` 查 git-show 出的归档 verify-report.md，**不经 anchors_in**——同一 bug 类，归档 verify 描述性提及 `verify=PASS` 而无真锚 → 可致**假 SHIPPED**。穷举确认锚检测**仅此两处**（`:237` 的 `"TG-02" in` 是触发标签、非 ship-gate 锚，故意子串，不动）。gate 的存在意义就是堵假✅，此洞直接侵蚀设计门与 SHIPPED 两道判定，值得在一个窄 change 内把**锚检测 bug 类**根治（非只补单实例）。

## What Changes

- **锚检测从子串升级到行锚定 + fence-aware，两处解析点统一到共用核心**〔grill Q1〕：抽文本级核心 `_line_scoped_hits(text, candidates)`——候选锚 MUST 以**独占一行**出现（`line.strip() == anchor` 整行字面等值，非子串）且**忽略 fenced code block（\`\`\`）内的行**；`anchors_in`（读文件）与 `archived_verify_state`（`:143`，git-show 文本）**都改走此核心**（后者三态 `conflict`/`pass`/`none` 返回逐字不变，只换检测维）。保留「字面查找（非正则）」精神：行级用等值比较，无需正则。
- **新增锚检测负例矩阵**（`sdflow-ship/tests/`）：断言一组 MUST NOT match 的报告文本——①锚**内联**在描述句中（前后有其它字符）→ 不命中；②锚在 \`\`\` 代码块内独占一行 → 不命中；③锚在行内反引号 span 中 → 不命中。正例回归：模板真产的独占一行锚（前后可有空白）→ 命中。冲突检测回归：`verify=PASS` 与 `verify=FAIL` 各独占一行并存 → 两者皆命中 → 仍判 UNKNOWN。
- **零行为外扩**：退出码语义、锚字面集、JSON 字段均不变；仅把「命中」从子串收紧为行级等值（收敛假阳性，不新增放行路径）。真锚（模板产出）在新旧实现下都命中，无回归。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `spec-workflow`：收紧「阶段三编排台账确定性（ship_gate）」需求中「gate 以字面查找（非正则）解析」一句——锚检测 MUST 为**行级整行等值 + 忽略 fenced code block**，MUST NOT 用纯子串（描述性提及/代码块内示例不得触发门禁）。既有锚字面集、冲突判 UNKNOWN、退出码语义不变。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（抽 `_line_scoped_hits` 文本核心；`anchors_in`（`:198`）+ `archived_verify_state`（`:143`）改走核心 + 头注释契约表锚检测语义一句）。
- **测试**：`sdflow-ship/tests/`（新增锚检测负例/正例锚测 + archived verify 描述性 PASS 负例；`test_gate_terminal.py` / 设计门相关既有用例回归）。
- **技术栈**：纯 Python 编排脚本 + pytest，不命中 TG-01/02/03 任何领域清单（backend·go / embedded / frontend 均不适用）。
- **下游**：`/sdflow-ship` 编排 skill 的所有未来运行；`anchors_in` 属 skill 本体，随 setup.sh symlink 即时生效，无需 sdflow-init update 推送。
- **不动**：完成判据（T32 命名空间 / T34 分段绑定 / B1 窗口 / B4 集合归属）、D3 归档终态、B2 豁免——`anchors_in` 与它们正交。

## Success Metrics

- **假命中收敛（两路径）** — 基准：B4 活体盘面（报告仅含描述性锚提及）首跑 `RUN_PLAN` 假过设计门 → 目标：同盘面判 `REFUSE_START`；归档 verify 描述性提及 PASS 不再 `has_pass=True` — 度量：负例用真实复现文本（内联锚句 + 代码块内锚）断言 `anchors_in`/`archived_verify_state` 不命中。
- **真锚零回归** — 基准：三模板产出的独占一行锚在旧实现命中（15 份归档报告实证锚均独占顶格）→ 目标：新实现仍命中、既有 gate 测试套全绿 — 度量：`pytest sdflow-ship/tests/` 通过数不降 + 正例/冲突回归用例绿。

## 需求优先级〔TG-19〕

| 优先级 | 项 | 理由 |
|---|---|---|
| P1 | 锚检测行锚定 + fence-aware（`anchors_in` + `archived_verify_state`） | 设计门假过的元 bug，活体复现；两处锚检测点的假阳性直穿设计门与 SHIPPED 两道判定 |
| P2 | 头注释契约表锚检测语义同步 | 防文档与实现漂移，随修不独立成活 |

## 假设〔TG-22〕

- **机判锚在合法报告中始终独占一行**：三个生成模板（sdflow-spec-review 拍板回写 / sdflow-done verify / sdflow-code-review 报告）均把锚写在**自己一行**（「结论区末行为机器锚行」「结论行下方紧跟机器锚行」）。行级等值判据信任此约定；若某模板未来把锚与其它文本同行输出，则该锚在新实现下不再命中——由锚检测契约测试（模板产出样本 ↔ `anchors_in` 命中）兜底钉死，模板改动同批更新。
- **fenced code block 以 \`\`\` 成对切换**：fence 追踪沿用 T34 `checkbox_done_ids` 已验证的整文 fence 状态扫描惯例（`~^\s*\`\`\`~` 计数奇偶），不引新解析器。
