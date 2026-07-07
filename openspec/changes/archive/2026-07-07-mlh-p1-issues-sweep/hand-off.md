# hand-off — mlh-p1-issues-sweep

> roadmap `mechanical-layer-hardening` 阶段 1（Leg1 脚本化开路）。verify PASS 后产出，随归档留档。

## ✅ 完成了什么（每条附机验锚点）

- **`issues.py sweep --change X` 原子子命令**（commit `98f3a66`）：入口守卫（非空 + `_reject_batch_key_unsafe`，先于写盘）→ `scan --change X --open-ungrouped`（非终态∧批次空）→ 逐项 subprocess `triage`（查 returncode）→ `batch add --if-exists skip` → `reindex`。全子步 subprocess CLI（不直调 cmd_*，D4 隔离）。测试 `test_sweep_open_ungrouped`/`idempotent`/`rejects_empty_change`/`excludes_orphans`/`triage_fail_closed`/`rerun_converges`/`reindex_fail_closed`。
- **SKILL 文档同步**（commit `56bf12c`）：`sdflow-done/SKILL.md` §2.1 手循环 → 一行 sweep（+设计原则汇总段同步）；`sdflow-issues/SKILL.md` 命令面补 sweep 段。
- **code-review 5 源冷审自动修 7 项**（commit `364bc39`，`[impl-review-fix]`）：F1 problems 透传（scan problems 回显 + reindex stderr 透传）· F2 0 命中不建僵尸批次 · F3「原子」措辞订正 · F4 scan+batch-add fail-closed 补测 · F5 首尾空白拒 · F6 reindex 测试断言加固 · F7 done 设计原则同步。新增 4 测试。
- **verify PASS**（opus 冷启独立复跑 **102 passed**，4 Scenario 逐条附锚，见 verify-report.md）。
- **dogfood 确认**：本 change 自身 sweep（0 项）→ `tagged 0 项，跳过 batch add/reindex`，无僵尸批次（F2 实测生效）。

## ⏳ 未完成 / 延后

- **正式 defer：0 项**（code-review 无 genuinely 拿不准的，全部当场修）。本 change 未新增 buglist/todolist；issues sweep 子步 0 命中、无批次。
- **既有非本 change 引入（一行带过留痕，未新建条目）**：① subprocess `text=True` 未显式 `encoding="utf-8"`（`repo_root`/`_scan_pool`/`read_pool` 同款既有模式，非 UTF-8 locale 窄触发）——可未来统一改；② sweep spawn-heavy（4+N 子进程）与 T66「subprocess 计数放大」同主题，是 D4「逐项精确报失败点位」的刻意取舍，非缺陷。
- **明确归后续（非本 change scope）**：`reindex --strict` enforcement（sweep 遇 problems 即失败，而非本次的「不吞可见」）= roadmap **T2.5**（触 sdflow-done 行为面，延迟绑定）。
- **verify Minor**：缺一条「已分批项不被 clobber」的专门断言测试（实现层 `not batch` 过滤已保证，orphan 测试覆盖的是源为空孤儿）——可选补，不阻断。

## ▶ 下一阶段建议

- **发布边界**：本 change 是 toolkit 源仓改动。merge 后须 push → 运行 checkout `/sdflow-upgrade`（pull+setup）激活 sweep skill；**消费仓**若要让 done §2.1 用上 sweep 命令，须在该仓跑 `sdflow-init update`（否则 done SKILL 引用的 `~/.claude/skills/sdflow-issues/scripts/issues.py sweep` 在旧版报 invalid choice——本次 dogfood 已实证此 install-timing）。
- **roadmap 下一阶段**：阶段 2 = **P2 anchor-lint**（复用 `lens_metric_aggregate.parse_anchor` 校验度量锚，高频门禁）；或阶段 3 = P3 确定性守卫（recorder 镜像一致性测试 + config/batches lint）。见 `openspec/roadmaps/mechanical-layer-hardening/roadmap.md`。
- **T2.5**（sweep 用 `reindex --strict`）可随阶段推进或单独小 change 兑现——本 change 已把 sweep 建好，T2.5 只需把末步 reindex 换 `--strict` + 补一条「pool 有 problems → sweep 非零」测试。
