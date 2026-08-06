---
ship-gate:
  code_review: pass
  reviewed_sha: 4ac1e7b084d000045451c4877808c8f52e9a97d2
---

## code-review 报告 — absorb-gstack-review

### 命中范围

- **栈**：markdown workflow bundle + Python lint/emit 工具 + SKILL 指令文本（非 TG-01/02/03 业务栈）。
- **TG 命中（模型判定）**：TG-06 · TG-08 · TG-10 · TG-14 · TG-18 · TG-19 · TG-20 · TG-23。
- **HR-TG ∩**：`TG-06, TG-08`（脚本重算）⇒ 单开 `site="hr-tg"` 领域专属 cross-model。
  <!-- sdflow:hr-tg v1 hit="TG-06,TG-08" declared="TG-06,TG-08,TG-10,TG-14,TG-18,TG-19,TG-20,TG-23" evidence="lens-metric-fold 机读块是 emitter/anchor_lint/retro/两评审 SKILL 共享的契约单一源，本次替换其 raw 名（TG-06）；同 change 移除代码审侧对第三方 gstack skill 的运行时依赖（TG-08）" -->
- **TG-27 判定：不命中**——本 change 改的 `anchor_lint.py` / `lens_metric_emit.py` 正是「评审工作流自身
  读取/校验同会话内受信任 agent 自报的控制面锚」，命中 TG-27 行的排除句。**该排除句正是本 change 新加、
  设计意图就是防这类自指假阳，本轮 dogfood 首次实测生效。**
- **清单**：`code-review-base.md` CR-01~09 + 本 change 新增 CR-10/CR-11。
  **backend domain 判不适用**（TG-06/TG-08 的领域列指向 backend 退避/错误段，但本 change 无后端服务代码面）
  ——如实记降级，非「看着过」。
- **Step1 自持 scope 审计**：scope-drift 零 creep（Non-Goals 六条逐条实测未被动）；完成度五态 23 条中
  22 DONE / 1 UNVERIFIABLE（6.4 dogfood，见下）。

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="broad,domain,adversarial,history" -->

`host=claude` ⇒ 免探针，恒 available。无降级。

### Step1 锚

<!-- sdflow:step1-broad-review v1 mode="subagent" -->

### 本轮的 dogfood 结论（tasks 6.4 的实跑观测，由本轮承担）

Task 6 收尾票只做了开窗前置并显式声明「实跑观测不由本票执行」。**该观测由本轮 code-review 兑现**，
三项待核锚逐条落定：

| 待核项 | 结果 | 证据 |
|---|---|---|
| `mode="subagent"` 锚 | ✅ | 见上 Step1 锚，本轮 Step1 由 fresh 中档子代理独立完成 |
| `scope-audit` 折叠出的 `lens="broad"` 行 | ✅ | 见下度量锚段 broad 行；emitter 以 `hits[].raw="scope-audit"` 输入、exit 0 归约为 `lens="broad"` |
| `anchor_lint` 通过 | ✅ | 见下「锚行自检」 |

**skew 探测四信号首次实跑**：①②③④ 全通过（③④ 为本 change 新引入）。
过程中发现一处**探测写法的坑**（非本 change 缺陷，已记 todo）：信号②若用 `sed -n '/```lens-metric-enums/,/```/p'`
（无行首锚定）会撞上散文里对该 fence 名的提及、截错范围而假阴 → 误硬停。改用 `awk '/^```lens-metric-enums/'`
行首锚定即正确。方向 fail-safe（假阴致停、非放行），但会造成误停。

### Findings（置信 ≥80 / 跨模型豁免）

| 严重度 | finding | 来源 | 处置 |
|---|---|---|---|
| Important | **skew 探测排在能力探针之后，而它自称「MUST 在任何 fan-out 之前跑」**——`host=codex` 时探针要派 trivial 子代理，那已经是一次 fan-out ⇒ 承诺自我违反，旧 bundle 下会白跑一次子代理才硬停 | code-voice（跨模型） | **已修** `[impl-review-fix]`：两项对调（skew=第5项、探针=第6项）+ 段内显式钉死顺序理由 |
| Important | **EXEMPT 作废的触发信号没有产生它的能力**——`trivial_shape.py:19` 明写「伪装成注释的逻辑改由本判器之外的 Step1 scope-drift 守卫（判器只看 diff 形状）」，把内容级检测**下放**给 Step1；但 Step1 轴一（文件级 scope 比对）与轴二（task 级完成度）**都不读 hunk 内容** ⇒「揭出隐藏逻辑」永不产生，EXEMPT 一经机判命中即不可撤销、Step2 多镜被静默跳过 | 对抗镜 B | **已修** `[impl-review-fix]`：给 Step1 补**条件轴三**（仅 EXEMPT 时 MUST 跑）——逐行读白名单 hunk 内容，四类具体检测目标 + 发现即判 EXEMPT 作废 |
| Minor | **引文纪律诚实边界只声明了一半**——原文只说「引文真实性无核验」，但「这条是否**真属**非局部类」这个分类判断同样自报同样无核验；局部 bug 自称「absence 类」即可绕开单行引文硬要求 | 对抗镜 B | **已修** `[impl-review-fix]`：边界补成两维度，并显式声明 **MUST NOT 靠再加一层校验来堵**（校验方同样是 LLM，只是把同一个自报判断多套一层） |
| Minor | **三处活文档仍写旧协议**——`docs/sdflow-fable5/02-module-reference.md` 第 5 行**自述「本文是活文档（非冻结快照）」**却在 `:129`/`:286` 仍写「gstack/review 原生并入」；`docs/workflow-map.md:140`（字段×判据速查）把 `step1-broad-review.mode` 限为 `native\|simulated`，读者会把合法新锚判成异常；`docs/workflow-skills/gstack-document-generate.md:6` 仍以「`/review` 是 Step1」作类比 | code-voice + hr-tg（跨模型） | **已修** `[impl-review-fix]`：三处同步新协议。**根因**：Task 5 的残留判定表按**目录名**把 `docs/sdflow-fable5/` 整体归为「历史文档合法保留」，没读文档自述定位 |

### 已裁掉（反静默压制，可审计）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | **hr-tg voice 判 high**：本仓 `openspec/workflow/` pin 的 contract 仍是 `gstack-adv`，新 skew 探测会硬停本仓评审 | **前提被证伪**：`resolve-workflow.sh` 步1 的 pin 判据是 `workflow.md` / `spec-checklists/` / `code-checklists/` **any-of**，本仓三者**实测全不存在** ⇒ `--explain` 实判 `source=global-canonical`，本仓根本不 pin 那份副本。至于**消费仓**在 `sdflow-init update` 前命中硬停——那正是 skew 探测的**设计意图**（fail-loud + 带修法指引），不是 bug。领域镜与对抗镜 A 各自独立复核同一结论 |
| X2 | 对抗镜 B（置信 55）：五态判据未区分「未做」与「天然不产生 diff 痕迹的验证动作」（如 task 3.4 的「跑一次脚本验证 parse 正常」） | **<80 数值滤除**。另有实证佐证：本轮 Step1 子代理实际把 6.4 判成了 `UNVERIFIABLE` 而非 `NOT DONE`，未踩该坑 |
| X3 | 领域镜 / 对抗镜 A 各自提出：仓根 `openspec/workflow/lens-metric-contract.md` 孤儿副本含旧 `gstack-adv` | 两镜均自行核实为**已知已 defer 项**（T269），且 `git merge-base --is-ancestor` 确认其上次改动早于 `DIFF_BASE`，非本 change 引入 |
| X4 | 对抗镜 A 六个攻击面 A1–A6 全部 refuted | 均附实跑证据（构造锚行喂 `anchor_lint.py`、256 测试全绿），非纸面推演 |
| X5 | 历史镜：`adr/0023:26` 的 `lens ∈ {domain, adversarial, grounding}` 未含 history | 非本 change 引入（`61ec9dd` 加 history 晚于该 ADR 最后更新 `c9b8325`），既有陈旧信息 |

### 修复 / defer 台账

- **自动修 4 项** `[impl-review-fix]`：commit `4ac1e7b`（4 文件、+24/-10，仅源码）。
- **自动选推荐 0 项**（无 ≥2 方案分歧，无需 `T10-choice` 复核）。
- **defer 0 项进 buglist**；**1 项进 todolist**：skew 探测信号②的 grep 写法需行首锚定（本仓「讨论锚自身的
  文档含锚字面」自指坑的同族，与既有 `gate 子串检测 dogfood 自指坑` 同因）。
- **复审一轮已跑**（硬上限 1，范围限定 `4ac1e7b` 本身）：R1 对症性 / R2 新引入问题（含重排序悬空交叉引用
  专项 grep）/ R3 托管区块字节级（91 passed）/ R4 scope-drift ——**零 finding，PASS**。未触及硬上限。

### 度量锚（lens-metric，`metrics.enabled: true`）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="2" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="1" 采纳="0" 裁掉="1" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="2" 采纳="2" 裁掉="0" defer="0" 独立="2" sev="致0/高0/中2/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低1" -->

**本轮镜价值观察（只呈现，不决策——复评归 `/sdflow-retro` 聚合 + 人拍板）**：4 条采纳里 **3 条独家出自
跨模型 voice**，同族 5 面镜合计独立贡献 1 条（对抗镜 B 的 EXEMPT 缺口，也是本轮最硬的一条）；
领域镜与历史镜本轮零独立产出。与本仓既有实证（跨模型 voice 产出碾压同族温镜）方向一致。

### outside-voice 锚

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="2" truncated="false" -->

**范围偏离（显式记录）**：规则要求 `code-voice` 喂 `DIFF_BASE..HEAD` **全量** diff。全量为 **548201 字节**，
超出 helper 头尾各 100KB 保留窗口 ⇒ 中段核心实现会被整段截断（本仓实证教训）。故收敛为**生产代码面**
（排除 `openspec/changes/**` 的四件套与 impl-reports，保留全部 SKILL / bundle / tools / tests / docs 改动，
102685 字节）。两站点 `.rc` sidecar 均为 `0`，`truncated=false`。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）。
- ☑ defer 残差已入 todolist（1 项，hand-off 会引用）；buglist 无新增。
