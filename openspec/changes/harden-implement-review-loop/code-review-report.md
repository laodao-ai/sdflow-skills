---
ship-gate:
  code_review: pass
  reviewed_sha: 5587d07d0b388ec4d0a2b4eafcc468365dd00517
---

## code-review 报告 — harden-implement-review-loop

### 命中范围

- **栈**：本仓 `openspec/config.yaml` 明文声明**不命中** `domains/` 的 backend·go / embedded·ml307c·esp32 / frontend 任一领域 ⇒ **领域清单未覆盖（降级已登记）**，标准源退到 `code-review-base.md` 的 CR-01~09 + `CLAUDE.md` 的四条通则与五条基准（重点基准 1 机械化优先、基准 5 无界语法禁手搓）。
- **diff**：`aba5547..HEAD`，75 文件 / +9707 行。可执行逻辑面窄（`ship_gate.py` / `impl_route.py` / `hack/check_tier_resolution_parity.py` / 各 `tests/` / `setup.sh`），其余为指令文本与文档。
- **TG 判定**：`TG-12,TG-14,TG-15,TG-18,TG-19,TG-23,TG-25`；∩ HR-TG = **∅** ⇒ 不开领域专属 cross-model。
- **trivial_shape**：`NOT_EXEMPT`（`non-doc-markdown:AGENTS.md`）⇒ 照常 fan-out。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-12,TG-14,TG-15,TG-18,TG-19,TG-23,TG-25" evidence="改动为工作流指令文本 + 确定性门禁脚本；无 DB schema/API 合约/外部依赖/并发共享可变状态/信任边界与敏感数据/性能可用性 NFR" -->
<!-- sdflow:declared-sites v1 declared="code-voice" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

### Step1 gstack/review（scope-drift + 完成度，主 session 原生执行）

**Scope Check: DRIFT DETECTED（信息性，不阻塞）**

- **Intent**：给 `sdflow-implement` 补档位解析、拆 T10 为两条具名规则、测试范围分层 + 强制收尾票、tickets 轨计划文件改名。
- **Delivered**：与 intent 一致，6 张票全部交付并各过双轴审。
- **漂移**：分支相对 `origin/main` 含 **2 个与本 change 无关的提交**，会随合并一起进 main：
  - `0296ca0 checkpoint(workflow-rules): G1 收窄：撤回「全流程不用 /clear」的过度泛化` —— workflow 规则改动 + `hack/tests/test_canonical_entry_sync.py` 断言同步（45 行）。属独立议题，不在本 change 的 proposal Impact 清单内。
  - `e5426e8 checkpoint(todolist): 记 T256：PreCompact 落盘调研` —— 该提交 subject **自述「挂 main，非本 change」**。
  - **未自动处置**：摘除需重写历史，而 `rebase` 会击穿归档报告的 `reviewed_sha` 审计锚（本仓既有教训）。∴ **如实登记，交 hand-off 让归档记录这两笔搭车**，不做静默合并。
- **完成度**：`tasks.md` §1–§7 逐节对照实现，未见 NOT DONE / PARTIAL；两处**有意的例外**（本 change 自身 plan 保留旧名走 grandfather；`openspec/specs/**` 与 delta 的差异属 delta-at-archive 纪律）已在收尾票报告核实，非缺口。
- **降级声明**：gstack/review 的 specialist army 与 codex 结构化审**未单独再跑**——其覆盖面已由本 skill 自身的四镜 + 跨模型 code-voice 承担，重复跑同一 diff 无边际收益。scope-drift 与完成度审计这两项 sdflow 明令必含的内容**已原生完成**（见上）。

### Findings（置信 ≥80）

| # | 严重度 | 位置 | 问题 | 命中镜 | 处置 |
|---|---|---|---|---|---|
| F1 | **CRITICAL** | `sdflow-ship/scripts/ship_gate.py` `plan_was_renamed()` | 用 `git log --follow` 的**内容相似度**启发式回答「plan 是否被改名」，三种失效模式均有 fixture 实证 | 域镜 + 对抗镜#1（**多镜确认**） | **已修** `[impl-review-fix]` |
| F2 | **CRITICAL** | `sdflow-done/SKILL.md` verify 步 | 用**文件名**判轨，违反 delta 明文「文件名 MUST NOT 参与轨道路由判定」；grandfather 下旧名同样覆盖 tickets 轨 | code-voice（跨模型独家） | **已修** `[impl-review-fix]` |
| F3 | Important | 四个编排 SKILL 的第零步核心段 | `eval "$MODELS_ENV"` 未检其自身退出码；delta 失败清单第②项「输出无法 eval」未实现 | code-voice（跨模型独家） | **已修** `[impl-review-fix]` |
| F4 | Important | `sdflow-implement/SKILL.md` 聚合套件契约 | 允许各层锚不同 SHA，「全部通过」可由不同盘面拼装，与 spec「全部功能票实现完毕**这一刻**」矛盾 | code-voice（跨模型独家） | **已修** `[impl-review-fix]` |
| F5 | Important | `review-loop-breaker` ①档 | 可在**未修复**前提下关闭仍成立的 Critical；D2b 的互斥终态只修了②③档 | code-voice（跨模型独家） | **defer → T259**（需改 delta 措辞，本 change 内改会触发 design 域失鲜） |
| F6 | INFORMATIONAL | Codex 子代理授权段三处 | 当前逐字节一致，但**无任何机械守卫**，漏改一处不会红 | 对抗镜#2 | **defer → T260**（结构性风险，非本 change 引入） |
| F7 | INFORMATIONAL | `sdflow-implement/SKILL.md` · `impl_route.py` docstring | 两处引用 `matt-workflow-integration/superpowers-plan.md` 已死链（该 change 早归档） | 对抗镜#2 | **defer → T261**（预存漂移，归档早于本 change 起点） |

#### F1 详情（本轮最重要的发现）

`--follow` 的重命名检测是**相似度阈值**判定，与「是否发生过 `git mv`」不是同一个问题：

1. **误报 → 永久自锁**：同一 commit 里「删 change A 的 `tickets.md` + 建 change B 的 `tickets.md`」被 git 配对成 `R074`（本 change 强制的统一 ticket 模板让相似度天然过线）⇒ 从未改过名的新文件判 True。错误提示「请改回原文件名」**无原名可改回**，唯一出路是历史重写（本仓禁 `-i`，且击穿 `reviewed_sha`）。
2. **漏报**：改名拆两次提交（先 `git rm`、后新建）—— git 的重命名配对只在单 commit 内做 ⇒ 检不出。
3. **漏报**：`git mv` + 同提交大幅编辑 ⇒ 相似度跌破阈值。天然触发路径：旧名迁新名**正需要**给每个 Task 段补 `R-ID:`/`Blocked-by:`。

**两镜给出的修法互相冲突**（调低阈值 `-M1%` 修模式 3，会让模式 1 更严重）——这本身证伪了启发式路线，正是基准 5 的警号。

**修法（`T10-choice` ①档，有客观判据）**：不再检测「有没有改名」（原因），改为直接检测「危害有没有发生」（结果）——`stray_done_tag_commits()`：本 change 是否有 `checkpoint(<change>:task<N>-…)` 标签落在窗口 `[plan_first_sha, HEAD]` **之外**。精确、非启发式，且覆盖面更宽（任何导致窗口起点错误的成因都被抓，不止改名）。三种模式已用真 git fixture 逐一实测：模式 1 绿（不误报）、模式 2/3 红（检出）。每个用例带 `_old_heuristic_would_flag()` 反算旧判据钉死 fixture 落点，防恒真绿。

### 已裁掉（反静默压制，可审计）

- **X1｜对抗镜#2 对 `sdflow-done` 聚合覆盖条件化判「写法正确」** —— 与 code-voice 的 F2 **直接冲突（TENSION）**。**裁决：采信 code-voice。** 理由：对抗镜#2 核的是「是否条件化了」（确实条件化了），code-voice 核的是「条件用的信号对不对」（用了文件名，而 delta 明文禁止文件名参与轨道路由）。后者是决定性的，且**本 change 自身即反例**（旧名 + tickets marker）。
- **X2｜历史镜判「完全遵守 ✅，无历史冲突」** —— 该结论在**意图层**成立（`plan_first_sha` 继续不用 `--follow` 的纪律确被遵守），但对**机制层**缺陷失明。**不算误报，也不推翻 F1**：两者不矛盾——设计意图对，实现手段错。保留其结论，仅注明其覆盖边界。
- **<80 置信滤除**：本轮无。四镜 findings 均有 `file:line` 或 fixture 实证；code-voice 的 4 条按合法组合矩阵判「跨模型」（`host=claude,runner=codex,reason_code=ok`）⇒ 依 ADR-5/C1 **豁免数值置信滤**，直通对抗裁决。
- **域镜 F2（`plan_task_ids` 重复解析）** —— 纯性能、单次 CLI 判定、文件仅数十行，按基准④不值得专门改动；且 F1 的重构已顺带减少一次 git 调用。一行带过，不单开 todo。

### 修复 / defer 台账

- **自动修 4 项** `[impl-review-fix]`：F1（gate 判据整体替换 + 三模式 fixture 用例）、F2（verify 轨道判定改读 config 键 + frontmatter marker）、F3（四 SKILL byte-locked 段补 `EVAL_RC` 检查）、F4（聚合套件「单一盘面」条款 + done 侧核验 SHA 一致）。
- **面治外溢 1 项**（基准 3）：F3 修复时 `grep` 查出**第五处**同缺陷 `sdflow-spec/SKILL.md` §0.2（精简变体，不在 parity `SITES` 名单、机械门照不到），一并修。
- **defer 3 项**：T259（F5）· T260（F6）· T261（F7），均显式带 `change` 字段。
- **状态变更 1 项**：T257 判 `WONTDO` —— 其标的（`plan_was_renamed` 与 `plan_first_sha` 的重复 git 调用）随该函数被删除而消失，evidence `5587d07`。
- **T10复核**：本轮无「无客观判据」的 ≥2 方案。F1 的方案选择走①档（有客观判据：两镜修法互相冲突 ⇒ 启发式路线被证伪；替换判据可对三种模式逐一实测验证），已按三镜记理由——**系统镜（主）**：消除永久自锁 + 堵住两类漏报，且判据从「一种成因」扩到「危害本身」，可回退（纯函数替换）；**用户镜**：错误提示从不可操作变为可操作；**开发循环镜**：删掉一个函数、净增 4 个测试，心智负担下降。

### 度量锚（lens-metric）

本仓 `openspec/config.yaml` 的 `metrics.enabled: true`（源仓 dogfood 缺省）⇒ 本段落锚。下列各行为 `lens_metric_emit.py --layer code-review --host claude` 的 stdout（exit 0），**未手拼**：

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="3" 采纳="1" 裁掉="0" defer="2" 独立="0" sev="致1/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="0" sev="致1/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="4" 采纳="3" 裁掉="0" defer="1" 独立="3" sev="致1/高2/中0/低0" -->

**读数注记（供 `/sdflow-retro` 聚合，本报告不做复评判断）**：跨模型 `outside-voice` 本轮 `独立=3`，为全 roster 最高；`domain` 与 `adversarial` 的 `独立=0` 并非无贡献——两者**共同**命中 F1 那条 CRITICAL（折叠后归一条、独立数不计入任一方），且各自的 fixture 实证是该 finding 得以成立的证据本体。`history` 本轮 `findings=0`（如实落零锚，非省略）。

> **信任边界**：emitter 只保证「给定输入的确定性归约」；分类正确性、roster 完备性、findings JSON 誊写准确仍是主 session 的信任边界，非机械可验。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

> `mirrors=` 的第三个 token `grounding` 按 `anchor_lint._FANOUT_MIRRORS` 的**固定三 token 词表**借用，仅表示「第三个 fan-out 镜跑了」（本层实为**历史镜**），非声称接地镜；镜的精确身份由各自 lens 记录。

### 本轮的诚实边界

- **code-voice context 收敛（偏离登记）**：全量 diff 为 **1002121 bytes**，远超 outside-voice helper 的 200KB 截断阈值（超阈仅保头尾各 100KB、**中段核心实现整段丢失**）。故 context 收敛为「生产面（脚本/测试/各 SKILL.md/bundle assets/setup.sh）+ 本 change 两份 delta spec」= 193083 bytes，排除 `impl-reports/*.diff`（评审快照，本身即被审 diff 的重复）与四件套/docs。**voice 因此未看到四件套与文档面**——该面由域镜与对抗镜#2 覆盖。
- **能力探针**：`host=claude` 免探，恒 `subagents="available"`；其「机制活但主 session 偷懒自代多镜」的残余无机械守，属语义层。
- **本报告的四镜结论均来自实际派出的独立子代理**，无一为主 session 代写；code-voice 的终态取自 sidecar `code-voice.rc`（内容 `0`），**非从 stdout 推断**。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 todolist（T259 / T260 / T261），hand-off 会引用
- ⚠️ **hand-off MUST 记录 scope drift**：分支携带 `0296ca0`（G1 规则收窄）与 `e5426e8`（T256 记录，自述「挂 main，非本 change」）两笔与本 change 无关的提交，将随合并进入 main
