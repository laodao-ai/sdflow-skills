# ship-gate-hardening — Tasks

> 需求追溯：全部任务对应 `specs/spec-workflow/spec.md` MODIFIED Requirement「阶段三编排台账确定性（ship_gate）」下的三组 Scenario——〔B1〕窗口闭区间、〔B2〕尾流修订豁免、〔B3〕归档终态。设计决策 = design.md D1-D4。

## 1. B1 窗口闭区间（design D1；Scenario〔B1〕×2）

- [ ] 1.1 `test_gate_impl_progress.py` 加失败测试：plan 与 `checkpoint(task1-<slug>)` 同 commit 的盘面，断言 task1 计入 done_tasks、齐 N 不误报 CONTINUE_IMPL〔Scenario: plan 与首个 task 锚同 commit 不漏数〕
- [ ] 1.2 改 `done_task_ids`（`ship_gate.py:155-167`）：追加解析 `git log -1 --format=%s <sha>` 自身 subject（同 `startswith` + `TAG_RE.match` 规则），窗口语义变闭区间 `[sha, HEAD]`；1.1 转绿
- [ ] 1.3 回归：plan 单独提交的既有路径用例保持绿（不多数、不少数）〔Scenario: 前置产物缺失点名〕

## 2. B2 尾流修订豁免（design D2；Scenario〔B2〕）

- [ ] 2.1 `test_gate_freshness.py` 加失败测试：design-approved 后 subject 闭合前缀 `checkpoint(impl-review)` 的提交触及 design.md+tasks.md，断言不失鲜、不 REFUSE_START〔Scenario: 阶段三合法尾流修订不失鲜〕。两种真实产物各一例：`checkpoint(impl-review)`（裸）与 `checkpoint(impl-review): 描述`
- [ ] 2.2 改 `is_stale`（`ship_gate.py:77-96`）design 域：git log 改带 subject 分帧遍历，**闭合字面前缀 `checkpoint(impl-review)`**（含右括号）的 commit 跳过失鲜判定；2.1 转绿。**护栏〔grill-amendment〕**：豁免分支 MUST 只在 `scope=="design"` 内生效，`scope=="code"`（cr/verify 新鲜度）路径行为逐字不变——重构 git log 循环时用既有 `test_gate_freshness.py` 的 code 域用例（`test_stale_pass_reruns_not_ship` 等）回归兜底
- [ ] 2.3 〔grill-amendment 反转边界断言〕反向回归测试：①拍板后普通 subject 触及 design.md 照判失鲜（既有行为）；②**边界用例 `checkpoint(impl-review-fix)`、`checkpoint(impl-reviewX)` 右括号后带尾串 → 不豁免、照判失鲜**（闭合前缀语义：右括号是第二道结构闸，从不由 checkpoint 脚本合法产生的变体不得蹭豁免）
- [ ] 2.4 `ship_gate.py` 头注释：D9 分域段追加豁免规则一句（闭合前缀 `checkpoint(impl-review)`）+「已知不覆盖」追加两条〔grill-amendment〕：①「伪造/手工 checkpoint(impl-review) subject 可绕过失鲜——gate 不核验生产者（显式越权同权级，git 留痕）」；②「拍板后经 impl-review 豁免的四件套编辑不经二次批准即随档 ship（安全边界=约定级『仅装饰性改动』，gate 不做 hunk 分析）」

## 3. B3 归档终态（design D3；Scenario〔B3〕×3）

- [ ] 3.1 新建 `test_gate_terminal.py` 加失败测试 ×6〔grill-amendment：终态判据改 change 域 + 后缀碰撞用例〕：①归档目录**已在 base 树**→SHIPPED exit 0；②归档目录**不在 base 树**（archive commit 停在未并分支）→RUN_VERIFY(next=sdflow-done)；③active 与 archive 均无→REFUSE_START reason 含「change 不存在」；④active 存在 + **精确同名**旧归档并存→active 优先（走既有 pre-flight，不受 archive 干扰）；⑤active 缺席 + 仅存在**后缀撞名**旧档（如查 `demo` 而 archive 只有 `2026-07-04-cross-demo`）→ 锚死日期前缀 glob 不命中 → REFUSE_START「change 不存在」（**非** SHIPPED 误报）；⑥**跨分支不误判**：demo 归档已并 base，HEAD 切到无关未并分支再查 demo → 仍 SHIPPED（**非** RUN_VERIFY——证明判据是 change 域而非全局 branch_state）
- [ ] 3.2 改 `decide()`（`ship_gate.py:192-211`）：git 健全性后、设计门 pre-flight 前插入归档短路分支（cdir 缺席 → **日期前缀锚死 glob `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-{change}`** → **change 域可达性判据**：`git ls-tree <base> -- openspec/changes/archive/<dir>/` 非空 → SHIPPED / 空 → RUN_VERIFY / glob 不命中 → REFUSE_START「change 不存在」；base 无 main/master → UNKNOWN）；**同步把 `ship_gate.py:289` 既有 `archived` 的 `*-{change}` 换成同款锚死 glob**；3.1 全绿
- [ ] 3.3 `ship_gate.py` 头注释契约表：verdict 表 SHIPPED 行补「（含归档后重跑识别）」、REFUSE_START 行补 change 不存在变体；「已知不覆盖」追加同名旧归档误中一条

## 4. 契约同步 + 收尾（proposal「契约文档同步」；design Migration）

- [ ] 4.1 `sdflow-ship/SKILL.md` 链序段核对：REFUSE_START 提示语与新 reason 变体一致（「未过设计门…补锚」与「change 不存在」两分支）；`test_skill_text.py` / `test_anchor_contract.py` 全绿（锚行字面集未动，应零改动通过——若红即契约破坏，停下修）
- [ ] 4.2 全量回归：`pytest sdflow-ship/tests/` 全绿 + 仓级 `pytest` 全绿（307+ 基线不降）
- [ ] 4.3 归档时主 spec 同步核对：`openspec/specs/spec-workflow/spec.md` 窗口语义句按 delta 更新（sdflow-done archive CLI 自动，人工核对不漏）

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
