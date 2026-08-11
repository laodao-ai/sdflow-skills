# spec-review-report · implement-workflow-optimization-2026-08-p3

> 评审日期 2026-08-11 · 宿主 claude（强档 opus 主审 / 中档 sonnet 镜 / 弱档 haiku 接地）·
> 单批 dispatch：broad 双镜（strategy/plan-eng）+ devex 领域镜 + 对抗镜 ×2 + 接地镜 + 跨模型 voice ×2（codex·gpt-5.6-sol）

## 锚区

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,grounding" -->
<!-- sdflow:step1-broad-review v1 mode="subagent" -->
<!-- sdflow:hr-tg v1 hit="TG-08" declared="TG-05,TG-08,TG-11,TG-13,TG-18,TG-19,TG-22,TG-23,TG-28" evidence="新增 3 个 git 上游 + npm registry 运行时访问（design TD2 + 失败模式表）" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

TG 判定：命中 TG-05/08/11/13/18/19/22/23/28（`hr_tg_intersect.py` 确定性交集 → HR-TG∩ = {TG-08}，
故单开 hr-tg 领域 cross-model）。领域镜按栈判定仅 devex 一面（TG-28：新 developer-facing skill 交付面；
无 go/embedded/frontend 面）。对抗镜 2 面（普通风险档）。voice 均 async·harness 分支真跑成功
（`.rc` sidecar = 0，未截断）。

## 决策登记区

### [自动决策]（默认采纳，设计门可覆盖；对应修订已按 [spec-review-amendment] 落进四件套）

- **D1（M1·Critical）superpowers 采集机制更换**：双对抗镜独立实查坐实（真 clone + GitHub API）——
  `claude-plugins-official` 仓**不 vendor 插件内容**，`plugins/superpowers` 路径不存在（superpowers 条目是
  `.claude-plugin/marketplace.json` 里指向 obra/superpowers + 固定 sha 的指针），设计的
  `git log -- plugins/superpowers` 会**永远返回空**且无任何降级信号——该源从第一天起静默空转。
  修法：改为追踪 marketplace.json 中 superpowers 条目 `source.sha` 字段的变更历史
  （`git log -- .claude-plugin/marketplace.json` + 逐次 diff 该 JSON 字段；有界 JSON 字段提取，符合基准 5）。
  **D3 拍板的观察面（盯 marketplace 仓）不变，仅换采集机制**。
- **D2（M5·Critical）首轮基线 per-source 拆分**：proposal Success Metric（首轮跑真 delta）与 spec 首轮
  Scenario（「当前态即基线」= 零 delta）互斥。修法：gstack 以**本地 checkout HEAD** 为天然锚（首轮即出
  960c3a8..上游 真 delta），其余三源无天然滞后锚 → 「当前态即基线」仅建锚；spec 拆成两条 Scenario。
- **D3（M2·High）报告-轮次绑定收紧**：报告文件名含 UTC 时间戳到秒（`reports/<UTC时间戳>.md`，一次运行
  一份，消同日覆盖）；`advance` 接收**报告路径 + facts 路径**双参数，并做弱机械校验——报告文本 ⊇ facts
  中每源全部 commit sha（零解析子串检查，防模型漏转录后锚照推）。
- **D4（M3·High）degraded 源锚不推进**：advance 只推进 `status=ok` 且观测值完整的源，degraded 源
  anchor 逐字保留 + 报告标注「该源锚未推进，下轮重试同一窗口」；tasks 补对应用例。`last_run` 默认保持
  全局单值（简化），备选见 Q2。
- **D5（M4·High）外部命令统一超时**：四采集器全部 subprocess 调用统一数字化超时常量（单点定义，默认
  60s/次），挂起（无非零退出）与不可达分列失败模式表两行；补「单源永久挂起其余源仍完成」测试。
- **D6（M6+M10·High）单仓运行守卫**：本 skill 全局分发但语义单仓专用——SKILL/脚本起手检测 cwd 为
  sdflow-skills 仓（git remote / 仓标识），非本仓 fail-loud 提示「本 skill 仅服务 sdflow-skills 工具链自身」；
  proposal 补假设 A4；description/README 显式声明单仓专用；watch 在开发 checkout 跑（提醒线读运行
  checkout 锚，push→pull 前提醒可陈旧，接受并写明）。
- **D7（M7·High）facts 落点与 advance 输入契约**：facts 写
  `openspec/upstream/.facts/<UTC时间戳>.json`（`.gitignore`，跨宿主可寻址，替代未定义的「scratch」）；
  advance 禁止发起任何网络/git 查询，观测值只读 facts（消 collect/advance 时序窗口丢 delta）。
- **D8（M11·High）锚祖先守卫**：取 log 前先 `git merge-base --is-ancestor 锚 HEAD`，非祖先 →
  degraded「上游历史疑似被重写，锚失效」（防 force-push 后 exit 0 假成功）。
- **D9（M12·Med）bare 缓存自愈**：fetch 失败 → 删缓存目录重 clone 一次，再失败才 degraded（原因文案带
  缓存路径）。
- **D10（M9·Med）三分诊证据条款**：SKILL 编排层——证据不足时 MUST 标「观望/待核查」不硬判吸/不吸；
  允许对候选 commit 在 bare 缓存 `git show` 按需取内容（git 自己回答，零解析维持）。
- **D11（M13–M22 批量·Med/Low）**：yq flavor 探测复用 `retro_report.py` idiom（各自实现不 import）｜
  `installed_plugins.json` 为多记录数组（对抗镜实查证实同插件跨 scope 版本可异），取值策略 = 优先
  `scope=user`、无则取版本最大，写进 spec + 测试｜R5「不改池」补契约测试（沙盒跑 collect+advance 后断言
  issues 树不变）+ 覆盖图行｜design 补组件清单表（BASE-25）｜Compliance 措辞修正 + git 跟踪产物路径一律
  tilde 记法｜spec 补 Scenario（R1 正向推进、R3 added/removed/定位失败降级、R6 未超阈值静默）｜
  description 触发词收敛补 `sdflow-maintain`（其 description 已含「上游」字样撞车）｜格式漂移分支修复提示
  本地化（不复用「上游 URL」模板）｜入池命令模板在报告内预生成（连 `source_change` 一起写好，人拍板后
  直接跑，替代纯 prose MUST）｜关键错误文案实现期定稿进脚本 docstring。

### [需拍板]

- **Q1（M8）T264 schema drift 对比基线**（voice 独家）：现设计对比 fork vs **本机已安装版**；registry 已出
  新版而本机未升级时，看不到新版 schema 细节（只有版本差一行）。
  - **推荐 A：维持已安装版对比** + 报告明示「drift 基于已安装版 X，registry 最新 Y」+ 版本差单独呈报。
    三面后果——系统镜：零新增实现面；用户镜：新版 schema 细节延迟到升级后一轮才见（「有新版」信号已在场，
    不失联）；开发循环镜：T264 收口口径 =「fork 漂移有机械提醒」已满足。**主次判定：开发循环镜为主**——
    T264 的痛点是「从不重看」，版本差提醒已破局。
  - 备选 B：`npm pack` 拉 registry 最新解包对比。系统镜：+网络+临时目录+清理面；用户镜：drift 细节即时；
    开发循环镜：实现与测试面增。
- **Q2（M3 残部）`last_run` 语义**：推荐 A=全局单值（D4 已按此改；代价：全源 degraded 的一轮也会刷新
  提醒时钟，掩盖连续失败——概率低影响小，记边角）。备选 B=per-source `last_success_at` + 提醒取最旧
  （两路 voice 均推荐；代价：anchors schema 与提醒逻辑复杂化）。

### [已裁掉]

- **X1（G-1·grounding）**「sdflow-upgrade/SKILL.md 缺第 5 步」——误读目标态为现状断言：design 写
  「现为四步结构（…），提醒段追加为第 5 步」是**改动计划**；spec-review 阶段实现未开始，第 5 步不存在
  是预期。接地实查（现为四步）恰确认 design 的现状描述准确。
- （机械引用核 [ref-check] 无裁掉项：合并池 23/23 pass，其中 M22 初次行号偏差 1 行，修正后 pass。）

## 合并 findings 池（去重后 23 条 → 采纳 21 / 需拍板 1 / 裁掉 1）

| ID | 问题 | 命中镜 | 严重度 | 裁决 |
|---|---|---|---|---|
| M1 | superpowers 路径过滤命中空气，采集永久空转（实查坐实） | 对抗A+对抗B+voice(hr-tg) | Critical | 采纳→D1 |
| M2 | 报告绑定仅存在性：同日覆盖/漏转录/「本轮」不可判 | voice×2+对抗B+devex+对抗A | High | 采纳→D3 |
| M3 | degraded 源推锚语义未定义；全局 last_run 掩盖失败 | voice×2+对抗B | High | 采纳→D4（+Q2） |
| M4 | 外部命令无超时契约，挂起阻塞整轮违反不传染 | plan-eng+voice(hr-tg) | High | 采纳→D5 |
| M5 | 首轮基线语义三文档互斥（真 delta vs 当前态基线） | 对抗B | Critical | 采纳→D2 |
| M6 | 单仓专用 skill 全局分发无范围守护 | strategy+devex | High | 采纳→D6 |
| M7 | facts「落 scratch」协议未定义；advance 观测值来源未定义 | 对抗A+对抗B | High | 采纳→D7 |
| M8 | T264 对比对象=本机安装版，registry 新版不可见 | voice(design) | High | 需拍板→Q1 |
| M9 | 三分诊仅凭 subject+路径，语义证据不足 | voice(design) | Med | 采纳→D10 |
| M10 | 跨 checkout 同步契约未声明（watch 在哪跑/提醒读哪侧） | voice(design) | Med | 采纳→D6 |
| M11 | force-push 后 `锚..HEAD` exit 0 假成功（本地可复现） | 对抗A | High | 采纳→D8 |
| M12 | bare 缓存中断损坏后无自愈，该源永久 degraded | 对抗A | Med | 采纳→D9 |
| M13 | yq flavor 探测未显式承诺复用（两种不兼容 yq） | 对抗A | Med | 采纳→D11 |
| M14 | R5「不改池」可机械验证却无测试项 | plan-eng | Med | 采纳→D11 |
| M15 | 缺 BASE-25 组件清单表 | plan-eng | Med | 采纳→D11 |
| M16 | 公开仓 git 跟踪产物 vs「不上传数据」声明张力 | plan-eng | Med | 采纳→D11 |
| M17 | spec Scenario 与 tasks 测试矩阵不对称（R1/R3） | strategy | Med | 采纳→D11 |
| M18 | description 收敛清单漏 sdflow-maintain（「上游」撞车） | devex | Med | 采纳→D11 |
| M19 | 格式漂移修复提示错配「上游 URL」模板 | devex | Med | 采纳→D11 |
| M20 | `source_change` MUST 纯 prose 无机械 guard（有前科） | devex | Med | 采纳→D11 |
| M21 | installed_plugins.json 实为多记录数组，取值策略未定义（实查证实） | 对抗B | Med | 采纳→D11 |
| M22 | 错误/降级文案无确切原文，DX-02 不可判 | devex | Low | 采纳→D11 |
| G1 | sdflow-upgrade 缺第 5 步 | grounding | — | 裁掉→X1 |

置信度分流：全部采纳项置信高/中（高者直接采信、中者并入对应 D 项修订）；无低置信项被滤除。
机械引用核：`findings_ref_check.py` 23/23 pass（M1 另有双镜实机 evidence_pack：clone + GitHub API）。

## 各镜独立产出摘要

- **strategy（broad）**：S-1 范围守护（→M6）、S-2 Scenario 不对称（→M17）；BASE-08/10/12/13/14/18/22/26/27/30 核查通过。
- **plan-eng（broad）**：P-1 超时（→M4）、P-2 组件清单（→M15）、P-3 R5 测试（→M14）、P-4 公开仓合规（→M16）；BASE-06/19 判可接受简化。
- **devex 领域镜**：DX-1（→M6）、DX-2（→M18）、DX-3（→M19）、DX-4（→M20）、DX-5（→M22）、DX-6（→M2）；DX-01/03/04 未见违反，setup.sh 自动纳入/recorder 契约已实证。
- **对抗镜 A（隐藏假设）**：A-1（→M1，真 clone 实证）、A-2（→M11，本地复现）、A-3（→M7）、A-4（→M12）、A-5（→M13）、A-6（→M2）；npm/`~/.skills` 硬编码/schema 定位三角度自证伪后放过。
- **对抗镜 B（失败模式）**：B-1（→M5）、B-2（→M2）、B-3（→M1，GitHub API 独立实证）、B-4（→M3）、B-5（→M7）、B-6（→M21，本机实查 claude-hud 三记录版本互异）。
- **接地镜**：15 项代码事实 14✓（本地锚源形状、yq v4.53.3(mikefarah)、setup.sh install_into、issues 四条、adr/0037、roadmap 决策 3、上游 URL 拼写均属实）；1 项误读（→X1）。
- **design-voice（跨模型）**：V-1（→M2）、V-2（→M8 独家）、V-3（→M9 独家）、V-4（→M10 独家）、V-5（→M3）。
- **hr-tg voice（跨模型）**：H-1（→M2）、H-2（→M3）、H-3（→M4）、H-4（→M1）。

TENSION：无（voice 与主审无未消解分歧；Q1/Q2 为方案择一，非立场冲突）。

## 图表核验（design-diagrams）

TG-13/TG-11 命中 → design「组件与数据流」ASCII 图存在且与 TD1–TD6 一致，未过时（D1/D7 修订后
superpowers 支路与 facts 落点标注需随 amendment 微调，已在修订中处理）；TG-18 → tasks 3.5 测试覆盖图
表在场。无缺失图。

## lens-metric（Step3 pre-gate 临时裁决；拍板回写时最终化〔SR-M〕）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="6" sev="致2/高4/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="6" 采纳="6" 裁掉="0" defer="0" 独立="4" sev="致0/高2/中3/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="4" 裁掉="0" defer="1" 独立="2" sev="致0/高2/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="0" sev="致1/高3/中0/低0" -->

残余信任边界声明：分类正确性、roster 完备性、findings 誊写准确仍是主 session 信任边界；emitter 只保证
确定性归约。`findings=N` 与合并池实收数的数值一致性同为信任边界，非机械可验。

## 收敛口

四件套修订（D1–D11 对应 amendment）已落盘，Q1/Q2 待人拍板。**建议进设计 HARD-GATE**：过本报告拍板
Q1/Q2 + 确认 D1–D11 默认采纳后即可批准进入阶段三（批准前若再改四件套，须按 1.7b 先单独 checkpoint 再回写锚）。
