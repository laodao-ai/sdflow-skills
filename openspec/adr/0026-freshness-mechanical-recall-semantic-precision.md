# 失鲜判定的机械层只保**召回**，精确率交语义层；**监视集是承重的、枚举不是**

`ship_gate.py` 的失鲜判定要回答「评审结论是否已被后续提交作废」。历史实现一律是**从 git 管道信号推断**「被审过的内容变了没有」：`git log --name-only` → `git diff-tree -m` → `--cc`。

一轮 grill + 一轮多镜设计审（4 镜 + 广审双声 + 2 站点跨模型 voice）在这条推断链上累计挖出**八个**缺陷，全部实测复现：

| # | 缺陷 | 方向 |
|---|---|---|
| 1 | `git log --name-only` 对 merge 提交不输出路径 | fail-open |
| 2 | rename detection 默认开，源路径逃出监视集 | fail-open |
| 3 | 非零退出折叠成空串 ⇒ 零帧 ⇒ 等价「无可疑提交」 | fail-open |
| 4 | `-m` 逐 parent 输出，parent2 常早于锚 ⇒ 重报锚前历史 | fail-**closed** 假阳 |
| 5 | `--cc` 只报「相对所有 parent 都不同」的文件 ⇒ 合并结果等于某 parent 时隐身 | fail-open |
| 6 | 控制字符路径被 C-quote 弄花，前缀判定失准 | 两域方向相反 |
| 7 | `diff.ignoreSubmodules=all` ⇒ 未审 submodule bump 判 fresh | fail-open |
| 8 | `GIT_ICASE_PATHSPECS=1` ⇒ 负向 pathspec 误排除真实代码目录 | fail-open |

**这八个不是八个 bug，是同一个根因的八张脸**：拿 git 管道当「内容是否改变」的代理。代理必有偏差，补偏差就长复杂度，而且**补不完**——4 与 5 互为对方的解药又互为对方的病（`-m` 修假阳造假阴，`--cc` 修假阴造假阳），7 与 8 更是**外部可控态**（一个 config、一个环境变量）就能翻转判定。这正是 `CLAUDE.md` 基准 5 警告的形状：「每轮 review 都在同一个函数里补一个新的语法分支，那不是还差最后一个 case，那是这个函数本来就不该存在」。

**决策**：失鲜判定的机械层**只承诺召回**（任何实质改动都不漏），**不承诺精确**（可以误报）；误报由**语义层**（主 session 读 diff 判断）分诊，分诊结论**MUST 落盘留痕**。据此，机械层放弃「从管道推断被碰过哪些路径」，改为**录锚 + 直接比内容**：

- **锚**：评审时把当时的 HEAD sha 写进报告 frontmatter（`reviewed_sha`）。锚是**记录的**，不是从「最后一次触碰报告路径的提交」反推的。
- **design 域**：监视集是**固定清单**（`proposal.md`/`design.md`/`tasks.md` + `specs/` 子树）⇒ 逐文件 `git show <锚>:<path>` 与 HEAD 比字节；`tasks.md` 比之前过 `_normalize_checkbox_lines`。
- **code 域**：监视集是「除 `openspec/` 外的一切」，列不出固定清单 ⇒ 退用**整树 sha 比较**，不等即交语义分诊。

**「监视集」与「枚举」MUST 分开看**：前者（只盯四件套 / 只盯非 `openspec/`）是**承重的**——它才是「实现期改源码不该让设计门失鲜」这条性质的来源；后者（从 git 管道推断哪些路径被碰过）只是实现监视集的一种**手段**，且是产出上述八个缺陷的那一种。**砍枚举，留监视集。**

## Considered Options

- **录锚 + 直接比内容，机械保召回、语义补精确（选中）**：八个缺陷**整类消失**而非逐个修补——不枚举路径 ⇒ 1/2/4/5/6 无从发生；不调 diff 做判定 ⇒ 7/8 无从发生；锚是记录值 ⇒ 不可被后续提交无声前移；缺字段 fail-closed ⇒ 3 无从发生。代价见 Consequences。
- **继续枚举，逐个修补八个缺陷**：未选——4 与 5 互为解药兼病灶，7/8 属外部可控态且**枚举面上补不完**（下一个 `diff.*` / `GIT_*` 会以同样方式重现）。这正是基准 5 点名的补丁螺旋。
- **`reviewed_sha == HEAD` 的裸比较（无监视集）**：未选——**实测证伪**：实现期每个 ticket 都在勾 `tasks.md`、每个提交都在动 HEAD ⇒ 设计门从实现的第一个提交起永远失鲜。这恰是 `fix-design-gate-freshness-proxy` 当初要修的缺陷，裸比较把它退了回去。**监视集不可砍。**
- **纯内容快照、无语义逃生口**：未选——表达不了「阶段三 `[impl-review-fix]` 修订可以改设计产物而不作废设计门」这条既有政策（原 BR-7 承载）。语义逃生口正是该政策的新载体。

## Consequences

- **BR-7（`checkpoint(impl-review)` subject 豁免）退役，其政策迁入语义层**：不再靠匹配 commit subject 字符串，改由主 session 读真实 diff 判断并**重锚 + 写理由**。判据从「谁改的」升级为「改了什么」，是升级不是降级；但**确定性被交换掉了**——同一盘面两次可能判不同，缓解 = 重锚 MUST 附理由、留 git 痕（与本仓既有「人机同权、篡改可审计」姿态一致，见 `adr/0008`）。
- **`frame_touched_paths` / 帧遍历 / `design_frame_exempt_reason` / 触发点诊断管道整体退役**，`_normalize_checkbox_lines`（内容豁免核心）**保留复用**。
- **读失败 MUST 与「内容为空」显式区分**：本 ADR 起草期的验证 fixture 亲历——两边 `git show` 都失败成空串、比较判「同」= 假绿。与缺陷 3（`run_git` 折叠非零退出）**同类**，∴ 内容比较 MUST 显式判 returncode，MUST NOT 让两次失败读比较相等。
- **子进程 MUST 清理 `GIT_*` 环境变量**：实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下直接 fatal 拒绝执行（方向安全，但会让门在该环境下无故罢工）。`_GIT_HARDEN` 的职责由「中和 `core.quotePath`」扩为「**中和一切能改变判定输入的外部态**」，config 面走 `-c`、环境面走子进程 env 清理。
- **存量 active 报告无 `reviewed_sha` ⇒ fail-closed ⇒ 须重审一次**。reader **MUST NOT** 在字段缺失时静默回退到旧的可移动锚（回退 = 缺陷原样存活）。
- **与基准 1 的关系（须知情）**：基准 1 是「能机械化的优先机械化」。本 ADR **不是**对它的例外——机械层仍在，且它承担的是**不可让渡的那一半（召回）**；让渡出去的是精确率，而精确率的机械化恰恰是八个缺陷的产地。切分线判据仍是 [[mechanical-judgment-split-signal-criterion]]：「内容变没变」有确定性信号（字节比较）⇒ 机械；「这处变化要不要紧」无确定性信号 ⇒ 语义。
- **与 `adr/0011` 的关系**：0011 立「改共用解析核心 MUST 逐调用方论证、MUST grep 列全调用点」。本轮再次自证其必要——proposal 假设 A5 写「无第三消费方 ✅」，实际三个（`:1214`/`:1291`/`:1311`），且现存唯一的 code 域用例走的正是第三个，`code-review-report` 那条路径零覆盖。
- **CONTEXT.md**：术语「问题先于原语」改写为「**召回归机械、精确归语义（Recall-Mechanical, Precision-Semantic）**」。
