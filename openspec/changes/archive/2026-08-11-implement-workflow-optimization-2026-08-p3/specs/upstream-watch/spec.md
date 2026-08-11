# upstream-watch Specification

## Purpose

为四个上游源（gstack / superpowers / matt 套件 / OpenSpec CLI）维护版本锚，机械采集
「锚点以来」的 delta 事实，产出人可拍板的分诊报告，并把吸收决定经 recorder 衔接进
issues 池——使上游重看从全量成本变为增量成本。

## ADDED Requirements

### Requirement: 锚文件由脚本独占维护，锚推进与本轮报告 + facts 绑定

`openspec/upstream/anchors.yaml` SHALL 只由 watch 机械层脚本读写（git 跟踪）。
锚推进 SHALL 以**报告路径 + facts 路径**双参数绑定本轮 [spec-review-amendment]：报告文件存在、
且报告文本包含 facts 中每源全部 commit sha（零解析子串校验）时方可执行；任一不满足 MUST 拒绝
推进并以非零退出。推进的观测值 MUST 取自 facts 文件，advance MUST NOT 发起任何网络 / git 查询
[spec-review-amendment]。推进范围 SHALL 仅覆盖 `status=ok` 且观测值完整的源；degraded 源的
anchor MUST 逐字保留 [spec-review-amendment]。
anchors.yaml 存在但无法解析时 MUST fail-loud 硬停，MUST NOT 按「无锚」猜测续跑。

#### Scenario: 报告缺失时拒绝推锚

- **WHEN** 调用锚推进而本轮报告文件不存在
- **THEN** 命令以非零退出且 anchors.yaml 内容不变，错误信息指明缺失的报告路径

#### Scenario: 报告漏转录时拒绝推锚 [spec-review-amendment]

- **WHEN** 报告文件存在但缺少 facts 中某源的至少一个 commit sha
- **THEN** 命令以非零退出且 anchors.yaml 内容不变，错误信息列出缺失的 sha

#### Scenario: 报告在场正常推进 [spec-review-amendment]

- **WHEN** 报告与 facts 双参数校验通过且四源均 ok
- **THEN** 各源 anchor 更新为 facts 记录的观测值，`last_run` 更新，命令零退出

#### Scenario: degraded 源锚保持不变 [spec-review-amendment]

- **WHEN** facts 中 matt 为 degraded、其余源 ok 时执行锚推进
- **THEN** matt 的 anchor 逐字保持推进前的值，其余源 anchor 正常推进，报告 matt 节标注
  「锚未推进，下轮重试同一窗口」

#### Scenario: 首轮无锚初始化（per-source 基线）[spec-review-amendment]

- **WHEN** anchors.yaml 不存在时执行一轮采集与推进
- **THEN** gstack 以本地 checkout HEAD 为天然锚产出「本地锚..上游 HEAD」的真 delta 事实；
  其余三源按「无锚 ⇒ 当前上游态即基线」产出零 delta 事实；推进时创建 anchors.yaml 并记录
  各源当前观测值与 `last_run`，报告标注「首轮建锚」

### Requirement: 四源 delta 事实机械采集，单源失败降级不传染

采集 SHALL 覆盖四源并输出结构化事实（facts，落 `openspec/upstream/.facts/<UTC时间戳>.json`，
不 git 跟踪 [spec-review-amendment]）：gstack 与 matt 两个 git 上游各产出「锚..HEAD 的 commit
清单 + 变更路径」；superpowers 产出 marketplace 仓 `.claude-plugin/marketplace.json` 中
superpowers 条目 `source.sha` 字段的变化序列（该仓不 vendor 插件内容，MUST NOT 用
`plugins/<name>` 路径过滤）[spec-review-amendment]；OpenSpec 产出本地版本 vs npm registry
最新版本对照。git 源取 delta 前 MUST 以 `merge-base --is-ancestor` 校验锚为 HEAD 祖先，非祖先
时该源 degraded「锚失效」[spec-review-amendment]。所有外部子进程 MUST 带统一数字化超时
（单点常量），挂起到点按该源 degraded 处置 [spec-review-amendment]。任一源采集失败
（上游不可达、超时、本地锚源缺失）时该源 SHALL 标记 degraded 并附原因，其余源 MUST 照常采集。
本地元数据文件（`installed_plugins.json` / `.skill-lock.json`）键路径断言失败时 MUST 显式报
格式漂移并将该源降级，MUST NOT 静默产出错误锚值；`installed_plugins.json` 为 per-plugin
多记录数组，版本取值 SHALL 优先 `scope=user` 记录、无则取版本最大 [spec-review-amendment]。

#### Scenario: 单源不可达其余照采

- **WHEN** 四源采集中仅 matt 上游不可达
- **THEN** facts 中 matt 标记 degraded 且含原因，其余三源事实完整在场

#### Scenario: 元数据格式漂移 fail-loud

- **WHEN** `installed_plugins.json` 中 superpowers 条目缺失预期的版本键
- **THEN** superpowers 源标记 degraded 且原因注明格式漂移，facts 中不出现猜测的版本值

#### Scenario: 单源挂起不阻塞整轮 [spec-review-amendment]

- **WHEN** matt 上游连接挂起（无退出）而其余源正常
- **THEN** matt 在超时常量到点后标记 degraded（原因=超时），其余三源事实完整在场，
  整轮 collect 正常返回

#### Scenario: 多 scope 版本取值 [spec-review-amendment]

- **WHEN** `installed_plugins.json` 中 superpowers 存在多条记录且版本不一致
- **THEN** facts 取 `scope=user` 记录的版本（无 user 记录则取版本最大者），不取数组首元素

### Requirement: OpenSpec schema fork drift 机械对比

采集 SHALL 对 schema fork 目录与已安装上游 schema 目录做逐文件整字节 digest 对比，
输出 changed / added / removed 文件清单；对比 MUST NOT 解析文件内容语义。报告 OpenSpec 节
SHALL 明示对比基线（已安装版本号）与 registry 最新版本号 [spec-review-amendment·拍板 Q1]。
上游 schema 目录定位失败时该子项 SHALL 降级并附原因。本 Requirement 为 T264（fork 漂移无
机械提醒）的收口实现。

#### Scenario: fork 与上游出现文件差异

- **WHEN** fork 目录某模板文件与上游安装目录同名文件字节不一致
- **THEN** facts 的 schema drift 清单将该文件列入 changed，报告 OpenSpec 节呈现该清单

#### Scenario: 双侧新增与删除文件分类 [spec-review-amendment]

- **WHEN** 上游安装目录新增一个 fork 没有的文件、且 fork 有一个上游已删除的文件
- **THEN** drift 清单分别将二者列入 added 与 removed

#### Scenario: 上游 schema 目录定位失败降级 [spec-review-amendment]

- **WHEN** `npm root -g` 下不存在上游 schema 目录
- **THEN** schema drift 子项降级并附原因，OpenSpec 源的版本对照子项不受影响

### Requirement: 分诊报告按源分节、降级不罢工、首轮携带 seed 条目

一次 watch 运行 SHALL 产出一份落盘报告（`openspec/upstream/reports/<UTC时间戳>.md`，文件名
含 UTC 时间戳到秒、一次运行一份，MUST NOT 覆盖既有报告 [spec-review-amendment]，git 跟踪），
按源分节；每条 delta 条目 SHALL 给三分诊结论之一（吸收候选 / 观望 / 不吸）及一句与本仓同类面
对照的理由——证据不足以支撑吸/不吸判断时 MUST 标「观望/待核查」，MUST NOT 仅凭 commit
subject 硬判 [spec-review-amendment]；每源节 SHALL 含采集状态行（ok / degraded / 首轮）。
「吸收候选」条目 SHALL 附预生成的完整 recorder `add` 命令（含 `source_change`）供拍板后直接
执行 [spec-review-amendment]。
degraded 源的节 SHALL 呈现原因与上游 URL 供人自查（本地元数据格式漂移分支例外：呈现本地文件
路径与键路径断言指引 [spec-review-amendment]），MUST NOT 因单源降级放弃整份报告。
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

#### Scenario: 未超阈值不提醒 [spec-review-amendment]

- **WHEN** upgrade 完成且 `last_run` 距今 10 天（阈值 30 天）
- **THEN** 无提醒输出，upgrade 正常收尾

### Requirement: watch 仅限 sdflow-skills 仓内运行 [spec-review-amendment]

本 skill 随 setup.sh 全局分发但语义单仓专用。watch 机械层两子命令起手 SHALL 校验 cwd 位于
sdflow-skills 仓（git remote 判定）；非本仓时 MUST fail-loud 退出并提示「本 skill 仅服务
sdflow-skills 工具链自身」，MUST NOT 在其他项目创建 `openspec/upstream/` 或发起网络请求。

#### Scenario: 其他项目误触发

- **WHEN** 在非 sdflow-skills 仓的项目 cwd 下调用 collect
- **THEN** 命令非零退出且提示单仓专用，该项目内无任何新增文件
