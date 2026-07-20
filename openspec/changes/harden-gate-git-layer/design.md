## Context

`ship_gate.py` 的失鲜判定有两个 scope、**三个消费方**：

| scope | 消费方（调用点） | 锚 | 监视集 |
|---|---|---|---|
| `design` | `:1214` spec-review-report | `design_approved` | 四件套 + `specs/`（**固定清单**） |
| `code` | `:1291` code-review-report | `code_review` | `openspec/` 之外的一切（**列不出清单** ⇒ 比顶层条目） |
| `code` | `:1311` verify-report | `verify` | 同上 |

历史实现一律**从 git 管道推断**「被审内容变了没有」。grill + 多镜设计审在这条推断链上累计挖出**十个缺陷、全部实测复现**（清单见 proposal「Why」）。其中两对互为解药兼病灶、两个只需外部 config/env 即可翻转判定 ⇒ 在枚举面上补不完。

∴ 本 change 不修补推断链，**改掉推断本身**。决策与实证落 `openspec/adr/0026`。

## Goals / Non-Goals

**Goals:**

- 机械层**只承诺召回**（任何实质改动都不漏），精确率交语义层，分诊结论落盘留痕。
- 锚点从「反推」改为「录锚」，缺失即 fail-closed。
- 十个缺陷**整类消失**，而非逐个修补。
- git 调用的环境级失败落进退出码契约集 `{0,3,4,5,6}`。
- **保住监视集**：实现期改源码 / 勾 plan 复选框 MUST NOT 让设计门失鲜。
- **豁免各归其位**：两条 design 域豁免只在其合法 churn 实际发生的阶段生效，MUST NOT 常开。

**Non-Goals:**

- 不做 T189、B18、全仓 git 调用盘点（理由见 proposal）。
- 不改退出码集合本身（`UNKNOWN(6)` 是既有取值，只新增到达它的路径）。
- 不引入任何第三方依赖（`ship_gate.py` 保零依赖不变量）。

## 组件清单〔BASE-25 · TG-14〕

| 组件 | 现状 | 本次动作 |
|---|---|---|
| `report_last_sha` | `git log -1 -- <report>`，锚可被后续触碰前移 | **退役**，由 `reviewed_sha` reader 取代 |
| `read_reviewed_sha(root, rel)` | 不存在 | **新增**：读 frontmatter；缺失/非法/对象不存在 → 抛 `GateIndeterminate` |
| `is_stale(root, rel, scope, change)` | design 分支约 50 行帧遍历；code 分支 4 行 | **重写**：两分支各约 15 行内容比较 |
| `frame_touched_paths` / 帧遍历 / `design_frame_exempt_reason` / BR-7 短路 | 帧枚举与 subject 豁免 | **退役** |
| `_normalize_checkbox_lines` | 内容豁免核心，已是 bytes 口径 | **保留复用** |
| `_stale_trigger_hint` / `StaleResult.trigger` | design 域专用触发点渲染 | **退役**（诊断改由语义层给，见 ADR-4） |
| `run_git` / `run_git_rc` / `run_git_bytes` | 三处裸 `subprocess.run`，无 timeout、无异常捕获、不清 env | **修改**：`OSError`+`TimeoutExpired` 映射、`timeout=30`、`GIT_*` 清理 |
| `decide()` 阶段判定 | 阶段在 design 域失鲜检查**之后**才算出 | **前移**：先判阶段，失鲜判据按阶段选（ADR-3） |
| `main()` | 无顶层异常处置 | **修改**：`GateIndeterminate` → `UNKNOWN(6)` 的唯一映射点 |

## Decisions

### ADR-1：机械层保召回、语义层保精确

**决定**：机械层只回答「被审内容有没有变」（有确定性信号：字节比较）；「这处变化要不要紧」（无确定性信号）交语义层，主 session 读 diff 判断，**重锚 + 写理由**。

**备选（已否决）**：继续在枚举面上逐个修补十个缺陷。理由——4 与 5 互为解药兼病灶，7/8 属外部可控态，补丁螺旋不收敛（基准 5）。

**与基准 1 的关系**：基准 1 是「能机械化的优先机械化」，本决定**不是**它的例外——机械层仍在，且承担**不可让渡的那一半**。让渡的是精确率，而精确率的机械化恰是十个缺陷的产地。切分线判据仍是「有无确定性信号」。

### ADR-2：录锚取代反推

**决定**：producer 在报告 frontmatter 写 `reviewed_sha: <当时 HEAD>`；reader 读它，**缺失 / 格式非法 / 对象不存在 ⇒ fail-closed**。

**备选（已否决）**：保留 `report_last_sha`，另加「该 frontmatter 字段值最后一次变成当前取值的提交」的定向 blame。理由——把 git 语义搬进 Python 手搓一遍（撞基准 5），且 blame 对 merge/rewrite 的行为又是一片新的推断面。

**reader 契约 MUST 与 producer 同批落地**：`ship_gate.py` 的 frontmatter parser 目前只认三个枚举字段、其余静默忽略。只做 producer 的结果只有两种——**新锚永远读不到**，或**缺字段时回退旧锚（= 缺陷 9 原样存活）**。∴ P0 MUST 含：reader/schema、完整 40 位 OID 校验（拒缩写 SHA / `HEAD` / 坏 SHA）、commit-object 存在性校验、字段缺失策略（**MUST NOT 静默回退**）、producer/gate 版本错配处置。

### ADR-3：失鲜判据**按阶段**定义，豁免各归其位

**决定**：`decide()` 先判阶段，再按阶段选失鲜判据。design 域的两条豁免不再常开，各自只在其**合法 churn 实际发生的那个阶段**生效：

| 阶段 | 对 design 监视集的合法 churn | 判据 | 逃生口 |
|---|---|---|---|
| 实现期 | **无**（实现勾的是 `superpowers-plan.md`，不在监视集内） | 四件套字节等值 | **无**，机械 fail-closed |
| 代码审期 | `[impl-review-fix]` 对四件套的修订 | 四件套字节等值 | **有**：不等 ⇒ 语义分诊 + 重锚留痕 |
| done 期 | `tasks.md` 复选框对账（`sdflow-done` 0.3 步） | 四件套字节等值，`tasks.md` 走 `_normalize_checkbox_lines` | **无** |

code 域的两个消费方**已经是位置即阶段**——`decide()` 里 `code-review-report` 的检查在代码审阶段之后才可达，`verify-report` 的在 done 阶段之后才可达（源码位置 `:1291` / `:1311`，均在阶段机走完对应分支之后）。design 域是唯一阶段无关的检查，也正是豁免堆得最厚的那个——**一个检查要同时容忍三个阶段的合法 churn，必然长出一堆豁免**。

**备选（已否决）**：维持单一判据 + 常开豁免（本 change 前一版方案）。理由——常开的语义逃生口没有任何机械约束，「什么阻止分诊方每次都重锚」无答案；阶段化之后，逃生口只在代码审期存在，而**阶段由 gate 自己算出、不靠自觉**，约束是机械的。

**BR-7 的定性由此改写**：它从来就是一条**阶段规则**，只是把阶段编码成了「commit subject 长什么样」——一个可伪造的代理（伪造 subject 即可在任意阶段取得豁免）。阶段化后它变成 gate 已知的事实，代理消失。

**实现约束**：阶段判定与失鲜判定**无循环依赖**——阶段只取决于盘面上有哪些产物（plan 在不在、code-review-report 在不在、verify-report 在不在及其锚），均不依赖失鲜结论。∴ 阶段判定可安全前移到 design 域检查之前。

### ADR-4：诊断降级为语义层产出

**决定**：退役 `_stale_trigger_hint` 与 `StaleResult.trigger`。gate 只报「哪个域失鲜」；「撞在哪」由语义分诊时给（主 session 手里就有 diff）。

**理由**：触发点诊断原本依附于帧遍历（要 sha + subject）。帧遍历退役后，为凑齐诊断而保留一条枚举路径，等于把刚砍掉的推断面从后门放回来。且 `decide()` 的两个 code 域调用点本来就二元解包丢弃了 `trigger`（`:1291`/`:1311`），该能力在 code 域**从未真正接通过**。

### ADR-5：`timeout = 30`，对齐仓内既有先例

**决定**：三个 helper 统一 `timeout=30`。

**理由**：`sdflow-buglist/scripts/buglist.py::repo_root` 的 `git_timeout = 30` 注释写明判据：「纯本地元数据查询（正常毫秒级），30 秒是**文件系统卡死 / 网络文件系统挂起**的判定线，**不是性能预算**」。判据一致 ⇒ 取同值，不另发明数字。**MUST NOT** 按「最慢的仓要多久」来定——那会把它误当性能预算。

**聚合上界**：design 域现在是「固定清单 × 2 次 `git show`」（约 8–10 次调用，与帧数无关），不再有帧遍历那种 30N 的无界聚合面。

### ADR-6：外部态中和是 `_GIT_HARDEN` 的职责，配置面与环境面一次扫全

**决定**：`_GIT_HARDEN` 的职责由「中和 `core.quotePath`」重定义为「**中和一切能改变判定输入的外部可控态**」——config 面走 `-c`，环境面走子进程 env 清理（剔除 `GIT_*`，保留必要的 `PATH`/`HOME`）。

**理由**：缺陷 7（`diff.ignoreSubmodules`）与 8（`GIT_ICASE_PATHSPECS`）是**同一片面**——外部可控态翻转判定。本方案已不调 diff、不用 pathspec，二者的直接利用面消失；但 `git show` / `ls-tree` 仍在子进程里跑，**MUST NOT** 依赖「我们碰巧没用到那些开关」作为安全论据（那是拿现状当保证）。实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工，方向安全但会让门无故坏掉。

### 关于「读失败 ≠ 内容为空」（本 change 的头号自噬风险）

内容比较 MUST **显式判 returncode**，MUST NOT 让两次失败读比较相等。

起草期实证：验证 fixture 里两边 `git show` 都因仓损坏失败、各返回空串，比较判「同」⇒ **假绿**。这与缺陷 3（`run_git` 把非零退出折成 `''`）是**同一个失效模式**——本 change 正是来修它的，而新方案的实现同样能踩进去。∴ 立为显式约束并配变异证明。

## 安全与数据保护〔BASE-28 · TG-17〕

**被保护的资产**：「设计审已拍板 / 代码审已放行 / verify 已通过」三个结论的有效性。它们是 merge 之前仅有的质量门。

**威胁模型**：

| 谁 | 怎么做 | 修复前 | 修复后 |
|---|---|---|---|
| 走正常流程的开发者/agent | 代码审后在 merge 提交里 resolve 出源码改动 | 🔴 判 fresh | ✅ 顶层条目不等 → stale |
| 同上 | `git mv` 把源码迁进 `openspec/` | 🔴 判 fresh | ✅ 源路径所属顶层条目不等 → stale |
| 同上 | 合并时把已批准产物换回锚前的旧草稿 | 🔴 判 fresh（`--cc`）/ ✅（`-m`） | ✅ 内容不等 → stale（构造性，不依赖拓扑） |
| 任何后续提交者（**无需恶意**） | 顺带碰一下报告文件（空行 / CI reformat）⇒ 锚前移，埋掉锚前的未审改动 | 🔴 判 fresh | ✅ 锚是记录值，推不动 |
| 环境异常（非攻击者） | git 调用失败 / 配置或环境变量异常 | 🔴 判 fresh | ✅ fail-closed → `UNKNOWN(6)` |
| 无（假阳面） | 设计门拍板后例行合并 main | 🔴 假判 stale，卡死正常流程 | ✅ 内容未变 → fresh |
| 无（假阳面） | done 写 `verify-report.md` / archive 移目录（纯 `openspec/` 记账） | — | ✅ 其余顶层条目未变 → fresh（**整树 sha 会在此假阳，已实测**） |

**残余面（显式登记，本次不覆盖）**：

- **语义分诊本身由被监管方执行** —— 主 session 判「这处变化不要紧」并重锚，无可信脚本捕获路径（承 [[signal-exists-not-equal-mechanical-capture]]）。缓解 = 机械层默认 fail-closed（不主动重锚就是 stale）+ 重锚 MUST 附理由 + git 留痕可审计。**MUST NOT 声称这是机械门。**
- **有写权限者直接改 `reviewed_sha`** —— 与改结论字段同权级，留痕可审计。不在失鲜判据职责内。
- **T189 耦合** —— `_normalize_checkbox_lines` 成为 **done 期** design 域比较的核心依赖，其口径缺陷（T189）会直接影响该阶段的豁免面（其余阶段不受影响，因归一化不在那些阶段生效）。本次不改，**显式登记**。
- 本 change 提升的是**误操作与流程漏洞**的拦截率，**不声称**能挡有意规避者。

## Risks / Trade-offs

- **[代码审期语义分诊频率过高]** → 缓解：阶段化后逃生口只在代码审期存在，触发面已从「任意阶段」收窄到「impl-review 修订四件套」这一种；A8 待实现期验证实际频率。若仍过高，须回补一条机械豁免（判据届时按实测定，不预先猜）。
- **[判定失去确定性]** → 缓解：机械层仍是确定的（内容比较），不确定的只有分诊；分诊默认 fail-closed，且 MUST 留痕。
- **[退役大量已上线行为（BR-7 真值表 8 格、帧遍历、触发点诊断）]** → 缓解：这些用例随其守护的机制一并退役，**MUST 在 impl-report 逐条说明每个删除的用例对应哪个退役机制**，MUST NOT 静默删测试。
- **[存量报告缺 `reviewed_sha` 撞门]** → 缓解：在途的只有本 change 自己；fail-closed 方向安全（停下问人，非假放行）。
- **[新实现踩进「读失败 = 内容为空」]** → 缓解：立为显式约束 + 变异证明（见 Decisions 末节）。
- **[变异证明流于形式]** → 缓解：spec 已把「删掉守卫即变红」写成需求；结果逐条落 impl-report，不得只写「已加测试」。

## Migration Plan

1. 本仓为 toolkit 源仓：改动经 push → 各消费仓 `/sdflow-upgrade` 生效。
2. **producer 与 gate MUST 同批发布**——只发 producer 则新锚读不到，只发 gate 则所有存量报告 fail-closed。
3. **存量 active 报告**（无 `reviewed_sha`）⇒ fail-closed ⇒ 须重审一次。**MUST NOT** 为兼容而静默回退旧锚。
4. **回滚**：`ship_gate.py` 是纯只读判官，无持久状态。回滚 = 还原文件 + 重跑 `setup.sh`；已写入的 `reviewed_sha` 字段对旧 gate 是未知字段，被静默忽略，不阻塞回滚。

## Open Questions

无。

## Compliance

实现期 MUST 遵守（本节逐字进 `superpowers-plan.md` 的 `## Global Constraints`）：

- 内容比较 **MUST** 显式判 returncode；**MUST NOT** 让两次失败读比较相等（读失败 ≠ 内容为空）。
- **MUST NOT** 在 `reviewed_sha` 缺失/非法时回退到 `report_last_sha` 或任何反推式锚。
- **MUST NOT** 为凑触发点诊断而保留任何路径枚举通路。
- 监视集 **MUST** 保住：实现期改源码、勾 `superpowers-plan.md` 复选框 **MUST NOT** 让设计门失鲜；done 期 `tasks.md` 复选框对账 **MUST NOT** 让设计门失鲜。各配用例。
- 两条 design 域豁免 **MUST** 按阶段生效（复选框归一化=done 期、语义分诊=代码审期），**MUST NOT** 常开；实现期与 done 期 **MUST NOT** 存在语义逃生口。
- 子进程 **MUST** 清理 `GIT_*` 环境变量；配置面中和走 `-c`。
- 每条新增守卫 **MUST** 附变异证明（删掉即变红），结果落 impl-report；**MUST NOT** 以「用例存在且为绿」充当证明。
- 新增用例 **MUST** 经 `is_stale` 公共入口求值，**MUST NOT** 只直接调内部 helper。
- code 域的**两个**消费方（`code-review-report`、`verify-report`）**MUST** 各有覆盖——后者是今天唯一有用例的，前者零覆盖。
- 删除既有用例 **MUST** 在 impl-report 逐条说明其对应哪个退役机制。
- `ship_gate.py` **MUST** 保持零第三方依赖；退出码 **MUST** 落在 `{0,3,4,5,6}` 内。
