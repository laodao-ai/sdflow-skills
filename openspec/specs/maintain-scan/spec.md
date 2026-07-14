# maintain-scan Specification

## Purpose
`maintain_scan.py` 是 `sdflow-maintain` 的确定性只读扫描核心：对比 `openspec/specs|rules` 与 `INDEX.md`（托管块外）产出双向 set-diff、扫 CLAUDE.md 过时引用、检测 workflow bundle 陈旧遮蔽，四类分节输出只读差异报告。脚本 MUST NOT 写任何文件；不可信输入一律 fail-closed（防「假一致」优先于「假报错」）；归组/是否修复的判断留给 SKILL.md 步骤 4 由模型据报告决定。

## Requirements
### Requirement: specs/rules ↔ INDEX 双向 set-diff

`maintain_scan.py` SHALL 扫描 `openspec/specs/` 下所有 `spec.md` 与 `openspec/rules/` 下所有 `.md`（`openspec/rules/` 为**可选**目录，缺失时按空集处理、非错误——见「坏输入 fail-closed」），解析 `INDEX.md` **sdflow-init 托管块之外**的已列表格条目，产出双向 set-diff 只读报告，分两类：**新增未索引**（文件系统存在、INDEX 未列）与 **已删未清理**（INDEX 列出、文件系统不存在）。脚本 MUST NOT 修改任何文件。〔grill-amendment：rules/ 可选 + 托管块排除〕

**join-key = 链接目标路径，非首列名〔spec-review-amendment H3/D1〕**：「已列条目」的提取 MUST 锚在**表格行链接目标路径模式**——只纳入链接匹配 `specs/{name}/spec.md`（→ spec 类）或 `rules/{name}.md`（→ rule 类）的行；链接不匹配这两式的行（如 INDEX 里指向 `retro/report.md`、`roadmaps/…` 的活文档索引行）**一律不参与 set-diff**。类型（spec/rule）由链接路径判，非首列名。理由：本仓真实 `INDEX.md` 托管块外含 `retro-report`→`retro/report.md` 一类非-spec/rule 行，按首列名 join 会误报「已删未清理」（dogfood 假阳）。

解析 INDEX 时 MUST 排除 sdflow-init 托管块——该块索引 workflow bundle（`openspec/workflow/*.md`），归 sdflow-init（`update` 刷新），非本能力的 set-diff 对象。**托管块边界按稳定 token 子串界定〔spec-review-amendment H1/Q2〕**：检测 `opsx-init:rules:start` / `opsx-init:rules:end` **token 子串**（`token in line`，镜像 `init.py:_find_marker_line` 的 `start.split()[1]` 口径），**MUST NOT 硬编裸短串** `<!-- opsx-init:rules:start -->`——真实 `init.MARK_IDX[0]` 是带中文尾注的长形（`<!-- opsx-init:rules:start —— 由 sdflow-init 维护，勿手改本区块 -->`），裸短串非其子串，照字面精确匹配会在每个真实仓（含本仓 dogfood）START 匹配失败→只配到 end→误判不配对→假 fail-closed。marker 检测 MUST fence-aware（跳 ``` 围栏内的 marker 示例，本仓是 marker 示例雷区）。

#### Scenario: 文件系统有新 spec 未进 INDEX
- **WHEN** `openspec/specs/foo/spec.md` 存在但 `INDEX.md` 未列 `foo`
- **THEN** 报告在「新增未索引」类下列出 `foo`（spec 类），退出码 0（有差异不算错误）
- **AND** `INDEX.md` 与文件系统内容保持不变（脚本零写）

#### Scenario: INDEX 列了已删除的 rule
- **WHEN** `INDEX.md` 托管块之外列出 rule `bar` 但 `openspec/rules/bar.md` 不存在
- **THEN** 报告在「已删未清理」类下列出 `bar`（rule 类）

#### Scenario: 完全一致
- **WHEN** specs/rules 集合与 INDEX 托管块之外已列条目完全一致
- **THEN** 报告输出「一致，无差异」标记，退出码 0

#### Scenario: 不误纳 sdflow-init 托管块条目
- **WHEN** `INDEX.md` 的 `opsx-init:rules` 托管块内列出 workflow bundle 条目（如 `trigger-catalog`），而 `openspec/rules/trigger-catalog.md` 不存在
- **THEN** 报告 MUST NOT 把托管块内条目当「已删未清理」——托管块被整段跳过，不产生该误报

#### Scenario: 非 specs/rules 链接行不误纳〔spec-review-amendment H3/D1〕
- **WHEN** `INDEX.md` 托管块外有一行链接指向 `retro/report.md`（既非 `specs/*/spec.md` 也非 `rules/*.md`）
- **THEN** 该行 MUST NOT 参与 set-diff，报告 MUST NOT 报「已删未清理: retro-report」
- **AND** 本仓 dogfood（真实 INDEX.md）跑出「无已删未清理」（retro-report 不被误纳）

#### Scenario: 疑似 spec 条目误置于托管块内→告警〔spec-review-amendment M8/D11〕
- **WHEN** 用户误把一条 `specs/foo/spec.md` 链接行写进 `opsx-init:rules` 托管块**内部**
- **THEN** maintain 跳过托管块时探到块内 `specs/*/spec.md` 模式 → 报「疑似 spec 条目误置于 init 托管块内」告警，而非无条件静默跳过（低成本堵审计无人区）

### Requirement: CLAUDE.md 过时引用扫描

`maintain_scan.py` SHALL 扫描根 `CLAUDE.md` 与各子目录 `CLAUDE.md`，报告其中引用了**已从文件系统删除**的 spec/rule 路径的位置（文件 + 行号），仅报告不修复。

**「引用」的匹配契约 MUST 显式定义〔spec-review-amendment M1/D4〕**：一次「引用」= 正则匹配 `openspec/(specs|rules)/<name>(/|\.md)` 形态的路径串，其中 `<name>` ∈ `[a-z0-9-]+` 且与「已删条目集」取交才报。MUST 排除：① ``` 代码围栏 / 行内 `code` 内的路径提及（文档举例非真引用）；② 字面占位符（`{name}`/`{change}` 等花括号 token）；③ 泛指路径（`openspec/specs/` 无具体 `<name>`）。理由：本仓 CLAUDE.md 大量泛指路径 + 占位符 + 举例，无匹配契约会在 dogfood 上刷屏误报（同 gate 子串 dogfood 自指坑）。

#### Scenario: CLAUDE.md 引用已删 spec
- **WHEN** 某 `CLAUDE.md` 含指向 `openspec/specs/gone/` 的引用（`gone` ∈ 已删集），非代码围栏内、非占位符
- **THEN** 报告「过时引用」小节列出该 `CLAUDE.md` 路径 + 行号 + 被引的已删条目名

#### Scenario: 占位符/泛指/围栏内提及不误报〔spec-review-amendment M1/D4〕
- **WHEN** CLAUDE.md 含 `openspec/roadmaps/{name}/`（占位符）、`openspec/specs/`（泛指无名）、或 ``` 围栏内的 `openspec/specs/foo/` 举例
- **THEN** 三者 MUST NOT 报为「过时引用」（匹配契约排除占位符/泛指/围栏）

#### Scenario: 无过时引用
- **WHEN** 所有 CLAUDE.md 引用的 spec/rule 路径均存在
- **THEN** 报告「过时引用」小节为空/标记无

### Requirement: workflow bundle 陈旧遮蔽兜底扫描

`maintain_scan.py` SHALL 检查 `openspec/workflow/` 下是否残留规则文件本体（判据 = `RULE_MARKERS`：`workflow.md` / `spec-checklists` / `code-checklists` 任一存在，及仓根 `hack/checkpoint-commit.sh` 孤儿副本），命中则报告为「陈旧遮蔽」告警——因规则真相源应为全局 canonical，仓内残留规则副本会 pin 遮蔽全局。仅报告不删除。judgement（是否删/pin）留人。此为 sdflow-init `stale_shadow_warnings` 的**周期性兜底消费者**（init 的检查只在 init/update 动作时跑）。〔grill-amendment〕

**告警文案漂移=已知残差 defer〔spec-review-amendment M3/D6〕**：maintain 抄 init 的告警文案 + checkpoint 孤儿路径（第三处跨脚本复述），R-guard 不机验文案（文案守卫脆）。与 `resolve-workflow.sh` bash 第 3 份 RULE_MARKERS 副本同级，**显式登记为已知残差 defer**（记 todolist），非无声留着。maintain 文案不追求逐字等同 init，只需语义等价（遮蔽全局/pin 二选提示）。

#### Scenario: workflow 下残留规则正文
- **WHEN** `openspec/workflow/workflow.md`（规则本体）存在
- **THEN** 报告「陈旧遮蔽」小节列出该残留文件，提示可能 pin 遮蔽全局 canonical

#### Scenario: workflow 仅剩 tools
- **WHEN** `openspec/workflow/` 下只有 `tools/`，无规则正文
- **THEN** 「陈旧遮蔽」小节为空/标记无

### Requirement: 跨脚本共享判据一致性守卫

maintain_scan 与 sdflow-init 共享判据。canonical 定义留 `sdflow-init/scripts/init.py`；maintain_scan 保自包含副本。为堵漂移（T17），pytest MUST 机验一致——不等即 fail。此为 T17 的真闭合（机验同步，非物理单一源）。〔grill-amendment〕

**〔spec-review-amendment H1/Q2·设计门已定 2026-07-09〕** 冷审证 `MARK_IDX` 全串守卫**给假信心**（护常量不护匹配逻辑：消费仓 marker 文案漂移时守卫仍绿、工具却假红）。**决定：删除 MARK_IDX 全串一致性守卫**，maintain 按稳定 token 子串定位托管块 + 守卫断言 `maintain 的 token == init.MARK_IDX[0].split()[1]`（token 是稳定契约），并**加端到端 fixture 守卫**（喂真实 INDEX.md 验托管块被识别+跳过，护匹配逻辑非只护常量字面）。RULE_MARKERS 无稳定子串替身、常量守卫保留。

**〔spec-review-amendment M2/D5〕** 守卫 pytest 用 `importlib.util.spec_from_file_location` 跨 skill 加载 init.py（不 import，照 determ-guards `test_mirror_consistency.py` 先例）；加载失败 MUST **hard-fail 非 silent-skip**（try/except-skip = 真空绿，漂移漏网），但对「sdflow-init 目录整体缺席」场景用显式 path-assert 先判（避免 collect-time ModuleNotFoundError 误红，defer 记 importorskip 兜底）。

#### Scenario: RULE_MARKERS 与 init 不一致
- **WHEN** `maintain_scan.RULE_MARKERS != init.RULE_MARKERS`（有人只改了一处）
- **THEN** 一致性守卫 pytest 失败（非零），CI/手动跑测即暴露漂移

#### Scenario: 托管块 token 与 init 不一致〔spec-review-amendment H1/Q2〕
- **WHEN** maintain_scan 用的托管块 token != `init.MARK_IDX[0].split()[1]`（`opsx-init:rules:start`）
- **THEN** 一致性守卫 pytest 失败，防边界判据漂移致误纳/误跳托管块

#### Scenario: 端到端匹配逻辑守卫〔spec-review-amendment H1/M2〕
- **WHEN** 喂 maintain 一份真实 INDEX.md（长形带尾注 marker）
- **THEN** maintain MUST 正确识别并跳过托管块（护「匹配逻辑」而非只护常量字面）；用带尾注的真实 marker fixture，MUST NOT 用裸短串合成夹具（合成短串会掩盖 H1）

#### Scenario: fence-aware 分支独立合成 fixture 覆盖〔spec-review-amendment 轻grill·low〕
- **WHEN** 真实 INDEX.md 无 ``` 围栏（实测 0 个）→ 上条 fixture 覆盖不到 fence-aware 代码路径
- **THEN** MUST 另加一份**合成 INDEX fixture**（围栏内放个 `opsx-init:rules:start` 示例），验证被跳过——否则 fence-aware 是无测试死代码

#### Scenario: 守卫导入失败 hard-fail〔spec-review-amendment M2/D5〕
- **WHEN** 守卫 pytest 无法加载 init.py 的常量（init 改名/移位致漂移）
- **THEN** 守卫 MUST 非零失败，MUST NOT try/except-skip 静默跳过（真空绿）

### Requirement: 坏输入 fail-closed——重锚防假『一致』

`maintain_scan.py` MUST 在**解析不可信**时 fail-closed——响亮报错（stderr）+ 非零退出码，绝不带半信半疑的解析结果输出「一致」（该红报绿 = 假绿同构）。fail-closed 判据锚在**「防假一致」方向**，非机械纠结「空 vs 畸形」：结构骨架可信但读到 0 条 = 合法响亮态（报全新），不 fail。〔grill-amendment：重锚方向 + rules/ 可选〕

#### Scenario: INDEX.md 缺失
- **WHEN** `openspec/INDEX.md` 不存在
- **THEN** 脚本非零退出并在 stderr 说明缺失，不输出「一致」误判

> **〔spec-review-amendment H2/Q1·设计门已定 2026-07-09 + 轻 grill 收敛〕** 少读→假一致的堵法取**选项 A**（链接路径 join + 严格表体行判据），反转 grill D2 对「N 对账=过度设计」的否决。轻 grill 掰开**四类表体行**，fail 判据 MUST 按此分层（避免误伤 retro-report/表头行、避免过度宣称闭合）：
>
> | 类 | 特征 | 处置 |
> |---|---|---|
> | ① 结构行 | `\|` 起头、**无** `[..](..)` 链接（表头 `\| 名称 \| 文件 \|`、分隔 `\|---\|`、散文） | 跳过、**不** fail |
> | ②a 条目 | 有链接、target 匹配 `specs/{n}/spec.md`\|`rules/{n}.md` | 入 set-diff；文件缺=报「已删未清理」**不** fail |
> | ②b 非-spec 链接 | 有链接、target 解析出路径但非 specs/rules（`retro/report.md` 等） | **静默排除**（H3），**不** fail |
> | ③ 真少读 | 有 `[..](..)` 链接语法但 target 空/畸形**解析不出任何路径** | **fail-closed**（唯一该 fail 的类） |
>
> **执行顺序 MUST**：托管块整段排除**先于**表体行 fail 评估（否则托管块内 workflow 行 target 非 specs/rules 会被误 fail）。
> **诚实残差登记〔spec-review-amendment 轻grill/M-res〕**：选项 A **只缩小不填平** H2 的少读面——「链接语法被**整体破坏**、退化成无 `[..](..)` 的散文行」（如 `\| foo \| specs/foo/spec.md笔误没方括号 \|`）落入①类被当结构行跳过，若 foo 同时删则仍假『一致』。此型 A **不覆盖**，为**已知接受残差**（唯一补法 = 被否决的 N 对账 B，defer 记 todolist 指向之）。scenario **MUST NOT** 宣称 A 关闭 H2 全部少读——只关③类。

#### Scenario: INDEX 结构不可信→fail（③真少读 + marker 不配对）〔H2/Q1 已定〕
- **WHEN** `opsx-init:rules` 托管 marker 不配对（**已机验锚**），或表体行有 `[..](..)` 链接语法但 target 解析不出任何路径（③真少读）
- **THEN** 脚本非零退出并报错「INDEX 结构不可信，拒绝输出一致」，绝不在此状态下判「无差异」

#### Scenario: 结构行/表头/分隔行不误 fail〔spec-review-amendment 轻grill〕
- **WHEN** `INDEX.md` 含表头行 `| 名称 | 文件 |`、分隔行 `|---|---|`、或 `|` 起头的散文行（①类，无 `[..](..)` 链接）
- **THEN** 一律跳过、**不** fail-closed（否则 maintain 在任何含表的 INDEX 上每次 fail = 自打脸假红）

#### Scenario: 散文化少读为已知残差，不假宣称闭合〔spec-review-amendment 轻grill〕
- **WHEN** 某已删 spec 的 INDEX 行链接语法被整体破坏、退化为无 `[..](..)` 的散文
- **THEN** 该行落①类被跳过、不报「已删未清理」——此为**已知接受残差**（A 不覆盖），报告/spec 不宣称此型已堵，defer 指向 N 对账

#### Scenario: INDEX 读到 0 条 spec 条目（合法响亮态）
- **WHEN** `INDEX.md` 结构完好但托管块之外无任何 spec 条目
- **THEN** 脚本退出 0，报告响亮列出全部 specs 为「新增未索引」（人可自纠），**不** fail-closed

#### Scenario: specs/ 目录缺失（fatal）
- **WHEN** `openspec/specs/` 目录不存在
- **THEN** 脚本非零退出并报错

#### Scenario: rules/ 目录缺失（可选，合法）
- **WHEN** `openspec/rules/` 目录不存在（可选目录，消费仓按需加）
- **THEN** 脚本按空集处理 rules 半场、退出 0（非错误），不与 specs 半场结果混淆

#### Scenario: 可选输入缺失=空集 benign〔spec-review-amendment M5/D8〕
- **WHEN** 根/子目录 `CLAUDE.md` 不存在、或 `openspec/workflow/` 不存在、或仓根 `hack/` 不存在
- **THEN** 各按空集处理、退出 0（无文件即无过时引用 / 无残留即干净），benign 非 fatal——与「存在但不可读→fatal」统一分治线（缺失=空集，存在坏=fail-closed）

### Requirement: devenv 健康度扫描——`devenv_lint` 的唯一触发点

`sdflow-maintain` 在扫描消费仓 `openspec/` 一致性时，若检出 `openspec/architecture/.devenv.json` 存在，**SHALL 调用 `devenv_lint`** 并把其结果**原样并入**扫描报告。

> **为什么这条必须存在（dogfood 自指坑）**：`add-sdflow-devenv` 把「**无门禁**——某些检查无任何自动触发点、全靠人记得跑」列为立项理由之一，而其 `devenv_lint` **原本自己也没有任何触发点**。
>
> 更要命的是：devenv 的**渐进 DoD** 允许泳道停在 `scaffolded`、槽停在 `⚠️ 待定`，而**防止它烂成僵尸文档的唯一措施就是「把代价摆到人眼前」**（`adr/0021`）——**若无人调用该 lint，该措施为空。**
> **「不强制完成」+「不检查未完成」= 名存实亡**，两者只能选一个。**本条是 devenv 选择「不强制完成」后必须配的那一半。**

报告 SHALL 包含（**逐条列出，MUST NOT 只给计数**）：

1. **代价横幅**——`⚠️ 本框架 N/M 格待定，尚不构成一份可用的测试策略` + 逐层列出待补的槽
2. **`environments.md` 的待定槽数**——并**点名最贵的三槽**（常见坑 · 回滚 · 构建副产物）
3. **未 `verified` 的泳道**（`planned` / `scaffolded`）及其 `blocked_by`
4. **敷衍的 `blocked_by`**（`TODO` / `环境问题` —— 它没告诉任何人下一步该干嘛）
5. **SAD contract 差集**（`covers` 未覆盖的）

---

**⚠️ 两条诚实边界，SHALL 显式登记，MUST NOT 佯装：**

**① 它是提醒，不是门禁**〔`adr/0021`〕
`devenv_lint` **退出码永远是 0**（除非数据坏了）。`sdflow-maintain` **MUST NOT** 把它渲染成一个「通过 / 不通过」的门。
它提供的是「**更响的提醒**」——**代价可见 > 机械拦截**。

**② 结构通过 ≠ 内容已审**
报告 **MUST NOT** 把 lint 的结果二次简化成「`verified` = ✓」式的绿色状态。
`verified` 的语义是 **`verified-at <sha>`**——**一次历史执行的记录，不是「当前状态的绿灯」**。业务代码一改，那个绿灯就在说谎。
**渲染 SHALL 原样带上 commit 锚与日期。**

---

**降级**：

| 情形 | 行为 |
|---|---|
| 消费仓无 `.devenv.json` | **跳过**本扫描项（非报错） |
| `devenv_lint` 不可用（未装 `sdflow-devenv`） | **显式提示**「检出 `.devenv.json` 但 `devenv_lint` 不可用，跳过健康度扫描」——**MUST NOT 静默略过** |

#### Scenario: 扫描逐条报出未 verified 泳道
- **WHEN** 消费仓存在 `.devenv.json`，其中两条泳道处于 `scaffolded`
- **THEN** 扫描报告**逐条**列出这两条泳道及其 `blocked_by`——**不只给「2 条未完成」这个计数**

#### Scenario: 代价横幅原样透传
- **WHEN** 三层框架有 12/15 格待定
- **THEN** 扫描报告含 `⚠️ 本框架 12/15 格待定，尚不构成一份可用的测试策略`

#### Scenario: 它是提醒不是门禁
- **WHEN** 三层框架十五格全待定
- **THEN** `sdflow-maintain` **报出来但不失败**——它没有硬拦截

#### Scenario: verified 不得渲染成无条件的绿
- **WHEN** 报告呈现一条 `verified` 泳道
- **THEN** 它带着 commit 锚与日期（`verified-at abc123f · 2026-07-14`），**MUST NOT** 呈现为「✓ 已通过」

#### Scenario: 无 .devenv.json 时跳过
- **WHEN** 消费仓不存在 `openspec/architecture/.devenv.json`
- **THEN** 跳过 devenv 健康度扫描，不报错

#### Scenario: devenv_lint 不可用时显式提示
- **WHEN** 消费仓存在 `.devenv.json` 但未安装 `sdflow-devenv`
- **THEN** 显式提示「检出 `.devenv.json` 但 `devenv_lint` 不可用，跳过健康度扫描」，**MUST NOT 静默略过**

### Requirement: 只读且可观测

`maintain_scan.py` SHALL 只读运行——不创建、修改、删除任何文件；输出的差异报告 MUST 可观测（人可读、结构分类清晰），供 SKILL.md 步骤 4 由模型据此判断是否修复。判断（新 spec 归哪主题分组、是否修复 INDEX）留给模型，脚本不做。

#### Scenario: 运行后工作树无变更
- **WHEN** 在任意状态的仓库跑 `maintain_scan.py`
- **THEN** 运行前后 `git status` **快照对比无新增 diff**（脚本零写；报告走 stdout，不落文件）〔spec-review-amendment L3：快照对比而非「绝对干净」，容工作树本有未提交改动〕

#### Scenario: 报告分类可读
- **WHEN** 存在多类差异（新增未索引 + 已删未清理 + 过时引用 + 陈旧遮蔽）
- **THEN** 报告按四类分节呈现，每类列出具体条目，无需模型再手扫文件系统即可判断修复

