# Design: cross-model-outside-voice（Phase C）

## Context

评审独立性现状 = fresh-context 同模型子代理（盲区同处）；`adr/0006` 锚定混编机队（opus/sonnet/gpt-5.5）后，跨家族 outside voice 既天然可得（机队里本来就有 GPT）又更必要（弱主模型兜底）。机制蓝本来自归档 design §9（streamline-workflow-automation，含 grill-amendment 两道焊缝），本 change 是其 Phase C 落地。前置耦合：sdflow-spec-review / sdflow-code-review 的 Step1 广审目前被「子代理读 SKILL.md 模拟执行」替换（T25，两轮运行实证自报偏离）——C2「复用 autoplan 产物」的前提是产物为真，故 T25 修复收进本 change。

现状锚点（已核验）：
- `sdflow-spec-review/SKILL.md:35-39` Step1 autoplan 子步已有反静默守卫「显形部分」+〔Phase C 补〕占位注（本 change 兑现）；`SKILL.md:41` Step2 = 规划镜头 + fan-out。
- `sdflow-code-review/SKILL.md:58-62` Step1 gstack/review 子步（显式降级已有）；`SKILL.md:64-66` Step2 规划镜头。
- 全局 hack 家已有 `checkpoint-commit.sh`、`resolve-workflow.sh`（源 = `sdflow-init/assets/hack/`，setup.sh 拷入 `~/.sdflow/hack/`）——新 helper 同家同机制。
- trigger-catalog 现有 TG-01~25，TG-26 为下一空号；`openspec/INDEX.md:16` 写「TG-01~24」存在既有计数漂移（本次一并修）。

## Goals / Non-Goals

**Goals:**
- C1/C6：自包含 codex helper（preflight + exec 包装 + prompt 模板 + off-switch）+ Claude 子代理 fallback，全程非阻塞。
- C2/C7：spec-review 复用 autoplan outside-voice findings + 反静默守卫回落；gstack 边界守恒（读产出物 ✓ 依赖内部 ✗）。
- C3：code-review 自带 code outside voice（always）。
- C4：HR-TG 判定 + TG-26 入 catalog（四列 + 消费方引用 + INDEX 计数）。
- C5：tension 适配（spec→决策登记区 / code→自动裁决或 defer），守 user sovereignty。
- T25：Step1 广审原生执行；模拟降级必须显式标注。

**Non-Goals:**（详见 proposal，均附可证伪假设）不改 gstack 内部；不做 codex 镜位；不新造风险分级；不含 T26 与 setup.sh 加固批次。

## Decisions（决策记录，TG-23）

### D1. helper = 全局家 bash 单脚本 `outside-voice.sh`
- **选中**：源 `sdflow-init/assets/hack/outside-voice.sh` → setup.sh 拷入 `~/.sdflow/hack/`（与 checkpoint-commit.sh / resolve-workflow.sh 同家同机制）；测试走 pytest subprocess 跑 bash（resolver 既有先例）。
- **备选**：①Python 脚本——测试更顺，但 hack/ 家先例全 bash、SKILL prose 直调 bash 链最短，未选；②放某 skill 的 `scripts/`——两 review skill 共享，仓内放谁家都造成另一家跨目录引用，全局家消除该耦合，未选。
- **代价**：改 assets/hack/ 后必须重跑 setup.sh（copy 非 symlink，CLAUDE.md 已有此纪律）。

### D2. helper 接口 = 子命令 + 结构化退出码（adr/0006(b) prose 脚本化）
- **选中**：`outside-voice.sh preflight` → stdout 单词 `ready|not_installed|not_authed|disabled`（exit 0）；`outside-voice.sh exec --prompt-file <f> [--timeout 300]` → codex findings 原样到 stdout（exit 0），超时 exit 124、codex 报错 exit 1（stderr 转发）。SKILL.md 只剩「跑脚本 → 按 mode/exit code 分支」。
- **边界**：fallback「派 fresh Claude 子代理」是模型动作（Task 调度），不进脚本；脚本只管探测/调用/超时这些机械段——机械活交脚本、模型只做判断。
- **备选**：单命令自动内部 fallback（脚本里没法派子代理，必然做半截）——未选。

### D3. off-switch = env `SDFLOW_CODEX_VOICE=off` 单轨起步
- **选中**：preflight 首查该 env，命中即返回 `disabled`。会话/机器级关停足够覆盖「不想让代码出境 / codex 抽风临时关」两个真实场景。
- **备选**：①`config.yaml` 仓级一行——bash 解析 YAML 引入重依赖或脆 grep，且 helper 是全局脚本不应绑仓级配置读取，未选（留待真实需求出现再加层）；②双轨——复杂度先付，未选。
- **注**：归档 design 写 `LAODAO_CODEX_VOICE`，按 `adr/0007` 品牌收拢定名 `SDFLOW_CODEX_VOICE`。

### D4. T25 修复路径 = 主 session Skill 机制原生执行（①），模拟仅显式降级（③）
- **选中**：Step1 由主 session 经 Skill 机制原生执行 autoplan / gstack review（指令直接进主 session，非子代理转述）——方向已拍板（用户 2026-07-03），sdflow-ship 评审轮已有原生执行先例；与 T20 串行纪律（Step1 checkpoint 后才 fan-out）天然兼容。原生不可用 → ③模拟广审 + 报告显式标注「模拟广审（降级模式）」。
- **备选**：②gstack headless 调用路径——是否存在未调研，作 P2 补充项不阻塞（见 Open Questions）。
- **两 skill 同修**：sdflow-code-review Step1 的 gstack/review 同构问题按同路径改。

### D5. HR-TG 子集单一源 = trigger-catalog 附录段
- **选中**：trigger-catalog.md 新增「HR-TG 子集」附录（成员 {TG-04/06/07/08/09/16/17/26} + 入选判据「做错会运行期爆炸/数据损坏/安全泄漏且难回退」）；两 SKILL 的规划镜头步只引用 ID 集合，不复制清单。
- **备选**：写死两 SKILL.md（两份副本必漂移，正是 ff-generation-constraints 背景一节实证过的反模式）——未选。

### D6. TG-26 四列定义（归类 D. 行为/状态）
| ID | 触发条件 | D约束 | 领域 | 画图 | 模版槽 |
|----|---------|-------|------|------|--------|
| TG-26 | **并发 / 共享可变状态**（多线程/多任务/ISR/goroutine 竞争读写同一状态） | — | backend-go·GO-01/GO-03 或 embedded·EMB-01/EMB-10(+芯片 delta)（按栈） | 序列图（竞态交互时序） | design: 并发与共享状态访问策略（挂 domain 既有 T 项，不新增 BASE） |

领域列锚点已核验：GO-01（goroutine 并发与同步）/GO-03（TOCTOU）、EMB-01（受限回调上下文）/EMB-10（volatile/内存可见性）、ML307C-01、ESP32-02 均为既有条目。

### D7. prompt 模板内嵌 helper（heredoc），不另立文件
- **选中**：「找漏」框定 +「文件系统边界」指令 ~1KB，heredoc 内嵌使 helper 单文件自包含，拷改与部署面最小。
- **备选**：独立模板文件进 `~/.sdflow/hack/`——多一个部署物、多一处路径解析失败模式，收益仅是模板可独立编辑，未选。

## 组件清单（BASE-25）

| 组件 | 职责 | 技术栈 | 部署 |
|------|------|--------|------|
| `outside-voice.sh` | preflight 探测 / codex exec 包装（超时、stderr 转发）/ prompt 模板 / off-switch | Bash | `sdflow-init/assets/hack/` → setup.sh → `~/.sdflow/hack/` |
| sdflow-spec-review Step1' | 原生执行 autoplan + 复用 outside-voice findings + 反静默守卫回落 | SKILL.md prose（判断层） | 仓根 skill 目录（symlink 安装） |
| sdflow-spec-review 规划镜头' | 顺带 HR-TG 判定 + 留痕 | SKILL.md prose | 同上 |
| sdflow-code-review Step1' | 原生执行 gstack /review（同构修复） | SKILL.md prose | 同上 |
| sdflow-code-review outside-voice 子步（新） | always code voice + HR-TG 领域 cross-model | SKILL.md prose 调 helper | 同上 |
| trigger-catalog.md（bundle 源） | TG-26 四列 + HR-TG 附录 | Markdown | `sdflow-init/assets/workflow/` → canonical → 消费仓 update |
| tests | preflight 四态 / exec 超时与退出码 / off-switch | pytest subprocess | `sdflow-init/tests/` |

## 组件/依赖图（TG-14）

```
  sdflow-spec-review ──┐                       ┌─→ codex CLI ─→ GPT（外部计费）
  (Step1'/规划镜头')    ├─→ ~/.sdflow/hack/ ────┤
  sdflow-code-review ──┘   outside-voice.sh    └─(非 ready/超时)→ exit code
  (voice 子步/Step1')            ▲                      │
        │                        │ setup.sh 拷入         ▼ SKILL 按码分支
        │ 读(产物,只读)     sdflow-init/assets/hack/   fresh Claude 子代理(fallback)
        ▼
  gstack-review.md ←─ autoplan(gstack 原生,不动) ←─ Step1' 主 session 原生执行
```

## 序列图（TG-10：code-review outside-voice 子步）

```
  主session          outside-voice.sh        codex CLI         Claude子代理
     │ preflight ────────→│                      │                  │
     │←─ mode ────────────│ (env off→disabled;   │                  │
     │                    │  command -v+试跑)     │                  │
     │ [ready] exec ─────→│─ prompt(找漏+边界) ──→│                  │
     │←─ findings(stdout)─│←─ stdout(5min封顶) ──│                  │
     │ [非ready/124/1] ───────────────────────────────同prompt────→│
     │←──────────────────────────────────────────── findings ──────│
     │ findings 进合并池 + 报告 outside-voice 段留痕(四态之一)         │
```

## 决策图（TG-12：preflight/守卫回落链）

```
  SDFLOW_CODEX_VOICE=off? ──是──→ disabled → 跳过+报告"已显式关闭"
        │否
  codex 装了/认证了/试跑通? ──否──→ not_installed/not_authed → fallback Claude 子代理(留痕)
        │是(ready)
  exec 5min 内返回? ──否(124/1)──→ fallback Claude 子代理(留痕原因)
        │是
  findings 进合并池(留痕"已跑 codex")

  〔spec-review 专属前置〕gstack-review.md 在? 解析出 codex 段? 条数>0?
        任一否 → 显式降级日志 → 回落自跑设计 voice(进上面的链)
        全是   → 复用不重开(留痕"复用 N 条")
```

## 失败模式表（BASE-06，D-4）

外部依赖声明：codex CLI 调用超时 **300s（5min）封顶**；本机制全程**只读**（读 diff/产物、发 prompt、收文本），无外部写操作，回滚路径不适用（N/A，声明依据：helper 不落盘、不改仓）。

| 失败模式 | 触发条件 | 处理者 | 用户可见行为 | 测试 |
|---------|---------|--------|------------|------|
| codex 未安装 | `command -v codex` 失败 | preflight → SKILL | 报告留痕「not_installed → 已回落子代理」 | pytest |
| codex 未认证 | 试跑报 auth 错 | preflight → SKILL | 同上（not_authed） | pytest（mock 试跑） |
| 显式关闭 | env=off | preflight | 报告「已显式关闭」，跳过 | pytest |
| exec 超时 | >300s | helper exit 124 → SKILL | 回落子代理，留痕「超时」 | pytest（sleep 假 codex） |
| exec 报错 | codex 非零退出 | helper exit 1 + stderr 转发 → SKILL | 回落子代理，留痕 stderr 摘要 | pytest |
| helper 缺失 | 未跑 setup.sh | SKILL `[ -x ]` 前置检查 | 显式提示「先在运行 checkout 跑 setup.sh」+ 回落子代理，不静默 | SKILL 步骤核验 |
| gstack-review.md 缺失/0 条 | autoplan 未跑或格式漂移 | spec-review 守卫 | 显式降级日志 + 回落自跑设计 voice | 冒烟 §8.3 |
| autoplan 原生执行不可用 | skill 未安装 | Step1' | 模拟广审 + 显式标注「降级模式」 | 冒烟 |

## 可观测性（BASE-11）

报告 outside-voice 段为必填、**四态穷尽留痕**：已跑 codex / 已回落子代理（含原因）/ 已显式关闭 / 守卫降级（含触发原因）——不存在「无记录」合法态。HR-TG 判定无论正反留痕（「命中 TG-xx → 已跑领域 cross-model」或「未命中」）。所有降级走显式日志，符合反静默守卫。

## 安全与数据保护（BASE-28，TG-17）

- **信任边界** = 仓库代码 → 外部 LLM（OpenAI）。发送范围限 prompt 模板 + diff/评审对象摘录；**文件系统边界指令**写进模板：不读 `~/.claude`、`~/.sdflow` 等 skill/规则定义，不读 `.env`、密钥文件，只看仓库代码。
- **总闸**：`SDFLOW_CODEX_VOICE=off` 即数据出境总闸（敏感仓一键关停，层降级为同模型子代理而非消失）。
- **凭证**：codex CLI 自管 auth，helper 不接触、不落日志；stderr 转发时按行透传原文（codex CLI 自身不在 stderr 打印凭证）。
- **最小权限**：helper 只读、无网络操作自身（网络由 codex CLI 发起）。

## 契约文档套件 scope-check 表（BASE-29，TG-25：TG-26 加入牵连面）

| 文档 | 本 change 改? | 改什么 / 不改的理由 |
|------|------|------|
| `trigger-catalog.md`（assets 权威源） | ✅ | TG-26 四列（D6）+ HR-TG 子集附录（D5）+ 消费方表补 design-diagrams 引用 |
| `openspec/INDEX.md` | ✅ | TG 计数「TG-01~24」→「TG-01~26」（顺带修 TG-25 既有漂移） |
| `design-diagrams.md`（assets） | ✅ | TG-26 画图列非空（序列图）→ 触发条件表加 TG-26 引用行 |
| `spec-checklists/`（base+domains） | ❌ | TG-26 模版槽挂 domain **既有** T 项（GO-01/03、EMB-01/10），不新增条目 |
| `code-checklists/` | ⚠️ 落地核对 | domains 与 spec-checklists 同源，若并发 CR 项已存在则只补 TG-26 引用，缺则补引用行（实现期逐文件核对后回填本表） |
| `ff-generation-constraints.md` | ❌ | TG-26 的 D约束列 = —（并发不满足 D 判据①「生成时主动行为」，走领域清单层） |
| `workflow.md`（assets） | ✅ | 阶段二/三步表追加 outside-voice 子步引用（归档 ROADMAP 约束1） |
| 消费仓副本 | ❌（本 change 内） | 经 `sdflow-init update` 推送，属部署动作非文档变更 |

## Risks / Trade-offs

- [codex CLI 接口/输出格式变化] → helper 是自维护拷贝，不自动继承 gstack 修复；低频可控，preflight 试跑能第一时间暴露，fallback 保底审查不断。
- [gstack-review.md 格式漂移捞 0 条] → 反静默守卫按「0 条即降级」处理——代价是 autoplan 真·零 finding 时多跑一次自查 voice（可接受：假阴性成本 ≪ 静默丢层）。
- [原生执行 autoplan 占主 session 上下文] → autoplan 指令直接进主 session 会消耗上下文窗口；T20 串行序 + checkpoint 已把 Step1 隔在 fan-out 之前，影响有界；实测超限再议 headless（OQ）。
- [跨模型 findings 质量参差] → tension 机制兜住：不静默采纳，spec 侧进决策登记区、code 侧拿不准 defer。
- [多一处全局部署物] → 忘跑 setup.sh → SKILL `[ -x ]` 前置检查显式提示（同 resolve-workflow.sh 既有模式），不静默。

## Migration Plan

1. dev checkout（本仓）改 assets/hack/ + assets/workflow/ + 两 SKILL.md → 跑 `bash setup.sh`（hack 是 copy 非 symlink）→ pytest + 冒烟。
2. merge 后运行 checkout `/sdflow-upgrade`（pull + setup 一体，堵窗口期）。
3. 各消费仓按需 `sdflow-init update` 刷 trigger-catalog 等规则（canonical 软链仓即时生效，规则副本 pin 仓需 update）。
4. **回滚**：运行 checkout `git checkout <上一良好 commit>` + 重跑 setup.sh（adr/0005 纪律）；helper 无状态无落盘，无数据回滚面。

## Open Questions

| 问题 | 归属 | 影响 |
|------|------|------|
| gstack headless 调用路径是否存在（T25 思路②） | 实现期 P2 调研 | 不阻塞——①原生执行已可用（sdflow-ship 先例） |
| code-checklists 并发 CR 项现状 | 实现期核对（scope-check 表 ⚠ 行） | 只影响 TG-26 引用行数量 |
| autoplan 原生执行的上下文占用实测 | 实现期观察 | 超限才升级为问题（连 OQ headless） |

## Compliance（规则/边界合规声明）

- `adr/0006`(a)(b)(c)：机械段全脚本化（D2）；档位措辞不写死模型名——**遵守**。
- C7 / 归档 design §9.0 grill-amendment（读产出物 ✓ 依赖内部 ✗）：helper 零 gstack 引用——**遵守**。
- `adr/0007` 命名（`SDFLOW_` 前缀，D3）——**遵守**。
- `adr/0005` dev/runtime checkout 纪律（Migration 步骤 1/2/4）——**遵守**。
- bundle 权威源纪律（改 assets、update 推下游，禁只改下游）——**遵守**。
- trigger-catalog 扩展约定（新 ID 不复用、四列回填、消费方引用不复制定义）——**遵守**（D6 + scope-check 表）。
- D-6 窄条款（跨产品共享数据模型）——**不适用**（N/A）。
