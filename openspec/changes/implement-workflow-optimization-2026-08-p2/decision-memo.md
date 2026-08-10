---
schema_version: 1
change: implement-workflow-optimization-2026-08-p2
branch: feat/implement-workflow-optimization-2026-08-p2
generated_at: 2026-08-10T23:06:23+08:00
decision_hash: b9df81e63d95
---

# 决策纪要 · implement-workflow-optimization-2026-08-p2

## 目标态

13 面待复评镜逐一处置（保留 / 降采样 / 淘汰，落处置表 + retro 可读注记）+ 裁决协议替换为「validator 机械前置 + 二元裁决 + 置信降排序」（adr/0041）+ dogfood 双轨验证 + sdflow-done 终态 token 快照。

## 拍板决策

- **D1（2026-08-10 人拍板）**：实修率判据薄至 2/13 面，照 design.md 假设 A1 闸门的 fallback（独立率 + 人工复核为主）推进阶段 2，不回头放宽归属文法提覆盖率。**砍掉的候选**：回头增强 join 覆盖（= 放宽文法猜归属，报告明禁「MUST NOT 为提覆盖率放宽文法」）；推迟复评攒样本（= roadmap design.md 决策 1 已否的方案 B）。
- **D2（2026-08-10 人拍板）**：裁决协议取合成形态——T112 validator 引用真实性复核为机械前置门（弱档）→ T106 二元裁决 采纳/裁掉/defer + critique（强档）→ 自报置信降级为排序信号不再滤除；severity 保留为输出字段不作门；code-review 跨模型豁免矩阵条款废除（边界见 C7）。全文见 `openspec/adr/0041`。**砍掉的候选**：纯 T106 原案（validator 反正同 scope，拆开无收益）；severity 三级作门（自报地基同病）；维持 <80 硬滤（文献动摇 + 豁免通道补丁摞补丁）。
- **D3（2026-08-10 人拍板）**：dogfood 双轨——轨 1 历史重放（3-5 份归档报告，部署前，验裁决协议：误杀率为红线指标；噪声重入率因 C4 降级为参考）+ 轨 2 前瞻 3 个真实 change 窗口（部署后，验 roster：漏检归 roster、采纳率方向性偏移归裁决协议；阈值不钉死数字，设计相位定宽松方向性判据）。**砍掉的候选**：只做前瞻 dogfood（裁决协议要动真实评审才拿到第一个信号，重放能部署前拿到）；钉死数值阈值（评审轮间方差大，精确阈值是假精确）。
- **D4（2026-08-10 人拍板）**：2.A.5 做——sdflow-done 收尾加终态 token 快照，复用 `token_snapshot.py`（C5），落盘位置与 anchor 标记设计相位细化。**砍掉的候选**：不做并记因（唯一理由「偏差稳定同向可事后校正」，但收尾占墙钟 27%、尾巴量级太大，靠脚注校正不如直接采）。
- **D5（2026-08-10 人拍板）**：同构只收敛「裁决动作层」（validator 引用核——spec-review 侧核对象为四件套文档 + 代码——+ 二元裁决 + critique + 无数值滤）；spec-review 的「拿不准 → 决策登记区」人门路由保留（与置信数字脱钩），阶段二有 HARD-GATE、阶段三无人门是层间真实结构差异。两边 Step3 条款不追求全文同构。**砍掉的候选**：全盘同构 + 决策登记区改由 severity 驱动（把刚拆的门换字段重装）。
- **D6（2026-08-10 人拍板）**：降采样 = SKILL roster 段的**条件化派发**，条件只允许 dispatch 时机械可判的信号（TG 命中 / diff 规模 / 栈 / change 类型），每镜具体条件由 2.A.1 处置表逐镜定；MUST NOT 运行时模型自判难度路由（误分类风险）。「按条件跳过」在 lens-metric 锚上的表达（复用 `runner="none"` 还是新 reason_code）设计相位定。**砍掉的候选**：频率制（每 N 轮跑一次——跨轮状态要落盘、轮次与 change 风险无关）。
- **D7（2026-08-10 人拍板）**：裁决地基改造立 `adr/0041`（D2+D5+C7 合并承载）；D6 不单独立 ADR（有 TG→domains 先例、可逆性好）；CONTEXT.md 无需更新（既有条目全兼容，见 B.7 回扫）。

## 承重约束

- **C1 冷层护栏**：冷主审 / 冷全 diff 不在候选砍单。**证据锚**：design.md 决策 2（`openspec/roadmaps/workflow-optimization-2026-08/design.md:128`，两条实证——sdflow-retro 致命 F1 冷主审独家、harden-gate 4 条跨 ticket 缺口唯冷层抓到）；retro 报告 13 面待复评镜名单（`openspec/retro/report.md:6-19`）实核不含冷层。
- **C2 判据 fallback**：实修率仅 code-review adversarial（可判定 6，33%）与 domain（6，50%）达 ≥5 阈值，其余 11 面以独立率 + 人工复核为主判据。**证据锚**：`openspec/retro/report.md:262-275` 聚合④实测 + 人 2026-08-10 明确确认「照 fallback 推进」。
- **C3 归因与回滚隔离**：roster 改动与裁决协议改动落独立 commit、可分别 revert；dogfood 判读分别归因（漏检→roster、噪声/采纳率→裁决）。**证据锚**：design.md 决策 2（`design.md:130-132`）。
- **C4 重放语料可得性（修正版）**：归档评审报告含 `reviewed_sha`（frontmatter）+ 采纳/defer findings 带 file:line 与描述（可支撑 validator 引用核 + 二元重裁 ⇒ **误杀率可算**）；但「已裁掉」区按反静默压制条款只留一行摘要，原始 finding 全文不落盘 ⇒ **噪声重入率只能 best-effort、标「参考」**。**证据锚**：实读 `archive/2026-08-07-fix-probe-scan-precision/code-review-report.md`（38 行，滤除项一行制实证）、`archive/2026-08-09-absorb-gstack-autoplan`（X1-X6 一行表）、`archive/2026-07-20-harden-gate-git-layer`（裁掉区中等保真）。另一实证：数值 <80 独立击杀的滤除项在样本中极少（autoplan 仅 X1 一条），多数裁掉出自对抗裁决的验证性理由 ⇒ 删数值滤的行为面变化比预想小。
- **C5 token 快照接线面**：`token_snapshot.py` 具 argparse 接口（`--step` 必填）+ anchor 布尔字段，done 终态快照可纯复用、无新采集路径。**证据锚**：实读 `sdflow-init/assets/hack/token_snapshot.py:244-246,197-205`。
- **C6 度量锚兼容面小**：lens-metric 锚字段为 findings/采纳/裁掉/defer/独立 + sev，**不含置信字段**；二元裁决三态（采纳/裁掉/defer）与锚三计数同构 ⇒ 裁决改造不动锚 schema，2.A.4 主要工作是 `lens_metric_emit.py` 输入侧（结构化 findings JSON 若含置信字段则兼容处理）。**证据锚**：实读 `sdflow-init/assets/workflow/lens-metric-contract.md:4,16`。
- **C7 跨模型豁免废除的边界**：废的是 code-review SKILL Step3 的「豁免直通」条款（`sdflow-code-review/SKILL.md:339`，依附于数值滤存在）；anchor_lint 的合法组合矩阵**保留**——它同时服务 lens-metric 跨模型性度量（contract §跨模型性），与滤除门无关。**证据锚**：实读 `lens-metric-contract.md:20`。
- **C8 处置记录需要机械落点**：`retro_report.py` 待复评区块纯按 (layer,lens,host,runner,site) 轮数 ≥ `LMA.REVIEW_ROUNDS_THRESHOLD` 机械触发，无处置记录输入源。**证据锚**：实读 `sdflow-retro/scripts/retro_report.py:602-629` ⇒ 满足验收「清空或逐镜带处置记录」必须新增：处置记录文件（格式/位置设计相位定）+ `retro_report.py` 读取后对已处置镜行内注记。属验收标准隐含范围，非加宽。

## 接受的边角

- **噪声重入率算不真**（C4）——概率：确定（滤除项原文结构性缺失）；影响：小（数值滤独立击杀本就极少，指标本身低承重）；完美成本：无解（历史报告不可补写）。**为何接受**：降级为参考指标即可，误杀率红线不受影响。
- **前瞻窗口拖尾**——change 先归档，3-change 观察窗口作为 roadmap 层验收残项挂着，不阻塞阶段 3/4 起手。概率/影响：窗口期发现问题走 C3 的独立 revert，成本有界。**为何接受**：等窗口收口再归档 = 阶段 2 墙钟膨胀 2 周+，收益只是账面整洁。
- **B 相位增量落盘的已知损失窗口**：两次保存点之间的对话内容崩溃即丢——本次运行实际全程未中断，无实际损失。

## 三镜代价

D2 裁决形态选择（本次唯一方案级选型）：**系统镜**——Step3 条款重写 + emitter 输入侧兼容（2.A.4）；强档裁决输入量变大，由 validator 机械前置对冲，净 token 变化 dogfood 观察。**用户镜**——报告三区形态不变，读感无迁移成本。**开发循环镜**——删豁免矩阵 + 三信号打架收敛为「机械门 + 二元判」两层，心智负担实降。**主次判定**：开发循环镜为主——裁决协议的复杂度正是地基改造要治的病。
