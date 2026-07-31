# Task 1 impl-report：配置分档与单一盘面条款（①②）

**R-ID:** IO-1
**状态:** DONE

## 修改的文件

### 1. `sdflow-init/assets/workflow/config.template.yaml`

在 `impl-pipeline` 键之后、`metrics` 段之前，新增 `test-suites`（可选段）的注释示例：

- 形状一（字符串）：quick/full 两档同命令，与旧形状完全一致，示范三层各一行命令。
- 形状二（映射）：`{quick: ..., full: ...}`，示范 unit 层完整分档、integration/e2e 未分档
  （只写 `full`）两种子情形，并在注释里点出「缺 `quick` 视为无 quick 档，unit 层例外：中间
  fix 轮缺 quick 取 full，MUST NOT 因此跳过 unit 层」「缺 `full` 视为未分档（quick=full）」。
- 注释说明命令由 `sdflow-devenv` 运行时调研写入、已有配置不覆盖，缺省不填。

全部以注释形式存在（沿用该模版其余可选段的既有风格：`model-tiers` / `impl-pipeline` 均为注释
示例，不是生效默认值），字符串形状保持为映射形状的合法子集，未配置消费仓行为不变。

### 2. `sdflow-implement/SKILL.md`

「聚合套件发现契约」段（原 :306-334，现 :306-349）：

- 原列表 1→6 六条中插入新的第 2 条（原 2-6 顺延为 3-7）：`test-suites` 支持成本分档的消费语义——
  字符串 ⇒ 两档同命令；映射 ⇒ 读 `quick`/`full`，缺 `quick` 视为该层无 quick 档（unit 层例外：
  缺 `quick` 取 `full`，MUST NOT 跳过该层）；缺 `full` 视为未分档（quick=full）。并注明具体命令
  由 `sdflow-devenv` 运行时调研写入，本处只定义消费规则。
- 原第 6 条「单一盘面」整条改写为第 7 条「中间 fix 轮与收口轮范围分离」：
  - 中间 fix 轮 = unit 全层（配 quick 取 quick，无 quick 取 full）+ 上轮失败的具体用例
    （⊂ unit 层）；集成/e2e 整层推迟到收口，中间轮结果仅供诊断，MUST NOT 作为最终报告的
    「通过」证据行。
  - 收口时各层取 `full`，全部「通过」行锚同一最终 SHA——**逐字保留了 Global Constraints 点名
    的既有正确性契约**（"报告里所有判『通过』的行 MUST 锚同一个最终 SHA"，对应旧 :330-332，
    改动后未削弱其措辞，只是嵌入了新的范围分离结构）。
  - 新增 🔴 条款：范围 MUST NOT 由「哪层受影响」的判断界定；要求写明依据不构成缓解。

未触碰「零依赖不变量」「GC-2 边界锁」等超出本票范围的内容。

### 3. `sdflow-devenv/SKILL.md`

在「⑤ 渲染 + 入口 + 交棒」步的既有三个产出物列表（`testing-strategy.md` / `environments.md` /
入口）之后，新增一段「`openspec/config.yaml` 的 `test-suites` 发现与写入」：

- 来源 = ②-1「怎么跑（命令）」已真跑验证过的逐层命令，不重新调研。
- 分档判据：层天然有 quick 变体（如 `-short` / `-m "not slow"` / CI 已分 smoke-full）⇒ 推荐映射
  形状；无天然 quick 变体 ⇒ 推荐字符串形状（quick=full），MUST NOT 造假 quick。
- 仓内确无某层 ⇒ 不写该层键，沿用「未覆盖」语义，MUST NOT 造假条目。
- 已有配置 MUST NOT 覆盖，只补缺失层。
- 落地方式：直接编辑 `openspec/config.yaml`（不是 `.devenv.json`，本 skill 无脚本 owns 这个
  文件——schema 归 `sdflow-init`），diff 走④冷审 + 人门既有的「落地物 diff 过目」环节，不单开
  人门。

未新增 Python 脚本（Global Constraints 已声明本 change 全部交付物是 prose + 配置模板）。

## 验证

- `git diff --stat`：确认仅 3 个目标文件被改动，行数增量 config.template.yaml +23、
  sdflow-implement/SKILL.md 净变化（插入新条 + 改写单一盘面条），sdflow-devenv/SKILL.md +17。
- 全仓 grep `受影响层`：命中仅存在于 change 自身的设计工件（`impl-reports/task1-brief.md`、
  `tickets.md`、`tasks.md`、`proposal.md`、`decision-memo.md`、`gstack-review.md`）与
  `openspec/adr/0035-*.md`、`openspec/roadmaps/workflow-cost-optimization/*` ——这些是本 change
  的问题陈述/历史文档，非本票编辑目标（forbidden 清单含 tasks.md/proposal.md/specs/design.md，
  且它们本就是在描述「要消除的旧提法」，出现该词是合理的自我指涉，不是残存的旧条款）。
  `sdflow-implement/SKILL.md`、`sdflow-devenv/SKILL.md`、`config.template.yaml` 三个被改动的
  目标文件本身干净，无该短语。

## 未做/无需做的部分

- 未修改 `sdflow-devenv/scripts/*.py`——本票不新增脚本（Global Constraints 明确声明本 change
  无 Python 脚本、无数据迁移）。
- 未同步 `openspec/workflow/config.template.yaml`（仓根副本）——该副本是历史遗留（CLAUDE.md
  称仓根应只保留 `tools/`，但物理上仍有全套规则文件），本票 brief 明确点名的是
  `sdflow-init/assets/workflow/config.template.yaml`（唯一权威源），未要求同步仓根副本，
  未顺手改动（通则④，不加宽范围）。
- 未改动 tickets.md 的验收复选框——权威表要求由双轴审通过后另行补打，本票不自行勾框。
