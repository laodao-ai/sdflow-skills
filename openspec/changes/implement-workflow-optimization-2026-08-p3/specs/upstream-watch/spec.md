# upstream-watch Specification

## Purpose

为四个上游源（gstack / superpowers / matt 套件 / OpenSpec CLI）维护版本锚，机械采集
「锚点以来」的 delta 事实，产出人可拍板的分诊报告，并把吸收决定经 recorder 衔接进
issues 池——使上游重看从全量成本变为增量成本。

## ADDED Requirements

### Requirement: 锚文件由脚本独占维护，锚推进与报告产出绑定

`openspec/upstream/anchors.yaml` SHALL 只由 watch 机械层脚本读写（git 跟踪）。
锚推进（把各源 anchor 更新为本轮观测值 + 更新 `last_run`）SHALL 仅在本轮分诊报告文件
已存在于 `openspec/upstream/reports/` 时执行；报告不存在时 MUST 拒绝推进并以非零退出。
anchors.yaml 存在但无法解析时 MUST fail-loud 硬停，MUST NOT 按「无锚」猜测续跑。

#### Scenario: 报告缺失时拒绝推锚

- **WHEN** 调用锚推进而本轮报告文件不存在
- **THEN** 命令以非零退出且 anchors.yaml 内容不变，错误信息指明缺失的报告路径

#### Scenario: 首轮无锚初始化

- **WHEN** anchors.yaml 不存在时执行一轮采集与推进
- **THEN** 采集按「无锚 ⇒ 当前上游态即基线」产出事实，推进时创建 anchors.yaml 并记录
  各源当前观测值与 `last_run`，报告标注「首轮建锚」

### Requirement: 四源 delta 事实机械采集，单源失败降级不传染

采集 SHALL 覆盖四源并输出结构化事实（facts）：gstack 与 matt、superpowers 三个 git 上游
各产出「锚..HEAD 的 commit 清单 + 变更路径」（superpowers 限定插件子路径）；OpenSpec 产出
本地版本 vs npm registry 最新版本对照。任一源采集失败（上游不可达、本地锚源缺失）时
该源 SHALL 标记 degraded 并附原因，其余源 MUST 照常采集。本地元数据文件
（`installed_plugins.json` / `.skill-lock.json`）键路径断言失败时 MUST 显式报格式漂移并
将该源降级，MUST NOT 静默产出错误锚值。

#### Scenario: 单源不可达其余照采

- **WHEN** 四源采集中仅 matt 上游不可达
- **THEN** facts 中 matt 标记 degraded 且含原因，其余三源事实完整在场

#### Scenario: 元数据格式漂移 fail-loud

- **WHEN** `installed_plugins.json` 中 superpowers 条目缺失预期的版本键
- **THEN** superpowers 源标记 degraded 且原因注明格式漂移，facts 中不出现猜测的版本值

### Requirement: OpenSpec schema fork drift 机械对比

采集 SHALL 对 schema fork 目录与已安装上游 schema 目录做逐文件整字节 digest 对比，
输出 changed / added / removed 文件清单；对比 MUST NOT 解析文件内容语义。上游 schema
目录定位失败时该子项 SHALL 降级并附原因。本 Requirement 为 T264（fork 漂移无机械提醒）
的收口实现。

#### Scenario: fork 与上游出现文件差异

- **WHEN** fork 目录某模板文件与上游安装目录同名文件字节不一致
- **THEN** facts 的 schema drift 清单将该文件列入 changed，报告 OpenSpec 节呈现该清单

### Requirement: 分诊报告按源分节、降级不罢工、首轮携带 seed 条目

一次 watch 运行 SHALL 产出一份落盘报告（`openspec/upstream/reports/<UTC日期>.md`，
git 跟踪），按源分节；每条 delta 条目 SHALL 给三分诊结论之一（吸收候选 / 观望 / 不吸）
及一句与本仓同类面对照的理由；每源节 SHALL 含采集状态行（ok / degraded / 首轮）。
degraded 源的节 SHALL 呈现原因与上游 URL 供人自查，MUST NOT 因单源降级放弃整份报告。
首轮报告 SHALL 将 T245 / T246 / T267 作为 seed 分诊条目呈报。

#### Scenario: 降级源仍出报告节

- **WHEN** superpowers 采集 degraded 而其余源正常
- **THEN** 报告仍产出且含四源节，superpowers 节呈现降级原因与上游 URL

#### Scenario: 首轮报告含 seed

- **WHEN** 首轮（无锚初始化）运行完成
- **THEN** 报告含 T245 / T246 / T267 三条 seed 分诊条目

### Requirement: 入池衔接只经 recorder 且需人拍板

watch SHALL NOT 直接创建、修改或关闭 issues 池条目。报告条目被人拍板「吸收」后，
入池 SHALL 经 recorder `add` 执行且 MUST 显式传 `source_change` 字段。

#### Scenario: 报告产出不改池

- **WHEN** 一轮 watch 运行完成（含报告落盘与推锚）
- **THEN** `openspec/issues/` 下无任何由本轮运行直接产生的新增或状态变更

### Requirement: sdflow-upgrade 陈旧提醒零网络零失败面

`/sdflow-upgrade` 收尾 SHALL 读取运行 checkout 内 anchors.yaml 的 `last_run`：距今超过
提醒阈值（默认 30 天，anchors.yaml 可配）时输出一行提醒；`last_run` 缺失、文件缺失或
不可解析时 SHALL 静默跳过。该提醒路径 MUST NOT 发起网络请求，MUST NOT 使 upgrade 流程
因提醒逻辑失败。

#### Scenario: 超阈值提醒一行

- **WHEN** upgrade 完成且 `last_run` 距今 45 天（阈值 30 天）
- **THEN** 输出一行含天数与 `/sdflow-upstream-watch` 指引的提醒，upgrade 结果不受影响

#### Scenario: 锚缺失静默跳过

- **WHEN** upgrade 完成而运行 checkout 尚无 anchors.yaml
- **THEN** 无提醒输出，upgrade 正常收尾无告警
