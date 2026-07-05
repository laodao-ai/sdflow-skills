## Context

阶段三 gate 与 checkpoint 标签契约的 6 个硬化残项（T26/T35/T36/T37/T38/T43），源自 4 个已 ship 的 change 的评审 defer 池。本 change 按 fold-vs-defer（BASE-18）把它们合一处理。

现状接地：

- **gate 无状态**：`ship_gate.py` 零副作用、盘面即状态（committed 产物为账本，不落 state 文件）〔adr/0006〕。
- **新鲜度 committed-only**：`ship_gate.py:64-65` 已注明「新鲜度只看已提交盘面，不看工作树 dirty（T33 停置），是否纳入待议」——即 T35。
- **熔断靠 prose 计数**：`sdflow-ship/SKILL.md` 链序末「同一 invocation 内同一步重跑一次仍无锚行 → UNKNOWN」由编排器短时记数，非 gate 判定——即 T26。
- **派发文案两处复述**：`checkpoint-commit.sh <change>:task<N>-<slug>` 派发指令在 `workflow.md` + `sdflow-ship/SKILL.md` 各写一份——即 T36。
- **标签形状 doc 副本**：主 spec `spec-workflow` 的 Scenario 也 prose 复述标签形状（T37）、用词 `<当前change>` 有歧义（T38）；`checkpoint-commit.sh` 头注释是事实真相源。
- **模板样例带装饰**：producer 展示的机器锚样例带反引号/同行尾注，而主 spec 行 306 已 MUST「各模板把锚写在独占一行」——即 T43。

## Goals / Non-Goals

**Goals**：① 定夺 T35（dirty 新鲜度）、T26（熔断计数）两个未决设计点并登记理由；② 把 checkpoint 标签契约收敛到**单一真相源**（T36/T37/T38），消除 doc 副本漂移；③ producer 模板样例对齐既有「独占 bare line」spec（T43）；④ merge 后清 3 整批。

**Non-Goals**：不改 gate 的盘面即状态 / 零副作用 / ship 零跨步状态三条地基红线；不动 gate-anchor-line-scoped 的 T41/T42（人读体验，归 REC-2）；不重构 checkpoint-commit.sh 的标签生成逻辑（B4 已修，本 change 只收敛"复述"）。

## Decisions

> 每个 ADR 按三镜（系统/用户/开发循环）+ 主次判定评估（BASE-12，命中 TG-23 书面必填）。T35/T26 为真设计点，标 **[需设计门拍板]**；T36/T37/T38/T43 为一致性修复，走 TG-25 scope-check。

### ADR-1 [需设计门拍板]：T35 工作树 dirty 是否纳入新鲜度

- **背景**：T33 曾 WONTDO（committed-only 与"盘面即状态"一致）；T35 复议。
- **候选**：
  - **A 不纳入**（维持 committed-only）
  - **B 纳入 gate 判定**（gate 检工作树 dirty 作失鲜信号）
  - **C 不进 gate，改由 `sdflow-ship` 收尾软提示**（"工作树有未提交非-openspec 改动，gate 判定不含它们"）
- **三镜**：
  - 系统镜：A 维持单一真相源、零耦合；**B 与"盘面即状态"地基张力**，且开发中途工作树常 dirty → 高假阳；C 把提示放编排器、不污染 gate 判定。
  - 用户镜：B/C 能提醒未提交改动（低频价值）；A 靠用户自觉 commit。
  - 开发循环镜：A 零改动零维护；B 加检测+测试+误报调参（重）；C 一句软提示（轻）。
- **决策（推荐）**：**C**。**主次：系统镜主导**——gate 判定层必须守"盘面即状态=committed"，B 引入的工作树信号既张力又假阳；用户镜的"提醒"价值真实但低频，放编排器收尾软提示即可满足，不必进门禁判定。T33/T35 gate 侧正式关 WONTDO（理由入 spec），提示能力落 sdflow-ship（非 spec 强约束）。
- **当前方案代价**：用户仍可能忘 commit 就以为 gate 覆盖了工作树改动——由软提示缓解，非根除。

### ADR-2 [需设计门拍板]：T26 熔断重试计数是否脚本化下沉

- **背景**：熔断需"单 invocation 内同步重跑一次仍无锚行 → UNKNOWN"，现靠编排器 prose 记数。
- **候选**：
  - **A 维持 prose 计数**（登记为接受取舍）
  - **B 下沉到 gate 确定性判据**
  - **C 下沉到 ship 侧无状态 helper**
- **三镜**：
  - 系统镜：**"重跑无新产物"本质无盘面差异**——gate 零副作用地无法区分首跑 vs 重跑（B 技术上撞"盘面即状态"）；跨 turn 计数须持久化，撞"ship 零跨步状态"D9（C 撞红线）；A 的 prose 计数是单 invocation 短时、SKILL 熔断条款已声明与红线不冲突。
  - 用户镜：无感（内部防护）。
  - 开发循环镜：A 零维护；B/C 高复杂度且撞红线。
- **决策（推荐）**：**A**。**主次：系统镜主导**——"盘面即状态 + gate 零副作用 + ship 零跨步状态"三红线使"持久化重试计数"架构上无处安放；prose 短时计数是已声明的合法例外。T26 从"探索"关为**已探索·结论=不下沉·理由=撞三红线**（诚实负结果）。
- **当前方案代价**：熔断计数不可被 gate 机验，依赖编排器遵守——与其余步序判定同属"编排器须遵 gate"信任面，无新增风险面。

### ADR-3：T36 checkpoint 派发文案单一真相源

- **候选**：A workflow.md 为源 / B SKILL 为源 / **C checkpoint-commit.sh 契约（头注释+`--help`）为唯一源，两处引用式**。
- **三镜**：系统镜——脚本头注释已是标签契约事实真相源（脚本自证 + B4 修复处），让 workflow.md/SKILL 指向它 = 真单源；A/B 仍留一处完整复述、仍会漂。用户镜无感。开发循环镜：C 后改契约只改一处。
- **决策**：**C**。主次：系统镜（单一真相源）主导。workflow.md 与 sdflow-ship/SKILL.md 改为"派发格式见 `checkpoint-commit.sh` 契约"引用式，不再各自写全格式串。

### ADR-4：T37/T38/T43 标签契约一致性（TG-25 → BASE-29 scope-check）

命中 TG-25（版本化多文件契约套件）。全套"携带 checkpoint 标签形状 / 机器锚样例"文档 scope-check：

| 文档 | 载何契约 | 本 change 改 | 不改则理由 |
|---|---|---|---|
| `sdflow-init/assets/hack/checkpoint-commit.sh`（头注释/help） | 标签形状**权威源** | ✅ 确立为唯一源（ADR-3 落点） | — |
| `sdflow-init/assets/workflow/workflow.md` | 派发指令复述 | ✅ 改引用式（T36） | — |
| `sdflow-ship/SKILL.md` | 派发指令复述 + 台账锚 | ✅ 改引用式（T36） | — |
| `openspec/specs/spec-workflow/spec.md` | Scenario 复述标签形状 + `<当前change>` 用词 | ✅ T37 标"样例非权威"/引用 + T38 `<当前change>`→`<change-slug>` | — |
| checkpoint 标签 **producer 模板样例**（脚本内/测试内展示的锚示例） | 机器锚样例 | ✅ T43 收紧为独占 bare line（无反引号/尾注） | — |
| `sdflow-code-review/SKILL.md`（T10 台账锚 `checkpoint(<change>:task…`） | 台账行格式 | ⬜ 不改 | 台账锚是消费格式非标签源，不复述完整生成规则，无漂移面 |
| `sdflow-spec-review/SKILL.md` | 无标签形状复述 | ⬜ 不改 | 不载该契约 |

- **主次**：系统镜（防漂移、一致性修复）主导；T37/T38/T43 均低增量、同"标签契约单源"主题 → fold 一处理。

### ADR-5：为何 6 项合一个 change（fold-vs-defer 自证）

同 capability（gate+checkpoint 契约）∧ 高耦合（同 `ship_gate.py` / 同标签契约单源）∧ 低增量（6 小项，多为措辞/引用/样例）→ AND 门三条齐，fold 成立。主次：开发循环镜主导——3 批各走一轮 workflow 循环固定成本 >> 合并后的增量审查成本。

## Risks / Trade-offs

- **[T35 软提示遗漏]** → 软提示非门禁，用户可能忽略；接受（gate 判定纯洁性优先，见 ADR-1 代价）。
- **[T26 负结果被误读为"没做"]** → hand-off/spec 明写"已探索·结论=不下沉·理由"，附三红线，避免后人重开。
- **[引用式文案降低就地可读性]** → 派发格式从"就地可抄"变"跳去看契约"；以 checkpoint-commit.sh `--help` 稳定接口缓解。
- **[spec delta 与主 spec 遗留中文格式冲突]** → 归档时按 sdflow-done 的 `--skip-specs` fallback 处理（既有流程）。

## Migration Plan

1. 改 `assets/workflow/workflow.md`、`assets/hack/checkpoint-commit.sh` 后，开发 checkout 跑 `bash setup.sh` 使全局 canonical 生效（否则测不到）。
2. 改 `ship_gate.py`（T35 关 WONTDO 注释 / 无逻辑变更）+ 跑 `sdflow-ship/tests/` 确认零回归。
3. merge 后运行 checkout 跑 `/sdflow-upgrade` 还原 canonical。
4. **回滚**：本 change 无破坏性逻辑变更（T35/T26 均为"维持现状 + 登记"），回滚 = `git revert` 文案/spec 提交。

## Open Questions

- ADR-1（T35）与 ADR-2（T26）的推荐（C / A）待**设计门拍板**确认；grill 会逐分支压测。
- T43 的 producer 模板样例具体在 `checkpoint-commit.sh` 内注释还是测试 fixture——实现期接地定位（接地镜/spec-review 核）。
