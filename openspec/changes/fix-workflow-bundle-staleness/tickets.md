---
impl-pipeline: tickets
---

## Global Constraints

逐字摘自 design.md 与 decision-memo.md 的硬约束：

- **Goals 边界**：每处修改是「措辞替换 / 整节移史 / 加横幅 / 移文件」四种操作之一；不引入任何新机制、新文件（workflow-history A5 条目除外）、新路径。
- **Non-Goals**：不重构 bundle 目录结构；不改 `workflow.md` 正文与任何机读块；不逐处改写 `Spec_Quality_Methodology.md` 的 5 处历史举例（仅顶部标注）；不触发消费仓 update。不为「号段漂移」新增机械守卫。
- **D4 MUST 保住** §四被 `test_canonical_entry_sync.py` 钉住的措辞（「推荐流水线」「唯一入口」「模型 SHALL 在以下情形自动 invoke」「模型 MUST NOT 自主判断」）——改后以 `pytest hack/tests/test_canonical_entry_sync.py` 核验六子串逐字保留。
- **D5 `ff-generation-constraints.md` 背景/历史节原位保留**，不收进 workflow-history。
- **D7 `Token_Saving_Strategies.md` git mv 不直接删除**（人未拍板删除，移动可逆）。
- **D8 `Spec_Quality_Methodology.md` 仅顶部标注**，不逐处改写举例（通则④最简方案）。
- **`quality-layering.md:14` 出处标注保留**（「设计脉络借鉴自已退役的 superpowers subagent-driven-development」——有意 provenance 标注，非失鲜）。
- **`spec-quality-base.md:7` 来源行保留**（provenance 非失鲜）。
- **A7 memo C3 证据锚失实已勘误**——writing-plans 退役真实锚 = `openspec/changes/archive/2026-08-12-remove-superpowers-pipeline/`（非 memo 原引的 CLAUDE.md 段落）。
- **A11 generation-process §四流水线图只插一行**（`↓ /clear → /sdflow-spec-review（阶段二设计审）`），不重排其他行；`test_canonical_entry_sync.py` docstring 明文「不锚跨行 ASCII 图」。
- **A12 自动触发规则 ② 只删「判断」二字**回归 spec:1608 措辞，不改写为其他措辞。
- **index-section.md 修正须在 `init.py update` 之前**（否则把失鲜行重新灌回 INDEX.md）。
- **收尾门序列**：`sync_principles --check` → `gen_workflow_guide --check` → `init.py update --root .` → 全仓 `/usr/bin/python3 -m pytest -W error`。

### Task 1: bundle 核心规则修正（spec-review / quality-layering / checklists / trigger-catalog）

**Blocked-by:** none
**R-ID:** D1, D2, D3, D6, D9

修正 bundle 核心规则文件中的两处正面矛盾（P3c / G2）、退役机制残留（subagent-dev / writing-plans / 官方 code-review / `/clear +` 措辞）、`/review` 消费方统一改写（8 处）、号段去上界，具体位点：

- `spec-review.md`：:72 AskUserQuestion→决策登记区；:29 删「`/clear` 后重审」；:91 brainstorming→生成期自检；:92 去 BASE 号段上界
- `reference/README.md`：:18 quality-layering 描述改 P3c 口径；:17 删 Token_Saving 行；:6-8 部署观改 canonical 口径
- `reference/quality-layering.md`：:25 `/clear +` 措辞改独立编排器口径；:42 表行改 sdflow-code-review；:84 删 subagent-dev；:38 `CR-01~09` 去上界；**保留 :14 出处标注**
- `spec-checklists/spec-quality-base.md`：:37 writing-plans→出 ticket；`spec-checklists/README.md`：:62 `rules/` 错路径→`../`、:64 R 落点现行化
- `/review` 消费方 8 处统一改写：`code-checklists/README.md`:3,13,28,53,68 + `code-review-base.md`:3 + `domains/llm.md`:5 + `trigger-catalog.md`:108

- [ ] 全部位点按 D1/D2/D3/D6/D9 改写完毕，无遗漏
- [ ] 改后 `quality-layering.md:14` 出处标注仍在
- [ ] 改后 `spec-quality-base.md:7` 来源行仍在

### Task 2: generation-process 收史 + ff-generation-constraints 外壳更新

**Blocked-by:** none
**R-ID:** D4, D5

`generation-process.md` 按 DOC-1 收史（§二现行化 + §三移入 workflow-history A5 + §六措辞 + §四定点两处 spec 回归）、`ff-generation-constraints.md` 外壳更新，具体位点：

- `generation-process.md` §二改现行两工具表（explore + /sdflow-spec），含 :21 节标题行同步 `[A8]`
- §三整节移除、原位留一行指路 workflow-history A5（§四编号不重排）
- §六「grill 是对话执行器」→「/sdflow-spec 相位 B 拷问」
- §四流水线图在 `/sdflow-spec` 与 `HARD-GATE 批准` 之间插一行 `↓ /clear → /sdflow-spec-review（阶段二设计审）` `[A11]`
- §四 :72 自动触发规则 ② 删「判断」二字 `[A12]`
- 改后跑 `pytest hack/tests/test_canonical_entry_sync.py` 核验 presence 六子串逐字保留 `[A9]`
- `workflow-history.md` 新增 A5 条目承接 §三论证考古
- `ff-generation-constraints.md`：标题改「生成起手强制规范（FF-0 + D-1~D-6）」；定位声明与调用方示例改 /sdflow-spec 语境（保「或 /opsx:ff 直呼」）；`@openspec/workflow/` 路径表述改 canonical；背景/历史节不动

- [ ] `generation-process.md` §二/§三/§六按 D4 改写完毕
- [ ] §四流水线图正确插入阶段二行，其余行未变
- [ ] §四 ② 已删「判断」二字，其余措辞未变
- [ ] `pytest hack/tests/test_canonical_entry_sync.py` 全绿（presence 六子串保留）
- [ ] `workflow-history.md` A5 条目已新增
- [ ] `ff-generation-constraints.md` 按 D5 更新完毕，背景/历史节未动

### Task 3: reference 处置 + 同族面治 + config 同步

**Blocked-by:** none
**R-ID:** D6, D7, D8, D9

reference 文件处置（横幅/标注/移动）、同族失鲜面治（index-section / config.template / config.yaml / docs），具体位点：

- `Spec_Quality_Collaboration.md` 顶部加历史横幅
- `Spec_Quality_Methodology.md` 顶部加 L1 历史举例标注（仅标注，不逐处改写）
- `git mv reference/Token_Saving_Strategies.md docs/` + 移动后顶部加历史横幅 `[A6]`
- `PRD_vs_Spec.md`:27,64,104,112 opsx:ff→sdflow-spec + 顶部历史举例标注 `[A5]`
- `config.template.yaml`:23-27 去号段 + blurb 现行化
- `snippets/index-section.md` 按内容定位改 6 行（:10/:11/:12/:13/:18/:19）`[A1]`
- `docs/sdflow-fable5/02-module-reference.md`:160 去号段上界 `[A3]`
- 本仓 `openspec/config.yaml` 与 template 同款行手动同步，diff 对照确认无分叉

- [ ] reference 三文件横幅/标注均已添加
- [ ] `Token_Saving_Strategies.md` 已 git mv 至 `docs/` 且有历史横幅
- [ ] `PRD_vs_Spec.md` 4 处 opsx:ff 已改 + 顶部标注已加
- [ ] `index-section.md` 6 行全部按 A1 修正
- [ ] `config.template.yaml` 号段去上界 + blurb 现行化
- [ ] `openspec/config.yaml` 与 template 同款行一致（diff 对照）
- [ ] `docs/sdflow-fable5/02-module-reference.md`:160 号段已改

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按收尾门序列运行全量验证并记录证据，同时复扫 Success Metrics 的 grep 清单确认 0 残留。

收尾门序列：
1. `python3 hack/sync_principles.py --check`
2. `python3 hack/gen_workflow_guide.py --check`
3. `python3 sdflow-init/scripts/init.py update --root .`（刷 INDEX/GUIDE 镜像）
4. 全仓 `/usr/bin/python3 -m pytest -W error`
5. Success Metrics 复扫：memo C4（8 处 `/review` 残留）/ C8（号段漂移）grep 清单 0 残留，含 A1-A3 增补位点
6. 三处矛盾对读口径一致（P3c / G2 / index-section「去 /clear」vs workflow.md:134）

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
