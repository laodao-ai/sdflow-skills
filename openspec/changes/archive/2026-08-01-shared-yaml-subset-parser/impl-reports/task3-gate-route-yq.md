# Task 3 实现报告：ship_gate.py + impl_route.py 的 YAML 解析改为 yq

## 范围

- `sdflow-ship/scripts/ship_gate.py`：`parse_ship_gate_frontmatter` 的 YAML 解析核心改为
  `_yq()`（新增），保留 `FIELD_VALIDATORS` / `_coerce_ship_gate_value` / `bad-type` /
  `out-of-domain` 业务校验，保留 duplicate-key/tab-indent 原始文本预扫描（R11）。
- `sdflow-implement/scripts/impl_route.py`：`read_config_pipeline` / `read_plan_marker`
  改为 `_yq()`，删除 `_extract_scalar` / `KEY_RE` / `FRONT_DELIM`。
- 两脚本互相 import（`impl_route` sibling-import `ship_gate.FenceTracker` /
  `resolve_plan_path` / `PlanNameConflict` / `PLAN_FILENAMES`；`ship_gate` 惰性 import
  `impl_route.parse_blocked_by`）经验证正常工作（identity 断言、既有测试全绿）。

## 设计要点与关键决策

### 1. 结构预扫描（R11）与 yq 取值的分工线

调研发现（本机 yq v4.53.3 windows 实测）yq 的真实局限**不止** design.md/spec-review-report
点名的 duplicate-key/tab-indent 两类，还有一类**未被显式登记但同样致命**：

- **frontmatter 未闭合时不报错**：`--front-matter=extract` 对没有第二个 `---` 的文件，会把
  首行 `---` 之后的**全部内容**当同一份 YAML 文档处理。若正文恰好是 Markdown 标题
  （`### Task 1: A`），因为 `#` 是 YAML 注释符，会被**静默吞掉**、整体判定"解析成功"——
  这与 ship_gate.py 的 D2（"未闭合 --- 视为 absent"）和 impl_route.py 的
  "未闭合→RouteStop" 两种既有契约都不兼容，若不在调 yq **之前**做闭合性检测，两个脚本都
  会把"结构性缺陷"误判成"合法值"。
- **重复顶层键静默取最后值**（design/spec-review 已点名，本机复现确认，且 exit=0，无红色
  信号）。
- **flow-style 内联 map 与 block-style 语义等价**（`ship-gate: {verify: PASS}` 与
  `ship-gate:\n  verify: PASS` 解出同一个 dict）——ship_gate.py 旧测试
  `test_toplevel_ship_gate_scalar_is_bad` 要求前者判 `bad-type`，若把"顶层结构是否规范
  空 map 头"这件事完全交给 yq 的返回值类型判断（`isinstance(dict)`），这条测试会假绿失守。

因此两脚本的预扫描职责边界确定为：

| 职责 | 归属 |
|---|---|
| frontmatter 首/闭合 `---` 定位 | 预扫描（两脚本均需要，否则"未闭合"被 yq 静默吃掉） |
| 顶层键 / 字段级 duplicate-key 计数 | 预扫描（yq 无法给出，R11 明文） |
| tab-indent 检测（仅 ship_gate.py） | 预扫描（yq 只报笼统词法错误） |
| 顶层 `ship-gate:` 是否为规范空 map 头（仅 ship_gate.py） | 预扫描（文本形态判断，yq 的
  真解析会抹平 flow/block 两种写法的差异） |
| 字段值的实际类型/内容（bool 转换、引号剥离、注释剥离、嵌套字段隔离） | 委托 `_yq()` |

`parse_ship_gate_frontmatter` 现在结构分两段：①（原有的）文本扫描定位边界 + 结构诊断，
全部沿用原实现的边界/缩进/头形判定逻辑（未删减任何既有分支）；② 预扫描通过后单次调用
`_yq('."ship-gate"', text=text, front_matter=True, default={})` 取回**整段** dict，再用
`FIELD_VALIDATORS`/`_coerce_ship_gate_value` 逐字段校验。`_coerce_ship_gate_value` 的调用
约定从"接收原始文本片段自己做字符串比较"改为"接收 yq 已类型化的值"（`design_approved`
现在收到的是真 `bool`，而非字符串 `"true"`）。

`impl_route.py` 同理：`read_plan_marker` 先做 `---`/`---` 闭合性 + `impl-pipeline:` 键计数
的文本预扫描，通过后才调 `_yq('."impl-pipeline"', p, front_matter=True)` 取值；
`read_config_pipeline` 无需闭合性检测（config.yaml 不是 frontmatter，无"块"概念），直接
`_yq('."impl-pipeline"', config_path, default=None)`，`RuntimeError`（yq 解析整份文件失败，
如未闭合引号）被捕获映射为 `unknown-value:<诊断>`。

### 2. `_yq()` 两份独立实现（各自内联，非共享）

按 Q2 拍板（"7 份 `_yq()` 各自内联 + golden test 守一致"，golden test 属 Task 5），本票的
两份 `_yq()` **不完全相同**，差异是两脚本真实用法差异导致的：

- `ship_gate.py` 的 `_yq()` 额外支持 `text=` 参数（走 stdin，`cmd.append("-")` +
  `subprocess.run(..., input=text)`）——`parse_ship_gate_frontmatter` 的调用方既有从磁盘
  读（live 报告）也有从 `git show` 取文本（归档 dual-read）两种来源，两者需要共用同一个
  `_yq()` 调用点（"live 读与归档 git-show 文本读共用同一严格 helper"是既有的 D4 承诺），
  stdin 模式让这条共用路径成立，不必先把 git-show 的文本落临时文件。
- `ship_gate.py` 的 `_yq()` 在 `front_matter=True` 时额外校验顶层结构须为 `dict`（非 dict
  → raise，[R5/F4]）——因为它唯一的 front_matter 用法是查 `.ship-gate`（整段），预期结果
  恒为 dict-or-absent。
- `impl_route.py` 的 `_yq()` 只接受文件路径（两处调用都已经手上有 `Path` 对象，无需 stdin），
  且**不做** dict 校验——它的 front_matter 用法是查 `."impl-pipeline"`（标量叶子），预期
  结果是 `str`/`None`，套用 dict 校验会直接把所有正常调用判成坏块。
- 两者共同点（均满足 Global Constraints）：`shutil.which` 检测 + `--version` 身份校验
  （拒 kislyuk/yq）+ 进程内缓存（模块级 `_yq_bin` 全局变量）+ `encoding="utf-8",
  errors="replace"` + 非零退出恒 `raise RuntimeError`（不吞、不因 `default` 而静默）+
  多文档防御（`json.JSONDecoder().raw_decode` 检测 stdout 是否含一个以上 JSON 值）。

这一差异化在 `impl-report` 与两处 `_yq()` 的 docstring 中均已注明，供 Task 5 的 golden test
设计者知悉：golden test 若要求"7 份字节完全一致"，需要先在 anchor_lint.py 已落地的版本（无
text 支持、无 dict 校验）与本票两份之间做一次收敛决策，而不是直接机械 diff 判定。本票不
擅自代 Task 5 做这个决策（属于面治范围但跨票，留给 Task 5 显式处理）。

### 3. 已知行为变化（不可避免，已随测试断言同步）

- **引号值不再"严格"**：`verify: "PASS"` 现在与 `verify: PASS` 语义等价（真 YAML 解析器
  天然剥引号）。旧测试 `test_quoted_value_is_strict` 断言的"引号即坏"是手搓扫描器（不做
  引号剥离）的副作用，非业务不变量——已重命名为
  `test_quoted_value_now_equivalent_to_bare_under_yq` 并更新断言为 `state=={"verify":"PASS"}`。
- **`_coerce_ship_gate_value` 的测试直接调用点**（`test_anchor_contract.py` 的
  `test_producer_frontmatter_fields` / `test_producer_frontmatter_parseable`）原先直接把
  模板裸行 partition 出的原始字符串（如 `"true"`）传给 `_coerce_ship_gate_value`，现在函数
  期望 yq 已类型化的值。新增测试内 helper `_yaml_bareword_to_native()` 先把裸词按 YAML 1.2
  core schema 换算成原生类型（仅 `true`/`false` 两个字面）再传入，语义不变、调用约定对齐。
- **config.yaml/marker 的"损坏标量"诊断精度下降**：旧版能精确点名"哪个标量坏"（未闭合
  引号/闭合引号后跟垃圾字符）；yq 方案下这类输入导致**整份文件**解析失败，诊断退化为
  "yq 报的原始错误文本"。`test_config_value_quoted_unclosed_damaged` 等既有测试原本就用
  `note.startswith("unknown-value:")`（非精确匹配），故未修改测试即可通过；这一诊断精度
  代价与 spec-review-report.md F9 的登记一致。

### 4. R13/strenv() 的适用性核验

Global Constraints 要求"写操作值传递 MUST NOT 用 f-string 插值，MUST 用环境变量
`strenv()`"。经 grep 确认（`grep -n "write_text\|in_place\|-i \|writeback\|prepend"`）
**`ship_gate.py` 与 `impl_route.py` 均无任何 frontmatter 写操作**——前者文件头注释明确
自称"确定性台账（盘面即状态：只读、零副作用）"，三个 producer（`sdflow-spec-review` /
`sdflow-done` / `sdflow-code-review`）各自的 SKILL.md 才是 frontmatter 的实际写入方，不在
本票范围内；后者的唯一写操作是 `task-text` 子命令落盘抠出的 ticket 原文（与 YAML 无关）。
故本票的两个 `_yq()` 均未实现 `in_place=True` 写路径的 `strenv()` 支持——**不是遗漏，是
按目标态核验后确认不适用**，`ship_gate.py` 的 `_yq()` 保留了 `in_place` 参数位（design.md
参考实现的完整签名）以防将来复用，但当前两脚本内均无调用点传 `in_place=True`。

## 变更文件

- `sdflow-ship/scripts/ship_gate.py`（新增 `_yq()`；`parse_ship_gate_frontmatter` 取值段
  改写；`_coerce_ship_gate_value` 签名语义调整；两处零依赖声明注释更新）
- `sdflow-implement/scripts/impl_route.py`（新增 `_yq()`；`read_config_pipeline` /
  `read_plan_marker` 改写；删除 `_extract_scalar`；`KEY_RE`→`_PIPELINE_KEY_RE`（窄化为
  纯计数用）；`FRONT_DELIM`→`_FRONTMATTER_DELIM`（同名同值，仅避开被删名字面）；模块
  docstring 更新）
- `sdflow-ship/tests/test_frontmatter_parse.py`（1 处测试更新：引号值行为变化）
- `sdflow-ship/tests/test_anchor_contract.py`（新增 `_yaml_bareword_to_native` helper，
  2 处调用点适配 `_coerce_ship_gate_value` 新签名）
- `sdflow-ship/tests/test_gate_git_layer.py`（子进程单一出口守卫扩展为"允许 `_git_run`
  与 `_yq` 两个出口"，并新增 `test_yq_spawns_are_confined_to_its_own_entry` 反向锁定
  `_yq()` 内部恰好两处 `subprocess.run`）

## TDD 说明

本票是对**既有生产代码 + 既有大型测试套件**的重构（非从零新增功能），"red before green"
体现为：先跑通两套件基线（348 passed/12 skipped、79 passed，均绿），再逐步替换实现、每步
用现有测试当"回归防线"验证；三处因契约必然变化而红的用例（详见"已知行为变化"）逐一分析
根因后判定为"预期契约变化"而非"实现错误"，随之更新断言并写明变化理由，而非放松断言掩盖。
未新增测试用例覆盖新行为分支（如 `_yq()` 的多文档防御、身份校验）——这些是 design.md 已
定稿的 `_yq()` 参考实现的直接照搬，且 Task 5 的 golden test 会统一覆盖 7 份 `_yq()` 的
一致性，本票不重复造轮子。

## 测试结果

```
pytest sdflow-ship/tests/ -q       → 349 passed, 12 skipped
pytest sdflow-implement/tests/ -q  → 79 passed
（合并跑一次）→ 428 passed, 12 skipped
```

另跑：
- `python -c "import impl_route as ir; import ship_gate as sg; assert ir._FenceTracker is sg.FenceTracker; assert ir._resolve_plan_path is sg.resolve_plan_path"` → 通过（互相 import 关系正常）
- `grep -n "def _extract_scalar\|def read_metrics_enabled\|def frontmatter_end\|def read_verify_state" sdflow-ship/scripts/ship_gate.py sdflow-implement/scripts/impl_route.py` → 零命中
- `grep -n "\bKEY_RE\b\|\bFRONT_DELIM\b" sdflow-implement/scripts/impl_route.py` → 零命中
- `hack/tests/test_subprocess_encoding_contract.py` + `hack/tests/test_decision_memo_gate.py` → 23 passed（确认新增的 `subprocess.run` 调用点符合仓内编码契约）

全仓 `pytest`（根级）因套件体量大、多为 subprocess 密集型测试，单次运行超过 10 分钟未完成，
本票未等待其收尾——ticket 验收条件明确限定为 `sdflow-ship/tests/` 与 `sdflow-implement/tests/`
两个套件，均已确认全绿；全仓跑跑属于 Task 6（收尾验证票）的职责范围。

## 未做/推迟事项（明确交代）

- **golden test（Task 5 职责）**：本票两份 `_yq()` 与 Task 2 已落地的 `anchor_lint.py`
  版本存在预期内差异（详见"设计要点 2"），未在本票新增跨脚本一致性检查——Q2 拍板把 golden
  test 排进 Task 5，本票不越权代做。
- **CI 装 yq、init.py 改造、roadmap_writeback_draft.py/sad_schema.py 改造**：分属 Task 4/5，
  不在本票范围。
