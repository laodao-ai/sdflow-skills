## Context

`ship_gate.py` 的失鲜判定有两个 scope、**三个 `is_stale` 消费方**：

| scope | 消费方（调用点） | 锚 | 监视集 |
|---|---|---|---|
| `design` | `:1214` spec-review-report | `design_approved` | 四件套 + `specs/`（**固定清单**） |
| `code` | `:1291` code-review-report | `code_review` | `openspec/` 之外的一切（**列不出清单** ⇒ 比顶层条目） |
| `code` | `:1311` verify-report | `verify` | 同上 |

**另有第二个 frontmatter 消费方**（非 `is_stale`）：`sdflow-done/scripts/roadmap_writeback_draft.py:151-202`
的 `read_verify_state`，独立正则实现。**已核实对新增 `reviewed_sha` 字段免疫**
（`re.match(r"^\s*verify:\s*(\S+)\s*$")` 只认 `verify:` 直接子键）——此处显式登记，
使「谁在读这个 frontmatter 块」成为盘点过的事实而非隐式假设（承 `adr/0011`）。

历史实现一律**从 git 管道推断**「被审内容变了没有」，并**全阶段求值**。grill + 两轮多镜设计审在这条链上累计挖出**十个缺陷、全部实测复现**（清单见 proposal「Why」）。

∴ 本 change 改三件事：**录锚**（取代反推）、**比内容**（取代枚举）、**限定求值窗口**（取代全阶段求值）。决策与实证落 `openspec/adr/0026`。

## Goals / Non-Goals

**Goals:**

- 锚从「反推」改为「录锚」，缺失即 fail-closed。
- 判定从「枚举路径」改为「比内容」，十个缺陷整类消失。
- 判据**只在其保护的风险真实存在的阶段求值**。
- **保住监视集**：实现期改源码 / 勾 plan 复选框 MUST NOT 让设计门失鲜。
- 判定**保持全机械**——无语义层、无逃生口。
- git 调用的环境级失败落进退出码契约集 `{0,3,4,5,6}`，且失败原因可行动。

**Non-Goals:**

- 不做 T189、B18、全仓 git 调用盘点、归档终态检查（理由见 proposal）。
- 不改退出码集合本身（`UNKNOWN(6)` 是既有取值，只新增到达它的路径）。
- 不引入任何第三方依赖（`ship_gate.py` 保零依赖不变量）。

## 求值窗口示意〔BASE-19 · TG-14〕

```
  阶段（由盘面产物推导）              design 域失鲜   code 域失鲜
  ─────────────────────────────────────────────────────────────
  RUN_SOP        （sop 产物缺）          ✅ 求值          —
  RUN_PLAN       （plan 缺）             ✅ 求值          —      ← 窗口
  CONTINUE_IMPL  （plan_ids ⊄ done）     ✅ 求值          —
  ─────────────────────────────────────────────────────────────
  RUN_CODE_REVIEW（cr 报告缺）           ❌ 不求值        —      ← 窗口外
  代码审进行中 / 已出结论                 ❌ 不求值      ✅ :1291
  RUN_VERIFY / verify 已出结论            ❌ 不求值      ✅ :1311
  SHIPPED（归档后，D3 短路）              ❌ 不求值      ❌ 不求值（残余面）

  ⚠ 窗口右边界的间隙：「实现刚完成」与「代码审进行中」在盘面上不可区分
    （都是 plan 全勾 + 无 cr 报告）⇒ 该间隙内的四件套改动不被求值。见残余面。
```

## 组件清单〔BASE-25 · TG-14〕

| 组件 | 现状 | 本次动作 |
|---|---|---|
| `report_last_sha` | `git log -1 -- <report>`，锚可被后续触碰前移 | **退役** |
| `read_reviewed_sha(root, rel)` | 不存在 | **新增**：读 frontmatter（语法级）+ commit-object 存在性校验（语义级，需 git 调用） |
| `parse_ship_gate_frontmatter` / `FIELD_ENUMS` | 三字段**有限枚举**校验（`val not in FIELD_ENUMS[field]`） | **改造**：升级为支持「字段 → 校验函数」，容纳不可枚举值域 |
| `is_stale(root, rel, scope, change)` | design 分支约 50 行帧遍历；code 分支 4 行 | **重写**：两分支各约 15 行内容比较 |
| `decide()` 阶段判定 | 阶段判定散落在**三处 early-return**（`emit()` 内部 `sys.exit()`） | **重构**：先算阶段、不立即退出；design 域失鲜只在实现窗口内求值 |
| `emit()` 的 stale 诊断 | 不含锚值 | **修改**：`extra` 补 `reviewed_sha`，reason 拼出可执行的 `git diff` 命令 |
| **design 域帧比较整簇**：`frame_touched_paths`、帧遍历、`design_frame_exempt` / `_reason`、`commit_parents`、`_parent_path_status`、`_plain_content_modification`、`_plain_modification_from_raw`、`blob_pair`、`design_watched_subs`、`STALE_CATEGORIES`、BR-7 短路 | 帧枚举、subject 豁免与其全部下游 helper | **整簇退役**（逐一列名，防留悬空引用与孤儿测试） |
| `_stale_trigger_hint` / `StaleResult.trigger` | design 域专用触发点渲染 | **退役**（见 ADR-4） |
| `DESIGN_WATCHED_NAMES` / `_tasks_content_exempt` / `_normalize_checkbox_lines` | 固定清单常量 / 内容豁免判据 / 归一化核心 | **保留复用，MUST NOT 误删** |
| `run_git` / `run_git_rc` / `run_git_bytes` | 三处裸 `subprocess.run`，无 timeout、无异常捕获、不清 env | **修改**：`OSError`+`TimeoutExpired` 映射、`timeout=30`、`GIT_*` denylist 清理 |
| `main()` | 无顶层异常处置 | **修改**：`GateIndeterminate` → `UNKNOWN(6)` 的唯一映射点，按 payload 拼可行动诊断 |

## Decisions

### ADR-1：录锚取代反推

**决定**：producer 在报告 frontmatter 写 `reviewed_sha`；reader 读它，**缺失 / 格式非法 / 对象不存在 ⇒ fail-closed**。

**锚的语义 = 「被批准的盘面」，不是「写报告的时刻」**：拍板 / 放行这个动作批准的是哪个提交，锚就指哪个。
gate 的职责是「批准之后有没有被改」，不是「批准的内容对不对」——后者是人的判断范围。

**三镜取舍〔TG-23〕**：
- **系统镜**（主导）：反推式锚可被任何后续触碰无声前移，且该提交无需改动任何结论字段 ⇒ 攻击面消除是主导理由。
- **用户镜**：撞门者需知道「锚是哪个提交」才能自查 ⇒ 由 ADR-4 的 `emit` 补锚值兜住。
- **开发循环镜**：producer 侧多写一行、reader 侧多一次校验，无持续成本。
- **主次判定**：以系统镜为主——缺陷 9 存在时，其余修复的威胁模型一行都不成立。

**备选（已否决）**：保留 `report_last_sha`，另加「该 frontmatter 字段值最后一次变成当前取值的提交」的定向 blame。理由——把 git 语义搬进 Python 手搓一遍（撞基准 5），且 blame 对 merge/rewrite 的行为又是一片新的推断面。

**reader 契约 MUST 与 producer 同批落地**：`ship_gate.py` 的 frontmatter parser 目前只认三个枚举字段、其余静默忽略。只做 producer 的结果只有两种——**新锚永远读不到**，或**缺字段时回退旧锚（= 缺陷 9 原样存活）**。

**两层校验 MUST 显式分层**（`FIELD_ENUMS` 是有限枚举，容不下「任意 40 位 hex」）：
- **语法级**留在纯文本函数 `parse_ship_gate_frontmatter`（live 读与归档 git-show 文本读共用）：40 位 hex 格式，拒缩写 SHA / `HEAD` / 坏 SHA。
- **语义级**必须在有 `root` 的 `read_reviewed_sha` 里另做一次 git 调用（如 `git cat-file -e <sha>^{commit}`），确认解析为 **commit** 而非任意 blob/tree。

**`design_approved` 与 `reviewed_sha` MUST 在同一次文件写入中落盘**（不可拆两步 Edit）：
拆开且中断落在中间 ⇒ 盘面变成「`design_approved: true` 在、`reviewed_sha` 缺」⇒ `design_ok` 判 True 跳过 `REFUSE_START`，
但 reader 抛 `GateIndeterminate` → `UNKNOWN(6)`，是一个可恢复但无指引的中间态。

**frontmatter 挂载位置 MUST 统一**：`reviewed_sha` 是顶层 `ship-gate:` 键的**直接子键**，与既有三字段同层。
三个 producer 的模板逐字对齐（某处写成独立顶层键 ⇒ 该 producer 的锚永远读不到）：

```yaml
---
ship-gate:
  design_approved: true
  reviewed_sha: 0123456789abcdef0123456789abcdef01234567
---
```

### ADR-2：比内容取代枚举

**决定**：不再枚举「哪些路径被碰过」，直接比内容。

- **design 域**：对锚与 HEAD **各跑一次** `git ls-tree -r -z <ref> -- proposal.md design.md specs/`，
  比较 `path → (mode, type, oid)` **映射**；映射不等即失鲜。
  `tasks.md` 因需过 `_normalize_checkbox_lines` 才单独取内容比较。
- **code 域**：比 `git ls-tree`（浅层、不递归）的**顶层条目**，排除 `openspec` 条目后求等值。

**为什么比映射而不是逐文件比字节**：`ls-tree -r` 输出即 `mode type oid\tpath`，**天然含 mode 与 type**
⇒ 一次比较覆盖「存在性 / 对象类型 / mode / 内容」四者，且**新增、删除、rename 自动落网**。
逐文件比字节必须先决定「枚举哪一侧」——只枚举 HEAD 侧则锚有而 HEAD 已删的文件根本不出现（fail-open），
只枚举锚侧则 HEAD 新增的被跳过；要正确就得显式取两侧并集，那正是映射比较天然给的东西。
副作用：git 调用 8–10 次 → 4 次。**这是减法**。

**三镜取舍〔TG-23〕**：
- **系统镜**（主导）：八个缺陷同源于「拿管道当代理」，代理必有偏差且补不完 ⇒ 换判据而非补分支。
- **用户镜**：判定更稳（不受 config/env 翻转），撞门结论可复现。
- **开发循环镜**：调用次数减半、可出错分支归零、退役大量 helper。
- **主次判定**：系统镜为主，开发循环镜为强辅（映射比较同时是修 bug 与减复杂度）。

**备选（已否决）**：
① 继续枚举、逐个修补八个管道缺陷——4 与 5 互为解药兼病灶，7/8 属外部可控态，补丁螺旋不收敛（基准 5）。
② code 域用整棵树的 sha——**实测证伪**：done 写 `verify-report.md` 即改变整树 sha ⇒ 正常流程第一步就假阳。
③ code 域用负向 pathspec `':!openspec'`——**实测证伪**：继承 `GIT_ICASE_PATHSPECS`，该环境变量下真实代码目录会被误排除。

**勾选豁免 MUST 常开、按内容切、不按阶段切**：`tasks.md` 勾选框的写入方是 **agent 自由行为、不是 SKILL 契约**（前序 change 假设表 A1′ 已证；本仓 20 个 checkpoint 提交碰过 `tasks.md`，散在各阶段）。按阶段切 ⇒ 非该阶段的勾选立刻假失鲜。豁免面精确等于「归一化后逐行等值」这一已证零信息量的集合。

### ADR-3：限定求值窗口——判据只在其保护的风险真实存在的阶段求值

**决定**：design 域失鲜**只在阶段三起手至实现完成期间求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`）；进入代码审后不再求值。code 域两个检查已经是「位置即阶段」，无需改动。

**理由**：design 域失鲜保护的风险是「照着一份已经变了的设计继续建」——**该风险只在实现期存在**。实现完成后代码已经写完，此后对设计文档的修订是**文档对账**，而非「目标在移动」。

**该判据的必要性有历史数据支撑**：全仓 **14 个 `checkpoint(impl-review)` 提交改过四件套**——
代码审期修订设计产物是**常态而非偶发**（`opsx:verify` step 7 亦明文允许「revise design.md to match reality」，
`.claude/commands/opsx/verify.md:99`）。全阶段求值会把这 14 类情形全部误拦，产出的只有噪声。

**窗口内的合法 churn：契约上不应有，历史上出现过**。`sdflow-implement` 只读 `design.md`、撞问题走 halt 上抛
——这是**目标契约**。但全仓有 **3 个确证反例**（实现期 checkpoint 改过自身设计产物，最近一个在拍板后 1.6 小时）。
⇒ 本判据**有意收紧**：这类「边写边纠偏」模式今后会被 `REFUSE_START` 拦下，逼回「halt → 重走 spec-review → 重新拍板」的正规流程。
**这是行为收紧，不是 bug**，MUST 在 hand-off 显式登记，避免后续维护者误读。
∴ 窗口内**不设逃生口**——撞门的正解是走重审，不是加旁路。

**阶段判定 MUST 前移，且这是真实的控制流重排**：`RUN_SOP`(`:1237`) / `RUN_PLAN`(`:1243`) /
`CONTINUE_IMPL`(`:1269`) 分散在三处独立 `emit()`，而 `emit()` 内部 `sys.exit()` 是硬 early-return；
现状 design 检查是单一调用点且在三者之前（`:1214`）。
⇒ 挪到三者之后永远到不了，挪到三者之前等于没做窗口限定。
**唯一可行实现**：把检查分别塞进三个分支各自的 emit 之前（如引入 `emit_windowed()` 辅助函数），
或把 steps 5.5–7 重构成「算出 tentative verdict 但不 emit」再统一检查。
🔴 **实现若走捷径只在 step 7 后加一次检查 ⇒ `RUN_SOP`/`RUN_PLAN` 两条路径完全逃出失鲜检查，方向 fail-open。**

**三镜取舍〔TG-23〕**：
- **系统镜**：让出「代码审期与 done 期的设计修订不被记录」这一面（见残余面）。
- **用户镜**（主导）：全阶段求值在 14 类真实情形上产出纯噪声，且噪声会逼出一整套补偿机制。
- **开发循环镜**：窗口限定使判定保持全机械，无语义层、无逃生口、无留痕字段。
- **主次判定**：以用户镜为主——判据在「它保护的风险不存在的阶段」求值，产出的只有假阳。

**备选（已否决）**：
① 全阶段求值 + 语义逃生口（分诊后重锚、留理由）——为工作流明文允许的动作加一道仪式，改变不了结果；
且逃生口的阶段限制**拦不住**（gate 只能比较 `reviewed_sha` 的值，拦不住谁去写它），其机械性被高估。
② 全阶段求值 + 豁免按阶段生效——见 ADR-2，写入方不受阶段约束，实测证伪。

**无循环依赖**：阶段只取决于盘面上存在哪些产物（plan / code-review-report / verify-report），不取决于失鲜结论。

### ADR-4：诊断降级，但锚值 MUST 可见

**决定**：退役 `_stale_trigger_hint` 与 `StaleResult.trigger`；**同时** `emit()` 的 `extra` 补 `reviewed_sha`，
reason 直接拼出可执行命令（如 `核对差异：git diff <reviewed_sha> HEAD -- proposal.md design.md tasks.md specs/`）。

**理由**：触发点诊断原本依附于帧遍历（要 sha + subject）。帧遍历退役后，为凑齐诊断而保留一条枚举路径，
等于把刚砍掉的推断面从后门放回来。且该能力在 code 域**从未真正接通过**——`decide()` 的两个 code 域调用点
（`:1291`/`:1311`）本来就二元解包丢弃了 `trigger`（已核实）。

**但「一条 `git diff` 命令即得」这个说法只有在锚值可见时才成立**：三处 stale 的 `emit` 原本都不含锚值，
撞门者得先开报告 frontmatter 抄。∴ 补锚值是本 ADR 的**必要组成**，不是可选优化。
**这不与「不为凑诊断保留枚举通路」冲突**——`reviewed_sha` 是**录下来的常量**，读出来打印零推断成本。

### ADR-5：`timeout = 30`，对齐仓内既有先例

**决定**：三个 helper 统一 `timeout=30`。

**理由**：`sdflow-buglist/scripts/buglist.py::repo_root` 的 `git_timeout = 30` 注释写明判据：「纯本地元数据查询（正常毫秒级），30 秒是**文件系统卡死 / 网络文件系统挂起**的判定线，**不是性能预算**」。判据一致 ⇒ 取同值。**MUST NOT** 按「最慢的仓要多久」来定——那会把它误当性能预算。

**聚合上界的数量级**：design 域现在是 4 次调用（2 次 `ls-tree` + `tasks.md` 2 次 `show`），与提交数无关。
最坏情形（文件系统级挂起）单次 `decide()` 约 **2 分钟**落进 `UNKNOWN(6)`。
**有界 ≠ 短**——此处写出数量级，使评审者与后续维护者不必各自心算。

### ADR-6：外部态中和是 `_GIT_HARDEN` 的职责，配置面与环境面一次扫全

**决定**：`_GIT_HARDEN` 的职责由「中和 `core.quotePath`」重定义为「**中和一切能改变判定输入的外部可控态**」——
config 面走 `-c`，环境面走子进程 env 清理。

**env 清理 MUST 用 denylist**：复制 `os.environ` 后剔除 `GIT_` 前缀键，其余原样传入。
**MUST NOT 用 allowlist**（只显式构造 `PATH`/`HOME` 等几个键）——后者在 Windows 会漏
`SYSTEMROOT`/`COMSPEC` 等 `CreateProcess` 依赖变量，导致子进程启动本身失败；
这与本仓已踩过的跨平台坑同类：**本地 macOS 测不出，只有真实 Windows runner 才暴露**。

**理由**：缺陷 7（`diff.ignoreSubmodules`）与 8（`GIT_ICASE_PATHSPECS`）是**同一片面**。本方案已不调 diff、不用 pathspec，二者的直接利用面消失；但 `git show` / `ls-tree` 仍在子进程里跑，**MUST NOT** 依赖「我们碰巧没用到那些开关」作为安全论据（那是拿现状当保证）。实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工——方向安全，但会让门无故坏掉。

### ADR-7：`reviewed_sha` 的写入时序 MUST 与自动修复分离（否则 code 域自锁）

**决定**：`sdflow-code-review` 的 checkpoint 改为**两段提交**——自动修复（`[impl-review-fix]`）先单独提交，
`reviewed_sha` 指该提交；报告再单独提交。

**理由**：现状是「产出报告 + 自动修复后」**一起** checkpoint（`sdflow-code-review/SKILL.md:256-257`）。
若锚取「写报告时的 HEAD」，该 HEAD **不含**尚未提交的修复；checkpoint 一落，HEAD 前进、源码顶层条目改变
⇒ **code 域相对自己刚写下的锚立刻失鲜**。**每一轮有自动修复的代码审都会自锁。**

**该修法在本设计下天然可行**：code 域比较**排除 `openspec` 条目** ⇒ report-only commit（只动 `openspec/`）
不改变非 openspec 顶层条目 ⇒ 不触发失鲜。

**design 域天然免疫此问题**：其监视集是四件套 + `specs/`，**不含 `spec-review-report.md` 自己**
⇒ 写报告那个 commit 不动监视集。

### 关于「读失败 ≠ 内容为空」（本 change 的头号自噬风险）

内容比较 MUST **显式判 returncode**，MUST NOT 让两次失败读比较相等。

验证 fixture 中已出现过该形态：两侧 `git show` 均因仓损坏失败、各返回空串，比较判「同」⇒ **假绿**。
这与缺陷 3、10（把非零退出折成 `''`）是**同一个失效模式**——本 change 正是来修它的，而新实现同样能踩进去。
∴ 立为显式约束并配变异证明。

**`ls-tree` 单侧缺失 MUST 判 stale，MUST NOT 混作读取失败**——二者是不同的事：
前者是「该路径在一侧不存在」（合法信号，映射不等），后者是「读不出来」（不可判，`GateIndeterminate`）。

### 关于 `GateIndeterminate` 的诊断结构

`GateIndeterminate` MUST 携带结构化 payload（复用仓内 `_fail_closed_on_bad(err, label)` `:956-959` 的
`(cause, category)` 二元组模式），`main()` 的映射点按 payload 拼出**各自可行动**的 reason：

| 原因 | 撞门者该做什么 |
|---|---|
| git 不在 PATH / 不可执行 | 检查环境、装 git |
| 调用超时（>30s） | 检查磁盘或网络文件系统 |
| `reviewed_sha` 缺失 | **该报告产出于本次硬化之前 → 重跑对应评审补锚** |
| `reviewed_sha` 非法 / 对象不存在 | 可能 force-push 改写了历史，需人工排查 |
| 读失败（仓损坏 / 权限） | 检查仓完整性 |

**MUST NOT** 用一句「git 调用失败」打天下——五者的补救动作完全不同，而 `UNKNOWN` 在 `/sdflow-ship`
链序里的处置正是「停并转述 reason」，reason 空洞 = 撞门者被裸退出码打发。

## 安全与数据保护〔BASE-28 · TG-17〕

**被保护的资产**：「设计审已拍板 / 代码审已放行 / verify 已通过」三个结论的有效性。它们是 merge 之前仅有的质量门。

**威胁模型**：

| 谁 | 怎么做 | 修复前 | 修复后 |
|---|---|---|---|
| 走正常流程的开发者/agent | 代码审后在 merge 提交里 resolve 出源码改动 | 🔴 判 fresh | ✅ 顶层条目不等 → stale |
| 同上 | `git mv` 把源码迁进 `openspec/` | 🔴 判 fresh | ✅ 源路径所属顶层条目不等 → stale |
| 同上 | 实现期把已批准设计换成别的内容后继续建 | 🔴 视手段可绕（缺陷 1/2/5） | ✅ 映射不等 → stale（构造性，不依赖拓扑） |
| 同上 | 实现期在 `specs/` 下新增 / 删除 / rename 文件 | 🔴 单侧枚举漏检 | ✅ `path→(mode,type,oid)` 映射不等 → stale |
| 任何后续提交者（**无需恶意**） | 顺带碰一下报告文件（空行 / CI reformat）⇒ 锚前移，埋掉锚前的未审改动 | 🔴 判 fresh | ✅ 锚是记录值，推不动 |
| 环境异常（非攻击者） | git 调用失败 / 配置或环境变量异常 | 🔴 判 fresh | ✅ fail-closed → `UNKNOWN(6)` + 可行动诊断 |
| 无（假阳面） | 设计门拍板后例行合并 main | 🔴 假判 stale，卡死正常流程 | ✅ 内容未变 → fresh |
| 无（假阳面） | done 写 `verify-report.md` / archive 移目录（纯 `openspec/` 记账） | — | ✅ 其余顶层条目未变 → fresh |
| 无（假阳面） | 代码审期修订四件套（14 个历史提交） | 🔴 假判 stale | ✅ 窗口外不求值 → fresh |

**残余面（显式登记，本次不覆盖）**：

- 🔴 **归档终态（`verify` 检查点之后到 `merge` 之间）无失鲜检查** —— 两条路径，**均已评估并有意接受**：
  ① **已提交路径**：`:1311` 检查后 → `sdflow-done` 执行 archive + commit + merge → 重跑 gate 时 `cdir` 已不存在
  → D3 短路凭归档 `verify=PASS` 判 `SHIPPED`，全程不调 `is_stale`。
  ② **未提交路径**：gate 只看 committed（T33/T35 明文定夺），而 `sdflow-done` 第四步是无范围限制的 `git add -u`
  ⇒ 早已躺在工作树、从未被检查过的改动会被一次性收编进最终提交。
  **接受理由**：`sdflow-done` 在 verify 之后的动作（archive / commit / merge）**本身都不改源码**，
  流程正常走完时该窗口是空的；工作树 dirty 是本仓已明文定夺的边界，且 merge 前已有 untracked 硬检查兜一层。
  **代价**：若有人手动在该窗口改源码，或改动早于 verify 就躺在工作树里，则不被记录。**与 T179 属同一盲区的两半。**
- 🔴 **窗口右边界的间隙** —— 「实现刚完成」与「代码审进行中」在盘面上**不可区分**（都是 plan 全勾 + 无 cr 报告）
  ⇒ 该间隙内的四件套改动不被求值。**纯盘面判据关不上它**，要关就得引入新盘面信号（如代码审起手先落标记文件），
  属加机制，与本 change 的简化方向相悖。
  **第二层覆盖**：代码审的 scope-drift 检查（Step1 走 `DIFF_BASE..HEAD` 全范围，本职即抓「顺手多改」）会看到它——
  但那是**模型判断、不是机械门**，此处不吹成已兜住。
- 🔴 **代码审期与 done 期对设计文档的修订不再被 gate 记录** —— 求值窗口之外的直接后果。
  **完整后果链**：`opsx:verify` 明文允许「revise design.md to match reality」⇒ 设计可被改成匹配已写出的代码
  ⇒ **verify 随后依据改写后的目标判 PASS**，即「唯一终门」在核对一个**可被移动的靶子**。
  **接受理由**：这是 `opsx:verify` 的流程性质（verify 被授权改靶子），不是失鲜判据能解决的；
  修它需引入不可变 approved-design digest，即把本 change 刚砍掉的那类机制加回来。
  落进既有的「人机同权、篡改留痕可审计」残余面，只有 git 历史可查。
- **拍板前的修订未被镜审** —— 镜子审的是 C1，人读报告后要求修改产生 C2，拍板批准的是 C2。
  **锚写 C2 是正确的**（拍板批准的就是它），但报告里的 findings 只针对 C1。
  **处置在流程层而非 gate 层**：`sdflow-spec-review` 收敛口加纪律——拍板前若四件套相对审查基线有**实质**改动，
  MUST 先跑一次窄复核再拍板。gate 看不出「这次改动有没有被审过」，不该由它管。
- **有写权限者直接改 `reviewed_sha`** —— 与改结论字段同权级，留痕可审计。不在失鲜判据职责内。
- 🔴 **T189 耦合与承重升格** —— `_normalize_checkbox_lines` 在旧设计里只是众多判据之一，
  **在新设计下是 design 域唯一的放行闸门**（比内容 + 单一内容豁免）；而它自己登记着基准 5 警号
  （T189：「已第 4 轮往同一函数补语法分支，口径应反转为白名单」）。
  承重程度上升而口径缺陷未修 ⇒ 显式登记，本次不 fold（独立面）。
- 本 change 提升的是**误操作与流程漏洞**的拦截率，**不声称**能挡有意规避者。

## Risks / Trade-offs

- **[实现走捷径导致 `RUN_SOP`/`RUN_PLAN` 逃出检查]** → 缓解：ADR-3 已写明唯一可行实现路径；tasks 拆显式子项；变异证明须分别覆盖三个分支。
- **[共享 fixture 与新锚模型结构性不兼容]** → 缓解：`approved_change()` 现为单次 `commit_all` 的根提交，**不存在先于报告的 HEAD 可填锚**；已立为显式任务（重构为两段提交），MUST NOT 指望「全套件回归」顺带发现。
- **[退役大量已上线行为]** → 缓解：退役清单已扩到完整簇（含全部下游 helper）；测试删除拆成「纯删除」与「需重新设计等价用例」两类，后者（evil-merge / `git mv` 等承载仍生效安全承诺的用例）并入新增用例编号体系。
- **[存量报告缺 `reviewed_sha` 撞门]** → 缓解：在途的只有本 change 自己；fail-closed 方向安全；诊断给针对性措辞；hand-off 提供消费仓只读自查命令。
- **[新实现踩进「读失败 = 内容为空」]** → 缓解：立为显式约束 + 变异证明。
- **[变异证明流于形式]** → 缓解：spec 已把「删掉守卫即变红」写成需求；两条手段不同源的守卫已单独说明；结果逐条落 impl-report。

## Migration Plan

1. 本仓为 toolkit 源仓：改动经 push → 各消费仓 **`/sdflow-upgrade`**（或手动 `git pull` + `setup.sh`）生效。
   ⚠️ **`sdflow-init update` 对本 change 无效**——`ship_gate.py` 与三个评审 SKILL 都不在
   `sdflow-init/assets/workflow/` bundle 内，它只刷新项目本地 `openspec/workflow/` 规则副本。
2. **producer 与 gate MUST 同批发布**——只发 producer 则新锚读不到，只发 gate 则所有存量报告 fail-closed。
   **分发原子性因平台而异**：Unix 走 `ln -snf`（`setup.sh:68`），`git pull` 落盘即同时生效，近乎瞬时一致；
   **Windows 走 `cp -r` 逐目录**（`:38`/`:53`），字母序 `sdflow-ship` 在 `sdflow-spec-review` 之前
   ⇒ setup.sh 中断会产生「新 gate + 旧 producer」（方向 fail-closed，安全但会挡住流程）。
   Windows 上 setup.sh 勿中断；中断后重跑可自愈（幂等）。
3. **存量 active 报告**（无 `reviewed_sha`）⇒ fail-closed ⇒ 须重审一次。**MUST NOT** 为兼容而静默回退旧锚。
   hand-off MUST 提供消费仓**只读自查命令**，一次列出「本仓有几个 active change 会因缺锚而 fail-closed」，
   而不是让人逐个撞门才发现代价（全仓无下游消费仓清单，实际影响面不可估算）。
4. **回滚**：`ship_gate.py` 是纯只读判官，无持久状态。回滚 = 还原文件 + 重跑 `setup.sh`；
   已写入的 `reviewed_sha` 对旧 gate 是未知字段，被静默忽略（已核实：`:876-877` `if field not in FIELD_ENUMS: continue`）。
   🔴 **但回滚不对称，MUST 人工核验后再回**：旧 gate 在 `:1214` **无条件全阶段求值** design 失鲜。
   若某 change 已在新 gate 下进入代码审后修订过四件套（这在新语义下合法、且历史上有 14 例），
   回滚会使其立刻撞 `REFUSE_START`(exit 3)，把正常推进中的 change 打回。
   **回滚前 MUST 核验在途 change 的阶段**——这是新语义特有、旧语义无对应保护的假阳，非「回滚到已知旧缺陷」的正常代价。

## Open Questions

无。

## Compliance

实现期 MUST 遵守（本节逐字进 `superpowers-plan.md` 的 `## Global Constraints`）：

- 内容比较 **MUST** 显式判 returncode；**MUST NOT** 让两次失败读比较相等（读失败 ≠ 内容为空）。
- `ls-tree` **单侧缺失 MUST 判 stale**，**MUST NOT** 混作读取失败。
- **MUST NOT** 在 `reviewed_sha` 缺失/非法时回退到 `report_last_sha` 或任何反推式锚。
- **MUST NOT** 为凑触发点诊断而保留任何路径枚举通路；但 `emit` **MUST** 输出 `reviewed_sha` 值。
- 勾选豁免 **MUST** 常开、按内容切；**MUST NOT** 按阶段切。
- design 域失鲜 **MUST** 只在实现窗口内求值，且 **MUST** 分别覆盖 `RUN_SOP`/`RUN_PLAN`/`CONTINUE_IMPL` 三个分支；
  **MUST NOT** 只在 step 7 后加一次检查（那会让前两个分支逃出检查）。
- **MUST NOT** 引入语义分诊层或任何形式的重锚逃生口。
- 监视集 **MUST** 保住：实现期改源码、勾 `superpowers-plan.md` 复选框 **MUST NOT** 让设计门失鲜。
- code 域 **MUST NOT** 用整棵树的 sha，**MUST NOT** 用负向 pathspec（二者均已实测证伪）。
- 子进程 env 清理 **MUST** 用 denylist（剔除 `GIT_` 前缀），**MUST NOT** 用 allowlist（Windows 会漏系统变量）。
- `design_approved` 与 `reviewed_sha` **MUST** 在同一次文件写入中落盘。
- `reviewed_sha` **MUST** 挂在顶层 `ship-gate:` 键下作直接子键，三个 producer 模板逐字对齐。
- `GateIndeterminate` **MUST** 携带结构化 payload，五类失败原因各给可行动诊断。
- 每条新增守卫 **MUST** 附变异证明（删掉即变红），结果落 impl-report；**MUST NOT** 以「用例存在且为绿」充当证明。
- 新增用例 **MUST** 经 `is_stale` 公共入口求值（**例外**：`OSError`/`TimeoutExpired` 用例的触发点可能在
  `is_stale` 调用范围之外，如 D3 短路分支——此类显式豁免，改为经 `decide()`/`main()` 求值）。
- code 域的**两个**消费方（`code-review-report`、`verify-report`）**MUST** 各有覆盖。
- 删除既有用例 **MUST** 在 impl-report 逐条说明其对应哪个退役机制，并区分「纯删除」与「需重新设计等价用例」。
- 共享 fixture（`approved_change` / `tail_ok` / `impl_done`）**MUST** 与新锚模型同批重构。
- `ship_gate.py` **MUST** 保持零第三方依赖；退出码 **MUST** 落在 `{0,3,4,5,6}` 内。
