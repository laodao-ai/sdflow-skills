# Task 5 Standards Compliance Review

结论：**BLOCKED**

- 固定审包：`impl-reports/task5-review-package.diff`（SHA-256 `8e5b975e3afc8c9958d13b1cf3411a86f4f7c60433c9bbe2f7f5e7b47da9995c`）
- 固定范围：`933066d1e95bcce38231b151fc9fd3d1d99c394d..a8b1bb27c32effd46110c943acadde67005886ab`；审包与 `git diff --binary 933066d..a8b1bb2` byte-identical
- Findings：Critical 0 / Important 4 / Minor 0
- 门禁：存在 Important，Task 5 不可通过 standards review。

## Checklist 适用性

workflow root 为 `/Users/cheneyzhao/.sdflow/workflow`。已检查 `code-checklists/README.md`、`code-review-base.md` 与 `domains/` 注册表；当前领域 delta 仅覆盖 backend、backend-go、embedded、embedded-ml307c、embedded-esp32，本变更是 Python CLI + Markdown/frontmatter 数据管道，**领域清单未覆盖**。本轮依据仓库规范、通用 CR-01~09、`superpowers-plan.md` Global Constraints/Task 5，以及 `tasks.md` 5.1–7.4、`SW-RI-1`、`SW-RI-2`、`SW-RI-3`、`SW-RI-4`、`DG-RI-1` 的目标态审查。

## Findings

### Important I1 — Windows smoke contract 在进入 Windows 专属断言前必然因缺失 delegation chain 失败

- 位置：`sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py:38-43`、`sdflow-buglist/scripts/buglist.py:293-307`
- 证据：测试直接进入 `recorder_lock(..., "reindex")` 后调用 `recorder_child_env("scan", owner.token)`，但没有像复合命令入口那样设置 `_ACTIVE_RECORDER_CHAIN=owner.chain`。`recorder_child_env()` 明确要求 active chain 存在且 `reindex -> scan` 在 delegation graph 中；当前调用稳定抛出 `RecorderLockError: ... delegation denied: <missing> -> scan`，到不了 participant、conflict、replace 或 cleanup 断言。该行为与 OS 无关，已在当前宿主对相同函数序列复现。
- 影响：实现报告把该文件描述为“有 Windows runner 后期望 2 passed”的可执行解锁合同，但现状即使拿到 runner 也会先在通用 delegation setup 失败，不能据此验收 owner→participant。
- 修复：通过真实复合命令入口验证 participant，或在测试中按生产入口设置并恢复 active token/chain 后再构造 child env；增加一个非 Windows 的 delegation-contract 测试覆盖此通用前半段，使 Windows-only 文件只承担 sharing/copy 等平台差异。修复后先在当前 POSIX 宿主跑通通用 delegation 契约，再进入 I2 的 Windows 实机门。

### Important I2 — tasks 7.4 明定的 Windows local-disk actual smoke 尚未执行

- 位置：`openspec/changes/mlh-p6-recorder-frontmatter/tasks.md:57`、`impl-reports/task5-delivery-reconciliation.md:60-76`
- 证据：当前为 `Darwin 25.5.0 arm64`，`docker/podman/wine/pwsh/powershell/QEMU` 均不可用，`gh workflow list --all` 与 `gh run list` 为空；定向 suite 的 `442 passed, 2 skipped` 两项正是 actual-Windows-only tests。报告如实承认未执行，没有伪报 PASS，但 Task 5 acceptance 与 spec 明确把 Windows 本地盘列为必须 smoke 的兼容目标。
- 影响：POSIX contract 与模拟 `PermissionError` 不能证明 Windows sharing、local-drive replace、owned copy/refresh 行为；跨平台兼容证据未闭环。
- 精确解锁条件：先修复 I1；随后让固定 commit 在 actual Windows local-disk runner 可达，并执行 `py -m pytest -q sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py -W error`，必须得到 `2 passed`、无 skip，保存 runner/commit/命令/结果。UNC/network temp path 必须失败；network FS 与完整 power-loss durability继续保持明确 non-goal。

### Important I3 — “升级前 baseline vs 新 dual-reader” corpus 对账是同实现自证，且跳过全部 overlay item

- 位置：`sdflow-buglist/tests/test_task5_delivery_contract.py:62-88`
- 证据：`document["effective_items"]` 与 expected 都来自当前同一个 module；expected 直接调用当前 `_legacy_item_from_row()`，而 dual-reader 的 legacy effective projection 本身也调用这个 helper。若 shared legacy parser 同步回归，两侧会一起变化，测试仍绿。测试还在 `canonical in owned` 时直接 `continue`，因此本次真实 dogfood 成 overlay 的 T85/T66/T67/T146/T2 不参与任何“升级前字段”比较。仓内没有独立的 pre-upgrade snapshot/reference parser artifact；实现报告所称 baseline 实际只是当前 parser 对当前未 shadow rows 的自洽检查。
- 目标态依据：Task 5 acceptance、`tasks.md` 6.1 与 `design.md` compatibility row 要求“升级前 legacy-only parser baseline”对“新 dual-reader”逐 item 相等，同时不得仅以硬编码总数代替动态 corpus。
- 修复：为 pre-dogfood corpus 生成独立、可审计的 legacy-only baseline（或以独立 reference parser 运行同一冻结 corpus），再用当前 dual-reader 比较每个 preexisting item 的全部关键字段；动态枚举 ID/file，不把 item 总数写成长期常量。overlay dogfood 项应明确区分预期 mutation 字段与必须保持的 immutable 字段，并覆盖 T85/T66/T67/T146/T2，不能整体跳过。

### Important I4 — `sdflow-issues/SKILL.md` 仍公开互相矛盾的旧恢复/并发契约

- 位置：`sdflow-issues/SKILL.md:160-162`、`:190-197`；另见 `sdflow-buglist/scripts/buglist.py:1505-1520` 与 todolist 对称输出
- 证据：同一文档一处说调用方要解析“已存在”错误且“脚本本身不做”幂等转换，另一处又正确写明 sweep 固定使用 `batch add --if-exists skip`；它还声称 `batch rename` 的 reindex failure 是 warn-only，并声称 sweep “并发安全未焊接、调用方 MUST 串行”。这些均与当前 target contract 冲突：rename 任一步未收敛必须 non-zero，sweep 顶层持有 exclusive snapshot lock 并通过 participant delegation 覆盖子命令。两池 scan 成功提示仍输出“✓ 表↔块一致”，对 canonical frontmatter-only 文档也把退役表写成现行真相。
- 影响：这是 Task 5 明确要求更新的 SKILL/help/术语交付面；用户按旧文档会建立错误恢复判断，reviewer 也可能把本应阻断的 rename 派生失败误认作成功边界。保守串行本身不会腐蚀数据，但文档否定了已交付的 cooperative concurrency guarantee。
- 修复：统一 `sdflow-issues/SKILL.md` 为当前 `--if-exists skip`、exclusive owner/participant、rename 任一阶段 fail-closed + 原命令重跑契约，删除 warn-only/D6 旧边界；把 bug/todo 人读 scan 成功术语改为 frontmatter/marker/legacy relation 的准确描述，并加文档断言覆盖这些禁止旧措辞，而不只检查几个关键词出现。

## 已核对通过的目标态行为

- 三脚本已删除 `_reject_cell_unsafe` 定义；`issues.py::_reject_batch_line_unsafe` 仅保护 `batches.md` 单行结构，未连带移除注入守卫。
- legacy `split_sections` / `parse_table_rows` / `_legacy_item_from_row` 保留在 dual-read、promotion 与 direct snapshot 路径；未发现 YAML 或跨 recorder Python import。
- mirror consistency、legacy/canonical/overlay installed-path consumer smoke、strict scan envelope 与 partial-install 门禁均有定向测试；已安装路径 smoke 会执行两 producer scan、issues strict reindex、empty sweep，并校验 INDEX/batches。
- README、ADR-0025、CONTEXT 与三 SKILL 已补 Shared Frontmatter Envelope、overlay、semantic ID、snapshot/document lock、rename provenance/retry 及平台/FS/durability 边界；ADR-0025 已升 Accepted。I4 是其中仍未清理的旧段落，不否定其余新增内容。
- dogfood 盘面与实现报告记录 T85/T66/T67/T146/T2 overlay、旧表 bytes 保持和 strict reindex 收敛；I3 针对的是“升级前全 corpus 对账”的独立性，不是当前 scan 结果本身。
- full ordinary `pytest` 的报告结果为 `1616 passed, 2 skipped`；full `pytest -W error` 如实记录 `38 failed, 1578 passed, 2 skipped`，38 项均归于既知 `sdflow-maintain`/`sdflow-architecture` ResourceWarning 基线。`tasks.md` 7.3 要求运行并保存结果而非在本 ticket 内修复这些非 recorder 基线，因此本轮不另立 Task 5 C/I，但最终 verify 必须继续如实保留该非绿状态。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `442 passed, 2 skipped`（两项 actual-Windows-only）
- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-buglist/tests/test_task5_delivery_contract.py -W error` → `12 passed`
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid
- `python3 hack/sync_principles.py --check` → `20` 个投放面一致
- `git diff --check 933066d..a8b1bb2` → PASS
- fixed review package SHA-256 与 `git diff --binary 933066d..a8b1bb2` → MATCH
- Windows contract 通用前半段只读 PoC：`recorder_lock(root, "reindex")` 后直接 `recorder_child_env("scan", owner.token)` → `RecorderLockError ... <missing> -> scan`
- 宿主/runner 探针：`Darwin 25.5.0 arm64`；本机无 Windows 执行层，GitHub Actions 当前无 workflow/run。
