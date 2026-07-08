## Context

`ship_gate.py` 的 `parse_ship_gate_frontmatter(text)`（`sdflow-ship/scripts/ship_gate.py`）是 mlh-p5 迁移后 live 与归档共用的唯一 frontmatter 解析核心。其首块边界判定逻辑（现状核验，行号为合并 `d94c385` 时快照）：

```python
# L307-308
if not lines or lines[0].strip() != "---":
    return {}, None                     # absent：无首块 frontmatter
# L309-315
end = None
for i in range(1, len(lines)):
    if lines[i].strip() == "---":
        end = i; break
if end is None:
    return {}, ("frontmatter", "unterminated")   # ← T74 焦点：无闭合 → 判「坏」
```

当报告首行是 `---` 且全文再无第二个 `---`，现判 `unterminated`（坏）→ live 侧 `live_ship_gate_state` 经 `_fail_closed_on_bad` emit `UNKNOWN(exit 6)`，硬崩一份本该走无锚语义的干净报告。当前语料侥幸不触发（报告均以 `#` 起），故 P5 code-review 标 A2「方向安全」defer。

**动机不止是"补个边界"**——现有 spec-workflow 内部两条 Scenario 措辞打架：

- 「frontmatter 只认文件首块」（A2，spec L374-376）：首块 = 第 1 行 `---` **到下一个 `---` 止**的唯一块。
- 「写坏 fail-closed」（spec L366-368）：① `---` 起止界定缺失/**不配对** → fail-closed。

按 A2 的首块定义，「没有下一个 `---`」意味着**首块根本不成立** = 无 frontmatter = absent；但 fail-closed Scenario 却把「不配对」打成「坏」。本 change 朝 A2 方向统一二者。

**约束**：`ship_gate.py` 是 bundle 权威源（经 `sdflow-init update` 下发消费仓）；`parse_ship_gate_frontmatter` 手写 stdlib、保零依赖不变量；机械层红线 = fail-closed + 可观测 + pytest 覆盖坏输入。

## Goals / Non-Goals

**Goals:**
- 「首行 `---` 无闭合」由 `unterminated`(坏) 改判 `absent`(无 frontmatter)，根除对 `---` 打头正文的误崩。
- 弥合 spec-workflow「只认首块」与「写坏 fail-closed」两 Scenario 的措辞张力（MODIFIED delta）。
- 退役 `unterminated` 死类别 + 清理 Task6 遗留的 live inline 死代码（anchors_in/pick_exclusive/ANCHOR_DESIGN/ANCHOR_CR_*）。

**Non-Goals:**
- 不动 P6（recorder 索引→frontmatter，north-star）。
- 不改归档 dual-read（`archived_verify_state` inline 兜底 + frontmatter 优先逐字不变，`_line_scoped_hits` 保留）。
- 不改其他坏类别（越域/重复键/tab/类型不符）的 `UNKNOWN(6)` 语义。

## Decisions

### ADR-1（TG-23）：「首行 `---` 无闭合」判 absent，而非 unterminated fail-closed

**接地前提（读码坐实，非记忆）——live 三个读点 `absent` 均不放行**〔grill-amendment Q1：补全 code-review 步 + 退出码 + next 语义，前两版表漏 code-review 且未澄清 exit 0 语义〕：

| 步 | 代码位（符号锚，抗行号腐蚀〔spec-review GR-1〕） | absent(=None) 下游 | 退出码 | next（编排器动作） |
|---|---|---|---|---|
| design | `decide()` design pre-flight：`sr_state = live_ship_gate_state(report,"spec-review")` | `sr_state=None` → `design_ok=False` → REFUSE_START | **3**（拒绝码） | 停，补设计门 |
| code-review | `decide()` code-review 门：`cr_front = live_ship_gate_state(cr,"code_review")` | `cr_state=None` → STEP_IN_PROGRESS | **0**（可推进码） | **重跑本步** `sdflow-code-review` |
| verify | `decide()` verify 终门：`vf_front = live_ship_gate_state(vf,"verify")` | `v_state=None` → STEP_IN_PROGRESS | **0**（可推进码） | **重跑本步** `sdflow-done` |

**⚠️ exit 0 ≠ 放行（对抗镜必戳点）**：code-review/verify 的 absent 返回 `EXIT_OK=0`（可推进码），直觉上像放行，但 `emit()` 的 `next` 字段指向**重跑本步**（`sdflow-code-review`/`sdflow-done`），编排器据此**原地重跑、不前进到下一步或 merge**。真正「放行到 SHIPPED」**唯一路径** = verify 落 `PASS` 锚 + change 归档 + base 树可达（`decide()` 开头 D3 短路 L660-689）；absent 永远进不了该路径（三步任一 absent 都在其之前拦停/重跑）。故「absent 不放行」成立，其依据是 **next 语义**而非退出码符号。

∴ `unterminated(UNKNOWN=6)` 相较 `absent` 的唯一实质差别 = 【硬崩逼人修】 vs 【走无锚常规语义（REFUSE_START / 重跑本步）】，**两者都不放行，fail-closed 在此无实际保护对象**。T74 由此从「安全问题」降格为「诊断精度问题」。

> **归档侧影响（订正原「只影响 live」事实错误）**〔grill-amendment Q2〕：`archived_verify_state`（`decide()` D3 短路的 SHIPPED 判据源）**共用**同一 `parse_ship_gate_frontmatter`，改判 absent 对归档侧行为**亦变**（非无影响）——详见 ADR-4。目标态论证结论：live/归档**目标态两侧同向 fail-safe**，原「T74 只影响 live」为事实错误、已订正。

**决策图（parse 首块归类，本 change 只挪 ★ 一格）**：

```
报告首行?
  ├─ 非 "---"  ──────────────────────────► absent ({}, None)     [不变]
  └─ "---"
       ├─ 存在第二个 "---"（首块闭合）
       │     ├─ 块内 ship-gate 键坏（越域/重复/tab/类型）─► UNKNOWN(6) [不变]
       │     ├─ 块内无 ship-gate 键 ──────────────────────► absent    [不变]
       │     └─ 块内有效键 ──────────────────────────────► state     [不变]
       └─ 无第二个 "---"（首块不成立）
             现状: ─► unterminated → UNKNOWN(6) 硬崩       ★ 本 change 挪为 ↓
             改判: ─► absent ({}, None)                    ★ 无闭合 ≠ 坏
```

**候选对比**：

| | 判据 | 误崩面 | 复杂度 | 自指风险 |
|---|---|---|---|---|
| **①（采纳）** | 无闭合 → absent | **根除** | 最低（改 1 行返回值） | **免疫** |
| ② | 无闭合时探测「下一非空行是否 `key:` 形态」，是→unterminated 否→absent | 收窄未根除（正文 `Status: WIP` 形态散文仍崩） | +启发式+测试面 | **加剧** |
| ③（现状） | 维持 unterminated→UNKNOWN | 全 `---` 打头正文误崩 | — | 最高 |

**采纳①的理由链**：
1. **安全等价**（上表已坐实）：absent 在 live 各步不放行，改判不引入任何假过面。
2. **语法本真**：无闭合就不构成 frontmatter block，absent 是正确判定而非妥协；且与 A2「首块 = 到下一 `---` 止」定义自洽（消除 spec 内张力）。
3. **★ 决定性理由——自指免疫**：本仓报告正文经常讨论 ship-gate frontmatter（design/review 报告满是 `ship-gate:` 示例块）。候选②的「下一非空行是 `key:` 形态」会在「讨论 gate 自身」的报告上**精准命中→误崩**，重蹈 `gate-substring-detection-dogfood`（本仓 gate 检测在讨论 gate 的 change 上假阳）覆辙；候选①对此免疫。
4. **最简根除**：改 1 行返回值，根除所有 `---` 打头正文的误崩；候选②加启发式却没根除、还扩测试面，与机械层「简单可测、勿塞过度启发式」取向相悖。

### ADR-2：unterminated 死类别退役（①的连带）

①落地后 `unterminated` 成永不产生的错误类别。为免留「看似可达实则死」的枚举误导读者：从 docstring 的 `category ∈ unterminated|duplicate-key|out-of-domain|bad-type|tab-indent` 移除 `unterminated`；测试中原断言 `unterminated` 的用例改为断言 `absent`（`({}, None)`）。**不做**：不保留 unterminated 作「向后兼容常量」——它无任何外部引用，保留即死代码。

### ADR-3：T75 死代码删除范围与保留边界

Task6 退役 live inline 读半场后，下列符号只剩 test 引用的孤儿，删除：
- 函数：`anchors_in`（L395）、`pick_exclusive`
- 常量：`ANCHOR_DESIGN`（L125）、`ANCHOR_CR_PASS`（L128）、`ANCHOR_CR_BLOCKED`（L129）；`ALL_ANCHORS`（L130-131）随之收缩。

**保留边界（读码核实，勿删）**：
- `ANCHOR_VERIFY_PASS` / `ANCHOR_VERIFY_FAIL`：`archived_verify_state` 归档 inline dual-read 真用（L202、L205）。
- `_line_scoped_hits`：归档 dual-read 现役唯一调用方（L263 注释已声明），保留。

### ADR-4〔grill-amendment Q2〕：归档侧影响按 producer 契约 + 目标态论证，目标态两侧同向 fail-safe（升 `adr/0011`）

**订正事实错误**：改判 absent **不只影响 live**——`parse_ship_gate_frontmatter` 有**三个**调用方〔spec-review BR-1/TC-1：初稿漏数，三镜独立命中〕：`live_ship_gate_state`(L477)、`archived_verify_state`(L196，D3 短路 SHIPPED 判据源)、**`anchor_set`(L412，熔断状态集 helper)**。**anchor_set 侧行为不变**（`err≠None` 旧 unterminated 与 `state={}` 新 absent 两路都 `→ frozenset()` 空集，熔断进展判据无净变化倾向，安全；须 pytest `test_anchor_set_absent_on_unclosed_frontmatter` 钉死不变量——见 tasks 3.6）。归档侧处置随之变：

```
                          现状(unterminated)          改判后(absent)
archived_verify_state:    err → return "none"          absent → 回退 inline dual-read
                          (fail-safe 不回退)            (L201-208 扫 ANCHOR_VERIFY_PASS/FAIL)
```

**安全论证 MUST 锚 producer 契约 + 目标态，MUST NOT 以迁移现状评估**（`adr/0011`）：`sdflow-done` verify 模板（SKILL.md L76-95）MUST prepend frontmatter、**不写 inline 锚**（实证 mlh-p5 归档 verify-report：正文 inline 锚数=0）。故目标态归档报告 = frontmatter-only，据此重估：

| 目标态归档形态 | 首块 | T74 后处置 | 结果 |
|---|---|---|---|
| 正常（配对闭合 frontmatter） | 成立 | 走 `"verify" in state` | 不受 T74 影响 |
| **漏闭合畸形**（LLM prepend 漏第二个 `---`） | 不成立 | absent → 回退 inline → **正文无 inline 可扫** | `none` → 不 SHIPPED（**fail-safe**） |

**结论**：live 侧漏闭合 → absent → REFUSE_START/重跑（不放行）；归档侧漏闭合 → absent → 回退 inline 扫空 → `none`（不 SHIPPED）——**目标态两侧同向 fail-safe**。初版所谓「归档侧回退 inline 判假 pass」需「`---` 打头 × 正文 inline PASS 锚」杂交形态，**无 producer 会产出**（未来 producer 不写 inline、旧 producer 首行 `#`），须手工伪造归档 = 显式越权（`adr/0008` 立场，git 可审计）→ 登记入 `ship_gate.py`「已知不覆盖」。

**为何不给归档侧特殊 fail-safe（选 ①绝，非方向 C）**：目标态归档侧对漏闭合本就 fail-safe，为 producer 不产出的杂交形态引入「无闭合」双语义会破坏 A4「共用严格核心」防漂移收益，ROI 负。

### ADR-5〔spec-review Q1=A 拍板〕：absent「首行 `---` 无闭合」子形态加纯结构诊断提示

**决策**：设计门拍板 Q1=A 纳入。live 读点遇 absent 且盘面为「首行 `---` 但无闭合」时，emit reason 附一句**纯结构**提示（如「首行为 `---` 但未见闭合 `---`，已按正文处理；欲声明状态请补闭合行」），恢复 DX actionability——防漏闭合 frontmatter 的开发者被「缺锚/你没写」误导。

**实现约束（load-bearing，防实现走偏）**：
- **纯结构 ≠ 意图探测**：只报客观结构（首行 `---` + 无第二个 `---`），MUST NOT 探测「下一非空行是否 `key:` 形态」（candidate②，已因自指风险弃）；不重开自指免疫。
- **不改 verdict**：仍判 absent → REFUSE_START(spec-review) / STEP_IN_PROGRESS(code-review·verify)，提示只进 reason 文案，MUST NOT 改退出码或放行语义。
- **MUST NOT 改 `parse_ship_gate_frontmatter` 返回签名**〔遵 adr/0011〕：为区分「首行 `---` 无闭合」absent 子形态，走 **live 读点上层独立轻量结构判定**（re-check 首行 `---` 且无闭合），MUST NOT 给 parse 加 hint 字段——否则再次波及三调用方（`anchor_set`/`archived_verify_state`/`live_ship_gate_state`），重蹈本轮 BR-1 覆辙。归档侧与 anchor_set 侧 MUST NOT 受此 DX 提示影响（提示仅 live 诊断用途）。
- 测试：断言「首行 `---` 无闭合」live 报告的 emit reason 含结构提示子串，且 verdict/退出码不变。

## Risks / Trade-offs

- **[诊断精度损失]** 报告真想用 frontmatter 声明状态却忘闭合 `---` → 判 absent → verify 走「未验」→ 不 SHIPPED，人看到的是「无锚」而非「unterminated 未闭合」。→ **可接受且方向安全（假阴漏判，非假阳假过）**，与 `ship_gate.py:115` 已登记接受的 "false absent → 方向安全" 完全同构；且 producer SKILL 模板产出的 frontmatter 均配对闭合，此情形属边缘中的边缘。
- **[归档侧共用核心行为变化]**〔grill-amendment Q2；spec-review BR-2〕 改判 absent 经共用 helper 波及 `archived_verify_state`：「首行 `---` 无闭合」归档报告由 `none`(fail-safe) 变为 absent→回退 inline dual-read。**「同向 fail-safe」仅在目标态（producer 只写 frontmatter、无 inline）成立**；过渡/旧档语境下该杂交形态（首行`---`无闭合 × 正文 inline PASS 锚）由 `none`→潜在 `pass` 是**净负**——即 T74 用 live 侧止崩换来归档侧此一形态 fail-safe 削弱。→ **Mitigation**：该杂交形态无 producer 产出（未来不写 inline、旧 producer 首行 `#`），须手工伪造归档=显式越权（adr/0008）；登记 `ship_gate.py`「已知不覆盖」；加目标态归档回归测试（tasks 3.5）钉死漏闭合→`none`。
- **[删错保留符号致归档 SHIPPED 回归]** 误删 `ANCHOR_VERIFY_PASS/FAIL` 或 `_line_scoped_hits` → 归档 dual-read 断裂、88 归档报告 SHIPPED 判定回归。→ **Mitigation**：ADR-3 显式钉死保留边界；删除后跑既有归档兼容测试（`test_frontmatter_archived.py` / dual-read 用例）验证不回归。
- **[unterminated 退役漏改测试留悬空引用]** docstring/测试仍提 unterminated → import/断言失败或误导。→ **Mitigation**：grep `unterminated` 与各死符号名，确认源码 + 测试零残留引用作为验收硬门。

## Migration Plan

- 部署：改 bundle 权威源 `ship_gate.py` → 本仓 `setup.sh` 刷 `~/.sdflow/workflow/tools/`；下游消费仓下次 `sdflow-init update` 自然拿到。无需数据迁移（纯解析行为 + 死代码删除）。
- 回滚：`git revert` 本 change 即恢复 unterminated 判定 + 死符号（向后兼容，无状态残留）。

## Open Questions

无。判据在 explore 已敲定并接地坐实，无未决项。

## Compliance

- **bundle 权威源纪律**：改 `sdflow-ship/scripts/ship_gate.py`（skill 源），非下游副本。
- **机械层红线**：absent 仍 fail-closed 取向（不放行、方向安全）；改判 + 死码删除均以 pytest 坏输入断言把关；判断不越权。
- **adr/0004（正文提及不假过门）**：absent 判定后 live 不回退 inline、不扫正文，与既有边界一致。
- **spec 措辞张力弥合**：MODIFIED 后「只认首块」与「写坏 fail-closed」两 Scenario 自洽，无沉默例外。
