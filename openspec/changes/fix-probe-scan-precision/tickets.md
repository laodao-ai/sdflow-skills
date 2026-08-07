---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自本 change `design.md` 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- **P0 四项 MUST 同批落地**：resolver 删步① · `copy_bundle` 停铺 tools/contract · 两个 SKILL 删探测段 · 对应测试——缺任一则新旧语义混态（SKILL 仍探测但副本已不铺 ⇒ 每仓永久硬停）。
- **Migration Plan 步序不可颠倒**：步 1（删 SKILL 探测段）必须在步 3（停铺 tools）之前——反序（先停铺、SKILL 仍探测）会让存量 pin 仓在失效提示下硬停。
- **`spec-workflow` 安全红线**：`sdflow-init update` MUST NOT 自动删除消费仓既有规则文件。仅告警。无豁免。
- **概念词表 sweep 归零词**（`local-pin` · `两条分发链` · `显式 pin` · `pin 遮蔽`）全仓 grep **不带 `--include` 限定** 归零，豁免表显式列出。
- **必红测试集一律以 pytest 实跑红名单为准**，MUST NOT 以 grep 零命中推断「无消费者」。
- **sane() 扩面 MUST 是形状级判据**：`tools/` 目录存在且非空 + `lens-metric-contract.md` 非空——MUST NOT 枚举具体 `.py` 成员。
- **resolver 退出码集不变**（`0` / `2` / `64`），MUST NOT 新增码位。
- **GUIDE 保留铺设（D14）**：`WORKFLOW-GUIDE.md` 照旧铺进消费仓。
- **告警文案 SHALL 带前置条件**（「若刚 `git pull` 还没跑 `bash setup.sh`，先跑 setup 再判断」），MUST NOT 用无条件绝对断言。
- **`--dev` 退役留 tombstone**：识别到参数 → fail-loud 提示退役（否则老用法只得 argparse generic error）。
- **DOC-1**：正文即最终态，演进史进附录。
- **基准 5**：无界语法禁手搓。本 change 不新增任何解析器。
- **`adr/0038` 删除**（本分支新建、从未进 main），候选与砍因写进 0039 取舍段——引用砍因 MUST 写「起手前提被证伪 ⇒ 决策撤销」，MUST NOT 写「问题域消失」（F32）。
- **`ship_gate` 腿退役理由 MUST 按仓型分开写**：toolkit 源仓——顶层腿覆盖；消费仓——镜像不复存在。MUST NOT 用「顶层腿覆盖」概括消费仓。
- **托管块权威源改动 MUST 改源**（`sdflow-init/assets/snippets/claude-section.md`），MUST NOT 直改本仓 CLAUDE.md 托管块——会被下次 update 覆写回。
- **`hack/tests/test_async_branch_parity.py` marker 区间**：两个 SKILL 的 `sdflow:async-branch` 区间受逐字节等值门约束，MUST 两文件同改。
- **GUIDE 生成器链接降级**：`hack/gen_workflow_guide.py` 把指向 sibling 规则文件的相对链接降为文字引用或内联对应小节——消费仓只有 GUIDE 一个文件，相对链接全断链。
- **删本仓镜像 MUST 与两处硬编码引用同批**：`hack/tests/test_yq_wrapper_consistency.py` 的 `TARGETS` + `hack/check_encoding_hygiene.py` 的镜像排除分支。

### Task 1: 删除两个评审 SKILL 的 skew 探测段

**Blocked-by:** none
**R-ID:** R1 (host-adaptive-execution REMOVED)

删除 `sdflow-code-review/SKILL.md` 与 `sdflow-spec-review/SKILL.md` 第零步的 skew 探测整段（code-review 四条信号、spec-review 两条信号），及其产生的悬空指代（档位解析步引用已删段的「三处均为…」措辞）。保持 `exit 2` 既有降级分支不变。

两个 SKILL 的 `sdflow:async-branch` marker 区间受 `hack/check_async_branch_parity.py` 逐字节等值门约束——MUST 两文件同改。区间内「两条分发链」措辞订正为单链表述（`manifest skew` 的修法保留）。`hack/tests/test_async_branch_parity.py` 的断言同批改写为新文案关键词。

- [x] 删除 `sdflow-code-review/SKILL.md` skew 探测整段，步序号顺延
- [x] 删除 `sdflow-spec-review/SKILL.md` skew 探测整段，步序号顺延
- [x] 清理档位解析步悬空指代（改写为不引用已删段）
- [x] 逐字比对确认两个 SKILL 的 `exit 2` 降级分支未被误改
- [x] `sdflow:async-branch` 区间内「两条分发链」→ 单链表述，两文件同改
- [x] `hack/tests/test_async_branch_parity.py` 断言同批改写
- [x] 验收 grep：`grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md` 命中数恰为各文件 1 处（anchor_lint 自检段合法引用）

### Task 2: resolver 收缩两步链 + 停铺 tools + 退役 --dev/full

**Blocked-by:** 1
**R-ID:** R2 (spec-workflow MODIFIED 规则解析), R3 (spec-workflow MODIFIED bundle 下发)

P0 核心：在 bundle 权威源 `sdflow-init/assets/hack/resolve-workflow.sh` 删除步①（本地 pin 判定），使规则解析只剩两步链（全局 canonical → 显式降级）。同批在 `sdflow-init/scripts/init.py` 删除 `copy_bundle` 的 tools/contract 铺设逻辑（只保留 GUIDE + schema）、退役 `--dev` 与 `full=True` 分支（`--dev` 留 tombstone fail-loud）。`sane()` 扩面追加 `tools/` 非空 + contract 非空两条形状级检查。配套测试全面改写——以 `pytest` 实跑红名单为准。

- [x] 删除 resolver 步①（本地 pin 判定），头部契约注释同批订正为两步链
- [x] 确认退出码集不变（0/2/64），`--root`/`--explain`/`SDFLOW_HOME` 入参契约保留
- [x] `sane()` 扩面：`tools/` 存在且非空 + `lens-metric-contract.md` 非空（形状级，不枚举 `.py` 成员）
- [x] `init.py` `copy_bundle()`：删 tools/contract 铺设，只保留 GUIDE + schema；GUIDE `copy2` 前加 `os.makedirs(dst, exist_ok=True)`
- [x] 退役 `--dev` argparse + toolkit 仓根守卫 + `stale_shadow_warnings` 豁免；留 tombstone fail-loud
- [x] 删除 `full=True` 分支 + `ignore_tools_tests()` + `LOCAL_TOOL_CACHES`
- [x] resolver 测试：新增「仓内放全套规则副本，断言仍解析到全局 canonical」反向锚
- [x] resolver 测试：`SDFLOW_HOME` 指向自备 canonical 正常解析（既有测试隔离契约）
- [x] `sane()` 反向锚：canonical 缺 `tools/` 或 contract → `exit 2`
- [x] 所有「造假 canonical 过 sane()」的 fixture 同步补 `tools/` + contract
- [x] init 测试：断言 `init` 后消费仓 `openspec/workflow/` 下只有 `WORKFLOW-GUIDE.md`（文件全集断言）
- [x] init 测试：断言 fresh init（裸 `tmp_path`）不抛异常
- [x] 先跑 pytest 看红名单，逐个改写/删除，不留与新契约矛盾的绿测试

### Task 3: 告警语义改写（stale_shadow_warnings + maintain_scan）

**Blocked-by:** 2
**R-ID:** R4 (spec-workflow MODIFIED 残留副本须告警), R5 (maintain-scan MODIFIED)

`init.py` `stale_shadow_warnings()` 判据扩员（原 `RULE_MARKERS` 三项之外增查残留 `tools/` + `lens-metric-contract.md`）+ 文案改为带前置条件的死件表述 + 可复制删除命令。清理 checkpoint 孤儿告警的旧 pin 措辞。`sdflow-maintain` 兜底扫描同步改写。

- [ ] `stale_shadow_warnings()` 判据扩员 + 新文案（带前置条件 + 可复制删除命令）
- [ ] 清理 checkpoint 孤儿告警的 pin 措辞
- [ ] `sdflow-maintain` `test_maintain_scan.py` 按新语义断言反转（tools-only 残留 → 报死件告警）
- [ ] 文案测试正反双断言：不含 `显式 pin`/`遮蔽全局`，含新死件文案关键词与前置条件提示

### Task 4: ship_gate 腿退役 + 死件清理 + 文档面级订正

**Blocked-by:** 2,3
**R-ID:** R6 (spec-workflow MODIFIED bundle 下发后果), R7 (encoding-hygiene), R8 (yq-yaml-operations), R9 (workflow-metrics)

退役 `ship_gate.py` 的 `tools_spec` 比较腿（正向锚 + 反向锚）。删除本仓 `openspec/workflow/` 下 7 个文件（6 tools + contract）。同批处理两处硬编码引用（yq TARGETS + encoding hygiene 排除分支）。GUIDE 生成器链接降级。托管块权威源 + 本仓 CLAUDE.md/AGENTS.md 非托管区 + ADR + docs + CONTEXT + 修法文案面——全部按 sweep 命中处置。记 todo（4 条，用开发 checkout 脚本、显式传 change 字段）。

- [ ] `ship_gate.py`：删 `tools_spec` 比较腿，退役理由注释按仓型分开写
- [ ] 正向锚：改 `sdflow-init/assets/workflow/tools/` 下文件，失鲜仍为 stale
- [ ] 反向锚：fixture 仓在 `openspec/workflow/tools/` 造文件 → 判 fresh（腿真退役）
- [ ] 删本仓 `openspec/workflow/` 下 7 个文件（只留 GUIDE）
- [ ] `hack/tests/test_yq_wrapper_consistency.py` 删镜像条目
- [ ] `hack/check_encoding_hygiene.py` 删不可达排除分支 + 测试改写
- [ ] 托管块权威源 `claude-section.md` 订正 + 对本仓跑 `sdflow-init update` 刷新
- [ ] `CLAUDE.md` 非托管区四处订正 + `AGENTS.md` 四处同义描述订正
- [ ] 修法文案面统一口径（lens_metric_emit / resolve-models / sdflow-upgrade / README）
- [ ] docs 面按 sweep 命中处置
- [ ] ADR 面：0003/0005/0019/0036 状态注记 + 0038 删除 + 0039 新落（含回滚步骤）
- [ ] `openspec/CONTEXT.md` 补 skew 术语 + T269 分治关闭 + T270 关闭
- [ ] `hack/gen_workflow_guide.py` 链接降级 + 重新生成 GUIDE
- [ ] 记 4 条 todo（hack 链 symlink 化 / resolver --help / setup.sh skipped 非零退出 / Windows 失鲜 CI）

### Task 5: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task5-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
