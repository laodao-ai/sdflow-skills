# impl-report — Task 3: skill 合并（SKILL.md 合一 + 骑墙规则 + 删旧目录）

R-ID: SC-R1, R7 · tasks.md 组 3（3.1/3.2/3.4/3.5；3.3 tests 迁移 = T2 已做）

## 做了什么

### 1. SKILL.md 合一（3.1）
- 幸存者 `sdflow-issues/SKILL.md` 承载合并结果，覆盖**两池记录 + 跨池管理**，470 行（design 目标 450–550 ✅）。
- frontmatter `description` 聚合三触发面：① 记 bug（缺陷）② 记 todo/优化想法（非缺陷）③ 跨池 reindex/batch/sweep，保留 sdflow-issues 既有的 done-sweep 自动调用叙述。单一触发面 `/sdflow-issues`。
- **去重的逐字重复正文**：buglist/todolist 两份 SKILL.md 正文有 189 行 ≈62% 逐字相同（design.md §Context 第 3 层实测 189/61.6%）——合并后按 pool 参数化：共有部分（目录结构/三维度 schema/状态机制/命令面/sweep 协议/batches.md grammar/ID 两池唯一/铁律/--root/并发边界）写一次，pool 差异（优先级 vs 类型、状态词表+终态集、每天 vs 每月文件粒度、B/T 前缀）用对照表呈现。无残留逐字重复正文。
- **DOC-1 正文即最终态**：只写最终态叙述，无「原来是两份/三份」考古层。修正了原 sdflow-issues SKILL.md 里已作废的「三脚本各自独立 symlink 为 sibling、issues.py 靠文件位置反查 buglist.py/todolist.py」架构叙述（T2 已把 spawn 改同目录）→ 改为「三脚本同在 `sdflow-issues/scripts/` 下、同目录路径 spawn」。

### 2. 骑墙规则 + 已知代价登记（3.2，AD-6/R7）
- **骑墙判定位置**：merged SKILL.md「🔀 骑墙判定：bug（坏了）还是 todo（没坏但可更好）？」节（约 SKILL.md 第 110–160 行区）。核心判据 =「坏了没」对照表（是否存在偏离预期的可观察故障/错误行为？需不需要根因+修复？）+ 4 组骑墙举例（性能退化 / 日志不够 / 命名重构 / spec-impl 不一致），逐个给 bug↔todo 归属判据。显式说明知道 pool 的调用方走显式入口 `buglist.py add`/`todolist.py add`、不经 NL 路由。
- **已知代价登记位置**：同节「⚠️ 已知代价：误判落错池不可机械恢复」小节——登记误判落错池拿错前缀(B↔T)/粒度/schema/词表、CLI 无 move/reclassify、纠正须手删+重 add 丢 ID 与历史；跨池 move --to-pool 命令显式 defer。

### 3. principles 托管块（3.5）
- merged SKILL.md 保留且仅保留**一份** `sdflow:principles` 托管块（grep 计数 = 1），byte-exact 保留（改动只在块外，未手动重写块内）。
- `python3 hack/sync_principles.py --check` → **exit 0**（`✅ 18 个投放面全部与真相源一致` = 15 SKILL.md + 3 project targets；删俩 SKILL.md 后动态枚举自动从 17 收敛到 15）。

### 4. 删除旧目录（3.4）
- **删前空目录确认**：`sdflow-buglist/scripts/`、`sdflow-buglist/tests/`、`sdflow-todolist/scripts/`、`sdflow-todolist/tests/` 均 `total 0`（T2 已迁走全部脚本+测试到 `sdflow-issues/scripts|tests/`）——无未迁文件，不阻断。
- `git rm -r sdflow-buglist sdflow-todolist` 移除 tracked SKILL.md（各池只剩此一 tracked 文件）。
- **⚠️ 额外一步（必要）**：`git rm -r` 后两目录**物理仍存在**——它们含 untracked 的空 `scripts/`/`tests/` 子目录（git 不跟踪空目录），残留空壳导致 (a) 目录未真正删除、(b) `cleanup_orphans` 的 `[ ! -d "$REPO_DIR/sdflow-buglist" ]` 判 false 令 orphan 清理失效（连带 test_legacy_marker 转红）。∴ 补 `rm -rf sdflow-buglist sdflow-todolist` 清物理空壳（已确认子目录 total 0，安全）。

## 跨票 fold（连带修复，保套件绿）

删目录后有**两处** test 立即转红（均为 hard-reference 已删目录的连带，本地 pytest 照得到，非 T5 的 CI/远端面）：

1. **`sdflow-init/tests/test_setup_sdflow.py`（编排层已裁定，task 5.6）**：
   - `:106` `test_rename_scenario_old_links_cleaned_new_links_made`：断言 setup 建 `sdflow-buglist` 链 → 目录删后 setup 不再建 → 改断言 roster `sdflow-buglist` → `sdflow-issues`；`:108` 新增 `for gone in ["sdflow-buglist","sdflow-todolist"]: assert not (skills/gone).exists()`（orphan 清理正断言）。
   - `TestBrandAndMarkerNarrowing`（`:151` OUR_NAMES）**未动且正确**——`_GONE_NAMES` 由 `(REPO/name/SKILL.md).is_file()` 动态派生，删目录后 sdflow-buglist/todolist 自动落入 GONE 桶，测试自适应断言其 orphan 清理；OUR_NAMES 保留旧名是对的（现为 legacy marker 名，setup.sh `OUR_LEGACY_NAMES` 亦保留，Task 5.10 已满足）。
2. **`sdflow-issues/tests/test_task5_delivery_contract.py::test_delivery_docs_name_operational_boundaries`（`:240`）**：原读 buglist+todolist+issues 三份 SKILL.md 拼接后断言 8 条操作边界短语（Shared Frontmatter Envelope/snapshot lock/重跑原命令/Windows 本地盘/network FS/power-loss/TOCTOU/break-glass）在 adr+context+skills 中在场。三合一后改读**唯一** `sdflow-issues/SKILL.md`；已逐条核验 8 短语在 `adr/0025 + CONTEXT.md + merged SKILL.md` 中全部在场（合并未丢任一短语）。

> 此第 2 处虽非编排层显式点名的 fold，但同属「hard-reference 已删目录、本地 pytest 转红」类连带，为满足「结束前全套件确认绿」的契约必须一并修。

## 验证

- `python3 hack/sync_principles.py --check` → **0**（18 投放面一致）。
- 全套件 `/usr/bin/python3 -m pytest -q`（仓根）→ **2100 passed, 8 skipped, 3 xfailed, 0 failed**（148s）。
  - 8 skipped 含 `test_task2_windows_local_fs_smoke.py`（Windows-only，`skipif sys.platform != win32`）。

## 留给 Task 5 的下游 handoff（本票未动，本地 pytest 照不到或非本票 scope）

以下仍引用旧 skill 目录名/脚本路径/slash，属 AD-5 / tasks 组 5，**本票不动**：

- **CI（5.5）**：`.github/workflows/windows-recorder-smoke.yml` 的 path-trigger（`sdflow-buglist/**`·`sdflow-todolist/**`）+ `:35` 测试调用 `sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py`；连带 `sdflow-issues/tests/test_task2_windows_local_fs_smoke.py:5`（docstring 命令）+ `:119`（`skills/sdflow-buglist` 安装路径，Windows runner 上会失配）+ `test_task5_delivery_contract.py:234`（断言 workflow 仍含旧路径——workflow 改后此断言需同步改）。**这三者当前互相自洽、本地全绿**（workflow 未改 ∧ 断言其未改 ∧ Windows smoke 本地 skip）。
- **ship_gate.py（5.3）**：`sdflow-ship/scripts/ship_gate.py:238,281` prose 注释引用 `sdflow-buglist/scripts/buglist.py::repo_root` 作先例——注释非路径解析，pytest 不红。
- **薄入口脚本 docstring**：`sdflow-issues/scripts/buglist.py:4`、`todolist.py:4` 的「原 sdflow-buglist/todolist skill …」provenance 叙述属 **T2 产物**，本票（Task 3）MUST NOT 动 scripts。
- **测试 docstring/注释**：`test_repo_root_identity_{buglist,todolist,issues}.py`、`test_buglist.py:4`、`test_todolist.py:4`、`test_issues.py:27/1726/1826` 的 sibling 旧路径引用均为 docstring/注释（harmless，cosmetic，T5 机械守卫扫到时按 allowlist/清理处理）。
- **README / CLAUDE / AGENTS / sdflow-init assets / 主 spec delta / 机械引用守卫 / test_sync_principles docstring 17→15**：AD-5 A/B/C/D/E 各项，Task 5.1–5.11。

## 契约遵守
- 未勾 superpowers-plan.md 复选框、未打 `task3-` 完成标签、未改 proposal/design/specs/tasks。
- 未跑 setup.sh 改运行环境（test_setup_sdflow.py 内部在 tmp HOME 跑 setup.sh 是测试自身行为）。
