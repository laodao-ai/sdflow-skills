## ADDED Requirements

### Requirement: 失鲜判定的枚举原语按各消费方要回答的问题选定

gate 判定「评审结论是否失鲜」时，所用的底层 git 原语 MUST 由**该消费方要回答的问题**决定；「两处共用一份实现」MUST NOT 作为目标被追求——它是问题相同时的结果，不是可独立追求的价值（承 `openspec/adr/0026`）。

两域问的不是同一个问题：**design 域**问「锚后每一个碰了四件套的提交，是否都拿到了豁免」——per-commit 的 subject 与内容判断，MUST 逐帧求值；**code 域**问「当前的树，与被审过的那棵，在 `openspec/` 之外有无差别」——状态比较，与提交拓扑无关。

枚举 MUST NOT 使用 `git log --name-only`。该协议有三个 fail-open 洞：**(a)** 不带 `-m`/`--cc` 时对 merge 提交不输出任何路径 ⇒ 整帧被跳过；**(b)** rename detection 默认开启，只输出目标路径 ⇒ 源路径逃出监视集；**(c)** 非零退出被折叠成空串 ⇒ 零帧 ⇒ 等价于「没有可疑提交」。

**code 域** MUST 使用 `git diff --raw --no-renames -z <锚> HEAD` 或等价的**树比较**保证。**design 域** MUST 逐帧使用 `git diff-tree --cc -r --raw --no-renames -z --root <帧>` 或等价保证：只报相对**所有** parent 都不同的路径、禁用 rename 归并、NUL 分隔承载任意路径字节、根提交可枚举。

〔本条**追认** `fix-design-gate-freshness-proxy` 期已落地但未进 spec 的 design 域行为，并按 adr/0026 修正其原语。此前该行为仅由测试守护，无需求层约束。〕

#### Scenario: merge 提交自身引入的改动不得逃逸（两域）

- **WHEN** 锚提交（design 域 = 设计门拍板提交；code 域 = 代码审放行提交 / verify 通过提交）之后存在一个 merge 提交，其两个 parent 各自只触及与本域监视集无关的路径，而 **merge 提交自身**（相对两个 parent 均为修改）触及本域监视集内的路径
- **THEN** gate MUST 判该结论失鲜（design 域 → `REFUSE_START`；code 域 → 相应重跑语义），MUST NOT 因 merge 帧路径集为空而跳过整帧判 fresh
- **AND** 该场景 MUST 在**两个域各有一个独立用例**——design 域用例通过 MUST NOT 被当作 code 域的覆盖证明
- **AND** 用例 MUST 经 `is_stale` 公共入口求值，MUST NOT 只直接调用内部 helper（只调 helper 的用例在真实洞存在时仍为绿，已有实证）

#### Scenario: 例行 merge MUST NOT 造成假失鲜（两域）

- **WHEN** 锚提交之后把另一分支合入，且该分支**只触及本域监视集之外**的路径（design 域：非四件套路径；code 域：`openspec/` 下的路径），merge 自身未 resolve 出任何监视集内的改动
- **THEN** gate MUST 判 fresh。MUST NOT 因 merge 相对某个**早于锚提交**的 parent 重报了锚前的历史改动，而判该结论失鲜
- **AND** 本场景是 `git diff-tree -m` 的直接后果（`-m` 逐 parent 输出，parent2 通常早于锚）⇒ 枚举 MUST NOT 使用 `-m`；design 域 MUST 用 `--cc`，code 域 MUST 用树比较
- **AND** MUST 在两个域各有一个经 `is_stale` 入口求值的用例

#### Scenario: rename 不得令路径逃出监视集（两域）

- **WHEN** 锚提交之后某提交以 `git mv` 把一个受本域监视的路径迁移到监视集之外（design 域：四件套内文件迁出；code 域：`openspec/` 之外的源码文件迁入 `openspec/`）
- **THEN** gate MUST 判该结论失鲜——rename 的**源路径** MUST 进入枚举结果
- **AND** MUST 在两个域各有一个经 `is_stale` 入口求值的用例

#### Scenario: 枚举失败保守判失鲜，MUST NOT 当作空集（两域）

- **WHEN** 枚举或帧内路径获取因任何原因失败（git 非零退出、输出形态不可解析、进程异常、锚 sha 不存在）
- **THEN** gate MUST 保守判失鲜，MUST NOT 把失败结果与「合法的空结果」共用同一表示（空串 / 空列表）而判 fresh
- **AND** 失败 MUST 携带可区分的分类原因，MUST NOT 与正常的「未触及监视集」输出同一 reason

#### Scenario: 新增守卫须附变异证明

- **WHEN** 本 change 为上述任一 fail-open 或假阳增加守卫
- **THEN** MUST 存在对应用例，且 MUST 已实证「删除该守卫 ⇒ 该用例变红」；MUST NOT 以「用例存在且当前为绿」作为守卫有效的证明——绿可能来自用例根本没走到被守护的判定路径（`fix-design-gate-freshness-proxy` 的 rename 用例即此形态：洞真实存在而用例为绿）

### Requirement: code 域采用树比较语义，其两条行为后果 MUST 显式锁定

code 域改用树比较后，**MUST** 显式承认并用测试锁定两条随之而来的行为变更，MUST NOT 作为「顺手的好事」静默发生。

二者都只在树语义下成立，是行为变更而非等价重构；不锁定则后续重构可能在无人察觉时把它们改回范围语义。

#### Scenario: 改动后又改回 ⇒ 判 fresh

- **WHEN** 锚提交之后某文件被修改，随后又被改回与锚提交完全相同的内容（或新增后又删除）
- **THEN** gate MUST 判 fresh——当前树与被审过的树等值 ⇒ 没有任何未经审查的内容会被 ship
- **AND** MUST 有用例锁定此语义

#### Scenario: 锚提交被 amend/rebase 成孤儿 ⇒ 按内容判

- **WHEN** 锚提交在被记录后经 `git commit --amend` 或 rebase 重写，旧 sha 不再是 HEAD 的祖先，但两棵树在监视范围内等值
- **THEN** gate MUST 判 fresh（例如仅修正报告中的错别字，不应要求重跑代码审）；MUST NOT 因旧 sha 脱离 HEAD 祖先链而把整条分支算作「锚后新增」
- **AND** 若锚 sha 在仓中**根本不存在**（而非仅脱离祖先链），git 非零退出 ⇒ 按上一条 Requirement 的「枚举失败」保守判失鲜

### Requirement: code 域谓词方向独立判定，MUST NOT 照搬 design 域补丁

推广枚举协议时，每一条 design 域的既有防护 MUST **逐条重新判定其在 code 域的方向**，MUST NOT 整体照搬。

理由是两域的监视谓词方向相反：design 域为**白名单**（路径命中固定监视集才纳入判定），code 域为**黑名单补集**（路径不在 `openspec/` 下即纳入判定）。同一个底层 git 行为在两域可落在相反的安全方向上。

#### Scenario: 控制字符路径在 `-z` 下正确解析为豁免，MUST 保持新方向

- **WHEN** `openspec/` 下某路径含换行 / Tab 等控制字符
- **THEN** 在 `-z` 协议下该路径 MUST 被解析为原始字节形态（如 `openspec/changes/c/we\nird.md`），因其确实以 `openspec/` 起头而在 code 域判为**豁免**。此为正确行为
- **AND** 老协议下该路径经 C-quote 变成 `"openspec/a\nb"`（含前导引号）⇒ 前缀不匹配 ⇒ 判失鲜。该 fail-closed 是**字符串被 C-quote 弄花的意外产物，不是有原则的保守** ⇒ MUST NOT 被当作「丢失的防护」补回来
- **AND** MUST 有用例锁死新方向，并在用例旁注明成因，防后续以「恢复 fail-closed」为由改回

### Requirement: gate 的 git 调用失败 MUST 落在退出码契约集内

`ship_gate.py` 对外承诺的退出码集为 `{0, 3, 4, 5, 6}`。调用 git 时的任何环境级失败 MUST 被映射进该集合，MUST NOT 以未捕获异常逸出而使退出码变成解释器默认值——调用方（`/sdflow-ship` 链序）按契约集解读退出码，集外取值会被误判为其他语义。

#### Scenario: git 二进制不可用

- **WHEN** `git` 不在 `PATH` 上（或不可执行），`subprocess.run` 抛 `FileNotFoundError`
- **THEN** gate MUST 捕获并映射为 `UNKNOWN`（exit 6），输出可读的诊断说明 git 不可用；MUST NOT 让异常冒泡产生 traceback 与 exit 1
- **AND** 该捕获 MUST 覆盖**全部** git 调用 helper，MUST NOT 只在部分调用点加防护

#### Scenario: git 调用挂起

- **WHEN** 某次 git 调用长时间不返回
- **THEN** 该调用 MUST 有超时上界；超时 MUST 映射为 `UNKNOWN`（exit 6），MUST NOT 令 gate 判定无限阻塞
- **AND** 超时值 MUST 对本仓正常规模的 git 元数据查询留足余量，MUST NOT 因超时值过紧而在大仓上产生假 `UNKNOWN`

### Requirement: code 域失鲜须携带触发点

code 域判失鲜时的输出 MUST 指明触发的路径，使撞门者知道撞在哪，MUST NOT 只输出无信息的「结论陈旧」。

#### Scenario: code 域失鲜输出诊断

- **WHEN** gate 因 code 域失鲜而拒绝推进
- **THEN** reason MUST 至少携带一条触发路径与分类原因
- **AND** 机读输出与人读文案 MUST 同源（同一份触发点数据的两个视图）
- **AND** 树比较语义下**无 commit sha 可报**属已知且已接受的代价（撞门后的正确动作是重跑代码审，路径比 sha 更可操作）；MUST NOT 为凑齐 sha 而退回逐帧枚举
- **AND** 该诊断 MUST 为纯输出，MUST NOT 改变退出码或失鲜判据本身
