# Hand-off — sdflow-retro-cleanup

> 轻量清理批 T58-T61（sdflow-retro 脚本代码质量残差）。2026-07-06。verify=PASS。

## ✅ 完成了什么

（每条附机验锚点，复核锚点确实存在）

- **T58 tilde fence 支持**：`lens_metric_aggregate.py:20` `_FENCE_OPEN` 含 `~{3,}`；`_fence_aware_lines` 追踪 `(marker字符,长度)` 元组、同字符且长度≥开启才闭合。锚点：`test_fence_aware_ignores_tilde_fence`、`test_tilde_fence_not_closed_by_backtick`、`test_backtick_fence_not_closed_by_tilde`（commit `094aeca`）。
- **T59 阈值共享常量**：`lens_metric_aggregate.py:16` `REVIEW_ROUNDS_THRESHOLD=10`，`render_table` + `retro_report.surfacing_block` 均引用同源，消除双处硬编码漂移。锚点：`test_review_rounds_threshold_is_shared_constant`、`test_surfacing_threshold_uses_shared_constant`（commit `1bea68b`）。
- **T60 `_run_git` 失败留痕**：`retro_report.py:48-52` returncode≠0 向 stderr 告警、返回契约不变（区分 git 故障 vs 真无提交）。锚点：`test_run_git_failure_traces_stderr`（commit `4e71708`）。
- **T61 死防御删除 + 显式契约**：`aggregate` 加 is_dir + glob 整扫描阶段「返空不抛」契约，`surfacing_block`/`build_report` 两处不可达死 try/except 删除 + 修误导注释。锚点：`test_aggregate_missing_archive_returns_empty`、`test_aggregate_file_as_root_returns_empty`（commit `9c2c72e`）。
- **code-review 冷主审加挖 4 缺陷全折叠修**（commit `9c2c72e` 之后 sdflow-code-review checkpoint）：
  - 【高】fence 闭合行尾部校验（`line[m.end():].strip()==""`）——此前 `` ``` extra `` 误闭合致状态失同步、漏真锚/混假锚。锚点 `test_closing_fence_with_trailing_content_not_a_close`。
  - 【中】fence 开启缩进 `\s*`→` {0,3}`——≥4 空格缩进代码块此前被误判 fence 吞真锚。锚点 `test_indented_4spaces_not_a_fence`、`test_3space_indent_still_a_fence`。
  - 【中】`aggregate` 「返空不抛」契约扩到覆盖 glob 遍历（对抗镜2 is_dir + codex outside-voice glob 收敛）。锚点 `test_aggregate_is_dir_oserror_returns_empty`、`test_aggregate_glob_oserror_returns_empty`。
  - 【低】surfacing_block docstring 去硬编码 10、引用 `LMA.REVIEW_ROUNDS_THRESHOLD`。
- **验证**：`pytest -W error sdflow-retro/scripts/tests/` → 58 passed 零 warning；dogfood 幂等无漂移、健康仓无 stderr 噪声。

## ⏳ 未完成 / 延后

- **批次 `sdflow-retro-cleanup`**（见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）：
  - **T62**（可观测性·低危）：`_run_git` 留痕在**系统性 git 损坏**下 O(commits) 无节流放大（seed_mass_shas per-sha 调用；仅真故障噪声、非虚警、view-only 不中断）。改法：同一 subcmd 失败去重，或 seed 循环 per-sha 失败聚合成一条。
- **无 ≥2 方案延后决策**（4 项修复方向唯一、均有反证测试客观判据）。
- **verify Minor**：无核心缺口；tasks.md 个别测试名以语义等价的拆分/改名落地（覆盖等同或更强），非缺口。

## ▶ 下一阶段建议

- **T62 优先级低**，可随下一批 sdflow-retro 相关清理或成本优化 roadmap 的 Leg2（降墙钟/可观测）一并处理，不必单开 change。
- 本批已把 sdflow-retro 首版 code-review 的全部 defer 残差（T58-T61）清零；sdflow-retro 脚本层无已知未清缺陷（仅剩 T62 一个低危 DX）。
- 归档后须 push → 运行 checkout `/sdflow-upgrade` 激活（sdflow-retro 脚本变更 + 聚合器 fence 修复对消费仓生效需 `sdflow-init update`）。
