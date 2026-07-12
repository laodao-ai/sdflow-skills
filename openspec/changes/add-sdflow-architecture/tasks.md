# Tasks: add-sdflow-architecture

> Requirement ID 对照（specs/architecture-design/spec.md）：
> REQ-1 事实三问锁 draft · REQ-2 十节完整性 · REQ-3 拆分规则集+AP 自检 · REQ-4 候选分歧驱动 ·
> REQ-5 假设显影+数值溯源 · REQ-6 状态机+frontmatter · REQ-7 冷走查+升档 · REQ-8 交棒骨架 proposal ·
> REQ-9 分家落位+单例 · REQ-10 lint 输出诚实

## 1. 共享 schema 与 scaffold 内核

- [ ] 1.1 `scripts/sad_schema.py`：frontmatter 字段/状态与成熟度枚举、十节标题锚常量、`[假设-N]` 正则、reason_code 枚举——单一格式源（REQ-6/REQ-10；DEC-1/DEC-2）
- [ ] 1.2 `scripts/sad_scaffold.py` 建骨架：从 sad-template 生成 `openspec/architecture/sad.md`，原子写 temp+rename；消费仓 preflight（无 openspec/ 布局 → fail-closed 指引 sdflow-init）（REQ-9；DEC-7/DEC-8）
- [ ] 1.3 scaffold 状态机：合法迁移表（draft→skeleton-ready→validated→frozen + 异常回落）、锁 draft 前置复检（事实三问 + 假设无未处置）、拒绝非法跳级、迁移/回落记录行（REQ-1/REQ-6；DEC-4）
- [ ] 1.4 scaffold 假设对账与单例保护：内联 `[假设-N]` ↔ 附录清单对账、`assumptions_open` 回写；SAD 已存在 → continue/replan 显式分流不静默覆盖（REQ-5/REQ-9；DEC-3）
- [ ] 1.5 `tests/test_sad_scaffold.py`：正负路径——缺三问拒升、未处置假设拒升、非法跳级拒绝、原子写、已存在不覆盖、preflight fail-closed（REQ-1/5/6/9）

## 2. lint（v1 最小机械集）

- [ ] 2.1 `scripts/sad_lint.py` 节断言：十节「存在 或 显式 N/A+理由」，缺节 → 对应 reason_code 非零（REQ-2）
- [ ] 2.2 lint 假设断言：内联标记数 == 清单行数 且 无「未处置」，输出假设计数（REQ-5）
- [ ] 2.3 lint 排序与枚举断言：质量属性全序存在（无并列/未排序 → reason_code）、frontmatter 枚举合法性（REQ-6）
- [ ] 2.4 lint 输出诚实：通过码 `structure-ok-SEMANTICS-UNCHECKED`；坏输入（文件缺失/frontmatter 不可解析）fail-closed 非零 + `[sad_lint] FAIL:` stderr，与正常判定物理区分（REQ-10；DEC-5）
- [ ] 2.5 `tests/test_sad_lint.py`：每类断言正负各 ≥2 用例（Success Metric 2 锚）（REQ-2/5/6/10）

## 3. references 六件

- [ ] 3.1 `references/sad-template.md`：十节骨架 + frontmatter 骨架 + contract 五层/成熟度字段 + `[假设-N]`/数值溯源标记示例 + 假设清单附录结构 + 深度分层注释（低风险节一句话/N/A 合法）（REQ-2/5/6）
- [ ] 3.2 `references/decomposition-rules.md`：R1–R11 + AP1–AP4（自 docs/sad/02 §5.1 定稿转写，含两轴正交提醒）（REQ-3/REQ-4）
- [ ] 3.3 `references/intake-questionnaire.md`：事实三问 + 各问追问提示（REQ-1）
- [ ] 3.4 `references/quality-criteria.md`：S1–S11 + 机械化拆解表（真相源，条目带 S 编号）（REQ-10 供源）
- [ ] 3.5 `references/review-lenses.md`：语义残余镜单（条目引用 S 编号）+ BASE-29 scope-check 人工核对清单 v1（REQ-7）
- [ ] 3.6 `references/checklists/`：横切概念模板、质量属性候选库、外部依赖典型集、R4 预期变化类别表（初版允许薄，P2）（REQ-3 R4 供料）

## 4. SKILL.md 编排

- [ ] 4.1 frontmatter + 触发描述（触发/不触发场景，措辞顾及生态触发精度纪律）
- [ ] 4.2 五步流程主体：①三问采集与锁 draft 声明 ②规则集跑候选 + AP 自检前置 + 分歧驱动数量（无分歧单方案显式声明行）③挂产物拍板（场景化二选一/推荐数值否决/Non-goals 勾选）④冷走查（禁生成 session 自查）+ 升档信号表 + outside voice 复用 spec-review 机制与降级不静默 ⑤交棒（REQ-1/3/4/7/8；DEC-6）
- [ ] 4.3 骨架 proposal 草案模版段：contract 穿越点清单硬槽 + 骨架 DoD 文案（每条 L1 contract 被真实调用穿过 + 部署链路通）（REQ-8）
- [ ] 4.4 分家指令：ADR → `openspec/adr/`（不可变 + supersession）、术语 → `CONTEXT.md`、SAD 只引用不复述；preflight 指引（REQ-9）
- [ ] 4.5 信任边界声明行：lint 通过 = 结构性通过 ≠ 内容已审（师承 review_disposition_check 口径）（REQ-10）

## 5. 收尾与端到端验证

- [ ] 5.1 README「Skills 列表」新增 sdflow-architecture 条目
- [ ] 5.2 开发 checkout 跑 `setup.sh`，验证 symlink 建立（adr/0005：不跑 setup 测不到）
- [ ] 5.3 端到端演练：样例需求走完五步 → skeleton-ready SAD + 骨架 proposal 草案（Success Metric 1 锚：产物路径 + sad_lint 退出 0 记录）
- [ ] 5.4 全套 pytest 绿 + Success Metrics 1/2/3 逐条核对留痕

## 测试覆盖图（TG-18）

| code path | 测试类型 |
|---|---|
| sad_schema 常量/正则 | pytest 单元 |
| scaffold 建骨架/原子写/preflight | pytest（tmp 文件系统） |
| scaffold 状态迁移（全迁移表正负 + 回落） | pytest 单元 |
| scaffold 假设对账/单例保护 | pytest 单元 |
| lint 四类断言 reason_code | pytest 正负各 ≥2 |
| lint 坏输入 fail-closed | pytest 负路径 |
| SKILL 五步流程 | 端到端演练（5.3，人工 + 产物锚） |
| outside voice 升档降级 | 演练观察留痕（外部 CLI，v1 无自动化——诚实标注） |
