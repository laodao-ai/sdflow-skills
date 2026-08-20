# Hand-off · sweep-pool-debt-2026-08

阶段三（/sdflow-ship 全自动链）收尾交接。verify PASS（强档 Do-Not-Trust 冷启，每 ✅ 附机验锚点）。

## ✅ 完成了什么（锚点均复核存在）

- **票 1 · ship_gate 内容锚**：失鲜判定从 commit-SHA 把手改为 manifest+digest 内容指纹单一源（`ship_gate.py` `fingerprint_entries`/`is_stale` digest 等值，两分支均改，不再取锚作 git ref）；勾框豁免层（`_normalize_checkbox_lines`/`_tasks_content_exempt`）物理删除（grep NONE）；新增 `anchor_writeback.py`（权威写锚，`--set` 原子 + 脏树/空域 fail-loud）；13 测试迁移；三产出方 SKILL 回写改调脚本；新 ADR 0044 + 0026 superseded。
- **票 2 · 归档面收敛 + CI**：17 归档 tasks.md 回填/改写（`validate --archived` 17→0 failed，78 passed）；`mechanical-gates.yml` pin 1.5.0→1.9.0 + `validate --archived` 门 + 定点破坏自证。
- **票 3 · 切片偏离对账**：`sdflow-code-review` Step1 三分支（`SKILL.md:246-260`），delta spec 3 Scenario 落实。
- **票 4 · SKILL.md 下沉**：5 段判据下沉 `references/execution-protocol-details.md`；resident-contract 全绿。
- **票 5 · 实现验证**：聚合套件 2580 passed @ `40585ab`（收尾票时点，e2e 本仓无此层记未覆盖）。
- **冷层代码审修复（commit 192f59a）**：2 Critical（跨模型 manifest digest 碰撞 C1、脏树守卫 git 失败 fail-open C2）+ 4 high + 2 中，8 条全修 + 10 红→绿回归测试；复审 1 轮干净。
- **最终盘面全量 pytest 2590 passed, 0 failed**（verify 亲跑 @ HEAD `7d805f8`）。

## ⏳ 未完成 / 延后

- **T297**（todo · 冷审对抗镜B）：`design.md:79`「其余在途 change 无旧报告存量」是现状快照非目标态不变量——新 gate 升级生效后，另一在途 change（如 `add-frontend-checklists`）若已有 40-hex live 报告，会触发与 task1.9 同构的自锁（UNKNOWN(6)，fail-closed 可恢复，重跑 anchor_writeback 即解）。**通则③靶心**，但 Non-Goal 范围人已定、机制 fail-closed。
- **T298**（todo · 冷审对抗镜C）：`anchor_writeback` 非 UTF-8 报告内容 `errors=replace` 不可逆写回损毁。基准④低概率（报告均 agent 生成纯文本），已 defer。
- **B27**（bug · 票 2 票外发现，`source_change` 显式置空脱离本 change）：`windows-recorder-smoke.yml` 的 windows-full-pytest 自 2026-08-12 起持续红（runner 缺 yq）。与本 change 无关的独立 CI 缺陷。
- **task1.9（CHANGED）**：设计要求重锚本 change 自身报告为 64-hex，执行期实测证伪（驱动 ship 的老门读 64-hex 自锁）→ 保留 40-hex，冷审两轴+跨模型独立核验推理成立（40-hex 在 ship 期与归档后均安全）。
- **task4.1（PARTIAL · 待人拍板）**：`sdflow-spec/SKILL.md` 17,164 字符，未达 design「目标 ≤16,000」（差 ~1,164）；红线（resident-contract 全绿 + 18,000 硬上限）达成余量 836。剩余大头（principles 托管块 + fail-closed 骨架）经双轴审两轴核验确属 DT-5 不可下沉类，继续压缩会削弱 fail-closed 防护（通则③不为凑字数砍范围）。**是否接受此差额留人拍板**。

## ▶ 下一阶段建议

1. **T297 值得一个后续清理 change**（优先级中）：给 gate 升级引入「upgrade 前扫描/批量重锚在途 change 存量 40-hex 报告」，或至少 `sdflow-upgrade` 时告警。这是本 change 迁移设计里唯一留下的目标态窗口——虽 fail-closed 可恢复，但多在途 change 场景会撞。可与 T298 一并清（同属 anchor 迁移收尾）。
2. **task4.1 字符数差额**：若坚持 ≤16,000 目标，须动 fail-closed 骨架/托管块——那是范围外重定，建议维持现状（红线已达成），或人明确要求再议。
3. **B27**（Windows CI yq）独立于本 change，可随 Windows CI 维护一并处理。
