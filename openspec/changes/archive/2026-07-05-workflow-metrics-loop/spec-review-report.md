# spec-review 报告 — workflow-metrics-loop

## 命中范围

- **镜阵**：广审（模拟，四视角）· 对抗镜×2（隐藏假设 / 失败模式）· 接地镜×1（核 10 条代码事实）· codex design-voice（跨模型）。**HR-TG=none**（旁路观测锚 + 只读聚合，读错顶多坏度量、非运行期爆炸/数据损坏/安全泄漏）。**无领域镜**（技术栈 Markdown+Python，不命中 backend/embedded/frontend）。
- **锚行**（三类 v1，机判契约）：

<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="旁路观测锚+只读聚合;读错顶多坏度量,非运行期爆炸/数据损坏/安全泄漏" -->

- 合并池实收 ≈ 23 条（广审10 + 对抗1×5 + 对抗2×4 + codex×4；接地镜 10 事实 0 不符=负例确认），去重合并为 **14 簇**（下）。

## 接地镜结论（负例——前提确认成立）

10 条代码事实**全核实、0 不符**：`_line_scoped_hits` 确为存在性检测（ship_gate.py:218）· `源(多源=高置信)` 列真存在记命中镜集合 · harness `duration_ms` 全仓零捕获 · `voice分桶` prose 格式属实 · outside-voice v1 锚从未被解析字段 · `design-approved` 锚存在 · `workflow/tools/` 存在（现装 UI 资产）· **design.md 示例锚确在 ``` fence 内（自指坑被 fence 保护）** · checkpoint 标签前缀可解析 · spec-workflow 是既有能力。→ 设计的代码事实主张扎实。

---

## 决策登记区

### [自动决策]（高置信，已 amend，设计门可覆盖）

| ID | 簇（来源镜） | 裁决 & amendment |
|---|---|---|
| SR-A | 回路空转/surfacing 无 hook（**广审 F-CEO-1 + 对抗2-3，高**） | 加 `/sdflow-maintain` 机械收尾检查步：`出现轮数≥10 未复评` 显著提示（呼应 grill-not-skippable）。spec + task 4.1b |
| SR-B | findings 数值一致性自检机制未设计（**广审 F-ENG-1，高**） | 诚实降级：机械层只兜「存在+枚举域+sev 子格式」；数值一致性=主 session 信任边界（自做去重又写锚、自核无独立性，同 verify judgment）。spec Scenario 新增 |
| SR-C | 枚举值/折叠正确性无校验（**对抗1-1a，高**） | 自检扩「`layer/lens/runner/sev` 取值越域也阻塞」（枚举成员机械可验）。spec + task 2.3 |
| SR-M | spec-review 采纳/裁掉在设计门**前**落锚可能非最终（**codex OV-1，高**） | spec-review 度量锚在**拍板回写时最终化**（与 design-approved 锚同步），反映门后裁决；code-review 无人类门故对称。spec-workflow 新增 |
| SR-L | code-review `broad`(gstack) 未显式列 + broad findings 口径未定义（**codex OV-2 + 广审 F-DES-3**） | spec-workflow scenario 显式列 broad；`broad` findings=汇总 gstack-review 去重后计入 |
| SR-H | Success Metric #2 依赖不存在的归档数据、verify 会卡壳（**广审 F-ENG-3 + 对抗2-2**） | reword：本 change 验收=pytest fixture；真实归档聚合=部署后观察项，非 verify 门槛 |
| SR-I | `sev` 子格式未定义完整 + 反例矩阵未测（**广审 F-DES-1**） | 钉 `致N/高N/中N/低N` 定序/零写0/分隔恒`/`；task 3.3 加 sev 健壮反例 |
| SR-E | enum 6 值无扩展治理，新镜静默塞 broad（**对抗1-4，中**） | 契约加治理：新镜 MUST 升 v2+更折叠表，MUST NOT 塞 broad |
| SR-J | 「不产合成分」场景残留「成本分列」（**codex OV-3**，Q1-A 漏网） | 删「成本分列」→ findings/独立/出现轮数分列 |
| SR-K | 落点 `workflow/tools/` 路径不确定（**codex OV-4 + 接地#7**） | 精确到 `sdflow-init/assets/workflow/tools/`（权威源，勿改派生副本） |
| SR-N | 自指坑残差：报告未 fence 的示范锚（**对抗2-1，低-中**） | 直白版已证伪；TG-25 契约加 MUST「报告示范锚 MUST 包 fence」闭合 |

### [需拍板]（≥2 真方案，设计门定）

**Q1 · 同轮 outside-voice 多 site 撞键（SR-D，对抗1-1b，中高）**
- 现实：code-review 同轮有 `code-voice`(always) + `hr-tg`(条件)，两次 codex 调用折叠成同一 `(code-review,outside-voice,codex)` → 四元组撞键。现有报告特意把 hr-tg 与泛检当两个「源」记（价值预期不同）。
- **三面后果**：系统镜——撞键行聚合器行为未定义（两行同 key / 加总抹区分）；用户镜——无差别；开发循环镜——若加总，"outside-voice 值不值得留"（正是本命题）因两质地混一失真、方向不可预测。
- **选项**：**A（推荐）加可选 `site` 消歧字段**（不进 lens enum、只消歧，保 hr-tg vs 泛检信号）｜ B 钉死合并规则（求和，丢区分，但 schema 简单）。
- **主次**：开发循环镜主导 → A——本命题就是量化各源价值，抹掉 site 区分自毁核心信号；`site` 成本极低（一个可选字段）。

**Q2 · 消费仓 opt-out（SR-G，广审 F-DX-1 + 对抗2-4，中）**
- 现实：无条件 SHALL 落锚 + 缺字段硬阻塞随 bundle 推**所有**消费仓；低频小仓永达不到 10 轮、聚合表长期空，却 100% 承担记账+硬阻塞成本、0 收益期。
- **三面后果**：系统镜——bundle 强推一个多数下游用不上的强制义务；用户镜——下游用户因「每轮必落锚、缺字段报错」困惑，反馈绕回 sdflow-init 维护者；开发循环镜——源仓（本仓，高频 dogfood）需要它，下游多数不需要。
- **选项**：**A（推荐）`config.yaml` 开关**（默认源仓 on / 下游 off，或下游自检降软警告）｜ B 无条件全推（接受下游负担，KISS）。
- **主次**：系统镜主导 → A——bundle 基础设施不该把「只有高频仓用得上」的义务硬铺给所有下游；开关是「被看见、被主动接受」而非隐性负担。

### [已裁掉 / 降级]（反静默压制，可审计）

- **X1** 对抗2-1 自指坑**直白版**（聚合器误取 design.md 示例锚）——接地证伪：glob 仅 `*-review-report.md`、design.md 不命中、示例锚在 fence 内。残差（报告未 fence 引用）已转 SR-N 闭合，非静默丢。
- **X2** 广审 F-ENG-2 硬阻塞挂旁路系统——**降级**：与现有 R1/R3/R5 锚自检硬阻塞一致，阻塞是「报告完整性」本步可补锚，非永久卡死；消费仓过重部分并入 Q2。不单独 amend。
- **X3** 对抗1-2 dedup 系统性漂移 / 对抗1-3 子代理失败 vs 真 0findings 无区分态——**采信为诚实声明**（非阻塞）：已入 design Risks；失败协议根治超 P0，defer todolist。
- **X4** 广审 F-CEO-2（ROI 未量化）/ F-DX-2（SKILL 自检清单变长后续抽象）——接受/记，不阻塞。

---

## 锚行自检

三类 v1 锚齐备（step1-broad-review×1 mode=simulated / outside-voice×1 site=design-voice runner=codex findings=4 / hr-tg×1 hit=none 带 evidence）。outside-voice `findings=4` 与 codex 实收 4 条一致 ✓。合并池 23→14 簇，去重记录见决策登记区。

## 结论

- **11 项 [自动决策] 已 amend**（标 `[spec-review-amendment]`，validate valid）。
- **2 项 [需拍板] 设计门已拍板**：**Q1=A**（加可选 `site` 消歧字段，键升 `(layer,lens,runner,site,轮)`）· **Q2=A**（`config.yaml` 度量开关，源仓默认 on / 消费仓默认 off）——已落契约 spec/design/tasks（4.1c/4.1d），validate valid。
- 接地诚实度高、代码事实 0 不符；grill 已消 3 处致命，spec-review 再补 11 处设计缺口 + 2 项拍板收敛。

## 拍板记录

用户 2026-07-06 过本报告，Q1=A / Q2=A 拍板，批准进阶段三（writing-plans）。

<!-- ship-gate: design-approved -->
