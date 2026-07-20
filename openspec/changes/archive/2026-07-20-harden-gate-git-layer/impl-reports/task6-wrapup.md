# impl-report — Task 6: 评审工作流不与新判定自锁，全套件回归并交接

**R-ID:** R3 · **Blocked-by:** 1,2,3,4,5（全部已 SHIPPED）
**范围:** tasks 1.6 / 1.6b / 1.7 / 1.7b / 1.8 / 6.1 / 6.2 / 6.3 / 6.4 / 6.5 + 测试 5.13 / 5.17（4.1b 前票已建）

## 做了什么

### ADR-7(a) code 域两段提交时序（tasks 1.6 / 1.6b）
`sdflow-code-review/SKILL.md` 的 checkpoint 步从「产出报告 + 自动修复**同一次**提交」改为**两段**：
① 自动修复先单独 commit（无修复则跳过）② `git rev-parse HEAD` 取锚 = 修复提交 → 写进报告 `reviewed_sha`
③ 报告单独 report-only commit。附 **1.6b 工作树纪律**：`checkpoint-commit.sh` 用 `git add -A`，故第 3 步前
MUST `git status --porcelain` 确认只剩报告文件，否则残留改动被卷进 report commit。
说明「本设计下天然可行」：code 域比较排除 openspec 顶层条目 ⇒ report-only 提交不动非 openspec 顶层条目 ⇒ 不触发失鲜。

### ADR-7(b) design 域拍板前二次修订（tasks 1.7 / 1.7b）
`sdflow-spec-review/SKILL.md`：
- **1.7b（拍板回写协议）**：加「拍板前二次修订 MUST 先单独 checkpoint 提交取 sha、再回写锚」，
  说明自锁成因（修订与 frontmatter 同提交 ⇒ 锚指更早提交 ⇒ 拍板即失鲜），并注明「design 域天然免疫只对
  正常路径成立」。
- **1.7（收敛口）**：加流程纪律「拍板前若四件套相对镜子审过的提交有实质改动，MUST 先跑窄复核再拍板」
  （C1/C2 论证：镜子审 C1、拍板批准 C2、锚写 C2、findings 只针对 C1）。

### 人工补锚指引（task 1.8）
三处同步说明**需补两个字段**（`design_approved` + `reviewed_sha`）+ 引 ADR-1 语义句「锚记的是被批准的盘面，
不是写报告的时刻」：
- `ship_gate.py` 的 `REFUSE_START` reason（`decide()` 内 design 门缺锚分支）；保留「补锚」字样（`test_gate_preflight` 断言）。
- `sdflow-spec-review/SKILL.md` 的「gate exit 3 人工补锚」段。
- `design.md` 的 ADR-1 已含该语义句原文，**无需改动**（且本票 MUST NOT 改四件套）——见下「A2 注记（建议区）」。

### 头注释与链序文档（tasks 6.1 / 6.2）
- `ship_gate.py` 头 docstring 的「D9 新鲜度」段整体重写为「**录锚 + 比内容 + 限定求值窗口**」，逐域展开
  （design ls-tree 映射比较 + 求值窗口三入口；code 顶层条目比较；读失败≠内容为空），指向 `openspec/adr/0026`。
  「已知不覆盖」段新增登记三项残余：**归档终态盲区**、**窗口右边界间隙**、**T189 耦合与承重升格**。
  旧段描述的退役机制（BR-7 subject 短路、`git diff-tree` 帧枚举协议）随重写清除。
- `sdflow-ship/SKILL.md` 链序段补「行为边界」段：design 域失鲜仅在 `RUN_SOP`/`RUN_PLAN`/`CONTINUE_IMPL`
  窗口内求值，进入代码审后不再检查；行为收紧非 bug。

### 测试（5.13 / 5.17）
- **5.13**（`test_gate_freshness.py`）：`test_code_review_autofix_two_stage_commit_does_not_self_stale`（正例，
  两段时序两消费方均 fresh、e2e 非 RERUN_STALE）+ `test_code_review_single_stage_commit_would_self_lock`
  （对照/变异，单段时序 → stale → RERUN_STALE）。
- **5.17**（`test_gate_reviewed_sha.py`）：`test_adr7b_second_revision_anchored_after_is_not_refused`（正例，
  锚含修订 → CONTINUE_IMPL 不被拒）+ `test_adr7b_second_revision_anchored_before_self_locks`（变异，
  锚指修订前 → REFUSE_START exit 3）。
- 4.1b（fixture 第三段建模）**前票已建**：`approved_change(revise=, anchor="head|pre-revision")` 已就绪，本票直接复用。

## 变异证明台账（按守卫计数）

每条「自锁/拒绝」用例承担**双重变异角色**：既是 ADR-7 时序纪律的对照物（SKILL 侧无 ship_gate 代码可删，
以「错误时序对照」承担变异，同 5.5 对比测试范式），**又是真实的 ship_gate 守卫变异体**。实测：

| 守卫 | 变异手段 | 受影响用例 | 结果 |
|---|---|---|---|
| code 域顶层条目比较（`is_stale` scope=code） | 恒 `return False,"fresh"`（ast.parse 通过） | `test_code_review_single_stage_commit_would_self_lock` | **转红** ✓（AssertionError@1405） |
| design 域失鲜求值（`is_stale` scope=design） | 分支入口恒 `return False,"fresh"`（ast.parse 通过） | `test_adr7b_second_revision_anchored_before_self_locks` | **转红** ✓（AssertionError@291） |

正例（fresh/不被拒）+ 变异例（stale/被拒）成对通过 = 「让锚指向改动前的提交 ⇒ 用例变红」的完整落地。
变异体均以恒真/恒假替换整条 return、非删多行布尔中一行，先 `ast.parse` 确认可运行（守 change 曾踩的 SyntaxError 零判别力）。

## 6.3 全历史核验（编排层已跑，此处照录，未重跑）

口径 = `checkpoint(<change>:taskN-*)` ∧ 触碰自身 `design.md`/`proposal.md`/`specs/`：
- **strict 口径**（在该 change `design_approved` frontmatter 之后）：`94c20b7`[mlh] / `5548921`[devenv] /
  `cfb9a67`[devenv] **三例确证 post-approval，与 A2 登记一致 ⇒ 三例仍是全部，A2 成立**。
- **宽口径补记（非缺陷）**：`2ef7ba5`[drop-per-dir-review-stub]、`26aeb2d`[checkpoint-tag-single-source]
  是 pre-frontmatter-机制的 post-approval 同形态例（无 `design_approved` 锚，落 strict 口径域外）；
  `a309fd8`[sdflow-init-hardening] 无门禁记录无法判定。A2 是「post-approval 设计改动会发生」的**目标态证据**，
  例子越多结论越强 ⇒ 文档完备性注记，**MUST NOT 当风险去缩设计**（详见 todolist T204）。

## 回归

`sdflow-ship/tests/` = **330 passed**（326 基线 + 4 新增）。仓根全套件回归见「验收」节。
「合并后主干再跑」归 `sdflow-done`（tasks 5.16 后半），本票不代跑。

## A2 注记（建议区 —— 归 archive 同步 delta 时处理，本票不改四件套）

`proposal.md`/`design.md` 是四件套、本票 **MUST NOT** 改。6.3 的宽口径补记（2 个 pre-frontmatter 同形态例 +
1 个无法判定例）建议在 archive 同步 delta-spec 时，作为「A2 目标态证据更强」的**文档完备性注记**并入
（残余面「T189 耦合」旁），**MUST NOT** 反向改写为风险去缩 design。design.md 的 ADR-1 语义句已是权威原文，
task 1.8 的三处补锚文案均引用它、未改动它。

## 遵从性自检（Global Constraints 相关项）

- `ship_gate.py` 保持零第三方依赖；本票只改 docstring 与一处 reason 文案，未动退出码集 `{0,3,4,5,6}`。
- 未引入语义分诊层 / 重锚逃生口；ADR-7(b) 的「先单独提交再回写」是**流程时序纪律**（SKILL 层），非 gate 层逃生口。
- 未改四件套；A2 注记走建议区。
- 未动任何 `sdflow:principles` 托管块。
- 新增守卫变异证明齐全（上表），未以「用例存在且为绿」充当证明。
