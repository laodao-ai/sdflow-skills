<!-- sdflow:step1-broad-review v1 mode="simulated" -->
<!-- sdflow:hr-tg v1 hit="TG-06,TG-08,TG-17" declared="TG-06,TG-08,TG-17" evidence="锚行 schema v2 是 bundle 分发给消费仓的跨仓契约(TG-06)+反向 runner 新增 claude CLI 调用(TG-08)+outside-voice context 出境新增 Anthropic 端点(TG-17)" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="file-missing" host="claude" runner="codex" reason_code="none" findings="7" truncated="false" -->

# spec-review-report — add-codex-host-support

> **层**：spec-review（阶段二设计审）· **对象**：add-codex-host-support（grill 后，commit e76193c）
> **镜阵**：对抗镜 ×3（fresh context 子代理）+ 接地镜 ×1 + **codex 跨模型 outside-voice**（design-voice，runner=codex≠host=claude，真跨模型）。广审（autoplan）**降级为 simulated**——autoplan 是 gstack plan-file 导向、不适配 OpenSpec 四件套；广度由 4 镜 + codex voice 覆盖，如实标注。
> **栈**：Bash+Python+Markdown，不命中任何 stack 领域清单（backend-go/embedded/frontend），故无 stack 领域镜。

> **⏭ 更新（2026-07-15，返工已落地）**：Q1/Q2/Q3 三条拍板「都同意」（按推荐），D1–D10 一并 amend 完成，`openspec validate` 绿。下方 findings + 决策登记保留为审计记录；各条落点见文末「返工落点」。

## 总判定（返工前）：⚠️ 不建议直接进设计 HARD-GATE，需一轮设计返工

冷层证实：**本 change 的「防伪（no false-green）」层扎实、方向对；但 grill（作者自审）收敛的两条 headline 修复（G1 机械下限、G2 allowlist）技术上都站不住，G5 码集漏一个，还引入一处 spec 自我矛盾。** 更重的是，冷层挖出 4 条**作者从未触及**的新洞（metrics 门控架空真实性守、emitter 跨版本 argparse 罢工【实测】、eval 注入面、efficacy 押未验假设且验证排在 BREAKING 之后）。多条 finding 由 2–3 个独立源汇合，置信高。

**核心一句**：这份 spec 不会在实现期「爆炸」（它 fail-loud 得很干净），它会更糟——**安静地实现完一个 BREAKING 跨仓契约，然后在 Codex 主力形态（headless/CI）下交付零跨模型价值，且没有任何门拦得住它 ship。**

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  G1「机械下限」降格 —— 探针非机械信号(推翻 grill 已批 G1)         │
│ [需拍板] Q2  G2 换机制 —— --tools 而非 --allowedTools + 沙箱对等声称降级       │
│ [需拍板] Q3  efficacy 前置门 —— A1/A3 真机核验上提到 BREAKING 契约之前         │
│ [自动决策] D1 F6 红线绑定到 outside-voice 锚(非 lens-metric)+定义其字段解析     │
│ [自动决策] D2 G5 降级码集补 preflight-error(核 missing-deps)                   │
│ [自动决策] D3 G2 denylist 残留清面(host-adaptive:27 / spec-workflow:33 等全改) │
│ [自动决策] D4 ADR-3 补 emitter 跨版本 skew 分析 + 选兼容策略(实测会罢工)        │
│ [自动决策] D5 resolver eval 注入面加固(%q/declare -p + 拒危险字符 + 值校验)     │
│ [自动决策] D6 no-execution 轮次 runner 表达(runner="none")                    │
│ [自动决策] D7 真实性守(自审/fanout/roster)与 metrics.enabled 解耦→always-on    │
│ [自动决策] D8 fanout 锚 MUST 落被 lint 的报告文件 + 探针失败模式补表           │
│ [自动决策] D9 行号漂移修(:146→:144,:122→:121)+ ADR-3 描述补 runner 枚举校验    │
│ [自动决策] D10 scope-check 表补面(openspec/workflow/ 副本 + gen 生成物)        │
│ [已裁掉]  —— 无。4 镜质量高，无 finding 被判不成立(低置信项均降级留档非丢弃)    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 需拍板（3 条，均推翻/重定 grill 或涉排序，人在设计门拍板）

### Q1 —— G1「机械下限」降格为「语义核验 + always-on 一致性 lint」〔推翻 grill 已批 G1〕

**冷层三源汇合**（对抗镜1 F-A · 对抗镜2 A3 · codex CV2）：我在 grill 里把 fan-out 探针当「机械下限」是**错的**——

1. **探针非机械捕获**：`make -n` 看 exit code 是机械的，因为**可信 shell 脚本**去捕获、被测方碰不到。但 fan-out 探针只能由**主 session（LLM）**去 spawn、观察、把 `subagents=` 写进锚。`anchor_lint` 读那行锚，无从核验它对应一次真 spawn。**探针结果经「被监管方」自报到达校验层**——落在 §0.0「防伪」那一侧。
2. **内部矛盾**：ADR-1 已承认 `host=` 可伪造、划为信任边界（host 还有 shell 源 `resolve-models.sh`）；而信号**更弱**的 `subagents=`（纯 LLM 观察、无 shell 源）却被上收成机械下限撑阻塞红线——同一把 §0.0 尺量出相反归属，方向反了。
3. **metrics 门控架空**（codex CV2，已复核）：`anchor_lint` 的 lens-metric 校验受 `metrics.enabled` 门控（`anchor_lint.py:473`），而消费仓默认 `metrics.enabled=false`。fanout 红线又依赖 lens-metric 行数 → **默认消费仓里这道「下限」根本不跑**，可「机制 unavailable、报告多镜」全绿。
4. **headline 过度声称**（对抗镜1 F-B）：红线只覆盖「机制死」，目标态下（消费仓已铺 AGENTS.md 授权）`available` 是常态，「机制活+偷懒自代」（同症状、无守）才是活风险；「事前拦截头号假绿」名不副实。
5. **红线会误伤 + 去重键未钉死**（对抗镜1 F-C · 对抗镜2 A2）：Codex-unavailable 下诚实的单 agent 多角度评审落 >1 lens 行会被拦；「≤1 行」强制与「镜数如实」拉扯；去重键（按 lens？还是全键？）没钉死——跟 G5 修前一样悬空。

**推荐**：**降格 + 保留有用的那部分**——
- 探针 = 「机制活着」的**语义核验**（诚实与 ADR-1 的 host= 信任边界并列），删掉 design:176/spec:97 的「机械下限/事前拦截头号假绿」措辞，改成成因限定表述（「机制死变体→一致性 lint 可拦；机制活+偷懒自代→残余语义层、仅事后 host 分组可见」）。
- 红线保留为**always-on 一致性 lint**（**与 metrics 解耦**，D7）：`fanout-capability` 锚记 `unavailable` 却出现多 lens 行 = **自相矛盾**（拦的是诚实错误/自相矛盾，不是伪造）；钉死去重键（建议按 `lens`）；解「≤1 行 vs 如实」的拉扯（单 agent 多角度允许落多行，但改用「独立性维度」而非「行数维度」判定）。
- fanout 锚落进被 lint 的报告文件（D8）+ `host=codex` 条件性要求锚存在（否则不落锚即绕过）。
- **代价**：G1 从「事前机械拦截头号假绿」缩为「拦机制死的自相矛盾 + 事后可发现」。诚实，但比 grill 承诺的弱。**这是我 grill 判错、冷层纠正的一条，需你重新拍板 G1 到底做到哪。**
- **备选**：找真机械捕获（shell wrapper 记录实际 spawn 次数由脚本落锚）——agent 运行时大概率做不到，探针只有 LLM 能调。

### Q2 —— G2 换只读机制 + 沙箱对等声称降级〔重定 grill 已批 G2〕

**冷层两源**（对抗镜2 B1，它自己跑了 `claude --help` · codex CV5）：我 grill 选的 `--allowedTools Read Grep Glob` 是**弱的那把旗**——
- `--allowedTools/--disallowedTools` 配的是**权限层**、会与 settings.json 的 `permissions.allow` **合并**：消费仓任何 `Bash(...)` 预批准都能**穿透** allowlist。它不是 deny-by-default。
- 真正的独占白名单是 **`--tools "Read,Grep,Glob"`**（把其余内建工具从可用集彻底移除）。
- 无 MCP 隔离（B2）：反向 `claude -p` 默认继承 ambient MCP servers，除非 **`--strict-mcp-config`**——prompt-injection 外传通道。codex `--ephemeral` 无此面。
- 应用层门控 ≠ codex 的内核级沙箱（B3 · codex CV5）：codex `-s read-only` 是 seccomp/sandbox-exec 内核级；claude 工具门控可被 settings/hook/plugin 削弱，即便 `--tools` 也是 best-effort 应用层。

**推荐**：① 反向调用改 `--tools "Read,Grep,Glob"`（实现期核对确切只读工具名）**+ `--strict-mcp-config`**（不传 `--mcp-config`）；② TG-17 表把「与 codex OS 沙箱**对等**」诚实降级为「**应用层尽力对齐 + 残余非内核级**」；③ 把「allowlist（含 `--tools`、不含 denylist 形态）」的测试断言标为**安全承重墙**（对抗镜3 F4：它是防子进程串味的唯一真机械闸）；④ Read 无 FS 边界（B4·CV5）→ `--add-dir` 限定或 ephemeral cwd + 登记「secret_scan 不覆盖运行时 Read」。
- **代价**：只读姿势诚实降级为「应用层尽力」——但真正致命的外传向量（Bash/WebFetch 网络）在干净 `-p` 运行里确被拒，残余风险主要取决于 ambient 配置，可接受。**需你确认降级声称 + 换旗。**

### Q3 —— efficacy 真机核验（A1/A3）上提到 BREAKING 契约**之前**〔排序，涉不可逆代价〕

**冷层**（对抗镜3 F1/F3）：本 change 的目标（Codex 里真跨模型）押在两个未验假设——A1（`CODEX_THREAD_ID` 在 headless/CI/spawned 都在）、A3（Codex 宿主 session 能发出 `claude -p` 网络请求）。而真机核验是 **task 10.1/10.2 = 最后一组**，排在 BREAKING 跨仓契约 schema v2（组 1，不可逆）**之后**。
- A1 若在 headless 缺失 → `host=unknown` → voice 永不跑。而 CI/headless 正是自动化评审主力形态、最想要无人跨模型复核的场景。
- A3 冒烟只在 Claude 宿主（有网络）做过；codex 只读姿势本身**封网络**（design:247 自己写的），却没问 Codex 宿主 session 有没有出境权。若封 → 永远同族 fallback（codex 审 codex，贴了诚实标签的自审）→ efficacy=0。

**推荐**：A1/A3 真机核验**上提为前置门**（task 0），改契约前先证。若 headless 缺 `CODEX_THREAD_ID`，design 须先补 headless 替代正信号或明确 scope 缩到「仅交互 Codex」——**否则 BREAKING 契约是为一个主力形态跑不起来的功能付的不可逆代价**。
- **备选**：维持顺序，但在 proposal 显著登记「efficacy 未验、headless 可能零交付」为 A1/A3 失效后果，并接受「先改契约后验证」的返工风险。

---

## 自动决策（清晰、默认采纳，返工时一并 amend）

| # | finding | 源 | 修法 |
|---|---|---|---|
| **D1** | F6 自审红线谓词绑到**不存在的单一锚**——`lens=` 在 lens-metric 锚、`reason_code=` 在 outside-voice 锚，无锚同时承载两者；字面诱导实现者绑 lens-metric 锚（无 reason_code）→ 红线**静默永不触发**（假绿）。且 anchor_lint 现状对 outside-voice 锚**零字段解析** | codex CV1 · 对抗镜2 A1（2 源） | spec + task 2.3 显式：F6 跑在 `sdflow:outside-voice` 锚上、读其 `runner/host/reason_code`（锚类型已隐含 lens=outside-voice）；`reason_code` 为该锚必填；新增 outside-voice 锚 KV 解析路径 |
| **D2** | G5 降级码集漏 `preflight-error`（两 SKILL preflight 段定义、是**产出 findings 的 runner==host 同族 fallback**）→ 被 F6 误判自审、阻塞（假红） | 接地镜 F-2 · codex CV7（2 源，已复核） | 码集补为 `{not-installed, preflight-error, timeout, exec-error}`；核 `missing-deps` 是否也需纳入；先定义完整 preflight 状态→原因码归约表 |
| **D3** | G2 denylist 残留在**规范正文**：`host-adaptive:27`(SHALL) 与 `spec-workflow:33`(Scenario THEN=验收判据) 仍写 `--disallowedTools`，与同文件 `:71` 的 MUST NOT 自我矛盾（point-fix 漏面，讽刺违反基准 3） | 对抗镜2 C1 · codex CV6（2 源） | 全面清 denylist 形态→硬化调用形态（Q2）；安全调用收敛为**一个契约片段**，测试从单一源断言；仅 design:16「历史冒烟记录」处保留并标注 |
| **D4** | ADR-3 只证 anchor_lint 侧安全，**emitter 侧跨版本 argparse 硬罢工**（实测：`lens_metric_emit.py --host codex` → `unrecognized arguments` exit 2）。两 skew 方向都炸：新SKILL×旧emitter→fail-closed→陈旧窗口内 lens-metric 整段静默清零；新emitter×旧SKILL→--host 必填→同样丢 | 对抗镜3 F2（实测复现，已复核） | ADR-3 补 emitter 双向 skew 分析；选兼容策略（荐 `parse_known_args`+缺 host 时受控 fail-closed 而非 argparse 崩，或 SKILL 先探 emitter 是否认 --host）；design:280「非假绿」对 emitter 不成立须改 |
| **D5** | `resolver eval` 收 repo config 值（模型覆盖）再输出六变量供 `eval`——含 `$()`/引号/换行即在 eval 时执行。config_lint 只校验**键**不校验**值**（已复核 init.py:335） | codex CV4 | resolver 输出用 `printf %q`/`declare -p` 可证安全编码，拒换行/控制字符/非模型 ID 字符；config 值校验加严；加恶意值回归测试。优先考虑取消 eval |
| **D6** | 「无 runner 执行」状态无法表达——`host-unknown`/`secret-hit` 不跑 voice，但锚文法强制 `runner="claude|codex"` 必填：省略被拦、任选伪造「谁执行」 | codex CV3 | 增 `runner="none"`（或拆 attempted/executed），给 no-execution 钉死合法组合 |
| **D7** | 真实性守受 `metrics.enabled` 关闭而失效——自审/fanout/roster 校验若挂在 metrics 门控后，默认消费仓（metrics=false）全 OFF（已复核 anchor_lint:473 + MANDATORY 不含 lens-metric/fanout） | codex CV2 | 把**真实性锚**（自审、fanout-capability、实际 roster）校验**与 metrics 价值度量解耦、always-on**；metrics 只门控「价值计数」不门控「防伪」。与 Q1 联动 |
| **D8** | fanout 锚未钉死落进被 lint 的 `--report` 文件（落别处则 anchor_lint 看不见→红线永不触发）；探针自身失败模式（歧义/超时/挂起）未进失败表 | 对抗镜2 A2 · 对抗镜1 F-D | spec 明写锚落被 lint 文件内；补探针失败模式（歧义→保守落 unavailable + timeout） |
| **D9** | 行号漂移 `:146`→`:144`、`:122`→`:121`（内容对、号旧）；ADR-3 描述漏述**承重的** runner 枚举校验（新锚 `runner="claude"` 不被判越域，恰因旧 contract enum 已含 claude） | 接地镜 F-1/F-3 | 修行号；ADR-3 补一句 runner 枚举承重前提 |
| **D10** | scope-check 表漏面：`openspec/workflow/lens-metric-contract.md`（规则副本，与 CLAUDE.md 自述相抵触）· `openspec/workflow/tools/outside_voice_guard.py`（逐字节副本）· `docs/workflow-skills/sdflow-{spec,code}-review.md`（gen_workflow_guide 生成物含 claude-fallback，只列了 workflow-map） | 接地镜 F-4 | scope-check 表补这些面；核 openspec/workflow/ 规则副本是否 pre-existing debris（另清） |

---

## 各镜 findings 溯源（可审计）

- **对抗镜1（证伪 G1/ADR-4）**：F-A 探针非机械捕获【致/高】· F-B headline 过度声称【高】· F-C 红线误伤+去重键悬空【中】· F-D 探针失败模式留白【低/中】。
- **对抗镜2（悬空 MUST + 安全）**：C1 denylist 残留自我矛盾【致/高】· A1 F6 锚绑定未钉死【高】· A2/A3 F7 前置不自保【中】· B1 `--allowedTools` 非 deny-by-default【高】· B2 无 MCP 隔离【中】· B3 非内核级【中】· B4 Read 无 FS 边界【中】· B5 冒烟用错形态【低】。
- **对抗镜3（隐藏假设/失败模式）**：F1 efficacy 押 A1、验证排 BREAKING 后【高】· F2 emitter 双向罢工【高·实测】· F3 反向 voice 网络出境、A3 环境错【高】· F4 host 诚实是地基但 ADR-1 不守、env 继承串味【中高】。
- **接地镜**：F-1 行号【低】· F-2 preflight-error 漏码集【高】· F-3 ADR-3 描述失准【中】· F-4 scope-check 漏面【中】。大量代码事实核验一致（见其表）。
- **codex 跨模型 voice（design-voice，runner=codex）**：7 条，与上述高度汇合（CV1=A1、CV2 metrics 门控【新·critical】、CV3 no-runner、CV4 eval 注入【新】、CV5=B4、CV6=C1、CV7=F-2）。**汇合本身即置信信号**：4 个独立冷源对 F6 锚绑定、preflight-error、denylist 残留各自独立命中。

## lens-metric 度量锚（本轮）

**本轮 lens-metric 锚延后至设计门拍板时最终化**（承 SKILL〔SR-M〕：采纳/裁掉随门后裁决重算）——因本报告结论是「需返工」、大量 finding 的 amend 去向取决于 Q1–Q3 拍板，此刻 pre-gate 计数无意义。返工 amend 后、拍板时补落并跑 `anchor_lint` 自检。（metrics.enabled=true 已确认，非因门控跳过。）

## 收敛口（返工后）

**返工已落地（Q1–Q3 拍板 + D1–D10），`openspec validate` 绿。** 这一轮冷审证明了「作者不该独审自己的设计」：我 grill 判「成立、没咬」的 G1/G2/G5 三处全被冷层纠正。

**关于是否进设计 HARD-GATE 的建议**：本轮返工**改动很大**（探针机制降格、安全机制换旗、加 efficacy 前置门、10 条 D）——**改动量本身就是"再审一轮"的理由**。但我也不想陷入无限评审。判断留人：
- **稳妥**：再跑一轮轻量 spec-review（只审本次 amend 的增量 + 交叉核 D1/D4/D5 的实现可行性），确认返工没引入新洞，再进门。
- **提效**：直接进设计 HARD-GATE，把 D1–D10 的实现正确性留给**阶段四 code-review**（那里有冷层兜底），设计门只拍「方向对不对」。

## 返工落点（审计）

| 决策 | 落点 |
|---|---|
| Q1（探针降格） | design ADR-4 重写 · adr/0023 降格 · host-adaptive「子代理降级」需求重写 + 3 scenario · workflow-metrics fanout scenario · tasks 2.5/9.2/9.4 · proposal SM#3 · Compliance |
| Q2（--tools） | design 安全表 + 铁律 · host-adaptive :27/只读 scenario/出境安全需求 · spec-workflow :33 scenario · tasks 7.3/7.4 · proposal SM#1 |
| Q3（efficacy 前置门） | tasks 组 0（新）· design Migration step 0 + Risks · tasks 组 10 改端到端 |
| D1（F6 绑 outside-voice 锚） | design F6 段 · host-adaptive 禁止自审 scenario · workflow-metrics 自审 scenario · tasks 2.2b/2.3 |
| D2（码集补 preflight-error） | 同 D1 各处 · tasks 2.3 |
| D3（denylist 清面） | 见 Q2（host-adaptive:27 + spec-workflow:33 已清） |
| D4（emitter skew） | design ADR-3 重写为 (a)/(b) · lens-metric-emit fail-closed scenario + skew 注 · tasks 3.1/3.2/3.2b |
| D5（eval 注入） | host-adaptive eval-safety scenario · design Risks · tasks 6.2d |
| D6（runner=none） | design 数据模型 · workflow-metrics 字段 · spec-workflow 锚文法 + scenario · lens-metric-emit scenario · host-adaptive scenarios |
| D7（真实性守解耦 metrics） | design ADR-4 · host-adaptive/workflow-metrics scenario（always-on）· tasks 2.3/2.5 |
| D8（fanout 锚在 lint 文件） | design 数据模型 · host-adaptive scenario · tasks 2.5/9.4 |
| D9（行号 + ADR-3 描述） | design Context 表 + ADR-3 · proposal :16/:119 |
| D10（scope-check 补面） | design scope-check 表 面 10/11 |

> **lens-metric 度量锚**仍延后至设计门拍板最终化（SR-M；返工中的临时裁决计数无意义）。`anchor_lint` 自检因 lens-metric 段有意延后而暂缓（非遗漏）。
