## ADDED Requirements

### Requirement: 失鲜判定的机械层只承诺召回，精确率由语义层分诊

失鲜判定的机械层 MUST 保证「被审内容发生任何实质改动都不漏判」，MUST NOT 为提高精确率而引入从 git 管道推断路径变更的机制。误报由语义层（主 session 读 diff 判断）分诊。

机械层 MUST NOT 使用下列任一方式判定「被审内容是否改变」：`git log --name-only`、`git diff-tree -m`、`git diff-tree --cc`、负向 pathspec。这些方式已累计产出十个实测复现的缺陷（详见 `openspec/adr/0026`），且互为解药兼病灶、可被外部 config/env 翻转。

机械层 MUST 改为**直接比较内容**：design 域按固定监视清单逐文件比较字节，code 域比较整树 sha。

#### Scenario: 实现期不得让设计门失鲜

- **WHEN** 设计门拍板后进入实现期，提交改动源码文件，并把 `tasks.md` 的复选框由 `- [ ]` 勾成 `- [x]`
- **THEN** gate MUST 判 design 域 fresh——源码不在 design 域监视集内；`tasks.md` 的复选框差异 MUST 经归一化后判等值
- **AND** 该场景 MUST 有用例。**监视集是承重的**：任何令实现期提交使设计门失鲜的实现（如裸 `reviewed_sha == HEAD` 比较）MUST 判为不合格

#### Scenario: 合并把已批准产物换回锚前旧内容

- **WHEN** 锚提交之后的一次合并，使某监视文件在 HEAD 上的内容变回锚**之前**某祖先版本（该内容不由锚后任何提交引入，故任何逐提交枚举都看不到它）
- **THEN** gate MUST 判失鲜——内容比较不依赖提交拓扑，锚与 HEAD 的字节不等即成立
- **AND** MUST 有用例，且 MUST 经 `is_stale` 公共入口求值

#### Scenario: `openspec/` 内的记账不得让 code 域失鲜

- **WHEN** 代码审通过后，正常收尾流程写入 `verify-report.md`、或 archive 把 change 目录移入 `openspec/changes/archive/`——即改动**全部落在 `openspec/` 之内**
- **THEN** gate MUST 判 code 域 fresh
- **AND** 该域的比较粒度 MUST 能排除 `openspec/`：整棵树的 sha 比较 **MUST NOT** 被采用——它在上述正常流程的第一步即假阳（已实测）
- **AND** MUST 有用例钉死此方向

#### Scenario: 语义分诊须留痕且默认 fail-closed

- **WHEN** 机械层判失鲜，而主 session 判定该差异无实质影响（如 `[impl-review-fix]` 修订）
- **THEN** 主 session MAY 把锚重锚到当前 HEAD，但 MUST 在报告中同时写下重锚理由
- **AND** 未执行重锚时 MUST 维持失鲜结论——机械层 MUST NOT 因「可能会被判为无害」而放行
- **AND** 本条 MUST NOT 被表述为机械门：分诊由被监管方执行，无可信脚本捕获路径，属显式登记的残余面

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
