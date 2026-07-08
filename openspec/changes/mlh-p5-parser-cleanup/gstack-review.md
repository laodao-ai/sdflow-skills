<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review — mlh-p5-parser-cleanup（autoplan 广审·原生执行）

> **native 佐证**：autoplan pipeline 原生载入主 session（非子代理转述）；按 `spec-review.md §五`「autoplan 瘦着跑、火力集中 Validation + 读码核验」执行其实质独立审——跨家族 codex outside-voice（真实调用 `codex exec`，exit 0，282KB 输出）+ fresh Claude eng/DX subagent（独立 context，120k tokens / 12 tool_uses / 逐点读码）。跳过对内部工具 change 空转的仪式（CEO 战略 10 sections / restore point / audit trail / Final Gate 交互——UI scope=no 故 Design skip；G2 本就不弹窗）。

## 双声 consensus（codex ↔ claude subagent）

| 维度 | codex | claude subagent | consensus |
|---|---|---|---|
| absent 三读点是否放行 | 无反例（核 decide） | 逐点核码不放行（另验 verify早检L713/cr_stale peek L780 附带读点亦安全丢弃） | **CONFIRMED 不放行** |
| live absent 误 SHIPPED 路径 | 无（SHIPPED 仅 L660 active缺+base归档+archived=="pass"） | 无（D3 短路读归档，live absent 到不了） | **CONFIRMED 无** |
| parse 调用方数 | **三个**（漏 anchor_set L412） | **三个**（anchor_set 是活 public API 非死符号） | **CONFIRMED 双命中** |
| 死符号删除运行时安全 | grep 无运行时引用 | decide() 零引用（仅 docstring+测试） | **CONFIRMED 安全** |

## Findings

### BR-1【CONFIRMED 双命中·置信高·严重度低】parser 第三调用方 `anchor_set` 未纳入论证，违 adr/0011 自铸 MUST
- 证据：`ship_gate.py:412` `anchor_set(text)` 内调 `parse_ship_gate_frontmatter`（熔断状态集 helper，T26/SR-1；经 `SKILL.md:29` 接进编排器熔断判据，`test_gate_breaker.py` 全覆盖，**活 API 非死符号**）。design ADR-4 + `adr/0011:2-3` 写「被**两个**调用方共用」= 事实错误，实为三个。
- 行为：anchor_set 对 T74 **不变量**——旧 `unterminated`→`err≠None`→`frozenset()`；新 `absent`→`err=None,state={}`→`frozenset({}.items())=frozenset()`，两路皆空集。**运行时安全、无功能回归**，但未被论证覆盖，违反本 change 自铸 adr/0011「改共用核心 MUST 对每个调用方分别论证」——**ADR 首次落地就自打脸**。
- 裁决：**采纳**。修 adr/0011 + design ADR-4 调用方清单补 `anchor_set` + 一句论证（两语义均映射空集、无净变化倾向、行为不变）；tasks 验收 grep 补数第三调用方。

### BR-2【置信高·严重度低】「两侧同向 fail-safe」措辞只在目标态成立
- 证据：`archived_verify_state:196-208`。旧 `---`无闭合归档→`unterminated`→`return "none"`（永不 SHIPPED）；新→`absent`→穿透 inline dual-read，杂交形态（首行`---`无闭合 × 正文独占行 inline PASS 锚）→pass→D3 SHIPPED。即该一形态改判后**比改判前更不 fail-safe**（none→潜在 pass）。design/spec/adr 已登记为「无 producer 产出、须手工越权伪造、已知不覆盖」（旧 88 归档无一 `---` 打头，稳态事实成立），故**不是漏**，但「两侧同向 fail-safe」措辞在过渡/旧档语境不成立。
- 裁决：**采纳（措辞精确化）**。限定为「**目标态**两侧同向 fail-safe」，Risks 点明「T74 用 live 侧止崩换归档侧一处（producer 不产出的）杂交面 none→潜在 pass」。

### BR-3【置信高·严重度中】`ALL_ANCHORS` 收缩会压垮既有归档语料契约测试
- 证据：`test_gate_anchor_scope.py:150` `test_contract_archived_corpus_anchor_hits` 用 `_sg.ALL_ANCHORS` 扫归档语料、L153 `assert DESIGN in exclusive`。ADR-3 说 `ALL_ANCHORS` 收缩为 verify-only → 收缩后 `_line_scoped_hits(text, ALL_ANCHORS)` 不返回 design 锚 → `exclusive` 不含 DESIGN → **AssertionError**，与 proposal Success Metric「pytest 全绿」直接冲突。且同文件混装可删孤儿（`anchors_in` L24-50 / `pick_exclusive` L84-97）与**保留路径守卫**（`_line_scoped_hits` L53-57、`archived_verify_state` L60-107），实现者见文件名「删孤儿」有整文件删、连带丢保留路径语料契约的 DX 风险。
- 裁决：**采纳**。tasks 补外科处理：删 `anchors_in`/`pick_exclusive` 测；`test_contract_archived_corpus_anchor_hits` **改写**为局部 verify 锚列表 `[VPASS,VFAIL]` 扫语料、去 `DESIGN in exclusive` 断言（gate 从不从归档读 design/CR 锚，该断言测的是消费不到的东西）；`_line_scoped_hits`/`archived_verify_state` 测**保留**。

### BR-4【置信高·严重度低】DX 诊断可加纯结构 reason 增强（决策登记）
- 证据：漏闭合→absent→开发者见 `decide():699`「缺 design-approved 锚」或「无锚重跑」，但他**确实写了** frontmatter（漏闭合行被当正文）。改判前 `unterminated`→UNKNOWN reason 至少指向 frontmatter 结构；改判后线索归零、误导向「你没写」。design Risks 把「不纳入意图（弃 candidate②）」推广成「不加任何诊断」——**二者可分**：emit reason 加纯结构观察「首行为`---`但未见闭合`---`，已按正文处理；欲声明状态请补闭合行」**不是**意图探测（candidate②=探测下一行是否 `key:` 形态），不改 verdict、不重开自指、不复崩。
- 裁决：**决策登记（需拍板）**——可选增强 vs 保持最简；是否纳入本 change scope 留设计门定（见报告决策区）。

## Eng 已审·未发现问题（背书）
- absent 三读点不放行成立（逐点核码 + 两附带读点安全）；死符号运行时零引用；unterminated 退役无第三方依赖（仅 test_frontmatter_parse.py:26-28）；边界 BOM/CRLF/空白 pre-existing、T74 只把无闭合从崩→absent 方向更安全。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="ok" findings="1" truncated="false" -->
