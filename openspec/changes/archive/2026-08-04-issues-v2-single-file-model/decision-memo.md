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

### C8: 并发安全策略——文件名级 O_CREAT|O_EXCL [spec-review-amendment]
- **约束**：`write_issue` 创建新文件时用 `O_CREAT|O_EXCL`（后到者 `FileExistsError` → `next-id` 重试），不需要仓级 `.recorder.lock`
- **证据**：v1 的 T146 记录了并发 `next-id` 竞态的修复历史（O_CREAT+O_EXCL 仓级互斥）；v2 单文件模型下文件名即互斥粒度，结构性简化了并发面——仓级锁的 participant 模式（sweep 嵌套）在 v2 不需要
- **影响**：`add` 原子写从 `.tmp+rename` 改为 `O_CREAT|O_EXCL` 直写目标文件；`set-status`/`reindex` 操作单文件无竞争
- 三镜：系统（复杂度从仓级锁降到文件级 EXCL）> 开发循环（无额外依赖）> 用户（数据安全不退化）。主次：系统复杂度主导

### C9: YAML 序列化策略——手写有界子集 + 值一律双引号 [spec-review-amendment]
- **约束**：frontmatter 写出时 `key: "value"`（双引号包裹，内部 `"` → `\"`），读回匹配 `^key: "(.*)"$` 或 `^key: null$`；不引入 PyYAML 依赖
- **证据**：ADR-0025 明确 reject PyYAML（消费仓零依赖）；真实语料有 5 个 summary 含 `# ` 或 `: ` 等 YAML 敏感字符（如 T73 的 `true # x`），plain scalar 写出会被截断
- **影响**：schema 只有 12 个扁平字段、值都是 string/null，这是有界语法面（基准 5），手写完全可控
- 三镜：系统（零依赖，可控）> 用户（数据不截断）> 开发循环（无需学 PyYAML API）。主次：系统零依赖主导

### C10: sdflow-done sweep 替代——scan --source-change + hand-off 列 ID [spec-review-amendment]
- **约束**：`scan` 补 `--source-change` 过滤参数；`add` 保留 `detect_change` 等价逻辑自动填 `source_change`；sdflow-done 改为 `issues.py scan --json --source-change {change_name} --status OPEN --status PROPOSED`；hand-off 直接列 ID 列表（v2 每个 ID 即文件名，不需要批次号间接引用）
- **证据**：v1 sweep 的核心价值是"给 hand-off 一个批次号引用"，v2 单文件模型下 ID 本身就是引用；scan 是只读操作，天然幂等（不像 sweep 会写 triage/batch）
- **影响**：sdflow-done §2.1 需重写（不是"改调用路径"），但新版更简单

## 候选方案对照 [spec-review-amendment]

| 候选 | 描述 | 否决理由 |
|------|------|---------|
| A. 维持现状 + 仅合一脚本 | 保留多条目大文件，只把三脚本合为一个 | 不解决行级精确解析和双写一致性问题（proposal Why #1），合一后仍需维护 POOL_SPEC 注入模式 |
| **B. 单文件模型（当前方案）** | 一个 issue 一个 .md + 合一脚本 + 砍 batch | 系统镜最优（消除行级解析、双写一致性、POOL_SPEC 复杂度）；代价是 287 个小文件（当前量级无性能问题） |
| C. SQLite | 结构化存储 | 不符合纯文件管理定位（proposal Non-Goals #1）；消费仓无 sqlite3 保证；git diff 不可读 |

## 拍板决策

### D1: 不保留 batch 机制
- 规划用 roadmap 替代，`batch` 字段不进 v2 schema
- 用户在 explore 阶段拍板
- [spec-review-amendment] 34 个 PLANNED 批次的成员/优先级/计划文本在迁移时搬入对应 issue body，不裸删
