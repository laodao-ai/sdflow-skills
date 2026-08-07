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
  在未显式设置 `SDFLOW_HOME` 覆盖的前提下，仓内规则副本**不再有任何生效路径**〔F42 限定〕。
  附带的安全收益〔F39〕：对不可信仓跑评审不再可能执行该仓自带的 `openspec/workflow/tools/*.py`
  ——消灭一个「克隆不可信仓 + 跑评审 = 执行仓自带代码」的供应链点（同受 F42 限定：`SDFLOW_HOME`
  被指向被评审仓时该性质失效）。
- **tools 与 `lens-metric-contract.md` 不再复制进消费仓**：`copy_bundle()` 非-full 分支删剩
  `WORKFLOW-GUIDE.md` + `openspec/schemas/<PROJECT_SCHEMA>` 两项。
- **两个评审 SKILL 的 skew 探测段整段删除，不做任何替代**（`sdflow-code-review/SKILL.md:206` 四条 ·
  `sdflow-spec-review/SKILL.md:180` 两条）。「工具真旧了」交回 tools 自身的 fail-closed 兜底。
- **`ship_gate.py` 的 `tools_spec` 失鲜腿退役**：它盯的 `openspec/workflow/tools/` 镜像将不复存在。
  退役理由**按仓型分开**〔F44〕：toolkit 源仓——tools 权威源位于顶层条目 `sdflow-init` 之下，顶层
  条目比较腿（`:947-950`，仅排除 `openspec`）已覆盖，改权威源必改其 tree sha；消费仓——镜像删除后
  「直接改镜像」动作不可能发生。消费仓侧「全局 canonical 在 review 与 done 之间变更不可见」是
  change 前即存在的盲区（旧腿只守仓内镜像、从不守 canonical），design Risks 登记接受。
- **`--dev` / `copy_bundle(full=True)` / T15 为其开的 `stale_shadow_warnings` 豁免三者一并退役**：
  `full=True` 自述「仅供 toolkit 源仓 `update --dev` dogfood 刷新 instance 用」，而源仓 dogfood
  此后同样走全局 canonical，无需本地 instance。
- **陈旧遮蔽告警语义升级**：`stale_shadow_warnings()` 与 `maintain_scan` 的检测**判据扩员**（原
  `RULE_MARKERS` 三项之外增查残留 `tools/` 与 `lens-metric-contract.md`），告警文案改为**带前置条件的
  死件表述**（「对评审已无生效路径——若刚 `git pull` 还没跑 `bash setup.sh`，先跑 setup 再判断」）并
  附**可直接复制的删除命令**；MUST NOT 用绝对断言「已无任何生效路径」（部署窗口与 `SDFLOW_HOME` 覆盖
  下为假）。存量死件的清理由人执行该命令完成，**不新增一次性自动清删代码**〔设计门 Q2：收益规模 =
  本机个位数仓 × 一次，不值得在 `init.py` 永久留一段迁移逻辑〕。
- **pin 的两个既有用途分流处置**〔设计门 Q4〕：**开发期测试隔离**走 `SDFLOW_HOME` 既有契约
  （`resolve-workflow.sh:8`「测试用它重定向，绝不写真实 `$HOME`」，第 1 层测试已在用）——CLAUDE.md
  的「逃生口」与「开发期测试三层」第 2 层同步改写为该用法。**「仓级版本冻结」不立替代承诺**：唯一
  存量 pin 仓（`05-sarvelo`）的实际诉求是跟全局最新而非冻结，为无人要的能力立一条 SHALL 比不立更坏
  （它还与 `setup.sh` 安装根同名复用，天然自毁）；写进 Non-Goals。
- **文档与记录**：牵连面由 design 的 **BASE-29 scope-check 表** + 概念词表 sweep 枚举（托管块权威源
  `claude-section.md` / `AGENTS.md` / 修法文案面 / docs / ADR 状态注记，见 tasks 6.x）· 新落
  `openspec/adr/0039`（消灭双链，含回滚步骤）· `openspec/adr/0038` **删除**〔设计门 Q3：本分支新建、
  从未进 main、其机制从未实现——born-superseded 的 ADR 只会误导未来读者〕，候选与砍因并入 0039 取舍段 ·
  `openspec/CONTEXT.md` 补 `skew` 术语定义（`manifest skew` 仍在用，该词继续存在）· `WORKFLOW-GUIDE.md`
  生成器把 sibling 相对链接降为文字引用（GUIDE 本身**保留铺进消费仓**，D14 不动）。
- **关闭 issues**：`T269` 分治关闭（contract 半成立、GUIDE 半误判）；`T270` 关闭理由为
  「**skew 探测段整体移除，问题对象消失**」——MUST NOT 写成「已修复」。

## Capabilities

### New Capabilities

（无——本 change 移除一条既有机制并收缩两条既有 Requirement，不引入新的行为级能力）

### Modified Capabilities

- `spec-workflow`：① 「规则全局解析 resolver」的三步链收缩为两步，步①（本地 pin）及其全部
  Scenario 移除；② 「workflow bundle 改在权威源、经部署下发」中 review 机械层脚本由
  「SHALL 复制进消费仓」翻转为「MUST NOT 复制」；③ 「存量消费仓迁移不自动删、陈旧遮蔽须告警」
  的告警语义由「遮蔽全局」改为带前置条件的死件表述 + 判据扩员（**不自动删除的安全红线不变**）；
  ④ 「评审报告锚自检由确定性脚本判定」删「契约机读块与 tools 同批部署下发」句及「防 pin 错配」
  Scenario——契约与 tools 此后同驻全局 canonical、同代性由单一 checkout 保证〔spec-review F6〕。
- `maintain-scan`：兜底扫描的告警语义同步（「pin 遮蔽全局」→ 死件）+ 判据扩员；「仅剩 tools 判干净」
  Scenario 反转为「报告死件残留」〔spec-review F7〕。
- `workflow-metrics`：删「`init.py` 的 `ignore_patterns("tests")` 排除 MUST 保留」注——tools 部署
  整体停止后该排除逻辑随之退役，不再有部署路径需要它护〔spec-review F8〕。
- `yq-yaml-operations`：R12 标题与正文去掉写死的「7 份」计数（改为「各内联 `_yq()` 封装」）；Purpose
  的脚本枚举删除镜像条目（Purpose 非 Requirement，随本 change 直接订正主 spec）〔spec-review F9〕。
- `encoding-hygiene`：入口脚本契约的目标集里「不含 `openspec/workflow/tools/**` 托管镜像」这条排除子句移除（镜像不复存在）；机械门的「bundle 源文件不被镜像排除规则连坐」Scenario 随之改写为「不再需要该豁免」——**该风险面因镜像消失而消失，保留排除分支即死代码**。
- `host-adaptive-execution`：「落锚/调 emitter 前探 tools 能力」这条要求**整体移除**——其保护的
  失效模式（bundle 陈旧）随分发链合一而消失，且其残余形态由 tools 自身 fail-closed 承接。

## Impact

- **代码/资产**：`sdflow-init/assets/hack/resolve-workflow.sh`（bundle 权威源） ·
  `sdflow-init/scripts/init.py` · `sdflow-code-review/SKILL.md` · `sdflow-spec-review/SKILL.md` ·
  `sdflow-ship/scripts/ship_gate.py` · `hack/gen_workflow_guide.py`（GUIDE 链接降级）·
  `sdflow-init/assets/snippets/claude-section.md`（托管块权威源）· `CLAUDE.md` / `AGENTS.md`（订正） ·
  `openspec/adr/`（0038 删、0039 新落、0003/0005/0019/0036 状态注记） ·
  `openspec/CONTEXT.md` · 本仓 `openspec/workflow/` 下 **7 个文件删除**（6 个 tools + contract，
  只留 `WORKFLOW-GUIDE.md`） · 相应 `hack/tests/`、`sdflow-init/tests/`、`sdflow-maintain/tests/`
  （必红集以 pytest 实跑为准，见 design BASE-29 表）。
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
| **不存在「必须冻结规则版本」的真实需求** | 已按此假设定案〔Q4〕：不立冻结承诺（唯一 pin 仓实际诉求是跟最新）。若未来出现真实需求，届时以独立 change 评估（`config.yaml` 仓级键等），MUST NOT 恢复仓内副本优先 |
| ~~tools 的 fail-closed 覆盖所有失败形态~~ **已验证关闭**〔A12〕 | 6 个 tool 全 `argparse required=True` 无静默默认；运行时读版本化输入的 3 个（`anchor_lint`→contract · `lens_metric_emit`→contract · `hr_tg_intersect`→trigger-catalog）均 fail-closed。不再是待验证前提 |

## Success Metrics

验收收敛为**三条闭环判据**（design「验收三判据」节，删除类 change 的完备性验收）：

1. **概念词表 sweep 归零**：归零词（`local-pin` · `两条分发链` · `显式 pin` · `pin 遮蔽`）全仓 grep
   （不带 `--include` 限定）归零，豁免表显式落 design BASE-29 节；逐条判词（`规则副本` ·
   `sdflow-init update` · `openspec/workflow/tools`）每命中必处置或登记豁免。两个评审 SKILL 的探测段
   删净后，`grep -n "skew 探测\|lens-metric-enums\|scope-audit:\|_MIRRORS_LEGAL"` 剩余命中恰为
   anchor_lint 自检段的两处合法引用（tasks 1.5 精确锚定）。
2. **全仓 pytest 绿 + 4 条反向锚用例在场**（副本忽略 / `sane()` 扩面 / 告警文案双断言 / `ship_gate`
   腿退役反向）——「绿」单独可被删测试满足，反向锚补齐证明力。本仓 `openspec/workflow/` 下只剩
   `WORKFLOW-GUIDE.md`。
3. **三态真跑 + `openspec validate --strict` 绿**（tasks 7.2–7.5）。

## Non-Goals

- **不自动删除消费仓既有的规则副本**——沿用 `spec-workflow` 既有安全红线（`sdflow-init update`
  MUST NOT 自动删除仓内既有规则文件），只升级告警文案。删与不删由各仓的人决定。
- **不覆盖 Windows 上「旧 SKILL × 新 tools」的失鲜**——Windows 无 symlink，`setup.sh:119` 用 `cp -r`
  装 SKILL ⇒ SKILL 是 setup 时快照而 canonical 指活 checkout。**运行时自检结构上不可自举**（检查者
  只能是 SKILL 自己或 `~/.sdflow/hack/` 的 helper，二者同为一次 `cp -r` 的产物，没跑 setup 就一起旧）；
  **CI 层面可测但目前未测**（`windows-recorder-smoke.yml` 已在 `windows-latest` 跑全量 pytest，补失鲜
  回归用例记 todo）〔spec-review-amendment F48：MUST NOT 表述为「结构性无测试面」〕。**已知且接受的边界。**
- **不提供「规则版本冻结」能力承诺**〔设计门 Q4〕——`SDFLOW_HOME` 保持既有「测试隔离重定向」契约；
  操作者自设 env 指向自备目录属环境行为、自担后果（它同时是 `setup.sh` 安装根，对其跑 setup 会覆盖
  内容）。需要冻结的真实需求出现时另立 change，MUST NOT 恢复仓内副本优先。
- **不动 `~/.sdflow/hack/capability-manifest.json`** 及其 preflight 消费方——那是 hack 链的 skew 机制，
  与 bundle 链无关，`manifest skew` 在本 change 后仍然存在。
- **不给 `WORKFLOW-GUIDE.md` 建新鲜度机制**——它纯人读、不参与执行、不被任何脚本机读，陈旧无害；
  为它建机制会把本 change 刚消灭的那类问题原样请回来。
- **不改 `openspec/schemas/` 的下发**——那是 openspec CLI 要读的 project-local schema，非 workflow 规则。

## Compliance

N/A（本仓为本地开发工具链，无外部合规面）。
