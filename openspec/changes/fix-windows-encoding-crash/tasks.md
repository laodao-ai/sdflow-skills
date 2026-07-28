## 1. 检测器先行（`decision-memo.md` D5：用检测器输出驱动后续注入，不手工枚举）

- [ ] 1.1 新增 `hack/check_encoding_hygiene.py`：扫描目标 glob（`hack/**/*.py` + `sdflow-*/scripts/**/*.py` + `sdflow-init/assets/{hack,hooks,workflow/tools}/**/*.py`，排除 `**/tests/**` 与 `openspec/workflow/tools/**`），对每个含 `if __name__ == "__main__":` 的文件做存在性检查（前几行是否含 `reconfigure(encoding=`），无 `--apply`，裸调用仿 `check_async_branch_parity.py` 模式（对应 Requirement: 新增机械门守护 reconfigure 前导块的存在性）
- [ ] 1.2 脚本自身从第一行起即带 reconfigure 前导（自证满足自己的规则，design.md Risks 第 4 条）
- [ ] 1.3 跑一遍 `python3 hack/check_encoding_hygiene.py`，记录当前缺失清单（即第 2 节要处理的真实文件集合，覆盖并核对是否等于本轮 grill 实测的 27 个入口脚本）

## 2. 27 个入口脚本注入 reconfigure 前导（对应 Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃）

- [ ] 2.1 按 1.3 的缺失清单，逐文件在顶部（`import sys` 之后、首个业务逻辑之前）插入 4 行前导：
      ```python
      for _s in (sys.stdout, sys.stderr):
          try: _s.reconfigure(encoding="utf-8", errors="replace")
          except Exception: pass
      ```
- [ ] 2.2 `hack/*.py`（`sync_principles.py` / `gen_workflow_guide.py` / `check_async_branch_parity.py` / `check_tier_resolution_parity.py` / `check_codex_efficacy_evidence.py` 等）
- [ ] 2.3 `sdflow-architecture/scripts/*.py`（`sad_lint.py` / `sad_scaffold.py`）
- [ ] 2.4 `sdflow-devenv/scripts/*.py`（`devenv_lint.py` / `devenv_scaffold.py`）
- [ ] 2.5 `sdflow-done/scripts/roadmap_writeback_draft.py`
- [ ] 2.6 `sdflow-implement/scripts/impl_route.py`
- [ ] 2.7 `sdflow-init/scripts/init.py` + `sdflow-init/assets/hack/outside-voice-job.py` + `sdflow-init/assets/hooks/ff0-branch-guard.py`
- [ ] 2.8 `sdflow-init/assets/workflow/tools/*.py`（`anchor_lint.py` / `hr_tg_intersect.py` / `lens_metric_emit.py` / `outside_voice_guard.py` / `review_disposition_check.py` / `trivial_shape.py`——**只改源，不手改 `openspec/workflow/tools/` 镜像**，`decision-memo.md` C5/D4）
- [ ] 2.9 `sdflow-issues/scripts/*.py`（`buglist.py` / `issues.py` / `todolist.py`）
- [ ] 2.10 `sdflow-maintain/scripts/maintain_scan.py`
- [ ] 2.11 `sdflow-retro/scripts/*.py`（`lens_metric_aggregate.py` / `retro_report.py`）
- [ ] 2.12 `sdflow-ship/scripts/ship_gate.py`
- [ ] 2.13 重跑 `python3 hack/check_encoding_hygiene.py`，确认缺失清单归零

## 3. subprocess / write_text 编码补全（对应 Requirement: subprocess 文本解码与文件写入 SHALL 显式声明 UTF-8 编码）

- [ ] 3.1 16 处 `subprocess ... text=True` 补 `encoding="utf-8", errors="replace"`（`devenv_scaffold.py` ×2、`roadmap_writeback_draft.py`、`impl_route.py`、`outside-voice-job.py`、`ff0-branch-guard.py`、`sdflow-init/assets/workflow/tools/trivial_shape.py`、`init.py`、`issues.py` ×4、`retro_report.py`、`ship_gate.py` ×2；`migrate_legacy.py:321` 已有，跳过）
- [ ] 3.2 2 处 `write_text()` 补 `encoding="utf-8"`（`hack/check_codex_efficacy_evidence.py:418`、`sdflow-devenv/scripts/devenv_scaffold.py:59`）

## 4. `openspec/workflow/tools/` 镜像同步（对应 Requirement: 入口脚本 SHALL NOT 因 stdout/stderr 编码崩溃）

- [ ] 4.1 跑 `python3 sdflow-init/scripts/init.py update --root .`，确认 `openspec/workflow/tools/*.py` 随源刷新，`diff -rq openspec/workflow/tools sdflow-init/assets/workflow/tools` 除 `tests/` 外零差异

## 5. `setup.sh` 接线新机械门（对应 Requirement: 机械门 SHALL 准确报告真实一致性状态，不因编码问题产生假红）

- [ ] 5.1 在 `setup.sh` 现有四道门之后，独立接入 `hack/check_encoding_hygiene.py`（不挂在其它门的条件分支下，同 `check_async_branch_parity.py` 的独立守卫写法）
- [ ] 5.2 本机 `bash setup.sh` 全程无 `UnicodeEncodeError`，五道机械门全部报告真实状态

## 6. CI 扩面与真实子进程验证（对应 Requirement: 机械门 SHALL 准确报告真实一致性状态，不因编码问题产生假红）

- [ ] 6.1 `.github/workflows/windows-recorder-smoke.yml` 的 `paths:` 从 3 条扩到本次改动覆盖的全部脚本目录（`hack/**`、`sdflow-architecture/scripts/**`、`sdflow-devenv/scripts/**`、`sdflow-done/scripts/**`、`sdflow-implement/scripts/**`、`sdflow-init/assets/**`、`sdflow-issues/**` 已含、`sdflow-maintain/scripts/**`、`sdflow-retro/scripts/**`、`sdflow-ship/scripts/**`）
- [ ] 6.2 新增一个 job 步骤：`PYTHONIOENCODING=gbk bash setup.sh` 真实子进程运行，断言退出码 0 且输出不含 `UnicodeEncodeError`
- [ ] 6.3 新增一个 job 步骤：`PYTHONIOENCODING=gbk python3 sdflow-init/scripts/init.py update --root .`（在临时 checkout 或 `--root` 指向一个已铺设的测试目录）真实子进程运行，断言退出码 0

## 7. 回归验证

- [ ] 7.1 本仓既有 pytest 套件全绿（`pytest`，仓根 rootdir）
- [ ] 7.2 `openspec validate "fix-windows-encoding-crash" --strict --type change` 通过
- [ ] 7.3 人工核对 `hack/check_encoding_hygiene.py` 的负向用例：新建一个刻意遗漏前导的临时脚本，确认被拦下后删除该临时脚本

## 测试覆盖图（TG-18）

| Code Path | 测试类型 | 对应任务 |
|---|---|---|
| 27 个入口脚本 stdout/stderr reconfigure | `check_encoding_hygiene.py` 存在性检查（机械门，非传统单测） | 1.1, 1.3, 2.13 |
| `check_encoding_hygiene.py` 自身检测逻辑 | 负向用例（人工核对，7.3） | 7.3 |
| `subprocess text=True` 解码 | 现有 pytest 套件中涉及 subprocess 调用的用例（间接覆盖，non-UTF-8 locale 需真机/CI 验证） | 7.1, 6.2 |
| `write_text()` 编码 | 现有 pytest 套件中涉及产出文件读写的用例（间接覆盖） | 7.1 |
| 四道既有机械门 + `init.py` 在 GBK 环境下的真实行为 | CI 真实子进程验证（pytest capsys 无法复现，见 `design.md` Risks） | 6.2, 6.3 |
| `setup.sh` 五道机械门整体接线 | 本机手动 `bash setup.sh` 全跑 + CI 6.2 | 5.2, 6.2 |
