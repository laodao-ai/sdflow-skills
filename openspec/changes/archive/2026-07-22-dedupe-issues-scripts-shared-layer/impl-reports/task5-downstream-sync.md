# Task 5 — 下游托管引用同步（AD-5 fail-closed + 机械引用守卫）

R-ID: SC-R4 · 分支 `feat/dedupe-issues-scripts-shared-layer`

前置状态：Task 0–4 已落地（`sdflow-buglist`/`sdflow-todolist` 目录已删除，三薄入口 +
`sdflow_issues_core` 已迁入 `sdflow-issues/scripts/`）。本 Task 只做「合并的必然连带」：
把凡引用旧 skill 目录名/脚本路径/slash 触发名的**活跃托管点**全部同步更新，并新增机械引用守卫。

## 1. 全仓 grep 结果 + 逐引用点「改 / 不改 + 范畴」

全仓扫 `sdflow-buglist` / `sdflow-todolist`（这两个字面覆盖目录名、脚本路径、slash 名——
后者都是前者的子串）。逐文件分范畴判定：

### 改（活跃托管点，已同步）

| 文件 | 位置 | 范畴 | 处理 |
|---|---|---|---|
| `README.md` | skills 列表 3 行 | 名单 3→1 | 合并为一行 `sdflow-issues`（bug+todo 两池） |
| `README.md` | 「三个 recorder」注记 | 名单 | → `sdflow-issues` |
| `README.md` | 曾用名对照表 `buglist-recorder`/`todolist-recorder` 行 | 名称映射 | 右列 → `sdflow-issues`（不再嵌旧 skill 名，否则守卫假阳） |
| `README.md` | Recorder 存储契约段 | 语义 | 「三者共享」→「两池共用」+ 三薄入口共 `sdflow_issues_core` |
| `README.md` | pytest 示例 ×2 | 路径 | `sdflow-issues/tests/` |
| `CLAUDE.md` | pytest 示例 ×2 / 数据类名单 ×2 / slash prose ×1 | 路径+名单+slash | 3→1，slash → `/sdflow-issues` |
| `AGENTS.md` | pytest 示例 / slash prose | 路径+slash | 同上 |
| `sdflow-init/assets/snippets/claude-section.md` | slash prose | slash（下游铺设面） | → `/sdflow-issues`；保 `openspec/issues/buglist\|todolist/` 池目录名 |
| `sdflow-init/assets/workflow/workflow.md` | 脚本分工句 | 名称（下游铺设面） | 「`sdflow-issues` 两池 scan/triage」 |
| `sdflow-init/SKILL.md:138` | slash prose | slash | → `/sdflow-issues` |
| `sdflow-done/SKILL.md:207-213` | sibling 独立分发**语义块** | 语义重写 | 三薄入口同属**一个** skill `sdflow-issues`，整目录一次 symlink，路径块改同目录 |
| `sdflow-implement/SKILL.md:378` | skill-名 doc-pointer | doc-pointer | → `sdflow-issues 的 todo 池 change 字段`（`:375/377` 「defer 进 buglist/todolist 池」= 池概念**不改**） |
| `sdflow-retro/SKILL.md:107-108` | slash prose | slash | → `/sdflow-issues` |
| `sdflow-ship/scripts/ship_gate.py:238,281` | `::repo_root` 先例注释 | 脚本路径 | → `sdflow-issues/scripts/sdflow_issues_core/__init__.py::repo_root`（repo_root 实测已迁 core；删去已失鲜的 `:613-618` 行号断言） |
| `.github/workflows/windows-recorder-smoke.yml` | path-trigger `:8-9,16-17` + 测试调用 `:35` | CI | 删旧 glob（`sdflow-issues/**` 已覆盖）+ 测试路径 → `sdflow-issues/tests/` |
| `hack/tests/test_sync_principles.py` | docstring 常量 `17` ×2 | 计数 | → `15`（少两个；`sync_principles.py` 动态枚举，自动收敛，只 test 常量手改） |
| `sdflow-issues/scripts/{buglist,todolist}.py:4` | 「原 sdflow-X skill」头注 | 名称 | 去旧 skill 名（provenance archaeology，DOC-1） |
| `sdflow-issues/tests/test_{buglist,todolist}.py:4` | Run-with docstring | 路径 | → `sdflow-issues/tests/` |
| `sdflow-issues/tests/test_repo_root_identity_{buglist,todolist,issues}.py` | sibling 三镜像注释 + Run-with | 语义+路径 | 三薄入口经唯一 `sdflow_issues_core` 取同一 repo_root（去「三份内联」旧述） |
| `sdflow-issues/tests/test_issues.py:27,1726,1826` | sibling 探测注释 + 镜像引用 | 语义+名称 | 同目录 co-located；去旧 tests 目录名 |
| `sdflow-issues/tests/test_task2_windows_local_fs_smoke.py:5,119` | Run-with + **安装路径断言** | 路径（`:119` 功能性） | 安装后 skill = `sdflow-issues` |
| `sdflow-issues/tests/test_task5_delivery_contract.py:234` | CI workflow 内容断言 | 断言同步 | 随 `:35` 改指新路径 |

### 不改（allowlist / 池概念 / 主 spec delta 纪律）

| 文件/面 | 范畴 | 理由 |
|---|---|---|
| `setup.sh:26 OUR_LEGACY_NAMES` | legacy marker 名 | **MUST 保留**旧名——Windows `.laodao-skills` legacy marker orphan 回收依赖（已确认在列） |
| `sdflow-init/tests/test_setup_sdflow.py` | marker-compat + orphan | `OUR_NAMES`（`setup.sh` 口径镜像）+ 改名端到端 orphan 场景，同 `OUR_LEGACY_NAMES` 理由须保留；`:108` T3 已 fold 修（断言旧目录**不**建链）——**已验证正确** |
| `openspec/specs/{spec-workflow,recorder-root-resolution}/spec.md` | 主 spec | 本 change 携 MODIFIED delta，主 spec 在 **archive 阶段**同步（delta-at-archive 纪律，tasks 5.7，**非本 sync 任务**） |
| `openspec/adr/**`（0007, 0027） | 历史决策 | 归档式历史记录 MUST NOT 回改 |
| `openspec/changes/archive/**` | 历史归档 | 同上 |
| `openspec/issues/**`（含 `buglist/`·`todolist/` 池目录 + T153/T154/T177/T180 legacy 行） | issue 台账 + 池目录 | 池**不合并**；ledger 历史行是既成记录 |
| `openspec/changes/dedupe-issues-scripts-shared-layer/**` | 在途活跃 change 目录整体 | 四件套 + specs delta + 评审产物（`spec-review-report.md`/`gstack-review.md` 等被旧名/`import core` 塞满） |
| `sdflow-ship`/`sdflow-code-review` SKILL.md「defer 进 buglist/todolist **池**」 | 池概念 | 指池目录（不合并），无脚本路径引用——**去 overclaim 确认：0 处路径引用，无需改** |
| `docs/**`（workflow-map.{md,html}、sdflow-fable5/02-module-reference.md、drafts/…） | 视图/快照文档 | 见 §3 决策 |

### 全仓核销确认

`git ls-files` 逐文件扫（排除上述 allowlist 路径）→ **0 处**残留旧名。命令与结果见 §2 守卫。

## 2. 机械引用守卫（`sdflow-issues/tests/test_downstream_reference_guard.py`，AD-5 E）

把兜底从「手 grep 自觉」升级为门。三个 test：
1. `test_no_legacy_skill_references_outside_allowlist`：`git ls-files`（= 托管点集）逐文件
   `read_bytes()` 子串扫两个旧名字节串，除 allowlist 外命中即 FAIL。
2. `test_guard_does_not_self_match`：实证本文件源码无连续旧名字面（守卫自身不假阳）。
3. `test_allowlist_paths_still_exist`：allowlist exact 路径 + 两池目录仍存在——防 allowlist 因
   改名静默失效放行。

**allowlist 构成**（路径前缀 + exact）：
- 前缀：`openspec/changes/archive/`、`openspec/adr/`、`openspec/issues/`、`openspec/specs/`、
  `openspec/changes/dedupe-issues-scripts-shared-layer/`、`docs/`。
- exact：`setup.sh`、`sdflow-init/tests/test_setup_sdflow.py`。
- 自身：`SELF` basename 显式跳过。

其中 `openspec/specs/`（主 spec，delta-at-archive 纪律）、`sdflow-init/tests/test_setup_sdflow.py`
（OUR_NAMES marker-compat，同 `OUR_LEGACY_NAMES` 理由）、`docs/`（视图快照，见 §3）为设计原始
清单**未显式列出、但按同类理由补入**的合法豁免（面治：诚实边界，非放水）。

**自指规避手法**（CLAUDE.md 基准 5「gate 子串自指坑」）：pattern 用拼接 `"sdflow-" + "buglist"`
构造，令本文件源码无连续旧名字面；`read_bytes` + 字节串子串扫（不解析 markdown 结构——基准 5
「别手搓解析器」）；`read_bytes` 而非 `read_text` 避免 encoding skip 漏掉 mis-encoded 文本文件。

**为什么用 `git ls-files`**：托管点 = 跟踪文件；未跟踪的 scratch/`__pycache__` 非托管点，天然排除。
内容仍从磁盘 `read_bytes`（读工作树，未提交编辑也被扫到）。

## 3. `docs/` 处理决策（allowlist + 后置刷新）

`docs/workflow-map.{md,html}`、`docs/sdflow-fable5/02-module-reference.md`、
`docs/drafts/sdflow-issues-toolchain-defects.md` 仍含旧 skill 名。判定为 **allowlist**（不在本
Task 强改），理由：
1. 设计 AD-5（多轮评审）清单**零** `docs/` 条目，尽管可 grep——信号：docs 非 fail-closed 托管点。
2. docs 自标「**视图文档，非真相源**」并 pin 到特定 git HEAD（`fc1b98b`）——快照性质。
3. AD-5 的 fail-closed 理由是「调用断裂/CI 打红/主 spec 死路径」；docs 不触发任一。
4. 连贯刷新到目标态 = 重述整套 recorder 架构（退役的 `test_mirror_consistency.py`、单一源 core、
   POOL_SPEC、mermaid 拓扑），属**独立文档交付物**（基准 4：一个 change 一件事），半改只满足
   守卫会让 docs 自相矛盾（违 DOC-1）。

**后置**：docs 刷新到 3→1 目标态建议记 todo（未由本 Task 写入 ledger——避免扰动 dogfood 语料
契约测 `test_task5_delivery_contract` 且属 Task 7 记 todo 范畴）。交编排层/Task 7 收口。

## 4. 计数变更 17→15

顶层含 `SKILL.md` 目录实测 15 个（删 `sdflow-buglist`/`sdflow-todolist` 后 = 17−2）。
`sync_principles.py:57-59` 动态枚举，`--check` 自动收敛；仅 `test_sync_principles.py` docstring
两处 `17` 常量手改 `15`。`sync_principles.py --check` = exit 0（`✅ 18 个投放面全部一致`）。

## 5. T3 fold 验证

`sdflow-init/tests/test_setup_sdflow.py`：
- `:108` `for gone in ["sdflow-buglist","sdflow-todolist"]: assert not (skills/gone).exists()`——
  断言旧目录删后**不建链**（orphan 清理）。**正确**，无需重做。
- `:153` `OUR_NAMES` 含旧名——marker-compat 边界，**须保留**（同 `OUR_LEGACY_NAMES`）。
`test_rename_scenario_old_links_cleaned_new_links_made` 端到端跑真 setup.sh 验旧链清零 + 新链建立——绿。

## 6. 全套件输出

```
$ /usr/bin/python3 hack/sync_principles.py --check
[sync_principles] ✅ 18 个投放面全部与真相源一致   exit=0

$ /usr/bin/python3 -m pytest -q
2114 passed, 9 skipped, 3 xfailed in 144.81s
```

含新增机械守卫 3 test、`test_sync_principles` 15 计数、`test_setup_sdflow` T3、
`test_task5_delivery_contract` 新 CI 路径断言，及既有全绿。
