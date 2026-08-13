---
ship-gate:
  verify: PASS
  reviewed_sha: c4911a3630ee5ae890867e3804c03ec4889f95fd
---

# fix-workflow-bundle-staleness · Verify Report

## 逐需求核对表

### 1. bundle 核心规则修正

| 任务 | 判定 | 证据锚 |
|------|------|--------|
| 1.1 `spec-review.md` :72 AskUserQuestion→决策登记区 | ✅ | `spec-review.md:72` grep 确认 `决策登记区` 存在、`AskUserQuestion` 零命中 |
| 1.1 :29 删「/clear 后重审」 | ✅ | grep `/clear.*重审` 零命中 |
| 1.1 :91 brainstorming→生成期自检 | ✅ | grep `brainstorming` 零命中 |
| 1.1 :92 去 BASE 号段上界 | ✅ | grep `BASE-.*~30` 零命中 |
| 1.2 `reference/README.md` :18 quality-layering 描述改 P3c 口径 | ✅ | `reference/README.md:18` 含「每次全跑·独立冷·强制主审（P3c」 |
| 1.2 :17 删 Token_Saving 行 | ✅ | 文件中无 Token_Saving 引用行 |
| 1.2 :6-8 canonical 口径 | ✅ | `reference/README.md:6-7` 含「全局 canonical `~/.sdflow/workflow/`」 |
| 1.3 `quality-layering.md` :25 独立编排器口径 | ✅ | `:25` 含「独立编排器」，无「/clear +」 |
| 1.3 :42 sdflow-code-review | ✅ | `:42` 含 `sdflow-code-review` |
| 1.3 :84 删 subagent-dev | ✅ | grep `subagent-dev` 零命中 |
| 1.3 :38 CR 去号段上界 | ✅ | grep `CR-01~09` 零命中；`:38` 含 `CR base` |
| 1.3 :14 出处标注保留 | ✅ | `quality-layering.md:14` 保留 `subagent-driven-development` 出处 |
| 1.4 `spec-quality-base.md` :37 writing-plans→出 ticket | ✅ | `:37` 含「出 ticket」；:7 来源行 writing-plans 为 provenance 保留 |
| 1.4 `spec-checklists/README.md` :62 路径修正 | ✅ | `:62` 含 `../ff-generation-constraints.md` |
| 1.4 :64 R 落点措辞现行化 | ✅ | `:64` 含 `/sdflow-spec 相位 B 拷问 / /sdflow-spec-review` |
| 1.5 /review 8 处消费方改写 | ✅ | `code-checklists/README.md` grep `/review` 零命中、含 5 处 `sdflow-code-review`；`code-review-base.md`/`domains/llm.md`/`trigger-catalog.md:108` grep `/review` 零命中、已改 sdflow-code-review |

### 2. generation-process 收史 + ff-generation-constraints

| 任务 | 判定 | 证据锚 |
|------|------|--------|
| 2.1 §二改现行两工具表 + :21 标题行 | ✅ | `generation-process.md:21`「两个相位 + 两个 skill」（含 explore + /sdflow-spec 两行表） |
| 2.1 §三移除、留一行指路 A5 | ✅ | `generation-process.md:36`「历史论证见 workflow-history.md A5」，无完整 grill 论证正文 |
| 2.1 §六 grill→相位 B 拷问 | ✅ | `generation-process.md:99` 含「`/sdflow-spec` 相位 B 拷问」 |
| 2.1 §四流水线图插阶段二行 | ✅ | `generation-process.md:50`「↓ /clear → /sdflow-spec-review（阶段二设计审）」 |
| 2.1 ② 删「判断」 | ✅ | grep `② .*判断.*需要开` 零命中（`:97` 的 ①② 是不相关上下文） |
| 2.1 test_canonical_entry_sync 8 tests | ✅ | `/usr/bin/python3 -m pytest hack/tests/test_canonical_entry_sync.py -v` 8 passed |
| 2.2 workflow-history.md A5 | ✅ | `workflow-history.md:50` 含 A5 条目标题 |
| 2.3 ff-generation-constraints.md 标题改 | ✅ | `:1`「生成起手强制规范（FF-0 + D-1~D-6）」 |
| 2.3 定位声明改 /sdflow-spec | ✅ | `:3` 含「`/sdflow-spec`（或 `/opsx:ff` 直呼）」 |
| 2.3 canonical 路径 | ✅ | 无 `@openspec/workflow/` 旧路径 |

### 3. reference 处置 + 同族面治

| 任务 | 判定 | 证据锚 |
|------|------|--------|
| 3.1 Spec_Quality_Collaboration.md 历史横幅 | ✅ | 文件头 blockquote 含「历史分析」+退役说明+现行替代 |
| 3.1 Spec_Quality_Methodology.md L1 历史举例标注 | ✅ | `Spec_Quality_Methodology.md:23-24` 含「L1 举例为历史工具名…现行对应」 |
| 3.2 git mv Token_Saving → docs/ | ✅ | `docs/Token_Saving_Strategies.md` 存在；原 `reference/` 下已无此文件 |
| 3.2 移动后历史横幅 | ✅ | 文件头含「个人历史笔记（superpowers 时代）」 |
| 3.3 PRD_vs_Spec.md opsx:ff→sdflow-spec (4 处) | ✅ | grep `opsx:ff` 仅存于 blockquote 说明行（:7 兼容声明）；`:31/68/108/116` 已改 `/sdflow-spec` |
| 3.3 PRD_vs_Spec.md 历史举例标注 | ✅ | 文件头 blockquote 含「历史举例标注」+历史工具名说明 |
| 3.4 config.template.yaml 去号段 + 现行化 | ✅ | grep `TG-01~`/`BASE-01~`/`CR-01~` 零命中；`:23-27` 现行 blurb |
| 3.4 index-section.md 6 行改 | ✅ | `:10` sdflow-implement+两处阶段交界 /clear 口径；`:11` TG-NN（无上界）；`:12` /sdflow-spec 语境；`:13` 三相位现行化；`:18` BASE-NN；`:19` CR-NN |
| 3.4 fable5 02-module-reference.md :160 去上界 | ✅ | grep `TG-01~26` 零命中；`:160` 含 `TG-NN` |
| 3.5 openspec/config.yaml 与 template 同步 | ✅ | 两文件 workflow 相关行内容一致（diff 仅为行号偏移+项目自有段差异） |

### 4. 收尾门与复扫

| 任务 | 判定 | 证据锚 |
|------|------|--------|
| 4.1 sync_principles --check | ✅ | 退出码 0，「28 个投放面全部与真相源一致」 |
| 4.1 gen_workflow_guide --check | ✅ | 退出码 0，「WORKFLOW-GUIDE.md 与单一源一致」 |
| 4.2 init.py update --root . | ✅ | INDEX.md 含更新后 index-section 内容（TG-NN/BASE-NN/CR-NN） |
| 4.3 全仓 pytest -W error | ✅ | 2650 passed, 10 skipped, 0 failed（本次 verify 实跑） |
| 4.4 C4 grep 清单 0 残留 | ✅ | `/review` 旧口径在 8 处消费方零命中（含增补位点） |
| 4.4 C8 号段漂移 0 残留 | ✅ | TG/BASE/CR 上界零命中（含 index-section + quality-layering + fable5） |
| 4.4 三处矛盾对读一致 | ✅ | P3c(README:18↔quality-layering)、G2(spec-review:72↔workflow.md)、index-section /clear↔workflow.md:134 |

### 附带修复

| 项 | 判定 | 证据锚 |
|----|------|--------|
| init.py _marker_schema 放宽 | ✅ | `init.py:626-639` 只要求 schema 键存在且非空字符串，不限额外键；`test_init.py:276` `test_migration_accepts_marker_with_extra_keys` 覆盖 |

## 结论

**PASS** -- tasks.md 全部 34 条需求（含 4 条收尾门）均有可机验证据锚，无 gap。
