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

### D2（B2）：design 域失鲜扫描按 commit subject 白名单豁免 `checkpoint(impl-review` 前缀 ⭐〔TG-23 决策记录〕

- **选定（方案 a）**：`is_stale(scope="design")` 逐 commit 判定时，subject 以字面前缀 `checkpoint(impl-review` 起始的提交**不触发失鲜**（其触及四件套视为阶段三合法尾流修订）。实现上把 `git log {sha}..HEAD --name-only --format=` 换为带 subject 的分组遍历（`--format=%x00%s` 分帧或 `%H` 逐条），按 commit 粒度过滤后再看触及路径。
- **备选 b）重申锚 `design-reaffirmed`**：code-review 完成时回写新锚行推进新鲜度基线。语义最正，但扩契约面（新锚行 × 脚本头注释 × 两 SKILL 模板 × `test_anchor_contract.py` 双向钉死），且回写者与补丁作者是同一主体（sdflow-code-review 主 session），相对方案 a 没有额外保证——成本高、增益零。弃（若未来出现多个合法尾流写者再升级）。
- **备选 c）监视面收窄（tasks.md 勾选-only diff 豁免）**：需 diff 内容分析（所有变更行均为 `- [ ]`→`- [x]`），复杂且**不覆盖 design.md 措辞补丁**（本轮实际触发源之一）。弃。
- **信任模型一致性**：gate 已信任 checkpoint subject——完成判据 `done_task_ids` 就靠 `checkpoint(task<n>-` 前缀（`ship_gate.py:158-166`，含 revert 防御的 `startswith` + `TAG_RE.match` 先例，豁免判定沿用同一「字面前缀」手法）。伪造 subject 绕过失鲜 = 显式越权同权级（git 留痕可审计），与既有「已知不覆盖」条目同类，追加声明即可。
- **豁免面刻意窄**：只豁免 `checkpoint(impl-review` 一个前缀。`checkpoint(spec-review` 发生在拍板前（无需豁免）；`checkpoint(task<n>-` 实现提交按约定不触碰四件套（若触碰，判失鲜是**正确**行为——实现改设计须重审）；人工/其他 subject 触及四件套照判失鲜。

### D3（B3）：pre-flight 前置归档终态短路（active 缺席时查 archive + 分支态）

- **选定**：`decide()` 在 git 健全性检查后、设计门 pre-flight 前，增加：`cdir` 不存在时 → 查 `openspec/changes/archive/*-{change}` glob——命中且 `branch_state()=="merged"` → **SHIPPED**（exit 0）；命中但 `pending` → **RUN_VERIFY**（next=sdflow-done，理由「已归档但分支未并，完成 merge 收尾」）；不命中 → **REFUSE_START** 但理由改为「change 不存在（active 与 archive 均无）」，与「未过设计门」区分。
- **顺序关键**：短路必须在设计门 freshness 检查**之前**——归档 commit 的 `--name-only` 会列出 active 路径的删除记录，若先跑 freshness 会引入新误报；短路后该路径天然不可达。
- **备选）改 sdflow-ship SKILL.md 提示「归档后勿重跑 gate」**：prose 治 prose，违反 adr/0006(b) 的立场。弃。
- **已知不覆盖（追加声明）**：同名 change 历史归档过（`archive/*-{change}` 命中旧档）且新一轮同名 change 尚未建目录时，gate 会按旧档误报 SHIPPED——change 重名属流程反模式（ROADMAP 登记可查），接受并记录。

### D4：测试以真实复现盘面为 fixture

三缺陷各 ≥2 用例，落点沿用既有测试文件结构：

| 缺陷 | 文件 | 用例 |
|---|---|---|
| B1 | `test_gate_impl_progress.py` | ①plan 与 task1 锚同 commit → task1 计入、齐 N 判完成；②plan 单独提交（既有路径）不回归 |
| B2 | `test_gate_freshness.py` | ①拍板后 `checkpoint(impl-review)` 触及 design.md/tasks.md → 不失鲜；②拍板后普通 subject 触及 design.md → 照判失鲜（既有行为不回归）；③伪 subject 前缀相近（如 `checkpoint(impl-review2`——前缀匹配语义边界）明确判定 |
| B3 | 新 `test_gate_terminal.py`（或并入 preflight） | ①归档+已并 → SHIPPED exit 0；②归档+未并 → RUN_VERIFY；③active 与 archive 均无 → REFUSE_START「change 不存在」理由；④active 在时 archive 同名旧档不干扰（active 优先） |

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
              │               │   ★D2: checkpoint(impl-review) 前缀豁免，不入此转换
              ▼               ▼
           RUN_SOP ──▶ RUN_PLAN ──▶ CONTINUE_IMPL(done<N) ──▶ 齐 N
          (TG-02时)           ★D1: 窗口含 plan commit 自身      │
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
  ★D3 active cdir 存在？──否──▶ archive/*-{change} 命中？──否──▶ REFUSE_START(change 不存在)
      │是                          │是
      │                            ▼
      │                     branch merged？──是──▶ SHIPPED
      │                            │否──▶ RUN_VERIFY(merge 收尾)
      ▼
  design-approved 锚在？──否──▶ REFUSE_START(未过设计门)
      │是
      ▼
  ★D2 四件套失鲜？(checkpoint(impl-review 前缀提交豁免)──失鲜──▶ REFUSE_START(重审)
      │鲜
      ▼
  (verify 冲突锚早检) → SOP → plan 在？→ ★D1 完成判据(窗口[sha,HEAD]闭区间)
      → code-review 门 → verify 终门 → final SHIPPED 判定（原有，保留）
```

## Risks / Trade-offs

- **[风险] 豁免前缀被滥用**（人工把设计改动伪装成 impl-review 提交）→ 缓解：与既有 subject 信任模型同级（人机同权、git 留痕可审计）；头注释「已知不覆盖」显式追加此条；review 时 git log 可查。
- **[风险] `--format=%x00%s` 分帧解析引入新解析 bug** → 缓解：沿用 `done_task_ids` 已验证的 `startswith` 字面前缀手法；B2 测试③覆盖前缀边界。
- **[风险] B3 的 archive glob 误中同名旧档** → 缓解：active 优先（测试④）；重名反模式声明进「已知不覆盖」。
- **[取舍] 方案 a 豁免粒度是 commit 级非 hunk 级**——一个 `checkpoint(impl-review)` commit 若同时夹带真正的设计变更也会被豁免。接受：该 commit 由 sdflow-code-review 编排产生（受 skill 约束），且 code-review 本身就是审过这些补丁的门。

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
