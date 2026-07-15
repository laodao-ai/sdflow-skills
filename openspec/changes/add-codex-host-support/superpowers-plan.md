# add-codex-host-support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **权威源**：本 change 的 `design.md`（ADR-1…ADR-9 + 合法组合矩阵 + 失败模式表 + 安全表 + scope-check 表）、六个 `specs/*/spec.md`（Requirement + Scenario）、`tasks.md`（组 0–11 逐条 + 测试覆盖图）是**逐字权威**——implementer **MUST 读对应 spec Scenario 与 design ADR** 再动手；plan 内的约束复述是"够不着 Global Constraints 的兜底"，冲突时以 spec/design 为准。

**Goal:** 让整套 sdflow 评审工作流在 Codex 宿主下跑对——把"宿主 = Claude Code"的隐含假设显式化，杀掉两个静默假绿：outside-voice 自审冒充跨模型、多镜静默退化成单镜仍报满 roster。

**Architecture:** 新增纯 shell `resolve-models.sh`（正信号判宿主 + 出机队档位）；`outside-voice.sh` 去 codex 硬编码、按 runner 分叉（Codex 宿主 → 反向调 `claude -p` 只读全仓）；锚行 schema 升 v2（加 `host=`、`runner` 枚举 `{claude,codex,none}` + 普通镜 `unknown`）；"跨模型性"提升为 **anchor_lint always-on 合法组合矩阵**的派生判定（单一真相源，`outside_voice_guard` 各自本地重实现 + 全笛卡尔 golden 守）；聚合器双代兼容读存量。

**Tech Stack:** Bash（helper）· Python 3 + pytest（tools/ 聚合器）· Markdown（规则/SKILL/契约机读块）。不命中 backend·go / embedded / frontend 领域清单。

---

## 🚨 DEFERRED PREREQUISITE — efficacy 前置门（组 0）已知未清，用户拍板 option B

> **决策留痕（2026-07-15，人门纪律）**：design 的 Migration step 0（efficacy 前置门 A1/A3 真机核验）**必须在真实 Codex 宿主执行**，当前实现跑在 Claude 宿主（`CLAUDECODE=1`）——**A1/A3 无法从 Claude 宿主验证**，proposal 假设表 A3 仍标"未在真实 Codex 沙箱内验证"。
>
> 用户**显式接受 design Risks 已登记的 Codex-efficacy 未验风险**，授权先完成本 plan 的 **Claude-side 全部实现（Task 1–10）+ 冷审**；A1/A3 真机核验 + Codex 端到端（下方"Deferred to Codex host"节）**deferred 至用户后续在 Codex 宿主执行**（"先做好 skill，再到 Codex 测"）。∴ 本 change **实现 + 冷审完成后 STOP，不自动 done/merge**——等用户 Codex 测过、把 A1/A3 实测真值写回 proposal/design（done/archive 阶段）后再收尾。
>
> **这不是走过场假绿**：决策留痕 + Codex 验证明确挂起 + 失效方向 fail-loud（不假绿）+ **MUST NOT 由任何子代理伪造 A1/A3 "passed"**（GC-10）。proposal/design 的写回**在 done/archive 阶段做**（四件套此期冻结，实现期改会触 ship_gate 设计门失鲜）。

---

## Global Constraints

> 项目级不变量——每个 Task 的要求隐含包含本节。逐字复制自 `design.md` / spec Requirement。**注：`scripts/task-brief` 只把 `### Task N` 段喂给 implementer，本节 implementer 看不到 ⇒ 每个 Task 段内已复述与其相关的条目 + 三条通则。**

- **GC-1 合法组合矩阵是「跨模型性」的机械单一源**（design 数据模型段 / spec `host-adaptive-execution` Req）：`anchor_lint` 一张 always-on 矩阵钉死 `sdflow:outside-voice` 锚的合法 `(host,runner,reason_code,findings)`。跨模型 = `host,runner∈{claude,codex} ∧ runner≠host ∧ reason_code="ok"`。派生语义 / 置信豁免 / 复用守卫 **MUST 引用矩阵判定，MUST NOT 各自写裸 `runner≠host`**（被 `runner="none"`（`none≠host` 恒真）击穿，C1）。
- **GC-2 矩阵跨工具 = 枚举域进契约块 + 关系式逻辑两工具各自本地重实现 + 全笛卡尔 golden**（spec 同 Req · r3-narrow）：`outside_voice_guard.py` 有 **`MUST NOT import`** 边界 ⇒ 不能共享函数。枚举域由 `lens-metric-contract.md` 机读块承载；**关系式判定逻辑**（三态分类 illegal/cross-model/same-family/no-exec）由 `anchor_lint` 与 `outside_voice_guard` **各自本地重实现**；防漂移靠一条 golden 对 `host×runner×reason_code×findings` **全笛卡尔积**（含 mutation）断言两工具**完整分类**逐条一致——**MUST NOT 只比布尔**（同源同错测不出）。
- **GC-3 always-on 校验独立成函数、不接受 `metrics_on` 参数**（design scope-check 面 2 · D11，照 `check_hr_tg` 先例）：自审红线（矩阵）+ fan-out 一致性 lint 均 always-on，其**判据数据源亦 always-on**——一致性 lint 读 `fanout-capability` 锚的 `mirrors=`（SKILL 直接落、不经 emitter/lens-metric、不读 `config.metrics`），**MUST NOT 数受 metrics 门控的 lens-metric 行**（C2）。
- **GC-4 出境安全三件套单份共用**（design 安全表 / spec "出境安全" Req）：`secret_scan` / `render_prompt`（FRAME + 三条通则 + UNTRUSTED 硬分隔）/ 200KB 保头尾截断 是**两条 runner 路径同一份代码**，只有最终 `exec` 一行按 runner 分叉。反向路径 **MUST NOT 另起炉灶组装 prompt**。
- **GC-5 反向 `claude -p` 三旗承重墙**（design 安全表 · spec "只读约束按 runner 落地" Scenario · C4）：`--tools "Read,Grep,Glob"` + `--strict-mcp-config` + `--add-dir <repo_root>` 三旗齐全。**MUST NOT** 给 Write/Bash/WebFetch / `--tools ""` 零工具 / `--disallowedTools` / `--allowedTools` / 漏 `--strict-mcp-config` / 漏 `--add-dir`。应用层尽力对齐（非声称与内核级沙箱对等）。只约束跨模型反向路径，**不改同族 fallback 子代理**。
- **GC-6 resolver 纯 shell + eval 注入加固**（ADR-1 · D5 · spec D5/D10 Scenario）：`resolve-models.sh` 纯 shell；输出六变量供 `eval` SHALL 用 `printf %q`/`declare -p` 安全编码 + 拒换行/控制字符/非模型 ID 字符；读 config 覆盖须与 `config_lint` **共用同一解析实现 + 畸形输入测试**。**MUST NOT 内联模型名**——从 `model-tiers.md` 读。
- **GC-7 宿主判定靠正信号、判不出 fail-loud、每轮单点判定**（spec "宿主判定" Req · ADR-7/ADR-9）：Claude=`CLAUDECODE=1`、Codex=`CODEX_THREAD_ID` 非空；**MUST NOT 用"缺失即另一方"推断**；两信号皆无或**同时存在** ⇒ `host=unknown` + stderr 明示，不猜。宿主每轮 eval 一次，`outside-voice.sh` **只从环境读 `$SDFLOW_VOICE_RUNNER`、MUST NOT 自调 `resolve-models.sh` 重判**。
- **GC-8 锚行 v2 枚举收缩**：`host∈{claude,codex,unknown}`；`runner∈{claude,codex,none,unknown}`——**`unknown` 仅合法于非-outside-voice 普通镜行 ∧ host=unknown**，outside-voice 锚 runner 恒 ∈{claude,codex,none}；`claude-fallback` **废弃**。成功哨兵 `reason_code="ok"`（D5）；无执行 `runner="none" ∧ findings=0`（D6）；合法同族降级码集钉死 `{not-installed,preflight-error,timeout,exec-error}`（`missing-deps` 归约 `preflight-error`，D7）。
- **GC-9 存量不迁移、聚合器唯一读存量、逐行一致回归**（spec `workflow-retro` Req）：`lens_metric_aggregate.py` 唯一读归档锚，双代兼容读（`claude-fallback`→`(claude,claude)`；无 `host`→`host=claude`），改造前后对存量归档聚合**逐行一致**（Success Metric 4，机验）。
- **GC-10 efficacy 前置门是人门纪律、MUST NOT 造假机械锁**（spec/design Migration step 0 · C5）：A1/A3 真机核验由**人门守**，**MUST NOT 造 `.efficacy-gate-passed` 之类假机械锁**（marker 自报无可信捕获路径，同探针之坑）。**MUST NOT 由子代理伪造"验过"。**
- **GC-11 面治一次扫全**（design scope-check 表 · 基准 3）：scope-check 表面 1–10 MUST 在**同一 change** 内改完，留一面 = 契约漂移。面 11（pre-existing debris）只核查登记、**不在本 scope 内改**。
- **GC-12 版本 & 测试纪律**：`outside-voice.sh` 版本升至 `1.2.0`；`scripts/` 改动必跑对应 `tests/`；每个任务末尾全量 `pytest` 绿 + `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿；枚举 **MUST 从契约机读块读、MUST NOT 在脚本内复制清单**。

### 三条通则（本项目一切任务适用 · 每个 Task 段已复述，此处存档全文）

**① 能查的自己查，能调研的自己调研**：答案在仓/机器/公开资料里 ⇒ 自己去拿、给结论。MUST NOT 拿一个自己查得到的问题去占用人的注意力。

**② 不确定的方案，先调研再给推荐 —— MUST NOT 甩开放题**：拿不准时先把能查的查了，带「推荐 + 依据 + 代价 + 备选」，人只拍板。

**③ 以最终目标为准，MUST NOT 拿现状反驳目标**：判断该不该做/做到什么程度一律锚**目标态**。MUST NOT 用「现在代码不是这么写的 / 存量里没出现过 / 现状里很少见 / 现有设计不支持所以改小」论证目标缩水。迁移中「旧数据还没新形态」是必然——问「目标态 producer 会不会产出这种形态」，不是「现存文件里有没有」。**评审/实现时高发：现状是唯一摆在眼前的东西，别把「现在能跑」当「是对的」。**

---

## 测试覆盖图（承 tasks.md TG-18）

```
  code path                                  │ 单元 │ 集成 │ 契约/回归 │ 真机(Codex,deferred)
 ────────────────────────────────────────────┼──────┼──────┼───────────┼──────
  resolve-models.sh   宿主判定（4 分支）      │  T6  │      │           │ ⏸ Deferred
  outside-voice.sh    runner 分叉 + 安全锁    │ T7   │ T7   │           │ ⏸ Deferred
  anchor_lint  host/矩阵/一致性lint/边界锁    │ T2   │      │           │ ⏸ Deferred
  fan-out 能力探针     语义核验(非机械门)      │      │ T9   │           │ ⏸ Deferred
  lens_metric_emit    行键升维 + skew         │ T3   │      │  golden   │
  outside_voice_guard 复用判定 + 全笛卡尔     │ T4   │      │  T4       │
  lens_metric_aggregate  双代兼容            │ T5   │      │  🔁 T5    │
  setup.sh            安装面(验安装路径)      │      │ T6   │           │
  Claude 宿主 e2e 回归                        │      │      │           │ T10(Claude 侧)
```
🔒 边界锁（防漂移回旧行为）· 🔴 核心红线（自审绑 outside-voice 锚 + fan-out 一致性 lint，均 always-on）· 🔁 回归基线（存量零丢失）· ⏸ Deferred = 真 Codex 宿主步，见文末"Deferred to Codex host"

---

### Task 1: 契约先行（枚举单一源）

**Files:**
- Modify: `sdflow-init/assets/workflow/lens-metric-contract.md`（`lens-metric-enums` 块 · `lens-metric-fold` 块 · 锚形示例 · 散文注记 · 归属规则段）

**Interfaces:**
- Produces: `lens-metric-enums` 块新增 `host: claude, codex, unknown`；`runner: claude, codex, none, unknown`（删 `claude-fallback`）；新增 `reason_code` 8 值域 `ok, not-installed, preflight-error, timeout, exec-error, host-unknown, secret-hit, fallback-unavailable`。**关系式矩阵逻辑 NOT 落机读块**（平铺 `key:值` 块装不下 `runner≠host` 等关系式，GC-2）——块只承载枚举域。`lens-metric-fold` 块删 `claude-fallback:` 行、保 `codex: outside-voice` + 新增 `claude: outside-voice`。行键升 `(lens,host,runner,site)`、唯一键 `(layer,lens,host,runner,site,轮)`。

- [ ] **Step 1** 改 `lens-metric-enums` 机读块：加 `host` 域、`runner` 加 `none`+`unknown` 删 `claude-fallback`、加 `reason_code` 8 值域。（tasks 1.1；注 r3-narrow：矩阵关系式不入块）
- [ ] **Step 2** 改 `lens-metric-fold` 块：删 `claude-fallback: outside-voice`，加 `claude: outside-voice`。（tasks 1.2）
- [ ] **Step 3** 改锚形示例 + 散文注记 + 归属规则段：行键升维；写明「跨模型性 = 合法组合矩阵派生量，MUST NOT 编码进枚举值、MUST NOT 简写裸 `runner≠host`（C1 击穿）」。（tasks 1.3）
- [ ] **Step 4** 跑全量 `pytest`，确认**工具测试如期变红**——红点位置 = 依赖契约枚举的全部落点，据此核对 design scope-check 表无遗漏。**本步产出是红点清单，不是绿。**（tasks 1.4）
- [ ] **Step 5: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task1-contract "契约先行: lens-metric-enums 加 host/runner=none,unknown/reason_code 8 值域、fold 块删 claude-fallback"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-1/GC-2/GC-8**：矩阵是单一源、关系式逻辑**不落机读块**只承载枚举域；`claude-fallback` 废弃；`unknown` 仅普通镜 ∧ host=unknown 合法。
- **权威**：spec `workflow-metrics`「度量锚契约」Req + design「数据模型」段。契约块是**所有工具的枚举单一源**，先改它、测试自然变红暴露依赖点。
- **三条通则**：① 用 `grep -rn "claude-fallback\|runner"` 自查落点；③ 锚目标态 v2 schema，**MUST NOT** 因"存量锚都是 v1、没有 host" 就把 host 设可选——目标态 producer 必落 host（GC-8）。

---

### Task 2: 校验工具 anchor_lint（🔴 核心红线：合法组合矩阵 + 一致性 lint）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/anchor_lint.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`

**Interfaces:**
- Consumes: `lens-metric-contract.md` 的 `lens-metric-enums` 机读块（Task 1 产出）——枚举域从块读，**MUST NOT 脚本内复制清单**。
- Produces: 新增 ① `REQUIRED_FIELDS` 含 `host`；② outside-voice 锚 KV 解析（现状只记存在性）；③ **always-on 合法组合矩阵**校验函数（不接受 `metrics_on` 参数）；④ `fanout-capability` 锚解析 + **always-on 一致性 lint 读 `mirrors=`**；⑤ lens-metric 普通镜行级组合校验；⑥ runner 枚举加 `none`。违规类型 `illegal-combo`/`self-review`/`dead-fanout-multi-mirror`。

- [ ] **Step 1 (TDD)** 加用例：`REQUIRED_FIELDS` 含 `host`；缺 `host`→missing-field；`host` 越域→out-of-enum；`runner="claude-fallback"`→out-of-enum。跑，FAIL。（tasks 2.1）
- [ ] **Step 2 (实现)** `REQUIRED_FIELDS` 加 `host`，枚举校验加 `host`（从契约块读）。→ PASS。（tasks 2.2）
- [ ] **Step 3 (TDD+实现)** 新增 **outside-voice 锚 KV 解析**（`runner`/`host`/`reason_code`，`reason_code` 该锚必填）。（tasks 2.2b）
- [ ] **Step 4 (TDD+实现) 🔴 合法组合矩阵 = 自审红线单一源** — always-on、独立成函数、不接受 `metrics_on`；枚举域从契约块读、**关系式判定逻辑本地重实现**（GC-2）。钉死 `sdflow:outside-voice` 锚合法 `(host,runner,reason_code,findings)`：① 跨模型 `host,runner∈{claude,codex}∧runner≠host∧reason_code="ok"` ② 同族 `runner==host∧reason_code∈{not-installed,preflight-error,timeout,exec-error}` ③ 无执行 `runner="none"∧findings=0∧reason_code∈{host-unknown,secret-hit,fallback-unavailable}`；余者报错。**F6 自审红线 = 矩阵②行 reason_code 子句，非并列规则。** 测试：三类合法各放行 1 例 + `runner=none findings=5`→拦 + `host=unknown runner=claude`→拦 + `runner==host reason_code=ok`→拦(自审) + **`outside-voice 锚 runner=unknown`→拦**（catch-all 显式回归锁）+ 绑错到 lens-metric 锚(无 reason_code)静默失效的反例锁 + **metrics=false 时仍拦（解耦锁）**。（tasks 2.3）
- [ ] **Step 5 (TDD+实现)** lens-metric 普通镜行级校验：`site="—"∧runner==host`；`runner="unknown"` **仅** host="unknown" 时合法；普通镜 MUST NOT `runner="none"`。测试：`host=claude lens=domain runner=unknown`→拦、`host=unknown lens=domain runner=unknown`→放行、普通镜 `runner=none`→拦。（tasks 2.3b）
- [ ] **Step 6 (TDD)** 🔒 边界锁：`anchor_lint` **不判宿主**（ADR-1）——MUST NOT import/调 `resolve-models.sh`。加测试锁死。（tasks 2.4）
- [ ] **Step 7 (TDD+实现) 🔴 fan-out always-on 一致性 lint 读 `mirrors=`** — 读会话级 `sdflow:fanout-capability` 锚；`subagents="unavailable"` 时**同锚 `mirrors=`** 中 `∈{domain,adversarial,grounding}` 去重计数 >1 ⇒ 报错（`dead-fanout-multi-mirror`）。**判据 MUST 读 `mirrors=`、MUST NOT 数 lens-metric 行（C2）。** 严格文法 fail-closed：`subagents=""`/未知值/缺字段→fail-closed；`mirrors=` 缺/空/未知 token/重复 token→fail-closed；capability 锚 host 与报告 host 不一致→fail-closed；重复 capability 锚→fail-closed；`host=codex` 报告缺该锚→报错。测试：unavailable+mirrors列3镜→拦；unavailable+1→放行；available+N→放行（残余留语义层）；**metrics=false 且无 lens-metric 行时仍拦（解耦锁）**；各 fail-closed 分支。（tasks 2.5）
- [ ] **Step 8** 跑 `pytest sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py` → 全绿。
- [ ] **Step 9: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task2-anchor-lint "anchor_lint: host 必填 + always-on 合法组合矩阵(自审红线) + fanout 一致性 lint(读 mirrors=) + 普通镜行级校验 + 不判宿主边界锁"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-1/GC-2/GC-3**：矩阵单一源、关系式本地重实现、always-on 独立成函数不接受 `metrics_on`、一致性 lint 判据读 `mirrors=` 不数 lens-metric 行。
- **权威**：spec `host-adaptive-execution`「合法组合矩阵」+「子代理不可用镜数如实降级」两 Req 全 Scenario；spec `workflow-metrics`「自审锚行被自检阻塞」+「fan-out 机制死却报多镜」；design ADR-1/ADR-4 + F6 红线段（读 outside-voice 锚非 lens-metric 锚——绑错静默永不触发）。
- **③ 目标态**：矩阵/红线防的是**目标态**才出现的 Codex 自审轮次；**MUST NOT** 因"存量没有 runner=none / host=codex 锚"就弱化校验——fixture 构造它们，非依赖存量。**MUST NOT 把「机制活+偷懒自代」也说成机械拦住**（诚实边界，只拦机制死变体）。

---

### Task 3: 产出工具 lens_metric_emit（行键升维 + skew 工具侧兜底）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/lens_metric_emit.py`
- Test: `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py` · `tools/tests/fixtures/lens_metric_input.json`

**Interfaces:**
- Consumes: `--host claude|codex|unknown`（单一源，无 per-finding/per-row host）；roster 行键含 `host`。
- Produces: 行键升 `(lens,host,runner,site)`；锚行带 `host=`；runner 域含 `none`；缺 `--host` 受控 fail-closed（非 argparse 崩）；`if extras: fail-closed`。

- [ ] **Step 1 (TDD)** 加用例：`--host` 缺失→**受控 fail-closed（可读错误、非崩，D4）**；越域（含 `claude-fallback`）→fail-closed；**MUST NOT 默认填 claude**；`runner="none"` 合法（伴 findings=0）。跑，FAIL。（tasks 3.1）
- [ ] **Step 2 (实现)** 加 `--host`（`parse_known_args`+显式必填校验使缺 host 受控降级非崩栈；`if extras: fail-closed` 拒多余/拼错参数，D12）；行键升维；锚带 `host=`；runner 域含 `none`。（tasks 3.2）
- [ ] **Step 3 (TDD)** skew 工具侧兜底：`parse_known_args` 受控 fail-closed **只护「新 emitter × 旧调用方」**（对已部署旧 emitter 够不着，SKILL 侧探测才是主守 Task 8）。（tasks 3.2b 工具侧）
- [ ] **Step 4** 更新 `fixtures/lens_metric_input.json` golden 至新行键；核对 `MIN_LENS_ROWS` 一致性测试仍绿。（tasks 3.3）
- [ ] **Step 5 (回归)** 四条既有 Scenario 升维后仍绿：零-finding 落全零、共抓不计独立、同类型多实例算独立、命中行不在 roster 则 fail-closed。（tasks 3.4）
- [ ] **Step 6** 跑 `pytest .../test_lens_metric_emit.py` → 全绿。
- [ ] **Step 7: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task3-emit "lens_metric_emit: --host 单一源(缺失受控 fail-closed 非崩)、行键升 (lens,host,runner,site)、runner=none 合法"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-8**：`--host` 单一源无 per-row host；缺失受控 fail-closed **MUST NOT 默认填 claude**（静默默认把 Codex 轮伪装成 Claude = 要杀的假绿）。
- **权威**：spec `lens-metric-emit`「计数由确定性 emitter 归约」Req 全 Scenario（"缺 --host 受控 fail-closed"、"runner=none 行合法"、"跨版本 skew"注）；design scope-check 面 3。
- **三条通则**：① 读 `lens_metric_emit.py` 现有 argparse 结构自查；③ **MUST NOT** 因"现在调用方都传 host"就省掉受控 fail-closed——目标态有旧调用方/拼写错。

---

### Task 4: 复用守卫 outside_voice_guard（引用矩阵 + 全笛卡尔 golden）

**Files:**
- Modify: `sdflow-init/assets/workflow/tools/outside_voice_guard.py`（`:93` `:101`）
- Test: `sdflow-init/assets/workflow/tools/tests/test_outside_voice_guard.py`

**Interfaces:**
- Consumes: 契约块枚举域（自读）；**MUST NOT import `anchor_lint`**（GC-2 铁律）——关系式分类本地重实现。
- Produces: `:93` 的 `runner != "codex"` → 引用矩阵「跨模型」判定；`runner==host`（同族）与 `runner="none"`（无执行）均输出 `same-family` 不复用；reason_code 枚举扩七码。

- [ ] **Step 1 (TDD)** `runner==host`（同族）⇒ 新 reason_code `same-family`、退出码非 0、MUST NOT 复用。跑，FAIL。（tasks 4.1）
- [ ] **Step 2 (TDD)** v1 旧锚（无 `host=`，`runner="codex"`）⇒ 读作 `host="claude"` ⇒ `runner≠host` ⇒ 可复用（v1 无 reason_code 兼容读作 `ok`），**MUST NOT 罢工**。（tasks 4.2）
- [ ] **Step 3 (实现)** `:93` 改为**引用合法组合矩阵的「跨模型」判定**（本地重实现，MUST NOT 自写 `runner==host`）；`runner==host` 与 `runner="none"` 均输出 `same-family`；reason_code 扩七码。（tasks 4.3）
- [ ] **Step 4 (TDD)** `runner="none"` 段（`host="codex" runner="none"`）⇒ 输出 `same-family`、退出码非 0、不复用（防 `none≠host` 误判，C1）。（tasks 4.4）
- [ ] **Step 5 (TDD) 🔒 矩阵跨工具全笛卡尔 golden** — 从契约块读枚举域 + 本地重实现关系式分类；golden 对 **host×runner×reason_code×findings 全笛卡尔积**（含边界 + mutation：越域/缺字段/坏值）喂 `anchor_lint` 与 `outside_voice_guard` 两者，断言二者**完整分类**（illegal/cross-model/same-family/no-exec，**非仅布尔**）逐条一致，任一漂移即红。（tasks 4.5）
- [ ] **Step 6 (TDD)** `codex#N` 标签旁路核（`:101`）：prose 标签计数是次选 findings 计数，**MUST NOT 单独构成"可复用"资格**——复用须至少一条被矩阵分类 `cross-model` 的可解析锚。测试：无锚/非法锚/`runner="none"` 锚 + `codex#1` prose 标签 ⇒ 拒复用。（tasks 4.6）
- [ ] **Step 7** 跑 `pytest .../test_outside_voice_guard.py` → 全绿。
- [ ] **Step 8: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task4-guard "outside_voice_guard: :93 引用矩阵跨模型判定(不自写 runner==host)、runner=none/同族=same-family、全笛卡尔 golden 跨工具一致、codex#N prose 旁路核"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-1/GC-2**：**MUST NOT import anchor_lint**、关系式本地重实现、golden 断言**完整分类**非布尔（同源同错测不出）。
- **权威**：spec `outside-voice-reuse-guard`「三判归约单一 reason_code」Req 全 Scenario（"同族不得复用"、"runner=none 不得复用"、"v1 旧锚仍可复用"）；design ADR-5 + scope-check 面 4。
- **③ 目标态**：v1 旧锚兼容读 = 目标态必然；**MUST NOT** 因缺字段就 fail-closed 罢工（旧产物依然可复用，GC-9）。

---

### Task 5: 聚合器双代兼容（唯一读存量的组件）

**Files:**
- Modify: `sdflow-retro/scripts/lens_metric_aggregate.py` · `sdflow-retro/scripts/retro_report.py`（若引用 runner 枚举/分组键）
- Test: `sdflow-retro/tests/test_lens_metric_aggregate.py`

**Interfaces:**
- Produces: 分组键升 `(layer,lens,host,runner,site)` + 双代兼容读（`claude-fallback`→`(host=claude,runner=claude)`；无 `host`→`host=claude`）；`render_table` 加 `host` 列。

- [ ] **Step 1 (回归基线)** 🔁 跑当前 `lens_metric_aggregate.py` 对全部存量归档报告，落基线快照（改造后须逐行一致）。（tasks 5.1）
- [ ] **Step 2 (TDD)** `runner="claude-fallback"` 旧锚读作 `(host=claude,runner=claude)`；无 `host` 读作 `host="claude"`；新旧混合仓正确分组不 parse 失败。跑，FAIL。（tasks 5.2）
- [ ] **Step 3 (实现)** 分组键升维 + 兼容读；`render_table` 加 `host` 列。（tasks 5.3）
- [ ] **Step 4 (回归验证)** 🔁 对 Step 1 基线快照，改造后除新增 `host` 列外**每行计数逐行一致**（机验非目测）。（tasks 5.4）
- [ ] **Step 5** 同步 `retro_report.py` 及测试；跑 `pytest sdflow-retro/tests/` → 全绿。（tasks 5.5）
- [ ] **Step 6: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task5-aggregate "lens_metric_aggregate: 分组键加 host + 双代兼容读(claude-fallback→claude,claude; 无 host→claude)，存量归档逐行一致回归"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-9**：聚合器是**唯一读存量**的组件；双代兼容读；改造前后逐行一致（机验）；view-only 不自动决策。
- **权威**：spec `workflow-retro`「聚合器双代兼容读锚行」Req 全 Scenario；design ADR-2/ADR-3 兼容读表。
- **③ 目标态**：**MUST NOT** rewrite 存量锚；host 分组分开统计（混算污染真跨模型信号）。

---

### Task 6: 宿主判定 helper resolve-models.sh（新组件 + eval 加固 + 安装面）

**Files:**
- Create: `sdflow-init/assets/hack/resolve-models.sh`
- Modify: `setup.sh` · `sdflow-init/assets/config.template.yaml` · `config_lint` 相关
- Test: `sdflow-init/tests/test_resolve_models.py` · `sdflow-init/tests/test_config_lint.py`

**Interfaces:**
- Produces: `eval` 导出 `SDFLOW_HOST` / `SDFLOW_TIER_{STRONG,MID,LIGHT}` / `SDFLOW_VOICE_RUNNER` / `SDFLOW_VOICE_MODEL` 六变量；档位从 `model-tiers.md` 读；覆盖按机队分键 `model-tiers.{claude,codex}.{strong,mid,light}`。

- [ ] **Step 1 (TDD)** `test_resolve_models.py`：`CLAUDECODE=1`→`HOST=claude`；`CODEX_THREAD_ID=<uuid>`→`HOST=codex`；两者皆无→`HOST=unknown`+stderr；**两者同时存在→`unknown`+信号冲突告警**（MUST NOT 静默取其一）。跑，FAIL。（tasks 6.1）
- [ ] **Step 2 (实现)** `resolve-models.sh` 纯 shell（ADR-1）；`eval` 导出六变量；档位从 `model-tiers.md` 读，**MUST NOT 内联模型名**。（tasks 6.2）
- [ ] **Step 3 (TDD+实现)** 覆盖按机队分键：`model-tiers.{claude,codex}.{strong,mid,light}` 按当前机队读；**扁平旧格式**兼容读作 **Claude 机队**覆盖，MUST NOT 罢工；无当前机队段回落缺省。测试：分键读对应段 / 扁平在 claude 宿主生效、在 codex 宿主**不生效**（回落 codex 缺省，不把 opus 塞给 codex）。（tasks 6.2b）
- [ ] **Step 4 (实现)** 同步 `config.template.yaml` 为分键格式 + `test_config_lint.py` 认识分键与扁平两种。（tasks 6.2c）
- [ ] **Step 5 (TDD+实现) eval 注入加固（GC-6）** — 六变量输出用 `printf %q`/`declare -p` + 拒换行/控制字符/非模型 ID 字符；`config_lint` 校验 model-tiers 的**值**为合法模型 ID；resolver 读嵌套 config 覆盖与 `config_lint` **共用同一解析实现 + 畸形输入测试**。测试：覆盖值含 `$()`/反引号/换行/引号的**恶意值回归**（断言不在 eval 时执行）。SHOULD 评估取消 eval。（tasks 6.2d）
- [ ] **Step 6 (实现+TDD)** `setup.sh` 装 `resolve-models.sh` 进 `~/.sdflow/hack/` + 测试守——⚠️ **dogfood 盲区**：测试 MUST 验**安装路径**（`~/.sdflow/hack/resolve-models.sh`）不是仓内路径。（tasks 6.3）
- [ ] **Step 7 (TDD)** 🔒 G6 同源锁：加测试断言 `outside-voice.sh` **不含**对 `resolve-models.sh` 的调用。（tasks 6.4）
- [ ] **Step 8** 跑 `pytest sdflow-init/tests/` → 全绿；`bash setup.sh` 绿。
- [ ] **Step 9: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task6-resolve-models "新增 resolve-models.sh(纯 shell 正信号判宿主+机队档位, eval 加固 printf %q), 覆盖按机队分键, setup 装入验安装路径, G6 同源锁"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-6/GC-7**：纯 shell；正信号判宿主、判不出/冲突 fail-loud；eval 注入加固；MUST NOT 内联模型名；`outside-voice.sh` MUST NOT 自调重判。
- **权威**：spec `host-adaptive-execution`「宿主判定靠正信号」+「模型档位按机队分列」Req 全 Scenario；spec `spec-workflow`「模型档位映射」Req；design ADR-1/ADR-8/ADR-9 + Risks「eval 注入面」。
- **③ 目标态 + dogfood**：**MUST NOT 用"缺失即另一方"推断**（CI 把 Claude 认成 Codex 造新假绿）；测试**MUST 验安装路径**（仓内绿≠消费仓装对，dogfood 盲区）。

---

### Task 7: outside-voice 去硬编码（🔒 安全承重墙，改动最敏感）

**Files:**
- Modify: `sdflow-init/assets/hack/outside-voice.sh`（`:121` `:144` 去 codex 硬编码 · `secret_scan` stderr 脱敏 · preflight stdout 契约 · 版本升 1.2.0）
- Test: `sdflow-init/tests/test_outside_voice.py`

**Interfaces:**
- Consumes: 环境 `$SDFLOW_VOICE_RUNNER` / `$SDFLOW_VOICE_MODEL`（来自 SKILL eval，MUST NOT 自调 resolve-models.sh）。
- Produces: `preflight` 探 `$SDFLOW_VOICE_RUNNER` CLI（stdout `ready|not_installed|missing-deps`，均 exit 0）；`exec` 按 runner 分叉；反向 claude 路径三旗齐全。

- [ ] **Step 1 (TDD)** `preflight` 探的是 `$SDFLOW_VOICE_RUNNER` CLI **不是固定 codex**；`HOST=codex` 时探 `claude`。跑，FAIL。（tasks 7.1）
- [ ] **Step 2 (实现)** `preflight`/`do_exec` 按 runner 分叉；**`secret_scan`/`render_prompt`(FRAME+三条通则)/200KB 截断保持单份共用**，只最终 exec 命令行一处分叉（GC-4）。（tasks 7.2）
- [ ] **Step 3 (TDD) 🔒 安全回归锁（承重墙）** — 断言反向路径走**同一** `secret_scan` 与 `render_prompt`；secret 命中时**两路径都 exit 3 拒发且不 fallback**、`secret_scan` stderr 只出规则类型+行号不出命中原行/匹配值（D8），断言测试密钥不现于 stdout/stderr/临时日志；**断言 claude exec 行三旗齐全**：`--tools "Read,Grep,Glob"` + `--strict-mcp-config` + `--add-dir <repo_root>`，**不含 Write/Bash/WebFetch、不含 `--tools ""`、不含 `--disallowedTools`、不含 `--allowedTools`**（GC-5）。跑，FAIL。（tasks 7.3）
- [ ] **Step 4 (实现)** 反向 runner 调用：`claude -p --model "$SDFLOW_VOICE_MODEL" --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir "$repo_root"`（只读全仓、对称 codex）。**只改跨模型反向路径，不改同族 fallback 子代理。**（tasks 7.4）
- [ ] **Step 5 (实现)** D8 脱敏：`secret_scan` stderr 只输出规则类型+行号，MUST NOT 打印命中整行/匹配值。（tasks 7.7）
- [ ] **Step 6 (实现+TDD)** missing-deps→preflight-error 映射：`preflight` 经 stdout 返回 `ready|not_installed|missing-deps`（均 exit 0）；调用 SKILL/helper 把 `missing-deps` 显式映射为锚 `reason_code="preflight-error"`，**MUST NOT 原样落 `missing-deps`**。测试：`preflight→missing-deps` ⇒ 锚 reason_code=preflight-error 放行。（tasks 7.8）
- [ ] **Step 7 (实现)** `HOST=unknown` ⇒ **不跑 voice** + `reason_code="host-unknown"`（fail-loud）。（tasks 7.5）
- [ ] **Step 8 (实现)** 版本号升 `1.2.0`；头部契约注释同步。（tasks 7.6）
- [ ] **Step 9** 跑 `pytest sdflow-init/tests/test_outside_voice.py` → 全绿。
- [ ] **Step 10: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task7-outside-voice "outside-voice.sh 去 codex 硬编码: preflight 探目标 runner, 反向 claude -p 三旗承重墙(只读全仓对称 codex), secret_scan/render_prompt 单份共用+stderr 脱敏, missing-deps→preflight-error, HOST=unknown 不跑 voice, 版本 1.2.0"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-4/GC-5/GC-8**：三件套单份共用只 exec 一行分叉；反向三旗承重墙（防漂移回写/网工具/零工具/denylist/allowlist）；`missing-deps` 归约 `preflight-error`；`host=unknown` fail-loud。
- **权威**：spec `host-adaptive-execution`「出境安全三件套一视同仁」Req 全 Scenario（"secret 命中两路径都拒发且不泄日志"、"只读约束按 runner 落地反向只读全仓"）；spec `spec-workflow`「跨模型 outside voice」Req；design 安全表 + C4 段 + 失败模式表 F1/F1b/F4/F5/F8。
- **③ 目标态**：反向路径是**新出境端点**（Anthropic）——**MUST NOT** 因"现在只跑 codex 路径"给反向路径松安全绑；三旗齐全是安全承重墙、回归即红。**MUST NOT** 单边给反向 claude 砍工具成零工具（r2 前提"codex 只发 context"实测错）。

---

### Task 8: 规则与 SKILL（引用变量 + 矩阵豁免 + skew 探测编排）

**Files:**
- Modify: `sdflow-init/assets/workflow/model-tiers.md` · `sdflow-spec-review/SKILL.md`(`:251,:253`) · `sdflow-code-review/SKILL.md`(`:172,:243,:245`) · ship/done SKILL 模型选择处

- [ ] **Step 1** `model-tiers.md`：档位表按机队分列（Claude opus/sonnet/haiku；Codex gpt-5.6-sol/terra/luna）+ 覆盖段注记改按机队分键（扁平旧格式兼容读作 Claude 机队，adr/0024）。（tasks 8.1）
- [ ] **Step 2** `sdflow-spec-review/SKILL.md`：锚行文法加 `host=` · outside-voice 调用协议引用 `resolve-models.sh` · lens-metric roster 构造带 `--host`。（tasks 8.2）
- [ ] **Step 3** `sdflow-code-review/SKILL.md`：同 Step 2 + **置信豁免规则引用合法组合矩阵的「跨模型」判定**（C1，MUST NOT 自写 `runner≠host`；`:172` 是旧假绿点）。（tasks 8.3）
- [ ] **Step 4** 各编排 SKILL（ship/done/spec-review/code-review）模型选择改引用 `SDFLOW_TIER_*` 变量，**MUST NOT 内联模型名**。（tasks 8.4）
- [ ] **Step 5** SKILL 写明「Codex 宿主下 `spawn_agent` 指定 model 的 task-specific reason = 本工作流 model-tiers（门禁步禁降档硬约束）」。（tasks 8.5）
- [ ] **Step 6** **C3+D1 统一 skew 探测写进两个评审 SKILL**：落锚/调 emitter 前探本仓 tools 能力——① `lens_metric_emit.py --help` grep `--host`；② grep 本仓 `lens-metric-contract.md` 的 `lens-metric-enums` 块 `runner:` 行含 `none`。**陈旧 ⇒ 在落任何 v2 锚之前硬停该评审步、不产出待 lint 报告 + 响亮提示 `sdflow-init update`（fail-loud）**——MUST NOT 产无锚报告(撞 MANDATORY)、MUST NOT 落 v1 旧锚(假绿)、MUST NOT 静默清零。（tasks 8.6）
- [ ] **Step 7** 跑 `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿；SKILL 改动触发 `gen_workflow_guide` 生成物变化则再生。
- [ ] **Step 8: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task8-rules-skill "model-tiers 按机队分列; 两评审 SKILL 加 host= 锚文法+引用 resolve-models+置信豁免引用矩阵; 编排 SKILL 引用 SDFLOW_TIER_*; skew 探测 fail-loud 硬停编排落点"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-1/GC-6**：置信豁免引用矩阵不自写 `runner≠host`；MUST NOT 内联模型名。skew 探到陈旧**硬停在落锚之前**（不产报告，解 MANDATORY 冲突）。
- **权威**：spec `host-adaptive-execution`「落锚/调 emitter 前探 tools 能力」Req 全 Scenario；spec `spec-workflow`「跨模型 outside voice」+「tension 不静默采纳」Req；design ADR-3 统一 skew + ADR-5 豁免 + scope-check 面 6/7。
- **③ 目标态**：`:172` 旧规则 `runner=codex` 豁免在 Codex 宿主恰是自审——**MUST NOT** 保留任何"按 runner 枚举值硬编码"的豁免/判据。

---

### Task 9: 消费项目铺设 + fan-out 能力探针（Codex 子代理授权）

**Files:**
- Modify: `sdflow-init/assets/snippets/claude-section.md` + AGENTS.md 段 · 两评审 SKILL（探针 + 缩 roster 落点）
- Test: `sdflow-init/tests/`（铺设产物含授权段机验）

- [ ] **Step 1** `claude-section.md` + AGENTS.md 段加 **Codex 子代理授权声明**（多镜 fan-out + model-tiers 构成 codex 要求的显式 task-specific reason）。（tasks 9.1）
- [ ] **Step 2** SKILL 写明「子代理不可用 ⇒ MUST 缩 roster 到实跑的镜 + 报告显著标注单镜降级」；**登记诚实边界**（探针=语义核验非机械门；一致性 lint 只拦"机制死却报多镜"自相矛盾；残余"第 N 镜跑没跑"+"机制活+偷懒自代"无机械守——MUST NOT 声称"头号假绿事前拦截"）。（tasks 9.2）
- [ ] **Step 3 (TDD)** `sdflow-init/tests/` 加守卫：铺设产物含授权段（机验存在性）。（tasks 9.3）
- [ ] **Step 4** SKILL fan-out 前跑**能力探针（语义核验）**：`host=codex`⇒派 trivial 探针子代理（回哨兵=available）；`host=claude`⇒免探恒 available；落会话级锚 `<!-- sdflow:fanout-capability v1 host="…" subagents="…" mirrors="…" -->` **到被 lint 的报告文件内**——`mirrors=` 由 SKILL 在 fan-out 时直接写本轮实际镜清单、**不经 emitter/lens-metric、不读 config.metrics**（C2）。探针 unavailable ⇒ 缩 roster 到单镜、`mirrors=` 也只列实跑镜。**探针值/mirrors 为主 session 自报、非机械核验——如实登记。**（tasks 9.4）
- [ ] **Step 5** 跑 `pytest sdflow-init/tests/` → 全绿。
- [ ] **Step 6: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task9-consumer-setup "claude-section/AGENTS.md 加 Codex 子代理授权声明; SKILL fan-out 前探针落 fanout-capability 锚(mirrors= 直接落不经 metrics); 子代理不可用缩 roster + 诚实边界登记"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-3**：`mirrors=` 由 SKILL 直接落、不经 emitter/lens-metric、不读 config.metrics（一致性 lint 判据源，Task 2 Step 7 读它）。
- **权威**：spec `host-adaptive-execution`「子代理不可用镜数如实降级」Req 全 Scenario；design ADR-4 + adr/0023。
- **③ 目标态 + §0.0**：探针经主 session 自报、无可信捕获路径 ⇒ **语义核验非机械门**；**MUST NOT** 为"available 后逐镜真独立"硬造假机械测试冒充门；也 MUST NOT 因它无测试漏掉 Task 2 的一致性 lint 测试。

---

### Task 10: 文档同步 + Claude 宿主 e2e 回归 + 面治收口

**Files:**
- Modify: `docs/workflow-map.md`(`:141,:150`) · `docs/workflow-map.html`(`:555,:563`)

- [ ] **Step 1** 同步 `docs/workflow-map.md` + `docs/workflow-map.html` 字段表与枚举（加 `host`、runner 加 `none`、删 `claude-fallback`）。（tasks 11.1）
- [ ] **Step 2 (Claude 宿主 e2e 回归)** Claude 宿主下跑一次评审/相关流程，确认现有行为不变（`host="claude" runner="codex"`），存量归档聚合逐行一致（Task 5 基线）。（tasks 10.2）
- [ ] **Step 3** 全量 `pytest` 绿 + `bash setup.sh` 两道门（`sync_principles --check` / `gen_workflow_guide --check`）绿。（tasks 11.2）
- [ ] **Step 4** 🔒 逐面核对 design **scope-check 表面 1–10 全部改完**（GC-11 面治：留一面=契约漂移）+ 面 11 pre-existing debris 已核（`openspec/workflow/lens-metric-contract.md` 规则副本 / `openspec/workflow/tools/outside_voice_guard.py` 副本——**核是否 pin 遮蔽，是则本 change 不改、另记 buglist 清 debris**，勿在本 change 内动 pre-existing 副本）。（tasks 11.3）
- [ ] **Step 5: Commit**
```bash
bash ~/.sdflow/hack/checkpoint-commit.sh add-codex-host-support:task10-docs-e2e-closeout "workflow-map.{md,html} 字段表同步 host/runner=none; Claude 宿主 e2e 行为不变+存量聚合逐行一致; 全量 pytest+setup 两道门绿; scope-check 面 1-10 收口 + 面 11 debris 核查登记"
```

**领域约束 + 三条通则（本任务必读）**
- **GC-9/GC-11**：Claude 宿主 e2e 行为不变 + 存量聚合逐行一致；面 1–10 一次扫全，留一面=契约漂移；面 11 只核查登记、**不在本 scope 内改**。
- **权威**：design scope-check 表（TG-25）全 11 面；proposal Success Metric 4/5。
- **① 自查**：用 `grep -rn "claude-fallback\|runner=\|host="` 全仓自查残留落点，逐面对照 scope-check 表核无遗漏。
- **③ 目标态**：Codex 宿主 e2e（`host=codex`）**不在本任务**——见下方"Deferred to Codex host"；**MUST NOT** 在 Claude 宿主 mock 一个 `host=codex` 跑过就当 Codex e2e 已做（那测的不是目标态）。

---

## 🚨 Deferred to Codex host（用户 out-of-band，非本 pipeline 自动执行 · 非 gate 计数任务）

> 以下两项**必须在真实 Codex 宿主**执行，Claude 宿主的 implementer 子代理**结构性做不到**——**MUST NOT 由子代理伪造完成**（GC-10）。用户 option B 已授权先做 Task 1–10 + 冷审，这两项 deferred 至用户后续 Codex 测试；测过后把实测真值写回 proposal 假设表 + design Risks（在 done/archive 阶段做，实现期改四件套会触设计门失鲜）。

- [ ] **D-1 efficacy 前置门 A1（原 tasks 0.1）** — Codex 交互 / headless / `codex exec` / spawned subagent 各形态各跑一次，确认 `CODEX_THREAD_ID` 存在。任一（尤其 headless/`codex exec`）缺失 ⇒ 停：design 补该形态替代正信号，或 scope 缩到"仅交互 Codex"。
- [ ] **D-2 efficacy 前置门 A3（原 tasks 0.2）** — 真实 Codex 宿主 session 内冒烟 `claude -p --model opus --output-format text --tools "Read,Grep,Glob" --strict-mcp-config --add-dir <repo_root>`——核验点 = **能否成功发出网络请求并拿回 findings**。Codex 封网 ⇒ 反向 voice 恒失效，design 须承认 scope 边界。
- [ ] **D-3 Codex 宿主端到端（原 tasks 10.1）** — Codex 宿主下跑一次真实评审，核对 outside-voice 锚为 `host="codex" runner="claude" reason_code="ok"`、fanout-capability 锚在场、`anchor_lint` 绿（含自审红线 + 一致性 lint always-on）。
- [ ] **D-4 结论写回（原 tasks 0.3，done/archive 阶段）** — A1/A3 实测真值写回 proposal 假设表 + design Risks；任一在主力形态失效 ⇒ 缩 scope 或补 headless 替代信号，MUST NOT 直接收尾 BREAKING 契约。

---

## Self-Review 记录

- **Spec coverage**：六 spec 的每个 Requirement 均有对应 Task —— `host-adaptive-execution`(T2/T6/T7/T9)、`workflow-metrics`(T1/T2)、`lens-metric-emit`(T3)、`outside-voice-reuse-guard`(T4)、`spec-workflow`(T6/T7/T8)、`workflow-retro`(T5)。efficacy 前置门（原组 0）+ Codex e2e（原 10.1）= Codex 真机步，移入"Deferred to Codex host"（用户 out-of-band，非 gate 计数）。T10 = Claude 侧 e2e + 文档 + 面治收口。
- **Type consistency**：行键 `(lens,host,runner,site)` 与唯一键 `(layer,lens,host,runner,site,轮)` 全 Task 一致；reason_code 8 值域 + runner `{claude,codex,none,unknown}` 全 Task 一致；矩阵三态分类命名 illegal/cross-model/same-family/no-exec 在 T2/T4 golden 一致。
- **无 Placeholder**：每 Task 的测试断言取自 tasks.md 逐条 + spec Scenario；exhaustive 实现细节以 in-repo design/spec 为权威（本仓 SDD 惯例：implementer 读 design/spec 而非 plan 复制 2000 行）。
- **Gate 结构**：numbered Task 1–10 全 Claude-side 可 checkpoint ⇒ gate 实现完成后 advance 到 RUN_CODE_REVIEW；Codex 真机步非 numbered、不阻塞 gate。冷审后 STOP（不自动 done/merge），等用户 Codex 测。
