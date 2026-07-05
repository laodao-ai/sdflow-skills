# Tasks — gate-checkpoint-hardening

> 规则/文案/注释/模板编辑 + `ship_gate.py`（TAG_RE 注释 + 熔断锚行比较 helper）+ `sdflow-done` merge untracked 检查 + 3 处测试加固。测试 = 既有 `sdflow-ship/tests` 零回归 + 新增回归断言。
> 每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。
> scope 边界〔grill Q5〕：不再 fold。spec-review 定稿：Q1=锚行集合判据+无状态 helper · Q2=merge 缩简版(只 untracked+halt)。

## 1. checkpoint 标签格式单源（T36 / SR-4 / SR-5）

- [ ] 1.1 接地核对 design ADR-4 锚族 A scope-check 表现状（TAG_RE / workflow.md / SKILL / spec / checkpoint-commit.sh）
- [ ] 1.2 T36 格式源：`ship_gate.py` TAG_RE 处加 canonical-shape 头注释（规范形状 + "格式权威在此、test_producer_parser_contract.py 钉一致、checkpoint-commit.sh 非源"）
- [ ] 1.3 T36 规则源：`workflow.md` 就地留规则一处（含格式串样例 + 标"权威见 TAG_RE"）；`sdflow-ship/SKILL.md` 改引用、删重复整句
- [ ] 1.4 **SR-5**：同步更新 `sdflow-ship/tests/test_workflow_authority.py:23`——原断言 SKILL 必含完整格式串，改为"workflow.md 含格式源/规则、sdflow-ship SKILL 只含引用且**不含**完整格式串"（否则 T36 与既有测试冲突）
- [ ] 1.5 **SR-4**：加人读串防漂移机械钩子——`TAG_RE` 定义旁 checklist 注释「改此正则先搜 workflow.md 格式串同步」+（可选）弱校验测试断言 workflow.md 该行不漂
- [ ] 1.6 机械核对：无第二份完整格式串复述；checkpoint-commit.sh 未被当格式源；test_workflow_authority 与新措辞一致
- [ ] 1.7 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task1-tag-format-single-source`

## 2. ship-gate 锚模板独占裸行（T43 / SR-6 / SR-10）

- [ ] 2.1 `sdflow-spec-review/SKILL.md:102` design-approved 锚去反引号、改独占裸行
- [ ] 2.2 `sdflow-code-review/SKILL.md:149-150`：pass/blocked 两锚各自的同行尾注移出锚行——**SR-10：pass→"建议进"、blocked→"存在未解 blocker" 语义不同，各锚配各注（注+锚 或 锚下另起行），MUST NOT 照 verify 合并成共享单脚注**
- [ ] 2.3 核验 `sdflow-done/SKILL.md:80-81` verify 锚已独占裸行（记录确认，不改）
- [ ] 2.4 **SR-6**：`sdflow-ship/tests/test_anchor_contract.py` 由子串 `a in text` 改为**逐行 `line.strip()==anchor`** + 断言锚行无反引号、无同行尾注（否则坏模板照过、修复无守卫会回归）
- [ ] 2.5 机械核对：三 SKILL 的 `<!-- ship-gate: -->` 锚 grep 出来均 `strip()` 后等值锚字面
- [ ] 2.6 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task2-anchor-bare-line`

## 3. gate 新鲜度 committed-only + merge untracked 硬检查（T35 / SR-2 缩简版）

- [ ] 3.1 `ship_gate.py` 新鲜度注释（原 T33 停置处）更新为定夺：committed-only 正式化 + 理由，无逻辑变更
- [ ] 3.2 `sdflow-ship/SKILL.md` 收尾段加非门禁软提示（工作树有未提交非-openspec 改动时告知"gate 判定不含它们"，不改退出码）
- [ ] 3.3 `sdflow-done/SKILL.md` merge 步加硬检查：**只查「本 change 分支生命周期内新产生的 untracked 文件」** → **halt+报告（非交互）停下上抛人工**（复用既有 halt 惯用法，**MUST NOT AskUserQuestion**）；判据排除仓库既有 debris
- [ ] 3.4 跑 `pytest sdflow-ship/tests/` 确认零回归
- [ ] 3.5 关账：T33/T35 gate 侧 → WONTDO 附理由；软提示+untracked 检查落 SKILL 记 DONE；**codex-2 tracked 路径已 defer todolist（本 change 不做）**
- [ ] 3.6 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task3-freshness-and-untracked-guard`

## 4. gate 熔断锚行集合判据 + 无状态 helper（T26 / SR-1）

- [ ] 4.1 实现**无状态锚行比较 helper**（`ship_gate.py` 子命令或小脚本）：输入两次锚行快照作参数、输出 bool（集合是否变化），**不落地任何文件、不跨 invocation 持久化**
- [ ] 4.2 `sdflow-ship/SKILL.md` 熔断条款改：判据 = 该步 ship-gate 锚行集合无净变化即判无进展熔断；**HEAD 移动/mtime 变化 MUST NOT 作免疫信号**；fail-safe 快照缺失保守判无进展；仅有锚报告步（STEP_IN_PROGRESS/RERUN_STALE）适用
- [ ] 4.3 **加 CI 测试**：helper 对"锚行集合未变"判无进展、对"新增结论锚"判有进展；覆盖 fail-safe 快照缺失分支
- [ ] 4.4 关账：T26 → 已探索·产出「锚行集合判据+无状态 helper」·持久化 defer（撞三红线，登记接受取舍）
- [ ] 4.5 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task4-breaker-anchor-set`

## 5. spec delta 对码核验 + 校验（含 SR-3 MODIFIED）

- [ ] 5.1 按实现实况核 `specs/spec-workflow/spec.md` 的 3 条 ADDED + 1 条 MODIFIED 需求与代码/文案一致；**verify 显式核 MODIFIED 块——归档后主 spec:517 `<当前change>` 已被同步为 `<change-slug>`（作可核验锚点）**
- [ ] 5.2 `openspec validate gate-checkpoint-hardening` 通过
- [ ] 5.3 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task5-spec-verify`

## 6. 部署 + 全量验证

- [ ] 6.1 开发 checkout 跑 `bash setup.sh`（改 assets/workflow 才让全局 canonical 生效、测得到）
- [ ] 6.2 `resolve-workflow.sh` 解析确认 canonical 指向本 checkout；抽查 workflow.md 改动经全局生效
- [ ] 6.3 全仓 `pytest` 确认零回归
- [ ] 6.4 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task6-deploy-verify`
