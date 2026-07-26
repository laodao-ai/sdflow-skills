# ship_gate 取防御纵深立场：不假设分支纪律成立，change 命名空间隔离即便 FF-0 不拦 stacking 也有价值

`ship_gate` 的完成判据以 `checkpoint(task<N>-)` 任务标签为主锚。跨 change 污染（同号 task 互相计入 → 假✅）的唯一触发入口是 **stacking**（在已有 feature 分支上再 `openspec new change` 建第二个变更，使两 change 的 checkpoint 交错落进同一分支历史）。关键实证（ship-gate-hardening-2 grill 2026-07-04）：**FF-0 只拦 `main`/`master` 上建 change，不拦 feature 分支上 stacking**（`ff0-branch-guard.py`）——故 stacking 可达但非常规。据此确立：gate 对完成判据取**防御纵深**立场——不把"每 change 独立分支"当作可依赖的不变量，change-命名空间隔离（`checkpoint(<change>:task<N>-)`，gate 只认当前 change）作为**防御纵深层**存在，即便触发场景需要 stacking 反模式。

派生铁律：

- **(a) 立论不得自否**：MUST NOT 用"每 change 独立分支是纪律"给命名空间隔离的残留兜底——该纪律若成立则污染从源头不可达、隔离本身失去意义（立论自否）。隔离有价值 ⇔ 承认纪律可能破。
- **(b) 定位为加固而非修活体 bug**：命名空间隔离触发需 stacking + 撞 plan 同号 + 窗口重叠三重条件（B4 集合归属已滤计划外号），故定 **P2 防御纵深**，非活体高频假✅——priority 不虚高，立论诚实。
- **(c) 取舍方向锚假✅**：兼容取舍一律向假阴（少计 = 多一次 CONTINUE_IMPL）安全倾斜，MUST NOT 引入假阳（假齐放行）。旧裸标签保留窗口计入（向后兼容），残留"裸污染方 stacking + 撞号"记入脚本头注释「已知不覆盖」。

## Considered Options

- **gate 防御纵深隔离（选中）**：gate 不信任上游纪律、自带 change 归属隔离。契约爆炸面最小（命名空间落在 sdflow-ship 派发 args，`checkpoint-commit.sh` producer 零改）；符合 gate「盘面即状态 + 堵假✅」天职。代价 = checkpoint 契约变更 + 向后兼容义务。
- **在 FF-0 里拦 stacking（禁 feature 分支上再建 change）**：从源头消除污染入口，gate 无需隔离。未选：① FF-0 是通用跨项目守卫，stacking 有时是合法工作流（栈式变更）不该一刀切禁；② 把正确性寄托于"入口守卫无漏"违反防御纵深——守卫绕过（手工 `git`/其它入口）后 gate 仍会假✅。
- **干脆砍掉隔离、接受 stacking 污染**：零改动，但把已知假✅ 入口留着不管，与"任何一层评审覆盖不得无声蒸发"元原则冲突。未选。

## Consequences

- **ship-gate-hardening-2 落地本 ADR**：`ship_gate.py` 完成判据加可选命名空间捕获组 + 归属规则；`sdflow-ship` 派发 args 产命名空间格式；旧裸标签向后兼容。
- **CONTEXT.md 补术语 Stacking**（含立论自否铁律）；后续 gate 加固写"分支/纪律"处受本 ADR 约束。
- **收紧后手留档**：per-change 模式检测（命名 change 忽略所有裸标签 → 对裸污染全免疫）审议后故意不做（KISS + A1 摩擦），若 stacking 变常态再作 D2-b 式升级（见 ship-gate-hardening-2 design ADR-2）。
- **与 adr/0006 同系**：均属"gate/workflow 不押上游理想假设"哲学——0006 不押"开发时的强模型"，本 ADR 不押"分支纪律"。

### 〔现状更新 · add-sdflow-spec 2026-07〕FF-0 已升为三分支判定，本 ADR 的决定不变

FF-0 与 `ff0-branch-guard.py` 已改为三分支判定：**在其它 feature 分支上建 change 会被 deny，要求先问人**（人拍板"就地继续"后带 `SDFLOW_FF0_ACK=1` 重跑即放行）。⇒ 正文"关键实证"那句（"FF-0 不拦 feature 分支上 stacking"）**已不再是当前行为**，但**本 ADR 的选择与派生铁律全部不变**：

- 上面 Considered Options 里拒绝"在 FF-0 里拦 stacking"的理由 ①（"stacking 有时是合法工作流，不该一刀切禁"）由 **ack 逃生口**满足——新判据挡的是"静默默认发生"，不是"禁止 stacking"；
- 理由 ②（"把正确性寄托于入口守卫无漏违反防御纵深"）**完全不受影响**：守卫仍可绕过（人 ack / 取不到 change 名或探测不到分支时 fail-open / 手工 `git` 与其它入口）⇒ `ship_gate` 的 change-命名空间隔离 **MUST NOT** 因"现在 FF-0 会拦了"而被撤掉或降级。
