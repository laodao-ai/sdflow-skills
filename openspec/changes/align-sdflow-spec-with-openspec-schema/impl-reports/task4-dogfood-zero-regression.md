# Task 4 实现报告：dogfood 零回归验证

状态：BLOCKED

## 范围

仅执行 Task 4 dogfood 验证；未修改生产实现，未勾选 `tickets.md`，未创建 task checkpoint。
验证用 change `task4-dogfood-validation-20260731` 已创建、读取 CLI 载荷并删除，不进入最终工作树。

## 验证证据

### 切换前状态

- CLI：`openspec --version` → `1.7.0`
- 在途 change：`align-sdflow-spec-with-openspec-schema`
- `openspec status --change align-sdflow-spec-with-openspec-schema --json`：schema=`spec-driven`；`proposal/specs/design/tasks` 均为 `done`。

### 初始化/更新流程

命令：

```text
python3 sdflow-init/scripts/init.py update --dev --root .
```

实际输出关键结论：

```text
版本门：不铺 project-local schema（命令不可用（[WinError 2] 系统找不到指定的文件。）），保持内置 spec-driven
迁移在途 change：跳过（CLI 版本门未通过）
铺 bundle：openspec/workflow/（--dev 整刷）（49 文件，覆盖）
config.yaml：update 保持 config.yaml（schema 已是目标值）
```

阻断原因：PowerShell 直接执行 `openspec --version` 成功，但 `init.py` 的 Windows Python 子进程以裸命令 `openspec` 启动失败；因此版本门没有通过，目标 schema 没有真正切换。该项不是静态配置推断，而是 `init.py` 的实际 stdout。

### 一次性验证 change

创建命令：

```text
openspec new change task4-dogfood-validation-20260731 --schema sdflow-spec-driven --json
```

实际 CLI 结果：

- change 创建成功，绑定 schema=`sdflow-spec-driven`。
- `openspec status --change task4-dogfood-validation-20260731 --json` 返回四个 artifact：`proposal` ready；`design` requires `proposal`；`specs` requires `proposal, design`；`tasks` requires `proposal, design, specs`。
- `openspec instructions specs --change task4-dogfood-validation-20260731 --json` 返回 dependencies 对象列表，包含 `proposal`、`design`，每项含 `id/done/path/description`。
- `openspec instructions tasks --change task4-dogfood-validation-20260731 --json` 返回 dependencies 对象列表，包含 `proposal`、`design`、`specs`，每项含 `id/done/path/description`。
- 载荷同时包含配对的 `sdflow:delegation` 标记和 `resolvedOutputPath`，证明 CLI 返回的是新 schema 的真实载荷。
- 验证后已删除该临时目录；`Test-Path openspec/changes/task4-dogfood-validation-20260731` 为 `False`。

### 切换后对比

再次执行 `openspec status --change align-sdflow-spec-with-openspec-schema --json`：

- 四个 artifact 仍为 `done`，状态未变化。
- 但 `schemaName` 仍为 `spec-driven`，不是目标 `sdflow-spec-driven`；因此只能证明内置 schema 下的状态零回归，不能宣称完成目标 schema 切换后的零回归。

## 回归测试

```text
python3 -m pytest sdflow-init/tests/test_init.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py -q
58 passed, 1 skipped in 1.94s

openspec validate align-sdflow-spec-with-openspec-schema --strict
Change 'align-sdflow-spec-with-openspec-schema' is valid

git diff --check
通过（仅有 CRLF→LF 提示）
```

## 结论与恢复步骤

Task 4 暂不能标记为 DONE：目标 schema 切换被 Windows 子进程无法解析裸 `openspec` 命令阻断。下一步应让 `sdflow-init/scripts/init.py` 的 CLI 调用在 Windows 解析到实际 `openspec.cmd`（或等价可执行入口），然后重新运行：

```text
python3 sdflow-init/scripts/init.py update --dev --root .
```

随后重跑本报告中的切换前/后 status 对比、一次性 change 载荷验证与回归测试。当前未修改该生产问题，以保持 Task 4 仅做验证的范围。
