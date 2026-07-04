<!-- sdflow:step1-broad-review v1 mode="native" -->
# gstack-review.md — ship-gate-hardening 广审（autoplan 原生 · Step1）

> **native 声明**：主 session 经 Skill 机制原生执行 autoplan 方法（CEO/Eng 独立镜 + codex 双声），非子代理转述。
> 侧信道佐证：CEO 镜 tool_uses=5/duration≈256s、Eng 镜 tool_uses=20/duration≈406s（含活体 git/pathlib 实验）、codex design-voice exit=0/OV_TRUNCATED=false（真实 codex-cli 0.142.5 调用）。
> UI scope=无 → Design 相跳过；DX 折进 Eng（reason 串质量）。对抗镜空间已由 Eng 镜 + codex 饱和覆盖。

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

## 广审 findings 池（供 Step3 合并去重 + 对抗裁决）

### HIGH（design-changing，须设计门拍板）

**BR-1〔B2 soundness：凭生产者信任而非改动类型〕** — codex-design#2(partial) + CEO-F1 + CEO-F6 三声独立命中
豁免正当性建立在约定「code-review 对四件套只做装饰改动」，但 code-review 本职就会改设计（产 `[impl-review-fix]` 补丁改 design.md）。语义级设计修正仍以 `checkpoint(impl-review)` 落盘 → 被豁免 → 未经二审随档 merge = gate 头号失效模式（静默假✅）。把"安全的假阳性"（误 REFUSE）换成"危险的假阴性"（改了设计静默过门）。
证据：design.md:118（自认静默 merge 窗口）、ship_gate.py:90-93（只看路径不看 hunk）、spec.md:39。
建议：按**改动类型**分岔——语义改 design.md → 重申锚(D2-b)/回落重跑 spec-review；纯勾选/措辞 → impl-review 豁免。用"改动类型"而非"commit 生产者"分叉。CEO-F6 补：D2-b 弃选"增益零"被夸大（重申锚给可 grep 审计记录 + 前移基线，对静默假✅ 失效面不是零增益）。

**BR-2〔B3 SHIPPED fail-green：短路不查 verify/hand-off 锚〕** — codex-design#2 + codex-design#3 + CEO-F2 三声
D3 短路判 SHIPPED 只凭"archive 目录在 base 树"，不复用 archived 内容的锚行/hand-off 校验；把最危险的 exit-0 verdict 从链尾提到 pre-flight，扩大假✅ 爆炸半径。精确同名旧档→假 SHIPPED 被"接受"而非"阻断"。
证据：design.md:42-49、spec.md:57-63、ship_gate.py:247-299。
建议：(a) 短路命中 archive 时把 cdir 指向 archive 目录复用锚检查，最少要求 archived spec-review/code-review=pass/verify=PASS/hand-off 全存在无冲突；(b) 同名歧义时 **fail-safe 到 UNKNOWN(exit6) 而非 fail-green 到 SHIPPED**（最危险 verdict 在歧义时 fail-safe）。

**BR-3〔完成判据 count vs 集合归属〕** — codex-design#1
`decide()` 用 `len(done) < n` 按计数判齐，不校验 done 任务号是否 ⊆ plan 任务号。`done={task1,task9}` 且 N=2 → 假齐进 RUN_CODE_REVIEW，漏 task2。D1 纳入 sha 自身 task 会放大此既有假✅。
证据：ship_gate.py:141-167、227-242（`len(done) < n`，未与 plan_ids 交集）。既有测试只覆盖单号不齐（test_merged_branch_inner_commits done=["9"]），未覆盖 task1+task9 假齐。
建议：解析 plan 任务号集合，判 `plan_ids ⊆ done_ids` 或只用 `done_ids ∩ plan_ids` 计数；补 task1+task9 缺 task2 的红测。

### MEDIUM

**BR-4〔B3 发现域 vs 判据域不一致〕** — Eng-F2（活体实验）
发现用文件系统 glob（依赖当前工作树含归档目录），判据用 base 树。"跨分支查也对"过强：从早于归档的分支查已 ship 的 change，工作树无该目录 → glob 落空 → 误 REFUSE「不存在」。附带：未 git 跟踪的归档垃圾目录 → glob 命中+base 空 → 误 RUN_VERIFY。
建议：要么显式声明「D3 发现以当前 checkout 工作树为准」并把「工作树无归档目录时的跨分支查」纳入已知不覆盖；要么发现改用 `git ls-tree HEAD ∪ ls-tree base` 保持纯 git 域。

**BR-5〔B2 token 无契约测试〕** — CEO-F3
豁免硬编码 `checkpoint(impl-review)` 与 checkpoint-commit.sh 的 step-name 是两个独立字符串须永久一致；gate 对锚行有 test_anchor_contract.py 双向钉死，此 token 无同类保护。step 改名 → B2 静默回归（假 REFUSE 重现）无报警。
建议：给 impl-review token 加与 checkpoint-commit.sh step-name 双向钉死的契约测试。

**BR-6〔is_stale 双 scope 共享：code 域回归 + 解析测试缺口〕** — CEO-F4 + Eng-F3 + codex-design(F5 隐含)
is_stale 被 design/code 双 scope 共用，D2 重构分帧遍历风险：(a) code 域可能有与 B2 对称的假失鲜（impl-review-fix 改真实代码提交排在 cr 报告后 → RERUN_STALE）；(b) MUST NOT 给 is_stale 加 --no-merges/--first-parent（头注释:43 承诺 merge 内部逐一枚举）；(c) 空 subject/无文件帧未测；(d) 多提交交错（同窗口 impl-review 改 tasks.md + 普通 subject 改 design.md）未测——分帧 bug 杀伤方向是假豁免，必须专测。
建议：task 2.2 护栏补「MUST NOT 加 --no-merges/--first-parent」；task 2.3 补空 subject + 交错回归用例；design.md 论证 code 域为何无对称 B2。

**BR-7〔D2 闭合前缀仍收尾串垃圾〕** — codex-design#4
`startswith("checkpoint(impl-review)")` 正确拒 `-fix`/`X`，但仍收 `checkpoint(impl-review)evil`（右括号后垃圾）。真实产物只有裸 `checkpoint(impl-review)` 或 `checkpoint(impl-review): …`。
建议：精确式 `subject == "checkpoint(impl-review)" or subject.startswith("checkpoint(impl-review):")`，补 `checkpoint(impl-review)evil` 不豁免测试。

**BR-8〔D1 头注释契约漂移无任务〕** — Eng-F1
D1 改闭区间，spec+代码同步，但头注释窗口块 ship_gate.py:30-32 + CONTINUE_IMPL reason 串:241 仍写旧排他 `{sha}..HEAD --no-merges`，无任务负责。设计自称"契约不漂移"唯一漏排面。
建议：task 1.x 补「同步 :30-32 窗口块 + :241 reason 为闭区间表述」。

### LOW

**BR-9〔锚死 glob 多命中未定义〕** — Eng-F4（活体实验）
同名 change 被 ship 多次（2026-01-01-demo + 2026-07-04-demo）→ glob 多命中；tasks 3.2 单数 `<dir>` 未定义取哪个。
建议：明确「任一匹配目录在 base 树 → SHIPPED，否则 RUN_VERIFY」（匹配集 any 可达）。

**BR-10〔契约表 RUN_VERIFY 行未更新〕** — Eng-F5
D3 让 RUN_VERIFY 新增「归档未并 base」触发，但契约表 :23 仅写「verify 缺」，task 3.3 未排此行。
建议：task 3.3 给 RUN_VERIFY 行补「/ 归档未并 base 待 merge 收尾」变体。

**BR-11〔D3 next=sdflow-done 链假设〕** — Eng-F6
归档未并时 emit RUN_VERIFY next=sdflow-done，但 done 面对 active 已不在的 change 能否只做 merge 收尾（不重跑 verify/重 archive 报错）超出 gate 测试域。
建议：非本次 gate 代码问题；hand-off/done 侧确认「archived-unmerged 入口」可优雅收尾。

**BR-12〔已知不覆盖债台账〕** — CEO-F7（meta）
本批次向「已知不覆盖」净增 3 条凭约定信任的绕过面；模式=每消一个假阳性就加一条绕过面，可靠性被掏空。
建议：设计门把「已知不覆盖」当债务台账过一遍，对每条问「若是真实攻击/事故路径，能否从 git 留痕发现」；「发现不了」的（如 BR-1 静默语义改动）必须升级处置（加审计锚），不与「发现得了」的（rebase 伪造 log 可查）混为接受。

## 确认无发现（多声正面确认）
D1 窗口机制（sha 非 merge、set 去重无双计）· D3 base 树可达性判据（change 域分类，评"本批次质量最高修订"）· D3 短路顺序 · 锚死 glob 后缀精度 · D2 闭合前缀拒 -fix/X · 既有 SHIPPED 测试不扰动 · 三修复代码路径两两互不交叠 · D3/D1 prose/脚本备选否决站得住。
