<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — checkpoint-tag-single-source（Step1 广审）

> **native 声明与佐证**：Step1 广审由主 session 原生执行（scope-drift + 完成度审计）；cross-model 第二声音由 `~/.sdflow/hack/outside-voice.sh`（codex 引擎，与 autoplan 双声同源）在 design-voice site 提供，preflight=ready、exec 真实运行（见 `.outside-voice/design-voice-context.md` 留档 + 下方 outside-voice 段）。**未另行 spin up gstack autoplan skill**：autoplan 本质是 plan-file 评审工具，本 change 处**设计阶段无 superpowers-plan.md**（plan 在阶段三才生成），且改动面 = 2 文档 + 1 测试的极小元改动，full autoplan 机器不成比例；以主 session 原生广审 + 同引擎 cross-model 替代，非静默跳过、此处显式声明。

## Scope-drift 审计（顺手多改？）

- **结论：无 scope 漂移。** proposal「Impact」明确划界：改 `workflow.md`（step6 自我声明）+ `SKILL.md`（派发段瘦身）+ 新增 `sdflow-ship/tests/` contract 测试；`ship_gate.py` **不改行为**（仅作被测锚点被引用）。deferred T33/T35（新鲜度越 committed 边界）显式排除在 scope 外。无「顺手改隔壁」迹象。

## 完成度审计（建的 = 计划的？）

- specs 三条 Scenario（双向绑定 / 裸兼容两端一致 / 引用非复述）↔ tasks 1.1/1.2/1.3 一一对应，覆盖完整。
- tasks 含 TDD 序（先红测试→瘦身转绿→回归）+ 部署步（setup.sh 推 assets 权威源）。结构完整。

## 主 session 广审 findings（纳入 Step3 合并池）

- **BR-1〔高〕既有测试冲突**：`sdflow-ship/tests/test_workflow_authority.py:23-27` 的 `test_skill_producer_arg_namespaced` 断言 `"<change>:task<N>-<slug>" in SKILL.md`。tasks 2.1 要把该字面**从 SKILL.md 删掉** → 既有断言必红。tasks 仅含糊写「既有断言可能顺带增强」，未点破此**直接冲突**。实现期 TDD 会卡（删字面→既有测试红且非预期）。修复方向：tasks 须显式含「改 `test_skill_producer_arg_namespaced` 断言（从『含格式字面』改为『含对 workflow.md 的引用』）」。
- **BR-2〔中〕测试抽取机制未定死**：spec Scenario「双向绑定」说「从文档出现的格式构造 subject」，但文档写的是**占位符** `<change>:task<N>-<slug>` 非真实标签。占位符→实例（demo/1/slug）的映射由测试作者手写，非从文档机械导出 → 测试实际锚定的可能是「作者对格式的理解」而非「文档字面」，防漂移名实待核（留对抗镜 A 深挖）。
- **BR-3〔低〕引用锚名义**：SKILL.md 拟引用 workflow.md「step6 tag 契约」，但 workflow.md step6 是**表格行**、无同名 heading 锚 → 引用目标可定位但非稳定命名锚（留对抗镜 B 核）。

## outside-voice（design-voice, cross-model）

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="" findings="4" truncated="false" -->

codex（preflight=ready、exec exit 0、OV_TRUNCATED=false）返回 4 条，全部纳入 Step3 合并池：

- **OV-1〔中〕** delta spec.md 自身复制格式字面 `checkpoint(<change>:task<N>-<slug>)`（spec.md:5），与「单一文档源=workflow.md」自相矛盾；归档同步后成持久 spec 副本（第四漂移源）。
- **OV-2〔高〕** 契约测试漏掉真实生产链 `checkpoint-commit.sh`（`sdflow-init/assets/hack/checkpoint-commit.sh:46/48` 把 `$1` 包成 `checkpoint($step): …`）——只测 doc→parser、未验脚本真产 gate 可识别 subject。建议加集成契约测试（临时 repo 跑脚本→读 commit subject→断言 TAG_RE 捕获）。
- **OV-3〔中〕** 既有 `test_workflow_authority.py:23-27` 断言 SKILL.md 必含格式字面，与 tasks「MUST NOT 含」互斥（= 接地 F4 = 广审 BR-1）。
- **OV-4〔高〕** SKILL.md 瘦身削弱运行时派发：SKILL.md:29 是实际 RUN_PLAN 派发指令，删字面改引用会制造 design D1 自己要避免的读依赖（= 对抗镜B F2）。
