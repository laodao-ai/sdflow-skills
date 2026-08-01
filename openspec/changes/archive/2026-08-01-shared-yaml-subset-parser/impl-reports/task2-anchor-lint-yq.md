# Task 2 实现报告 · anchor_lint.py 的 YAML 解析改为 yq

## 状态：DONE

## 做了什么

两份 `anchor_lint.py`（`openspec/workflow/tools/anchor_lint.py` 与
`sdflow-init/assets/workflow/tools/anchor_lint.py`）：

1. 新增 `_yq()` 薄封装（design.md §1 参考实现逐字照抄，仅按 R6 精神去掉本文件用不到的
   `os` import——本文件只读、无 `in_place`/环境变量写路径，保留会是死代码）：
   `shutil.which` 检测 → `--version` 身份校验（`mikefarah` 字符串命中，拒 kislyuk/yq）→
   进程内缓存（`_yq_bin` 模块级变量）→ `subprocess.run` 起 yq 子进程，`encoding="utf-8",
   errors="replace"` → exit≠0 一律 `raise RuntimeError`（不吞）→ `stdout` 为空/`"null"`
   走 `default` 参数、否则 `json.loads`。
2. `read_metrics_enabled` 改为：
   ```python
   def read_metrics_enabled(root):
       cfg = Path(root) / "openspec" / "config.yaml"
       if not cfg.exists():
           return False                                        # ①
       val = _yq(".metrics.enabled", cfg, default=False)
       if not isinstance(val, bool):
           raise MetricsError(f"metrics.enabled 不是合法布尔值: {val!r}")
       return val
   ```
   删除了手搓的 `_ENABLED` 正则（`^\s+enabled:\s*(true|false)\s*$`）与整段逐行扫描
   （定位 `metrics:` 顶层键 → 扫到下一顶层键前找 `enabled:` 行）。
3. 更新模块顶部零依赖声明注释（此前该文件从未有此类注释——新增一条，非改写旧的）：
   > 零依赖不变量：本文件 MUST NOT `import yaml`/pyyaml；唯一的 YAML 读取点（metrics.enabled）
   > 委托给外部 yq 二进制（mikefarah/yq，同 git 的外部二进制先例，见 `_yq()`），不手搓解析。
4. 两份副本 `diff` 确认字节一致。

## 关于「真四态」语义在 yq 委托下的保真度（TDD 过程中定位的关键决策点）

先探明了本机 yq（mikefarah v4.53.3，通过 winget 安装，见下方「环境准备」）在四态输入下的
实际返回值（`yqtest/` 临时探针，见 `git status` 确认未纳入仓库）：

| 输入 | yq `.metrics.enabled` 返回 | 旧实现（正则）行为 |
|---|---|---|
| 文件不存在 | exit 1（yq 报错，非 exit0+null） | return False |
| 无 `metrics:` 顶层键 | `null`（exit 0） | return False |
| `enabled: yes` | JSON 字符串 `"yes"`（YAML 1.2 不认 `yes` 为布尔，与旧正则拒绝的原因不同但结论一致） | raise MetricsError |
| `enabled: true` | JSON 布尔 `true` | return True |
| 同级另一段 `other:\n  enabled: true` 干扰 | yq 路径查询天然按 `.metrics.enabled` 定位，不受干扰 | return False（旧实现靠"下一顶层键"扫描做到） |
| `metrics:\n# 注释\n  enabled: true` | `true`（yq 原生跳过注释） | return True |

**文件不存在**这一态与 yq 原生行为冲突（yq 对不存在的文件是 exit 1 而非 exit0+null）——
若直接 `_yq(".metrics.enabled", cfg, default=False)` 不做前置判断，会在消费仓
"从未生成过 `openspec/config.yaml`"这一**最常见路径**上把 `RuntimeError` 意外抛给
调用方（`main()` 目前只 catch `MetricsError`，不会 catch 到会导致未处理异常直接崩溃）。
故保留了 `cfg.exists()` 前置短路——这是 Python 侧的文件存在性判断，不是 YAML 解析逻辑，
不违反"YAML 解析全部委托 yq"的约束（R6：业务逻辑保留在 Python 侧）。

**`enabled: yes` 仍须 raise**（`test_metrics_block_illegal_raises` 既有测试断言）——但 yq
不会因为 `"yes"` 而报错（它是合法 YAML 标量，只是类型不是布尔）。故在 `_yq()` 调用之后加了
一行 `isinstance(val, bool)` 校验，非法则 raise `MetricsError`。这是本票在"最简单替换"
（design.md 原话）之上唯一必要的补充逻辑，理由：不加此行，`test_metrics_block_illegal_raises`
（既有测试，覆盖 mlh-p2-anchor-lint 原始设计意图"metrics.enabled 只接受严格小写
true/false"）会变红——而 ticket 验收要求"两份 `anchor_lint.py` 全绿"，且该测试并非本票
要删除或改写的范围（design.md 未点名它需要重写，不同于 tasks.md Task 8.3 明确点名的
`test_impl_route.py` 等）。

## 已知行为漂移（诚实边界，非缺陷，未被任何现有测试覆盖）

- `enabled: True`（首字母大写）：旧正则严格要求全小写 `true`，`True` 会被拒（raise）；
  yq 遵循 YAML 1.2 Core Schema，`True`/`TRUE` 均解析为合法布尔 `true`，因此新实现
  **放行**（不 raise）。这比旧实现更贴合 YAML 规范语义，且未被任何现有测试锁定为
  "必须拒绝"，判断为可接受的漂移（基准④：低概率、影响小、完美复刻旧字符串级怪癖的
  成本不成比例）。
- `metrics:` 顶层键存在但块内完全没有 `enabled` 子键（如 `metrics: {}`）：旧实现的
  "从下一顶层键前扫描"逻辑找不到匹配行会 `raise MetricsError`；新实现里 `.metrics.enabled`
  对 yq 而言等价于"键不存在"（`null`），委托给 `default=False`，**不 raise**、直接返回
  `False`。同样未被任何现有测试覆盖（现有测试只覆盖"无 `metrics:` 键"和"`enabled` 值非法"
  两种，未覆盖"`metrics:` 键在但空/无子键"）。保守方向仍是"默认不开度量"（False），
  未放宽任何 fail-closed 语义（该字段本身是 opt-in 开关，非安全关卡）。

## 附带修复：`test_anchor_lint_does_not_reference_resolve_models` 的字面断言过严

该既有测试（ADR-1 边界锁）字面断言 `"subprocess" not in code_only`——其真实意图是
"MUST NOT 起子进程调 resolve-models.sh 判宿主"，但字面实现把"起子进程"本身当作
代理信号，在当时（anchor_lint.py 从不起子进程）等价成立。引入 `_yq()` 后该代理信号
不再成立（yq 是合法子进程调用，与判宿主无关）。已改写该测试：保留
`resolve-models`/`resolve_models` 字符串缺席断言不变，把子进程检查改为"提取所有
`subprocess.run([...` 调用的参数列表，逐一断言不含 `resolve-models`/`resolve_models`"——
真正核验 ADR-1 意图（子进程只用来起 yq，不用来判宿主），而非"根本不起子进程"这个
已被本票合法推翻的更强断言。

## 环境准备（仅为跑测试，不影响仓库内容）

开发机（Windows）此前未装 `yq`：`shutil.which("yq")` 返回 None，导致所有走 `_run()`
CLI 路径（子进程调 `anchor_lint.py`）的既有测试都会在 `read_metrics_enabled` 内
`sys.exit(1)`。经 `winget list --id MikeFarah.yq` 确认 winget 已装 4.53.3 但未在
PATH（未生成 `WinGet/Links` 符号链接），复制
`.../WinGet/Packages/MikeFarah.yq_.../yq.exe` 到已在 PATH 上的 `~/bin/yq.exe`
使其可用。此为本机环境操作，未改动仓库任何文件。

## TDD 过程

1. Red：在既有测试文件追加 6 个 `_yq()` 专项测试（读值/default/非零退出 raise/未安装
   fail-loud/身份校验拒绝 kislyuk/进程内缓存只做一次身份校验），跑
   `pytest -k yq` 确认全部因 `AttributeError: module 'anchor_lint' has no attribute
   '_yq'`/`'shutil'`/`'subprocess'` 报红（`_mod()` 每次都新建独立模块实例，
   monkeypatch 互不污染）。
2. Green：实现 `_yq()` + 改写 `read_metrics_enabled` + 删 `_ENABLED` 正则，
   跑整个测试文件：142/143 绿，1 红（`test_anchor_lint_does_not_reference_resolve_models`
   的字面 `"subprocess" not in code_only` 断言，见上节分析）。
3. 按上节分析改写该测试的核验方式（保留真实意图、去掉已被合法推翻的字面断言），
   复跑：143/143 绿。
4. 同步两份副本、`diff` 确认字节一致，重跑一遍确认。

## 测试

新增 6 个 `_yq()` 专项测试（`sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`）：

- `test_yq_reads_scalar_true` — 真实 yq 读 `metrics.enabled: true` → `True`
- `test_yq_default_for_null` — 键不存在（stdout=null, exit0）→ `default` 参数原样返回
- `test_yq_raises_on_nonzero_exit` — 畸形 YAML（未闭合引号）→ 真实 yq exit 1 → `RuntimeError`
- `test_yq_not_installed_fails_loud` — monkeypatch `shutil.which` 返回 None → `SystemExit`
- `test_yq_identity_check_rejects_non_mikefarah` — monkeypatch `subprocess.run` 伪造
  kislyuk/yq 的 `--version` 输出 → `SystemExit`（且断言身份校验先于业务调用）
- `test_yq_version_check_runs_once_then_cached` — spy 包一层 `subprocess.run`，连续两次
  `_yq()` 调用只触发一次含 `--version` 的子进程（证明进程内缓存生效，非仅"变量非 None"
  的弱断言）

既有 137 个测试（含 `test_metrics_*` 六个真四态用例）全部保留、无删减，全绿。

改写 1 个既有测试（`test_anchor_lint_does_not_reference_resolve_models`，见上节说明）。

## 验证证据

| 命令 | 结果 |
|---|---|
| `python -m pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q` | **143 passed** |
| `diff openspec/workflow/tools/anchor_lint.py sdflow-init/assets/workflow/tools/anchor_lint.py` | 无输出（字节一致） |
| `grep -rn "_ENABLED\b" --include="*.py" .` | 无匹配（手搓正则确认清除，全仓） |
| `git status --short` | 仅 3 个文件被改：两份 `anchor_lint.py` + 1 份测试文件 |

全仓 `pytest`（跑其余 skills 的测试）已在后台发起，尚未回收结果；本票改动范围严格限于
`anchor_lint.py` 及其唯一测试文件，其余 skill 的测试逻辑上不应受影响（`read_metrics_enabled`/
`_yq()` 均为该文件私有符号，无任何跨文件 import）。

## Global Constraints 符合性

- 零依赖不变量：`yq` 是外部二进制（同 git 先例），`subprocess` 调用不违反
  `MUST NOT import yaml`——本文件全程未 `import yaml`/pyyaml。
- GC-2 边界锁：不受影响——`_yq()` 内联于本文件，未跨脚本 import，也未被其他脚本 import。
- `_yq()` 薄封装含 `shutil.which` 检测 + `--version` 身份校验（`mikefarah`）+ 进程内缓存
  （`_yq_bin` 模块级变量）+ fail-loud（`sys.exit(1)`）+ `encoding="utf-8",
  errors="replace"`。
- yq 非零退出 raise（`RuntimeError`），不吞；键不存在（exit0+null）与解析失败（exit≠0）
  是两条独立分支（`if r.returncode != 0: raise` 在前，`if not raw or raw == "null":
  return default` 在后，互斥触达）。
- 业务逻辑（`isinstance(val, bool)` 校验、`cfg.exists()` 前置短路）保留在 Python 侧，
  YAML 解析本身全部委托 yq。

## 未做 / 超出范围说明

- 未新增 `os` import——design.md §1 的参考实现签名含 `in_place`/环境变量写路径用得到
  `os`，但本文件只读 `.metrics.enabled`，不含任何写操作，保留会是死代码（基准④简化，
  且 Task 8.2 提到的"7 份封装核心逻辑字节一致"golden test 尚未落地，无法预先验证是否会
  因此产生假红；若未来该 golden test 要求连 import 行也字节一致，届时按其实际比对范围
  调整，不在本票预先加宽）。
- 未触碰其余 6 个待迁移脚本（`init.py`/`ship_gate.py`/`impl_route.py`/
  `roadmap_writeback_draft.py`/`sad_schema.py`/`setup.sh` 依赖预检已在 Task 1 完成）——
  均为 tasks.md 其余任务的范围。
