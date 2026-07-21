# design — dedupe-issues-scripts-shared-layer `[grill-amendment]`

## Context

issues 台账由三个物理脚本承载：`buglist.py`（1814 行）/ `todolist.py`（1788 行）/ `issues.py`（2539 行），共 6141 行。三者的重复分**三层**：

1. **执行逻辑**：bug↔todo 有 **75 个同名 `def`、~85% 剥 docstring 后 AST 等价**（`determinism-guards` 的 TWO_WAY roster；接地镜实测 75/85.3%，`test_mirror_consistency.py` 现役 roster = THREE_WAY 37 + TWO_WAY 24）〔spec-review-amendment：原「77/90%」偏乐观〕。
2. **共享 helper**：`atomic_write`/`repo_root`/`canonical_id`/`recorder_lock`/整套 frontmatter document mechanics **三份都内联**（THREE_WAY roster）——含 `issues.py`。
3. **台账约定（`SKILL.md` 正文）**：`sdflow-buglist`/`sdflow-todolist` 两份 `SKILL.md` 正文有 **189 行（≈62%）**逐字相同〔spec-review-amendment：实测 189/61.6%，原「133/58%」低报实际重复〕。

此前靠「物理多份 + AST 等价守」维持一致——每次改动多写、漂移风险常驻，且第 3 层（`SKILL.md` 正文）根本无守。

这三脚本的边界是增量生长的疤（buglist 先造 → todolist 克隆 → issues 后挂做编排器），不是设计出来的 seam。domain model（`CONTEXT.md`「三维度分家」）早已把台账当**一个概念**：一条债务 item、三正交字段、status 词表按 pool 各异——即「一个东西 + 一个 pool 参数」。

## Goals / Non-Goals

**Goals:**
- 三脚本的**三层重复全消**：执行逻辑 + 共享 helper 收敛为唯一命名 package `sdflow_issues_core`；`SKILL.md` 正文合一。
- CLI 逐命令外部行为等价，现有 **603 测试零回归**。
- 三 skill 合并为一个 `sdflow-issues`，owns 整个 issues 台账。

**Non-Goals:**
- 不改数据模型（三态 / versioned frontmatter）、不改台账文件格式、不改 CLI 命令语法与既有触发短语（只改脚本路径前缀）。
- **不改读取路径行为**（= 后置的 `harden-issues-read-path`）。
- **不做 CLI 子命令树重整**（`issues.py bug add …`）——纯审美收益，将来另开 CLI change。

## 设计图（TG-13 C4 Context+Container · 组件/依赖图）

### C4 — Context（系统 ↔ 外部）

```
   ┌───────────┐   记 bug / 记 todo / 跨池      ┌──────────────────────┐
   │  用户 /    │──── /sdflow-issues ──────────▶│  sdflow-issues       │
   │  编排 skill │   (done sweep 调 reindex)     │  (一个 skill·整台账)  │
   └───────────┘                                └──────────┬───────────┘
                                                           │ 读写
                                                   ┌───────▼────────┐
                                                   │ openspec/issues │
                                                   │ dated md + INDEX│
                                                   │ + batches.md    │
                                                   └────────────────┘
```

### C4 — Container（目标态：一个 skill·单一源）

```
  dev repo / 运行 checkout（整目录随 setup.sh symlink）:
   sdflow-issues/
    ├─ SKILL.md                    ← 一份，覆盖两池 + 跨池，一个触发面
    └─ scripts/
        ├─ sdflow_issues_core/     ← 唯一命名内部 package（THREE_WAY + TWO_WAY 共享逻辑）〔Q1〕
        │    └─ __init__.py        ← 单模块起步（god-module 拆子模块 = R10 显式 defer）
        ├─ buglist.py              ← 薄入口：解析 args → 注入 bug POOL_SPEC → from sdflow_issues_core import
        ├─ todolist.py             ← 薄入口：todo POOL_SPEC → from sdflow_issues_core import
        └─ issues.py               ← 薄入口：跨池 reindex/batch/sweep + 同目录 spawn buglist/todolist
   [三薄入口同目录 package import·唯一命名避 sys.modules["core"] 碰撞·零跨目录 import·零副本·零 sibling 安装]
```

### 组件/依赖图（目标态）

```
      sdflow_issues_core  ── 参数注入 ──▶ POOL_SPEC{ bug | todo }（封闭 schema）
              ▲  ▲  ▲              (月/日·目录·字段·词表·终态集·前缀·scan键·legacy glob)
  同目录 package │  │  │ import
   ┌────────────┘  │  └────────────┐
 buglist.py      todolist.py      issues.py
 (bug POOL_SPEC) (todo POOL_SPEC) (跨池；同目录 spawn buglist/todolist scan --json)
```

## Decisions

### AD-1：三 skill 合一为 `sdflow-issues`，共享逻辑单一物理源（唯一命名内部 package）

见 `adr/0027`。要点：一个 skill 一个触发面（幸存者 `sdflow-issues`，`sdflow-buglist`/`sdflow-todolist` 目录删除，触发并入）；共享逻辑收敛为唯一 `sdflow-issues/scripts/sdflow_issues_core/`；随整目录 symlink 分发，三薄入口同目录 package import——**零跨目录 import、零副本、零 sibling 安装、setup.sh 无需为分发 core 改动**。

**〔spec-review-amendment Q1/R4：唯一命名 package 而非裸 `core.py`〕** 用**唯一命名内部 package** `sdflow_issues_core/`（起步单 `__init__.py`），三薄入口 `from sdflow_issues_core import ...`。**理由**：裸模块名 `core` 共享全局 `sys.modules["core"]`——别处（测试/插件）先加载同名模块时薄入口拿错 `core` 且无 `__file__` 校验（Codex 广审 G4）；唯一命名消该碰撞。**测试加载策略 MUST 声明**：多数测试用 `importlib.util.spec_from_file_location()` 按文件加载、**不设 `sys.path`**（`test_task2_semantic_lock.py:15`/`test_frontmatter_dual_reader.py:17`）——∴ 薄入口顶部 MUST 显式 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 后再 import package（或测试改 package-aware 加载）；二者择一，spec 钉死（SC-R3 Scenario）。

撤销独立分发前提的依据、以及对 `determinism-guards` 架构的正式反转，均见 `adr/0027`。

### AD-2：CLI 保三薄入口，命令语法不动（但**非**「只有路径前缀」）

`sdflow-issues/scripts/` 下保 `buglist.py`/`todolist.py`/`issues.py` 三个薄入口（各自解析 args、注入 pool 的 `POOL_SPEC`、`from sdflow_issues_core import`），**命令语法一字不改**。

**〔spec-review-amendment R8：修正「只有路径前缀」误导〕** 「零回归」**不是**「机械的路径替换」那么简单——除脚本路径前缀外，`issues.py:66-69` 的运行期 sibling-spawn 常量 `SKILLS_ROOT`/`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT`（上两级 join 到 `sdflow-buglist`/`sdflow-todolist`，`reindex`/`sweep` 靠它 `subprocess.run` 真跑子进程 `issues.py:1443/1500-1501`）**MUST 重写为同目录** `os.path.join(SCRIPT_DIR, "buglist.py")`，其承重注释（`issues.py:59-65` 明写「siblings」前提）**MUST 重写**去掉已作废的 sibling 前提（DOC-1）。∴「零回归」= 路径前缀替换 **+ 内部 spawn 常量改同目录 + import 机制改 package**，命令**输入输出**逻辑与断言不动。三薄入口 + 一份 package + 一份 `SKILL.md` 与「一个 skill」完全自洽。

### AD-3：差异经 `POOL_SPEC`（封闭 schema）注入，`core` 无 pool 条件分支

bug↔todo 差异收敛为一张**封闭 schema** 参数表 `POOL_SPEC`，`core` 按它取值。**〔spec-review-amendment R3：封闭 schema + 补漏项维 + 关系守 + 禁任意 callable〕**

| 差异维 | bug | todo | 关系/正确性约束 |
|---|---|---|---|
| 文件粒度 | 日（`file_for_date`/`today_str`） | 月（`file_for_month`/`this_month`） | — |
| 目录 | `buglists_dir` | `todolists_dir` | — |
| **legacy dir glob**〔补〕 | `openspec/buglists/*` | `openspec/todolists/*` | 与目录维成对（`issues.py:245-247`） |
| 特定字段 | `priority` ∈ `PRIORITIES` | `type` ∈ `TYPE_TAGS` | 字段名与枚举成对 |
| 状态词表 | `OPEN/VERIFIED/PROPOSED/IN_PROGRESS/FIXED/WONTFIX/BLOCKED` | `OPEN/PROPOSED/DONE/WONTDO` | — |
| 终态集 | `{FIXED, WONTFIX}` | `{DONE, WONTDO}` | **`terminal_set ⊆ 状态词表`**（hr-tg H2） |
| **ID 前缀 `DEFAULT_PREFIX`**〔补〕 | `"B"` | `"T"` | canonical_id 空间隔离依赖它（领域镜 BE-05.1，`buglist.py:83`） |
| **scan 输出键**〔补〕 | `"bugs"` | `"items"` | 各池 scan JSON envelope 键（`issues.py:1456`） |

**守法从「查 presence」升为「封闭 schema + 关系正确性」**：
- `POOL_SPEC` 定义为**封闭 dataclass/TypedDict**，required 维 = 类型字段全集——**新增维必须改 schema**（堵「作者没想到的差异被硬编码进 core / 塞进 argparse default / 塞进 callable」的后门，对抗A NEW-2）。
- 对可枚举维加**值正确性**断言：`terminal_set ⊆ 状态词表`、`POOL_SPEC` 值与 `RECORDER_POOL_CONFIG` 现值一致（非只 non-None，hr-tg H2 + 对抗B F3）。
- `POOL_SPEC.keys()` **fail-closed 断言 `== {"bug","todo"}`**（额外 key 即红），或令 snapshot/read/sweep 的跨池 consumer roster 从同一 registry 派生（hr-tg H3 registry-consumer 闭包）。

`core` 源码 MUST NOT 出现针对 pool 值（`"bug"`/`"todo"`）的条件分支——差异一律来自 `POOL_SPEC` 取值。**〔Q2 拍板：禁任意 callable〕** 若某深层逻辑证伪「差异全可参数化」，**MUST NOT** 塞进任意 callable 逃生口（那会让 A1 永不失败、把重复从 core 挪进策略函数、不可证伪）；须保留为**命名 + 限定签名的策略钩子**，逐个在本节记为例外 + 说明为何不能数据化 + 对 bug/todo 各跑同一 contract suite，**不默认整体退回多写**。

### AD-4：`determinism-guards` 守法演进（镜像 AST 守退役）

物理只剩一份 `sdflow_issues_core` ⇒ `determinism-guards` 的「三份剥 docstring AST 等价 + THREE_WAY/TWO_WAY roster」requirement **整体退役**（`test_mirror_consistency.py` 删除）。守法改为守新面：

- **无 pool 分支守 —— AST 级、诚实标 best-effort〔R2〕**：`core` 内**无针对 pool 值的条件分支**。守法**MUST NOT** 用字面 `if pool == "bug"` 子串扫描（真实分岔有 `document["pool"]=="bug"` subscript、`expected_pool==` 别名、`"bugs" if pool==...` 三元、`match`、dict-dispatch 五形态，字面扫必漏——CLAUDE.md 基准 5「无界语法禁手搓」+「gate 子串自指坑」复发）。改 **AST 级**：拦 `If`/`IfExp`/`Match`/`Compare` 右操作数 ∈ `{"bug","todo"}` 且左操作数解析到 pool 值（含别名）+ mutation test 证守卫对 `expected_pool=="bug"`、`document["pool"]=="bug"` 反红。**且 spec MUST 诚实声明此扫描是 best-effort 代理、非 fail-closed 充要保证**（基准 5：机械判定须正确 ⇒ 真正的不变量由 AD-3 的 POOL_SPEC 封闭 schema + 无硬编码常量正面保证，扫描只作辅助）。
- **`POOL_SPEC` 封闭 schema 完备 + 关系正确性守**（见 AD-3：缺维/值错/额外 pool key 即红）。
- **薄入口 thinness 同一性守〔R9〕**：三薄入口 MUST NOT shadow `core` helper。守法断言 THREE_WAY/TWO_WAY 名单每个 helper 从薄入口 `getattr` 解析的对象 `__module__ == 'sdflow_issues_core'`（复用旧 mirror roster，把「等价守」转「同一性守」，成本极低）。删「大幅归零」这类不可判词，换成上述可 fail 断言。

**〔spec-review-amendment R6：golden 诚实降级〕** `issues.py` direct rename snapshot 与 recorder `scan --json` 的 golden 合一后是**同源两 code-path**（跑同一 `core` parser）⇒「一方漏某 rule」结构上不可能（两方同漏）、golden 恒绿（自比自己 = tautology）。∴ 该 golden **不再是 rule-omission 守**——降级为「同源两 code-path 的接线正确性（envelope 组装/字段投影）守」。若要真 rule-完整性守，须 **core-parse vs 外部 golden fixture**（外部锚，非 core 自比 core）。spec 的 Scenario MUST 删「任一方漏 rule → 失败」的宣称（该能力已由「core 是 rule 单一源」结构事实取代）。

本 change 携带 `determinism-guards` 的 **MODIFIED delta**（见 specs/）。其 `config.yaml` 结构 lint / `batches.md` grammar lint / scan-envelope fail-closed 校验三条 requirement 与本合并无关，**不动**（领域镜实测 `validate_scan_envelope` 合一后仍 fail-closed）。

### AD-5：下游托管引用同步（合并的必然连带，fail-closed）

合并 3→1 后，凡引用 `sdflow-buglist`/`sdflow-todolist` **目录名 / 脚本路径 / slash 触发名**的活跃托管点 **MUST 同步更新**，否则合并后调用断裂/CI 打红/主 spec 留死路径（fail-closed，非可选）。**〔spec-review-amendment R1：原清单不全，补全 + 加机械守卫 + 去 overclaim〕**

**A. 路径/名称引用（机械替换或语义重写）**：
- `README.md` skills 列表、`CLAUDE.md`/`AGENTS.md` 配套 skill 表 + 数据类 skill 名单。
- `sdflow-init/assets/{snippets/claude-section.md, workflow/workflow.md}`（下游铺设面，改后 `sdflow-init update` 推）。
- `sdflow-done/SKILL.md:207-211`——**语义块**（描述整个 sibling-独立分发架构，正是被反转的东西），需**语义重写**非路径替换。
- `sdflow-ship`(**仅** `ship_gate.py`)——路径引用在 `ship_gate.py`（repo_root 先例 + todolist T189，`:238/281/288/111`）。
- `sdflow-retro/SKILL.md:107-108`、`sdflow-init/SKILL.md:138`——**prose 引用已删的 slash `/sdflow-buglist`·`/sdflow-todolist`**〔补：原清单漏〕；`sdflow-implement/SKILL.md:378` 是 **skill-名 doc-pointer**（非 slash，指向 sdflow-todolist 文档 → 改指 sdflow-issues）、其 `:375/377` 的「defer 进 buglist/todolist 池」属池概念**不改**〔窄复核 F3 分范畴〕。
- `issues.py:66-69` 的 `SKILLS_ROOT`/`BUGLIST_SCRIPT`/`TODOLIST_SCRIPT` sibling-spawn 常量改同目录（见 AD-2）〔补〕。

**B. CI + 测试（本地 pytest 照不到，须显式枚举，非只靠 5.5 sweep）**〔补：原清单漏〕：
- `.github/workflows/windows-recorder-smoke.yml`：`paths:` 的 `sdflow-buglist/**`·`sdflow-todolist/**` glob（`:8-9,16-17`）+ `:35` 的 `py -m pytest sdflow-buglist/tests/test_task2_windows_local_fs_smoke.py` 调用（该测试文件 3.2 迁到 `sdflow-issues/tests/`）——不改则**下次 Windows runner hard-fail**，且改幸存 skill 即触发（`:18` 含 `sdflow-issues/**`）。
- `sdflow-init/tests/test_setup_sdflow.py:97,106,151`：端到端安装测试断言 setup 后 `sdflow-buglist` 建链——目录删后须改断言为 `sdflow-issues`。

**C. 主 spec（须带 MODIFIED delta，非 grep 替换）**〔补：原清单漏〕：
- `recorder-root-resolution/spec.md:5-6,77-78`：三 recorder 路径写死为契约 → **本 change 新增该 capability 的 MODIFIED delta**（路径更新，语义不变）。
- `spec-workflow/spec.md:285,293,297`：`:285` 是活跃 **MUST**（RENAME-MAP 枚举旧 skill 名）+ Scenario → **新增 MODIFIED delta**（skill 已不存在，枚举 + 场景**修订**，非 grep 替换会静默改 requirement）。

**D. 计数**：`hack/tests/test_sync_principles.py` 投放面计数 **17→15（少两个**，删 buglist+todolist 两 skill；`sync_principles.py` 已动态枚举、自动收敛，只 test 的 docstring 常量 `17` 手改 `15`）〔修正原「自动少一个」的自相矛盾〕。

**E. 机械引用守卫（把 A3 从「实现者手 grep 自觉」升级为门）**〔补〕：新增全仓引用守卫 test——除 **allowlist** 外出现旧 skill 目录名/脚本路径/slash 名即 FAIL。allowlist 放行：`openspec/changes/archive/`、历史 `adr/`、issue ledger（`openspec/issues/*`）、`setup.sh` 的 `OUR_LEGACY_NAMES`（**MUST 保留旧名用于 Windows `.laodao-skills` legacy marker orphan 回收**，领域镜 BE-10.3——别当陈旧引用删）、**整个在途活跃 change 目录 `openspec/changes/{active}/**`**（含四件套 + `specs/` 两 delta + 评审产物 `spec-review-report.md`/`gstack-review.md`/`.outside-voice/`——后二者被旧名/脚本路径/`import core` 塞满，**只豁免「四件套」会让守卫在自己 change 的评审报告上假阳、实现期第一次跑就红**，窄复核 F2）、**池目录名引用**（`openspec/issues/buglist/`·`todolist/` 池不合并）。

**⚠️ 去 overclaim**：`sdflow-ship`/`sdflow-code-review` 的 **SKILL.md** 只有「defer 进 buglist/todolist **池**」概念（`sdflow-code-review/SKILL.md:7/101/215/423/427`）——指池目录（**不合并**），**无脚本路径引用、无需改**（接地镜 ⑨ 实测 0 处路径引用；原 AD-5 把两 SKILL.md 列为「路径引用」是 overclaim，删）。全部进 tasks.md。

## AD-6：误判落错池的恢复缺口（Q3·记为已知代价）〔spec-review-amendment R7〕

触发面塌缩后 bug↔todo 分池由「选哪个 skill」改为「模型在 skill 内按坏了没判」。**逃生口**：CLI 仍保**显式 pool 入口**（`buglist.py add`/`todolist.py add`），知道 pool 的调用方走显式入口、不经 NL 路由。**残余缺口**：NL 层骑墙输入（如「性能退化」——todo 的 `type` 恰有「性能优化」）模型可能误判 → item 落错池，拿错前缀（B↔T）/粒度/schema/词表；而 CLI **无 `move`/`reclassify` 命令**（此缺口 pre-merge 也在，非本 change 新引入）→ 纠正须手删+重 add、丢 ID 与历史。

**决策（记为已知代价，非阻断）**：① 合一 `SKILL.md` MUST 给**骑墙输入判定规则**（明确「坏了没」的判据 + 举例，降低 NL 误判率）；② design 显式登记「误判落错池不可机械恢复」为已知代价；③ `move --to-pool` 跨池搬运命令为 **nice-to-have，显式 defer**（换前缀+粒度文件+schema+保 provenance，属将来另开——非本 change 阻断项）。

## AD-7：god module 拆子模块显式 defer（Q4/R10）〔spec-review-amendment〕

`sdflow_issues_core` 起步为单 `__init__.py`；将来按 cohesive 边界拆子模块（recorder/document/locking/ledger/policies）+ `issues` 内部对一 snapshot 调两次 pool view 消掉自调用子进程——**显式 defer**（非本 change 阻断项，同 CLI-子命令树 defer 先例；本 change 目标 = 消三层重复，不含内部再分层 + 子进程→import 重构）。记 todo 占位。

## Risks / Trade-offs

- **[大重构引入行为回归]** → 重构前后 CLI 逐命令行为等价**留存 param 化测试** + **覆盖判据零回归门**（node-id manifest allowlist + 全 subcommand 触达，**非 `≥603` 魔数**——魔数被删 7 mirror 测试证伪，见 A2/AD-4/SC-R3）为硬门；分命令渐进迁移，每步跑对应 tests。
- **[漏改某个下游引用 → 合并后调用断裂/CI 打红/主 spec 死路径]** → AD-5 的引用清单（含 CI/主 spec/测试/prose）是 fail-closed 必改项；**机械引用守卫（allowlist）**把兜底从「手 grep 自觉」升级为门；`test_sync_principles.py` 计数 + 全仓 pytest 暴露漏网。
- **[`import core` 非纯路径替换]** → 唯一命名 package + 薄入口显式 `sys.path.insert` + 测试加载策略钉死（AD-1/R4），消 `sys.modules["core"]` 碰撞 + file-based 测试加载断裂。
- **[守法「看着守实测放行」]** → 无 pool 分支守升 AST 级 + 诚实标 best-effort；POOL_SPEC 封闭 schema + 关系正确性守；golden 诚实降级为接线守；thinness 同一性守（AD-3/AD-4，杀 R2/R3/R6/R9 的假绿）。
- **[误判落错池不可机械恢复]** → 记为已知代价 + SKILL.md 骑墙判定规则；move 命令 defer（AD-6）。
- **[`SKILL.md` 合并后变大]** → 靠 pool 参数表 + 清晰分节压到 ≈450–550 行；一份大文件 loaded once，替代原三份分别 load。
- **[per-pool 启用/禁用粒度丢失]** → config-skills 四态今可单独禁 `sdflow-todolist` 记录，合并后只能整体 toggle `sdflow-issues`；bug/todo 本是一台账，可接受（记为已知 trade-off，非缺陷）。

## Migration Plan

- 纯结构重构 + skill 目录合并，**无数据迁移**（不碰台账文件）。
- **迁移前先冻结 node-id manifest**（零回归门的 allowlist 基线）；渐进：建 `sdflow_issues_core` package 骨架 + 封闭 `POOL_SPEC` schema → 逐命令把 bug/todo 逻辑上移 core（**含 issues.py:1365/677/689 三处现存 pool 分支重写为 POOL_SPEC 取值**）+ 注入 → buglist/todolist 壳化并迁入 `sdflow-issues/scripts/`（`from sdflow_issues_core import` + 顶部 `sys.path.insert`）→ issues.py 迁入 + **sibling-spawn 常量改同目录 + 重写 59-65 注释** → 合并 `SKILL.md`（含骑墙判定规则）→ 删 `sdflow-buglist`/`sdflow-todolist` 目录 → **AD-5 全面下游同步（含 CI/主 spec delta/测试/prose/机械守卫）** → 镜像 AST 守退役 + 新守法（AST 级无分支 + 封闭 schema + 关系 + thinness + golden 降级）→ 全量行为等价（留存 param 测试）+ 覆盖判据零回归。
- 部署 = 合并后随 setup.sh 生效（orphan 清理回收被删的两个旧 symlink；`OUR_LEGACY_NAMES` 保留旧名；数据类 skill 改 scripts → 必跑对应 tests）。
- 回滚 = revert change commit + 重跑 setup.sh（恢复三 skill symlink），无残留数据副作用（三脚本合一前已统一 `sdflow-issues:` frontmatter marker，无数据格式回滚坑）。

## Compliance

- **D-6 架构边界（核心）**：本 change 显式**重评并变更**「独立分发」边界——三 skill 合一、撤销独立分发前提，已由 grill + 设计 HARD-GATE 拍板（见 `adr/0027`），非悄悄改。
- 遵守 `adr/0027`（本 change 的架构决策源）与 `CONTEXT.md`「三维度分家 / 单一源共享 core」——重构不改 item 数据语义。
- **`determinism-guards` 契约演进**：镜像 AST 守退役换为单一源 + AST 级无分支守 + `POOL_SPEC` 封闭 schema/关系守 + thinness 同一性守 + golden 接线守（AD-4）。一致性从「事后拦漂移」升级为「结构上无从漂移」，**但诚实边界**（spec-review R2/R6）：无分支源码扫描是 best-effort 代理（真正的正面保证靠 POOL_SPEC 封闭 schema），golden 降级为接线守、不再宣称抓 rule 遗漏——不 overclaim「机械充要」，不降级实质守护力。
- 遵守 `CLAUDE.md` 基准 4（一个 change 一个完整内聚交付物）——本 change = 「issues 台账统一为一个 skill」一件事；读取路径修复（`harden-issues-read-path`）显式后置、不 fold；god-module 拆子模块 + move 命令（AD-6/AD-7）显式 defer；AD-5 下游引用同步（含 CI/主 spec delta）是合并的**必然连带**（漏改即断裂），属同一交付物、非另一件事。
