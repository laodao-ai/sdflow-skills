# Task 2 impl report: Step2 fan-out 编排拆为两段 dispatch

## 改动面

仅 `sdflow-spec-review/SKILL.md`，两处条款改写（均在「第二步：规划镜头 + 并行 fan-out 子代理」内，Task 1 已改写的 :197 串行纪律条款之后）：

1. **能力探针段（原 :207）**：
   - 头部措辞从「fan-out 前 MUST 先跑」改为「Step1 开始时跑一次，非 Step2 前才跑」。
   - 新增一句显式说明：本轮全程只探测一次——早于接地镜 dispatch①（Step1 起始即派），也早于领域/对抗镜 dispatch②（Step1 checkpoint 后派）；探针结果对两段 dispatch 的全部镜（domain/adversarial/grounding）共用，MUST NOT 因分两段 dispatch 而重复探测。
   - 探针内部判定逻辑（`$SDFLOW_HOST` 三分支、诚实边界、`unavailable` 处置、落锚格式）原样不动——brief 未要求改动这部分机制。

2. **fan-out 段（原 :232 表格上方）**：
   - 原标题「fan-out（一条消息内全部派出，各子代理 fresh context、无用户交互、返回结构化 findings）」已不准确（现在不是一条消息全部派出，而是两条消息分两段派出），改为「两段 dispatch（各段各自一条消息内派出该段全部镜……）」。
   - 表格前插入 ASCII 时序图，显式描述三段时序：
     - `Step1 开始（能力探针通过后，与 autoplan 同时起跑）` → dispatch① 接地镜
     - `Step1 checkpoint 完成后（autoplan amendment 已落盘）` → dispatch② 领域镜 + 对抗镜
     - `Step3 合并去重（不变）` → 接地镜 findings（dispatch①）与领域/对抗镜 findings（dispatch②）+ outside-voice 同池合并裁决，不因完成先后单独处理或降权
   - **fan-out 表格本身（三行：领域镜/对抗镜/接地镜的数量·职责·建议档位）原样保留，未加时序列**——按 brief 明确要求「表格本身只列镜的职责和档位，不涉及时序」。
   - 表格下方「档位与缺省见『模型选择』节」这句之后追加一句指引，把读者引回上方时序图对应各镜的 dispatch 时点，避免表格与时序图脱节。

## 未改动的面（确认一致性）

- `git diff --stat` 只命中 `sdflow-spec-review/SKILL.md` 一个文件（另有 tickets.md 的 Task 1 验收框勾选，非本次改动，Task 1 完成时已由 checkpoint 打上）。
- 全文 grep `fan-out 前|一条消息内全部派出|Step2 前` 确认改写后无残留的旧措辞引用。
- Step3 合并/裁决段（:249 起）未改动——与 design.md「不动的面」一致：接地镜 findings 无论何时完成都进同一合并池，本次只在两段 dispatch 时序图里重申这一点，未改 Step3 正文的合并去重逻辑本身。
- `fanout-capability` 锚格式、`lens-metric` 体系、`anchor_lint` 均未触碰。

## 验收标准自查

- [x] fan-out 段清晰描述两段 dispatch 的时序关系（ASCII 时序图 + 标题改写）
- [x] 能力探针时机明确为 Step1 开始时（而非 Step2 前），一次探针共用
- [x] 接地镜 dispatch 时序 = Step1 启动后（能力探针通过后）
- [x] 领域/对抗镜 dispatch 时序 = Step1 checkpoint 后

## 验证

`git diff sdflow-spec-review/SKILL.md` 已核验，改动面与上述描述一致，无越界改动。
