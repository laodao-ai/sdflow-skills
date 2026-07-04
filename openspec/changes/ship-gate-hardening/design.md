# ship-gate-hardening — Design

## Context

`sdflow-ship/scripts/ship_gate.py`（313 行，只读零副作用）以「盘面即状态」判定阶段三步序（adr/0006(b)）。首个全链实战（`cross-model-outside-voice`）暴露三个判定缺陷，全部有活体复现与人工越权留痕：

- **B1**：完成判据窗口 `{sha}..HEAD --no-merges`（`decide()` → `plan_first_sha` `ship_gate.py:147-152` + `done_task_ids` `ship_gate.py:155-167`）以 plan 落地 commit 为**排他**起点。`checkpoint-commit.sh` 用 `git add -A`，未提交的 `superpowers-plan.md` 会随 task1 的 checkpoint 一起入库——此时 task1 锚就在 `sha` 自身，被窗口排除 → done_tasks 少 1（实录 11/12 误报，空 commit 6b94531 补锚绕过）。
- **B2**：design 域新鲜度 `is_stale(scope="design")`（`ship_gate.py:77-96`）对 design-approved 锚提交之后**任何**触及四件套（proposal/design/tasks.md、specs/）的提交判失鲜。但 sdflow-code-review 按工作流设计会对 design.md（措辞修正）/tasks.md（勾选回填）打 `[impl-review-fix]` 补丁并以 `checkpoint(impl-review)` 提交——合法尾流被误判「拍板失鲜」REFUSE_START（实录两次，均人工重申越权）。
- **B3**：pre-flight 按 active 路径 `openspec/changes/{change}/` 找 `spec-review-report.md`（`ship_gate.py:199-205`）；归档后目录移入 `openspec/changes/archive/<date>-{change}/`，gate 误报「未过设计门」。行 287-297 已有 SHIPPED 判定逻辑（handoff+archived+merged），但归档后控制流在 pre-flight 就断，永远不可达。

约束：gate 保持只读零副作用（D8）、锚行字面集不变、退出码语义不变、不引入 state 文件（盘面即状态红线）。

## Goals / Non-Goals

**Goals：**
- 三个误报路径归零（以真实复现盘面为回归测试 fixture）。
- 契约文档（脚本头注释、spec-workflow Requirement、SKILL.md 提示语）与新行为同步，不留漂移。

**Non-Goals：**
- 熔断重试计数脚本化（T26）——独立设计题，不触及本次三条判定路径（可证伪：三修复均不改 STEP_IN_PROGRESS 分支）。
- rebase/--amend 历史改写防伪——维持既有「已知不覆盖」声明，不扩威胁模型。
- T28/T29（提示 prompt / 时长度量）——归 workflow-metrics-loop。

## Decisions

### D1（B1）：窗口起点改为「含 plan 落地 commit 自身」——追加解析 `sha` 自身 subject

- **选定**：`done_task_ids` 除扫 `{sha}..HEAD --no-merges` 外，追加读取 `git log -1 --format=%s {sha}` 并以同一前缀+`TAG_RE` 规则解析计入。窗口语义变为 **`[sha, HEAD]` 闭区间**。
- **备选 a）`{sha}^..HEAD`**：sha 为根 commit 时 `sha^` 不存在而报错，需特判；且 `sha^..HEAD` 在 sha 有多 parent（merge）时语义歧义。弃。
- **备选 b）改 checkpoint-commit.sh 先单独提交 plan**：治因不治判定——gate 应对「plan 与 task1 同 commit」这一合法盘面健壮，而不是要求上游永不产生它（人工手跑也可能产生）。弃。
- 理由：追加一次 `-1` 解析零边界风险、语义直白；spec 原文的窗口表述（`<sha>..HEAD`）随修为闭区间表述。

### D2（B2）：design 域失鲜扫描按 commit subject 白名单豁免 `checkpoint(impl-review)` 前缀 ⭐〔TG-23 决策记录〕

- **选定（方案 a）**：`is_stale(scope="design")` 逐 commit 判定时，subject 以**闭合字面前缀 `checkpoint(impl-review)`**（含右括号）起始的提交**不触发失鲜**（其触及四件套视为阶段三合法尾流修订）。实现上把 `git log {sha}..HEAD --name-only --format=` 换为带 subject 的分组遍历（`--format=%x00%s` 分帧或 `%H` 逐条），按 commit 粒度过滤后再看触及路径。
  - 〔grill-amendment〕**前缀必须闭合**：`checkpoint-commit.sh <step>` 恒产出 `checkpoint(<step>)` 或 `checkpoint(<step>): <desc>`，code-review 的 step 名恒为 `impl-review`（`[impl-review-fix]` 只是报告标记，非 step 名）。排除 `checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)` 等**从不合法产生**的变体。开口前缀 `checkpoint(impl-review`（无右括号）会把这些变体误纳入豁免，凭空放宽绕过面，与「豁免面刻意窄」自相矛盾。
  - 〔spec-review-amendment BR-7〕**判据用精确式而非裸 startswith 闭合前缀**：`subject == "checkpoint(impl-review)" or subject.startswith("checkpoint(impl-review):")`。因 `startswith("checkpoint(impl-review)")`（闭合前缀）虽正确拒 `-fix`/`X`（第 22 字符非 `)`），却仍**收 `checkpoint(impl-review)evil` 这类右括号后带垃圾尾串**的 subject（codex-design#4 + 核验镜实证）；真实产物只有裸 `checkpoint(impl-review)` 与带冒号描述两种，精确式对二者零漏、对尾串垃圾零误豁免。
- **备选 b）重申锚 `design-reaffirmed`**：code-review 完成时回写新锚行推进新鲜度基线。语义最正，但扩契约面（新锚行 × 脚本头注释 × 两 SKILL 模板 × `test_anchor_contract.py` 双向钉死），且回写者与补丁作者是同一主体（sdflow-code-review 主 session），相对方案 a 没有额外保证——成本高、增益零。弃（若未来出现多个合法尾流写者再升级）。
- **备选 c）监视面收窄（tasks.md 勾选-only diff 豁免）**：需 diff 内容分析（所有变更行均为 `- [ ]`→`- [x]`），复杂且**不覆盖 design.md 措辞补丁**（本轮实际触发源之一）。弃。
- **信任模型一致性**：gate 已信任 checkpoint subject——完成判据 `done_task_ids` 就靠 `checkpoint(task<n>-` 前缀（`ship_gate.py:158-166`，含 revert 防御的 `startswith("checkpoint(task")` + `TAG_RE.match` **两道闸**先例）。〔grill-amendment〕豁免判定的闭合前缀 `checkpoint(impl-review)`（右括号即第二道结构闸的等效物）正是为对齐该先例——先例靠 `TAG_RE` 挡掉 `checkpoint(task` 开头但非 `task<n>-` 的噪声，豁免靠右括号挡掉 `impl-review` 开头但非精确 step 名的变体。伪造 subject 绕过失鲜 = 显式越权同权级（git 留痕可审计），与既有「已知不覆盖」条目同类，追加声明即可。
- **豁免面刻意窄**：只豁免闭合前缀 `checkpoint(impl-review)` 一个 step 名。`checkpoint(spec-review)` 发生在拍板前（无需豁免）；`checkpoint(task<n>-` 实现提交按约定不触碰四件套（若触碰，判失鲜是**正确**行为——实现改设计须重审）；`checkpoint(impl-review-fix)`/`checkpoint(impl-reviewX)` 等右括号后带尾串的变体从不由 checkpoint 脚本合法产生，**照判失鲜**；人工/其他 subject 触及四件套照判失鲜。

### D3（B3）：pre-flight 前置归档终态短路（active 缺席时查 archive + 分支态）

- **选定**：`decide()` 在 git 健全性检查后、设计门 pre-flight 前，增加：`cdir` 不存在时 → 查**日期前缀锚死 glob**（见下条）——命中且**该 archive 目录已在 base 树里**（change 域可达，见下「终态判据」）→ **SHIPPED**（exit 0）；命中但不在 base 树 → **RUN_VERIFY**（next=sdflow-done，理由「已归档但分支未并，完成 merge 收尾」）；不命中 → **REFUSE_START** 但理由改为「change 不存在（active 与 archive 均无）」，与「未过设计门」区分。
- **终态判据必须是 change 域，不用全局 `branch_state()`**〔grill-amendment〕：`branch_state()`（`ship_gate.py:178-189`）答的是「当前 HEAD 分支有没有并进 base」，是**全局**问题，与「demo 这个 change 有没有 merge」无关。反例：demo 已在 `feat/demo` 上 archive+merge 到 main，之后切到无关新分支 `feat/other`（有未并提交）再查 demo → 全局 `branch_state()=pending` → 误判 RUN_VERIFY「去跑收尾」，而 demo 早已 ship。这与它要修的 B3 是**同一类缺陷**（判据取错域）。改用**匹配到的那个 archive 目录是否已存在于 base(main/master) 的树里**判定：`git ls-tree <base> -- openspec/changes/archive/<dir>/` 非空（或 `cat-file -e <base>:<path>`）即「demo 的归档已落 base」→ SHIPPED；不在 base 树 → RUN_VERIFY。**与当前 HEAD 在哪条分支无关**：并了就是 SHIPPED、没并就是 pending，跨分支查也对。base 不存在（无 main/master）时回落 UNKNOWN（同 `branch_state()` 的 unknown 语义）。只多一个 `git ls-tree` 只读调用，守 D8 零副作用红线，是真正的盘面推导。
- **顺序关键**：短路必须在设计门 freshness 检查**之前**——归档 commit 的 `--name-only` 会列出 active 路径的删除记录，若先跑 freshness 会引入新误报；短路后该路径天然不可达。
- **glob 必须锚死日期前缀**〔grill-amendment〕：归档命名恒为 `<YYYY-MM-DD>-<change>`，用 `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-{change}` 而非 `*-{change}`。开口 `*-{change}` 是**后缀匹配**，`*` 吞任意前缀 → 别的 change（如 `cross-demo`）的归档会撞进 `demo` 的查询，让 gate 对不存在的 change 误报 SHIPPED/RUN_VERIFY。B3 之前该 glob 只喂 final SHIPPED（active 齐全时碰撞无害），D3 把它提为**pre-flight 载荷判据**，碰撞从无害升级为误判源，故须锚死。`ship_gate.py:289` 既有 `archived` 一并换同款保持一致。注意这与「同名旧档」（精确同名 `demo` 历史归档）是**两个问题**：后缀碰撞靠锚死日期前缀消除；精确同名旧档走下方「已知不覆盖」。
- **备选）改 sdflow-ship SKILL.md 提示「归档后勿重跑 gate」**：prose 治 prose，违反 adr/0006(b) 的立场。弃。
- **已知不覆盖（追加声明）**：**精确同名** change 历史归档过（日期前缀锚死 glob 仍命中真同名旧档 `YYYY-MM-DD-{change}`，且该旧档已在 base 树）、而新一轮同名 change 尚未建 active 目录时，gate 会按旧档报 SHIPPED——change 重名属流程反模式（ROADMAP 登记可查），接受并记录。〔grill-amendment〕注意与后缀碰撞区分：后缀撞名（`cross-demo` 撞 `demo`）已由锚死日期前缀 glob 消除，不在此「已知不覆盖」内；这里残留的仅是**字面完全同名**这一反模式。

#### D3 硬化 bundle〔spec-review-amendment · 设计门 Q3 全采纳〕

评审发现 grill 拍的 change 域判据虽方向对（评"本批次质量最高"），但**不完整**，six 处硬化全采纳：

- **H1（BR-2+HRTG-1，假✅ 高危）SHIPPED 前追读 archived verify=PASS 锚**：D3 短路判 SHIPPED **MUST 追读**归档目录内 `verify-report.md` 的 `<!-- ship-gate: verify=PASS -->` 锚（CLI 归档必携带，近零漏报）——不再把「归档⟹已验」当无条件蕴含（手工 `mkdir` 空壳目录 commit+merge 会假 SHIPPED）。与「盘面即状态、锚即 ground truth」一致：终态判定 MUST 读锚，MUST NOT 只信目录存在性。**同理 active 存在时的 final SHIPPED 路径（`ship_gate.py:287-299`）的 `archived` 谓词须收紧**——不得被旧/垃圾同名 archive glob 触发（当前 `any(glob)` 只判存在性）；active 存在时归档已发生本属异常，宜 RUN_VERIFY/UNKNOWN 而非 SHIPPED。
- **H2（BR-4）发现改纯 git 域，与判据同域**：发现 MUST NOT 用文件系统 glob（工作树域，依赖当前 checkout 含归档目录 + 会误纳未跟踪垃圾目录）。改用 `git ls-tree HEAD` ∪ `git ls-tree <base>` 列 `openspec/changes/archive/` 子项：**在 base 树 → SHIPPED、仅在 HEAD 树（归档提交未并）→ RUN_VERIFY、皆无 → REFUSE「不存在」**。工作树无关、天然忽略未跟踪垃圾。这才真正兑现 grill 的「change 域跨分支也对」（否则发现环节仍工作树域，主张名不副实）。
- **H3（HRTG-2）返回码可见 git helper + 单一 `base_ref()`**：`run_git()` 把 git 错误与「路径不在树」都折叠成空串，D3 无法区分「base 不存在→UNKNOWN」vs「ls-tree 空→REFUSE/RUN_VERIFY」。MUST 加返回码可见的 git helper + 单一 `base_ref()`（main/master 优先级 + 缺失=UNKNOWN 语义），先定 base 再 ls-tree。
- **H4（HRTG-3）detached HEAD 契约调和**：D3 改 change 域可达性后，detached HEAD 对 D3 判定**已无关**（不再经 branch_state）。MUST 更新头注释/状态机的「detached→UNKNOWN」契约：detached 下 D3 短路仍可 SHIPPED（凭 base 树可达），仅 active 路径的 final branch_state 判定保留 detached→UNKNOWN。补 detached+archived=SHIPPED 测试。
- **H5（HRTG-4）`--change` 注入防御**：`--change` 值 MUST 校验为 slug（`[a-z0-9][a-z0-9-]*`）或对 archive 子项遍历用 `re.escape(change)` fullmatch，MUST NOT 把用户输入直接插进 glob（`* ? []` 会被当元字符，且 active 查找当字面、archive 查找当模式，两域不一致）。
- **H6（BR-9）多命中确定性**：同名 change 多次 ship（多个日期前缀归档）时，判据为**匹配集任一目录在 base 树 → SHIPPED，否则 RUN_VERIFY**（纯 git 域方案天然支持 any-可达，不需选「取哪个 `<dir>`」）。

### D5（BR-3）：完成判据从基数比较改任务号集合归属〔spec-review-amendment · 设计门 Q1 纳入 · scope +1 缺陷〕

- **选定**：`decide()` 完成判据从 `len(done) < n`（基数）改为**任务号集合归属** `plan_ids ⊆ done_ids`。新增 `plan_task_ids(plan)` 解析 `### Task <n>:` 的号集（复用 `TASK_TITLE_RE`），`done_task_ids` 已返回号集，判 `plan_ids - done_ids == ∅` 为齐；未齐时 `CONTINUE_IMPL` 上报 `done_tasks = sorted(done_ids ∩ plan_ids)`（只报计划内已完成）。
- **理由**：现基数比较把「完成计数 == 计划计数」当齐——一个**计划外任务号**（`checkpoint(task9-…)` 遗留/错号/merge 内提交）可**顶替**一个缺失的计划内号（活体复现：plan=task1/task2、done={"1","9"}、len=2 → 假齐进 code-review，task2 从未完成）。既有 `test_merged_branch_inner_commits_do_enter_window` 已证计划外 "9" 会进 done_ids，"只差补 task1 即成灾"。集合归属根治。
- **与 D1 正交叠加**：D1 让 plan 落地 commit 自身的 task **入窗口**（修漏数/假红），D5 让「入窗口的号必须属计划内、且计划内号全齐」（修假齐/假✅）。同函数、两个方向，叠加后完成判据既不漏也不假。复选框辅通道（`ship_gate.py:234-236`）语义不变（仍在未齐分支内兜底），但其判定基准随主判据改为集合归属。

### D4：测试以真实复现盘面为 fixture

三缺陷各 ≥2 用例，落点沿用既有测试文件结构：

| 缺陷 | 文件 | 用例 |
|---|---|---|
| B1 | `test_gate_impl_progress.py` | ①plan 与 task1 锚同 commit → task1 计入、齐 N 判完成；②plan 单独提交（既有路径）不回归 |
| B2 | `test_gate_freshness.py` | ①拍板后 `checkpoint(impl-review)`/`: 描述` 触及 design.md/tasks.md → 不失鲜；②普通 subject 触及 design.md → 照判失鲜；③变体 `checkpoint(impl-review-fix)`/`impl-reviewX` + 尾串 `checkpoint(impl-review)evil` → 不豁免〔BR-7〕；④空 subject 帧 → 照失鲜〔BR-6〕；⑤同窗口 impl-review+普通 subject 交错各改一件套 → 普通那件照失鲜〔BR-6〕 |
| B3 | 新 `test_gate_terminal.py` | ①归档在 base 树+verify=PASS 锚 → SHIPPED；②归档仅在 HEAD 树（未并）→ RUN_VERIFY；③皆无 → REFUSE「不存在」；④active + 精确同名旧档 → active 优先；⑤后缀撞名旧档 → 不误命中；⑥跨分支查已并 change → 仍 SHIPPED；⑦〔BR-2〕archive 命中但无 verify=PASS 锚（空壳）→ 不 SHIPPED；⑧〔BR-4〕未跟踪垃圾 archive 目录 → 不误 RUN_VERIFY；⑨〔H4〕detached HEAD+归档已并 → SHIPPED；⑩〔H5〕`--change` 含 glob 元字符 → 安全（slug 校验/re.escape） |
| B4〔D5·Q1〕 | `test_gate_impl_progress.py` | ①plan=task1/task2、done={task1,task9 计划外} → **CONTINUE_IMPL 非假齐**（集合归属，task2 未完不放行）；②plan 号全被 done 覆盖 → 判齐；③计划外号不计入 done_tasks 上报 |

## 状态机图〔TG-09：change 生命周期终态修复〕

```
                     ┌──────────────────────────────────────────────────────┐
                     │            gate 眼中的 change 生命周期                │
                     └──────────────────────────────────────────────────────┘
  (无目录)──────────────────────REFUSE_START「change 不存在」★D3 新增区分
      │ openspec new
      ▼
  未拍板 ──REFUSE_START──▶ 拍板(design-approved 锚)
                              │
              ┌───────────────┤ 失鲜(四件套被改)──REFUSE_START
              │               │   ★D2: checkpoint(impl-review) 闭合前缀豁免，不入此转换
              ▼               ▼
           RUN_SOP ──▶ RUN_PLAN ──▶ CONTINUE_IMPL(plan_ids⊄done) ─▶ plan_ids⊆done
          (TG-02时)     ★D1: 窗口含 plan commit 自身 ★D5: 集合归属非计数  │
                                                               ▼
        BLOCKED_UPSTREAM ◀──blocked── RUN_CODE_REVIEW ──pass──▶ RUN_VERIFY
                                                               │
                              VERIFY_FAIL ◀──FAIL──────────────┤PASS
                                                               ▼
                                  收尾(hand-off+archive+merge 由 sdflow-done)
                                                               │
      ┌────────────────────────────────────────────────────────┤
      ▼ 归档+未并                                               ▼ 归档+已并
  RUN_VERIFY(完成 merge 收尾)★D3 ──────────────────────────▶ SHIPPED(终态)★D3
                                                            （旧行为：误报 REFUSE_START）
  异常转换：任意态 → UNKNOWN（多锚冲突/双通道不可判/标题0/detached HEAD/git 不可用）
```

## 决策图〔TG-12：decide() 判定序与三个修复点〕

```
  git 健全性 ──不可用──▶ UNKNOWN
      │
      ▼
  ★D3 active cdir 存在？─否─▶ ls-tree HEAD∪base 列 archive/(纯git域,re.escape)──无──▶ REFUSE(不存在)
      │是                       │命中（H2 发现=判据同域,H5 注入防御）
      │                         ▼
      │                  在 base 树 且 archived verify=PASS 锚?(H1)──是──▶ SHIPPED
      │                         │仅在HEAD树(未并)──▶ RUN_VERIFY(merge收尾)  [base无→UNKNOWN H3]
      ▼
  design-approved 锚在？──否──▶ REFUSE_START(未过设计门)
      │是
      ▼
  ★D2 四件套失鲜？(checkpoint(impl-review) 精确式提交豁免)──失鲜──▶ REFUSE_START(重审)
      │鲜
      ▼
  (verify 冲突锚早检) → SOP → plan 在？→ ★D1 窗口[sha,HEAD]闭区间 ★D5 plan_ids⊆done 集合归属
      → code-review 门 → verify 终门 → final SHIPPED(★H1 archived 谓词收紧,不被旧档触发)
```

## Risks / Trade-offs

- **[风险] 豁免前缀被滥用**（人工把设计改动伪装成 impl-review 提交）→ 缓解：与既有 subject 信任模型同级（人机同权、git 留痕可审计）；头注释「已知不覆盖」显式追加此条；review 时 git log 可查。
- **[风险] `--format=%x00%s` 分帧解析引入新解析 bug** → 缓解：沿用 `done_task_ids` 已验证的 `startswith` 字面前缀手法；B2 测试③覆盖前缀边界。
- **[风险] B3 的 archive glob 误中同名旧档** → 缓解：active 优先（测试④）；重名反模式声明进「已知不覆盖」。
- **[取舍] 方案 a 豁免粒度是 commit 级非 hunk 级**——一个 `checkpoint(impl-review)` commit 若同时夹带真正的设计变更也会被豁免。〔grill-amendment：正当性主张降级为「约定+已知窗口」〕安全边界是**约定级**，不是 gate 保证的门：①gate 只锚 subject 前缀，**不核验生产者**——手跑 `checkpoint-commit.sh impl-review` 或他步复用该 tag 同样被豁免；②对四件套的编辑**无独立门审过**——code-review 是 design.md 措辞补丁的作者而非审阅者（D2-b 弃选理由已承认「回写者与补丁作者同一主体」）。真实安全依赖「code-review 对四件套仅作装饰性改动（措辞/勾选）」这一**约定**，gate 不核验、不做 hunk 分析。由此存在**已知窗口**：拍板后经 `impl-review` 豁免的四件套编辑不经二次批准即随档 ship；若某次"措辞修正"实际改动设计语义，会静默 merge。接受并记录（进头注释「已知不覆盖」）——契合「任何一层覆盖不得无声蒸发」：把窗口显形，不以"审过的门"糊过。加轻量 hunk 约束（D2-c）复杂度高、重申锚（D2-b）成本高增益零，均已弃。

## Migration Plan

- 单文件脚本经 `setup.sh` symlink 安装，merge 即时生效，无部署步骤、无数据迁移。
- 回滚 = `git revert`（运行 checkout 回退 + 重跑 setup.sh，见 CLAUDE.md 回滚约定）。
- spec 同步：`openspec/specs/spec-workflow/spec.md` 的窗口语义句随归档 delta 更新（MODIFIED Requirement）。

## Open Questions

（无——B2 选型已在 D2 拍定推荐，交设计门确认或推翻。）

## Compliance（规则/边界合规声明）

- **adr/0004**（ship 窄编排、不越两个人类门）：遵守——仅修判定精度，人类门位置不动。
- **adr/0006(b)**（确定性台账、prose 不记步序）：遵守并强化——D3 备选「prose 提示」正因违反此条被弃。
- **盘面即状态（无 state 文件）**：遵守——三修复全部只读推导，零新副作用。
- **锚行契约（脚本头注释与模板双向钉死）**：遵守——锚行字面集不变；头注释契约表随行为更新，`test_anchor_contract.py` 兜底。
- D-2/D-4/D-6：N/A（无 DB/外部依赖/共享 schema 边界）。
