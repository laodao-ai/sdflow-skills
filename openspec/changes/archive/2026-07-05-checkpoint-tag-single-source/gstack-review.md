<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack-review — checkpoint-tag-single-source（Step1 广审 · Round 2 / Q1=B 修订版复审）

> **Round 说明**：本文件原为 Round 1（原始设计：workflow.md/SKILL.md 瘦身 + doc 正则抽取）广审，该设计已被四路冷审实质证伪、用户拍板 Q1=B 收敛为**纯测试新增、零 doc/skill 改动**。本文件已重写为 **Round 2**（对 Q1=B 修订版的复审门广审）；Round 1 findings（BR-1 删 SKILL.md 字面冲突、OV-1~4 等）随原方案作废，不再适用。
>
> **native 声明与佐证**：Step1 广审由主 session 原生执行（scope-drift + 完成度审计）；cross-model 第二声音由 `~/.sdflow/hack/outside-voice.sh`（codex 引擎）在 design-voice site 提供——本轮 codex **exec 超时（exit 124）**，按 helper 协议回落 claude-fallback 只读子代理（见下方 outside-voice 段 + `.outside-voice/design-voice-context.md` 留档）。**未 spin up gstack autoplan skill**：autoplan 本质是 plan-file 评审工具，设计阶段无 superpowers-plan.md（阶段三才生成），且改动面 = 1 新增测试文件 + 文档产物的极小元改动，full autoplan 不成比例；以主 session 原生广审 + 同引擎 cross-model 替代，非静默跳过、显式声明。

## Scope-drift 审计（顺手多改？）

- **结论：无 scope 漂移。** `git diff --stat e3faea9..5233d29` 显示实现三 commit 只改 `openspec/changes/checkpoint-tag-single-source/*` 文档产物 + 唯一新增 `sdflow-ship/tests/test_producer_parser_contract.py`；`ship_gate.py` / `workflow.md` / `SKILL.md` / 既有测试断言**均未触碰**（接地镜 16/16 + 三镜 diff 核实一致）。与 proposal「零 doc/skill 改动」声明相符。deferred T33/T35 显式排除。无「顺手改隔壁」迹象。

## 完成度审计（建的 = 计划的？）

- delta spec Scenario ↔ tasks 1.1/1.2/2.1/3.x 一一对应，覆盖完整（接地镜逐条核实实现文件与 design 一致）。
- tasks 含 TDD 序（写测试→跑绿→回归确认）+ 回填复选框步。结构完整、实现已全绿（sdflow-ship 85/85、仓级 348/348）。

## 主 session 广审 findings（纳入 Step3 合并池）

- **BR-1〔process·高·= B4〕设计门复审时序**：本轮复审是**事后审计**——实现三任务已落地（26aeb2d/dc35c7d/5233d29）后才做本轮设计门复审，且报告"拍板记录"明写"修订版须回设计门再过一次"、`design-approved` 真锚从未写入。诱因 = gate `anchors_in` 子串误配描述性文字（已记 **B4/VERIFIED**）。三路冷审（对抗镜#2 时序观察 + OV-fallback #1）独立复现。**对人类设计门**：本次拍板须**追认覆盖 task1-3**（非仅"往后修 B4"）。
- **BR-2〔CEO/价值·通过〕**：值不值得做？值——producer→parser 是 gate 完成判据主锚、**当前零测试守卫**，脚本包裹或 TAG_RE 漂移会静默不计入完成集（假✅家族）。改动极小、纯回归防护网、零运行时行为变更。scope 收敛得当（砍掉被证伪的 doc 瘦身/循环抽取，只留经得起冷审的内核）。
- **BR-3〔DX·通过〕**：对开发者无感（纯测试网），对维护者有值（未来重构无声破 producer→parser 链时翻红）。

## outside-voice（design-voice, cross-model · 本轮回落）

<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="claude-fallback" reason_code="timeout" findings="4" truncated="false" -->

codex exec 超时（exit 124，xhigh 推理逐文件读取被 300s 砍断，未产最终 findings）→ 按 helper 协议回落 claude-fallback 只读子代理（同源同 render-prompt）。fallback 返回 4 条，纳入 Step3 合并池：

- **OV-1〔process·critical = B4/BR-1〕** 设计门复审从未真正发生（gate `anchors_in` 子串假阳）；mutation 模拟独立复现。建议人类追认覆盖 task1-3。
- **OV-2〔informational〕** 负例矩阵 + 集成测试经 mutation 模拟核实**真 sound**：4 条负例各对应一类真实放松的哨兵（非空断言）；集成测试双层独立断言（先硬编码 subject 字面、再 TAG_RE 捕获），无假绿；sys.path 注入安全（ship_gate 模块唯一、import 无副作用）；6/6 + 85/85 绿。
- **OV-3〔informational〕** D3「零 doc/skill/ship_gate.py 改动」跨三 commit diff 核实成立，既有 authority 断言原样未动仍绿。
- **OV-4〔低·可移植〕** 测试造文件名含冒号 `f-demo:task1-slug.txt`（NTFS 非法），Unix 跑绿、若上 Windows CI 会误红——本测试层 Unix 取向，极低概率。
