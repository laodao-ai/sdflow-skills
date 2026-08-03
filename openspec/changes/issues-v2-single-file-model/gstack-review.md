<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- 佐证：autoplan 经 Skill 机制原生执行，CEO + Eng 双声各自独立子代理（sonnet 档） -->

# Autoplan 广审 — issues-v2-single-file-model

## CEO 广审结论

方向（单文件、合一、砍 batch）基本正确，但四件套严重低估了要拆的东西的重量。

### Findings

| # | 发现 | 严重度 | 修法 |
|---|------|--------|------|
| E | `sdflow_issues_core`（2175 行）的硬化能力（跨进程锁、reindex 防丢数据守卫、Windows 编码）去留完全未判定——design.md 只说「无 sdflow_issues_core 包……内联为常量」，没说这些不变量是被结构性消除还是必须移植 | **CRITICAL** | design.md 逐条过 determinism-guards / recorder-root-resolution 两份现存 spec，每条标注消解/移植，移植项补 Requirement + task |
| A | batch「已被 roadmap 替代」前提被数据证伪——batches.md 46 个批次中 34 个（74%）仍 PLANNED | HIGH | 用真实调用频率核实理由，或改写为真实理由 |
| B | 34 个 PLANNED 批次的优先级/成员信息删除无撤离出口 | HIGH | 迁移进 issue body 或汇总存档 |
| F | determinism-guards / recorder-root-resolution 两份主 spec 未打 delta，与现实脱节 | HIGH | 补 MODIFIED/REMOVED delta |
| G | tasks 5.3 测试清理一刀切，格式无关的不变量测试（仓根解析、Windows 编码、原子写）被误删 | HIGH | 拆分处理：格式耦合删、格式无关改造保留 |
| H | 仓外消费仓协调缺失；v2 无 fail-closed 检测（v1 残留目录时应提示先跑 migrate） | HIGH | 枚举消费仓逐个迁移 + issues.py 加 v1 检测 |
| D | 无 Alternatives Considered，三代存储格式改型未交代取舍 | MEDIUM | design.md 补候选方案对照 |

## Eng 广审结论

单文件架构方向正确，但设计静默丢弃两个安全关键子系统（并发锁 + reindex 守卫），且迁移核心前提与语料矛盾。

### Findings

| # | 发现 | 严重度 | 修法 |
|---|------|--------|------|
| C1 | `add`/`set-status` 丢弃 `.recorder.lock` 并发协议（ADR-0025），无替代——两个并发 `add` 可静默覆盖（永久数据丢失，exit 0） | **CRITICAL** | 重新采用锁（scope 可缩小）或 decision-memo 显式记录并发风险接受 |
| C2 | `git mv` 无非 git 回退、无部分失败恢复（frontmatter 写了但 git mv 失败 → 不一致状态） | **CRITICAL** | 指定操作顺序 + 非 git 环境 fallback 到 plain fs move |
| C3 | 迁移 spec 的「两种格式互斥」前提被语料证伪——todolist 文件同时有 152 legacy 行 + 146 overlay 项，34 个 ID 两边都有（frontmatter 为权威，表格行是冻结快照） | **CRITICAL** | 迁移 MUST 按 ID 去重，frontmatter 优先于 table row；复用 `_build_effective_snapshot` 的 shadowing 逻辑 |
| C4 | `closed_date` 字段映射声称「取 status 变更历史」但 v1 schema 不存在 status 变更日志——实际只有 `time`（创建时间），所有迁移 closed_date 都是文件日期近似值 | **CRITICAL** | design.md 明确说明 closed_date 对迁移项是已知不精确的近似，不是真实关闭时间 |
| H1 | sdflow-done 的 sweep 集成被错误描述——当前不是「两次 scan」而是一次 `issues.py sweep`（含 lock + triage + batch add + reindex 的复合操作），v2 砍掉 batch/sweep 后需要设计替代 triage 机制 | HIGH | design.md 补充 sweep→v2 替代方案设计 |
| H2 | determinism-guards / recorder-root-resolution 两份 live spec 未被 delta 触碰 | HIGH | 补 spec delta |
| H3 | 测试计划丢弃并发锁测试、Windows 冒烟、覆盖率门禁——均为格式无关的已验收能力 | HIGH | 并发测试取决于 C1；Windows 冒烟 + 覆盖率门禁应保留 |
| H4 | 消费方清单漏 AGENTS.md、sdflow-init/assets/snippets/claude-section.md、openspec/CONTEXT.md | HIGH | 补进 Impact/tasks |

## CEO-Eng 收敛分析

| CEO | Eng | 判定 |
|-----|-----|------|
| E（硬化能力未判定） | C1（锁丢弃） | **同一问题的两面**，合并——CRITICAL |
| F（spec delta 缺失） | H2（同） | **完全重叠**，合并——HIGH |
| G（测试清理过猛） | H3（同） | **完全重叠**，合并——HIGH |
| H（消费仓协调） | H4（消费方列表不全） | **部分重叠**（H 更广含仓外，H4 聚焦仓内漏项），合并——HIGH |
| A+B（batch 前提 + 数据撤离） | — | CEO 独有——HIGH |
| — | C2（git mv 回退） | Eng 独有——CRITICAL |
| — | C3（迁移格式前提证伪） | Eng 独有——CRITICAL |
| — | C4（closed_date 数据源不存在） | Eng 独有——CRITICAL |
| — | H1（sweep 描述错误） | Eng 独有——HIGH |

## 自动决策（autoplan 6 原则 · G2 适配：不弹窗，登记进报告）

| # | 决策 | 分类 | 原则 | 理由 |
|---|------|------|------|------|
| D1 | 所有 CRITICAL findings → 需回流修改四件套 | Mechanical | P1(completeness) | 并发安全和迁移正确性是阻塞级缺口 |
| D2 | batch PLANNED 数据不可裸删 → 需加撤离任务 | Mechanical | P1(completeness) | 34 条人工判断记录不是派生物 |
| D3 | 测试清理 5.3 应拆为「格式耦合删 / 格式无关保留」 | Mechanical | P5(explicit) | 不变量测试与存储格式正交 |
| D4 | 不建议拆分 change（合一 + 单文件 + 砍 batch 三件高耦合） | Taste | P3(pragmatic) | 三件事分开做成本反而更高 |

[gstack-amendment]
