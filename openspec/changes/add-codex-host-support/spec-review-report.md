<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08,TG-17" declared="TG-06,TG-08,TG-17" evidence="锚行 schema v2 是 bundle 分发给消费仓的跨仓契约(TG-06)+反向 runner 新增 claude CLI 调用(TG-08)+outside-voice context 出境新增 Anthropic 端点(TG-17)" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="file-missing" host="claude" runner="codex" reason_code="none" findings="7" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="none" findings="4" truncated="false" -->

# spec-review-report — add-codex-host-support

> **本文件是第二轮（返工后复审）报告。** 首轮（commit 4e88918）判「需返工」，返工（c9b8325）落 Q1–Q3 + D1–D10。本轮对返工后的四件套重跑一次冷审，核对返工是否真闭合 + 是否引入新洞。首轮记录见文末「附录：首轮记录」（全文在 git 历史）。

## 二次审（返工后复审 · 2026-07-15）

> **层**：spec-review（阶段二设计审 · 复审）· **对象**：add-codex-host-support（返工后，commit c9b8325）
> **镜阵**：对抗镜 ×3（fresh context 子代理：返工闭合核验 / 隐藏假设失败模式 / §0.0 自指防伪完整性）+ 接地镜 ×1（机械核验代码事实）+ **codex 跨模型 outside-voice ×2**（design-voice + hr-tg 领域镜，runner=codex ≠ host=claude，真跨模型）。广审（autoplan）**mode=simulated**——autoplan 是 gstack plan-file 导向、不适配 OpenSpec 四件套（首轮已确认），广度由 4 镜 + 2 codex voice 覆盖，如实标注。
> **outside-voice 补偿声明（guard=file-missing）**：无 `gstack-review.md`（本 change 未跑 autoplan），复用守卫返 `file-missing` ⇒ 自跑设计 outside-voice（design-voice + hr-tg 两切片）。**仅补偿 outside-voice 切片，广审其余镜（CEO/DX 视角）仍缺**——本轮由对抗/接地镜 + 领域 cross-model 覆盖。
> **栈**：Bash+Python+Markdown，不命中任何 stack 领域清单（backend-go/embedded/frontend），故无 stack 领域镜。

> **⏭ 更新（2026-07-15，二次审返工已落地）**：Q1–Q5 五条经用户拍板同意（含**方案自检修正**：C3+D1 合并统一 skew 探测、C5 撤回机械 marker 归人门——见下 Q5 更正），D1–D14 一并 amend 完成，`openspec validate --strict` 绿。下方 findings + 决策登记保留为审计记录；各条落点见文末「二次审返工落点」。

## 总判定（二次审）：⚠️ 仍不建议进设计 HARD-GATE，需一轮**聚焦返工**（比首轮近得多）

**返工确实闭合了首轮的 Q1–Q3 + D1–D10**（对抗镜 A 逐条对码核对：探针降格措辞、`--tools`+`--strict-mcp-config` 换旗、efficacy 前置门组 0、F6 绑 outside-voice 锚 + 降级码集含 preflight-error、真实性守 always-on 解耦措辞、行号修正——在 host-adaptive-execution / workflow-metrics / spec-workflow 三份核心 spec 与对应 tasks 之间字面一致）。接地镜也**坐实了返工押的关键代码事实**：`--tools` / `--strict-mcp-config` / `--add-dir` 是真实 claude CLI 旗且 `--tools` 语义确为独占白名单（对抗镜 B 实测 `--tools` 下 Bash 不可用，Q2 换旗判断成立）；`lens_metric_emit --host` 实测 exit 2（ADR-3-b 的实测复现属实）；`:144`/`:121` 行号正确；`config_lint` 确只校验键不校验值（D5 前提成立）。

**但返工自己的两条 amend 各砸了一个新洞——都在它们本要加固的不变式上，且都是多源冷层收敛 + 主审对码坐实的致命项**：

- **C1（致命）**：D6 加 `runner="none"` 击穿了本 change 的核心判据 `runner ≠ host`。
- **C2（致命）**：D7「真实性守 always-on 解耦 metrics」只解耦了一半——lint 函数解了耦，lint 的**输入数据**（lens-metric 行）在生产端仍被 metrics 门控，默认消费仓（metrics=false）下整条一致性 lint 结构性空转。

**核心一句**：首轮的洞补上了，方向对、闭合真；但**这个 change 反复要杀的病（「机械层看起来在防伪、实际没在防」）在它自己返工新增的两处机制上又各长了一次**——C2 尤其讽刺，是「always-on 解耦」这句承诺在默认配置下的空转。**距离很近了，但这两条必须在进门前修，不能留给实现期「顺手补」。**

---

## 决策登记区

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  C1 runner="none" 击穿 runner≠host 判据 —— 状态矩阵 lint（面治）    │ 致命·4源
│ [需拍板] Q2  C2 metrics=false 一致性 lint 空转 —— 独立信号 vs 强制最小行        │ 致命·3源
│ [需拍板] Q3  C3 旧 lint 拒 runner="none" 罢工 —— 两阶段发布 vs 真升 v2 wire      │ 高·2源
│ [需拍板] Q4  C4 反向 Read 出境缓解逻辑不成立 —— 去工具对称 codex vs OS 沙箱     │ 高·2源
│ [需拍板] Q5  C5 efficacy 前置门无机械锁 —— 廉价证据 marker vs 接受人门纪律      │ 中高·1源(§0.0自指)
│ [自动决策] D1  ADR-3(b)「推荐①」够不着「新SKILL×旧emitter」向 —— 拆①②各配一向  │ 中高·2源
│ [自动决策] D2  序列图 TG-10 仍写 --disallowedTools（Q2 已否决的旧旗）           │ 高·1源
│ [自动决策] D3  proposal:27 runner 仍 {claude,codex}，与全文 {..,none} 冲突      │ 中·2源
│ [自动决策] D4  lens-metric-emit spec:10 outside-voice 行 runner 域排除 none 自矛 │ 高·1源
│ [自动决策] D5  成功路径 reason_code 无规格定义（de-facto=none 未文档化）        │ 中·1源
│ [自动决策] D6  runner="none" ∧ findings=0 无机械交叉校验（并入 Q1 状态矩阵）     │ 中·2源
│ [自动决策] D7  missing-deps 仍「实现期核」，与 Open Questions 已清零矛盾         │ 中·3源
│ [自动决策] D8  secret_scan 把命中整行打进 stderr = 日志泄密                     │ 中·1源
│ [自动决策] D9  组合失败（目标CLI缺+子代理不可用）无 fallback runner 可落        │ 中·2源
│ [自动决策] D10 resolver 纯 shell 解析嵌套 config.yaml vs「无界语法面为零」冲突   │ 中·1源(基准5)
│ [自动决策] D11 F6 缺 metrics=false 测试（与 F7 不对称）+ MUST 独立函数不入门控   │ 高·1源
│ [自动决策] D12 parse_known_args 静默吞所有未知参数（非仅 --host）—— 显式拒 extras│ 低·1源
│ [自动决策] D13 host 伪造单点废 F6+F7 两门（防御纵深：resolver 落旁路 host 证据） │ 中·1源(有 ADR-1 张力)
│ [自动决策] D14 失败表缺 preflight-error 行 · design:16 冒烟未标注 · proposalA3弱 │ 低·对抗镜A/B
│ [已裁掉]  X1  REQUIRED_FIELDS 尚无 host —— 现状待实现非设计缺陷(scope面2已列)    │ 非缺陷
│ [已裁掉]  X2  lens-metric-contract.md debris —— design 面 11 已登记(不改只记)   │ 已知
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 需拍板（5 条，均致命/高，人在设计门拍板）

### Q1 —— C1：`runner="none"` 击穿 `runner ≠ host`，建议上「状态矩阵 lint」而非逐点补〔致命·4 源收敛〕

**冷层四源汇合**（design-voice #1 · hr-tg #1 · 对抗镜B F5 · 对抗镜A F2）+ **主审对码坐实**：D6 为「无执行轮次」加了 `runner="none"`，但本 change 的核心判据 `跨模型 ⟺ runner ≠ host`（design:83）是在 `none` 出现**之前**写的。`none ≠ claude` 且 `none ≠ codex` 恒真 ⇒ 任何 `runner="none"` 行都满足「runner ≠ host」，被三处同时误判：

| 落点 | 现状判据 | `host="codex" runner="none"` 的后果 |
|---|---|---|
| 派生语义（design:83） | `runner ≠ host` = 跨模型 | 机判为**跨模型第二意见** ✗ |
| ADR-5 置信豁免（design:194） | `runner ≠ host` → 豁免 <80 滤 | **豁免**（自审绕过置信滤）✗ |
| 复用守卫（tasks 4.3） | `runner == host` 判同族 | `none≠host` → 判**非同族 → 可复用为跨模型** ✗ |
| F6 自审红线（design:239） | `runner==host ∧ 非法码` → 拦 | `runner="none"` **不触发**（红线只管 `==host`）✗ |

∴ 一条伪造/bug 的 `host="codex" runner="none" findings="3"` 锚会被机判为跨模型、豁免置信滤、复用为第二意见——**正是本 change 立项要杀的假绿类，由 D6 亲手重新打开**。design:78 虽写「`runner="none"` MUST 伴 findings=0」，但对抗镜 B F5 + 主审核对确认**无任何机械交叉校验**（`anchor_lint.py:407-431` 各字段独立校验、不联动），`runner="none" findings="5"` 通过全部现有+新增检查。

**推荐（≥2 方案 → 面治优先，基准 3）**：
- **选项 A（逐点补）**：把三处判据各加 `∧ runner ∈ {claude,codex} ∧ host ∈ {claude,codex}`。最小改动，但三处散落、易漏、下次加枚举值又重演。
- **选项 B（推荐 · 状态矩阵 lint）**：`anchor_lint` 新增一条 always-on「合法组合矩阵」校验，一处 owns 全部 `host × runner × reason_code × findings` 合法态：跨模型要求 host/runner 均 ∈ `{claude,codex}` 且不同；`runner="none"` MUST `findings=0` 且 `reason_code ∈ {host-unknown,secret-hit}`；`host="unknown"` 只能配 `runner="none"`。派生语义/豁免/复用守卫都引用这张矩阵的「跨模型」判定，不各写一遍。
- **三面后果**：系统——B 把「什么是合法跨模型」收敛成单一机械真相源，杜绝枚举扩展再破判据（D6 就是前车）；用户——消费仓拿到的是「伪造 none 也拦得住」的强守而非「三处判据各自为政」；开发循环——B 多一条 lint + 一组矩阵测试，但省掉未来每加一个 runner/host 值就要巡三处的成本。
- **主次判定**：**主 = 选 B**。C1 是致命且是本 change 命门（跨模型不变式），逐点补留下的「下次扩枚举再破」正是碎片化根因（基准 4）。

### Q2 —— C2：默认消费仓 metrics=false 下一致性 lint 结构性空转，「always-on 解耦」只做了一半〔致命·3 源收敛〕

**冷层三源汇合**（design-voice #2 · 对抗镜B F1 · 对抗镜C F-1）+ **主审对码坐实**：D7 的承诺是「F7 一致性 lint MUST always-on、与 `metrics.enabled` 解耦」，理由明写「否则默认消费仓 metrics=false 时空转（codex CV2）」。但**这条 lint 的判据数据来源本身仍被 metrics 门控**：

- 判据 = lens-metric 锚中 `lens ∈ {domain,adversarial,grounding}` 的去重行数（tasks 2.5 / workflow-metrics spec:35）。
- **实测**：`config.template.yaml:72` 消费仓默认 `metrics.enabled: false`；`SKILL.md:176/152` metrics=false ⇒ **不调 emitter** ⇒ 报告里**零 lens-metric 行**；`anchor_lint.py:473` `if metrics_on: check_lens_metric(...)`。
- D7 只把 lint **函数**从 `if metrics_on:` 里拿出来（解决「函数会不会被跳过」），**没触及「lint 依赖的数据会不会存在」**（更上游、同一个开关卡在生产端）。

**推演链**：Codex 宿主 + metrics=false（默认）消费仓 → fan-out 机制死（`subagents="unavailable"`）→ 主 session 自代 3 镜、报告写「3 镜」→ **无任何 lens-metric 锚被写** → `anchor_lint` 读到 0 行（≤1）→ 一致性 lint 判 CLEAN 放行。**Success Metric 3 在默认配置下不可验/为假**——而默认消费仓正是本 change 的主要受益方。tasks 2.5 的「metrics=false 时仍拦」测试若靠人工塞入 metric 行，测的不是真实关闭路径（真实路径零行）。

**推荐（≥2 方案）**：
- **选项 A（推荐 · 独立信号）**：一致性 lint 的判据改读一个**不经 metrics 门控**的独立锚——让 `sdflow:fanout-capability` 锚**伴随写一份本轮实际 fan-out 镜清单**（或强制的最小镜存在性行），与 lens-metric 管线完全解耦。lint 读这份，lens-metric 继续只管价值度量。
- **选项 B（强制最小行）**：显式要求 SKILL 生产层在 `host=codex` 时即便 metrics=false 也落 fan-out 镜的**最小存在性行**（domain/adversarial/grounding 各一行，不要求完整 findings 计数）——把这条 lint 明列为「不受 metrics 影响」的例外。
- **三面后果**：系统——A 让真实性信号（谁跑了几镜）彻底脱离价值度量开关，架构更干净；用户——默认消费仓（绝大多数）终于真的拦得住「机制死却报多镜」；开发循环——A/B 都要改 design D7 + workflow-metrics spec 对应 Scenario + SKILL 生产层，工作量相当，A 的解耦更彻底。
- **主次判定**：**主 = 选 A**。C2 击穿的正是「always-on」这句核心承诺，且在默认态成立；把信号从被门控的管线里搬出来（A）比「给门控开例外」（B）更根治。**MUST 在 design 显式改写 D7 + spec Scenario，不留实现期。**

### Q3 —— C3：陈旧窗口旧 lint 拒 `runner="none"` 罢工，击穿 ADR-3(a)「旧 lint 静默放行新锚」〔高·2 源〕

**冷层两源**（design-voice #4 · hr-tg #2）+ **主审对码坐实**：ADR-3(a) 论证「旧 lint 见新锚的 `host=` → 无分支校验 → 静默放行」，承重前提是「新 `runner="claude"` 恰在旧 contract runner 枚举 `{claude,codex,claude-fallback}` 内」。**但 D6 加的 `runner="none"` 不在旧枚举内**——`anchor_lint.py:424` `if kv["runner"] not in enums["runner"]: → out-of-enum`，旧 contract 枚举（`lens-metric-contract.md:22`）无 `none`。∴ 陈旧窗口（消费仓 pull 新 bundle、tools 未 `sdflow-init update`）里，一份 codex 宿主报告只要出现 host-unknown/secret-hit 轮次（→ `runner="none"` 锚）→ **旧 lint 判 out-of-enum → 评审步 fail-closed 罢工**。这正是基准 5「一批仓被拒之门外」的病灶形态，而 ADR-3 的整个立论是**避免罢工**。ADR-3(a) 只分析了 `runner="claude"`，漏了 `none`。

**推荐（≥2 方案，涉版本策略）**：① **两阶段发布**——先让所有 validator 接受新枚举（含 none），再启用 producer 落 none 锚；② **真升 wire version `v2`** + 显式双读协商（锚行改 `v2`，旧工具见 v2 明确降级而非按 v1 硬校验）；③ 维持 v1 + 接受「host-unknown/secret-hit 轮次在陈旧窗口内罢工」并**如实登记**该窗口（诚实但把一类降级轮拒之门外）。
- **三面后果**：系统——②最干净（版本可协商）但改动最大；①无需改 wire 但要发布纪律；③零改动但留罢工窗口。用户——③下 CI/headless（Codex 主力形态）撞上 host-unknown 会评审罢工，体验差。开发循环——①落一条「新 producer × 旧 lint × runner=none」契约测试即可暴露；②要全套双读。
- **主次判定**：**主 = ①两阶段发布 + 补契约测试**（最小代价关掉罢工窗口）；若本就要动 wire 版本则并入②。**MUST NOT 维持现状声称「旧工具普遍静默兼容」——该结论对 none 已不成立。**

### Q4 —— C4：反向 Read 出境的「网络禁则无法外传」缓解逻辑不成立〔高·2 源〕

**冷层两源**（design-voice #3 · hr-tg #3）+ 对抗镜 B 实测佐证：design:263 的缓解「`Read` 可读 `~/.ssh`/`.env` 但**网络禁则读到也无法外传**」**逻辑不成立**——一次成功的 `claude -p` 本身**必须联网**，`Read` 读到的内容进入模型 prompt、**随该请求出境到 Anthropic**。禁的是 Bash/WebFetch 这些**工具**，不是底层 API 调用；`secret_scan` 只扫 context 文件、**不扫运行时 Read 的内容**。而 `--add-dir`/ephemeral cwd 只被列为「实现期核对」（tasks 7.4），**未进 7.3 测试锁**（对抗镜 B 实测：claude CLI 无 cwd 覆盖旗，7.3 只锁 `--tools`/`--strict-mcp-config` 存在性）——即「MUST 级 FS 边界保护」实际可能是空的。

**推荐（≥2 方案）**：
- **选项 A（推荐 · 去工具、对称 codex 路径）**：反向 claude 路径**不给 Read/Grep/Glob 工具**，只消费 `render_prompt` 产出的、已过 `secret_scan` 的 context（与 codex `-s read-only --ephemeral` 只发 context 的姿势**对称**）。一举关掉运行时 Read 出境面，且让两条路径的出境面**完全一致**（secret_scan 全覆盖）。代价：反向 voice 失去「自行探索代码库」能力——但 codex 路径本就没有这个能力，对等即可。
- **选项 B（OS 沙箱）**：把 claude CLI 放进 repo-only 只读挂载 + 隔离 HOME 的容器/sandbox，加「读 `.env`/`~/.ssh`/仓外文件必须失败」的真机负向测试。代价：实现复杂、跨平台。
- **三面后果**：系统——A 让安全模型对称、可 secret_scan 全证；用户——A 下反向 voice 只看被扫过的材料，最安全；开发循环——A 几乎零额外实现（去掉 `--tools` 给工具那一步），B 要搭沙箱。
- **主次判定**：**主 = 选 A**。它同时消解 design 里那条不成立的缓解叙述，且把「应用层尽力、非内核级」的残余风险压到与 codex 路径同级。**MUST 改 design:263 那句缓解论证（现为虚假正当性）+ TG-17 安全表。**

### Q5 —— C5：efficacy 前置门（组 0）无机械锁，是本 change 最重风险的唯一守门却纯散文〔中高·§0.0 自指〕

**冷层**（对抗镜 B F2）+ 主审核对：tasks 组 0（A1/A3 真机核验）是三个 markdown 复选框，design 明文「任一失效 ⇒ 停下、MUST NOT 开工组 1」，但**无任何脚本/gate 检查组 0 先于组 1 完成**——本仓 `ship_gate.py` 是 tickets 管线专用且本 change 该键已撤回（走经典 tasks 顺序流）。本 change 唯一标 🔴 的风险（efficacy 押 A1/A3、design:291）的**唯一缓解手段本身无机械性**——与它自己「杀机械层防伪」的立场自指矛盾。

**关键判据（基准 1）**：与探针不同（探针是 LLM 自报、无可机械捕获路径 ⇒ 诚实归语义层），**efficacy 证据（真实 `CODEX_THREAD_ID` 值 + 真机冒烟结果）是可确定性捕获的信号**——它落在「有信号 ∧ 有捕获路径」一侧，基准 1 说该机械化。

**推荐（≥2 方案）**：
- **选项 A（推荐 · 廉价证据 marker）**：组 0 产出一个带真机证据的落盘文件（`.efficacy-gate-passed`，内含真实捕获的 `CODEX_THREAD_ID` 值样式 + A3 冒烟 exit + 时间戳），组 1 首任务或 setup 门断言其存在 + 内容形状（拒空文件/人工敲的假值）。代价：一条廉价断言。
- **选项 B（接受人门纪律）**：维持复选框，靠设计 HARD-GATE（人读报告时核对「A1/A3 验了没」）兜底——与四件套流程其余任务同级（没有任何任务是机械强制顺序的）。
- **三面后果**：系统——A 给本 change 最重风险配一个诚实机械锁；B 与既有流程一致、不引入 bespoke gate。用户——A 下 BREAKING 契约不会建在未验 efficacy 上；B 依赖评审人尽责。开发循环——A 落一个 marker + 断言（小）；B 零成本但留「走过场勾掉」的口子。
- **主次判定**：**倾向 A，但承认它略超常规**（四件套流程本就人门为主，为单个 change 造机械 gate 有 scope 争议）。鉴于**契约不可逆 + 这是本 change 唯一 🔴 风险的唯一守门 + 证据可机械捕获**，A 的性价比成立。**留人拍板 A/B。** 若选 B，须在 proposal 显著登记「efficacy 未机械守、A1/A3 走过场则 BREAKING 建在未验假设上」。

> **🔴 更正（拍板前方案自检抓到——本条推荐 A 是错的）**：「efficacy 证据可机械捕获」这句判断**重犯了 grill 时把自报信号当机械门的坑**。`.efficacy-gate-passed` marker 由主 session（LLM）写 ⇒ 「A1/A3 真的在**真** Codex 宿主验过」的捕获环节仍由被监管方把持，marker 里塞个真格式 uuid 也是自报，无可信捕获路径（同探针/§0.0）。∴ **撤回 A，改选 B（归人门纪律）**：A1/A3 由人在真 Codex 宿主验 + 回写四件套，设计 HARD-GATE + 冷审复核守，proposal 显著登记走过场风险，**MUST NOT 造假机械锁**。已按 B amend（design Migration step 0 / Risks / Compliance §0.0 三次同源教训 / proposal A3 行）。

---

## 自动决策（清晰、默认采纳，返工时一并 amend）

| # | finding | 源 | 修法 |
|---|---|---|---|
| **D1** | ADR-3(b)「MUST 选一…推荐①」把两个正交方向包成三选一：①（emitter `parse_known_args` 受控 fail-closed）**结构上只改得到新 emitter**、只解「新 emitter × 旧 SKILL」向；「新 SKILL × 旧 emitter」（旧 emitter 已部署、本 change 够不着）**只能靠 SKILL 侧探测（②）**，而②无任何 spec 约束、tasks 3.2b 仅软推荐、8.2/8.3 改 SKILL 时只字未提探测 | 对抗镜A F3 · 对抗镜B F4（2 源，实测复现） | ADR-3(b) 明写「①②非互斥、各配一向」；补一条 host-adaptive/spec-workflow Requirement+Scenario 钉死 SKILL 侧探 emitter 能力；落进 tasks 8.2/8.3 实现项 |
| **D2** | design TG-10 序列图（:115-116）仍写 `--disallowedTools Write Edit`、无 `--strict-mcp-config`——Q2 已否决的旧旗，与同文件 ADR 铁律(:260-265) 自矛。首轮 D3 修 denylist 时漏了序列图这一面（同「点补漏面」类，讽刺违反基准 3） | 对抗镜A F1（1 源，直接比对） | 改 design:115-116 为 `claude -p --model opus --tools "Read,Grep,Glob" --strict-mcp-config`；D3 落点表补「序列图」扫描面 |
| **D3** | proposal:27「runner 收缩为 `{claude,codex}`」是 D6 前旧措辞，与 proposal 自己 :48（用 `runner="none"`）+ design:71 + 全部 spec + tasks 的 `{claude,codex,none}` 冲突；首轮 D6 落点表未含 proposal | 对抗镜A F4 · 对抗镜C F-4（2 源） | proposal:27 改为 `{claude,codex,none}`（`none` 见 D6 无执行轮次） |
| **D4** | `lens-metric-emit/spec.md:10` 输入 schema 写「outside-voice 行显式带 `runner`∈{claude,codex}」（排除 none），与同文件 :49-51 Scenario「runner='none' 行合法」直接矛盾——D6 只补 Scenario、没回改 Requirement 正文的 roster 类型声明 | 对抗镜A F2（1 源，同文件自矛） | spec:10 改为「`runner`∈{claude,codex,none}（none 见无执行轮次 Scenario）」 |
| **D5** | 成功跨模型路径（`runner ≠ host`）该往 `reason_code` 写什么值**全仓无规格定义**（穷举 grep：所有 reason_code 均绑降级分支；成功 Scenario spec:35-37 只字未提）。de-facto helper 现写 `reason_code="none"`（本报告自己的 design-voice 锚即是），但**未文档化** ⇒ 违反「MUST NOT 留实现裁量」；且 `reason_code="none"` 与 `runner="none"` 词面重载 | 对抗镜C F-2（1 源，穷举 grep；主审下修严重度：de-facto 惯例存在故非 happy-path 硬阻塞，是文档缺口） | 补 Scenario/条款：`runner ≠ host` 时 `reason_code` SHALL = 固定哨兵（建议 `none`，或换个不与 runner=none 重载的词如 `ok`）；tasks 2.2b/2.3 补「成功路径 reason_code 放行」正例 |
| **D6** | `runner="none"` ∧ `findings=0` 无机械交叉校验（各字段独立校验、不联动）；`runner="none" findings="5"` 通过全部检查，削弱「grep 可机械筛降级轮」可观测性承诺 | 对抗镜B F5 · hr-tg #1（2 源） | 并入 Q1 状态矩阵：`runner=="none" ⇒ findings=="0"` 校验（lens-metric 锚 + outside-voice 锚均查），钉进 F6/F7 同批测试 |
| **D7** | `missing-deps` 仍标「实现期核」（tasks 2.3/27 + design 括注），与 Open Questions「无」（design:313）矛盾；helper preflight 契约确会返 `missing-deps`（outside-voice.sh 头注释），它是产出 findings 的同族 fallback ⇒ 不纳入降级码集则被 F6 误报自审（假红） | design-voice #7 · hr-tg #7 · 对抗镜A（3 源） | 现在就定死：`missing-deps` 归约映射为 `preflight-error`（或纳入降级码集第 5 码），写进 spec + 失败表 + 测试，禁实现期临场决定 |
| **D8** | `outside-voice.sh:50-52` `secret_scan` 把 `grep -n` 命中的**整行**（含密钥）存入并原样打印到 stderr——拒发出境却造成**日志泄密**；新设计两路径复用该函数，测试只验 exit 3 不 fallback、无脱敏断言 | hr-tg #4（1 源，读码坐实） | stderr 只输出规则类型 + 行号，绝不打印原行/匹配值；补断言「测试密钥不出现在 stdout/stderr/临时日志」。**注：此为 pre-existing helper 行为，本 change 因「两路径复用」把它拉进 scope，宜顺手修** |
| **D9** | 组合失败（目标 runner CLI 缺 **且** codex 子代理不可用）无 fallback runner 可落——spec:43 要求 CLI 缺时派同宿主子代理落 `runner=host`，但 spec:125 又允许子代理不可用；两者同时发生时无处可落，设计仍要求记 `runner=codex` | design-voice #5 · hr-tg（2 源） | 补组合失败 Scenario：fallback spawn 失败/capability unavailable ⇒ 落 `runner="none" findings=0 reason_code="fallback-unavailable"`（新增第 8 码），禁生成同族 findings |
| **D10** | tasks 6.2/6.2b 要求纯 shell resolver 从 `model-tiers.md` + 按机队分键的 `config.yaml` 读值；新格式加三级结构+值+引号+注释语义，却在 design:325 声称「无界语法面为零」——与基准 5 张力（现有 config_lint 已是手写行扫描，init.py:254/290） | design-voice #6（1 源，基准 5） | 要么把覆盖格式收缩成**有界机器块**（如 model-tiers 专用的定长 KV 块），要么 resolver 与 config_lint **共用同一解析实现 + 畸形输入测试**；修正 design:325 Compliance 基准 5 措辞（承认有一个受控的 config 解析面） |
| **D11** | tasks 2.3（F6 测试）无「metrics=false 时仍拦」项，与 2.5（F7 有此项）不对称；且现状 `anchor_lint.py:152-171` `check_existence` 是「同函数体混必查家族+metrics 门控家族」的活例——实现者若把新 outside-voice KV 解析塞进它而非像 `check_hr_tg` 单独成函数，会把 F6 也拖进门控 | 对抗镜C F-3（1 源） | 给 2.3 补对等「metrics=false 时 F6 仍拦」测试；实现指引明写「新 outside-voice KV 解析 + 自审红线 MUST 独立成函数、不接受/不用 `metrics_on` 参数」（照抄 `check_hr_tg` 先例） |
| **D12** | `parse_known_args`（tasks 3.2）会静默吞**所有**未识别参数、不止 `--host`——`--laye` 误拼被静默忽略而非报错，弱化参数拼写防护 | 对抗镜B F6（1 源） | emitter 显式 `if extras: fail-closed`（只放行预期的缺省行为，多余 extras 报错） |
| **D13** | host 伪造是单点：主 session 系统性把所有锚写 `host="claude"` ⇒ 同时废掉 F6 自审红线 **和** F7 fanout 缺锚检查（判不出 codex 报告 ⇒ 不要求 fanout 锚 ⇒ 整套新机制对该报告完全不生效）。爆炸半径大于 lens-metric 信任边界（后者仅让一行计数失真） | 对抗镜B F3（1 源，有 ADR-1 张力） | 防御纵深：`resolve-models.sh`（可信 shell、读真实 env）把判定的 host 落一份**独立于评审锚行文本**的 sidecar（带 mtime），供 CI/人事后交叉核对。**注 ADR-1 张力**：ADR-1 否决过「anchor_lint 自判宿主」，但 sidecar 由可信 shell 捕获真 env、强于 LLM 写的锚 host=（信号捕获环节不同），非 ADR-1 否决的那个方案；是否加留人定 |
| **D14** | 低危三合一：① design 失败表缺 `preflight-error` 独立行（对抗镜A F5）② design:16 历史冒烟未按首轮 D3 承诺标「旧旗、已被 Q2 取代」（对抗镜A F6）③ proposal A3 行登记力度弱于 design 🔴（对抗镜B F7/对抗镜A） | 对抗镜A/B（低） | 失败表补 preflight-error 行；design:16 加标注；proposal A3 行补「目标态可能在 Codex 主力形态不可达、需考虑缩 scope」对等登记 |

---

## 已裁掉（escalate-not-drop，反静默压制，可审计）

- **X1 —— 接地镜「`anchor_lint.py:24` REQUIRED_FIELDS 尚无 `host`」**：**非设计缺陷**。这是**实现前的现状代码态**——本 change design scope-check 面 2 正是要求「REQUIRED_FIELDS 加 host」。spec-review 审的是设计，代码还没写，「现状没 host」恰恰印证了设计前提（要改这里）。裁掉理由：把「现状代码待实现」误判为「设计漏了」，违反通则 ③（拿现状反驳目标态）。**留档供人复核裁得对不对。**
- **X2 —— 接地镜「`openspec/workflow/lens-metric-contract.md` 是 debris」**：**已知、非新洞**。design scope-check **面 11 已登记**该副本为 pre-existing debris，明写「本 change 不改它、另记 buglist 清 debris」。接地镜坐实了它确实存在（与 CLAUDE.md「openspec/workflow/ 只留 tools/」自述抵触）——这只是**确认面 11 的判断准确**，非本 change 要修的项。裁掉理由：已在 scope 决策内，重复登记。**留档：若 owner 想在本 change 顺手清 debris（而非另开），可翻此裁决。**

---

## 各镜 findings 溯源（可审计）

- **对抗镜1（返工闭合核验，sonnet）**：逐条对码核 Q1–Q3+D1–D10 落点 → 确认闭合，挖出 6 处残留漂移：F1 序列图旧旗【高】(→D2)· F2 emit spec runner 域排 none 自矛【高】(→D4)· F3 ADR-3(b) 够不着一向【中高】(→D1)· F4 proposal:27 枚举冲突【中】(→D3)· F5 失败表缺 preflight-error 行【低】(→D14)· F6 design:16 未标注【低】(→D14)。**明确核对通过**：Q1/Q3/D1/D2/D6/D7/D8/D9 三处口径一致。
- **对抗镜2（隐藏假设/失败模式，sonnet）**：F1 metrics=false 一致性 lint 空转【致命】(→Q2)· F2 efficacy 前置门无机械锁【致命】(→Q5)· F3 host 伪造单点废两门【高】(→D13)· F4 ADR-3(b) 三选一漂移【中高】(→D1)· F5 runner=none∧findings=0 无交叉校验【中】(→D6/Q1)· F6 parse_known_args 吞 extras【低】(→D12)· F7 proposal A3 登记弱【低】(→D14)。**实测证伪候选 4**：`--tools`/`--strict-mcp-config` 真实存在、实测 Bash 被禁，Q2 换旗成立（残余：`--add-dir` 未进 7.3 测试锁）。
- **对抗镜3（§0.0 自指防伪完整性，sonnet）**：F-1 metrics=false 空转【致命】(→Q2，与镜2 F1 汇合)· F-2 成功路径 reason_code 无定义【高→主审降中】(→D5)· F-3 F6 缺 metrics=false 测试 + 混函数风险【高】(→D11)· F-4 proposal 枚举自矛【中】(→D3)。**验证通过未见缺陷**：聚合器兼容读机制成立（`lens_metric_aggregate` 无 runner 越域校验，claude-fallback→(claude,claude) 不冲突）；探针诚实限定全仓一致（无一处把探针包装成机械保证，§0.0 自指干净）。
- **接地镜（代码事实核验，haiku）**：**9 项一致**——`--tools`/`--strict-mcp-config`/`--add-dir`/`--disallowedTools`/`--allowedTools`/`-p`/`--model` 真实存在且 `--tools`=独占白名单；`anchor_lint.py:473` metrics 门控、`:407-431` check_lens_metric、`:24` REQUIRED_FIELDS（无 host=X1）；`outside_voice_guard.py:93`=`runner != "codex"`；`lens_metric_emit --host` 实测 exit 2；`init.py:335` config_lint 只校验键；两 SKILL preflight reason_code=`not-installed|preflight-error`；`resolve-models.sh` 确不存在；`outside-voice.sh` `:144`/`:121` 行号正确。**2 项标注**：X1（host 待实现）· X2（contract debris 存在）。
- **codex 跨模型 voice · design-voice（runner=codex ≠ host=claude，7 条）**：#1 runner=none 击穿判据【critical】(→Q1)· #2 metrics=false 空转【high】(→Q2)· #3 Read 出境缓解不成立【critical】(→Q4)· #4 旧 lint 拒 none【high】(→Q3)· #5 组合失败无 fallback runner【high】(→D9)· #6 shell 解析嵌套 YAML vs 基准5【medium】(→D10)· #7 missing-deps 未决【medium】(→D7)。
- **codex 跨模型 voice · hr-tg 领域镜（runner=codex，4 条）**：#1 runner=none/host=unknown 误判跨模型【high】(→Q1)· #2 旧 lint 拒 none 漏失败路径【high】(→Q3)· #3 反向 Read 无可验 FS 边界【high】(→Q4)· #4 secret_scan 整行入 stderr 泄密【medium】(→D8)。
- **汇合即置信信号**：C1（runner=none 击穿）4 独立源、C2（metrics 空转）3 独立源、C3（旧 lint 拒 none）2 源、C4（Read 出境）2 源——多源冷层各自独立命中同一洞，且主审对码逐条坐实。

## lens-metric 度量锚（本轮）

**本轮 lens-metric 锚延后至设计门拍板时最终化**（承 SKILL〔SR-M〕）——本报告结论是「需聚焦返工」、大量 finding 的 amend 去向取决于 Q1–Q5 拍板，此刻 pre-gate 计数无意义。`metrics.enabled=true` 已确认（非因门控跳过）；返工 amend + 拍板后补落 roster+findings 调 `lens_metric_emit.py --host claude` 并跑 `anchor_lint` 自检。**`anchor_lint` 自检因 lens-metric 段有意延后而暂缓（非遗漏，与首轮口径一致）。** 其余四类锚（step1-broad-review / hr-tg / outside-voice ×2）已落于本文件头部。

## 收敛口（二次审）

**返工方向对、首轮的洞真闭合了——但返工自己的 D6/D7 各引入一条致命新洞（C1/C2），加 C3/C4 两条高危，必须再修一轮才进门。**

- **不建议直接进设计 HARD-GATE**：C1（runner=none 击穿核心判据）+ C2（metrics=false 空转击穿 always-on 承诺）都是**默认态成立的致命项**、且都是本 change 命门（跨模型不变式 + 杀 7 镜假绿），留给「阶段四 code-review 兜底」不合适——它们是**设计层的判据/架构洞**，不是实现细节。
- **建议**：跑一轮**聚焦返工**——只处理 Q1–Q5（5 条需拍板）+ D1–D14（多为顺手的口径/文档漂移），**重点是 C1 的状态矩阵 lint（Q1）与 C2 的独立信号解耦（Q2）落进 design + spec + tasks**。返工量比首轮小得多（首轮是机制降格/换旗/加前置门，本轮主要是「D6/D7 的收尾没做全」+ 文档漂移清理）。amend 后可直接进门，无需三轮——这两洞的修法都是确定性的。
- **为何仍需一轮而非直接放行**：C1/C2 由 4 源/3 源独立冷层收敛 + 对码坐实，置信极高；且讽刺地正是本 change「杀机械层防伪」命题在自己身上的复现——**在这个 change 上放过「看起来在防伪、实际没防」，等于否定它自己的立项理由**。

---

## 二次审返工落点（审计，2026-07-15 amend）

| 决策 | 落点 |
|---|---|
| **Q1**（C1 合法组合矩阵） | design 数据模型「合法组合矩阵」段 + 派生语义重写 · ADR-5 豁免引用矩阵 · F6 段（矩阵同族行子句 + 成功哨兵 ok）· 失败表 · scope-check 面 2 · host-adaptive「锚行合法组合矩阵」新 Requirement + 3 Scenario · workflow-metrics 自审 Scenario · spec-workflow 豁免 · outside-voice-reuse-guard 引用矩阵 + runner=none Scenario · tasks 2.3/4.3/4.4/8.3 |
| **Q2**（C2 独立信号 mirrors=） | design 锚行 v2 加 `mirrors=` · ADR-4 一致性 lint 改读 mirrors= · Risks C2 行 · host-adaptive 子代理降级 Requirement + fan-out/解耦锁 Scenario · workflow-metrics fan-out Scenario · tasks 2.5/9.4 |
| **Q3+D1**（C3 统一 skew 探测） | design ADR-3 重写（合并两症状 + 统一探测策略）· Risks skew 行 · host-adaptive「探 tools 能力」新 Requirement + 2 Scenario · lens-metric-emit skew 注 · tasks 3.2b/8.6 |
| **Q4**（C4 零工具） | design Context:16 · 序列图 · 安全表只读约束/FS 边界行 · Q2 段重写 · 铁律 · host-adaptive 出境安全 Requirement + 只读约束 Scenario · spec-workflow Codex voice Scenario · proposal What Changes · tasks 0.2/7.3/7.4 |
| **Q5**（efficacy 归人门，撤回机械 marker） | design Migration step 0 · Risks efficacy 行 · Compliance §0.0（三次同源教训）· proposal A3 行 · tasks 0.3 · 本报告 Q5 更正 |
| **D2**（序列图旧旗） | design:115-116（并入 Q4） |
| **D3**（proposal:27 枚举） | proposal What Changes BREAKING 行 |
| **D4**（emit spec runner 域含 none） | lens-metric-emit spec:10 |
| **D5**（成功哨兵 ok） | design F6 段 · host-adaptive 矩阵 + voice Scenario · workflow-metrics 自审 Scenario（并入 Q1） |
| **D6**（none⇒findings=0） | 并入 Q1 矩阵 |
| **D7**（missing-deps→preflight-error） | design F6 段 + 失败表 F1b · workflow-metrics 自审 Scenario |
| **D8**（secret_scan stderr 脱敏） | host-adaptive secret 命中 Scenario · tasks 7.3/7.7 |
| **D9**（fallback-unavailable） | design 失败表 F8 · host-adaptive 组合失败 Scenario · tasks（矩阵无执行码） |
| **D10**（resolver config 解析共用） | design Compliance 基准5 + Risks eval 行 · host-adaptive eval Scenario · tasks 6.2d |
| **D11**（F6 metrics=false 测试 + 独立函数） | design scope-check 面 2 · host-adaptive/workflow-metrics（独立成函数措辞）· tasks 2.3 |
| **D12**（parse_known_args 拒 extras） | lens-metric-emit fail-closed Scenario · tasks 3.2 |
| **D13**（host 伪造旁路证据） | 登记于 design ADR-4/Risks（有 ADR-1 张力，防御纵深，未强制——留人定） |
| **D14**（失败表/冒烟标注/proposal A3 登记） | design 失败表 F1b · Context:16 · proposal A3 行 |

> **lens-metric 度量锚**仍延后至设计门拍板最终化（SR-M）。`anchor_lint` 自检因 lens-metric 段有意延后而暂缓（非遗漏，与首轮口径一致）。`openspec validate --strict` 绿。

## 附录：首轮记录（2026-07-15，commit 4e88918 判定 → c9b8325 返工）

> 首轮全文见 git 历史。核心：4 镜 + codex voice 判「不建议进 HARD-GATE、需返工」，证伪 grill 的 G1（探针非机械）/G2（--allowedTools 非 deny-by-default）/G5（码集漏 preflight-error），新挖 metrics 门控架空真实性守 / emitter 跨版本罢工 / eval 注入 / efficacy 押未验假设。收敛为 Q1–Q3 + D1–D10，用户拍板「都同意」，返工落地 c9b8325、`openspec validate` 绿。
>
> **首轮 → 本轮的关系**：本轮确认首轮 Q1–Q3+D1–D10 **已闭合**（对抗镜1 逐条核对）；本轮的新 finding（C1/C2/C3…）**不是首轮漏审**，而是**返工新增的 D6（runner=none）/D7（metrics 解耦）自己引入的**——即「返工引入新洞」，正是首轮报告「稳妥选项：再跑一轮轻量 spec-review 确认返工没引入新洞」所预期要抓的东西。
