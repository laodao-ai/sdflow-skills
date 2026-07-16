# tasks — add-codex-host-support

> **顺序即 design 的 Migration Plan**：**efficacy 前置门（组 0）**→ 契约先行 → 工具 → 聚合器 → helper → 规则/SKILL → 铺设 → 文档。
> **追溯**：每任务标注所属 capability 的 Requirement 名（本仓 spec 用中文标题作 ID）。
> **测试纪律**：`scripts/` 改动必跑对应 `tests/`；全量 `pytest` 在每个任务组末尾绿。

## 0. efficacy 前置门（Q3 · 改 BREAKING 契约之前先证，冷层对抗镜3 F1/F3）

> **为何在最前**：目标（Codex 里真跨模型）押在 A1/A3 两个未验假设；核验若排在契约之后 = 为可能跑不起来的功能付不可逆代价。**任一在主力形态失效 ⇒ 停下补 headless 替代信号或缩 scope，MUST NOT 直接开工组 1。**

- [ ] 0.1 **A1 核验**：〔⚠ 未做·deferred 至 Codex 宿主——本轮 Claude 宿主(`CLAUDECODE=1`)无法验；用户显式授权(C)未验即合并、风险自负〕Codex 交互 / headless / `codex exec` / spawned subagent 各形态各跑一次，确认 `CODEX_THREAD_ID` 存在。**任一（尤其 headless/`codex exec`）缺失** ⇒ 停下：design 补该形态的替代正信号，或明确 scope 缩到"仅交互 Codex" + proposal 显著登记〔host-adaptive-execution · 宿主判定靠正信号〕
- [ ] 0.2 **A3 核验**：〔⚠ 未做·deferred 至 Codex 宿主——本轮无法验；用户授权(C)未验即合并〕在**真实 Codex 宿主 session** 内冒烟 `claude -p --model opus --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>`〔spec-review-r3 C4：只读全仓、对称 codex〕——核验点是**"能否成功发出网络请求并拿到 findings"**（非"claude 装没装"）。Codex 若封出境网络 ⇒ 反向 voice 恒失效、永远同族 fallback，design 须承认该 scope 边界〔host-adaptive-execution · outside voice = 另一个机队的强档〕
- [ ] 0.3 〔⚠ 未做·A1/A3 未在 Codex 验、无实测真值可写回；前置门未过，用户授权(C)未验即合并〕前置门结论写回 proposal 假设表 + design Risks（A1/A3 实测真值）；两者皆通过才进组 1。**〔spec-review-r2 C5〕此门是人门纪律（设计 HARD-GATE + 冷审复核守），MUST NOT 造 `.efficacy-gate-passed` 之类假机械锁**（marker 由主 session 自报、无可信捕获路径）；若 A3 失效则本 change 须缩 scope（proposal 已显著登记零交付风险）

## 1. 契约先行（枚举单一源）

- [x] 1.1 改 `assets/workflow/lens-metric-contract.md` 的 `lens-metric-enums` 机读块：新增 `host: claude, codex, unknown`；`runner: claude, codex, none, unknown`（删 `claude-fallback`；加 `none`——无执行轮次 D6；加 `unknown`——host=unknown 时普通镜主审机队，spec-review-r3 codex#1，仅普通镜行合法、outside-voice 锚不取）。**注（r3-narrow 修正）**：合法组合矩阵的**关系式判定逻辑**（三态分类）**不**落成可 parse 机读块（平铺 enums 块表达力装不下 `runner≠host` 等关系式）——契约块只承载**枚举域**，矩阵逻辑由 anchor_lint + outside_voice_guard **各自本地重实现**（承 D5）、由全笛卡尔 golden 守（见 2.3/4.5）〔workflow-metrics · 度量锚契约；host-adaptive-execution · 矩阵逻辑两工具各自重实现〕
- [x] 1.2 改同文件 `lens-metric-fold` 机读块：删 `claude-fallback: outside-voice` 行，保 `codex: outside-voice` 并新增 `claude: outside-voice`（任一 runner 的 voice 都折叠到 outside-voice）〔workflow-metrics · 度量锚契约〕
- [x] 1.3 改同文件的锚形示例 + 散文注记 + 归属规则段：行键升为 `(lens, host, runner, site)`，唯一键升为 `(layer,lens,host,runner,site,轮)`；写明「跨模型性 = **合法组合矩阵**判定（`host,runner∈{claude,codex}∧runner≠host∧reason_code="ok"`）的派生量，MUST NOT 编码进枚举值、**MUST NOT 简写为裸 `runner≠host`**（被 `runner="none"` 击穿，spec-review-r2 C1）」〔workflow-metrics · 度量锚契约〕
- [x] 1.4 跑全量 pytest 确认**工具测试如期变红**（红的位置 = 依赖契约枚举的全部落点，据此核对 design 的 scope-check 表无遗漏）——**此步的产出是一份红点清单，不是绿**

## 2. 校验工具（anchor_lint）

- [x] 2.1 TDD：`test_anchor_lint.py` 加用例——`REQUIRED_FIELDS` 含 `host`；缺 `host` 判 missing-field；`host` 越域判 out-of-enum；`runner="claude-fallback"` 判 out-of-enum（已废弃）〔workflow-metrics · 锚字段缺失或取值越域被自检阻塞〕
- [x] 2.2 实现：`anchor_lint.py` 的 `REQUIRED_FIELDS` 加 `host`，枚举校验加 `host`（枚举仍从契约机读块读，**MUST NOT 在脚本内复制清单**）〔workflow-metrics〕
- [x] 2.2b TDD + 实现：**新增 outside-voice 锚 KV 字段解析**（D1）——`anchor_lint` 现状对 `sdflow:outside-voice` 锚只记存在性、零字段解析；须解析其 `runner`/`host`/`reason_code`（`reason_code` 为该锚必填），供 2.3 自审红线用〔host-adaptive-execution · 禁止自审〕
- [x] 2.3 TDD + 实现：**合法组合矩阵 = 自审红线的单一源（C1/Q1）**——`anchor_lint` 加一条 **always-on、独立成函数、不接受 `metrics_on` 参数**（D11，照 `check_hr_tg` 先例）的合法组合矩阵校验，**枚举域从契约机读块读、关系式判定逻辑本地重实现（r3-narrow：矩阵是关系式谓词，平铺块装不下；MUST NOT 硬凑可 parse 块），与 `outside_voice_guard` 由全笛卡尔 golden 守一致（4.5）**，钉死 `sdflow:outside-voice` 锚的合法 `(host,runner,reason_code,findings)`：① 跨模型 `host,runner∈{claude,codex}∧runner≠host∧reason_code="ok"`（成功哨兵 ok，D5）② 同族 `runner==host∧reason_code∈{not-installed,preflight-error,timeout,exec-error}`（`missing-deps` 归约入 `preflight-error`，D7）③ 无执行 `runner="none"∧findings=0∧reason_code∈{host-unknown,secret-hit,fallback-unavailable}`；余者报错（违规类型 `illegal-combo`/`self-review`）。**F6 自审红线 = 矩阵②行的 reason_code 子句，非并列规则**。测试：三类合法各放行 1 例 + `runner=none findings=5`→拦 + `host=unknown runner=claude`→拦 + `runner==host reason_code=ok`→拦(自审) + **`outside-voice 锚 runner=unknown`→拦（r3-narrow #5/#6：`unknown` 在共享 runner 域内、会被第一层域校验放行，必须由矩阵 catch-all 拦——显式回归锁，防 if/elif 漏 else）** + 绑错到 lens-metric 锚(无 reason_code)会静默失效的反例锁 + **metrics=false 时仍拦(解耦锁 D11，与 2.5 对称)**〔host-adaptive-execution · 锚行合法组合矩阵 / 禁止自审；workflow-metrics · 自审锚行被自检阻塞〕
- [x] 2.3b TDD + 实现：**lens-metric 普通镜行级组合校验（r3-narrow #6）**——合法组合矩阵只管 `sdflow:outside-voice` 锚；lens-metric 非-outside-voice（普通镜）行 SHALL 另有行级校验：`site="—" ∧ runner==host`；`runner="unknown"` **仅** `host="unknown"` 时合法；普通镜 MUST NOT `runner="none"`。测试：`host=claude lens=domain runner=unknown`→拦、`host=unknown lens=domain runner=unknown`→放行、普通镜 `runner=none`→拦〔workflow-metrics · runner 枚举；lens-metric-emit · roster 行键〕
- [x] 2.4 核验 `anchor_lint` **不判宿主**（ADR-1）：它只读锚行自身的 `host`/`runner` 字段做内部一致性校验，MUST NOT import 或调用 `resolve-models.sh`——加一条测试锁死此边界〔host-adaptive-execution〕
- [x] 2.5 TDD + 实现：**fan-out always-on 一致性 lint，判据读 `mirrors=`（C2）**〔spec-review-amendment Q1 / adr/0023 / spec-review-r2 C2〕——`anchor_lint` 读会话级 `sdflow:fanout-capability` 锚（该锚须在被 lint 的报告文件内，D8-orig）；`subagents="unavailable"` 时，**同锚 `mirrors=` 清单**中 `∈ {domain,adversarial,grounding}` 的**按值去重计数 >1 ⇒ 报错阻塞**（违规类型 `dead-fanout-multi-mirror`，拦**自相矛盾**非伪造）。**判据 MUST 读 `mirrors=`、MUST NOT 数 lens-metric 行**（C2 纠正首轮致命洞：lens-metric 行受 metrics 门控、默认消费仓 metrics=false 零行 → lint 空转；`mirrors=` 由 SKILL 直接落、不受门控）。**MUST always-on、判据数据源亦 always-on、独立成函数**；`host=codex` 报告缺该锚 ⇒ 报错。测试：unavailable+mirrors列3镜→拦；unavailable+1→放行；available+N→放行（残余留语义层，注释注明）；**metrics=false 且无 lens-metric 行时仍拦（解耦锁——构造无 lens-metric 行的报告，验 mirrors= 独立生效）**；host=codex 缺锚→拦；**`subagents=""`/未知值/缺字段→fail-closed（非放行，r3-narrow #5）；capability 锚 host 与报告 host 不一致→fail-closed；重复 capability 锚→fail-closed**〔host-adaptive-execution · 子代理不可用时镜数如实降级 / fanout-capability 锚严格文法〕

## 3. 产出工具（lens_metric_emit）

- [x] 3.1 TDD：`test_lens_metric_emit.py` 加用例——`--host` 必填但**缺失走受控 fail-closed（可读错误、非 argparse 崩，D4）**；越域（含 `claude-fallback`）⇒ fail-closed；**MUST NOT 默认填 claude**；`runner="none"` 合法（D6，伴 findings=0）〔lens-metric-emit · 缺 --host 或取值越域则受控 fail-closed / runner="none" 行合法〕
- [x] 3.2 实现：`lens_metric_emit.py` 加 `--host` 参数（单一源，无 per-finding/per-row host；用 `parse_known_args`+显式必填校验使缺 host 受控降级、非崩栈，D4；**且 `if extras: fail-closed` 拒多余/拼错参数，D12**）；行键升为 `(lens, host, runner, site)`；输出锚行带 `host=`；runner 域含 `none`〔lens-metric-emit · 计数由确定性 emitter 归约〕
- [x] 3.2b **统一 skew 策略落地（C3+D1，r3 fail-loud 硬停）**：编排 SKILL 在 **fan-out / 落任何锚之前**探本仓 tools 能力（emitter 认不认 `--host`：`--help` grep；anchor_lint 枚举含不含 `none`：grep 契约块 runner 行——因 `init.py copy_bundle` 契约与 tools 原子配对拷贝、不独立漂移，此 grep 天然代理 anchor_lint 版本，r3-narrow 已证），**陈旧 ⇒ 硬停该评审步、不产出待 lint 的报告 + 响亮提示 `sdflow-init update`（fail-loud）**〔spec-review-r3 C3-A/B：不产无锚报告(撞 MANDATORY)、不落 v1 旧锚(假绿)、不静默清零〕；emitter 侧 `parse_known_args` 受控 fail-closed **只护「新 emitter × 旧调用方」**（对已部署旧 emitter 够不着，见 spec Scenario）。测试：探到旧 emitter/旧 lint → **硬停不产报告 + 告警**（非"产无锚报告"、非罢工、非清零）〔host-adaptive-execution · 落锚/调 emitter 前探 tools 能力；lens-metric-emit · 跨版本 skew〕
- [x] 3.3 更新 `tools/tests/fixtures/lens_metric_input.json` golden fixture 至新行键；核对 `MIN_LENS_ROWS` 一致性测试仍绿〔lens-metric-emit〕
- [x] 3.4 回归：零-finding 行、共抓不计独立、同类型多实例算独立、finding 命中行不在 roster 则 fail-closed —— 四条既有 Scenario 在升维后仍绿〔lens-metric-emit〕

## 4. 复用守卫（outside_voice_guard）

- [x] 4.1 TDD：`test_outside_voice_guard.py` 加用例——`runner == host`（同族）⇒ 新 reason_code `same-family`、退出码非 0，MUST NOT 复用〔outside-voice-reuse-guard · 同族 fallback 段不得复用〕
- [x] 4.2 TDD：v1 旧锚（无 `host=`，`runner="codex"`）⇒ 读作 `host="claude"` ⇒ `runner ≠ host` ⇒ 可复用（向后兼容读，**MUST NOT 罢工**）〔outside-voice-reuse-guard · v1 旧锚无 host 字段仍可复用〕
- [x] 4.3 实现：`outside_voice_guard.py:93` 的 `attrs.get("runner") != "codex"` 改为**引用合法组合矩阵的「跨模型」判定**（C1，MUST NOT 自写 `runner==host`——否则 `runner="none"` 被误判可复用）；`runner==host`(同族) 与 `runner="none"`(无执行) 均输出 `same-family` 不复用；reason_code 枚举扩至七码〔outside-voice-reuse-guard · 三判归约为单一 reason_code〕
- [x] 4.4 TDD：`runner="none"` 段（`host="codex" runner="none"`）⇒ 输出 `same-family`、退出码非 0、不复用（防 `none≠host` 误判可复用，C1）〔outside-voice-reuse-guard · runner="none" 无执行段不得复用〕
- [x] 4.5 **矩阵跨工具全笛卡尔 golden（C2-cross-tool，r3-narrow #3 强化）**：`outside_voice_guard` 从契约块读枚举域 + 本地重实现关系式分类（承 `MUST NOT import` 边界，D5）；golden 测试 SHALL 对 **host×runner×reason_code×findings 全笛卡尔积**（含边界 + mutation：越域/缺字段/坏值）喂 `anchor_lint` 与 `outside_voice_guard` 两者，断言二者**完整分类**（illegal/cross-model/same-family/no-exec，非仅「跨模型」布尔——否则两工具同源同错测不出）逐条一致，任一漂移即红〔host-adaptive-execution · 矩阵逻辑两工具各自重实现且全笛卡尔 golden 守〕
- [x] 4.6 **codex#N 标签旁路核（r3-narrow #4）**：核 `outside_voice_guard.py:101` 的 `codex#N` prose 标签计数是**次选 findings 计数**（供 zero-findings 判），**MUST NOT 单独构成"可复用"资格**——复用资格 SHALL 要求至少一条被矩阵分类为 `cross-model` 的可解析锚；测试：无锚/非法锚/`runner="none"` 锚 + `codex#1` prose 标签 ⇒ **拒复用**（防 prose 标签绕过矩阵）〔outside-voice-reuse-guard · 结构判按矩阵〕

## 5. 聚合器双代兼容（唯一读存量的组件）

- [x] 5.1 **先固化回归基线**：跑当前 `lens_metric_aggregate.py` 对全部存量归档报告，落基线快照（改造后须逐行一致）〔workflow-retro · 改造前后对存量归档的聚合结果逐行一致〕
- [x] 5.2 TDD：`test_lens_metric_aggregate.py` 加用例——`runner="claude-fallback"` 旧锚读作 `(host=claude, runner=claude)`；无 `host` 字段读作 `host="claude"`；新旧锚混合仓正确分组不 parse 失败〔workflow-retro · 旧锚按兼容规则读入不丢行 / 新旧锚混合仓正确分组〕
- [x] 5.3 实现：分组键升为 `(layer, lens, host, runner, site)` + 兼容读；`render_table` 加 `host` 列〔workflow-retro · 聚合器双代兼容读锚行〕
- [x] 5.4 回归验证：对 5.1 的基线快照，改造后除新增 `host` 列外**每行计数逐行一致**（机验，非目测）〔workflow-retro〕
- [x] 5.5 同步 `retro_report.py` 及其测试（若引用 runner 枚举或分组键）〔workflow-retro〕

## 6. 宿主判定 helper（新组件）

- [x] 6.1 TDD：`sdflow-init/tests/test_resolve_models.py` —— `CLAUDECODE=1` ⇒ `HOST=claude`；`CODEX_THREAD_ID=<uuid>` ⇒ `HOST=codex`；两者皆无 ⇒ `HOST=unknown` + stderr 明示；**两者同时存在 ⇒ `unknown` + 信号冲突告警**（MUST NOT 静默取其一）〔host-adaptive-execution · 宿主判定靠正信号〕
- [x] 6.2 实现 `sdflow-init/assets/hack/resolve-models.sh`：纯 shell（ADR-1：校验侧不需要宿主判定，故无需 Python 双实现）；`eval` 导出六个变量；档位表从 `model-tiers.md` 读，**MUST NOT 内联模型名**〔host-adaptive-execution · 模型档位按机队分列〕
- [x] 6.2b TDD + 实现：**覆盖按机队分键读**〔grill-amendment G4 / adr/0024〕——`config.yaml` 的 `model-tiers.{claude,codex}.{strong,mid,light}` 按当前机队读；**扁平旧格式**（`model-tiers.strong: …`）兼容读作 **Claude 机队**覆盖，MUST NOT 罢工；无当前机队段回落机队缺省。测试：分键格式读对应段 / 扁平格式在 claude 宿主生效、在 codex 宿主**不生效**（回落 codex 缺省，不把 opus 塞给 codex）〔host-adaptive-execution · 消费仓覆盖段仍生效；spec-workflow · 模型档位映射〕
- [x] 6.2c 同步 `config.template.yaml` 示例为分键格式 + `test_config_lint.py` 认识分键与扁平两种〔host-adaptive-execution〕
- [x] 6.2d **eval 注入加固**（D5 · 冷层 codex CV4）：`resolve-models.sh` 输出六变量 SHALL 用 `printf %q`/`declare -p` 安全编码 + 拒换行/控制字符/非模型 ID 字符；`config_lint` 校验 model-tiers 的**值**（非仅键）为合法模型 ID。测试：覆盖值含 `$()`/反引号/换行/引号的**恶意值回归**（断言不在 eval 时执行）。**SHOULD 评估取消 eval**（改 source 受控生成文件 / 数组读取）。**〔spec-review-r2 D10〕** `resolve-models.sh` 读嵌套 `config.yaml` model-tiers 覆盖 SHALL 与 `config_lint` **共用同一解析实现 + 畸形输入测试**（MUST NOT 各手搓一套），或把覆盖收缩成有界机器块——它是受控有界 config 解析面，非无界语法〔host-adaptive-execution · resolver 输出不得成为 eval 注入面〕
- [x] 6.3 `setup.sh` 装 `resolve-models.sh` 进 `~/.sdflow/hack/` + 测试守（**dogfood 盲区**：`skill-principles.md` 曾因 setup 只拷 `*.sh` 而漏装、仓内测试全绿——本条测试 MUST 验**安装路径**，不是仓内路径）〔host-adaptive-execution〕
- [x] 6.4 **G6 同源锁**〔grill-amendment G6 / ADR-9〕：`resolve-models.sh` 每轮 eval 一次导出六变量供 SKILL export；`outside-voice.sh` **只从环境读 `$SDFLOW_VOICE_RUNNER`、MUST NOT 自调 `resolve-models.sh` 重判宿主**——加测试断言 `outside-voice.sh` 不含对 `resolve-models.sh` 的调用〔host-adaptive-execution · outside voice = 另一个机队的强档〕

## 7. outside-voice 去硬编码（安全面，改动最敏感）

- [x] 7.1 TDD：`test_outside_voice.py` 加用例——`preflight` 探测的是 `$SDFLOW_VOICE_RUNNER` 的 CLI，**不是固定的 codex**；`HOST=codex` 时探 `claude`〔host-adaptive-execution · outside voice = 另一个机队的强档〕
- [x] 7.2 实现：`outside-voice.sh` 的 `preflight` / `do_exec` 按 runner 分叉；**`secret_scan` / `render_prompt`（FRAME + 三条通则）/ 200KB 截断保持单份共用**，只有最终 exec 命令行一处分叉〔host-adaptive-execution · 出境安全三件套对两条路径一视同仁〕
- [x] 7.3 TDD：**安全回归锁（承重墙，spec-review-r3 C4 只读全仓对称 codex）**——加测试断言反向路径（claude）走同一个 `secret_scan` 与同一个 `render_prompt`；secret 命中时**两条路径都 exit 3 拒发且不 fallback**、**且 `secret_scan` 的 stderr 只出规则类型+行号、不出命中原行/匹配值（D8），断言测试密钥不现于 stdout/stderr/临时日志**；**且断言 claude exec 行三旗齐全：`--tools "Read,Grep,Glob"`（只读工具集）+ `--strict-mcp-config` + `--add-dir <repo_root>`，不含 Write/Bash/WebFetch 等非只读工具、不含 `--tools ""` 零工具、不含 `--disallowedTools`、不含 `--allowedTools`**（防漂移回给写/网工具/零工具/denylist/弱 allowlist，C4）〔host-adaptive-execution · secret 命中时两条路径都拒发（且不泄进日志）/ 只读约束按 runner 落到对应机制〕
- [x] 7.4 实现反向 runner 调用：`claude -p --model "$SDFLOW_VOICE_MODEL" --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir "$repo_root"`〔spec-review-r3 C4：**只读全仓、对称 codex `-C repo_root -s read-only`**——撤回 r2 零工具（前提「codex 只发 context」实测为错：codex `-C repo_root` 全仓只读，FRAME 明请读仓库代码；零工具单边削弱 claude voice 检索能力 + 加剧幻觉）。三旗承重墙：只读工具集（无 Write/Bash/WebFetch）+ MCP 隔离 + `--add-dir` 增量授权确保覆盖仓库（`--add-dir` 是"加目录"非"收窄边界"；claude Read 与 codex read-only 均无硬 FS 读边界，r3-narrow #1）。**双边预存残余如实登记**：两条路径都读仓库→出境各自模型商、均无硬 FS 读边界，FRAME 缓解非铁桶。**只改跨模型 `claude -p` 反向路径，不改同族 fallback 子代理**〕〔host-adaptive-execution · 只读约束按 runner 落到对应机制〕
- [x] 7.7 **D8 脱敏落地**：改 `outside-voice.sh` 的 `secret_scan` stderr 诊断只输出规则类型 + 行号，MUST NOT 打印命中整行/匹配值（现状 `grep -n` 整行原样入 stderr = 日志泄密）〔host-adaptive-execution · secret 命中时两条路径都拒发（且不泄进日志）〕
- [x] 7.8 **missing-deps → preflight-error 映射落地（D7，spec-review-r3 A-F 补漏）**：`outside-voice.sh` 的 `preflight` 经 **stdout 字符串**返回 `ready|not_installed|missing-deps`（**均 exit 0**，`:6`）——调用 SKILL/helper SHALL 把 `preflight` 返回的 `missing-deps` 显式映射为锚 `reason_code="preflight-error"`（合法同族降级码集内），**MUST NOT 原样落 `reason_code="missing-deps"`**（不在码集内 → 被 2.3 矩阵校验判 illegal-combo/自审假红）。测试：`preflight`→`missing-deps` ⇒ 锚 reason_code=preflight-error 放行〔host-adaptive-execution · 禁止自审（合法降级码集）；workflow-metrics · 自审锚行被自检阻塞〕
- [x] 7.5 实现 `HOST=unknown` ⇒ **不跑 voice** + `reason_code="host-unknown"`（fail-loud，MUST NOT 任选 runner 充作跨模型）〔host-adaptive-execution · 宿主 unknown 则不跑 voice〕
- [x] 7.6 `outside-voice.sh` 版本号升至 1.2.0；头部契约注释同步（它是两个 review SKILL 引用的契约单一源）

## 8. 规则与 SKILL

- [x] 8.1 改 `assets/workflow/model-tiers.md`：档位表按机队分列（Claude: opus/sonnet/haiku；Codex: gpt-5.6-sol/terra/luna）+ 覆盖段注记改为**按机队分键**（`model-tiers.{claude,codex}.*`，扁平旧格式兼容读作 Claude 机队，见 adr/0024）〔grill-amendment G4；host-adaptive-execution · 模型档位按机队分列；spec-workflow · 模型档位映射〕
- [x] 8.2 改 `sdflow-spec-review/SKILL.md`：锚行文法（加 `host=`）· outside-voice 调用协议引用 `resolve-models.sh` · lens-metric roster 构造带 `--host`〔spec-workflow · 跨模型 outside voice〕
- [x] 8.3 改 `sdflow-code-review/SKILL.md`：同 8.2 + **置信豁免规则引用合法组合矩阵的「跨模型」判定**（C1，MUST NOT 自写 `runner≠host`——被 `runner="none"` 击穿；`SKILL.md:172` 是旧假绿点）〔spec-workflow · outside-voice tension 不静默采纳〕
- [x] 8.4 各编排 SKILL（ship/done/spec-review/code-review）的模型选择改引用 `SDFLOW_TIER_*` 变量，**MUST NOT 内联模型名**〔spec-workflow · 模型档位映射〕
- [x] 8.5 SKILL 写明「Codex 宿主下 `spawn_agent` 指定 model 的 task-specific reason = 本工作流的 model-tiers（门禁步禁降档是硬约束）」〔host-adaptive-execution · 子代理不可用时镜数如实降级〕
- [x] 8.6 **C3+D1 统一 skew 探测写进两个评审 SKILL**：落锚/调 emitter 前探本仓 tools 能力（emitter 认 `--host`、anchor_lint 枚举含 `none`），陈旧 ⇒ fail-loud 降级 + 报告/终端响亮提示 `sdflow-init update`（承 3.2b 实现，此处是 SKILL 编排落点）〔host-adaptive-execution · 落锚/调 emitter 前探 tools 能力〕

## 9. 消费项目铺设（Codex 子代理授权）

- [x] 9.1 `sdflow-init/assets/snippets/claude-section.md` + AGENTS.md 段加 **Codex 子代理授权声明**（多镜 fan-out + model-tiers 构成 codex 要求的显式授权）〔host-adaptive-execution · 授权声明存在〕
- [x] 9.2 SKILL 写明「子代理不可用 ⇒ MUST 缩 roster 到实跑的镜 + 报告显著标注单镜降级」；**登记诚实边界**〔spec-review-amendment Q1：探针=机制活着的**语义核验**（非机械门，主 session 自报 trust-based）；一致性 lint（2.5）只拦「机制死却报多镜」的**自相矛盾**、always-on；残余「第 N 镜跑没跑」+「机制活+偷懒自代」无机械守——诚实分开，MUST NOT 声称"头号假绿事前拦截"〕〔host-adaptive-execution · 子代理不可用则缩 roster〕
- [x] 9.3 `sdflow-init/tests/` 加守卫：铺设产物含授权段（机验存在性）
- [x] 9.4 SKILL fan-out 前跑**能力探针（语义核验）**〔spec-review-amendment Q1 / adr/0023 / spec-review-r2 C2〕：`host=codex` ⇒ 派 trivial 探针子代理（回哨兵值=available）；`host=claude` ⇒ 免探针恒 available；落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="…" mirrors="…" -->`**到被 lint 的报告文件内**（D8-orig）——**`mirrors=` 由 SKILL 在 fan-out 时直接写本轮实际镜清单、不经 emitter/lens-metric、不读 config.metrics**（C2：它是一致性 lint 的判据源，MUST NOT 依赖受 metrics 门控的 lens-metric 行）。探针为 unavailable ⇒ SKILL MUST 缩 roster 到单镜、`mirrors=` 也只列实跑镜（否则 2.5 一致性 lint 拦）。**探针值/mirrors 为主 session 自报，非机械核验**——如实登记〔host-adaptive-execution · 子代理不可用时镜数如实降级〕

## 10. 端到端真机核验（A1/A3 已上提组 0 前置门）

> A1/A3 的存在性核验已上提为**组 0 前置门**（Q3）——本组只留改造后的端到端验证。

- [ ] 10.1 〔⚠ 未做·deferred 至 Codex 宿主——本轮无法验；用户授权(C)未验即合并〕端到端：Codex 宿主下跑一次真实评审，核对 outside-voice 锚为 `host="codex" runner="claude"`、fanout-capability 锚在场、且 `anchor_lint` 绿（含新增的自审红线 + 一致性 lint always-on）
- [x] 10.2 回归：Claude 宿主下跑一次，确认现有行为不变（`host="claude" runner="codex"`），存量归档聚合逐行一致（组 5 基线）

## 11. 文档与收尾

- [x] 11.1 同步 `docs/workflow-map.md`(:141,:150) + `docs/workflow-map.html`(:555,:563) 的字段表与枚举
- [x] 11.2 全量 `pytest` 绿 + `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿
- [x] 11.3 逐面核对 design 的 **scope-check 表 面 1–10** 全部改完（基准 3 面治：留任何一面 = 契约漂移）+ 面 11 pre-existing debris 已核（登记非改）

---

## 测试覆盖图（TG-18）

```
  code path                                  │ 单元 │ 集成 │ 契约/回归 │ 真机
 ────────────────────────────────────────────┼──────┼──────┼───────────┼──────
  resolve-models.sh   宿主判定（4 分支）      │  ✅  │      │           │ 10.1
    ├ CLAUDECODE=1        → claude           │ 6.1  │      │           │
    ├ CODEX_THREAD_ID     → codex            │ 6.1  │      │           │
    ├ 皆无                → unknown+stderr   │ 6.1  │      │           │
    └ 冲突（两者皆有）    → unknown+告警     │ 6.1  │      │           │
  ────────────────────────────────────────── │      │      │           │
  outside-voice.sh    runner 分叉            │      │  ✅  │           │
    ├ preflight 探目标 runner CLI            │ 7.1  │      │           │
    ├ exec → codex（正向，现有）             │      │ 7.2  │           │ 10.3
    ├ exec → claude（反向，新增）            │      │ 7.4  │           │ 10.2
    ├ 🔒 secret_scan 两路径共用（安全锁）    │ 7.3  │      │           │
    ├ 🔒 render_prompt 两路径共用（安全锁）  │ 7.3  │      │           │
    └ HOST=unknown → 不跑 voice              │ 7.5  │      │           │
  ────────────────────────────────────────── │      │      │           │
  anchor_lint         锚行校验               │  ✅  │      │           │
    ├ host 必填 / 枚举 + runner=none          │ 2.1  │      │           │
    ├ outside-voice 锚 KV 解析（新增）        │ 2.2b │      │           │
    ├ 🔴 自审红线 绑 outside-voice 锚(D1)     │ 2.3  │      │           │ 10.1
    │   降级码集含 preflight-error(D2)+always-on│      │      │           │
    ├ 🔴 fan-out 一致性 lint 机制死却报多镜    │ 2.5  │      │           │ 10.1
    │   always-on(与metrics解耦,D7)+host=codex缺锚拦│  │      │           │
    └ 🔒 不判宿主（ADR-1 边界锁）            │ 2.4  │      │           │
  ────────────────────────────────────────── │      │      │           │
  fan-out 能力探针     语义核验(非机械门,Q1)  │      │  ✅  │           │
    ├ host=codex → 探针落 available/unavail  │ 9.4  │      │           │ 10.1
    └ host=claude → 免探针恒 available       │ 9.4  │      │           │
  ────────────────────────────────────────── │      │      │           │
  lens_metric_emit    行键升维               │  ✅  │      │  golden   │
    ├ --host 必填 / fail-closed              │ 3.1  │      │           │
    ├ 行键 (lens,host,runner,site)           │ 3.2  │      │   3.3     │
    └ 四条既有 Scenario 回归                 │      │      │   3.4     │
  ────────────────────────────────────────── │      │      │           │
  outside_voice_guard 复用判定               │  ✅  │      │           │
    ├ runner==host → same-family（新码）     │ 4.1  │      │           │
    └ v1 旧锚兼容读（不罢工）                │ 4.2  │      │           │
  ────────────────────────────────────────── │      │      │           │
  lens_metric_aggregate  双代兼容            │  ✅  │      │  🔁 5.1   │
    ├ claude-fallback → (claude,claude)      │ 5.2  │      │           │
    ├ 无 host → host=claude                  │ 5.2  │      │           │
    ├ 新旧混合分组                           │ 5.2  │      │           │
    └ 🔁 存量归档聚合逐行一致（回归基线）    │      │      │   5.4     │
  ────────────────────────────────────────── │      │      │           │
  setup.sh            安装面                 │      │  ✅  │           │
    └ ⚠️ 验安装路径而非仓内路径（dogfood 坑）│      │ 6.3  │           │
```

**图例**：🔒 = 边界锁（防实现漂移回旧行为，含 7.3 `--tools` 安全承重墙）· 🔴 = 核心红线（自审绑 outside-voice 锚 + fan-out 一致性 lint，均 always-on）· 🔁 = 回归基线（存量数据零丢失）· ⚠️ = 已知 dogfood 盲区

**覆盖缺口（诚实登记，spec-review 二次审后精化）**：「子代理不可用时镜数如实降级」拆三层——① **一致性 lint 拦「机制死却报多镜」的自相矛盾**（探针 9.4 落 `mirrors=` + lint 2.5 读 `mirrors=`，有自动化测试、always-on、判据源不受 metrics 门控 C2），**但它拦的是自相矛盾非伪造**（写 `subagents="available"` 或只列 1 镜即绕过）；② **探针值/`mirrors=` 本身是主 session 自报**（无机械交叉核验，trust-based）；③ **残余「第 N 镜跑没跑」+「机制活+偷懒自代」无确定性信号**（ADR-4/adr/0023），归语义层（SKILL 指令 + 人读报告 + 事后 host 分组），**无自动化测试**。**MUST NOT 为 ②③ 硬造假机械测试冒充门，也 MUST NOT 因它们无测试而漏掉 ① 的一致性 lint 测试（含 metrics=false 解耦锁——判据读 `mirrors=` 而非 lens-metric 行 + host=codex 缺锚锁）。** **〔efficacy 前置门同理，spec-review-r2 C5〕**：A1/A3 真机验的「真的在真 Codex 宿主跑过」由人门守，MUST NOT 造 `.efficacy-gate-passed` 假机械锁。
