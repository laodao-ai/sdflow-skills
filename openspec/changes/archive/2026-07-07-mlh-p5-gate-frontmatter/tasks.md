# Tasks — mlh-p5-gate-frontmatter

> 全部任务追溯 spec-workflow「阶段三编排台账确定性（ship_gate）」（MODIFIED）。
> 迁移顺序遵 design.md「Migration Plan」——dual-read 先行保证任意中间态可用；TDD 先写失败测试；新解析路径 fail-closed + pytest 坏输入断言非零（adr/0006 R3）。

## 0. spec-review-amendment 必办（冷审拦下 1 致命 + 3 高，MUST 优先）

- [x] 0.1〔D1 致命〕产出 **live 结论读点完整清单**：审 ship_gate.py 全部 live inline 读点 = `anchors_in`(design-approved) + `pick_exclusive`×3(verify 早检 519/终门 588、code-review 563) + peek `anchors_in`(576) + `anchor_set`熔断 helper(250)。frontmatter 化/退役范围 MUST 覆盖全部，MUST NOT 只动 `anchors_in`（否则 verify/code-review 迁后读不出 → STEP_IN_PROGRESS 永卡）。
- [x] 0.2〔D2 高〕手写解析器契约钉死：只认文件第 1 行 `---`（去 BOM）起唯一首块、`splitlines()` 口径、正文 `---`/`ship-gate:` 不参与。测试含「正文含多处 `---` 横线的真实旧报告」+「body 注入 `ship-gate: verify: PASS`」负例。
- [x] 0.3〔D3 高〕坏输入→退出码映射表落实现 + 测试：越域/重复键/坏语法/类型不符 → UNKNOWN(6)；纯缺字段 → 既有无锚语义(REFUSE_START 3 / STEP_IN_PROGRESS 0)。坏≠无键：坏 frontmatter 永不回退 inline。
- [x] 0.4〔D4 高〕单一自持 helper `parse_ship_gate_frontmatter_text(text)`，live 读与归档 `git show` 文本读都调它（防漂移）；归档坏 frontmatter → fail-safe none 不回退。
- [x] 0.5〔D12〕fail-closed reason 携带被拒字段名 + 失败类别，测试断言 reason 含缺陷标识。
- [x] 0.6〔Q2 P0 决策门〕**写任何 producer 前**实测 `openspec validate`/`archive` 对带 `ship-gate:` frontmatter 的样例报告，拿 GO/NO-GO。

## 1. 起手核实（现状核查，不改行为）

- [x] 1.1 核三报告模板现状：`sdflow-spec-review`（拍板回写）/`sdflow-done`（verify 模板）/`sdflow-code-review`（报告格式）现有报告是否已带 YAML frontmatter；迁入 `ship-gate:` 键后 `openspec validate` 是否受影响（Open Q2）。
- [x] 1.2 ~~核解析选型~~ **grill 已决 = 手写 stdlib**（D3：ship_gate 零依赖不变量、门禁不崩）：本步改为确认手写解析器实现边界（`---` 界定 + 顶层 `ship-gate:` 键 + 一层标量），MUST NOT `import yaml`。
- [x] 1.3 核 `ship_gate.py` 中 live 读半场（`anchors_in` 对 live 文件）与归档读半场（`archived_verify_state:151/485`）的调用边界，标出「退役 live / 保留归档」的精确删除点。

## 2. gate frontmatter 解析 + dual-read（读侧先行，零破坏）

- [x] 2.1 写失败测试：gate 对 live 报告 frontmatter（`ship-gate.design_approved/verify/code_review`）解析出正确结论（`test_frontmatter_state_parse`）。
- [x] 2.2 实现 `ship_gate.py` **手写 stdlib** frontmatter 解析路径（不 import yaml）：读 live 报告 `ship-gate:` 键 + 严格枚举校验（`verify∈{PASS,FAIL}`/`code_review∈{pass,blocked}`/`design_approved` bool）。
- [x] 2.3 写失败测试（G4 攻击面穷举）：坏 frontmatter 各分支——① `---` 界定缺失/不配对；② 顶层 `ship-gate` 或同字段**重复键**（须**显式判 UNKNOWN，MUST NOT 静默取最后一个**）；③ tab/混合缩进；④ 值越域 `verify: MAYBE`；⑤ 类型不符 `design_approved: yes` → 均 fail-closed 判「无有效状态」，断言非零 / 判定不能（`test_frontmatter_fail_closed`）。
- [x] 2.4 实现 fail-closed 兜底：解析失败/越域/缺字段 → 判无有效状态，gate 停下报告或判该步进行中，绝不静默过门。
- [x] 2.5 写失败测试 + 实现 dual-read：**live** 读 frontmatter（过渡期 frontmatter 优先→无键回退 inline，G3 渐进）；**归档** frontmatter 优先→无则回退 inline（G2 双读，新归档 frontmatter / 旧归档 inline）。producer 未迁时零破坏（`test_dual_read_live_and_archived`）。

## 3. 三 producer SKILL 迁移（写侧）

- [x] 3.1 `sdflow-spec-review`：拍板回写改写报告 frontmatter `ship-gate.design_approved: true`（替代 inline `<!-- ship-gate: design-approved -->`）。
- [x] 3.2 `sdflow-done`：verify 模板改写 frontmatter `ship-gate.verify: PASS|FAIL`。
- [x] 3.3 `sdflow-code-review`：报告格式改写 frontmatter `ship-gate.code_review: pass|blocked`。
- [x] 3.4〔D8/D9 订正〕每 producer 迁移拆细：(a) 头部 frontmatter prepend/merge 写入（非追加末尾，D9）；(b) 正文保留人读结论行；(c) 更新交叉引用（尤其 spec-review〔SR-M〕lens-metric 锚仍在正文注释、拍板时头 frontmatter + 正文注释两处各写）；(d) `ship_gate.py` docstring 契约块 ↔ `test_anchor_contract.py` 双向钉死同步。契约测试 MUST 断言**精确字段名**（`design_approved`/`verify`/`code_review` 下划线，防与锚字面 `code-review` 连字符漂移）+ 枚举值；**producer 模板改动与其契约断言同 commit**。

## 4. 契约测试迁移 + 归档兼容 + 正文免疫

- [x] 4.1〔D6 spec-review-amendment，盘面订正〕**审计全部 8 个 `test_gate_*` 文件**（freshness/tail/anchor_scope/terminal/breaker/anchor_contract/preflight/impl_progress，~45 处 inline fixture），逐 fixture 标「live→迁 frontmatter / 归档→留 inline」，迁移前后 fixture 计数作退役 DoD。迁 `test_anchor_contract.py`（断言三 producer frontmatter 字段 + gate 读出）；~~移除 `test_producer_parser_contract.py`~~ → **收尾 T10 裁决改为保留**（该文件验 `TAG_RE` 现行行为，删则丢覆盖；"错配"仅指无 ship-gate 锚可迁、应移出迁移范围而非删除；superpowers-plan 已订正为"不动它"）。
- [x] 4.2 写测试：归档**双读**兼容（G2），**基于行为、MUST NOT 硬编码 88/168 或全量扫 archive/**〔D13〕——(a) 构造**旧 inline** archived fixture → `archived_verify_state` 识别 verify=PASS、SHIPPED 不回归（`test_archived_inline_read`）；(b) 构造**新 frontmatter** archived fixture `ship-gate.verify: PASS` → 归档 frontmatter 读识别、SHIPPED 不回归（`test_archived_frontmatter_read`）；(c) 归档坏 frontmatter → fail-safe none 不 SHIPPED——**MUST NOT 只读 inline**（否则新归档 SHIPPED 回归）。
- [x] 4.3 写测试：live 报告正文任意提及锚字面（描述句/对账清单/fence 内示例/独占一行）不参与 live 解析（B4/B5 根治，`test_live_body_mention_immune`）——frontmatter 无字段时正文提及 → design-approved 判 REFUSE_START。
- [x] 4.4 迁移 B5 聚合语料测试到 frontmatter（live 侧）+ 保留归档 inline 语料（归档侧）。
- [x] 4.5 写测试：归档未闭合 fence 隔断互斥 inline 锚对 → `archived_verify_state` 保守判 `none` 不假 SHIPPED（归档读半场语义保留，`test_archived_unclosed_fence`）。

## 5. 退役 live 解析半场（收尾，依赖 3+4 全绿）

- [x] 5.1〔D1/D11 订正〕确认三 producer 全迁 + 第 2/4 组测试全绿后，退役**全部 live inline 读点**（0.1 清单：`anchors_in`-design + `pick_exclusive`×3 + peek `anchors_in` + `anchor_set`熔断 helper 迁「状态集合」解析）；`_line_scoped_hits` 归档读半场保留。同步更新 `sdflow-ship/SKILL.md` 熔断文案 + `test_gate_breaker.py`（before 无状态、after 仅 frontmatter PASS → 判有进展）。
- [x] 5.2 保留 `archived_verify_state` 的归档读 `_line_scoped_hits`（冷审 F2 永久保留）；脚本头注释更新「live 读 frontmatter / 归档读 inline」分流说明 + 「已知不覆盖」清单同步。
- [x] 5.3〔D10 订正〕全仓 `pytest` 回归全绿；`ship_gate.py` 无 live inline 解析残留；**把 mlh-p5 自身 spec-review-report / verify-report / code-review-report 的 inline 锚迁为 frontmatter**（合法迁移收尾、非越权补锚——本 change 自身报告用旧 inline 拍板，退役后 gate 只读 frontmatter 会 REFUSE on itself）；dogfood：自身报告用 frontmatter 跑一遍 gate 验证闭环。
- [x] 5.4〔D10 symlink 窗口纪律〕Migration 执行顺序：先落 gate dual-read commit + 本地 `bash setup.sh` 生效，再改 producer SKILL（skill 全局 symlink 即时生效，改 sdflow-done/ship_gate 的中途窗口会波及并发 /sdflow-done；分步提交缩窗口）。

## 6. 收尾同步

- [x] 6.1 回填 roadmap「阶段 5」前置区 F6 订正（归档锚实测 88 文件/168 锚行，非 ~39）+ task-log「阶段 5 完成总结」。
- [x] 6.2 `openspec validate mlh-p5-gate-frontmatter` 通过；spec delta 与终审后代码实况一致。
