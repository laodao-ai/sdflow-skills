---
name: sdflow-spec-review
description: >
  阶段二「设计评审编排器」——把 autoplan（广审）+ 本项目标准的并行多镜审（领域镜 + 对抗镜 + 接地镜）
  编排成一次连续跑、产出**一份** spec-review-report.md 的评审。主 session（强档）协调：Step1 跑
  autoplan 吃其 findings，Step2 fan-out 多个 fresh 子代理并行审本项目标准，Step3 去重合并 + 对抗裁决 →
  一份报告。**中途不打断**——撞到"≥2 方案 / 核验不了的事实"不 AskUserQuestion，而是写进报告「决策登记区」
  （≥2 方案：选项 + 推荐 + 三面后果(系统/用户/开发循环) + 主次判定；事实核验：待核验证据 + 风险 + 默认处理，不强制三镜），人工在设计 HARD-GATE 一次性过报告拍板。**不依赖 /clear**——子代理 fresh
  context 即独立性。只审 prevention（config 固化的结构/约束）焊不住的残差：①Validation ②对抗 ③接地读码。
  与 autoplan 互补不重复（autoplan 已含 eng 镜）。出报告标 [spec-review-amendment]。也可说"sdflow 设计审"。
  Trigger with /sdflow-spec-review。
---

# sdflow-spec-review — 阶段二设计评审编排器

<!-- sdflow:principles:start —— 由 hack/sync_principles.py 从 hack/skill-principles.md 注入，勿手改本区块 -->
## 🟢 三条通则（所有 sdflow skill 共用 · 违反即本次运行失败）

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力。**

❌「你们前端用什么测试框架？」（`package.json` 里写着）
❌「有没有 CI？」（`.github/workflows/` 看一眼）
❌「这个函数在哪调用？」（grep）

**给结论，不给过程**：「你们的集成测试是 `make integration`，我跑过了，绿」——
**而不是**「我看到 Makefile 里好像有个 integration target，你确认一下？」

### ② 不确定的方案，先调研再给推荐 —— **MUST NOT 甩开放题**

拿不准的时候，**MUST NOT 把几个选项原样丢给人**——那是**把调研的活布置给了人**。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」进人门，人只负责拍板。**

> ❌「Windows 包怎么产出？（买台机器？GitHub Actions？还是 non-goal？）」——三个选项，零调研，零推荐
> ✅「**建议走 GitHub Actions 的 windows runner。** 依据：① 本仓已有 workflows ② 工具链官方支持
> ③ 公开仓免费。**代价**：签名要证书，首版只能出未签名包。**备选**：降为 non-goal（后果：Windows
> 用户没有可用产物）。**要不要这么定？**」

**⇒ ①② 合起来的三分判据**（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论。**不问**（①） |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐 + 依据 + 代价 + 备选 → 人拍板**（②） |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权 · 组织约束） | **问** —— **注意力该全花在这里** |

> **人做的是拍板，不是替你做调研。**
> 人的注意力是唯一消耗掉就补不回来的资源：每问一个「你们用什么测试框架？」，
> 就挤掉一个「你上次被这个东西坑到是什么事？」——**而后者只有人知道。**

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

判断「该不该做 / 做到什么程度」**一律锚目标态**，**不受现有代码与设计的束缚**。

**MUST NOT** 用下面这些来论证「目标不该做 / 该缩水 / 可以妥协」：

- ❌「现在的代码不是这么写的」
- ❌「存量数据里没出现过这种情况」
- ❌「现状里这种情况很少见」
- ❌「现有设计不支持，所以改小一点」

> 迁移中「旧数据还没有新形态」是**必然**——拿它当风险基线，会把「**目标态才暴露的面**」
> 误判成「不存在」。这是**拿现状给目标松绑**。
>
> **正确的问法**：「**目标态下的 producer 会不会产出这种形态？**」
> **不是**：「现存文件里有没有？」

> 🔴 **评审类场景是本条的高发区**——评审时，**现状是唯一摆在眼前的东西**，
> 于是「它现在能跑 / 现在没出过事」极易被当成「它是对的 / 不用改」。
> **评审的基准是目标态，不是现状。**

### 🔴 传播纪律：**fan-out 子代理 / outside-voice MUST 原文带上这三条**

**子代理与 outside-voice 跑在 fresh context —— 它们看不见本文件。**

⇒ **每一个 fan-out 子代理的 prompt、每一份 outside-voice 的 context，MUST 把本区块
（`sdflow:principles` 从 `start` 到 `end`）原文整段复制进去。**
**MUST NOT 转述、MUST NOT 摘要、MUST NOT 只给指针。**

> **漏带的后果是确定的，不是概率的**：一个冷上下文的镜子，眼前只有现状，
> 它**必然**把「现在能跑」当成「是对的」，把「存量里没见过」当成「不会发生」——
> 而这正是 ③ 要杀的病。**冷是它的价值，也正是它的破绽。**

<!-- sdflow:principles:end -->

把 workflow 规则集的 `spec-review.md`（经 resolve-workflow.sh 解析，Detection 方法论）+ `spec-checklists/domains/`（领域 R 项）
操作化为一次**连续跑的编排评审**：Step1 autoplan（广审）→ Step2 并行多镜（本项目标准）→ Step3 合并成
**一份** `spec-review-report.md`。取代旧"autoplan + spec-review 各出报告 + 人工手动合并（旧 step 7）"三步。

> **两条连续性铁律（阶段二自动流的前提）**：
> - **不依赖 `/clear`（G1）**：评审 fan-out 到 fresh-context 子代理，独立性由"子代理冷上下文"给，不由 `/clear` 给。
>   主 session 携带生成历史进裁决，接受一丝合成层偏置——但**反静默压制**焊死其边界（见 Step3）。
> - **中途不 AskUserQuestion（G2）**：撞到决策点写进报告「决策登记区」，继续跑完；人工在设计 HARD-GATE
>   一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可（且报告摊开三面后果 + 主次判定，比中途弹窗看得全）。

---

## 第零步：确认对象 + 读规则

1. 未指定变更则 `openspec list` 让用户确认。记 `{change_dir}` = `openspec/changes/{name}/`。
2. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用评审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用评审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/spec-review.md`（方法论）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。

## 第一步：autoplan 子步（广审·原生执行，吃其 findings）

1. **原生执行〔T25·R5〕**：主 session 经 Skill 机制原生执行 autoplan（其指令直接进主 session 执行，MUST NOT 派子代理读其 SKILL.md 转述模拟）。autoplan 跑自己的流程，prompt 不注入；其内部 AskUserQuestion 人类门（premise 确认 / 最终批准）按 G2/C5 适配：不弹窗，连同其自动决策一并登记进本评审报告「决策登记区」，设计门一次拍板。
2. **主 session 落盘〔R5〕**：autoplan 原生机制只写 plan file，无「写任意路径」能力——执行完由**主 session** 汇总其结论 Write 落盘 `{change_dir}/gstack-review.md`（改动标 `[gstack-amendment]`），文件头 + 本报告 Step1 段各写 v1 锚行 `<!-- sdflow:step1-broad-review v1 mode="native" -->`；native 声明附一句侧信道佐证（如 autoplan 双声真实调用事实/运行痕迹）。
3. **降级路径**：autoplan skill 不可用 → 子代理模拟广审 + 报告显式标注「模拟广审（降级模式）」+ 锚行 `mode="simulated"`，MUST NOT 伪装原生。
4. **吃其 findings**：读 `gstack-review.md`，把 autoplan 的 findings + 自动决策纳入 Step3 的合并池（autoplan 的自动决策也登记进报告决策区）。
5. **outside-voice 复用守卫（确定性脚本门·R2）〔mlh-p4 T80〕**：复用 `gstack-review.md` 的 codex outside-voice findings 前，调守卫脚本出 reason_code——三前置（来源 mode / 新鲜度 fs-mtime / 结构 codex 段）的机械判定归脚本，复用/回落的**编排**归你：
   `python3 $RULES_ROOT/tools/outside_voice_guard.py --review-path {change_dir}/gstack-review.md --change-dir {change_dir}`——脚本纯 stdlib、无 subprocess、新鲜度用源文件 fs-mtime 直比（排除评审产物自身，捕获未提交编辑；不调 git），归约出唯一 reason_code（`none|file-missing|section-not-found|zero-findings|stale|simulated-source`）落 stdout；`none` = 三前置全过、退出码 0；其余码退出码非 0（坏输入如 `step1-broad-review` 锚缺失/mode 非枚举 → stderr `[outside_voice_guard] FAIL` + 无 stdout，遵其判定 MUST NOT 静默吞）。
   - **reason_code=`none`（退出 0）** → 复用不重开（避免双 codex），报告记「复用 autoplan outside voice N 条」。
   - **其余 reason_code** → 打印带该原因码的显式降级日志，**回落自跑设计 outside voice**（按下方「helper 调用协议」，site="design-voice"）；诱因为 `file-missing`（文件整体缺失）时措辞 MUST 声明「仅补偿 outside-voice 切片，广审其余镜仍缺」。
   > **C2 依赖 P2b 交叉引用〔3.2〕**：C2"复用"成立仅当 autoplan 每次都跑（P2b）；autoplan 未跑的变更本 skill MUST 自跑设计 outside voice（即守卫回落路径），不得因"复用了一个没产生的东西"漏掉整层。
6. **checkpoint 提交（P2c 第 1 次）**：`~/.sdflow/hack/checkpoint-commit.sh spec-review-autoplan "autoplan 广审 + gstack-amendment"`。

## 第二步：规划镜头 + 并行 fan-out 子代理（本项目标准）

> **串行纪律〔T20〕**：**MUST 待 Step1 checkpoint 完成后才 fan-out，禁止与 Step1 并行**（多镜评审对象须含 autoplan amendment）；若历史运行已并行，Step3 裁决须 diff autoplan amendment 增量核对并在报告注明。

**规划镜头（主 session）**：

- 按 `{change_dir}` 实际涉及的栈 + 内容判命中的 TG/领域 → 决定开哪几个**领域镜**（backend·go / embedded·ml307c·esp32 / frontend）。
- 按风险定**对抗镜**数量：普通 2 个，高风险 3 个。固定 1 个**接地镜**（机械读码核验）。
- 只审命中的；config 已固化的结构/占位/一致性（T/S）不进任何镜。
- **防重叠（1.4）**：autoplan 已含 eng 镜 → 本 skill 领域镜**不重复跑 eng 视角**，只跑本项目 `spec-checklists/domains` 里 autoplan 不碰的 R 项，别让两层重复计数。
- **HR-TG 判定〔C4·R3〕〔mlh-p4 T81〕**：**你判**命中 TG 集（命中哪些 TG 无确定性信号，判断归模型），交脚本做确定性交集 + 出锚——`python3 $RULES_ROOT/tools/hr_tg_intersect.py --tg-set "TG-xx,TG-yy" --trigger-catalog $RULES_ROOT/trigger-catalog.md`（空集传 `--tg-set ""`；HR-TG 子集由脚本从 trigger-catalog `## 七、HR-TG` 段 `> 成员：` 行单一源 parse，**不在此复制清单**）。脚本 stdout 两行：结果行 `hit:[…]｜依据模型判定:[…]` 或 `none｜依据模型判定:[…]`（你给的命中集显式可见供复审）+ 规范锚行 `<!-- sdflow:hr-tg v1 hit="…|none" declared="…" -->`（`declared=` 承你判定的命中集，adr/0018 输入可见）；坏输入/单一源损坏 → 退出码非 0 + stderr `[hr_tg_intersect] FAIL`，遵其判定 MUST NOT 静默吞。**hit 非空**（∩ HR-TG ≠ ∅）→ 单开一次领域专属 cross-model（按「helper 调用协议」，site="hr-tg"，context=命中判据触发点+相关 diff hunk，「找领域镜漏的」）。判定无论正反写报告，报告锚行取脚本 emit 的 `hit=`/`declared=`，再由你手填 `evidence="<判据触发点一句>"`（命中必填 evidence，30 秒可人工复核）。

**fan-out（一条消息内全部派出，各子代理 fresh context、无用户交互、返回结构化 findings）**：

| 镜 | 数量 | 干什么 | 建议档位 |
|----|------|--------|-----------|
| **领域镜** | 每命中领域 1 个 | 读 `{change_dir}` design/specs + 相关真实代码，逐条过 `spec-checklists/domains/<栈>` 的 **R 项**，列违反/存疑项（带文件:行证据） | 中档（判断） |
| **对抗镜** | 2-3 | 各从一个**不同角度**「证明这份 spec 会在实现期爆炸」：隐藏假设 / 失败模式 / 乐观估计与边界。默认 refuted=true，找不到爆点才放过 | 中档（对抗推理） |
| **接地镜** | 1 | grep/读真实代码，核验 spec 里**所有代码事实**（函数名/字段/API 路径/schema）是否真实存在且一致，列不符项 | 弱档（机械） |

> 档位与缺省见「模型选择」节。

> 每个子代理 prompt 必须自带：`{change_dir}` 路径、它负责的清单/角度、"返回结构化 findings 列表（每条带：问题 / 证据 file:line / **置信度(高/中/低)** / 严重度 / 建议），**不要 AskUserQuestion**"。
>
> **🔴 每个子代理 prompt MUST 原文携带本 SKILL.md 顶部的「三条通则」区块**（`sdflow:principles` 从 start 到 end，**整段复制，不转述、不摘要**）——见传播纪律。
> **设计审是通则 ③ 的最高发区**：子代理眼前只有「现在的代码/现在的设计」，漏带这三条，它**必然**把「现状不是这么做的」当成「这个设计该缩水」。**评审的基准是目标态。**

## 第三步：综合 + 对抗裁决 → 决策登记进报告（主 session · 强档）

- **合并去重**：把 autoplan findings（Step1）+ 各镜 findings 汇成一池，**去重**（同一问题多镜命中合并）；去重时记录每条 finding 的**命中镜集合**，折叠到 canonical lens 后供第四步落锚时导出各镜`独立`（唯一报过 ∧ 被采纳 +1；归属/折叠规则见规则根 `lens-metric-contract.md`，唯一权威源）。
- **对抗裁决**：对每条 finding 判"是否真的会在实现期出问题"——对抗镜的反驳若 ≥ 多数成立则采信；存疑的降级或标"需人确认"。
- **反静默压制（escalate-not-drop，Q3 铁律）**：热主 session 裁决对 reviewer 子代理的 finding **只能降级 / 批注、不得静默丢弃**。判"不成立"的也须连理由落入报告「已裁掉」区（原始发现 + 裁掉理由），供人类设计门复核"裁得对不对"。
- **置信分流**：高=直接采信、中=标"需人确认"进决策区、低=**仍上抛（一行带过），绝不静默滤除**。**不照搬 sdflow-code-review 的数值 <80 一刀切**：设计漏掉的代价高（传导进实现），spec 评审优化召回而非精度；对抗裁决（强档带上下文）已强于数值打分。
- **outside-voice findings 直通〔R4〕**：runner=codex 的 voice findings 与各镜同池对抗裁决；tension（voice 与主审分歧）→ 决策登记区 TENSION 条目（两方视角 + 推荐 + 三面后果(系统/用户/开发循环) + 主次判定），绝不静默采纳（user sovereignty）。
- **lens-metric 度量锚门控**：落锚前读 config.yaml 的 `metrics.enabled`——缺省或 `false` → 本轮**不落** `lens-metric` 锚、第四步对应自检项跳过、**不调 emitter**（仅本仓源仓 dogfood 默认 `true`）；为 `true` → 按第四步「度量锚」描述构造 roster+findings 并调 `lens_metric_emit.py`（**采纳/裁掉/defer 为设计门拍板前的临时裁决，MUST 在拍板回写时最终确定，见〔SR-M〕**）。
- **锚行自检（确定性脚本门）〔R1/R3/R5〕〔mlh-p2-anchor-lint〕**：出报告后调 `$RULES_ROOT/tools/anchor_lint.py --report {change_dir}/spec-review-report.md --layer spec-review --root "$(git rev-parse --show-toplevel)" --trigger-catalog $RULES_ROOT/trigger-catalog.md`——退出码非 0（1=违规/2=fail-closed）即本步报错阻塞，遵其判定，MUST NOT 静默吞。脚本机验四类 v1 锚存在性 + lens-metric 字段/枚举/sev/layer==--layer/计数 int≥0（枚举从契约 `lens-metric-enums` 块单一源读）+ metrics 开时 broad/outside-voice 最小必有行。**保留信任边界声明**：`findings=N` 与合并池实收数的**数值一致性**仍是主 session 信任边界、非机械可验——脚本不谎称保证数值正确。config `metrics.enabled` 关/无 metrics 块时 lens-metric 一类跳过（脚本内门控）。**此门只挡「同一会话内忘记跑这步」，挡不住「整段跳过本步」**（诚实拦截力）。
- **决策登记（取代中途 AskUserQuestion，G2）**：撞到"≥2 方案 / 核验不了的事实"→ **不打断**，写进报告「决策登记区」（见下格式）。
- 按 `design-diagrams.md`：命中触发的图**只验证存在/正确/未过时**，缺失/过时标记，不重画。
- **checkpoint 提交（P2c 第 2 次）**：产出报告 + amendments 后 → `~/.sdflow/hack/checkpoint-commit.sh spec-review "并行多镜审 + 合并报告 + spec-review-amendment"`。

**报告决策登记区格式**：

```
  spec-review-report.md · 决策登记区
  ┌─────────────────────────────────────────────────────┐
  │ [自动决策] D1  autoplan/裁决已定,附理由,默认接受可覆盖  │  高置信 → 默认采纳
  │ [需拍板]  Q1  ≥2 方案: 选项A/B + 推荐 + 三面后果 + 主次判定 │  人工设计门时勾
  │ [需拍板]  Q2  核验不了的事实(函数名/字段/API 路径)     │  人工确认
  │ [已裁掉]  X1  reviewer 原始发现 + 主 session 裁掉理由   │  反静默压制,可审计(不静默丢)
  └─────────────────────────────────────────────────────┘
```

## 第四步：产出

- 写 `{change_dir}/spec-review-report.md`：**决策登记区**（自动决策 / 需拍板 / 已裁掉）+ 各镜 findings（带置信/严重度，低置信项一行带过、可审计不静默丢）+ 裁决。
- **度量锚（lens-metric，受 config `metrics.enabled` 门控——关闭则本段整体不落、不调 emitter，见第三步）〔spec-review-amendment mlh-p4〕**：Step3 裁决后**构造** `{roster:[{lens,runner,site}…本轮实际跑过的每个行键（domain/adversarial/grounding/broad + outside-voice 每个调用过的 site）], findings:[{hits:[{raw,runner?,site?}…],verdict,sev}…]}`（input schema 权威见契约 `lens-metric-contract.md` 的 `lens-metric-input-schema` 机读块——bundle 分发可达、消费仓亦可读；源仓另有 golden fixture 示范 `tools/tests/fixtures/lens_metric_input.json`，消费仓非 full 拷贝不含 `tests/`，以契约 schema 块为准）〔impl-review-fix mlh-p4：引用改指 bundle 可达契约块，原指 lens-metric-emit 能力块实不存在于 bundle〕→ 调 `python3 $RULES_ROOT/tools/lens_metric_emit.py --layer spec-review --input <构造的f>` → **exit 0 才**把其 stdout（逐镜 `<!-- sdflow:lens-metric v1 … -->` 行）落进报告本段 → 再由 Step3「锚行自检」跑 `anchor_lint` 自检；exit ≠0（fail-closed）→ 本段**不落**、报告注明 emitter 报错原因，MUST NOT 手拼锚行顶替。
  **保留残余信任边界声明**：分类正确性（某条 finding 该归哪个/哪些 lens）+ roster 完备性（是否漏报本轮实际跑过的行键）+ findings JSON 誊写准确（hits/verdict/sev 是否如实转录裁决结果）仍是主 session 信任边界，emitter 只保证「给定输入的确定性归约」，不保证输入本身对不对。
  字段/取值域/归属/折叠规则见规则根 `lens-metric-contract.md`（唯一权威源，此处只引用不复制清单）。
- **反馈回路免责声明（与 sdflow-code-review 对称）〔impl-review-fix CF-补〕**：本 skill 只落锚，**不做聚合、
  不做复评判断、不主动 surfacing**——跨 change 归档后的锚聚合、按采纳率+独立率复评、"出现轮数≥10"的显著提示，
  一律由 `/sdflow-retro` 聚合（跑 `sdflow-retro/scripts/lens_metric_aggregate.py` 只读聚合所有归档报告）；是否保留/
  降采样/收紧触发/淘汰某镜一律人决，本 skill MUST NOT 自行判断或执行。
- 据此更新 design/specs，改动处标 `[spec-review-amendment]`。
- **收敛口（1.6）**：结尾一句——是否建议进设计 HARD-GATE（用户批准 → writing-plans）。人工过这一份报告拍板，即阶段二唯一人类门。
**拍板回写协议（ship-gate 锚，D2，mlh-p5 迁 frontmatter）**：设计门拍板**发生后**，主 session MUST 立即把 `ship-gate.design_approved`
写入 `spec-review-report.md`**的报告头部 frontmatter**（文件首块，非文件末尾、非正文）——写入者=主 session、触发点=用户批准动作；
这是 `/sdflow-ship` pre-flight 的唯一机判依据（**写入报告时 `ship-gate:` 顶格列 0，忽略本处 markdown 列表缩进**——下方 yaml
代码块已置于无缩进独立段落，照抄其文本即可，不要复刻本节说明文字的排版缩进）：

```yaml
---
ship-gate:
  design_approved: true
---
```

写入规则：若 `spec-review-report.md` 已有首块 frontmatter（首行即 `---`），MUST 将 `ship-gate:` 键合并进该已有块（不新开第二块、
不破坏已有其他键）；若尚无 frontmatter，MUST 在文件最顶端新建此块（**prepend**，MUST NOT 追加到文件末尾）。
**正文人读拍板记录行保留不删**：决策登记区/拍板记录区仍写一行人读结论（如"设计门已拍板批准，日期 XXXX-XX-XX"）——
frontmatter 是机判锚，人读行仍留在正文供人阅读、不因迁移而消失。

gate exit 3 时若拍板已发生，人工补此 frontmatter 块 = 显式越权留痕（人机同权）。

**〔SR-M〕lens-metric 锚随拍板最终化（best-effort，无机械兜底，仍在正文、不迁移）〔impl-review-fix CF-8〕**：spec-review 的
`采纳`/`裁掉`/`defer`（决策登记区「自动决策」/「已裁掉」/「需拍板」三态，需拍板项设计门可翻改其去向）因中置信项设计门可翻改，
其 `lens-metric` 锚 SHOULD 在**拍板回写时**（与上方 `ship-gate.design_approved` frontmatter **同步**写入 `spec-review-report.md`，
两处各写——头部 frontmatter 落机判状态、正文 lens-metric 注释落度量）最终确定/重算，
反映门后最终裁决，避免用 Step3 pre-gate 临时裁决充当最终采纳率——门前若因 `metrics.enabled=true` 已落的锚视为草稿值，
拍板时原地更新覆盖，不新开一行。**此为 best-effort、无机械兜底**：与 `ship-gate.design_approved` frontmatter 不同（后者有
`ship_gate.py` 硬拦截），此重算**无任何下游校验**——聚合器（`/sdflow-retro` 的 `lens_metric_aggregate.py`）
不知晓某行锚是"草稿"还是"已最终化"，主 session 漏执行本步不会被任何机制发现；采纳率/独立率的门后复评可能悄悄
停留在 pre-gate 的临时值上。与本节前述"数值一致性是主 session 信任边界、非机械门"口径一致——此局限已知且不新增
`ship_gate` 兜底（超本 change scope）。

---

## 模型选择（按本步性质，逐步定）

档位与缺省见规则根 `model-tiers.md`（经 `~/.sdflow/hack/resolve-workflow.sh` 解析；config.yaml 的 model-tiers 段可覆盖映射）。

```
  主 session（协调/对抗裁决/决策登记/出报告）  强档 ← 这是门禁,弱档=假绿
  领域镜 / 对抗镜（判断、对抗推理）             中档
  接地镜（grep/读码核验，机械）                 弱档
```

依据：评审是门禁，综合判断这层弱档会"看着过其实没深究"；机械读码可下放弱档。
**不要**把综合判断委派给弱档子代理。中途不 AskUserQuestion（决策进报告，G2）。

## 与 autoplan 的分工（编排内两层，别重复）

| | autoplan（Step1） | 多镜 fan-out（Step2，本 skill 标准） |
|---|---|---|
| 镜 | CEO/design/eng/DX + 双声 | 领域镜 + 对抗镜 + 接地镜（我们的标准） |
| 清单 | 四个 gstack skill 各自的 | 本项目 spec-checklists/domains |
| 决策 | 自动决策（登记进报告） | 主 session 对抗裁决（登记进报告） |
| eng 视角 | **已含** | **不重复**（防重叠 1.4） |

## outside-voice helper 调用协议（契约单一源 = `~/.sdflow/hack/outside-voice.sh` 头注释，此处只给分支决策，不转述接口细节）

```
HELPER=~/.sdflow/hack/outside-voice.sh
[ -x "$HELPER" ] 不成立 → 显式提示「outside-voice.sh 未安装——先跑 bash setup.sh」+ 直接派 fallback 子代理（不静默）
版本核对：$HELPER version 输出与本 SKILL 预期主版本(1.x)不符 → 告警"helper 疑似陈旧，重跑 setup.sh"后继续
preflight：仅精确匹配 "ready" 走 codex；"not_installed" 或任何畸形输出/非零退出 → fallback（reason_code=not-installed|preflight-error）
context 构造（摘录规则定死，不现场发挥）：写 {change_dir}/.outside-voice/<site>-context.md（固定命名、下轮覆盖、不删，留调试证据）；该目录 MUST 在 .gitignore 内（防 checkpoint 的 git add -A 把全量 diff/敏感内容永久入库）
  site=design-voice → proposal「What Changes」+ design「Decisions」全文
  site=hr-tg       → 命中 TG 判据触发点 + 相关 diff hunk
exec：$HELPER exec --context-file <f>
  exit 0   → stdout 即 findings 进合并池；锚行 runner="codex"
  exit 124 → fallback（reason_code=timeout）      exit 1 → fallback（reason_code=exec-error，stderr 摘要写锚行外正文）
  exit 3   → 本次 voice 拒发不 fallback（reason_code=secret-hit；密钥既不出境也不进子代理 prompt）
fallback：以 $HELPER render-prompt --context-file <f> 的输出为 prompt 派 fresh **只读型** Claude 子代理（禁写/禁执行副作用）（同源同 prompt；框架已含范围收窄）；
  无硬超时（与 codex 侧 300s 不对称，接受并留痕）；findings=0 的 fallback 在报告标注供抽查；锚行 runner="claude-fallback"
锚行（每调用位点一行，truncated 取 helper stderr 的 OV_TRUNCATED）：
  <!-- sdflow:outside-voice v1 site="…" guard="none|file-missing|section-not-found|zero-findings|stale|simulated-source" runner="codex|claude-fallback" reason_code="…" findings="N" truncated="true|false" -->
```

## 注意

- **只做 prevention 焊不住的残差**（T/S 项交给 config/lint，不重扫）。
- **必须读真实代码**，不得只验 spec 自洽（接地镜专司此事）。
- 项目无关：规则路径一律经 `~/.sdflow/hack/resolve-workflow.sh` 解析（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`。
- checkpoint 脚本 = `~/.sdflow/hack/checkpoint-commit.sh`（setup.sh 全局安装）；缺失则先跑 setup，或退化为普通 `git add -A && git commit`。
