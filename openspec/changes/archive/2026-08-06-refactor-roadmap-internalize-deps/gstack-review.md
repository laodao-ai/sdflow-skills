<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack 广审报告 · refactor-roadmap-internalize-deps

> **执行形态**：`mode="native"` —— autoplan 经 Skill 机制在主 session 原生执行（非子代理转述模拟）。
> 侧信道佐证：autoplan 的 preamble bash 实跑（`BRANCH: feat/refactor-roadmap-internalize-deps` /
> `REPO_MODE: solo` / `SESSION_KIND: interactive` / `SLUG: laodao-ai-sdflow-skills` 均由
> `~/.claude/skills/gstack/bin/*` 真实返回）；`plan-ceo-review/SKILL.md`、
> `plan-ceo-review/sections/review-sections.md` 经 Read 工具实读；三相位 Codex 双声经
> `codex exec -s read-only -c model_reasoning_effort="high"` 实跑（session id 见各 voice 输出）。
>
> **本报告由 `/sdflow-spec-review` Step1 编排产出**，findings 汇入 Step3 合并池。
> 改动标记用 `[gstack-amendment]`。

## Phase 0 · Intake

- **被审对象（plan）**：`openspec/changes/refactor-roadmap-internalize-deps/` 四件套 +
  `decision-memo.md` + `specs/roadmap-planning/spec.md`（主入口 = `design.md`）。
- **UI scope**：**否**（无任何前端/UI 面）⇒ Phase 2（Design Review）整相位跳过。
- **DX scope**：**是**（产物本身是开发者工具：`SKILL.md` 指令文本即 API，消费者 = 人 + 执行指令的 AI agent）
  ⇒ Phase 3.5 执行。
- **Restore point 适配偏离**：autoplan 原文要求把 plan file 全文另存并在其顶部 prepend 一行 HTML 注释。
  **本次不做**——被审对象是 git-tracked 的 OpenSpec 四件套（`openspec validate --strict` 会读它们，
  且 `.openspec.yaml` 与 change 目录结构受 CLI 约束），往正文 prepend 注释会污染产物。
  等价保障：分支 `feat/refactor-roadmap-internalize-deps` 工作树干净，`git diff main --stat` 仅
  8 个新增文件、979 行、零删除 ⇒ `git checkout main` 即完整还原。
- **双声并行偏离**：autoplan 原文要求「Claude 子代理与 Codex 顺序前台跑」。本次三相位六个 voice
  **并行后台跑**（主 session 起后台任务，实测跨轮次存活）。分析深度不变，仅省墙钟；
  「双声都完成才建 consensus 表」的实质约束照守。

---

## Phase 1 · CEO Review（Strategy & Scope）

**Mode：HOLD SCOPE**（自动决策 D-A1）。依据：autoplan 默认 `SELECTIVE EXPANSION`，
但本仓 `CLAUDE.md` 基准 3/4 与四条通则③明确禁止「顺手加宽」「补一层以后可能用得上的抽象」，
且 `decision-memo.md` 的 D1–D14 已由真人在 2026-08-05 逐条拍板。
⇒ 本次不 surface 任何 scope 扩张提案（cherry-pick ceremony 整个跳过），
火力全部投向「现有 scope 是否 bulletproof」。**这是 autoplan 缺省的偏离，理由已写明。**

### 0A. Premise Challenge（前提拷问）

| # | 承重前提（proposal / decision-memo 原文） | 核验结果 | 判定 |
|---|---|---|---|
| P1 | 「Codex 宿主接地实测无 wayfinder，降级路径常驻生效，长档持久化保护对半数宿主是空头承诺」 | 现行 spec `:79` 的 SR-9 Scenario 明文记载了同一事实（「matt 套件当前仅装 `~/.claude/skills/`，Codex 宿主无 wayfinder」）⇒ **前提为真** | ✅ 成立 |
| P2 | C1「matt 无其他运行时消费方」 | **不成立（见 F-1）**。`openspec/matt/issue-tracker.md:16` 明文把 `to-tickets` / `triage` / `to-spec` / `qa` 列为消费方；这四个 skill **本机 `~/.claude/skills/` 下全部已安装**。C1 的检验方法（全仓 grep 路径字符串）对「指令驱动、仓外安装」的消费方结构性失明 | ❌ 证伪 |
| P3 | C3「存量 footage 真实存在」 | **不成立（见 F-2）**。全仓 `find . -type d -name footage` **零命中** | ❌ 证伪（结论仍成立，但依据错） |
| P4 | C10「增量落盘同构先例（sdflow-spec B.4）」 | `sdflow-spec/SKILL.md:337-343` 实存且语义一致 | ✅ 成立 |
| P5 | 「本次将讨论层能力内化」= 能力等价替换 | **部分不成立（见 F-4）**：wayfinder 的 map+票承载 frontier 排序 / 依赖 / claim / 闭环，memo 是线性追加文本，二者非同构 | ⚠️ 部分证伪 |

**P2/P3/P5 是三条被证伪的承重前提**——其中 P2、P5 直接支撑人已拍板的 D2、D4。
按反静默压制，全部上抛 HARD-GATE（不代人翻案）。

### 0B. Existing Code Leverage（已有代码复用图）

| 子问题 | 已有实现 | 本 change 是否复用 |
|---|---|---|
| B 相位增量落盘 + 重入探测 | `sdflow-spec/SKILL.md` B.1④ / B.4 / 0.3 | ✅ 声明同构复用 |
| 草稿 / 定稿状态标记 | `sdflow-spec` 用 frontmatter `decision_hash` 空/非空表达 | ❌ **D4 明确弃用，且未提供替代**（F-3 根因） |
| 存量形态兼容条款 | 现行 spec `:8` 的 requirements.md 兼容先例（SR-1） | ✅ footage 冻结条款照抄其结构 |
| 收尾机械门 | 现行 checklist ① 的既有脚本门 | ✅ 不动 |
| review 分档 | `/plan-eng-review` + `/autoplan` | ✅ D1 保留原样 |

**结论**：复用充分，唯一缺口是「草稿/定稿状态」——这正是本轮最高收敛度的缺陷（F-3）。

### 0C. Dream State（12 个月理想态）

```
  CURRENT                          THIS PLAN                     12-MONTH IDEAL
  roadmap 讨论层押 5 个外部      → 讨论层内化，只剩 review     → 全部 sdflow-* skill 共享
  skill；宿主间行为不一致；        层 2 个外部依赖；与             同一套「A 澄清 / B 拷问 /
  长档持久化对 Codex 宿主是        sdflow-spec 三相位对齐          C 生成 + 纪要增量落盘」
  空头承诺                                                        骨架，宿主无关
```

**Dream state delta**：本 plan 把 roadmap 从「5 依赖」推到「2 依赖」并对齐三相位骨架，
方向与理想态一致。**但留下一个反向缺口**：sdflow-spec 的纪要有机械身份层（`decision_hash`），
roadmap 的没有 ⇒ 两个 skill 的「同一骨架」在状态表达上分叉，未来统一时要么补回、要么再改一次。

### 0C-bis. Implementation Alternatives（强制项）

```
APPROACH A: 全量内化 + matt 一并移除（= 本 plan）
  Summary: 讨论层 5 依赖全删，三相位重写，openspec/matt/ 整目录删
  Effort:  L    Risk: Med
  Pros:    一次到位；与 sdflow-spec 骨架对齐；宿主无关
  Cons:    matt 移除与 roadmap 重构耦合在一个 change（见 F-1）；能力等价性未证（F-4）
  Reuses:  sdflow-spec 三相位 / requirements.md 兼容先例 / 既有 review 分档

APPROACH B: 只内化讨论层，matt 移除另开 change（最小可行）
  Summary: 同 A，但保留 openspec/matt/ 与 CLAUDE/AGENTS 三区块，只删 wayfinder preflight 一处引用
  Effort:  M    Risk: Low
  Pros:    scope 单一内聚；不触碰 4 个已安装 matt skill 的配置面；回滚面更小
  Cons:    留一个「配置在、消费方只剩 3 个 skill」的中间态；要跑两次 workflow 循环
  Reuses:  同上

APPROACH C: 修依赖契约而非删依赖（理想架构候选）
  Summary: 保留 wayfinder，把「宿主无 wayfinder」做成一等公民降级（memo 长档模式转正）
  Effort:  M    Risk: Med
  Pros:    保住 map+票的 frontier/依赖/闭环语义（F-4 指的能力）
  Cons:    双路径永久并存，维护面不降反升；与「消除外部依赖」的人定目标直接冲突
  Reuses:  现行 SR-9 降级路径

RECOMMENDATION: A —— 目标范围由真人在 D1/D2 定死（「讨论层内化 + matt 移除」），
C 与目标直接冲突（属通则③的「砍窄/改造」），B 是 A 的拆分变体、拆不拆是真人的 scope 决定。
∴ 推荐 A 原样推进，把 B 作为 F-1 的备选一并上抛设计门。
```

### 0D. Mode-Specific Analysis（HOLD SCOPE）

- **复杂度检查**：本 plan 触及 **13 类改动面**（SKILL.md / 5 模板 / spec delta / matt 4 文件 /
  CLAUDE.md / AGENTS.md / bundle 2 文件 / CONTEXT.md / adr / issues / docs / INDEX.md）——
  超过 autoplan 的「>8 文件即 smell」阈值。**但不建议缩**：这些是同一次能力替换的**必然牵连面**
  （删一个机制必须同步删它的契约、词条、指路），拆开会留半改态（proposal P1 已说明）。
  唯一真正可分的是 matt（F-1）。
- **最小改动集**：P0 = SKILL.md 三相位重写 + spec delta（不成对完成即出现 spec/实现矛盾）。
  其余 P1/P2 均为「不做就留半改态」，无可延后项。

### 0E. Temporal Interrogation（实现期会撞上什么）

| 时点 | 实现者会撞上的歧义 | 现在该定的事 |
|---|---|---|
| HOUR 1（骨架） | 「实战案例：博客 v2 重建」这一节留还是删？骨架里没有它 | **F-6** |
| HOUR 1 | memo.md 的「定稿标记」写成什么字面？ | **F-3** |
| HOUR 2-3（B 相位） | B 什么条件下算收敛？tasks 1.3 写了「停止条件」，spec 没有任何规范条款 | **F-5** |
| HOUR 2-3 | continue/replan 放弃时，「本次新增」怎么算出来？ | **F-7** |
| HOUR 4-5（治理收尾） | `docs/external-dependencies.md` §8 依赖图里的 `/grilling`、`/domain-modeling` 要不要改？tasks 5.4 只说删 §5 | **F-8** |
| HOUR 6+（验证） | 6.4 的演练包没有 footage，怎么演练冻结条款？ | **F-2** |

**六条全部已在下方 findings 落定，无「实现期再说」的悬空项。**

### 0F. Mode Confirmation

HOLD SCOPE + APPROACH A。已 commit，后续各节不再回头论证缩/扩。

### Step 0.5 · CEO 双声

**CODEX SAYS (CEO — strategy challenge)** — 7 条，session `019fd237-ce48-7143-a951-b8629d643710`：
① matt 移除是伪装成依赖清理的无关治理移除（critical）② memo 不等价于长档规划状态（critical）
③ 未证明问题大到值得破坏性重设计，success metrics 只量「删掉的字符串」（high）
④ 直接生成分支与持久化策略自相矛盾：判定点①要求写 task-log.md，而该路径此刻文件不存在（high）
⑤「商业化信号」是错的控制变量，应按决策风险（不可逆性/爆炸半径/不确定性/花费/合规）路由（high）
⑥ 遗留处置是遗弃而非迁移（high）⑦ 验证只测文档完整性、不测规划器有效性（medium）

**CLAUDE SUBAGENT (CEO — strategic independence)** — 9 条（含 2 条正面结论）：
① C3 证伪（high，实测 `find . -iname footage` 零命中；C3 引的「footage 引用」实为
`archive/workflow-cost-optimization/memo.md:1` 标题里的比喻词「（memo · 考古 footage）」，
把 memo 自称当成 wayfinder 产出的实证）② 由 ① 级联的验证空转 = **恒真锚**（high）
③ 6 个月后悔场景：ticket-DAG（open/claimed/resolved/abandoned + Blocked-by + frontier 查询）
降级为扁平追加日志，C10 的「本质同模式」是未经验证的等价性断言（high，战略级）
④「为什么不并入 sdflow-spec」候选从未被分析（medium）
⑤ Why 段把 5 个依赖打包论证——**office-hours 双宿主皆可用**，「Codex 宿主无 X」理由对它不成立（medium）
⑥ matt 早于本 change 已事实废弃（`sdflow-issues` 生于首个 commit 2026-07-03，早 `openspec/matt/`
2026-07-10 一周），fold 论证的因果表述需修正（medium）
⑦「实战案例」节两不管（low/medium）
⑧ **正面**：matt fold 不违反基准 4 ⑨ **正面**：handoff 草稿的「二路径」简化已被 C6/D6 主动纠正为三态路由

### CEO 双声 consensus 表

| # | 维度 | Claude | Codex | Consensus |
|---|---|---|---|---|
| 1 | 前提是否成立 | ✗（C3 证伪 · C10 等价性未证 · Why 打包论证） | ✗（C1 / C3 均被质疑） | **CONFIRMED ✗**（+ 主 session 独立亲验 C1/C3 双双证伪） |
| 2 | 是否在解决正确的问题 | ✓（方向对） | ✓（方向对，论证不足） | **CONFIRMED ✓** |
| 3 | scope 标定是否正确 | ✓（fold 不违规，仅因果表述需修） | ✗（matt 应拆为独立 change） | **DISAGREE → 上抛 Q1** |
| 4 | 备选是否充分探索 | ✗（缺「并入 sdflow-spec」候选） | ✗ | **CONFIRMED ✗** |
| 5 | 竞争/市场风险 | N/A（内部工具） | N/A | N/A |
| 6 | 6 个月轨迹是否稳健 | ✗（frontier 追踪能力无承接物） | ✗（memo 语义缺口会复现） | **CONFIRMED ✗ → Q2** |

> **DISAGREE #3 的处理**：Codex 主张拆分，Claude 子代理实测了时间线后主张不拆（但要求改因果表述）。
> 主 session 裁决：**两边都对了一半**——Claude 的时间线证据（matt 早已事实废弃）恰恰**削弱**了
> 「因本次改动而孤立」的 fold 理由，但同时**也削弱**了「必须拆开」的理由（一个早已死的配置，
> 顺手清掉的成本极低）。真正的新信息是 F-1：matt 还有 4 个**活着的、已安装的**消费方。
> ⇒ 不由我裁，上抛 Q1。

---

## Phase 2 · Design Review

**SKIPPED — no UI scope.** 本 change 无任何用户界面、渲染、交互面。
按 autoplan 的 skip 条件整相位跳过，非压缩。

---

## Phase 3 · Eng Review

### Step 0 · Scope Challenge（实读代码）

- 读了 `sdflow-roadmap/SKILL.md`（635 行，19 个 `##` 节）、`openspec/specs/roadmap-planning/spec.md`
  （176 行，8 个 Requirement）、`openspec/matt/`（4 文件）、`CLAUDE.md`/`AGENTS.md` 的 matt 段、
  `sdflow-init/scripts/init.py`（分发机制）、`hack/sync_principles.py`、5 个 references 模板。
- **spec delta 契约覆盖交叉核验（本步最高优先项）**：现行 spec 8 个 Requirement 逐条过——

  | # | 行 | Requirement | 是否引用被删机制 | delta 处置 | 判定 |
  |---|---|---|---|---|---|
  | 1 | :6 | 三件套直写产出 | 是（「结晶」×4、包生命周期） | MODIFIED | ✅ |
  | 2 | :30 | design.md 需求与目标态伸缩头部章 | 否（用「产品型项目」自有措辞，不含 野心/结晶/footage） | 未触碰 | ✅ 正确 |
  | 3 | :49 | 讨论层按规模分档路由 | 是 | REMOVED | ✅ |
  | 4 | :83 | footage 落盘位置与引用边界 | 是 | REMOVED | ✅ |
  | 5 | :112 | review 按项目野心分档 | 是（术语） | REMOVED + ADDED 承接 | ✅ |
  | 6 | :131 | 收尾 checklist 软门 | 是（④ wayfinder 闭环、domain-modeling） | MODIFIED | ✅ |
  | 7 | :150 | roadmap.md 近细远雾分层 | 是（「产品/商业野心信号」「结晶阶段」） | MODIFIED | ✅ |
  | 8 | :169 | 新项目起步的架构先行指路 | 否 | 未触碰（tasks 1.1 显式防丢） | ✅ 正确 |

  **结论：无悬空 SHALL。** 这一条 Codex eng voice 独立跑出同一结论（「no dangling formal
  Requirement remains」）——**双向一致，本项判绿有据。**
- `openspec validate refactor-roadmap-internalize-deps --strict --type change` → **实跑通过**
  （`Change 'refactor-roadmap-internalize-deps' is valid`）。
- `sdflow:principles` 托管块：`sdflow-roadmap/SKILL.md` 仅 **1 个**区块（`:15`–`:154`，140 行）。
  `sync_principles.py` 的 `_blocks()` 支持多区块、且明写「只更新首个 ⇒ 第二份静默留旧版」的坑——
  本文件单块 ⇒ tasks 1.8「块外全重写、块内零字节不动」的做法**充分**。✅
- matt 区块所有权：CLAUDE.md 的三个 matt 小节在 `<!-- opsx-init:end -->`（:430）**之后**，
  `sdflow-init/assets/snippets/` 内零 matt 命中 ⇒ **手删安全，不会被 `sdflow-init update` 重铺**。✅

### Step 0.5 · Eng 双声

**CODEX SAYS (eng — architecture challenge)** — 7 条 + 一条独立交叉核验结论，
session `019fd238-...`：① memo draft/final 状态不可表达（critical）② 「只删本次新增」不可安全实现（high）
③ `docs/external-dependencies.md` §8 依赖图残留，且 tasks 6.1 的 `docs/` 白名单正好把它藏起来（high）
④ 分发窗口缓解基于错误的部署模型（high）⑤ 无主 spec 提升/核验任务（medium）
⑥ 唯一的 legacy footage 演练不含 legacy footage（high）⑦ 验证可以在核心新行为缺失时照样通过（medium）

**CLAUDE SUBAGENT (eng — independent review)** — 7 条 + 3 条正面结论：
① **定稿标记的唯一候选载体被模板重写规格显式砍掉**（critical）——
`memo-template.md:27` **现存** `> 状态：DRAFT / FINAL` 字段，而 D13 / task 2.1 把新模板头部规格
钉为「头部包名 + 日期」，只字未提状态字段；D4 又堵死了 hash 式机械判据 ⇒ 两头夹击，
「无定稿标记」判据在实现期没有可操作定义
② continue/replan「只删本次新增」无机制、无 Scenario（high）
③ **6.1 grep 白名单枚举式不完整**，遗漏 ≥8 处合法保留文件——含 D10 明确拍板保留的
`ff-generation-constraints.md` 规则本身，以及 6 处 DOC-1 语境「考古层」与 1 处同形异义「野心」（high）
④ **CONTEXT.md 实有三处相关词条**，proposal / design / tasks 一律只认「两处」（high）
⑤ TG-09 状态机只有一条 continue 路径演练（high）
⑥ 并发 / 部分写失败 / 多包重入三类边角是**沉默遗漏**而非显式接受的边角（medium）
⑦ task 1.4 颗粒度不足以作独立验收锚（medium）
**正面**：契约覆盖无悬空 SHALL ✓；`sync_principles.py` 保护机制充分 ✓；改名 grep 思路方向正确 ✓

### Eng 双声 consensus 表

| # | 维度 | Claude | Codex | Consensus |
|---|---|---|---|---|
| 1 | 架构是否稳健 | ✗（定稿标记不可实现） | ✗（同左） | **CONFIRMED ✗ · 三源** |
| 2 | 契约覆盖是否完整 | ✓（8 Requirement 逐条过，无悬空） | ✓（无悬空 SHALL） | **CONFIRMED ✓ · 三源**（主 session 独立第三次核验一致） |
| 3 | 测试覆盖是否充分 | ✗（状态机只演练 1/8 路径） | ✗（可在核心行为缺失时通过） | **CONFIRMED ✗** |
| 4 | 部署/分发风险是否可控 | 未审此项 | ✗（模型错，实证 `init.py:213/329`） | **单声 ✗ → 主 session 亲验确认** |
| 5 | 错误路径是否有处置 | ✗（三类边角沉默遗漏） | ✗（只写禁令不写恢复） | **CONFIRMED ✗** |
| 6 | 任务覆盖是否完整 | ✗（CONTEXT.md 第三处词条） | ✗（§8 依赖图、主 spec 核验） | **CONFIRMED ✗**（两边各抓到对方漏的，合并后 3 处缺口） |

### Section 1 · Architecture（依赖图 · 本 change 的前后对照）

```
BEFORE                                          AFTER
sdflow-roadmap                                  sdflow-roadmap
 ├─▶ /opsx:explore（分支 A）                     （上游可选 /opsx:explore，非内部分支）
 ├─▶ wayfinder（分支 B）                         ├─▶ /plan-eng-review   ┐ review 层
 │    ├─▶ /grilling                              └─▶ /autoplan          ┘ 原样保留
 │    ├─▶ /domain-modeling
 │    └─▶ openspec/matt/issue-tracker.md ◀── 🔴 该文件同时被 to-tickets /
 ├─▶ /office-hours（分支 C）                          triage / to-spec / qa 四个已装 skill 消费
 └─▶ /plan-eng-review · /autoplan                    （本 change 一并删除，见 F-1）
```

耦合评估：AFTER 的耦合面严格小于 BEFORE，**方向正确**。
唯一新增耦合 = memo.md 同时承担「决策纪要」+「包生命周期状态位」两个职责，
而后者无字面表示（F-3）——这是本 change 引入的**新单点失败**。

### Section 2 · Error & Rescue Map（TG-08 必填槽 · design 缺失）

design.md 现有 14 个小节，**无 `失败模式表`（BASE-06）、无 `可观测性`（BASE-11）**。
TG-08（修改外部依赖）命中 ⇒ 两槽 MUST 有。补出应有内容（此表即 F-9 的修复物）：

```
  码路 / 状态                  | 会出什么错                        | 操作者看到什么      | 处置 | 测?
  ----------------------------|----------------------------------|--------------------|------|----
  B 起手建目录                 | 目录建成、草稿 memo 写失败         | ？未定义            | GAP  | N
  B 增量落盘                   | 两次落盘之间中断                  | 已声明「非零损失」   | OK   | N
  重入探测                     | 命中 ≥2 个未定稿 memo             | ？未定义（F-3）      | GAP  | N
  重入探测                     | memo 存在但「定稿标记」无字面定义   | 各 agent 判定不一    | GAP  | N
  放弃清理（create）            | 删包目录                         | 已定义              | OK   | N
  放弃清理（continue/replan）   | 「本次新增」不可判定 ⇒ 误删既有    | ？未定义（F-7）      | GAP  | N
  C 生成部分失败                | 三件套只写出 1-2 个               | 不被重入探测覆盖     | GAP  | N
  两 session 同名并发           | 后者覆盖前者                      | ？未定义            | GAP  | N
  review skill 不可用           | 「未审待恢复」+ 修复步骤           | 已定义（D1 保留）    | OK   | N
  存量 footage 包续跑           | 一行冻结提示                      | 已定义              | OK   | N（无 fixture，F-2）
  存量四件套包续跑              | 一行兼容提示                      | 已定义              | OK   | N
  存量**单文件**包续跑          | issues-triage-2026-08 即此形态    | ？未定义（F-10）     | GAP  | N
```

**7 个 GAP，全部 RESCUED=N ∧ TEST=N ⇒ 按 autoplan 判据均为 CRITICAL GAP。**

### Section 3 · Security & Threat Model

新增攻击面：**无**（无端点、无输入、无凭据、无第三方包）。
唯一沾边项：放弃清理条款是**删文件**动作，且删除范围判据不可判定（F-7）——
这是「破坏性操作 + 判据不明」的组合，按安全口径也应收紧。已并入 F-7，不另立条目。

### Section 4 · Test Review（新增行为 → 覆盖方式）

```
  新增码路（指令层）                    覆盖方式                        缺口
  三态路由（3 条分支）                  人读终审 + grep                 无任何执行级验证
  B 七维裁剪（3 种裁剪基准）             同上                            同上
  B 增量落盘 / 停止条件                  同上                            停止条件连规范条款都没有（F-5）
  重入探测（0/1/N 个未定稿 memo）        同上                            标记未定义 ⇒ 不可测（F-3）
  放弃清理（create / continue / replan） 同上                            continue/replan 无 Scenario（F-7）
  存量 footage 冻结                      tasks 6.4 演练                  演练对象无 footage（F-2）
  存量四件套兼容                         无                              archive 下有两个真实四件套包，未用
  principles 托管块完整性                sync_principles --check         ✅ 真机械门
  spec delta 结构                        openspec validate --strict      ✅ 真机械门（已实跑绿）
  matt 移除对脚本的波及                  全仓 pytest                     ✅（但本 change 不改任何 .py）
```

`sdflow-roadmap` 无 `tests/`（已核实）⇒ **6.2 的 pytest 对本 change 主体改动零覆盖**。
tasks.md 的测试覆盖图把「全仓 pytest」列在「matt 移除对脚本/测试的波及」一行是准确的，
但整张表给人的印象是「有三道机械门」，实际只有两道触及本 change 的产物（`--check` 与 `validate`）。

---

## Phase 3.5 · DX Review

### Step 0 · DX Scope

产品类型 = **AI agent skill（指令即 API）**。开发者旅程 = 人触发 `/sdflow-roadmap` →
agent 按 SKILL.md 执行 → 产出 `openspec/roadmaps/{name}/` 三件套。
初始 DX 完备度评分：**5/10**（路由与产物清楚，异常态与恢复动作大面积未定义）。

### Step 0.5 · DX 双声

**CODEX SAYS (DX — developer experience challenge)** — 8 条，session `019fd238-33d1-...`：
①「直接生成」是名义快路径而非可靠快路径（critical）② B 无可执行停止规则 ⇒ 七维产生无界摩擦（critical）
③ 重入无法按规范工作，因「定稿 memo」无表示（critical）④ 放弃清理有删错风险（high）
⑤ 迁移把在飞 wayfinder 讨论当无害遗留包（high）⑥ 异常态只写禁令不写恢复动作（high）
⑦ 指令过载，先被跳过的恰是安全/可追溯部分（high）⑧「与 sdflow-spec 同构」过度声称（medium）

**CLAUDE SUBAGENT (DX — independent review)** — 9 条 + 3 条正面结论：
① C3 证伪 + Success Metrics 空转（critical）
② **TG-22 假设的「明确兜底路径」（手工转录）只存在于 decision-memo 与 design——
运行时 agent 读不到**；spec 的「历史存档冻结」Requirement 全文无一句要求 agent 去读
`footage/map.md` 提炼要点（high）
③ **「逐节同构」实测至少两处未承认的差异**：(a) sdflow-spec 用 5 个 `references/*.md`
按需加载压密度，roadmap 骨架全内联；(b) sdflow-spec 的 B.6（惰性钩子）+ B.7（收敛前逐条回扫）
是**两道**防线，新 roadmap 只有一层（high）
④ 指令过载，**点名最先被静默跳过的三处**：裁剪表（倾向「全跑保险」）、放弃清理（低频 + 长节尾部）、
重入探测（不是独立标题，而 sdflow-spec 把它做成「第零步」置于 Phase A 之前）（high）
⑤ **design「起手四步」vs spec/tasks「起手三步」计数不一致**（medium）
⑥ 状态清单逐条核对表（5/6 已指定，footage 半途场景是唯一漏项）（medium）
⑦ escape hatch 不对称：review 有覆盖机制，B 相位维度裁剪没有（medium）
⑧ `INDEX.md:52` 整句陈旧，5.5 措辞有「只替换『野心』一个词」的浅改风险（medium）
⑨ 放弃删除前未要求向操作者复述完整路径，与 CLAUDE.md 全局安全规则不齐（medium）
**正面**：C1 仓内 grep 成立 ✓（注：其检验面限于仓内，未覆盖 F-1 的仓外消费方）；
C7 office-hours 六问结构核实成立 ✓；gate-0 五项新旧未变、快路径可达性与旧版持平 ✓

### DX 双声 consensus 表

| # | 维度 | Claude | Codex | Consensus |
|---|---|---|---|---|
| 1 | 首次产出路径够短吗 | ✓（快路径与旧版持平，但摩擦增量未承认） | ✗（快路径名存实亡） | **DISAGREE → 主 session 裁决见 F-13**（Claude 侧有实测支撑，采信） |
| 2 | 指令可被 agent 可靠执行吗 | ✗（点名三处会被跳过） | ✗（过载，先丢安全/可追溯） | **CONFIRMED ✗ · 两侧独立点名同一类** |
| 3 | 异常态消息可操作吗 | ✗（1 处漏项，5 处已指定） | ✗（大面积只写禁令） | **CONFIRMED ✗**（Claude 侧更精确：漏的是 footage 半途场景） |
| 4 | 逃生舱/覆盖是否齐全 | ✗（B 相位裁剪无覆盖口） | 部分 | **CONFIRMED ✗（弱）** |
| 5 | 迁移日体验 | ✗（兜底路径未工程化进产物） | ✗（在飞 map 无探测无交接） | **CONFIRMED ✗ · 两侧同指** |
| 6 | 同构声称是否属实 | ✗（实测 2 处未承认差异） | ✗（实测 3 处） | **CONFIRMED ✗**（合并后 ≥5 处，见 F-14 改写） |

### DX 记分卡（8 维）

| 维度 | 分 | 依据 |
|---|---|---|
| 首次产出时间 | 6/10 | 三态路由清楚；新增七维 B 相位的摩擦增量未量化，也无「先给骨架再细化」契约 |
| 指令人机工效 | 4/10 | B 相位单节要装 8 类机制；无「做完 X 才能进 Y」的强制序，不可见的记账动作最先被跳过 |
| 异常态消息 | 3/10 | 12 个状态里 7 个只写 MUST NOT、不写操作者看到什么/能做什么（见 Section 2 表） |
| 逃生舱 | 6/10 | 保留了 requirements.md 逃生舱、review 跳过授权、显式覆盖分档；**缺**「跳过 B 拷问」的显式授权口 |
| 迁移体验 | 3/10 | 在飞 wayfinder map 无探测、无引导交接，只有「手工转录」一句 |
| 一致性（与 sdflow-spec） | 5/10 | A/B/C 词汇与增量落盘一致；B 可跳过、memo 无身份层、重入范围更窄——三处实质分叉未成表 |
| 文档可发现性 | 8/10 | frontmatter 指路句与前置条件保留（tasks 1.1 显式防丢，对应 spec Requirement #8）✅ |
| 升级安全 | 5/10 | 分发链路模型写错（F-8）；回滚路径清楚（revert merge） |
| **总分** | **5/10** | |

---

## Findings（主 session 综合裁决 · 合并去重后）

> 严重度按 autoplan 口径；置信度为主 session 对抗裁决后的值。
> **带 ✅亲验 的条目 = 主 session 自己跑命令 / 开文件确认过，不是转述 voice。**

### F-1 · [critical · 高置信 ✅亲验] C1 前提证伪：matt 有 4 个已安装的活消费方

- **证据**：`openspec/matt/issue-tracker.md:16`「当 `to-tickets`、`triage`、`to-spec` 或 `qa`
  需要发布、读取或更新工作项时：…」；`ls ~/.claude/skills/` 实测 **`qa` / `to-spec` /
  `to-tickets` / `triage` 四个 skill 全部已安装**。
- **为什么 C1 会漏**：C1 的检验方法是「全仓 grep `openspec/matt` 路径 + 看有无代码读它」。
  这四个消费方是**仓外安装的指令驱动 skill**，它们靠 `CLAUDE.md` / `AGENTS.md` 的
  「## Agent skills」三段（Issue tracker / Triage labels / Domain docs）找到路径——
  grep 仓内代码对它们结构性失明。
- **牵连**：`### Domain docs` 一段（「单一上下文布局：`openspec/CONTEXT.md` 与 `openspec/adr/`」）
  是**与 wayfinder 无关的通用治理配置**，删掉它，那四个 skill 在本仓失去领域文档指路。
- **注意**：D2 是真人 2026-08-05 拍板的。本条**不推翻 D2**，只报告「拍板所依据的 C1 不成立」——
  翻不翻是真人的事。**上抛设计门（Q1）。**

### F-2 · [high · 高置信 ✅亲验] C3 前提证伪 + 6.4 演练不可执行

- **证据**：`find . -type d -name footage` **全仓零命中**；
  `openspec/roadmaps/issues-triage-2026-08/` 实际只含 **`roadmap.md` 一个文件**；
  archive 下 `workflow-cost-optimization` / `mechanical-layer-hardening` 是**四件套 + memo**，
  文本里提到 footage，但**没有 footage 目录**。
- **两个后果**：
  1. C3 按字面读不成立（存量 footage 不在本仓）。**但冻结条款仍必要**——skill 经全局 symlink
     分发给一切消费仓，目标态的 producer（旧版 skill）确实产出过 footage。**这是「锚目标态、
     不拿现状反驳目标」的正解，条款不该砍**，只是 C3 的依据要改写。
  2. tasks 6.4 指定 `issues-triage-2026-08` 做续跑演练来证明冻结条款——该包**没有 footage**，
     演练**证不到任何冻结分支**。Success Metrics 第 5 条随之落空。
- **修复**：① C3 改写为「目标态 producer（旧版 skill）会产出 footage，消费仓存量不可见但必然存在」；
  ② 6.4 改为「构造 fixture：复制一个存量包 + 手工造 `footage/map.md` + 一张 open 票，跑续跑/重入/
  收尾三条路径，断言不迁移、不新增票、不阻塞收尾」。

### F-3 · [critical · 高置信 · 四源收敛] memo「定稿标记」无定义 ⇒ 重入协议不可实现

- **收敛度**：hr-tg cross-model voice #1、Codex eng #1、Codex DX #3 **三个独立冷上下文**
  各自单独判为 critical/high，主 session 亲验第四次确认。**本轮最高收敛项。**
- **证据**：delta spec 的 ADDED「B 相位拷问与增量落盘」写「探测未定稿 memo
  （`openspec/roadmaps/*/memo.md` 存在且**无定稿标记**）」；而 D4 明确「头部只记包名 + 日期，
  无 frontmatter/decision_hash 机械核验」⇒ **「定稿标记」在全部四件套里没有任何字面定义**。
- **根因（亲验）**：`sdflow-spec/SKILL.md:314-319` 的 `decision_hash` 是**一物两用**——
  既做身份核验，又做 draft/final 状态位（`留空`=草稿，B.8⑤ 补齐=定稿）。
  D4 只论证了「不需要身份核验」，却把**状态位一起砍掉了**，没有补替代。
- 🔴 **加重（Claude eng 镜独家 · 主 session 亲验）**：该状态位**今天就存在**——
  `sdflow-roadmap/references/memo-template.md:27` 现有 `> 状态：DRAFT / FINAL` 一行。
  而 D13 与 task 2.1 把新模板头部规格钉为「**头部包名 + 日期**」，只字未提状态字段
  ⇒ **重写会把唯一现成的候选载体主动删掉**，同时 D4 又堵死了 hash 式替代。
  两头夹击 ⇒ 这不是「忘了定义」，是「现有的被删、替代的被否」。
- **修复（最简，不违 D4）**：**保留** memo 头部的 `状态：DRAFT / FINAL` 一行（或改写为
  `Status: draft|finalized` + 定稿日期），并在 delta spec 与 SKILL.md 正文里**显式点名
  该字段就是「定稿标记」判据的实现载体**。这不是 D4 否掉的 hash/schema 机械层，是状态位本身。
  并补规范：命中 ≥2 个 draft 时怎么呈现、「新开」对既有 draft 做什么。

### F-4 · [high · 中置信] 「内化」是文本承接，不是能力等价

- **来源**：Codex CEO #2（critical）。主 session 裁决：**成立但降级为 high**。
- **实质**：wayfinder 的 map + 票承载 frontier 排序、依赖关系、claim、闭环门；
  memo 是线性追加的决策文本。delta 明确删除了「收尾 checklist ④ wayfinder 闭环」这道
  **唯一的未决项闭环门**，并把存量 open/claimed 票判为「历史遗留、不阻塞收尾」。
  ⇒ 「未决的规划问题」从有门禁的显式状态，变成 memo 正文里的一句话。
- **降级理由**：真人在 D7 显式拍板了「④ 整项删除——检查对象不复存在」。
  检查对象（wayfinder 票）确实不复存在，这一步没错。
  **但「未决项闭环」这个能力本身**在新流程里没有承接物——这是 D7 没被问到的那一半。
- **修复（最简）**：memo 增一个 `## 未决项` 小节 + 收尾 checklist ④（memo 对账）扩一句
  「未决项小节非空时须逐条标 已决/显式延后/放弃，MUST NOT 带未决项定稿」。
  零新机械层，复用已有的 checklist ④。**上抛设计门（Q2）——这是补能力还是接受缺口，是 scope 判断。**

### F-5 · [high · 高置信 ✅亲验] B 相位「停止条件」在 spec 里完全缺失

- **证据**：`design.md:78` 与 `tasks.md:10` 都列了「停止条件」，
  但 delta spec 的 ADDED「B 相位拷问与增量落盘」**全文无任何收敛判据**——
  grep「停止条件」在 `specs/roadmap-planning/spec.md` 零命中。
- **对照（亲验）**：`sdflow-spec/SKILL.md:348` 有 B.5「停止信号（**最小充分条件**，
  MUST NOT 用形容词）」，且带硬约束「只有主 session 的判断、没有锚 ⇒ MUST NOT 计入已站稳」。
  同构声称在这一点上落空。
- **后果**：七维拷问无收敛判据 = 无界摩擦，或者反过来——agent 自行判「够了」，B 相位形同虚设。
- **修复**：spec 补一条规范：每个**被裁剪进本次**的维度须落一个终态（`已决` /
  `显式延后（附触发条件）` / `不适用`），全部维度有终态才可进 C。

### F-6 · [medium · 高置信 ✅亲验] 「实战案例」整节静默丢失

- **证据**：`sdflow-roadmap/SKILL.md:624-635` 是独立 `##` 小节「实战案例：博客 v2 重建（2026-04-19）」；
  `design.md:72-81` 的新骨架**完全没有它**，proposal / tasks / decision-memo **全文未提**。
- **后果**：实现者按骨架整体重写 ⇒ 该节静默消失，且无人做过「留还是删」的判断。
  （附带：该节正文引用「上文『结晶：产出三件套』」，若留下不改则改名后成为悬空引用。）
- **修复**：骨架显式写明处置（建议**删**：其中「彼时结构含独立需求文件…现行流程见上文」
  已是考古层，正合 DOC-1「正文即最终态」；删掉即可，但要**明写**而非静默）。

### F-7 · [high · 高置信 · 三源收敛] continue/replan 的「只删本次新增」不可安全实现

- **收敛度**：hr-tg voice #2、Codex eng #2、Codex DX #4。
- **证据**：delta spec 的 ADDED Requirement 要求「continue / replan 场景只删本次新增内容，
  MUST NOT 动既有文件」，但 memo 无 run-id、无 manifest、无段落边界 ⇒ **无可执行的归属判据**；
  且该 Requirement 的 5 个 Scenario 里**只有 create 场景的放弃**，continue/replan 放弃无 Scenario。
- **后果**：agent 要么跳过清理，要么按猜测删——后者是删既有内容的破坏性动作。
- **修复（最简，二选一，推荐前者）**：① **continue/replan 一律不自动删**，只在 task-log 留
  一行「本次 B 放弃」痕迹（与「拷问中途放弃未删目录，由下次重入呈现」的既有接受口径一致）；
  ② 或 B 相位写入一律 append-only 且带 run 标记，删除按标记枚举。
  并补 continue-abandon / replan-abandon 两个 Scenario。

### F-8 · [high · 高置信 ✅亲验] 分发链路模型写错 + 残留面被自己的白名单藏住

两件事同源，合并一条：

- **(a) 分发模型错**：proposal〔TG-20〕写「bundle 改动需 `sdflow-init update` 推送」，
  design Risks 的「下游消费仓漂移」也建在这个模型上。**实测不成立**：
  `sdflow-init/scripts/init.py:213` 的 docstring 明写「R-MRF-1 分层部署：**默认只铺 `tools/` 子树**
  （规则经全局 canonical 解析，不复制进消费仓）。`full=True` 整 bundle 铺设——**仅供 toolkit 源仓
  `update --dev`**」。⇒ 消费仓跑 `sdflow-init update` **根本不会**收到
  `ff-generation-constraints.md` / `workflow-history.md` 的改动；它们经全局 canonical
  （`~/.sdflow/workflow/` → symlink 到运行 checkout）解析，与 skill symlink **走同一条通道**。
  真正的风险面是另一个：**有本地 `openspec/workflow/` 规则副本（pin）的消费仓**——
  它遮蔽全局且 `update` 不刷新（`init.py:329` 的「反静默守卫·陈旧遮蔽」正是为此）。
- **(b) 残留面**：`docs/external-dependencies.md` **§8「内部跨 Skill 依赖」的依赖图 `:148`**
  仍有 `/grilling、/domain-modeling`；tasks 5.4 **只说删 §5 的 Wayfinder 依赖节**，
  而 tasks 6.1 的白名单把**整个 `docs/`** 排除 ⇒ 残留扫描**正好照不到它**。
  加剧因素（亲验）：该文件**在 main 上不存在**，是本分支新建的活文档（+177 行），
  把它当「`docs/` 历史文档」白名单掉是错的分类。
- **修复**：① 改写 TG-20 与 Risks 的分发段为真实模型（canonical symlink 主路径 + pin 遮蔽为真风险）；
  ② tasks 5.4 扩到「§5 依赖节 + §8 依赖图」；③ tasks 6.1 白名单从 `docs/` 收窄为**具名历史文档**。

### F-9 · [medium · 高置信 ✅亲验] TG-08 命中但 design 缺两个必填槽

- **证据**：TG-08（修改外部依赖）在 `trigger-catalog.md` 的模版槽列写明
  「design: 失败模式表(BASE-06) + 可观测性(BASE-11)」；`design.md` 的 14 个小节里**两者皆无**
  （只有一个 `## Risks / Trade-offs`，是风险叙述不是失败模式表）。
- **修复**：把本报告 Section 2 的失败模式表并入 design.md；可观测性一节按本 skill 实际形态写
  （无日志/指标面 ⇒ 写「可观测性 = 判定留痕三点 + memo 增量落盘 + task-log 记录」，
  并说明这就是本 skill 的全部可观测面）。

### F-10 · [medium · 中置信 ✅亲验] 存量包有第三种形态（单文件），两条兼容条款都没覆盖

- **证据**：`openspec/roadmaps/issues-triage-2026-08/` 只有 `roadmap.md`；
  `openspec/roadmaps/archive/high-value-issues-cleanup/` 与 `archive/openspec-1.7.0-followup/`
  同样只有 `roadmap.md`。delta 的兼容条款只覆盖「四件套包」与「含 footage 的包」两种形态。
- **后果**：续跑单文件包时，「三件套相互引用完整」（收尾 ②）必然不通过（缺 design/task-log），
  而没有任何条款说这算合法历史形态。
- **修复**：兼容条款把「缺件包」一并纳入（或明说单文件包不属续跑对象、需先补齐）。

### F-11 · [medium · 中置信 ✅亲验] 判定点①要求写 task-log.md，而该文件此时不存在

- **证据**：delta ADDED「讨论层三态路由」+ 其 Scenario「路由判定显式留痕」要求
  「判定依据…写入 task-log.md」；但 `{name}` 在**B 起手**才确定、目录在 B 起手（或直接生成路径的
  落盘前）才建 ⇒ 相位 A 收束时刻 `openspec/roadmaps/{name}/task-log.md` **不存在**。
- **诚实边界**：这个矛盾在现行 `SKILL.md:275` 里**已经存在**。但本 change 把它**重新写进一条
  新的 ADDED Requirement 并配了专门的 Scenario** ⇒ 是新契约面上的缺陷，不能以「现状也这样」放行。
- **修复**：改为「判定依据在对话中显式陈述一行；包目录建立后**补记**进 task-log.md」，
  或把「建包 + task-log 落盘」前移到相位 A 收束。

### F-12 · [low · 中置信] 「商业化信号」作为唯一分档变量偏窄

- **来源**：Codex CEO #5（判 high）。主 session 裁决：**降级 low，且不建议本次改**。
- **理由**：该词表是**现行 spec 已有**的分档判据，本 change 只做**术语改名、词表不变**（D5 明确）。
  Codex 提的「按决策风险路由」是**扩大目标范围**（通则③的「加宽」），不属本 change scope。
- **处置**：一行带过，**不进修改清单**；若真人想改，是另一个 change。

### F-13 · [low · 低置信] 「直接生成」快路径几乎不可达

- **来源**：Codex DX #1（判 critical）。主 session 裁决：**降级 low，裁掉主张、保留半条**。
- **裁掉的部分**：「gate-0 五项太严 ⇒ 快路径名存实亡」——gate-0 五项（`SKILL.md:265-271`）
  是**现行设计**，D6 是真人 2026-08-05 明确拍板保留的，且 D6 的论证（两关独立）站得住。
  这属于重新论证一个已拍板的决定。
- **保留的半条**：新增的七维 B 相位**确实是新摩擦**，四件套里**没有任何一处量化或承认这个增量**。
  建议 proposal 的 Success Metrics 或 design 的 Risks 补一句摩擦评估。

### F-14 · [low · 中置信] 「与 sdflow-spec 逐节同构」过度声称

- **来源**：Codex DX #8。主 session 裁决：成立，但**表述问题、非设计缺陷**。
- **证据**：design.md:144 说差异「只保留在两处（产物形态、无 ship gate ⇒ memo 轻量化）」。
  实测至少还有三处实质分叉：① sdflow-spec 的 B **不可跳过**，roadmap 的可跳过；
  ② sdflow-spec 的 memo 有身份/状态层，roadmap 的没有（F-3）；
  ③ sdflow-spec 的重入探测覆盖全部在途 change，roadmap 只覆盖未定稿 memo（不覆盖直接生成路径产物）。
- **修复**：把「只有两处差异」改为一张分叉表（3-5 行），或把措辞降为「共享 A/B/C 词汇与增量落盘模式」。
- **[双声补强]** 两个独立冷镜各自实测出**不同**的分叉，合并后 **≥5 处**：
  ① B 可跳过 vs 不可跳过 ② memo 有无状态/身份层 ③ 重入探测覆盖面
  ④ **sdflow-spec 用 5 个 `references/*.md` 按需加载压密度，roadmap 骨架全内联**
  ⑤ **sdflow-spec 的 B.6（惰性钩子）+ B.7（收敛前逐条回扫）是两道防线，roadmap 只一层**。
  ⑤ 尤其值得注意——B.7 的原文自述就是「B.6 漏掉的在此兜底捕获」，砍掉即砍掉兜底。

### F-15 · [high · 高置信 ✅亲验] `openspec/CONTEXT.md` 实有第三处词条，三份产物一律只认「两处」

- **证据**：`openspec/CONTEXT.md` 的 **`ticket（实现分解单位）`** 词条正文明写
  「**matt 套件中 wayfinder 的讨论 ticket（map 的 `issues/<NN>`）是另一种 ticket**（讨论单位，
  非实现分解），需限定词区分」，`_Avoid_` 行还专列「把 wayfinder 讨论 ticket 与实现 ticket 混为一谈」。
  而 `proposal.md:70` / `design.md:67` / `tasks.md:37` **一律写「词条两处」**（footage 重写 + 商业化信号新增）。
- **后果**：改完后这条词条会把一个已被冻结为历史遗留的机制，描述成仍需「限定词区分」的现役概念；
  且它含字面 `wayfinder`，6.1 的残留 grep 会命中，而白名单和任务都没预期到它 ⇒ 实现者会困惑。
- **附带**：`footage` 词条正文还含「决策**结晶**」——改名的第二个消费点，task 5.2 重写该词条时会顺带覆盖，
  但同样没被点名。
- **修复**：三份产物统一改为「词条**三处**」，5.2 明确 ticket 词条的改法。

### F-16 · [high · 高置信 ✅亲验] 6.1 残留扫描的白名单是枚举式的，实测遗漏 ≥7 处合法保留文件

- **实测**（全仓 grep，不带 `--include`，扣除白名单已覆盖项后仍命中的**活文件**）：
  - **DOC-1 语境「考古层」** —— `sdflow-architecture/references/{review-lenses,intake-questionnaire,decomposition-rules,quality-criteria}.md`（4）、
    `openspec/adr/0020-sad-ecosystem-position-and-lifecycle.md`（1）、`openspec/issues/INDEX.md`（1）
    ⇒ **6 处**。白名单只点名了 `rules/doc-authoring.md`、`CLAUDE.md` 基准区、`T169` 三处。
  - **同形异义「野心」** —— `openspec/issues/open/todo/T227.md`（「spec 野心之外的加固」，与商业化信号无关）⇒ **1 处**。
  - **D10 明确拍板保留的规则本身** —— `sdflow-init/assets/workflow/ff-generation-constraints.md:46-47`
    的 `wayfinder-resolved:` 前缀规则**不在白名单里**，而它正是 D10 拍板「保留 + 加 legacy 标注」的那条。
- **后果**：6.1 不是能干净跑绿/跑红的机械门，而是「跑完还要人工甄别一堆已知假阳性」。
  更危险的是：若执行者照单全收去「修」这些命中，**会直接违反 C5**（禁止全局替换 DOC-1 语境的「考古层」）。
- **修复**：白名单改为**规则化描述**而非枚举（如「凡『考古层』紧邻 DOC-1 / BASE-30 语境者一律排除」），
  并把 `ff-generation-constraints.md` 显式加入并注明理由（D10 legacy 保留）。

### F-17 · [high · 中置信] TG-22 假设的「明确兜底路径」没有被工程化进任何运行时产物

- **证据**：`proposal.md:113-115`（TG-22）称在飞 wayfinder 讨论的失效影响「有明确兜底路径」=
  「讨论要点从 map 手工转录进 memo 继续」。但这句只出现在 `decision-memo.md`（本 change 的过程件）
  与 `design.md` 的 Non-Goals（设计文档）——**两者运行时 agent 都不读**。
  delta spec 的「历史存档引用边界与存量 footage 冻结」Requirement 全文**没有一句**要求 SKILL.md
  指导 agent 去读 `footage/map.md` 提炼要点写进 memo。
- **后果**：某消费仓有半途 map（讨论未收敛、无三件套）时，续跑走到「包已存在 → continue」，
  B 相位从零拷问，历史讨论对执行 agent 不可见。「明确兜底路径」只存在于人的假设里。
- **修复**：二选一——① spec 补一条 Scenario（「包含 `footage/` 但无三件套 ⇒ continue 判定前
  SHALL 提示操作者是否先摘要要点写入 memo」）；② 或如实把假设改为「无自动化兜底，靠操作者手工转录」。

### F-18 · [medium · 高置信 ✅亲验] 同一 change 内「B 起手几步」计数不一致

- **证据**：`design.md:78`「起手**四步**」+ `decision-memo.md:117`「B 起手**四步**：判定进 B → 定 `{name}`
  → 判同名包 → 建目录+草稿 memo」 **vs** `tasks.md:10`「起手**三步**」+ delta spec「起手完成**三步**」
  （均把「判定进 B」排除在外）。四份产物二比二分裂。
- **修复**：统一为「三步」（「判定进 B」是进入前提而非步骤），四处措辞对齐。

### F-19 · [medium · 高置信 ✅亲验] `openspec/INDEX.md:52` 是整句陈旧，5.5 措辞有「浅改」风险

- **证据**：该行完整描述了本 change 要删的全部旧机制——「讨论层双判据路由（explore/wayfinder/office-hours）、
  footage 落盘位置与引用边界（**含票状态机 open/claimed/resolved/abandoned**）、review 按**野心**分档、
  收尾 checklist **五项**软门（含 wayfinder 闭环全目录扫描）」。
  而 `tasks.md:40`（5.5）措辞是「核对……与『**野心**』措辞残留，随 delta 同步」。
- **后果**：若被理解成「只替换『野心』一个词」，会漏改整句结构性描述。
- **修复**：5.5 改为「按新结构（三态路由 / 历史存档 / checklist 四项）**整句重写**，非局部替词」。

### F-20 · [medium · 中置信] 三类状态机边角是沉默遗漏，不是显式接受的边角

- **证据**：本 change 自己派给 hr-tg cross-model 的 context 明确列了三类应死磕的异常转换
  （并发两 session 同包 / 建了目录但草稿 memo 写失败 / 重入命中多个未定稿包）。
  `decision-memo.md`「接受的边角」逐条裁定了四类（B 中断损失 / memo 无身份核验 / ⑤ 盲区 / 半途包残留），
  **唯独这三类不在其中**。
- **为什么这条单独立项**：按本仓基准 4 的五问，**沉默遗漏与显式裁定接受，风险性质不同**——
  前者可能是真没想到，后者才是有意识的简化。
- **修复**：补一句显式裁定即可（如「并发：无锁机制，后写覆盖前写——概率低（单人操作）、
  影响可逆（git 可追溯）、完美成本 = 引入锁，不做」），并写进 SKILL.md 让操作者知情。

### F-21 · [medium · 高置信 ✅亲验] proposal Why 段把两类性质不同的依赖打包论证

- **证据（实测）**：`~/.codex/skills/` 下 **`gstack-office-hours` 存在**——office-hours **双宿主皆可用**；
  且现行 `SKILL.md` 的 office-hours 分支**没有任何宿主探测/降级逻辑**（那套机制只在 wayfinder 分支）。
- ⇒ proposal Why 的「每个都拖着宿主探测、降级路径……Codex 宿主接地实测无 wayfinder」
  **只对 wayfinder / grilling / domain-modeling 成立，对 office-hours 不成立**。
- **注意**：office-hours 该不该内化，理由本身站得住（结构对齐 + 维护面精简）——问题只在
  **用一句话打包论证掩盖了这个区分**，属 `premise-verification.md` 面的精度问题。
- **修复**：Why 段拆成两句，各自给各自的理由。

### F-22 · [medium · 中置信] 「为何不并入 sdflow-spec」这个候选从未被分析

- **证据**：design.md Goals 明确写「新 SKILL.md 的相位协议与 sdflow-spec **逐节同构**」
  （A/B/C 三相位、增量落盘、B 起手建目录、create/continue/replan 判定全部对齐）。
  在这种收敛程度下，「两个 500+ 行的独立 skill 长期并存各自维护」本身是个需要论证的选择，
  但 D1–D14 **没有任何一条**讨论过它。
- **注意**：`SKILL.md:158-169` 给的角色区分（roadmap = 长期真相源 / change = 短期经 CLI）是合理的，
  但「合理」不等于「已论证过反面」。**本条不主张合并**（那是加宽），只指出决策记录有洞。
- **修复**：decision-memo 或 ADR 补一句显式的「为何维持两个 skill」论证。

### F-23 · [medium · 中置信] matt fold 的因果表述不准

- **证据（实测 git log）**：`sdflow-issues`（本仓实际在用的问题追踪）生于**首个 commit（2026-07-03）**，
  早于 `openspec/matt/` 的建立（2026-07-10）**一周**；本仓自始至终用的是 `sdflow-issues`（T1…T230 那套）。
  ⇒ matt 的 issue-tracker 角色**从未真正投入使用**，它**早在本 change 之前就是事实性废弃**。
- **影响**：D2 的论证角度是「roadmap 重构后 matt 失去全部活消费方 ⇒ 一并移除」（fold 因果）。
  实际应为「matt 是历史遗留死配置，独立可删；与本 change 同批做的理由是操作成本低 + 避免半改状态」。
  **结论不变（该删），措辞需准确**——这直接关系到 Q1 该怎么拍。
- **修复**：D2 补一句因果澄清。

### F-24 · [low · 中置信] escape hatch 不对称：B 相位维度裁剪无覆盖口

- 同一份 spec 已给 review 分档建了「显式覆盖」先例（强制三连审 / 强制单审），
  也给存量形态建了逃生舱（保留 requirements.md），也给 review 建了「跳过授权」；
  但 **B 相位内部的七维裁剪没有对应的操作者覆盖机制**（「这次不用查⑦前提质疑」无处安放）。
- **修复**：补一句覆盖机制，或明说取舍理由（一句话即可，不必建机制）。

### F-25 · [low · 中置信] 放弃清理未要求删除前复述完整路径

- delta spec 的「create 场景中途放弃」Scenario 只规定结果（删除目录、不留半途包），
  未要求 agent 删除前向操作者复述「即将删除 `openspec/roadmaps/{name}/`」。
- 本仓 CLAUDE.md 全局安全规则明写「Never delete files or run destructive commands without
  explicit confirmation」。「放弃」来自操作者本人可论证为隐式同意，但**具体删了什么**操作者看不见。
- **修复**：Scenario 补一句「删除前 SHALL 向操作者复述将被删除的完整路径」。
  （与 F-7 的修复方向一致，可合并实施。）

---

## Required Outputs

### NOT in scope（本轮明确不做的）

| 项 | 理由 |
|---|---|
| 按决策风险重做分档变量（F-12） | 扩大目标范围，属另一个 change |
| 重新论证 gate-0 五项 / 直接生成路径（F-13 主张部分） | D6 真人已拍板，重复论证违反「人重申后 MUST 立即照做」 |
| 内化 review 层 | D1 真人拍板保留 |
| 存量 roadmap 包结构迁移 | proposal Non-Goals（T129 受控延后） |
| 给 memo 补 hash/schema 机械层 | D4 真人拍板；F-3 的修复是**状态位**不是 hash 层，不冲突 |

### What already exists（复用面）

见上方 0B 表。核心结论：`sdflow-spec` 的 B 相位机制是现成的、可逐条对照的复用源，
本 change 复用了它的**落盘节奏**但漏掉了它的**状态位**（F-3）。

### Dream state delta

见 0C。方向一致；唯一反向缺口 = 两个 skill 的纪要状态表达分叉。

### Failure Modes Registry

见 Section 2 表（7 个 CRITICAL GAP）。

### Diagrams

- 依赖图（before/after）：见 Section 1 ✅（design.md 已有，本报告补了 matt 消费方标注）
- 状态机图：design.md:102 已有 ✅，但**缺 4 条异常转换**（C 部分失败 / 并发 / 多 draft / 单文件包）
- 数据流图：N/A（无数据管道）
- 部署时序图：**缺**，且现有分发叙述是错的（F-8）⇒ 建议补一张三行时序

### Stale Diagram Audit

`design.md` 的状态机图与三态路由图均为本 change 新画，与 delta spec 一致（除 F-11 的 task-log 时点）。
现行 `SKILL.md` 内无 ASCII 图需同步。

---

## Implementation Tasks（本广审产出的可执行清单）

- [ ] **T1 (P1, human: ~1h / CC: ~10min) — decision-memo** — 改写 C1，如实记入「matt 有 4 个已安装消费方」
  - Surfaced by: F-1 · `openspec/matt/issue-tracker.md:16` + `ls ~/.claude/skills/`
  - Files: `openspec/changes/refactor-roadmap-internalize-deps/decision-memo.md`
- [ ] **T2 (P1, human: ~30min / CC: ~5min) — decision-memo** — 改写 C3 为目标态论证
  - Surfaced by: F-2 · `find . -type d -name footage` 零命中
- [ ] **T3 (P1, human: ~2h / CC: ~15min) — spec delta + design** — memo 增 `Status: draft|finalized` 一行状态位 + 转换时机 + 多 draft/新开语义
  - Surfaced by: F-3（四源收敛）
  - Files: `specs/roadmap-planning/spec.md`, `design.md`, `tasks.md`(1.3/2.1)
- [ ] **T4 (P1, human: ~1h / CC: ~10min) — spec delta** — 补 B 相位停止条件规范条款
  - Surfaced by: F-5 · 对照 `sdflow-spec/SKILL.md:348`
- [ ] **T5 (P1, human: ~1h / CC: ~10min) — spec delta** — continue/replan 放弃改为不自动删 + 补两个 Scenario
  - Surfaced by: F-7（三源收敛）
- [ ] **T6 (P1, human: ~1h / CC: ~10min) — proposal + design + tasks** — 改写分发模型；5.4 扩到 §8；6.1 白名单收窄
  - Surfaced by: F-8 · `init.py:213/329`、`docs/external-dependencies.md:148`
- [ ] **T7 (P1, human: ~1h / CC: ~10min) — tasks** — 6.4 改为构造 fixture 演练
  - Surfaced by: F-2
- [ ] **T8 (P2, human: ~1h / CC: ~10min) — design** — 补 BASE-06 失败模式表 + BASE-11 可观测性
  - Surfaced by: F-9 · TG-08 必填槽
- [ ] **T9 (P2, human: ~30min / CC: ~5min) — design** — 骨架显式写明「实战案例」节的处置
  - Surfaced by: F-6 · `SKILL.md:624-635`
- [ ] **T10 (P2, human: ~30min / CC: ~5min) — spec delta** — 兼容条款纳入单文件/缺件包
  - Surfaced by: F-10
- [ ] **T11 (P2, human: ~30min / CC: ~5min) — spec delta** — 判定点①留痕时点改为「先陈述、建包后补记」
  - Surfaced by: F-11
- [ ] **T12 (P3, human: ~30min / CC: ~5min) — design** — 同构声称改为分叉表
  - Surfaced by: F-14
- [ ] **T13 (P3, human: ~15min / CC: ~2min) — proposal/design** — 补一句七维 B 相位的摩擦增量评估
  - Surfaced by: F-13（保留的半条）
- [ ] **T14 (P1, human: ~30min / CC: ~5min) — 三份产物** — CONTEXT.md 词条「两处」改「三处」+ 5.2 明确 ticket 词条改法
  - Surfaced by: F-15
- [ ] **T15 (P1, human: ~1h / CC: ~10min) — tasks** — 6.1 白名单改规则化描述 + 显式纳入 `ff-generation-constraints.md`
  - Surfaced by: F-16（实测 ≥7 处遗漏）
- [ ] **T16 (P2, human: ~30min / CC: ~5min) — spec delta 或 proposal** — TG-22 兜底路径二选一：补 Scenario 或如实降级表述
  - Surfaced by: F-17
- [ ] **T17 (P2, human: ~15min / CC: ~2min) — design/decision-memo/tasks/spec** — 「起手三步/四步」四处统一
  - Surfaced by: F-18
- [ ] **T18 (P2, human: ~15min / CC: ~3min) — tasks** — 5.5 改为「整句重写」
  - Surfaced by: F-19
- [ ] **T19 (P2, human: ~30min / CC: ~5min) — decision-memo + SKILL.md** — 三类边角显式裁定
  - Surfaced by: F-20
- [ ] **T20 (P2, human: ~15min / CC: ~3min) — proposal** — Why 段拆两句（office-hours 另立理由）
  - Surfaced by: F-21（实测 `~/.codex/skills/gstack-office-hours` 存在）
- [ ] **T21 (P3, human: ~15min / CC: ~3min) — decision-memo** — 补「为何维持两个 skill」论证
  - Surfaced by: F-22
- [ ] **T22 (P2, human: ~10min / CC: ~2min) — decision-memo** — D2 补因果澄清（matt 早已事实废弃）
  - Surfaced by: F-23（git log 实测）
- [ ] **T23 (P3, human: ~10min / CC: ~2min) — spec delta** — B 相位裁剪覆盖口（补机制或说明取舍）
  - Surfaced by: F-24
- [ ] **T24 (P2, human: ~10min / CC: ~2min) — spec delta** — 放弃前复述完整路径（并入 T5）
  - Surfaced by: F-25
- [ ] **T25 (P1, 需人拍板)** — matt 是否拆成独立 change（F-1 的 APPROACH B）
- [ ] **T26 (P1, 需人拍板)** — 未决项闭环能力是否补（F-4）

---

## Completion Summary

```
  +====================================================================+
  |            GSTACK 广审 (autoplan native) — COMPLETION SUMMARY      |
  +====================================================================+
  | Mode selected        | HOLD SCOPE（偏离缺省，理由已写明）           |
  | System Audit         | 分支干净；8 新文件 979 行；零删除            |
  | Step 0               | 5 条承重前提中 3 条被证伪（P2/P3/P5）        |
  | Sec 1 (Arch)         | 1 issue（memo 双职责单点）                   |
  | Sec 2 (Errors)       | 12 条错误路径已映射，7 个 CRITICAL GAP       |
  | Sec 3 (Security)     | 0 新攻击面；破坏性删除并入 F-7 / F-25        |
  | Sec 4 (Tests)        | 覆盖图已产出，2 道真机械门 / 主体零执行覆盖  |
  | Phase 2 (Design/UI)  | SKIPPED（无 UI scope）                       |
  | Phase 3.5 (DX)       | 5/10；8 维记分卡已产出                       |
  +--------------------------------------------------------------------+
  | NOT in scope         | written (5 items)                            |
  | What already exists  | written                                      |
  | Dream state delta    | written                                      |
  | Failure modes        | 12 total, 7 CRITICAL GAPS                    |
  | Findings             | 25 (2 critical / 8 high / 11 medium / 4 low) |
  | Implementation tasks | 26 (9 P1 / 12 P2 / 3 P3 / 2 需人拍板)        |
  | Outside voice        | ran (codex ×3, exit 0) + Claude 子代理 ×3     |
  | 双声 consensus       | CEO 4/6 · Eng 6/6 · DX 5/6 达成一致          |
  | Diagrams produced    | 2 复核 + 1 补（依赖图带消费方标注）           |
  | Stale diagrams       | 0                                            |
  | Unresolved decisions | 2（Q1 matt 拆分 / Q2 未决项闭环）            |
  +====================================================================+
```

### 双声独立贡献分布（供 `/sdflow-retro` 参考）

| 来源 | 独家贡献（唯一报出且被采纳） |
|---|---|
| Codex CEO | F-4（能力等价性）· F-12（分档变量，已裁降） |
| Codex Eng | F-8(b)（`external-dependencies.md` §8 依赖图）· F-8(a) 的 `init.py` 实证 |
| Codex DX | F-13 的摩擦增量半条 · F-14 的 references 密度分叉 |
| hr-tg cross-model | F-8(a) 分发模型证伪（最早报出）· F-11 的 C 相位部分失败面 |
| Claude CEO 子代理 | F-21（office-hours 双宿主）· F-22（并入候选）· F-23（matt 时间线） |
| Claude Eng 子代理 | **F-15（CONTEXT.md 第三处词条）· F-16（白名单 ≥7 处遗漏）· F-3 的 memo-template 加重** |
| Claude DX 子代理 | F-17（兜底路径未工程化）· F-18（步数不一致）· F-19（INDEX 浅改风险）· F-24 · F-25 |
| 主 session 亲验 | **F-1（matt 4 个已安装消费方 — 唯一源）**· F-2 · F-6（实战案例节）· F-9（TG-08 必填槽） |

> **值得记一笔**：F-1 是本轮唯一一条**所有子代理与 voice 都没抓到**的 critical——
> 六个冷镜里有两个专门核过 C1，都只在**仓内** grep 就判「成立」；
> 只有跳出仓、去 `~/.claude/skills/` 看一眼「谁被 matt 文档列为消费方、这些消费方装没装」才照得到。
> 教训：**「无消费方」类断言的检验面必须跨出仓库边界**，指令驱动的消费方不会在 grep 里现形。

### Unresolved Decisions

- **Q1**：matt 移除是否拆成独立 change（F-1 / F-23）——D2 所依据的 C1 已被证伪
  （有 4 个已安装的活消费方），且 fold 的因果表述也不准（matt 早已事实废弃）。重新确认还是照原样。
- **Q2**：「未决项闭环」能力是否补承接物（F-4）——D7 删掉了唯一的闭环门。

**STATUS: DONE_WITH_CONCERNS** —— 广审跑完，**25 条 findings 全部落定**；
2 条需真人在设计 HARD-GATE 拍板，其余 23 条为可直接执行的四件套修订。
findings 全量汇入 `/sdflow-spec-review` Step3 合并池。
