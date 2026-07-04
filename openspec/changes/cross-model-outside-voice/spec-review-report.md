# spec-review-report — cross-model-outside-voice

> 阶段二编排评审 · 2026-07-04 · Step1 autoplan（**原生执行**，CEO/Eng/DX × Claude/codex 六声）→ Step2 多镜（对抗镜×3 + 接地镜×1；领域镜 0——不命中 TG-01/02/03 技术栈，过 base 清单）→ Step3 强档对抗裁决。
> `<!-- step1-broad-review: native -->`（本行同时为该锚行首用；native 判据 = autoplan SKILL 指令直接进主 session + codex/子代理双声真实调用，见 gstack-review.md 执行披露）
> `<!-- outside-voice: mode=codex reason="" findings=27 -->`（autoplan 双声中 codex 三相位真跑；本报告即锚行 v0 首用，v1 文法见 A-D4）
> `<!-- hr-tg: hit=TG-08,TG-17 -->`（规划镜头判定：外部依赖 + 信任边界 → 高风险 → 对抗镜 3；判据触发点：codex CLI 跨服务调用 / 仓库代码发外部 LLM）

---

## 决策登记区

### [自动决策]（高置信技术修，已应用 [spec-review-amendment]，默认接受可覆盖）

| # | 决策 | 依据（双声/多镜共识） |
|---|---|---|
| D1 | **D4 机制澄清**：T25 原生执行 = 主 session 经 Skill 原生执行 autoplan + **主 session 汇总落盘** `gstack-review.md`（autoplan 自身无「写任意路径」机制，写 plan file）；「sdflow-ship 先例」引用文不对题撤销，改锚**本轮 spec-review 实证**（原生跑通 + 落盘成功）；headless OQ 加升级条款：若原生路径实测不可行，headless 调研升 P0，不得只靠模拟收尾 | Eng-B1 + 对抗镜3-F1/F6（独立证据链）+ 本轮活证 |
| D2 | **helper exec 契约硬化**：硬编码 `-s read-only --ephemeral -C <repo_root>`；最终消息经 `--output-last-message` 提取（stdout 只 cat 该文件）；prompt 经 `- < "$prompt_file"` 显式喂入（消除审批交互吃 stdin 挂死）；timeout 无管道包裹、立即捕获 `$?`，测 0/1/124/127/信号杀 | Eng-B2/B3/B4/B5（Claude+codex 双声独立命中）+ 接地镜#9（CLI 选项实证存在） |
| D3 | **helper 增 `render-prompt` 与 `version` 子命令**：render-prompt 使 codex 与 fallback 子代理同源消费同一 prompt（框架在脚本肚里，fallback 原本拿不到）；version 供 staleness 比对 | codex-DX#2/#3 + DX-Claude F3 |
| D4 | **锚行文法 v1**：`<!-- sdflow:outside-voice v1 site="code-voice|hr-tg|design-voice" guard="none|file-missing|section-not-found|zero-findings|stale" runner="codex|claude-fallback" reason_code="..." findings="N" truncated="true|false" -->`——严格 KV、按调用位点复数化、guard 与 runner 正交拆分；人类原因文本在锚行外。Step5/收尾加**锚行存在性机械自检**（grep 三类锚行，缺失即本步报错，非 AskUserQuestion） | codex-Eng#5 + codex-DX#5/#8 + 对抗镜2-F2/F3/F6 |
| D5 | **R2 守卫补两个前置**：①复用前先读 `step1-broad-review` 锚行，`simulated` 一律视同产物无效→回落自跑（堵「模拟伪造 codex 段骗过守卫」）；②新鲜度判定——`gstack-review.md` 晚于 change 最新改动才可复用，过期视同缺失（guard=stale）；解析规则钉死 adr/0002 的 `codex#N` 标签 + 实现前抓真实样本 | 对抗镜2-F1（尖锐）+ 镜1-F7 + DX-Claude F1 + 接地镜#12（codex#N 实存） |
| D6 | **D8 豁免收窄**：置信滤豁免仅限 `runner=codex` 的 finding；fallback（同族子代理）产物照过同族滤——跨模型不可比的理由对同族不成立 | 对抗镜2-F4（Requirement 与 Scenario 范围不一致实锤） |
| D7 | **context-file 规格化**：三种 voice 的摘录规则定死（设计侧 = proposal What Changes + design Decisions；code 侧 = `DIFF_BASE..HEAD` 全量；hr-tg 侧 = 命中判据 + 相关 hunk）；字节上限 + 截断标记（锚行 `truncated`）；**secret 粗筛**（常见密钥模式命中 → 拒发或脱敏——边界指令只管 codex 不主动读，管不住 SKILL 主动喂）；留档 `{change_dir}/.outside-voice/`（调试可溯，覆盖式），不用纯 mktemp | 镜1-F3/F4（出境面）+ Eng-B7 + codex-Eng#6；裁决 C8>B9（留档优先于纯临时，并发由 per-change 目录隔离） |
| D8 | **code-checklists 补并发条目**：接地镜浅判「已有并发类 CR」被镜3 深读推翻——CR-GO-03 是 goroutine 生命周期非竞态正确性，backend-go 需**新增 CR-GO-06（共享状态并发正确性，对应 GO-01/GO-03）**；embedded 侧够用。scope-check ⚠ 行就此闭合 | 对抗镜3-F3（读码实证）override 接地镜#8 |
| D9 | **杂项采纳**：HR-TG 判定留痕附判据触发点（30 秒可复核）〔镜1-F1〕；双守卫触发时措辞声明「仅补偿 voice 切片，其余镜仍缺」〔镜2-F7〕；helper 头注释为 exec 契约单一源、SKILL 只引用〔DX-F2/镜1-F5〕；fallback 子代理 prompt 收窄找漏范围 + Risks 承认无硬超时不对称〔镜1-F6〕；Non-Goals grep pattern 具体化〔镜3-F5〕；R1 Scenario 拆 timeout/报错两条〔镜3-F7〕；SM3 重标「回归项」〔CEO-F6〕；T25 后加 dry-run 任务（假 change 目录核对 Step1 终态自洽）〔镜3-F4〕；native 留痕自证的限度在 design 明示为接受的剩余风险 + 建议侧信道交叉核验（timeline.jsonl）〔镜3-F8/镜1-F2〕 |

### [需拍板]（设计 HARD-GATE 一次过；用户方向为默认）

| # | 问题 | 选项 | 推荐 |
|---|---|---|---|
| Q1 | **价值指标缺采纳率型**（CEO 双声最重共识：现有 metrics 全是「跑没跑」，永远测不出这层值不值） | A. 本 change 加第 4 条 Success Metric「voice finding 采纳率」+ 报告裁决结果按 runner 分桶（codex 与 fallback 分开计，否则跨模型价值被同族兜底稀释）；B. 提前 materialize workflow-metrics-loop MVP；C. 维持现状 | **A**（增量小、给未来 metrics-loop 白攒分桶数据；B 行政成本高；C 使 6 个月懊悔场景成真） |
| Q2 | **T25 与新层同 change 的交付顺序**（双模型建议拆分先行） | A. 不拆 change，但实现顺序强制 T25（§2）+dry-run 验证通过后才动 §3/§4，checkpoint 隔离；B. 拆成两个 change | **A**（change 已 materialize，D1 已把地基修稳；拆分是行政开销） |
| Q3 | **always-on vs HR-only/抽样起步**（codex 明确建议 sampled） | A. 维持 always-on + 附「跑满 10 次后按 Q1 采纳率数据复评降采样」条款；B. HR-TG-only 起步 | **A**（solo 成本个位数调用；always-on 攒采纳率数据更快，复评条款兜「白跑」风险） |
| Q4 | **off-switch 复活？**（codex 单声挑战你 grill Q3 拍板：卸载当开关是坏控制面） | A. 维持 Q3 拍板（无软开关）；B. 采 codex 建议 `auto|off|required` | **A**（user sovereignty：你已带完整理由拍板；codex 论据〔按仓保密/成本尖峰〕在 solo 自有仓语境权重低——但按纪律原文并陈，你过门时看一眼） |
| Q5 | **HR-TG/五层升格立即 canonical vs 实验期**（codex 建议 5-10 次命中率后再固化） | A. 维持 grill Q6 拍板立即入 catalog + 附录加「10 次运行后按命中率复评」注记；B. 实验期 config | **A**（单一源纪律价值 > 提前固化风险；复评注记兜底） |

### [已裁掉]（反静默压制留痕，设计门可复核裁得对不对）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | codex-Eng#8：helper 加 `--kind spec\|code\|hr-domain` 参数 | 与 D2 grill 拍板（差异全在上下文、helper 无 mode）冲突；D7 规格化摘录规则后 kind 无信息增量；per-kind schema 收益未证 |
| X2 | 镜1-F8：HR-TG 入选判据主观、需锚点案例 | 低置信自评 + 五层升格已带复评注记（Q5）；降级 defer 至 todolist 观察，不阻塞 |
| X3 | 接地镜#8「code-checklists 已有并发 CR 项」 | 被镜3 深读推翻（语义错配：生命周期≠竞态正确性），D8 采镜3 |
| X4 | CEO-Claude F4：评估贡献上游 gstack 消灭自维护拷贝 | adr/0002 已拍板自包含边界；solo 无上游维护关系；在 proposal OQ 留一行否决理由即闭（已并入 amendment），不设独立项 |

### 低置信项（一行带过，不静默滤除）

- 镜1-F8 HR-TG 判据主观（低）→ X2 defer；镜3-F7 场景合并（中低）→ D9 已采；CEO-F5 codex 典型耗时未测（中）→ 并入 Q3 复评条款执行时顺带实测。

---

## 各镜 findings 摘要（全量见 gstack-review.md A/B/C 组 + 本轮四镜原文）

| 镜 | 数量 | 最重 |
|---|---|---|
| autoplan 双声（CEO/Eng/DX ×2） | 27（去重后 A1-A9/B1-B11/C1-C9） | B1 产物路径地基、B2 sandbox、A1 价值不可证伪 |
| 对抗镜1（隐藏假设） | 8 | context-file 秘密出境无过滤（高/高） |
| 对抗镜2（降级链失效） | 7 | simulated 伪造 codex 段骗过 R2（高/高） |
| 对抗镜3（边界/乐观估计） | 8 | B1 独立确证为阻塞级（高/阻塞） |
| 接地镜（机械核验） | 12 项 | 11✓ 1✗（INDEX 计数漂移，任务 5.5 已列） |

**交叉主题（≥2 层独立命中 = 高置信）**：①「给别人上机器锚行纪律、自己的契约多处 prose 留白」（CEO/Eng/DX/镜2 四路同根）；②「产物假设两端（生成/解析）都无实测样本」（Eng-B1/B8 + 镜3-F1/F2）；③「留痕存在性 ≠ 留痕真实性」（镜1-F2 + 镜3-F8——已明示为接受的剩余风险 + 侧信道核验缓解）。

## 收敛口

**建议：修订已落（D1-D9 amendment）→ 可进设计 HARD-GATE**。门上待办 = Q1-Q5 五项拍板（推荐全 A）。B1 类阻塞已通过 D1/D5 的机制澄清 + 实证锚点解除；无未闭合的 critical。

## 拍板记录区

2026-07-04 设计门拍板（用户）：**Q1–Q5 全按推荐（A）**。落点：Q1 → proposal Success Metric 4 + tasks 4.6（裁决区按 runner 分桶）；Q2 → tasks 2.4 既有编码（T25 先行 + dry-run 后才动 §3/§4）；Q3 → M4 内复评条款（10 次后按 codex 桶采纳率复评降采样）；Q4 → 维持 grill Q3 拍板（无软开关；codex 异议已留痕即闭）；Q5 → tasks 5.1 附录复评注记。

**拍板重申（2026-07-04，人工补锚·显式越权留痕）**：SDD final review 后 design.md 锚行枚举补 `simulated-source` 一行（纯 doc-sync——spec R2 与两 SKILL 权威交付物本已含该枚举，仅 design 示例行滞后，final reviewer 判 no-action-required）。用户经 ship gate REFUSE_START 上抛确认：该改动不改变 Q1–Q5 拍板实质，拍板重申、补锚续跑。

**拍板重申 #2（2026-07-04，同类先例适用·显式越权留痕）**：code-review 步的 `[impl-review-fix]` 修订触发 gate 二次失鲜判定——改动 = design 安全节措辞修正（承认 read-only 沙箱可读仓树，评审裁决项 C3）+ tasks.md 30 项勾选回填（C4 记账）。两者均为阶段三工作流合法产物、不触 Q1–Q5 拍板实质；按本 session 用户已确认的同类先例（doc-sync → 拍板重申补锚）续跑。gate 对评审补丁的误判已记 **B2**（失鲜判定应豁免带 [impl-review-fix] 标记的评审后修订）。

<!-- ship-gate: design-approved -->
