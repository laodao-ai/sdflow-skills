# Tasks · add-frontend-checklists

> 追溯：本 change `skip_specs: true`（见 proposal Capabilities），任务不挂 Requirement ID，
> 逐条标注 proposal 优先级（P0/P1）与 design 决策号；条目内容源 = `research/absorption-candidates.md`（已拍板）。

## 1. Domain 条目落盘（P0）

> [spec-review-amendment] 1.1~1.4 共同要求：候选表列头无独立「触发条件」列，落盘套进既有四列表（ID/规则/触发条件/检查点）时 MUST 为**每条**提炼独立触发条件短语（沿 FE-01~05 / CR-BE-01/02 的「新增 X / 含 Y 操作」简短句式），不得留空或以检查点散文充数——26 条中约半数（A4/A5/A6/B2/B3/B4/B5/C2/D2/D6 等）无现成短语可抄，提炼是显式生成步骤。

- [x] 1.1 `spec-checklists/domains/frontend.md` 增补 FE-06~FE-13（候选表 A 组 8 条，逐条对照原文检查点）+ 文件头机械层前置注记〔D5〕
- [x] 1.2 新建 `spec-checklists/domains/frontend-react.md`：REACT-01~03（C 组，extends frontend，REACT-03 标 `[仅RSC]`〔D6，触发条件措辞见 design D6 细化版〕）+ 机械层前置注记
- [x] 1.3 新建 `code-checklists/domains/frontend.md`：CR-FE-01~08（B 组 **B1~B8，B7/B8 正式条文已在候选表 B 组起草**〔spec-review-amendment〕；CR-FE-06 注「CR-04 的前端特化」〔D4〕；CR-FE-07/08 以纯键盘交互口径措辞，不用 a11y/辅助技术叙述）+ 机械层前置注记
- [x] 1.4 新建 `code-checklists/domains/frontend-react.md`：CR-REACT-01~07（D 组，extends frontend，CR-REACT-07 标 `[仅RSC]`〔D6〕）+ 机械层前置注记

## 2. 接线（P0）

- [x] 2.1 `trigger-catalog.md` TG-03 领域列：`frontend` → `` `frontend`(+`frontend-react`) ``（与 TG-01/02 记法同构）
- [x] 2.2 `spec-checklists/README.md`：架构图加 frontend-react 分支、ID 约定表加 `REACT-` 行、领域注册表加 frontend-react 行
- [x] 2.3 `code-checklists/README.md`：架构图加 frontend 链、选用规则 L33「frontend（如有）」接实为 `frontend(+frontend-react)`、ID 表加 `CR-FE-`/`CR-REACT-` 行、注册表加 2 行；[spec-review-amendment·人拍板指针式] 另加一行扩展约定**指针**（该侧原无此节；查表式规则按仓内纪律用指针不复制文本，避免 +1 漂移面）：「扩展约定（五步）见 `../spec-checklists/README.md` §如何新增一个领域，两侧同法、ID 用 CR- 前缀」
- [x] 2.4 [spec-review-amendment] `code-checklists/domains/backend.md:11`：CR-BE-02 检查点内「客户端框架渲染（`dangerouslySetInnerHTML` / `v-html` 等）待 frontend domain 覆盖，本条不声称覆盖」改为「客户端框架渲染 XSS 见 `domains/frontend.md` CR-FE-01（本条聚焦服务端模板渲染）」；不动该条其余内容（4 镜 + voice 收敛的 IOU 关闭项）
- [x] 2.5 [spec-review-amendment] 三处栈枚举文本追加 react delta：`sdflow-spec-review/SKILL.md:223` 与 `sdflow-init/SKILL.md:195` 的 `（backend·go / embedded·ml307c·esp32 / frontend）` → `（backend·go / embedded·ml307c·esp32 / frontend(+frontend-react)）`；`config.template.yaml:24` 同式（`sdflow-code-review/SKILL.md:680` 用「…」省略式列举、非穷举清单，不改）

## 3. 同步与留痕（P1）

- [x] 3.1 `checklists-guide.html` 更新为目标态——[spec-review-amendment] 6 镜收敛：改动面远超「覆盖表」一处，逐块清单如下（不动脚本/样式；改后自检标签配对与目录锚点 + **通读内容一致性**——标签自检查不出内容矛盾）：
  - §一架构图 ASCII 树（L286-287）：去「`[frontend.md ← 缺失]`」标注，两侧补 frontend-react 分支（沿 backend-go 画法；`<pre>` 手工空格对齐，改后目视核对齐）
  - §二覆盖矩阵（L358 附近 pill-gap → 就绪）+「已知缺口」callout（L380 整段前提消失，删除或改写为已覆盖记述）
  - domain cards 区（L394-450）：按 backend-go 先例判断是否需 frontend/frontend-react 新卡片与矩阵独立行
  - §四「缺口分析与扩展建议」（L454-489）：整节以「code-frontend 缺失」为前提，且其建议 ID 表 CR-FE-01~05（含 CR-FE-05=可访问性，与人拍板排除 a11y 直接矛盾）与实际交付 CR-FE-01~08 同 ID 不同义——删除或彻底重写，处理 `<h2>` 硬编码序号（一~六）级联
  - §五「如何新增一个领域」教程（L490-517）：唯一 worked example =「补齐 code-frontend」，前提失效——换例或改为「已建成回顾」叙事，并加一行「实际条目见 `code-checklists/domains/frontend.md`」
- [x] 3.2 `openspec/INDEX.md` L23-24：沿既有「含 devex」括注先例扩注（如「含 devex、frontend(+frontend-react)」）[spec-review-amendment 定性澄清：此处为**新增**注记（现两行无 frontend 失鲜文本可修），非失鲜修正]
- [x] 3.3 核验 `research/absorption-candidates.md` 附件完整（26 条 + 备选冻结区 + 拍板头注 + 来源清单）

## 4. 收尾核验（P0）

- [x] 4.1 proposal Success Metrics 逐条自验：`grep -rn "frontend（如有）"` 归零；TG-03 行含 delta 记法；spec 侧注册表 +1 行 / code 侧 +2 行〔spec-review-amendment 修正数〕；4 文件 ID 连续无冲突、形制一致（extends 头 + 表 + 尾注）；[spec-review-amendment 补 P1 交付面核验锚] `grep -rn "待 frontend domain 覆盖" sdflow-init/assets/workflow/` 归零；三处栈枚举行含 `frontend(+frontend-react)`；`grep -n "缺失\|已知缺口" sdflow-init/assets/workflow/checklists-guide.html` 逐条人工判定 + 通读 guide §四/§五 确认无矛盾 ID 表与失效叙事
- [x] 4.2 全仓 pytest 兜底（`/usr/bin/python3 -m pytest`），确认无既有断言受影响
