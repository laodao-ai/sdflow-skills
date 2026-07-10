# 领域文档

本仓库采用单一上下文布局。Engineering skills 在探索代码库或产出工作项前，按任务范围读取以下文档：

- `openspec/CONTEXT.md`：跨 change 复用的领域术语、边界和约束。
- `openspec/adr/`：与当前工作区域相关的架构决策记录。

本仓不使用 `CONTEXT-MAP.md`，也不需要查找多个上下文目录。

## 使用规则

- 在工作项标题、设计、假设或测试名称中，使用 `openspec/CONTEXT.md` 已定义的术语，避免无意引入同义词。
- 若输出与既有 ADR 冲突，显式指出冲突及重新评估的理由，不要静默推翻原决策。
- 新增或调整稳定的领域术语时，更新 `openspec/CONTEXT.md`；新增或调整架构取舍时，在 `openspec/adr/` 新增或更新相应记录。
- 若上述文件在某个分支或历史版本中暂不存在，继续当前工作，不因缺失而阻塞。

## 文件结构

```text
openspec/
├── CONTEXT.md
├── adr/
└── matt/
    ├── issue-tracker.md
    ├── triage-labels.md
    └── domain.md
```
