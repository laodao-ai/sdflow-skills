## 1. 录锚：producer + reader 同批（P0）

- [ ] 1.1 三个评审 SKILL 的报告模板各加 `reviewed_sha: <当时 HEAD>`：`sdflow-spec-review`（拍板回写时，与 `design_approved` 同批）、`sdflow-code-review`（出报告时）、`sdflow-done`（verify 报告）
- [ ] 1.2 新增 `read_reviewed_sha(root, rel)`：读 frontmatter；**缺失 / 非 40 位 OID / 对象不存在 → 抛 `GateIndeterminate`**。**MUST NOT** 回退 `report_last_sha`
- [ ] 1.3 `ship_gate.py` 的 frontmatter parser 认 `reviewed_sha` 字段（现只认三个枚举字段、其余静默忽略 ⇒ 不改则新锚永远读不到）
- [ ] 1.4 退役 `report_last_sha`；hand-off 写明存量 active 报告须重审一次

## 2. 直接比内容，退役枚举（P0）

- [ ] 2.1 design 域：固定清单 `proposal.md`/`design.md`/`tasks.md` 逐个 `git show <锚>:<path>` 与 HEAD 比字节；`specs/` 子树经 `ls-tree -r -z` 枚举后同样逐个比
- [ ] 2.2 `tasks.md` 比较前过既有 `_normalize_checkbox_lines`（已是 bytes 口径，直接复用）——**仅 done 期生效**（见 2.7）
- [ ] 2.3 code 域：`git ls-tree <锚>` 与 `git ls-tree HEAD` 各一次（**浅层、不递归**），去掉 `openspec` 条目后比较，不等即失鲜。**MUST NOT 用整树 sha**——实测 done 写 `verify-report.md` 即改变整树 sha ⇒ 正常流程假阳
- [ ] 2.4 **读失败与内容为空显式区分**：每次 `git show` / `ls-tree` 显式判 returncode，任一失败 → `GateIndeterminate`。**MUST NOT** 让两次失败读比较相等
- [ ] 2.5 退役 `frame_touched_paths`、帧遍历、`design_frame_exempt_reason`、BR-7 subject 短路、`_stale_trigger_hint` 与 `StaleResult.trigger`
- [ ] 2.6 `sdflow-ship` SKILL 加语义重锚协议（**仅代码审期**）：撞失鲜 → 读 `reviewed_sha..HEAD` diff 判断 → 若无实质影响则重锚并**在报告写理由**；不重锚即维持失鲜
- [ ] 2.7 **阶段化**：`decide()` 的阶段判定前移到 design 域失鲜检查之前；按阶段选判据——实现期（零豁免）/ 代码审期（可分诊重锚）/ done 期（复选框归一化）。阶段只取决于盘面产物，无循环依赖

## 3. git 调用层（P1）

- [ ] 3.1 `run_git` / `run_git_rc` / `run_git_bytes` 统一捕获 `OSError`（含 `FileNotFoundError`/`PermissionError`）与 `subprocess.TimeoutExpired` → `GateIndeterminate`
- [ ] 3.2 三处统一 `timeout=30`，注释写明判据来源（对齐 `buglist.py::repo_root`：文件系统卡死判定线，非性能预算）
- [ ] 3.3 子进程 env 清理 `GIT_*`（保留 `PATH`/`HOME` 等必要项）；`_GIT_HARDEN` 注释改写为「中和一切能改变判定输入的外部可控态」
- [ ] 3.4 `main()` **整个函数体**捕获 `GateIndeterminate` → `UNKNOWN(6)` + 可读诊断（注意 `--root` 解析处的 `run_git` 在 `decide()` 之前）

## 4. 测试与变异证明

- [ ] 4.1 **监视集保住**：实现期改源码 + 勾 `superpowers-plan.md` 复选框 ⇒ design 域 fresh（经 `is_stale` 入口）
- [ ] 4.1b **阶段化双向用例**：`tasks.md` 仅复选框翻转 ⇒ **done 期 fresh / 非 done 期 stale**；实现期与 done 期**无重锚通路**
- [ ] 4.2 合并把已批准产物换回锚前旧内容 ⇒ 失鲜（该内容不由锚后任何提交引入）
- [ ] 4.3 无关的报告排版提交不移动锚 ⇒ 仍失鲜
- [ ] 4.4 `reviewed_sha` 缺失 / 缩写 SHA / `HEAD` / 坏 SHA / 对象不存在 ⇒ 各判 `UNKNOWN(6)`，且**不回退旧锚**
- [ ] 4.5 读失败（仓损坏 / 对象缺失）⇒ 不判等值
- [ ] 4.6 `GIT_ICASE_PATHSPECS=1` 与 `diff.ignoreSubmodules=all` 环境下，判定结论与干净环境一致
- [ ] 4.7 `OSError` 三个 helper **各自**验证（`main()` 首次调用失败即退出，单一端到端用例只覆盖一个）；`TimeoutExpired` 同理
- [ ] 4.8 code 域两个消费方各有覆盖（`code-review-report` 今天零覆盖；`verify-report` 是现存唯一用例）
- [ ] 4.8b **code 域不得被 `openspec/` 记账打假阳**：done 写 `verify-report.md`、archive 移目录 ⇒ 仍 fresh（**整树 sha 实现会在此变红，这正是本用例要钉死的**）
- [ ] 4.9 **变异证明**：逐条删除 4.1–4.8 各自守护的守卫，确认对应用例变红，结果逐条落 impl-report。**MUST NOT** 以「用例存在且为绿」充当证明
- [ ] 4.10 **删除既有用例须逐条说明**：BR-7 真值表 8 格、帧遍历相关、触发点诊断相关用例随其机制退役，impl-report 逐条写明「删哪条 / 对应哪个退役机制」。**MUST NOT** 静默删测试
- [ ] 4.11 全套件回归（仓根 `pytest`），并在 merge 后于 `main` 上再跑一次

## 5. 文档与收尾

- [ ] 5.1 `ship_gate.py` 头注释重写：判定改为「录锚 + 比内容」、机械保召回语义补精确、指向 `adr/0026`；「已知不覆盖」段登记语义分诊的残余面与 T189 耦合
- [ ] 5.2 hand-off：① 存量报告须重审一次 ② 撞 code 域失鲜先确认不是真漏审 ③ 记 A8 待验（impl-review 修订四件套的分诊频率）

## 测试覆盖图〔TG-18〕

```
                    ┌────────────── is_stale 公共入口 ──────────────┐
                    │                                               │
        scope=design（固定清单比内容）        scope=code（顶层条目去 openspec）
                    │                                               │
    ┌───────────────┼───────────────┐              ┌────────────────┼──────────────┐
  监视集保住     锚前旧内容      读失败≠空          两消费方各覆盖        读失败≠空
  改源码+勾选     换回即失鲜      不判等值        code-review / verify   不判等值
    4.1            4.2            4.5                  4.8               4.5
    │              │              │                    │                 │
    └──────────────┴──────┬───────┴────────────────────┴─────────────────┘
                          │
                   [变异证明 4.9]
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
   录锚层（跨两域）                    git 调用层（跨两域，main 入口）
   排版提交不移锚 4.3                  OSError × 3 helper 各自 4.7
   缺失/非法/不存在 → UNKNOWN 4.4      TimeoutExpired × 3      4.7
   且不回退旧锚                        GIT_* env 无关性        4.6

  覆盖口径：每个叶子 = 一个经公共入口求值的用例 + 一次「删掉守卫即变红」的变异证明。
  MUST NOT 只调内部 helper（fix-design-gate-freshness-proxy 的 rename 用例即此形态，
  在真实洞存在时仍为绿）。
  退役机制的既有用例删除须逐条登记（4.10），MUST NOT 静默删。
```
