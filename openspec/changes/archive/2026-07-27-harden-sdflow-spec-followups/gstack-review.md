<!-- sdflow:step1-broad-review v1 mode="native" -->

# Native autoplan review · harden-sdflow-spec-followups

运行模式：native。主 session 实际执行 CEO → Engineering → DevEx；本 change 无 UI 范围，Design phase 按 autoplan 条件跳过。外部 Claude voice 的 helper preflight 通过，但 dispatch 因相对 `run-dir` 被 helper 拒绝，返回 `state=usage-error`、`fallback_allowed=false`；按防重复计费纪律未重派，因此本文件不宣称双声完成。

<!-- sdflow:outside-voice v1 site="design-voice" host="codex" runner="none" findings="0" reason_code="fallback-unavailable" truncated="false" -->

## CEO review

### 目标与范围

本 change 的价值是把 `/sdflow-spec` 从“文案似乎有保证”收口为“保证边界可证、未知可见、默认上下文可控”。范围锁定源仓 T233–T238、T240–T242 与 T132 前置订正；T239 下游 rollout、阶段二外派启用与 shell 解析明确排除。

### 10x alternative

不引入 shell AST，也不继续扩充“危险结构”黑名单。最简可靠形态是：只对有限且完整匹配的直接 `openspec new change <literal>` 调用执行 FF-0；其余复合、动态、跨目录形态统一进入无决策审计。

### Findings

1. `[P1] (confidence: 9/10) design.md:D1` — “命令文本不包含任何可能改变工作目录的 shell 结构”是对无界 shell 语法的负向证明，无法支撑“可证明作用仓就是 payload 仓”的目标。`[gstack-amendment]` 推荐改为直接调用 allowlist，并把未命中统一归为 undecided。
2. `[P1] (confidence: 9/10) decision-memo.md:C1 / tasks.md:2.3` — C1 只纳入 T132 的前置订正，task 2.3 却写“实现或更新机械门”，会静默扩大范围。`[gstack-amendment]` 推荐明确本 change 不实现 T132，T132 保持 OPEN。
3. `[P2] (confidence: 8/10) tasks.md:3.1-3.2` — 台账关闭没有逐票完成条件，可能把“归档已修”“本 change 待修”“独立后续”混为一类。`[gstack-amendment]` 推荐加入 closure matrix。

## Engineering review

### Architecture

FF-0 应拆成两个逻辑边界：有限 grammar 识别“可在 payload cwd 执法的直接调用”，再复用原三分支决策；未命中 grammar 只产出 context，不得进入 allow/deny。这样不需要 shell parser，也不会用 payload 仓替未知实际仓背书。

### Execution and tests

```text
Bash payload
├── 非创建命令 ───────────────────────── silent pass
├── 直接 literal 创建调用
│   ├── protected branch ─────────────── deny
│   ├── feat/{same-change} ───────────── silent pass
│   └── other feature ────────────────── ack ? pass : deny
└── 未能证明作用仓/唯一 literal change
    ├── 目录切换/包装/复合形态 ───────── additionalContext(cwd-ambiguous)
    └── 变量/替换/通配符 ─────────────── additionalContext(change-name-unparseable)
                                            均无 permissionDecision
```

4. `[P1] (confidence: 9/10) design.md:D2 / spec-authoring:SA-14` — “标题 + reference 存在”可保留空壳标题却移走必执行语义。`[gstack-amendment]` 推荐用最小 resident-contract token map 锚 frontmatter、Phase 0/A/B/C、终审、两个 checkpoint、strict validate、出口序列和 reference 加载条件。
5. `[P2] (confidence: 8/10) tasks.md:4.2` — “核验全局安装状态”不可判定。`[gstack-amendment]` 推荐明确比对 canonical hook/skill 与全局安装副本或 symlink target。
6. `[P2] (confidence: 8/10) spec-workflow delta` — 只要求人类可读“具体原因”，测试与排障只能匹配易漂移散文。`[gstack-amendment]` 推荐在 `additionalContext` 固定有限 reason code，同时保留中文说明。

### Security, performance, distribution

- 安全：undecided 必须无 `permissionDecision: allow`；protected branch deny、一次性 ack 与 TTL 语义不得回退。
- 性能：本地有界匹配，无值得单列的瓶颈。
- 分发：没有新 artifact；canonical 修改通过现有 `setup.sh` 刷新，本 change 不做 T239 rollout。

## DevEx review

| Pass | 评分 | 结论 |
|---|---:|---|
| Getting started | 8/10 | 无新入口，薄化降低默认上下文 |
| Time to first success | 8/10 | 直接调用不变；复杂调用改为诚实未判定 |
| Naming/API | 7/10 | 需稳定 reason code |
| Errors/debuggability | 6/10 | 当前“具体原因”仍偏散文；采纳 finding 6 后可到 8/10 |
| Docs/discoverability | 8/10 | 按需 reference 必须由入口确定条件链接 |
| Workflow integration | 8/10 | setup 刷新；T239 仍独立 |
| Extensibility | 7/10 | grammar 以测试表扩展，禁止演化成 shell parser |
| Removal/recovery | 8/10 | 同一提交回滚后重跑 setup |

## Autoplan 自动决策

- 采纳 findings 1–6，进入阶段二多镜复核与最终合并池。
- T132 固定为“只订正前置、保持 OPEN”；T239 保持 OPEN。
- 视觉设计阶段因无 UI scope 跳过。
- outside voice 本轮未执行，相关 finding 数为 0；这是一条显式能力降级，不计作独立镜。
