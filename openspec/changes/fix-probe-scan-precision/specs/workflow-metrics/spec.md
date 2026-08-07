## MODIFIED Requirements

### Requirement: 跨 change 聚合为只读可重生 view，不落新持久态

聚合 SHALL 由只读脚本 grep 所有归档 review 报告的 `lens-metric` 锚产出，输出**多列可排序**的各镜价值表；锚行本身 SHALL 为 state 真相源，聚合表 SHALL 为可随时重跑的 view，MUST NOT 写入新持久化聚合文件/数据库（守盘面即状态、避免双写不一致）。字段提取解析器**是净新路径**（现有 `_line_scoped_hits` 仅做固定字符串存在性检测、提不了字段），MUST 沿用同一 **fence-aware 行级纪律**（跳 fenced block、锚独占行前缀匹配、受限 kv 解析、**禁裸 `split`/substring**），SHALL 在聚合器内重实现 fence 核而 MUST NOT 跨 skill import `ship_gate`（避免 bundle→sdflow-ship 反向依赖）。**〔sdflow-retro SR-K 修订〕聚合器落 `sdflow-retro/scripts/`**（skill 独占——改后唯一运行时消费者 = `/sdflow-retro`，全局安装即用），MUST NOT 再落 bundle `sdflow-init/assets/workflow/tools/`、MUST NOT 再随 `sdflow-init update` 派生到消费仓（消费仓不再背此工具）。〔fix-probe-scan-precision〕`copy_bundle` 的 tools 部署路径整体退役后，`init.py` 侧不再存在任何 tools 拷贝动作 ⇒ 原「`ignore_patterns("tests")` 排除 MUST 保留以护 `trivial_shape.py` 部署」的约束**随部署路径一并退役**（无部署即无需排除；`tools/tests/` 只在 toolkit 源仓存在、由 pytest 直接收集）。

#### Scenario: 聚合表可重生且标注无锚样本
- **WHEN** 聚合脚本对 ≥2 个归档 change 运行
- **THEN** 输出一张多列可排序表、各镜 `独立` 列非空；对无 `lens-metric` 锚的老报告 SHALL 显式计「无锚样本 N，不纳入」，MUST NOT 静默跳过

#### Scenario: 聚合器随 skill 全局安装、不再派生消费仓
- **WHEN** 在任意仓运行 `/sdflow-retro`
- **THEN** 聚合器 SHALL 由 skill 自带（`sdflow-retro/scripts/`，setup.sh 全局安装）直接可用，MUST NOT 依赖消费仓 `openspec/workflow/tools/` 存在派生副本

#### Scenario: 不产合成价值分
- **WHEN** 聚合输出评审价值维度
- **THEN** SHALL 保持描述性多列（采纳率、独立率、findings/独立计数、出现轮数分列可排序），MUST NOT 产出单一合成价值分（避免焊死未验证权重、诱导自动砍镜）〔spec-review-amendment SR-J：删原「成本分列」——成本维度已撤出另立 T29〕
