<!-- sdflow:principles:start —— 真相源 sdflow-init/assets/snippets/principles-project.md，由 hack/sync_principles.py 注入，勿手改本区块 -->
## 🟢 三条通则（在本项目里干活，一律适用）

> 适用于**一切**任务——回答问题、写代码、做设计、跑评审。**违反即本次工作失败。**
>
> **为什么内联在这里、而不是放进 rules/ 只留一个指针**：这三条要防的失效模式，**恰恰包含「不会想到要去查它」**——
> 「拿现状反驳目标」的那一刻，你正觉得自己证据确凿；「你们用什么测试框架？」问出口的那一刻，你根本没意识到这该自己查。
> **会想起去查这条规则的人，本来就不会犯这个错。** ∴ 它必须一直在场。

### ① 能查的自己查，能调研的自己调研

答案在**仓里 / 这台机器上 / 公开资料里** ⇒ **自己去拿**，查完**直接给结论**。
**MUST NOT 拿一个自己查得到的问题去占用人的注意力**（「你们用什么测试框架？」——`package.json` 里写着）。

**给结论，不给过程**：「集成测试是 `make integration`，我跑过了，绿」——
**而不是**「Makefile 里好像有个 integration target，你确认一下？」

### ② 不确定的方案，先调研再给推荐 —— **MUST NOT 甩开放题**

拿不准时 **MUST NOT 把几个选项原样丢给人**——那是**把调研的活布置给了人**。
正确动作：**先把能查的查了，带着「推荐 + 依据 + 代价 + 备选」来，人只负责拍板。**

**⇒ ①② 合起来的三分判据**（每个问句先归一次类）：

| 答案在哪 | 动作 |
|---|---|
| 仓 / 机器 / 公开资料 | **自己查** → 给结论。**不问** |
| 查得到候选与依据（选型 · 路线 · 工具） | **调研 → 推荐 + 依据 + 代价 + 备选 → 人拍板** |
| **只在人脑子里**（偏好 · 踩过的坑 · 拍板权 · 组织约束） | **问** —— **注意力该全花在这里** |

> **人做的是拍板，不是替你做调研。**

### ③ 以最终目标为准，MUST NOT 拿现状反驳目标

判断「该不该做 / 做到什么程度」**一律锚目标态**，**不受现有代码与设计的束缚**。

**MUST NOT** 用「现在的代码不是这么写的」「存量数据里没出现过」「现状里这种情况很少见」
「现有设计不支持，所以改小一点」来论证**目标该缩水**。

> 迁移中「旧数据还没有新形态」是**必然**——拿它当风险基线，会把「目标态才暴露的面」误判成「不存在」。
> **问「目标态下的 producer 会不会产出这种形态」，不是问「现存文件里有没有」。**
>
> 🔴 **评审时最容易犯**：现状是唯一摆在眼前的东西，于是「它现在能跑 / 没出过事」
> 极易被当成「它是对的 / 不用改」。**评审的基准是目标态。**

> **fan-out 子代理 / outside-voice 跑在 fresh context，看不见本文件** ⇒ **它们的 prompt MUST 原文带上这三条**。

<!-- sdflow:principles:end -->

## OpenSpec 工作流（sdflow-init 铺设）

端到端流程见 workflow 规则集 `workflow.md`（真相源；本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。规则集在 `openspec/workflow/`：
`trigger-catalog.md`（触发单一源 TG）· `spec-checklists/`、`code-checklists/`（设计审/代码审）·
`ff-generation-constraints.md` · `design-diagrams.md` · `spec-review.md` · `generation-process.md`。
质量分层与升级安全见 `openspec/workflow/reference/quality-layering.md`（本仓有 `openspec/workflow/` 规则副本则用之，否则在全局 `~/.sdflow/workflow/`）。

**强制操作规范**

- **起手判触发**：收到 `opsx:ff` / `propose` / `explore`，先按 `trigger-catalog.md` 的 TG 判命中，
  据此激活对应的生成约束 / 领域清单 / 画图 / 模版必填槽（深度由触发决定，不分 S/M/L）。
- **审查顺序不可颠倒**：`/review`（本地 diff）→ push PR → `/code-review`（远程 PR）。
  子 agent 调度期间（subagent-driven-development / sdflow-implement / sdflow-spec-review / sdflow-code-review 运行中）禁 `/clear`。
- **ff 开分支**：`opsx:ff` 若不在 feature 分支，先 `git checkout -b feat/{change}`（FF-0）。
- 🔴 **ff 之后是 grill，不是 spec-review**：`opsx:ff` 产出四件套后，**MUST 提示下一步 = `/grill-with-docs`**
  （阶段一的对抗层），**MUST NOT 直接跳到 `/sdflow-spec-review`**。
  **且 MUST 把 `workflow/prompts/step3-grill.md` 原样贴出来**给用户复制（整个文件就是那段 prompt，**只有 500 字节，别去读 workflow.md**）——
  `grill-with-docs` **只能人手动触发**（`disable-model-invocation: true`），**光说「下一步跑 grill」等于没提示**。
  **MUST NOT 转述、精简、或凭记忆重写那段 prompt**（单一源 = `workflow/prompts/step3-grill.md`，照抄）。
- **INDEX 同步**（仅规则副本 pin 仓/toolkit 源仓适用）：新增/删 `openspec/workflow/` 规则后，同步 `openspec/INDEX.md`。

**配套 skill（workflow 依赖，需先安装）** — 均来自 sdflow-skills（`bash ~/.skills/sdflow-skills/setup.sh` 装到 Claude+Codex）：

| skill | 在流程中的角色 |
|---|---|
| `/sdflow-spec-review` | 设计审**主审**——并行多镜，按 `spec-checklists/domains` + 对抗 + 接地读码 |
| `/sdflow-code-review` | 代码审**主审**——并行多镜，按 `code-checklists/domains` + 对抗 + 置信过滤 |
| `/sdflow-done` | **闭环**——verify → archive（delta 对码核验同步）→ commit → merge |

> 另有两个记录类配套 skill（按需）：`/sdflow-buglist`（缺陷）、`/sdflow-todolist`（改进收集池），
> 同样来自 sdflow-skills，写入 `openspec/issues/buglist|todolist/`。

> **`/grill-with-docs`（阶段一对抗层，来自 superpowers 插件，不是 sdflow-skills）**——**ff 之后、设计审之前的必经步**。
> 它 **`disable-model-invocation: true`，只能人手动触发**：模型唤不起它，只能**把 prompt 贴给人、由人敲**。
> 因此它极易被静默跳过——**跳过 grill = 把一份没被拷问过的设计直接送进设计审**，
> 而 spec-review 的多镜是在**已有设计的框架内**找问题，**不会替你质疑这个框架本身**。
