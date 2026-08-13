# fix-workflow-bundle-staleness · Tasks

> 追溯锚：本 change `skip_specs: true`（无 Requirement ID），每任务标注 decision-memo 的 **D-编号**
> 双向追溯（D1-D10 ↔ 任务，无幽灵任务）。无新增测试计划（复用既有机械门），不产测试覆盖图。

## 1. bundle 核心规则修正

- [ ] 1.1 `spec-review.md`：:72「进 AskUserQuestion」改决策登记区口径〔D1〕；:29 删「`/clear` 后重审」〔D9〕；:91「brainstorming 自检」→「生成期自检」〔D9〕；:92 去 BASE 号段上界〔D6〕
- [ ] 1.2 `reference/README.md`：:18 quality-layering 描述改 P3c「每次全跑」口径〔D1〕；:17 删 Token_Saving 行〔D7〕；:6-8 部署观改 canonical 口径〔D9〕
- [ ] 1.3 `reference/quality-layering.md`：:25「/clear + sdflow-code-review」改独立编排器口径；:42 表行「官方 code-review」改 sdflow-code-review；:84 删 subagent-dev；:38「CR-01~09」去号段上界 `[spec-review-amendment A2]`；**保留** :14 出处标注〔D2/D6〕
- [ ] 1.4 `spec-checklists/spec-quality-base.md`:37「writing-plans」→「出 ticket」〔D2〕；`spec-checklists/README.md`:62 `rules/` 错路径 → `../`、:64 R 落点措辞现行化〔D9〕
- [ ] 1.5 `/review` 消费方统一改写（**8 处** `[spec-review-amendment A4]`）：`code-checklists/README.md`:3,13,**28**,53,68 + `code-review-base.md`:3 + `domains/llm.md`:5 + `trigger-catalog.md`:108〔D3〕

## 2. generation-process 收史 + ff-generation-constraints 外壳

- [ ] 2.1 `generation-process.md`：§二改现行两工具表（explore + /sdflow-spec），**含 :21 节标题行**（「三种对话相位 + 四个 skill」随正文同步）`[spec-review-amendment A8]`；§三整节移除、原位留一行指路 workflow-history A5（§四编号不重排）；§六「grill 是对话执行器」→「/sdflow-spec 相位 B 拷问」；**§四定点两处按 spec 回归** `[spec-review-amendment A11/A12]`——流水线图在 `/sdflow-spec` 与 `HARD-GATE 批准` 之间插一行 `↓ /clear → /sdflow-spec-review（阶段二设计审）`（锚 `openspec/specs/spec-workflow/spec.md:1604` 唯一线性路径字符串；只插一行，不重排图内其他行）+ :72「② 用户描述需求且**判断**需要开 change 时」删「判断」二字回归 spec :1608 措辞；**改后以 `pytest hack/tests/test_canonical_entry_sync.py` 核验 §四 presence 三对断言（六子串）逐字保留**（勿凭记忆 grep「四短语」）`[spec-review-amendment A9]`〔D4〕
- [ ] 2.2 `workflow-history.md` 新增 A5 条目承接 §三论证考古〔D4〕
- [ ] 2.3 `ff-generation-constraints.md`：标题改「生成起手强制规范（FF-0 + D-1~D-6）」；定位声明与调用方示例改 /sdflow-spec 语境（保「或 /opsx:ff 直呼」）；`@openspec/workflow/` 路径表述改 canonical；背景/历史节不动〔D5〕

## 3. reference 处置 + 同族面治

- [ ] 3.1 `Spec_Quality_Collaboration.md` 顶部加历史横幅〔D7〕；`Spec_Quality_Methodology.md` 顶部加 L1 历史举例标注〔D8〕
- [ ] 3.2 `git mv reference/Token_Saving_Strategies.md docs/`，移动后顶部加「个人历史笔记（superpowers 时代），不代表现行工作流」横幅 `[spec-review-amendment A6]`〔D7〕
- [ ] 3.3 `reference/PRD_vs_Spec.md`:27,64,104,112 opsx:ff 举例 → sdflow-spec；另顶部加历史举例标注（D8 同款——:33/37/68/70/79/97/113 的 plan-ceo-review/autoplan/brainstorming 为历史工具名）`[spec-review-amendment A5]`〔D9〕
- [ ] 3.4 `config.template.yaml`:23-27 去号段 + blurb 现行化；`snippets/index-section.md` **按内容定位改 6 行** `[spec-review-amendment A1：memo D6/D9 的 :13,15,16 行号错位勘误 + 面扩]`——:10（`ff+grill`→现行阶段口径、`subagent-dev`→`sdflow-implement`、删「去 /clear」改「两处阶段交界 `/clear`」口径）、:11（TG-01~28 去上界）、:12（`opsx:ff` blurb 随 D5 改 /sdflow-spec 语境）、:13（brainstorming/grill 三相位现行化）、:18（BASE-01~30 去上界）、:19（CR-01~09 去上界）；`docs/sdflow-fable5/02-module-reference.md`:160（TG-01~26 去上界）`[spec-review-amendment A3]`〔D6/D9〕
- [ ] 3.5 本仓 `openspec/config.yaml` 与 template 同款行手动同步，diff 对照确认无分叉〔D9〕

## 4. 收尾门与复扫

- [ ] 4.1 `python3 hack/sync_principles.py --check` + `python3 hack/gen_workflow_guide.py --check` 均绿〔D10〕
- [ ] 4.2 `python3 sdflow-init/scripts/init.py update --root .` 刷本仓 INDEX/GUIDE 镜像〔D10〕
- [ ] 4.3 全仓 `/usr/bin/python3 -m pytest -W error` 全绿〔D10〕
- [ ] 4.4 Success Metrics 复扫：memo C4/C8 grep 清单 0 残留（C4 按 **8 处**口径；复扫面含 index-section :10-:19、quality-layering:38、docs/sdflow-fable5:160 增补位点 `[spec-review-amendment]`）；**三处**矛盾对读口径一致（P3c / G2 / index-section「去 /clear」vs workflow.md:134）〔D1/D10〕
