## Context

roadmap `mechanical-layer-hardening` 阶段 2 的实施。整体设计复用 `openspec/roadmaps/mechanical-layer-hardening/design.md`（两腿六阶段、adr/0006 机械协议脚本化根契约、家族①②③④ 分治）。

现状：两审 SKILL（`sdflow-spec-review` Step3、`sdflow-code-review` Step5）出报告后，由主 session **手 grep 四类 v1 锚 + 肉眼核 `layer`/`lens`/`runner`/`sev` 枚举与子格式**。这是「机械 prose 协议」——执行机队（opus/sonnet/gpt-5.5）弱档档位或走神时易静默跳步/核错，正是 adr/0006 靶心。

**接地事实（已核验代码）**：
- 复用源 `sdflow-retro/scripts/lens_metric_aggregate.py`：`parse_anchor(line)`（仅匹配 `<!-- sdflow:lens-metric v1` 前缀、返回字段 dict）、`_fence_aware_lines(text)`（CommonMark fence 语义、产非 fenced 行）、`_KV`（受限 `key="value"` 正则）。**该文件硬编码** `LAYER_ENUM`/`LENS_ENUM`（仅 layer+lens，**无 runner**），注释称契约在 `.md` 但代码内复制了清单。
- 契约单一源 `sdflow-init/assets/workflow/lens-metric-contract.md`：enum 以散文 bullet 列（`layer ∈ {…}` / `lens ∈ {…}` / `runner∈ {…}` / `sev = 致N/高N/中N/低N`）；`site` 显式声明**不纳入越域自检**（CF-补2）。
- 落点先例：`trivial_shape.py` 在 `sdflow-init/assets/workflow/tools/`，退出码承载判定 + 双输出（human + JSON）+ 纯 stdlib；tests 在 `tools/tests/`；repo-root `openspec/workflow/tools/` 副本由 `sdflow-init update` 刷。code-review SKILL 以 `$RULES_ROOT/tools/trivial_shape.py` 调用（RULES_ROOT 经 resolve-workflow.sh 解析）。
- **repo 无 yaml 模块**（`import yaml` 失败），无任何脚本 parse config.yaml——`metrics.enabled` 现由主 session 模型读。
- spec 归属：`workflow-metrics` spec 拥有 lens-metric 自检 scenario（措辞「复用现有锚存在性自检机制」= **机制无关**，脚本化后不矛盾）；本变更新需求落 `spec-workflow`（与 line 221 resolve-workflow、line 327 ship_gate 的脚本化模式同处，roadmap 指定）。

## Goals / Non-Goals

**Goals:**
- 把两审锚自检从「模型手 grep + 肉眼核枚举」降为确定性脚本门 `anchor_lint`，fail-closed + 可观测。
- 枚举取值域从 `lens-metric-contract.md` 单一源读，不在脚本内形成第二份清单。
- 复用现成 fence-aware 纯函数，不重实现 fence 核；不触 gate 锚原语。
- 保留数值一致性（`findings=N` vs 实收数）诚实边界——脚本不谎称机验。

**Non-Goals:**
- 不改 lens-metric 锚形/字段/枚举（契约不动）。
- 不做数值一致性机验。
- 不改 `lens_metric_aggregate.py`（只复用纯函数；其硬编码 enum 的潜在不一致见风险 R4，out-of-scope）。
- 不做 config/batches 结构 lint（阶段 3 P3.B）；不迁 gate 锚 frontmatter（阶段 5）。

## Decisions

### 决策 1：枚举取值域从契约 `## 机读取值域` fenced 块读〔grill Q2=B〕

`anchor_lint.py` 位于 `.../workflow/tools/`，契约位于 `.../workflow/lens-metric-contract.md`（同 workflow bundle、随 resolve-workflow.sh 解析同树）。脚本用 `Path(__file__).resolve().parent.parent / "lens-metric-contract.md"` 定位，**解析契约里 info-string 恒为 `lens-metric-enums` 的 fenced 块**（本 change 给契约新增，见下）——块内 `key: 逗号分隔值` 行提 `layer`/`lens`/`runner` 枚举 + `sev-format` 模板。**契约文件缺失 / 找不到 `lens-metric-enums` 块 / 块解析空 → fail-closed 非零退出（ERROR 2）**（不回落硬编码兜底，否则第二真相源复活）。

- **为何机读块而非散文 bullet**〔grill Q2=B，推翻原「正则解散文」〕：契约原枚举是散文 bullet（`layer ∈ {…}`，尾带「（canonical 投影…」注记），正则解 `{…}` 虽可行但脆（格式漂移即碎）。给契约加一段格式钉死的 `lens-metric-enums` fenced 块，机读稳定、人也可读；散文 bullet 保留作语义注记（折叠/消歧说明）并加指针指向机读块。**代价**：scope 触及契约文件（bundle 权威源，经 `sdflow-init update` 下发）——已接受。
- **为何不硬编码**：roadmap 明令「从 `.md` 单一源读，不复制清单」；硬编码就是 aggregator 现在的隐患（改 `.md` 加镜种、脚本不跟；见决策 6）。
- **为何不 import aggregator 的 `LAYER_ENUM`/`LENS_ENUM`（含 fence 核）**：①跨 skill import——anchor_lint 在 sdflow-init/tools、aggregator 在 sdflow-retro/scripts，是**两个 skill**；anchor_lint 作 bundle tools/ 经 `sdflow-init update` 铺进消费仓，但 sdflow-retro/scripts **不在消费仓**，运行时 `import lens_metric_aggregate` 会 ImportError（对抗A/B 读码确认）——aggregator 自己也立规「禁跨 skill import ship_gate」，本仓反模式；②aggregator 只有 layer+lens、**无 runner**，取不全。故 anchor_lint MUST **在脚本内重实现 fence-aware 行级核 + 前缀匹配 kv**（与 aggregator 平行、同 CommonMark 纪律、不共享代码）。
- **覆盖父 roadmap「复用不重实现」并调和**〔spec-review H3·BASE-08〕：父 roadmap `design.md:56`/`roadmap.md:61` 写「复用 parse_anchor/_fence_aware_lines、不重实现」。本 change **遵其实质**（roadmap F1 的实质 = 用变长 KV 前缀匹配、**不用** `ship_gate._line_scoped_hits` 定长整行原语），仅把字面「import 复用」**澄清/覆盖**为「脚本内重实现同款逻辑」——理由=上条①消费仓 import break。**须同步**改 roadmap 两处文档 + task-log 注记（tasks 新增同步任务），不留「roadmap 权威源与实现相反」的悬置矛盾。
- **三镜主次**〔BASE-12 补〕：系统镜——消费仓可运行性（import break）压倒代码复用之简；用户镜——消费仓不因缺 sibling 脚本而崩；开发循环镜——两份 fence 核维护成本由交叉一致性测试（决策6/M1）兜。**主判据=系统镜（消费仓可运行）**，重实现虽多一份代码但为必需。

### 决策 2：`metrics.enabled` 门控——anchor_lint 自读 config.yaml（受限 stdlib，无 yaml 依赖）

anchor_lint 自读 `<root>/openspec/config.yaml` 的 `metrics.enabled`，**不接受调用方传 `--metrics-enabled` flag**。

- **为何自读不接 flag**：P2 的全部意义是「别信模型手做机械核验」；若门控状态由模型读了再传 flag，等于把 P2 想消灭的「信模型正确读 config」搬回来，部分自我否定。自读 = 完全确定性门。
- **无 yaml 依赖怎么读**：repo 无 yaml、纯 stdlib 传统。`metrics.enabled` 是顶层 `metrics:` 块下唯一布尔子键，用**受限行锚定正则**读（`^metrics:` 块内 `^\s+enabled:\s*(true|false)`），非通用 YAML parse。边界：只读这一个布尔键，不 parse 任意嵌套（通用结构 lint 是阶段 3 P3.B scope）。
- **真四态分治**〔grill Q1=A 起手，spec-review H1 三镜收敛精化〕：grill 原二分（缺→false / 坏→ERROR）把「config 存在但从未声明 `metrics:` 块」（消费仓**常态**——对抗B 实测本机 4 消费仓 `grep "^metrics:"` 全零命中，`sdflow-init update` 从不为已存在 config 注入新顶层键）误归 ERROR 分支 → 会让 100% 消费仓每轮评审假阻塞（本仓 dogfood 因 config 有 `metrics: enabled: true` 掩盖测不出）。**精化为真四态**：
  ① `openspec/config.yaml` **文件不存在** → enabled=false（放行）；
  ② 文件存在但**无顶层 `^metrics:` 行**（该键从未声明，消费仓常态）→ 视同未配置 → enabled=false（放行，与①同分支）；
  ③ 有 `^metrics:` 行但其块内（至下一顶层键前）**解不出合法 `enabled: true|false`**（拼错/非法布尔/结构损坏）→ **ERROR(2) fail-closed**（真结构异常，反静默：不因 config 读取静默失败悄悄跳过整类校验）；
  ④ 解出 → 对应 bool。
  「坏」严格收窄到③（块**在**但值非法），②（块**不在**）走放行。块边界须先定位 `^metrics:` 行再限范围至下一顶层键（防多段 config 误配对，L2）。
- `--root` 参数（默认 cwd）定位 config；两审 SKILL 从仓根跑（cwd=仓根），`--root .` 即可。

### 决策 3：落点 = `sdflow-init/assets/workflow/tools/anchor_lint.py` + `tools/tests/`

bundle 权威源，trivial_shape.py 同款。两审 SKILL 以 `$RULES_ROOT/tools/anchor_lint.py` 调用（RULES_ROOT 经 resolve-workflow.sh 解析）。repo-root `openspec/workflow/tools/` 副本由 `sdflow-init update` / setup 托管刷新，不手 copy。测试落 `tools/tests/test_anchor_lint.py`（`init.py` 的 `ignore_patterns("tests")` 保证 tests 不派生进消费仓）。

### 决策 4：CLI 契约与退出码（trivial_shape 先例）

```
anchor_lint.py --report <path> --layer spec-review|code-review [--root <dir>]
  退出码 0 = CLEAN     （四类恒须锚齐 + lens-metric 全合法；或 metrics 关闭时豁免 lens-metric）
  退出码 1 = VIOLATION （缺恒须锚 / lens-metric 越域枚举 / 缺字段 / 坏 sev / fence 外真锚违规）
  退出码 2 = ERROR     （读不到报告 / 定位不到契约或 lens-metric-enums 块 / 解析不出枚举 / config 存在但读不出 metrics.enabled → fail-closed，调用方当 VIOLATION 处理）
双输出：human 行（哪类锚缺 / 哪锚哪字段越域）+ JSON（机读违规清单）。
脚本内重实现 fence-aware 行级核（不跨 skill import；与 aggregator 平行同纪律）。
```

- **存在性判据**：`--layer` 决定恒须锚集——两 layer 均须 `outside-voice`/`hr-tg`/`step1-broad-review`；`lens-metric` 恒须**仅当** metrics.enabled。锚族识别用各自前缀（`<!-- sdflow:outside-voice v1`、`<!-- sdflow:hr-tg v1`、`<!-- sdflow:step1-broad-review v1`、`<!-- sdflow:lens-metric v1`），fence 外独占行前缀匹配。
- **metrics 开时 lens-metric 最小必有行**〔spec-review Q2=A〕：metrics.enabled 时不止「≥1 条 lens-metric」——`lens="broad"` 与 `lens="outside-voice"` 各 MUST 至少一行（两者恒跑：broad=Step1 广审、outside-voice=code-voice/design-voice 恒调），缺即 VIOLATION。其余 per-lens（domain/adversarial/grounding）完整性属主 session 动态知识、非机械可验（报告读不出「本轮跑了哪些镜」），仍是信任边界。
- **lens-metric 字段校验**：仅对 fence 外真 lens-metric 锚——①`layer`/`lens`/`runner` ∈ 契约枚举；②**`layer` MUST == CLI `--layer`**〔spec-review H2=codex〕（防错层度量锚漏网：`--layer code-review` 放过 `layer="spec-review"` 的锚）；③`sev` 匹配 `^致\d+/高\d+/中\d+/低\d+$`；④**五计数字段 `findings`/`采纳`/`裁掉`/`defer`/`独立` MUST 为十进制非负整数**〔spec-review H3=codex M3〕（拒负/浮点/空/中文数字，防坏值进聚合——aggregator `_int` 虽兜但 anchor_lint 应前置拦）；⑤必填字段齐（layer/lens/runner/findings/采纳/裁掉/defer/独立/sev）；**site 不校验**（CF-补2）。

### 决策 5：两审 SKILL 自检步改写——接脚本 + 保留诚实边界

`sdflow-spec-review/SKILL.md` Step3 与 `sdflow-code-review/SKILL.md` Step5 的锚自检段：把「grep 四类 v1 锚行 + 核 enum」改为「调 `$RULES_ROOT/tools/anchor_lint.py --report <report> --layer <layer>`，非零退出即本步阻塞」。**保留**原文「`findings=N` 与合并池实收数的数值一致性仍是主 session 信任边界、非机械可验」声明——诚实反映脚本只兜存在+枚举+子格式，不兜数值。config 门控措辞与现有一致（metrics.enabled 关则 lens-metric 一类跳过）。

### 决策 6：契约加 `lens-metric-enums` 机读块 + aggregator 一致性测试〔grill Q2=B / Q3=B〕

本 change 触两处本可留在 scope 外、grill 拍板纳入的加固：
1. **契约文件加机读块**：`lens-metric-contract.md` 新增 `## 机读取值域` 段 + `lens-metric-enums` fenced 块（layer/lens/runner/sev-format），作消费脚本单一机读源；散文 bullet 保留作注记 + 指针。bundle 权威源改动，经 `sdflow-init update` 下发消费仓 + setup 刷 repo-root 副本。
2. **aggregator 一致性测试**〔落点订正 spec-review L1：`sdflow-retro/scripts/tests/`——接地镜实测现有测试在 `sdflow-retro/scripts/tests/test_lens_metric_aggregate.py`，非 `sdflow-retro/tests/`〕：并入该文件，断言 `lens_metric_aggregate.LAYER_ENUM`/`LENS_ENUM` == 契约块解析的 layer/lens 集。**仍不改 aggregator `.py`**（只加测试守卫，不重构其读取路径——超本 change）。测试自带极简契约块解析（**不跨 skill import anchor_lint**，避免 sdflow-retro→sdflow-init 测试期反向依赖）；runner 枚举 aggregator 无、不纳入该断言。收尾须加跑 `pytest sdflow-retro/scripts/tests/`。

### 决策 7：copy_bundle 一并刷 `lens-metric-contract.md`〔spec-review Q1=A〕

anchor_lint 运行时读契约机读块 → 契约已成 `tools/anchor_lint.py` 的**运行时机读依赖**。但 `sdflow-init` 的 `copy_bundle` 非 full 模式只拷 `tools/`（契约是 tools/ 的 sibling、不在其子树）→ **本地 pin 消费仓**（RULES_ROOT 落本地 pin）`update` 刷了新 anchor_lint 却不刷旧契约 → 块缺 → 永久 fail-closed（对抗A R-MRF-1）。**修**：`copy_bundle`（或 update 路径）在刷 `tools/` 时**一并刷 `lens-metric-contract.md`**，锁同版本。改 `sdflow-init/scripts/init.py` + 测试（pin 场景刷新契约后块存在）。**边界**：常态 tools-only 消费仓不触发 pin（RULES_ROOT 落 canonical 全树，契约恒有块，无此问题）；此修专堵本地 pin（边缘、当前零现用户，但机读依赖须锁版本，正确性根治）。

### 决策 8：契约文档套件 scope-check 表（TG-25/BASE-29）〔spec-review H4〕

本 change 动 lens-metric 契约 + 新增消费者，须列全套件同步义务（workflow-metrics-loop 先例）：

| 部件 | 角色 | 本 change 改？ | 同步义务 |
|---|---|---|---|
| `lens-metric-contract.md` | 枚举契约权威源 | ✅ 加 `lens-metric-enums` 机读块 | 机读块为消费脚本单一源；散文 bullet 加指针 |
| `anchor_lint.py`（新） | 新消费者（运行时读机读块） | ✅ 新增 | 读块单一源、不复制；随 tools/ + 契约同批下发（决策7） |
| `lens_metric_aggregate.py` | 既有消费者（硬编码 layer/lens） | ❌ 不改 .py | 加一致性测试守卫硬编码 == 机读块（决策6.2） |
| `sdflow-spec-review/SKILL.md` | 生产者 + 自检调用方 | ✅ 自检步接 anchor_lint | 保留数值一致性诚实边界（决策5） |
| `sdflow-code-review/SKILL.md` | 生产者 + 自检调用方 | ✅ 自检步接 anchor_lint | 同上 |
| `spec-workflow` spec delta | 规范增量 | ✅ ADDED 自检需求 | 归档同步主 specs |
| `workflow-metrics` spec | lens-metric 契约需求所有者 | ❌ 不改 | 现「复用现有锚存在性自检机制」措辞机制无关，脚本化后不矛盾 |

## Risks / Trade-offs

- **R1 契约机读块格式依赖**〔grill Q2=B 已缓解〕：改为解析格式钉死的 `lens-metric-enums` fenced 块（info-string 恒定、块内 `key: csv` 行），比原散文 bullet 稳。残余风险：块被改乱 / info-string 打错 → 解析空 → fail-closed 非零（不静默放行）；测试喂真实契约断言解出三枚举 == 预期集。契约块与散文 bullet 的**同文件内漂移**（人改 bullet 忘改块）不设机验（过度工程）——机读块为唯一权威、bullet 仅注记，指针已声明「取值以机读块为准」。
- **R2 metrics.enabled 受限正则读**：在去字符串化 roadmap 里用正则读 YAML 略讽刺，但只读单一布尔键、有界，非通用 parse；通用 config 结构 lint 是阶段 3。三态判据（缺文件/无块/块坏）见决策 2（已按 spec-review H1 精化为真四态）。
- **R3/R4 双份解析器（fence 核 + 契约块）漂移 → 交叉断言缓解**〔spec-review M1 收敛 3 镜〕：anchor_lint 脚本内重实现 fence-aware + 契约块解析，与 aggregator（fence 核）、一致性测试（契约块 mini-parser）各成独立实现。**风险**：一致性测试守的是「测试自己的解析 == aggregator」而非「anchor_lint 运行时解析 == aggregator」；两解析器边界处理（逗号后空格/空行/未闭合 fence/`~~~` vs ```）分歧则假绿。**缓解**：①一致性测试对**同一真实契约 fixture** 让 anchor_lint 的解析路径与 mini-parser **交叉断言输出相等**（非仅各自终集）——降低「两 bug 恰好抵消」；②anchor_lint `load_enums` 自身有 task1.1 对真实契约的断言兜；③fence 核两份各有 fixture 测试 + 一组同 fixture 对两工具 fence-outside 行集交叉断言。**契约块与散文 bullet 同文件内漂移**（人改 bullet 忘改块）不设机验（过度工程）——机读块唯一权威、bullet 仅注记+指针。
- **R5 发布窗口**：改 bundle 权威源后须开发 checkout 跑 setup.sh 刷新全局 canonical，两审 SKILL 运行时才解析到新脚本；dogfood 测试须在 dev checkout 直接跑脚本路径验证，不靠 `~/.claude/skills` 符号链（P1 已踩此坑）。**本地 pin 消费仓部署错配**由决策 7（copy_bundle 一并刷契约）根治。
- **R6 SR-M 拍板回写在 anchor_lint 保护范围外（已知缺口·仅记录）**〔spec-review M2=对抗B〕：spec-review SKILL 的 SR-M 在设计门拍板时「原地更新」lens-metric 锚，发生在 Step3 anchor_lint 自检**之后**，SKILL 自承「best-effort 无机械兜底」。故若 SR-M 手滑破坏 sev/字段，无机械信号发现，直到 `/sdflow-retro` 聚合可能静默计入「解析失败」桶。**本 change 不修**（超 scope），仅记录——避免误传「两审全流程锚格式已机械保证」；anchor_lint 只兜「拍板前的 Step3 那一刻」的报告。

## Compliance

- adr/0006 机械协议脚本化：✅（本变更即其实施）。
- design §决策 5 fail-closed + 可观测 + 判断留人：✅（退出码 fail-closed、双输出、数值一致性留主 session）。
- D4（recorder 禁跨 import）：N/A（不碰 recorder）；但**跨 skill import 禁令泛化**到本脚本——不 import aggregator，脚本内重实现（决策 1/4）。
- bundle 权威源纪律：✅（改 assets、经 update 下发）。
- 无安全面（TG-17 N/A）、无外部服务成本（TG-24 N/A）。
