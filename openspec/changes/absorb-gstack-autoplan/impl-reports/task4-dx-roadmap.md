# Task 4: DX 吸收与 roadmap 侧重写 — 实现报告

## 范围（对齐 task4-brief.md 六项）

1. `trigger-catalog.md` 新增 TG-28
2. 新建 `spec-checklists/domains/devex.md`（可判表式）
3. `spec-checklists/domains/frontend.md` 增补 litmus/AI-slop 精华 R 项
4. `sdflow-roadmap/SKILL.md` review 节重写（判定点②删、恒跑双镜、sync voice）
5. Roadmap sync-only outside voice 接入
6. `openspec/INDEX.md` 同步

## 变更清单

| 文件 | 改动 |
|---|---|
| `sdflow-init/assets/workflow/trigger-catalog.md` | 新增 TG-28 行（A. 技术栈组，紧随 TG-27），领域列 `devex`（**spec-review-only**，同 TG-27 反向先例）。**HR-TG 判定「否」**——不入 HR-TG 成员行（design DD6 明确判据：不满足「运行期爆炸/数据损坏/安全泄漏」）。 |
| `sdflow-init/assets/workflow/spec-checklists/domains/devex.md`（新建） | DX-01~DX-05 五条，六列可判表式（ID/规则/触发条件/必需文本证据/PASS/FAIL/N.A）：TTHW 分档（附文本推导规则）、错误信息三件套、命名可猜性/默认值/渐进式披露、升级路径、Claude Code Skill DX 清单（sdflow 新作，非蒸馏，design DD6 M16 已订正出处声明）。头注声明收录判据（对着 design/specs 文本可判真伪，不收依赖外部工具/竞品/`~/.gstack/` 状态的过程方法论）。 |
| `sdflow-init/assets/workflow/spec-checklists/domains/frontend.md` | 新增 FE-04（首屏可辨识+克制装饰，litmus 精华）、FE-05（AI-slop 视觉黑名单浓缩）。 |
| `sdflow-init/assets/workflow/spec-checklists/README.md` | 领域注册表新增 `domains/devex.md` 行（步骤4「登记一行」，同 llm.md 先例；未动架构 ASCII 图——llm.md 加入时同样未动，先例一致）。 |
| `sdflow-roadmap/SKILL.md` | review 节整体重写：见下方「review 节重写细节」。 |
| `openspec/INDEX.md` + `sdflow-init/assets/snippets/index-section.md` | 移除 `outside-voice-reuse-guard` capability 行（含其"工具行"描述——同一行，非两行）；新增「设计审规则集」prose 行（含 `devex`，对称既有 code-checklists 行）；`trigger-catalog` 行的 TG 计数由过时的 `TG-01~24` 更正为 `TG-01~28`；`roadmap-planning` 行描述同步新 review 机制（恒跑双镜+sync voice+处置四态，删除已作废的"按商业化信号分档(plan-eng-review/autoplan)"表述）。 |

## review 节重写细节（sdflow-roadmap/SKILL.md）

- **判定留痕总则**：三判定点→两判定点（①三态路由 / ②收尾 checklist），原②（review 按商业化信号分档）已退役，显式记一句说明为何不再占用编号。
- **工作流概览图**：review 行改为「恒跑 strategy/plan-eng 双镜 + sync-only outside voice（不分档）」；收尾 checklist 判定点号由③改②。
- **`## review：恒跑 strategy/plan-eng 双镜 + sync-only outside voice`**（原标题「按商业化信号分档（判定点②）」）：
  - 删除「分档判据」子节（含 `/plan-eng-review` 默认单审 / `/autoplan` 三连的分档逻辑）。
  - 新增「双镜派发（恒跑，不分档）」子节：resolve-models 一次（取 `$SDFLOW_HOST`/`$SDFLOW_TIER_MID`/`$SDFLOW_VOICE_RUNNER`/`$SDFLOW_VOICE_MODEL`，fail-loud 硬停 + 空值/unknown 分家）→ 双镜 host-agnostic 恒跑 → voice 与双镜重叠启动（不串行）。
  - 「把三件套作为"整体 plan"告知双镜」：原「告诉 review skill」改为「告知双镜」，措辞与调用对象同步更新，存活验收语义不变。
  - 新增「sync-only outside voice（site=`roadmap-voice`）」子节：context（design.md Decisions + roadmap.md 全文，task-log 有意排除）、run 目录（`openspec/roadmaps/{name}/.outside-voice/<run-id>/`）、命令形态（内层 `--timeout 300`、外层 ≥330000ms）、⑦ 表映射引用（不转述，单一源 = `outside-voice.sh` 头注释 + `sdflow-spec-review/SKILL.md`）、失败 fallback（带编排方时间预算）、不落 `anchor_lint`/`lens-metric` 锚。**MUST NOT 移植 async 段**——本节未复制 dispatch manifest / collect barrier / `sdflow:async-branch` 等值门任何内容。
  - 「跳过 review」子节保留（跳过仍需人类显式授权，`review-waived` 语义不变）；措辞去掉过期的「判定点②」编号引用。
  - 「review 依赖不可用...」→「双镜派发失败 / voice 失败时不静默，且阻塞收尾」：失败来源改述为「双镜派发失败」或「voice 与其同族 fallback 均失败」，`未审待恢复` 阻塞收尾语义原样保留。
  - 「review 结果如何处理」：新增第四态 🔸 未审待恢复（包级状态标记，区别于逐条 finding 的✅/❌/⏭三态）；新增 voice 留痕规则（`runner=`/`reason_code=` 一行，同族降级 MUST 含"降级"字样）。
- 全文其余散落引用同步清理：
  - 商业化信号词表处的"（与 review 分档共用同一张表）"括注删除，改为末尾说明该表仅供三态路由/七维裁剪使用。
  - 判定点①「操作者覆盖」段删除"与 review 分档的显式覆盖先例同构"的失效类比。
  - 「补细时机与重判分档」标题与正文改为「补细时机与重新触发 review」，不再提"重判分档"（无档可判）。
  - 收尾 checklist 标题的判定点号③→②。
  - 陷阱 6 的表现/正确描述去掉 `/plan-eng-review`/`/autoplan` 具名引用，改述新 review 机制。

## 验收自证

- `grep -n "autoplan\|gstack" sdflow-roadmap/SKILL.md sdflow-spec-review/SKILL.md` → 零命中。
- `grep -n "plan-eng-review\b\|/autoplan"` sdflow-roadmap/SKILL.md → 零命中（`plan-eng` 镜名本身保留，属新内部镜名非外部 skill 调用）。
- `python3 hack/sync_principles.py --check` → `✅ 22 个投放面全部与真相源一致`（未触碰 `sdflow:principles`/`sdflow:broad-mirror-def` 托管块内容）。
- 全仓 `/usr/bin/python3 -m pytest -q`：**2487 passed, 10 skipped, 1 failed**（348.76s）。
  - 失败用例：`sdflow-init/tests/test_outside_voice_job.py::test_supervisor_transcript_and_state_carry_no_context_stdout_or_secret`——该用例受 `@pytest.mark.skipif(_REAL_CLAUDE_SKIP ...)` 门控，是真跑 `claude --bg --exec` + 轮询 `claude logs` 的**真实环境集成测试**（对照组 canary 未出现在 `claude logs` 输出里）。本票改动**零 Python 代码**，未触碰 `outside_voice_job.py`/`outside-voice.sh` 或任何后台 job 机制；该失败与本环境下 `claude` CLI 后台日志的实时可用性有关（本机 timing/CLI 版本状态），与本票内容无因果关系。已核实：该测试文件与函数均非本票改动范围。
- `openspec/INDEX.md` 与 `sdflow-init/assets/snippets/index-section.md` 表格结构核对：无孤行/断表。

## 已知边角（未在本票范围内处理，供后续/主审知悉）

- **`openspec/specs/outside-voice-reuse-guard/spec.md`（主 specs 树）尚未删除**：task4-brief 第 6 条明确只要求 INDEX.md 同步（移除该 capability 行），实际脚本 `outside_voice_guard.py` 与该 capability 的正式 REMOVED 落地是任务组 3（守卫脚本退役，独立票，Blocked-by 任务组 1/2）的范围。当前状态是 INDEX 已不再列出该行、但源文件与主 specs 树条目仍在——本 change 归档前任务组 3 完成后即消解，不构成本票遗留。
- **Codex 宿主下 roadmap 双镜的 `spawn_agent` 授权边界**：`CLAUDE.md`「Codex 子代理授权」段当前仅显式授权 `sdflow-spec-review`/`sdflow-code-review`/`sdflow-implement` 三处 fan-out；design DD7/DD8 与 `roadmap-planning` spec 均未提及扩展该授权范围给 `sdflow-roadmap`。本票按最小改动原则未触碰该授权段——roadmap 双镜派发在 `$SDFLOW_HOST=codex` 下是否需要额外显式授权是设计层遗留的空白点（不属 task4-brief 列出的六项范围），未自行扩权，如实记录供后续决策。
