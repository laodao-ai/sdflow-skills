## MODIFIED Requirements

### Requirement: 落锚/调 emitter 前探 tools 能力，陈旧则 fail-loud 降级〔spec-review-r2 C3+D1 统一 skew 策略〕

编排 SKILL SHALL 在 fan-out / 调 `lens_metric_emit` / 落 v2 锚**之前**探测本仓 bundle 是否与全局 canonical 同步，陈旧则 fail-loud 降级——因 bundle 内 SKILL（symlink 即时生效）与 tools（copy，须 `sdflow-init update` 刷新）**更新不原子**，存在「新 SKILL × 旧 tools」窗口，旧 tools 有两个同根罢工症状：旧 `lens_metric_emit.py` 不认 `--host`（argparse exit 2 → lens-metric 整段静默清零）；旧 `anchor_lint.py` 枚举无 `none`（`runner="none"` 锚 → out-of-enum 罢工）。

**探测判据 = 分发链版本对比，MUST NOT 逐能力探内容特征〔fix-probe-scan-precision · adr/0038〕**：判据 SHALL 为「两条分发链各自写下的 bundle 版本是否相等」——`setup.sh` 刷全局 canonical 时写全局侧版本，`sdflow-init` 的 bundle 拷贝函数写消费仓侧版本，探测 = 比这两个字符串。版本取值 SHALL 为 **bundle 作用域**的 `git log -1 --format=%H -- <bundle 路径>`（**非整仓 HEAD**——整仓 HEAD 每个 commit 都变而 bundle 大多数 commit 未动，用它会令源仓每提交一次即需 update，判据会因烦人被绕过），形式 SHALL 为纯 40 位 commit SHA（**MUST NOT 用 `git describe --dirty`**——脏工作树会令版本恒不相等、天天误报）。

**MUST NOT 回退为「逐能力内容探测」**（即为每个 bundle 特性各写一条「打开某文件 grep 某字符串」的检测）：该形状每加一个特性就要补一条信号（补丁螺旋），且因判据只以散文描述于 SKILL、**结构上无法被机械守**（验证「所写检测是否仍正确」需先从 markdown 提取命令 = 手写解析器）；其失效方向为假阴——已实证一次 `sed` 无行首锚定命中文件散文中对 fence 名的提及、截出散文段而误判 bundle 陈旧，几乎硬停一轮完整评审。理由全文见 `openspec/adr/0038`。

**陈旧的处置 = fail-loud 硬停在落锚之前（不产出被 lint 的报告），非"产出无锚报告"〔spec-review-r3 C3-A/B：解 MANDATORY 冲突〕**：`anchor_lint` 的 outside-voice 锚是**无条件必查**（`MANDATORY`，`anchor_lint.py:203` 〔spec-review-amendment：原写 `:148`，实测该行是 fence 解析代码；`MANDATORY = ("outside-voice", "hr-tg", "step1-broad-review")` 在 `:203`〕）——∴ "陈旧则不落 v2 锚**但仍产出报告**"会撞 MANDATORY 阻塞、"落回 v1 旧锚（无 host）"又被读作 Claude 宿主 = Codex 轮次重新假绿。二者皆不可取。**正解**：探到陈旧 ⇒ 编排 SKILL 在**开始 fan-out / 落任何锚之前**硬停该评审步，**不产出待 lint 的报告**，终端/hand-off **响亮提示「tools 陈旧，请先跑 `sdflow-init update` 再重跑评审」**（fail-loud、actionable、非假绿、非静默清零、不撞 MANDATORY、不落会让旧 lint 罢工的 `runner="none"` 锚）。

**版本缺失即陈旧；非 git 环境 fail-open**：任一侧版本文件缺失 SHALL 判定陈旧并按上述硬停（语义自洽——从未跑过新版写入方的仓正是陈旧态），提示分别指向 `bash setup.sh`（全局侧缺）与 `sdflow-init update`（消费仓侧缺）。两侧版本**同为字面 `unknown`**（非 git 环境或取版本命令失败）SHALL 判定相等并放行（fail-open，与既有 `setup.sh` 的 `|| echo "unknown"` 降级一致；改 fail-closed 会令非 git 安装完全无法评审）。

**残余诚实登记（探测漏网窗口）〔spec-review-r3 C3-C · fix-probe-scan-precision 改述〕**：SKILL 侧探测是**主守**。版本对比**不覆盖**「有人手改消费仓部署副本而不回灌权威源」——版本文件不变、探测放行；该窗口在改判据前的逐能力内容探测下**同样不被覆盖**，故非本判据引入，如实登记为残余。若探测被跳过/漏网（`metrics.enabled=false` 消费仓本就不调 emitter，此路径主要护 metrics-on 仓），旧 `lens_metric_emit.py` 撞 `--host` argparse 罢工、旧 `anchor_lint.py` 撞 `runner="none"` out-of-enum 罢工——**二者皆 fail-loud 罢工（非假绿）**，如实登记该残余窗口未被第二道机械覆盖（对比 emitter 侧：`parse_known_args` 兜底**只对新 emitter × 旧调用方成立**，对"已部署旧 emitter"结构上够不着，见下 Scenario）。

#### Scenario: 两侧版本不等则 fail-loud 硬停（不产出报告）
- **WHEN** 编排 SKILL 读到全局侧与消费仓侧的 bundle 版本**不相等**（消费仓 pull 新 bundle 未 `sdflow-init update`）
- **THEN** SHALL 在落任何 v2 锚之前**硬停该评审步、不产出待 lint 的报告**，终端/hand-off 响亮提示 `sdflow-init update`；MUST NOT 产出无锚报告（撞 MANDATORY）、MUST NOT 落 v1 旧锚（假绿）、MUST NOT 静默清零

#### Scenario: 任一侧版本文件缺失同样判陈旧
- **WHEN** 全局侧或消费仓侧的 bundle 版本文件**不存在**（从未跑过写入该文件的新版 `setup.sh` / `sdflow-init update`）
- **THEN** SHALL 按「陈旧」同等处置（硬停、不产出报告），且提示 SHALL 指向缺失的那一侧对应的命令；MUST NOT 因「读不到就当没问题」而放行

#### Scenario: 两侧版本相等则放行
- **WHEN** 两侧 bundle 版本字符串**相等**（含两侧同为字面 `unknown` 的非 git 环境）
- **THEN** SHALL 正常进入后续步骤，MUST NOT 因版本之外的内容特征再行阻塞

#### Scenario: 探测判据不得随 bundle 新增特性而增条目
- **WHEN** bundle 新增任一能力（新 tool、新契约块、新枚举值）
- **THEN** 探测判据 SHALL 保持不变（仍为版本对比），MUST NOT 为该能力追加一条内容特征检测；新能力的兼容性由版本相等性隐含覆盖

#### Scenario: 受控 fail-closed 只护「新 emitter × 旧调用方」，不护「旧 emitter」〔spec-review-r3 C3/D1 诚实拆分〕
- **WHEN** 调用方（旧 SKILL）不传 `--host` 给**新** `lens_metric_emit.py`
- **THEN** 新 emitter SHALL `parse_known_args` + 缺 `--host` 受控 fail-closed（可读错误、非 argparse 崩栈，且 `if extras: fail-closed`），MUST NOT 默认填 `claude`。**注**：此兜底**只对新 emitter 成立**；「新 SKILL × **已部署旧 emitter**」方向旧 emitter 代码不会因本 change 改变，**只能靠上方 SKILL 侧探测拦截**（parse_known_args 够不着旧文件），MUST NOT 声称此兜底覆盖后者
