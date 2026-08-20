# Proposal · sweep-pool-debt-2026-08

## Why

池内四条遗留 todo（T287/T290/T292/T294）各自内嵌一个已拍板的设计岔路，且全部有实测证据支撑：`sdflow-spec/SKILL.md` 距 18,000 字符门仅余 66 字符（下次加内容即撞门）；「切片偏离」审计行落盘后全仓零消费方（MUST NOT 静默偏离无执行方）；ship_gate 失鲜锚以 commit sha 为取内容把手，rebase 重写 SHA 即取不到锚，现靠「MUST NOT rebase」指令层纪律兜底；78 个归档 change 中 17 个过不了 `openspec validate --archived`（openspec 1.9.0 新门），归档面无 CI 防回潮。人已拍板四合一、一个 change 四张独立票（decision-memo D1）。

## What Changes

- **T292（大头）**：ship_gate 失鲜锚由 commit sha 改为**监视集内容指纹**（单一 digest，D3）；**tasks.md 移出 design 失鲜监视集**（D2），随之删除勾选框豁免层（`_tasks_content_exempt` 23 行 + `_normalize_checkbox_lines` 37 行 + `is_stale` 内 tasks 支路及其测试；fence 词法单一源为四处共用且属有界合法件，**保留**——T189 所称 ~140 行含该共用件，实际可删面约 60–80 行）；锚值由脚本**权威计算**写入 frontmatter，产出方 SKILL 不再手写 40 位 hex（D4，A1 后半）；design 域的 `checkpoint(impl-review)` subject 豁免通道从 gate 端退役、改为 producer 重锚协议（D9，相位 C 期追加拍板）。**BREAKING**（仓内契约）：三份评审报告的锚字段格式变更，ship_gate 读取逻辑、3 个产出方 SKILL（spec-review / code-review / done）、约 10 个测试文件同步迁移；落一条新 ADR 修订 adr/0026 的锚记录（D8）。消掉的两条指令层纪律：MUST NOT rebase、（已由既有豁免解决的勾框假失鲜不再需要豁免层）。
- **T290**：code-review Step1 scope 审计输入清单新增 `impl-reports/planning-decisions.md` 的「切片偏离」行，做偏离-diff 对账（抓静默偏离；已申报偏离出票期已有对抗镜复核）（D6）。
- **T294**：17 个归档失败 change 三桶收敛——桶B（14 个漏勾 1–4 条）与桶A（2 个 tickets 管线 change 0/N）按 done SKILL 0.3 既有对账语义对照 git log 回填真实完成项；桶C（scoped-test-per-task，未落地即被 supersede）改写为无勾选框的作废说明段（补勾即伪造，D5，已沙盒实测可过门）；收敛干净后把 `openspec validate --archived` 接进 `mechanical-gates.yml`（openspec pin 1.5.0→1.9.0，本地 1.9.0 全量已预验证）。
- **T287**：`sdflow-spec/SKILL.md` 部分判据下沉 `references/`（已有 6 个先例文件），18,000 门不动（D7），下沉后留出健康余量。

## Capabilities

### New Capabilities

- `archive-validation`: 归档 change 的 tasks.md 记录诚实性约束（真实完成才勾、作废改写为说明段、MUST NOT 为过门假勾）+ `openspec validate --archived` 全量绿由 CI 机械守。

### Modified Capabilities

- `spec-workflow`: ship_gate 失鲜锚契约由「reviewed_sha（commit sha 把手）+ tasks.md 勾框豁免 + impl-review subject 豁免」改为「监视域内容锚（manifest+digest，不含 tasks.md）+ 锚值脚本权威计算 + 合法尾流修订走重锚协议」；MUST NOT rebase 纪律与 gate 端豁免通道一并退役。
- `impl-orchestration`: 「切片偏离」审计行新增消费方要求——code-review Step1 scope 审计 SHALL 以其为输入做偏离-diff 对账（原 MUST NOT 静默偏离获得执行方）。

## Impact

- **代码**：`sdflow-ship/scripts/ship_gate.py`（失鲜域重写，净删行）+ 新增/扩展一个锚值计算脚本；`sdflow-ship/tests/` 约 10 个测试文件 fixture 与断言迁移。
- **SKILL 指令**：`sdflow-spec-review` / `sdflow-code-review` / `sdflow-done`（锚回写步骤改调脚本 + done 预检的 40-hex 校验句更新）；`sdflow-code-review` Step1 输入清单；`sdflow-spec/SKILL.md` 内容下沉（本体语义不变）。
- **文档/规范**：新 ADR（修订 adr/0026 锚记录）；`openspec/specs/spec-workflow`、`impl-orchestration` delta。（已 grep 核实：仓内无「MUST NOT rebase」条款文本——该纪律存在于会话记忆层，非仓内文件，无清理面。）
- **归档区**：17 个 `openspec/changes/archive/*/tasks.md` 回填或改写（动历史文件，已报备拍板）。
- **CI**：`.github/workflows/mechanical-gates.yml` openspec pin 升级 + 新增 `validate --archived` 步。
- **无外部依赖变更**；不命中 backend/embedded/frontend 领域清单（纯 Markdown + Python 工具仓）。

## Success Metrics

- `openspec validate --archived` 全量 0 failed，且 CI 有该门（定点破坏一个归档 tasks.md → CI 红）。
- rebase 重写 commit SHA 后（内容不变）ship_gate 失鲜判定仍 CURRENT（新增测试钉住）。
- `ship_gate.py` 失鲜域净删行（豁免层 ~140 行消失），全仓 pytest 绿。
- `sdflow-spec/SKILL.md` 字符数 ≤ 16,000（余量 ≥ 2,000）。
- 「切片偏离」行 grep 命中含消费处（code-review Step1 输入清单）。

## Non-Goals

- 不做锚字段的向后兼容双读（旧 reviewed_sha 报告在途 change 为零，无迁移窗口需求）。
- 不改 `_tasks_content_exempt` 之外的 gate 域（窗口语义、UNKNOWN 分类学、preflight 结构不动）。
- 不调整 18,000 字符门本身（阈值、计数口径均不动）。
- 不引入「调用时机」的机械捕获（D4 诚实边界：脚本堵值错/伪造，不堵时机自报）。
- 不迁移 openspec 1.9.0 的其他新能力（只取 validate --archived）。

## Compliance

N/A（无合规 / 隐私 / 安全审计要求；单人工具仓）。
