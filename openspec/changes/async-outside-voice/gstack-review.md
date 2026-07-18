<!-- sdflow:step1-broad-review v1 mode="simulated" -->

# async-outside-voice · Step1 广审（simulated 降级）

> **mode=simulated 的诚实声明**：autoplan skill **可用**，但对本 change 类型**架构性不匹配**——autoplan 是 gstack 产品评审管线（CEO/design/eng/DX 镜），以 `~/.gstack/projects/*/…-design-*.md` 计划文件为输入（autoplan SKILL line 895-897），而本 change 是 OpenSpec workflow-orchestration 变更、无 gstack 计划文件，其产品镜与基础设施编排不对味。故 Step1 走**主 session 派一个 fresh-context 冷广审子代理**（sonnet），而非硬套产品管线。**未伪装原生**（`mode="simulated"`），下游 `outside_voice_guard` 会据此判 `simulated-source` → Step2 自跑 design-voice（正确路径）。

冷广审子代理产出 7 条 findings（进 Step3 合并池对抗裁决）：

## B1 — collect「不阻塞」依赖未定义的轮询原语（核心不确定项）
- **证据**：design ADR-3(L34-37)「collect @Step3 轮询后台任务到它自己终止」；序列图(L51-68)；tasks §3.1(L16)。全篇未指定「轮询」在 SKILL Markdown 编排层落成什么工具调用序列。
- **风险**：本 change 全部收益系于「dispatch 秒返 + collect 不再单次超长阻塞」。若某次评审把「轮询」退化成一次性 `sleep 900`，就在 collect 点复现「外层单次阻塞」——即本 change 要消灭的 bug 换调用点复现。tasks §4.1/4.3 验证只「观察 reason_code=ok / 模拟」，未把 collect 实现钉成可审指令。
- 置信 中 · severity **高（阻塞级）**
- 建议：design/tasks 补「collect MUST 用非阻塞轮询原语、单次检查 MUST NOT 超秒级、MUST NOT 单次长 sleep 模拟等待」；smoke(4.1) 验收加严为「同时核验 collect 期间无单次 Bash 调用 > 明确阈值(如 30s)」。

## B2 — ADR-6 / A2 证据引用与实际文本不符，Q2 非「已解」而全靠 1.3 自探兜底
- **证据**：ADR-6(L47-48) 引「ship line 101『主 session inline 执行』」证 code-review inline。但 ship line 101 该短语字面指 `sdflow-implement mode=tickets-plan` 的派发方式，**不是** `RUN_CODE_REVIEW→/sdflow-code-review`；后者同行只写映射、无 inline/子代理注记。结论（code-review 跑主 session）大概率仍成立（靠 line 96「ship 自身不直接派子代理」泛化陈述），但具体到 code-review 步「确实 inline」的证据链不如 ADR-6 呈现得扎实。
- 置信 高（读码核实）· severity 中（1.3/2.1 自探降级是独立 fail-safe）
- 建议：ADR-6 措辞从「读码已解」改为「读码强烈提示但无逐字直接证据；1.3/2.1 自探因此不是『兜底未来漂移』的冗余，而是当前验证 A2 的实际防线」——不改机制、更诚实反映证据强度。
- **主审注**：本条挑战主审自己的 ADR-6，Step3 grounding 镜 MUST 亲自核 ship line 96/101 定夺。

## B3 — 「起了没收无孤儿危害」只论进程生命周期，未论跨会话文件竞态 + 遗弃完成 token 浪费
- **证据**：design 并发节(L90-93)「reparent PID1 自行跑完无害」+ (L84)「context 文件站点间不共写」。context 文件协议 = 固定命名、下轮覆盖、不删（两 SKILL ~L272/270）。
- **风险**：run_in_background 专门让子进程跨会话/中止存活——这把「上轮 voice 未 collect 仍在跑、下轮对同一固定路径 `{change_dir}/.outside-voice/hr-tg-context.md` 重写」的竞态窗口从「不存在」（同步旧模型：中止=进程随之死）变成「存在」。若 outside-voice.sh 运行期间可能重读 context → TOCTOU。另：遗弃但跑完的 voice 消耗**完整 token**且结果永不被读，比「300s 被杀部分消耗」更浪费，proposal Cost(L56-58) 未覆盖此第三态。
- 置信 中 · severity 中
- 建议：① design 补 outside-voice.sh 读 context 文件时机声明（一次性读入 vs 运行期重读）；若一次性读入则竞态窗极窄可接受，需显式写明入契约。② Cost 补「孤儿完成未 collect」token 浪费声明（即便标可接受也须显式承认）。

## B4 — Why 与 Success Metrics 的 scope 落差易让人误判「efficacy=0 已解」
- **证据**：Why(L3) 把 Codex 3/3 timeout + Claude→codex 超时并列为动机；Success Metrics(L29-33) 只写 Claude 宿主验收，「Codex 方向仍 efficacy=0」只在 Non-Goals(L38)。只读 Why+Metrics（常见汇报场景）易得「efficacy=0 已解决」错觉——尤其 Why 直接引了最触目的 Codex 3/3 数字，而该方向本 change 后仍是 0。
- 置信 高 · severity 中
- 建议：Success Metrics 补一条负向断言「Codex 宿主方向 reason_code 仍 timeout（efficacy 仍 0），非回归、是已知未解范围（见 Non-Goals）」——把「没解决什么」也列入验收。

## B5 — ADR-5 夹带「现状论」式理由，与目标态基准有措辞摩擦
- **证据**：ADR-5(L44-45)「两 SKILL 本就各有一份(既有重复)，本 change 循既有形态最小改动」——形式上是拿现状支撑「不做全抽取」，贴近通则③禁止项。真正站得住的理由（抽取需新建 include 机制=越 scope）同 ADR 已有。
- 置信 高 · severity 低
- 建议：删/改「本就各有一份(既有重复)」为纯事实陈述、不作决策依据，只留「抽取需新建机制、超一个完整交付物范围」作 defer 唯一理由。

## B6 — A1「已验风险低」的验证时长可能不覆盖 900s 天花板量级
- **证据**：A1(L52) spike 证「reparent PID1 跑到完成 + run_in_background poll 无缝」；memory 原文未注 sleep 时长；本 change 天花板默认 900s(tasks §3.3 L18)。A1 验的是「跨 tool call 二元存活」，不代表「900s 量级仍稳定」（会话级资源回收/后台任务上限/harness 静默清理超长任务，多在长时长下才暴露）。
- 置信 低-中 · severity 低-中
- 建议：smoke(4.1) 不止步「reason_code=ok」，刻意构造 voice 时长逼近天花板场景，实测接近 900s 量级下可靠存活+可 collect。

## B7 — config 读取路径留「impl 定」，但仓内已有先例可设计阶段拍板
- **证据**：tasks §3.3(L18)「读取路径 resolve-* 导出 vs SKILL 直读 impl 定」。仓内先例：`metrics.enabled` 是 SKILL 直读 config.yaml（spec-review L179 / code-review L206）。若两 SKILL 各选不同路径 → 机械等值门首跑即红、多一轮返工。
- 置信 高 · severity 低
- 建议：design 直接拍「沿用 metrics.enabled 先例，SKILL 直读 config.yaml」，消除本可设计阶段拍板的开放项。
