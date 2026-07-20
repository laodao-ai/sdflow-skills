## 1. 录锚：producer + reader 同批（P0）

- [ ] 1.1 `parse_ship_gate_frontmatter` 的 `FIELD_ENUMS` 升级为支持「字段 → 校验函数」（现为有限枚举，`val not in FIELD_ENUMS[field]` 容不下「任意 40 位 hex」⇒ 直接加字段会判 `out-of-domain`，等价于新锚永远读不到）
- [ ] 1.2 `reviewed_sha` 的**语法级**校验落在该纯文本函数内：完整 40 位 hex，拒缩写 SHA / `HEAD` / 坏 SHA
- [ ] 1.3 新增 `read_reviewed_sha(root, rel)` 做**语义级**校验：`git cat-file -e <sha>^{commit}` 确认对象存在**且为 commit**（非 blob/tree）；缺失 / 格式非法 / 对象不存在 → 抛 `GateIndeterminate`。**MUST NOT** 回退 `report_last_sha`
- [ ] 1.4 三个 producer 报告模板各加 `reviewed_sha`，**挂在顶层 `ship-gate:` 下作直接子键**，三处逐字对齐 design.md ADR-1 的 YAML 示例
- [ ] 1.5 `sdflow-spec-review` 拍板回写：`design_approved` 与 `reviewed_sha` **MUST 在同一次文件写入中落盘**（不可拆两次 Edit）
- [ ] 1.6 **`sdflow-code-review` 改两段提交时序**〔ADR-7〕：自动修复先单独 commit → `reviewed_sha` 指该 commit → 报告单独 commit。不改则每轮有自动修复的代码审都自锁
- [ ] 1.7 `sdflow-spec-review` 收敛口加流程纪律：拍板前若四件套相对镜子审过的提交有**实质**改动，MUST 先跑窄复核再拍板
- [ ] 1.8 更新人工补锚指引文案：`ship_gate.py:1212` 的 `REFUSE_START` reason + `design.md` 与另两个 SKILL 的同类文案，说明**需补两个字段**并给出「该填哪个 commit」的操作指引
- [ ] 1.9 退役 `report_last_sha`；hand-off 写明存量 active 报告须重审一次

## 2. 比内容 + 求值窗口（P0）

- [ ] 2.1 design 域：对锚与 HEAD **各跑一次** `git ls-tree -r -z <ref> -- proposal.md design.md specs/`，比较 `path → (mode,type,oid)` 映射；映射不等即失鲜（天然覆盖增/删/rename，无需另做双侧并集）
- [ ] 2.2 `tasks.md` 单独取内容比较，比较前过既有 `_normalize_checkbox_lines`（bytes 口径，直接复用）——**常开，不按阶段**
- [ ] 2.3 code 域：`git ls-tree <锚>` 与 `git ls-tree HEAD` 各一次（**浅层、不递归**），去掉 `openspec` 条目后比较。**MUST NOT 用整树 sha**（done 写 verify 报告即假阳）、**MUST NOT 用负向 pathspec**（继承 `GIT_ICASE_PATHSPECS`）
- [ ] 2.4 **读失败与内容为空显式区分**：每次 `ls-tree` / `git show` 显式判 returncode，任一失败 → `GateIndeterminate`。**单侧路径缺失判 stale，MUST NOT 混作读失败**
- [ ] 2.5 **求值窗口 · 阶段判定前移**：把 steps 5.5–7 改造成「算出 tentative verdict 但不立即 `emit`」，或引入 `emit_windowed()` 辅助函数
- [ ] 2.6 **求值窗口 · 三分支各自接入**：`RUN_SOP`(`:1237`) / `RUN_PLAN`(`:1243`) / `CONTINUE_IMPL`(`:1269`) 各自在 emit 前求值 design 失鲜。**MUST NOT 只在 step 7 后加一次检查**（前两个分支会完全逃出，方向 fail-open）
- [ ] 2.7 `emit()` 的 stale 诊断补 `reviewed_sha`（`extra` 字段 + reason 拼出可执行的 `git diff <sha> HEAD -- …`）
- [ ] 2.8 **退役 design 域帧比较整簇**（逐一列名，防悬空引用与孤儿代码）：`frame_touched_paths`、帧遍历、`design_frame_exempt` / `_reason`、`commit_parents`、`_parent_path_status`、`_plain_content_modification`、`_plain_modification_from_raw`、`blob_pair`、`design_watched_subs`、`STALE_CATEGORIES`、BR-7 subject 短路、`_stale_trigger_hint`、`StaleResult.trigger`
- [ ] 2.9 **确认保留复用、MUST NOT 误删**：`DESIGN_WATCHED_NAMES`（`:238`）、`_tasks_content_exempt`（`:576-595`）、`_normalize_checkbox_lines`

## 3. git 调用层（P1）

- [ ] 3.1 三个 helper 统一捕获 `OSError`（含 `FileNotFoundError`/`PermissionError`）与 `subprocess.TimeoutExpired` → `GateIndeterminate`
- [ ] 3.2 三处统一 `timeout=30`，注释写明判据来源（对齐 `buglist.py::repo_root`：文件系统卡死判定线，非性能预算）
- [ ] 3.3 子进程 env 清理走 **denylist**：`os.environ.copy()` 后剔除 `GIT_` 前缀键。**MUST NOT 用 allowlist**（Windows 会漏 `SYSTEMROOT`/`COMSPEC` 致子进程启动失败）
- [ ] 3.4 `_GIT_HARDEN` 注释改写为「中和一切能改变判定输入的外部可控态」（config 面 `-c` + 环境面 denylist）
- [ ] 3.5 `GateIndeterminate` 携带**结构化 payload**（复用 `_fail_closed_on_bad` 的 `(cause, category)` 模式），区分五类原因
- [ ] 3.6 `main()` **整个函数体**捕获 `GateIndeterminate` → `UNKNOWN(6)`，按 payload 拼**各自可行动**的诊断（见 design.md 五行表）。**MUST NOT** 用一句「git 调用失败」打天下

## 4. 测试基座（先行，否则后续用例无法构造）

- [ ] 4.1 **重构共享 fixture 为两段提交模型**：`approved_change` / `tail_ok` / `impl_done` 现为单次 `commit_all` 且 `repo` 无初始提交 ⇒ 报告与其审查对象同属根提交 ⇒ **不存在可填的 `reviewed_sha`**。改为「先提交四件套并读出 sha → 再提交携带该 sha 的报告」
- [ ] 4.2 跑通 fixture 重构的连带影响：`approved_change` 调用点共 **44 处**（`test_gate_impl_progress.py` 24 / `test_gate_freshness.py` 13 / `test_gate_namespace.py` 6 / `test_gate_tail.py` 1），其中 30 处与失鲜主题无关但都穿过 `:1214`。**MUST NOT 指望 4.13 的全套件回归顺带发现**

## 5. 测试与变异证明

- [ ] 5.1 **监视集保住**：实现期改源码 + 勾 `superpowers-plan.md` 复选框 ⇒ design 域 fresh（经 `is_stale` 入口）
- [ ] 5.2 `tasks.md` 纯复选框翻转 ⇒ fresh，**且与阶段无关**（至少两个阶段各验一次）；差异超出复选框 ⇒ stale
- [ ] 5.3a **求值窗口 · `RUN_SOP` 分支**求值且无旁路
- [ ] 5.3b **求值窗口 · `RUN_PLAN` 分支**求值且无旁路
- [ ] 5.3c **求值窗口 · `CONTINUE_IMPL` 分支**求值且无旁路
- [ ] 5.3d **窗口外**：代码审期 / done 期修订四件套 ⇒ **不判 design 失鲜**
- [ ] 5.4 合并把已批准产物换回锚前旧内容 ⇒ 失鲜
- [ ] 5.5 无关的报告排版提交不移动锚 ⇒ 仍失鲜。**变异手段与其余不同源**（新实现无反推逻辑可删，复活 `report_last_sha` 违反 Compliance）⇒ 改为「以旧实现为参照物做对比测试」，impl-report MUST 说明此差异
- [ ] 5.6a `reviewed_sha` **缺失** ⇒ `UNKNOWN(6)`，且不回退旧锚
- [ ] 5.6b `reviewed_sha` **格式非法**（缩写 SHA / `HEAD` / 坏 SHA）⇒ `UNKNOWN(6)`
- [ ] 5.6c `reviewed_sha` **对象不存在或非 commit**（指向 blob/tree）⇒ `UNKNOWN(6)`
- [ ] 5.6d **结论字段在、锚缺失**的中间态 ⇒ `UNKNOWN(6)` 且诊断指明缺的是 `reviewed_sha`
- [ ] 5.7 读失败（仓损坏 / 对象缺失）⇒ 不判等值；**单侧路径缺失 ⇒ 判 stale 而非读失败**
- [ ] 5.8 `GIT_ICASE_PATHSPECS=1` 与 `diff.ignoreSubmodules=all` 环境下判定结论与干净环境一致；**且非 `GIT_*` 环境变量原样透传**（守 denylist 实现）
- [ ] 5.9a `OSError` × `run_git` / `run_git_rc` / `run_git_bytes` **各自**验证（三组）
- [ ] 5.9b `TimeoutExpired` × 三个 helper **各自**验证（三组）
- [ ] 5.9c `main()` 顶层映射 + 五类诊断文案各自可区分
  > 5.9a–c 的触发点可能在 `is_stale` 调用范围之外（如 D3 短路分支），**显式豁免**「必须经 `is_stale` 入口」，改为经 `decide()`/`main()` 求值
- [ ] 5.10 `specs/` 子树 **新增** / **删除** / **rename（内容不变）** 三类各一用例 ⇒ 均判 stale（经公共入口）
- [ ] 5.11a **code 域正例**：代码审后经 merge 提交 resolve 引入源码改动 ⇒ stale
- [ ] 5.11b **code 域正例**：`git mv` 把源码迁进 `openspec/` ⇒ stale
  > 5.11a/b 是 code 域改用顶层条目比较**唯一的正面收益证明**，MUST 各附变异证明
- [ ] 5.12 code 域两个消费方各有覆盖（`code-review-report` 今天零覆盖）；`openspec/` 内记账（写 verify 报告 / archive 移目录）⇒ 仍 fresh
- [ ] 5.13 **code-review 自动修复非空**的端到端用例：两段提交时序下锚不自失鲜（守 ADR-7）
- [ ] 5.14 **变异证明**：逐条删除上述各守卫，确认对应用例变红，结果逐条落 impl-report。**按守卫计数、非按任务号计数**（5.9 一条对应 7 组独立守卫，5.6 对应 4 组）。**MUST NOT** 以「用例存在且为绿」充当证明
- [ ] 5.15a **删除既有用例 · 纯删除清单**：随退役机制消失且无等价替代需求者（`tt_*` BR-7 真值表 8 格、`stale_trigger_category_*`、直调退役 helper 的单元测试等，约 45+ 个），impl-report 逐条登记「删哪条 / 对应哪个退役机制」
- [ ] 5.15b **删除既有用例 · 需重新设计等价用例清单**：承载**仍然生效**安全承诺者（`test_evil_merge_*`、`test_git_mv_*`、`test_merge_frame_*` 等约 10+ 个）MUST 改写成内容比较版本的等价用例，并入本节编号体系。**MUST NOT 静默删除**
- [ ] 5.16 全套件回归（仓根 `pytest`，含 `test_gate_impl_progress.py` / `test_gate_namespace.py` / `test_gate_tail.py`），并在 merge 后于 `main` 上再跑一次

## 6. 文档与收尾

- [ ] 6.1 `ship_gate.py` 头注释重写：判定改为「录锚 + 比内容 + 限定求值窗口」，指向 `adr/0026`；「已知不覆盖」段登记归档终态盲区、窗口右边界间隙、T189 耦合
- [ ] 6.2 `sdflow-ship/SKILL.md` 链序段补一句行为边界：「design 域失鲜仅在 `RUN_SOP`/`RUN_PLAN`/`CONTINUE_IMPL` 窗口内求值，进入代码审后不再检查」（该行为目前只落在源码注释里）
- [ ] 6.3 实现期**再跑一次全历史核验**：确认 A2 的三个确证反例仍是全部（口径 = `checkpoint(<change>:taskN-*)` ∧ 触碰自身 `design.md`/`proposal.md`/`specs/` ∧ 在该 change `design_approved` 之后）。**预先带上已知三例，不要从零发现后临场纠结是否开逃生口**
- [ ] 6.4 hand-off：① 存量报告须重审一次 ② 撞 code 域失鲜先确认不是真漏审 ③ **登记行为收紧**：「实现期直接改设计纠偏」今后被 `REFUSE_START` 拦下，这是有意为之、非 bug ④ 注明 **`sdflow-init update` 对本 change 无效**，须 `/sdflow-upgrade`
- [ ] 6.5 hand-off 附**消费仓只读自查命令**：一次列出「本仓有几个 active change 会因缺 `reviewed_sha` 而 fail-closed」，免得逐个撞门才发现代价

## 测试覆盖图〔TG-18〕

```
                  ┌──────────── is_stale 公共入口 ────────────┐
                  │                                           │
      scope=design（ls-tree 映射比较）      scope=code（顶层条目去 openspec）
                  │                                           │
   ┌──────────┬───┴───┬──────────┐        ┌────────┬──────────┼─────────┐
 监视集保住  勾选豁免  锚前旧内容  specs   两消费方  code 正例  openspec  读失败
 源码+plan   常开与     换回即     增/删/   各覆盖   merge/mv   记账仍    ≠空
 勾选        阶段无关   失鲜       rename                       fresh     单侧缺失
  5.1         5.2       5.4        5.10     5.12   5.11a 5.11b  5.12      5.7
   │           │         │          │         │        │          │        │
   └───────────┴────┬────┴──────────┴─────────┴────────┴──────────┴────────┘
                    │
        ┌───────────┴────────────┬─────────────────────┐
   求值窗口                    录锚层                测试基座
 5.3a RUN_SOP                5.5  排版不移锚      4.1 fixture 两段提交
 5.3b RUN_PLAN               5.6a 缺失            4.2 44 处调用点连带
 5.3c CONTINUE_IMPL          5.6b 格式非法
 5.3d 窗口外不求值            5.6c 非 commit 对象
                             5.6d 结论在锚缺
                             5.13 修复非空不自锁
                    │
        git 调用层（跨两域，main 入口）
   5.9a OSError×3 · 5.9b Timeout×3 · 5.9c main 五类诊断 · 5.8 GIT_* 无关性
                    │
   [变异证明 5.14 覆盖以上全部叶子 · 按守卫计数而非任务号]
   [退役用例 5.15a 纯删除 / 5.15b 重新设计等价用例]
   [全套件回归 5.16 — 含三个受 fixture 重构连带影响的测试文件]

  覆盖口径：每个叶子 = 一个经公共入口求值的用例 + 一次「删掉守卫即变红」的变异证明。
  例外：5.9a–c 的触发点在 is_stale 之外，经 decide()/main() 求值（Compliance 已显式豁免）。
  MUST NOT 只调内部 helper（fix-design-gate-freshness-proxy 的 rename 用例即此形态，
  在真实洞存在时仍为绿）。
```
