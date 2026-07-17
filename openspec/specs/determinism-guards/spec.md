# determinism-guards Specification

## Purpose
TBD - created by archiving change mlh-p3-determ-guards. Update Purpose after archive.
## Requirements
### Requirement: recorder 镜像 helper 由「剥 docstring 后 AST 等价」一致性测试守护

三份 recorder（`buglist.py`/`todolist.py`/`issues.py`）为保持 skill 自包含而各自内联的真共享 helper MUST 由剥函数 docstring 后 `ast.dump` 相等的断言守护行为不漂移。frontmatter 目标态的三向组 SHALL 至少包含 `atomic_write`、`atomic_write_bytes`、`repo_root`、`recorder_lock`、`canonical_id`、`semantic_id_key`、`_reject_line_unsafe`、`read_recorder_document`、`parse_recorder_document`、`render_recorder_namespace`、`split_sections`、`parse_table_rows`、`block_ranges`；buglist↔todolist 两向组 SHALL 包含其共享的 change/doc/ID/定位 helpers，包括 `detect_change`、`normalize_doc_paths`、`auto_default_doc`、`_find_row_file`、`_id_sort_key`、`validate_doc_paths`、`all_ids`、`next_id`、`_die`、`_load_json`。实现若为满足已批准 design 增减或重命名共享 helper，MUST 在同一提交中更新显式 roster 与本 requirement，MUST NOT 以动态发现所有同名函数替代人工审定的边界。

`[spec-review-amendment]` 因 `issues.py::read_rename_snapshot()` 必须直接解析两池 dated files 才能达成 whole-command read=1，legacy region discovery、semantic-ID/overlay merge、marker relation 与 envelope lexical scanner 升为三向**行为契约**。能用同签名纯 helper 表达的部分 SHALL 进入 THREE_WAY AST roster；pool-specific legacy 字段差异与 `read_rename_snapshot` 编排则用同一 canonical/pure-legacy/overlay fixture 做 golden equivalence：`issues.py` direct snapshot 的 effective items/problems 必须等于 bug+todo `scan --json` contract join，且额外保留 raw bytes/spans。`validate_scan_envelope` 是 issues consumer 独有 helper，须以坏 JSON/缺键/错型/缺 file contract tests 守护，不伪塞进三向 AST roster。

`_reject_cell_unsafe` 不再属于目标态 roster；`split_sections`/`parse_table_rows` 只作为三份 recorder 的 legacy read 半场保留（`issues.py` 侧供 `read_rename_snapshot()` 直读两池 legacy table），MUST NOT 被新写路径调用。契约继续锁**行为等价层而非字面层**：docstring/注释按 recorder 语境分化合法，逻辑 AST 分叉才报红。测试 MUST NOT 抽公共运行时模块或建立 recorder 间 import。`PRIORITIES` 等非函数常量继续走独立值相等断言，不塞进函数 source harness。

#### Scenario: 三向 frontmatter/lock helper 逻辑分叉
- **WHEN** 三向 roster 中任一 helper 在 buglist/todolist/issues 三份剥 docstring 后 AST 不等
- **THEN** 一致性测试失败并指明 helper 与不一致 recorder，MUST NOT 因三条 CLI 当前样例恰好都绿而放行

#### Scenario: dated bytes helper 与 text helper 边界漂移 `[grill-amendment]`
- **WHEN** 任一 recorder 缺少 `atomic_write_bytes`/binary document helper，或 dated writer 回退调用 text `atomic_write`
- **THEN** mirror/call-graph 测试失败；生成型 INDEX/batches 继续使用 text helper不算漂移

#### Scenario: 两向 legacy/ID helper 逻辑分叉
- **WHEN** 两向 roster 中任一 helper 在 buglist 与 todolist 剥 docstring 后 AST 不等
- **THEN** 一致性测试失败；`[spec-review-amendment]` 已被 direct rename snapshot 提升为三向行为契约的 scanner/semantic/merge 规则不得继续只靠两向守护，pool-specific 展开以 golden equivalence 覆盖

#### Scenario: direct rename snapshot 与 recorder scan 语义漂移 `[spec-review-amendment]`
- **WHEN** 同一 canonical/pure-legacy/overlay fixture 分别经 issues direct snapshot 与 bug/todo `scan --json` contract 解析
- **THEN** effective items/problems 按 semantic key 完全等价，issues 结果另带 raw bytes/spans；任一方漏掉 lexical/marker/overlay/ID rule 时测试失败

#### Scenario: scan JSON consumer validator 不默认空池 `[spec-review-amendment]`
- **WHEN** producer JSON 缺 `bugs|items`/`problems`、类型错误或 item 缺 `file`
- **THEN** `validate_scan_envelope` 测试要求 issues fail-closed，MUST NOT 以 `.get(..., [])`/falsey fallback 继续

#### Scenario: docstring 与注释差异不报漂移
- **WHEN** 某共享 helper 的可执行 AST 等价，但 docstring/注释按 bug/todo/issues 语境不同
- **THEN** 一致性测试通过，不把合法说明差异误报为行为漂移

#### Scenario: roster helper 被删除或改名
- **WHEN** 某 recorder 删除/改名一个仍在显式 roster 的 helper而未同步契约
- **THEN** 测试因 source lookup 失败而红，MUST NOT 动态跳过不存在的名字

#### Scenario: 已退役 table-cell helper 不再被强制存在
- **WHEN** 实现按 SW-RI-1 删除三份 `_reject_cell_unsafe`
- **THEN** mirror test 不因该旧 helper 缺失而失败，且 source/调用图检查确认新索引写路径无其引用；Markdown 单行安全由 `_reject_line_unsafe` 独立守护

#### Scenario: legacy parser 只读边界
- **WHEN** 新 canonical/overlay item 经 add/set-status/triage/batch rename 写入
- **THEN** 调用跟踪显示 `split_sections`/`parse_table_rows` 仅在 legacy read/overlay merge 中执行，writer 不渲染或修改 legacy table row

#### Scenario: PRIORITIES 常量跨脚本一致性
- **WHEN** `issues.py` 声明的 `PRIORITIES` 与 `buglist.py` 值不相等
- **THEN** 独立列表值相等断言报红；该断言不进入 `inspect.getsource` 函数 harness

#### Scenario: mirror guard 不建立运行时耦合
- **WHEN** 一致性测试加载三个 recorder
- **THEN** 它以测试期 importlib/inspect 读取源码完成比较，生产脚本之间没有新增 Python import，独立安装/调用仍成立

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

