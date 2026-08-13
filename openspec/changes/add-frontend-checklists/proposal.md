# Proposal · add-frontend-checklists

## Why

前端领域的评审规则集严重不完整：spec 侧 `frontend.md` 仅 5 条（交互状态 + 视觉品味），a11y 之外的性能、安全、表单、URL 状态、错误降级等设计审查面整块缺失；code 侧**没有** frontend domain——`backend.md` CR-BE-02 明文欠着「客户端框架 XSS（dangerouslySetInnerHTML/v-html）待 frontend domain 覆盖」的 IOU，React 项目的代码审只有语言无关 base 可用。2026-08-13 已完成权威源调研（react.dev / web.dev / OWASP / W3C / Front-End-Checklist）并由人逐条拍板 26 条吸收候选，本 change 将其落成正式规则资产。

## What Changes

- `spec-checklists/domains/frontend.md` 增补 8 条（FE-06 ~ FE-13）：CWV 指标锚定、请求瀑布、CSP 规划、URL 即状态、表单设计语义、错误边界与降级、i18n 就绪度、响应式断点。
- 新建 `spec-checklists/domains/frontend-react.md`（REACT-01 ~ 03，extends frontend）：Suspense 边界设计、server/client state 分离、[仅RSC] 端界切分。
- 新建 `code-checklists/domains/frontend.md`（CR-FE-01 ~ 08，extends base）：XSS sink 数据流、postMessage 校验、凭证存放、CSRF 配合、跳转/嵌入安全、长驻页面资源清理（CR-04 前端特化）、模态框焦点生命周期、表单错误提示与恢复（后两条以纯键盘交互口径措辞）。**接走 CR-BE-02 的 IOU**。
- 新建 `code-checklists/domains/frontend-react.md`（CR-REACT-01 ~ 07，extends frontend）：Effect 存在性、纯度语义违规、Compiler 时代 memo 观、React 19 API 正确性、列表 key 语义、状态所有权与 re-render 半径、[仅RSC] 边界纪律。
- 接线：`trigger-catalog.md` TG-03 领域列 `frontend` → `` `frontend`(+`frontend-react`) ``（与 TG-01/02 的 +delta 记法同构）；两侧 README 架构图 + ID 表 + 注册表登记；`code-checklists/README.md:33`「frontend（如有）」占位接实。
- 同步：`checklists-guide.html` 覆盖表（人读手册，现记「code frontend 缺失」将失鲜）；`openspec/INDEX.md:23-24` 目录级括注。
- 每个新建/增补文件头加「机械层前置」注记（lint 能确定性抓的不进清单，指明 eslint-plugin-react-hooks / jsx-a11y / TypeScript 等推荐面）。
- 研究附件随 change 落盘：`research/absorption-candidates.md`（26 条候选全文 + 来源 + 备选冻结区：a11y 10 条、多端剔除项、主动淘汰名单）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——`.openspec.yaml` 已设 `skip_specs: true`。）

本 change 是纯规则资产（Markdown checklist 内容）增量：spec 层对 domain 清单仅泛指（`spec-workflow` spec「`domains/` 栈特定 R 项归领域镜」），不枚举 domain 文件；先例 `2026-08-09-absorb-gstack-autoplan` 新增 devex domain（TG-28）时同样未为 checklist 内容建 capability。评审工作流的行为契约（TG 选用机制、镜分工）不变，变的只是可选用的领域清单集合。

## Success Metrics

- 4 个 domain 文件落盘且形制与既有一致（extends 头 + 表格 + 尾注），26 条全部落位、ID 连续无冲突。
- `grep -rn "frontend（如有）"` 归零；TG-03 行含 `+frontend-react` delta 记法；两侧 README 注册表各含 2 行新登记。
- `checklists-guide.html` 与 INDEX.md 无「frontend code 缺失」类失鲜表述。
- 备选文档在 `research/` 且含全部被裁剪候选（a11y 12 条中 10 条冻结 + 2 条捞回留痕）。

## Non-Goals

- **不动 base 与既有父层**（`spec-quality-base.md` / `code-review-base.md` / 既有 FE-01~05 均零改动；扩展是纯增量——README 扩展约定第 5 条）。
- **不新增 TG 条目**（TG-03 已存在，只改其领域列记法）。
- **不建 Vue/Svelte 等其他框架 delta**（结构已就绪，未来按需另开）。
- **a11y 与多端条目不进正式清单**（人拍板裁剪，冻结存档于备选文档；模态框焦点/表单错误恢复两条以纯交互口径捞回不在此列）。
- **不改评审 SKILL 与 workflow 机制**（选用逻辑由既有 TG 机制承载）。
- **不向下游消费仓推送**（`sdflow-init update` 是使用动作，不在本 change 交付面；发布随常规 push + 运行 checkout 升级）。

## 需求优先级

- **P0**：4 个 domain 文件 + trigger-catalog/两侧 README 接线（缺任一即功能不闭环）。
- **P1**：checklists-guide.html 与 INDEX.md 同步、研究附件落盘（一致性与留痕，不影响选用功能）。

## 假设

- 〔未核实〕标记的 8 条候选（A2/A4/A6/A8/B6/C1/C2/D6 及 B3 局部）内容依据模型知识/业界共识，未逐字核对权威页面——若个别表述不准，失效影响限于单条检查点措辞，评审期可修订（清单条目可轻易 amend，非难逆转）。
- React delta 锚 React 19.x 语义（含 Compiler）——若目标项目用 React 18-，Compiler 条目（CR-REACT-03）按触发条件自然不命中，不产生误导。

## Compliance

N/A——纯仓内 Markdown 规则资产，无 PII、无第三方数据外发、无合规约束。
