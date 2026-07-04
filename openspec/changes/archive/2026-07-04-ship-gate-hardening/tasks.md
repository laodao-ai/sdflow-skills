# ship-gate-hardening — Tasks

> 需求追溯：全部任务对应 `specs/spec-workflow/spec.md` MODIFIED Requirement「阶段三编排台账确定性（ship_gate）」下的 Scenario——〔B1〕窗口闭区间、〔B2〕尾流修订豁免、〔B3〕归档终态（+D3 硬化 H1-H6）、〔B4〕完成判据集合归属。设计决策 = design.md D1-D5。〔spec-review-amendment：B4/D5 + D3 硬化 bundle 经设计门 Q1/Q3 拍板纳入；B2 取舍经 Q2 维持〕

## 1. B1 窗口闭区间（design D1；Scenario〔B1〕×2）

- [x] 1.1 `test_gate_impl_progress.py` 加失败测试：plan 与 `checkpoint(task1-<slug>)` 同 commit 的盘面，断言 task1 计入 done_tasks、齐 N 不误报 CONTINUE_IMPL〔Scenario: plan 与首个 task 锚同 commit 不漏数〕
- [x] 1.2 改 `done_task_ids`（`ship_gate.py:155-167`）：追加解析 `git log -1 --format=%s <sha>` 自身 subject（同 `startswith` + `TAG_RE.match` 规则），窗口语义变闭区间 `[sha, HEAD]`；1.1 转绿
- [x] 1.3 回归：plan 单独提交的既有路径用例保持绿（不多数、不少数）〔Scenario: 前置产物缺失点名〕
- [x] 1.4 〔spec-review-amendment BR-8：头注释契约漂移收口〕同步 `ship_gate.py:30-32`「完成判据窗口」头注释块（旧写 `git log <sha>..HEAD --no-merges`）+ CONTINUE_IMPL 人读 reason 串 `ship_gate.py:241`（旧硬编码 `窗口 {sha[:7]}..HEAD --no-merges`）为闭区间表述——设计自称「契约不留漂移」，D1 唯一漏排的 prose 面，`test_anchor_contract.py` 不覆盖此段故会静默漂移

## 2. B2 尾流修订豁免（design D2；Scenario〔B2〕）

- [x] 2.1 `test_gate_freshness.py` 加失败测试：design-approved 后 subject 闭合前缀 `checkpoint(impl-review)` 的提交触及 design.md+tasks.md，断言不失鲜、不 REFUSE_START〔Scenario: 阶段三合法尾流修订不失鲜〕。两种真实产物各一例：`checkpoint(impl-review)`（裸）与 `checkpoint(impl-review): 描述`
- [x] 2.2 改 `is_stale`（`ship_gate.py:77-96`）design 域：git log 改带 subject 分帧遍历，豁免判据用**精确式 `subject == "checkpoint(impl-review)" or subject.startswith("checkpoint(impl-review):")`**〔spec-review-amendment BR-7，非裸闭合前缀 startswith——后者仍收 `)evil` 尾串〕的 commit 跳过失鲜判定；2.1 转绿。**护栏**：①豁免分支 MUST 只在 `scope=="design"` 内生效，`scope=="code"`（cr/verify 新鲜度）路径行为逐字不变〔grill-amendment〕；②〔spec-review-amendment BR-6〕**MUST NOT 给 is_stale 加 `--no-merges`/`--first-parent`**（头注释 :43 承诺 merge 内部提交逐一枚举不漏检，`done_task_ids` 的 `--no-merges` 习惯不得蔓延过来）——用既有 `test_gate_freshness.py` code 域用例（`test_stale_pass_reruns_not_ship` 等）回归兜底
- [x] 2.3 反向回归测试：①拍板后普通 subject 触及 design.md 照判失鲜（既有行为）〔grill-amendment〕；②**边界用例 `checkpoint(impl-review-fix)`、`checkpoint(impl-reviewX)` → 不豁免照失鲜**〔grill-amendment〕；③〔spec-review-amendment BR-7〕**`checkpoint(impl-review)evil` 右括号后尾串垃圾 → 不豁免**（精确式语义边界）；④〔spec-review-amendment BR-6：分帧解析边界〕**空 subject 帧**（空消息提交触及 design.md，帧形如 `\x00\n\n<path>`）→ 照失鲜；⑤〔spec-review-amendment BR-6：多提交交错〕同一 `{sha}..HEAD` 窗口内 `checkpoint(impl-review)`（改 tasks.md）+ 普通 subject（改 design.md）**并存** → 后者仍判失鲜（分帧 bug 杀伤方向=假豁免，必须专测文件名归帧正确）
- [x] 2.4 `ship_gate.py` 头注释：D9 分域段追加豁免规则一句（精确式 `checkpoint(impl-review)`）+「已知不覆盖」追加两条〔grill-amendment〕：①「伪造/手工 checkpoint(impl-review) subject 可绕过失鲜——gate 不核验生产者（显式越权同权级，git 留痕）」；②「拍板后经 impl-review 豁免的四件套编辑不经二次批准即随档 ship（安全边界=约定级『仅装饰性改动』，gate 不做 hunk 分析）」
- [x] 2.5 〔spec-review-amendment BR-5：token 契约测试〕新增契约测试（类比 `test_anchor_contract.py`）把豁免 token `checkpoint(impl-review` 与 `~/.sdflow/hack/checkpoint-commit.sh` 的 code-review step 名（`impl-review`）**双向钉死**——step 改名时测试变红报警，防豁免静默失配 → B2 悄悄回归（假 REFUSE 重现）无痕。注：token 是 code-review 编排约定，测试锚定该约定字面即可（脚本本身不含 `impl-review` 字面，由 sdflow-code-review 传入）

## 3. B3 归档终态（design D3；Scenario〔B3〕×3）

> **设计门 Q3 拍板：D3 硬化 bundle 全采纳**，3.1/3.2 已按 H1-H6 落实（下）。

- [x] 3.1 新建 `test_gate_terminal.py` 失败测试 ×10：①归档在 base 树+archived verify=PASS 锚→SHIPPED exit0；②归档仅在 HEAD 树（未并）→RUN_VERIFY(next=sdflow-done)；③皆无→REFUSE reason 含「change 不存在」；④active+精确同名旧档→active 优先；⑤后缀撞名旧档→不误命中→REFUSE；⑥跨分支查已并 change→仍 SHIPPED（change 域证明）；⑦〔H1/BR-2〕archive 命中在 base 但**无 verify=PASS 锚**（空壳目录）→**不 SHIPPED**（降 RUN_VERIFY 或 UNKNOWN）；⑧〔H2/BR-4〕磁盘有**未 git 跟踪**的 archive 垃圾目录→glob 时代会假 RUN_VERIFY，纯 git 域下**不误命中**；⑨〔H4/HRTG-3〕detached HEAD + 归档已并 base→SHIPPED（detached 对 D3 无关）；⑩〔H5/HRTG-4〕`--change` 含 `* ? []` 元字符→安全（slug 校验/re.escape，不当 glob 模式）
- [x] 3.2 改 `decide()`（`ship_gate.py:192-211`）插入归档短路（git 健全性后、pre-flight 前），按 D3 硬化 bundle：
  - **H3** 加 `base_ref()`（main/master 优先，缺失→UNKNOWN）+ 返回码可见 git helper（区分 git 错误 / 空树 / 不存在）
  - **H2** 发现用纯 git 域：`git ls-tree HEAD -- openspec/changes/archive/` ∪ `git ls-tree <base> -- …`，对子项名以 **H5** `re.escape(change)` 套日期前缀 `\d{4}-\d\d-\d\d-` fullmatch（不用文件系统 glob、不把 `--change` 插进 glob）
  - 分派：匹配集**任一在 base 树 且该目录 archived `verify-report.md` 含 `verify=PASS` 锚**（**H1** 追读）→ SHIPPED；仅在 HEAD 树（未并）→ RUN_VERIFY「已归档未并 base，完成 merge 收尾」；皆无匹配 → REFUSE「change 不存在」（**H6** 多命中经 any-可达天然确定）
  - **H1 续**：收紧 `ship_gate.py:287-299` final SHIPPED 的 `archived` 谓词——不再 `any(glob("*-{change}"))` 凭存在性，改判「当前 lifecycle 的归档」（active 存在时归档本属异常，宜 RUN_VERIFY/UNKNOWN 不 SHIPPED）；**H5** `ship_gate.py:289` 一并去 glob 元字符风险
  - **H4** 头注释/状态机「detached→UNKNOWN」契约调和：detached 下 D3 短路仍可 SHIPPED，仅 active 路径 final branch_state 保留 detached→UNKNOWN；3.1 全绿
- [x] 3.3 `ship_gate.py` 头注释契约表：SHIPPED 行补「（含归档后重跑识别，追读 archived verify=PASS 锚）」、REFUSE_START 行补 change 不存在变体、〔BR-10〕RUN_VERIFY 行（:23）补「/ 归档未并 base 待 merge 收尾」变体、〔H4〕detached HEAD 语义分域注记；「已知不覆盖」追加精确同名旧档误中一条

## 4. B4 完成判据集合归属（design D5；设计门 Q1 纳入 · Scenario〔B4〕）

- [x] 4.1 `test_gate_impl_progress.py` 加失败测试：plan=task1/task2（N=2），窗口内 `checkpoint(task1-…)` + **计划外** `checkpoint(task9-…)`，断言 **CONTINUE_IMPL 非假齐**（task2 未完不放行）、`done_tasks` 只报计划内已完成（不含 9）〔Scenario: 计划外任务号不顶替缺失计划内号〕
- [x] 4.2 改 `decide()` 完成判据（`ship_gate.py:227-242`）：新增 `plan_task_ids(plan)`（解析 `### Task <n>:` 号集，复用 `TASK_TITLE_RE`），判据从 `len(done) < n` 改 `plan_ids - done_ids != ∅`（未齐）；CONTINUE_IMPL 上报 `done_tasks = sorted(done_ids ∩ plan_ids, key=int)`；4.1 转绿。复选框辅通道基准随改集合归属
- [x] 4.3 回归：既有 `test_all_tags_present_advances`（task1+task2 全齐）、`test_continue_impl_with_done_set`（仅 task1）、`test_merged_branch_inner_commits_do_enter_window`（done=["9"] 计划外，N=2）保持绿——最后一条现应更明确为 CONTINUE_IMPL（9∉plan_ids，plan_ids={1,2}⊄done）

## 5. 契约同步 + 收尾（proposal「契约文档同步」；design Migration）

- [x] 5.1 `sdflow-ship/SKILL.md` 链序段核对：REFUSE_START 提示语与新 reason 变体一致（「未过设计门…补锚」与「change 不存在」两分支）；`test_skill_text.py` / `test_anchor_contract.py` 全绿（锚行字面集未动，应零改动通过——若红即契约破坏，停下修）
- [x] 5.2 全量回归：`pytest sdflow-ship/tests/` 全绿 + 仓级 `pytest` 全绿（307+ 基线不降）
- [x] 5.3 归档时主 spec 同步核对：`openspec/specs/spec-workflow/spec.md` 窗口语义句按 delta 更新（sdflow-done archive CLI 自动，人工核对不漏）

## 测试覆盖图（TG-18）

```
  code path                                  测试类型            文件
  ─────────────────────────────────────────────────────────────────────────
  done_task_ids 闭区间(含 sha 自身)      →  pytest 单元(git fixture)  test_gate_impl_progress.py
  done_task_ids 排他窗口既有路径         →  pytest 回归               test_gate_impl_progress.py(既有)
  is_stale design 域豁免前缀命中/不命中  →  pytest 单元(git fixture)  test_gate_freshness.py
  is_stale 普通 subject 照失鲜           →  pytest 回归               test_gate_freshness.py(既有)
  decide 归档短路 SHIPPED/RUN_VERIFY/
    REFUSE(不存在)/active 优先            →  pytest 单元(目录 fixture) test_gate_terminal.py(新)
  锚行字面集/SKILL 文案契约              →  pytest 契约               test_anchor_contract.py / test_skill_text.py(既有)
  端到端(下一真实 change ship 全程)      →  实战计数(人工越权=0)      Success Metrics 度量
```
