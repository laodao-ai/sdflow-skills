<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review — gate-anchor-line-scoped（Step1 广审·原生）

> 执行方式：主 session **原生广审**（非子代理转述模拟）。autoplan 是 gstack plan-file 流水线、与 OpenSpec change dir 不直接契合，故按 sdflow-spec-review 定位由主 session 原生跑 design/eng/CEO 镜（DX 镜不适用——本 change 无用户可见面）。侧信道佐证：本文件由主 session 直接 Write，非 subagent 读 SKILL.md 模拟；codex 双声经 outside-voice.sh 独立跑（见 spec-review-report Step1.5 锚行）。

## 广审 findings（纳入 Step3 合并池）

- **BR-1〔design·中〕TG 头注误标**：proposal 头把本 change 标 `〔TG-01：工具链〕`，但 trigger-catalog 的 **TG-01 = 后端服务变更**（→ backend 领域）。本 change 是元仓 Python gate 脚本，**不命中任何技术栈 TG（01/02/03）**。命中的是 TG-25（契约套件）/23（≥2 方案）/22（未验证前提）/18（测试计划）/12（决策逻辑）。建议改 proposal 头 TG 标注、去掉 TG-01。证据 proposal.md:3。
- **BR-2〔eng·高〕task 2.1 测试落法与被测函数签名不符**：`archived_verify_state(root, ref, archive_dir)` **不接受文本**——它内部 `git show <ref>:openspec/changes/archive/<dir>/verify-report.md` 取 `out` 再判。tasks.md 2.1 写「造一份 archived verify-report.md 文本 → 断言 archived_verify_state 判 none」落不了地（没有传文本的入口）。**修向**：把文本级断言测 `_line_scoped_hits(out_text, [...])` 直接（单元），archived_verify_state 的端到端另用 git fixture（commit 一个 archive 目录到临时 repo）覆盖。证据 ship_gate.py:139-146 / tasks.md 2.1。
- **BR-3〔design·中〕fence-aware 自指风险（操作性）**：`anchors_in` 对 spec-review-report.md 查 design-approved 时，报告本身含 ``` 决策登记区块。若报告 fence **未闭合**，其后的真 design-approved 锚会被吞进 in-fence → 假 REFUSE_START。这不是代码 bug（失败到安全侧），但是**报告作者约束**：模板产报告须保持 fence 成对、锚在 fence 外。建议在 ship_gate 头注释/模板侧记一句，且本 change 自己的 spec-review-report.md MUST fence 平衡 + 锚独占行在所有 fence 外。
- **BR-4〔CEO·低·正向〕scope 纪律良好**：line 237 `"TG-02" in ...`（触发标签检测、故意子串）被显式排除、未误纳入；折入的只有真属同 bug 类的 line 143。scope 收敛得当，无漂移。
- **BR-5〔design·低〕返回契约保持**：`_line_scoped_hits` 返回 `[a for a in candidates if a in hit]`（候选原序去重）与旧 `anchors_in` 逐字一致；下游 `pick_exclusive` 用成员判定（序无关）。无回归，登记备核。

## 自动决策（登记进 spec-review-report 决策区）
- 无高杠杆自动决策改动；BR-1/BR-2/BR-3 作 amendment 候选交 Step3 裁决。
