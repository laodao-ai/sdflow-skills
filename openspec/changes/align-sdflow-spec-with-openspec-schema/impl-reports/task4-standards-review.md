# Task 4 Standards 轴复审：dogfood 零回归（fix1）

## 结论

**PASS**

## 审查范围

只读核对以下材料与当前工作树：

- `impl-reports/task4-dogfood-zero-regression-fix1.md`
- 旧报告 `impl-reports/task4-dogfood-zero-regression.md`
- `impl-reports/task4-brief.md`
- `tickets.md` 的 Task 4
- `design.md` 的迁移计划与失败模式
- `tasks.md` 的 Task 4 验收项
- 当前 `git diff`、工作树状态及可复验命令输出

未修改生产代码，未修改 `tickets.md`。

## 核验结果

### 1. 回归测试与 schema 验证

fix1 报告记录的定点回归套件为：

```text
python3 -m pytest sdflow-init/tests/test_init.py sdflow-init/tests/test_init_contract_sync.py hack/tests/test_task3_phase_c_contract.py -q
58 passed, 1 skipped
```

本次复跑结果同样为 `58 passed, 1 skipped`。

另外复跑并通过：

```text
openspec schema validate sdflow-spec-driven
✓ Schema 'sdflow-spec-driven' is valid

openspec validate align-sdflow-spec-with-openspec-schema --strict
Change 'align-sdflow-spec-with-openspec-schema' is valid
```

### 2. 在途 change 零回归

fix1 报告给出了切换前后 CLI `status --json` 的 artifact 状态对比：
`proposal`、`specs`、`design`、`tasks` 均保持 `done`，artifact 路径未改变。

当前复核中，目标 change 的 `.openspec.yaml` 仍将其 schema 固定为既有的
`spec-driven`；因此当前 CLI status 返回 `schemaName=spec-driven` 是既有 change
绑定的正常结果，不构成 config 切换失败或回归。仓库 config 已指向
`sdflow-spec-driven`，本地 schema bundle 存在且可通过 schema validate。

### 3. 一次性验证 change 与 CLI 载荷

fix1 报告记录了一次性 change 的实际 CLI 输出，确认：

- `openspec new change ... --schema sdflow-spec-driven --json` 返回目标 schema；
- `instructions specs --json` 的 dependencies 含 `proposal`、`design`；
- `instructions tasks --json` 的 dependencies 含 `proposal`、`design`、`specs`；
- 载荷含成对委派标记与 `resolvedOutputPath`。

当前工作树中不存在 `openspec/changes/task4-dogfood-validation-20260731-fix1`
或其他 `task4-dogfood-*` 临时 change，清理核验通过。

### 4. diff 与范围核对

`git diff --check` 通过，无空白错误。

当前生产 diff 的相关改动为：

- `sdflow-init/scripts/init.py`：Windows CLI 版本门优先解析 `openspec` / `openspec.cmd`；
- `openspec/config.yaml`：指向 `sdflow-spec-driven`。

未发现 Task 4 验证遗留的临时 change、临时生产文件或对 `tickets.md` 的修改。

## 结论依据

Task 4 要求的迁移前后 artifact 状态保持、project-local schema 下发与配置切换、一次性
change 的真实 CLI 依赖图验证、验证 change 清理，以及回归测试和 diff 检查均有报告证据，
并完成了关键命令复跑。因此 Standards 轴结论为 **PASS**。

## 限定说明

- 本复审未运行全仓 `pytest`；Task 4 fix1 报告的验收套件已通过，未将未运行的全仓结果
  记为绿。
- `task4-brief.md` 与 `tickets.md` 的 checkbox 是实施台账状态，未在本复审中改写；
  本报告只记录独立核验结论。
