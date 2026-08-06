# Task 4 实现报告：code-checklists 吸收五类缺口并新建 LLM 领域清单

## 做了什么

按 `design.md` §4「checklist 吸收」+ §5「TG-27」+ `tickets.md` Task 4 逐条落地：

1. `sdflow-init/assets/workflow/code-checklists/code-review-base.md`：新增 CR-10（命令/代码注入）、
   CR-11（枚举/取值完备性）两条 base 层规则。
2. `sdflow-init/assets/workflow/code-checklists/domains/backend.md`：新增 CR-BE-03（DB 层竞态）；
   CR-BE-02 检查点扩点补服务端模板渲染 XSS，并注明客户端框架面（`dangerouslySetInnerHTML`/`v-html`）
   待 frontend domain、本条不声称覆盖。
3. 新建 `sdflow-init/assets/workflow/code-checklists/domains/llm.md`：CR-LLM-01（输出信任边界）+
   CR-LLM-02（prompt 一致性），标注 `code-review-only domain`。
4. `sdflow-init/assets/workflow/code-checklists/README.md`：注册表加 `domains/llm.md` 行
   （extends base，ID 前缀 `CR-LLM-`）；「选用规则」示例块加 `命中 TG-27(LLM 集成面) → code-review-base + llm` 行。
5. `sdflow-init/assets/workflow/trigger-catalog.md`：类别 A「技术栈（决定过哪些领域清单）」表追加
   TG-27 行（措辞「代码消费 LLM/agent 产出并持久化/执行/外呼」+ 排除句 + `code-review-only domain` 行内注）；
   HR-TG 成员行 `TG-26` 后追加 `TG-27`。
6. 副带修复：`sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py::test_reads_real_catalog_members`
   是读真实 `trigger-catalog.md` 断言 HR-TG 成员集的 golden 测试，我对 catalog 的编辑（第 5 点）令其从
   8 个成员变 9 个，必然使该测试变红——已确认变红（见下方「TDD 契约」一节），随即把断言更新为 9 个成员
   （含 `TG-27`）。此文件不在我的文件所有权清单内（清单只列 `code-checklists/` + `trigger-catalog.md`），
   但它是对 `trigger-catalog.md` 单一源直接、机械的验证，属于「不留半成品」而非越界改动。

措辞纪律：全部新条目遵循「语言无关 + 括号里给多语言示例」（如 CR-10 括号内同时给 Python
`subprocess(shell=True)`/`os.system()`、JS `new Function()`、Go `os/exec.Command("sh","-c",...)`）。
ID 纪律：CR-10/CR-11/CR-BE-03/CR-LLM-01/CR-LLM-02 全部新号，未复用/重排既有 ID（`grep` 核实见下）。

## 验收标准逐条证据

1. **base 清单含 CR-10（命令/代码注入）**
   `sdflow-init/assets/workflow/code-checklists/code-review-base.md:19`：
   > `| CR-10 | **命令 / 代码注入** | 外部输入拼进可执行命令或代码前先隔离：拼 shell 命令用参数数组而非字符串插值（禁 \`subprocess(..., shell=True)\` / \`os.system()\` / 反引号拼接 直接插值外部输入）；\`eval\`/\`exec\` 类动态求值（\`eval()\` / \`exec()\` / \`new Function()\` / \`os/exec.Command("sh","-c",...)\`）执行的内容若来自模型输出或外部输入，须走沙箱或白名单，不得未经校验直接执行 |`

2. **base 清单含 CR-11（枚举/取值完备性）**
   `sdflow-init/assets/workflow/code-checklists/code-review-base.md:20`：
   > `| CR-11 | **枚举 / 取值完备性** | 新增枚举值 / 状态串 / 类型常量后，逐个消费点 trace 是否已处理该新值（**必须读 diff 外代码**——grep 该枚举的兄弟取值找出全部消费点，逐个确认新值有无被同等处理，不能只看本次 diff 改了哪些行）；allowlist / 过滤数组需同步核对新增值是否已收录；\`switch\`/\`case\`/\`if-else\` 链的默认分支不得静默 fall-through 到错误行为（未识别的取值须显式报错或拒绝，而非被当作某个已知分支处理） |`
   含明写「必须读 diff 外代码」（design §4 逐字要求）。

3. **backend 领域含 CR-BE-03（DB 层竞态）**
   `sdflow-init/assets/workflow/code-checklists/domains/backend.md:12`：
   > `| CR-BE-03 | **DB 层竞态** | 含并发写路径的 DB 操作 | find-or-create 类操作无唯一索引兜底会在并发下重复插入（先查后插不是原子操作）；check-then-set（先读状态再据其更新）须用带旧值条件的原子 \`UPDATE ... WHERE 状态=旧值\`，而非读出来判断后再单独写；状态迁移的多步更新非原子会导致中间态可见或非法跳变（双跳）；绕过 ORM/模型层校验直接写 DB（原生 SQL/批量脚本）会漏掉模型内建的约束检查 |`

4. **CR-BE-02 扩点覆盖服务端模板渲染 XSS，注明客户端框架待 frontend**
   `sdflow-init/assets/workflow/code-checklists/domains/backend.md:11`（CR-BE-02 检查点列追加句）：
   > `…；用户可控数据进不安全 HTML 渲染前防 XSS——**仅服务端模板渲染场景**（如 Jinja2 \|safe / Django mark_safe / Rails html_safe / Go template.HTML）；客户端框架渲染（dangerouslySetInnerHTML / v-html 等）待 frontend domain 覆盖，本条不声称覆盖`

5. **新建 llm.md，含 CR-LLM-01（输出信任边界）+ CR-LLM-02（prompt 一致性）**
   `sdflow-init/assets/workflow/code-checklists/domains/llm.md:11-12`（全文见文件；两行摘录）：
   > `| CR-LLM-01 | **输出信任边界** | 代码消费外部/不可信 LLM 或 agent 产出并持久化/执行/外呼 | LLM 生成的结构化值（email / URL / 名称 / JSON 对象等）在持久化或对外发送前须做格式与 shape 校验…LLM 生成的 URL 在发起外呼前须过 allowlist（防 SSRF…）；LLM 输出写入知识库/向量库/RAG 索引前须做防注入处理（防存储型 prompt 注入…） |`
   > `| CR-LLM-02 | **Prompt 一致性** | 新增/修改 prompt 或工具（tool/function）声明 | prompt 中的列表/序号采用 1-indexed…prompt 里声称提供的工具/能力与代码实际的 wiring…一致…限额/约束…只在单一处声明… |`

6. **清单注册表登记 LLM 领域行（extends base，ID 前缀 CR-LLM-）**
   `sdflow-init/assets/workflow/code-checklists/README.md`（登记表新行）：
   > `| \`domains/llm.md\` | base | LLM 集成面（代码消费 LLM/agent 产出） | \`CR-LLM-\` |`

7. **选用规则示例块含 `TG-27 → llm.md` 映射行**
   `sdflow-init/assets/workflow/code-checklists/README.md`（选用规则代码块新行）：
   > `命中 TG-27(LLM 集成面) → code-review-base + llm`

8. **触发目录领域清单段含 TG-27 行，措辞含排除句 + code-review-only 行内注**
   `sdflow-init/assets/workflow/trigger-catalog.md:47`（类别 A 表新行，全文）：
   > `| TG-27 | **代码消费 LLM/agent 产出**并持久化/执行/外呼（工具 wiring、RAG/知识库写入等；排除句：评审工作流自身读取/校验同会话内受信任 agent 自报的控制面锚〔如 <!-- sdflow:… --> 〕不算，只有消费**外部/不可信** LLM 产出（用户对话内容、RAG 检索结果、第三方 agent 产出）才算） | — | \`llm\`（**code-review-only domain**，spec-checklists 侧无对应文件） | — | — |`
   触发措辞逐字匹配 design §5 定案句「代码消费 LLM/agent 产出并持久化/执行/外呼」；排除句逐字匹配
   tickets.md Global Constraints 的 TG-27 排除句；`code-review-only domain` 在「领域」列行内注明（非
   另开脚注），满足 design §5「注一句『code-review-only』防未来读者误判缺失」。

9. **HR-TG 成员行追加 TG-27，`hr_tg_intersect.py` 实跑正确 parse**
   `sdflow-init/assets/workflow/trigger-catalog.md`（HR-TG 成员行）：
   > `> 成员：**TG-04, TG-06, TG-07, TG-08, TG-09, TG-16, TG-17, TG-26, TG-27**`

   实跑命令与输出：
   ```
   $ /usr/bin/python3 sdflow-init/assets/workflow/tools/hr_tg_intersect.py \
       --tg-set "TG-27,TG-01" --trigger-catalog sdflow-init/assets/workflow/trigger-catalog.md
   hit:[TG-27]｜依据模型判定:[TG-01,TG-27]
   <!-- sdflow:hr-tg v1 hit="TG-27" declared="TG-01,TG-27" -->
   EXIT=0
   ```
   TG-27 被正确识别为 HR-TG 成员（`hit=`含之）、TG-01 正确不在 HR-TG（未入 hit，符合预期——TG-01
   不是 HR-TG 成员）。回归 sanity（未申报，纯自证脚本未被我误改）：
   ```
   $ /usr/bin/python3 sdflow-init/assets/workflow/tools/hr_tg_intersect.py \
       --tg-set "TG-99" --trigger-catalog sdflow-init/assets/workflow/trigger-catalog.md
   [hr_tg_intersect] FAIL: declared 含「触发词目录」全集外 TG（不存在，M-new）: TG-99
   EXIT=1
   ```
   fail-closed 路径未受影响。零代码改动（`hr_tg_intersect.py` 本身未动，动态 parse 单一源生效）。

10. **全部新条目为新 ID，未复用/重排既有 ID**
    ```
    $ grep -rn "CR-10\|CR-11\|CR-BE-03\|CR-LLM-01\|CR-LLM-02" sdflow-init/assets/workflow/code-checklists/
    code-review-base.md:19: CR-10 …
    code-review-base.md:20: CR-11 …
    domains/backend.md:12:  CR-BE-03 …
    domains/llm.md:11:      CR-LLM-01 …
    domains/llm.md:12:      CR-LLM-02 …
    ```
    每个 ID 全仓恰出现一次（新增行），既有 ID（CR-01~09、CR-BE-01~02）未改号未重排——`git diff` 对
    `code-review-base.md`/`backend.md` 显示均为纯新增行，无既有行被移动或改号。

## TDD 契约（本票新增/修改的断言性测试）

本票产物以 markdown 数据资产为主，无自动化测试覆盖（tasks.md 测试覆盖图明写
`checklists/llm.md 内容 → 人审`）。唯一有机械信号、且被我改动过的断言性测试文件是
`sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py::test_reads_real_catalog_members`：

- **先确认会红**：编辑 `trigger-catalog.md` 加入 TG-27 到 HR-TG 成员行后、在改测试断言之前，跑：
  ```
  $ /usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py::test_reads_real_catalog_members -v
  FAILED …AssertionError: assert {'TG-04', ... 'TG-27', ...} == {'TG-04', ... }  (Extra items in the left set: 'TG-27')
  ```
  确认为真红（预期内：我改了单一源，断言集合还是旧的 8 个）。
- **修复**：把断言的成员集合字面量从 8 个改为 9 个（追加 `"TG-27"`），docstring 同步说明。
- **复测绿**：
  ```
  $ /usr/bin/python3 -m pytest sdflow-init/assets/workflow/tools/tests/test_hr_tg_intersect.py sdflow-init/assets/workflow/tools/tests/test_hr_tg_cross_tool.py sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py -q
  188 passed in 0.89s
  ```

## 回归验证（我改动范围内 + 消费者面）

- `/usr/bin/python3 -m pytest sdflow-init/ -q` → **1143 passed, 4 skipped in 198.25s**（全绿，含
  anchor_lint / hr_tg_intersect / hr_tg_cross_tool / init / resolve_workflow / resolve_models 等全部
  既有用例，未破坏任何既有测试）。
- 额外核查：`sdflow-maintain`、`sdflow-init/tests/test_resolve_*` 中提及 `trigger-catalog`/
  `code-checklists` 的用例均用合成 fixture（`tmp_path` 临时目录），未读真实文件内容，不受本票文本
  编辑影响（已逐一 grep 确认，见对话内检索）。

## 与其他 Task 的边界确认

- 未改 `sdflow-code-review/SKILL.md`（Task 3）、`tools/*.py`（Task 1/2，`anchor_lint.py`/
  `lens_metric_emit.py`/`hr_tg_intersect.py` 均零改动，仅动其配套测试里一条读真实 catalog 的断言）、
  `docs/`（Task 5）。
- 未改四件套（proposal/design/specs/tasks.md），未勾 `tickets.md`/`tasks.md` 任何复选框。

## Concerns

无功能性 Concern。唯一需编排层知悉的点：本票为满足自身验收标准 9（HR-TG 成员行追加 TG-27 且脚本
实跑验证）而顺带修复了 `test_hr_tg_intersect.py` 里一条读真实 catalog 的 golden 断言——该文件严格说
不在 Task 4 的文件所有权清单内，但改动是我对 `trigger-catalog.md`（清单内文件）编辑的直接、必然后果，
且已用「先红后绿」验证。若双轴审认为此修复应归属 Task 1/2 或收尾票，请告知，我可以把它拆出。
