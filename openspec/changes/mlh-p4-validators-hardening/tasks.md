# tasks — mlh-p4-validators-hardening

> 需求 ID：**R1** = hr-tg-intersection-check「命中 TG 集与成员行严格解析」（T138）· **R2** = outside-voice-reuse-guard「step1 锚数量一致性」（T139）· **R3** = spec-workflow「anchor_lint hr-tg 内部一致性重算 + grace」（T136/T140）。
> 切片对应 design D5：T-a=R3 · T-b=R1 · T-c=R2（3 张垂直切片，出票期由 sdflow-implement 定稿）。

## 1. T-b · hr_tg_intersect 严格解析（R1 / T138）

- [ ] 1.1 `parse_tg_set`（`:54-62`）删「空 cell 静默过滤」——仅原始空串表空集；split 后出现空/纯空白 cell → `EmitError`。〔R1〕
- [ ] 1.2 成员抽取改词边界严格 token（整体 `^TG-\d+$` 级），畸形 token（`TG-04x`）→ `EmitError`，不宽松正规化。〔R1〕
- [ ] 1.3 pytest 坏输入断言（TG-18）：`TG-04,,TG-16` / `,` / 前后逗号 → 非零；`""` 空串 → `none`；成员 `TG-04x` → 非零。〔R1〕

## 2. T-c · outside_voice_guard 双锚一致性（R2 / T139）

- [ ] 2.1 `parse_mode`（`:51-61`）改 `.search` → 收集 fence 外全部 step1-broad-review 锚 mode。〔R2〕
- [ ] 2.2 数量/一致性归约：1 锚取之；≥2 一致取之（容重复）；≥2 冲突 → `EmitError`；0 锚保持既有 fail-closed。〔R2〕
- [ ] 2.3 pytest（TG-18）：单锚照常；双锚 native+simulated → 非零；双锚同 mode → 取之退 0。〔R2〕

## 3. T-a · anchor_lint hr-tg 锚加固（R3 / T136+T140）

- [ ] 3.1 `check_hr_tg`（`:163-174`）接 `--trigger-catalog` 入参；复用 hr_tg_intersect 成员解析 + 严格 tg-set 解析（依赖 T-b 严格口径）。〔R3〕
- [ ] 3.2 新格式锚（含 `declared=`）重算 `declared∩HR-TG`、要求 `hit=` 逐元素一致（含 none⟺空交集），不一致/畸形 → 新违规 `kind`（建议 `hit-declared-mismatch`）。〔R3·T136〕
- [ ] 3.3 诚实边界：文档/docstring 显式声明「只堵内部一致性、非 tamper-proof」；含「同改两字段一致但错 → 仍过」边界确认负例。〔R3·T136〕
- [ ] 3.4 旧格式锚（`evidence=` 无 `declared=`）缺 declared 降级 WARN 不 exit1；纯畸形锚仍违规。〔R3·T140〕
- [ ] 3.5 `--trigger-catalog` 未传 → 仅字段在场 + WARN 未重算，不硬失败既有调用点。〔R3·T140〕
- [ ] 3.6 pytest（TG-18）：一致→过；单字段手改→违规；同改两字段一致但错→过（边界确认）；旧格式缺 declared→WARN 不 exit1；未传 catalog→WARN 降级。〔R3〕

## 4. SKILL 接线（薄，引用单一源）

- [ ] 4.1 若 3.1 需 SKILL 侧供 `--trigger-catalog`：`sdflow-code-review`/`sdflow-spec-review` 的 anchor_lint 调用步补 `--trigger-catalog $RULES_ROOT/trigger-catalog.md`，引用不复述。〔R3〕
- [ ] 4.2 design Open Question 核验：grep 本仓有无重 lint `spec-review-report.md` 的流程，结果写回（定 T140 grace 定位）。〔R3·假设核验〕

## 5. bundle 回灌 + 验收

- [ ] 5.1 三工具 + tests 落权威源 `sdflow-init/assets/workflow/tools/(tests/)`；dev `setup.sh` 同步 canonical。
- [ ] 5.2 `sdflow-init update` 推下游 `openspec/workflow/tools/`（下游不含 tests/，核对脚本本体一致）。
- [ ] 5.3 全套件 pytest 绿（三工具 tests 无回归）；Success Metrics 三项达标核对。
