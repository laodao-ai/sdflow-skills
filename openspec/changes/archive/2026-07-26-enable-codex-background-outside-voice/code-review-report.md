---
ship-gate:
  code_review: pass
  reviewed_sha: 3cc89c129a174ebc1778c3cfca314073da15ec7d
---

## code-review 报告 — enable-codex-background-outside-voice

### 命中范围

- **diff base**：`a1aac9d`（`merge-base main HEAD`）→ HEAD。66 文件 / +26922 −119。
- **栈**：Python + POSIX shell + Markdown 编排指令。
- **清单**：`code-review-base.md` CR-01~09。
  🔴 **领域清单未覆盖（诚实降级，不是「全覆盖通过」）**：`proposal.md` 明确声明不命中
  backend / frontend / embedded，而 `code-checklists/domains/` 下只有 `backend*.md` /
  `embedded*.md` ⇒ 无对应领域 delta 可注入，领域镜只以通用 base + Fowler smell 为标准源。
- **TG 判定**（四件套未声明 TG，由本层判定）：TG-08 外部依赖（`claude` / `codex` CLI，
  且 `--bg --exec` 是 research preview）· TG-09 多状态生命周期（job 状态机）·
  TG-16 NFR（5s dispatch / 900s timeout / 30s grace / 300s 旧天花板）· TG-17 信任边界
  （入境出境 secret scan、read-fence 四旗、stderr 不入 tracked）· TG-26 并发共享可变状态
  （双站点并发 + 跨 shell 共享 sidecar）。**五条全属 HR-TG** ⇒ 已单开领域 cross-model。
- **`trivial_shape`**：`NOT_EXEMPT`（`non-doc-markdown:AGENTS.md`）⇒ 照常 fan-out。
- **本轮 roster**：broad（Step1）· domain · adversarial ×3（并发竞态 / 资源泄漏 / 错误路径+信任边界）·
  history · outside-voice ×2 站点。

<!-- sdflow:step1-broad-review v1 mode="native" -->

> **Step1 的执行边界（MUST NOT 读成「gstack /review 全量跑过了」）**：gstack `/review` 的指令
> 原生进主 session 执行（非子代理模拟），本轮实际跑的是它的 **scope-drift + 计划完成度审计 +
> checklist critical pass**。**未跑**它自带的 specialist 军团与 Codex structured review：前者与
> sdflow Step2 的 domain/adversarial/history roster 是同维度重复，后者与本层的 outside-voice
> 同为跨模型第二意见；且其 AskUserQuestion 门与「阶段三无人类门」冲突。这是**有意裁剪**，
> 裁掉的维度由本层自有 roster 覆盖，不是静默跳过。

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

<!-- sdflow:hr-tg v1 hit="TG-08,TG-09,TG-16,TG-17,TG-26" declared="TG-08,TG-09,TG-16,TG-17,TG-26" evidence="新增 outside-voice-job.py 用 claude --bg --exec(research preview) 托管跨 shell worker，双站点并发读写同组 sidecar 派生状态机，并把 context 交给外部模型 runner，受 secret scan + read-fence 四旗约束" -->

### Scope check：**DRIFT DETECTED**（信息性，不阻断）

- **Intent**：给 outside-voice 加后台作业能力，消除 Codex 宿主 300 秒同步天花板。
- **Delivered**：与 intent 一致的六张票（helper / 终态派生 / 恢复清理 / runner 隔离 /
  两 SKILL 调度 + 安装 / efficacy 检查器）。
- **Drift（3 个提交，落在设计门批准之后、plan 落盘之前）**：
  - `de549f4` `feat(sdflow-issues): 新增历史问题数据迁移工具` —— `migrate_legacy.py`(+384)
    + 测试(+198) + `sdflow-issues/SKILL.md`(+20)。**`openspec/` 下查无对应 change/spec**
    （`grep -rl migrate_legacy openspec/` 零命中）⇒ 合并即把一个未走 change 流程的功能带上 main。
  - `2a587a1` / `edf2ff9` 两份调研文档（`docs/sdflow-context-policy.md` +288、
    `docs/subagent-definitions-plan.md` +328），除自引用外无消费者。
  - **不是 drift 的**：`impl-reports/*.diff` 评审交接包有先例（归档区 56 份），属既定约定。
- **完成度**：`superpowers-plan.md` Task 1–5 复选框全勾、Task 6 勾 3/6（1/2/3 为
  efficacy 动作项，人拍板 A 降级后**刻意留白**）。`tasks.md` 19 项全未勾 ——
  **这是设计如此**（实现期勾会触发设计门失鲜 `REFUSE_START`，复选框在 done 的 archive 阶段勾），
  非缺口。

### Findings（置信 ≥80）

| # | 严重度 | 位置 | 问题 | 处置 |
|---|---|---|---|---|
| F1 | 高 | `outside-voice-job.py:748` | `communicate()` 只捕 `TimeoutExpired`。`text=True` 默认 `errors="strict"`，管道 `OSError` / 解码异常一路逃出 `cmd_dispatch` ⇒ ① reservation 不释放（该 site **永久占坑**，后续 dispatch 全被 duplicate-site 挡掉）② 已 Popen 的进程树不回收（孤儿计费）③ 调用方拿不到那行带 `fallback_allowed` 的 JSON，「5 秒级诚实降级」退化成哑崩溃 | **已修** `[impl-review-fix]` |
| F2 | 中 | `outside-voice-job.py:1892 / 1328 / 1929 / 2018` | **自指指引**：四处拒绝分支输出的 orphan warning 都写「先跑 `cleanup --cancel`」，而其中三处**就是 `cleanup` 自己的拒绝分支**——照做只会原地拿回同一句话。拒绝本身是对的（删 reserve = 把「可能已花一次」变成「确定花两次」），**说谎的是指引** | **已修**（面治扫全四处） |
| F3 | 中 | `outside-voice-job.py:1925` | 终态 `rm` 之后 roster 句柄就没了，而 `subtree` 探到 `alive`/`unverifiable` 时仍报一句干净的「已移除」、无警告 ⇒ 未证退出的子树从此**既没人管也没人看得见**。（计费论证成立、闸门不动，缺的是警告） | **已修** |
| F4 | 低 | 分支范围 | 上述 scope drift：`migrate_legacy.py` 无对应 change/spec 即随本分支上 main | 已如实记录，处置属人 |

### 已裁掉（反静默压制，可审计）

- **X1｜伪造 / 损坏的 collected witness 可绕过终态证据假绿**（hr-tg voice，high）——**证伪**。
  `load_collected` 已绑定 `schema_version`/`site`/`run_id`/`attempt_nonce` 四项到本次 attempt；
  写入是 temp+rename 原子的；而**能写 `.collected.json` 的只有本机用户自己**——runner 被四旗
  限定为只读工具集（`Read,Grep,Glob`，无 Write/Bash），写不了任何文件。「job 仍在跑却已有匹配
  witness」需要有人手写该文件。对本机自己人再加一层重校验属低概率×高成本，按通则④不做。
- **X2｜identity 四项核验「退化」为 job id 唯一 + 无矛盾**（hr-tg voice，high）——**描述属实，
  但结论反了**。`verify_identity` 的 docstring 写明依据：真机上 `state="done"` 的 roster 条目
  **没有 `name` 字段**（Task 1 实测），四项都要求肯定证据的话正常完成的 job 永远 rm 不掉，
  那是把「不猜目标」写成「什么也别做」。且 `canonical-id` **必须**肯定核验、其余三项矛盾即
  一票否决。⇒ **实现是对的，spec 措辞过时** → 转 T229（archive delta 同步）。
- **X3｜dispatch 的 5 秒不是端到端**（hr-tg voice，medium）——属实，但是**有意且写明理由的**
  设计（核验用独立 grace，不与 dispatch 抢同一份预算；`duration` 覆盖到核验结束，正是为了让
  拿它跟 deadline 比的断言不恒真）。⇒ spec 措辞问题 → 并入 T229。
- **X4｜置信 <80 滤除项**（一行带过，可审计）：`_py` 解释器装配顺序（历史镜与对抗镜 C 独立复核
  均确认正确）· pgid 复用误判（代码已声明为 fail-closed 的已知权衡）· reserve→job.json 崩溃窗口
  （`classify_existing_reserve` 显式 `unknown-cost`，设计内）· `outside-voice.sh` 全局副本仍是
  **1.4.3** 而分支已升 **1.5.0**（运行 checkout 未重跑 `setup.sh`，属已知发布窗口，非缺陷；
  主版本仍 1.x 故本轮继续）。

### 修复 / defer 台账

**自动修 3 项** `[impl-review-fix]` + **诚实边界声明 1 处**，共 `+198 −9`（`3cc89c1`）：

1. `cmd_dispatch`：新增非 timeout 异常出口（kill 进程树 → 收进同一判定 → 按 nonce 命中决定
   `unknown-cost` 还是 release+fallback）；并给 `Popen` 加 `encoding="utf-8", errors="replace"`
   从根因上消掉解码那一类。
2. 新增 `MANUAL_ONLY_WARNING_TEMPLATE`，替换四处自指指引，给**真正可执行**的人工步骤
   （读 sidecar 取 nonce/pid → `claude agents --all --json` 定位 → 手动 stop/rm → 手删 reserve）。
3. 终态 `rm` 前若 `subtree != exited`，输出 orphan warning（闸门与 fallback 决策不变）。
4. `check_codex_efficacy_evidence.py` docstring 的「诚实边界」节写死：**`check` 不是防伪门**。

**新增 5 条锚，逐条已证非恒真**（scratchpad 副本上定点回退 → 必红）：

| 锚 | 变异 | 结果 |
|---|---|---|
| `test_dispatch_stays_honest_when_reading_the_spawn_output_blows_up` | 删掉新 `except` 分支 | 红（`OSError` 逃出） |
| `test_cleanup_warns_when_it_rms_a_terminal_job_whose_subtree_exit_is_unproven` | 删掉 `subtree != SUBTREE_EXITED` 分支 | 红 |
| `test_cleanup_never_tells_the_operator_to_re_run_the_command_that_just_refused` | 四处模板回退 | 红 |
| `test_bare_reservation_cleanup_warning_gives_manual_steps_not_a_dead_end` | 同上 | 红 |
| `test_reserved_status_warning_gives_manual_steps_not_a_dead_end` | 同上 | 红 |

> 第 3 条第一次写出来时**被自己的解释性注释满足**（注释里提了那个常量名）——已改成先剥注释
> 再判。「门被自己的注释满足」是恒真锚的一种成因，记在此处备查。

**defer 7 项**（均带 `"change"` 字段）：

| ID | 池 | 内容 | 为什么不当场修 |
|---|---|---|---|
| **B21** | bug | `acquire_reservation` slot-limit TOCTOU：三方并发全部自我回退，30 轮实测 12 轮 0 存活预留 | 目标态 `declared-sites` 公式结构上**至多 2 站点**，2 站点下 `len>2` 恒假、走不到该分支。判据是**可达性**（目标态 producer 不产出该形态），不是「现状少见」 |
| **B22** | bug | `migrate_legacy.py` 迁移写入与 reindex 不在同一锁事务内 | **不属本 change 范围**（来自同分支的独立提交），处理时应另开 change |
| **T226** | todo | efficacy 检查器 `check` 补 `--run-dir` 交叉核验 | 见下方专节 |
| **T227** | todo | worker 无信号转发 + cleanup 从不 kill `runner_pid` | 实现**符合 OVBG-05 原文**（spec 只要求核验+告警，未要求 MUST kill）⇒ 自行补上是加宽（通则③）。且前提未验：`claude --bg` 的 stop 走 per-pid 还是 killpg 没核实过，走 killpg 则整条不成立 |
| **T228** | todo | `secret_scan` 被 NUL 切断 + 二进制命中时 stderr 措辞 | **既有代码**、本 change 未改这些行。且要真泄漏需「模型蓄意插控制字符 + 接收方主动剥除」，而正则扫描器对蓄意混淆本就一概无效——是该类防线的固有边界 |
| **T229** | todo | 两处 spec 措辞被实现证伪（X2/X3）+ Task 4 遗留的「四旗」 | 实现期 MUST NOT 改 `openspec/specs/`（触发设计门失鲜）⇒ **archive 阶段必做项** |
| **T230** | todo | 出境 `.stdout` 无大小上限 | 影响低，且 `.outside-voice/` 已 gitignore 不入库 |

#### 🔴 T226 单列：efficacy 检查器**不是防伪门**

**两个独立来源同时命中**（对抗镜 C 实跑复现 + code-voice 跨模型），是本轮置信最高的一条：
`verify()` 只读传入的那一个 JSON，**从不打开 `<site>.collected.json`** 去对 `job_id` /
`attempt_nonce` / `stdout_sha256`；`layer`/`repo`/`change` 纯来自 CLI，`run_id` 只取首个 witness
且不在 `SITE_KEYS` 内。⇒ **一份全手工伪造的 evidence.json 能让三条门全过、exit 0**（已实跑）。
它挡的是「手抄失误」，不是「自报为真」——而它存在的理由（adr/0018）恰恰是后者。这是本仓反复
出现的失效模式：**外壳看起来机械（sha256 / schema / 单调时序），捕获环节却由被监管方把持。**

**没有当场修的判据（T10 ①，客观可核）**：该检查器**今天不 gate 任何东西**——Task 6 已按人
拍板 A 降级，T162 保留 OPEN、`design.md` 的「Codex efficacy=0」一字未改、**从未产出过任何
evidence.json**。而它要绑定的 run-dir 真证物，其产生恰恰就是被额度封锁的那件事。现在修，
新绑定只能对着**我自己造的 fixture** 验（等于用被测对象自身的假设去验被测对象），且不会再有
评审轮兜底。⇒ **fold 进 T225**（额度恢复后跑真实 efficacy 的那张票），届时对真证物验。
当前无假绿风险，且已在文件 docstring 写死边界声明防后人误读。

### 度量锚（lens-metric，`metrics.enabled=true`）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="5" 采纳="0" 裁掉="0" defer="5" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="3" 采纳="1" 裁掉="0" defer="2" 独立="1" sev="致0/高0/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="1" 裁掉="1" defer="2" 独立="1" sev="致0/高0/中1/低0" -->

> 历史镜 `findings=0` 是真值：它逐条核了三类历史坑（共享字符串 grep 漂移 · 一次性 migration 门
> 归档后失效 · 协议漂移），并复核两个归档 change 的旧评审意见（`add-codex-host-support` C2′、
> `async-outside-voice` C2/C3/C4）均已在 Task 1–5 修复，未重蹈。

### outside-voice（跨模型第二意见 —— 本轮**真跑通了**）

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="true" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="4" truncated="false" -->

两站点均 **exit 0**（退出码取自 runner 写不了的 `.rc` sidecar，非 stdout），`host=claude` ×
`runner=codex` × `reason_code=ok` ⇒ 矩阵判**跨模型**，findings 免同族置信滤、直通对抗裁决。
run 目录 `.outside-voice/20260726T003415Z-tCPxKn/`（gitignored）。

> **`code-voice` 的 context 偏离（T10 ①，客观判据，MUST NOT 读成「按规则跑的」）**：规则写
> 「site=code-voice → 全量 diff」。实测全量 **1.84 MB**，而 helper 是**保头尾各 100KB** 截断
> ⇒ 按 git 路径序，核心的 `outside-voice-job.py`（2369 行，位于中段）会被**整段丢弃**，
> 拿到的 200KB 几乎全是 impl-reports 与 `*-review-package.diff`。∴ 收敛到**生产代码面**
> （helper / 脚本 / 两 SKILL / `setup.sh`，300 KB）。排除项是 `impl-reports/*.md` 与
> `*-review-package.diff`——后者是**本 diff 自身的逐票旧快照副本**，喂进去等于让 voice 复审
> 已被取代的代码。即便如此仍触发截断（丢 95518 字节，`truncated="true"`）。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☑ defer 残差已入 buglist / todolist：**B21 · B22 · T226 · T227 · T228 · T229 · T230**（hand-off 会引用）
- 🔴 **交给 `/sdflow-done` 的 archive 阶段必做**：T229 的三处 spec 措辞订正
  （OVBG-01 的 5 秒口径 · OVBG-05 的四项核验判据 · 主 spec 仍写「四旗」）。

**门禁实跑**：全量 `2634 passed, 10 skipped, 3 xfailed`（新增 5 条锚）·
`check_async_branch_parity.py` ✅ 2 处逐字节一致 · `sync_principles.py --check` ✅ 18 个投放面 ·
`git diff --check` 干净 · `openspec validate --strict` valid。
