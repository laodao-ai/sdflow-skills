---
ship-gate:
  design_approved: true
---

# 设计评审报告 — harden-repo-root-fail-closed

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-08" declared="TG-08,TG-18,TG-19,TG-22,TG-23" evidence="repo_root 消费 git 子进程 stdout，本 change 全部内容即重新定义对该外部依赖的信任边界" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="11" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="5" truncated="false" -->

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="7" 采纳="5" 裁掉="2" defer="0" 独立="5" sev="致1/高0/中1/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="10" 采纳="9" 裁掉="1" defer="0" 独立="4" sev="致1/高1/中5/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中3/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="8" 采纳="7" 裁掉="0" defer="1" 独立="5" sev="致3/高2/中1/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="4" 采纳="4" 裁掉="0" defer="0" 独立="3" sev="致2/高2/中0/低0" -->

## 结论（先说）

> **⚠️ 本节及以下正文为评审当时（返修前）的原始结论，保留原文供审计——MUST NOT 据此判断当前状态。
> 返修已三轮完成、设计门已于 2026-07-19 拍板批准，最终状态见文末「拍板记录（设计 HARD-GATE）」。**

**不建议直接进设计 HARD-GATE。** 这份设计的核心机制需要一轮实质性返修，不是补几句话。

原因是一句话：**信任边界画错了位置。** 我只盯着「git 的 stdout 长什么样」，而真正要守的是「这个根是不是 start 所属仓库的根」「用户显式传的 `--root` 可不可信」「同一次调用里两次解析拿到的是不是同一个仓」。四条 critical 全部落在这条线上，且**三条有实测复现**。

`isabs + isdir` 这个判据在返修后**仍然需要**（它挡住了 cwd 相对路径绕过），但它远不是充分条件——它只回答「这是个既存绝对目录」。

---

## 镜头编排

| 层 | 镜 | 数量 | 说明 |
|---|---|---|---|
| Step1 广审 | autoplan（CEO / Eng / DX + codex 跨模型） | 4 声 | Design phase 跳过（UI scope=0） |
| Step2 领域镜 | — | **0** | 本仓不命中 backend·go / embedded / frontend 任一领域清单（CLAUDE.md 明载）。**如实记 0，不虚构领域镜** |
| Step2 对抗镜 | 并发与文件系统语义 / 验证方法论自洽性 | 2 | 高风险（已出 3 critical）但 codex 已覆盖大量对抗面 ⇒ 2 个聚焦未覆盖角度 |
| Step2 接地镜 | 代码事实机械核验 | 1 | 逐条比对四件套里每个 file:line 与数字断言 |
| outside-voice | design-voice（复用）+ hr-tg（实派） | 2 站点 | HR-TG ∩ = {TG-08} 非空 ⇒ 单开领域专属跨模型 |

**能力探针**：`host=claude` ⇒ 免探，`subagents="available"`，无降级。
**outside-voice 复用守卫**：`outside_voice_guard.py` 判 `reason_code=none`（exit 0）⇒ 复用 autoplan 的 11 条 codex findings，不重开 design-voice（避免双 codex）。
**hr-tg 站点**：首次 dispatch 因**调用方错误**失败（`SDFLOW_VOICE_RUNNER` 未 export——harness 每次 Bash 调用是独立 shell，第零步的 resolve-models 输出没在同一条命令内 `eval`）；按 run-id 不可变纪律保留失败证据于 `20260719T082511Z-LK4qhd/`，新建 `20260719T082653Z-hY7E5p/` 重试，exit 0、`OV_TRUNCATED=false`。

---

## 决策登记区

```
┌──────────────────────────────────────────────────────────────────────┐
│ [需拍板] Q1  信任边界重画：ADR-1/ADR-2 需实质返修（4 条 critical 同根）  │
│ [已归属] Q2  镜像手工同步 → T170（下一步工作，已补证据；顺序已拍板）    │
│ [需拍板] Q3  Windows 覆盖：加 CI 泳道 vs 显式登记未验证假设            │
│ [需拍板] Q4  ship_gate.py 第 4 个消费点：纳入 vs 显式论证排除          │
│ [自动决策] D1-D6  见下（高置信，默认采纳）                            │
│ [已裁掉]  X1-X3  reviewer 原始发现 + 裁掉理由（可审计，未静默丢）      │
└──────────────────────────────────────────────────────────────────────┘
```

### 🔴 Q1（需拍板 · 阻塞）— 信任边界重画

四条 critical 是**同一个根因的四个面**，合并处理：

| 面 | 来源 | 实测？ | 内容 |
|---|---|---|---|
| **a. 根身份未验证** | codex X2 + hr-tg V1 | ✅ **实测** | `isabs+isdir` 只证明「是既存绝对目录」。hr-tg voice 实测：`recorder_child_env()` 完整继承 `GIT_DIR`/`GIT_WORK_TREE`，在本仓 cwd 下设置后 `git rev-parse --show-toplevel` 返回 `/private/tmp` ⇒ **判据直接放行，可跨仓覆盖 `openspec/issues`**。不需要假想的企业 git wrapper，两个环境变量就够 |
| **b. 显式 `--root` 零校验** | codex X1 + hr-tg V2 | — | argparse 默认普通字符串。坏 `--root` → `subprocess.run(cwd=start)` 抛 `FileNotFoundError` → `except Exception` 回落 `abspath(start)`（就是那个坏路径）→ 下游 `makedirs` 照样具现。**本 change 做完，最直接的坏根输入仍 fail-open** |
| **c. 跨调用身份漂移** | 对抗镜1 F1 | ✅ **实测** | 同一次 CLI 调用里 `repo_root()` 被解析**两次**（`main()` + 各 `cmd_*`），判据**逐次独立**不问一致性。若两次之间目标失去 `.git`，第二次静默爬升到外层祖先仓库——两次都 rc=0、都是既存绝对目录、双判据全放行。`cmd_batch_add`/`set_status`/`rename` 在第二次解析后**直接 `atomic_write`** ⇒ 把数据写进**外层错误仓库**的 `batches.md` |
| **d. `except Exception` 过宽** | codex X3 + hr-tg V2 | — | ① 它会**吞掉新抛的 ValueError**——按最自然的原位改法，fail-closed 归零；② 它把「cwd 不存在 / 权限错 / 解码错 / 超时」全当「非 git 仓库」 |

**我的推荐（带依据与代价）**：

```
1. 单点解析：root 只在 main() 进程边界解析一次，cmd_* 只接受已验证的 root，
   不再调 repo_root。                          ← 结构性消除 c，同时解决 codex X5
2. 显式输入同等对待：argparse default 改 None，区分「未指定→探测」与「显式指定」；
   显式 root 必须先验证为既存绝对目录，不合格直接受控失败，绝不回落后创建。 ← 堵 b
3. 身份校验而非形状校验：清除 GIT_DIR/GIT_WORK_TREE 等仓库选择类环境变量；
   canonicalize(start/top) 后要求 top 是 start 的祖先 + 顶层有 .git marker。 ← 堵 a
4. 窄 catch：try 只包 subprocess.run，只捕 OSError/CalledProcessError；
   stdout 校验与 raise 位于 try 之外。禁 except Exception。            ← 堵 d
```

**代价**：`repo_root` 从「一个 try/except」变成一个真正的解析器 + 校验器（~25 行），三份同步；`cmd_*` 的签名或前置约定要改（16 处二次解析点）；测试面显著扩大。**这是把补丁升级成一次小重构。**

**备选**：只做 1+4（结构性问题），把 2+3 记 buglist 另开 change。**代价**：a/b 两条 fail-open 路径留在生产里，而 a 已被实测证明可触发 ⇒ **不推荐**。

### Q2（**已有归属，非开放题**）— 镜像手工同步 → T170

codex X6 报的问题（**37 个三向 + 24 个两向 = 61 个 helper** 手工同步，AST guard 只发现漂移不消除漂移源）**早已登记为 T170**：

```
T170 | 基础设施 | PROPOSED | batch: fix-mechanical-layer-silent-failures
「recorder 三份物理复制 parser + 双取数路径的结构问题，
  与 B11/B12 统一处理（adr/0025 推翻候选）」
```

且它绑在一条**正在推进**的线上——同 batch 的 B9/B10 已完成，**B11 + T170 就是下一步**。
`adr/0025` 那句「三个自包含脚本不建立运行时 import，却不能各写一套漂移语义」正是三份复制的
约束来源，T170 是它的推翻候选。

**⇒ 这不是本 change 的开放题。** 本轮的增量证据（61 个实数、`sync_principles.py` 可复用模式、
本 change Task 1.1 的活例子、codex 的 high 判定）已于 2026-07-19 补进 T170 详细块。

**顺序决定（已拍板）**：**先做本 change，再做 T170**。依据：本 change 的 4 条 critical 含
**实测可触发**的跨仓写入（`GIT_DIR`/`GIT_WORK_TREE` 两个环境变量即可让校验放行），安全缺陷
不等结构改造；而此刻三改的增量成本很小（只 1 个 helper）。

**⚠️ 由此产生一条对 Q1 返修的硬约束**：`repo_root` 的最终形态 MUST 保持**抽取友好**——
不引入任何脚本专属分支（与自动决策 D5「raise 消息用通用文案、不含脚本名/`__file__`」同向），
使 T170 落地时是纯搬运而非二次改写。**这条要写进 design。**

> **过程注记（本次评审自己的失误）**：codex 报 X6 时我没先查 issues 池就把它摆成开放题，
> 是通则①「能查的自己查」的违反。T170 早就在池子里。

### Q3（需拍板）— Windows 覆盖

DX D2：`windows-recorder-smoke.yml` 的 `paths` **精确匹配**本 change 要改的三个目录，但它只跑 `test_task2_windows_local_fs_smoke.py`——该文件直传 `tmp_path` 给 `recorder_lock`，**绕开 `repo_root`**；主矩阵只有 ubuntu/macos。四件套全文 grep "Windows" 零命中。

**我的推荐：加一条正向回归进 Windows 泳道**（真实 git 仓库下 `repo_root()` 不抛异常 + 一条负例）。依据：`ntpath.isabs("C:/...")` 「理论上大概率能过」正是 PV 规则 1 要拦的自洽推理，而这个 change 自己正要把 PV 规则挂进 CLAUDE.md。代价：Windows runner 一次约 2-3 分钟。**备选**：在 design 的 Open Questions 显式登记这条未验证跨平台假设（当前 Open Questions 写的是「无」）。

### Q4（需拍板）— `ship_gate.py` 第 4 个消费点

CEO E2：`sdflow-ship/scripts/ship_gate.py:837` 是同款反模式的第 4 处，四件套全篇未提。CEO 已实测其**有 `--git-dir` 前置兜底 + 全文件无 `makedirs`** ⇒ 坏根会安全落 `UNKNOWN`，后果比 recorder 轻得多。

**我的推荐：不改代码，但在 Non-Goals 显式论证排除**（连同 init.py 一起，把「不属 roster」这个**程序性理由**换成**安全论证**：sink 只读 / 无 makedirs / 有前置兜底）。依据：CLAUDE.md 基准 3「面治优先于点补」要求的是**扫全面**，不是**改全部**——扫过并论证清楚即达标。代价：一段文字。

### 自动决策（高置信，默认采纳，可在门上覆盖）

| # | 决策 | 依据 |
|---|---|---|
| **D1** | **80 字节截断算法必须在 design 里定死**：按 UTF-8 字节截断会抛 `UnicodeDecodeError`（Eng 实测：`("a"*78+"雪茄").encode()[:80].decode()` 抛错），而这会**击穿 spec 自己的「MUST NOT 含 Traceback」**——fail-closed 路径自身先崩。定为：先 `ascii()` 等价方式生成单行转义表示（同时解决 hr-tg V5 的控制字符伪造多行日志），再按**字符**截断；tasks 1.2 补一个多字节卡边界负例 | Eng G1 · codex X10 · DX D3 · hr-tg V5 四声独立命中 |
| **D2** | **`out.stdout.strip()` 改为只剥行结束符**：`strip()` 会删掉合法路径末尾的空格/Tab，而 spec 只承诺去行结束符；截短后若恰好命中另一既存目录 → 静默写错地方 | hr-tg V3 |
| **D3** | **给 `subprocess.run` 加 `timeout`**：现无 timeout ⇒「不重试、直接失败」这句话不成立，git 在网络 FS 卡顿时无限阻塞，既不失败也不可观测。超时必须 fail-closed | hr-tg V4 |
| **D4** | **订正三处事实错误**：①「14 个调用点」→ **19**（issues 7 / buglist 6 / todolist 6，`ast.walk` 精确统计）②「AST dump 长度均 1146」**双 Python 版本都复现不出**（3.9=1291 / 3.14=1165）—— 删数字或注明版本 ③ `init.py:553` → **543** | Eng G2 · 对抗镜2 F1 · 接地镜 |
| **D5** | **「三份逐字一致」措辞降级为「剥 docstring 后 executable AST 等价」**，并在 tasks 1.1 明写「raise 消息 MUST 是通用文案，不含脚本名/`__file__`」——否则实现者出于「让诊断更有用」的自然冲动会当场把 guard 打红 | codex X11 · Eng G3 |
| **D6** | **conftest 契约收窄 + 三处配套**：spec 现称覆盖「一切落盘物」，实现只比顶层条目集 ⇒ 收窄为「禁止新增 cwd 顶层条目」；conftest 顶部加范围声明注释（仅承载 cwd 断言，MUST NOT 塞其他共享 fixture）；tasks 1.3 明写用 `monkeypatch.chdir` 禁裸 `os.chdir`；补 `.DS_Store` 类环境噪声豁免 | codex X9 · CEO E5 · 对抗镜1 F4 · 对抗镜2 F5 |

### defer（记 issues，不在本 change 做）

| # | 内容 | 去向 |
|---|---|---|
| **F1** | 镜像手工同步的分发机制改造（61 个 helper） | **T170**（既有，本轮已补证据）。顺序：本 change → T170 |
| **F4** | recorder 缺「给已存在 item 追加证据/思路」的命令（补 T170 时撞到：`add` 撞新 ID、`set-status` 只收状态转换 ⇒ 只能手工编辑 prose 块 + `scan` 自检兜底） | **T180**（本轮新记） |
| **F2** | `_ACTIVE_RECORDER_TOKEN` 复位在 `args.func(args)` 之后 ⇒ 异常跳过复位。**既有问题**，非本变更引入，CLI 一次性进程下生产影响为零 | buglist（如实登记，不 fold） |
| **F3** | `sdflow-init/tests/test_outside_voice.py::test_exec_claude_reverse_path_three_flags_golden` 全量红/单独绿 | buglist（原 tasks 4.5 已列） |

### 已裁掉（反静默压制：原始发现 + 裁掉理由，可审计）

| # | 原始发现 | 裁掉理由 |
|---|---|---|
| **X1** | 对抗镜1 F3：symlink 仓根可能绕过 `isdir` | **实测 refuted**：`git rev-parse --show-toplevel` 自身把结果规范化为真实路径（macOS + git 2.x 实测与 `os.path.realpath` 完全一致）⇒ 两个 symlink 指向同一物理目录会收敛到同一字符串，锁能正确识别同仓。**命中基准 5**——规范化是 git 自己做的，不是我们手搓的 |
| **X2** | 对抗镜1 F4 前半：新 conftest fixture 与被测代码自身子进程存在时序竞态 | **实测 refuted**：`pytest-xdist` 未安装；`_scan_pool`/`cmd_sweep` 的子进程调用全是阻塞式 `subprocess.run` ⇒ 子进程必在 fixture 快照边界内跑完。（**后半保留**：环境噪声误报 → 已并入 D6） |
| **X3** | 对抗镜2 F3 后半：「三份同样改错」会让 AST 守护全绿 | **降级为已覆盖**：tasks 1.2–1.5 是**独立于镜像等价**的黑盒行为测试（构造坏值断言异常 + 断言不建目录），不依赖三份互比 ⇒ 这条攻击线已被挡住，非空白。（**前半保留**：追溯表未显式引用既有 `test_logic_drift_is_caught` → 并入 D4 的文档订正） |

### 低置信项（一行带过，不静默滤除）

- 对抗镜2 F2：Task 0 删除 4 棵垃圾树后，design 里那句「PoC 属**当前**事实证据、非考古层」会追溯性变假。缓解已存在（Task 1.3 用 `tmp_path` 合成同款病理场景续命），但两者关系未在正文显式化。
- 对抗镜2 F4：Scenario 2/3/4 天生 **mock-only**（「git rc=0 但坏值」在真实 git 下不可达——这正是 ADR-1 自己的论证）。Success Metric 1 的可信度上限 = mock 保真度，文档宜显式承认。**codex X4 是同根因在 CLI 层的表现**：Task 1.5 只传坏 `--root` 触发不了目标分支，需 PATH 注入 fake git。
- CEO E6：exit 2 语义复用（坏 root / 坏 scan id）。已扫 4 份 SKILL.md，无脚本按 exit code 分流 ⇒ 当前无外部消费方受影响，记为观察项。
- 对抗镜2 F6：Success Metric 5 比 Metric 2 好一档——「不再生成」这半有 Task 3 的 fixture 做真机械保障，只有「此刻已清干净」是一次性检查（合理分工，不需整改）。
- codex X8：Task 2.2 变异验证是一次性手工动作、无永久产物 ⇒ 不构成 Success Metric。建议改为提交**永久 negative-control**（对派生 writer 注入 spy，坏 scan id 时只要触达 writer 即失败）。**已并入 D 组待办**。

---

## 跨镜收敛信号（2+ 独立来源命中 ⇒ 高置信）

| 主题 | 命中来源 | 收敛度 |
|---|---|---|
| 80 字节截断有坑 | codex · Eng（实测）· DX · hr-tg | **4 声** |
| 信任边界只校验形状不校验身份 | codex X1/X2 · hr-tg V1（实测）· V2 · 对抗镜1 F1（实测） | **5 面同根** |
| 根 conftest 的契约与边界 | codex X9 · CEO E5 · 对抗镜1 F4 · 对抗镜2 F5 | **4 声** |
| 面没扫全（第 4 个消费点 / 排除理由是程序性的） | CEO E2 · CEO E3 · codex X7 | **3 声** |
| 文档事实错误 | Eng G2 · 对抗镜2 F1 · 接地镜 | **3 声** |
| 一次性手工验证不是 metric | codex X8 · 对抗镜2 F6 | 2 声 |

---

## 这轮评审的元观察

四条 critical 里**三条有实测复现**（`GIT_DIR` 重定向、`UnicodeDecodeError`、git 身份漂移），不是「推理出来的风险」。而它们全部**在 grill 之后**才被发现——grill 那轮打掉的是我 ADR 里的逻辑漏洞（假二选一、自我掩盖、假绿），这轮打掉的是**我根本没想到要问的问题**（根的身份是什么？输入可信吗？两次解析是同一个仓吗？）。

另外，这个 change 正要把 `premise-verification.md` 挂进 CLAUDE.md，而它自己被抓出**三处未经验证的事实断言**（调用点 14→19、AST 长度 1146 复现不出、行号 553→543）。规则写下来和规则被执行之间的距离，这份报告本身就是证据。

---

## 收敛口

> **本段是评审当时（返修前）的结论，保留原文供审计。返修已完成、设计门已拍板，最终状态见下方「拍板记录」。**

**建议：不进 HARD-GATE，先做一轮设计返修。**

返修范围 = Q1（四条 critical 合并重画信任边界）+ D1–D6（自动决策，直接改）+ Q3/Q4 待你拍板。
Q2 已归属 T170（下一步工作），但它对本次返修留下一条硬约束：`repo_root` 最终形态须**抽取友好**。
返修完成后**建议重跑一次轻量冷复审，只盯返修接缝**——依据：返工在接缝处引入新洞是本仓的高发模式（扩枚举不回改派生判据 / 解耦只解耦函数不解耦输入数据 / 期望集定义取错范畴）。

---

## 拍板记录（设计 HARD-GATE）

**设计门已拍板批准，2026-07-19。** 机判锚见本文件头部 frontmatter 的 `ship-gate.design_approved: true`。

### 拍板时的决策去向

| # | 状态 | 去向 |
|---|---|---|
| **Q1** 信任边界重画 | **已闭合**（非门上拍板，由返修完成） | 三轮返修落地：ADR-2 改「证明身份而非校验形状」、祖先校验立为主防线、ADR-5 单点解析、ADR-6 函数局部常量、ADR-7 起点取 `os.getcwd()`。四条 critical 全部有对应 spec Scenario + tasks 用例 |
| **Q2** 镜像手工同步 | **已归属 T170** | 顺序：本 change → T170。本次留硬约束「`repo_root` 抽取友好」（Success Metric 6） |
| **Q3** Windows 覆盖 | **批准（按推荐）** | 加正向回归进 Windows 泳道 → tasks 4.6。design Open Questions 同时显式登记该未验证跨平台假设（双保险，非二选一） |
| **Q4** `ship_gate.py` 第 4 个消费点 | **批准（按推荐）** | 不改代码，Non-Goals 以**安全论证**排除（前置 `--git-dir` 兜底 + 全文件无 `makedirs`），连同 `init.py` 一并；程序性理由已删除 |
| **D1–D6** 自动决策 | **默认采纳，门上未覆盖** | 全部已落四件套 |
| **X1–X3** 已裁掉 | **裁决维持** | 门上复核裁掉理由，未翻案 |
| **F1/F2/F3/F4** defer | **维持 defer** | T170 · T180 · buglist ×2 |

### 三轮返修的收敛轨迹

```
grill        → 打掉 ADR 里的逻辑漏洞（假二选一 / 自我掩盖 / 假绿）
spec-review  → 打掉「我根本没想到要问的问题」（根的身份？输入可信吗？两次解析同一个仓吗？）
冷复审接缝   → 打掉「修的时候新引入的」（判据复制粘贴 / 静默弱化验证 / 新常量落进旧盲区）
```

第三轮 11 条中 8 条为本次返修**自身引入或遗留**——「返工在接缝处引入新洞」的又一次实测。
11 条中**无一条是「方案错了」**，全为精度问题 ⇒ 收敛信号明确，不再开第四轮。

### 已知未验证面（进阶段三时携带）

- **Windows**：`ntpath.isabs` / `normcase`+`commonpath` 在盘符·大小写·UNC 下的行为、`realpath` 对 SUBST —— 本地 macOS 照不到，由 tasks 4.6 的 Windows 泳道兜。
- **Task 0 前置**：仓根 4 棵垃圾目录树**仍在**（当前作为「坏值被具现」的活证据锚）；**MUST 最先删**，否则后续 `isdir` 判据在被污染环境下得到的绿不可信。

### 拍板后的零语义文档订正（出 ticket 时抽约束撞到）

出 ticket 逐字抽 design.md 的 MUST 条款时，撞到第三轮返修**自己留下的两处接缝残留**，当场随本
提交一并修掉——**两处均为零语义变更**，不构成对已批准设计的实质修改：

1. **重复段落**：「MUST NOT 写入 stdout / 退出码可区分性」整块被写了两遍（第三轮插入新版时未删
   旧版）。删去较短的那份，保留信息更全的一份。违反 DOC-1。
2. **Compliance 漏列**：`BASE-12 决策记录` 仍写 `ADR-1 / ADR-2 / ADR-3 / ADR-4`，而第二三轮新增
   了 ADR-5 / ADR-6 / ADR-7。补齐。

> 这两处正是**同一个模式的第 12、13 次实例**——「返工在接缝处引入新洞」。三轮冷复审全部没抓到
> 它们，抓到的是「逐字抄 design 去写 ticket」这个动作：**抄写强制逐行读，比评审更容易撞见重复段。**

**下一步**：`/sdflow-ship` 进阶段三。
