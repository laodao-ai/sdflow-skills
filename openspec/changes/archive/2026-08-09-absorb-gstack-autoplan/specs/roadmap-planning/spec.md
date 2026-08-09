## REMOVED Requirements

### Requirement: review 按商业化信号分档

**Reason**: 分档(默认 `/plan-eng-review` 单审 / 商业化信号命中 `/autoplan` 三连)的存在理由是外部三连审成本高;review 执行体自持化(两个并行中档子代理)后该成本前提消失,且两个外部 skill 依赖随 gstack 运行时依赖全退役(ADR 0040)而移除。strategy 视角(前提/范围/长期轨迹)对技术型 roadmap 同样承重,不应按商业化信号才给。

**Migration**: 由「review 恒跑自持双镜与跨模型声」Requirement 承接;调用契约(整体 plan 声明)、跳过授权(`review-waived`)、处置四态、未审待恢复阻塞收尾条款全部原样保留在新 Requirement 内;商业化信号词表仍由讨论层三态路由使用,仅 review 分档消费点退役。

## ADDED Requirements

### Requirement: review 恒跑自持双镜与跨模型声

三件套完成后 SHALL 执行内容质量 review:恒跑 **strategy 镜 + plan-eng 镜**(两个并行 fresh 子代理;镜职责定义与 `sdflow-spec-review` 广审镜**同源——由单一源资产经模板注入两 SKILL 的托管 marker 块承载,机械等值由注入脚本 `--check` 门禁保证;MUST NOT 无注入守卫的手工第二份拷贝,MUST NOT 无机械守的 prose 跨 SKILL 引用**〔spec-review-amendment Q2〕)+ **sync-only 跨模型 outside voice**(`outside-voice.sh` 同步分支,site=`roadmap-voice`,前台执行、当场取退出码;MUST NOT 移植 async 协议段)。

**调用契约**:触发 review 时 SHALL 显式声明「把三件套(design/roadmap/task-log)视为一个整体 plan 来 review」并指定主入口文件(roadmap.md)——缺此声明会退化为单文件审。**跳过授权**:跳过 review 仅限人类操作者显式授权(agent 自身 MUST NOT 代决跳过),产物状态记 `review-waived` 不与已审混同;task-log.md 留「未做 review,风险自担」痕迹。review 产出的每条 issue SHALL 在 task-log.md「Review 处置」小节标注 采纳/拒绝/延后 之一且附理由。

**voice 处置**:voice SHALL 在双镜派出后**立即**启动(与双镜墙钟重叠,MUST NOT 串行等双镜返回再跑)〔spec-review-amendment K-3〕;成功(reason_code=ok)则 findings 与双镜同池进「Review 处置」;失败 SHALL 同族 fallback 只读子代理——**fallback 派发 SHALL 带编排方时间预算(与 sync 内层 300s 同量级),超预算未返回视为 fallback 亦失败、当场落「未审待恢复」**,MUST NOT 无界等待(裸 Agent spawn 挂起时「未审待恢复」将永远写不出来,既无状态也无阻塞)〔spec-review-amendment M12〕;task-log SHALL 留一行 runner/reason_code 痕迹,同族 fallback 成功时该行 SHALL 含「降级」字样(如实标注非跨模型)〔spec-review-amendment M27〕(人读,不落 anchor_lint/lens-metric 锚——roadmap 无度量锚体系)。

**失败处置**:双镜派发失败/voice 与 fallback 均失败/无输出时 SHALL 显式留痕「未审待恢复」并提示修复步骤,MUST NOT 静默当已完成。**该状态阻塞收尾**:包状态为 `未审待恢复` 时 SHALL 阻塞收尾 checklist,MUST NOT 因「Review 处置小节无未处置条目」而误判可以收尾;只有 review 成功执行、或人类操作者显式授权 `review-waived` 两种状态方可进入 checklist。

#### Scenario: 恒跑双镜不分档

- **WHEN** 任意类型 roadmap(技术重构型或商业化型)三件套完成
- **THEN** 触发同一套 strategy + plan-eng 双镜 review(调用语含三件套整体声明与主入口 roadmap.md),MUST NOT 按商业化信号增减镜数

#### Scenario: sync voice 成功进处置池

- **WHEN** `outside-voice.sh` sync 执行退出码 0
- **THEN** voice findings 与双镜 findings 同池进 task-log「Review 处置」四态标注;task-log 留 runner/reason_code 一行痕迹

#### Scenario: voice 失败同族 fallback 不静默

- **WHEN** sync voice 执行失败(非零退出/helper 缺失)
- **THEN** SHALL 派同族只读 fallback 子代理补第二意见(带时间预算),task-log 记降级原因与「降级」字样;MUST NOT 静默当「本次无 voice」

#### Scenario: fallback 超时间预算按双败处置〔spec-review-amendment M12〕

- **WHEN** 同族 fallback 子代理超出编排方时间预算仍未返回
- **THEN** 视为「voice 与 fallback 均失败」,当场落「未审待恢复」并阻塞收尾;MUST NOT 继续无界等待

#### Scenario: 跳过 review 必留痕

- **WHEN** 人类操作者显式决定跳过 review
- **THEN** task-log.md 存在「未做 review,风险自担」条目、包状态记 review-waived,收尾 checklist 方可通过

#### Scenario: review 失败不静默且阻塞收尾

- **WHEN** 双镜派发失败或 voice 与 fallback 均失败导致 review 无产出
- **THEN** 显式提示 + task-log 留「未审待恢复」痕迹 + 给出修复/重试步骤;该状态阻塞收尾 checklist,修复重跑成功后方可继续

#### Scenario: 整体 plan 调用话术存活

- **WHEN** 触发 roadmap review 双镜
- **THEN** 派发语中出现「把三件套(design/roadmap/task-log)视为一个整体 plan 来 review」的显式声明且指定主入口 `roadmap.md`;缺此声明即视为该次 review 未按契约执行,SHALL 重新触发
