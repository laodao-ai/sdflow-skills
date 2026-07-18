---
name: sdflow-code-review
description: >
  阶段三「代码评审编排器」——**每次全跑·独立冷视角·强制主审**（非"高风险才跑的边际抽查"；实测能抓循环内被
  controller 说服放过的真问题）。主 session（强档）协调：Step1 并入 gstack/review（scope-drift + 计划
  完成度审计），Step2 fan-out 多个 fresh 子代理并行审本项目 code-checklists（领域镜 + 对抗镜 + 历史镜），
  Step3 置信过滤（<80 滤除）+ 对抗裁决，Step4 **能修的自动修**（标 [impl-review-fix]）、≥2 方案按 T10 三级协议自动选推荐（按三镜 + 主次记理由）、修不了/拿不准的 defer 进 buglist/todolist，Step5 汇总**一份** code-review-report.md。
  **阶段三无人类门**——不 AskUserQuestion，自动修/自动裁/defer，残差交 hand-off 异步再入口。**不依赖 /clear**
  ——子代理 fresh context 即独立性。代码即 ground truth（无接地镜，换历史镜 + 置信过滤）。出报告标
  [impl-review-fix]。也可说"sdflow 代码审"。Trigger with /sdflow-code-review。
---

# sdflow-code-review — 阶段三代码评审编排器（每次全跑·独立冷·强制主审）

<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/hack/skill-principles.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
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

把 workflow 规则集的 `code-checklists/`（经 resolve-workflow.sh 解析，通用 base CR-01~09 + 领域 delta CR-*）操作化为一次
**连续跑的编排代码评审**：Step1 gstack/review（scope-drift + 完成度）→ Step2 并行多镜（本项目清单）→
Step3 置信过滤 + 对抗裁决 → Step4 自动修/defer → Step5 **一份** `code-review-report.md`。

> **定位升级（P3c，须知情）**：本 skill **不是**"高风险才跑的冷独立抽查、边际残差"——那是旧
> `quality-layering.md §五` 的结论，**已被否决**。sdflow-code-review 是**每次全跑的独立强制主审**：实测能抓出
> 生成循环内被 controller 说服放过的真问题。它把旧 `gstack/review`（scope-drift）+ 自制多镜清单审
> 合并成一个编排器，产出一份 `code-review-report.md`（取代旧 staff-review-report.md + impl-review-report.md 分裂）。

## 两条连续性铁律（阶段三自动流的前提）

- **不依赖 `/clear`（G1）**：评审 fan-out 到 fresh-context 子代理，独立性由"子代理冷上下文"给。主 session
  携带生成历史进裁决，接受一丝合成层偏置——但**反静默压制**焊死其边界（见 Step3）。
- **阶段三无人类门（P3e）**：过设计门后一口气跑到 merge，本 skill **不 AskUserQuestion**。**能修的当场修**、
  **≥2 方案按 T10 三级协议自动选推荐（按三镜 + 主次记理由）**、**genuinely 拿不准的 defer**（进 buglist/todolist + hand-off 异步再入口）。
  与阶段二不同——阶段二决策高杠杆（错设计→白做）值一个门；阶段三已实现、残差可追踪可另修。

## 与注入点 B 的关系（2.4，**别把本 skill 优化掉**）

阶段三"领域审两遍"**不是重复**，两遍机制/职责不同——这是最反直觉、最该防后人"优化掉"的一条：

```
  第一遍: subagent-dev 终审 + 注入点B        第二遍: 本 skill（事后 sdflow-code-review）
  ────────────────────────────────────────────────────────────────
  时机   生成循环内                          全部实现完成后
  机制   命中即派 fix 子代理修 + re-review 闭环  出报告 → 编排器修（无 re-review 紧闭环）
  独立性 reviewer 冷,controller 热(在循环内)   完全冷独立(脱 controller)
  职责   即时修复确认(shift-left,便宜早修)    独立兜底网(实测能抓真问题)
```

- **注入点B 不可替代 = subagent-dev 的即时修复确认**（发现即派 fix 子代理修 + re-review 到 Approved，循环内闭环）。
- **本 skill 不可替代 = 独立冷视角 + 实测捕获**（抓循环内被 controller 说服放过的真问题）。撤任一个都留洞。

---

## 第零步：确认对象 + diff base + 读规则

1. 未指定变更则 `openspec list` 让用户确认。记 `{change_dir}` = `openspec/changes/{name}/`。
2. 确认代码已实现且在 feature 分支（`git branch --show-current`）。算 diff base：
   `git fetch origin <base> --quiet && DIFF_BASE=$(git merge-base origin/<base> HEAD)`。
3. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用代码审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用代码审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/code-checklists/README.md`（架构/选用）、`$RULES_ROOT/code-checklists/code-review-base.md`（CR-01~09）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。
4. **宿主/档位解析（每轮恰好一次，ADR-9 同源约束）**〔host-adaptive-execution · 模型档位按机队分列〕：**MUST 按下述带防护次序解析**（V1：裸 `eval "$(…)"` 会被脚本缺失静默吞——`sdflow-init update` 不装 hack 脚本、须 setup.sh，skew 窗口高发；`eval ""` 返回 0 且同 shell 上一轮的 `SDFLOW_*` 旧值原样留存 ⇒ 拿旧宿主假绿）：**(a)** 先 `unset SDFLOW_HOST SDFLOW_TIER_STRONG SDFLOW_TIER_MID SDFLOW_TIER_LIGHT SDFLOW_VOICE_RUNNER SDFLOW_VOICE_MODEL` 清脏（eval 失败也只得空值、不复用上轮脏值）；**(b)** `[ -x ~/.sdflow/hack/resolve-models.sh ]` 预检（与本步第 3 项 resolve-workflow 预检同 idiom），不成立 → **fail-loud 硬停本轮评审**「resolve-models.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」，MUST NOT 继续；**(c)** 捕获退出码再 eval：`MODELS_ENV="$(~/.sdflow/hack/resolve-models.sh --root "$(git rev-parse --show-toplevel)")"`，退出码非 0 → fail-loud 硬停（同文案 + 原样转发 stderr），否则 `eval "$MODELS_ENV"`；**(d)** eval 后校验：`$SDFLOW_HOST` MUST 精确 ∈ {claude,codex,unknown} 且非空，host≠unknown 时三 `$SDFLOW_TIER_*` MUST 非空——任一不满足（尤其 `$SDFLOW_HOST` **取到空值 = resolver 根本没跑成**）→ **在任何 fan-out / 调 emitter / 落 v2 锚之前 fail-loud 硬停**（同本步第 5 项 skew 探测纪律），**空值 MUST NOT 回落当 `host=unknown` 处置**（unknown = 跑成但判不出宿主、空 = 工具没装没跑成，把后者吸进 unknown 宽容路径又是一层假绿）。**诚实边界**：unset/eval/校验 MUST 内联本 SKILL（eval 要 export 进主 session shell，包子脚本无法把变量 export 回来）∴ 是对主 session 的**指令、非机械门**（与第 3 项预检、第二步能力探针同类），MUST NOT 声称机械门。校验通过后取本轮 `$SDFLOW_HOST`（`claude|codex|unknown`）、`$SDFLOW_TIER_STRONG`/`$SDFLOW_TIER_MID`/`$SDFLOW_TIER_LIGHT`（本机队已解析好的具体模型 id，供下方「模型选择」节引用）、`$SDFLOW_VOICE_RUNNER`/`$SDFLOW_VOICE_MODEL`（跨模型 voice 目标，供下方「outside-voice helper 调用协议」引用）。**本轮全程只 eval 这一次**——后续锚行的 `host=`/`runner=` 与 `outside-voice.sh` 一律读这次导出的环境变量，MUST NOT 各自重判宿主（ADR-1/ADR-9，防信号跨调用点漂移）。
5. **skew 探测（fail-loud，MUST 在本轮任何 fan-out / 调 emitter / 落 v2 锚之前跑）**〔host-adaptive-execution · 落锚/调 emitter 前探 tools 能力〕：bundle 内 SKILL（symlink 即时生效）与 tools（copy，须 `sdflow-init update` 刷新）更新不原子，存在「新 SKILL × 旧 tools」窗口——探两条具体信号：① `python3 "$RULES_ROOT/tools/lens_metric_emit.py" --help` 的输出 grep 到 `--host`；② `$RULES_ROOT/lens-metric-contract.md` 的 `lens-metric-enums` 机读块内 `runner:` 行 grep 到 `none`。**任一探不到（陈旧）** ⇒ **在落任何 v2 锚 / fan-out / 调 emitter 之前，硬停本次评审（不产出待 lint 的报告）**，终端/hand-off 响亮提示「tools 陈旧，请先跑 `sdflow-init update` 再重跑评审」——fail-loud、actionable，MUST NOT 产出无锚报告（撞 `anchor_lint` 的 outside-voice 锚 MANDATORY 硬拦）、MUST NOT 落 v1 旧锚（假绿）、MUST NOT 静默清零本段。两条均探到 ⇒ 正常进入第一步。

## 第一步：gstack/review 子步（并入·原生执行，scope-drift + 完成度）

- **原生执行〔T25·R5〕**：主 session 经 Skill 机制原生执行 gstack `/review` 全量流程（指令直接进主 session，MUST NOT 派子代理读其 SKILL.md 模拟；不因 prompt 措辞裁剪原生步骤），**必须含 scope-drift（顺手多改）与计划完成度缺口（建的=计划的?）**，结论纳入 Step3 合并池；报告 Step1 段写 v1 锚行 `<!-- sdflow:step1-broad-review v1 mode="native" -->`。
- **显式降级**：gstack/review 不可用 → 子代理模拟 + 显式日志（"scope/完成度审计层缺失 → 模拟降级"）+ 锚行 `mode="simulated"`，MUST NOT 伪装原生，**不静默跳过**。

## 第二步：规划镜头 + 并行 fan-out 子代理（本项目清单）

**Step2 前置·无逻辑面白名单免除判定（机判·post-diff）**：fan-out 前跑
`python3 $RULES_ROOT/tools/trivial_shape.py --base "$DIFF_BASE" --root "$(git rev-parse --show-toplevel)"`——
退出码 **0=EXEMPT**（diff 仅无逻辑面白名单形状：代码内注释/约定文档路径 README·CHANGELOG·docs·VERSION/仅新增 tests/；
多镜结构上零产出）→ **免本步 fan-out**，报告 Step2 段注明「无逻辑面豁免（trivial_shape EXEMPT）」并附判器 JSON 的 `reason`；
Step1（scope-drift）已恒跑守卫伪装逻辑。**1=NOT_EXEMPT**（有逻辑面 / 命中行为面路径 bundle·SKILL.md·workflow.md·
ship_gate.py，即便 diff 是 markdown）/ **2=ERROR** → **照常 fan-out**（保守）。**默认开、仅机判无逻辑面才关，非「高风险才跑」**；
判器缺失/不可执行 → 视同 NOT_EXEMPT 照跑（不静默免）。

**规划镜头（主 session）**：按 `{change_dir}` 命中的 TG/栈定**领域镜**；按风险定**对抗镜**（普通 2 / 高风险 3）；
固定 1 个**历史镜**。linter/typechecker/编译器能抓的（导入/类型/格式/纯风格）不进任何镜——CI 会跑。

- **HR-TG 判定〔C4·R3〕〔mlh-p4 T81〕**：**你判**命中 TG 集（命中哪些 TG 无确定性信号，判断归模型），交脚本做确定性交集 + 出锚——`python3 $RULES_ROOT/tools/hr_tg_intersect.py --tg-set "TG-xx,TG-yy" --trigger-catalog $RULES_ROOT/trigger-catalog.md`（空集传 `--tg-set ""`；HR-TG 子集由脚本从 trigger-catalog `## 七、HR-TG` 段 `> 成员：` 行单一源 parse，**不在此复制清单**）。脚本 stdout 两行：结果行 `hit:[…]｜依据模型判定:[…]` 或 `none｜依据模型判定:[…]`（你给的命中集显式可见供复审）+ 规范锚行 `<!-- sdflow:hr-tg v1 hit="…|none" declared="…" -->`（`declared=` 承你判定的命中集，adr/0018 输入可见）；坏输入/单一源损坏 → 退出码非 0 + stderr `[hr_tg_intersect] FAIL`，遵其判定 MUST NOT 静默吞。**hit 非空**（∩ HR-TG ≠ ∅）→ 单开一次领域专属 cross-model（按「helper 调用协议」，site="hr-tg"，context=命中判据触发点+相关 diff hunk，「找领域镜漏的」）——**context 就绪即派；async 分支下 dispatch 调用派出即返回，MUST 立刻继续本步余下工作（能力探针、fan-out 各镜），结果在 Step3 barrier 处 collect**。判定无论正反写报告，报告锚行取脚本 emit 的 `hit=`/`declared=`，再由你手填 `evidence="<判据触发点一句>"`（命中必填 evidence，30 秒可人工复核）。

**能力探针（fan-out 前 MUST 先跑，语义核验非机械门，ADR-4/adr/0023）**〔host-adaptive-execution · 子代理不可用时镜数如实降级〕：

- `$SDFLOW_HOST="claude"` → 免探，恒 `subagents="available"`。
- `$SDFLOW_HOST="unknown"` → 不 fan-out（本轮不会走到本段——第零步已判定）。
- `$SDFLOW_HOST="codex"` → **MUST** 先派一个 trivial 探针子代理（prompt 只要求回复固定哨兵，如 `PROBE_OK`，
  不做任何实质工作）；派不出/机制报错 → `subagents="unavailable"`；派出且收到哨兵 → `subagents="available"`。
  **Codex 子代理授权见 AGENTS.md「Codex 子代理授权」段**（多镜 fan-out + model-tiers 构成显式 task-specific reason）。
- **诚实边界（MUST 显著登记，§0.0）**：探针结果由**主 session 自己**观察并落锚——「是否真派出了一次子代理、
  是否真收到回复」无可信脚本捕获路径，`anchor_lint` 的一致性 lint 只核**锚行文法自洽**（`unavailable`
  却报多镜的自相矛盾），**核不了它是否对应一次真 spawn**。MUST NOT 声称这是机械门。
- **`subagents="unavailable"` 处置（MUST）**：本轮**缩 roster 到主 session 实际独立完成的镜**（不再假装
  派了子代理）；报告本段**显著标注**「⚠️ 单镜降级（子代理不可用，host=codex）」；第五步 lens-metric roster
  （若 `metrics.enabled`）与下方 `mirrors=` **只含实际独立完成的镜**，MUST NOT 为未独立跑过的镜落锚
  （承 spec「子代理不可用则缩 roster」Scenario）。
- **落锚（每轮恰好一条，落进本报告文件供 `anchor_lint` 读，`host=codex` 报告该锚必填）**：

  `<!-- sdflow:fanout-capability v1 host="$SDFLOW_HOST" subagents="available|unavailable" mirrors="domain,adversarial,grounding|—" -->`

  `mirrors=` MUST 由本 skill 在 fan-out 决策落定时**直接写本轮实际派出/独立完成的镜清单**（去重、逗号
  分隔，token ∈ `{domain,adversarial,grounding}`——`anchor_lint._FANOUT_MIRRORS` 是**跨层共用的固定
  三 token 词表**，不按层各自命名第三镜；本 skill 第三镜（历史镜）落 `mirrors=` 时借用既有 token
  `grounding` 记该镜跑过（仅表示"第三个 fan-out 镜跑了"，非声称"这是接地镜"——镜的精确身份仍由
  lens-metric 的 `lens="history"` 各自记录，二者不是同一件事、不互相替代），`—`=未 fan-out）——
  **不经 emitter/lens-metric、不读 config.metrics**（GC-3，判据 always-on 于 metrics 开关，不受门控）。
- **残余诚实边界（§0.0，无信号⇒语义层）**：一致性 lint 只拦「机制死却报多镜」的**自相矛盾**；「机制活但
  主 session 偷懒自代多镜」**无机械守，残余语义层**（事后按 host 分组独立率异常可复评）——
  **MUST NOT 声称"头号假绿（多镜静默退化）已被事前机械拦截"**。

**fan-out（一条消息内全部派出，各子代理 fresh context、无用户交互、返回结构化 findings）**：

| 镜 | 数量 | 干什么 | 建议档位 |
|----|------|--------|-----------|
| **领域镜** | 每命中领域 1 个 | 读 `DIFF_BASE..HEAD` diff + 相关真实代码，逐条过 `code-review-base.md` CR-01~09 + `domains/<栈>` CR-* 项，列违反/存疑项（带 `file:line`） | 中档（判断） |
| **对抗镜** | 2-3 | 各从一个**不同角度**「证明这段代码运行期会爆」：并发竞态 / 资源泄漏 / 错误路径未覆盖。默认 refuted=true，找到爆点才记 | 中档（对抗推理） |
| **历史镜** | 1 | `git blame` 改动行 + 读历史 PR 评论：这块以前修过/revert 过吗？本次是否重蹈或忽略旧 review 意见 | 弱档（机械） |

> 每个子代理 prompt 必须自带：`{change_dir}` + diff 范围、负责的清单/角度、"返回结构化 findings（每条带：
> 问题 / CR 编号 / 证据 `file:line` / 严重度 / 建议），**不要 AskUserQuestion**"。
>
> **🔴 每个子代理 prompt MUST 原文携带本 SKILL.md 顶部的「三条通则」区块**（`sdflow:principles` 从 start 到 end，**整段复制，不转述、不摘要**）——见传播纪律。
> **代码审是通则 ③ 的最高发区**：子代理眼前只有「已经写出来的代码」，漏带这三条，它**必然**把「它现在能跑 / 现在没出过事」当成「它是对的、不用改」。
> **判据是「目标态下会不会出问题」，不是「现在出没出过问题」。**

**第二步半：code outside voice（跨模型，always〔C3·R1〕）**：按「helper 调用协议」（site="code-voice"，context = `git diff $DIFF_BASE..HEAD` 全量）跑一次整体找漏第二意见——不受清单约束、不占镜位。**context 就绪即派；async 分支下 dispatch 调用派出即返回，MUST 立刻继续本步余下工作（进第三步汇总），结果在 Step3 barrier 处 collect**。findings 进 Step3 合并池；v1 锚行按位点写入报告。**复评条款已泛化〔workflow-metrics-loop ADR-5，见第五步「反馈回路」〕**：原「累计 10 次后按采纳率复评降采样为 HR-only」是本条 outside-voice 专属规则，现升级为 per-(层,镜) 通用条款（本镜只是其中一个评估单元，不再单独定义判据）。

## 第三步：置信过滤 + 综合 + 对抗裁决（主 session · 强档）

0. 🔴 **进汇总去重前 MUST 先完成 outside-voice collect barrier**（见「outside-voice helper 调用协议」节 ⑥⑧）：按 ⑧ 的站点↔任务标识表**逐站点**取，每个**实际 dispatch 过的**站点其结果 MUST 已在手、或已按 ⑦ 降级完毕（仍 RUNNING 的站点 MUST 让出轮次等通知，MUST NOT 早退落 `timeout`），方可进下面的汇总去重。
1. 汇总 gstack/review（Step1）+ 各镜 findings，**去重**（同一问题多镜命中合并）；去重时记录每条 finding 的**命中镜集合**，
   折叠到 canonical lens 后供 Step5 落锚时导出各镜 `独立`（唯一报过 ∧ 被采纳 +1；归属/折叠规则见规则根 `lens-metric-contract.md`，唯一权威源）。
2. **置信过滤**（借官方 code-review rubric，可下放弱档子代理逐条打分）：每条打 0–100，**滤掉 <80**。
   明确滤除：CI 能抓的 / 纯 nitpick / 未改动行的既有问题 / 仅主观风格 / 已被注释显式抑制的。
   **outside-voice 豁免〔R4·D8，ADR-5/C1〕**：豁免判据 = 该条 finding 所属 outside-voice 锚被 `anchor_lint` **合法组合矩阵**判定为「跨模型」（`host,runner 均∈{claude,codex}∧runner≠host∧reason_code="ok"`）——**MUST NOT 自写裸 `runner≠host`**（被 `runner="none"` 击穿）、**MUST NOT 按 runner 取值硬编码**（旧规则 `runner=codex` 在 Codex 宿主下恰是自审，是本条要杀的假绿点）。矩阵判「跨模型」为真的 findings 跳过 <80 数值滤直通对抗裁决（跨模型自评不可比、异见不被同族标尺误杀）；**其余一律照过同族置信滤**——含同族 fallback（`runner==host`，`claude-fallback` 枚举值已废弃）与无执行（`runner="none"`，findings 恒 0，豁免无意义）。
3. **对抗裁决**：对每条存活 finding 判"是否真的运行期出问题"——对抗镜反驳 ≥ 多数成立则采信。
4. **反静默压制（escalate-not-drop，Q3 铁律）**：裁决对 reviewer finding **只能降级/批注、不得静默丢弃**；
   判"不成立"的连理由落入报告「已裁掉」区。<80 滤除项也**一行带过（可审计），不静默丢**（静默 = "全过了"的假象）。
5. **lens-metric 度量锚门控**：落锚前读 config.yaml 的 `metrics.enabled`——缺省或 `false` → 本轮**不落** `lens-metric` 锚、
   Step5 对应自检项跳过、**不调 emitter**（仅本仓源仓 dogfood 默认 `true`）；为 `true` → 按 Step4「裁决计数」构造 roster+findings，
   Step5 调 `lens_metric_emit.py` 产出后落进「报告格式」区。

## 第四步：自动修 / 自动裁 / defer（阶段三无人类门，P3e）

- **能修的自动修**：标 `[impl-review-fix]`，**不进延后池**。
- **≥2 方案（T10 三级协议，替换旧「有把握自动选」）**：①有客观判据（测试/断言/基准可判）→ 自动选并**按三镜 + 主次记理由**入报告；②无客观判据 → 派对抗镜复核推荐项，通过才自动选（复核记录写台账）；③复核不过/无从复核 → defer。**MUST NOT 以自评置信（"有把握"）作为自动选定的唯一依据。** 不问人。
- **修不了 / genuinely 拿不准**：defer → 写 buglist（本 change 引入的代码 bug）/ todolist（改进/关注点），
  本 change 不处理，交 hand-off 引导另开清理 change。
- **绝不 AskUserQuestion**（阶段三无人类门）。
- **裁决计数〔4.6·M4，已被 lens-metric 锚吸收〕〔impl-review-fix mlh-p4〕**：各参与镜（outside-voice 按 `site=code-voice|hr-tg`
  各独立计数）的裁决结果**构造进** `{roster:[{lens,runner,site}…本轮实际跑过的每个行键（domain/adversarial/history/broad +
  outside-voice 每个调用过的 site）——若 Step2 能力探针判 `subagents="unavailable"` 已缩 roster，此处 MUST 同步只含实际
  独立完成的行键], findings:[{hits:[{raw,runner?,site?}…],verdict,sev}…]}`（input schema 权威见契约
  `lens-metric-contract.md` 的 `lens-metric-input-schema` 机读块——bundle 分发可达、消费仓亦可读，非手数；源仓另有 golden fixture
  示范 `tools/tests/fixtures/lens_metric_input.json`，消费仓非 full 拷贝不含 `tests/`，以契约 schema 块为准）〔impl-review-fix mlh-p4：引用改指 bundle 可达契约块〕——原「voice分桶」自由 prose 台账行已被此锚吸收
  取代，这份 roster+findings 是下方「反馈回路〔泛化〕」判据的数据来源，Step5 调 emitter 归约后落成结构化可 grep 的锚。

## 第五步：产出 + 收敛口

- 写 `{change_dir}/code-review-report.md`（见下格式：命中范围 + Findings≥80 + 已裁掉区 + 裁决 + 修复/defer 台账 + 度量锚）。
- **度量锚落锚〔impl-review-fix mlh-p4〕**：`metrics.enabled=false` → 本段不落、**不调 emitter**；`true` → 用 Step4「裁决计数」
  构造好的 roster+findings 调 `python3 $RULES_ROOT/tools/lens_metric_emit.py --layer code-review --host "$SDFLOW_HOST" --input <构造的f>`
  （`--host` 取第零步同一次 `resolve-models.sh` 导出值；roster 中非 outside-voice 普通镜行 `runner` MUST 等于 `--host`；
  emitter 缺 `--host` / `--host` 越域走受控 fail-closed）→
  **exit 0 才**把 stdout（逐镜 `<!-- sdflow:lens-metric v1 … -->` 行）落进「报告格式」度量锚段；exit ≠0（fail-closed）→ 本段
  **不落**、报告注明 emitter 报错原因，MUST NOT 手拼锚行顶替。**保留残余信任边界声明**：分类正确性 + roster 完备性 +
  findings JSON 誊写准确仍是主 session 信任边界，emitter 只保证「给定输入的确定性归约」。
- **锚行自检（确定性脚本门）〔R1/R3/R5〕〔mlh-p2-anchor-lint〕**：出报告后调
  `$RULES_ROOT/tools/anchor_lint.py --report {change_dir}/code-review-report.md --layer code-review --root "$(git rev-parse --show-toplevel)" --trigger-catalog $RULES_ROOT/trigger-catalog.md`——
  退出码非 0（1=违规/2=fail-closed）即本步报错阻塞，遵其判定，MUST NOT 静默吞。脚本机验四类 v1 锚（Step1
  broad-review / hr-tg / outside-voice / **lens-metric**）存在性 + lens-metric 字段/枚举/sev/layer==--layer/
  计数 int≥0（枚举从契约 `lens-metric-enums` 块单一源读）+ metrics 开时 broad/outside-voice 最小必有行。
  **此自检由同一执行落锚的主 session 自行运行、非独立外部门**（与 `design-approved` 锚由 `ship_gate.py` 外部
  拦截不同）——诚实反映其拦截力：只挡"同一会话内忘记跑这步"，挡不住"整段跳过本步"。
  **保留信任边界声明**：数值一致性（`findings`/`采纳`/`独立`等是否与合并池实收数吻合）**是主 session 信任
  边界、非机械可验**，脚本 MUST NOT 谎称能机械保证数值正确。
  **config 门控**：`metrics.enabled` 为缺省/`false` 时，lens-metric 一类（含此自检）整体跳过（不落锚不阻塞）。
  **旁路声明**：lens-metric 锚缺失/取值违规仅拦报告完整性，**MUST NOT** 反向改写已裁决 findings 的采纳结论
  或本轮「建议进 /sdflow-done」结论。
- **反馈回路〔泛化，workflow-metrics-loop ADR-5〕**：原「outside-voice 累计 10 次后按采纳率复评降采样为
  HR-only」条款**泛化到 per-(层,镜)**——本 skill 落的每条 `lens-metric` 锚（domain/adversarial/history/
  outside-voice(各 site)/broad 均适用，非仅 outside-voice）都是该判据的原始数据；判据本身升级为**采纳率 +
  独立率双列**（单看采纳率会误留"高采纳但全冗余"的镜，独立率才是砍镜依据；两率定义/归属见规则根
  `lens-metric-contract.md`）。**本 skill 不做聚合、不做复评判断、不主动 surfacing**——聚合与「出现轮数≥10」
  的机械显著提示由 `/sdflow-retro` 聚合（跑 `sdflow-retro/scripts/lens_metric_aggregate.py` 只读聚合所有归档报告）；
  是否保留/降采样/收紧触发/淘汰某镜**一律人决，本 skill MUST NOT 自动执行**（阶段三无人类门管的是修复/裁决，
  不含评审架构本身的取舍）。
- 修复代码，改动处标 `[impl-review-fix]`。
- **checkpoint 提交**：产出报告 + 自动修复后 → `~/.sdflow/hack/checkpoint-commit.sh impl-review "多镜代码审 + 自动修 + 报告"`。
- **收敛口**：结尾一句——建议进 `/sdflow-done`（verify → hand-off → archive → commit → merge）。

---

## outside-voice helper 调用协议（契约单一源 = `~/.sdflow/hack/outside-voice.sh` 头注释，此处只给分支决策，不转述接口细节）

```
HELPER=~/.sdflow/hack/outside-voice.sh
[ -x "$HELPER" ] 不成立 → 显式提示「outside-voice.sh 未安装——先跑 bash setup.sh」+ 直接派 fallback 子代理（不静默）
版本核对：$HELPER version 输出与本 SKILL 预期主版本(1.x)不符 → 告警"helper 疑似陈旧，重跑 setup.sh"后继续
$SDFLOW_HOST="unknown"（第零步 resolve-models.sh 判不出宿主）→ 不调用本 helper、不跑 voice；锚行 host="unknown" runner="none" reason_code="host-unknown"（ADR-7），报告显著标注本轮无跨模型第二意见
以下分支仅在 $SDFLOW_HOST∈{claude,codex} 时适用；helper 只读第零步已 export 的 $SDFLOW_VOICE_RUNNER/$SDFLOW_VOICE_MODEL，MUST NOT 自行重判宿主（ADR-9）：
preflight：stdout 仅精确匹配 "ready" 走目标 runner（$SDFLOW_VOICE_RUNNER）；"not_installed" → fallback（reason_code="not-installed"）；"missing-deps" → fallback 且 MUST 映射锚 reason_code="preflight-error"（D7，MUST NOT 原样落 reason_code="missing-deps"——该值不在契约 reason_code 枚举内，会被 anchor_lint 矩阵判 illegal-combo）；任何畸形输出/非零退出 → fallback（reason_code="preflight-error"）
context 构造（摘录规则定死，不现场发挥）：本轮**起手先占一个 run 目录**，本轮所有站点共用、定后不再变；context 写 {change_dir}/.outside-voice/<run-id>/<site>-context.md
  **run-id 生成 + 占坑（唯一性交给 OS 判，不靠自觉）**：MUST 逐字跑下面这两条——`mktemp -d` **原子地建目录并保证唯一**，唯一性由它负责，不靠时间戳精度、不靠自觉。前缀带 UTC 时间戳只为人读排序；后缀 `XXXXXX` 由 `mktemp` 填随机位，故**同秒起的两轮并行评审也必得不同目录**。
    `mkdir -p {change_dir}/.outside-voice`
    `RUN_DIR="$(mktemp -d "{change_dir}/.outside-voice/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")" && basename "$RUN_DIR"`
  **MUST NOT 自己拼 run-id 再 `mkdir`**（手拼要么撞名、要么退化成 `$RANDOM`/`od` 这类不可移植写法，还得自造重试循环与上界）——`mktemp -d` 一条就把唯一性、原子性、失败非零退出全给了；父目录不可写 / 磁盘满时它非零退出且错误直接浮出，此时 MUST 显式停、MUST NOT 继续跑 voice
  🔴 **run-id MUST 当场取回字面值，MUST NOT 靠 shell 变量跨调用存活**：harness 每次 Bash 调用是独立 shell（env var 不持久）⇒ `$RUN_DIR` 在**下一次**调用里必为空、路径会退化成 `/dispatch-manifest.tsv` 这种写根目录的废值，而 dispatch 必然发生在建目录之后的另一次调用。∴ MUST 在**建目录的同一次调用内**跑 `basename "$RUN_DIR"` 把 run-id 打印出来，记下该**字面串**，后续所有路径一律代入字面 run-id
  **per-run 不可变**：同一 run-id 下每站点只写一次，写完不改不删（留调试证据）；后续轮次一律换新 run-id，**MUST NOT 复用或覆盖既有 run 目录**（helper 的入境扫描与渲染是对该文件的两次独立读——不可变路径令二者恒对同一快照，闭掉「上轮 voice 尚未读完、下轮重写同一路径」的跨会话 TOCTOU；`mkdir` 占坑令「run-id 是否真每轮换新」由 OS 判定，而非诚实边界）
  **父目录 MUST 仍在 {change_dir}/.outside-voice/ 下**：`.gitignore` 的 `**/.outside-voice/` 递归覆盖该层级；落到该目录之外 = checkpoint 的 `git add -A` 把全量 diff / 敏感 context 永久入库，正是该条款要防的
  **dispatch manifest（落盘审计证据，F-I）**：每次实际发起 voice 时**追加**一行到 {change_dir}/.outside-voice/<run-id>/dispatch-manifest.tsv——MUST 逐字用下面这条 `printf`（`printf` 把 `\t` 解释成真制表符；MUST NOT 手拼字符串或用 `echo`，那会落成字面 `\t`），时间戳格式与 run-id 同为 `%Y%m%dT%H%M%SZ`：
    `printf '%s\t%s\t%s\n' "<site>" "<task_id>" "$(date -u +%Y%m%dT%H%M%SZ)" >> "{change_dir}/.outside-voice/<run-id>/dispatch-manifest.tsv"`（`<run-id>` 代入上面取回的字面串，不是 shell 变量）
  `<task_id>`：后台派发填该后台任务标识；同步 exec 填字面 `sync`。「是否真派发过某站点」以本文件为准，MUST NOT 靠会话记忆
  site=code-voice → git diff $DIFF_BASE..HEAD 全量
  site=hr-tg      → 命中 TG 判据触发点 + 相关 diff hunk
<!-- sdflow:async-branch:start —— 站点无关的 host 调度段。与另一评审 SKILL 的同名 marker 段 MUST 字节相同（hack/check_async_branch_parity.py 机械守）。站点枚举 / context 构造 / reuse-guard 门控 / declared-sites 计算 MUST 留在本 marker 之外 -->
exec（host 分支：**只读第零步已 export 的 $SDFLOW_HOST，MUST NOT 在此重判宿主**，ADR-4）
  **① 内层超时 `<VOICE_TIMEOUT>` 取值（config.yaml 直读，沿 `metrics.enabled` 先例；MUST NOT 走 resolver——两 SKILL 同法，否则等值门红）**：
    读仓根 `openspec/config.yaml` 的 `outside-voice.async-timeout-seconds`；**仅 async 分支用它**，sync / 降级分支恒 `300`。
    校验：MUST 为**正整数**（纯十进制数字串，无小数点 / 无单位后缀 / 无正负号 / 无空白）且 `1 ≤ v ≤ 3600`（`3600` = 理智上界——helper 内层 `timeout -k 10` 自身无上限，误配成 `86400` 会把一轮评审永久挂住；3600 远高于 900 默认，留足调宽空间）。
    缺键 / 缺 config 文件 / 读失败 / 非整 / `0` / 负数 / 越界 → **一律回落默认 `900`**（fail-safe 恒生效：**MUST NOT fail-closed 罢工**、**MUST NOT 传 `--timeout 0`**——那会取消 helper 的「≤天花板必终止」保证）。
  **② 后台能力自探（dispatch 前 MUST 先跑；语义核验非机械门。这是验证「本调用上下文真能后台化」的实际防线，不是冗余保险，ADR-6）**：
    `$SDFLOW_HOST≠"claude"` → 不自探，直接走 sync 分支。
    `$SDFLOW_HOST="claude"` → 用 run_in_background 派一条 trivial 命令（如 `printf PROBE_OK`）：拿得到后台任务标识**且**取得回 `PROBE_OK` → `background="available"`；派不出 / 机制报错 / 取不回哨兵 → `background="unavailable"`。
    `background="unavailable"` ⇒ **降级走 sync 分支**，且报告本段 MUST 显著标注「⚠️ voice 同步降级（后台能力不可用，host=claude）」——**MUST NOT 假装 async 成功**、MUST NOT 因此跳过 voice、MUST NOT 因此改动锚行契约。
  **③ 执行模式矩阵（F-B；三行始终满足「外层 ≥ 内层+30s」）**：
    🔴 **内层秒数一律代入十进制字面值**（如 `900` / `300`）——**MUST NOT 写 `$VOICE_TIMEOUT` 之类 shell 变量**：harness 每次 Bash 调用是独立 shell，上一次调用设的变量在这里必为空（同 ④ 的 `$HELPER` 条款、同 context 构造节的 run-id 条款）。下表 `<VOICE_TIMEOUT>` 是**占位符**，指 ① 解析出的那个数。
    | 分支 | 条件 | 内层 `--timeout` | 外层 Bash 工具超时 |
    | async | host=claude ∧ `background="available"` | `<VOICE_TIMEOUT>`（默认 900） | 不适用——dispatch 调用 <1s 即返回；后台任务**不受 Bash 工具超时约束**（spike 实证 2026-07-18：后台跑满 660s、跨过 600000ms 上限、exit 0、ppid 稳定）⇒ 有效外层无界 ≥ 内层+30s。**MUST NOT** 因它"是长命令"就给 dispatch 调用设长超时 |
    | sync | host=codex | `300` | ≥330000ms |
    | sync（降级） | host=claude ∧ `background="unavailable"` | `300` | ≥330000ms |
    ⏱ **sync 两行的外层超时（调用方 MUST，防假超时）**：exec 是长命令（helper 内部 `timeout -k 10` 300s + 10s grace）——MUST 把外层 Bash/shell 工具超时设为 **≥330000ms**，MUST NOT 用 harness 默认（常 120s）：外层短于内层会在 helper 正常干活时先 kill，造成"假超时→重跑"浪费（reason_code 会误落 timeout、实则未真超时）。**指令层约束**（外层超时由调用方逐调用设、helper 作被调方无法机械强制，同 host 解析 eval 那类诚实边界）。
  **④ 命令形态（两分支共用同一哨兵 envelope）**：整条命令 MUST 逐字为——
    `~/.sdflow/hack/outside-voice.sh exec --timeout <T> --context-file <f>; rc=$?; printf '\n<<<SDFLOW_EXEC_EXIT>>>%s\n' "$rc"`
    （`<T>` 代入本分支内层秒数的**字面值**，`<f>` 代入 context 文件**字面路径**；**MUST 代入 `~/.sdflow/hack/outside-voice.sh` 字面路径、MUST NOT 写 `$HELPER`**——harness 每次 Bash 调用是独立 shell，上一次调用设的变量在这里必为空）
    async 分支：该命令**以 run_in_background 派出**，立刻记下返回的后台任务标识（见 ⑧）；sync 分支：前台跑，当场即得退出码。
    🔴 **为什么是 `printf '\n…'` 而不是 `echo`**：helper 末尾 `cat last-message.md` **逐字节透传模型自由文本、且不保证尾换行** ⇒ 朴素 `echo` 会与 voice 正文末行**粘成同一物理行**（实测：整行锚定 0 命中 → 把**成功**的 voice 假降级）。强制前置换行把这层不确定性彻底消掉。
  **⑤ 退出码 MUST 从哨兵 envelope 取，MUST NOT 从 voice 正文推断（F-D）**：
    在该命令输出上做**整行锚定**扫描 `^<<<SDFLOW_EXEC_EXIT>>>([0-9]+)$`，数命中行数：
      **恰好 1 行** → 取其捕获组为退出码，进 ⑦。
      **0 行 或 ≥2 行 → `exec-error`**（wrapper 恒发且只发一行 ⇒ ≥2 行正是 voice 正文注入了一行的**确定性信号**；审「讨论本机制自身」的 change 时 voice 正文必然出现该字样，此判据即为此而设）。
    **MUST NOT** 用宽松 grep / 子串匹配 / 取末行代替整行锚定。
  **⑥ 通知驱动 collect @Step3 barrier（F-A；async 分支专属，sync 分支当场就有退出码）**：
    本 harness 的 run_in_background 是**完成推送通知**（"you will be notified — do not poll"），**不是**可主动查询的状态接口 ⇒
      · dispatch 时 MUST 就地记「**站点 ↔ 后台任务标识**」映射（见 ⑧），并按 context 构造节把该 task_id 追加落盘 `dispatch-manifest.tsv`；
      · 完成通知**异步到达**（可能早于 Step3）→ 收到即**暂存该站点的输出与退出码**，MUST NOT 丢弃；
      · **Step3 是 barrier**：每个**实际 dispatch 过的**站点，其结果 MUST 已在手、或已按 ⑦ 降级完毕，才可进综合裁决。
    🔴 **正向 barrier 语义**：某 dispatch 站点在 Step3 时**尚无终态退出码**（仍 RUNNING）⇒ MUST **让出轮次、等该后台任务的完成/超时通知**后再继续（通知由 harness 推送，这既非长 sleep 也非轮询）。
      **MUST NOT** 单次长 sleep 等待、**MUST NOT** 自造轮询循环。
      **`reason_code="timeout"` 只允许由实际观测到的 `exit 124` 产生**——**MUST NOT** 在未收到该站点终态通知前落 `timeout`。早退假 timeout 把「慢但会成功」的 voice 假降级，正是本机制要消灭的失效模式；且它**逃得过 per-site 站点集核**（该站点仍在集合内、照样判绿），∴ 本条是唯一防线。
    🔴 **barrier 的执行位：MUST 在主 session，MUST NOT 委派子代理**：本 barrier 的「让出轮次等通知」以及各站点的 collect，MUST 由**主 session 自己**执行——**MUST NOT** 把等待/取回动作交给任何子代理，也 MUST NOT 在子代理内 dispatch 后由外层跨轮次接手。
      依据（2026-07-18 实测，两侧都有正面证据）：**子代理上下文的轮次终结会连带回收该上下文在飞的后台任务**——一次观测中该上下文 3 个在飞任务同时被 SIGTERM，**无 envelope、无完成通知** ⇒ 等待方既拿不到退出码、也永远等不到那条通知；而**主 session 让出轮次转空闲不触发回收**——心跳探针 702s 跑满、exit 0、ppid 全程稳定无 reparent、并跨过 600000ms 外层上限。
      ∴ dispatch 与 collect MUST 同在主 session：子代理内派出的后台任务只允许在**该子代理自己的轮次内**取回，MUST NOT 跨其轮次边界等待。
    **安全（MUST）**：collect **只取「结构化退出码 + exit 0 时的 stdout findings」**。helper 在 exit≠0 时把 runner **原始 stderr + 未扫描的 final-message 前 3 行**写 stderr，该段**绕过出境 `secret_scan`**（既有缺口），而后台化把它落进了 harness 托管的后台任务输出文件（新持久化载体）⇒ **MUST NOT 把后台文件里的原始 stderr 当 findings 采信**，只允许摘要写进锚行外正文。
  **⑦ 退出码 → 去向 / reason_code（两分支同一张表，无遗漏；未知码 MUST NOT 读作 ok）**：
    exit 0   → stdout 即 findings 进合并池；锚行 host="$SDFLOW_HOST" runner="$SDFLOW_VOICE_RUNNER" reason_code="ok"（唯一合法跨模型第二意见，矩阵判 cross-model）
    exit 124 → fallback（reason_code="timeout"）——**仅当真观测到 124**，见 ⑥ 正向 barrier 语义
    exit 1   → fallback（reason_code="exec-error"，stderr 摘要写锚行外正文）
    exit 2   → 用法错 / context 不可读 → fallback（reason_code="exec-error"；`2` 不在 reason_code 枚举内，**并入 exec-error**，枚举不新增）
    exit 3   → 本次 voice 拒发不 fallback（锚行 host="$SDFLOW_HOST" runner="none" findings="0" reason_code="secret-hit"；密钥既不出境也不进子代理 prompt）
    其余一切情形（未知码 / envelope 0 行或 ≥2 行 / 后台任务标识查不到 / 输出取不回）→ **保守** fallback（reason_code="exec-error"）；**MUST NOT 读作 `ok`**、MUST NOT 静默丢该站点、MUST NOT 落零锚
  **⑧ 站点 ↔ 后台任务标识记账（MUST 在指令执行中显式维护此表；model-driven 记账易错，故既落盘又逐站点取）**：
    | 站点 | 本轮是否 dispatch | 后台任务标识 |
    | <逐个填本轮涉及的站点> | 是 / 否（否则附未派原因） | `<task_id>` 或字面 `sync` |
    · 本表的集合 = **实际 dispatch 过的站点**（后台 voice 数不定 0/1/2）——**它与「应有锚的站点集」不是同一个集合**（门控/复用态可以不派却仍落锚），二者 MUST NOT 混用。
    · collect 时 MUST **按本表逐站点取**（不靠"好像都回来了"的整体印象），每站点各自独立走 ⑤ 与 ⑦。
    · 「是否真派发过某站点」以 `dispatch-manifest.tsv` 为准，MUST NOT 靠会话记忆。
<!-- sdflow:async-branch:end -->
fallback（同族降级，reason_code ∈ {not-installed,preflight-error,timeout,exec-error}）：以 $HELPER render-prompt --context-file <f> 的输出为 prompt 派 fresh **只读型**（与 $SDFLOW_HOST 同宿主）子代理（禁写/禁执行副作用）（同源同 prompt；框架已含范围收窄）；
  无硬超时（与 codex 侧 300s 不对称，接受并留痕）；findings=0 的 fallback 在报告标注供抽查；锚行 host="$SDFLOW_HOST" runner="$SDFLOW_HOST"（同族——`claude-fallback` 枚举值已废弃，跨模型性是派生量，同族 fallback 由 runner==host 表达）
  **F8（同族 fallback 也起不来）**：若该 fallback 只读子代理**本身也派不出**（spawn 失败/机制报错）→ 无同族降级可用 → 锚行 host="$SDFLOW_HOST" runner="none" findings="0" reason_code="fallback-unavailable"（host-adaptive-execution spec：同族 fallback 也起不来 ⇒ 无执行段、非自审；runner="none" 恒 findings=0，anchor_lint 矩阵判 no-exec 合法）
锚行（每调用位点一行，truncated 取 helper stderr 的 OV_TRUNCATED；host/runner 恒取第零步同一次 resolve-models.sh 导出值，不重判）：
  <!-- sdflow:outside-voice v1 site="…" guard="none|file-missing|section-not-found|zero-findings|stale|simulated-source" host="claude|codex|unknown" runner="claude|codex|none" reason_code="ok|not-installed|preflight-error|timeout|exec-error|host-unknown|secret-hit|fallback-unavailable" findings="N" truncated="true|false" -->
```

**per-site 完整性声明〔async-outside-voice §3.5·F-C〕**（**本段留 `sdflow:async-branch` marker 外**——两层的站点集不同，放进等值门内会永红）：报告 MUST 落**恰好一条** `declared-sites` 锚，声明**本层「应有锚」的站点集** = `{code-voice}` ∪ `{hr-tg | HR-TG∩≠∅}`（HR-TG∩ 取第二步 `hr_tg_intersect.py` 的判定，是本公式**唯一动态输入**）。逗号分隔、字典序、无重复：

  `<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->`（HR-TG∩=∅ 时 → `declared="code-voice"`）

- 🔴 **是「应有锚」集、不是「应 dispatch」集**：`code-voice` 是 always〔第二步半 C3·R1〕⇒ 它**恒在**本集合内。本集合与上文「站点↔task_id 记账表」（＝**实际 dispatch 过**的站点集）**不是同一个集合**，MUST NOT 混用。
- 🔴 **MUST NOT 拿 `guard=` 当本集合的判据**——该字段语义**站点相关**（复用/填充两义）。
- **机械核**：`anchor_lint.py` 的 `check_declared_sites` 同时比对「declared == 公式重算期望集」与「declared == 报告实落 `site=` 集」，任一不等即 VIOLATION——补上家族级门（有 ≥1 条 outside-voice 锚即过）的 per-site 盲区，**并发 2 站点漏收一个不再被判 CLEAN**。锚缺失 / ≥2 条 / 缺 `declared=` 一律 fail-closed。
- 🔴 **漏收某站点 MUST NOT 靠删 declared 抹平**：期望集由公式独立重算，declared 与实落一起缩水仍判红。

## 报告格式（code-review-report.md）

**报告头部 frontmatter（ship-gate 契约，mlh-p5 迁 frontmatter，模板写死二选一，勿改写字段名、勿两键并存）**：
MUST 在文件**最顶端**（prepend，非追加末尾）写：

```yaml
---
ship-gate:
  code_review: pass
---
```
或
```yaml
---
ship-gate:
  code_review: blocked
---
```

——`code_review` 字段二选一（`pass`/`blocked`，下划线字段名、小写值），/sdflow-ship 读此 frontmatter 机判。
若文件已有首块 frontmatter，MUST 合并 `ship-gate:` 键进已有块（不新开第二块）；若无则新建。头部之后紧接下方正文（含人读结论行，不可省略）：

```
## code-review 报告 — {change}
### 命中范围
  栈: backend·go / embedded·ml307c …   清单: CR-01~09 + CR-GO-* + …   gstack/review: scope-drift/完成度 结论
### 子代理能力锚（host=codex 报告必填，语义核验非机械门，见 Step2「能力探针」）
  <!-- sdflow:fanout-capability v1 host="…" subagents="available|unavailable" mirrors="domain,adversarial,grounding|—" -->
  subagents="unavailable" 时本报告 MUST 显著标注「⚠️ 单镜降级」（见命中范围/结论区）。
### Findings（置信 ≥80）
  [严重度] CR-04 资源泄漏 | file.go:42 | 错误路径未释放 conn | 置信 90 | 已修[impl-review-fix] / defer→buglist
### 已裁掉（反静默压制，可审计）
  X1  reviewer 原始发现 + 主 session 裁掉理由；<80 滤除项一行带过
### 修复 / defer 台账
  自动修 N 项[impl-review-fix]；自动选推荐 M 项(按三镜+主次附理由)；defer K 项 → buglist/todolist
  T10复核: <方案> | 对抗镜结论 <通过/证伪> | <理由(三镜+主次)>   ← 无客观判据的 ≥2 方案自动选必附
### 度量锚（lens-metric，受 config `metrics.enabled` 门控——关闭则本段整体不落、不调 emitter，见第三步/第五步）
  domain / adversarial / history / outside-voice（同轮 site="code-voice" 与 site="hr-tg" 若均调用，各独立一行）/ broad（gstack/review Step1）
  各一行——本段内容 = Step5「度量锚落锚」调 `lens_metric_emit.py` 后 exit0 落进来的 stdout，MUST NOT 手拼：
  <!-- sdflow:lens-metric v1 layer="code-review" lens="…" host="…" runner="…" site="…" findings="N" 采纳="N" 裁掉="N" defer="N" 独立="N" sev="致N/高N/中N/低N" -->
  字段/取值域/归属/折叠规则见规则根 `lens-metric-contract.md`（唯一权威源，此处只引用不复制清单）；
  原「voice分桶」自由 prose 行已被 outside-voice 镜的此锚吸收取代。
  这些锚跨 change 归档后由 `/sdflow-retro` 聚合、按 per-(层,镜) 采纳率+独立率双列复评（见第五步「反馈回路」），
  本报告不重复该判据、只负责落准确的锚。
### 结论
  □ 建议进 /sdflow-done   □ defer 残差已入 buglist/todolist（hand-off 会引用）

  （机判锚已迁至报告**头部** frontmatter `ship-gate.code_review: pass|blocked`，见上；此处结论区末行只保留人读勾选结论，不再重复机判锚）
```

## 模型选择（按本步性质，逐步定）

档位与缺省见规则根 `model-tiers.md`（按机队分列，经 `~/.sdflow/hack/resolve-workflow.sh` 解析；config.yaml 的 model-tiers 段可按机队分键覆盖）。**取值 MUST 引用第零步同一次 `eval "$(resolve-models.sh)"` 导出的 `$SDFLOW_TIER_STRONG`/`$SDFLOW_TIER_MID`/`$SDFLOW_TIER_LIGHT`**（已按当前宿主机队 + config.yaml 覆盖解析好的具体模型 id）派子代理，**MUST NOT 内联具体模型 id（各机队缺省专名，见 `model-tiers.md` 机读块）**。**Codex 宿主下 `spawn_agent` 指定 `model` 的 task-specific reason**〔host-adaptive-execution · 模型档位按机队分列〕一律填「本工作流的 model-tiers（门禁步禁降档是硬约束）」，不必另编理由。

```
  主 session（裁决 / 自动裁 / 出报告）        强档 = $SDFLOW_TIER_STRONG ← 这是门禁,弱档=假绿
  领域镜 / 对抗镜（判断、对抗推理）           中档 = $SDFLOW_TIER_MID
  历史镜 / 置信过滤（git blame/打分，机械）   弱档 = $SDFLOW_TIER_LIGHT
```

依据：评审是门禁，综合判断这层弱档会"看着过其实没深究"；机械读 blame/打分可下放弱档。
**不要**把综合判断委派给弱档子代理。阶段三无人类门（不 AskUserQuestion，自动修/裁/defer）。

## 与 gstack/review、官方 code-review 的分工（并入 vs 弃用）

| | gstack/review | 官方 /code-review | 本 skill（sdflow-code-review 编排器） |
|---|---|---|---|
| 现状 | **并入本 skill Step1** | **弃用为独立 step（P3d）** | 每次全跑·独立冷·强制主审 |
| 干什么 | scope-drift + 完成度审计 | 插件能力仅供历史镜/置信过滤**内部借用** | 清单逐条 + 对抗 + 置信过滤 + 合并出报告 |
| 决策 | 自动（纳入合并池） | 不再独立 gh 回帖 | 主 session 对抗裁决 + 自动修/裁/defer |

> P3d：官方 `/code-review` 不再作独立 step（subagent-dev production-readiness + 本 skill 已覆盖，
> 本地合并无需 gh 留痕）；但保留其插件能力供历史镜 / 置信过滤内部借用。

## 注意

- **每次全跑，非高风险才跑**（P3c；旧 quality-layering §五"缩成残差"结论已否决）。
- **置信过滤要可审计**：滤掉的 <80 项一行带过，不静默丢。
- **不重扫 CI 能抓的**：linter/typechecker/编译器范围内的不进镜。
- **代码即 ground truth**：直接读 diff 与真实代码，不设接地镜（与 sdflow-spec-review 的唯一结构差异，换历史镜 + 置信过滤）。
- checkpoint 脚本 = `~/.sdflow/hack/checkpoint-commit.sh`（setup.sh 全局安装）；缺失则先跑 setup，或退化为普通 `git add -A && git commit`。
- 项目无关：规则路径一律经 `~/.sdflow/hack/resolve-workflow.sh` 解析（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`。
