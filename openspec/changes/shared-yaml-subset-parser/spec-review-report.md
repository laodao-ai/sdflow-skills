# spec-review-report · shared-yaml-subset-parser

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:hr-tg v1 hit="TG-08" declared="TG-08,TG-18" evidence="引入 yq 外部依赖（TG-08），有测试计划（TG-18）" -->
<!-- sdflow:declared-sites v1 declared="design-voice,hr-tg" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="section-not-found" host="claude" runner="claude" reason_code="exec-error" findings="0" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" host="claude" runner="claude" reason_code="exec-error" findings="0" truncated="false" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="10" 采纳="10" 裁掉="0" defer="0" 独立="9" sev="致2/高3/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="7" 采纳="5" 裁掉="2" defer="0" 独立="4" sev="致1/高3/中1/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="claude" site="design-voice" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->

## 评审范围

- **Change**: `shared-yaml-subset-parser`
- **触发命中**: TG-08（外部依赖 yq）、TG-18（测试计划）
- **HR-TG**: TG-08 命中（外部依赖做错运行期爆炸/难回退）
- **镜 roster**: autoplan（CEO 广审，Claude+Codex 双声）+ 接地镜 + 对抗镜 ×2
- **outside-voice**: design-voice 回落同族 fallback（autoplan 无 codex outside-voice section → guard `section-not-found` → 回落但 fallback 派发失败 → reason_code=exec-error）

---

## Findings（已合并去重 + 对抗裁决，按严重度排序）

### 🔴 CRITICAL — F1: duplicate-key/tab-indent 检测在 yq 方案下结构性不可保留

**四方独立确认**：Codex CEO (C4) · Claude CEO (CRITICAL) · 对抗镜1 (F1/F2) · 对抗镜2 (F3)

`ship_gate.py:938` 的现有设计是 fail-closed 安全门——frontmatter 出现重复 `ship-gate:` 键时返回 `("ship-gate", "duplicate-key")` 拒绝放行。design.md/tasks.md 4.3 声称「在 yq 读出的 dict 上验证」，但：

- **对抗镜1 实测**：yq 对重复键**不报错**（exit 0），json.loads 静默取最后值——重复键信息在到达 Python dict 之前永久丢失
- **tab-indent 同理**：yq 遇 tab 缩进整体解析失败，给出通用 go-yaml 词法错误，无法反解析出 `tab-indent` 这个精细分类
- **联网核实**：[mikefarah/yq Issue #2228](https://github.com/mikefarah/yq/issues/2228) 确认 yq 对重复键静默取最后值

**后果**：ship-gate frontmatter 因 merge 冲突出现 `design_approved: true` + `design_approved: false` 时，现状 fail-closed 拒绝；迁移后静默采信最后值放行。**这是安全门失效且无任何红色信号。**

**裁决**：**采纳（CRITICAL）**。design/spec/tasks 需要承认这些精细诊断不可迁移，并由人拍板：
- 选项 A：duplicate-key/tab-indent 保留轻量原始文本预扫描（不算「手搓 YAML 解析」——只做键名出现次数/缩进字符检测，基准5 打的是通用 YAML 解析器），R10 显式排除这几个函数
- 选项 B：接受这些诊断能力退化（需人明确确认安全门降级可接受）

### 🔴 CRITICAL — F2: `_yq()` 封装把「键不存在」和「真解析错误」混为一谈

**来源**：对抗镜2 (F1)

design.md 的 `_yq()` 参考实现：当 `default is not None` 时，**任何**非零退出（包括文件损坏、YAML 语法错误）都被静默吞成 default 值。而 design §1 给出的全部四个读操作示例都带 `default=`。

- **直接违反 R7**（fail-loud，不静默降级）
- **直接与 design.md §4 错误处理表矛盾**（表中声称「YAML 语法错误 → exit 1 → raise」）

**裁决**：**采纳（CRITICAL）**。`_yq()` 必须区分：exit 0 + stdout=null → 用 default（键缺失）；exit≠0 → 必须 raise（无论何种原因）。[spec-review-amendment]

### 🟠 HIGH — F3: 多文档 YAML 下 json.loads 崩溃

**来源**：对抗镜1 (F4，实测确认) · Codex CEO (C3)

**实测**：yq 对多文档输出多个 JSON 值拼接，`json.loads` 抛 `JSONDecodeError: Extra data`。R3 scenario 声称「多文档 yq 正常处理」——**实测为假**。

虽然 config.yaml 和 frontmatter 目前均为单文档，但 config.yaml 的 `context:` 段含大段自由格式文本，**粘贴时丢缩进可能意外产生文档边界**（对抗镜1 实测确认此场景）。

**裁决**：**采纳（HIGH）**。`_yq()` 封装需要多文档防御（如 json.loads 前检测是否只含一个 JSON 值），R3 scenario 需修正。[spec-review-amendment]

### 🟠 HIGH — F4: frontmatter 未闭合行为是内容相关的偶然性，非确定性契约

**来源**：对抗镜1 (F3，实测三场景)

**实测**：`--front-matter=extract` 遇到未闭合 frontmatter 时，行为取决于 body 正文**碰巧是不是合法 YAML**——注释行→成功(exit 0)、带冒号散文→失败(exit 1)、无 frontmatter→把正文当 YAML 标量返回。R5 scenario 「未闭合 → yq 非零退出」写成确定性契约是错的。

**裁决**：**采纳（HIGH）**。spec R5 该 scenario 需改为 best-effort 声明；`_yq()` 封装需补返回类型 sanity check（预期 dict，非 dict → 视为坏块）。[spec-review-amendment]

### 🟠 HIGH — F5: 版本检测只查 mikefarah 不查最低版本

**来源**：Codex CEO (C2) · Claude CEO

design 声称 v4.53+，但 spec R1 和 `check_dependencies()` 只做 `grep -q "mikefarah"`，不查版本号。`--front-matter` 选项在 v4.16+ 才可用。

**裁决**：**采纳（HIGH）**。spec R1 增加版本门 scenario。[spec-review-amendment]

### 🟠 HIGH — F6: `_yq()` 缺身份校验——5/7 脚本可能调用 kislyuk/yq（pip 版）

**来源**：Claude CEO

身份区分（mikefarah vs kislyuk）只在 setup.sh（一次性、不阻断）和 init.py 的 `_check_yq()` 做。其余 5 个脚本的 `_yq()` 只做 `shutil.which("yq")`，不判身份。kislyuk/yq 是 jq 语法，与 design.md 的表达式完全不兼容。

**裁决**：**采纳（HIGH）**。`_yq()` 封装需加身份校验（首次调用时 `--version` 探测 + 进程内缓存）。[spec-review-amendment]

### 🟠 HIGH — F7: yq 表达式注入风险

**来源**：Codex CEO (C7)

`_yq(f'.schema = "{new_schema}"', ...)` 直接 f-string 插值——如果 `new_schema` 含 `"` 或 yq 特殊字符，会产生表达式注入。

**裁决**：**采纳（HIGH）**。改为 yq 的 `env()` 函数传值或对值做转义。[spec-review-amendment]

### 🟠 HIGH — F8: CI（mechanical-gates.yml）缺 yq 安装步骤

**来源**：Claude CEO

本仓 CI 对 openspec CLI 有显式安装 + 钉版本的处理范式，但 tasks/design 完全没提 yq 入 CI。

**裁决**：**采纳（HIGH）**。tasks.md 补一条 CI 任务。[spec-review-amendment]

### 🟠 HIGH — F9: 既有测试精确诊断断言不可复现

**来源**：对抗镜2 (F2)

`test_impl_route.py:138-149` 的 `unknown-value:` 前缀断言依赖手搓逐行扫描器的局部诊断能力——yq 对文档级语法错误整体失败，无法产出同样精度的诊断。tasks.md 未提及重写这些测试断言。

**裁决**：**采纳（HIGH）**。tasks.md 需显式列出需要重写断言的测试用例清单。[spec-review-amendment]

### 🟡 MEDIUM — F10: Windows subprocess 编码缺 encoding="utf-8"

**来源**：对抗镜2 (F4)

`_yq()` 用 `text=True` 无 `encoding=`，Windows 默认用 GBK/cp936。本仓既有代码（`impl_route.py:435`）已有 `encoding="utf-8", errors="replace"` 惯例。

**裁决**：**采纳（MEDIUM）**。`_yq()` 模板补齐。[spec-review-amendment]

### 🟡 MEDIUM — F11: Windows --front-matter stderr 噪音

**来源**：对抗镜1 (F5，实测)

yq v4.53.3 在 Windows 上每次 `--front-matter` 调用都在 stderr 打 `level=ERROR msg="Failed to remove temp file"`（exit 0）。不影响正确性但会误导使用者和 CI 日志扫描。

**裁决**：**采纳（MEDIUM）**。在 design `_yq()` 封装说明中显式记录「不检查 stderr 内容，只信 returncode」。

### 🟡 MEDIUM — F12: _yq() 不共享理由被既有 sibling-import 反驳

**来源**：对抗镜2 (F6)

`impl_route.py:48-70` 已有跨脚本 sibling-import 模式（从 ship_gate 导入 FenceTracker 等）。「各脚本零依赖不变量不允许互 import」不准确——不允许的是 import 第三方包，不是 stdlib-only 的 sibling import。7 份手抄 `_yq()` 以后改一处漏另 6 处时，就是本 change 控诉的"各自漂移"的同构复现。

**裁决**：**需拍板 Q2**——接受 7 份各自抄（按通则④简化）还是共享一份。

### 🟡 MEDIUM — F13: 零依赖精神 vs 字面合规

**来源**：Claude CEO · Codex CEO (C1)

yq 是对每个下游消费仓新增的环境前置条件。Compliance 一句「同 git，不违反」回避了对不变量精神的陈述。

**裁决**：**采纳（MEDIUM）**。ADR-0036 补一句代价陈述。

### 🟢 LOW — F14: yq -i 静默 CRLF→LF

**来源**：对抗镜1 (F7，实测)

现有 `_set_schema_key` 显式保留文件原有换行风格。yq 写操作后全部变 LF。

**裁决**：**记为已知边角**。影响面小（一次性 diff 噪音），按通则④接受。

### 🟢 LOW — F15: yq merge-anchor 版本漂移

**来源**：对抗镜1 (F6，实测)

yq 的 merge-anchor 默认行为计划翻转。当前 config.yaml 未使用 merge anchor。

**裁决**：**记为已知边角**。当前无影响，spec Non-Goals 可登记。

---

## 决策登记区

### [自动决策]

| ID | 决策 | 原则 | 理由 |
|---|---|---|---|
| D1 | C1（零依赖重定义）降级 MEDIUM | ④ | proposal 已明确 yq 同 git 层级，setup.sh 降级范式一致 |
| D2 | C3（多文档 YAML）**升级** HIGH（原降级 INFO 被对抗镜实测推翻） | ③ | 对抗镜1 实测证明 config.yaml 的 context 段丢缩进可产生多文档 |
| D3 | C5（yq -i fidelity）接受 | ④ | decision-memo 已记录为接受的边角 |
| D4 | C6（subprocess 开销）降级 INFO | ④ | yq <100ms，不在热路径 |
| D5 | C8（企业安装现实）降级 INFO | ④ | 目标用户是开发者个人机 |
| D6 | C9（PyYAML 被意识形态否定）否决 | ③ | decision-memo D1 已详述三候选比较 |

### [需拍板]

| ID | 问题 | 选项 + 推荐 | 三面后果 |
|---|---|---|---|
| Q1 | F1: duplicate-key/tab-indent 检测在 yq 管线下结构性丢失 | **A) 保留轻量原始文本预扫描（推荐）**——只做键名计数和缩进字符检测（~20行），不算通用 YAML 解析，不违反基准5。B) 接受诊断退化——承认 ship-gate 的 duplicate-key 门降级。| 系统：A 保住 fail-closed 安全门；B 引入静默放行面。用户：A 保持现有错误信息精度；B 出问题时只拿到笼统 parse error。开发循环：A 增加 ~20行轻量代码但目的明确；B 简单但安全门打洞。**主次：系统镜（安全门完整性）** |
| Q2 | F12: 7 份 `_yq()` 各自抄 vs 共享一份 | **A) 接受各自抄 + golden test 守一致（推荐）**——按 resolve-models.sh 的既有范式（各自实现 + golden 测试守一致）。B) 共享一份——用 impl_route.py 已验证的 sibling-import 模式。| 系统：A 零新依赖关系；B 减 6 份重复但增加一个跨脚本导入点。开发循环：A 需加 golden test（7份一致性机械检查）；B 改一处即生效但 import 路径在 Windows copy 模式下需额外处理。**主次：开发循环镜** |

### [已裁掉]

| ID | 原始发现 | 裁掉理由 |
|---|---|---|
| X1 | C9: PyYAML/共享解析器被意识形态否定 | decision-memo D1 已逐候选比较理由，基准5 有判据 |
| X2 | C8: 安装策略忽略企业现实 | 本工具目标用户非企业气隙部署 |

---

## [spec-review-amendment] 修订清单

根据采纳的 findings，以下修订应在设计门拍板后执行：

1. **spec R1 增加版本门 scenario**：`WHEN yq --version 输出的版本 < 4.16.0 THEN 输出版本过低警告 + 升级指引`（F5）
2. **design §1 `_yq()` 封装重写错误处理**：exit 0 + null → default；exit≠0 → 必须 raise，不吞（F2）
3. **design §1 `_yq()` 封装加身份校验**：首次调用时 `--version` 探测 + 进程内缓存（F6）
4. **design §1 `_yq()` 封装加编码参数**：`encoding="utf-8", errors="replace"`（F10）
5. **design §1 `_yq()` 封装加多文档防御**：json.loads 前检测是否单值（F3）
6. **design §1 写操作改为 env() 传值**：消除表达式注入（F7）
7. **spec R5 frontmatter 未闭合 scenario 改为 best-effort**：补返回类型 sanity check（F4）
8. **tasks.md 补 CI 任务**：mechanical-gates.yml 显式装 + 钉版本 yq（F8）
9. **tasks.md 补测试重写任务**：列出需改断言的测试用例清单（F9）
10. **proposal Success Metrics 增第5条**：yq 安装 + 端到端读写验证通过（C10）
11. **ADR-0036 补代价陈述**：对零依赖不变量精神的有意识收窄（F13）

---

## 收敛

**10 条采纳 findings（2 CRITICAL + 8 HIGH）、2 条需拍板、2 条已裁掉、11 条修订。**

建议进设计 HARD-GATE：本 change 的方向正确（与基准5 高度自洽），但 design/spec 存在两处结构性缺陷（duplicate-key 信息丢失、`_yq()` 错误处理逻辑错误）需要在实现前修正。
设计门拍板时请一并裁决 Q1/Q2 两个需拍板项。
