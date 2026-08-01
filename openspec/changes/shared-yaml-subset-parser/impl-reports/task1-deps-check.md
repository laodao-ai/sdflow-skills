# Task 1 实现报告 · setup.sh 依赖预检系统

## 状态：DONE

## 做了什么

`setup.sh` 新增 `_version_ge()` 辅助函数 + `check_dependencies()` 函数（`setup.sh:473-565`），
调用点在 `install_agents` / `install_sdflow` 之后、retire-hooks 段与四道门禁检查之前
（`setup.sh:573` 的 `check_dependencies` 调用）。

统一检测并报告 5 项运行依赖：

| 依赖 | 检测方式 | 缺失/不满足时的行为 |
|---|---|---|
| python3 >= 3.7 | 复用 `[T48]` 已选出的 `$_py`（不重新检测，见下方"既有逻辑迁入"） | `✗` + 计入 `missing[]` |
| git | `command -v git` | `✗` + 计入 `missing[]` |
| yq (mikefarah, >= 4.16.0) | `command -v yq` + `--version` 输出含 `mikefarah` + 正则提取版本号与 `_version_ge` 比较 | 未安装 → `✗` + 三平台安装命令；kislyuk/yq → `⚠` + 卸载重装指引；版本 < 4.16.0 → `⚠` 版本过低 + 升级指引；三种情形均计入 `missing[]` |
| openspec（可选） | `command -v openspec` | `·` 提示 npm 安装命令，**不计入** `missing[]` |
| pytest（开发可选） | `$_py -m pytest --version` | `·` 提示 pip 安装命令，**不计入** `missing[]` |

`missing[]` 非空时在预检块末尾输出汇总（含 yq 的三平台安装/升级命令），**不调用 `exit`**，
函数返回后脚本照常往下执行 retire-hooks → Summary → 四道机械门禁。

## 关于「既有 python3 检测逻辑迁入 check_dependencies()，不重复」

design.md 给出的 `check_dependencies()` 参考实现就是**消费**已选出的 `$_py`（`if [ -n "$_py" ]`），
不是重新跑一遍候选检测。核实后确认这是唯一可行读法：`[T48]` 的候选选择循环（`setup.sh:465-471`，
在 `python3`/`python` 间选首个 3.7+ 解释器）是脚本自身的**功能性前提**——`install_sdflow`
（写 capability manifest）与 retire-hooks 段都消费 `$_py`，且两者都跑在 `check_dependencies`
调用点**之前**；把候选选择本身挪到 `check_dependencies()` 内部会让这两处拿不到 `$_py`。

因此本实现的处理是：**候选选择循环原地不动**（它本就在 `install_sdflow` 之前），
`check_dependencies()` 只做统一的**状态报告**——这是此前脚本里从未存在过的（原来只有
`$_py` 的选择，没有任何地方把结果 echo 成一行状态供用户看）。「不重复」验证为：
全脚本运行一次的 stdout 中，`python3` 状态行（`✓`/`✗` 开头）**只出现一次**——测试
`test_python3_status_line_is_not_duplicated` 机械核验此点。脚本尾部四道机械门禁各自独立的
`command -v python3` 守卫（如 `sync_principles.py` 门前的检测）保持不动：那是各门禁调用
Python 脚本前的**防御性存在性检查**，与"给用户看的依赖状态报告"是不同性质的东西，
改动它们超出本 ticket 范围（不加宽）。

## 关于 yq 版本门（spec-review-amendment F5）

`tickets.md` Task 1 的验收复选框未逐字列出版本检测，但 `specs/yq-yaml-operations/spec.md`
Requirement R1（Task 1 的 R-ID 之一）在 spec-review-amendment F5 后明确要求：

> WHEN yq 已安装且为 mikefarah/yq 但版本 < 4.16.0 THEN 输出版本过低警告 + 升级指引

`spec-review-report.md` F5：`--front-matter` 选项在 yq v4.16+ 才可用，只查 `mikefarah` 不查
版本号会让"检测通过但实际用不了"的组合悄悄放行。design.md 的参考实现是 F5 裁决**之前**写的，
未反映这条修正；因为 R1 是本任务的权威需求源（且已定稿），本实现在 design.md 参考代码基础上
补上了版本比较（`_version_ge` + 正则提取 `--version` 输出中的 `X.Y.Z`）。

## TDD 过程

1. 先写 `hack/tests/test_check_dependencies.py`（6 个用例），跑 `pytest` 确认全部 RED
   （`check_dependencies` 不存在，函数调用点缺失）。
2. 按 design.md 参考实现 + F5 版本门实现 `check_dependencies()`，跑测试：4/6 绿，2 个失败
   ——**失败原因是测试自身的正则过宽**（`re.findall(r"[✓✗·][^\n]*openspec", stdout)` 命中了
   汇总段里 `sdflow-spec` / `openspec-upgrade` 等无关行；另一处 `⚠[^\n]*yq` 命中了 pytest
   为该测试函数生成的临时目录路径 `.../test_mikefarah_yq_with_suffici0/...`，因为该路径**字面包含**
   `"yq"` 子串）。修正：新增 `_deps_section()` 辅助函数，把断言范围收窄到
   `"运行依赖预检："` 到下一个 `"退役 hook 清理"` 标题之间的输出块，并把正则改为行首锚定
   （`^  [✓✗·] <label>\b`）。
3. 复跑：6/6 绿。
4. 追加跑 `hack/tests/` 全量（含 `test_install_agents.py` 等其余 6 个消费 `setup.sh` 的测试文件）
   核验无回归——见下方「验证证据」。

## 测试

新增 `hack/tests/test_check_dependencies.py`（6 用例，均通过）：

- `test_reports_a_status_line_for_each_of_the_five_dependencies` — 5 项依赖各恰好一行状态
- `test_python3_status_line_is_not_duplicated` — python3 状态行不重复（核验「既有逻辑迁入」验收项）
- `test_missing_yq_reports_cross_and_three_platform_install_commands` — yq 未安装 → `✗` + 三平台命令 + 不中止
- `test_kislyuk_yq_warns_and_gives_correct_install_guidance` — kislyuk/yq → 警告 + 正确安装指引 + 不中止
- `test_mikefarah_yq_with_sufficient_version_reports_ok` — mikefarah + >=4.16.0 → `✓`，无告警
- `test_mikefarah_yq_below_min_version_warns_upgrade` — mikefarah 但 <4.16.0 → 版本过低告警 + 升级指引（F5）

沿用仓内既定的 `setup.sh` 测试范式（`tmp_path` 当假 `HOME` 真跑 `bash setup.sh`，子进程），
yq 各分支通过在 `PATH` 前置一个假 `yq` 可执行脚本确定性复现（同
`test_sdflow_spec_agents.py::_scan_with_broken_grep` 注入假 `grep` 的手法）；"未安装"分支通过
`_path_without_yq()` 从真实 `PATH` 剔除含可解析 `yq` 的目录来复现（本机开发环境本就未装 yq，
该辅助函数对本机是恒等变换，对可能装了 yq 的 CI/其他机器仍具确定性）。

## 验证证据

| 层 | 命令原文 | 退出码 |
|---|---|---|
| 单元/集成（子进程真跑 setup.sh） | `python3 -m pytest hack/tests/test_check_dependencies.py -v` | 0（6 passed，137.61s） |
| 回归（同目录其余 setup.sh 消费方 + 全部 hack/tests） | `python3 -m pytest hack/tests/ -q` | 0（369 passed, 6 skipped，169.10s；6 个 skip 为既有 Windows 平台边界跳过，与本次改动无关） |
| Shell 语法 | `bash -n setup.sh` | 0（syntax OK） |

`git status --short` 确认改动范围只有 `setup.sh`（修改）+
`hack/tests/test_check_dependencies.py`（新增）+ 本报告，测试运行未污染仓外真实
`~/.claude/` / `~/.sdflow/`（`_run_setup` 全程走假 `HOME`）。

## Global Constraints 符合性

- 未新增 Python 入口脚本，`reconfigure` 前导要求不触发（本任务纯 shell）。
- `resolve-models.sh` 未改动。
- 未把 yq 打包进 `~/.sdflow/bin/`，检测逻辑只做 `shutil.which`/`command -v` 判定 + 提示，
  不下载不安装。
- 不重构依赖管理为框架——`check_dependencies()` 是单一函数、五个独立分支，无抽象层。

## 已知边界（诚实声明，非缺陷）

- `_version_ge` 只处理 `X.Y.Z` 三段整数比较，不处理预发布标签（如 `4.16.0-rc1`）——
  yq 官方 release 版本号不带此类后缀，正则 `[0-9]+\.[0-9]+\.[0-9]+` 会跳过不匹配的候选，
  此时 `yqnum` 为空，判定分支降级为"版本过低"（保守方向，不会误判为满足）。
- 四道机械门禁（`sync_principles.py` 等）各自的 `command -v python3` 防御性检查保持不动，
  不属于本任务范围（见上方说明）。
