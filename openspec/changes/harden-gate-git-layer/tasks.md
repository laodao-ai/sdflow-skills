## 1. 录锚：producer + reader 同批（P0）

- [ ] 1.1 三个评审 SKILL 的报告模板各加 `reviewed_sha: <当时 HEAD>`：`sdflow-spec-review`（拍板回写时与 `design_approved` 同批）、`sdflow-code-review`（出报告时）、`sdflow-done`（verify 报告）
- [ ] 1.2 新增 `read_reviewed_sha(root, rel)`：读 frontmatter；**缺失 / 非 40 位 OID / 对象不存在 → 抛 `GateIndeterminate`**。**MUST NOT** 回退 `report_last_sha`
- [ ] 1.3 frontmatter parser 认 `reviewed_sha` 字段（现只认三个枚举字段、其余静默忽略 ⇒ 不改则新锚永远读不到）
- [ ] 1.4 退役 `report_last_sha`；hand-off 写明存量 active 报告须重审一次

## 2. 比内容 + 求值窗口（P0）

- [ ] 2.1 design 域：固定清单 `proposal.md`/`design.md`/`tasks.md` 逐个 `git show <锚>:<path>` 与 HEAD 比字节；`specs/` 子树经 `ls-tree -r -z` 枚举后同样逐个比
- [ ] 2.2 `tasks.md` 比较前过既有 `_normalize_checkbox_lines`（bytes 口径，直接复用）——**常开，不按阶段**
- [ ] 2.3 code 域：`git ls-tree <锚>` 与 `git ls-tree HEAD` 各一次（**浅层、不递归**），去掉 `openspec` 条目后比较。**MUST NOT 用整树 sha**（done 写 verify 报告即假阳）、**MUST NOT 用负向 pathspec**（继承 `GIT_ICASE_PATHSPECS`）
- [ ] 2.4 **读失败与内容为空显式区分**：每次 `git show` / `ls-tree` 显式判 returncode，任一失败 → `GateIndeterminate`
- [ ] 2.5 **求值窗口**：`decide()` 阶段判定前移；design 域失鲜只在 `RUN_SOP`/`RUN_PLAN`/`CONTINUE_IMPL` 窗口内求值，进入代码审后跳过
- [ ] 2.6 退役 `frame_touched_paths`、帧遍历、`design_frame_exempt_reason`、BR-7 subject 短路、`_stale_trigger_hint` 与 `StaleResult.trigger`

## 3. git 调用层（P1）

- [ ] 3.1 三个 helper 统一捕获 `OSError`（含 `FileNotFoundError`/`PermissionError`）与 `subprocess.TimeoutExpired` → `GateIndeterminate`
- [ ] 3.2 三处统一 `timeout=30`，注释写明判据来源（对齐 `buglist.py::repo_root`：文件系统卡死判定线，非性能预算）
- [ ] 3.3 子进程 env 清理 `GIT_*`（保留 `PATH`/`HOME` 等必要项）；`_GIT_HARDEN` 注释改写为「中和一切能改变判定输入的外部可控态」
- [ ] 3.4 `main()` **整个函数体**捕获 `GateIndeterminate` → `UNKNOWN(6)` + 可读诊断（`--root` 解析处的 `run_git` 在 `decide()` 之前）

## 4. 测试与变异证明

- [ ] 4.1 **监视集保住**：实现期改源码 + 勾 `superpowers-plan.md` 复选框 ⇒ design 域 fresh（经 `is_stale` 入口）
- [ ] 4.2 `tasks.md` 纯复选框翻转 ⇒ fresh，**且与阶段无关**（至少两个阶段各验一次）；差异超出复选框 ⇒ stale
- [ ] 4.3 **求值窗口**：代码审期 / done 期修订四件套 ⇒ **不判 design 失鲜**；实现期同样修订 ⇒ 判失鲜且无旁路
- [ ] 4.4 合并把已批准产物换回锚前旧内容 ⇒ 失鲜
- [ ] 4.5 无关的报告排版提交不移动锚 ⇒ 仍失鲜
- [ ] 4.6 `reviewed_sha` 缺失 / 缩写 SHA / `HEAD` / 坏 SHA / 对象不存在 ⇒ 各判 `UNKNOWN(6)`，且**不回退旧锚**
- [ ] 4.7 读失败（仓损坏 / 对象缺失）⇒ 不判等值
- [ ] 4.8 `GIT_ICASE_PATHSPECS=1` 与 `diff.ignoreSubmodules=all` 环境下，判定结论与干净环境一致
- [ ] 4.9 `OSError` 三个 helper **各自**验证（`main()` 首次调用失败即退出，单一端到端用例只覆盖一个）；`TimeoutExpired` 同理
- [ ] 4.10 code 域两个消费方各有覆盖（`code-review-report` 今天零覆盖）；`openspec/` 内记账（写 verify 报告 / archive 移目录）⇒ 仍 fresh
- [ ] 4.11 **变异证明**：逐条删除 4.1–4.10 各自守护的守卫，确认对应用例变红，结果逐条落 impl-report。**MUST NOT** 以「用例存在且为绿」充当证明
- [ ] 4.12 **删除既有用例须逐条说明**：BR-7 真值表 8 格、帧遍历相关、触发点诊断相关用例随其机制退役，impl-report 写明「删哪条 / 对应哪个退役机制」。**MUST NOT** 静默删测试
- [ ] 4.13 全套件回归（仓根 `pytest`），并在 merge 后于 `main` 上再跑一次

## 5. 文档与收尾

- [ ] 5.1 `ship_gate.py` 头注释重写：判定改为「录锚 + 比内容 + 限定求值窗口」，指向 `adr/0026`；「已知不覆盖」段登记「代码审/done 期设计修订不被记录」与 T189 耦合
- [ ] 5.2 实现期**再跑一次全历史核验**：确认无实现期提交（`checkpoint(<change>:taskN-…)`）改过 design 监视集（A2 的可证伪命题）
- [ ] 5.3 hand-off：① 存量报告须重审一次 ② 撞 code 域失鲜先确认不是真漏审

## 测试覆盖图〔TG-18〕

```
                  ┌──────────── is_stale 公共入口 ────────────┐
                  │                                           │
        scope=design（固定清单比内容）        scope=code（顶层条目去 openspec）
                  │                                           │
   ┌──────────────┼──────────────┐            ┌───────────────┼──────────────┐
 监视集保住   勾选豁免常开   锚前旧内容      两消费方各覆盖   openspec 记账   读失败
 源码+plan勾选  与阶段无关    换回即失鲜      cr / verify      仍 fresh      ≠空
   4.1           4.2           4.4             4.10            4.10          4.7
   │             │             │                │               │            │
   └─────────────┴──────┬──────┴────────────────┴───────────────┴────────────┘
                        │
              ┌─────────┴─────────┐
       求值窗口 4.3           录锚层 4.5 / 4.6
   代码审&done 不求值        排版提交不移锚
   实现期求值且无旁路        缺失/非法 → UNKNOWN 且不回退
                        │
              git 调用层（跨两域，main 入口）
              OSError × 3 helper 各自 4.9 · TimeoutExpired × 3 4.9 · GIT_* 无关性 4.8
                        │
                 [变异证明 4.11 覆盖以上全部叶子]

  覆盖口径：每个叶子 = 一个经公共入口求值的用例 + 一次「删掉守卫即变红」的变异证明。
  MUST NOT 只调内部 helper（fix-design-gate-freshness-proxy 的 rename 用例即此形态，
  在真实洞存在时仍为绿）。退役机制的既有用例删除须逐条登记（4.12）。
```
