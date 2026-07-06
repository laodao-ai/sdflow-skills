# Proposal — adaptive-workflow-routing

> 〔设计门 Q1=A 收敛，2026-07-06〕本 change 原为「workflow 深度自适应大机制」，经 spec-review 4 冷源审出**地基级问题**（前向机制在 diff 前的阶段不可机判、HR-TG 不可脚本化、门核正交、ROI 被 D4/D6 抽空），设计门裁定**收敛为最小安全子集**：仅在 code-review 入口机判「无逻辑面白名单形状」免 Step2 多镜。**名保留、scope 大幅收窄。**

## Why

现 `sdflow-code-review` 每次全跑多镜 fan-out（领域+对抗+历史）。对**结构上无行为面**的 diff（纯注释/文档、仅加测试、纯展示版本号），多镜**跑了也必然零产出**——白付 N 个 fresh 子代理的成本。把这类**机判可靠、语义面为空**的形状免掉 Step2，是「安全的省」的最大诚实子集：零语义风险、无需前向路由/无需自评/无需校准。

（原设计想覆盖更广的「有逻辑面 routine change」轻量化，但冷审证明那在 diff 前不可机判、且收益被 grill/code-review 不可跳的既有约束抽空——已放弃，见 `spec-review-report.md` 决策登记区 Q1。）

## What Changes

- **MODIFIED（spec 级，沿用原需求标题）**：`sdflow-code-review 为每次全跑` 精确化为**两层**——**Step1（scope-drift+完成度）恒跑**（评审地板 + 验白名单诚实性的守卫）；**Step2（多镜 fan-out）对任何有逻辑面的 change 全跑，仅机判命中「无逻辑面白名单形状」时可免**。**默认开、仅机判无逻辑面才关**，非「高风险才跑」。
- **无逻辑面白名单形状**（机判、post-diff、确定性脚本、语言感知）：①仅动注释/纯文档行；②仅新增 `tests/` 下文件（排除被生产码 import 的 helper）；③仅改无 code-path 依赖的纯展示版本常量（整行匹配、拒附加 token）。
- **行为面路径豁免清单**：diff 触及 workflow bundle 自身（`assets/workflow/**`、编排/评审 `SKILL.md`、`ship_gate.py`、`workflow.md`、判器脚本）即 NOT 无逻辑面——**bundle markdown 承载行为**（吸收原 TG-27 元层护栏，且与部署无关，硬编码路径前缀）。
- **判器脚本**：`assets/workflow/tools/` 下新增无逻辑面形状判器，沿 `ship_gate.py` 纪律（只读/git-harden/双输出）；`sdflow-code-review/SKILL.md` Step2 前调用它。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `spec-workflow`: 「sdflow-code-review 为每次全跑的独立强制主审」需求精确化为两层深度（Step1 恒跑 + Step2 仅无逻辑面白名单免）。**非 BREAKING**——不变式「code-review 必跑、有逻辑必多镜」完整保留，仅对结构零产出形状免多镜。

## Impact

- **规则/需求**：`spec-workflow` delta（code-review 两层）。
- **脚本（新）**：`assets/workflow/tools/` 无逻辑面形状判器（语言感知 + 行为面路径豁免）+ pytest。
- **编排 SKILL**：`sdflow-code-review/SKILL.md` Step2 前调判器。
- **吸收 issues**：无（原吸收的 T9/T28/T19 属前向机制，已随 Q1=A 放弃；相关想法留 todolist）。
- **部署**：属 bundle 权威源改动，merge 后 push → 运行 checkout `/sdflow-upgrade` 激活。

## Success Metrics

1. 纯注释/文档 diff、仅加测试、纯版本号三类形状的 change 免 Step2 多镜（可测：给三类样本 diff，判器命中、Step2 不 fan-out、仍产报告）。
2. **反误免**：改 `SKILL.md`/`workflow.md`/`ship_gate.py` 一行（形状似 markdown-only）**不**被误判无逻辑面（行为面路径清单命中→Step2 照跑）；load-bearing 版本常量不免（可测）。
3. Step1 恒跑守卫有效：伪装成「仅注释」但含逻辑的 diff 被 scope-drift 揭穿 → Step2 照跑（可测）。

## Non-Goals

- 不做前向自适应路由 / 非平凡四谓词 / 平凡声明 / HR-TG 双向化 / route.py-at-ff / 托管块驱动 / 后向 calibrator（Q1=A 全部放弃）。
- 不轻量化 grill（不可自动跳，承 `grill-not-skippable`）、不轻量化 spec-review、不放松 done。
- 判器 MUST NOT 依作者自评——纯机判 diff 形状。

## Compliance

- 承 adr/0004：不削弱设计门红线（本 change 只动 code-review Step2 深度，Step1 恒跑、有逻辑必多镜）。
- 承 spec-workflow「code-review 每次全跑」的实测硬化：不变式保留，仅对**机判证明零产出**的形状免多镜——非「高风险才跑」。
- 承 `grill-not-skippable`：grill 不在本 change 触碰。
