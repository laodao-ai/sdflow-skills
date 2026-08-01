# Task 4 实现报告 · init.py 的 YAML 解析改为 yq

## 状态：DONE（含两处对 design.md 字面指令的证据驱动偏离，见下）

## 做了什么

`sdflow-init/scripts/init.py` 新增 `_yq()` 薄封装 + `_check_yq()` 探测门，把以下函数的
YAML **语法层**解析迁到 yq，Python 侧只保留业务判断：

- `_marker_schema` → `_yq('.', marker, default={})` + Python 校验（恰一个 `schema` 键、
  非空字符串），语义与旧版手搓正则一致。
- `_validate_schema_authority` → `_yq('[.artifacts[].template]', schema_asset, default=[])`
  + 模板路径存在性校验（业务逻辑不变）。
- `lint_config` → **一次性** `_yq('.', cfg_path, default={})` 读出整份 config.yaml 为
  dict，随后对 `schema`/`rules`/`model-tiers`/`metrics` 四项做 Python 侧结构校验（不再
  按键路径分别调用——任何一处语法错误都会让 yq 对同一文件的任何查询同等失败，一次读出
  更简单也更快）。
- `_parse_model_tiers_block`（行扫描 fleet_ctx 状态机）→ `_model_tiers_from_dict`（在 yq
  已解析出的 dict 上做 fleet/tier 键集校验、越域键检测、畸形头检测），设计上采用
  design.md §2「分离设计」的思路。
- 删除：`_strip_inline_comment` / `_find_top_level_block` / `_second_level_keys` /
  `_parse_model_tiers_block`（全部调用点已确认清空，见下方验证证据）。
- `lint_config` 入口前新增 `_check_yq()` 门：yq 不可用（未装/非 mikefarah）时返回一条
  带安装指引的 reason（不崩溃/不退出），与 `run()`（init/update）路径依赖既有
  `except (..., RuntimeError): _die()` 兜底的处理方式有意区分——`lint_config` 的公开
  契约是「返回 reason 列表」。
- 零依赖声明注释已更新（`_yq()` 定义处 + config-lint 小节头部两处）。

## 两处对 design.md 字面指令的偏离（证据驱动，均已用真实 yq 二进制验证）

### 偏离 1：`_schema_from_config` / `_set_schema_key` 保留既有字节级正则实现，未接入 yq

**design.md 字面指令**：`_schema_from_config` → `_yq('.schema', ...)`；`_set_schema_key` →
`_yq(f'.schema = "{schema}"', ..., in_place=True)` + `strenv()`。

**实测证据**（本机 yq v4.53.3 winget 安装，Windows）：

1. **写路径会破坏数据，不只是格式**：`yq -i` 对
   `--- # local config\ncontext: keep\n` 执行 `.schema = "x"` 后，输出
   `# local configcontext: keep\nschema: x`——`context: keep` 被合并进注释行，
   `context` 键从此在语义上消失（`yq -o=json '.' <file>` 复读验证：`{"schema": "x"}`，
   `context` 彻底丢失）。这超出 spec-review-report.md F14「yq -i 静默 CRLF→LF，记为已知
   边角」已接受的范围——F14 讨论的是换行风格差异（cosmetic），这里是键级数据丢失
   （semantic）。
2. **读路径同样受影响，且两个缓解方向互斥**：mikefarah/yq 的 `--header-preprocess`
   （管理文档头部注释/分隔符的预处理特性）在「`--- # 注释` 紧跟一个真实内容行」的输入上
   会把**该内容行整体吞并进注释**，那一行在解析结果里彻底消失（非格式差异）：
   - 默认 `true`：`--- # local config\nschema: x\ncontext: keep\n` 查 `.` 得到
     `{"context": "keep"}`——`schema` 键消失。
   - 显式传 `--header-preprocess=false`：确实修好了上面这个场景，但会让含
     `%YAML 1.2` / `%TAG` 文档指令的文件直接解析失败
     （`yaml: found incompatible YAML document`），而这正是本文件已有测试
     `test_update_inserts_schema_after_yaml_directives_and_document_start` 覆盖的场景。
   两个设置各打破一类本文件测试套件已锁定的真实场景，**没有能同时满足两者的单一 flag**
   （已尝试寻找第三条路，未找到；yq 也没有更细粒度的开关）。
3. `_schema_from_config` 与 `_set_schema_key` 是一对读写搭档（`handle_config` 用前者做
   「是否需要写」的比较基准，二者语义耦合），保持两者同为既有实现，逻辑最简单也最一致。

**为什么这不违反基准 5（无界不手搓）**：这两个函数处理的语法面是「一个固定字面量键
`schema:`」的定位与原地替换，是**有界**语法面（穷举得完：BOM 前缀、大小写、行内注释、
键前空白、文档起始符——本文件已有测试把这些边界全部枚举并锁定），不是通用 YAML 递归
结构解析器。基准 5 警戒的是「无界语法面手搓」，这里恰恰相反：继续手搓是因为**手搓已经
正确、且比 yq 更正确**（yq 在这个具体场景上有确认的缺陷）。

**影响面**：`_set_schema_key` 写操作因此**未**改用 `strenv()` 传值（ticket 验收项之一
未按字面完成）——但该函数从未经过 subprocess/shell，是纯 Python 正则替换，本来就没有
`strenv()` 要防护的注入面（R13 针对的是「值经 shell 命令行/yq 表达式插值」的注入风险，
这里根本不成立）。

### 偏离 2：`_yq()` 统一附加 `--header-preprocess=false`

design.md §1 参考实现没有这个 flag。为保证 `_marker_schema`/`_validate_schema_authority`/
`lint_config` 三处消费点（marker 文件、schema.yaml 资产、任意用户 config.yaml）在
「文档以 `--- # 注释` 起始」时不触发上述吞行 bug，`_yq()` 统一附加该 flag。三处消费点
的实际文件形状均不含 YAML 指令（`%YAML`/`%TAG`），故不会撞上该 flag 的另一侧代价。
`lint_config` 现有测试语料未覆盖「config.yaml 以 `--- # 注释` 起始」这一形状，但保留该
flag 是纯粹的防御性加固（不会让任何现有测试变红，见验证证据）。

### 未偏离但值得记录：`_validate_schema_authority` 未采用 ticket 字面表达式

ticket 与 design.md 均写 `_validate_schema_authority` → `_yq('.template', schema_yaml_path)`。
实测该表达式对真实 `schema.yaml`（`template:` 键嵌套在 `artifacts[].template`，非顶层）
恒返回 `null`——若照抄会让本函数**永远检测不到缺失模板**（`test_schema_bundle_missing_
authority_fails_loudly` 与 `test_update_missing_referenced_template_does_not_prune_or_
switch_config` 两个既有测试会假绿放行）。改用 `_yq('[.artifacts[].template]', ...)`
（数组包裹回避 F3 多文档防御误判，见函数 docstring），两个既有测试均已验证通过。

## `_parse_model_tiers_block` → `_model_tiers_from_dict` 的行为变化（既定代价，非缺陷）

旧版行扫描器能局部容错两类语法错误（漏冒号叶子、机队头带尾随内容+更深缩进子块），
在真实 YAML 语法下二者都是 `mapping values are not allowed in this context` /
`found character that cannot start any token` 级别的**整份文档语法错误**——yq 委托后，
这类输入会让 `_yq('.', cfg_path)` 直接对**整份 config.yaml**报错（不只是 model-tiers
段），`lint_config` 相应给出一条通用「解析失败」reason，不再有旧版「fleet_ctx 保持、
局部诊断」的能力。已确认涉及测试：

- `sdflow-init/tests/test_config_lint.py::TestConfigLintWholeDocumentParseFailure`
  （重写自原 `TestConfigLintLeafMissingColonNoPoison`）。
- `sdflow-init/tests/test_config_lint.py::TestModelTiersFromDict`（新增，替代原直测
  `_parse_model_tiers_block`/`_find_top_level_block` 的白盒测试）。
- `sdflow-init/tests/fixtures/model_tiers_cases.py` 四条用例（`leaf_missing_colon_
  sustains_fleet` / `fleet_header_trailing_content_rogue` / `injection_backtick` /
  `injection_double_quote`）的 `lint_reason_substrs` 改为通用 `"解析失败"`
  （`lint_clean` 不变，仍为 False）——`resolver`/`injection_marker` 字段未动，
  `test_resolve_models.py` 消费方式不受影响（已验证 31 passed）。
- `test_config_lint.py::TestConfigLintModelTiersFleetKeyed::test_flat_invalid_model_id_
  value_nonzero`（反引号值，同一根因，同一处理）。

这是 spec-review-report.md F9/decision-memo 已接受的既定代价（yq 委托换取「不手搓 YAML
解析器」，诊断精度必然下降到「整文件解析失败」粒度），不是本票引入的新缺陷。

## 附带发现的测试基础设施问题（已修复）

`test_init.py::TestProjectLocalSchema._version()` 辅助方法原先**无差别**把
`init_mod.subprocess.run` 换成一个恒返回假 `openspec --version` 输出的 stub——这在
`_yq()` 引入之前是安全的（`_openspec_cli_version` 是模块内唯一的 `subprocess.run`
调用点），但 `_yq()` 加入后，同一 mock 会截获 yq 自身的 `subprocess.run` 调用（版本
身份校验 + 实际查询），把假的 "1.7.0\n" 当作 yq 输出去解析，导致
`_validate_schema_authority` 等函数报「不可读取」。已改为按命令行是否指向 yq 二进制
分流（`"yq" in os.path.basename(cmd[0]).lower()` 则放行给真实 `subprocess.run`），
只在探测 `openspec --version` 时才返回假 Proc。5 个此前受影响的测试
（`test_semver_numeric_gate_accepts_1_10` 等）修复后全绿。

## 测试

```
pytest sdflow-init/tests/test_config_lint.py -q          → 31 passed
pytest sdflow-init/tests/test_init.py -q                 → 70 passed, 1 skipped
pytest sdflow-init/tests/test_init_hardening.py \
       sdflow-init/tests/test_init_contract_sync.py -q   → 10 passed, 2 skipped
pytest sdflow-init/tests/test_task5_regression.py -q     → 8 passed
pytest sdflow-init/tests/test_resolve_models.py -q       → 31 passed（共享 fixture 未破坏）
pytest sdflow-init/tests/test_runtime_gitignore.py \
       sdflow-init/tests/test_setup_failsafe.py -q       → 16 passed
pytest sdflow-init/tests/ -q                              → 2 failed, 379 passed, 20 skipped
```

**关于全仓 `pytest sdflow-init/tests/` 的 2 个失败（如实报告，非本票引入）**：

1. `test_hack_shell_multibyte_guard.py::test_no_unbraced_variable_before_non_ascii[setup.sh]`
   ——`setup.sh:530`（Task 1 新增的 `check_dependencies()` yq 版本检测代码：
   `echo "... ($yqv，需 >= ..."`）里一个中文全角逗号紧跟 `$yqv`，触发 bash 3.2 下
   `set -u` 的变量名吞字节风险。**已用 `git stash` 验证 baseline（无本票任何改动）同样
   失败**——与 Task 4/init.py 无关，是 Task 1 遗留、本票范围外的问题。
2. `test_outside_voice_utf8.py::test_pure_ascii_loses_zero_bytes`（或同文件另一测试，两次
   独立全量跑分别在不同用例上超时）——300 秒 bash 子进程超时，该测试对
   `outside-voice.sh` 的 `utf8_head_trim`/`utf8_tail_skip` 做 O(n) 次逐字节 bash 子进程
   扫描（n≈300+），与 init.py/yq 无任何交集（该文件不 `import init`）。两次全量跑
   （分别耗时 26 分钟、25 分钟）命中的具体超时用例不同，指向系统负载导致的非确定性超时，
   而非确定性回归——本次开发过程中长期有多个并行 yq/pytest 子进程在跑，推高了系统负载。

两者均已确认**不在本票改动范围内**（`grep "import init"` 两文件均无命中）。逐文件隔离跑
（见上方列表）覆盖了本票实际改动的全部消费面，均 100% 绿；仅供参考的全量跑因这两个
无关问题非 100% 绿，如实记录，非隐瞒。

## TDD 说明

本票是对既有生产代码 + 既有大型测试套件的重构（非从零新增功能）。流程：先跑通基线，
逐函数替换实现，每步用现有测试当回归防线验证；红→绿的转折点逐一分析根因（yq 语义 vs
旧手搓语义的必然差异 / 真实 yq 缺陷 / 测试基础设施的隐藏耦合），归类为「预期契约变化」
（已更新断言并写明理由）或「需要保留旧实现」（已在上方偏离 1/2 中详述证据），而非放松
断言掩盖或强行削足适履。新增测试覆盖 `_yq()`/`_check_yq()` 本体（default 分支、非零
退出 raise、未安装 fail-loud、身份校验拒绝 kislyuk）与 `_model_tiers_from_dict`
（entries 归属、bad_headers 分支、None→空串映射）。

## Global Constraints 符合性

- 零依赖不变量：`yq` 是外部二进制，`subprocess` 调用不违反 `MUST NOT import yaml`。
- GC-2 边界锁：`_yq()` 内联于本文件，未跨脚本 import。
- `_yq()` 含 `shutil.which` 检测 + `--version` 身份校验（拒 kislyuk/yq）+ 进程内缓存 +
  fail-loud（`raise RuntimeError`，非 `sys.exit`——遵循 init.py 自身既有的错误处理模式：
  `run()` 路径靠既有 `except (..., RuntimeError): _die()` 统一兜底，`lint_config` 路径
  经 `_check_yq()`/`try-except` 转成 reason 字符串，两条路径都不需要 `_yq()` 自己
  `sys.exit`）。
- yq 非零退出恒 `raise`，不吞；键不存在（exit0+null）与解析失败（exit≠0）两条独立分支。
- `_set_schema_key` 写操作**未**接入 `strenv()`（见「偏离 1」——保留纯 Python 实现，
  无 subprocess/shell 注入面，R13 的防护对象不成立）。
- 业务逻辑（fleet/tier 键集校验、模板路径存在性、marker 单键校验）保留在 Python 侧。

## 未做 / 明确交代

- `_set_schema_key` 未迁 yq（偏离 1，证据见上）。
- `_schema_from_config` 未迁 yq（同一偏离，二者是读写搭档）。
- 全仓 `pytest`（Task 7.2 收尾票职责）与 CI yq 钉版本（Task 8.1）不在本票范围。
- Task 5 的 golden test（7 份 `_yq()` 核心逻辑一致性）需要知悉：本文件的 `_yq()` 比
  anchor_lint.py 的版本多了 F3 多文档防御 + `--header-preprocess=false`，比
  ship_gate.py/impl_route.py 的版本少了 `text=` stdin 支持（本文件所有调用点都有磁盘
  文件路径，无需从 git-show 取文本）——差异原因已在 `_yq()` docstring 中说明。
