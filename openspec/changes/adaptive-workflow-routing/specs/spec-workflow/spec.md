# Spec Delta — spec-workflow

## MODIFIED Requirements

### Requirement: sdflow-code-review 强制主审，两层深度按逻辑面自适应

阶段三的 `sdflow-code-review` MUST **每次必跑**、以独立冷视角作强制代码评审主审，MUST **恒产 code-review-report.md**，SHALL NOT 跳过代码评审。深度按**两层**规则（承实测硬化，**非**「只高风险才跑」的边际抽查）：

- **Step1（gstack/review：scope-drift + 计划完成度）MUST 每次必跑**，MUST NOT 因任何路由判定降级或跳过——它既是便宜的评审地板，又是**验「平凡」诚实性的守卫**（自称无逻辑面的 diff 若偷藏逻辑改动，scope-drift 抓）。
- **Step2（多镜 fan-out：领域镜+对抗镜+历史镜+置信过滤+对抗裁决）MUST 对任何含行为/逻辑面的 change 每次全跑**（依据实测能抓 controller 说服放过的真问题）；**仅当** change 匹配「通用平凡形状白名单」（注释/文档-only · tests/-only · 版本常量-only，**机判无逻辑面**，多镜结构上零产出）时**可免 Step2**。此免除 MUST 由 Step1 scope-drift 守卫：scope-drift 若揭出隐藏逻辑改动 → 白名单形状声明作废 → Step2 照跑。**默认开**（有逻辑必跑多镜），仅机判无逻辑面才关，MUST NOT 以「风险高低」判断作为 gate-off Step2 的依据。

#### Scenario: 有逻辑面的普通变更 Step2 多镜照跑
- **WHEN** 一个 HR-TG∅、有先例、routine 但**含逻辑改动**的变更完成实现
- **THEN** sdflow-code-review 的 Step1 与 Step2（多镜 fan-out）均 MUST 全跑，MUST NOT 因判定「routine/平凡」而免多镜

#### Scenario: 白名单无逻辑面形状免 Step2 但 Step1 恒跑
- **WHEN** 一个 diff 仅动注释/文档行（匹配白名单形状、机判无逻辑面）的变更
- **THEN** Step1（scope-drift+完成度）MUST 跑；确认无隐藏逻辑后 Step2 多镜可免（结构零产出），仍产 code-review-report.md，MUST NOT 跳过 Step1

#### Scenario: scope-drift 揭穿伪装的白名单形状
- **WHEN** 某 change 自称「仅改注释」但 Step1 scope-drift 揭出其顺手改了逻辑
- **THEN** 白名单形状判定 MUST 作废、Step2 多镜 MUST 照跑，MUST NOT 凭作废的形状声明免多镜

#### Scenario: 命中 HR-TG 的变更强制两层全跑
- **WHEN** 一个命中 HR-TG（如 TG-27 改 gate/bundle 自身）的变更完成实现
- **THEN** sdflow-code-review MUST 全跑 Step1 + Step2 多镜 fan-out，MUST NOT 免任何一层

## ADDED Requirements

### Requirement: 设计门核平凡声明与脚本硬信号一致

阶段二设计门 SHALL 在放行任何轻量化路径前，核对 ff 产物的**平凡声明**与确定性脚本的 L0/L1 硬信号（HR-TG 命中集 / 变更面 / 开放决策 / 先例）。声明与硬信号一致方可放行轻量化；矛盾（声明平凡但脚本命中 HR-TG 或面超阈）MUST 拒并点名冲突项。此核验为**新增门禁项**，MUST NOT 削弱既有设计门红线（承 adr/0004）。

#### Scenario: 声明平凡但脚本命中 HR-TG 被设计门拒
- **WHEN** 某 change 的平凡声明称 HR-TG∅，但脚本算出命中 TG-27
- **THEN** 设计门 SHALL 判矛盾、拒绝轻量化放行、点名 TG-27 冲突，MUST NOT 采信声明越过脚本硬信号
