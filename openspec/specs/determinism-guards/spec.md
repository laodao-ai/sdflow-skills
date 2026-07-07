# determinism-guards Specification

## Purpose
TBD - created by archiving change mlh-p3-determ-guards. Update Purpose after archive.
## Requirements
### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

三份 recorder（`buglist.py`/`todolist.py`/`issues.py`）各自内联持有的共享 helper MUST 由**剥函数 docstring 后 `ast.dump` 相等**的断言守护其**行为**不漂移，按实测拓扑分组：3 向组（`atomic_write`/`repo_root`/`_reject_cell_unsafe`，3 个）三份 AST 等价、2 向组（`detect_change`/`normalize_doc_paths`/`auto_default_doc`/`split_sections`/`parse_table_rows`/`block_ranges`/`_ids_in_files`/`_find_row_file`/`_id_sort_key`/`validate_doc_paths`/`all_ids`/`next_id`/`_die`/`_load_json`，共 14 个）buglist↔todolist AST 等价（3+14=17 个 helper 受本守卫覆盖）。**注**：TWO_WAY 组自代码审查 [impl-review-fix] F3 起由最初审计的 8 个扩至 14 个——冷审 + codex 独立复现发现 `_id_sort_key`/`validate_doc_paths`/`all_ids`/`next_id`/`_die`/`_load_json` 这 6 个同样在 buglist/todolist 两处逐字同款、却此前未纳入覆盖范围，遗漏会让它们能悄悄改动而不拉红；`_die` 虽三份都存在，但其三向等价性未经核验，故只补进 TWO_WAY、不扩大 THREE_WAY。契约锁**行为等价层非字面层**（grill 实测证伪「逐字同款」前提）：docstring/注释差异合法（按 recorder 语境分化，如 issues 记录内联原因），**不**算漂移；逻辑分叉（AST 不等）才报红。测试 MUST NOT 抽公共模块或跨 recorder import（守 D4 隔离）。

#### Scenario: 3 向 helper 逻辑分叉
- **WHEN** `atomic_write`/`repo_root`/`_reject_cell_unsafe` 任一在三份中剥 docstring 后 AST 不等
- **THEN** 一致性测试断言失败（红），失败信息指明漂移的 helper 名与不一致的 recorder

#### Scenario: 2 向 helper 逻辑分叉
- **WHEN** TWO_WAY 组 14 个表解析/文档/ID helper 任一在 buglist↔todolist 剥 docstring 后 AST 不等
- **THEN** 一致性测试断言失败；且测试范围 MUST NOT 把 issues.py 纳入这 14 个 helper 的比对（issues 依 D4 不含表解析 helper）

#### Scenario: docstring 差异不报漂移
- **WHEN** 某 helper 三份/两份行为一致（剥 docstring 后 AST 等）但 docstring 或注释不同
- **THEN** 一致性测试通过（docstring 按 recorder 分化合法，非漂移）

#### Scenario: helper 被某 recorder 删除
- **WHEN** 某 recorder 删掉了受守护的 helper 定义
- **THEN** 测试因取源失败（AttributeError）而红，暴露删除，绝不静默跳过

#### Scenario: 现状基线（含 2 个逻辑异写归一 + F3 覆盖扩容后）
- **WHEN** 对当前三份 recorder（本 change 已把 `split_sections`/`block_ranges` 的 todolist 侧归一到 buglist 写法——block_ranges 两处差异均归一；代码审查 F3 又把 TWO_WAY 覆盖范围从 8 个扩到 14 个）跑一致性测试
- **THEN** 全部断言通过（剥 docstring 后全 17 个 helper——3 个 THREE_WAY + 14 个 TWO_WAY——AST 等价）

#### Scenario: PRIORITIES 常量跨脚本一致性（非函数、独立断言路径）
- **WHEN** `issues.py` 声明的 `PRIORITIES` 常量与 `buglist.py` 的不相等
- **THEN** 一致性测试用**值相等断言** `BUG.PRIORITIES == ISS.PRIORITIES` 报红——此断言走独立代码路径（`==` 比较列表值），MUST NOT 塞进 THREE_WAY/TWO_WAY 的 `inspect.getsource` 函数 harness（getsource 对 list 常量抛 TypeError）

### Requirement: config.yaml 由 fail-closed 结构 lint 校验（手写 stdlib、条件化）

`config_lint`（`init.py` 第 4 个 mode，`python3 init.py config-lint [--root]`）MUST 校验 `openspec/config.yaml` 的结构：`schema` 与 `rules`（含 proposal/specs/design/tasks 四段）必填、`model-tiers`（若存在）子键 ∈ {`strong`/`mid`/`light`}、`metrics`（若存在）`enabled` 为 bool。**MUST 手写 stdlib 行级结构扫描（follow `anchor_lint.py::read_metrics_enabled` 范式），MUST NOT `import yaml`**（零依赖惯例 + 消费仓 symlink 运行防 ImportError）。**任何顶层块缺失 MUST 条件化处理（`.get()` 防御、不裸取），不得抛 KeyError 脏 traceback**。任一违规 MUST 非零退出并输出 human 可读 reason；MUST NOT 校验各段内容文案（只校验结构存在性/枚举/类型）；MUST NOT 引入 add_subparsers 重构、不扰动既有 `init`/`update`/`retire-hooks` 三 mode。

#### Scenario: 坏结构（无法定位必填顶层键）
- **WHEN** config.yaml 结构损坏到扫不出 `schema:`/`rules:` 顶层键
- **THEN** config_lint 非零退出，reason 指明缺失的键，绝不 fail-open 当「无错」

#### Scenario: 缺必填段
- **WHEN** config.yaml 缺 `schema` 或 `rules` 下 proposal/specs/design/tasks 任一子段
- **THEN** config_lint 非零退出，reason 指明缺失的段

#### Scenario: model-tiers 子键越域（若存在）
- **WHEN** `model-tiers` 段存在且含非 {strong,mid,light} 的子键
- **THEN** config_lint 非零退出，reason 指明越域子键

#### Scenario: model-tiers/metrics 块整段缺失
- **WHEN** config.yaml 无 `model-tiers:` 或无 `metrics:` 顶层块（消费仓常态）
- **THEN** config_lint **放行该块**（条件化「若存在才校验」），MUST NOT 因块缺失报错或抛 KeyError（防 mlh-p2 同类假阳，见 memory dogfood-blind-spot-source-config）

#### Scenario: metrics.enabled 非 bool（块存在时）
- **WHEN** `metrics:` 块存在但 `enabled` 值不是布尔（如 `yes-please`）
- **THEN** config_lint 非零退出，reason 指明类型错

#### Scenario: 现存真实 config 回归
- **WHEN** 对当前 openspec/config.yaml（有 metrics 块、无 model-tiers 活跃段）跑 config_lint
- **THEN** 退出 0（零假阳）；注：model-tiers 越域分支须靠构造样例测，当前真实文件测不到该 codepath

### Requirement: batches.md 人写字段由 fail-closed grammar lint 校验

`issues.py batch lint` 子命令 MUST 逐条校验 `openspec/issues/batches.md` 人写字段：`优先级`/`计划` 值 == `BATCH_PLACEHOLDER`（`<待填>`）时**两字段均豁免**；否则 `优先级` 的前导 token（`re.match(r"^(P[0-4](?!\d)|—)", v.strip())`）∈ `PRIORITIES` ∪ {`—`}、**匹配后剩余内容一律不校验**（token 后可跟括注/星号/任意备注）；`计划` 非占位符态时非空。复用 `_split_batches_entries` 逐条切分（其返回 entry 原始文本行，须新写 `优先级:`/`计划:` 行正则取值）。任一违规 MUST 非零退出并指明批次与字段；MUST NOT 覆写任何人写行（只读校验）。**注**：正则曾是 `^(P\d|—)`，代码审查 [impl-review-fix] F3 收紧为 `^(P[0-4](?!\d))`——旧正则对 `P10`/`P40` 这类两位数会截断匹配出 `P1`/`P4`（合法 token）而误判通过，负向前瞻 `(?!\d)` 排除"匹配数字后仍紧跟数字"的情况，两位数及以上一律不匹配、落入 `token is None` 分支被拒。

#### Scenario: 优先级前导 token 非法
- **WHEN** 某批次 `优先级: 高` 或 `优先级: PX` 或 `优先级: P10`/`P40`（前导 token 不 ∈ PRIORITIES∪{—}、或为两位数越界值、且非占位符）
- **THEN** batch lint 非零退出，reason 指明该批次与非法值

#### Scenario: 优先级 token 后带任意后缀合法
- **WHEN** 某批次 `优先级: P2（T10/T11 已 DONE）`（括注）/ `优先级: —（已闭合）` / `优先级: P1 ★`（裸星号后缀）
- **THEN** batch lint 通过该字段（前导 token `P2`/`—`/`P1` 合法，其后一切不校验）

#### Scenario: 优先级占位符豁免
- **WHEN** 某批次 `优先级: <待填>`（`batch add` 缺省写入，同 `计划` 的占位符机制）
- **THEN** batch lint 通过该字段（占位符是合法未分诊态）

#### Scenario: 计划非占位符态为空
- **WHEN** 某批次 `计划:` 值既非 `<待填>` 占位符、又为空白
- **THEN** batch lint 非零退出，reason 指明该批次计划为空

#### Scenario: 计划占位符态豁免
- **WHEN** 某批次 `计划: <待填>`（`batch add` 缺省写入的合法未填态）
- **THEN** batch lint 通过该字段（占位符是合法未填态）

#### Scenario: 现存真实 batches.md 回归
- **WHEN** 对当前 openspec/issues/batches.md 全部条目（含 3 条 `优先级: <待填>`、1 条 `P1 ★`、`—（已闭合）`、`P2（…）`）跑 batch lint
- **THEN** 退出 0（零假阳，接地实测过全部实样）

### Requirement: 确定性守卫不越权、不破 D4 隔离

本 capability 的所有守卫 MUST 只判机械可判的一致性/语法，MUST NOT 判内容合理性（helper 副本该不该改、优先级填什么值、计划写什么）——那是人的判断（roadmap design 决策 5）。一致性测试 MUST 用 `inspect.getsource` 只读断言、MUST NOT 引入跨 recorder import；batch lint MUST NOT 覆写人写行（D4）。

#### Scenario: 脚本不做内容判断
- **WHEN** helper 内容被有意修改但三份同步、或优先级填了合法但语义存疑的值
- **THEN** 守卫通过（不越权评判内容对错），内容判断留给人/模型

#### Scenario: 守卫不引入新 import 耦合
- **WHEN** 一致性测试运行
- **THEN** 它经 importlib 从各脚本独立加载读源码，不建立 recorder 间的 import 依赖，不破 D4 隔离

