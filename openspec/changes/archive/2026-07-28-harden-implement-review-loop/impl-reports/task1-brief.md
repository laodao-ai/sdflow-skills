### Task 1: 四个编排 skill 的宿主/档位解析第零步 + 机械 parity 守卫

**Blocked-by:** none
**R-ID:** R-tier（sdflow-implement 档位解析与声明）, R-tiers-map（模型档位映射）

**交付的行为**：`sdflow-implement` 起手就能解出本机队档位并据此派发四类子代理（implementer / Standards 轴 / Spec 轴 / fix），解析失败一律 fail-loud 硬停而非用空档位继续；`sdflow-done` 的同一位置不再是裸 `eval`；四份第零步拷贝由一个机械守卫锁住，任何一方单边改动即判红。

工作清单权威见 `tasks.md` §1（1.1–1.12）与 §7.2、§7.7；需求见 delta `impl-orchestration` 的「sdflow-implement 档位解析与声明」与 `spec-workflow` 的「模型档位映射」。

要点提醒（皆已在 Global Constraints 展开）：四步语义对齐而非逐字复制；跨文件引用用具名锚点；第零步置于文件最前、两入口共用无条件执行；`host=unknown` 与三档任一为空 **分别**报错且都硬停；Codex 子代理授权清单与其机械断言测试同批改（不改即红）。

- [ ] 解析成功路径：`$SDFLOW_HOST ∈ {claude,codex}` 且三档非空时，四类 dispatch 均引用 `$SDFLOW_TIER_MID`，全文无内联模型名
- [ ] 失败路径覆盖八类（resolver 不存在 / 不可执行 / 非零退出 / 输出无法 eval / host 非法 / host 空 / tier 缺失 / host=unknown），逐类给 problem+cause+fix，且沿用五要素 halt envelope（ticket 号字段填「—(起手失败,无票上下文)」）
- [ ] `host` 空值与 `host=unknown` 报**不同**的 cause 与 fix，空值 MUST NOT 被吸进 unknown 路径
- [ ] `sdflow-done` 的裸 `eval` 已升级为同一套四步语义
- [ ] parity 守卫测试落地并通过，锁住四个 skill 的第零步归一化核心段（marker token 单行字面量匹配，MUST NOT 演化成解析 Markdown 结构）
- [ ] **变异实测**：逐个删除四个 skill 第零步中的任一步，parity 测试**必红**；两种恒真成因（门被别的断言满足 / 压根没用例走到那行）都已排除，变异记录写进 impl-report
- [ ] Codex 子代理授权段已含 `sdflow-implement`，其机械断言测试同步通过
- [ ] `grep -n "SDFLOW_TIER" sdflow-implement/SKILL.md` 不再是零命中
- [ ] `[e2e]` Success Metric 1 证据：Codex 宿主下实跑一次 `sdflow-implement` tickets-plan，记录四类 dispatch 解析到的 model id，确认全 ∈ Codex 机队缺省集、零命中 Claude 机队专名；**配额不可用时如实记「未验证」并留 todo，MUST NOT 用 Claude 宿主的运行冒充**
  - 🔴 该实跑 **MUST NOT 以本 change 为目标**（会覆盖本 plan 文件 = 毁掉完成判据窗口锚，见 Global Constraints）——用一次性 fixture change 或只走到档位解析步即止，二选一并在报告写明取哪种

---

