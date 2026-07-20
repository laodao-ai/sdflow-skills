# 失鲜判定的枚举原语按各消费方**要回答的问题**选，MUST NOT 为「统一」而统一；`git diff-tree -m` 会把锚前历史当作锚后改动重报

`ship_gate.py` 的失鲜判定有两个 scope、**三个消费方**：`design`（守 `spec-review-report` 的 `design_approved`）、`code`×2（守 `code-review-report` 的 `code_review`、守 `verify-report` 的 `verify`）。`fix-design-gate-freshness-proxy` 把 design 域的帧枚举协议换成 `git diff-tree -m -r --raw --no-renames -z --root`，关掉了三个 fail-open（merge 帧恒空、rename 吞源路径、枚举失败折成空串）。后续 change `harden-gate-git-layer` 初稿的目标是「把该协议抽成两域共用的唯一一处实现，推广到 code 域」——**「共用」被当作目标本身写进了 Goals**。

grill 期实测推翻了这个起手式，两个独立发现：

**(a) `-m` 会过报，造成假失鲜。** `git diff-tree -m` 输出 merge **相对每个 parent** 的 diff，而 parent2 通常**早于锚提交**——于是整条 feature 分支在锚**之前**的工作，被当成「这一帧触及的路径」重新报一遍。实测：侧支只碰了 `openspec/changes/c/notes.md`、锚后四件套一字未动，design 域仍判 `stale` → `REFUSE_START`。**这是已上线缺陷，例行「把 main 合进 feature 分支」即触发**。正解是 `--cc`（只报相对**所有** parent 都不同的文件，即 merge 自身 resolve 出来的内容）：例行 merge 输出 `[]`，evil merge 输出 `src.py`，且 `::` 三列形态在 `-z` 下被既有 `:`-前缀成对解析器原样吃下。**`-m` 与 `--cc` 的区别不是"详略"，是"问了不同的问题"**——`-m` 问「这一帧相对各 parent 有何不同」，`--cc` 问「这一帧自己引入了什么」；失鲜判定要的是后者。

**(b) 两域的问题结构不同，∴ 不该共用原语。** design 域问「锚后**每一个**碰了四件套的提交，是否都拿到了豁免」——BR-7 是 per-commit subject 判断，**必须逐帧**。code 域问「**现在的树**，和被审过的那棵，在 `openspec/` 之外有没有差别」——这是**状态比较**，零豁免、零 subject 判断，与提交拓扑无关，`git diff --raw --no-renames -z <锚> HEAD` 一次调用即答完。把帧枚举推给 code 域，等于让它背一套它不需要的循环，还连带继承 (a) 的假阳。

**决策**：失鲜判定（及同类门禁判据）选择底层 git 原语时，MUST 先分别写出**每个消费方要回答的问题**，按问题选原语；「两处共用一份实现」**MUST NOT 作为目标写进 Goals**——它是问题相同时的*结果*，不是可独立追求的价值。同时，MUST 用 `grep` 列全 `is_stale` 之类判定函数的**全部调用点**作为论证清单（承 adr/0011 的机械核验条款），MUST NOT 凭记忆枚举消费方数量。

## Considered Options

- **按消费方问题选原语：design 域逐帧 + `--cc`，code 域累积 diff（选中）**：两域各自答自己的问题。附带收益是结构性的、非补丁式的——code 域侧 merge 拓扑整个不参与判定；rename 在 `--no-renames` 下天然分解成 A+D；枚举失败只剩一个 rc 要判；N 次 subprocess 降到 1 次，`timeout` 从「每帧 30 秒、总量无上界」变成真上界。代价：① code 域诊断拿不到 commit sha，只有路径（撞门后要做的是重跑代码审，路径比 sha 更可操作；真需要 sha 可单独补一次 `git log --format=%H -- <path>`）；② 「共用唯一实现」的 Goal 作废，两域各有一处枚举代码，防漂移改由 spec 的**逐域 Scenario** 承担（两域正确行为本就不同，共用反而会诱导「顺手统一」把方向改错）。
- **两域都换 `--cc` 并保留共用帧枚举**：未选——修得掉 (a) 的假阳，但 code 域白背一套帧循环、N 次 subprocess，`timeout` 总量仍无上界；且它把「共用」这个被证伪的前提继续供着，下一个人仍会以为两域该同构。
- **维持初稿「共用帧枚举 + `-m` 推广到 code 域」**：未选——会把已上线的 (a) 假阳原样复制进第三个消费方，且 spec 的 Requirement 2 与协议自相矛盾（见下）。

## Consequences

- **`harden-gate-git-layer` 落地本 ADR**：Goals 删「两域共用唯一实现」；ADR-1 由「抽 `iter_frames` 共用源」改为「按域选原语」；新增 design 域 `-m`→`--cc` 的修复（承基准 4，同一原语面 fold 进本 change，不另开循环）。
- **spec 的控制字符需求被本 ADR 连带证伪，MUST 改写方向**：初稿 Requirement 2 锁「含换行/Tab 的路径经 C-quote 成 `"openspec/a\nb"`、不以 `openspec/` 起头 ⇒ code 域判失鲜，此 fail-closed 方向 MUST 保持」。实测：**`-z` 输出原始字节，引号根本不存在**，路径正确解析为 `openspec/a\nb` ⇒ 判 fresh。该 fail-closed 是**字符串被 C-quote 弄花的意外产物，不是有原则的保守**——文件真在 `openspec/` 下，豁免它才是对的。∴ Requirement 2 MUST 改为锁**新**方向，并写明旧方向的成因，防后人把它当"丢失的防护"补回来。**注意此反转是 `-z` 的属性，与选哪个原语无关**（帧枚举走 `-z` 一样反转）。
- **两条语义变化 MUST 显式进 spec 并上锁测试，不得作为"顺手的好事"静默发生**：① **改了又改回去 ⇒ 判 fresh**（树等值 = 没有任何新东西会被 ship，正确，且是范围语义做不到的）；② **锚提交被 amend/rebase 成孤儿 ⇒ 判 fresh 而非 stale**（改报告错别字不该要求重跑代码审）。二者都只在树语义下成立，是行为变更而非等价重构。
- **印证 adr/0011 的机械核验条款**：`harden-gate-git-layer` 的假设 A5 写「失鲜判定只有 design/code 两个 scope，**无第三消费方** ✅ 源码只有 `scope == "design"` 与其 else 分支」——scope 数对，**消费方数错**（三个）。grep 调用点一次即现形。更值得记的是后果：现存唯一一个 code 域测试用的正是第三个消费方（`verify-report`），**`code-review-report` 那条路径今天零测试覆盖**——「假设写 ✅」把这个覆盖缺口一并盖住了。
- **与 adr/0008（gate 纵深防御，非信任纪律）同向**：本 ADR 是其在**原语选择**层的专项——纵深防御要求每层各自成立，而「为统一而共用」会让两层被迫同构，一层的错误方向直接传染另一层。
- **CONTEXT.md**：新增术语「**问题先于原语（Question-before-Primitive）**」。
