<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# gstack-review（广审）— ship-gate-hardening-2

> **降级声明**：autoplan 是 gstack **plan-file** 评审工具，对 OpenSpec 四件套不直接适配；本 Step1 广审由 fresh-context 子代理模拟 autoplan 的 CEO/design/eng/DX 四视角执行（mode="simulated"，非原生），MUST NOT 伪装原生。cross-model outside-voice 由 `outside-voice.sh`（codex，runner=codex）真实执行覆盖（见报告 Step2）。

## 广审 findings（CEO/design/eng/DX）

- **F1〔blocker·高〕协议套件 scope-check 漏权威源 producer 契约点**：design 的 scope-check 表只点 `sdflow-ship/SKILL.md`，漏了 **`sdflow-init/assets/workflow/workflow.md:74`**（CLAUDE.md 明定 bundle **唯一权威源**）与 `test_workflow_authority.py:16`（钉死旧 token `task<N>-`）。后果：本仓真实 dogfood 主路径经 workflow.md 手动编排，不同步改则该路径产的 task tag 恒裸格式 → **T32 对主用路径形同虚设**（A 自己 tag 裸 → 连同号裸污染都免疫不了）。
- **F2〔minor·中〕producer 指令无单一真相源**：同一条 checkpoint 派发文案分别硬编码在 SKILL.md + workflow.md 两处独立维护、无引用关系 → 本次实证会漏改。根因结构问题，建议记 todolist（超本 change 窄 scope）。

## 广审正向复核（无新问题的三视角）

- **CEO/scope**：T32 P2 降级 / T33 停置论证充分（adr/0008 + grill Q1 已封闭"独立分支纪律"自证陷阱）；Success Metrics M1-M4 可锚测，M4=328 与实测吻合。
- **design**：ADR-1 正则边界手工验算（裸/命名/含数字连字符名）均正确回溯；ADR-1 producer 零改经读 checkpoint-commit.sh 源码核实成立；decision-logic 图已含 `startswith` 放宽注记。
- **eng**：tasks 1.6/2.5 回归测试名全部存在于 test_gate_impl_progress.py（逐一核对）；M4=328 与 `pytest --collect-only` 吻合。

〔gstack-amendment：广审 F1/F2 已并入 spec-review-report.md 合并池；F1 触发 design/tasks scope-check 表 [spec-review-amendment] 补全权威源契约点〕
