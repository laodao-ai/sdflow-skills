# Task 5 实现报告：移除 legacy 写半场并完成交付对账

## 结论

Task 5 除“实际 Windows runner 执行结果”外已完成。Windows smoke 的可运行 contract 已覆盖
acquire/conflict/participant/replace/cleanup 与 setup copy/refresh，但当前授权范围内没有可达的
Windows runner；本报告不把 macOS 的两项 skip 或模拟执行写成 Windows PASS。

## 实现与文档

- 三脚本删除 `_reject_cell_unsafe` 定义；mirror roster 同步移除。`issues.py` 对 `batches.md` 的窄单行
  验证改名为 `_reject_batch_line_unsafe`，避免与退役的 legacy table writer 混淆。legacy
  `split_sections` / `parse_table_rows` / `_legacy_item_from_row` 只保留 dual-read 与 promotion 用途；
  batch registry 语法未改变。
- 新增 `test_task5_delivery_contract.py`：锁定无 legacy row writer、无 YAML/跨 recorder import、动态
  corpus 逐 item 对账、交付文档关键词与 upgraded installed-path consumer smoke。
- Windows contract 扩为 owner→participant delegation，并真实执行 `setup.sh` 两次验证 Windows copy、
  marker 与刷新后脚本 bytes。
- 更新 README、三 SKILL、ADR-0025、CONTEXT：Shared Frontmatter Envelope、overlay precedence、
  semantic ID、exclusive snapshot/document lock、rename provenance/retry，以及 POSIX/Windows 本地盘、
  network FS、power-loss、TOCTOU、break-glass 边界。ADR-0025 升 `Accepted`。

## 历史 corpus 与 dogfood

- baseline 测试运行时枚举仓内全部 buglist/todolist dated 文档；对每个未被 overlay shadow 的 legacy
  row，逐 item 比较 `module/summary/priority|type/status/time/change/batch` 与 dual-reader effective
  projection。测试不固化动态 item 总数。
- 通过真实命令执行：

  ```bash
  python3 sdflow-todolist/scripts/todolist.py --root . set-status --id T85  --to DONE --evidence mlh-p6-recorder-frontmatter
  python3 sdflow-todolist/scripts/todolist.py --root . set-status --id T66  --to DONE --evidence mlh-p6-recorder-frontmatter
  python3 sdflow-todolist/scripts/todolist.py --root . set-status --id T67  --to DONE --evidence mlh-p6-recorder-frontmatter
  python3 sdflow-todolist/scripts/todolist.py --root . set-status --id T146 --to DONE --evidence mlh-p6-recorder-frontmatter
  python3 sdflow-todolist/scripts/todolist.py --root . set-status --id T2 --to DONE --evidence "mlh-p6-recorder-frontmatter（根治兑现）"
  python3 sdflow-issues/scripts/issues.py --root . reindex --strict
  ```

- 结果：2026-07 todolist 为 `mode=overlay`；T85/T66/T67/T146/T2 的当前 effective status 均为
  `DONE`，T2 保持 DONE 并新增根治兑现历史；旧 legacy 总览 table region 与 Task 5 base
  `933066d` 的对应 bytes 相等。`reindex --strict` exit 0，INDEX 当前为 open 105 / closed 55。
- mechanical-layer-hardening roadmap/task-log、issues batches/index 已回写交付状态；原 provenance
  `change` 与 batch 不被迁移篡改，关联本 change 的兑现证据落在追加历史与交付记录。

## 验证

| 命令 | 结果 |
|---|---|
| `pytest sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error`（经 `uv run --with pytest`） | `442 passed, 2 skipped`；skip 均为 actual-Windows-only contract |
| `pytest sdflow-buglist/tests/test_mirror_consistency.py -W error` | `7 passed` |
| Task 5 delivery contract（dogfood 后重跑） | `5 passed` |
| source grep | 三脚本无 `_reject_cell_unsafe`，无 YAML/跨 recorder import；legacy parser/promotion helper 与独立 batch line guard 保留 |
| full `pytest` | `1616 passed, 2 skipped`，exit 0 |
| full `pytest -W error` | `38 failed, 1578 passed, 2 skipped`：精确保持既知基线，`sdflow-maintain` 37 个 unclosed-file ResourceWarning + `sdflow-architecture` 1 个 subprocess pipe ResourceWarning；无 Task 5 新 failure |
| `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` | valid，exit 0 |
| `git diff --check` | exit 0 |
| `python3 hack/sync_principles.py --check` | 20 个投放面一致 |
| upgraded installed-path consumer smoke | legacy + canonical bug、overlay todo 的 scan JSON、`reindex --strict`、empty sweep、INDEX/batches contract 均通过 |

## 唯一未闭合项：实际 Windows runner

穷尽证据（2026-07-17）：

- 当前宿主 `Darwin arm64`；`docker`、`podman`、`wine`、`pwsh`、`powershell`、QEMU 均不可用。
- `gh` 已认证且有 `repo/workflow` scope，但 `gh workflow list --all` 与 `gh run list` 均为空。
- GitHub API 返回本仓 `actions/runners.total_count=0`、`actions/workflows.total_count=0`。
- ship 契约禁止本阶段自行 push；创建 workflow 并 push 会扩大授权范围，因此未执行。

在有 Windows local-disk runner 且代码可达后，精确命令为：

```powershell
py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error
```

期望 2 passed：第一项覆盖 local-drive acquire/conflict/participant/replace/cleanup，第二项覆盖
`setup.sh` copy/owned-marker/refresh。UNC/network temp path 会主动失败；network FS 与完整 power-loss
durability 保持非承诺。
