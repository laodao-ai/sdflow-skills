# tasks — dedupe-issues-scripts-shared-layer

> 需求 ID 溯源：`SC-R1`~`SC-R4` = `issues-scripts-shared-core` 四需求；`DG-M1`/`DG-M2` = `determinism-guards` 两 MODIFIED 需求；
> `RR-M` = `recorder-root-resolution` MODIFIED；`SW-M` = `spec-workflow` MODIFIED。
> `[spec-review-amendment]` 标记为设计审后补入的任务。
> 复选框在 archive 阶段勾（实现期改 change 四件套会触失鲜门）。

## 0. 迁移前冻结基线〔spec-review-amendment·SC-R3〕

- [x] 0.1 冻结 pre-refactor pytest node-id manifest（零回归门的 allowlist 基线）；标注意图删除项 = `test_mirror_consistency.py` 的 7 个测试 node〔SC-R3〕

## 1. 建共享源骨架 `sdflow_issues_core` package + 封闭 `POOL_SPEC`〔Q1·R3〕

- [x] 1.1 在 `sdflow-issues/scripts/` 建**唯一命名内部 package** `sdflow_issues_core/`（起步单 `__init__.py`，**非**裸 `core.py`——避 `sys.modules["core"]` 碰撞）〔SC-R2〕
- [x] 1.2 定义**封闭 schema** `POOL_SPEC`（dataclass/TypedDict）：required 维含 文件粒度/目录/**legacy dir glob**/特定字段/状态词表/终态集/**`DEFAULT_PREFIX`(B/T)**/**scan 输出键(bugs/items)**——新增维必须改 schema〔SC-R2, DG-M1〕
- [x] 1.3 把 THREE_WAY 共享 helper（`atomic_write`/`repo_root`/`canonical_id`/`recorder_lock`/frontmatter mechanics …）上移 `sdflow_issues_core`，作唯一物理源〔SC-R2, RR-M〕
- [x] 1.4 把 TWO_WAY 的 bug↔todo 镜像逻辑（table/block 解析、doc/ID/定位 helper）上移 `sdflow_issues_core`，差异点改读 `POOL_SPEC`〔SC-R2〕
- [x] 1.5 **重写现存 pool 分支为 POOL_SPEC 取值**：`issues.py:1365`（三元 `"bugs" if pool=="bug"`）、`:677`/`:689`（`expected_pool==` 别名）等——迁进 core 前消除，否则 AST 守拦红〔SC-R2, DG-M1〕

## 2. 三薄入口壳化并迁入 `sdflow-issues/scripts/`〔R4·R8〕

- [x] 2.1 `buglist.py` 壳化：解析 args → 注入 bug `POOL_SPEC` → `from sdflow_issues_core import`；顶部 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`（令 file-based 测试加载可解 package import）；迁入 `sdflow-issues/scripts/`〔SC-R2, SC-R3〕
- [x] 2.2 `todolist.py` 壳化：注入 todo `POOL_SPEC` → `from sdflow_issues_core import` + 同 sys.path 处理；迁入〔SC-R2, SC-R3〕
- [x] 2.3 `issues.py` 迁入（原地即幸存 skill），跨池 reindex/batch/sweep 改用 `from sdflow_issues_core import`；**`SKILLS_ROOT`/`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT`（:66-69）改同目录** `os.path.join(SCRIPT_DIR, "buglist.py")`；**重写 `:59-65` 承重注释**去掉已作废的「siblings」前提（DOC-1）〔SC-R2, SC-R3, R8〕
- [x] 2.4 逐命令核验：`core` 源码无针对 pool 值的条件分支（含 subscript/别名/三元/match/dict-dispatch 形态）〔SC-R2, DG-M1〕

## 3. skill 合并（目录 + SKILL.md + 触发 + 骑墙规则）〔R7〕

- [x] 3.1 合并两份 `SKILL.md` 正文并入 `sdflow-issues/SKILL.md`（一份覆盖两池 + 跨池，去重 189 行重复正文），触发短语聚合到一个触发面〔SC-R1〕
- [x] 3.2 `SKILL.md` **给骑墙输入判定规则**（明确「坏了没」判据 + 举例，降 NL 层误判率）+ 显式登记「误判落错池不可机械恢复」为已知代价〔SC-R1, R7〕
- [x] 3.3 迁移 `sdflow-buglist/tests/` + `sdflow-todolist/tests/` 到 `sdflow-issues/tests/`，路径与 import 改指 `sdflow-issues/scripts/` + package〔SC-R3〕
- [x] 3.4 删除 `sdflow-buglist/`、`sdflow-todolist/` 目录〔SC-R1〕
- [x] 3.5 保留 `sdflow-issues` 的 `sdflow:principles` 托管块一份〔SC-R1〕

## 4. determinism-guards 守法切换〔R2·R6·R9〕

- [x] 4.1 删除 `test_mirror_consistency.py`（三向/两向 AST roster——单一物理源使其无对象）〔DG-M1〕
- [x] 4.2 **无 pool 分支守（AST 级）**：拦 `If`/`IfExp`/`Match`/`Compare` 右操作数 ∈{"bug","todo"} 且左操作数解析到 pool 值（含别名/subscript）；配 mutation test 证守卫对 `expected_pool=="bug"`/`document["pool"]=="bug"` 反红；spec/test **诚实标 best-effort 代理**、非充要〔DG-M1, R2〕
- [x] 4.3 **POOL_SPEC 封闭 schema 完备 + 关系正确性守**：缺 required 维即红；`terminal_set ⊆ 状态词表`、与 `RECORDER_POOL_CONFIG` 一致；`POOL_SPEC.keys()` fail-closed `=={"bug","todo"}` 或 consumer roster registry 派生〔DG-M1, R3〕
- [x] 4.4 **薄入口 thinness 同一性守**：THREE_WAY/TWO_WAY 名单每 helper 从薄入口 `getattr` 解析对象 `__module__ == 'sdflow_issues_core'`（未被 shadow）〔DG-M1, R9〕
- [x] 4.5 **golden 诚实降级**：`direct↔scan` 改为守「同源两 code-path 接线正确」，删「任一方漏 rule→失败」宣称（同源自比 = tautology）〔DG-M1, R6〕
- [x] 4.6 确认 `validate_scan_envelope` fail-closed / `config.yaml` lint / `batches.md` lint 随迁移继续绿、不受影响〔DG-M1, DG-M2〕
- [x] 4.7 核验三薄入口经**同目录 package** `from sdflow_issues_core import` 取共享逻辑，无跨目录 import / sys.path 污染（除入口自身 dir）〔DG-M2, SC-R3〕

## 5. 下游托管引用同步（AD-5·fail-closed·机械守卫兜底）〔R1〕

- [x] 5.1 `README.md` skills 列表 3→1；`CLAUDE.md`/`AGENTS.md` 配套 skill 表与数据类 skill 名单更新〔SC-R4〕
- [x] 5.2 `sdflow-init/assets/{snippets/claude-section.md, workflow/workflow.md}` + `sdflow-init/SKILL.md:138` 的 buglist/todolist 引用更新（下游铺设面须 `sdflow-init update` 推）〔SC-R4〕
- [x] 5.3 `ship_gate.py` 路径引用 + `sdflow-done/SKILL.md:207-211`（语义块重写，非路径替换）改指 `sdflow-issues`〔SC-R4〕
- [x] 5.4 **prose 引用（分范畴）**：`sdflow-retro/SKILL.md:107-108` 的 `/sdflow-buglist`·`/sdflow-todolist` slash prose 更新；`sdflow-implement/SKILL.md:378` 是 **skill-名 doc-pointer**（「坑见 sdflow-todolist 的 `change` 字段说明」，该文档合并后在 sdflow-issues）→ 改指 `sdflow-issues`；**`:375/377` 的「defer 进 buglist/todolist 池」属池概念、不改**〔SC-R4·spec-review-amendment·窄复核 F3〕
- [x] 5.5 **CI**：`.github/workflows/windows-recorder-smoke.yml` 的 path-trigger（`:8-9,16-17`）+ 测试调用（`:35`）改指 `sdflow-issues/tests/`〔SC-R4·spec-review-amendment〕
- [x] 5.6 **安装测试**：`sdflow-init/tests/test_setup_sdflow.py:97,106,151` 断言由 `sdflow-buglist` 建链改为 `sdflow-issues` 建链 + 旧目录 orphan 清理〔SC-R4·spec-review-amendment〕
- [x] 5.7 **主 spec MODIFIED delta**：本 change 已带 `recorder-root-resolution`（RR-M：单一源+路径）+ `spec-workflow`（SW-M：RENAME-MAP 枚举+sibling 场景）两份 delta；archive 时同步进主 spec〔SC-R4·spec-review-amendment〕
- [x] 5.8 `hack/tests/test_sync_principles.py` docstring 常量 `17→15`（**少两个**，`sync_principles.py` 动态枚举自动收敛）〔SC-R4〕
- [x] 5.9 **机械引用守卫 test**：allowlist（archive/历史 adr/issue ledger/`setup.sh` OUR_LEGACY_NAMES/在途 change 四件套/池目录名）外出现旧 skill 目录/脚本路径/slash 名即 FAIL〔SC-R4·spec-review-amendment〕
- [x] 5.10 确认 `setup.sh:26 OUR_LEGACY_NAMES` **保留** `sdflow-buglist`/`sdflow-todolist` 旧名（Windows `.laodao-skills` legacy marker orphan 回收依赖，勿删）〔SC-R4·spec-review-amendment〕
- [x] 5.11 全仓检索确认：除 allowlist 外无活跃托管点仍引用旧 skill 目录/脚本路径/slash；`sdflow-ship`/`sdflow-code-review` 的「defer 进 buglist/todolist **池**」（池目录不合并）**不改**〔SC-R4〕

## 6. 行为等价 + 覆盖判据零回归〔R5·SC-R3〕

- [x] 6.1 CLI 逐命令行为等价**留存 param 化测试**（遍历 argparse 全 subcommand：`add`/`scan --json`/`set-status`/`triage`/`reindex`/`batch add|set-status|rename`/**`next-id`/`sweep`**：stdout JSON + 落盘字节 + 退出码）——**非丢弃的一次性快照**〔SC-R3, R5〕
- [x] 6.2 覆盖判据零回归：冻结 node-id manifest 除 allowlist（`test_mirror_consistency.py` 7 个）外每 node 仍 pass；全 argparse subcommand migration 后逐一有测试触达；无 FAILED、无因重构导致的 skip（**非 `≥603` 魔数**）〔SC-R3, R5〕
- [x] 6.3 跑 `setup.sh`：确认建 `sdflow-issues` 链接、orphan 清理回收 `sdflow-buglist`/`sdflow-todolist` 旧链接〔SC-R1〕

## 7. 显式 defer（记 todo 占位·非本 change 阻断项）〔AD-6·AD-7〕

- [x] 7.1 记 todo：`sdflow_issues_core` god-module 拆 cohesive 子模块（recorder/document/locking/ledger/policies）+ issues 内部对一 snapshot 调两次 pool view 消自调用子进程〔AD-7·R10〕
- [x] 7.2 记 todo：`move --to-pool` 跨池搬运命令（误判落错池的机械恢复路径）〔AD-6·R7〕
