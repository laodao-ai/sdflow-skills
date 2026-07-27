# Task 4 fix1 standards 回归修复报告

## 结果

已关闭 standards reviewer 的三个 Important；未修改 `proposal.md`、`design.md`、`specs/`、`tasks.md` 或
`superpowers-plan.md`，未创建 `checkpoint(harden-sdflow-spec-followups:task4-...)` 提交，也未纳入五个
未跟踪的 review package diff。

## 修复与回归

1. `inject()` 仅在 content 以 `<!-- sdflow:principles:start` 开头时保留 nested principles 所需的
   分隔空行；普通 `MARK_IDX` 布局恢复紧邻格式。回归同时覆盖 nested 与 ordinary index 两侧；
   `python3 sdflow-init/scripts/init.py update --root . --dev` 已将 `openspec/INDEX.md` 的无关空行收回。
2. `copy_bundle()` 的 ignore callback 只在 source 正好为 `BUNDLE_SRC/tools` 时排除 `tests`；full
   bundle 的其他层级 `tests` 会保留，且仍会删除 `dst/tools/tests` 的历史遗留副本。
3. 非 POSIX 时 `run_preflight()` 不调用 `which` 或 Claude CLI；`claude-version` 与 `agents-json`
   均显式返回 `未执行：POSIX gate 未通过`，整体仍 fail-closed 为 `preflight-error`。

## 验收记录

| 项目 | 结果 |
| --- | --- |
| RED | 三条新增 public-seam 回归在修复前均失败，分别命中空行、过宽 tests 忽略、PATH 误报。 |
| GREEN | 三条新增回归 `3 passed`；受影响 focused 集 `16 passed in 0.23s`。 |
| 规则与规格门 | `python3 hack/sync_principles.py --check` 通过（22 个投放面）；`openspec validate --all --strict` 通过（21 passed）；`git diff --check` 通过。 |
| dogfood / setup | `python3 sdflow-init/scripts/init.py update --root . --dev` 与 `bash setup.sh` 通过；清除本次生成的 13 项未跟踪 workflow rules。 |
| 安装机械比对 | `~/.sdflow/workflow`、Codex `sdflow-init` 均链接到源；安装的 `outside-voice-job.py` 与源字节一致。 |
| 全量 pytest | fix agent 的首次前台通道在 35% 脱离，未取得退出码，因此未作为通过证据。主 session 随后在同一 `656c5c1` 盘面运行唯一补证命令 `uv run --with pytest pytest -q`，持续轮询同一 session 至完成：**2846 passed, 11 skipped, 3 xfailed in 285.92s，exit 0**。 |
