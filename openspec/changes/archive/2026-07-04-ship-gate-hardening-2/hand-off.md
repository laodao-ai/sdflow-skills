# hand-off.md — ship-gate-hardening-2

> 阶段三收尾交接（verify 之后 / archive 之前）。异步人类再入口 + 下个 change 种子。

## ✅ 完成了什么（每条附机验锚点，已复核锚点存在性）

`ship_gate.py` 完成判据二批加固全落实，仓级 **342 pytest 全绿**（基线 328 + 新增 R1/R2/impl-review-fix 锚测，零回归）：

- **T32 change 命名空间隔离**（R1，P2 防御纵深）：`TAG_RE` 可选命名组（`ship_gate.py:231`）+ `done_task_ids(root,sha,change)` 精确 `ns==change` 归属（`:286-289`）+ **`startswith("checkpoint(")` 放宽**（`:281`，堵 A-F1 静默失效洞）。锚：`test_gate_namespace.py` 6 例（真 git fixture，含判别性负例 `test_namespace_isolation_discriminating`——B 的号=A 缺号方有区分力，非 vacuous）。
- **T32 producer 三契约点同批改齐**（G1 blocker，代码审 3 声共识）：bundle **唯一权威源** `workflow.md:74` + `SKILL.md:29` + `test_workflow_authority.py`（断言命名空间格式）；`checkpoint-commit.sh` **零改**（`git diff 9b5501b..HEAD` 证实空，逐字插值 step 即产命名标签）。
- **T34 复选框分段绑定**（R2，P2）：`checkbox_done_ids` 按段全勾（替换全局 `checkboxes_all`）+ 重号→UNKNOWN + 两通道并集。锚：`test_t34_*` 系列。
- **代码审 critical 假✅ 修复 [impl-review-fix]**（CR-F1，对抗镜 B + outside-voice fallback 两声共识）：`_parse_plan` **fence-aware 单遍**（Task 标题+复选框共享全文围栏状态）+ **未闭合围栏→UNKNOWN**——修掉"先切段各自重置 in_fence"致悬空/跨段围栏泄漏假✅。锚：`test_t34_unclosed_fence_unknown` / `test_t34_task_header_in_fence_not_counted` / `test_t34_fence_any_checkbox_consistent`。
- **spec delta 转 MODIFIED**（设计门 Q2=A）：`spec-workflow` 的「阶段三编排台账确定性」需求逐字保真 16 Scenario + 追加 6 条 T32/T34 Scenario + 消解「前置产物缺失点名」的"全勾为辅"书面矛盾。
- **头注释**：完成判据窗口段（命名空间/分段/重号/未闭合 UNKNOWN）+ 已知不覆盖（裸污染残留，声明 MUST NOT 用独立分支纪律缓解，引 adr/0008）+ T33 停置理由（`:60-66`）。

## ⏳ 未完成 / 延后

- **批次 `ship-gate-hardening-2`**（`openspec/issues/batches.md` + INDEX，PLANNED，成员 T35/T36 均 PROPOSED）：
  - **T35** 新鲜度可选纳入工作树 dirty 状态（= 设计门 T33 停置延续）——需先 grill 拍板 gate 该不该越过 committed 边界（与「盘面即状态=committed 产物」本质张力），再决定实施。
  - **T36** checkpoint 派发指令文案收敛为单一真相源（broad-F2）——现 workflow.md 权威源 + SKILL.md 两处独立文案，本轮实证会漏改一处（G1 根因）；建议 workflow.md 权威定义、SKILL.md 引用/参数化复述。
- **代码审裁掉项**（非 defer）：CR-naming（T34 锚测 `t34_` 前缀 vs 文档预期名）——纯命名、断言完整覆盖，裁掉不改。
- **Minor**：无核心缺口（verify PASS）。CR-F3（非 kebab change 名）已由 openspec kebab 强制兜底 + 防御性守卫测试锁定。

## ▶ 下一阶段建议

- 批次 `ship-gate-hardening-2`（T35/T36）优先级 **P2/P3**——非阻塞。**T35（工作树 dirty）是 gate 三批最有价值项**，但必须先单独 grill「盘面即状态 该不该看 committed 边界外」这个设计张力再动，别直接实现。T36 是纯重构（消 producer 文案重复），可搭 T35 或独立小 change。
- **本 change 首次落地命名空间 producer 格式**（workflow.md/SKILL.md 已改）——但本 change 自己的 checkpoint 用**裸格式**（设计门 Q1=A：RUN_PLAN 早于派发 args 更新，无自动传导）。**下一个真实 change 的 ship 将首次端到端消费命名空间格式**——那是 T32 activation 的活体度量点，注意观察其 checkpoint 是否为 `checkpoint(<change>:task<N>-)`。
- **代码审实测价值**：本轮 grill+spec-review 都没抓到的 CR-F1 围栏假✅ 被独立冷代码审 + outside-voice 抓出——印证 sdflow-code-review「独立兜底网」不可撤。
- 无 push（手动控制）；toolkit 源仓需 push 后新会话 `/sdflow-upgrade` 激活；**merge 后运行 checkout 需重跑 setup.sh 还原 symlink**（dev/runtime 纪律，本 session 曾指 dev checkout dogfood）。
