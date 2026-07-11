# tasks — harden-hr-tg-anchor-consistency

> 需求 ID：**R1** = hr-tg-intersection-check「命中 TG 集/成员行严格解析 + TG 存在性、畸形 fail-closed」（M3+M-new）· **R2** = spec-workflow「hr-tg 锚定义回灌 declared= canonical（MODIFIED :550）+ anchor_lint 一致性机械化面治 M1/M2/M4/M-new + --trigger-catalog 必需（ADDED）」。
> 内聚边界（design D5，非 tickets 票）：出锚侧（R1 + M-new emit）· 校验侧（R2 + M-new lint）。ship 时按 merit 走 superpowers（~2 片，非 tickets 样本）。

## 1. hr_tg_intersect 出锚侧（R1 / M3 + M-new）

- [x] 1.1 `parse_tg_set`（`:54-62`）删空 cell 静默过滤（`:58`）——仅原始空串表空集；split 出现空/纯空白 cell（前后/连续逗号）→ `EmitError`。〔R1·M3〕
- [x] 1.2 成员抽取改词边界严格 token，畸形（`TG-04x`）→ `EmitError`，不宽松正规化。〔R1·M3〕
- [x] 1.3 **M-new**：加「catalog 全 TG 集」解析（A–G 段表行 `| TG-NN |`，复用成员解析同源口径）；declared/hit 每 TG 须 ∈ 全集，`TG-99`/`TG-1` → `EmitError`。〔R1·M-new〕
- [x] 1.4 pytest（TG-18）：`TG-04,,TG-16`/`,`/前后逗号→非零；`""`→`none`；成员/tg-set `TG-04x`→非零；`TG-99`（shape 合法不存在）→非零。〔R1〕

## 2. anchor_lint 校验侧（R2 / M1+M2+M4+M-new + 回灌 + 必需 catalog）

- [x] 2.0 **回灌 spec-workflow:550**〔Q1〕：主 spec hr-tg 锚定义锚格式 `hit=/evidence=` → `hit=/declared=/evidence=`，declared= canonical、`hit≠none` 时 evidence 非空（delta 已 MODIFIED，实现期确认主 spec 同步）。〔R2〕
- [x] 2.1 `check_hr_tg`（`:163-174`）接 **必需** `--trigger-catalog`；未传 → **非零退出（fail-closed）**，MUST NOT WARN 降级放行。复用出锚侧成员/全集/严格 tg-set 解析。〔R2·零妥协〕
- [x] 2.2 **M1**：`declared=` 硬必填，缺失 → 违规（`missing-field`）。**MUST NOT** 内建永久 grace / `--allow-legacy`。〔R2·M1〕
- [x] 2.3 **M2**：重算 `declared∩HR-TG`、`hit=` 逐元素一致（none⟺空交集），不一致/畸形 → `hit-declared-mismatch`。〔R2·M2〕
- [x] 2.4 **M4**：`hit≠none ⟹ evidence=` 在场非空，缺/空 → `evidence-missing`。〔R2·M4〕
- [x] 2.5 **M-new**（lint 侧）：declared/hit 每 TG ∈ catalog 全集，否则违规。〔R2·M-new〕
- [x] 2.6 诚实边界：改 docstring「字段值任意合法、不校验 CSV 内容」旧表述 → 显式声明「M2 只堵内部一致性、declared 正确性属语义残余、非 tamper-proof」。〔R2·S1〕
- [x] 2.7 **故意测试反转**〔grill B4〕：`test_hr_tg_whatever_declared_anything`（传 catalog 后 `hit="whatever"` 应违规，非旧 `[]`）；删/改 docstring「任意合法」旧断言。〔R2〕
- [x] 2.8 SKILL 接线：`sdflow-code-review`/`sdflow-spec-review` anchor_lint 调用步补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`（**与工具改动同 change 原子落**，防 skew）。〔R2〕
- [x] 2.9 pytest（TG-18）：无 catalog→非零；缺 declared→违规（无 grace）；M2 一致→过、单字段手改→违规、**同改两字段一致但错(`hit="none" declared=""`)→过（诚实边界确认负例）**；M4 缺/空白 evidence→违规；M-new 不存在 TG→违规。〔R2〕

## 3. spec-review 冷层增补〔spec-review-amendment 2026-07-11，5 源冷审 fold〕

> 全为"同片 hr-tg 一致性"的更多确定性维度/回归修复，按 decomposition standard 相关即 fold（非另开）。冷层承重：F1 是热层引入的 spec bug、F2/F3 是热层漏的跨消费者/跨文件一致性。

- [x] 3.1 **F1 sentinel**：M2/边界负例改 `hit="none" declared=""`（非 `"none"`）；实现 + 测 `declared="none"`/`hit=""` 判违规。〔R2〕
- [x] 3.2 **F2 整行严格解析**：hr-tg 锚拒重复键（`hit=`/`declared=`/`evidence=` 两次）/未闭合注释/残留；测跨消费者回归（`hit="none" hit="TG-04"…` 应违规，防 lint 末值胜 vs retro 取首）。〔R2〕
- [x] 3.3 **F3 跨文件一致性 golden 测试**（"非 import"契约的机械兜底，仿 lens-metric 先例）：同一 catalog+tg-set，断言 `hr_tg_intersect` emit 的 hit ⟺ `anchor_lint` 独立重算的 hit **逐元素相等**（含 numeric 同序）。〔R1+R2〕
- [x] 3.4 **F4 fixture retrofit**：`test_hr_tg_intersect.py` 的 `_catalog()` helper 补最小 A–G 表行（≥ 所有测试用到的 TG 号），否则 M-new 接线打崩 10+ 现有正例。〔R1〕
- [x] 3.5 **F5 test_single_source_mutability 重设计**：现用 `TG-99` 当"合法自定义成员"，与 M-new 反例 `TG-99`=不存在语义直撞；改用"A–G 表内存在但不在 HR-TG 8 员集"的 TG 号证"改 HR-TG 段即改行为"（全集不变）。〔R1〕
- [x] 3.6 **F6 check_hr_tg 签名 + _run() 巧合假绿**：更新全部 6 处单参 `check_hr_tg` 调用 + `_run()` helper 补 `--trigger-catalog`；`test_config_bad_block_exit2`/`test_missing_report_error_exit2` 改断言 **stderr 原因码**（非只 `returncode==2`，防 argparse 缺参 exit2 撞码假绿）。〔R2〕
- [x] 3.7 **F7 catalog 内部一致**：加载断言 `HR-TG 成员 ⊆ 全集`，成员含全集外 TG→fail-closed；`test_single_source_mutability` 类 fixture 若造全集外成员改为损坏源负例。〔R1+R2〕
- [x] 3.8 **F8 全集边界钉死**：全集只取 `## 三` 段 `^\s*\|\s*TG-\d+\s*\|` 表行（正文游离 TG 不入）；token 逐个 `fullmatch` 拒残留（`TG-04.0`）；测正文游离 `TG-99` 不入全集 + 残留后缀 fail-closed。〔R1〕
- [x] 3.9 **F9 错误处理契约**：新增校验就地转 violation dict（collect-not-raise），MUST NOT raise EmitError；测畸形 `hit=/declared=` 走结构化 violation、stdout 仍合法 JSON。〔R2〕
- [x] 3.10 **F12 docs 同步**：更新 `docs/workflow-map.md` + `docs/workflow-skills/{sdflow-spec-review,sdflow-code-review}.md` 里写死的 anchor_lint 调用串（补 `--trigger-catalog`），防 ground-truth 文档失真。

## 4. bundle 回灌 + 验收

- [x] 3.1 两工具 + tests 落权威源 `sdflow-init/assets/workflow/tools/(tests/)`；dev `setup.sh` 同步 canonical。
- [x] 3.2 `sdflow-init update` 推下游（不含 tests/，核对脚本本体）。
- [x] 3.3 全套件 pytest 绿；Success Metrics 三项达标核对；主 spec :550 回灌确认。
