# Task 4 实现报告：dogfood 零回归验证（fix1）

状态：PASS

## 范围

仅执行 Task 4 dogfood 验证；本轮未修改生产代码，未勾选 `tickets.md`，未创建 task checkpoint。一次性验证 change 已创建、读取 CLI 载荷并删除。

## 切换前在途 change 快照

在运行 update 前，仓内唯一在途 change 为 `align-sdflow-spec-with-openspec-schema`。

`openspec status --change align-sdflow-spec-with-openspec-schema --json` 返回：

| artifact | status | requires |
|---|---|---|
| proposal | done | — |
| specs | done | proposal |
| design | done | proposal |
| tasks | done | specs, design |

切换前 CLI 返回 `schemaName=spec-driven`；这是该既有 change 自身 `.openspec.yaml` 的绑定，不代表项目默认 schema。

## init.py update

命令：

```text
python3 sdflow-init/scripts/init.py update --dev --root .
```

实际关键输出：

```text
版本门：铺设 project-local schema（openspec 1.7.0）
迁移在途 change：补写 0 个（仅 proposal.md 且无 .openspec.yaml）
铺 bundle：openspec/workflow/（--dev 整刷）（54 文件，覆盖）
config.yaml：update 保持 config.yaml（schema 已是目标值）
```

版本门已通过，未再出现旧报告中的 Windows `[WinError 2]` 裸 `openspec` 启动失败。

## 切换后核验

- `openspec/config.yaml` 首行：`schema: sdflow-spec-driven`
- `openspec/schemas/sdflow-spec-driven/schema.yaml` 存在；templates 下的 `design.md`、`proposal.md`、`spec.md`、`tasks.md` 均存在。
- `openspec schema validate sdflow-spec-driven`：通过。
- 在途 change 的逐 artifact 对比：proposal、specs、design、tasks 均由 `done` 保持为 `done`；artifact 路径未变化。
- 该既有 change 的 `schemaName` 仍为 `spec-driven`，与切换前一致，符合其已存在的 schema 绑定。

## 一次性 change CLI 验证

创建命令：

```text
openspec new change task4-dogfood-validation-20260731-fix1 --schema sdflow-spec-driven --json
```

CLI 实际返回 `schema: sdflow-spec-driven`。

`openspec instructions specs --change task4-dogfood-validation-20260731-fix1 --json` 实际返回：

- `schemaName=sdflow-spec-driven`
- `dependencies` 含 `proposal`、`design`
- 载荷含 `sdflow:delegation:start` / `sdflow:delegation:end`
- 返回 `resolvedOutputPath`

`openspec instructions tasks --change task4-dogfood-validation-20260731-fix1 --json` 实际返回：

- `schemaName=sdflow-spec-driven`
- `dependencies` 含 `proposal`、`design`、`specs`
- 载荷含 `sdflow:delegation:start` / `sdflow:delegation:end`
- 返回 `resolvedOutputPath`

临时 change 已删除；最终 `Test-Path openspec/changes/task4-dogfood-validation-20260731-fix1` 为 `False`。

## 回归验证

```text
python3 -m pytest sdflow-init/tests/test_init.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py -q
58 passed, 1 skipped in 21.56s

openspec validate align-sdflow-spec-with-openspec-schema --strict
Change 'align-sdflow-spec-with-openspec-schema' is valid

git diff --check
通过
```

## 结论

Task 4 通过。Windows CLI 版本门已真实通过；目标 project-local schema、bundle、依赖载荷和委派标记均由 CLI 实际输出证实；在途 change 的四个 artifact 状态无回归。
