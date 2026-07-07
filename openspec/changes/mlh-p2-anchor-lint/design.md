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

### 决策 1：枚举取值域从 `lens-metric-contract.md` 读（`__file__` 相对定位）

`anchor_lint.py` 位于 `.../workflow/tools/`，契约位于 `.../workflow/lens-metric-contract.md`（同 workflow bundle、随 resolve-workflow.sh 解析同树）。脚本用 `Path(__file__).resolve().parent.parent / "lens-metric-contract.md"` 定位，正则解析 `^-?\s*(layer|lens|runner)\s*[∈=]\s*\{([^}]*)\}` 提枚举 + 单独提 `sev` 子格式规则。**契约文件缺失/解析不出枚举 → fail-closed 非零退出**（不回落硬编码兜底，否则第二真相源复活）。

- **为何不硬编码**：roadmap 明令「从 `.md` 单一源读，不复制清单」；且硬编码就是 aggregator 现在的隐患（改 `.md` 加镜种、脚本不跟）。
- **为何不 import aggregator 的 `LAYER_ENUM`/`LENS_ENUM`**：①跨 skill import（anchor_lint 在 sdflow-init/tools、aggregator 在 sdflow-retro/scripts）——aggregator 自己就立规「禁跨 skill import ship_gate」，跨 skill import 是本仓反模式；②aggregator 只有 layer+lens、**无 runner**，取不全。
- **复用 vs 重实现的边界**：`parse_anchor` / `_fence_aware_lines` / `_KV` 是**同 skill 内**（都在 sdflow-retro）还是跨 skill？anchor_lint 在 sdflow-init/tools、aggregator 在 sdflow-retro——**这也是跨 skill**。故 anchor_lint MUST **在脚本内重实现 fence-aware 行级核**（同 aggregator 的做法：aggregator 注释明说「脚本内重实现 fence-aware，禁跨 skill import ship_gate」），而非 import。→ 见决策 4 修订：**不 import lens_metric_aggregate，脚本内自带 fence 核 + 前缀匹配 kv**（与 aggregator 平行、同纪律、不共享代码）。

### 决策 2：`metrics.enabled` 门控——anchor_lint 自读 config.yaml（受限 stdlib，无 yaml 依赖）

anchor_lint 自读 `<root>/openspec/config.yaml` 的 `metrics.enabled`，**不接受调用方传 `--metrics-enabled` flag**。

- **为何自读不接 flag**：P2 的全部意义是「别信模型手做机械核验」；若门控状态由模型读了再传 flag，等于把 P2 想消灭的「信模型正确读 config」搬回来，部分自我否定。自读 = 完全确定性门。
- **无 yaml 依赖怎么读**：repo 无 yaml、纯 stdlib 传统。`metrics.enabled` 是顶层 `metrics:` 块下唯一布尔子键，用**受限行锚定正则**读（`^metrics:` 块内 `^\s+enabled:\s*(true|false)`），非通用 YAML parse。边界：只读这一个布尔键，不 parse 任意嵌套（通用结构 lint 是阶段 3 P3.B scope）。
- **缺 config / 读不出键**：保守判 **enabled=false**（lens-metric 一类不强制）——避免因 config 读取问题把干净报告误判缺锚阻塞。〔grill 待议：缺 config 时 fail-open(false) vs fail-closed(要求 lens-metric)？倾向 fail-open：门控本就默认关，且缺 config 是环境问题非报告缺陷。〕
- `--root` 参数（默认 cwd）定位 config；两审 SKILL 从仓根跑（cwd=仓根），`--root .` 即可。

### 决策 3：落点 = `sdflow-init/assets/workflow/tools/anchor_lint.py` + `tools/tests/`

bundle 权威源，trivial_shape.py 同款。两审 SKILL 以 `$RULES_ROOT/tools/anchor_lint.py` 调用（RULES_ROOT 经 resolve-workflow.sh 解析）。repo-root `openspec/workflow/tools/` 副本由 `sdflow-init update` / setup 托管刷新，不手 copy。测试落 `tools/tests/test_anchor_lint.py`（`init.py` 的 `ignore_patterns("tests")` 保证 tests 不派生进消费仓）。

### 决策 4：CLI 契约与退出码（trivial_shape 先例）

```
anchor_lint.py --report <path> --layer spec-review|code-review [--root <dir>]
  退出码 0 = CLEAN     （四类恒须锚齐 + lens-metric 全合法；或 metrics 关闭时豁免 lens-metric）
  退出码 1 = VIOLATION （缺恒须锚 / lens-metric 越域枚举 / 缺字段 / 坏 sev / fence 外真锚违规）
  退出码 2 = ERROR     （读不到报告 / 定位不到契约 / 解析不出枚举 → fail-closed，调用方当 VIOLATION 处理）
双输出：human 行（哪类锚缺 / 哪锚哪字段越域）+ JSON（机读违规清单）。
脚本内重实现 fence-aware 行级核（不跨 skill import；与 aggregator 平行同纪律）。
```

- **存在性判据**：`--layer` 决定恒须锚集——两 layer 均须 `outside-voice`/`hr-tg`/`step1-broad-review`；`lens-metric` 恒须**仅当** metrics.enabled。锚族识别用各自前缀（`<!-- sdflow:outside-voice v1`、`<!-- sdflow:hr-tg v1`、`<!-- sdflow:step1-broad-review v1`、`<!-- sdflow:lens-metric v1`），fence 外独占行前缀匹配。
- **lens-metric 字段校验**：仅对 fence 外真 lens-metric 锚——`layer`/`lens`/`runner` ∈ 契约枚举、`sev` 匹配 `^(致\d+/高\d+/中\d+/低\d+)$`、必填字段齐（layer/lens/runner/findings/采纳/裁掉/defer/独立/sev）；**site 不校验**（CF-补2）。

### 决策 5：两审 SKILL 自检步改写——接脚本 + 保留诚实边界

`sdflow-spec-review/SKILL.md` Step3 与 `sdflow-code-review/SKILL.md` Step5 的锚自检段：把「grep 四类 v1 锚行 + 核 enum」改为「调 `$RULES_ROOT/tools/anchor_lint.py --report <report> --layer <layer>`，非零退出即本步阻塞」。**保留**原文「`findings=N` 与合并池实收数的数值一致性仍是主 session 信任边界、非机械可验」声明——诚实反映脚本只兜存在+枚举+子格式，不兜数值。config 门控措辞与现有一致（metrics.enabled 关则 lens-metric 一类跳过）。

## Risks / Trade-offs

- **R1 契约 `.md` 非机读格式**：enum 是散文 bullet，正则解析 `∈ {…}` 依赖格式稳定（如 `lens` 行 `}` 后跟「（canonical 投影…」尾注——正则须只取 `{…}` 内、容忍尾注）。缓解：解析器只锚 `{…}` 捕获组；测试喂真实契约断言解出的枚举 == 预期集；契约行若被改乱，解析空集 → fail-closed 非零（不静默放行）。〔grill 待议：是否值得给契约 `.md` 加机读锚区（如 fenced yaml 块）让解析更稳？倾向不——过度工程，散文 bullet 正则够用且有测试兜。〕
- **R2 metrics.enabled 受限正则读**：在去字符串化 roadmap 里用正则读 YAML 略讽刺，但只读单一布尔键、有界，非通用 parse；通用 config 结构 lint 是阶段 3。缺 config → fail-open(false) 的选择见决策 2 grill 待议点。
- **R3 双份 fence 核**：anchor_lint 脚本内重实现 fence-aware，与 aggregator 各一份（不共享）。这是本仓既定纪律（禁跨 skill import）的代价——两处 fence 核逻辑须各自测试、未来同步演进靠纪律。缓解：两处都有 fence 测试；roadmap 阶段 3 的镜像一致性测试思路**未来**可考虑覆盖（当前不强绑）。
- **R4 aggregator 硬编码 enum 潜在不一致（out-of-scope）**：anchor_lint 读 `.md`、aggregator 硬编码 `.md` 的副本——若 `.md` 改而 aggregator 不跟，两者对「合法枚举」判断会漂移。本变更**不修** aggregator（scope 外），但**记录**：后续可让 aggregator 也读 `.md`（或加一致性测试断言 aggregator 常量 == `.md` 解析值）。留 todolist。
- **R5 发布窗口**：改 bundle 权威源后须开发 checkout 跑 setup.sh 刷新全局 canonical，两审 SKILL 运行时才解析到新脚本；dogfood 测试须在 dev checkout 直接跑脚本路径验证，不靠 `~/.claude/skills` 符号链（P1 已踩此坑）。

## Compliance

- adr/0006 机械协议脚本化：✅（本变更即其实施）。
- design §决策 5 fail-closed + 可观测 + 判断留人：✅（退出码 fail-closed、双输出、数值一致性留主 session）。
- D4（recorder 禁跨 import）：N/A（不碰 recorder）；但**跨 skill import 禁令泛化**到本脚本——不 import aggregator，脚本内重实现（决策 1/4）。
- bundle 权威源纪律：✅（改 assets、经 update 下发）。
- 无安全面（TG-17 N/A）、无外部服务成本（TG-24 N/A）。
