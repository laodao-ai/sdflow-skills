# ship-gate-hardening — Tasks

> 需求追溯：全部任务对应 `specs/spec-workflow/spec.md` MODIFIED Requirement「阶段三编排台账确定性（ship_gate）」下的三组 Scenario——〔B1〕窗口闭区间、〔B2〕尾流修订豁免、〔B3〕归档终态。设计决策 = design.md D1-D4。

## 1. B1 窗口闭区间（design D1；Scenario〔B1〕×2）

- [ ] 1.1 `test_gate_impl_progress.py` 加失败测试：plan 与 `checkpoint(task1-<slug>)` 同 commit 的盘面，断言 task1 计入 done_tasks、齐 N 不误报 CONTINUE_IMPL〔Scenario: plan 与首个 task 锚同 commit 不漏数〕
- [ ] 1.2 改 `done_task_ids`（`ship_gate.py:155-167`）：追加解析 `git log -1 --format=%s <sha>` 自身 subject（同 `startswith` + `TAG_RE.match` 规则），窗口语义变闭区间 `[sha, HEAD]`；1.1 转绿
- [ ] 1.3 回归：plan 单独提交的既有路径用例保持绿（不多数、不少数）〔Scenario: 前置产物缺失点名〕

## 2. B2 尾流修订豁免（design D2；Scenario〔B2〕）

- [ ] 2.1 `test_gate_freshness.py` 加失败测试：design-approved 后 subject 前缀 `checkpoint(impl-review` 的提交触及 design.md+tasks.md，断言不失鲜、不 REFUSE_START〔Scenario: 阶段三合法尾流修订不失鲜〕
- [ ] 2.2 改 `is_stale`（`ship_gate.py:77-96`）design 域：git log 改带 subject 分帧遍历，字面前缀 `checkpoint(impl-review` 的 commit 跳过失鲜判定；2.1 转绿
- [ ] 2.3 反向回归测试：拍板后普通 subject 触及 design.md 照判失鲜（既有行为）；前缀边界用例（如 `checkpoint(impl-review-fix`、`checkpoint(impl-reviewX` 均属前缀命中——字面 startswith 语义）明确断言
- [ ] 2.4 `ship_gate.py` 头注释：D9 分域段追加豁免规则一句 +「已知不覆盖」追加「伪造 checkpoint(impl-review subject 可绕过失鲜（显式越权同权级，git 留痕）」

## 3. B3 归档终态（design D3；Scenario〔B3〕×3）

- [ ] 3.1 新建 `test_gate_terminal.py` 加失败测试 ×4：①归档+已并→SHIPPED exit 0；②归档+未并→RUN_VERIFY(next=sdflow-done)；③active 与 archive 均无→REFUSE_START reason 含「change 不存在」；④active 存在 + 同名旧归档并存→active 优先（走既有 pre-flight，不受 archive 干扰）
- [ ] 3.2 改 `decide()`（`ship_gate.py:192-211`）：git 健全性后、设计门 pre-flight 前插入归档短路分支（cdir 缺席 → archive glob → branch_state 分派 SHIPPED / RUN_VERIFY / REFUSE_START「change 不存在」）；3.1 全绿
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
