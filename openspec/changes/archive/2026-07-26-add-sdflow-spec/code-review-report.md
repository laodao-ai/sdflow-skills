---
ship-gate:
  code_review: pass
  reviewed_sha: a9e62d4c3a9f506fbece6c292d9ad42808c7267f
---

## code-review 报告 — add-sdflow-spec

### 命中范围

- **diff base**：`84bfc05b6905c81b3d782f8357beeb3121bdc0ae`（`merge-base origin/main HEAD`）；156 文件、+14769/−176。
- **栈**：bash（`setup.sh` / `outside-voice.sh`）+ Python(stdlib)（hook / 脚本 / 测试）+ Markdown 指令（SKILL / agent 定义 / canonical 规则）。
- **清单**：`code-review-base.md` CR-01~09。
  ⚠️ **领域清单降级**：`code-checklists/domains/` 下只有 `backend.md` / `backend-go.md` / `embedded*.md`，
  本 diff 的栈**无对应领域 delta** ⇒ 领域镜按 base 单独运行，**未宣称「领域维度全面通过」**。
- **trivial_shape**：`NOT_EXEMPT`（`logic-line:.github/workflows/mechanical-gates.yml`）⇒ 照常 fan-out。
- **gstack/review（Step1）结论**：**无 scope 越界、无完成度缺口**。156 文件逐一对回 `tasks.md` 1.1–9.3 /
  `superpowers-plan.md` 6 票 / SA-01~SA-14；两个刻意留空的验收框（Task 1 `validate --strict` 覆盖不到 design.md、
  Task 6 下游推广）理由均核实成立，分别登记 T232 / T239。
  ⚠️ 已认账的一处**票级知情偏离**（编排层裁定，非票面字面授权）：Task 6 票面写「Task 5 判回退则本票不执行」，
  编排层裁定其中三项（8.1 分发核验 / 8.3 回滚演练 / 8.4 sunset 判定）在回退下仍该做并据此改了 `setup.sh`。
  Step1 复核确认**其实际改动范围未超出所声明的三项**。认账权在人，见 `impl-reports/task6-stage3-conditional.md` §0.0。

<!-- sdflow:step1-broad-review v1 mode="simulated" -->

> **Step1 模拟降级的诚实理由**：主 session 上下文预算已近极限（本轮 ship 连跑 6 票 + 全部返修），
> 原生执行 gstack `/review` 全量流程会挤掉合成裁决所需的上下文 ⇒ 按 skill 的显式降级路径派 fresh 子代理
> 顶上其两项核心职责（scope-drift + 计划完成度），锚行标 `mode="simulated"`。**未伪装原生、未静默跳过。**

### 子代理能力锚

<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->

`host="claude"` ⇒ 免探针、恒 `available`。本轮实际派出：领域镜 ×1、对抗镜 ×3（并发/时序 · 资源泄漏/副作用外溢 · 错误路径/假绿门禁）、历史镜 ×1。
`mirrors=` 的第三个 token 按跨层固定词表借用 `grounding` 记「第三个 fan-out 镜跑过」，其精确身份由 lens-metric 的 `lens="history"` 承载。

### outside-voice

<!-- sdflow:declared-sites v1 declared="code-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="code-voice" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="codex" reason_code="ok" findings="3" truncated="false" -->

- **HR-TG 判定**：`hit="TG-08,TG-17"`（∩ HR-TG ≠ ∅）⇒ 单开 `site="hr-tg"` 领域专属跨模型。

<!-- sdflow:hr-tg v1 hit="TG-08,TG-17" declared="TG-08,TG-10,TG-14,TG-17,TG-18,TG-21,TG-23" evidence="TG-08=新增全局 FF-0 hook 的 deny/哨兵/TTL 三条路径与 install_agents 铺设清理，都存在「失败了会不会被看见」；TG-17=三个 agent 定义的工具面（Bash 非只读 / Write）+ 定义铺进全局对全机器可见 + 出境查询过 secret scan" -->

- 🔴 **context 收敛偏离（如实登记）**：全量 diff = **1.37MB**，远超 helper 的 200KB 保头尾窗口
  ⇒ 中段核心实现会**整段丢失**。故 code-voice 的 context **收敛为「生产脚本 + 新 skill 本体 + 三个 agent 定义」= 121KB**；
  hr-tg 为「TG-08/TG-17 判据触发点 + 相关 hunk」= 74KB。**未纳入**：测试面 187KB（由领域镜/对抗镜 C 覆盖）、
  四件套设计文档（已过设计门）、impl-reports 与 A/B 原始日志。两站点 `OV_TRUNCATED=false`。
- **一次失败重派（如实登记）**：首次派发两站点均 `.rc=1`，helper 报 `SDFLOW_VOICE_RUNNER 未设置`——
  根因是 harness 每次 Bash 调用是独立 shell、`export` 不跨调用存活（正是本 change 的 `design.md` D4 记载的那条）。
  在同一次调用内解析后重派，两站点 `.rc=0`。**首次失败未落 `host-unknown` 锚**（那会是假降级：宿主已解析为 claude）。

### Findings（置信 ≥80）

> **跨模型豁免**：两条 outside-voice 锚经合法组合矩阵判定为**跨模型**（`host=claude ∧ runner=codex ∧ runner≠host ∧ reason_code="ok"`）
> ⇒ 其 findings 跳过 <80 数值滤、直通对抗裁决（跨模型自评不可比，异见不被同族标尺误杀）。

| # | 严重度 | CR | 问题 | 证据 | 处置 |
|---|---|---|---|---|---|
| F1 | **高** | CR-01/CR-07 | `secret-scan` 扫描器执行失败时**静默判干净** —— 管道吞掉 `grep` 及后续命令的失败后 `return 0`。**这是出境安全门 fail-open**：扫描器坏了 = 判「没命中」= 未扫描的查询直接放行 | `sdflow-init/assets/hack/outside-voice.sh:240,249`；voice 注入恒返回 2 的 `grep` 后 `secret-scan --context-file README.md` 仍得 `rc=0` | 已修 `[impl-review-fix]` |
| F2 | **高** | CR-02 | FF-0 只解析命令串**第一个** change 名，前置文本即可绕过其它 change 的分支拦截 | `ff0-branch-guard.py:195,234`；payload `echo openspec new change add-sdflow-spec; openspec new change unrelated-change` ⇒ **无 deny、exit 0** | 已修 `[impl-review-fix]` |
| F3 | **高** | CR-04 | 跨 checkout 删除 agent 后，**持 `Bash`/`Write` 的废弃定义永久残留全局名册**、对本机所有项目可见（只接管当前源目录仍存在的名字；孤儿清理无条件保留有效软链）。既有测试只覆盖跨 checkout 的**悬空**链 | `setup.sh:171,242` | 已修 `[impl-review-fix]`（installer-owned manifest） |
| F4 | **高** | CR-02 | S4 路径检查漏掉 change root 及**上级目录**的 symlink 逃逸 —— 从 `root` 起步却先拼接子路径再 `is_symlink()` ⇒ `openspec`/`changes`/`<name>` 本身是指向仓外的软链时仍可通过 | `hack/tests/test_sdflow_spec_agents.py:352` | 已修 `[impl-review-fix]`（逐组件检查 + 指令侧同步） |
| F5 | **高** | CR-01 | `install_into()` 与 `install_sdflow()` 的裸 `ln -snf` 在并发下触发 `set -e` **中止整个 setup**（无汇总报告、`~/.sdflow` 未铺设）。**同款防御已在本轮的 `install_agents()` 里写好，只补了一处、漏了同面另两处**（基准 3 点补 vs 面治） | `setup.sh:68,271`；对抗镜 A **4/4 复现**：`ln: …: File exists` + `EXIT:1` | 已修 `[impl-review-fix]`（面治扫全文 12 处裸调用） |
| F6 | 中 | CR-02 | 重入状态机漏两态：change 目录建好后、首次持久化前崩溃 ⇒ **partial state 无法被重入探测识别**；`complete` 态只有一句声明、无操作判定。与「session 崩溃无损」承诺冲突 | `sdflow-spec/SKILL.md:214,231,345,376` | 已修 `[impl-review-fix]`（B.1 加「立即落草稿纪要」+ 0.3 三态分治 + 承诺改为有界损失） |
| F7 | 中 | CR-01 | FF-0 deny 文案的 `touch {token}` **未经 shell quoting** —— 仓库路径含空格时命令不可用，含元字符时复制执行可能产生额外命令 | `ff0-branch-guard.py:252`；元字符路径下旧实现实测 exit 127 且 `$(id)`/`&` 被展开 | 已修 `[impl-review-fix]`（`shlex.quote` + 元字符路径测试） |

### 已裁掉（反静默压制，可审计）

- **X1**〔对抗镜 C，[低]，置信 <80 滤除〕`test_ttl_window_has_a_single_source` 的 `\d+\s*分钟` 正则挡不住**中文数字**形式的分钟数硬编码（变异：追加「哨兵约十分钟后失效」⇒ 仍绿）。
  **裁掉理由**：报告方自评「风险极低（该文档全是技术散文，极少用中文数字写时长），不建议为此纠结完美方案」——按通则④ 概率×影响÷完美成本分诊，判为可接受边角。**未静默丢弃，此行即其审计留痕。**
- **X2**〔对抗镜 C 自述〕「指令在场锚不保证正文别处没说反话」——**不是新发现**：该性质已由被守文件自己的 docstring 显式披露为语义残余（Task 4 fix2 按基准 5 警号主动把门收窄到确定性信号后的诚实边界）。
- **X3**〔领域镜〕`map_stage` 对 `checkpoint(gateway-refactor)` 的整串子串误判 —— 领域镜实测确认是**旧代码既有行为**（本 diff 只在新增的 tail 回退分支上加了 token 边界），属「未改动行的既有问题」，按规则不进本镜。

### 修复 / defer 台账

- **自动修 7 项**〔`[impl-review-fix]`，commit `a9e62d4`〕：F1–F7 全部 TDD 先红后绿 + **12 处定点变异「期望红 ⊆ 实际红」**。
  仓根全量 `2795 passed / 11 skipped / 3 xfailed / 0 failed`；`bash setup.sh` rc=0；三道一致性门全绿；`sdflow-spec/SKILL.md` = 600 行（上限内）。
- **自动选推荐 1 项（T10 第①级，有客观判据）**：F3 的修法在「installer-owned manifest」与「按路径形状就删」之间取前者。
  `T10复核: installer-owned manifest（而非路径形状判据） | 对抗镜结论 通过（既有第六格用例明写「同形状但有效的第三方链 MUST 保留」，形状判据会删掉别人仓同布局的有效链 = 数据丢失） | 理由(三镜+主次)：系统镜——多一个名册状态文件、首趟无名册有一次性窗口（已在代码注释与报告标注），但所有权判据从「猜形状」变为「installer 自己记的账」，可回退；用户镜——不再有「删掉别人东西」的风险；开发循环镜——多一处状态需维护。主次：**用户镜主导**（本仓硬标准「绝不覆盖非本仓库拥有的同名目录」是不可让的底线）`
- **defer 0 项**（本轮 findings 全部当场修完）。
- **本 change 既有的 defer 台账**（`/sdflow-done` 的 archive 阶段承接）：T232（`validate --strict` 只读 delta spec，SA-05 措辞需订正）、
  T238（`model` 是枚举非完整 id，SA-07 措辞需订正）、T239（七处 canonical 未推下游）、T240（`setup.sh` 无 uninstall 分支，Migration Plan 描述了不存在的开关）、
  T241（阶段三验收门缺 ❌/回退分支）、T242（≤600 行门可由重排换行规避）。

### 度量锚（lens-metric · `metrics.enabled: true`）

<!-- sdflow:lens-metric v1 layer="code-review" lens="adversarial" host="claude" runner="claude" site="—" findings="2" 采纳="1" 裁掉="1" defer="0" 独立="1" sev="致0/高1/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="history" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="code-voice" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" host="claude" runner="codex" site="hr-tg" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="3" sev="致0/高2/中1/低0" -->

> **本轮最值得记的一条**：**7 条采纳 findings 里 6 条出自跨模型 outside-voice（独立率 6/6），
> 5 个同族温镜（领域 / 对抗 ×3 / 历史）合计只独立贡献 1 条。**
> 其中 F1（出境安全门 fail-open）与 F2（全局 hook 绕过口）都是**同族镜全体漏掉**的高危项。
> 这一轮为「跨模型 voice 是否值得保留」提供了强正向数据点（N=1，判据与复评归 `/sdflow-retro` 聚合，本报告只落锚不做复评）。

### 诚实边界

1. **Step1 是模拟降级**（`mode="simulated"`），非原生 gstack/review；理由已在上方登记。
2. **code-voice context 经收敛**（1.37MB → 121KB），测试面 187KB 未进 voice —— 由领域镜与对抗镜 C 覆盖，但**不等价**。
3. **对抗镜 C 未跑完全部靶子**：优先攻了 1/2/3（覆盖面最大），靶子 4/6/7（checkpoint slug glob 绕过深挖 / FF-0 分支③与 TTL 定点变异 / setup.sh 清理逻辑定点删除）只做了基线通过确认、**未做定点变异**，如实登记。
4. **F3 的 installer-owned manifest 有一次性窗口**：首趟无名册时无法区分「本仓旧定义」与「他仓同名」，已在代码注释与 `impl-reports/code-review-fix.md` 标注。
5. **F6 无新增机械门**：重入状态机的三态分治是**指令层**改动（grep 确认无 needle 锁这几段），属语义残余，未硬造恒真锚背书。
6. **子代理能力锚是语义核验非机械门**：`host=claude` 免探针，`anchor_lint` 只核锚行文法自洽，核不了「是否真派了 5 个镜」。

### 结论

- ☑ **建议进 `/sdflow-done`**（verify → hand-off → archive → commit → merge）
- ☐ defer 残差已入 buglist/todolist —— 本轮 findings **零 defer**；本 change 既有的 T232/T238–T242 六项由 archive 阶段承接（hand-off 会引用）
