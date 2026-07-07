## Why

roadmap「机械层固化」阶段 3（Leg1）的收口项：仓内有两处「本该机械校验、当前却靠约定/人自觉」的守卫缺口，一旦漂移无任何自动信号，直到下游炸出才发现——

1. **recorder 镜像 helper 漂移**：`buglist.py`/`todolist.py`/`issues.py` 三份 recorder **刻意各自 verbatim 持有**一批共享 helper（`atomic_write`/`repo_root`/`_reject_cell_unsafe` 三向；`detect_change`/`split_sections`/`parse_table_rows` 等八个两向），D4 红线禁止抽公共模块跨 recorder import。但「verbatim 副本」只是约定——改一份忘同步另两份，行为静默分叉，无测试拦截。
2. **config/batches 人写字段无 lint**：`openspec/config.yaml`（schema/rules/model-tiers/metrics）与 `openspec/issues/batches.md` 的 `优先级:`/`计划:` 是人手填写，打错 tier 子键、写坏 yaml、缺必填段、优先级非枚举、计划留空——当前零校验，坏值一路带到消费端。

现在做：Leg1 前三阶段已交付（P1 sweep ca66d60、P2 anchor-lint e43460c），P3 是 Leg1 纯增测/校验器收尾，就绪度高、爆炸半径低（零行为改动、零 SKILL.md 改动）。

## What Changes

- **3.A recorder 镜像一致性测试**（新测试 + 顺手归一 2 个逻辑异写，不改行为）〔grill-amendment〕：**契约 = 剥 docstring 后 AST 等价**（非 byte 全等——grill 实测证伪「helper 逐字同款」前提，见 design D2/D6：11 个 helper 中 9 个仅 docstring 漂移合法分化、2 个逻辑等价异写本 change 顺手归一）。按实测拓扑——**3 向**（buglist/todolist/issues）守 `atomic_write`/`repo_root`/`_reject_cell_unsafe`；**2 向**（buglist↔todolist）守 `detect_change`/`normalize_doc_paths`/`auto_default_doc`/`split_sections`/`parse_table_rows`/`block_ranges`/`_ids_in_files`/`_find_row_file`（issues.py 依 D4「绝不解析人写行」不含表解析 helper）。故意造逻辑分叉 → AST 断言变红。**MUST NOT 抽公共模块**（守漂移，非消重）；docstring 按 recorder 分化合法、不强求统一。
- **3.B config + batch lint**（新校验器，fail-closed）：
  - `config_lint`（`init.py` 第 4 个 mode，**手写 stdlib 结构扫描、不 import yaml**——follow `anchor_lint.py::read_metrics_enabled` 范式，见 design D3）：`schema`/`rules`（proposal/specs/design/tasks 四段）必填 + `model-tiers`（若存在）子键 ∈ {`strong`/`mid`/`light`} + `metrics`（若存在）`enabled` bool。**顶层块缺失一律条件化放行**（消费仓常态，防 mlh-p2 同类假阳）。
  - `issues.py batch lint`：`优先级` 合法（语法见 design——**须容忍现存实样 `P2（T10/T11 已 DONE）`、`—（已闭合）` 的括注/破折号形态，非朴素 `∈ PRIORITIES`**）、`计划` 非占位符（≠`<待填>`）时非空；复用 `_split_batches_entries` 逐条 grammar 校验。
  - 各自坏输入测试断言非零退出。

## Capabilities

### New Capabilities
- `determinism-guards`: 机械层确定性守卫——把「本该脚本判定、当前靠约定/人自觉」的一致性/字段合法性约束固化为 fail-closed 校验器/测试（recorder verbatim 镜像不漂移、config/batches 人写字段合法）。roadmap 附录 C「recorder skills 自包含 + config schema」落点；未来 P4 机械层下沉可扩展本 capability。

### Modified Capabilities
<!-- 无。P3 纯增守卫，不改任何现有 capability 的需求语义。 -->

## Impact

- **改动文件**：新增 `sdflow-buglist/tests/`（或就近 recorder tests 目录）镜像一致性测试；新增 `config_lint`（`sdflow-init/scripts/init.py` 子命令或独立脚本）+ 测试；`sdflow-issues/scripts/issues.py` 加 `batch lint` 子命令 + 测试。
- **零行为改动**：不改 recorder 现有读写逻辑、不改 config/batches 现有内容、不改任何 SKILL.md、不触 bundle 行为面。
- **测试纪律**：数据类改动，改 scripts/ 必同步跑 `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ sdflow-init/tests/`。
- **技术栈**：不命中 backend·go / embedded / frontend 任一领域清单。**纯 Python stdlib**〔spec-review 订正〕——config_lint 手写行级结构扫描（follow anchor_lint 范式），**不引 PyYAML**（全仓零第三方依赖惯例；脚本 symlink 铺消费仓，import yaml 会 ImportError 崩）。原「现有 yaml 处理」表述已证伪删除（init.py 现无 import yaml、从不解析 config 内容）。

## Success Metrics

- 改任一 verbatim helper 逻辑 → 一致性测试红（故意逻辑分叉用例证实守卫生效）；docstring 分化不报红。
- 坏 config.yaml（坏结构 / 缺必填段 / tier 越域子键 / metrics.enabled 非 bool）→ `config_lint` 非零退出 + human reason。
- batches.md `优先级` 非法语法 / `计划` 空（非占位符态）→ `batch lint` 非零退出；**现存所有真实批次条目（含 `<待填>` 占位、`P1 ★` 后缀、`—（已闭合）`）→ lint 通过**（无假阳，接地实测过全部实样）。
- `pytest` 全绿；新校验器均有坏输入断言非零退出的用例。
- **触发可靠性分层〔spec-review 订正·M5〕**：3.A（一致性测试）随 `pytest` 例行自动跑到、天然生效；**3.B（config_lint/batch lint）是新增子命令、不在任何现有自动化路径**——现阶段需人工/未来 change 接入门后才自动生效（等于新增了锁、但接入门是后续 scope，见 Non-Goals + design R5）。两者保护力度不同，勿混同。

## Non-Goals

- **不抽公共 helper 模块**、不消除 recorder 间 verbatim 重复（D4 红线；本 change 守其不漂移，反其道消重是破坏刻意设计）。
- **不改 config/batches 的既有 schema 或内容**、不迁移字段格式（那是 Leg2 P6 north-star 的 scope）。
- **不下沉编排 SKILL 机械步**（P4 scope）、不碰 gate 锚/frontmatter（P5 scope）。
- **不做 recorder 行为重构**——一致性测试只读源码断言，不改被测函数。

## Compliance

- 全局红线（roadmap design §决策 5）：新校验器 fail-closed + 可观测；判断部分（helper 副本本身该不该改、优先级填什么值）显式保留给人/模型，脚本只判机械可判的一致性/语法，不越权。
- D4 红线〔spec-review 订正·M6，拆两层防混读〕：**硬红线 = ①recorder 绝不跨 skill import、②绝不覆写人写行**——一致性测试用 importlib 独立加载 + `inspect.getsource` 只读断言、不建 import 依赖；batch lint 只读、不覆写任何人写行，二者均守硬红线。**batch lint 对 `优先级`/`计划` 做只读语法校验（取前导 token 比枚举）= 对「绝不解析人写行」的一个限定于*只读语法层、不解读语义合理性*的窄化例外**（母 roadmap 该句原为证成「issues.py 不含表解析 helper」，非禁止只读语法 lint）；不与硬红线冲突。
- 数据类改动纪律：改 scripts/ 必跑对应 tests/（CLAUDE.md 项目约定）。

## 假设列表〔TG-22〕

| # | 假设 | 失效影响 | 核实状态 |
|---|---|---|---|
| A1 | verbatim helper 拓扑 = 3 向 {atomic_write, repo_root, _reject_cell_unsafe} + 2 向 {detect_change, normalize_doc_paths, auto_default_doc, split_sections, parse_table_rows, block_ranges, _ids_in_files, _find_row_file} | 拓扑写错 → 一致性测试守错对象（漏守或误报） | ✅ 已接地核实（grep def 三份/两份实测吻合，2026-07-07） |
| A2 | ~~三份 helper 当前 byte-identical~~ **已证伪** → 实为「行为等价、字面分化」：9 个仅 docstring 异、2 个逻辑等价异写 | 决定契约层：byte-equal 会对 6/11 假阳 | ❌ **grill 已证伪并定夺**：契约改锁「剥 docstring 后 AST 等价」（Path B），2 个逻辑异写本 change 顺手归一（见 design D2/D6） |
| A3 | `PRIORITIES = ["P0".."P4"]` 是优先级枚举权威源（buglist.py:57） | 若 batch 优先级另有语义 → 枚举校验错 | ✅ 已核实存在 |
| A4 | batches.md `优先级` 实样含括注/破折号（`P2（…）`/`—`） | 若 lint 用朴素 `∈ PRIORITIES` → 现存条目全假阳 | ✅ 已核实（实样见 design 开放问题 Q-batch-prio） |

## 开放问题〔TG-21〕

| # | 问题 | 倾向 | 定夺时机 |
|---|---|---|---|
| Q-config-loc | `config_lint` 落 `init.py` 子命令 vs 独立脚本 | ✅ 已决 → init.py 子命令（design D3） | design ADR（TG-23） |
| Q-batch-prio | batch `优先级` lint 语法：如何容忍 `P2（T10/T11 已 DONE）`/`—（已闭合）` 又能抓真错 | ✅ 已决 → 前导 token ∈ PRIORITIES∪{—}，其后可跟括注（design D4） | design ADR |
| Q-a2-drift | A2 证伪（现状已漂移）：契约锁哪层 + 逻辑异写怎么办 | ✅ **grill 已拍板 Path B** → 锁 AST 等价(剥 docstring) + 顺手归一 2 个逻辑异写（design D2/D6） | grill（已定夺 2026-07-07） |
