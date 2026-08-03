# Hand-off: issues-v2-single-file-model

## ✅ 完成了什么

- **核心脚本 issues_v2.py**（1145 行）：add/set-status/scan/reindex/next-id/migrate 六命令，O_CREAT|O_EXCL 并发保护，YAML 手写有界子集双引号序列化，零 PyYAML 依赖（锚：`sdflow-issues/scripts/issues_v2.py`，55 测试绿 `sdflow-issues/tests/test_issues_v2.py`）
- **迁移工具**：双格式解析（legacy 表格 + frontmatter overlay）+ shadow 去重 + 字段映射 + PLANNED 批次信息迁移（锚：`test_issues_v2.py` 14 条迁移测试）
- **本仓数据迁移**：287 issue 全部迁移（open 156 + closed 131），v1 三脚本 + sdflow_issues_core 2175 行包 + 17 个格式耦合测试文件已删除（锚：`checkpoint(issues-v2-single-file-model:task3-data-migration)`）
- **12 消费方更新**：SKILL.md/sdflow-done/CLAUDE.md/README.md/AGENTS.md/claude-section.md/CONTEXT.md/3 个 delta spec/CI workflow/hack test（锚：`checkpoint(issues-v2-single-file-model:task4-consumers)`，全仓 2471 passed）
- **代码审修复**：resolved_by 正则误匹配修复 + 7 条被污染数据修正（锚：`checkpoint(impl-review): 多镜代码审自动修复`）

## ⏳ 未完成 / 延后

双轴审 + 代码审 defer 到 todolist 的 Minor 项：
- 并发 set-status 同 ID 的错误路径未保护（设计已承认的无仓级锁取舍）
- set-status 三处 git 子进程缺 timeout 保护
- os.rename 失败分支无结构化异常处理
- exit code 1 vs 2 不一致
- cmd_add 缺并发 N 进程端到端压力测试
- generate_index_md/generate_closed_md 重复逻辑（DRY）
- closed_reason 提取来源偏差（历史行 note vs marker block reason）

## ▶ 下一阶段建议

以上 defer 项均为 Minor，无需立即开 cleanup change。建议：
1. 在消费仓（如有）执行 `python3 issues_v2.py migrate --root .` 完成迁移
2. 之后可开一个轻量 cleanup change 处理上述 Minor 项（优先级低）
