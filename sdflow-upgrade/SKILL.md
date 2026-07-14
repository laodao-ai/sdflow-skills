---
name: sdflow-upgrade
description: 升级 sdflow 工具链运行 checkout（~/.skills/sdflow-skills）：git pull → bash setup.sh（skills 软链 + ~/.sdflow canonical/hack 同步刷新，堵 pull→setup 窗口期）→ 显示版本与最新变更，并提示消费仓按需跑 sdflow-init update。当用户说"升级 sdflow"、"更新 sdflow skills"、"sdflow upgrade"、"sdflow 有新版本吗"、"刷新 sdflow"，或使用 /sdflow-upgrade 时触发。
---

# sdflow-upgrade — 运行 checkout 一键升级

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

对**运行 checkout** `~/.skills/sdflow-skills/` 执行升级三连。pull 与 setup 必须连跑——
SKILL.md 软链即时生效、`~/.sdflow/hack/` 脚本拷贝生效，只 pull 不 setup 会造成两者版本错位（陈旧遮蔽的脚本变体）。

## 步骤

1. **pull**：`git -C ~/.skills/sdflow-skills pull --ff-only`
   - 非 ff（本地被改过）→ 停下报告，不强推；提示"运行 checkout 只读，改动应发生在开发 checkout"。
2. **setup**：`bash ~/.skills/sdflow-skills/setup.sh`
   - 刷 skills 软链 + `~/.sdflow/workflow` canonical + `~/.sdflow/hack/{checkpoint-commit.sh,resolve-workflow.sh}`。
3. **展示**：`cat ~/.skills/sdflow-skills/VERSION 2>/dev/null || echo unknown` + `git -C ~/.skills/sdflow-skills log --oneline -5`，向用户汇报版本与最新变更。
4. **提示**：各消费仓如需拿最新 tools/ 或看陈旧遮蔽告警 → 在该仓跑 `sdflow-init update`（本 skill 不代跑）。

## 回滚

推坏一版规则时：`git -C ~/.skills/sdflow-skills checkout <上一已知良好 commit> && bash ~/.skills/sdflow-skills/setup.sh`。

## 注意

- 只动运行 checkout；开发 checkout（编辑规则/skill 的 clone）不归本 skill 管。
- 运行 checkout remote 必须是 `laodao-ai/sdflow-skills.git`——不是则先按 minimize-repo-footprint 的 0.1 迁移。
