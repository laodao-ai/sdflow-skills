# tasks — harden-hr-tg-anchor-consistency

> 需求 ID：**R1** = hr-tg-intersection-check「命中 TG 集/成员行严格解析 + TG 存在性、畸形 fail-closed」（M3+M-new）· **R2** = spec-workflow「hr-tg 锚定义回灌 declared= canonical（MODIFIED :550）+ anchor_lint 一致性机械化面治 M1/M2/M4/M-new + --trigger-catalog 必需（ADDED）」。
> 内聚边界（design D5，非 tickets 票）：出锚侧（R1 + M-new emit）· 校验侧（R2 + M-new lint）。ship 时按 merit 走 superpowers（~2 片，非 tickets 样本）。

## 1. hr_tg_intersect 出锚侧（R1 / M3 + M-new）

- [ ] 1.1 `parse_tg_set`（`:54-62`）删空 cell 静默过滤（`:58`）——仅原始空串表空集；split 出现空/纯空白 cell（前后/连续逗号）→ `EmitError`。〔R1·M3〕
- [ ] 1.2 成员抽取改词边界严格 token，畸形（`TG-04x`）→ `EmitError`，不宽松正规化。〔R1·M3〕
- [ ] 1.3 **M-new**：加「catalog 全 TG 集」解析（A–G 段表行 `| TG-NN |`，复用成员解析同源口径）；declared/hit 每 TG 须 ∈ 全集，`TG-99`/`TG-1` → `EmitError`。〔R1·M-new〕
- [ ] 1.4 pytest（TG-18）：`TG-04,,TG-16`/`,`/前后逗号→非零；`""`→`none`；成员/tg-set `TG-04x`→非零；`TG-99`（shape 合法不存在）→非零。〔R1〕

## 2. anchor_lint 校验侧（R2 / M1+M2+M4+M-new + 回灌 + 必需 catalog）

- [ ] 2.0 **回灌 spec-workflow:550**〔Q1〕：主 spec hr-tg 锚定义锚格式 `hit=/evidence=` → `hit=/declared=/evidence=`，declared= canonical、`hit≠none` 时 evidence 非空（delta 已 MODIFIED，实现期确认主 spec 同步）。〔R2〕
- [ ] 2.1 `check_hr_tg`（`:163-174`）接 **必需** `--trigger-catalog`；未传 → **非零退出（fail-closed）**，MUST NOT WARN 降级放行。复用出锚侧成员/全集/严格 tg-set 解析。〔R2·零妥协〕
- [ ] 2.2 **M1**：`declared=` 硬必填，缺失 → 违规（`missing-field`）。**MUST NOT** 内建永久 grace / `--allow-legacy`。〔R2·M1〕
- [ ] 2.3 **M2**：重算 `declared∩HR-TG`、`hit=` 逐元素一致（none⟺空交集），不一致/畸形 → `hit-declared-mismatch`。〔R2·M2〕
- [ ] 2.4 **M4**：`hit≠none ⟹ evidence=` 在场非空，缺/空 → `evidence-missing`。〔R2·M4〕
- [ ] 2.5 **M-new**（lint 侧）：declared/hit 每 TG ∈ catalog 全集，否则违规。〔R2·M-new〕
- [ ] 2.6 诚实边界：改 docstring「字段值任意合法、不校验 CSV 内容」旧表述 → 显式声明「M2 只堵内部一致性、declared 正确性属语义残余、非 tamper-proof」。〔R2·S1〕
- [ ] 2.7 **故意测试反转**〔grill B4〕：`test_hr_tg_whatever_declared_anything`（传 catalog 后 `hit="whatever"` 应违规，非旧 `[]`）；删/改 docstring「任意合法」旧断言。〔R2〕
- [ ] 2.8 SKILL 接线：`sdflow-code-review`/`sdflow-spec-review` anchor_lint 调用步补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`（**与工具改动同 change 原子落**，防 skew）。〔R2〕
- [ ] 2.9 pytest（TG-18）：无 catalog→非零；缺 declared→违规（无 grace）；M2 一致→过、单字段手改→违规、**同改两字段一致但错→过（诚实边界确认负例）**；M4 缺 evidence→违规；M-new 不存在 TG→违规。〔R2〕

## 3. bundle 回灌 + 验收

- [ ] 3.1 两工具 + tests 落权威源 `sdflow-init/assets/workflow/tools/(tests/)`；dev `setup.sh` 同步 canonical。
- [ ] 3.2 `sdflow-init update` 推下游（不含 tests/，核对脚本本体）。
- [ ] 3.3 全套件 pytest 绿；Success Metrics 三项达标核对；主 spec :550 回灌确认。
