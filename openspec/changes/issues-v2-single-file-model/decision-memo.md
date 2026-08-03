---
schema_version: "1"
change: issues-v2-single-file-model
branch: feat/issues-v2-single-file-model
generated_at: "2026-08-03T21:40:15+0800"
decision_hash: "cc450ea4b705"
---

# Decision Memo: issues-v2-single-file-model

## 承重约束

### C1: 全量拆分——open 和 closed 均为单文件模型
- **约束**：迁移时所有 issue（含已关闭）全部拆成单个 .md 文件，`closed/` 不保留旧多条目格式
- **证据**：用户拍板"如果工作量不大的话，可以全量迁移"
- **影响**：runtime 脚本只需处理一种格式（单文件 frontmatter），reindex 逻辑统一

### C2: 不兼容旧格式，提供独立迁移工具
- **约束**：v2 脚本不读旧格式；提供一次性迁移脚本 `migrate_issues.py` 供所有项目仓使用
- **证据**：用户"不用兼容，提供一个工具对项目仓的历史数据进行迁移"+"不只是考虑当前仓，要考虑项目仓的情况，所以需要一个独立工具"
- **影响**：v2 脚本复杂度降低；迁移脚本需解析两种旧格式（legacy 表格 + frontmatter overlay）

### C3: sdflow-done 同步更新
- **约束**：sdflow-done 的 sweep 调用同步改为 v2 接口
- **证据**：用户"sdflow-done 也更新一下"

### C4: B/T ID 序列保持分开，扫文件名取 max+1
- **约束**：bug 用 B 前缀，todo 用 T 前缀，各自独立编号；next-id 扫 `open/` + `closed/` 文件名
- **证据**：用户同意推荐

### C7: frontmatter schema 定稿
- **约束**：字段集 = `id`, `pool`, `status`, `priority`(bug only), `type`(todo only), `date`, `source_change`, `module`, `summary`, `resolved_by`(关闭时), `closed_date`(关闭时), `closed_reason`(WONTFIX/WONTDO 必填)
- 砍 `time`（日期粒度够用）和 `batch`（D1）
- 终态按池分：bug→FIXED/WONTFIX，todo→DONE/WONTDO
- **证据**：用户同意推荐

### C6: body 自由格式，脚本只读写 frontmatter
- **约束**：frontmatter 下方的 body 是自由 Markdown，脚本不解析；迁移时原 marker block 内容搬到 body
- **证据**：用户同意

### C5.5: set-status 终态自动移文件，不支持 reopen
- **约束**：`set-status --to FIXED/WONTFIX/DONE/WONTDO` 自动填充关闭字段并 `git mv open/ → closed/`；不提供 reopen 命令
- **证据**：用户同意

### C5: 合一脚本架构
- **约束**：`buglist.py` + `todolist.py` + `issues.py` 合为单个 `issues.py`，`--pool` 区分；旧入口不保留薄壳
- **证据**：用户"同意合一"
- **影响**：消费方（sdflow-done、SKILL.md、测试）统一改为调 `issues.py`

## 拍板决策

### D1: 不保留 batch 机制
- 规划用 roadmap 替代，`batch` 字段不进 v2 schema
- 用户在 explore 阶段拍板
