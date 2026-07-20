## ADDED Requirements

### Requirement: 判据 MUST 只在其保护的风险真实存在的阶段求值

失鲜判据 MUST 只在其保护的风险真实存在的阶段求值，MUST NOT 全阶段求值后再为「合法 churn 阶段」补造豁免或逃生口。

design 域失鲜保护的风险是「照着一份已经变了的设计继续建」——该风险只在实现期存在。∴ design 域失鲜 MUST 只在阶段三起手至实现完成期间求值；进入代码审后 MUST NOT 再求值。

阶段判定 MUST 在失鲜判定**之前**完成。二者无循环依赖：阶段只取决于盘面上存在哪些产物，不取决于失鲜结论。

#### Scenario: 代码审期与 done 期不求值 design 域失鲜

- **WHEN** 流程已进入代码审期或 done 期，此时对四件套的修订发生（如 `[impl-review-fix]` 修订，或 verify 的 design adherence 检查判定「revise design.md to match reality」）
- **THEN** gate MUST NOT 因该修订判 design 域失鲜——这些修订是工作流明文允许的动作，且在本仓历史上是常态而非偶发
- **AND** MUST 有用例锁死此方向

#### Scenario: 实现窗口的三个分支各自受保护

- **WHEN** 盘面处于 `RUN_SOP`、`RUN_PLAN`、`CONTINUE_IMPL` 三者中的**任意一个**，且 design 域监视集内容与锚版本不等值
- **THEN** gate MUST 判失鲜
- **AND** 三个分支 MUST **各有**用例——它们是三处独立的提前返回点，只在其中最后一个之后加检查会使前两个完全逃出判定（方向为 fail-open）
- **AND** MUST NOT 提供任何「分诊后重锚」「按 commit subject 豁免」之类的旁路

#### Scenario: 实现期的四件套实质修订被拦下并逼回重审

- **WHEN** 在实现窗口内，四件套被实质修订（差异不止于复选框状态）
- **THEN** gate MUST 判失鲜，撞门者 MUST 走「重审 → 重新拍板」的正规流程
- **AND** 这是**有意的行为收紧**——该模式在本仓历史上出现过，本判据将其逼回正规流程，MUST NOT 被后续维护者当作缺陷而放宽

### Requirement: 失鲜判定 MUST 直接比较内容，MUST NOT 从 git 管道推断路径变更

机械层 MUST NOT 使用下列任一方式判定「被审内容是否改变」：`git log --name-only`、`git diff-tree -m`、`git diff-tree --cc`、负向 pathspec、整棵树的 sha。这些方式已累计产出实测复现的缺陷（详见 `openspec/adr/0026`），且互为解药兼病灶、可被外部 config/env 翻转。

机械层 MUST 改为直接比较内容：

- **design 域** MUST 对锚与 HEAD 各枚举一次监视集，比较 `path → (mode, type, oid)` **映射**；映射不等即失鲜。
  MUST NOT 只枚举单侧——只枚举 HEAD 侧会漏掉「锚有而 HEAD 已删」的路径，只枚举锚侧会漏掉「HEAD 新增」的路径，两者方向均为 fail-open。
- **code 域** MUST 比较 `git ls-tree` 的顶层条目（排除 `openspec` 条目后）。

复选框豁免 MUST 常开、按**内容**切，MUST NOT 按阶段切——`tasks.md` 复选框的写入方是不受阶段约束的自由行为，按阶段切会立即产生假失鲜。

#### Scenario: 实现期不得让设计门失鲜

- **WHEN** 设计门拍板后进入实现期，提交改动源码文件，并把 `superpowers-plan.md` 中该 ticket 的验收复选框由 `- [ ]` 勾成 `- [x]`
- **THEN** gate MUST 判 design 域 fresh——源码与 `superpowers-plan.md` 均不在 design 域监视集内
- **AND** **监视集是承重的**：任何令实现期提交使设计门失鲜的实现（如裸 `reviewed_sha == HEAD` 比较）MUST 判为不合格

#### Scenario: `specs/` 子树的新增、删除与 rename 均判失鲜

- **WHEN** 锚之后在 `specs/` 下新增文件、删除文件、或 rename 文件（后者内容可完全不变）
- **THEN** gate MUST 判失鲜——三者均使 `path → (mode, type, oid)` 映射不等
- **AND** MUST 各有用例，且 MUST 经 `is_stale` 公共入口求值
- **AND** 某路径只在一侧存在 MUST 判失鲜，MUST NOT 混作「读取失败」处理——二者是不同的判定

#### Scenario: `tasks.md` 纯复选框翻转不失鲜（任何阶段）

- **WHEN** `tasks.md` 的内容差异在复选框标记归一化后逐行等值
- **THEN** gate MUST 判 fresh，且该豁免 MUST 与当前处于哪个阶段无关
- **AND** 差异超出复选框状态时 MUST 照常判失鲜

#### Scenario: 合并把已批准产物换回锚前旧内容

- **WHEN** 锚提交之后的一次合并，使某监视文件在 HEAD 上的内容变回锚**之前**某祖先版本（该内容不由锚后任何提交引入，故任何逐提交枚举都看不到它）
- **THEN** gate MUST 判失鲜——内容比较不依赖提交拓扑，锚与 HEAD 的映射不等即成立
- **AND** MUST 有用例，且 MUST 经 `is_stale` 公共入口求值

#### Scenario: 代码审后的源码改动 MUST 被 code 域捕获

- **WHEN** 代码审出具结论之后，源码经由 merge 提交中 resolve 引入改动，或经 `git mv` 从顶层迁入 `openspec/`
- **THEN** gate MUST 判 code 域失鲜——两者均使非 `openspec` 顶层条目集合改变
- **AND** 二者 MUST **各有**用例并附变异证明——它们是 code 域改用顶层条目比较后**唯一的正面收益证明**

#### Scenario: `openspec/` 内的记账不得让 code 域失鲜

- **WHEN** 代码审通过后，正常收尾流程写入 `verify-report.md`、或 archive 把 change 目录移入 `openspec/changes/archive/`——即改动全部落在 `openspec/` 之内
- **THEN** gate MUST 判 code 域 fresh
- **AND** 该域的比较粒度 MUST 能排除 `openspec/`：整棵树的 sha 比较 **MUST NOT** 被采用——它在上述正常流程的第一步即假阳（已实测）

### Requirement: 评审锚 MUST 由 producer 记录，MUST NOT 从提交历史反推

评审结论的锚 MUST 是评审时由 producer 写入报告 frontmatter 的显式提交标识（`reviewed_sha`），MUST NOT 由「最后一次触碰报告文件路径的提交」之类的反推方式得出。

反推式锚可被任何后续触碰该文件的提交无声前移，从而把锚前的未审改动埋在判定范围之外——该提交无需修改任何结论字段，在 `git log -p` 中与评审结论毫无关联，其隐蔽性不被「篡改结论字段留痕可审计」这一既有残余面覆盖。

锚的语义是「**被批准 / 被放行的那个盘面**」，而非「写报告的时刻」。

#### Scenario: 锚 MUST 指向被放行的提交，而非写报告的时刻

- **WHEN** 某评审步在出具结论的同一轮内还修改了它所审查的对象（如代码审的自动修复）
- **THEN** producer MUST 先提交该修改、令锚指向该提交，再单独提交报告；MUST NOT 让锚指向不含该修改的更早提交
- **AND** 否则报告落盘后判定立即失鲜（锚不含刚提交的修改），使该评审步每轮自锁
- **AND** MUST 有用例覆盖「该评审步的修复非空」这一情形

#### Scenario: 结论落盘前对被审对象的追加修订 MUST 先单独提交

- **WHEN** 评审结论已产出、但在写入结论字段与锚之前，被审对象又被实质修订（如人读评审报告后要求修改设计文档）
- **THEN** 该修订 MUST 先单独提交、取得其提交标识后，才写入结论字段与 `reviewed_sha`
- **AND** MUST NOT 让该修订与结论字段的写入落进同一次提交——那会使锚指向不含该修订的更早提交，结论落盘后首次判定即失鲜，形成自锁
- **AND** MUST 有用例覆盖此路径，且其变异证明为「令锚指向修订前的提交 ⇒ 判定失鲜」

#### Scenario: 无关的报告排版提交不得移动锚

- **WHEN** 评审通过后，先有提交引入未经审查的源码改动，再有一个与之无关的提交仅修改报告文件的排版（如补一个换行），且不改动任何结论字段
- **THEN** gate MUST 仍判失鲜——锚为 producer 记录值，不因报告文件被触碰而前移

#### Scenario: 锚缺失或非法时 fail-closed

- **WHEN** 报告 frontmatter 缺 `reviewed_sha`、其取值不是完整 40 位 OID、或该对象在仓中不存在 / 不是 commit 对象
- **THEN** gate MUST 判 `UNKNOWN`（exit 6），MUST NOT 回退到任何反推式锚、MUST NOT 判 fresh
- **AND** 格式校验（语法级）与对象存在性校验（语义级，需 git 调用）MUST 分层实现——前者所在的解析函数为纯文本函数，供 live 读与归档文本读共用
- **AND** reader 契约 MUST 与 producer 同批落地：只落 producer 会使新锚永不被读取，只落 reader 会使存量报告全部 fail-closed
- **AND** 存量无 `reviewed_sha` 的报告 MUST 要求重审一次，MUST NOT 为兼容而静默回退

#### Scenario: 结论字段与锚 MUST 原子写入

- **WHEN** producer 写入评审结论字段（如 `design_approved`）与 `reviewed_sha`
- **THEN** 二者 MUST 在同一次文件写入中落盘
- **AND** 否则中断可产生「结论字段已在、锚缺失」的中间态：该态下结论字段判定通过、锚读取却 fail-closed，撞门者得不到「缺的是哪个字段」的指引

### Requirement: 内容比较 MUST 区分读失败与内容为空

比较两个版本的文件内容时，MUST 显式判定读取操作的返回码，MUST NOT 让两次失败的读取因各自返回空结果而比较相等。

此为「非零退出被折叠成空结果」这一失效模式在新实现上的复现面——同一模式已在旧实现的 `run_git` 上造成 fail-open，且在本 change 的验证 fixture 中再次出现（两侧读取均失败、比较判等值、结论假绿）。

#### Scenario: 读取失败保守判失鲜

- **WHEN** 取锚版本或 HEAD 版本的内容时，git 以非零退出返回（对象不存在、仓损坏、权限不足等）
- **THEN** gate MUST 保守判失鲜或 `UNKNOWN`，MUST NOT 因两侧均为空结果而判等值
- **AND** MUST 有用例，且 MUST 附变异证明——删除该 returncode 判定 ⇒ 用例变红

#### Scenario: 存在性判定 MUST 由能区分「缺失」与「失败」的原语承担

- **WHEN** 需要判断某监视路径在锚或 HEAD 一侧是否存在
- **THEN** MUST 使用「路径不存在时正常退出并返回空结果」的枚举原语，使「缺失」与「调用失败」在返回码上判然二分
- **AND** MUST NOT 让「路径不存在与仓损坏返回同一退出码」的取内容原语承担存在性判定——那会使被删除或迁走的监视文件被误诊为读取失败，向撞门者给出错误的补救指引
- **AND** 取内容的调用 MUST 只在存在性已确认之后发生，其非零退出方可一律视为真实读取失败
- **AND** MUST 有用例：监视清单内的文件在一侧被删除或迁出监视集 ⇒ 判失鲜，且诊断不呈现为读取失败

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

#### Scenario: 失败原因 MUST 可区分且可行动

- **WHEN** gate 因任一环境级失败判 `UNKNOWN`
- **THEN** 诊断 MUST 区分「git 不可用」「调用超时」「锚缺失」「锚非法或对象不存在」「读取失败」五类，各给出对应的补救指引
- **AND** MUST NOT 以单一通用文案覆盖全部五类——五者的补救动作互不相同，而 `UNKNOWN` 在上游链序中的处置是「停并转述该诊断」

#### Scenario: 环境变量不得改变判定输入

- **WHEN** 调用方环境中存在影响 git 路径匹配或 diff 行为的变量（如 `GIT_ICASE_PATHSPECS`）
- **THEN** gate 的 git 子进程 MUST 不继承该类变量，判定结果 MUST 与该变量是否设置无关
- **AND** 环境清理 MUST 以排除法实现（剔除 `GIT_` 前缀键），MUST NOT 以白名单方式只保留少数变量——后者会在部分平台上漏掉进程创建所必需的系统变量
- **AND** MUST 有用例：在设置该类变量的环境下判定结论与未设置时一致，且非 `GIT_*` 的环境变量原样透传
