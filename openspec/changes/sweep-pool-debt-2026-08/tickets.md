---
impl-pipeline: tickets
---

## Global Constraints

逐字摘自 `design.md` 的 MUST / MUST NOT / SHALL 硬约束与 Compliance 条款（implementer 与两轴审 reviewer 共享同一注意力透镜）：

- **DT-1 校验分层**〔spec-review-amendment R1，防 SHIPPED 大面积回归〕：解析层（`FIELD_VALIDATORS`）对 `reviewed_sha` 只做语法校验并放宽为「40 或 64 位小写 hex」、`reviewed_manifest` 注册单行 base64 语法校验器——解析核不 fork、无归档模式参数（承 A4 共核纪律，对存量行为零回归）；64-hex + manifest 互证的语义强制上移 `read_reviewed_sha`（live 读点），40-hex 判 ANCHOR_INVALID → UNKNOWN(6)，诊断指明「旧格式锚，重跑写锚脚本」；`archived_verify_state` 只消费 `verify` 结论，34 份 40-hex 归档报告自然通过解析（无 fail-open：新鲜度恒要求 digest 等值，40-hex 不可能等于重算 digest）。旧值(40-hex)进新 gate 判 ANCHOR_INVALID → UNKNOWN(6) 可恢复，天然 fail-closed。
- **DT-2 等值判定只走 digest**（重算 HEAD 侧 manifest → sha256 → 与锚值比对）；**诊断走 manifest**（digest 不等时对 HEAD 侧枚举求差集 → 点名路径，`git log -1 -- <路径>` 点名提交）。**监视域按报告分**：design 域 = change 目录内 `proposal.md`/`design.md`/`specs/`（tasks.md 移出，D2）；code/verify 域 = 顶层条目映射（非递归、排除 `openspec`，既有口径）——两域锚值均为 manifest digest，**gate MUST NOT 将锚值作 git ref 解析**（现 code 分支 `ship_gate.py:950` 以锚 sha 取 `ls_tree_map`，MUST 一并重写为 HEAD 侧重算 digest 等值）。
- **DT-2 manifest 规范编码 MUST 字节保真**：记录取 `ls-tree -z` 原始 path 字节（git 路径可含 Tab/换行/非 UTF-8），按原始 path 字节序排序；frontmatter 存储用单行字节保真编码（base64 该规范字节流），digest 对解码后原始字节计算；**MUST NOT 依赖 YAML 文本行清单的转义/归一化**（会致同内容不同 digest 或异路径折叠）；互证 = 解码字节流的 sha256 == `reviewed_sha`。比较端不取锚侧字节 ⇒ 无 dangling-blob 依赖。
- **DT-3 脚本 MUST 支持同批写入结论字段**（如 `--set design_approved=true` / `--set verify=PASS`），producer 一次调用同时落结论+锚（单次原子替换）；**MUST NOT 先手写结论再调脚本补锚**（中间态 = 结论在、锚缺 → UNKNOWN）。**脏树守卫**〔spec-review-amendment R2〕：监视集路径存在未提交改动（`git status --porcelain -- <监视集>` 非空）时 **MUST fail-loud 拒写**并提示「先提交修订再写锚」；逃生口（如 `--allow-dirty`）仅显式越权留痕场景。脚本带 4 行 `reconfigure` 前导（第五道机械门要求）。判官只读语义不破。
- **枚举失败 fail-closed**〔tasks 1.4〕：HEAD 侧枚举非零退出 **MUST NOT 折叠为空 manifest 参与比较**（空集 digest 假等值面）。
- **DT-7 impl-review 豁免通道改造**：gate 端 subject 豁免与勾框内容豁免在 spec 层一并退役（subject 豁免代码已于先前 impl-review-fix 物理删除、无货可删；勾框豁免代码仍在、真删），`is_stale` 缩为「重算指纹 → digest 等值」；`sdflow-code-review` **新建** impl-review 重锚协议段——修订提交后跑 `anchor_writeback.py` 刷新 spec-review-report 锚（不动结论字段）并随提交落盘。忘重锚 ⇒ REFUSE_START（fail-closed，补跑即恢复）。
- **Compliance**：遵守 `openspec/rules/doc-authoring.md`（DOC-1：正文即最终态，无演进史层）；遵守 `premise-verification`（断言带核验锚，引用前真打开）；**基准 5：不新增任何 Markdown/语法解析——指纹是零解析字节级 digest；fence 有界词法共用件保留原状**（`fence_delim`/`FenceTracker` 四处共用件不在删除面内）。

### Task 1: ship_gate 内容锚（指纹单一源 + is_stale 重写 + anchor_writeback + 测试迁移 + 消费面收口）

**Blocked-by:** none
**R-ID:** SW1-SW6（spec-workflow delta 全部 Requirement：内容锚台账确定性 / 失鲜直接比较内容 / 评审锚 producer 记录 / 内容比较区分读失败与空 / gate git 调用失败退出码契约 / sdflow-code-review 复审边界；及 REMOVED 旧「阶段三编排台账确定性(ship_gate)」）

把 `ship_gate.py` 的失鲜判定从「以锚 commit SHA 作把手、ls-tree 映射等值 + tasks.md 逐提交豁免 walk」改为「监视域内容指纹（manifest + digest）单一源等值」，并交付权威写锚脚本，使 producer 写锚与 gate 验锚跑同一函数（物理同源）。对外可观察行为：设计门失鲜以内容 digest 判定（rebase/amend 不改内容即 CURRENT）、旧格式锚 fail-closed 判 UNKNOWN(6) 可恢复、归档 40-hex 报告仍可判 SHIPPED、`sdflow-code-review` 具备 impl-review 尾流修订的重锚协议。

- [x] 指纹单一源函数落地：监视域枚举 → manifest 规范记录（字节保真编码，见 Global Constraints DT-2）→ sha256 digest；design 域监视集去 `tasks.md`（`DESIGN_WATCHED_NAMES` 调整），code/verify 域沿用顶层条目口径
- [x] `is_stale`（design + code/verify 两分支）重写为「HEAD 侧重算 digest vs 锚 digest 等值」；`ship_gate.py:950` 现以锚 sha 作 git ref 取 `ls_tree_map` 的 code 分支一并改写为 HEAD 侧重算 digest 等值，锚值不再作 git ref 解析
- [x] 删除勾框豁免层（`_normalize_checkbox_lines` / `_tasks_content_exempt` / `is_stale` 内联 tasks 豁免段，约 60–80 行 + 对应测试退役）；`grep -n "subject\|BR-7" ship_gate.py` 确认 subject 豁免 walk 已无残留（先期已删、无货可删，MUST NOT 在 report 报「删除了 walk」）
- [x] 锚读取层 `read_reviewed_sha` 读 `reviewed_sha`(64-hex)+`reviewed_manifest` 并互证（manifest 字节 sha256 == digest）；缺失/非法/不互证 → UNKNOWN(6)；「锚指向对象不存在或非 commit」分类与诊断文案物理删除（六类→五类），五类 UNKNOWN 诊断 MUST 齐 problem/cause/fix 三段
- [x] 校验分层落地（见 Global Constraints DT-1）：`FIELD_VALIDATORS["reviewed_sha"]` 放宽为 40|64 位小写 hex 语法校验 + `reviewed_manifest` 单行 base64 语法校验器（解析核不 fork）；`archived_verify_state` 仅消费 `verify` 结论，归档 34 份 40-hex 锚报告保持可判 SHIPPED
- [x] HEAD 侧枚举失败 fail-closed：非零退出 MUST NOT 折叠为空 manifest（含变异证明用例）
- [x] 新增 `sdflow-ship/scripts/anchor_writeback.py`（sibling，`import ship_gate` 复用指纹函数、4 行 reconfigure 前导、原子替换写 frontmatter、`--set` 同批写结论字段、空监视域/枚举失败 fail-loud 拒写、脏树守卫 fail-loud 拒写 + `--allow-dirty` 越权逃生口、头注释登记「手跑重锚=显式越权留痕」）
- [x] 测试迁移：`sdflow-ship/tests/` 全部 `reviewed_sha` 相关 fixture 与断言迁到内容锚（实测 11 文件）；MUST 含 rebase 免疫（内容不变重写提交历史 → CURRENT）、manifest 字节保真 round-trip（Tab/换行/非 UTF-8 路径/CRLF）、code/verify 域 digest 等值（锚非 git 对象仍可判）、锚互证/缺失/非法 → UNKNOWN(6)、归档 40-hex + `verify: PASS` → SHIPPED 回归（变异证明：归档读点走 64-hex 校验 ⇒ 红）、anchor_writeback 写入/拒写单测
- [x] 三个产出方 SKILL 回写步骤改调 `anchor_writeback.py`（`sdflow-spec-review` 拍板回写 / `sdflow-code-review` 报告落盘 / `sdflow-done` verify 模板与预检句 40→64-hex+manifest），并写明脚本调用失败（非零退出/空监视域）处置指引文案
- [x] `sdflow-code-review` **新建** impl-review 重锚协议段（触发条件：对监视集文件打 `[impl-review-fix]` 补丁提交后；授权边界；调脚本刷新锚不动结论字段并随提交落盘）
- [x] 新增独立 ADR 文件（为何 manifest+digest、tasks.md 移出、豁免通道改重锚协议）+ `adr/0026` 头部加 superseded-by 指针
- [x] 全仓 `grep -rn reviewed_sha`（不加 --include）收口清零（归档区除外；实测消费面 21 文件，含 `openspec/specs/openspec-170-followup/spec.md` 与 `docs/workflow-skills/sdflow-spec-review.md` 的 40 位格式句）；全量 pytest 绿
- [x] 票 1 收尾：本 change 自身 `spec-review-report.md` 锚已确认对 ship+归档生命周期正确并实跑 `ship_gate` 确认 design 域 CURRENT——**执行期修正：保留 40-hex 而非重锚 64-hex**（驱动 ship 的是运行 checkout 老门，读 64-hex 自锁 UNKNOWN(6)，实测证伪 task1.9 前提；40-hex 在 ship 期与归档后均安全，见 `impl-reports/planning-decisions.md`「执行期修正」节，双轴审两轴独立核验推理成立）

### Task 2: 归档面收敛 + CI 校验步

**Blocked-by:** none
**R-ID:** AV1, AV2（archive-validation：归档 tasks.md MUST 如实反映完成状态 / 归档面校验 MUST 由 CI 机械守）

把归档区 tasks.md 收敛到「如实反映完成状态」，并加一道 CI 机械门守住归档面校验。执行序不可颠倒（DT-6）：先本地全量收敛并 `validate --archived` 0 failed，再改 CI。

- [ ] 桶B 14 个 change：逐条对照 git log / 实现 commit 回填漏勾复选框（确未做的留 `- [ ]` + 说明）
- [ ] 桶A 2 个 tickets 管线 change（remove-superpowers-pipeline 0/21、sdflow-init-readwrite-paths 0/12）：对照 git log 逐条回填
- [ ] 桶C scoped-test-per-task：tasks.md 改写为无勾选框作废说明段（指明被 remove-superpowers-pipeline supersede、从未执行）
- [ ] 本地 `openspec validate --archived` 全量 0 failed
- [ ] `.github/workflows/mechanical-gates.yml`：openspec pin 1.5.0→1.9.0 + 新增 `validate --archived` 步；新步复用既有 openspec 泳道同一 `if` 条件（CLI 仅装于 ubuntu-latest×3.12），同步更新该泳道「断言 CLI 1.5.0 具体行为」注释
- [ ] 定点破坏自证：临时引入一个未勾复选框确认该步真红后还原（恒真锚防线）

### Task 3: 切片偏离对账接线（code-review Step1）

**Blocked-by:** none
**R-ID:** IO1（impl-orchestration：切片偏离审计行 SHALL 被代码审 scope 审计对账消费）

给 `sdflow-code-review` 的 scope 审计接上 `planning-decisions.md` 切片偏离对账，使出票期申报的偏离在代码审阶段被机械核对。

> 执行说明（并行安全）：本票与票 1 均改 `sdflow-code-review/SKILL.md`（本票动 Step1 输入清单，票 1 动 impl-review 重锚协议段，两节相隔）。Claude 宿主各票独立 worktree，编排层按号序 merge，`git merge --no-ff` 对相隔两节 3-way 干净合并、真冲突则 fail-loud（并行安全约束兜底）。见 `impl-reports/planning-decisions.md`。

- [ ] `sdflow-code-review/SKILL.md` Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行
- [ ] 对账逻辑三分支：静默偏离上报 / 已申报核对 / 无输入降级不中断

### Task 4: sdflow-spec/SKILL.md 判据下沉

**Blocked-by:** none
**R-ID:** DT-5（memo D7，无 spec delta）

按 DT-5 判据把 `sdflow-spec/SKILL.md` 可下沉小节移入 `references/`，把 SKILL 本体压回预算，既有 resident-contract 契约测试保持全绿。

- [ ] 按 DT-5 判据（可下沉 = 执行到该步才需展开的判据表/参考细节；不可下沉 = 流程骨架/铁律/fail-closed 分支）挑选 `sdflow-spec/SKILL.md` 可下沉小节 → `references/`（含路由句），本体 ≤16,000 字符（余量 ≥2,000）
- [ ] `pytest hack/tests/test_sdflow_spec_resident_contract.py` 全绿 + 全量 pytest 复核

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

全部功能票完成后，按「聚合套件发现契约」运行本 change 的聚合测试套件（单元+集成+e2e）并全部通过。本仓聚合套件命令由本票 implementer 依仓内既有约定判定并在 report 写明命令原文与判定依据（本仓无 `openspec/config.yaml` `test-suites` 段时）——本仓已知形态：单元/集成由 `pytest`（系统 python：`/usr/bin/python3 -m pytest`，见本仓测试环境事实）；e2e 层视仓内是否存在判定，无则记「未覆盖（本仓无此层）」+ 判定依据。证据落 `impl-reports/task5-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`），全部判「通过」的行锚同一最终 SHA。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
