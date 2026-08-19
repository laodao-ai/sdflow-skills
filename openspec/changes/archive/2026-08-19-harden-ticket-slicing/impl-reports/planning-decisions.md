# planning-decisions · harden-ticket-slicing

出票模式（`sdflow-implement mode=tickets-plan`）的 `T10-choice` 仲裁与切片偏离审计落点。
行格式见 `sdflow-implement/SKILL.md`（出票模式起手检查段）。

## T10-choice 复核

`T10-choice` 复核: T-d 收尾票物化方式（方案 A = 把 tasks 4.1「T141 set-status DONE」并入契约强制收尾票；方案 B = 4.1 独立成功能票、收尾票顺延） | 对抗镜结论 证伪（判方案 A 不成立，指名改用方案 B） | 系统镜——收尾票验收标准被 delta spec 穷举式 SHALL 锁死为「运行聚合套件并全部通过」，且 SKILL 明令该票 implementer「不亲自改产品代码」；而 4.1 是 rename + 改 frontmatter 的真 diff，并入后该 implementer 会同时收到「不要改文件」与「把 T141 改成 DONE」两条互斥指令。用户镜——`ship_gate` 第四道只校验「恰一张 R-ID: all」+「Blocked-by ⊇ 全部功能票号」，方案 A 照过，∴ 这是**静默失效**：人看到全绿，实际有一处改动未被任何轴审到，出票是唯一拦截点。开发循环镜——修正成本近零（4.1 独立成 Task 4，收尾票顺延 Task 5、Blocked-by 1,2,3,4；功能票 4 张仍在 3–6 预算内，收尾候选仍唯一）。主次判定：系统镜主导——验收边界失守 + 指令层自相矛盾是决定性代价，开发循环镜为辅（便宜到没有理由不付）。**出票方已按复核确认的方案 B 出票。**

## 切片偏离

切片偏离: design.md「切片建议」T-d 由一张票拆为 Task 4（T141 收口，功能票）+ Task 5（契约强制收尾票） | 系统镜——契约收尾票由出票契约自动追加、不占 3–6 预算、验收标准由 delta spec 固定，草图作者无权撰写其内容，∴ T-d 应读作第 4 张功能垂直切片而非那张收尾票；按此物化反而更忠实于草图意图。用户镜——人门审过的是「T-d 收尾包含 T141 收口与回归验证」这一交付内容，拆分后两项内容全部保留、无增无删，人门可见性不受损。开发循环镜——多一张票多一轮双轴审，但换来 T141 收口改动真正被审到。主次判定：系统镜主导——避免真 diff 落进「豁免 red-before-green + Standards 轴收窄」的零审查区间。（本条为上述 `T10-choice` 复核的落地结果，非出票方独断。）

切片偏离: Task 5 的 `Blocked-by` 显式枚举 1,2,3,4（草图 T-d 只写 Blocked-by T-b, T-c） | 形式性偏离，语义等价——T-c 已 Blocked-by T-a，传递闭包与显式枚举一致；`ship_gate` 第四道校验要求收尾票 `Blocked-by` ⊇ 全部功能票号（不做传递闭包推导），故必须列全。三镜代价均为零，无主次可判。

切片偏离: Task 1 的验收标准把 tasks.md 1.4「`openspec/INDEX.md` 同步登记新增的 reference 文件」改写为「改托管块真相源 snippet + 经注入路径刷新仓内 INDEX，两侧一致」，并追加一条「消解 reference/ 目录『说明类（可删不影响执行）』描述与三处 spec 引其为执行必需规范之间的矛盾」 | 系统镜——按 1.4 字面执行即违规：目标行位于 `openspec/INDEX.md` 的 `opsx-init:rules` 托管区块内部（第 5–27 行，「勿手改本区块」），真相源在 `sdflow-init/assets/snippets/index-section.md`；且该行只按**目录**登记，本无「登记单个文件」的槽位。仓内无 snippet↔INDEX 的 parity 守卫 ⇒ 漏一侧是静默漂移，只会在下次 `sdflow-init update` 时以「你的修改被覆盖」反向暴露。用户镜——无可感知行为变化。开发循环镜——分类矛盾若不消解，等于给未来「这份标准文可删」留了书面授权，成本是一行 snippet 文案。主次判定：系统镜主导。**这是票内验收标准的修正，非切片边界偏离**（Task 1 的范围与阻塞边与草图 T-a 完全一致）。
