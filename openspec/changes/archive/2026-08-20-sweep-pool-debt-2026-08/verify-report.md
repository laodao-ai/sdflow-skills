---
ship-gate:
  verify: PASS
  reviewed_sha: 7d805f80981d99b03cc5c54ffcf8f188af59c084
---

# Verify Report · sweep-pool-debt-2026-08

- 日期：2026-08-20
- Change：sweep-pool-debt-2026-08
- 验证者：sdflow verify（anti-false-green，Do-Not-Trust-the-Report）
- HEAD：`7d805f80981d99b03cc5c54ffcf8f188af59c084`
- 聚合套件：`/usr/bin/python3 -m pytest -q` → **2590 passed, 10 skipped, exit 0**（本次在当前 HEAD 亲跑，375.95s）
- 归档面：`openspec validate --archived` → **78 passed, 0 failed**（本次亲跑）

## 结论

**PASS。** 逐条核对代码/测试真实反映 tasks.md 与三份 specs（spec-workflow / archive-validation / impl-orchestration）每条要求，未发现真实核心缺口。两处已知 CHANGED/PARTIAL（task1.9 保留 40-hex、task4.1 SKILL 17,164 字符）均已如实报告、有据，非隐瞒，不判 FAIL。

## 逐需求核对表

| 需求 / 任务 | 代码出处（机验锚点） | 状态 |
|---|---|---|
| 1.1 指纹单一源 + 字节保真 manifest + design 域去 tasks.md | `ship_gate.py:571` `_manifest_bytes_from_entries`、`:596` `fingerprint_entries`、`:625` `DESIGN_WATCHED_NAMES=("proposal.md","design.md")` | ✅ |
| 1.2 `is_stale` 改 HEAD 侧 digest 等值（design+code 两分支）+ 删豁免层 | `ship_gate.py:817-863`（两分支均 `head_digest != sha`，不再取锚作 git ref）；`grep def _normalize_checkbox_lines/_tasks_content_exempt/anchors_in/pick_exclusive` → 全部 NONE；无 `BR-7`/subject 豁免残留 | ✅ |
| 1.3 锚读取 64-hex+manifest 互证 + 校验分层 + 六类→五类 | `ship_gate.py:514-565` `read_reviewed_sha`/互证；`:942` `FIELD_VALIDATORS["reviewed_manifest"]`；test `test_old_format_40_hex_anchor_is_unknown_on_live`（gate_reviewed_sha.py:134） | ✅ |
| 1.4 枚举失败 fail-closed，不折空集 | `ls_tree_map` rc≠0 抛 `GateIndeterminate`（`ship_gate.py:698`）；test `test_ls_tree_read_failure_is_indeterminate_not_fresh`（gate_freshness.py:323，带变异证明） | ✅ |
| 1.5 `anchor_writeback.py`：import ship_gate 复用指纹 + `--set` 原子 + 空域/脏树 fail-loud + `--allow-dirty` | `anchor_writeback.py`（reconfigure:45、import:49、fingerprint_entries:273、脏树守卫 porcelain + C2 非零 fail-loud:184、`--allow-dirty`）；test `test_dirty_watch_set_rejects_write`、`test_allow_dirty_escape_hatch_permits_write`、`test_dirty_guard_fails_loud_when_git_status_returns_nonzero` | ✅ |
| 1.6 测试迁移 + rebase 免疫 + 40-hex 归档 SHIPPED 回归 + 字节保真 round-trip | rebase 免疫（gate_freshness.py:794）；40-hex 归档 SHIPPED（gate_terminal.py:135 `test_archived_legacy_40hex_frontmatter_shipped`）；空壳归档不 SHIPPED（gate_terminal.py:75） | ✅ |
| manifest 编码碰撞抗性（冷审 C1）`\0` 分隔 + 回归 | `_manifest_bytes_from_entries` 用 `b"\0".join`（ship_gate.py:601）；test `test_manifest_no_collision_when_path_contains_newline`（gate_freshness.py:494）+ `test_manifest_record_separator_is_nul_not_newline` | ✅ |
| 1.7 三产出方 SKILL 回写改调 anchor_writeback | grep 命中：`sdflow-spec-review/SKILL.md`(3)、`sdflow-code-review/SKILL.md`(3)、`sdflow-done/SKILL.md`(2) | ✅ |
| 1.8 新 ADR + 0026 superseded-by + grep 收口 | `openspec/adr/0044-content-fingerprint-anchor-...md`；`0026...md:1` `superseded-by`；残留 40 位提及仅为迁移说明句（spec-review SKILL:414）与归档时才 sync 的主 spec（现 reviewed_manifest 计数 0，符合 pre-archive） | ✅ |
| 1.9 票 1 收尾（执行期修正保留 40-hex） | tasks.md 已如实标注 CHANGED（老门读 64-hex 自锁，实测证伪原前提，冷审两轴+跨模型核验） | ⚠️ CHANGED（有据，非 FAIL） |
| 2.1-2.3 归档 tasks.md 如实反映（桶 B/A/C） | `openspec validate --archived` 78 passed 0 failed（结构+完整度全绿） | ✅ |
| 2.4 CI pin 1.9.0 + validate --archived 复用 if 条件 | `mechanical-gates.yml:120` `@1.9.0`、`:136` `openspec validate --archived`、`:135` `if: matrix.os=='ubuntu-latest' && matrix.python=='3.12'`（同泳道）；注释已更新 CLI 1.5.0→1.9.0 | ✅ |
| 2.5 定点破坏自证（恒真锚） | task2-archive-convergence.md:12-14（临时改回 `- [ ]` 确认真红后还原）；证据链偏弱经 Spec 轴标 Minor（流程建议），非缺陷 | ✅（Minor 注明） |
| 3.1 切片偏离审计行被 code-review Step1 消费（三分支） | `sdflow-code-review/SKILL.md:246-260`（输入清单含 planning-decisions.md；无申报降级不中断 / 已申报核对 / 静默偏离 SCOPE-CREEP 上报） | ✅ |
| 4.1 SKILL.md 下沉（目标 16,000） | `sdflow-spec/SKILL.md` = 17,164 字符；红线（resident-contract 全绿 + 18,000 硬上限，余量 836）达成；差额留人拍板 | ⚠️ PARTIAL（有据，非 FAIL） |
| 4.2 resident-contract pytest + 全量复核 | `hack/tests/test_sdflow_spec_resident_contract.py` 存在；全量 pytest 2590 passed | ✅ |
| **实现期聚合覆盖（R-ID: all）** | `impl-reports/task5-verify.md`：单元+集成同套件 `/usr/bin/python3 -m pytest -q` 退出码 0，**两「通过」层同锚 SHA `40585ab`（一致）**，e2e 记「未覆盖」+ 判定依据（本仓无 e2e 层）；语义 = **实现期结束时聚合套件通过**（非最终全量回归）。锚 SHA `40585ab` 为 fix 前，属收尾票定位的设计已知时效缺口；冷层代码审后 fix（commit `192f59a`，8 条修复，cr-fix1.md 记 2590 passed），当前 HEAD `7d805f8` 本次亲跑聚合套件 2590 passed 独立复核 | ✅ |

## 缺口清单

无真实核心缺口。

说明性事项（均非 FAIL）：
- **task1.9**（40-hex 保留）：执行期修正，实测证伪原「重锚 64-hex」前提（运行 checkout 老门读 64-hex 自锁 UNKNOWN(6)），40-hex 在 ship 期与归档后均安全，已如实记录并经冷审两轴+跨模型独立核验。
- **task4.1**（SKILL 17,164 vs 目标 16,000）：红线（resident-contract 全绿 + 18,000 硬上限）达成，余量 836；剩余为 DT-5 不可下沉的 principles 托管块/fail-closed 骨架（通则③不为凑字数砍范围）；差额留人拍板。
- **task5-verify 锚 SHA `40585ab` 为 fix 前**：设计已知时效缺口（收尾票定位），当前 HEAD 亲跑聚合套件 2590 passed 已独立复核。
- **task2.5 定点破坏自证证据链偏弱**：Spec 轴 Minor 流程建议（未来 impl-report 可附临时改动/还原 diff），非本票缺陷。
- **工作树 tasks.md 未提交改动**：仅复选框回填（全部 `[x]`），tasks.md 已移出 design 域监视集（D2），不触失鲜；属 verify 前的正常 reconcile。
