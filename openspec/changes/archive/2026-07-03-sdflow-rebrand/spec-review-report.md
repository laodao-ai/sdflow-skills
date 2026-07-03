# spec-review-report — sdflow-rebrand

> 2026-07-03 · spec-review 编排器（主审 = 主 session）
> 镜面：autoplan 广审（2 CRITICAL + 4 HIGH + 7 MED + 8 LOW，四镜 + Codex 双声，详见 [gstack-review.md](./gstack-review.md)）
> ＋对抗镜×2（引用面完备性 4 findings / 迁移边界·自指 4 findings + 2 证伪失败，均实测复现型）＋接地镜（11 项核验）。
> 领域镜 = 0（无栈命中）。规则根 = resolver 真实调用 `source=local-pin`。
> ⚠ **执行偏差自认（T20）**：autoplan 与多镜实际并行（SKILL 设计为串行）——已核实 autoplan 未改动四件套，镜审快照未失效，本轮无增量核对需求；顺序纪律已记 T20 待落权威源。

---

## 一、决策登记区

### [需拍板]（设计门勾选）

**Q1 · 前置修复纳入 scope（推荐：纳入）**
`cleanup_orphans` dangling 枚举 bug（主干既有死代码，双镜独立沙箱实证）+ `inject()` marker 全文匹配含旧名（改名后消费仓 update 追加重复区块，CRITICAL）——两者是本 change 承诺（孤儿清理、托管区块重注入）的硬依赖。**A（推荐）**：纳入本 change（tasks 0.1/0.2 已备好）——改名是第一个非可选依赖它们的变更，前置修复与改名同验收面；B：切独立小 change 先行——边界干净但串行拖长，且两 bug 脱离改名语境后验收退化为"理论正确"。

**Q2 · no-stub 维持确认**（autoplan 唯一 DISAGREE 项，DR-6）
autoplan 有声部建议留旧名 stub 一个过渡期；用户方向 = 不留（单用户干脆切）。**默认维持你的 no-stub**——旧链清理后失灵是响的（skill not found）、消费仓经 update 重注入即愈；stub 会污染命名空间且给"旧名还能用"的假信号。如你被 autoplan 说动可翻案。

**Q3 · grill 跳过事后追认**（程序留痕，非技术项）
本 change 起手时跳过 grill 轮（判定依据当时埋于长消息，呈现不当）；你已事后放行并记 T19（跳过条件后续重新评估）。此处正式登记供门存档：**追认跳过 ✅ / 或要求补一轮 grill 再进实现**——注：本轮 Detection 层抓到的 6 条设计缺陷（sweep 面漏、断言子串碰撞等）已全部 amendment 回流，补 grill 的边际价值主要在"你想亲自再压一遍设计"。

> ✅ **设计门拍板（2026-07-03）**：Q1 = **A**（前置修复 0.1/0.2 纳入本 change scope）；Q2 = **维持 no-stub**；Q3 = **追认 grill 跳过**（T19 评估债保留）。

### [自动决策]（高置信采纳，已回流 amendment，可覆盖）

| # | 决策 | 依据 |
|---|---|---|
| D1 | 新增 tasks 0 组：0.1 修 cleanup_orphans（find 枚举）+ 0.2 inject() token 基匹配迁移，均带防假绿测试 | autoplan F0/F1 + 迁移镜 F1，三方独立实证 |
| D2 | 引用面四类扩六类 + 显式文件清单（规则方法论文档 ⑥ / config.yaml context / setup.sh:109·:133 承重路径 / gen_review_stub 报错文案 / 7 个测试文件） | 引用面镜 F1/F2 + 接地镜 #10/#11 + autoplan F4/F6 |
| D3 | 4.3 断言硬化：逐名定制 pattern（负向排除 `sdflow-` 前缀防子串碰撞；`workflow/spec-review.md` 文件名白名单化）+ 执行时点挪 5.4 之后 + 白名单补 issues 池/docs/memo | autoplan F2/F3/F5（264 处子串碰撞实测） |
| D4 | **真实激活改道**：实现期禁跑真实 setup（仅沙箱测试）；merge+push 后**新会话**经 `/sdflow-upgrade` 在 canonical 激活——同时化解 REPO_NAME 错配（dev=04-sdflow-skills≠sdflow-skills，本机实测）与同 session 自指死锁 | 迁移镜 F2/F3 + autoplan F7 |
| D5 | marker 兼容收窄：`.laodao-skills` 仅对 RENAME-MAP∪保留名单内目录识别为自属——防 Windows 双仓共存误刷 laodao misc 财产 | autoplan F8（推翻我 design 原稿的"永久全量兼容"） |
| D6 | 触发等价从"3 条人工抽查"升格为机械断言（旧触发短语逐条 ⊆ 新 description，脚本核验留档） | autoplan F9 / adr-0006 |
| D7 | 回滚措辞如实收窄："本机可逆；消费仓侧非全自动"（design §七 + adr/0007 收录） | autoplan F10 |
| D8 | hand-off 升格四项：消费仓迁移验收带时限 / 新会话触发抽查 / 用户全局 CLAUDE.md 提醒（仓外，grep 网结构性够不到）/ merge 后激活步骤 | autoplan F11 + 引用面镜 F3 |

### [已裁掉]（反静默压制，连理由归档）

- **X1** autoplan LOW"「最佳窗口」表述应去伪量化"→ 降级不改：proposal 的窗口论证给了机制依据（消费仓数量、canonical 新立），非纯修辞；量化无数据源（metrics-loop 未建）。
- **X2** 接地镜将 `change-review-stub.py`/`checkpoint-commit.sh` 内旧名列为待改 → 采引用面镜复核结论**降级为顺手项**：均为注释/示例参数串，功能无涉（hook 靠正则匹配命令触发、checkpoint 不校验 label）——归 1.2 低优先顺手，不计功能性缺口。
- **X3** 迁移镜建议"setup.sh 加 canonical 路径断言（REPO_DIR 必须=预期路径）"→ 不采：会破坏 adr/0005 授权的 setup-from-dev 知情临时切换；改用 D4 的流程侧解法（激活只在 canonical 做）。

### 低置信上抛（一行带过）

- autoplan LOW"旧会话静默失效实测"：D4 改道后本 session 不再切链，风险面消失，随 hand-off 新会话抽查顺带覆盖。
- `openspec-upgrade` 与 `sdflow-init` 触发混淆：迁移镜证伪失败（既有风险非本 change 引入/放大），不设防、adr/0007 记一句。

## 二、合并 findings 总览（去重后 8 簇）

| 簇 | 来源 | 严重度 | 处置 |
|---|---|---|---|
| C1 cleanup_orphans dangling 死代码 | autoplan F0 / 迁移镜 F1 | **CRITICAL** | D1→tasks 0.1（Q1 拍板确认 scope） |
| C2 inject() marker 旧名匹配 → 重复区块 | autoplan F1 | **CRITICAL** | D1→tasks 0.2 + R-SR-3（ADDED） |
| C3 断言机制缺陷（子串碰撞/时序/白名单缺口） | autoplan F2/F3/F5 | 高 | D3→tasks 4.3 重写 |
| C4 引用面遗漏（第⑥类/config.yaml/承重路径/报错文案/测试×7） | 引用面镜 F1/F2/F4 + 接地镜 + autoplan F4/F6 | 高 | D2→tasks 1.2/1.3 扩列 |
| C5 激活时序（REPO_NAME 错配 + 同 session 自指死锁） | 迁移镜 F2/F3 + autoplan F7 | 高 | D4→tasks 5.3 改道 |
| C6 marker 全量兼容误伤 laodao misc | autoplan F8 | 中 | D5→tasks 3.2 收窄（推翻 design 原 D3） |
| C7 验证强度（触发抽查薄/布局冒烟/Windows 分支缺测） | autoplan F9/F12/F13 | 中 | D6→tasks 2.2/4.1 |
| C8 措辞与文档（回滚边界/LOW 8 项/spec 内 opsx-ship 引注） | autoplan F10/LOW | 低 | D7/D8 + adr/0007 收录 |

**证伪失败方向**（如实申报）：触发混淆非本 change 放大；VERSION 路径假设一致；hooks/checkpoint 旧名功能无涉；generation-process/trigger-catalog/design-diagrams/两 checklists 目录零命中；官方 CLI skills 零命中。

## 三、图核验

design §三 RENAME-MAP + 引用传播图：✓ 存在；经 D2 amendment 补第⑥类与承重路径后**已更新为准确**。§七迁移序图已按 D4 重排（⓪-⑧）。

## 四、amendment 清单（已全部回流，标 [spec-review-amendment]）

tasks.md（新增 0 组 / 1.2 六类显式清单 / 2.2 机械断言 / 3.2 收窄 / 4.3 重写+挪位 / 5.3 改道 / 5.5 升格）；design.md（传播图 / D1 / D3 / §七）；proposal.md（What Changes ⓪ / Success Metrics 两条）；specs delta（R-SR-2 加名单收窄 Scenario；ADD R-SR-3 marker 迁移 + 跨改名孤儿清理 Scenario）。

## 五、收敛口

**有条件建议进设计门**：机制内核（RENAME-MAP + 反向断言 + 触发等价）未被击穿，被击穿的是两块**地基**（C1/C2 主干既有 bug）与执行序细节——均已 amendment 收进任务。**批准前提 = Q1 拍板**（推荐 A：前置修复纳入本 change）+ Q2/Q3 确认。批准后进 writing-plans（阶段三）。
