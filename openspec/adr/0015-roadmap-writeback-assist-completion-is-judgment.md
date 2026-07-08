# roadmap 回填降摩擦助手：完成判定含判断，机械搬运自动化、判断留人

`done-roadmap-writeback` 经两轮 grill + 两轮 7 镜 spec-review，骨架从「起手锚 best-effort」→「编号统一」→「归属镜像 + scaffold 双向」逐步被揭穿，最终经**现状实践核验**收敛为最小核。本 ADR **supersede `adr/0013` 与 `adr/0014` 的机械回写骨架**。

## Context（两轮 spec-review 两致命 + 现状实证）

**第二轮 spec-review 两个致命（源码/公式证实，非推理）**：
- **C1（scaffold↔opsx:ff 结构冲突）**：`@fission-ai/openspec` CLI 判 artifact done **只看文件存在**（`state.js` `artifactOutputExists`），`apply: requires: [tasks]`。scaffold 作官方 CLI 之外的第二 producer 写 change 产物文件（tasks/proposal），会让 opsx:ff 的「文件存在=done」判定**短路整条产出链**（proposal/specs/design 被跳过）。两个独立 producer 无写入协议，判定机制在官方 CLI、改不了。
- **C2（阶段 enum 不可机械）**：聚合公式 `全非deferred完成=delivered` **自身循环**（算 delivered 要先知 deferred，deferred 是输出）；且 deferred **无机器信号**（二值复选框 `[ ]` 无法区分「未做」vs「显式放弃」）。把**规划判断**当机械聚合是范畴错误。

**现状实践核验（用户问，实地查 git/roadmap）**：roadmap 完成判定 = 人在 change 归档**后**，读确定性盘面（merge / verify=PASS / 归档目录进 base）+ 对照人写的 `### 验收标准`（语义判断），**手动**勾复选框 + 写交付标注 + task-log 完成总结（commit 关键词「回填对账」）。**完成判定本质含判断，现状无任何机械判据**——「某子任务算不算完成」从来不是机械读复选框，是人对照验收标准判的；deferred（◐排后）更是纯规划判断，复选框根本不承载。

## Decision（最小核 + 判断留人）

1. **完成判定的盘面-判断切分**（现状实证）：**确定性盘面**（change 是否归档/merge/verify=PASS，已有机械锚，`ship_gate` 在用）= 机械可读；**是否满足验收标准 / 算不算完成 / 勾哪些** = 判断，现状人做、目标态仍人做。
2. **定位 = 回填降摩擦助手，非无人干预自动回写**：sdflow-done 收尾读确定性盘面，生成人可确认的**回填草稿**（候选复选框 + task-log 完成总结骨架含机械锚），**判断留人**（确认勾哪些 / 补价值叙述 / 验收 / 阶段状态 / deferred）。同 `lens-metric`（计数机械/分类判断）、`issues sweep`（triage 机械/归批判断）、现状（人回填）的切分。
3. **弃机械回写骨架**：
   - MUST NOT scaffold 双向预建（消 C1：不写 change 产物文件、不碰 opsx:ff 的 done 判定）。
   - MUST NOT 阶段状态 enum 机械聚合（消 C2：阶段状态/deferred 是判断，留人写散文）。
   - MUST NOT 编号统一 / 归属镜像（消粒度失配：roadmap 复选框=change 级、tasks=实现分解，各保现状格式）。
   - MUST NOT 强制 roadmap 机读化 / 存量迁移（判断留人、不需机械镜像，roadmap 现状散文格式即可，助手适配它）。
4. **触发（阶段三无人类门约束）**：sdflow-done 收尾检测 change 关联 roadmap（轻量声明）→ 回填草稿进 hand-off，**提示人异步确认回填**（同现状独立「回填对账」commit，从纯手写降为改草稿）；不弹窗（阶段三无 AskUserQuestion）、不阻塞归档/merge。
5. **关联漏 = 现状**：未声明关联 = 退回现状人全手工回填，**不 fail-closed 阻塞**（辅助非正确性门）；可轻量提示、不强制。

## supersede

- **`adr/0014` 全部**（归属镜像 / scaffold 双向 / 编号统一）—— 撞 C1/C2/粒度失配。
- **`adr/0013` 机械回写骨架**（起手锚 / best-effort 三级 / 生成侧结构化强制）—— 整体弃。
- 保留内核：真相源 = 归档实况盘面——但用于**盘面读取生成草稿**（供人确认），非脚本机械镜像。

## Considered Options

- **最小核回填助手（选中）**：盘面 → 草稿 → 人确认，判断留人；弃全部机械回写骨架；消 C1（不写 change 产物）/C2（不机械聚合 enum）/粒度失配/H4（不迁移）；ROI 配得上「降低手工回填摩擦」。
- **归属镜像 + scaffold 双向（`adr/0014`，弃）**：C1 源码短路 + C2 enum 不可实现 + defer 重现原痛点。
- **lint-only + done create-or-update 机械镜像（部分弃）**：去 scaffold 可消 C1，但**仍机械镜像 tasks→roadmap**——仍撞 C2（阶段状态判断）+ 完成判定含验收标准判断（现状实证），机械镜像仍越界判断。
- **完全不做 / 纯人工（现状，弃）**：不降摩擦，痛点不解。

## Consequences

- design/proposal/specs/tasks 重写为最小核 `[spec-review-amendment]`。scope 从 6 件砍到：done 收尾提示步 + 回填草稿生成（盘面读 + 骨架）+ 关联声明约定 +（可选）轻脚本。**无 scaffold / 无 enum 聚合 / 无迁移 / 无生成侧模板大改**。
- roadmap/tasks 保**现状散文格式**（人读），助手适配、不要求机读化。
- CONTEXT：新术语「回填降摩擦助手」「完成判定的盘面-判断切分」。
- **元教训**：两轮 grill + 两轮 spec-review 反复揭穿「想把记录维护过度机械化」；现状实证锚定「完成判定本质含判断」——**目标态论证的正确用法是锚现状实践揭示的判断/机械真实边界，而非一厢情愿把判断也机械化**（这是对 `adr/0011` 目标态论证的一次边界校准：目标态 producer 契约能机械保证的是「盘面搬运」，不是「判断」）。
