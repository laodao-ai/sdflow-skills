# Tasks · sweep-pool-debt-2026-08

四张垂直切片（见 design.md「切片建议」），票间无阻塞边。每任务标注对应 Requirement（specs delta 内名称）。

## 1. 票 1 · T292 ship_gate 内容锚

- [ ] 1.1 `ship_gate.py` 新增指纹单一源函数：监视域枚举 → manifest 规范记录清单（**字节保真编码**：`ls-tree -z` 原始 path 字节、按原始字节序排序、base64 单行标量落 frontmatter，见 DT-2〔spec-review-amendment〕）→ sha256 digest；design 域监视集去 `tasks.md`（`DESIGN_WATCHED_NAMES` 调整），code/verify 域沿用顶层条目口径——**但比较机制 MUST 一并改写**：现 code 分支以锚 sha 作 git ref 取 `ls_tree_map`（ship_gate.py:950），MUST 重写为 HEAD 侧重算 digest 等值，MUST NOT 将 64-hex 锚作 git ref 解析〔spec-review-amendment〕〔Req: 失鲜判定 MUST 直接比较内容；阶段三编排台账确定性（ship_gate·内容锚）〕
- [ ] 1.2 `is_stale` 重写为「HEAD 侧重算 digest vs 锚 digest 等值」（design 与 code/verify 两分支均改）；删除 `_normalize_checkbox_lines` / `_tasks_content_exempt` / `is_stale` 内联 tasks 豁免段（合计 ~100 行）〔spec-review-amendment：subject 豁免逐提交 walk（BR-7 真值表）**gate 代码已于 impl-review-fix 先期删除、无货可删**——本步该部分 = `grep -n "subject\|BR-7" ship_gate.py` 确认无残留即可，MUST NOT 在 impl-report 报「删除了 walk」〕；诊断改 manifest 差集点名路径 + `git log -1 -- <路径>` 点名提交；REFUSE_START 分类原因按新判据分支更新，五类 UNKNOWN 诊断文案 MUST 齐 problem/cause/fix 三段〔spec-review-amendment，devex DX-02〕〔Req: 同上 + 阶段三…内容锚 REFUSE_START Scenario〕
- [ ] 1.3 锚读取层：`read_reviewed_sha` 改为读 `reviewed_sha`（64-hex）+ `reviewed_manifest` 并做互证校验（manifest 字节 sha256 == digest）；缺失/非法/不互证 → UNKNOWN(6)；「锚指向对象不存在或非 commit」分类与其诊断文案物理删除（六类→五类）；**校验分层**〔spec-review-amendment R1，防 SHIPPED 大面积回归〕：解析层 `FIELD_VALIDATORS["reviewed_sha"]` 放宽为 40|64 位小写 hex 语法校验 + `reviewed_manifest` 注册单行 base64 语法校验器（解析核不 fork，承 A4 共核）；64-hex+互证语义强制只落 `read_reviewed_sha`（live），40-hex 诊断指明「旧格式锚，重跑写锚脚本」；`archived_verify_state` 只消费 `verify` 结论（归档区 34 份 40-hex 锚报告 MUST 保持可判 SHIPPED）〔Req: 评审锚 MUST 由 producer 记录；gate 的 git 调用失败…；归档报告旧 40-hex 锚不阻断 SHIPPED Scenario〕
- [ ] 1.4 HEAD 侧枚举失败 fail-closed：非零退出 MUST NOT 折叠为空 manifest 参与比较（空集 digest 假等值面）；变异证明用例〔Req: 内容比较 MUST 区分读失败与内容为空〕
- [ ] 1.5 新增 `sdflow-ship/scripts/anchor_writeback.py`（sibling，`import ship_gate` 复用指纹函数〔可行性已实测：模块顶层零副作用〕；4 行 reconfigure 前导；原子替换写 frontmatter；**支持同批写入结论字段（`--set` 类接口），producer 一次调用落结论+锚**〔spec-review-amendment，满足「结论字段与锚 MUST 原子写入」Scenario〕；空监视域/枚举失败 fail-loud 拒写；**监视集路径有未提交改动时 fail-loud 拒写**〔spec-review-amendment R2 脏树守卫：`git status --porcelain -- <监视集>` 非空即拒、提示先提交；逃生口 `--allow-dirty` 类仅显式越权留痕〕；头注释登记「手跑重锚=显式越权留痕」）〔Req: 评审锚…（锚值 MUST 由脚本计算 Scenario）；内容比较…（写锚时空监视域 Scenario）〕
- [ ] 1.6 测试迁移：`sdflow-ship/tests/` 全部 reviewed_sha 相关 fixture 与断言迁到内容锚（11 个文件，实测 grep〔spec-review-amendment〕；含 rebase 免疫新测试：内容不变重写提交历史 → CURRENT；勾框豁免层删除后对应测试退役；anchor_writeback 单测）；另 MUST 含〔spec-review-amendment〕：manifest 字节保真 round-trip（Tab/换行/非 UTF-8 路径/CRLF）、code/verify 域 digest 等值（锚非 git 对象仍可判）、归档 40-hex + `verify: PASS` → SHIPPED 回归（变异证明：归档读点也走 64-hex 校验 ⇒ 红）〔Req: spec-workflow delta 各 Scenario 的「MUST 有用例」条目〕
- [ ] 1.7 三个产出方 SKILL 回写步骤改调 `anchor_writeback.py`（`sdflow-spec-review` 拍板回写 / `sdflow-code-review` 报告落盘 / `sdflow-done` verify 模板与预检句 40-hex→64-hex+manifest），并 MUST 写明脚本调用失败（非零退出/空监视域）时的处置指引文案〔spec-review-amendment，devex DX-05〕；`sdflow-code-review` **新建** impl-review 重锚协议段（现 SKILL 无既有协议可「补」〔spec-review-amendment〕——含触发条件：对监视集文件打 `[impl-review-fix]` 补丁提交后；授权边界；调脚本刷新锚不动结论字段并随提交落盘）〔Req: 评审锚…；阶段三…内容锚 B2 Scenario〕
- [ ] 1.8 新 ADR（**新增独立 ADR 文件** + adr/0026 头部加 superseded-by 指针，按仓 ADR 惯例〔spec-review-amendment〕：为何 manifest+digest、tasks.md 移出、豁免通道改重锚协议）；全仓 `grep -rn reviewed_sha`（不加 --include）收口核查（归档区除外；实测消费面 21 文件，含 `openspec/specs/openspec-170-followup/spec.md` 与 `docs/workflow-skills/sdflow-spec-review.md` 的 40 位格式句〔spec-review-amendment〕）；全量 pytest 绿〔Req: 全部；memo D8〕

- [ ] 1.9 票 1 收尾：用 `anchor_writeback.py` 重锚**本 change 自身** `spec-review-report.md`（40-hex→64-hex+manifest，不动结论字段）并 checkpoint 落盘，随后实跑 `ship_gate` 确认 design 域 CURRENT——否则票 2/3/4 期间 gate 读本报告旧锚判 UNKNOWN(6) 自锁〔spec-review-amendment，对抗镜自举发现；Req: 评审锚…（存量旧格式锚重跑写锚）〕

## 2. 票 2 · T294 归档面收敛 + CI

- [ ] 2.1 桶B 14 个 change：逐条对照 git log / 实现 commit 回填漏勾复选框（确未做的留 `- [ ]` + 说明）〔Req: 归档 tasks.md MUST 如实反映完成状态〕
- [ ] 2.2 桶A 2 个 tickets 管线 change（remove-superpowers-pipeline 0/21、sdflow-init-readwrite-paths 0/12）：对照 git log 逐条回填〔Req: 同上（已 ship 的 tickets 管线 change 回填 Scenario）〕
- [ ] 2.3 桶C scoped-test-per-task：tasks.md 改写为无勾选框作废说明段（指明被 remove-superpowers-pipeline supersede、从未执行）〔Req: 同上（作废 change 改写 Scenario）〕
- [ ] 2.4 本地 `openspec validate --archived` 全量 0 failed 后：`.github/workflows/mechanical-gates.yml` openspec pin 1.5.0→1.9.0 + 新增 `validate --archived` 步；新步 MUST 复用既有 openspec 泳道同一 `if` 条件（CLI 仅装于 ubuntu-latest×3.12），并同步更新该泳道「断言 CLI 1.5.0 具体行为」注释（1.9.0 已本地实测既有面全绿）〔spec-review-amendment〕；顺序不可颠倒（DT-6）〔Req: 归档面校验 MUST 由 CI 机械守〕
- [ ] 2.5 定点破坏自证：临时引入一个未勾复选框确认该步真红后还原（恒真锚防线）〔Req: 同上（定点破坏必红 Scenario）〕

## 3. 票 3 · T290 切片偏离对账接线

- [ ] 3.1 `sdflow-code-review/SKILL.md` Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行；对账逻辑三分支（静默偏离上报 / 已申报核对 / 无输入降级不中断）〔Req: 切片偏离审计行 SHALL 被代码审 scope 审计对账消费〕

## 4. 票 4 · T287 SKILL.md 下沉

- [ ] 4.1 按 DT-5 判据挑选 `sdflow-spec/SKILL.md` 可下沉小节 → `references/`（含路由句），本体 ≤16,000 字符〔Req: 无 spec delta，memo D7〕
- [ ] 4.2 `pytest hack/tests/test_sdflow_spec_resident_contract.py` 全绿 + 全量 pytest 复核〔Req: 同上〕

## 测试覆盖图（TG-18）

| code path | 测试类型 |
|---|---|
| 指纹函数（manifest 生成/排序/digest，含字节保真 round-trip〔spec-review-amendment〕） | 单测（票 1.6） |
| is_stale digest 等值（design + code/verify 两分支）+ rebase 免疫 | 单测 + git fixture 集成（票 1.6） |
| 归档 40-hex 锚 SHIPPED 回归〔spec-review-amendment〕 | git fixture 集成（票 1.6） |
| 锚互证/缺失/非法 → UNKNOWN(6) | 单测（票 1.6） |
| 枚举失败不折叠空集 | 变异证明单测（票 1.4） |
| anchor_writeback 写入/拒写 | 单测（票 1.6） |
| 归档面 validate | `openspec validate --archived` 实跑（票 2.4）+ CI 定点破坏自证（票 2.5） |
| SKILL.md 体量/结构 | 既有 resident-contract pytest（票 4.2） |
| SKILL 指令层改动（票 1.7 / 3.1） | 无自动化（指令层，评审兜底） |
