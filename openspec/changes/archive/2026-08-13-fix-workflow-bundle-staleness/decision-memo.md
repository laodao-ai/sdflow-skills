---
schema_version: 1
change: fix-workflow-bundle-staleness
branch: feat/fix-workflow-bundle-staleness
generated_at: 2026-08-13T09:42:12+08:00
decision_hash: f87f5d3a1b85
---

# 决策纪要 · fix-workflow-bundle-staleness

## 目标态

workflow bundle（`sdflow-init/assets/workflow/`）全部 md 与现行工作流口径一致：无正面矛盾、无退役机制残留、无旧入口时代措辞；非 bundle 内容（个人使用笔记）移出；同族失鲜（index-section / config.template / 本仓 config.yaml blurb）一并面治。**只改文字与文件归属，不动结构、不动路径、不动规则语义。**

## 拍板决策

- **D1 两处正面矛盾按现行口径改写** — `reference/README.md:18`（quality-layering 描述仍是被 P3c 否决的「缩成高风险残差」旧结论）与 `spec-review.md:72`（「进 AskUserQuestion」vs G2 决策登记区）按 P3c/G2 现行口径改写；依据：现行口径有归档 change 与机械测试锚，旧口径无任何支撑。**砍掉的候选**：无（单方案）。
- **D2 退役机制残留清理** — `quality-layering.md:84` 删 subagent-dev（adr/0042 后 tickets 唯一管线）；`:42` 表行「官方 code-review」改指 sdflow-code-review（P3d 已弃用官方独立 step）；`:25`「事后 `/clear + /sdflow-code-review`」改独立编排器口径（G1）；`spec-quality-base.md:37`「writing-plans 前尤为有用」改「出 ticket 前尤为有用」。**保留** `quality-layering.md:14` 的「设计脉络借鉴自已退役的 superpowers subagent-driven-development」——那是有意的出处标注，非失鲜。
- **D3 `/review` 消费方统一改写** — 全部改为「sdflow-code-review（+ sdflow-implement Standards 轴必填槽）」：`code-checklists/README.md:3,13,53,68`、`code-review-base.md:3`、`domains/llm.md:5`、`trigger-catalog.md:108`。
- **D4 generation-process.md 按 DOC-1 收史** — §二改为现行两工具表（explore 发散 + /sdflow-spec 澄清拷问生成）；§三（grill 价值反超 brainstorming 论证）整节移入 `workflow-history.md` 新增 A5 条目；§六「grill 是对话执行器」改「/sdflow-spec 相位 B 拷问」。**MUST 保住** §四被 `test_canonical_entry_sync.py` 钉住的措辞（「推荐流水线」「唯一入口」「模型 SHALL 在以下情形自动 invoke」「模型 MUST NOT 自主判断」）。
- **D5 ff-generation-constraints.md 外壳更新** — 标题改「生成起手强制规范（FF-0 + D-1~D-6）」；定位声明与调用方示例改 /sdflow-spec 语境（保留「或 /opsx:ff 直呼」兼容提法）；`@openspec/workflow/` 路径表述改 canonical 口径。文末「背景」「历史」节**原位保留**（已是文末历史节，不混正文）。**砍掉的候选**：整节收进 workflow-history（成本高于收益，节本身已自我隔离）。
- **D6 号段硬编码一律去上界** — `config.template.yaml:23`（TG-01~24，实到 28）`:24` + `openspec/config.yaml:6,8`（BASE-01~28，实到 30）+ `index-section.md:16`（TG-01~28）+ `spec-review.md:92`（BASE-01~28）改为不带号段上界的表述。依据：号段漂移已实证两处发生（24→28 漏、28→30 漏），删数字后无漂移面。**砍掉的候选**：改成当前正确号段（下次新增又漂，同一失效模式复发）。
- **D7 reference 两份处置** — `Spec_Quality_Collaboration.md` 顶部加历史横幅（不移动：README 已标「历史分析」，`spec-review.md:34` 的引用保持有效）；`Token_Saving_Strategies.md` git mv 至 `docs/` + 删 `reference/README.md:17` 行（唯一引用面，已 grep 实证）。**砍掉的候选**：Token_Saving 直接删除（人未拍板删除，移动可逆）。
- **D8 Methodology 轻标注** — `Spec_Quality_Methodology.md` 顶部加一行「L1 举例为历史工具名（brainstorming/autoplan），现行对应 /sdflow-spec 与评审编排器」，不逐处改写 5 处举例。依据：通则④最简方案，L3 框架本身不受举例影响。**砍掉的候选**：逐处改写（成本高、举例在框架语境里无害）。
- **D9 同族面治** — `index-section.md:13`（brainstorming/grill 三相位）`:15`（ff+grill、subagent-dev）+ `config.template.yaml:27` + 本仓 `openspec/config.yaml:5-11` 同款行手动同步（update 不覆盖 config.yaml，已实证「update 保持 config.yaml」）；`reference/README.md:6-8` 部署观改 canonical 口径；`spec-review.md:29`「/clear 后重审」删除；`spec-review.md:91`「brainstorming 自检」改「生成期自检」；`PRD_vs_Spec.md:27,64,104,112` opsx:ff 举例改 sdflow-spec。
- **D10 收尾门** — 全仓 `/usr/bin/python3 -m pytest -W error` + `gen_workflow_guide --check`（workflow.md 未动，应绿）+ `init.py update --root .` 刷 INDEX/GUIDE 镜像。

## 承重约束

- **C1 P3c 矛盾属实** — 验证方式：并读两文件；**证据锚**：`reference/README.md:18`「事后 sdflow-code-review 缩成高风险残差」vs `reference/quality-layering.md:59-66` §五「〔grill-amendment / P3c〕此推论已被否决……每次全跑·独立冷·强制主审」。
- **C2 G2/G1 矛盾属实** — 验证方式：并读；**证据锚**：`spec-review.md:72`「置信中 → 进 AskUserQuestion」vs `workflow.md:86` G2「中途不弹窗，写进报告决策登记区」；`spec-review.md:29`「`/clear` 后重审」vs `workflow.md:85` G1「独立性由 fresh 子代理提供」。
- **C3 退役事实有档可查** — 验证方式：查归档与演进史；**证据锚**：subagent-dev 退役 = `workflow-history.md` A1 + adr/0042（tickets 唯一管线）；官方 code-review 弃用 = `workflow-history.md:15`（P3d）；writing-plans 退役 = remove-superpowers-pipeline（CLAUDE.md「历史参考（已退役）」段）。
- **C4 `/review` 残留全集经面扫** — 验证方式：`grep -rn "/review"` bundle 全量 + 手动补被过滤项；**证据锚**：`code-checklists/README.md:3,13,53,68`、`code-review-base.md:3`、`domains/llm.md:5`、`trigger-catalog.md:108`（grep 输出，2026-08-13）；`scope-drift-diagnosis.md:13` 的「plan/review/code」为泛指非 skill 名，不改。
- **C5 §三移史安全** — 验证方式：grep 外部引用；**证据锚**：`workflow.md:60` 只锚 generation-process §四；§三无任何 bundle 外引用（grep 输出，2026-08-13）。
- **C6 机械守卫边界已核** — 验证方式：读测试源码；**证据锚**：`hack/tests/test_canonical_entry_sync.py:83-90`（presence 四短语）`:94-100`（absence 退役短语）；`gen_workflow_guide.py:24-28` 只消费 workflow.md + prompts/（本次不动二者 ⇒ GUIDE 无需重生成）；update 不覆盖 config.yaml = 本次 update 实跑输出「config.yaml：update 保持 config.yaml」（2026-08-13 09:14）。
- **C7 Token_Saving 引用面唯一** — 验证方式：全仓 grep（不带 --include 限定的变体亦跑）；**证据锚**：仅 `reference/README.md:17` 一处（grep 输出，2026-08-13）。
- **C8 号段漂移已实证** — 验证方式：对照现行清单；**证据锚**：trigger-catalog 实有 TG-01~28（`trigger-catalog.md:47-48` TG-27/28 在列）而 `config.template.yaml:23` 写 24；spec-quality-base 实有 BASE-29/30（`spec-quality-base.md:53-54`）而三处写 28。
- **C9 人机共识** — 验证方式：对话记录；**证据锚**：人 2026-08-13 09:36 对完整审计清单方案（含 D7 两项处置推荐）明确「go」。

## 接受的边角

- **generation-process §三移史后编号空洞**（§四不重排以保外部锚）— 概率低/影响小：读者见 §二跳 §四；为保 `workflow.md:60` 的「§四」外部锚不失效，编号留空不重排，正文加一行「§三已移入 workflow-history A5」。
- **WORKFLOW-GUIDE 不重生成** — workflow.md 本次仅动 :85-86 以外？（实际 workflow.md 本次只动 `spec-review.md:92` 同款号段？否——workflow.md 本次不动）。若判断有误，`gen_workflow_guide --check` 在收尾门当场红，有兜底。
- **消费仓下次 update 前继续读旧文案** — 发布边界既有行为，非本次引入。

## 三镜代价

本次无 TG-23 命中（各处均为单一合理方案或琐碎选择，候选与理由已随 D 条目记录，按 BASE-12 琐碎决策不强制三镜书面）。
