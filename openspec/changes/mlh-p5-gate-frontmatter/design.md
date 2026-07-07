## Context

ship-gate 的三类结论（设计门 / verify / code-review）当前以 inline HTML 注释锚承载在报告**正文**：

```
<!-- ship-gate: design-approved -->      spec-review-report.md
<!-- ship-gate: verify=PASS|FAIL -->     verify-report.md
<!-- ship-gate: code-review=pass|blocked --> code-review-report.md
```

`ship_gate.py` 用 `_line_scoped_hits`（`ship_gate.py:218`）做**行级字面查找 + fence-aware**解析。此核心被两处共用：

- `anchors_in`（读 **live** 报告文件）→ 判 design-approved / verify / code-review 结论。
- `archived_verify_state`（`ship_gate.py:151/485`，git-show 读**归档**报告文本）→ 判 base 已并 change 的 verify 态、SHIPPED。

**现状问题（B4/B5）**：inline 锚与人读正文同处一个文本平面。B4 用「行级 + fence-aware」缓解了正文对锚串的**描述性提及**误判，但 B5 自认**非根治**——只要正文在非 fence 行原样写出锚字面（对账清单、示范、讨论），仍假命中。**实测活证据**：归档 88 个报告文件含 168 行 ship-gate 锚，其中 `ship-gate: X` / `ship-gate: --` / `ship-gate: tg=` / 空值等**噪声锚**（正文讨论锚串处）与真结论锚混处同一解析平面。

**核实落定（起手第一步，红线 5）**：
- 归档 inline 锚 = **88 文件 / 168 锚行**（design-approved 66·verify=PASS 50·code-review=pass 38·verify=FAIL 13·code-review=blocked 7 + 少量噪声）——**订正** roadmap 的「57 约数 / ~39」为实测 88 文件（F6）。这是 dual-read 归档读语料的真实范围。
- `ship_gate.py` **只在 `sdflow-ship/scripts/`、走 skill symlink、非 bundle 回灌消费仓**（survey 实测）→ 迁移不触 `sdflow-init update` 下发链、消费仓 tools/ 侧零改动。

**stakeholders**：`sdflow-ship` 编排器（消费 gate 判定）、三 producer SKILL、本仓 dogfood。

## Goals / Non-Goals

**Goals:**
- gate live 报告结论从**正文 inline 锚**迁到**报告 YAML frontmatter**，使正文平面与状态平面彻底分离，根治 B4/B5 类正文提及假命中。
- 迁移**零门禁语义漂移**：退出码、UNKNOWN 冲突判定、checkpoint 命名空间隔离、新鲜度分域等既有契约不变。
- 归档 88 文件 inline 锚经 dual-read **永久保留正确识别**。
- 写坏 frontmatter → **fail-closed**（判无有效状态、gate 停下报告，绝不静默过门）。

**Non-Goals:**
- 不迁家族②（recorder 索引，roadmap 阶段 6 north-star）。
- 不删归档读半场（`archived_verify_state` 的 inline 读永久保留，归档不可变）。
- 不迁度量层锚（lens-metric/outside-voice/hr-tg/step1，roadmap 决策 3 保留 HTML 注释 KV 载体）。
- 不触 bundle 回灌链（ship_gate 非 bundle）。

## Decisions

### D1：live 报告读 frontmatter；归档报告 frontmatter+inline **双读** —— 按路径分流

**决策**：gate 按报告路径分流解析——
- **live**（`openspec/changes/{change}/*.md`）：**只读 frontmatter**（正文平面隔离，B4/B5 根治）。
- **归档**（`archive/<date>-{change}/*.md`）：**frontmatter + inline 双读**〔grill G2 订正〕——**frontmatter 优先，无则回退 inline**。

**grill G2 关键订正（原「归档读纯 inline」不完整）**：迁移后 `sdflow-done` **归档的**报告本身就是 frontmatter 格式（producer 已迁），故 `archived_verify_state` 读归档时会遇**两种**语料——**迁移前旧归档 = inline 锚**、**迁移后新归档 = frontmatter**。因此归档读**必须双读**：新增 frontmatter 读（认迁移后新归档）+ **永久保留** inline 读（认迁移前旧归档，`_line_scoped_hits` 归档半场）。原 design 把归档简化为「只读 inline」只对迁移前旧归档成立，会让**迁移后新归档的 verify=PASS 判不出 → SHIPPED 回归**。

**理由**：归档报告是历史事实、不可回改。inline 归档半场永久保留（旧归档不可变，冷审 F2）；frontmatter 归档读是迁移的必然结果（新归档即 frontmatter）。gate 已有 active/archive 分流逻辑（假设 A3），分流点天然存在。

**Alternatives 考量**：
- **A. 回填 frontmatter 进历史归档**（让旧归档也走 frontmatter、可省 inline 读）→ 改 88 个不可变历史文件、篡改归档纪律，否决。
- **B. 归档只读 inline**（不加 frontmatter 读）→ **迁移后新归档 verify=PASS 判不出、SHIPPED 回归**（grill G2 证伪），否决。
- **C. live 也保留 inline 双写**（frontmatter + inline 都写）→ 没消除正文平面锚、B4/B5 未根治，违背立论，否决。

### D2：frontmatter 状态 schema —— 极简三标量字段

**决策**：报告 frontmatter 承载单一终态，schema：

```yaml
---
ship-gate:
  design_approved: true          # spec-review-report.md（bool；缺省/false=未拍板）
  verify: PASS                   # verify-report.md（枚举 PASS|FAIL）
  code_review: pass              # code-review-report.md（枚举 pass|blocked）
---
```

每报告只落**自己那一类**字段（spec-review 报告只写 `design_approved`，verify 报告只写 `verify`，code-review 报告只写 `code_review`）。字段值域**严格枚举**，越域/缺字段/类型不符 → 判无有效状态（fail-closed）。

**理由**：家族① 是「每报告一个终态」的整块状态（roadmap 决策 3），schema 极简 → 手写解析 + 严格校验可完全掌控 fail-closed。保留 `ship-gate:` 顶层命名空间键，避免与报告可能已有的其它 frontmatter（title/date）冲突。

### D3（grill 已决 = 手写 stdlib）：frontmatter 解析用手写 stdlib，不 import yaml

**决策（grill 拍板，用户确认）：手写 stdlib 极简 frontmatter 解析（不 import yaml）**，与 `anchor_lint.py` / `config_lint`（P3）零依赖惯例一致。

**判据与理由**：
- **`ship_gate.py` 零第三方依赖是硬不变量**（grill 查代码核实）：现有 import 仅 `argparse/json/re/subprocess/sys/pathlib`——**全 stdlib**。gate 是**门禁**，`import yaml` 会让它在**任何**缺 PyYAML 的环境（其他开发者机 / CI / 裸 python3）崩溃 = **无判定**（比 fail-closed 更糟）。判据不是「本机有无 yaml」（本机实测 PyYAML 6.0.3 可用），而是**不赌所有运行环境 + 门禁不能因缺库崩溃**——本机有 yaml 不改变结论。
- 本仓已有**两例先例**（`anchor_lint.py`、P3 `config_lint`）证明「手写 stdlib 行扫描解析结构化头部」可行且可控。
- frontmatter schema 极简（`---` 界定 + 顶层 `ship-gate:` 键 + 一层标量字段），手写解析 trivial；手写能对坏输入精确控制 fail-closed 语义（safe_load 异常类型面更宽、更难穷举断言）。

**Alternatives 考量（否决）**：
- **A. `yaml.safe_load`**（roadmap design.md 决策 6 原倾向）→ 破坏 ship_gate 零依赖不变量、赌运行环境 PyYAML。roadmap 那句写在 P3「手写 stdlib」先例**之前**、未权衡门禁 `import` 崩溃面。**否决**。
- roadmap design.md 决策 6 / tech-stack 表的 `yaml.safe_load` 提法据此 grill 结论**订正为手写 stdlib**（收尾回填，tasks 6.1）。

**手写解析器攻击面（grill G4，fail-closed 穷举）**：解析器 MUST 显式处理——① 缺 `---` 收尾 → 无有效 frontmatter；② 顶层 `ship-gate:` 键**重复** / 同字段（如 `verify:`）**重复键** → 判 UNKNOWN/fail-closed（手写须显式判重，MUST NOT 静默取最后一个——safe_load 的默认取后行为在此是危险的假定）；③ tab 缩进 / 混合缩进 → 拒；④ 值含前后空白 → strip 后严格枚举；⑤ 字段值非枚举成员 → fail-closed。每条 MUST 有 pytest 坏输入用例断言判定不能。

### D4：退役仅 live inline 读半场；归档读 = frontmatter + inline 双读

**决策**：迁移收尾时删 `anchors_in` 对 **live 报告**的 inline 读（`_line_scoped_hits` **live 半场**）；`archived_verify_state`（`ship_gate.py:151/485`）的**归档读双读永久保留**——① inline 读半场（`_line_scoped_hits`，认迁移前旧归档）**永久保留**（冷审 F2）；② **新增** frontmatter 读（认迁移后新归档）〔grill G2〕。

**理由**：见 D1 + G2。live 侧退役 inline 读（正文免疫）；归档侧因新旧两种语料必须双读，`_line_scoped_hits` 归档半场是其中的 inline 分支，永久留存。这是 S1 change 的收尾任务，非全删。

### D5：门禁语义与锚字面不变，仅换承载层

**决策**：退出码语义（0/3/4/5/6）、UNKNOWN 冲突判定、checkpoint 命名空间隔离、design-approved 新鲜度分域、复选框辅通道等既有契约**全部不变**。frontmatter 只替换「结论状态从哪读」，不改「读到后怎么判」。

### D6：过渡期 live 读「frontmatter 优先，回退 inline」——渐进迁移（grill G3）

**决策**：迁移三态区分——
- **过渡期**（Migration 步骤 1–3，producer 未全迁）：live 读 = **frontmatter 优先，无 ship-gate 键则回退 inline**。已迁 producer 的报告立即走 frontmatter（正文免疫）；未迁 producer 的报告仍走 inline（兼容）。**每迁一个 producer，那一类报告即刻免疫**——渐进、任意中间态可用（符合 Migration Plan「dual-read 保证中间态」）。
- **终态**（步骤 4 后）：live 读 = **只读 frontmatter**，删 inline 回退（D1 决策的终态）。

**已知短时取舍（登记）**：过渡期内**未迁** producer 的 live 报告，其正文对锚串的提及仍有 B4/B5 假阳风险——但该风险仅存于「该 producer 尚未迁移」的短时窗口，迁完即消。**不因过渡期未根治而阻塞**（roadmap 决策 6 兼容矩阵：回退安全）。

**理由**：原子全体切换（live 只读 frontmatter、producer 必须一次全迁）会让迁移期未迁 producer 的报告 gate 读不出 → 破坏。渐进回退是「dual-read 保证中间态可用」的直接落实。

### D7〔spec-review-amendment〕迁移影响面订正（冷审 1 致命 + 3 高）

多镜冷审揭示迁移影响面被系统性低估，以下并入 specs「迁移正确性五铁律」，design 层补记：

- **D7a（致命，= specs A1）live 读点完整集合**：live inline 读点不止 `anchors_in`——真实代码里 verify/code-review 结论走 `pick_exclusive`(ship_gate.py:519/563/588)、peek `anchors_in`(576)、熔断走 `anchor_set`(250)。D4「退役仅 live 半场」原表述「删 anchors_in 对 live」**不完整**，会让迁移后 verify/code-review 读不出 → STEP_IN_PROGRESS 永卡。订正：退役/frontmatter 化范围 = 全部 live inline 读点（anchors_in-design + pick_exclusive×3 + peek + anchor_set），实现起手先产「live 读点清单」。
- **D7b（高，= specs A2/A3）解析契约收紧**：D3「trivial」下修——① 只认文件第 1 行 `---` 首块（报告正文 `---` 横线密布）；② 坏≠无键（坏永不回退、直接 fail-closed）；③ 坏输入→退出码确定映射（越域/重复键/坏语法→UNKNOWN(6)、纯缺字段→既有无锚语义 3/0），消除「停下或进行中」歧义。G4 攻击面补 BOM/CRLF/空标量/嵌套>1层/内嵌---。
- **D7c（高，= specs A4）共用严格核心**：live 与归档 frontmatter 读须共用单一自持 helper（防 `_line_scoped_hits` 式漂移），归档坏 frontmatter → fail-safe none 不回退 inline。
- **D7d（= specs D5）D5 措辞订正**：冲突判定触发承载从行级并存 → 重复键，等价性仅「歧义即不放行」层。
- **D7e（D9）frontmatter 写入 = 文件头 prepend/merge**：现三 producer 报告均无 frontmatter，拍板/结论锚现写「报告末尾」→ 迁 frontmatter 是**文件头 prepend**（无既有 frontmatter）或 **merge**（若报告将来带 title/date frontmatter 则往其加 `ship-gate` 键），非追加一行。producer 模板须拆「头 frontmatter + 正文保留人读结论行」，且更新 SR-M 交叉引用（lens-metric 锚仍在正文注释、不迁）。
- **D7f 解析选型残留清理（safe_load）**：D3 已决手写 stdlib，proposal.md「Modified Capabilities」与本 design v_old/v_new 对照表/失败模式表/Mitigation 的 `safe_load`「倾向/若选」摇摆措辞订正为手写 stdlib（safe_load 标已否决存档）；契约测试加 `assert "import yaml" not in ship_gate.py 源码`。
- **D7g（D13）88 降级为叙述**：归档「88 文件/168 锚行」是移动靶，仅作核实落定的一次性背景数字，**从 Success Metric 断言语义移除**；dual-read 测试基于行为（构造 fixture）、MUST NOT 硬编码计数或全量扫 archive/。

## Risks / Trade-offs（TG-08 失败模式表）

| 失败模式 | 严重度 | gate 行为（fail-closed） | Mitigation |
|---|---|---|---|
| LLM 写坏 frontmatter YAML（缩进/语法错） | 中 | 坏语法/越域/重复键 → UNKNOWN(6) 停下报告点名（坏≠无键，不回退）〔D7b〕 | D3 手写解析穷举坏输入断言退出码 |
| frontmatter 缺 ship-gate 字段（半成品报告） | 中 | 判「无结论」→ 不推进（等同旧「报告无锚」STEP_IN_PROGRESS） | 保持既有「报告存在但无结论」判定语义 |
| 字段值越域（verify: MAYBE） | 中 | 严格枚举校验失败 → fail-closed | 枚举白名单，非白名单即无效 |
| 归档 88 文件 inline 锚被误退役 | 高 | —（回归风险） | D1/D4：归档读 `_line_scoped_hits` 永久保留 + dual-read 兼容测试覆盖 88 语料 |
| live 报告同报告 frontmatter + 残留正文 inline 锚冲突 | 中 | frontmatter 为唯一 live 真相源；正文 inline 不再参与 live 解析（正文平面隔离） | 迁移后 live 解析**只**读 frontmatter，正文锚串天然免疫 |
| gate 运行环境无 PyYAML（已否决方案 safe_load 的风险，仅存档） | 高 | `import yaml` 崩溃 = 无判定 | D3 已决手写 stdlib 规避（不 import yaml），此风险不适用最终方案 |
| 迁移引入新静默面（异常吞 + exit0） | 高 | — | adr/0006 R3 红线：新解析路径 fail-closed + pytest 坏输入断言非零 |

## Migration Plan

**部署顺序（dual-read 保证任意中间态可用）**：
1. **先加 gate dual-read**：`ship_gate.py` live 解析先支持「frontmatter 优先，回退 inline」——此时 producer 尚未迁，gate 仍认旧 inline，零破坏。
2. **迁三 producer SKILL**：`sdflow-spec-review`/`sdflow-done`/`sdflow-code-review` 报告模板改写 frontmatter。迁一个、gate 已能读一个。
3. **契约测试迁移** + 88 归档语料 dual-read 兼容测试 + 写坏 YAML fail-closed 测试。
4. **收尾退役 live 半场**：确认三 producer 全迁 + 测试全绿后，删 `anchors_in` 的 live `_line_scoped_hits` 调用（归档读保留）。

**Rollback**：dual-read 窗口内，回退某 producer SKILL 到写 inline 锚即可——gate 仍认旧 inline（回退安全，roadmap 决策 6 兼容矩阵）。

## Open Questions

- ~~**Q1（= D3）**：手写 stdlib vs `yaml.safe_load`~~ → **grill 已决：手写 stdlib**（ship_gate 零依赖不变量 + 门禁不崩，见 D3）。
- **Q2〔spec-review-amendment，升 P0 决策门〕**：三类报告注入 `ship-gate:` frontmatter 后 `openspec validate`/`archive` CLI 是否报错？归档走 `openspec archive`（禁手动 mv），若 CLI 解析 report frontmatter 并对未知键报错则归档步炸。风险实际偏低（validate 只吃 proposal/tasks/specs、report 非校验对象——接地/领域镜均判低风险），但 **MUST 在写任何 producer 前实测 GO/NO-GO**（tasks 1.1 从「核」升为 P0 决策门）。
- ~~**Q4**~~ → **设计门已决（frontmatter 有效即采信 + 登记盲区）**：归档 frontmatter 有效 PASS 时 MUST NOT 再交叉扫 inline FAIL——frontmatter 即真相（简单路径）；「好 frontmatter=PASS 掩盖残留 inline=FAIL」的盲区 MUST 在 `ship_gate.py`「已知不覆盖」头注释登记（迁移后新归档不会有残留 inline，风险低）。
- **Q3**：live 报告若同时有 frontmatter 与正文残留 inline 锚，是否需迁移期一次性清正文旧锚？倾向否（live 解析只读 frontmatter，正文锚天然失效），design 定为不强制清、只不解析。

## Compliance

- **adr/0006 硬约束**：新 frontmatter 解析路径 fail-closed + 可观测；pytest 覆盖坏输入（坏 YAML/越域/缺字段）断言非零退出或判定不能。纯机械换承载层，不新增模型判断面（决策 5）。
- **R3 红线（不引入更糙静默面）**：frontmatter parse 失败面比 inline grep 更集中，fail-closed 兜底是迁移前提而非可选（roadmap 决策 6）。
- **workflow bundle 纪律**：`ship_gate.py` 非 bundle 权威源、无下游回灌（假设 A2）；三 producer 为本仓 skill，setup.sh symlink 即生效。若实现中发现 ship_gate 已被纳入 bundle → 停下核对，改权威源 + 走 `sdflow-init update` 回灌全流程，绝不 fold/sweep 行为面路径。

## 附：锚承载形态 v_old / v_new 对照（TG-04）

| 维度 | v_old（inline 锚） | v_new（frontmatter） |
|---|---|---|
| 承载层 | 报告正文 HTML 注释行 | 报告 YAML frontmatter |
| live 解析 | `_line_scoped_hits` 行级字面 + fence-aware | 手写 stdlib 读文件首块 `ship-gate:` 键（不 import yaml）〔D7f〕 |
| 正文提及锚串 | 需 fence-aware 规避、B5 非根治 | 天然免疫（正文不参与 live 解析） |
| 归档解析 | `_line_scoped_hits`（保留） | `_line_scoped_hits`（**永久保留**，dual-read） |
| 坏输入 | 缺锚 → 无结论 | 坏 YAML/越域 → fail-closed 判无有效状态 |
| 门禁语义 | 退出码/UNKNOWN/命名空间 | **不变** |

## 附：live 报告状态解析数据流（迁移后）

```
              gate 需判某 change 结论
                       │
          ┌────────────┴────────────┐
     报告在 live?                报告在 archive?
  openspec/changes/{c}/       archive/<date>-{c}/
          │                          │
   只读 YAML frontmatter      frontmatter 优先 → 无则回退 inline〔G2 双读〕
   ship-gate.{字段}          新归档=frontmatter / 旧归档=_line_scoped_hits（永久保留）
          │                          │
   解析成功?                    任一命中?
    ├─ 是 → 严格枚举校验 → 状态       ├─ 是 → 状态
    └─ 否/坏YAML/越域/重复键        └─ 否 → 无结论（fail-safe 不 SHIPPED）
        → fail-closed
        「无有效状态」停下报告

（过渡期 live 亦「frontmatter 优先→回退 inline」，退役后 live 只读 frontmatter，见 D6）
```
