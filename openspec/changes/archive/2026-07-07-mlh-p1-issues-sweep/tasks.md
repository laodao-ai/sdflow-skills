# Tasks — mlh-p1-issues-sweep

> roadmap 阶段 1（1.A）。数据类 skill：改 `scripts/` MUST 跑 `pytest sdflow-issues/tests/`。TDD：先写失败测试 → 实现 → 跑绿。
>
> v2〔spec-review-amendment〕：补空 change 守卫 / triage 失败 fail-closed / 部分失败收敛测试；口径 `--open-ungrouped`；全子步 subprocess CLI + `--if-exists skip`。

## 1. `issues.py sweep` 子命令（TDD）

- [x] 1.1 **先写失败测试**：`test_issues.py` 加 `test_sweep_open_ungrouped`——造含 `源==X ∧ 批次空` 的 bug+todo（状态含 OPEN 与 VERIFIED/IN_PROGRESS），跑 `sweep --change X`，断言**全部**非终态未分批项进批次 X（含非 OPEN 的）、`batches.md` 有 PLANNED 条目、`INDEX.md` 刷新；已在别批次的项未被 clobber。跑 → FAIL（无 sweep 子命令）。
- [x] 1.2 **实现 `cmd_sweep(args)` + 注册子命令**：① 入口守卫 `args.change` 非空 + `_reject_batch_key_unsafe`（先于写盘，D5）；② subprocess `scan --change X --open-ungrouped --json`（buglist+todolist，D3）；③ 逐项 subprocess `triage --id --批次 X`，**每项查 returncode 非零即中止报点位**（D4）；④ subprocess `issues.py batch add X --if-exists skip`（D2）；⑤ subprocess `issues.py reindex`。`main()` 加 `sweep` subparser（`--change` 必填、`--root` 缺省）。跑 1.1 → PASS。
- [x] 1.3 **幂等测试**：`test_sweep_idempotent`——同一 sweep 跑两次，第二次 triage no-op、`batch add --if-exists skip` no-op、reindex 幂等、**退出码 0**、盘面无净变化。跑 → PASS。
- [x] 1.4 **空 change 守卫测试**（致命 B1）：`test_sweep_rejects_empty_change`——`sweep --change ""`（及仅空白 / 含 ` — `/`|`/换行）MUST 在任何写盘前 `_die` 非零退出；断言孤儿项（源="")**未**被 triage 进任何批次、dated 文件无改动。跑 → PASS。
- [x] 1.5 **孤儿排除测试**：`test_sweep_excludes_orphans`——合法非空 change 下，池含源为空孤儿项，`sweep --change X` 后孤儿项未进批次 X。跑 → PASS。
- [x] 1.6 **triage 失败 fail-closed 测试**（B2）：`test_sweep_triage_fail_closed`——注入某项 triage 子进程非零退出（如喂不存在的 id / mock returncode=1），断言 sweep 整体非零退出 + stderr 报明失败点位（第 i 项/pool/已 tag id）。跑 → PASS。
- [x] 1.7 **部分失败重跑收敛测试**（B5/backend-F5）：`test_sweep_rerun_converges`——注入第 k 项失败 → 前 k-1 项已 tag、后续未 tag；修掉注入后重跑 sweep，断言收敛到全部 tag + batches.md 建 + INDEX 刷新（已 tag 项未被重复 triage）。跑 → PASS。
- [x] 1.8 **reindex 致命 fail-closed 测试**：`test_sweep_reindex_fail_closed`——reindex 步致命错误 → sweep 非零退出（对齐 D4「sweep 末步也 fail-closed」，区别于 rename 的 warn-only）。跑 → PASS。
- [x] 1.9 **全套件**：`pytest sdflow-issues/tests/` 全绿。
- [x] 1.10 **checkpoint**：`~/.sdflow/hack/checkpoint-commit.sh task1-sweep "issues.py sweep 原子子命令 + 守卫/幂等/孤儿/fail-closed/收敛测试"`

## 2. SKILL 文档同步

- [x] 2.1 `sdflow-done/SKILL.md` §2.1：手写 4 步循环替换为一行 `python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . sweep --change {change_name}`；保留「孤儿项(源="")不归本 sweep，交 `scan --open-ungrouped` 兜底」+「显式传 --change 不靠 detect_change 猜」（D4）+「调用方 MUST 串行、勿与手动 triage 交叉」（D6）边界声明。
- [x] 2.2 `sdflow-issues/SKILL.md` 命令面「共享」段补 `sweep --change X` 文档（`--open-ungrouped` 口径、`--if-exists skip` 幂等、空 change 守卫、非原子 fail-closed 重跑收敛、D6 串行边界）。
- [x] 2.3 **checkpoint**：`~/.sdflow/hack/checkpoint-commit.sh task2-docsync "sdflow-done §2.1 + sdflow-issues 命令面同步 sweep"`

## 3. 收尾验证

- [x] 3.1 全套件绿（`pytest sdflow-issues/tests/`）；T1-T2 标 DONE。
- [x] 3.2 delta 对码核验：spec-workflow「issues sweep 原子子命令」需求 4 场景（open-ungrouped 口径 / 幂等 exit0 / 空 change 守卫 / triage 失败 fail-closed 重跑收敛）与实现逐条对齐。
- [x] 3.3 语义核验：sweep 对齐 done SKILL 文档边界（非终态∧批次空），比原手循环 `--status OPEN` 更精确（补批次空过滤）——非逐字复刻原命令，proposal「行为保持」按此理解（见 spec-review Q1 拍板）。
