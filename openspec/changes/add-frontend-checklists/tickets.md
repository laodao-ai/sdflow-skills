---
impl-pipeline: tickets
---

## Global Constraints

逐字摘自 design.md Compliance + decision-memo 承重约束：

- **扩展走既有「通用 base + 领域 delta」架构，纯增量**：只写本层新增规则、`extends:` 声明父层、不改 base/父层、注册表登记一行。
- **ID 前缀无冲突、不复用不重排**：spec 侧 `FE-`（从 FE-06 起）/ `REACT-`；code 侧 `CR-FE-` / `CR-REACT-`。
- **分层选用记法 = 括号 +delta 式**：TG-03 `` `frontend`(+`frontend-react`) ``，与 TG-01/02 同构。
- **DOC-1 正文即最终态**：新条目不带演进史。
- **premise-verification**：承重约束逐条带锚。
- **备选文档在 `research/` 不进 `assets/workflow/`**（部署面权威源纯净性）。
- **每个新建/增补 domain 文件头加「机械层前置」注记**：一行说明该域推荐的 lint 面，lint 能确定性抓的不进清单。
- **条目语言与形制沿既有**：中文、紧凑表格（ID/规则/触发条件/检查点）、尾注「规则集 v1 · extends … · 项目无关」。
- **候选表列头无独立「触发条件」列**（tasks 1.1~1.4 共同要求）：落盘套进既有四列表时 MUST 为每条提炼独立触发条件短语，不得留空或以检查点散文充数。
- **不改 base/父层内容**（Non-Goals）；**不新增 TG 条目**；**不改评审 SKILL 与 workflow 机制**（栈枚举文本追加属接线一致性修正）。

### Task 1: 四个 domain 文件落盘

**Blocked-by:** none
**R-ID:** R1

将已拍板的 26 条候选（`research/absorption-candidates.md`）落成正式 domain checklist 文件，逐条对照原文检查点：

- spec 侧 `spec-checklists/domains/frontend.md` 增补 FE-06~FE-13（A 组 8 条）+ 文件头机械层前置注记
- 新建 `spec-checklists/domains/frontend-react.md`：REACT-01~03（C 组，extends frontend，REACT-03 标 `[仅RSC]`，触发条件措辞见 design D6）+ 机械层前置注记
- 新建 `code-checklists/domains/frontend.md`：CR-FE-01~08（B 组，CR-FE-06 注「CR-04 的前端特化」，CR-FE-07/08 以纯键盘交互口径措辞）+ 机械层前置注记
- 新建 `code-checklists/domains/frontend-react.md`：CR-REACT-01~07（D 组，extends frontend，CR-REACT-07 标 `[仅RSC]`）+ 机械层前置注记

每条须提炼独立触发条件短语（tasks 1.1~1.4 共同要求）。

- [x] 4 个文件落盘，26 条全部落位
- [x] 每条有独立触发条件短语（非留空非检查点充数）
- [x] 形制与既有一致（extends 头 + 四列表 + 尾注）
- [x] 机械层前置注记到位
- [x] ID 连续无冲突

### Task 2: 接线（trigger-catalog + 两侧 README + backend IOU + 栈枚举）

**Blocked-by:** 1
**R-ID:** R2

完成所有消费面的接线，使新 domain 文件在选用链中可达：

- `trigger-catalog.md` TG-03 领域列改为 `` `frontend`(+`frontend-react`) ``
- `spec-checklists/README.md`：架构图加 frontend-react 分支、ID 约定表加 `REACT-` 行、注册表加 frontend-react 行
- `code-checklists/README.md`：架构图加 frontend 链、选用规则 L33 接实、ID 表加 `CR-FE-`/`CR-REACT-` 行、注册表加 2 行、扩展约定指针行
- `code-checklists/domains/backend.md:11` CR-BE-02 IOU 句改为交叉引用 CR-FE-01
- 三处栈枚举文本追加 `(+frontend-react)`：`sdflow-spec-review/SKILL.md:223`、`sdflow-init/SKILL.md:195`、`config.template.yaml:24`

- [ ] TG-03 行含 delta 记法
- [ ] spec 侧 README 注册表 +1 行、ID 表含 `REACT-`
- [ ] code 侧 README 注册表 +2 行、ID 表含 `CR-FE-`/`CR-REACT-`、扩展约定指针行到位
- [ ] `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零
- [ ] 三处栈枚举行含 `frontend(+frontend-react)`

### Task 3: 同步与留痕（guide + INDEX + research 附件）

**Blocked-by:** 1,2
**R-ID:** R3

更新人读手册与目录级注记，确保无失鲜表述：

- `checklists-guide.html` 全面更新为目标态（6 处改动面见 tasks 3.1 逐块清单：架构图 ASCII 树、覆盖矩阵、domain cards、§四缺口分析重写、§五教程换例；不动脚本/样式；改后自检标签配对+目录锚点+通读内容一致性）
- `openspec/INDEX.md` L23-24 括注扩注（沿「含 devex」先例，如「含 devex、frontend(+frontend-react)」）
- 核验 `research/absorption-candidates.md` 附件完整（26 条 + 备选冻结区 + 拍板头注 + 来源清单）

- [ ] guide §一架构图去「缺失」标注、补 frontend-react 分支
- [ ] guide §二覆盖矩阵 pill-gap→就绪、「已知缺口」callout 消除
- [ ] guide §四无矛盾 ID 表与失效叙事（旧 CR-FE-01~05 建议表已删除或重写）
- [ ] guide §五教程区无「以 frontend 缺失为前提」的叙事
- [ ] `grep -n "缺失\|已知缺口" checklists-guide.html` 逐条判定无失鲜
- [ ] INDEX.md 括注到位
- [ ] research 附件完整

### Task 4: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落 `impl-reports/task4-verification.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

另逐条自验 proposal Success Metrics：
- `grep -rn "frontend（如有）"` 归零
- TG-03 行含 delta 记法
- 4 文件 ID 连续无冲突、形制一致
- spec 侧注册表 +1 行 / code 侧 +2 行
- `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零
- 三处栈枚举行含 `frontend(+frontend-react)`
- `grep -n "缺失\|已知缺口" sdflow-init/assets/workflow/checklists-guide.html` 逐条判定

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
