# Tasks — gate-checkpoint-hardening

> 规则/文案/注释/模板编辑 + `ship_gate.py` 注释与（T26）触发对照说明 + `sdflow-done` merge 前置检查，无重构、无新格式。测试 = 机械核对 + 既有 `sdflow-ship/tests` 零回归。
> 每任务 commit 步 MUST 用 `bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。
> scope 边界〔grill Q5〕：就此打住，不再 fold。

## 1. checkpoint 标签格式单源（T36/T37/T38，格式源=TAG_RE）

- [ ] 1.1 接地核对 design.md ADR-4 锚族 A scope-check 表：TAG_RE、workflow.md、sdflow-ship/SKILL、spec Scenario、checkpoint-commit.sh、code-review 台账锚——逐一确认现状
- [ ] 1.2 T36 格式源：`ship_gate.py` TAG_RE 处加 canonical-shape 头注释（规范形状 `checkpoint(<change>:task<N>-<slug>)` + "格式权威在此、test_producer_parser_contract.py 钉一致"）；确认 `checkpoint-commit.sh` 不被引作格式源（如 `--help` 有误导则改为"格式见 TAG_RE 契约"）
- [ ] 1.3 T36 规则源：`workflow.md` 就地留"plan 每任务用命名空间标签"规则一处（含格式串一次 + 标"形状由 TAG_RE 执行"）；`sdflow-ship/SKILL.md` 改**引用** workflow.md，删除重复整句
- [ ] 1.4 T38：spec/doc 占位符 `<当前change>` 等 → `<change-slug>`（先 grep 接地确认哪些文件真含歧义写法再逐处改）
- [ ] 1.5 T37：主 spec 复述标签形状的 Scenario 标注"样例非权威（权威在 TAG_RE）"
- [ ] 1.6 机械核对：无第二份完整格式串复述；grep 确认无残留 `<当前change>`；checkpoint-commit.sh 未被当格式源
- [ ] 1.7 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task1-tag-format-single-source`

## 2. ship-gate 锚模板独占裸行（T43，锚族 B）

- [ ] 2.1 `sdflow-spec-review/SKILL.md:102` 的 design-approved 锚去反引号、改独占裸行
- [ ] 2.2 `sdflow-code-review/SKILL.md:149-150` 的 code-review 锚：同行尾注「（建议进…）」移出锚行（尾注另起行或删），使锚独占裸行
- [ ] 2.3 核验 `sdflow-done/SKILL.md:80-81` verify 锚确为独占裸行（如已是则记录确认，不改）
- [ ] 2.4 机械核对：三 SKILL 的 `<!-- ship-gate: -->` 锚模板 grep 出来均 `strip()` 后等值锚字面（无反引号/尾注）
- [ ] 2.5 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task2-anchor-bare-line`

## 3. gate 新鲜度 committed-only + merge 硬检查（T35/T33，ADR-1）

- [ ] 3.1 `ship_gate.py` 新鲜度注释（原 T33 停置处）更新为定夺结论：committed-only 正式化 + "盘面即状态"理由，无逻辑变更
- [ ] 3.2 `sdflow-ship/SKILL.md` 收尾段加**非门禁软提示**：工作树有未提交非-openspec 改动时提示"gate 判定不含它们"（明确不改退出码）
- [ ] 3.3 `sdflow-done/SKILL.md` merge 步加**硬前置检查**：工作树有未提交非-openspec 改动 → 停下问、不静默 merge（定义"非-openspec 改动"判据 + 用户显式放行通道）
- [ ] 3.4 跑 `pytest sdflow-ship/tests/` 确认零回归
- [ ] 3.5 关账：T33/T35 gate 侧 → WONTDO 附理由；软提示 + merge 检查落 SKILL 记 DONE
- [ ] 3.6 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task3-freshness-and-merge-guard`

## 4. gate 熔断触发判据硬化（T26，ADR-2）

- [ ] 4.1 `sdflow-ship/SKILL.md` 熔断条款改：触发判据 = 重跑前检查 `HEAD` 与该步报告自本 turn 上次跑后是否未推进（HEAD 未移 + 报告 mtime/sha 未变），未推进即判无进展停上抛；替换原"数重试次数"表述
- [ ] 4.2 `sdflow-ship/SKILL.md` 熔断条款补：持久化计数不下沉（撞盘面即状态/gate 零副作用/ship 零跨步状态三红线），保留 within-invocation before-快照 bit
- [ ] 4.3 关账：T26 → 已探索·产出"触发硬化"·持久化 defer（登记接受取舍），非纯 WONTDO
- [ ] 4.4 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task4-breaker-trigger-harden`

## 5. spec delta 对码核验 + 校验

- [ ] 5.1 按实现实况核 `specs/spec-workflow/spec.md` 三条 ADDED 需求与代码/文案一致（格式源=TAG_RE、committed-only+merge 检查、熔断盘面对照触发都已落实）
- [ ] 5.2 `openspec validate gate-checkpoint-hardening` 通过
- [ ] 5.3 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task5-spec-verify`

## 6. 部署 + 全量验证

- [ ] 6.1 开发 checkout 跑 `bash setup.sh`（改 assets/workflow 才让全局 canonical 生效、测得到）
- [ ] 6.2 `resolve-workflow.sh` 解析确认 canonical 指向本 checkout；抽查 workflow.md 改动经全局生效
- [ ] 6.3 全仓 `pytest` 确认零回归
- [ ] 6.4 commit：`checkpoint-commit.sh gate-checkpoint-hardening:task6-deploy-verify`
