## Why

评审工具经两条**更新方式不同**的分发链落地：SKILL.md 走 symlink（`git pull` 即生效），
`openspec/workflow/` 下的 tools 与契约走拷贝（须 `sdflow-init update`）。为拦住二者不同代的窗口
（skew），两个评审 SKILL 的第零步各写了一段**逐能力内容探测**散文（`sdflow-code-review` 四条、
`sdflow-spec-review` 两条，其中①②逐字重复）。

该形状有三个已实证的问题：**它是补丁螺旋**（每加一个 bundle 特性补一条信号，命中 CLAUDE.md 基准 5
的警号）· **它结构上无法被机械守**（验证「SKILL 里写的检查还对不对」需从 markdown 抠命令 = 手写
markdown 解析器，撞同一条基准 5）· **它实证误停过**（`absorb-gstack-review` dogfood 首跑，信号②的
`sed` 无行首锚定命中散文，假阴，差点硬停整轮评审，而 bundle 实际是新的 —— `T270`）。

**但这三条都是症状。** 相位 B 的拷问查出根因：

1. **这个探测器保护的窗口，在主流配置下结构上不存在。** `resolve-workflow.sh` 判为
   `global-canonical` 的消费仓，其 `$RULES_ROOT` 解析到 `~/.sdflow/workflow` —— Unix 是软链、
   Windows 是存活 checkout 路径的指针文件，**两者都指向运行 checkout 内的文件树本身**，与 SKILL
   同属一个 checkout ⇒ `git pull` 一次两者同时变，**没有「拷贝」这个动作，就没有「忘了拷」这件事**。
   本机三个装了 workflow 的仓，两个属此类。
2. **skew 只可能在 local-pin 仓发生，而它发生时失败是响的、不是静默的。** 旧 tools 被新 SKILL 调用
   会自己 fail-closed 退出（`anchor_lint.py` 契约块读不出 → exit 2「绝不回落硬编码」；
   `hr_tg_intersect.py` catalog 段缺失 → `EmitError`「不静默按空集放行」）。**评审结果不会错**，
   代价只是跑到末步才发现、白花一轮算力。
3. ∴ **skew 探测不是正确性机制，是省钱机制。** 而一个省钱机制误报一次的代价 = 成功一次的收益
   （都是一轮评审）⇒ 净收益 = (真阳 − 假阳) × 一轮评审成本。**至今真阳 0 次、假阳 1 次（T270）。**

∴ 正解不是把探测做得更准，而是**消灭被探测的对象**：规则与工具**全局单份共享**，消费仓不再持有
任何 workflow 副本，取消 resolver 的本地 pin 旁路 ⇒ **skew 这一整类问题结构上不再存在**。

这也是把主 spec 已定方向做完：`openspec/specs/spec-workflow/spec.md:175` 早已规定「**规则** MUST
不再复制进消费仓」，而 `:176` 仍规定「**review 机械层脚本** SHALL 复制进消费仓」——本 change 把
后者翻转，使两者一致。

同批还有一条 `T269`（清理仓根 `openspec/workflow/` 的两个「孤儿副本」）。**调研后判定为一半成立**：
`lens-metric-contract.md` 是 `tools/` 的运行时机读依赖，随 tools 一并走全局 ⇒ 在消费仓不再是活件，
T269 对它成立；`WORKFLOW-GUIDE.md` 是有意为之的人读手册（「得在自己的仓里、随仓走」），仍是误判。

## What Changes

- **BREAKING · 取消 resolver 的本地 pin 分支**：`resolve-workflow.sh` 的三步链
  （本地 pin → 全局 canonical → 显式降级）收缩为**两步**（全局 canonical → 显式降级）。
  仓内规则副本**不再有任何生效路径**。
- **tools 与 `lens-metric-contract.md` 不再复制进消费仓**：`copy_bundle()` 非-full 分支删剩
  `WORKFLOW-GUIDE.md` + `openspec/schemas/<PROJECT_SCHEMA>` 两项。
- **两个评审 SKILL 的 skew 探测段整段删除，不做任何替代**（`sdflow-code-review/SKILL.md:206` 四条 ·
  `sdflow-spec-review/SKILL.md:180` 两条）。「工具真旧了」交回 tools 自身的 fail-closed 兜底。
- **`ship_gate.py` 的 `tools_spec` 失鲜腿退役**：它盯的 `openspec/workflow/tools/` 镜像将不复存在；
  而它保护的东西**早已被第一条腿覆盖**——顶层条目比较（`:947-950`，仅排除 `openspec`）中，tools
  权威源位于顶层条目 `sdflow-init` 之下，改权威源必改其 tree sha。该腿唯一多抓的情形（直接改镜像
  而不改权威源）在副本删除后**文件不存在、动作不可能发生**。
- **`--dev` / `copy_bundle(full=True)` / T15 为其开的 `stale_shadow_warnings` 豁免三者一并退役**：
  `full=True` 自述「仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用」，而源仓 dogfood
  此后同样走全局 canonical，无需本地 instance。
- **陈旧遮蔽告警语义升级**：`stale_shadow_warnings()` 与 `maintain_scan` 的规则残留检查行为不变，
  但告警文案从「它遮蔽全局且不再被刷新」改为「**它已不再被任何路径读取，可安全删除**」。
- **pin 的两个既有用途改用 `SDFLOW_HOME`**：`resolve-workflow.sh:8` 的契约**已明写**该环境变量
  （「测试用它重定向，绝不写真实 `$HOME`」）且第 1 层测试已在用它。CLAUDE.md 的「逃生口」（`:237`）
  与「开发期测试三层」第 2 层（`:226-228`）须同步改写。
- **文档与记录**：`CLAUDE.md` 关于仓根 `openspec/workflow/` 与测试三层的描述订正 ·
  新落 `openspec/adr/0039`（消灭双链）· `openspec/adr/0038` 标记为 **Superseded**（其主题
  「bundle skew 用版本对比而非能力探测」的**问题域随本 change 整个消失**，非结论被推翻）·
  `openspec/CONTEXT.md` 补 `skew` 术语定义（`manifest skew` 仍在用，该词继续存在）。
- **关闭 issues**：`T269` 分治关闭（contract 半成立、GUIDE 半误判）；`T270` 关闭理由为
  「**skew 探测段整体移除，问题对象消失**」——MUST NOT 写成「已修复」。

## Capabilities

### New Capabilities

（无——本 change 移除一条既有机制并收缩两条既有 Requirement，不引入新的行为级能力）

### Modified Capabilities

- `spec-workflow`：① 「规则全局解析 resolver」的三步链收缩为两步，步①（本地 pin）及其全部
  Scenario 移除；② 「workflow bundle 改在权威源、经部署下发」中 review 机械层脚本由
  「SHALL 复制进消费仓」翻转为「MUST NOT 复制」；③ 「存量消费仓迁移不自动删、陈旧遮蔽须告警」
  的告警语义由「遮蔽全局」改为「已无生效路径、可删」（**不自动删除的安全红线不变**）。
- `encoding-hygiene`：入口脚本契约的目标集里「不含 `openspec/workflow/tools/**` 托管镜像」这条排除子句移除（镜像不复存在）；机械门的「bundle 源文件不被镜像排除规则连坐」Scenario 随之改写为「不再需要该豁免」——**该风险面因镜像消失而消失，保留排除分支即死代码**。
- `host-adaptive-execution`：「落锚/调 emitter 前探 tools 能力」这条要求**整体移除**——其保护的
  失效模式（bundle 陈旧）随分发链合一而消失，且其残余形态由 tools 自身 fail-closed 承接。

## Impact

- **代码/资产**：`sdflow-init/assets/hack/resolve-workflow.sh`（bundle 权威源） ·
  `sdflow-init/scripts/init.py` · `sdflow-code-review/SKILL.md` · `sdflow-spec-review/SKILL.md` ·
  `sdflow-ship/scripts/ship_gate.py` · `CLAUDE.md`（订正） · `openspec/adr/{0038,0039}` ·
  `openspec/CONTEXT.md` · 本仓 `openspec/workflow/` 下 **7 个文件删除**（6 个 tools + contract，
  只留 `WORKFLOW-GUIDE.md`） · 相应 `hack/tests/` 与 `sdflow-init/tests/`。
  `hack/check_encoding_hygiene.py`（删镜像排除分支） · `hack/tests/test_yq_wrapper_consistency.py`（`TARGETS` 硬编码了 `openspec/workflow/tools/anchor_lint.py`，删文件后必红，须同批处置）。
  栈标注：bash + Python 工具 + markdown 指令资产（**不命中** TG-01/02/03 业务栈）。
- **依赖**：无新增。**净删除远大于净新增**——pin 两用途改用既有正式契约 `SDFLOW_HOME`，不新建机制。
- **🔴 存量 pin 消费仓有可感知的行为改变**：本机 `05-sarvelo` 实测为 `local-pin`（自留全套规则副本，
  `workflow.md` mtime = Jun 29 2026）。本 change 后它将**从「用自己冻结的规则」切换到「用全局规则」**。
  这是 pin 语义取消的直接后果，非缺陷；须由 `stale_shadow_warnings` 告警明确告知并提示删除死件。
  该仓同时实测**没有 `tools/`**——它现状跑评审会在 `python3 $RULES_ROOT/tools/anchor_lint.py` 拿到裸
  `can't open file`，本 change 顺带消灭该既存洞（此后恒走全局 tools）。
- **分发窗口**：本 change 同时改 SKILL（symlink 即时）与 bundle（`resolve-workflow.sh` 经
  `setup.sh` 拷进 `~/.sdflow/hack/`）。发布纪律沿用既有 push → pull → **立即** `setup.sh`。
  消费仓**不再需要** `sdflow-init update` 才能评审。

## 需求优先级

- **P0**：resolver 删步① + `copy_bundle` 停铺 tools/contract + 两个 SKILL 删探测段 + 对应测试
  —— 缺任一则新旧语义混态（例如 SKILL 仍探测但副本已不铺 ⇒ 每仓永久硬停）。
- **P1**：`ship_gate` 腿退役 · `--dev`/`full` 退役 · 告警文案改写 · CLAUDE.md 与 ADR/CONTEXT 订正 ·
  关闭 T269/T270（记录一致性，独立可验）。

## 假设

| 假设 | 若失效的影响 |
|---|---|
| **消费仓能可靠访问全局 canonical**（`~/.sdflow/workflow` 或 `workflow-path`） | 失效即 resolver 步③ 显式降级通用评审——**该路径已存在且已被测**，非新风险 |
| **不存在「必须冻结规则版本」的真实需求** | 若存在，`SDFLOW_HOME` 指向自备 canonical 是替代路径；比 pin 更真实（走步②主路径而非旁路） |
| **tools 的 fail-closed 覆盖所有「旧工具被新 SKILL 调用」的失败形态** | 若某工具在旧版下静默给出错误结果而非退出，则末步兜底失效。已核 `anchor_lint.py` / `hr_tg_intersect.py` 两个主要消费方均 fail-closed；**其余 tools 未逐一核验，登记为待验证前提** |

## Success Metrics

- 两个评审 SKILL 中**不再有任何 skew 探测描述**：
  `grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL" sdflow-code-review/SKILL.md sdflow-spec-review/SKILL.md`
  在第零步段内归零（其它段落的合法引用不计）。
- `resolve-workflow.sh` 中**无本地 pin 分支**：`grep -c "local-pin" ` 归零。
- 本仓 `openspec/workflow/` 下**只剩 `WORKFLOW-GUIDE.md`** 一个文件。
- 全仓 pytest 绿，含 resolver 两步链、`copy_bundle` 新拷贝集、告警文案的新增/改写用例。
- `openspec validate --strict` 绿。

## Non-Goals

- **不自动删除消费仓既有的规则副本**——沿用 `spec-workflow` 既有安全红线（`sdflow-init update`
  MUST NOT 自动删除仓内既有规则文件），只升级告警文案。删与不删由各仓的人决定。
- **不覆盖 Windows 上「旧 SKILL × 新 tools」的失鲜**——Windows 无 symlink，`setup.sh:119` 用 `cp -r`
  装 SKILL ⇒ SKILL 是 setup 时快照而 canonical 指活 checkout。该面**结构上不可自举**（检查者只能是
  SKILL 自己或 `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物，没跑 setup 就一起旧），
  且本仓对 Windows 分支结构性无测试面。**已知且接受的边界。**
- **不动 `~/.sdflow/hack/capability-manifest.json`** 及其 preflight 消费方——那是 hack 链的 skew 机制，
  与 bundle 链无关，`manifest skew` 在本 change 后仍然存在。
- **不给 `WORKFLOW-GUIDE.md` 建新鲜度机制**——它纯人读、不参与执行、不被任何脚本机读，陈旧无害；
  为它建机制会把本 change 刚消灭的那类问题原样请回来。
- **不改 `openspec/schemas/` 的下发**——那是 openspec CLI 要读的 project-local schema，非 workflow 规则。

## Compliance

N/A（本仓为本地开发工具链，无外部合规面）。
