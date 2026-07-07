# hand-off — issues-pool-hardening（2026-07-07）

## ✅ 完成了什么（均有 verify 锚点）

issues 池三 recorder（buglist/todolist/issues）盘面完整性 + 可观测性 + 幂等健壮化（T1-T5 + spec-review OV-1/2/3）：

- **T2 总览管道表 table-cell-safe 写时 reject**（全写路径覆盖）：`_reject_cell_unsafe` 挂各命令**入口原始参数**（非 join sink，C1 BLOCKER）——cmd_add(module/summary/change/batch/time/id/**title/source**)、cmd_triage(batch)、_retag(new_key)、**cmd_set_status(evidence/reason/date/month)**、batch_add(优先级/计划)。OV-2 batch key slug（拒 `|`/换行/` — `/空/首尾空白）。OV-3 id `fullmatch([A-Z]\d+)`+查重+**scan 跨文件 dup**。
- **T1** reindex problems 回显 stderr + `--strict`（预置接口）+ **OV-1 scan 行 arity** 检测（读侧盘面完整性）；`_echo_problems` 在 reindex + rename auto-reindex 两处复用。
- **T3** 终态集跨脚本+内联字面量一致性守卫测试（含 cmd_scan 严格 == 抠取，真锁漂移）。
- **T4** `batch add --if-exists skip`=skip-with-warn（零字段比较）+ rename auto-reindex（抽 `_reindex_core`，失败吞-warn+exit0）。
- **T5** `_find_row_file` 各 recorder 内抽（behavior-preserving，D4 无跨模块共享）。
- **doc-sync** 三 SKILL.md rename 段同步 auto-reindex + 订正「无副作用」过时措辞。

**质量**：SDD 10 任务（含 Task4/Task6 各 1 fix 轮）+ **whole-branch code-review 冷主审自动修 6 项 [impl-review-fix]**（cold review 抓到 SDD 任务审全放过的真 bug：set-status 块注入静默截断 / scan 跨文件 dup / 空 batch key 僵尸 / rename 丢 problems / 优先级计划注入 / cmd_add title/source 未守 C7）。全仓 **552 passed**（基线 480 + 72 新测试）。verify=PASS，诚实性 gate 通过。

## ⏳ 未完成 / 延后

- **批次 `issues-pool-hardening`**（`openspec/issues/batches.md` / `INDEX.md`）——本 change code-review defer 的 2 项：
  - **T66**（性能优化）：cmd_scan 对同批行双切（OV-1 arity + OV-3 dup 可合一次循环）；batch rename 跑两次 read_pool（4 子进程 scan）可优化。
  - **T67**（代码质量）：显式 id 前导零歧义（`B007`≠`B7` 共存，人工识别混淆，置信 55）。
- **T2.5（延迟绑定 follow-up，行为面）**：`sdflow-done` sweep 调 `reindex --strict`——触 `sdflow-done/SKILL.md`（行为面 + 别 capability），故本 change 只交付 `--strict` 预置接口 + scan arity 检测（读侧当场生效），**enforcement 价值待此 follow-up wire 消费者才落地**（诚实降级，见 adr/0010 + Q1）。
- **对抗B-F2（记注非缺陷）**：rename auto-reindex 的 `except Exception` 偏宽、不分数据一致性 vs 基础设施故障（磁盘满/权限）——design/D2 明确拍板取舍，若未来要收紧可对 OSError/PermissionError 单独处理。

## ▶ 下一阶段建议

1. **roadmap「去字符串化机器状态层」**（`sdflow-roadmap` 建）——两阶段：Path B（recorder 索引层结构化 = YAML frontmatter 索引 + prose 块，让 T2 腐蚀类整个蒸发、删大片表解析机械）+ T65（gate 状态锚迁 frontmatter）。本 change 的 reject 是其低成本前置桥（adr/0010）。**触发时机**：recorder 持续出同类 bug、或想在数据上建工具时才值那次迁移。
2. **T2.5**：wire `sdflow-done` sweep 用 `reindex --strict`——让 --strict enforcement + scan arity 检测凑成完整的"收尾抓不一致"。小改，随下次触碰 sdflow-done 顺手带。
3. **批次 issues-pool-hardening（T66/T67）**：低优先，随任何触碰 recorder 的 change 搭便车清。
