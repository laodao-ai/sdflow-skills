# Task 5 Standards Compliance Review — fix 1

结论：**BLOCKED**

- 固定审包：`impl-reports/task5-review-fix1-package.diff`（SHA-256 `8e710530d33de1bef16f600672ca2d00b05f96cf1ee5d6e82deef3a00df6d6ca`）
- 固定范围：`28362448137e94c203bfd181b76c2078f20b3806..c4bb39812dea5f139af98ddb928e58e8b2cb7a5c`；审包与 `git diff --binary 2836244..c4bb398` byte-identical
- Findings：Critical 0 / Important 1 / Minor 0
- 门禁：I1、I3、I4 已闭合；只剩 actual Windows 证据 I2。存在 Important，Task 5 仍不可通过 standards review。

## Checklist 适用性

workflow root 为 `/Users/cheneyzhao/.sdflow/workflow`。已核对 `code-checklists/README.md`、
`code-review-base.md` 与 `domains/` 注册表；当前领域 delta 仅覆盖 backend、backend-go、embedded、
embedded-ml307c、embedded-esp32，本变更是 Python CLI + Markdown/frontmatter 数据管道，**领域清单未覆盖**。
本轮依据仓库规范、通用 CR-01~09、Task 5 acceptance、`tasks.md` 5.1–7.4 与首轮四个 Important 复审。

## 仍阻断的 finding

### Important I2 — actual Windows local-disk smoke 仍未执行

- **位置**：`tasks.md:57`、`.github/workflows/windows-recorder-smoke.yml`、
  `sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py`、
  `impl-reports/task5-delivery-reconciliation-fix1.md:29-34`。
- **证据**：当前宿主仍为 Darwin；定向命令得到 `8 passed, 2 skipped`，两项 skip 正是
  actual-Windows-only。`gh workflow list --all` / `gh run list` 仍无可引用 run，远端也尚无当前 feature
  branch。因此没有 `windows-latest` 本地盘上的 `2 passed` 结果，不能把本地 skip、YAML 静态检查或
  POSIX delegation test 记作 tasks 7.4 PASS。
- **影响**：Windows sharing、local-drive replace、owned copy/refresh 的平台实际行为仍缺验收证据；
  Task 5 acceptance 5 未闭环。
- **最小解锁动作**：授权 push 当前 `feat/mlh-p6-recorder-frontmatter`。新 workflow 的 `push` 没有
  `branches` 限制，`paths` 包含 workflow 自身及全部 recorder 相关目录；仓库 Actions 已启用，当前
  token 具 `workflow` scope，因此首次 feature-branch push 会匹配并在 `windows-latest` 精确执行：

  ```text
  py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error
  ```

  保存 run URL、pushed commit、runner、命令及 `2 passed`（无 skip）结果后，I2 才可关闭。UNC/network
  temp path 必须失败；network FS 与完整 power-loss durability 继续保持明确 non-goal。

## 首轮本地三项复审

### I1 — 已闭合：delegation contract 在 Windows 专属断言前可执行

- Windows smoke 现在按生产复合入口语义临时建立并在 `finally` 恢复 `_ACTIVE_RECORDER_TOKEN` /
  `_ACTIVE_RECORDER_CHAIN`，随后验证 `reindex -> scan` participant chain。
- 独立 POSIX 测试 `test_reindex_to_scan_delegation_contract_runs_before_windows_smoke` 已在当前宿主实际
  通过，证明通用前半段不再以 `<missing> -> scan` 假阻塞；Windows 文件只剩平台差异断言待实机。

### I3 — 已闭合：独立 corpus reference 覆盖 159 rows 与五项 overlay delta

- `_reference_legacy_rows()` 只直接读取冻结 Markdown table，不调用 `parse_table_rows`、
  `_legacy_item_from_row` 或其他 production legacy parser；由当前 dual-reader 作为被测侧逐 item 比较。
- 独立计数为 bug 7 + todo 152 = **159 个 legacy rows**；五个 shadow item
  `T2/T66/T67/T85/T146` 全部进入比较。`T66/T67/T85/T146` 仅允许 `status: PROPOSED -> DONE`，`T2`
  不允许字段 delta，其余关键字段必须与 reference 相等。新增 canonical-only `T153` 不属于升级前 legacy
  corpus，未被误计为迁移 baseline。

### I4 — 已闭合：公开 SKILL 与人读术语已统一到目标态

- `sdflow-issues/SKILL.md` 现在明确 ensure 调用方使用 `--if-exists skip`，rename 任一阶段 fail-closed
  并在修正故障后重跑原命令，sweep 为 exclusive owner + allowlist participant；首轮指出的 warn-only、
  错误文案解析与“并发安全未焊接 / 调用方 MUST 串行”旧合同均已删除。
- bug/todo 成功提示已改为 `frontmatter/marker/legacy 关系一致`，并有禁止退役措辞的文档回归测试。

## Workflow 静态触发核对

- `on.push` 与 `on.pull_request` 均无 branch filter；`workflow_dispatch` 也已声明。
- `push.paths` 包含 `.github/workflows/windows-recorder-smoke.yml`，所以首次推送包含该文件的 feature
  branch 不会因 path filter 漏触发；job 固定 `runs-on: windows-latest`。
- 唯一测试 step 精确运行 actual smoke 文件并带 `-W error`；没有把 POSIX contract 或扩大 suite 当成
  Windows 证据。
- 上述仅证明 workflow 配置具备自动触发路径，**不等于实际 run 已发生**。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_task5_delivery_contract.py sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error` → `8 passed, 2 skipped`（skip 仅 actual Windows）
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `445 passed, 2 skipped`
- 独立 reference projection → `independent_legacy_rows=159`，overlay delta IDs = `T146,T2,T66,T67,T85`
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/windows-recorder-smoke.yml")'` → PASS
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid
- `python3 hack/sync_principles.py --check` → 20 个投放面一致
- `git diff --check 2836244..c4bb398` → PASS
- fixed review package 与 `git diff --binary 2836244..c4bb398` → MATCH
- GitHub 探针：Actions enabled；当前 token scopes 含 `workflow`；远端 feature branch 不存在，workflow/run 尚无实际结果
