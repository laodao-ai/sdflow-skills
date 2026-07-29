# Task 1 实现报告：编码卫生机械门

## 交付

- 新增只读检查器 `hack/check_encoding_hygiene.py`。
  - 扫描 `hack/**/*.py`、`sdflow-*/scripts/**/*.py` 及 canonical bundle 的
    `sdflow-init/assets/{hack,hooks,workflow/tools}/**/*.py`。
  - 仅检查包含 `if __name__ == "__main__":` 的入口脚本；测试目录被排除，
    `openspec/workflow/tools/` 仅以相对仓根路径前缀排除。
  - 通过 AST 对整份文件分别识别 stdout `reconfigure`、stderr `reconfigure` 和
    `errors="replace"`；不存在行数窗口。
  - 失败时逐文件列出缺少的契约，并输出指向 `CLAUDE.md` 模板的 `修：` 行。
  - 不提供 `--apply`；任何 CLI 参数都会被明确拒绝。
  - 检查器自身在模块顶层含同一前导，并被回归测试自证。
- 新增常驻回归测试 `hack/tests/test_encoding_hygiene.py`（8 项）：完整前导、完全缺失、
  缺 stderr、缺 replacement、canonical 源/托管镜像同尾路径、190 行后前导、检查器自证、
  `--apply` 拒绝。
- 在 `CLAUDE.md`「修改本仓库的注意」补充入口脚本前导模板；失败输出直接指向该位置。

## TDD 记录

1. 先新增“完整前导判绿”测试；运行 `python -m pytest hack/tests/test_encoding_hygiene.py -q`
   在 collection 阶段因 `check_encoding_hygiene` 不存在而失败。
2. 实现最小检查器后，该测试通过。
3. 先新增“`--apply` 必须拒绝”测试；它因检查器错误地继续扫描仓库而失败。
4. 加入裸调用参数守卫后，该测试通过。

## 初始真实扫描

执行 `python hack/check_encoding_hygiene.py` 后退出码为 1，检查器自身通过，发现恰好 28 个
缺失前导的既有入口脚本，集合为：

```text
hack/check_async_branch_parity.py
hack/check_codex_efficacy_evidence.py
hack/check_tier_resolution_parity.py
hack/gen_workflow_guide.py
hack/sync_principles.py
sdflow-architecture/scripts/sad_lint.py
sdflow-architecture/scripts/sad_scaffold.py
sdflow-devenv/scripts/devenv_lint.py
sdflow-devenv/scripts/devenv_scaffold.py
sdflow-done/scripts/roadmap_writeback_draft.py
sdflow-implement/scripts/impl_route.py
sdflow-init/assets/hack/outside-voice-job.py
sdflow-init/assets/hooks/ff0-branch-guard.py
sdflow-init/assets/workflow/tools/anchor_lint.py
sdflow-init/assets/workflow/tools/hr_tg_intersect.py
sdflow-init/assets/workflow/tools/lens_metric_emit.py
sdflow-init/assets/workflow/tools/outside_voice_guard.py
sdflow-init/assets/workflow/tools/review_disposition_check.py
sdflow-init/assets/workflow/tools/trivial_shape.py
sdflow-init/scripts/init.py
sdflow-issues/scripts/buglist.py
sdflow-issues/scripts/issues.py
sdflow-issues/scripts/migrate_legacy.py
sdflow-issues/scripts/todolist.py
sdflow-maintain/scripts/maintain_scan.py
sdflow-retro/scripts/lens_metric_aggregate.py
sdflow-retro/scripts/retro_report.py
sdflow-ship/scripts/ship_gate.py
```

该集合供后续 Task 2 逐个注入前导；本票不修改这些入口文件。

## 验证

- `python -m pytest hack/tests/test_encoding_hygiene.py -q` → `8 passed`
- `python -m py_compile hack/check_encoding_hygiene.py` → 通过
- `git diff --check` → 通过
- `python hack/check_encoding_hygiene.py` → 按设计为红，完整报出上述 28 个真实缺失项及修复指针。

未运行全仓 `pytest`；本票完成前的后续任务仍会让新门保持预期红态，直至 Task 2 注入全部前导。
