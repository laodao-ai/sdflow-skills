# 归档盲测：逐声边际贡献（tasks 6.5 / Q3）

> 随 change `absorb-gstack-autoplan` 归档。测试对象：新架构的 `strategy` 镜 / `plan-eng` 镜 /
> `design-voice`，对照旧架构（`autoplan` 原生执行的 CEO/Eng/DX 三阶段广审，落 `lens="broad"` 锚）。
> 目的：①旧 broad 独家高危 findings 召回率 ②新三声之间的边际独家贡献——为 F-adv1
> （聚合 broad 独立率 33% 全镜种最低）与「双镜是否都值得每轮付费」提供实证。

## 方法论

**语料选取**：对全部归档 change 的 `spec-review-report.md` 提取 `lens="broad"` 锚行，按
`独立`（broad 排他命中数）降序 + 高严重度（致/高）数量排序，取前 3 份：

| change | broad findings/采纳/独立 | sev（致/高/中/低） |
|---|---|---|
| `fix-probe-scan-precision`（2026-08-07） | 36/34/34 | 3/12/17/2 |
| `harden-implement-review-loop`（2026-07-28） | 37/31/28 | 2/11/13/5 |
| `refactor-roadmap-internalize-deps`（2026-08-06） | 25/22/15 | 1/8/10/3 |

**执行**：对每份语料的**归档时四件套**（proposal/design/tasks/specs），分别单独派出 3 个 fresh
子代理——`strategy` 镜（BASE 计划级 R 项范围）、`plan-eng` 镜（BASE 工程级 R 项范围）、`design-voice`
（自由式第二意见，聚焦 proposal「What Changes」+ design「Decisions」）。三者互不可见彼此输出，也不
可见该 change 的历史 `spec-review-report.md`/`gstack-review.md`（prompt 显式禁止读取，且未提供内容）。

**两条诚实边界（如实登记，不回避）**：

1. **design-voice 是同族代理，非真跨模型**——生产环境的 `design-voice` 经 `outside-voice.sh` 调用
   Codex（跨模型第二意见）；本次盲测受限于子代理只能同为 Claude 家族，是**同族 proxy**，测的是
   "跨检查清单的自由式读法"而非"跨模型盲区互补"，与生产 `design-voice` 的实际价值来源不完全等价，
   结果**只能证伪/佐证"检查清单范围"这一个变量**，不能回答跨模型那部分。
2. **旧 broad 高危 findings 的逐条来源归属，仅 1/3 语料可精确复原**——`harden-implement-review-loop`
   的报告对每条 Critical/High 都标注了来源镜（如"来源:Codex Eng voice #1"），可做逐条召回核对；
   另两份报告的 Findings 明细未逐条标注来源镜（只在少数条目标注，如"〔接地镜〕"），无法从报告文本
   精确复原"哪些高危 finding 严格排他属于 broad"——`lens-metric` 锚的 独立 计数是**聚合数字**，不
   反解到具体 finding ID。这两份只能做**主题层面**的召回判断，如实标注置信度更低。

## 结果 A：`harden-implement-review-loop`（唯一可逐条核对的语料）

旧报告明确标注来源的 **Critical+High** 中，可归为「CEO/Eng/DX（旧 broad）主导或独家」的 11 条：
C1（Codex Eng）、C2（Codex CEO+DX）、H5（Codex Eng+DX）、H6（Codex Eng）、H7（Codex CEO/DX/Eng）、
H8（Codex CEO+DX）、H9（Codex DX/Eng/CEO）、H10（Codex DX）、H11（Claude DX+Codex Eng）、
H12（Codex Eng+Claude Eng）、H15（Claude CEO）。（H3/H4 明确来源 design-voice、H2/H13/H14 明确来源
对抗镜，**不计入本次要检验的"broad 独家"目标集**——它们本就不该由 strategy/plan-eng 补，而应由新
架构的 design-voice/对抗镜承接，另行核对见下。）

**新三声召回情况（逐条核对）**：

| 旧 finding | 内容 | 新三声是否召回 |
|---|---|---|
| C1 | verify 位置违反既有 Requirement（stale 锚点） | ❌ 三声均未提及 |
| C2 | 聚合回归只覆盖非默认 tickets 轨，verify 锚无条件 | ❌ 三声均未提及 |
| H5 | Migration Plan 部署渠道写错（update vs setup.sh） | ❌ 未提及 |
| H6 | delta 静默删除 T10 语义 | ❌ 未提及 |
| H7 | 聚合套件无确定性定义（含 flaky/超时处理） | 🟡 **plan-eng 部分召回**（超时/挂起场景，未覆盖 flaky/环境故障全貌） |
| H8 | 3 项 Success Metrics 全是文本存在性检查 | 🟡 **plan-eng+design-voice 主题层面呼应**（quota 降级/grandfather 矛盾，非同一具体点） |
| H9 | 验证票执行契约与普通票不兼容 | ❌ 未提及 |
| H10 | 档位解析状态机自相矛盾（unknown 语义） | ❌ 未提及 |
| H11 | Codex 子代理授权范围未覆盖 sdflow-implement | ❌ 未提及 |
| H12 | 「最后一票」无拓扑/gate 机械保证 | ❌ 未提及 |
| H15 | ADR 判定不一致（D1/D3 满足条件却未开） | ❌ 未提及 |

**召回率：11 条中 0 条精确命中，2 条（H7/H8）仅主题层面呼应——严格计 0/11，宽松计 2/11（≈18%）。
两条 Critical（C1/C2）全部未召回。**

同一语料里，新三声**确实**独立重现了旧报告 H3/H4（review-loop-breaker 指纹身份键缺陷，strategy 与
plan-eng **各自独立**给出，且 plan-eng 版本还引用了后续归档 change `curb-rework-loop-cost`/`adr/0035`
的真实反例佐证，比旧 H3/H4 更扎实）与 H2（D2a 论据取错组，design-voice 独立给出）——但这两条旧
报告明确标注来源为 **design-voice / 对抗镜，不是 broad**。这说明：**新架构下 strategy/plan-eng 的
"读法"覆盖到了旧架构里原本由design-voice/对抗镜负责的内容**（一种交叉冗余，非坏事），**但没有覆盖
到旧 broad（CEO/Eng/DX）本身负责的战略/流程/部署一致性类内容**（verify 时序、部署渠道、Codex 授权
范围、tier 状态机——这些是"通读整条流水线、核对跨 skill 契约是否自洽"的**广度型**发现，不是"对着
四件套挑单点逻辑洞"的**深度型**发现）。

## 结果 B：`fix-probe-scan-precision`、`refactor-roadmap-internalize-deps`（主题层面，置信度较低）

无法逐条核对来源，改用主题匹配：

- **`fix-probe-scan-precision`**：新 design-voice 独立发现的 `sane()` 决策图与散文自相矛盾，与旧
  F16（`sane()` 未扩面查 `tools/`+contract）落在**同一话题区**（`sane()` 覆盖范围），但**具体指控不同**
  （旧=实现缺口，新=文档图文不同步）——算部分主题呼应，不算精确召回。新 plan-eng 发现的
  `ship_gate` `tools_spec` 腿退役缺 spec Scenario，与旧 F44（`ship_gate` 论证只在源仓成立）同属
  `ship_gate`/`tools_spec` 话题区，同样是不同角度。**其余旧 P0 高危项**（F1/F10-F14/F6-F9 的漏测/
  spec 分叉类）**新三声均未触及**——这批恰恰需要"通读多份 spec delta + 现有测试文件互相比对"的
  跨文件核对深度，新三声的 R 项范围清单本身不含"逐条比对 spec delta 间是否自相矛盾"这类专项。
- **`refactor-roadmap-internalize-deps`**：新 design-voice 找到的 matt 归因表述不准，与旧 SR-33
  （Claude CEO 独家：matt fold 因果表述不准）**主题高度重合**，可算一次成功的（同主题）复现。
  其余 CEO/DX 独家条目（SR-26/27 判定点时序矛盾、SR-31 office-hours 双宿主论证打包、SR-24 死链案例）
  新三声未触及。

## 结果 C：新三声之间的边际独家贡献（可精确核对，无需对照旧报告）

3 个 change × 3 声，共 9 组产出，逐组比对彼此内容后**几乎零字面重复**——每一声在同一语料上给出的
具体问题点，其余两声都未提及（唯一的部分重叠是 `harden-implement-review-loop` 里 strategy 与
plan-eng 都独立发现了 review-loop-breaker 指纹缺陷，属于"殊途同归"而非同一条被两声各报一次）。
三声各自命中的问题类型也有系统性差异：

- **strategy** 偏好抓：正文考古层残留（DOC-1）、Non-Goals/假设缺口、标签/编号复用错位。
- **plan-eng** 偏好抓：spec delta 与代码/其余 spec 的追溯链缺口、错误处理/超时未量化、组件清单遗漏。
- **design-voice** 偏好抓：文档内部自相矛盾（前后论述打架）、验收指标与其自身豁免条款冲突、
  论据与结论错配。

**结论：三声在"读法"层面互补，边际独家贡献真实存在**——这与 D1（双镜自持 + design-voice 恒跑）的
设计方向一致，没有证据支持"某一声可直接砍掉"。

## 总体结论（对 F-adv1 / D1 留存决策的证据贡献）

1. **不支持"新架构能力不缩水"的乐观假设**——在唯一可精确核对来源的语料
   （`harden-implement-review-loop`）上，旧 broad（CEO/Eng/DX）独家/主导的 11 条 Critical/High 中，
   **两条 Critical 全部未被新三声召回**，高危条目严格召回率为 0（宽松主题匹配也只有 ~18%）。
   这**印证而非反驳** F-adv1 的担忧方向：旧 broad 六声（尤其 CEO/Eng 的"通读全链路找跨 skill 契约
   洞"式发现）里存在一类**广度型、跨文件一致性**的价值，新 strategy/plan-eng 的 base R 项清单式
   读法**目前接不住**这类发现——它们的失效模式是"逐点对着清单打分"，而不是"通读三份 spec delta
   + 相关 SKILL.md 找矛盾"。
2. **但新三声（尤其 design-voice）确实贡献了旧架构没有的独立价值**——文档内部一致性、
   论据质量类问题在旧报告里覆盖薄弱，新三声在三份语料里都独立挖出了同类问题，且部分（如
   review-loop-breaker 指纹缺陷）比旧报告的对应发现（同主题但由 design-voice/对抗镜给出）**论证
   更扎实**（引用了后续归档 change 的真实实证）。
3. **本次盲测样本量小（3 份语料、1 份可逐条核对）+ design-voice 为同族代理**，不足以支撑"砍掉某一
   声"或"新架构整体降级"的结论性裁决——按 Q3 拍板（D1 双镜形态照拍板落地不动，数据说话后再议降声），
   这份报告的定位是**留存/降声证据基线**，不是当次裁决依据。**建议 `/sdflow-retro` 后续持续在真实
   evaluation 轮次里跟踪"广度型跨文件一致性发现"这一类的召回率**（可作为一个新的人工复评维度，
   现有 lens-metric 契约的 `独立`/`采纳率` 聚合数字看不出这个维度），而不是止步于本次一次性盲测。
4. **具体的、可操作的改进候选**（供后续 change 参考，非本 change 强制）：
   给 `strategy`/`plan-eng` 镜各补一句"跨文件一致性核对"义务（如"核对本 change 触及的多份 spec
   delta 之间、及与相关 SKILL.md 实际内容之间是否自相矛盾/未声明分叉"），可能是低成本补上 C1/C2/H5/
   H6/H9-H12 这类发现的手段——它们本质上都是"跨文件/跨制品一致性"缺口，而非"单份文档内部质量"缺口，
   目前两镜的 R 项范围表述（BASE-01/08/09/...）里没有一条精确对应"跨制品一致性核对"这个动作本身。
