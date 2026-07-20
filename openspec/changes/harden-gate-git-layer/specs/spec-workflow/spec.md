## ADDED Requirements

### Requirement: 判据 MUST 只在其保护的风险真实存在的阶段求值

失鲜判据 MUST 只在其保护的风险真实存在的阶段求值，MUST NOT 全阶段求值后再为「合法 churn 阶段」补造豁免或逃生口。

design 域失鲜保护的风险是「照着一份已经变了的设计继续建」——该风险只在实现期存在。∴ design 域失鲜 MUST 只在阶段三起手至实现完成期间求值；进入代码审后 MUST NOT 再求值。

阶段判定 MUST 在失鲜判定**之前**完成。二者无循环依赖：阶段只取决于盘面上存在哪些产物，不取决于失鲜结论。

#### Scenario: 代码审期与 done 期不求值 design 域失鲜

- **WHEN** 流程已进入代码审期或 done 期，此时对四件套的修订发生（如 `[impl-review-fix]` 修订，或 verify 的 design adherence 检查判定「revise design.md to match reality」）
- **THEN** gate MUST NOT 因该修订判 design 域失鲜——这些修订是工作流明文允许的动作
- **AND** MUST 有用例锁死此方向

#### Scenario: 实现期无逃生口

- **WHEN** 在实现窗口内，design 域监视集内容与锚版本不等值（且差异不止于复选框状态）
- **THEN** gate MUST 判失鲜，且 MUST NOT 提供任何「分诊后重锚」「按 commit subject 豁免」之类的旁路
- **AND** 实现窗口内**无合法的四件套实质修订流程**（实现只读 `design.md`，撞问题走 halt 上抛）⇒ 该判定不会误拦合法动作
- **AND** MUST 有用例

### Requirement: 失鲜判定 MUST 直接比较内容，MUST NOT 从 git 管道推断路径变更

机械层 MUST NOT 使用下列任一方式判定「被审内容是否改变」：`git log --name-only`、`git diff-tree -m`、`git diff-tree --cc`、负向 pathspec、整棵树的 sha。这些方式已累计产出实测复现的缺陷（详见 `openspec/adr/0026`），且互为解药兼病灶、可被外部 config/env 翻转。

机械层 MUST 改为直接比较内容：design 域按固定监视清单逐文件比较字节；code 域比较 `git ls-tree` 的顶层条目（排除 `openspec` 条目后）。

复选框豁免 MUST 常开、按**内容**切，MUST NOT 按阶段切——`tasks.md` 复选框的写入方是不受阶段约束的自由行为，按阶段切会立即产生假失鲜。

#### Scenario: 实现期不得让设计门失鲜

- **WHEN** 设计门拍板后进入实现期，提交改动源码文件，并把 `superpowers-plan.md` 中该 ticket 的验收复选框由 `- [ ]` 勾成 `- [x]`
- **THEN** gate MUST 判 design 域 fresh——源码与 `superpowers-plan.md` 均不在 design 域监视集内
- **AND** **监视集是承重的**：任何令实现期提交使设计门失鲜的实现（如裸 `reviewed_sha == HEAD` 比较）MUST 判为不合格

#### Scenario: `tasks.md` 纯复选框翻转不失鲜（任何阶段）

- **WHEN** `tasks.md` 的内容差异在复选框标记归一化后逐行等值
- **THEN** gate MUST 判 fresh，且该豁免 MUST 与当前处于哪个阶段无关
- **AND** 差异超出复选框状态时 MUST 照常判失鲜

#### Scenario: 合并把已批准产物换回锚前旧内容

- **WHEN** 锚提交之后的一次合并，使某监视文件在 HEAD 上的内容变回锚**之前**某祖先版本（该内容不由锚后任何提交引入，故任何逐提交枚举都看不到它）
- **THEN** gate MUST 判失鲜——内容比较不依赖提交拓扑，锚与 HEAD 的字节不等即成立
- **AND** MUST 有用例，且 MUST 经 `is_stale` 公共入口求值

#### Scenario: `openspec/` 内的记账不得让 code 域失鲜

- **WHEN** 代码审通过后，正常收尾流程写入 `verify-report.md`、或 archive 把 change 目录移入 `openspec/changes/archive/`——即改动全部落在 `openspec/` 之内
- **THEN** gate MUST 判 code 域 fresh
- **AND** 该域的比较粒度 MUST 能排除 `openspec/`：整棵树的 sha 比较 **MUST NOT** 被采用——它在上述正常流程的第一步即假阳（已实测）

### Requirement: 评审锚 MUST 由 producer 记录，MUST NOT 从提交历史反推

评审结论的锚 MUST 是评审时由 producer 写入报告 frontmatter 的显式提交标识（`reviewed_sha`），MUST NOT 由「最后一次触碰报告文件路径的提交」之类的反推方式得出。

反推式锚可被任何后续触碰该文件的提交无声前移，从而把锚前的未审改动埋在判定范围之外——该提交无需修改任何结论字段，在 `git log -p` 中与评审结论毫无关联，其隐蔽性不被「篡改结论字段留痕可审计」这一既有残余面覆盖。

#### Scenario: 无关的报告排版提交不得移动锚

- **WHEN** 评审通过后，先有提交引入未经审查的源码改动，再有一个与之无关的提交仅修改报告文件的排版（如补一个换行），且不改动任何结论字段
- **THEN** gate MUST 仍判失鲜——锚为 producer 记录值，不因报告文件被触碰而前移

#### Scenario: 锚缺失或非法时 fail-closed

- **WHEN** 报告 frontmatter 缺 `reviewed_sha`、其取值不是完整 40 位 OID、或该对象在仓中不存在
- **THEN** gate MUST 判 `UNKNOWN`（exit 6），MUST NOT 回退到任何反推式锚、MUST NOT 判 fresh
- **AND** reader 契约 MUST 与 producer 同批落地：只落 producer 会使新锚永不被读取，只落 reader 会使存量报告全部 fail-closed
- **AND** 存量无 `reviewed_sha` 的报告 MUST 要求重审一次，MUST NOT 为兼容而静默回退

### Requirement: 内容比较 MUST 区分读失败与内容为空

比较两个版本的文件内容时，MUST 显式判定读取操作的返回码，MUST NOT 让两次失败的读取因各自返回空结果而比较相等。

此为「非零退出被折叠成空结果」这一失效模式在新实现上的复现面——同一模式已在旧实现的 `run_git` 上造成 fail-open，且在本 change 的验证 fixture 中再次出现（两侧读取均失败、比较判等值、结论假绿）。

#### Scenario: 读取失败保守判失鲜

- **WHEN** 取锚版本或 HEAD 版本的文件内容时，git 以非零退出返回（对象不存在、仓损坏、权限不足等）
- **THEN** gate MUST 保守判失鲜或 `UNKNOWN`，MUST NOT 因两侧均为空结果而判等值
- **AND** MUST 有用例，且 MUST 附变异证明——删除该 returncode 判定 ⇒ 用例变红

### Requirement: gate 的 git 调用失败 MUST 落在退出码契约集内，且不受外部态影响

`ship_gate.py` 对外承诺的退出码集为 `{0, 3, 4, 5, 6}`。调用 git 时的任何环境级失败 MUST 被映射进该集合，MUST NOT 以未捕获异常逸出使退出码变成解释器默认值。

git 子进程 MUST 中和一切能改变判定输入的外部可控态：配置面经 `-c` 显式覆盖，环境面清理 `GIT_*` 环境变量。MUST NOT 以「当前实现碰巧没用到那些开关」作为免于中和的理由。

#### Scenario: git 不可用或不可执行

- **WHEN** `git` 不在 `PATH` 上、不可执行、或为无效可执行格式，`subprocess.run` 抛出 `OSError` 家族异常（含 `FileNotFoundError`、`PermissionError`）
- **THEN** gate MUST 捕获并映射为 `UNKNOWN`（exit 6），输出可读诊断；MUST NOT 让异常冒泡产生 traceback 与 exit 1
- **AND** 该捕获 MUST 覆盖**全部** git 调用 helper，且 MUST 对每个 helper **各有**验证——`main()` 首次 git 调用失败即退出，单一端到端用例只能覆盖其中一个

#### Scenario: git 调用挂起

- **WHEN** 某次 git 调用长时间不返回
- **THEN** 该调用 MUST 有超时上界，超时 MUST 映射为 `UNKNOWN`（exit 6）
- **AND** 超时值 MUST 对本仓正常规模的本地元数据查询留足余量

#### Scenario: 环境变量不得改变判定输入

- **WHEN** 调用方环境中存在影响 git 路径匹配或 diff 行为的变量（如 `GIT_ICASE_PATHSPECS`）
- **THEN** gate 的 git 子进程 MUST 不继承该类变量，判定结果 MUST 与该变量是否设置无关
- **AND** MUST 有用例：在设置该类变量的环境下，判定结论与未设置时一致
