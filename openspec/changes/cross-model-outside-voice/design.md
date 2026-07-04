# Design: cross-model-outside-voice（Phase C）

## Context

评审独立性现状 = fresh-context 同模型子代理（盲区同处）；`adr/0006` 锚定混编机队（opus/sonnet/gpt-5.5）后，跨家族 outside voice 既天然可得（机队里本来就有 GPT）又更必要（弱主模型兜底）。机制蓝本来自归档 design §9（streamline-workflow-automation，含 grill-amendment 两道焊缝），本 change 是其 Phase C 落地。前置耦合：sdflow-spec-review / sdflow-code-review 的 Step1 广审目前被「子代理读 SKILL.md 模拟执行」替换（T25，两轮运行实证自报偏离）——C2「复用 autoplan 产物」的前提是产物为真，故 T25 修复收进本 change。

现状锚点（已核验）：
- `sdflow-spec-review/SKILL.md:35-39` Step1 autoplan 子步已有反静默守卫「显形部分」+〔Phase C 补〕占位注（本 change 兑现）；`SKILL.md:41` Step2 = 规划镜头 + fan-out。
- `sdflow-code-review/SKILL.md:58-62` Step1 gstack/review 子步（显式降级已有）；`SKILL.md:64-66` Step2 规划镜头。
- 全局 hack 家已有 `checkpoint-commit.sh`、`resolve-workflow.sh`（源 = `sdflow-init/assets/hack/`，setup.sh 拷入 `~/.sdflow/hack/`）——新 helper 同家同机制。
- trigger-catalog 现有 TG-01~25，TG-26 为下一空号；`openspec/INDEX.md:16` 写「TG-01~24」存在既有计数漂移（本次一并修）。

## Goals / Non-Goals

**Goals:**
- C1/C6：自包含 codex helper（preflight + exec 包装 + prompt 框架）+ Claude 子代理 fallback，全程非阻塞（无软开关，grill Q3）[gstack-amendment]。
- C2/C7：spec-review 复用 autoplan outside-voice findings + 反静默守卫回落；gstack 边界守恒（读产出物 ✓ 依赖内部 ✗）。
- C3：code-review 自带 code outside voice（always）。
- C4：HR-TG 判定 + TG-26 入 catalog（四列 + 消费方引用 + INDEX 计数）。
- C5：tension 适配（spec→决策登记区 / code→自动裁决或 defer），守 user sovereignty。
- T25：Step1 广审原生执行；模拟降级必须显式标注。

**Non-Goals:**（详见 proposal，均附可证伪假设）不改 gstack 内部；不做 codex 镜位；不新造风险分级；不含 T26 与 setup.sh 加固批次。

## Decisions（决策记录，TG-23）

### D1. helper = 全局家 bash 单脚本 `outside-voice.sh`
- **选中**：源 `sdflow-init/assets/hack/outside-voice.sh` → setup.sh 拷入 `~/.sdflow/hack/`（与 checkpoint-commit.sh / resolve-workflow.sh 同家同机制）；测试走 pytest subprocess 跑 bash（resolver 既有先例）。
- **备选**：①Python 脚本——测试更顺，但 hack/ 家先例全 bash、SKILL prose 直调 bash 链最短，未选；②放某 skill 的 `scripts/`——两 review skill 共享，仓内放谁家都造成另一家跨目录引用，全局家消除该耦合，未选。
- **代价**：改 assets/hack/ 后必须重跑 setup.sh（copy 非 symlink，CLAUDE.md 已有此纪律）。

### D2. helper 接口 = 子命令 + 结构化退出码（adr/0006(b) prose 脚本化）〔grill-amendment: prompt 归属两层拆分〕
- **选中**：`outside-voice.sh preflight` → stdout 单词 mode（exit 0）；`outside-voice.sh exec --context-file <f> [--timeout 300]` → codex findings 原样到 stdout（exit 0），超时 exit 124、codex 报错 exit 1（stderr 转发）。SKILL.md 只剩「跑脚本 → 按 mode/exit code 分支」。
- **preflight 浅探针二态（grill Q2/Q3 拍板）**：`not_installed | ready`——砍掉归档设计照搬的 `not_authed` 深探：试跑判 auth = 每次评审白烧一次真调用 + 对 codex stderr 的脆模式匹配（CLI 升级即漂移）。auth 失败由 exec 阶段自然暴露（exit 1 + stderr 转发），走同一条回落链，报告留痕「exec 失败（stderr 摘要）」——可观测性等价、原因可见。
- **exec 契约硬化〔spec-review-amendment，Eng 双声共识〕**：①硬编码 `codex exec -C "$repo_root" -s read-only --ephemeral`（只读从 prompt 自觉升为 CLI 强制，--ephemeral 免会话残留）；②最终消息经 `--output-last-message <tmpfile>` 提取，helper stdout 只 `cat` 该文件（codex 裸 stdout 混推理/事件噪声，不是干净 findings 通道）；③prompt 显式 `- < "$prompt_file"` 喂入（stdin 被 prompt 耗尽后审批交互无从读取的挂死面，已被 read-only 消除，仍显式化防回归）；④`timeout` 无管道包裹、紧邻捕获 `$?`，测试覆盖 0/1/124/127/信号杀（124 经管道/子进程易丢）。
- **子命令补两个〔spec-review-amendment〕**：`render-prompt --context-file <f>` 输出「框架+上下文」拼接结果——codex 与 fallback 子代理**同源消费**同一 prompt（原设计 fallback 拿不到脚本肚里的框架，「同 prompt 派子代理」落空）；`version` 输出源内嵌版本串，供 staleness 比对（`[ -x ]` 挡不住旧版本）。exec 契约全文写进脚本头注释（resolve-workflow.sh 先例），两 SKILL 只引用不转述——契约单一源。
- **prompt 归属（grill Q1 拍板）**：**框架归 helper、上下文归 SKILL**——「找漏」框定 + 文件系统边界指令以 heredoc 内嵌 helper（安全措辞不依赖调用方自觉，忘传即无边界的失效被结构性消除）；SKILL 经 `--context-file` 传评审对象上下文（设计四件套摘录 / code diff / 命中的 HR-TG 域）；helper 拼接「框架 + 上下文」经 stdin 喂 `codex exec`（stdin 喂法已核验，codex-cli 0.142.5）。设计/代码/领域三种 voice 差异全在上下文，helper 无 mode 参数。
- **边界**：fallback「派 fresh Claude 子代理」是模型动作（Task 调度），不进脚本；脚本只管探测/调用/超时这些机械段——机械活交脚本、模型只做判断。
- **备选**：单命令自动内部 fallback（脚本里没法派子代理，必然做半截）——未选。

### D3. 不设 off-switch——启停由环境层决定〔grill-amendment Q3 拍板〕
- **选中**：工作流层**不提供任何软开关**（env / config 均不做）。出境同意在安装 + 认证 codex CLI 那一刻已成立（该 CLI 的唯一用途就是把代码发给 OpenAI），工作流只是复用一条环境已同意的通道；「不想出境」的机器/CI 不装 codex 即天然关停（preflight `not_installed` → 回落子代理，留痕）。preflight 随之缩为**二态** `not_installed | ready`。
- **备选**：①env `SDFLOW_CODEX_VOICE=off` 单轨（原稿）——靠人记忆或 shell profile，粒度错位，未选；②config.yaml 仓级 + env 双层 fail-closed（grill 中间稿）——为环境层职责在工作流层造开关，未选。归档 design 的 off-switch 项（自 gstack 提炼）随之裁掉，不再是 C1/C6 交付物。
- **接受的剩余风险**：混用机器上某仓想单独关无软手段（codex 抽风时也无快捷止损，最坏每调用等 300s 超时后回落）——接受，属环境层问题；真成痛点再评估，不预付复杂度。

### D4. T25 修复路径 = 主 session 原生执行 + **主 session 汇总落盘**（①），模拟仅显式降级（③）〔spec-review-amendment: 机制澄清〕
- **选中**：Step1 由主 session 经 Skill 机制原生执行 autoplan / gstack review（指令直接进主 session，非子代理转述），**执行完由主 session 自行汇总结论 Write 落盘 `{change_dir}/gstack-review.md`**——autoplan 原生机制只写 plan file（plan-mode 产物），**没有**「写任意路径」能力，落盘责任在编排方（评审揭穿：原稿把落盘默认给了 autoplan）。原「sdflow-ship 先例」引用文不对题（那是 gstack /review 非 autoplan）——撤销，改锚**本 change spec-review 2026-07-04 本轮实证**：原生执行 + 主 session 落盘全链路跑通；autoplan 的两处 AskUserQuestion 人类门按 G2/C5 适配登记进报告决策区（同轮实证）。与 T20 串行纪律天然兼容。原生不可用 → ③模拟广审 + 报告显式标注「模拟广审（降级模式）」。
- **假设三态**〔spec-review-amendment〕：机制可用 / **可用但产物不落编排期望路径**（本条即其修复）/ 不可用——旧假设二元模型漏掉了已实际发生的中间态。
- **备选**：②gstack headless 调用路径——P2 调研；**升级条款**：若①实测不可行，headless 升 P0 阻塞项，不得只靠③模拟收尾（防「合规地永远 simulated」）。
- **两 skill 同修**：sdflow-code-review Step1 的 gstack/review 同构问题按同路径改。
- **留痕自证的限度（接受的剩余风险）**：`step1-broad-review` 锚行由执行者自写，防无意误判有效、防伪装无效；缓解 = 报告附侧信道交叉核验（如 gstack timeline.jsonl 的 autoplan started/completed 事件）。

### D5. HR-TG 子集单一源 = trigger-catalog 附录段，且 catalog 升格五层〔grill-amendment Q6〕
- **选中**：trigger-catalog.md 新增「HR-TG 子集」附录（成员 {TG-04/06/07/08/09/16/17/26} + 入选判据「做错会运行期爆炸/数据损坏/安全泄漏且难回退」）；两 SKILL 的规划镜头步只引用 ID 集合，不复制清单。
- **五层升格（grill Q6 拍板）**：评审 cross-model 事实上是 catalog 第五消费维度，维护协议 MUST 同步，否则未来新 TG 无机制提醒判 HR、子集「未列入」型腐烂（BASE-29 语义）：①自述「四层」→「五层」；②「四、消费方」表加行（评审 cross-model | 消费方 = 两 review skill 规划镜头 | 引用 HR-TG 附录 ID 集）；③「五、扩展约定」加一条——新增触发 MUST 显式判定是否入 HR-TG（是/否都写，不许空着）；④「六、检查清单」加对应核对项。
- **备选**：①写死两 SKILL.md（两份副本必漂移，ff-generation-constraints 背景一节实证过的反模式）——未选；②附录不入维护协议（低调姿态，靠人记得判 HR）——grill Q6 揭穿即「未列入」型漂移温床，未选。

### D6. TG-26 四列定义（归类 D. 行为/状态）
| ID | 触发条件 | D约束 | 领域 | 画图 | 模版槽 |
|----|---------|-------|------|------|--------|
| TG-26 | **并发 / 共享可变状态**（多线程/多任务/ISR/goroutine 竞争读写同一状态） | — | backend-go·GO-01/GO-03 或 embedded·EMB-01/EMB-10(+芯片 delta)（按栈） | 序列图（竞态交互时序） | design: 并发与共享状态访问策略（挂 domain 既有 T 项，不新增 BASE） |

领域列锚点已核验：GO-01（goroutine 并发与同步）/GO-03（TOCTOU）、EMB-01（受限回调上下文）/EMB-10（volatile/内存可见性）、ML307C-01、ESP32-02 均为既有条目。

### D8. outside-voice findings 豁免自评置信滤，直通对抗裁决〔grill-amendment Q4 拍板〕
- **选中**：code-review Step3 的「<80 置信滤」**只作用于同族镜 findings**；outside-voice findings 跳过置信滤、一律直通对抗裁决（有把握裁决记理由 / 拿不准 defer），被裁掉的连理由落报告「已裁掉」区（反静默压制既有机制）。
- **豁免收窄〔spec-review-amendment〕**：豁免**仅限 `runner=codex`** 的 finding；fallback（同族 Claude 子代理）产物照过同族置信滤——「跨模型不可比」的豁免理由对同族不成立，否则低质量 fallback finding 永久绕滤占裁决位。
- **理由**：①T8 已实证同族阈值尚且跨模型不可比，拿 Claude 校准的 80 筛 GPT 自评纯属噪声；②outside voice 价值在异见，用同族标尺筛异见 = 结构性自我审查，违反「任何一层评审覆盖不得无声蒸发」元原则；③单次 voice findings 量级个位数，粗筛降噪收益不存在。
- **边界**：不动 T8 本身（同族阈值改判据留其自身的债）。

### D7. prompt 框架内嵌 helper（heredoc），不另立文件〔grill-amendment: 与 D2 两层拆分对齐〕
- **选中**：「找漏」框定 +「文件系统边界」指令（框架层，~1KB）heredoc 内嵌，helper 单文件自包含；评审对象上下文**不在此列**——由 SKILL 经 `--context-file` 传入（见 D2）。
- **备选**：①独立模板文件进 `~/.sdflow/hack/`——多一个部署物、多一处路径解析失败模式，未选；②prompt 全由 SKILL 组装——文件系统边界指令沦为「靠调用方记得写」的 prose 协议，违反 adr/0006(b)，未选（grill Q1 揭穿的原 D2/D7 矛盾即由此消解）。
- **context-file 规格〔spec-review-amendment：原设计留白，实现期自由发挥点收编〕**：
  - 摘录规则定死：设计 voice = proposal「What Changes」+ design「Decisions」段；code voice = `DIFF_BASE..HEAD` diff 全量；hr-tg voice = 命中 TG 的判据触发点 + 相关 diff hunk。
  - **预算契约**：字节上限（缺省 200KB，helper 内截断保头尾）+ 锚行 `truncated` 字段留痕——大 diff 静默变「partial voice」是反静默同构。
  - **secret 粗筛**：构造后、发送前过常见密钥模式（AWS key / PEM 头 / `password=` 类正则），命中 → 拒发该次 voice 并留痕（guard=secret-hit 归入 reason_code）——文件系统边界指令只管 codex 不主动读，**管不住 SKILL 主动喂**（对抗镜1 揭穿的出境面另一半）。
  - **留档**：写 `{change_dir}/.outside-voice/<site>-context.md`（固定命名、下轮覆盖、不删）——voice 产出文不对题时可回溯「当时到底发了什么」；并发隔离由 per-change 目录天然提供（裁决：调试可溯 > 纯 mktemp 即弃）。

## 组件清单（BASE-25）

| 组件 | 职责 | 技术栈 | 部署 |
|------|------|--------|------|
| `outside-voice.sh` | preflight 二态探测 / codex exec 包装（超时、stderr 转发）/ prompt 框架内嵌 | Bash | `sdflow-init/assets/hack/` → setup.sh → `~/.sdflow/hack/` |
| sdflow-spec-review Step1' | 原生执行 autoplan + 复用 outside-voice findings + 反静默守卫回落 | SKILL.md prose（判断层） | 仓根 skill 目录（symlink 安装） |
| sdflow-spec-review 规划镜头' | 顺带 HR-TG 判定 + 留痕 | SKILL.md prose | 同上 |
| sdflow-code-review Step1' | 原生执行 gstack /review（同构修复） | SKILL.md prose | 同上 |
| sdflow-code-review outside-voice 子步（新） | always code voice + HR-TG 领域 cross-model | SKILL.md prose 调 helper | 同上 |
| trigger-catalog.md（bundle 源） | TG-26 四列 + HR-TG 附录 | Markdown | `sdflow-init/assets/workflow/` → canonical → 消费仓 update |
| tests | preflight 二态 / exec 超时与退出码 [gstack-amendment] | pytest subprocess | `sdflow-init/tests/` |

## 组件/依赖图（TG-14）

```
  sdflow-spec-review ──┐                       ┌─→ codex CLI ─→ GPT（外部计费）
  (Step1'/规划镜头')    ├─→ ~/.sdflow/hack/ ────┤
  sdflow-code-review ──┘   outside-voice.sh    └─(非 ready/超时)→ exit code
  (voice 子步/Step1')            ▲                      │
        │                        │ setup.sh 拷入         ▼ SKILL 按码分支
        │ 读(产物,只读)     sdflow-init/assets/hack/   fresh Claude 子代理(fallback)
        ▼
  gstack-review.md ←─ autoplan(gstack 原生,不动) ←─ Step1' 主 session 原生执行
```

## 序列图（TG-10：code-review outside-voice 子步）

```
  主session          outside-voice.sh        codex CLI         Claude子代理
     │ preflight ────────→│                      │                  │
     │←─ mode ────────────│ (command -v;         │                  │
     │                    │  不试跑、无软开关)     │                  │
     │ [ready] exec ─────→│─ prompt(找漏+边界) ──→│                  │
     │←─ findings(stdout)─│←─ stdout(5min封顶) ──│                  │
     │ [非ready/124/1] ───────────────────────────────同prompt────→│
     │←──────────────────────────────────────────── findings ──────│
     │ findings 进合并池 + 报告 outside-voice 段留痕(四态之一)         │
```

## 决策图（TG-12：preflight/守卫回落链）

```
  codex 装了?(command -v) ──否──→ not_installed → fallback Claude 子代理(留痕)
        │是(ready；auth 不预探,exec 段暴露〔grill Q2〕)
  exec 5min 内返回? ──否(124/1)──→ fallback Claude 子代理(留痕原因)
        │是
  findings 进合并池(留痕"已跑 codex")

  〔spec-review 专属前置〕gstack-review.md 在? 解析出 codex 段? 条数>0?
        任一否 → 显式降级日志 → 回落自跑设计 voice(进上面的链)
        全是   → 复用不重开(留痕"复用 N 条")
```

## 失败模式表（BASE-06，D-4）

外部依赖声明：codex CLI 调用超时 **300s（5min）封顶**；本机制全程**只读**（读 diff/产物、发 prompt、收文本），无外部写操作，回滚路径不适用（N/A，声明依据：helper 不落盘、不改仓）。

| 失败模式 | 触发条件 | 处理者 | 用户可见行为 | 测试 |
|---------|---------|--------|------------|------|
| codex 未安装 | `command -v codex` 失败 | preflight → SKILL | 报告留痕「not_installed → 已回落子代理」 | pytest |
| codex 未认证 | exec 阶段 auth 报错 | helper exit 1 + stderr 转发 → SKILL | 回落子代理，留痕 stderr 摘要（含 auth 原因）〔grill Q2：不预探〕 | pytest（假 codex 非零退出） |
| exec 超时 | >300s | helper exit 124 → SKILL | 回落子代理，留痕「超时」 | pytest（sleep 假 codex） |
| exec 报错 | codex 非零退出 | helper exit 1 + stderr 转发 → SKILL | 回落子代理，留痕 stderr 摘要 | pytest |
| helper 缺失 | 未跑 setup.sh | SKILL `[ -x ]` 前置检查 | 显式提示「先在运行 checkout 跑 setup.sh」+ 回落子代理，不静默 | SKILL 步骤核验 |
| gstack-review.md 缺失/0 条 | autoplan 未跑或格式漂移 | spec-review 守卫 | 显式降级日志（原因码 file-missing/section-not-found/zero-findings 三分）+ 回落自跑设计 voice | 冒烟 §8.3 |
| gstack-review.md 过期〔spec-review-amendment〕 | 产物早于 change 最新改动（断点续跑/改码后重审） | spec-review 守卫（新鲜度判定） | guard=stale 视同缺失 → 回落自跑，不静默复用旧盘 | 冒烟 |
| gstack-review.md 来自模拟广审〔spec-review-amendment〕 | step1 锚行 mode=simulated | spec-review 守卫（来源前置检查） | 视同产物无效 → 回落自跑（堵「模拟臆造 codex 段骗过守卫」） | 冒烟 |
| context 超预算〔spec-review-amendment〕 | 大 diff 超字节上限 | helper 截断 | 保头尾截断 + 锚行 truncated=true 留痕 | pytest |
| secret 粗筛命中〔spec-review-amendment〕 | context-file 含密钥模式 | SKILL 构造侧 | 拒发该次 voice + reason_code=secret-hit 留痕 | pytest |
| autoplan 原生执行不可用 | skill 未安装 | Step1' | 模拟广审 + 显式标注「降级模式」 | 冒烟 |
| timeout/gtimeout 缺失 | 环境未装 GNU coreutils（macOS 常见） | preflight missing-deps / exec 显式报错 | 报告留痕 reason_code 可诊断，不与 codex 报错混淆 | pytest |

## 可观测性（BASE-11）

报告 outside-voice 段为必填、**三态穷尽留痕**〔grill-amendment Q3：裁软开关后〕：已跑 codex / 已回落子代理（含原因）/ 守卫降级（含触发原因）——不存在「无记录」合法态。HR-TG 判定无论正反留痕。所有降级走显式日志，符合反静默守卫。

**机器锚行 v1（grill-amendment Q5 + spec-review-amendment 文法硬化·盘面即状态）**：留痕不押自然语言措辞——SKILL.md 模板**逐字规定**下列 HTML 注释锚行（叙述随模型写，锚行不许改），供 Success Metrics 机验与 `workflow-metrics-loop` 直接 grep。v1 修正三个评审揭穿的坑：①严格 KV（原 `reason="自由文本"`、`hit=…|none` 松散文法必漂移——人类原因文本放锚行外）；②**按调用位点复数化**（一次评审 0–4 次调用，单数「固定首行」装不下 code-voice 成功 + hr-tg 回落的组合态）；③**guard 与 runner 正交拆分**（原 `mode=guard-degraded` 塌缩「守卫为何触发」与「实际谁跑的」两个独立维度，守卫触发频率永远无法追踪）：

```
<!-- sdflow:outside-voice v1 site="code-voice|hr-tg|design-voice" guard="none|file-missing|section-not-found|zero-findings|stale|simulated-source" runner="codex|claude-fallback" reason_code="<枚举码或空>" findings="N" truncated="true|false" -->
<!-- sdflow:hr-tg v1 hit="TG-08,TG-17|none" evidence="<判据触发点一句>" -->
<!-- sdflow:step1-broad-review v1 mode="native|simulated" -->
```

**锚行存在性门禁〔spec-review-amendment〕**：两评审 skill 收尾步（Step3/Step5 出报告后）MUST 机械 grep 自检三类锚行存在，缺失即本步报错阻塞（机械可测的失职拦截，非人类门）；`findings=N` 的 N 与合并池实收条数做一次机械 diff（留痕存在性 ≠ 真实性的最低成本交叉核验）。

## 安全与数据保护（BASE-28，TG-17）

- **信任边界** = 仓库代码 → 外部 LLM（OpenAI）。发送范围 = prompt 模板 + 上下文摘录，且 codex 在 -C <repo_root> 只读沙箱内**可自行读取仓库树**（含 gitignored 文件）——「不读 .env/密钥」是 prompt 层约束非文件系统 ACL，属接受的剩余风险[impl-review-fix]；**文件系统边界指令**写进模板：不读 `~/.claude`、`~/.sdflow` 等 skill/规则定义，不读 `.env`、密钥文件，只看仓库代码。
- **总闸 = 环境层**〔grill-amendment Q3〕：是否安装/认证 codex CLI 即出境总闸——装即同意、不装即天然关停（层降级为同模型子代理而非消失）；工作流层不设软开关，不替环境层操心。
- **凭证**：codex CLI 自管 auth，helper 不接触、不落日志；stderr 转发时按行透传原文（codex CLI 自身不在 stderr 打印凭证）。
- **最小权限**：helper 只读、无网络操作自身（网络由 codex CLI 发起）。

## 契约文档套件 scope-check 表（BASE-29，TG-25：TG-26 加入牵连面）

| 文档 | 本 change 改? | 改什么 / 不改的理由 |
|------|------|------|
| `trigger-catalog.md`（assets 权威源） | ✅ | TG-26 四列（D6）+ HR-TG 子集附录（D5）+ **五层升格四处同步**（自述/消费方表/扩展约定/检查清单，grill Q6）+ 消费方表补 design-diagrams 引用 |
| `openspec/INDEX.md` | ✅ | TG 计数「TG-01~24」→「TG-01~26」（顺带修 TG-25 既有漂移）+ 描述「驱动…四层」→「五层」（grill Q6） |
| `design-diagrams.md`（assets） | ✅ | TG-26 画图列非空（序列图）→ 触发条件表加 TG-26 引用行 |
| `spec-checklists/`（base+domains） | ❌ | TG-26 模版槽挂 domain **既有** T 项（GO-01/03、EMB-01/10），不新增条目 |
| `code-checklists/` | ✅〔spec-review-amendment：⚠ 已闭〕 | 评审读码实证：backend-go 现有 CR-GO-01~05 **无一覆盖共享状态并发正确性**（CR-GO-03 是 goroutine 生命周期，非竞态）——需**新增 CR-GO-06**（对应 spec 侧 GO-01/GO-03）+ TG-26 引用；embedded 侧现有条目（CR-EMB-01/04 等）够用只补引用 |
| `ff-generation-constraints.md` | ❌ | TG-26 的 D约束列 = —（并发不满足 D 判据①「生成时主动行为」，走领域清单层） |
| `workflow.md`（assets） | ✅ | 阶段二/三步表追加 outside-voice 子步引用（归档 ROADMAP 约束1） |
| 消费仓副本 | ❌（本 change 内） | 经 `sdflow-init update` 推送，属部署动作非文档变更 |

## Risks / Trade-offs

- [codex CLI 接口/输出格式变化] → helper 是自维护拷贝，不自动继承 gstack 修复；低频可控，preflight 试跑能第一时间暴露，fallback 保底审查不断。
- [gstack-review.md 格式漂移捞 0 条] → 反静默守卫按「0 条即降级」处理——代价是 autoplan 真·零 finding 时多跑一次自查 voice（可接受：假阴性成本 ≪ 静默丢层）。
- [原生执行 autoplan 占主 session 上下文] → autoplan 指令直接进主 session 会消耗上下文窗口；T20 串行序 + checkpoint 已把 Step1 隔在 fan-out 之前，影响有界；实测超限再议 headless（OQ）。
- [跨模型 findings 质量参差] → tension 机制兜住：不静默采纳，spec 侧进决策登记区、code 侧拿不准 defer。
- [多一处全局部署物] → 忘跑 setup.sh → SKILL `[ -x ]` 前置检查显式提示（同 resolve-workflow.sh 既有模式），不静默；`[ -x ]` 挡不住「存在但陈旧」→ `version` 子命令比对兜底〔spec-review-amendment〕。
- [fallback 侧无硬超时（不对称）]〔spec-review-amendment〕 → codex 侧 300s 封顶，Task 子代理无 timeout 参数——「非阻塞」只在 codex 侧有硬保证；缓解 = fallback prompt 显式收窄范围（只找漏、不递归探索），并承认不对称而非伪装对称。
- [fallback 返回质量无下限]〔spec-review-amendment〕 → fallback prompt 加最低产出要求（findings 或「未发现+已读清单」证据）；findings=0 的 fallback 在报告额外标注供抽查。

## Migration Plan

1. dev checkout（本仓）改 assets/hack/ + assets/workflow/ + 两 SKILL.md → 跑 `bash setup.sh`（hack 是 copy 非 symlink）→ pytest + 冒烟。
2. merge 后运行 checkout `/sdflow-upgrade`（pull + setup 一体，堵窗口期）。
3. 各消费仓按需 `sdflow-init update` 刷 trigger-catalog 等规则（canonical 软链仓即时生效，规则副本 pin 仓需 update）。
4. **回滚**：运行 checkout `git checkout <上一良好 commit>` + 重跑 setup.sh（adr/0005 纪律）；helper 无状态无落盘，无数据回滚面。

## Open Questions

| 问题 | 归属 | 影响 |
|------|------|------|
| gstack headless 调用路径是否存在（T25 思路②） | 实现期 P2 调研 | 〔spec-review-amendment〕带升级条款：①原生路径实测不可行则本项升 P0 阻塞（原「不阻塞」依据的 sdflow-ship 先例已被评审证伪，现依据 = 本轮 spec-review 实证）。调研结论：codex 侧 `codex exec` 已提供 `review` 子命令与通用 headless prompt 入口可用；gstack 侧 `~/.claude/skills/gstack/bin/` 下仅有 `gstack-review-log`/`gstack-review-read` 两个日志读写辅助工具，未发现独立无头广审入口，故本 change 原生路径已实证可行 → 维持 P2 不升级。 |
| ~~code-checklists 并发 CR 项现状~~ | 已闭〔spec-review-amendment〕 | 评审读码实证：backend-go 需新增 CR-GO-06，见 scope-check 表 |
| autoplan 原生执行的上下文占用实测 | 实现期观察 | 超限才升级为问题（连 OQ headless）；本轮实证一次全量原生跑（三相位双声）可完成，量级已知 |

## Compliance（规则/边界合规声明）

- `adr/0006`(a)(b)(c)：机械段全脚本化（D2）；档位措辞不写死模型名——**遵守**。
- C7 / 归档 design §9.0 grill-amendment（读产出物 ✓ 依赖内部 ✗）：helper 零 gstack 引用——**遵守**。
- `adr/0007` 命名——**不再涉及**（D3 裁掉 env 开关后本 change 无新品牌前缀标识符，N/A）。
- `adr/0005` dev/runtime checkout 纪律（Migration 步骤 1/2/4）——**遵守**。
- bundle 权威源纪律（改 assets、update 推下游，禁只改下游）——**遵守**。
- trigger-catalog 扩展约定（新 ID 不复用、四列回填、消费方引用不复制定义）——**遵守**（D6 + scope-check 表）。
- D-6 窄条款（跨产品共享数据模型）——**不适用**（N/A）。
