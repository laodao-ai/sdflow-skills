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

---

## 第三轮 spec-review 精化：切分线重画（Q1–Q5）〔spec-review-amendment〕

第三轮 4 镜 + 广审 + outside-voice **高度收敛**：最小核消掉了 C1/C2 机械回写致命，但残留 **2 致命 + 3 高**，**同一根因 = 「机械搬运/判断」切分线画错位置**。据此精化（方向不变、位置校准）：

- **P-1 时序锚清单收窄（消 C-1 致命）**：草稿在 done 第二步(hand-off) 生成，此刻 archive 路径(第三步，含 `{date}`)与 merge(第五步) **尚不存在**——`盘面即状态` 铁律下它们不是状态、是预测。草稿机械锚**只含步2 已实现事实**：`verify=PASS frontmatter / tasks 完成态 / change 名 / feat 分支`。archive 路径 / merge 状态**留占位「待归档后由人补」**，MUST NOT 当确定性盘面预填（防跨零点日期漂 + merge opt-out 后记一次没发生的 merge）。
- **P-2 定位切分线校准（消 C-2 致命，本轮核心）**：「定位哪些复选框」被误划机械侧——实则拆两半：
  - **机械（助手）**：从 **change 名前缀 `implement-{roadmap}-pN-*` 确定性解析** roadmap+phase（命名约定本已编码双粒度，`adr/0014` 曾弃之、本轮复用）→ 定位到该 **phase 的候选复选框行集**（借现状 `- [ ] {id}` 格式）。
  - **判断（人）**：这个 change 到底勾该 phase 里**哪几行**（phase 跨多 change 时 change→行是判断）+ 算不算满足验收标准。
  - 助手只产**阶段级候选行集**，MUST NOT 产 per-行「建议勾」（那是判断）。这样定位(阶段级)机械、勾哪些判断，与 D-1 盘面-判断切分自洽。
- **P-3 格式分形态 fail-loud（消 C-3 高）**：两存量 roadmap 格式**实测分裂**（mlh 复选框式 `- [ ] 1.A.1` grep 54 / wco 表格 `| ✅` + 散文 grep 0）。助手**探测承载形态**：复选框式→定位阶段候选行；表格/散文式→**不产复选框草稿、fail-loud 告知**「roadmap {name} 非复选框格式、复选框回填请人工」（反静默，非静默退现状）。task-log 完成总结骨架两形态都产。
- **P-4 异步闭环可见（消 C-4 高）**：草稿进 hand-off **且** done 第六步摘要**抬一行**「⚠ roadmap {name} 回填草稿待人确认(见 hand-off)」使其在 merge 时点可见(不只冻结进归档)。design 显式登记残差：**产草稿即止、apply 由人异步、不保证**（经 `/sdflow-ship` 全自动链人被支走时尤然）——诚实登记而非宣称降摩擦却留断头路。MAY 落 todolist 一条，非强制。
- **P-5 detection fail-closed 防自指（消 C-5 高）**：关联检测 MUST **fence-aware**(跳过 code fence/行内 code)+**行锚定**(标记独占一行)+**排除 change 自身讨论区**——本 change 8 处产物字面含 marker 串，朴素子串检测必假阳(MEMORY「gate 子串检测 dogfood 自指坑」同型)。change 名前缀解析(P-2)为主通道时 detection 是兜底，但兜底路径仍须 fence-aware。
- **D1 低风险五条**：C-6 marker 定兜底通道(change 名前缀为主)、`--roadmap` 仅直调 done 覆写、不一致 warn；C-8 pytest 数锚「有测试从 verify-report 取、无则 N/A」不当交付事实预填(纯 Markdown change 无测试)；C-9 坏输入契约**三分**(absent 留人工 / malformed fail-closed 标畸形 / verify≠PASS 不出完成候选)、写成与载体无关的可判定行为规范；C-12 反静默 MAY→**SHOULD**(未声明疑似 roadmap 驱动→hand-off 留一行提示)；C-15 `artifactOutputExists` 定位订正(定义于 `outputs.js`，已改)。

**元教训（续 adr/0011 边界校准）**：切分线的正确位置由**现状实践 + 确定性盘面的真实边界**决定——「定位到阶段」有确定性信号(change 名前缀)故机械，「勾哪几行/算不算完成」无机械判据故留人。前两轮把整个「回写」当机械是过度机械化；本轮把整个「定位」当判断则是矫枉过正——**精确切分线落在「有无确定性信号」上**。
