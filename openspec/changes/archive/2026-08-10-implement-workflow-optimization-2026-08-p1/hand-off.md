# Hand-off — implement-workflow-optimization-2026-08-p1

## ✅ 完成了什么

- **reopen 命令**（R-IS1）：`issues_v2.py:612` 新增 `reopen` 子命令，守卫/字段清理/M-2 原子序/自动 reindex/中断残留幂等恢复全落地。锚：12 个契约测试（`test_issues_v2.py`）+ 全仓 2513 passed。
- **实修率历史回算**（R-WR1）：`retro_report.py:333-554` 窄文法提取 + LENS_ENUM 六值映射 + 聚合④段渲染。锚：14+ 专项测试 + 真仓冒烟 + 三轮真语料试算（`impl-reports/task2-fixrate.md`）。
- **token 快照采集**（R-TS1/2/3）：`token_snapshot.py` 271 行 + `checkpoint-commit.sh` 接线。锚：13 个沙盒集成测试 + dogfood 验收（`token-log.jsonl` 8 行真实 anchor=true）。
- **token 列渲染**（R-WR2）：`retro_report.py:639-781` 全局 session 分组差分 + 四计数紧凑串。锚：8+ 专项测试 + 全仓冒烟。
- **收尾集成**：report.md 再生（聚合④ + tokens 列在场）、roadmap task-log 追加 1.B 交付记录、SKILL.md 文档同步。

## ⏳ 未完成 / 延后

本 change 代码审 defer 7 项（均 Minor，见 `code-review-report.md` 台账）：

1. **F1 endswith 子串碰撞**（`retro_report.py:449`）：佐证 flag 的归档目录匹配用 `endswith` 而非 `_DATE_PREFIX` 正则——仅影响展示 flag，不影响实修率数值
2. **OV#2 表格行分类用整行**（`retro_report.py:434`）：`_fr_classify_status(line)` 理论上可被「问题」列中的 needle 误判——真实语料未发现此形态
3. **F2 残留判定单信号**（`issues_v2.py:643`）：手工损坏 closed/ 文件会被误判为残留——design 已接受的简化
4. **OV#1 timeout 覆盖缺口**（`token_snapshot.py:249`）：`_resolve_change_dir` 不在 alarm 窗口内，最坏 ~20s——核心安全约束（不挡 checkpoint）已由 `|| true` + subprocess timeout 满足
5. **OV#5 空 reason 通过**：argparse `required=True` 不拒绝空串
6. **OV#4 SDFLOW_HOME 未尊重**：checkpoint-commit.sh 硬编码 `~/.sdflow/hack/`
7. **F3 docstring 不一致**：`_collect` 声称 `_Timeout` 可上抛但会被内部 `except Exception` 吞

Issues scan：本 change 无新增未闭合 bug/todo（`scan --source-change --status OPEN --status PROPOSED` 返回空）。

CONTEXT.md「实修率」词条：**未经用户确认，未写入**。

## ▶ 下一阶段建议

1. **阶段 1.A 池对账**（roadmap 下一步）：用本 change 交付的 `reopen` 命令重开 T98/T99/T101/T102，逐条跑五问重分诊。建议作为独立操作执行（非 change scope）。
2. **阶段 2 复评拍板**（`implement-workflow-optimization-2026-08-p2`）：本 change 产出的两个判据（per-镜实修率 + per-change token 维）已就绪，阶段 2 可起手。
3. 上方 7 项 defer Minor 可在下一个清理 change 中一并处理，或按优先级逐条 fold 进后续 change。

### ▶ roadmap 回填草稿（workflow-optimization-2026-08#1，关联来源: prefix）

> 助手机械搬运（定位到 phase + 盘面锚），**判断留人**：勾哪几行 / 算不算满足验收标准 / 价值叙述 / 阶段状态 / deferred。

**候选复选框行集（phase 1，请人判断勾哪几行）**：
- [ ] 1.B.1 T108 实修率指标
- [ ] 1.B.2 T104 token 维度量
- [ ] 1.B.3 retro 报告模版增列
- [ ] 1.B.4 recorder 增强 reopen 命令
