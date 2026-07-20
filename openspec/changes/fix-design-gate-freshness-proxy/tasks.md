## 1. 判据角色分流（P0，`ship_gate.py`）

- [ ] 1.1 在 `is_stale()` 的 design 分支内，对 `sub == "tasks.md"` 追加 plan 存在性判定；plan 存在 ⇒ 不判失鲜，plan 不存在 ⇒ 照判失鲜
- [ ] 1.2 plan 路径构造 MUST 复用完成判据侧同一来源（不另写路径拼接），避免两处口径漂移
- [ ] 1.3 确认 `proposal.md` / `design.md` / `specs/` 分支逐字未改（diff 自审）
- [ ] 1.4 确认判据只做存在性检查，无任何文件内容读取 / diff（Compliance 硬条款）
- [ ] 1.5 脚本头注释「已知不覆盖」段补一条：手写 plan 令 `tasks.md` 改动追溯获豁免属显式越权同权级〔grill-amendment〕

## 2. 失鲜诊断指引（P1，`ship_gate.py`）

- [ ] 2.1 design 失鲜的 `REFUSE_START` reason 携带触发提交（subject 或 sha）与触发文件路径
- [ ] 2.2 reason 附两条分支处置提示（真实设计变更 ⇒ 重跑设计门；阶段三尾流修订 ⇒ 走 `checkpoint(impl-review)` subject 通道）
- [ ] 2.3 确认退出码与判定结果不受本项影响（纯诊断）

## 3. dispatch 信号权威表（P2，`sdflow-implement/SKILL.md`）

- [ ] 3.1 implementer / fix dispatch prompt 必填槽补信号权威表（正面陈述，非禁令清单）
- [ ] 3.2 表内容与 `ship_gate.py` 实际消费的完成判据一致（plan 分段复选框 + checkpoint 标签）
- [ ] 3.3 SKILL 文本守（`test_skill_text.py` 同族）机械断言权威表在场

## 4. 测试

- [ ] 4.1 新增正例：plan 存在 + 提交触及 `tasks.md` ⇒ 不失鲜
- [ ] 4.2 新增负例：plan 不存在 + 提交触及 `tasks.md` ⇒ 失鲜
- [ ] 4.3 新增负例：plan 存在 + 提交触及 `design.md` ⇒ 仍失鲜（分流未误伤邻近路径）
- [ ] 4.4 新增负例：plan 存在 + 同一提交同时触及 `tasks.md` 与 `design.md` ⇒ 失鲜
- [ ] 4.5 回归：既有豁免用例全绿（`test_impl_review_exempt_bare_and_colon` / `test_impl_review_evil_suffix_stale` / `test_impl_review_fix_variant_stale` / `test_interleaved_impl_review_and_normal_stale`）
- [ ] 4.6 新增：失鲜 reason 含触发文件路径与处置提示的断言
- [ ] 4.7 **变异验证**：删掉 1.1 的分流分支 ⇒ 4.1 转红；删掉 2.1 的 reason 增强 ⇒ 4.6 转红（PV 规则 5，每道新守护须证「删掉会红」）
- [ ] 4.8 跑全套件确认无新增 failure / warning

### 测试覆盖图〔TG-18〕

```
                      is_stale(scope="design")
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   subject 豁免面          路径成员面            reason 输出面
        │                      │                      │
   4.5 回归 ×4        ┌────────┼────────┐         4.6 断言
  （既有锚不动）       │        │        │              │
                    4.1     4.2      4.3/4.4          │
                 plan 在   plan 无   邻近路径          │
                 tasks.md  tasks.md  未误伤            │
                 不失鲜     失鲜       失鲜             │
                    └────────┴────────┴───────────────┘
                               │
                        4.7 变异验证（删守护 ⇒ 转红）
```

## 5. 收尾

- [ ] 5.1 面治扫描：`DESIGN_WATCHED_NAMES` 上是否还有其他「零设计信息量」的成员形态未被审视（一次扫全，不只补 `tasks.md` 一点）
- [ ] 5.2 hand-off 声明生效条件：消费仓需 `/sdflow-upgrade` 后才拿到修复
