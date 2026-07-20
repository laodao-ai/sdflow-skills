# 失鲜判定：**录锚 + 比内容 + 只在判据保护的风险真实存在的阶段求值**

`ship_gate.py` 的失鲜判定要回答「评审结论是否已被后续提交作废」。历史实现一律是**从 git 管道信号推断**「被审过的内容变了没有」：`git log --name-only` → `git diff-tree -m` → `--cc`。

一轮 grill + 一轮多镜设计审（4 镜 + 广审双声 + 2 站点跨模型 voice）在这条链上累计挖出**十个缺陷、全部实测复现**：

| # | 缺陷 | 方向 |
|---|---|---|
| 1 | `git log --name-only` 对 merge 提交不输出路径 | fail-open |
| 2 | rename detection 默认开，源路径逃出监视集 | fail-open |
| 3 | 非零退出折叠成空串 ⇒ 零帧 ⇒ 等价「无可疑提交」 | fail-open |
| 4 | `-m` 逐 parent 输出，parent2 常早于锚 ⇒ 重报锚前历史 | 假阳 |
| 5 | `--cc` 只报「相对所有 parent 都不同」者 ⇒ 合并结果等于某 parent 时隐身 | fail-open |
| 6 | 控制字符路径被 C-quote 弄花，前缀判定失准 | 两域方向相反 |
| 7 | `diff.ignoreSubmodules=all` ⇒ 未审 submodule bump 判 fresh | fail-open |
| 8 | `GIT_ICASE_PATHSPECS=1` ⇒ 负向 pathspec 误排除真实代码目录 | fail-open |
| 9 | `report_last_sha` = 「最后触碰报告路径的提交」⇒ 任何后续触碰把锚前移，埋掉锚前的未审改动 | fail-open |
| 10 | 锚获取的 `run_git` 非零退出折成 `''` ⇒ 判 `uncommitted` ⇒ fresh | fail-open |

**这不是十个 bug，是两个根因**：

**根因一（1–8、10）：拿 git 管道当「内容是否改变」的代理。** 代理必有偏差，补偏差就长复杂度且补不完——4 与 5 互为对方的解药又互为对方的病（`-m` 修假阳造假阴，`--cc` 修假阴造假阳），7 与 8 更是**外部可控态**（一个 config、一个环境变量）即可翻转判定。这正是 `CLAUDE.md` 基准 5 点名的补丁螺旋。

**根因二（9）：拿「最后触碰」反推锚。** 锚可被任何后续触碰无声前移，且该提交无需改动任何结论字段。

**决策**：

1. **录锚**：评审时由 producer 把当时的 HEAD sha 写进报告 frontmatter（`reviewed_sha`）。锚是**记录的**，不是反推的。缺失 / 非 40 位 OID / 对象不存在 ⇒ **fail-closed**，MUST NOT 回退反推式锚。
2. **比内容**：不再枚举「哪些路径被碰过」，直接比内容。design 域监视集是**固定清单**（`proposal.md`/`design.md`/`tasks.md` + `specs/` 子树）⇒ 逐文件 `git show <锚>:<path>` 与 HEAD 比字节，`tasks.md` 比之前过 `_normalize_checkbox_lines`（已证零信息量的内容豁免，**常开、按内容切、不按阶段切**）。code 域监视集列不出清单 ⇒ 比 `git ls-tree` 的**顶层条目**、排除 `openspec` 条目后求等值（**MUST NOT 用整棵树的 sha**——实测 done 写 `verify-report.md` 即改变整树 sha，正常流程第一步就假阳）。
3. **求值窗口**：判据 MUST **只在它保护的风险真实存在的阶段求值**。design 域失鲜的风险是「照着一份已经变了的设计继续建」——该风险**只在实现期存在**。∴ design 域失鲜**只在阶段三起手至实现完成期间求值**（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`）；进入代码审后不再求值。code 域的两个检查**已经是「位置即阶段」**（`:1291` 在代码审之后才可达，`:1311` 在 done 之后），无需改动。

**第 3 条是本 ADR 的核心，也是最反直觉的一条**：剩余的假阳全部来自**在不该求值的阶段继续求值**——代码审期的 `[impl-review-fix]` 修订、done 期 `opsx:verify` 的「revise design.md to match reality」（`.claude/commands/opsx/verify.md:99`）都是工作流**明文正解**，在那些阶段判失鲜产出的只有噪声。而为噪声造豁免，会长出一整套补偿机制（语义分诊、重锚协议、重锚留痕、不可变锚字段……）——**限定窗口把这一整套证明成不必要的**。

## Considered Options

- **录锚 + 比内容 + 限定求值窗口（选中）**：十个缺陷整类消失；且因窗口内**无合法 churn**（`sdflow-implement` 只读 `design.md`，撞问题走 halt 上抛；全仓历史零个实现期提交改过监视集），**无需任何逃生口**，判定保持全机械、确定性不被交换掉。
- **继续枚举，逐个修补**：未选——4/5 互为解药兼病灶，7/8 属外部可控态，枚举面上补不完（下一个 `diff.*` / `GIT_*` 会以同样方式重现）。
- **全阶段求值 + 语义逃生口（分诊后重锚、留理由）**：未选——起草期曾选中并写入四件套，后被推翻。它为「后期合法修订」造了一整套补偿机制，而这些修订**本就是工作流明文允许的**，gate 拦它只能多加一道仪式、改变不了结果；且逃生口的阶段限制**拦不住**（gate 只能比较 `reviewed_sha`，拦不住谁去写它），机械性被高估。限定窗口后该机制整体不需要。
- **全阶段求值 + 豁免按阶段生效**：未选——**实测证伪**：`tasks.md` 勾选框的写入方是 **agent 自由行为、不是 SKILL 契约**（前序 change `fix-design-gate-freshness-proxy` 假设表 A1′ 已证；本仓 20 个 checkpoint 提交碰过 `tasks.md`，散在各阶段）。把勾选豁免按阶段切 ⇒ 非该阶段的勾选立刻假失鲜 ⇒ 退回前序 change 修的那个缺陷。**内容豁免 MUST 常开、按内容切。**
- **`reviewed_sha == HEAD` 的裸比较（无监视集）**：未选——实现期每个提交都在动 HEAD ⇒ 设计门从第一个实现提交起永远失鲜。**监视集是承重的、枚举不是**：前者（只盯四件套 / 只盯非 `openspec/`）才是「实现期改源码不该让设计门失鲜」的来源；后者只是实现它的一种手段，且是十个缺陷里八个的产地。**砍枚举，留监视集。**

## Consequences

- **BR-7（`checkpoint(impl-review)` subject 豁免）退役**：它的政策（阶段三修订设计产物不作废设计门）由**求值窗口**承载——那些修订发生在窗口之外，根本不被求值。判据从「谁改的」（可伪造的 subject 代理）变成「什么时候改的、那时这条判据还管不管用」，且后者由 gate 自己算出。
- **`frame_touched_paths` / 帧遍历 / `design_frame_exempt_reason` / `_stale_trigger_hint` / `StaleResult.trigger` / `report_last_sha` 整体退役**；`_normalize_checkbox_lines` **保留复用**。
- **判定保持全机械**：本 ADR 起草中途曾引入语义分诊层，后随窗口限定一并取消。**MUST NOT** 因「精确率难做」而重新引入语义层——精确率的问题大部分是求值窗口画错了，不是判据不够聪明。
- **残余面（显式登记）**：**代码审期与 done 期对设计文档的修订不再被 gate 记录**。可接受，两条理由：① 那些修订是工作流明文允许的（`[impl-review-fix]`、`opsx:verify` design adherence），gate 拦它只能加仪式；② 落进既有的「人机同权、篡改留痕可审计」残余面，与「有写权限者直接改结论字段」同权级。
- **读失败 MUST 与「内容为空」显式区分**：本 ADR 起草期的验证 fixture 亲历——两边 `git show` 都失败成空串、比较判「同」= 假绿。与缺陷 3、10 **同一失效模式**，∴ 内容比较 MUST 显式判 returncode。
- **子进程 MUST 清理 `GIT_*` 环境变量**：实测 `ls-tree` 在 `GIT_ICASE_PATHSPECS=1` 下 fatal 罢工（方向安全，但会让门无故坏掉）。`_GIT_HARDEN` 职责由「中和 `core.quotePath`」扩为「**中和一切能改变判定输入的外部可控态**」，config 面走 `-c`、环境面走 env 清理。
- **存量 active 报告无 `reviewed_sha` ⇒ fail-closed ⇒ 须重审一次**；reader **MUST NOT** 在缺字段时静默回退。
- **与 `adr/0011` 的关系**：0011 立「改共用解析核心 MUST 逐调用方论证、MUST grep 列全调用点」。本轮再次自证其必要——初稿假设「无第三消费方 ✅」，实际三个（`:1214`/`:1291`/`:1311`），且现存唯一的 code 域用例走的正是第三个。
- **CONTEXT.md**：新增术语「**求值窗口（Evaluation Window）**」。
