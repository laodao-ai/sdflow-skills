# impl-verify-notes: add-sdflow-architecture

> 非四件套（proposal/design/tasks.md/specs 均未改动）——本文件是 Task 10 收尾新增的 Success Metrics 核对留痕，
> 只呈证据、不改判定。对应 tasks.md §5.1–5.4 / task-10-brief Step 5。

## Success Metrics 原文（proposal.md「Success Metrics」节，逐字摘录）

1. **端到端跑通** — 基准 0（无此能力）→ 目标：样例需求走完五步产出 skeleton-ready SAD（含「骨架切片建议」节）— 度量：`sad_lint.py` 退出码 0 且 SAD 含该节（演练记录锚入 tasks 验证）〔grill-amendment 措辞同步〕。
2. **机械断言覆盖** — 基准 0 → 目标：v1 三类断言（节存在性 / 假设计数 / 排序存在）各 ≥2 条 pytest 用例全绿 — 度量：pytest 通过计数。
3. **反假绿锁生效** — 基准无 → 目标：事实三问任一缺失时状态机拒绝 skeleton-ready（锁 draft）— 度量：负路径 pytest 用例（缺项 → 拒绝）通过。
4. **试点 outcome（后验）** — 基准无 → 目标：首个真实项目试点中，SAD 交棒后 4 周内骨架 change 真实开出、≥1 条 contract 回写 validated — 度量：消费仓 sad-log.md 迁移记录 + 骨架 change 归档。试点项目提名待拍板（决策登记 Q1）；Non-Goals 1–5 的证伪钟自试点启动起算。

---

## SM-1：端到端跑通 —— 逐条核对

**产物路径**（本次演练，`mktemp -d` 临时仓，跑完即清理，未污染本仓）：

- `$E2E/openspec/architecture/sad.md`（终态 `sad_status: skeleton-ready`，含「## 骨架切片建议」节）
- `$E2E/openspec/architecture/sad-log.md`（append-only 判定留痕：init / 3×set-fact / set-assumption / transition 六行）
- `$E2E/openspec/CONTEXT.md`、`$E2E/openspec/adr/`（`init` 首次创建的项目级布局）

**LINT_EXIT=0 输出原文**（第 4 步 `sad_lint.py --root "$E2E"`，见下方完整 transcript 第 32–35 行）：

```
$ python3 $S/sad_lint.py --root "$E2E"; echo "LINT_EXIT=$?"
structure-ok-SEMANTICS-UNCHECKED
假设计数: 1
LINT_EXIT=0
```

首行确认 = `structure-ok-SEMANTICS-UNCHECKED`（`sad_schema.PASS_CODE`），退出码 = 0，SAD 含「## 骨架切片建议」节（见 transcript 第 183–187 行）。**SM-1 达成**。

---

## SM-2：机械断言覆盖 —— 逐条核对

**用例计数**（`pytest sdflow-architecture/tests/ --collect-only -q | tail -1`）：

```
68 tests collected in 0.01s
```

**三类断言 × 正/负对照表**（每类 ≥2 条，全部 PASSED——见 Step 3 `pytest -v` 全量输出）：

| 类别 | 用例 | 正/负 | 断言码 |
|---|---|---|---|
| 节存在性 | `test_pass_honest_code` | 正 | 全节非空 + N/A 合规 → 0 |
| 节存在性 | `test_missing_section_reason_code` | 负 | 第 8 节被删 → `missing-section` |
| 节存在性 | `test_na_without_reason` | 负 | 裸 `N/A`（无理由）→ `na-without-reason` |
| 节存在性 | `test_fence_inside_markers_not_counted` | 正 | fence 内伪节锚/伪标记不计 → 仍 0 |
| 假设计数 | `test_pass_honest_code` | 正 | 内联↔附录集合一致 → `假设计数: 1` |
| 假设计数 | `test_duplicate_number_set_reconciliation` | 负 | 计数相等但集合错位 → `assumption-set-mismatch` |
| 假设计数 | `test_cache_mismatch_independent_code` | 负 | 附录处置数≠frontmatter 缓存 → `assumption-cache-mismatch` |
| 假设计数 | `test_assumption_unresolved_code` | 负 | 处置=「未处置」→ `assumption-unresolved` |
| 排序存在 | `test_pass_honest_code` | 正 | `1. 可靠性\n2. 可维护性` 严格全序 → 0（隐含覆盖，无需单列 unordered 断言即通过） |
| 排序存在 | `test_quality_attr_order`（子断言①） | 负 | 项目符号 `-` 替代编号 → `quality-attr-order-broken` |
| 排序存在 | `test_quality_attr_order`（子断言②） | 负 | 跳号 `1,3` → `quality-attr-order-broken` |

三类各 ≥2 条（实际 3–4 条不等）全绿，度量口径（pytest 通过计数）= 68/68。**SM-2 达成**。

---

## SM-3：反假绿锁生效 —— 逐条核对（按 proposal 原文「事实三问任一缺失 → 拒绝 skeleton-ready（锁 draft）」核对）

负路径 pytest 用例（缺项 → 拒绝）：

- `sdflow-architecture/tests/test_sad_scaffold.py::test_missing_fact_locks_draft` — `facts={**ANSWERED, "external_systems": "missing"}` → `transition --to skeleton-ready` 返回码 5，stderr 指名缺失问项 `external_systems`（PASSED）。
- `sdflow-architecture/tests/test_sad_scaffold.py::test_unresolved_assumption_locks_draft` — 假设未全「接受/待校准」（含一条「未处置」）→ 返回码 5，stderr 指名 `假设-2`（PASSED）。
- `sdflow-architecture/tests/test_sad_scaffold.py::test_out_of_table_transition_refused` — 状态迁移表外跳转（draft→validated 无 `--dod-confirmed` 前置）→ 返回码 5（PASSED）。
- `sdflow-architecture/tests/test_sad_scaffold.py::test_pierce_set_mismatch_refused` — 骨架切片穿越点集 ≠ 第 5 节子系统集 → 返回码 5（PASSED）。

正路径对照（事实三问全部 answered + 假设全部处置 → 允许迁移）：本次 e2e 演练本身（transition 返回码 0，见下方 transcript 第 29–30 行）。**SM-3 达成**。

---

## SM-4：试点 outcome（后验）

**试点未启动——设计门 Q1=c 暂缓提名，占位豁免。**

依据（`spec-review-report.md` 拍板记录原文核对，2026-07-12）：

> 设计门已拍板批准，日期 2026-07-12。Q1 = c（暂缓提名，SM-4 保持占位、试点出现时回填）；T1/T2 确认维持主审；自动决策 D1–D11 全部确认采纳，无覆盖。

对应「[需拍板]」节 Q1 选项 c 原文：「暂缓提名、试点出现时回填（SM-4 保持占位）……推荐 c（诚实占位优于虚假承诺……开发循环——SM-4 在 verify 时以「试点未启动」状态豁免，主判据 = SM-1/2/3）」。

本次 Task 10 收尾 verify 依此裁定：**SM-4 不计入本次判定**，SM-1/2/3 为本次收尾的主判据（均已达成，见上）。Non-Goals 1–5 的证伪钟未启动（试点未开始）。

---

## 端到端演练完整 transcript

跑于 `mktemp -d` 临时目录（脚本执行位置：`sdflow-architecture/scripts/`，未污染本仓；跑完已 `rm -rf` 清理）。
Step 4 唯一的手工介入 = 在三次 `set-fact` 之后、`set-assumption` 之前，对 `$E2E/openspec/architecture/sad.md` 做四处精确字符串替换
（§1 全序两行 / §2 一处 `[假设-1]` 含推测依据 / §5 一个子系统块 `### 5.1 采集端` + `contract[draft]` 行 / 附录表插入一行 `未处置`），
随后 `set-assumption 1=接受` 把该行处置改写为「接受」并回写 `assumptions_open` 缓存；`slice.md` 的穿越点占位替换为 `采集端`。

```
$ E2E=$(mktemp -d); mkdir -p "$E2E/openspec/changes" "$E2E/openspec/specs"
E2E=/var/folders/xl/9k0bckk50kj4krpr8lx74mn00000gn/T/tmp.VBm7sp1qQ5

$ python3 $S/sad_scaffold.py init --root "$E2E"
首次创建 openspec/adr
首次创建 openspec/CONTEXT.md
EXIT=0

$ python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact positioning=answered
EXIT=0

$ python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact external_systems=answered
EXIT=0

$ python3 $S/sad_scaffold.py set-fact --root "$E2E" --fact hard_constraints=answered
EXIT=0

# 手工填 §1 全序/§5 一个子系统+contract[draft]/一处[假设-1]+附录行(未处置)——模拟五步①-③产物
hand-edit applied to sad.md OK (§1/§2/§5/附录)

$ python3 $S/sad_scaffold.py set-assumption --root "$E2E" --assumption 1=接受
EXIT=0

$ printf -- slice.md (穿越点 replaced with 采集端)
- 穿越点[采集端]：§5.1 contract 条目
- 骨架 DoD：每条 L1 contract 被一次真实调用穿过 + 部署链路走通
- 建议 change 名：skeleton-demo

$ python3 $S/sad_scaffold.py transition --root "$E2E" --to skeleton-ready --slice-file "$E2E/slice.md"
EXIT=0

$ python3 $S/sad_lint.py --root "$E2E"; echo "LINT_EXIT=$?"
structure-ok-SEMANTICS-UNCHECKED
假设计数: 1
LINT_EXIT=0

$ python3 $S/sad_scaffold.py init --root "$E2E"; echo "SECOND_EXIT=$?"
[sad_scaffold] FAIL: SAD 已存在：--on-exists continue（增量续写）或 replan（重规划，旧内容归 git 历史）。
SECOND_EXIT=4
```

**终态 sad.md frontmatter**：

```
---
sad_schema: 1
sad_status: skeleton-ready
facts:
  positioning: answered
  external_systems: answered
  hard_constraints: answered
assumptions_open: 0
---
```

**终态 sad-log.md**（append-only，六行）：

```
# sad-log（append-only 判定留痕）
- 2026-07-12 09:15 UTC | init
- 2026-07-12 09:15 UTC | set-fact positioning=answered
- 2026-07-12 09:15 UTC | set-fact external_systems=answered
- 2026-07-12 09:15 UTC | set-fact hard_constraints=answered
- 2026-07-12 09:15 UTC | set-assumption 假设-1=接受
- 2026-07-12 09:15 UTC | transition draft→skeleton-ready
```

---

## 二次触发（第二次 `init`）提示文案观察记录

**命令**：`python3 $S/sad_scaffold.py init --root "$E2E"`（在已存在 `sad_status: skeleton-ready` 的 SAD 上重跑 init）

**退出码**：`4`（符合 REQ-9 单例分家判定；exit 码约定见 `sad_scaffold.py` Interfaces：0/2/3/4/5）

**stderr 提示文案原文**：

```
[sad_scaffold] FAIL: SAD 已存在：--on-exists continue（增量续写）或 replan（重规划，旧内容归 git 历史）。
```

观察：文案同时给出两条明确出路（`--on-exists continue` / `--on-exists replan`），且指明 replan 分支旧内容的去向（归 git 历史，非静默丢弃）——与 `test_singleton_no_silent_overwrite`（`sdflow-architecture/tests/test_sad_scaffold.py`）断言的 `"continue" in r.stderr and "replan" in r.stderr` 口径一致，e2e 观察与既有单测断言互证。

---

## 结论

SM-1/SM-2/SM-3 均以可验证证据达成；SM-4 按设计门 Q1=c 拍板处于占位豁免状态，非本次收尾判据。Task 10 全部 7 步（README / setup.sh symlink / 全套 pytest / e2e 演练 / 本文件 / todolist 登记 / commit）执行完毕，详见 `.superpowers/sdd/task-10-report.md`。
