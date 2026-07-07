# spec-workflow（delta）

> v2〔spec-review-amendment〕：spec-review 5 源冷审订正——口径、幂等 flag、空 change 守卫、triage 失败检测、非原子收敛。

## ADDED Requirements

### Requirement: issues sweep 原子子命令（机械活脚本化）

`issues.py` SHALL 提供 `sweep --change X` 子命令，把 `sdflow-done` 收尾的 issues 分诊从「模型手跑 4 步 bash 循环」固化为一次**确定性、非原子、fail-closed、可重跑收敛**的操作（roadmap `mechanical-layer-hardening` 阶段 1，兑现 adr/0006「机械 prose 协议 MUST 脚本化」）。

sweep 的所有子步 SHALL 走 subprocess CLI（不直调 cmd_* 函数，避 args-namespace 脆弱性），依次：① **入口守卫**——`args.change` 非空（`strip()` 后非空）且过 `_reject_batch_key_unsafe`（拒 `|`/换行/` — `/首尾空白），**MUST 先于任何写盘**（否则空 change 精确误纳孤儿、含 ` — ` 的 change 污染项后才被拒）；② 子进程 `scan --change X --open-ungrouped --json` 扫 buglist + todolist 两池（`--open-ungrouped` = 源==X ∧ 非终态 ∧ 批次空，单原语，MUST NOT 用 `--status OPEN`——后者只精确匹配 OPEN、漏非终态、不过滤批次空）；③ 逐项子进程 `triage --id {id} --批次 X`（bug 走 buglist.py、todo 走 todolist.py），每项 MUST 查子进程 returncode、非零即中止；④ `issues.py batch add X --if-exists skip`（MUST 带 `--if-exists skip`——默认对已存在 key 是 `_die` 报错，不带则幂等重跑破产）；⑤ `issues.py reindex`。

sweep SHALL 幂等——靠 ① triage 既有幂等（已 PROPOSED / 已终态 no-op）+ ② `batch add --if-exists skip`（已存在 key no-op）+ ③ reindex 确定性重建；sweep 自身无状态、可安全重跑。sweep SHALL 只圈 `源==X` 的项，**空 `--change` MUST 被入口守卫拒绝**（防 `源==""` 误纳源为空的孤儿项）；孤儿项（源="")在合法非空 change 下天然不匹配、不纳入。sweep SHALL fail-closed 且**非原子**——任一子步（scan / 某项 triage / batch add / reindex）非零退出时，sweep 整体 MUST 以非零退出、stderr 报明**失败步 + 失败点位**（第 i 项 / 哪个 pool / 已成功 tag 的 id 列表），MUST NOT 静默继续。sweep 的部分失败 SHALL **重跑收敛**——已 tag 项在重跑时被 `--open-ungrouped` 的「批次空」过滤排除、未 tag 项补做、batch add 补建、reindex 收敛到完成。

`sdflow-done/SKILL.md` §2.1 sweep 子步 SHALL 调 `issues.py sweep --change {本change}` 取代手写 4 步循环，保留「孤儿项不归本 sweep」「显式传 --change 不靠 detect_change 猜」边界声明。

#### Scenario: sweep 用 --open-ungrouped 口径扫全非终态未分批项
- **WHEN** 池中有 `源==X ∧ 批次空` 的项，状态含 OPEN 与 VERIFIED/IN_PROGRESS/BLOCKED（非终态非 OPEN）
- **THEN** sweep MUST 经 `scan --change X --open-ungrouped` 把这些非终态未分批项**全部**纳入 triage（不因 `--status OPEN` 漏掉非 OPEN 的非终态项）；已在别的批次（批次非空）的项 MUST NOT 被 clobber

#### Scenario: 幂等重跑退出码 0（batch add --if-exists skip）
- **WHEN** 对同一 change X 连跑两次 `sweep --change X`
- **THEN** 第二次 SHALL 无副作用（triage no-op、`batch add --if-exists skip` no-op、reindex 幂等）、退出码 0；MUST NOT 因 batch add 遇已存在 key 而 `_die` 非零退出

#### Scenario: 空 change 被入口守卫拒绝（防孤儿误纳入）
- **WHEN** 跑 `sweep --change ""`（或仅空白 / 含 ` — `/`|`/换行的 change）
- **THEN** sweep MUST 在任何写盘前 `_die` 非零退出；孤儿项（源="")MUST NOT 被 triage 进任何批次

#### Scenario: 某项 triage 失败 fail-closed 且重跑收敛
- **WHEN** sweep 逐项 triage 时第 i 项子进程非零退出
- **THEN** sweep MUST 整体非零退出、stderr 报明失败点位（第 i 项/pool/已 tag 的 id）；前 i-1 项已 tag 但 batches.md 未建/INDEX 未刷；重跑同一 sweep SHALL 收敛（已 tag 项被批次空过滤排除、剩余补做）
