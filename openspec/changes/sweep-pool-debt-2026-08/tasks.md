# Tasks · sweep-pool-debt-2026-08

四张垂直切片（见 design.md「切片建议」），票间无阻塞边。每任务标注对应 Requirement（specs delta 内名称）。

## 1. 票 1 · T292 ship_gate 内容锚

- [ ] 1.1 `ship_gate.py` 新增指纹单一源函数：监视域枚举 → manifest 规范行清单（path 排序）→ sha256 digest；design 域监视集去 `tasks.md`（`DESIGN_WATCHED_NAMES` 调整），code/verify 域沿用顶层条目口径〔Req: 失鲜判定 MUST 直接比较内容；阶段三编排台账确定性（ship_gate·内容锚）〕
- [ ] 1.2 `is_stale` 重写为「HEAD 侧重算 digest vs 锚 digest 等值」；删除 `_normalize_checkbox_lines` / `_tasks_content_exempt` / tasks 支路 / subject 豁免逐提交 walk（BR-7 真值表）；诊断改 manifest 差集点名路径 + `git log -1 -- <路径>` 点名提交；REFUSE_START 分类原因按新判据分支更新〔Req: 同上 + 阶段三…内容锚 REFUSE_START Scenario〕
- [ ] 1.3 锚读取层：`read_reviewed_sha` 改为读 `reviewed_sha`（64-hex）+ `reviewed_manifest` 并做互证校验（manifest 字节 sha256 == digest）；缺失/非法/不互证 → UNKNOWN(6)；「锚指向对象不存在或非 commit」分类与其诊断文案物理删除（六类→五类）〔Req: 评审锚 MUST 由 producer 记录；gate 的 git 调用失败…〕
- [ ] 1.4 HEAD 侧枚举失败 fail-closed：非零退出 MUST NOT 折叠为空 manifest 参与比较（空集 digest 假等值面）；变异证明用例〔Req: 内容比较 MUST 区分读失败与内容为空〕
- [ ] 1.5 新增 `sdflow-ship/scripts/anchor_writeback.py`（sibling，`import ship_gate` 复用指纹函数；4 行 reconfigure 前导；原子替换写 frontmatter；空监视域/枚举失败 fail-loud 拒写；头注释登记「手跑重锚=显式越权留痕」）〔Req: 评审锚…（锚值 MUST 由脚本计算 Scenario）；内容比较…（写锚时空监视域 Scenario）〕
- [ ] 1.6 测试迁移：`sdflow-ship/tests/` 全部 reviewed_sha 相关 fixture 与断言迁到内容锚（含 rebase 免疫新测试：内容不变重写提交历史 → CURRENT；豁免层/walk 删除后对应测试退役；anchor_writeback 单测）〔Req: spec-workflow delta 各 Scenario 的「MUST 有用例」条目〕
- [ ] 1.7 三个产出方 SKILL 回写步骤改调 `anchor_writeback.py`（`sdflow-spec-review` 拍板回写 / `sdflow-code-review` 报告落盘 / `sdflow-done` verify 模板与预检句 40-hex→64-hex+manifest）；`sdflow-code-review` impl-review 提交协议补「修订提交后重跑写锚」一步〔Req: 评审锚…；阶段三…内容锚 B2 Scenario〕
- [ ] 1.8 新 ADR（修订/接续 adr/0026 锚记录：为何 manifest+digest、tasks.md 移出、豁免通道改重锚协议）；全仓 `grep -rn reviewed_sha`（不加 --include）收口核查（归档区除外）；全量 pytest 绿〔Req: 全部；memo D8〕

## 2. 票 2 · T294 归档面收敛 + CI

- [ ] 2.1 桶B 14 个 change：逐条对照 git log / 实现 commit 回填漏勾复选框（确未做的留 `- [ ]` + 说明）〔Req: 归档 tasks.md MUST 如实反映完成状态〕
- [ ] 2.2 桶A 2 个 tickets 管线 change（remove-superpowers-pipeline 0/21、sdflow-init-readwrite-paths 0/12）：对照 git log 逐条回填〔Req: 同上（已 ship 的 tickets 管线 change 回填 Scenario）〕
- [ ] 2.3 桶C scoped-test-per-task：tasks.md 改写为无勾选框作废说明段（指明被 remove-superpowers-pipeline supersede、从未执行）〔Req: 同上（作废 change 改写 Scenario）〕
- [ ] 2.4 本地 `openspec validate --archived` 全量 0 failed 后：`.github/workflows/mechanical-gates.yml` openspec pin 1.5.0→1.9.0 + 新增 `validate --archived` 步；顺序不可颠倒（DT-6）〔Req: 归档面校验 MUST 由 CI 机械守〕
- [ ] 2.5 定点破坏自证：临时引入一个未勾复选框确认该步真红后还原（恒真锚防线）〔Req: 同上（定点破坏必红 Scenario）〕

## 3. 票 3 · T290 切片偏离对账接线

- [ ] 3.1 `sdflow-code-review/SKILL.md` Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行；对账逻辑三分支（静默偏离上报 / 已申报核对 / 无输入降级不中断）〔Req: 切片偏离审计行 SHALL 被代码审 scope 审计对账消费〕

## 4. 票 4 · T287 SKILL.md 下沉

- [ ] 4.1 按 DT-5 判据挑选 `sdflow-spec/SKILL.md` 可下沉小节 → `references/`（含路由句），本体 ≤16,000 字符〔Req: 无 spec delta，memo D7〕
- [ ] 4.2 `pytest hack/tests/test_sdflow_spec_resident_contract.py` 全绿 + 全量 pytest 复核〔Req: 同上〕

## 测试覆盖图（TG-18）

| code path | 测试类型 |
|---|---|
| 指纹函数（manifest 生成/排序/digest） | 单测（票 1.6） |
| is_stale digest 等值 + rebase 免疫 | 单测 + git fixture 集成（票 1.6） |
| 锚互证/缺失/非法 → UNKNOWN(6) | 单测（票 1.6） |
| 枚举失败不折叠空集 | 变异证明单测（票 1.4） |
| anchor_writeback 写入/拒写 | 单测（票 1.6） |
| 归档面 validate | `openspec validate --archived` 实跑（票 2.4）+ CI 定点破坏自证（票 2.5） |
| SKILL.md 体量/结构 | 既有 resident-contract pytest（票 4.2） |
| SKILL 指令层改动（票 1.7 / 3.1） | 无自动化（指令层，评审兜底） |
