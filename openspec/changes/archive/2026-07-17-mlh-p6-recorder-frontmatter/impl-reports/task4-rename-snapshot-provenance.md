# Task 4 — 单次 snapshot batch rename / provenance / fail-closed reindex 实现报告

状态：DONE

## 交付结论

- `issues.py` 新增 `read_rename_snapshot(root)`：直接 binary read 两池 dated documents，每文件一次 read、一次 `parse_recorder_document`，snapshot 保留 raw bytes、frontmatter span/model、effective items、problems、pool/file/path；rename 不再调用 bug/todo `scan --json`。
- `retag_rename_snapshot()` 在内存更新 canonical/overlay model；pure legacy item 以 overlay promotion 接管，bug legacy block 只在外围增加 canonical marker，历史 table row 与既有 prose bytes 不改。BOM、CRLF、外部 sibling namespace 在 recorder 自有 splice 外逐字节保留；legacy alias（如 `A007`）promotion 后 machine ID canonicalize 为 `A7`。
- `_reindex_core(root, snapshot=...)` 直接消费 retag 后的同一 snapshot 生成 INDEX 并同步 batches，不重新读取两池；独立 `reindex` 仍通过 recorder CLI，且 `_scan_pool` 现由 `validate_scan_envelope()` 严格校验 JSON、必需键/list、item 字段/type/file 与枚举。
- batch rename 改为 registry-first：首次执行严格要求 old 存在、new 不存在且无 new orphan，先原子改 header 并写/替换 machine-owned `重命名自: old`；重试只有 new provenance 精确匹配 old 时放行，全 old、old/new 混合、全 new 均继续补齐 dated/INDEX/batches。
- old/new 双 key、两者皆无、unknown source、provenance 缺失/不匹配、preexisting new orphan 均在写盘前 fail-closed。registry、dated、INDEX、batches 任一阶段失败均 non-zero，诊断含 `stage=` 与可复制的原 `batch rename old new` 恢复命令；恢复测试证明重跑收敛。
- 删除旧 `_retag_items_in_dated_files` legacy row patch 路径；reindex failure 不再 warning-only success。与目标 retag 无关的 legacy nonfatal problems 仍回显 stderr，并保持默认 reindex 成功语义；`--strict` 既有门禁语义不变。

## TDD 证据

- consumer seam：先因 `validate_scan_envelope` 不存在 collection red；最小实现后坏 JSON、缺键、错型、缺 file、枚举漂移与正常 contract 共 `6 passed`。
- direct snapshot seam：先因 `read_rename_snapshot` 不存在 red；实现 direct bytes snapshot/instrumentation 后 `7 passed`，明确 recorder scan subprocess 为零。
- provenance seam：先因 `classify_batch_rename` 不存在 red；完成 first/retry/unknown-source 纯函数矩阵后 `19 passed`。
- retag/reindex seam：先因 `retag_rename_snapshot` 不存在 red；完成 legacy bytes splice 与 `_reindex_core(snapshot=...)` 后 `21 passed`。
- rename cutover seam：旧实现被新测试击中为四次 recorder scan，且 canonical item 未 retag；切换 direct snapshot 后 scan=0、parse=1、provenance/INDEX 全部转绿。
- crash-cut seam：registry/dated/INDEX/batches 四阶段 fault injection 全部先验证 non-zero + stage + 原命令，再解除注入并以同一命令 retry convergence；最终 Task 4 定向 `36 passed`。
- 旧测试按目标态重基线：legacy row 仍含 old batch（frozen bytes），live scan/frontmatter 返回 new batch；原 warning-only reindex 用例改为 non-zero 恢复诊断；非致命 problem fixture 补合法 target bug prose block，没有放宽 parser。

## 验证

- `uv run --with pytest pytest -q sdflow-buglist/tests/test_mirror_consistency.py sdflow-issues/tests/test_task4_rename_snapshot.py -W error` → `43 passed`。
- `uv run --with pytest pytest -q sdflow-buglist/tests/ sdflow-todolist/tests/ sdflow-issues/tests/ -W error` → `381 passed, 1 skipped`；唯一 skip 为既有 Windows local-disk smoke。
- `uv run --with pytest pytest -q --disable-warnings` → `1556 passed, 1 skipped in 71.49s`。
- `python3 -m py_compile sdflow-issues/scripts/issues.py` → PASS。
- `openspec validate mlh-p6-recorder-frontmatter --strict --no-interactive` → valid。
- `git diff --check` → PASS。

## 边界

- batch rename 仍是多文件非事务流程；registry provenance + snapshot lock + 原命令重试提供可恢复收敛，不宣称跨文件原子事务。
- 未修改 `sdflow-init/assets/workflow/`，未勾选 `tasks.md` checkbox，未创建 Task 4 checkpoint。
