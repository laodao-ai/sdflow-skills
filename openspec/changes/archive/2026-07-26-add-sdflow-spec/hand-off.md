# hand-off — add-sdflow-spec

> 产出于 verify 之后、archive 之前。verify 结论：**PASS**（`verify-report.md`，`reviewed_sha=3a80b17`）。
> 本文件随归档进 `openspec/changes/archive/`，作**异步人类再入口 + 下个 change 种子**。

---

## ✅ 完成了什么

> 每条已复核锚点存在性（测试名 / 文件:行 / commit 真的在），**未直接搬运 verify 的 ✅**。

| 交付 | 锚点 |
|---|---|
| **`sdflow-spec` skill 本体上线** —— 三相位管线（澄清 A → 拷问 B → 生成 C）、相位状态机与重入探测、纪要身份核验（四判含 `decision_hash` 重算）、强制阅读清单、「存在态 vs 合格态」分离核验、降级阶梯与三要素诊断、出口序列原样贴、相位 checkpoint | `sdflow-spec/SKILL.md`（600 行，`disable-model-invocation: true`）+ `sdflow-spec/references/` ×3；commit `210298a` |
| **两道会红的机械门** —— 决策纪要必填小节非空；`validate --strict` 的「存在态 ≠ 合格态」正面证明 + 覆盖边界钉子 | `hack/tests/test_decision_memo_gate.py`（19 例）；`::test_status_says_done_while_validate_says_red`、`::test_validate_strict_only_covers_delta_specs` |
| **canonical 七处同步，阶段一入口不再分叉** —— 流水线分支 A/B、G1 具名例外（两处载体各自成立）、生成物重生成、既有 Requirement 声明共存路由、托管块条款显式处置、FF-0 弱判据改三分支 | `hack/tests/test_canonical_entry_sync.py`（30 例，逐处锚 + 变异回验）；commit `2ab6fd7` |
| **FF-0 三分支判定（含全局 hook）** —— 保护分支（含探测到的默认分支）建 / 本 change 分支跳过 / 其它 feature 分支 halt；逃生口 = 一次性哨兵 + 双边 TTL；deny 文案两步化且经 `shlex.quote` | `sdflow-init/assets/hooks/ff0-branch-guard.py`；`sdflow-init/tests/test_ff0_branch_guard.py`（25 例） |
| **四入口选择规则双落点 + sunset 条件落定** —— 人读侧（`CLAUDE.md`/`AGENTS.md` 非托管区，含逐字相等守卫）与 AI 读侧（canonical 分支）各一份；sunset 三档阈值 + 起算点 + 「未到期 ≠ 未达标」显式区分 | `CLAUDE.md:215-231`；`test_canonical_entry_sync.py::test_two_human_carriers_are_verbatim_identical` |
| **阶段一端到端验收** —— dogfood（真实非玩具需求，A→B→C 全程）+ **六种故障注入固化为 pytest**（19 例，锚强度逐条分级）+ 冷读抽检 | `hack/tests/test_sdflow_spec_failure_modes.py`；`impl-reports/task3-stage1-acceptance*.md` |
| **retro 归因修复** —— `map_stage` 整串无命中时回退 tail 匹配 + token 边界；unknown 桶墙钟占比 **55% → 18%**（≈170 hr 被正确归因） | `sdflow-retro/scripts/retro_report.py`；`test_retro_report.py::test_map_stage_longest_prefix`、`::test_every_skill_slug_is_classifiable` |
| **三个 agent 定义 + 全仓首个 `setup.sh` 测试** —— `install_agents()` 新写（所有权守卫位置无关、installer-owned manifest）、`AGENT_TARGETS` glob 投放面、S1~S5 五面处置 | `sdflow-spec/agents/` ×3；`hack/tests/test_install_agents.py`、`test_sdflow_spec_agents.py`；commit `b4595b5` |
| **GO/NO-GO 派发实测门 = GO** —— fresh 进程派 `subagent_type: sdflow-local-researcher`，`WebSearch` **工具不存在**（否定式硬证据，通用 fallback 工具面为 `*`）；同轮证伪 `tools` 作用域参数不生效 | `impl-reports/task4-agents-step2.md` |
| **阶段二 A/B 三路实测（原始日志可第三方复算）** | `impl-reports/task5-logs/`（74 份 JSON + harness + prompts + README 复算方法） |
| **回滚演练正反两向** —— 正序 0 悬空 / 错序留 3 条悬空软链；并当场捞出「`install_agents()` 源目录消失时早退 ⇒ 连孤儿清理都不跑」的真洞 | `impl-reports/task6-stage3-conditional.md`；`test_install_agents.py` 新增格 |
| **代码审 7 条 findings 全修** —— 含出境安全门 fail-open、全局 hook 绕过口、跨 checkout 废弃定义残留、S4 祖先 symlink 逃逸、`setup.sh` 并发 `set -e` 中止 | `code-review-report.md`；commit `a9e62d4`（12 处定点变异「期望红 ⊆ 实际红」） |

**机械层终态**：仓根全量 `2795 passed / 11 skipped / 3 xfailed / 0 failed`；`bash setup.sh` rc=0；`sync_principles --check` 22 面一致。

---

## ⏳ 未完成 / 延后

> 本 change 新增的未分诊项已由 `issues.py sweep --change add-sdflow-spec` 归入**批次 `add-sdflow-spec`**
> （11 项：T232–T242），见 `openspec/issues/batches.md` 与 `openspec/issues/INDEX.md`。以下按性质分组。

### 🔴 A 组 · **archive 阶段必做**（spec 文本与实测不符，实现期不能改四件套故后延）

| ID | 内容 |
|---|---|
| **T232** | SA-05 Scenario 与 `design.md` 失败模式表逐字点名 **design.md**：「`status` 报 done 但 `validate --strict` 不过」—— 对 design.md **恒假**。CLI 1.5.0 的 `validate --strict` 只跑 `validateChangeDeltaSpecs`、**只读 `specs/*/spec.md`**（`proposal.md` 整份删掉仍报 valid，三方独立复现）。措辞须改成与 CLI 实际覆盖面一致 |
| **T238** | SA-07 写「派发时 `model` 参数 SHALL 填该轮解析出的**具体模型 id**」—— 实测 Agent 工具的 `model` 是**枚举** `sonnet\|opus\|haiku\|fable`，填完整版本化 id 被 `InputValidationError` 当场拒。SKILL.md 侧已是正确措辞，spec 侧滞后 |
| **T240** | `design.md` Migration Plan 的回滚第①步写「在仍运行新版 installer 时先跑 **uninstall 分支**移除 agents」—— `setup.sh` 里**根本没有 uninstall 分支**（全文零命中）。须校正为实际可执行的动作 |
| **T241** | `tasks.md` 的**阶段三验收门只有 ✅ 分支、无 ❌/回退分支** ⇒ 回退形态下「可进 `/sdflow-done`」在票面上无书面出处。须补该分支 |

### 🟡 B 组 · 结论性事项（**需人拍板 / 知情**）

1. **🔴 阶段二验收门判「回退到阶段一薄编排」** —— 外派现为**未启用资产**（三个 agent 定义保留、SKILL.md 已标「当前未启用」）。
   依据（N=1，非统计显著；原始日志已归档可复算）：

   | 指标 | legacy | thin | subagent |
   |---|---:|---:|---:|
   | 总美元 | $14.86 | **$9.06** | **$11.68** |
   | 总 token | 15.20M | **8.81M** | **12.57M** |
   | 冷审 Important findings | 1 | **0** | 1 |
   | 人工返工量 | 3 | **2** | 3 |

   **质量轴独立不达标**：subagent 路的 `design.md` 把最承重的那条约束（skill 独立分发 ⇒ 只能 build-time 内联）
   连同被砍候选与具体反例**整条丢失**——纪要分节结构被 writer 原样复制成 design 分节结构。thin/legacy 两路都留住了。
   **方法论修正**：`design.md` NFR 的估算只算档位差、**漏算子代理自身 context**——外派确实把主 session 压了 18.9%（省 $1.04），
   但 researcher + writer 自己烧掉 $3.66 ⇒ 净 **+$2.62**。
   ⚠️ 成本幅度**已作废**（两轮中断轮计费不可信），结论降级为「**未观察到 subagent 更便宜**」；门判回退靠的是**质量轴**。

2. **🔴 Task 6 的票级知情偏离（认账权在人）** —— 票面写「Task 5 判回退则本票不执行」，
   编排层裁定其中三项（8.1 分发核验 / 8.3 回滚演练 / 8.4 sunset 判定）在回退下仍该做，**并据此改了 `setup.sh`**。
   净收益为正（8.3 捞出使回滚正序静默失效的真洞），但这是**编排层判断、非票面字面授权**。
   见 `impl-reports/task6-stage3-conditional.md` §0.0。**不认可可 revert 本票的 `setup.sh` 与文档改动。**

3. **T239 · 下游推广未做（`tasks.md` 唯一留空框 8.2）** —— 阶段三条件收敛。
   **真实后果**：七处 canonical 只落源仓，**下游消费项目仍读旧的阶段一入口规则**。何时/由谁/怎么推见该条目。

4. **T237 · FF-0 守卫的文档化 fail-open 是模型可自触发、且不留哨兵审计痕的绕过口**；
   **T235 · FF-0 按 session `cwd` 判仓**（跨仓调用判错仓）。二者互指。
   ⚠️ 修 T235 需解析 `cd`/`-C`/`&&`（**无界语法面，基准 5 禁手搓**）⇒ 只能是诚实边界 + 有界缓解（检测改 cwd 的 token → fail-open 并明写「本次没判」）。

5. **T242 · `sdflow-spec/SKILL.md` 的 ≤600 行门可由重排软换行规避、且无机械覆盖**（唯一出处是 `tasks.md` 一句人跑的 `wc -l`）。本轮实测正好 600 行、在门内。

### ⚪ C 组 · 未核项与残余

- **T233** · `disable-model-invocation` 在 **Codex 宿主**下的语义未核（本仓已有该字段非直觉行为的实测先例）。
- **T234** · 旧编号 T132（spec-review 起手机械核验拷问已收敛信号）**已存在但内容不再准确**，须按四入口现状重列。
- **T236** · 终审「中间态判据」与「纪要不并入 design.md」架构之间的张力（dogfood 实测发现）。
- **诚实边界（verify 报告与 code-review 报告各有一节，此处只点题）**：
  拷问 / 判断质量结构上未经真人验证（全程由 agent 扮演请求方）；`/clear` 无损用 fresh 子代理冷读代替、不等价；
  Windows 分支无机械覆盖（本机 Darwin）；S3/S5 只有指令在场锚；code-voice 的 context 因 1.37MB 全量 diff 远超
  helper 保头尾窗口而**收敛到 121KB 生产面**（测试面 187KB 未进 voice）；Step1 广审是**模拟降级**（`mode="simulated"`）。

### ⚠️ D 组 · **merge 后必须做的环境还原**

`~/.claude/skills/`、`~/.claude/agents/`、`~/.sdflow/workflow` 当前**均指向开发 checkout**（为测试而在 dev 跑过 `setup.sh`，属 adr/0005 记载的知情临时态）。
**merge 后 MUST 在运行 checkout `~/.skills/sdflow-skills` 重跑 `bash setup.sh` 还原**，否则全局 skill/agent/规则都钉在这个开发副本上。
另：`~/.claude/hooks/ff0-branch-guard.py` 已换新（三分支判定，本机所有项目生效）。

---

## ▶ 下一阶段建议

1. **【P0 · 就在 archive 阶段做】** A 组四项（T232 / T238 / T240 / T241）随 delta 同步一并订正 —— 它们是 spec/design/tasks 的**文本与实测不符**，不订正会让下一个读 spec 的人（或 agent）照着错的写。
2. **【P0 · merge 后立刻】** D 组环境还原（运行 checkout 重跑 `setup.sh`）。
3. **【P1 · 建议开一个 change】** **下游推广**（T239）：把七处 canonical 经 `sdflow-init update` 推至消费项目并核验。
   这是本 change 交付价值真正落到下游的最后一公里，**拖越久「人读新入口 / AI 读旧入口」的分叉窗口越长**。
4. **【P1 · 同一个 change 可一起清】** T235 + T237（FF-0 守卫的判仓与 fail-open 绕过口）——
   二者同面、修法都是「有界缓解 + 诚实声明」，**MUST NOT 走 shell 解析**（基准 5）。
5. **【P2】** T233 / T234 / T236 / T242 —— 未核项与轻量残余，可随手清或并入上面任一 change。
6. **【拍板题 · 只有你能定】** 阶段二回退之后，三个 agent 定义是**继续保留为未启用资产**，还是**删除**？
   `tasks.md` 的失败分支写的是「保留或删除」。当前选择是**保留**（它们仍铺在全局 `~/.claude/agents/`，
   排他式 `description` 是指令层而非机械门）。若倾向删除，删源 + 重跑 `setup.sh` 即可（孤儿清理已验证生效）。
