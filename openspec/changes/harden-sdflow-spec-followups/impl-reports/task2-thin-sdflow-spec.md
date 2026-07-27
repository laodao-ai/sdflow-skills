# Task 2 实现报告：薄化 `sdflow-spec` 常驻入口

## 状态

DONE

## 实现结果

- `sdflow-spec/SKILL.md` 从 21,186 缩至 16,972 个 Python Unicode 字符，保留 frontmatter、完整四条通则、
  Phase 0/A/B/C、C.1 四判、终审、strict validate、两个 checkpoint 和出口三步。
- 默认阶段一继续由主 session 亲查、亲写；未启用外派协议移到
  `references/delegation-protocol.md`，详细失败诊断继续由 `references/degradation-ladder.md` 承载，
  演进依据与 T132 未来输入契约移到 `references/evolution-notes.md`。入口为三类资料分别保留明确加载条件和可达相对链接。
- Codex 文案只记录本 session 已观察到用户显式触发被接受、没有模型可调用的 Skill 执行面；未把接口缺席写成机械拒绝。
- 终审明确以整个 change 目录为追溯边界；被砍候选与理由只存在于 `decision-memo.md`、
  `design.md` 仅保留一行纪要指针均为合法形态。
- T132 只记录未来 gate 的 A/B 输入：A = 有效 memo + `checkpoint(sdflow-spec-grill)`；
  B = `checkpoint(grill)` 或认可的 `sdflow:grill-done`。未实现 gate，状态保持 OPEN。

## TDD 记录

公共 seam：安装后由宿主读取的 `sdflow-spec/SKILL.md` 与它按条件加载的 versioned references。

- RED：`uv run --with pytest pytest hack/tests/test_sdflow_spec_resident_contract.py -q`
  - 结果：`6 failed`。
  - 失败覆盖：21,186 字符超限、常驻终审语义缺口、三类 reference 路由缺失、Codex 边界缺失、
    change 目录追溯边界缺失、T132 reference 不存在。
- GREEN：同命令在实现后为 `7 passed`。
- 既有外派契约测试改为读取按需 reference，不再误要求完整协议常驻入口；扫描器、派发参数、
  model 枚举与降级边界断言保持原语义。

## 验证

- `uv run --with pytest pytest hack/tests/test_sdflow_spec_resident_contract.py hack/tests/test_sdflow_spec_agents.py hack/tests/test_sdflow_spec_failure_modes.py hack/tests/test_decision_memo_gate.py hack/tests/test_sync_principles.py hack/tests/test_checkpoint_slug_coverage.py hack/tests/test_canonical_entry_sync.py -q`
  - `129 passed in 9.63s`
- `python3 hack/sync_principles.py --check`
  - `22 个投放面全部与真相源一致`
- `openspec validate harden-sdflow-spec-followups --strict`
  - `Change 'harden-sdflow-spec-followups' is valid`
- `git diff --check`
  - 通过
- Python `len(Path("sdflow-spec/SKILL.md").read_text(encoding="utf-8"))`
  - `16972`

## 范围边界

- 未修改 `proposal.md`、`design.md`、`specs/`、`tasks.md` 或 `superpowers-plan.md`。
- 未实现或关闭 T132，未更新问题台账，未执行 T239 下游 rollout，未启用外派。
- Task 1 的两个未跟踪 review package 原样保留，不纳入本票提交。
