---
schema_version: 1
change: add-frontend-checklists
branch: feat/add-frontend-checklists
generated_at: 2026-08-13T15:32:43+08:00
decision_hash: b26635380818
---

# 决策纪要 · add-frontend-checklists

## 目标态

前端领域两级（通用 / React 19）× 两侧（spec 设计审 / code 代码审）共 4 个 domain checklist 文件齐备并完成接线（README 注册 + trigger-catalog TG-03 delta 记法 + INDEX/guide 同步），条目 = 已拍板的 26 条权威调研候选；备选（a11y/多端/淘汰）冻结存档随 change。

## 承重约束

1. **扩展走既有「通用 base + 领域 delta」架构，纯增量**：只写本层新增规则、`extends:` 声明父层、不改 base/父层、注册表登记一行。
   锚：`sdflow-init/assets/workflow/spec-checklists/README.md:82-88`（扩展约定五步）。[spec-review-amendment 锚订正：code 侧 README **无**扩展约定节（68 行，注册表后即尾注）——「同构」仅指注册表/ID 表结构；扩展纪律以 spec 侧为单一源，code 侧缺节随 task 2.3 补齐。]
2. **ID 前缀无冲突**：spec 侧 frontend 增补沿用 `FE-`（从 FE-06 起，ID 不复用不重排，README:53）；新层 `REACT-` 未被占用；code 侧 `CR-FE-` / `CR-REACT-` 未被占用。
   锚：`spec-checklists/README.md:45-53` ID 表、`code-checklists/README.md:37-47` ID 表。
3. **分层选用记法 = 括号 +delta 式**：TG-03 的领域列由 `frontend` 改为 `` `frontend`(+`frontend-react`) ``，与 TG-01 `backend`(+`backend-go`)、TG-02 `embedded`(+芯片 delta) 同构；react delta 的触发子条件 = 变更实际涉及 React 栈（与 backend-go 语言 delta 同语义），**无需新触发机制**。
   锚：`trigger-catalog.md:44-46`；`spec-checklists/README.md:30-37` 选用规则。
4. **TG-03/frontend 消费面完整清单**（grep 实测，2026-08-13）：`trigger-catalog.md:46`、`code-checklists/README.md:33`（「frontend（如有）」占位正好接实）、两侧 README 架构图+注册表、`checklists-guide.html`（覆盖表含「frontend.md ← 缺失」记述，本 change 后失鲜）、`INDEX.md:23-24`（目录级括注）。`spec-quality-base.md` 仅叙述性提及（BASE-28 特化方向、审计说明），与新文件一致无需改。
   锚：本 change 拷问期 grep 输出（`grep -rn "TG-03" / "frontend"` 于 assets/workflow 与四个评审 SKILL 目录）。
   [spec-review-amendment 清单补漏（评审多镜 grep 复测）]：原清单漏 4 处消费面——`code-checklists/domains/backend.md:11`（CR-BE-02 IOU 句，本 change 兑现后原句失鲜）、`sdflow-spec-review/SKILL.md:223`（领域镜派发指令的栈枚举，活执行文本）、`sdflow-init/SKILL.md:195` 与 `config.template.yaml:24`（栈枚举）；INDEX.md:23-24 定性订正为**新增**括注（沿「含 devex」先例），该两行现无 frontend 失鲜文本。
5. **26 条条目内容与归属已由人拍板**：24 条候选全收 + B6 独立成条 + a11y #3/#5 以纯交互口径捞回进 code-frontend。
   锚：2026-08-13 对话拍板（「都收吧。其他的都同意推荐」）+ 候选表 `scratchpad/research/absorption-candidates.md` 拍板头注。
6. **change 目录可携带四件套之外的附件**：`decision-memo.md` 本身即先例；研究附件随 change 落盘、归档随行合法。
   锚：本仓既有 change 目录惯例（impl-reports/、verify-report.md 等均为四件套外附件）。
7. **候选表中 8 条标〔未核实〕**（A2/A4/A6/A8/B6/C1/C2/D6 及 B3 局部）：依据模型知识/业界共识，未逐字核对权威页面；其余条目有已打开的权威来源（react.dev 6 页、web.dev 3 页、OWASP 5 页、W3C 16 页、Front-End-Checklist）。写入正式清单时不区分呈现（清单条目本身不带来源），来源表留研究附件。
   锚：`absorption-candidates.md` §F 调研诚实边界。

## 拍板决策

1. **落点与编号**（人拍板 2026-08-13）：
   - A 组 8 条 → `spec-checklists/domains/frontend.md` 增补 **FE-06 ~ FE-13**；
   - B 组 8 条 → 新建 `code-checklists/domains/frontend.md` **CR-FE-01 ~ CR-FE-08**（含 CR-FE-07 模态框焦点生命周期、CR-FE-08 表单错误提示与恢复——**以纯键盘交互正确性口径措辞，不用 a11y/辅助技术叙述**）；
   - C 组 3 条 → 新建 `spec-checklists/domains/frontend-react.md` **REACT-01 ~ REACT-03**（extends frontend）；
   - D 组 7 条 → 新建 `code-checklists/domains/frontend-react.md` **CR-REACT-01 ~ CR-REACT-07**（extends frontend）。
2. **B6 独立成条**（人拍板）：长驻页面资源清理不并入 CR-04，条文内注明「CR-04 的前端特化」关系。
3. **备选文档随 change 落盘**（人拍板）：a11y 其余 10 条（完整检查点+W3C 来源）、多端剔除项、主动淘汰名单，冻结存档于 `openspec/changes/add-frontend-checklists/research/`，归档时随行；正式清单不收，除非人改口（记忆 frontend-checklist-scope-exclusions 同步在案）。
4. **RSC 条目标 `[仅RSC]`**：REACT/CR-REACT 中 RSC 相关条目触发子条件 = 项目使用 RSC 框架。
5. **每个新建/增补 domain 文件头加「机械层前置」注记**：一行说明该域推荐的 lint 面（eslint-plugin-react-hooks 含 Compiler 规则 / eslint-plugin-jsx-a11y / TypeScript），lint 能确定性抓的不进清单——基准 1 的落地（设计自由度内，随四件套一并终审）。
6. **checklists-guide.html 覆盖表同步更新**（fold 判定：同 capability ∧ 高耦合 ∧ 低增量——它就是这套 checklist 的人读手册且已预写扩展方向）；仓根 `openspec/workflow/` 无镜像（D13 后仅 WORKFLOW-GUIDE.md），无双写面。
7. **INDEX.md:23-24 括注轻量同步**（标注 frontend 链就绪），目录级登记，不逐文件列。
8. **条目语言与形制沿既有**：中文、紧凑表格（ID/规则/触发条件/检查点）、每文件尾注「规则集 v1 · extends … · 项目无关」；四文件均为纯 Markdown，无脚本/测试面。
