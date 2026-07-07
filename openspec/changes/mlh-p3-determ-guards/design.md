# design — mlh-p3-determ-guards

## Context

roadmap「机械层固化」阶段 3（Leg1 收尾）的实施设计。**复用 roadmap `design.md` 两条决策，不重新 litigate**：
- **决策 5（脚本不越权）**：下沉脚本只 own 机械归约；判断部分显式保留给人/模型。本 change 的守卫只判「机械可判」的一致性/语法（helper 源码是否 byte-identical、yaml 是否可解析、字段是否合枚举），**不判**「helper 副本该不该改、优先级填什么值合不合理」——那是人的判断。
- **决策 7（recorder 镜像用测试兜底、不抽公共模块）**：verbatim helper 漂移用 `inspect.getsource` 相等断言，按实测拓扑 3 向/2 向分组，**不**跨 recorder 抽 import（撞 D4 隔离红线）。本 change 是该决策的落地。

本 change scope = roadmap 3.A + 3.B 合批。零行为改动、零 SKILL.md 改动、纯增测/校验器。

## 决策

### D1：一致性测试落点 = recorder skill 自己的 tests/，按拓扑分文件

**决策**：3 向断言（buglist/todolist/issues）+ 2 向断言（buglist↔todolist）统一放一个新测试文件。落点选 `sdflow-buglist/tests/test_mirror_consistency.py`（buglist 是 2 向对的一端、又参与全部 3 向，覆盖面最全；且 test_issues.py:171 终态集测试已在 issues 侧树范式，镜像测试换 buglist 侧避免堆一处）。

**实现骨架**：
```python
import importlib.util, inspect
def _load(path): ...  # importlib 从三份 recorder 脚本各自加载 module（不 import 包，避免耦合）
BUG, TODO, ISSUES = _load(...), _load(...), _load(...)
THREE_WAY = ["atomic_write", "repo_root", "_reject_cell_unsafe"]
TWO_WAY   = ["detect_change","normalize_doc_paths","auto_default_doc","split_sections",
             "parse_table_rows","block_ranges","_ids_in_files","_find_row_file"]
# 3 向：getsource(BUG.f)==getsource(TODO.f)==getsource(ISSUES.f)
# 2 向：getsource(BUG.f)==getsource(TODO.f)
```

**替代方案**：
- A. 放 `sdflow-issues/tests/`（与终态集测试同处）→ 但 issues 不参与 2 向对，语义上 buglist 更中心。次选，非硬伤。
- B. 三份 tests/ 各放一份 → 重复三倍、又违「测试也别 verbatim 抄」，弃。

**保留给人**：断言变红时「改哪份对齐哪份」是人的判断，测试只报「三处/两处不一致」。

### D2〔grill-amendment：前提坍塌，反转原判〕：一致性契约 = 剥 docstring 后 AST 等价，非 byte 全等

**背景（grill 实测证伪 A2）**：起手实测三份 recorder 的 11 个 helper，**当前 6 个即漂移**：9 个仅 docstring/注释不同（剥 docstring 后 AST 等价）、2 个逻辑等价异写（`split_sections`：`sep=hdr+1;rows_start=sep+1` vs `rows_start=hdr+2`；`block_ranges`：for-loop vs 列表推导+walrus）——**全部经 diff/AST 核实行为等价、无藏 bug**。且 `issues.atomic_write` 多出的 docstring 段是**有意注记**（记录「Phase B 各自内联一份、不互 import」的原因）——docstring 本就该按 recorder 分化。故原 D2「byte 全等含注释」的前提（helper 逐字同款）**不成立**。

**决策（grill 拍板 Path B）**：一致性契约锁**行为等价层**——`ast.parse` 各 helper、**剥函数首个 docstring 表达式**、`ast.dump` 后比对相等。docstring/注释差异**不算漂移**（合法按 recorder 分化）；逻辑分叉（AST 不等）才报红。

**选择理由**：真正有价值、且真实维护的不变量是「三份 helper **行为**一致」，不是「字面一致」。byte-equal 会对 6/11 现存 helper 假阳、并逼迫抹掉 issues 有意的 docstring 注记，得不偿失。AST-after-docstring-strip 精确捕捉行为漂移（逻辑改动必改 AST），放过合法的 docstring 分化。stdlib `ast`/`inspect` 够用，零依赖。

**2 个逻辑异写的处理**：`split_sections`/`block_ranges` 当前 AST 不等（虽行为等价）。本 change **顺手把 todolist 侧归一到 buglist 侧的写法**（纯格式统一、已核实行为等价，符合 design D6 的 fold 判据）使 AST 全等——这样 AST 契约对全 11 个 helper 成立、无需「已知等价例外」豁免口子（豁免口子会成为未来真漂移的藏身处）。归一只改 todolist 表达式、不改行为，SDD 须跑 todolist 现有测试确认零回归。

**权衡**：docstring 漂移不再被守卫捕捉——接受。docstring 该随各 recorder 语境分化，强求统一是伪不变量；行为一致才是真契约。

### D3〔ADR·TG-23·Q-config-loc〕〔spec-review-amendment：多镜订正前提〕：`config_lint` 作 `init.py` 第 4 个 mode + **手写 stdlib 结构扫描**（不 import yaml）

**决策**：`config_lint` 落 `sdflow-init/scripts/init.py`，**作现有扁平 `mode` positional 的第 4 个值**（`python3 init.py config-lint [--root]`，与 `init`/`update`/`retire-hooks` 同款早分支 return），**MUST NOT 引入 `add_subparsers()` 重构 CLI**（接地实测 init.py 现是 `p.add_argument("mode", choices=[...])` 扁平结构，重构 argparse 有破坏既有 3 个 mode 解析的风险、且无 CLI 级测试兜底）。

**yaml 处理〔spec-review 订正·H2 四镜收敛〕**：**手写 stdlib 逐行结构扫描，MUST NOT `import yaml`**。接地实测：init.py 全文无 `import yaml`，全仓无 PyYAML、无依赖声明机制，脚本以 symlink 铺给消费仓运行——`import yaml` 会在未装 PyYAML 的消费仓 `ImportError` 崩（非 fail-closed）。仓内既有范式 = `sdflow-init/assets/workflow/tools/anchor_lint.py::read_metrics_enabled`（手写行锚正则、故意不用 yaml 库、零依赖惯例）。config_lint 照此范式：只扫本 lint 需要的**特定顶层键**（`schema:` 存在、`rules:` 下 proposal/specs/design/tasks 四子键、`model-tiers:` 若存在其 strong/mid/light 子键、`metrics:` 若存在其 enabled 值），**非全量 yaml 解析**。proposal「纯 stdlib」由此**成真**（原「现有 yaml 处理」表述已证伪、删除）。

**--root 缺省语义〔M7〕**：与 anchor_lint / 其他 recorder 一致——`subprocess git rev-parse --show-toplevel` 探 git 根，非 git 环境降级 `"."`（不沿用 init.py 现有 `default="."`，那对 lint 语义不对）。

**metrics 条件化〔M3·mlh-p2 教训复用〕**：`metrics.enabled` 校验**MUST 条件化**（与 `model-tiers` 同款「若存在才校验」）——`metrics:` 块整段缺失 → **放行**（消费仓常态，`sdflow-init update` 从不为已存在 config 注入新顶层键，100% 老消费仓无 metrics 块）；`metrics:` 块在但 `enabled` 值非 bool → ERROR。这正是姊妹 change mlh-p2-anchor-lint 的四态教训（源仓 config 有 `metrics: enabled: true` 掩盖 dogfood，见 memory `dogfood-blind-spot-source-config`），MUST NOT 重犯。同理**任何顶层块缺失都不得用 `cfg["k"]["j"]` 裸取**（KeyError 出脏 traceback 而非 human reason）——一律 `.get()` 防御 + 显式 reason。

**替代方案**：
- A.（选中）init.py mode 值 + 手写扫描 → 最小侵入、零新依赖、follow anchor_lint 范式、消费仓不炸。
- B. 独立 `config_lint.py` → 多入口，弃。
- C. `import yaml`（PyYAML）→ 引入全仓首个第三方依赖 + 消费仓 symlink 运行 ImportError，**否决**（违零依赖惯例 + 非 fail-closed）。

**保留给人**：config 各段**内容**对不对（context 文案、rules 措辞）不校验，只校验**结构存在性/枚举/类型**。

**〔需拍板 Q1〕** 手写 stdlib 扫描 vs 引 PyYAML 是本 change 的关键路径反转（推荐 A：手写，follow 范式 + 零依赖 + 消费仓安全）——设计门请确认；若拍板引 PyYAML，须同步补依赖声明机制 + 消费仓降级策略（本设计不含）。

### D4〔ADR·Q-batch-prio〕：batch `优先级` lint = 前导 token 校验，容忍括注/破折号

**决策**：`优先级` 值按「**前导 token** ∈ PRIORITIES ∪ {`—`}，其后可跟任意括注」校验，非朴素整值 `∈ PRIORITIES`。

**依据（接地实测）**：现存 batches.md 实样：`P2（T10/T11 已 DONE）`、`P3（T25 已 DONE）`、`—（已闭合）`、`P2`。朴素整值枚举会对**所有带括注的现存条目假阳**（成功指标明确要求「现存所有真实批次 → lint 通过」）。

**实现〔spec-review 订正·H4 三镜收敛〕**：`优先级` 值 strip 后，先判占位符豁免（见下 D5 合并），否则 `re.match(r"^(P\d|—)", v.strip())` 取前导 token——**匹配即过、其后剩余内容一律不校验**（MUST NOT 要求后缀为空或必须是括注）。接地实测现存实样含 `P1 ★`（token 后裸星号、非括号包裹）、`P2（…）`（括注）、`—（已闭合）`——三者都须过；「只看前导 token、忽略剩余」是唯一能覆盖全部实样的写法。spec 措辞「容忍其后括注」易被误读为「只容忍括注」→ 已订正为「前导 token 校验，其后不校验」。`—` = U+2014（接地核实，与正则字面一致）。`PRIORITIES` 单一源见下 R4〔M1 订正〕。

**替代方案**：
- A. 朴素 `value in PRIORITIES` → 现存条目全假阳，弃。
- B. 严格「token + 仅容忍括注后缀」正则 `^(P\d|—)(（.*）)?$` → 拒 `P1 ★`，破零假阳基线，弃。
- C.（选中）前导 token match、剩余不校验。

**保留给人**：token 之后的一切（括注/星号/备注）不校验，那是人写标注。

### D5〔spec-review-amendment·H1 五镜收敛〕：`优先级` 与 `计划` **两字段**均豁免 `BATCH_PLACEHOLDER` 占位符

**决策**：`优先级` 和 `计划` 值 == `<待填>`（`BATCH_PLACEHOLDER`，issues.py:438）→ **均豁免**（合法「未分诊/未填」态）；≠ 占位符时：`计划` 必须非空白、`优先级` 走 D4 前导 token 校验。

**背景（原设计漏洞）**：原 D5 只给 `计划` 开占位符豁免。但接地实测 batches.md **现存 3 条 `优先级: <待填>`**（`sdflow-retro`/`sdflow-retro-cleanup`/`mlh-p2-anchor-lint`）——因 `cmd_batch_add`（issues.py:709-710）对 `优先级`/`计划` 走**同一套** `BATCH_PLACEHOLDER` 缺省机制。原 D4「前导 token ∈ PRIORITIES∪{—}」会把 `<待填>`（前导 `<`）判非法 → 3 条真实批次假阳 → 破 proposal 成功指标「现存全过」。五镜收敛（broad/domain/adv-A/adv-B/ov-fallback）实测复现。

**选择理由**：两字段同源占位符机制，豁免必须对称。`BATCH_PLACEHOLDER` 从 issues.py 单一源读（同文件内）。

### D6〔grill 已定夺〕：A2 已证伪，漂移全属行为等价，本 change 顺手归一 2 个逻辑异写

**结论（grill 实测 + 分类完成）**：A2「三份当前 byte-identical」**已证伪**。漂移分类：
- **9 个纯 docstring/注释漂移**（AST 等价）→ 由 D2 新契约（剥 docstring 比 AST）**直接放行**，非漂移、不处理。
- **2 个逻辑异写**（`split_sections`/`block_ranges`，AST 不等但行为等价，已 diff 核实无藏 bug）→ 本 change **顺手把 todolist 侧归一到 buglist 写法**（纯格式统一、fold 判据 [[change-fold-vs-defer-cycle-cost]]），使 AST 契约全 11 个成立。
  - `split_sections`：todolist `rows_start = table_hdr + 2` → buglist `sep = table_hdr + 1; rows_start = sep + 1`（一处差异）。
  - `block_ranges`〔spec-review 订正·H3 广审〕：**两处**独立差异，均须归一才 AST 全等——① starts 构造：todolist 列表推导+walrus → buglist for-loop+append；② 消费循环签名：todolist `for i, bid in starts:` → buglist `for idx, (i, bid) in enumerate(starts):`（含未用的 `idx`）。只归一 ① AST 仍不等（接地实测复现）。归一以 buglist 为单一真相源、两处一并改。

**关键**：无任何漂移是「一份修过 bug 另份没修」的语义分叉——故**无需转 buglist**、无「合并修复」情形。grill 门已过（用户拍板 Path B 即含「2 个逻辑异写顺手归一」）。

**边界**：归一只改 todolist 的表达式写法、不改行为；SDD Task 1 归一后 MUST 跑 todolist 现有全测确认零回归。若归一意外触碰行为（不应发生）→ 停下退 buglist。

## 失败模式表〔TG-15，新校验器 codepath〕

| 场景 | 输入 | 期望行为 | fail 方向 |
|---|---|---|---|
| helper 漂移 | 三份/两份 `getsource` 不等 | 测试 assert 失败，指明哪个 helper 哪几处不一致 | fail-closed（红） |
| helper 缺失 | 某 recorder 删了某 helper | `getattr` 抛 AttributeError → 测试红（暴露删除） | fail-closed |
| config yaml 坏 | 非法 yaml 语法 | `safe_load` 抛异常 → config_lint 非零退出 + reason | fail-closed |
| config 缺必填段 | 无 `schema` 或 `rules.proposal` | 校验报缺失段 → 非零退出 | fail-closed |
| config tier 越域 | `model-tiers`（若存在）含非 {strong,mid,light} 子键 | 报越域子键 → 非零退出 | fail-closed |
| metrics 非 bool | `metrics:` 块在但 `enabled` 值非 bool（`yes-please`） | 报类型错 → 非零退出 | fail-closed |
| metrics 块缺失〔M3〕 | 无 `metrics:` 顶层块（消费仓常态） | **放行**（条件化，与 model-tiers 同款「若存在才校验」） | 放行（非漂移） |
| model-tiers 块缺失 | 无 `model-tiers:`（现源仓即注释态） | **放行**（条件化）；越域分支只能靠构造样例测，非真实文件 | 放行（非漂移） |
| batch 优先级错 | `优先级: PX` / `优先级: 高` | 前导 token 不 ∈ PRIORITIES∪{—} → 非零退出 | fail-closed |
| batch 计划空 | `计划: `（非占位符、无内容） | 报空 → 非零退出 | fail-closed |
| config/batch 文件缺失 | 目标文件不存在 | 报文件缺失 → 非零退出（不静默当「无错」） | fail-closed |
| 现存真实数据 | 当前 config.yaml + batches.md 全部条目 | **全部通过**（零假阳） | 回归基线 |

## 可观测性

- 所有校验器：违规时 stderr 输出 human 可读 reason（哪个文件/哪条/哪个字段/期望什么），退出码非零；干净时退出 0。
- 一致性测试：pytest 失败信息含不一致的 helper 名 + 哪几份 recorder。

## Risks

| # | 风险 | 缓解 |
|---|---|---|
| R1 | `getsource` 含外层缩进差异致 `ast.parse` 失败 | D2：解析前 `textwrap.dedent`；比 AST 而非字符串，缩进/空白差异天然不入 AST |
| R2 | A2 证伪已发生（6/11 漂移）打乱 scope | 〔已消解〕D2/D6：grill 拍板锁 AST 等价（9 个直接过）+ 顺手归一 2 个逻辑异写；全属行为等价、无语义分叉、无需退 buglist |
| R6 | 归一 2 个逻辑异写意外改行为 | D6：只改 todolist 表达式、归一后跑 todolist 全测；已 diff 核实行为等价，回归为空即证 |
| R3 | batch 优先级语法容忍过宽/过严 | D4：接地实样校准 + 成功指标「现存全过」回归基线双向锁 |
| R4〔spec-review 订正·M1 三镜〕 | PRIORITIES 跨脚本读撞 D4 隔离；且原「纳入 D1 守护集」技术不可行 | issues.py 内声明同款 `PRIORITIES` 常量；一致性用**值相等断言** `assert BUG.PRIORITIES == ISS.PRIORITIES`（**独立代码路径、非 `inspect.getsource`**——getsource 对 list 常量抛 TypeError，D1 的 THREE_WAY/TWO_WAY 是函数专用 harness，常量不能塞进去）。断言物理落在 test_mirror_consistency.py 同文件，但走独立 `==` 比较，不复用函数 AST harness。不跨 import。 |
| R5 | config_lint 未接入任何门 = 写了没人跑 | 本 change 只交付 validator + 测试；接入 done/CI 门是 P4/后续 scope，proposal Non-Goals 已声明，不在此假装接入 |
