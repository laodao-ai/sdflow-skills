# ship-gate-hardening-2 — gate 完成判据二批加固

〔TG-01：工具链（Python+bash gate 脚本）〕〔TG-25：契约套件〕〔TG-23：≥2 方案〕〔TG-19：多需求〕〔TG-22：未验证前提〕〔TG-12：决策逻辑〕

## Why

`ship_gate.py` 的**实现完成判据**（阶段三主锚）目前有两处 pre-existing 精度局限（ship-gate-hardening 代码审 HR-TG code 镜发现、非其引入、defer 为 T32/T34）：

1. **checkpoint 任务号无 change 归属**——`checkpoint(task<N>-)` 标签不带 change 名，同一 feature 分支上交错推进两个 change（**stacking**：已在 feat/A 上再建 change B）时同号任务会互相污染完成集。窗口下界 `plan_first_sha` 只做**部分**隔离，一旦两 change 的 plan 与 task 提交落进同一窗口区间即撞号，可致**假齐 → 误放行 RUN_CODE_REVIEW**（假✅）。**注**〔grill Q1〕：触发需 **stacking 反模式 + 撞 plan 同号 + 窗口重叠** 三重条件（FF-0 只拦 main 建 change、不拦 feature 分支上 stacking；B4 集合归属已滤计划外号）——故本项定位为**契约正确性加固 + 防御纵深**（gate 不假设分支纪律永不破），非活体高频 bug。
2. **复选框辅通道全局粒度**——`checkboxes_all` 只看全文有无 `- [ ]`/`- [x]`，一个全局勾选即放行**所有** plan task，未按 `### Task <n>:` 分段绑定；与 checkpoint 集合归属主锚并存时可放大假齐面。

两者都是"绝大多数盘面正确、但在特定交错/回勾盘面下产生假✅"的精度洞。gate 的存在意义就是堵假✅，这两处属其自身判据的残留缝隙，值得在一个窄 change 内根治。

## What Changes

- **T32（P2，防御纵深）checkpoint 任务标签加 change 命名空间**：checkpoint 任务提交格式引入 change 归属（具体编码格式经 design ADR 定夺，候选：步名内嵌 `checkpoint(<change>:task<N>-)` / git trailer / 旁挂字段）；gate 完成判据**只认当前 change 的任务标签**，跨 change 同号不再互相计入。**BREAKING（契约层）**：checkpoint 任务提交格式变更，牵连 producer（`checkpoint-commit.sh` 调用约定）+ consumer（`ship_gate.py` 解析）+ `sdflow-ship` 派发 args + 下游 plan 模板。
- **T32 向后兼容**：旧无命名空间 `checkpoint(task<N>-)` 历史标签的读取语义必须保留、不得因新格式判读崩溃（具体归属策略——宽松「无命名空间视同任意 change」vs 严格「命名空间 change 忽略裸标签」——经 design ADR 定夺）。
- **T34（P2）复选框辅通道按 Task 分段绑定**：`checkboxes_all` 全局判据改为按 `### Task <n>:` 分段解析，每段复选框状态绑定到对应 task_id；辅通道完成集与 checkpoint 主锚完成集按号合并，一个全局勾选不再放行未各自勾选的其它 task。自包含于 `ship_gate.py` + tests。

## Capabilities

### New Capabilities
<!-- 无新增能力：本 change 只加固既有 ship_gate 完成判据需求 -->

### Modified Capabilities
- `spec-workflow`: 收紧「阶段三编排台账确定性（ship_gate）」需求的**实现完成判据**——task 完成号集 MUST 按 change 归属隔离（T32）、复选框辅通道 MUST 按 `### Task <n>:` 分段绑定（T34）；既有 B1/B2/B3/B4 语义不变。

## Impact

- **`sdflow-ship/scripts/ship_gate.py`**：`TAG_RE` / `done_task_ids`（命名空间过滤）、`checkboxes_all` → 分段绑定；`decide()` 完成判据分支。
- **`sdflow-init/assets/hack/checkpoint-commit.sh`**：任务 checkpoint 契约（若 ADR 选步名内嵌，则 producer 侧仅约定不改脚本；若选 trailer，则改脚本——ADR 定夺后确定牵连面）。
- **`sdflow-ship/SKILL.md`**：RUN_PLAN → writing-plans 派发 args 的 checkpoint 格式约定（`task<N>-<slug>` → 命名空间格式）。
- **`sdflow-ship/tests/`**：新增 T32 命名空间隔离 + 向后兼容 + T34 分段绑定锚测。
- **不动**：ship-gate-hardening 已固化的 D3 归档终态 / B2 豁免 / B1 窗口 / B4 集合归属；已声明「已知不覆盖」接受项。

## 需求优先级〔TG-19〕

| 优先级 | 需求 | 依据 |
|--------|------|------|
| **P2** | T32 change 命名空间隔离（防御纵深） | 加固契约正确性；污染需 stacking+同号+窗口三重巧合，非活体高频〔grill Q1 降 P1→P2〕 |
| **P2** | T34 复选框分段绑定 | 回勾型执行器全局单勾可在**单 change 内**发生假✅，更贴近活体 |
| **停置** | T33 工作树 dirty 新鲜度 | 与「盘面即状态=committed 产物」有本质张力，**不在本次范围**，需先单独拍板 |

## 假设〔TG-22〕

- **A1**：旧格式 `checkpoint(task<N>-)` 仍可能存在于历史提交与进行中的 change → 向后兼容读取**必须**保留（不是可选）。
- **A2**：同一 change 的所有 task checkpoint 由同一 plan 统一派发、格式一致（命名空间由 `sdflow-ship` 派发 args 统一注入，非逐 task 手写）。
- **A3**：change slug 不含破坏 tag 解析的字符（若 ADR 选步名内嵌 `<change>:task`，`:`/`)` 需 sanitize 或选不冲突分隔符）。
- 假设证伪任一 → design ADR 须回应（尤其 A1 决定向后兼容策略、A3 决定编码格式）。

## 不在本次范围

- **T33 工作树 dirty 新鲜度**（需先拍板 gate 是否越过 committed 边界，与盘面即状态张力）。
- checkpoint 契约以外的 gate 判定（D3 归档、B2 豁免、模型档位等 ship-gate-hardening 已固化项）。
- 已声明「已知不覆盖」的 evil-merge / 精确同名旧档 / 伪造 subject 绕过。

## Success Metrics

- **M1（T32）**：构造同分支交错两 change 盘面（各自 plan + 同号 task checkpoint 落同窗口），gate 完成判据互不污染——被污染 change 判 CONTINUE_IMPL 而非假齐 RUN_CODE_REVIEW。锚测复现。
- **M2（T32 兼容）**：旧无命名空间 `checkpoint(task<N>-)` 历史盘面按 ADR 归属策略判读，不崩溃、语义符合。锚测覆盖。
- **M3（T34）**：全局单个 `[x]`（其它 task 段未勾）不再放行未勾 task；按段绑定后完成集正确。锚测复现。
- **M4**：仓级 pytest 全绿（当前 328），新增锚测计入；`ship_gate.py` 头注释「已知不覆盖」同步更新（T33 停置理由、命名空间边界）。

## 合规声明

- **destructive-commands**：不适用（gate 只读盘面、零副作用；本 change 不引入写操作）。
- **契约兼容**：T32 属契约变更，向后兼容为一等约束（A1），design 出协议套件 scope-check 表〔TG-25〕。
