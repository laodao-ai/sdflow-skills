## Context

`ship_gate.py` 的失鲜判定有两个 scope、**三个消费方**：

| scope | 消费方（调用点） | 锚 | 监视集 |
|---|---|---|---|
| `design` | `:1214` spec-review-report | `design_approved` | 四件套 + `specs/`（**固定清单**） |
| `code` | `:1291` code-review-report | `code_review` | `openspec/` 之外的一切（**列不出清单** ⇒ 比顶层条目） |
| `code` | `:1311` verify-report | `verify` | 同上 |

历史实现一律**从 git 管道推断**「被审内容变了没有」，并**全阶段求值**。grill + 多镜设计审在这条链上累计挖出**十个缺陷、全部实测复现**（清单见 proposal「Why」）。

∴ 本 change 改三件事：**录锚**（取代反推）、**比内容**（取代枚举）、**限定求值窗口**（取代全阶段求值）。决策与实证落 `openspec/adr/0026`。

## Goals / Non-Goals

**Goals:**

- 锚从「反推」改为「录锚」，缺失即 fail-closed。
- 判定从「枚举路径」改为「比内容」，十个缺陷整类消失。
- 判据**只在其保护的风险真实存在的阶段求值**。
- **保住监视集**：实现期改源码 / 勾 plan 复选框 MUST NOT 让设计门失鲜。
- 判定**保持全机械**——无语义层、无逃生口。
- git 调用的环境级失败落进退出码契约集 `{0,3,4,5,6}`。

**Non-Goals:**

- 不做 T189、B18、全仓 git 调用盘点（理由见 proposal）。
- 不改退出码集合本身（`UNKNOWN(6)` 是既有取值，只新增到达它的路径）。
- 不引入任何第三方依赖（`ship_gate.py` 保零依赖不变量）。

## 组件清单〔BASE-25 · TG-14〕

| 组件 | 现状 | 本次动作 |
|---|---|---|
| `report_last_sha` | `git log -1 -- <report>`，锚可被后续触碰前移 | **退役** |
| `read_reviewed_sha(root, rel)` | 不存在 | **新增**：读 frontmatter；缺失/非 40 位 OID/对象不存在 → 抛 `GateIndeterminate` |
| `is_stale(root, rel, scope, change)` | design 分支约 50 行帧遍历；code 分支 4 行 | **重写**：两分支各约 15 行内容比较 |
| `decide()` 阶段判定 | 阶段在 design 域失鲜检查**之后**才算出 | **前移**：先判阶段；design 域失鲜只在实现窗口内求值 |
| `frame_touched_paths` / 帧遍历 / `design_frame_exempt_reason` / BR-7 短路 | 帧枚举与 subject 豁免 | **退役** |
| `_normalize_checkbox_lines` | 内容豁免核心，已是 bytes 口径 | **保留复用**（常开，按内容切） |
| `_stale_trigger_hint` / `StaleResult.trigger` | design 域专用触发点渲染 | **退役**（见 ADR-4） |
| `run_git` / `run_git_rc` / `run_git_bytes` | 三处裸 `subprocess.run`，无 timeout、无异常捕获、不清 env | **修改**：`OSError`+`TimeoutExpired` 映射、`timeout=30`、`GIT_*` 清理 |
| `main()` | 无顶层异常处置 | **修改**：`GateIndeterminate` → `UNKNOWN(6)` 的唯一映射点 |

## Decisions

### ADR-1：录锚取代反推

**决定**：producer 在报告 frontmatter 写 `reviewed_sha: <当时 HEAD>`；reader 读它，**缺失 / 格式非法 / 对象不存在 ⇒ fail-closed**。

**备选（已否决）**：保留 `report_last_sha`，另加「该 frontmatter 字段值最后一次变成当前取值的提交」的定向 blame。理由——把 git 语义搬进 Python 手搓一遍（撞基准 5），且 blame 对 merge/rewrite 的行为又是一片新的推断面。

**reader 契约 MUST 与 producer 同批落地**：`ship_gate.py` 的 frontmatter parser 目前只认三个枚举字段、其余静默忽略。只做 producer 的结果只有两种——**新锚永远读不到**，或**缺字段时回退旧锚（= 缺陷 9 原样存活）**。∴ P0 MUST 含：reader/schema、完整 40 位 OID 校验（拒缩写 SHA / `HEAD` / 坏 SHA）、commit-object 存在性校验、字段缺失策略（**MUST NOT 静默回退**）、producer/gate 版本错配处置。

### ADR-2：比内容取代枚举

**决定**：不再枚举「哪些路径被碰过」，直接比内容。

- **design 域**：固定清单 `proposal.md`/`design.md`/`tasks.md` 逐个 `git show <锚>:<path>` 与 HEAD 比字节；`specs/` 子树经 `ls-tree -r -z` 枚举后同样逐个比；`tasks.md` 比之前过 `_normalize_checkbox_lines`。
- **code 域**：比 `git ls-tree`（浅层、不递归）的**顶层条目**，排除 `openspec` 条目后求等值。

**备选（已否决）**：① 继续枚举、逐个修补八个管道缺陷——4 与 5 互为解药兼病灶，7/8 属外部可控态，补丁螺旋不收敛（基准 5）。② code 域用整棵树的 sha——**实测证伪**：done 写 `verify-report.md` 即改变整树 sha ⇒ 正常流程第一步就假阳。③ code 域用负向 pathspec `':!openspec'`——**实测证伪**：继承 `GIT_ICASE_PATHSPECS`，该环境变量下真实代码目录会被误排除（而 `--raw` + 字节前缀判定免疫）。

**勾选豁免 MUST 常开、按内容切、不按阶段切**：`tasks.md` 勾选框的写入方是 **agent 自由行为、不是 SKILL 契约**（前序 change 假设表 A1′ 已证；本仓 20 个 checkpoint 提交碰过 `tasks.md`，散在各阶段）。按阶段切 ⇒ 非该阶段的勾选立刻假失鲜 ⇒ 退回前序 change 修的那个缺陷。豁免面精确等于「归一化后逐行等值」这一已证零信息量的集合。

### ADR-3：限定求值窗口——判据只在其保护的风险真实存在的阶段求值

**决定**：design 域失鲜**只在阶段三起手至实现完成期间求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`）；进入代码审后不再求值。code 域两个检查已经是「位置即阶段」，无需改动。

**理由**：design 域失鲜保护的风险是「照着一份已经变了的设计继续建」——**该风险只在实现期存在**。实现完成后代码已经写完，此后对设计文档的修订是**文档对账**，而非「目标在移动」。而那些修订恰恰是工作流**明文允许**的：代码审期的 `[impl-review-fix]`、done 期 `opsx:verify` step 7 的「Update implementation **or revise design.md to match reality**」（`.claude/commands/opsx/verify.md:99`）。在那些阶段判失鲜，产出的**只有噪声**。

**这是本 change 复杂度的分水岭**：起草期曾为「后期合法修订」设计过一整套补偿机制——语义分诊层 → 重锚协议 → 重锚必须留理由 → `design_approved_sha` 不可变字段。**限定窗口把这一整套证明成不必要的**，判定得以保持全机械、确定性不被交换掉。

**备选（已否决）**：① 全阶段求值 + 语义逃生口——为明文允许的动作加一道仪式，改变不了结果；且逃生口的阶段限制**拦不住**（gate 只能比较 `reviewed_sha`，拦不住谁去写它），其机械性被高估。② 全阶段求值 + 豁免按阶段生效——见 ADR-2，写入方不受阶段约束，实测证伪。

**窗口内无合法 churn**（∴ 无需豁免）：`sdflow-implement` 只读 `design.md`，撞问题走 halt 上抛而非自行改设计；**全仓历史零个实现期提交（`checkpoint(<change>:taskN-…)`）改过监视集**。

**无循环依赖**：阶段只取决于盘面上存在哪些产物（plan / code-review-report / verify-report），不取决于失鲜结论 ⇒ 阶段判定可安全前移到 design 域检查之前。

### ADR-4：诊断降级，不为凑诊断保留枚举通路

**决定**：退役 `_stale_trigger_hint` 与 `StaleResult.trigger`。gate 只报「哪个域失鲜」。

**理由**：触发点诊断原本依附于帧遍历（要 sha + subject）。帧遍历退役后，为凑齐诊断而保留一条枚举路径，等于把刚砍掉的推断面从后门放回来。且 `decide()` 的两个 code 域调用点本来就二元解包丢弃了 `trigger`（`:1291`/`:1311`），该能力在 code 域**从未真正接通过**。撞门者需要细节时，`git diff <reviewed_sha> HEAD` 一条命令即得。

### ADR-5：`timeout = 30`，对齐仓内既有先例

**决定**：三个 helper 统一 `timeout=30`。

**理由**：`sdflow-buglist/scripts/buglist.py::repo_root` 的 `git_timeout = 30` 注释写明判据：「纯本地元数据查询（正常毫秒级），30 秒是**文件系统卡死 / 网络文件系统挂起**的判定线，**不是性能预算**」。判据一致 ⇒ 取同值。**MUST NOT** 按「最慢的仓要多久」来定——那会把它误当性能预算。

**聚合上界**：design 域现在是「固定清单 × 2 次 `git show`」（约 8–10 次调用，与提交数无关），不再有帧遍历那种 30N 的无界聚合面。

### ADR-6：外部态中和是 `_GIT_HARDEN` 的职责，配置面与环境面一次扫全

**决定**：`_GIT_HARDEN` 的职责由「中和 `core.quotePath`」重定义为「**中和一切能改变判定输入的外部可控态**」——config 面走 `-c`，环境面走子进程 env 清理（剔除 `GIT_*`，保留必要的 `PATH`/`HOME`）。

**理由**：缺陷 7（`diff.ignoreSubmodules`）与 8（`GIT_ICASE_PATHSPECS`）是**同一片面**。本方案已不调 diff、不用 pathspec，二者的直接利用面消失；但 `git show` / `ls-tree` 仍在子进程里跑，**MUST NOT** 依赖「我们碰巧没用到那些开关」作为安全论据（那是拿现状当保证）。实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工——方向安全，但会让门无故坏掉。

### 关于「读失败 ≠ 内容为空」（本 change 的头号自噬风险）

内容比较 MUST **显式判 returncode**，MUST NOT 让两次失败读比较相等。

起草期实证：验证 fixture 里两边 `git show` 都因仓损坏失败、各返回空串，比较判「同」⇒ **假绿**。这与缺陷 3、10（把非零退出折成 `''`）是**同一个失效模式**——本 change 正是来修它的，而新实现同样能踩进去。∴ 立为显式约束并配变异证明。

## 安全与数据保护〔BASE-28 · TG-17〕

**被保护的资产**：「设计审已拍板 / 代码审已放行 / verify 已通过」三个结论的有效性。它们是 merge 之前仅有的质量门。

**威胁模型**：

| 谁 | 怎么做 | 修复前 | 修复后 |
|---|---|---|---|
| 走正常流程的开发者/agent | 代码审后在 merge 提交里 resolve 出源码改动 | 🔴 判 fresh | ✅ 顶层条目不等 → stale |
| 同上 | `git mv` 把源码迁进 `openspec/` | 🔴 判 fresh | ✅ 源路径所属顶层条目不等 → stale |
| 同上 | 实现期把已批准设计换成别的内容后继续建 | 🔴 视手段可绕（缺陷 1/2/5） | ✅ 内容不等 → stale（构造性，不依赖拓扑） |
| 任何后续提交者（**无需恶意**） | 顺带碰一下报告文件（空行 / CI reformat）⇒ 锚前移，埋掉锚前的未审改动 | 🔴 判 fresh | ✅ 锚是记录值，推不动 |
| 环境异常（非攻击者） | git 调用失败 / 配置或环境变量异常 | 🔴 判 fresh | ✅ fail-closed → `UNKNOWN(6)` |
| 无（假阳面） | 设计门拍板后例行合并 main | 🔴 假判 stale，卡死正常流程 | ✅ 内容未变 → fresh |
| 无（假阳面） | done 写 `verify-report.md` / archive 移目录（纯 `openspec/` 记账） | — | ✅ 其余顶层条目未变 → fresh |

**残余面（显式登记，本次不覆盖）**：

- 🔴 **代码审期与 done 期对设计文档的修订不再被 gate 记录** —— 求值窗口之外的直接后果。可接受，两条理由：① 那些修订是工作流**明文允许**的（`[impl-review-fix]`、`opsx:verify` design adherence），gate 拦它只能多加一道仪式、改变不了结果；② 落进既有的「人机同权、篡改留痕可审计」残余面，与「有写权限者直接改结论字段」同权级。**代价是**：设计文档被事后改成「合理化已经写出来的代码」时无门禁记录，只有 git 历史可查。
- **有写权限者直接改 `reviewed_sha`** —— 与改结论字段同权级，留痕可审计。不在失鲜判据职责内。
- **T189 耦合** —— `_normalize_checkbox_lines` 是 design 域内容比较的核心依赖，其口径缺陷（T189）会直接影响豁免面。本次不改，**显式登记**。
- 本 change 提升的是**误操作与流程漏洞**的拦截率，**不声称**能挡有意规避者。

## Risks / Trade-offs

- **[求值窗口画错，漏掉真实风险]** → 缓解：A2/A3 已用「SKILL 契约 + 全仓历史实证」双证；「窗口内无合法 churn」是可证伪命题，实现期须再跑一次全历史核验。
- **[退役大量已上线行为（BR-7 真值表 8 格、帧遍历、触发点诊断）]** → 缓解：这些用例随其守护的机制一并退役，**MUST 在 impl-report 逐条说明每个删除的用例对应哪个退役机制**，MUST NOT 静默删测试。
- **[存量报告缺 `reviewed_sha` 撞门]** → 缓解：在途的只有本 change 自己；fail-closed 方向安全（停下问人，非假放行）。
- **[新实现踩进「读失败 = 内容为空」]** → 缓解：立为显式约束 + 变异证明。
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
- 勾选豁免 **MUST** 常开、按内容切；**MUST NOT** 按阶段切。
- design 域失鲜 **MUST** 只在实现窗口内求值；**MUST NOT** 因「多查一次更安全」而恢复全阶段求值——那会重新引出整套补偿机制。
- **MUST NOT** 引入语义分诊层或任何形式的重锚逃生口（已由求值窗口证明不必要）。
- 监视集 **MUST** 保住：实现期改源码、勾 `superpowers-plan.md` 复选框 **MUST NOT** 让设计门失鲜。
- code 域 **MUST NOT** 用整棵树的 sha，**MUST NOT** 用负向 pathspec（二者均已实测证伪）。
- 子进程 **MUST** 清理 `GIT_*` 环境变量；配置面中和走 `-c`。
- 每条新增守卫 **MUST** 附变异证明（删掉即变红），结果落 impl-report；**MUST NOT** 以「用例存在且为绿」充当证明。
- 新增用例 **MUST** 经 `is_stale` 公共入口求值，**MUST NOT** 只直接调内部 helper。
- code 域的**两个**消费方（`code-review-report`、`verify-report`）**MUST** 各有覆盖——后者是今天唯一有用例的，前者零覆盖。
- 删除既有用例 **MUST** 在 impl-report 逐条说明其对应哪个退役机制。
- `ship_gate.py` **MUST** 保持零第三方依赖；退出码 **MUST** 落在 `{0,3,4,5,6}` 内。
