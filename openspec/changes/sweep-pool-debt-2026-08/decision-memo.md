---
schema_version: 1
change: sweep-pool-debt-2026-08
branch: feat/sweep-pool-debt-2026-08
generated_at: 2026-08-20T17:01:34+08:00
decision_hash: 2d859634e06a
---

# 决策纪要 · sweep-pool-debt-2026-08

## 目标态

一个 change 收敛池内四条遗留 todo：`sdflow-spec/SKILL.md` 体量回落到 18,000 门内且留出健康余量（T287）；「切片偏离」审计行获得真实消费方（T290）；ship_gate 失鲜锚改为内容寻址（rebase 免疫，消掉 MUST NOT rebase 指令层纪律）且锚值由脚本权威计算（T292 + A1 后半）；78 个归档 change 全量通过 `openspec validate --archived` 并把该门接进 CI（T294）。

## 拍板决策

- **D1 四条 todo 四合一，一个 change 四张独立票** — 依据：人 2026-08-20 两次明确拍板（explore 切法呈现后「直接一个 change 做掉」；T292 爆炸半径 22 文件如实报告后「都同意」）；**砍掉的候选**：三 change 切法（T292 独立 + T294 独立 + T287/T290 收尾）——多付两轮流程固定成本，人判不值。scope 内聚检查的「混拼」偏离已呈现，人拍板豁免。
- **D2 tasks.md 移出 design 失鲜监视集** — 依据：勾框假失鲜已由 `_tasks_content_exempt` 解决（C3），移出后豁免层整层可删（~140 行手搓 CommonMark fence tracker，T189 登记的基准 5 靶子）；实质改动漏检有两层旁路兜底（done 0.3 对账 + code-review Step1 scope 审计）。人 2026-08-20 拍板（Q1）。**砍掉的候选**：保留 tasks.md 于监视集 + 锚存 path→oid 逐条映射——豁免层保留、锚格式复杂化，仅换来对「批准后实质改 tasks.md」的直接检测。
- **D3 失鲜锚 = 监视集内容指纹（单一 digest）** — 依据：D2 成立后 digest 即充分（无需锚侧字节做勾框豁免）；比较语义不变（C1：现行就是内容比较，只换把手）。**砍掉的候选**：① path→oid 映射锚（D2 已消其必要性）；② 双轨 fallback（commit sha 主 + digest 备）——两套表示、罕用路径测不实。
- **D4 锚值由脚本权威计算写入，LLM 不再手写**（A1 后半，薄版） — 依据：现状锚值由被监管方自报（「有信号≠有可机械捕获路径」）；产出方 SKILL 因锚格式变更本就要编辑，边际成本小。人 2026-08-20 拍板（Q2）。**诚实边界：调用时机仍是 LLM 自报，脚本只堵值错/伪造，不堵时机错。** **砍掉的候选**：另立 todo 后做——同一批文件将来再改一遍。
- **D5 T294 桶C 改写为作废说明段（prose，无勾选框）** — 依据：补勾即伪造完成（todo 明禁）；CI 排除清单是永久疣；无勾选框可过 validate 已沙盒实测（C4）。动归档历史文件已向人报备，人 2026-08-20 拍板（Q3）。桶A/桶B 按 done 0.3 既有语义对照 git log 回填（C5，非新语义）。
- **D6 T290 接线 = code-review Step1 输入清单加 `impl-reports/planning-decisions.md` 切片偏离行，做偏离-diff 对账** — 依据：出票期对抗镜只覆盖已申报偏离，Step1 对账才能抓静默偏离（spec 的 MUST NOT 静默偏离现无执行方，C8）；**砍掉的候选**：挑明定位为存档——留一条无人执行的 MUST NOT。
- **D7 T287 = 下沉 references/，18,000 门不动** — 依据：门是 T242 常驻上下文瘦身契约，调门废其目的；下沉模式已有 6 个先例文件（C7）。下沉哪些小节属实现细节，design 定。
- **D8 ADR：D2+D3+D4 合并落一条新 ADR（修订/接续 adr/0026 的失鲜锚记录）** — 依据：TG-23 命中 + ADR 三条件（难逆转：锚格式是 gate 契约字段；缺上下文会意外：为何 digest 而非 commit sha；真实权衡：D2 的 fail-open 面）。ADR 正文实现期随票落，设计门时人可见。

## 承重约束

- **C1 现行 is_stale 已是内容比较，commit sha 只是「取锚侧内容的把手」** — 验证方式：读 ship_gate.py 失鲜域文档与实现；证据锚：`sdflow-ship/scripts/ship_gate.py:72-100`（ls-tree path→(mode,type,oid) 映射等值比较）。∴ 改内容寻址锚 = 换把手，不换比较语义。
- **C2 reviewed_sha 消费面 = 22 个文件**（3 产出方 SKILL + ship_gate.py + 10 个测试文件 + ADR 0026 + spec-workflow spec + docs） — 验证方式：`grep -rln reviewed_sha`（不限文件类型，排除 archive/issues/retro）；证据锚：2026-08-20 grep 输出 22 行。改锚格式的爆炸半径以此为准。
- **C3 「勾 tasks.md 触发假失鲜」已被 `_tasks_content_exempt` 解决**，不再是本 change 待消约束 — 证据锚：`sdflow-ship/scripts/ship_gate.py:78`；T292 summary 订正段亦确认。
- **C4 无勾选框的 tasks.md 能通过 `openspec validate --archived`（1.9.0）** — 验证方式：scratchpad 沙盒仓实测（纯 prose tasks.md → `✓ 1 passed, 0 failed`）；证据锚：2026-08-20 沙盒命令输出。∴ 桶C「改写为作废说明段」技术上可行。
- **C5 tasks.md 在 tickets 管线下的对账语义已由 done SKILL 0.3 定义**（对照 git log，真实完成的勾上、未做的留 `[ ]` + 说明，MUST NOT 假勾） — 证据锚：`sdflow-done/SKILL.md:185-191`。∴ T294 桶A 不是「定新语义」而是「按既有语义回填」。
- **C6 归档失败面 = 17/78，桶分布 2(桶A tickets 0/21+0/12) + 14(桶B 漏勾 1-4 条) + 1(桶C scoped-test-per-task 0/5 未落地即 superseded)** — 验证方式：本地 `openspec validate --archived --json` 实跑（openspec 1.9.0）；证据锚：2026-08-20 实跑输出。
- **C7 18,000 字符门只计 `sdflow-spec/SKILL.md` 本体 Unicode 字符数，references/ 不计入** — 证据锚：`hack/tests/test_sdflow_spec_resident_contract.py:117`（`len(SKILL.read_text())`）。当前 17,934，余 66。
- **C8 「切片偏离」审计行全仓零消费方**（3 处命中全是定义处） — 证据锚：grep 命中 `sdflow-implement/SKILL.md:265` + `openspec/specs/impl-orchestration/spec.md:239,329`，无任何读取方。
- **C9 code-review Step1 scope 审计的输入清单在 `sdflow-code-review/SKILL.md:245`**（proposal + tasks + design + DIFF），planning-decisions.md 不在其中 — 证据锚：该行原文。T290 接线点即此。
- **C10 上游 A1 原记录含两个机制（内容寻址锚 + 绑定字段权威计算、忽略自报值），T292 现 summary 只承载前半** — 证据锚：`openspec/upstream/reports/20260820T012010Z.md` 尾部 A1 预生成命令原文 vs `openspec/issues/open/todo/T292.md` summary。后半去留需人拍板。
- **C11 CI openspec pin=1.5.0，本地 1.9.0 全量 --archived 可跑** — 证据锚：`.github/workflows/mechanical-gates.yml:119` + 本地 `openspec --version`。

## 接受的边角

- **D2 fail-open 面：批准后对 tasks.md 的实质内容改动不再直接触失鲜** — 概率：低（tickets 管线下工作清单是 tickets.md，批准后实质改 tasks.md 非常规动作）；影响：中低（done 0.3 对账 + Step1 scope 审计两层旁路可捕）；完美成本：保留 path→oid 锚 + 140 行豁免层。**为何接受**：人拍板 Q1；删无界语法面解析器的系统镜收益为主。
- **D4 时机自报残余：脚本堵值不堵调用时机** — 概率：低；影响：低（时机错=锚到错误盘面，评审报告与 diff 不符会在下游对不上）；完美成本：无可信机械捕获路径（捕获环节天然在产出方手里）。**为何接受**：诚实边界即合法残余。
- **锚侧 blob 依赖 git 对象存活（D3 的 digest 比较不需取锚侧字节，此边角实际已随 D2 消失）** — 记录备查：若未来把豁免类逻辑加回，须重估 dangling blob gc 风险。
- **change 名 sweep-pool-debt-2026-08 与「四张票各自主题」贴合度一般** — 通则④可接受边角，重命名无 CLI 支持。
- **B 相位增量落盘的已知损失窗**：两次保存点之间的对话内容（本次实际损失：无——约束全部当场落盘）。

## 三镜代价

TG-23 命中（Q1/D2-D3 为非显然设计选择），书面写满：

- **系统镜**：digest 锚 + 移出 tasks.md ⇒ `is_stale` 从 ~200 行（含豁免层）缩到 ~20 行，删除一个无界语法面手搓解析器（T189 靶）；耦合面缩小（gate 不再解析 Markdown）；可回退性好（恢复=revert 单 change）。代价：22 文件消费面一次性迁移，10 个测试文件 fixture 更新。
- **用户镜**：rebase 不再击穿失鲜检查 ⇒ 「MUST NOT rebase」纪律消失，分支操作自由度恢复；勾框/整理 tasks.md 不再误触门。代价：批准后实质改 tasks.md 的静默窗（两层旁路兜底）。
- **开发循环镜**：锚值脚本化 ⇒ 产出方 SKILL 指令更短、无手抄 40 位 hex 的心智负担；CI 新增 --archived 门防归档面回潮。代价：本次一次性迁移工作量（大头在 T292 票）。
- **主次判定**：系统镜收益（删解析器 + 契约简化）为主，一次性迁移成本为次；fail-open 边角以旁路兜底可接受。
