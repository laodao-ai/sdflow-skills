# spec-review-report — harden-gate-git-layer

**结论：不建议直接进设计 HARD-GATE。** 三条 Critical 中有两条**推翻了本 change 的核心设计决定**
（其中一条推翻的是 grill 阶段我自己给出、用户已拍板的推荐），须先拍 Q1/Q2 再改四件套。

- 宿主/档位：`host=claude`，强档 `opus` / 中档 `sonnet` / 弱档 `haiku`，voice runner `codex`（跨模型成立）
- 镜数：领域镜 1 + 对抗镜 2 + 接地镜 1 + 广审（autoplan 双声）+ outside-voice 2 站点
- `metrics.enabled=true`

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-17" declared="TG-14,TG-17,TG-18,TG-19,TG-22,TG-23" evidence="被保护资产=三个评审结论的有效性，是 merge 前仅有的质量门；判错方向即未审代码随档 ship" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->

---

## Step1 广审（autoplan 原生）

<!-- sdflow:step1-broad-review v1 mode="native" -->

详见 `gstack-review.md`。CEO 双声共识表 2 项 CONFIRMED、3 项 DISAGREE，分歧根源已升为 Q2。

---

## 决策登记区

### 🔴 需拍板

**Q1 — design 域的枚举原语到底怎么定？（`-m` 有假阳，`--cc` 有假阴，两个都不对）**

grill 阶段我推荐 `-m`→`--cc` 修「例行 merge 假阳」，用户已拍板同意。**对抗镜 B 证伪了它，我已亲自复现**：

| 原语 | 例行 merge（应 fresh） | 合并结果与某 parent 逐字节相同（应 stale） |
|---|---|---|
| `-m`（现状） | ❌ 假阳 → `REFUSE_START` | ✅ 拦住 |
| `--cc`（grill 推荐） | ✅ | ❌ **假阴 → 已批准产物被换回旧草稿仍判 fresh** |

复现（我跑的 fixture）：侧支停在「旧草稿（已被否决）」且之后不碰 `tasks.md`；锚提交把它改成「已批准内容」；
合并时冲突消解选了侧支边 ⇒ HEAD 上 `tasks.md` = 旧草稿。**锚后无任何提交碰过 `tasks.md`**（逐帧 walk 看不见），
`--cc` 也看不见（结果与 parent2 逐字节相同）⇒ 判 fresh。`-m` 能看见。

根因：`--cc` 的语义是「只报相对**所有** parent 都不同的文件」，那个「只」字剪掉的正是这一支；
而承载旧内容的祖先提交早于锚点，天然在 `{sha}..HEAD` 之外，逐帧兜底也够不着。

> **推荐：混合式 —— 树比较做主判定，逐帧降级为「豁免归因」，归因不能时 fail-closed。**
>
> 1. 先比**锚 tree vs HEAD tree** 上四件套各文件的内容。**完全等值 ⇒ fresh，立即返回**（拓扑完全不参与
>    ⇒ 例行 merge 假阳**结构性消失**，不是靠打补丁）。
> 2. 有差异 ⇒ 才逐帧走 `{锚}..HEAD`，判该差异是否全部由豁免通道解释（BR-7 subject 豁免 + 内容豁免）。
> 3. **归因不到（如上面这个 merge 场景：有差异但无提交碰过它）⇒ 判 stale**，MUST NOT 当「没找到 ⇒ 没问题」。
>
> **依据**：这一条同时杀掉假阳与假阴，且**两个都是结构性消失而非补丁**——假阳源于「拿拓扑当内容的代理」，
> 假阴源于「拿拓扑当内容的代理」，是同一个根因的两面。**代价**：BR-7 的语义从「这一帧豁免」变成
> 「这处差异的归因」，须重新表述并重跑真值表 8 格。**备选**：保留 `-m` + 调用方过滤锚前 parent
> ——已被 ADR-2 以「把 git 语义搬进 Python 手搓（撞基准 5）」否决，本次评审无新证据推翻该否决。

**Q2 — 锚点模型（C1/C3）纳入本 change，还是另开？**

对抗镜 A 与 Codex 镜**独立命中同一根因**（高置信）：`report_last_sha` = 「最后一次触碰报告**路径**的提交」，
不是「结论字段最后一次变成当前值的提交」。任何后续触碰（一个空行、一次 CI reformat、一次顺带碰到该文件的 merge）
都把锚**前移**，把锚前的未审改动永久埋掉。**三个消费方全中，完全绕过本 change 修的全部四个洞**——
因为它作用在枚举原语介入**之前**。

> **推荐：纳入本 change，作为 P0。**
>
> **依据**：① 本 change 的 Why 写的是「同一片面只治了一半」，而锚获取与枚举同在 `is_stale` 的**同一个函数、
> 同一片 git 调用面**——把枚举修到极致却留着锚点可被无声移动，是又一次「只治一半」，正是基准 3 面治要杀的形态。
> ② design.md 的威胁模型表四行「🔴→✅」在 C1 存在时**都不成立**，即本 change 的核心承诺无法兑现。
> ③ C3（锚获取 fail-open：git 读不到 → 判 fresh）已由我复现，它字面就是「git 调用层的 fail-open」，
> 与 P0 同类同面，排除它需要理由而非纳入它需要理由。
> **代价**：scope 变大，需 producer 侧配合（评审 skill 写 `reviewed_sha` 进 frontmatter），
> 涉及 `sdflow-spec-review`/`sdflow-code-review`/`sdflow-done` 三个 SKILL 的模板。
> **备选**：本 change 只做 C3（纯 gate 侧，锚获取 tri-state：`found`/`genuinely-uncommitted`/`git-failed`，
> 第三态 → `UNKNOWN(6)`），C1（显式 `reviewed_sha`）另开——后果：C1 在窗口期内仍可被利用，
> 但至少「读不到 git 就放行」这个洞当场堵上。
>
> 🔴 **若拍板纳入，reader 侧 MUST 一并定契约**〔design-voice 独家命中，我核实属实〕：我上面的推荐只写了
> producer（评审 skill 写 `reviewed_sha`），而 gate 的 frontmatter parser 只认三个枚举字段、其余静默忽略
> （`ship_gate.py:789-900`），且 Migration Plan 仍写「无 schema 变更」。照这样实现，结果只有两种：
> **新锚永远读不到**，或**缺字段时回退 `report_last_sha`（= C1 原样存活）**。∴ P0 MUST 含：reader/schema、
> 完整 OID 校验（拒缩写 SHA / `HEAD` / 坏 SHA）、commit-object 存在性校验、**字段缺失策略**
> （存量 active report 明确要求一次性重审，**MUST NOT 静默回退可移动锚**）、producer/gate 版本错配处置。

**Q3 — 若采纳 Q1 混合式，BR-7 政策怎么表述？**

Codex 镜 P1-战略：「design 必须逐帧」的唯一理由是既有 BR-7 按 subject 豁免，这是**拿既有代理机制论证
目标必须继续依赖该代理**（通则③ 的自指命中——我在 design.md ADR-1 里正是这么论证的）。

我的判断：BR-7 **不只是**代理，它编码了一条**政策**——「阶段三代码审的 `[impl-review-fix]` 修订可以改设计
产物而不作废设计门」。纯内容快照模型表达不了这条政策（内容变了就是变了，不问是谁改的）。∴ Codex 的
「10x 重构 = 纯快照」**过头了**；但它指出的论证缺陷成立：design.md 从未说明 BR-7 是政策而非实现细节。

> **推荐**：采纳 Q1 混合式（政策保留，只是归因的粒度从「帧」变成「差异」），并在 design.md 补一段
> 显式说明「BR-7 是政策不是代理」，把这个判断从隐含变显式。

### ✅ 自动决策

| # | 决策 | 依据 |
|---|---|---|
| ~~D1~~ | ~~负向 pathspec `git diff --quiet <锚> HEAD -- . ':!openspec'`~~ **→ 已推翻，维持原设计的 `--raw -z` + Python 前缀判定** | **翻转过程留档**：先采纳（Claude CEO 镜，理由=零解析、贴合基准 5，我实测 6 例全绿）→ **design-voice 证伪**：负向 pathspec 继承 `GIT_ICASE_PATHSPECS`，我实测 `:!readme.md` 在该环境变量下**排除了** `README.md`（exit 0 = fail-open），而 `--raw` + 字节前缀判定**免疫**（如实报出）。在大小写敏感文件系统上，仓内同时存在 `openspec/` 与真实代码目录 `OpenSpec/` 时即可被利用。**教训**：基准 5「让工具自己回答」不是无条件的——当工具的回答依赖**环境态**、而显式判定不依赖时，显式判定更强 |
| ~~D2~~ | ~~P2 诊断懒加载~~ | 依赖 D1。D1 已翻 ⇒ 主判定本来就走 `--raw -z`，诊断路径同源，无懒加载可言 |
| D3 | 异常捕获从 `FileNotFoundError` 扩到 `OSError`（含 `PermissionError`） | Codex-3 属实；`OSError` 是二者共同父类，一处覆盖 |
| D4 | category 统一：design 域沿用 `frame-enum-failed`，code 域用 `enum-failed`，措辞改为「语义对应、非字面复用」 | 三镜独立命中（领域镜 F4 / 接地镜 / Codex-6），我核实 `ship_gate.py:712,743` 确为 `frame-enum-failed` |
| D5 | 删除 spec 的「孤儿锚 ⇒ 按内容判」Scenario | 我复现确认**不可达**：`report_last_sha` 动态重查，amend 后返回新提交，永远拿不到孤儿 sha。为不可达状态写 Requirement 正是本 spec 自己要禁的形态 |
| D6 | tasks 第 4 节补一条：改 `decide()` 的 `:1291`/`:1311` 两处二元解包 + 对应 `emit` | 领域镜 F1，我核实属实：`cr_stale, cr_fresh = is_stale(...)` 丢弃 trigger ⇒ P2 在真实调用链上不成立 |
| D7 | tasks 显式点名 `test_gate_freshness.py:989` 的断言随 P2 反转（属预期改动非破坏契约） | 领域镜 F2：该用例断言 `res.trigger is None`，与 P2 字面对立 |
| D8 | 修 proposal 三处残句（`:40` 哪个 commit / `:54` 两域统一 / `:62` 逐字不变、只抽共用源） | Codex-5，我核实属实——grill 期分片编辑留下的自相矛盾 |
| D9 | 5.8/5.9 拆成对三个 helper 各自的单元级验证 | 领域镜 F5：`main()` 首次 git 调用走 `run_git`，一旦 exit 6 当场退出，后两个 helper 根本走不到 ⇒ 端到端单例只覆盖 1/3 |
| D10 | 补测试：干净合并、只碰一侧、该侧提交在范围内 ⇒ 仍判 stale | 领域镜 F6：现有 evil-merge 夹具全用 `_merge_amended`（构造两侧都没有的内容），结构性测不到「与某侧相同」这一支 |
| D11 | ADR-5 补「备选（已否决）」+ 论证为何共享诊断通道不重演 ADR-1 的风险 | Claude CEO-2 |
| D12 | design 域 30N 聚合超时：记 todolist 挂钩本 change，hand-off 显式提示 | Claude CEO-3；本次不解决但不散落在 ADR 一句话里 |
| D13 | **`_GIT_HARDEN` 的职责重定义为「中和一切能改变*报告哪些路径*的环境态」，配置面与环境变量面一次扫全** | 有客观判据（T10 ①），两条实测：① `diff.ignoreSubmodules=all` ⇒ 未审 submodule bump 判 fresh（C4）；② `GIT_ICASE_PATHSPECS=1` ⇒ 负向 pathspec 误排除（D1 翻转依据）。**面治（基准 3）**：这两条是**同一片面**——`_GIT_HARDEN` 存在的全部理由就是中和外部可控态，而它今天只有 `core.quotePath=false`。本次 MUST 系统枚举「哪些 config + 哪些 `GIT_*` 环境变量能改变报告的路径集」并一次性中和（config 走 `-c`，环境走子进程 env 清理），**MUST NOT 只补 `--ignore-submodules=none` 一个 flag** 了事——否则下一个 `diff.*` / `GIT_*` 会以同样方式重现 |

### ❌ 已裁掉（反静默压制，连理由留档）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | Codex-4：应改「纯内容快照模型」，可删除 merge 拓扑/`--cc`/30N/subject 全量豁免 | **部分采纳、整体裁掉**。其论证缺陷指认成立（已入 Q3），但结论过头：BR-7 是政策不是代理，纯快照表达不了「impl-review 修订不作废设计门」。已降级为 Q1 混合式（保政策、换归因粒度） |
| X2 | Codex-7：T189 应纳入 | 依赖 X1（纯快照模型）成立。X1 已裁 ⇒ T189 仍属内容豁免面，维持 Non-Goal。**但须在 design.md 残余面登记它与 design 域新鲜度的耦合** |
| X3 | 领域镜 F7：`frame_touched_paths` 与 `code_changed_paths` 的 raw-token 解析重复，建议抽公共 helper | 若采纳 D1（负向 pathspec），code 域主判定**不解析任何 token**，重复不成立。诊断路径的懒加载解析可复用既有 helper，不新增抽象 |
| X4 | Claude CEO-4：全仓 ~8 个脚本同类 git 调用安全面 | 本 change 之外的面（基准 4：别为"顺手"把不相关的面拖进来）。记独立 todolist |
| X5 | 接地镜 1/2/3/5：`code_changed_paths`/`GitUnavailable`/code 域 category/`--cc` 在代码里不存在 | **非缺陷**——这些是本 change 的**待实现项**，接地镜把「设计写了但代码还没实现」误报为「文档与代码不符」。接地镜第 4/6 项及 11 项符合项汇总有效 |

---

## Findings 汇总（按严重度）

### 🔴 Critical

**C1 — 锚点可被无声前移，三个消费方全中，绕过本 change 修的全部四个洞**
命中镜：对抗镜A + Codex（**独立双命中**）。证据：`ship_gate.py:234` `report_last_sha` = `git log -1 -- <report>`。
复现（对抗镜 A 实跑 fixture）：`C1` 报告落盘 → `C2` 后门只碰 `src/app.py` → `C3` 无关的人给报告补个换行。
锚 = `C3` = HEAD ⇒ `锚..HEAD` 为空 ⇒ 判 fresh，后门在树里。**已登记的残余面「有写权限者改 frontmatter」不覆盖它**
——本攻击**不需要改任何结论字段的值**，隐蔽性是另一个量级。→ Q2

**C2 — `--cc` 引入假阴：已批准产物被换回旧草稿仍判 fresh**
命中镜：对抗镜B（**主 session 已独立复现**）。见 Q1 表格与复现步骤。这是我在 grill 阶段给出的推荐，**被证伪**。→ Q1

**C3 — 锚获取本身 fail-open：git 读不到就判 fresh**
命中镜：Codex（**主 session 已独立复现**）。`run_git` 非零 → `''` → `is_stale` 判 `(False,'uncommitted')` = **fresh**。
实测：非 git 目录下 `is_stale(...)` 返回 `(False, 'uncommitted')`。→ Q2

**C4 — 配置依赖的 fail-open：一个普通 git 配置就能让未审改动判 fresh**
命中镜：outside-voice `hr-tg`（**独家命中，四面镜与主 session 全漏**；**主 session 已复现**）。
`diff.ignoreSubmodules=all`（或 `submodule.<name>.ignore=all`）会让 `git diff` 不报 gitlink 变更 ⇒
锚后的 submodule bump（**指向未经审查的代码**）在 code 域判 **fresh**。实测：

```
默认配置                    : `:160000 160000 … M vendor`  → stale ✅
diff.ignoreSubmodules=all   : (空)                          → fresh ❌
+ --ignore-submodules=none  : `:160000 160000 … M vendor`  → stale ✅
```

**我推荐的 D1 `--quiet` 原语同样中招**（`ignoreSubmodules=all` 下 exit=0）。`_GIT_HARDEN`
（`ship_gate.py:166`）当前只中和 `core.quotePath=false`——**它中和配置依赖的职责是不完整的**。→ D13

### 🟠 High

- **H1** `decide()` 二元解包丢 trigger，tasks 无对应任务 ⇒ P2 在真实调用链上不成立〔领域镜F1，已核实〕→ D6
- **H2** 既有测试 `:989` 断言与 P2 字面对立，tasks 未点名允许改〔领域镜F2〕→ D7
- **H3** spec 的「孤儿锚」Scenario **不可达**（grill 期我写的）〔Codex 推论，已复现〕→ D5
- **H4** proposal 三处残句与 design/spec 自相矛盾〔Codex-5，已核实〕→ D8
- **H5** 异常覆盖不全（`PermissionError` / 无效可执行格式等 `OSError` 逸出）+ spec「枚举失败判 stale」与「环境失败判 UNKNOWN」边界未划清〔Codex-3 + hr-tg voice **双命中**〕→ D3
- **H6** `GIT_ICASE_PATHSPECS` 使负向 pathspec 误排除真实代码目录〔design-voice **独家**，已复现〕→ 推翻 D1，并入 D13
- **H7** `reviewed_sha` 只规划 producer、未定 reader/schema/迁移契约 ⇒ 新锚读不到或静默回退可移动锚〔design-voice **独家**，已核实〕→ 并入 Q2

### outside-voice 锚

<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->

两站点均**实跑**（非复用）：`design-voice` 因守卫判 `section-not-found` 走回落自跑；`hr-tg` 因 HR-TG∩≠∅ 单开。
run 目录 `\.outside-voice/20260720T124137Z-LeqSvg/`，退出码取自 `.rc` sidecar（均为 `0`），**非从正文推断**。
两站点合计 4 条 findings，其中 **3 条是四面镜与主 session 全漏的独家命中**（C4、H6、H7）——
本轮跨模型层的边际产出显著高于历史均值，建议 retro 时留意。

### 🟡 Medium

- **M1** category 命名不一致却称「同名同义」〔三镜命中〕→ D4
- **M2** 5.8/5.9 只测得到 1/3 个 helper〔领域镜F5〕→ D9
- **M3** `--cc` 日常干净合并的兜底不变量无测试锁定〔领域镜F6〕→ D10
- **M4** `_stale_trigger_hint` 对 code 域的 sha/subject 占位值未规范（缺 key 会 `KeyError`）〔领域镜F3〕
- **M5** design 域 30N 聚合超时无处置〔Claude CEO-3〕→ D12
- **M6** ADR-5 无备选论证〔Claude CEO-2〕→ D11
- **M7** 负向 pathspec 备选未评估〔Claude CEO-1，已实测可行〕→ D1

### ⚪ Low（一行带过，可审计不静默丢）

- L1 `archive` 后 `is_stale` 不对已移走路径求值——当前 `decide()` 分支顺序保证，但无用例锁死该顺序假设〔对抗镜B〕
- L2 全仓 ~8 脚本同类 git 调用安全面未盘点〔Claude CEO-4〕→ X4

---

## 度量锚（lens-metric）

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="2" sev="致2/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="4" 采纳="2" 裁掉="2" defer="0" 独立="2" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="7" 采纳="6" 裁掉="1" defer="0" 独立="5" sev="致0/高2/中4/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="8" 采纳="6" 裁掉="2" defer="0" 独立="3" sev="致2/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="1" sev="致1/高1/中0/低0" -->

**信任边界声明**：emitter 只保证「给定输入的确定性归约」。**分类正确性**（某条 finding 归哪个 lens）、
**roster 完备性**、**findings JSON 誊写准确**仍是主 session 的信任边界，非机械可验。
`采纳/裁掉` 为设计门拍板**前**的临时裁决，MUST 在拍板回写时重算（〔SR-M〕，best-effort 无机械兜底）。

## 镜的独立性观察

对抗镜 B 与领域镜**都**检查了 `--cc`，但只有对抗镜 B 找到假阴——领域镜 F6 检查的是「干净合并单侧修改」
（被逐帧 walk 兜住，判无洞），对抗镜 B 检查的是「合并结果等于某 parent 且该内容源自**锚前祖先**」
（逐帧兜不住）。差别只在一个前提：内容的来源提交在不在枚举范围内。**这条边界正是本次唯一的 Critical 设计缺陷所在**，
也说明「对抗角度」与「领域清单」不可互相替代。
