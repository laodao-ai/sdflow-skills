# Spec Delta — spec-workflow

> 〔设计门 Q1=A 收敛〕本 change 从「前向自适应路由大机制」收敛为**仅** code-review 入口的无逻辑面白名单豁免。故只保留对 code-review 需求的一处 MODIFIED，**沿用原需求标题**（保 OpenSpec MODIFIED 定位）。

## MODIFIED Requirements

### Requirement: sdflow-code-review 为每次全跑的独立强制主审

阶段三的 `sdflow-code-review` MUST **每次必跑**、以独立冷视角作为强制代码评审主审（依据实测能抓真问题），MUST **恒产 code-review-report.md**，SHALL NOT 跳过代码评审、SHALL NOT 降级为「高风险才跑的残差抽查」（**默认开、仅机判无逻辑面才关**，非风险判断 gate-on）。深度按**两层**规则：

- **Step1（gstack/review：scope-drift + 计划完成度）MUST 每次必跑**，MUST NOT 因任何判定降级或跳过——既是便宜的评审地板，又是**验白名单形状诚实性的守卫**（自称无逻辑面的 diff 若偷藏逻辑改动，scope-drift 抓）。
- **Step2（多镜 fan-out：领域镜+对抗镜+历史镜+置信过滤+对抗裁决）MUST 对任何含行为/逻辑面的 change 每次全跑**；**仅当** change 的 diff **机判命中「无逻辑面白名单形状」**时可免 Step2（多镜结构上零产出）。免除 MUST 由 Step1 scope-drift 守卫：scope-drift 揭出隐藏逻辑 → 白名单判定作废 → Step2 照跑。

**无逻辑面白名单形状**（机判、post-diff、由确定性脚本判，MUST NOT 依作者自评）SHALL 仅含：①`diff 仅动代码内注释行（语言感知）或约定文档文件`——约定文档**扩展名锚定**：`VERSION` / `README·CHANGELOG·LICENSE·NOTICE`（无扩展或 `.md/.rst/.txt`）/ `.rst` / `docs/` 下 `.md·.rst·.txt`；**裸 `*.txt` 不算文档**（`requirements.txt`/`runtime.txt` 等依赖 pin 是 load-bearing，落 NOT）、**`docs/` 下 `.py` 等源码不算文档**（按代码判定）、**任意其他 `.md`（消费仓散落 markdown 可能承载行为）默认 NOT**；②`diff 仅新增 tests/ 下文件`（排除 import 副作用 `conftest.py`/`__init__.py`）；③版本常量收窄为 `VERSION`/`CHANGELOG`（代码里的 `API_VERSION`/`SCHEMA_VERSION` 无法机判是否切 code-path → NOT）。判器 MUST **语言感知**（按语言解析注释/块注释/多行字符串边界，MUST NOT 裸正则前缀）；MUST 应用**行为面路径豁免清单**——凡 diff 触及 workflow bundle 自身（`sdflow-init/assets/workflow/**`、编排/评审 `SKILL.md`、`ship_gate.py`、`route`/判器脚本、`workflow.md`）即 NOT 无逻辑面（**这些 markdown/脚本承载行为，非文档**），即便 diff 形状看似「仅动 markdown」；`tests/` 豁免 MUST 排除被生产码 import 的 test helper（如 `conftest.py`）；版本常量 MUST 整行匹配 `^\s*<IDENT>\s*=\s*<version-literal>\s*$` 且拒绝任何附加 token（防夹带 `API_VERSION`/`SCHEMA_VERSION` 等切 code-path 的 load-bearing 常量）。

#### Scenario: 有逻辑面的普通变更 Step2 多镜照跑
- **WHEN** 一个含逻辑改动的变更完成实现（不匹配任何白名单形状）
- **THEN** sdflow-code-review 的 Step1 与 Step2 多镜 fan-out 均 MUST 全跑，MUST NOT 因「routine/低风险」而免多镜

#### Scenario: 纯注释/文档 diff 免 Step2 但 Step1 恒跑
- **WHEN** 一个 diff 仅动注释/纯文档行（语言感知判定、且不触行为面路径清单）的变更
- **THEN** Step1（scope-drift+完成度）MUST 跑；确认无隐藏逻辑后 Step2 多镜可免（结构零产出），仍产 code-review-report.md

#### Scenario: scope-drift 揭穿伪装的白名单形状
- **WHEN** 某 change 自称「仅改注释」但 Step1 scope-drift 揭出顺手改了逻辑
- **THEN** 白名单判定 MUST 作废、Step2 多镜 MUST 照跑

#### Scenario: 改 bundle/SKILL/gate 自身即便是 markdown 也不免多镜
- **WHEN** 一个 diff 只改 `sdflow-code-review/SKILL.md` 或 `workflow.md` 一行指令（形状=仅动 markdown）
- **THEN** 判器 MUST 因行为面路径豁免清单判其 NOT 无逻辑面 → Step2 多镜照跑，MUST NOT 因「仅动 markdown」误免（bundle markdown 承载行为）

#### Scenario: load-bearing 版本常量不免多镜
- **WHEN** 一个 diff 改 `API_VERSION = 2` 或 `SCHEMA_VERSION`（切 code-path/契约）
- **THEN** 判器 MUST NOT 判其为白名单版本常量（其有 code-path 依赖）→ Step2 照跑
