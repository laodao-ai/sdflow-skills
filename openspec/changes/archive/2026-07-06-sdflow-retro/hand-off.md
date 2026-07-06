# hand-off — sdflow-retro

> 异步人类再入口 + 下个 change 种子。verify PASS 后产出，随归档留档。

## ✅ 完成了什么（锚点已复核存在）

新 skill `sdflow-retro`——只读再生全项目 OpenSpec change 成本×价值复盘（`openspec/retro/report.md`），成本维(git 阶段墙钟) + 价值维(lens-metric 锚)合成一张报告，只呈现不决策。

- **change 边界靠提交路径不靠 tag**：`retro_report.py:boundary_for_change`（查裸 `changes/<name>` ∪ archive 去重排序）+ seed-mass≥3 剔除 + 0/1 守卫。测试 `test_seed_mass_excluded_and_0_1_guard`（反证真哨兵 len==0）、`test_archived_change_full_boundary_via_bare_path`（F1 修复哨兵）。
- **done 靠 path-rename（D8）**：`is_archive_rename`（R 状态 + 目录边界锚定正则，F5 修）。测试 `test_archive_rename_detects_done`。
- **阶段词表最长前缀（D-C）**：`map_stage`（impl-review>review + 补 done-archive/done-verify/gate，F6 修）。测试 `test_map_stage_longest_prefix`。
- **阶段墙钟只到阶段级含人时间（adr/0009）+ 负Δ钳0**：`stage_walltimes`。测试 `test_stage_walltimes_and_negative_clamp`。
- **价值维双源双报告分 layer（D11）**：`lens_value_for_change`（active+archive×spec+code，复用聚合器 parse_report fence-aware + _int 元组解包 + F3 num_bad 传播）。测试 `test_lens_value_active_change_has_anchor`。
- **hr-tg 双列（D10）+ fence-aware + 多锚取最终（F4/F7）**：`hr_tg_flags`/`_read_hr_hit`。测试 `test_hr_tg_two_columns`/`test_hr_tg_skips_fenced_example`/`test_hr_tg_multi_anchor_takes_last`。
- **N≥10 surfacing 机械契约固定前缀（D12）**：`surfacing_block` + `group_key` 共享函数消除 render_table 漂移。测试 `test_surfacing_block_fixed_prefix`/`test_surfacing_groupkey_matches_render_table_on_empty_lens`。
- **报告 view-only 幂等 + 原子写（D13）+ per-change 阶段Δ列（F12）+ 顶部覆盖计数 N/M/K**：`build_report`/`atomic_write`。测试 `test_report_idempotent`/`test_atomic_write_preserves_mode_on_overwrite`（反证哨兵）/`test_build_report_coverage_counts`/`test_build_report_per_change_stage_columns`。
- **级联（workflow-metrics MODIFIED）**：聚合器 `git mv` 进 `sdflow-retro/scripts/`；`init.py` `ignore_patterns("tests")` 保留（F5/G2 铁律，仅 docstring 改）、`test_init` 改指 trivial_shape（41 passed）；maintain 步骤5 薄指针；4 prose+docs 改指 /sdflow-retro；INDEX/README/CLAUDE.md 同步。
- **dogfood**：`openspec/retro/report.md` 实测 覆盖18/有真锚3/边界不可解析2，自身标 in-progress。全仓 453 passed（1 pre-existing B5）。

## ⏳ 未完成 / 延后

**批次 `sdflow-retro`（PLANNED，见 `openspec/issues/batches.md` + `openspec/issues/INDEX.md`）** — code-review 冷主审 defer 的 4 项低危/既有/design-accepted：
- **T58** fence-aware 只支持反引号不支持 `~~~` tilde fence（既有聚合器限制，非本 change 引入；retro 复用 parse_report 连带受益）
- **T59** ≥10 待复评阈值硬编码两处（surfacing_block + render_table）无共享常量（同 group_key 漂移类，低危）
- **T60** `_run_git` 无 returncode 检查，git 失败与真无提交不可区分（design fail-open）
- **T61** build_report/surfacing 包 aggregate 的 except 死防御（glob 缺目录不抛）+ 注释误导

无被延后的 ≥2 方案决策（code-review 所有修复判据客观）。verify Minor 缺口：committed report 相对最新 git 历史 stale = spec 明示接受取舍。

## ▶ 下一阶段建议

- **建议开 cleanup change** 清批次 `sdflow-retro`（T58-T61）。优先级：T58(fence tilde) 与 T59(阈值常量) 都是"防漂移/健壮性"低危，可与其它聚合器改进合批；T60/T61 极低危可随手。均非阻塞。
- **⚠️ 部署激活（重要）**：本 change 触及 bundle（聚合器移出 `assets/workflow/tools/` + init.py 派生逻辑改）+ 新 skill sdflow-retro。**merge 后须 push → 运行 checkout 跑 `/sdflow-upgrade` 激活**（sdflow-done 不代 push）；各消费仓如需拿最新 tools/（聚合器已移出）跑 `sdflow-init update`。
- **本 change 兑现的教训**（值得记进复盘）：冷主审抓到致命 F1（归档 change 丢 pre-archive 历史，17/18 假不可解析）是 SDD 任务 review + dogfood 全放过的——`grill-not-skippable` 再次应验：dogfood"看着过"≠真过。retro 工具自身正是为量化"哪个镜抓到东西"而建，此次它自己的 code-review 数据（致命1/高2）就是首批高价值样本。
