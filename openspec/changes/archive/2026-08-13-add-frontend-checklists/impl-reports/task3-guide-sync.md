# Task 3 实施报告：同步与留痕（guide + INDEX + research 附件）

## 3.1 `checklists-guide.html` 更新为目标态

文件：`sdflow-init/assets/workflow/checklists-guide.html`

6 处改动面逐块落实：

1. **§一架构图 ASCII 树**（原 L286-287）：去除 `[frontend.md ← 缺失]` 标注；两侧新增
   `frontend-react.md`（`└` 子层，沿 `backend-go.md` 画法），手工计算列对齐（右列起始列参照同
   层其余行 ~35/37 字符位，与既有行视觉一致）。原 `frontend.md` 行右侧的 `llm.md` 挪到新增行下方
   （`devex.md` / `llm.md` 同行保留原有单侧领域对照）。

2. **§二覆盖矩阵**：`frontend` 行 code 列 `pill-gap`（缺失）→ `pill-ok`（就绪，`CR-FE-01~08`）；
   spec 列计数 `FE-01~05` → `FE-01~13`。新增 `frontend-react` 独立行（spec `REACT-01~03` /
   code `CR-REACT-01~07`，均就绪，TG-03）。删除「已知缺口：`code-checklists/domains/frontend.md`」
   callout 整段（前提已消失，无改写价值——直接删除，矩阵本身已表达就绪状态）。

3. **Domain cards 区**（§三）：按 backend-go 先例，两侧 domain-grid 均新增 `frontend-react` 卡片
   （`extends: frontend`，列出 REACT-01~03 / CR-REACT-01~07 摘要）。`frontend` 卡片 desc 从
   FE-01~05 摘要扩为 FE-01~13 全量摘要（新增 CWV/请求瀑布/CSP/URL 即状态/表单语义/错误边界/
   i18n/响应式八项）；code 侧新增 `frontend` 卡片（CR-FE-01~08 摘要，原完全缺失）。

4. **§四「缺口分析与扩展建议」**：整节重写。原「高优先级：前端代码审清单」子节（含与实际
   CR-FE-01~08 同 ID 不同义的建议表 CR-FE-01~05，且 CR-FE-05=可访问性与人拍板排除 a11y 矛盾）
   **整段删除**。保留「潜在新领域」表格但移除已完成的 `frontend-react` 行（该表原第 4 行
   「先建 frontend 通用，再按框架分层」的前提已完成）；节标题改为「扩展建议：潜在新领域」并加
   一句「前端已于 add-frontend-checklists（2026-08）补齐」说明。`<h2>` 序号未级联改动——保留
   「四、」编号，只换标题文字与正文，规避重排 §五/§六 序号与 side-toc 的连锁改动（简化取向，
   语义等价于删除+重写但影响面更小）。侧栏目录 `#gaps` 链接文字同步「缺口分析」→「扩展建议」。

5. **§五「如何新增一个领域」教程**：唯一 worked example（补齐 `code-checklists/domains/frontend.md`）
   改写为「已建成回顾」叙事——开场句从「以补齐...为例，完整流程」改为「已建成回顾：...是这套
   五步流程的最近一次实跑，以它为例复盘完整流程」；步骤列表本身（建文件/写 delta/更新注册表/
   检查触发/同步 config/走 change 流程）保持不变（仍是准确的操作序列，只是叙事时态从"将要做"
   变"已做过"）；步骤后新增一句「实际条目见 `code-checklists/domains/frontend.md`（CR-FE-01~08）；
   设计审侧同批同法补齐见 `spec-checklists/domains/frontend.md`（FE-06~13）」。结尾
   `callout-info`（分层原则：React/Vue 特化建 frontend-react.md）改为「分层原则的实例」，
   注明已建成状态与 REACT-01~03 / CR-REACT-01~07 计数。

6. **自检**：
   - 标签配对：`div`/`section`/`table`/`tr`/`td`/`th`/`ul`/`li`/`ol`/`pre` 开闭标签计数逐一核对，
     全部平衡（62/62、6/6、3/3、26/26、72/72、11/11、3/3、22/22、2/2、3/3）。
   - 目录锚点：`side-toc` 六个 `href="#..."` 与对应 `<section id="...">` 一一对应（`arch` /
     `matrix` / `domains` / `gaps` / `howto` / `conventions`），均有效。
   - `grep -n "缺失\|已知缺口" checklists-guide.html`：唯一命中为 §二矩阵图例说明句
     「绿色 = 已就绪，红色 = **缺失**且应补，灰色 = 设计上不需要」——这是颜色图例的通用释义，
     不是对 frontend 的失鲜断言，判定为**无失鲜**。
   - 通读内容一致性：`frontend`/`frontend-react` 在架构图、矩阵、domain cards、§四、§五、§六
     「分工」表中的表述互不矛盾；ID 计数（FE-01~13 / REACT-01~03 / CR-FE-01~08 /
     CR-REACT-01~07）与 `spec-checklists/domains/frontend*.md`、`code-checklists/domains/frontend*.md`
     实际文件核对一致。

## 3.2 `INDEX.md` 括注

文件：`openspec/INDEX.md` L23-24（`opsx-init:rules` 托管区块内）

沿「含 devex」先例扩注：
- 设计审规则集行：`（base BASE-NN + domains，含 devex）` → `（base BASE-NN + domains，含 devex、frontend(+frontend-react)）`
- 代码审规则集行：`（base CR-NN + domains）` → `（base CR-NN + domains，含 frontend(+frontend-react)）`

两行均为**新增**注记（原文本无 frontend 相关失鲜表述，不是失鲜修正）。

## 3.3 research 附件核验

文件：`openspec/changes/add-frontend-checklists/research/absorption-candidates.md`

核验结果：**完整，通过**。

- **拍板头注**：文件开头「拍板结果（2026-08-13 用户）」段落存在，含调研路径、过滤判据、标记说明。
- **26 条**：A 组（spec-frontend 增补）8 条 A1-A8 + B 组（code-frontend 新建）8 条 B1-B8 +
  C 组（spec-react 新建）3 条 C1-C3 + D 组（code-react 新建）7 条 D1-D7 = 8+8+3+7 = **26 条**，与
  实际交付计数一致（FE-06~13=8、CR-FE-01~08=8、REACT-01~03=3、CR-REACT-01~07=7）。
- **备选冻结区**：§E 存在，含 E1（a11y 全路 12 条，W3C 一手来源）、E2（多端条目，剔除）、
  E3（调研中主动淘汰条目），均标注冻结/不进正式清单。
- **来源清单**：§F「调研诚实边界」存在，逐条列出〔未核实〕标记条目、spec-review 前端领域镜复核
  结论、未抓取来源、子代理调研故障复盘。

无需改动此文件。

## 完成状态

3.1/3.2/3.3 全部完成，`sdflow-init/assets/workflow/checklists-guide.html`（改动）与
`openspec/INDEX.md`（改动）已 `git add` + 普通 commit；research 附件核验通过、未改动。
