# tasks — add-codex-host-support

> **顺序即 design 的 Migration Plan**：**efficacy 前置门（组 0）**→ 契约先行 → 工具 → 聚合器 → helper → 规则/SKILL → 铺设 → 文档。
> **追溯**：每任务标注所属 capability 的 Requirement 名（本仓 spec 用中文标题作 ID）。
> **测试纪律**：`scripts/` 改动必跑对应 `tests/`；全量 `pytest` 在每个任务组末尾绿。

## 0. efficacy 前置门（Q3 · 改 BREAKING 契约之前先证，冷层对抗镜3 F1/F3）

> **为何在最前**：目标（Codex 里真跨模型）押在 A1/A3 两个未验假设；核验若排在契约之后 = 为可能跑不起来的功能付不可逆代价。**任一在主力形态失效 ⇒ 停下补 headless 替代信号或缩 scope，MUST NOT 直接开工组 1。**

- [ ] 0.1 **A1 核验**：Codex 交互 / headless / `codex exec` / spawned subagent 各形态各跑一次，确认 `CODEX_THREAD_ID` 存在。**任一（尤其 headless/`codex exec`）缺失** ⇒ 停下：design 补该形态的替代正信号，或明确 scope 缩到"仅交互 Codex" + proposal 显著登记〔host-adaptive-execution · 宿主判定靠正信号〕
- [ ] 0.2 **A3 核验**：在**真实 Codex 宿主 session** 内冒烟 `claude -p --model opus --output-format text --tools "Read,Grep,Glob" --strict-mcp-config`——核验点是**"能否成功发出网络请求并拿到 findings"**（非"claude 装没装"）。Codex 若封出境网络 ⇒ 反向 voice 恒失效、永远同族 fallback，design 须承认该 scope 边界〔host-adaptive-execution · outside voice = 另一个机队的强档〕
- [ ] 0.3 前置门结论写回 proposal 假设表 + design Risks（A1/A3 实测真值）；两者皆通过才进组 1

## 1. 契约先行（枚举单一源）

- [ ] 1.1 改 `assets/workflow/lens-metric-contract.md` 的 `lens-metric-enums` 机读块：新增 `host: claude, codex, unknown`；`runner` 收缩为 `claude, codex, none`（删 `claude-fallback`，加 `none`——无执行轮次，D6）〔workflow-metrics · 度量锚契约〕
- [ ] 1.2 改同文件 `lens-metric-fold` 机读块：删 `claude-fallback: outside-voice` 行，保 `codex: outside-voice` 并新增 `claude: outside-voice`（任一 runner 的 voice 都折叠到 outside-voice）〔workflow-metrics · 度量锚契约〕
- [ ] 1.3 改同文件的锚形示例 + 散文注记 + 归属规则段：行键升为 `(lens, host, runner, site)`，唯一键升为 `(layer,lens,host,runner,site,轮)`；写明「跨模型性 = `runner ≠ host` 的派生量，MUST NOT 编码进枚举值」〔workflow-metrics · 度量锚契约〕
- [ ] 1.4 跑全量 pytest 确认**工具测试如期变红**（红的位置 = 依赖契约枚举的全部落点，据此核对 design 的 scope-check 表无遗漏）——**此步的产出是一份红点清单，不是绿**

## 2. 校验工具（anchor_lint）

- [ ] 2.1 TDD：`test_anchor_lint.py` 加用例——`REQUIRED_FIELDS` 含 `host`；缺 `host` 判 missing-field；`host` 越域判 out-of-enum；`runner="claude-fallback"` 判 out-of-enum（已废弃）〔workflow-metrics · 锚字段缺失或取值越域被自检阻塞〕
- [ ] 2.2 实现：`anchor_lint.py` 的 `REQUIRED_FIELDS` 加 `host`，枚举校验加 `host`（枚举仍从契约机读块读，**MUST NOT 在脚本内复制清单**）〔workflow-metrics〕
- [ ] 2.2b TDD + 实现：**新增 outside-voice 锚 KV 字段解析**（D1）——`anchor_lint` 现状对 `sdflow:outside-voice` 锚只记存在性、零字段解析；须解析其 `runner`/`host`/`reason_code`（`reason_code` 为该锚必填），供 2.3 自审红线用〔host-adaptive-execution · 禁止自审〕
- [ ] 2.3 TDD + 实现：**自审红线，绑 outside-voice 锚（非 lens-metric，D1）**——`sdflow:outside-voice 锚 ∧ runner == host ∧ reason_code ∉ {not-installed,preflight-error,timeout,exec-error}` ⇒ 报错阻塞（新违规类型 `self-review`）。**降级码集 MUST 钉死含 `preflight-error`**〔D2：grill G5 初钉漏它=会误报诚实 preflight-error fallback；实现期核 `missing-deps`〕；此校验 **MUST always-on、不受 metrics 门控**（D7）。测试：四个合法降级码各放行 1 例（含 preflight-error）+ `reason_code=none`/缺失各拦 1 例 + 绑错到 lens-metric 锚会静默失效的反例锁〔host-adaptive-execution · 禁止自审；workflow-metrics · 自审锚行被自检阻塞〕
- [ ] 2.4 核验 `anchor_lint` **不判宿主**（ADR-1）：它只读锚行自身的 `host`/`runner` 字段做内部一致性校验，MUST NOT import 或调用 `resolve-models.sh`——加一条测试锁死此边界〔host-adaptive-execution〕
- [ ] 2.5 TDD + 实现：**fan-out always-on 一致性 lint**〔spec-review-amendment Q1 / adr/0023〕——`anchor_lint` 读会话级 `sdflow:fanout-capability` 锚（该锚须在被 lint 的报告文件内，D8）；`subagents="unavailable"` 时，lens-metric 锚里 `lens ∈ {domain,adversarial,grounding}` 的**按 `lens` 去重行数 >1 ⇒ 报错阻塞**（新违规类型 `dead-fanout-multi-mirror`，拦**自相矛盾**非伪造）。**MUST always-on、与 `metrics.enabled` 解耦**（D7：否则默认消费仓空转）；`host=codex` 报告缺该锚 ⇒ 报错（缺锚不得绕过）。测试：unavailable+3 fan-out 行→拦；unavailable+1→放行；available+N→放行（残余留语义层，注释注明）；metrics=false 时仍拦（解耦锁）；host=codex 缺锚→拦〔host-adaptive-execution · 子代理不可用时镜数如实降级〕

## 3. 产出工具（lens_metric_emit）

- [ ] 3.1 TDD：`test_lens_metric_emit.py` 加用例——`--host` 必填但**缺失走受控 fail-closed（可读错误、非 argparse 崩，D4）**；越域（含 `claude-fallback`）⇒ fail-closed；**MUST NOT 默认填 claude**；`runner="none"` 合法（D6，伴 findings=0）〔lens-metric-emit · 缺 --host 或取值越域则受控 fail-closed / runner="none" 行合法〕
- [ ] 3.2 实现：`lens_metric_emit.py` 加 `--host` 参数（单一源，无 per-finding/per-row host；用 `parse_known_args`+显式必填校验使缺 host 受控降级、非崩栈，D4）；行键升为 `(lens, host, runner, site)`；输出锚行带 `host=`；runner 域含 `none`〔lens-metric-emit · 计数由确定性 emitter 归约〕
- [ ] 3.2b 兼容策略落地（D4 · ADR-3-b）：按 design 选定策略处置「新 SKILL × 旧 emitter argparse 罢工」——推荐 SKILL 侧调 emitter 前探其是否认 `--host`（`--help` grep / version），旧则降级 + 报告标注；或工具锁步升级检测〔lens-metric-emit · 跨版本 skew〕
- [ ] 3.3 更新 `tools/tests/fixtures/lens_metric_input.json` golden fixture 至新行键；核对 `MIN_LENS_ROWS` 一致性测试仍绿〔lens-metric-emit〕
- [ ] 3.4 回归：零-finding 行、共抓不计独立、同类型多实例算独立、finding 命中行不在 roster 则 fail-closed —— 四条既有 Scenario 在升维后仍绿〔lens-metric-emit〕

## 4. 复用守卫（outside_voice_guard）

- [ ] 4.1 TDD：`test_outside_voice_guard.py` 加用例——`runner == host`（同族）⇒ 新 reason_code `same-family`、退出码非 0，MUST NOT 复用〔outside-voice-reuse-guard · 同族 fallback 段不得复用〕
- [ ] 4.2 TDD：v1 旧锚（无 `host=`，`runner="codex"`）⇒ 读作 `host="claude"` ⇒ `runner ≠ host` ⇒ 可复用（向后兼容读，**MUST NOT 罢工**）〔outside-voice-reuse-guard · v1 旧锚无 host 字段仍可复用〕
- [ ] 4.3 实现：`outside_voice_guard.py:93` 的 `attrs.get("runner") != "codex"` 改为 `runner == host` 判同族；reason_code 枚举扩至七码〔outside-voice-reuse-guard · 三判归约为单一 reason_code〕

## 5. 聚合器双代兼容（唯一读存量的组件）

- [ ] 5.1 **先固化回归基线**：跑当前 `lens_metric_aggregate.py` 对全部存量归档报告，落基线快照（改造后须逐行一致）〔workflow-retro · 改造前后对存量归档的聚合结果逐行一致〕
- [ ] 5.2 TDD：`test_lens_metric_aggregate.py` 加用例——`runner="claude-fallback"` 旧锚读作 `(host=claude, runner=claude)`；无 `host` 字段读作 `host="claude"`；新旧锚混合仓正确分组不 parse 失败〔workflow-retro · 旧锚按兼容规则读入不丢行 / 新旧锚混合仓正确分组〕
- [ ] 5.3 实现：分组键升为 `(layer, lens, host, runner, site)` + 兼容读；`render_table` 加 `host` 列〔workflow-retro · 聚合器双代兼容读锚行〕
- [ ] 5.4 回归验证：对 5.1 的基线快照，改造后除新增 `host` 列外**每行计数逐行一致**（机验，非目测）〔workflow-retro〕
- [ ] 5.5 同步 `retro_report.py` 及其测试（若引用 runner 枚举或分组键）〔workflow-retro〕

## 6. 宿主判定 helper（新组件）

- [ ] 6.1 TDD：`sdflow-init/tests/test_resolve_models.py` —— `CLAUDECODE=1` ⇒ `HOST=claude`；`CODEX_THREAD_ID=<uuid>` ⇒ `HOST=codex`；两者皆无 ⇒ `HOST=unknown` + stderr 明示；**两者同时存在 ⇒ `unknown` + 信号冲突告警**（MUST NOT 静默取其一）〔host-adaptive-execution · 宿主判定靠正信号〕
- [ ] 6.2 实现 `sdflow-init/assets/hack/resolve-models.sh`：纯 shell（ADR-1：校验侧不需要宿主判定，故无需 Python 双实现）；`eval` 导出六个变量；档位表从 `model-tiers.md` 读，**MUST NOT 内联模型名**〔host-adaptive-execution · 模型档位按机队分列〕
- [ ] 6.2b TDD + 实现：**覆盖按机队分键读**〔grill-amendment G4 / adr/0024〕——`config.yaml` 的 `model-tiers.{claude,codex}.{strong,mid,light}` 按当前机队读；**扁平旧格式**（`model-tiers.strong: …`）兼容读作 **Claude 机队**覆盖，MUST NOT 罢工；无当前机队段回落机队缺省。测试：分键格式读对应段 / 扁平格式在 claude 宿主生效、在 codex 宿主**不生效**（回落 codex 缺省，不把 opus 塞给 codex）〔host-adaptive-execution · 消费仓覆盖段仍生效；spec-workflow · 模型档位映射〕
- [ ] 6.2c 同步 `config.template.yaml` 示例为分键格式 + `test_config_lint.py` 认识分键与扁平两种〔host-adaptive-execution〕
- [ ] 6.2d **eval 注入加固**（D5 · 冷层 codex CV4）：`resolve-models.sh` 输出六变量 SHALL 用 `printf %q`/`declare -p` 安全编码 + 拒换行/控制字符/非模型 ID 字符；`config_lint` 校验 model-tiers 的**值**（非仅键）为合法模型 ID。测试：覆盖值含 `$()`/反引号/换行/引号的**恶意值回归**（断言不在 eval 时执行）。**SHOULD 评估取消 eval**（改 source 受控生成文件 / 数组读取）〔host-adaptive-execution · resolver 输出不得成为 eval 注入面〕
- [ ] 6.3 `setup.sh` 装 `resolve-models.sh` 进 `~/.sdflow/hack/` + 测试守（**dogfood 盲区**：`skill-principles.md` 曾因 setup 只拷 `*.sh` 而漏装、仓内测试全绿——本条测试 MUST 验**安装路径**，不是仓内路径）〔host-adaptive-execution〕
- [ ] 6.4 **G6 同源锁**〔grill-amendment G6 / ADR-9〕：`resolve-models.sh` 每轮 eval 一次导出六变量供 SKILL export；`outside-voice.sh` **只从环境读 `$SDFLOW_VOICE_RUNNER`、MUST NOT 自调 `resolve-models.sh` 重判宿主**——加测试断言 `outside-voice.sh` 不含对 `resolve-models.sh` 的调用〔host-adaptive-execution · outside voice = 另一个机队的强档〕

## 7. outside-voice 去硬编码（安全面，改动最敏感）

- [ ] 7.1 TDD：`test_outside_voice.py` 加用例——`preflight` 探测的是 `$SDFLOW_VOICE_RUNNER` 的 CLI，**不是固定的 codex**；`HOST=codex` 时探 `claude`〔host-adaptive-execution · outside voice = 另一个机队的强档〕
- [ ] 7.2 实现：`outside-voice.sh` 的 `preflight` / `do_exec` 按 runner 分叉；**`secret_scan` / `render_prompt`（FRAME + 三条通则）/ 200KB 截断保持单份共用**，只有最终 exec 命令行一处分叉〔host-adaptive-execution · 出境安全三件套对两条路径一视同仁〕
- [ ] 7.3 TDD：**安全回归锁（承重墙，spec-review-amendment Q2）**——加测试断言反向路径（claude）走同一个 `secret_scan` 与同一个 `render_prompt`；secret 命中时**两条路径都 exit 3 拒发且不 fallback**；**且断言 claude exec 行含 `--tools "Read,Grep,Glob"` + `--strict-mcp-config`、不含 `--disallowedTools`、不含 `--allowedTools`**（防漂移回 denylist 或弱 allowlist）〔host-adaptive-execution · secret 命中时两条路径都拒发 / 只读约束〕
- [ ] 7.4 实现反向 runner 调用：`claude -p --model "$SDFLOW_VOICE_MODEL" --output-format text --tools "Read,Grep,Glob" --strict-mcp-config`（实现期核对 claude CLI 确切只读工具名 + `--add-dir`/ephemeral cwd 收紧 Read）〔spec-review-amendment Q2：**MUST 用 `--tools` 独占白名单**（`--allowedTools` 会与 settings `permissions.allow` 合并被穿透、非 deny-by-default；`--disallowedTools` denylist 留 Bash/WebFetch）+ `--strict-mcp-config` 隔离 ambient MCP；只读姿势诚实登记为「应用层尽力、非内核级对等」〕〔host-adaptive-execution · 只读约束按 runner 落到对应机制〕
- [ ] 7.5 实现 `HOST=unknown` ⇒ **不跑 voice** + `reason_code="host-unknown"`（fail-loud，MUST NOT 任选 runner 充作跨模型）〔host-adaptive-execution · 宿主 unknown 则不跑 voice〕
- [ ] 7.6 `outside-voice.sh` 版本号升至 1.2.0；头部契约注释同步（它是两个 review SKILL 引用的契约单一源）

## 8. 规则与 SKILL

- [ ] 8.1 改 `assets/workflow/model-tiers.md`：档位表按机队分列（Claude: opus/sonnet/haiku；Codex: gpt-5.6-sol/terra/luna）+ 覆盖段注记改为**按机队分键**（`model-tiers.{claude,codex}.*`，扁平旧格式兼容读作 Claude 机队，见 adr/0024）〔grill-amendment G4；host-adaptive-execution · 模型档位按机队分列；spec-workflow · 模型档位映射〕
- [ ] 8.2 改 `sdflow-spec-review/SKILL.md`：锚行文法（加 `host=`）· outside-voice 调用协议引用 `resolve-models.sh` · lens-metric roster 构造带 `--host`〔spec-workflow · 跨模型 outside voice〕
- [ ] 8.3 改 `sdflow-code-review/SKILL.md`：同 8.2 + **置信豁免规则改判据**——`runner ≠ host` 豁免 <80 数值滤、`runner == host` 照过滤（`SKILL.md:172` 是旧假绿点）〔spec-workflow · outside-voice tension 不静默采纳〕
- [ ] 8.4 各编排 SKILL（ship/done/spec-review/code-review）的模型选择改引用 `SDFLOW_TIER_*` 变量，**MUST NOT 内联模型名**〔spec-workflow · 模型档位映射〕
- [ ] 8.5 SKILL 写明「Codex 宿主下 `spawn_agent` 指定 model 的 task-specific reason = 本工作流的 model-tiers（门禁步禁降档是硬约束）」〔host-adaptive-execution · 子代理不可用时镜数如实降级〕

## 9. 消费项目铺设（Codex 子代理授权）

- [ ] 9.1 `sdflow-init/assets/snippets/claude-section.md` + AGENTS.md 段加 **Codex 子代理授权声明**（多镜 fan-out + model-tiers 构成 codex 要求的显式授权）〔host-adaptive-execution · 授权声明存在〕
- [ ] 9.2 SKILL 写明「子代理不可用 ⇒ MUST 缩 roster 到实跑的镜 + 报告显著标注单镜降级」；**登记诚实边界**〔spec-review-amendment Q1：探针=机制活着的**语义核验**（非机械门，主 session 自报 trust-based）；一致性 lint（2.5）只拦「机制死却报多镜」的**自相矛盾**、always-on；残余「第 N 镜跑没跑」+「机制活+偷懒自代」无机械守——诚实分开，MUST NOT 声称"头号假绿事前拦截"〕〔host-adaptive-execution · 子代理不可用则缩 roster〕
- [ ] 9.3 `sdflow-init/tests/` 加守卫：铺设产物含授权段（机验存在性）
- [ ] 9.4 SKILL fan-out 前跑**能力探针（语义核验）**〔spec-review-amendment Q1 / adr/0023〕：`host=codex` ⇒ 派 trivial 探针子代理（回哨兵值=available）；`host=claude` ⇒ 免探针恒 available；落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="…" -->`**到被 lint 的报告文件内**（D8）。探针为 unavailable ⇒ SKILL MUST 缩 roster 到单镜（否则 2.5 一致性 lint 拦）。**探针值为主 session 自报，非机械核验**——如实登记〔host-adaptive-execution · 子代理不可用时镜数如实降级〕

## 10. 端到端真机核验（A1/A3 已上提组 0 前置门）

> A1/A3 的存在性核验已上提为**组 0 前置门**（Q3）——本组只留改造后的端到端验证。

- [ ] 10.1 端到端：Codex 宿主下跑一次真实评审，核对 outside-voice 锚为 `host="codex" runner="claude"`、fanout-capability 锚在场、且 `anchor_lint` 绿（含新增的自审红线 + 一致性 lint always-on）
- [ ] 10.2 回归：Claude 宿主下跑一次，确认现有行为不变（`host="claude" runner="codex"`），存量归档聚合逐行一致（组 5 基线）

## 11. 文档与收尾

- [ ] 11.1 同步 `docs/workflow-map.md`(:141,:150) + `docs/workflow-map.html`(:555,:563) 的字段表与枚举
- [ ] 11.2 全量 `pytest` 绿 + `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿
- [ ] 11.3 逐面核对 design 的 **scope-check 表 面 1–10** 全部改完（基准 3 面治：留任何一面 = 契约漂移）+ 面 11 pre-existing debris 已核（登记非改）

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

**覆盖缺口（诚实登记，spec-review 后精化）**：「子代理不可用时镜数如实降级」拆三层——① **一致性 lint 拦「机制死却报多镜」的自相矛盾**（探针 9.4 + lint 2.5 有自动化测试、always-on），**但它拦的是自相矛盾非伪造**（写 `subagents="available"` 即绕过）；② **探针值本身是主 session 自报**（无机械交叉核验，trust-based）；③ **残余「第 N 镜跑没跑」+「机制活+偷懒自代」无确定性信号**（ADR-4/adr/0023），归语义层（SKILL 指令 + 人读报告 + 事后 host 分组），**无自动化测试**。**MUST NOT 为 ②③ 硬造假机械测试冒充门，也 MUST NOT 因它们无测试而漏掉 ① 的一致性 lint 测试（含 metrics=false 解耦锁 + host=codex 缺锚锁）。**
