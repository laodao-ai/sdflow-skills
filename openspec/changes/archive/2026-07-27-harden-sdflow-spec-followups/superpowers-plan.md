---
impl-pipeline: tickets
---

## Global Constraints

以下为逐字摘自本 change `design.md` 的硬约束与 Compliance 条款（非转述），对每张 ticket 的
implementer 与两轴审 reviewer 同等生效。

- 不做 T239 的下游 rollout，不重启外派模式，不解析 shell 语法。
- [spec-review-amendment] 只有整条命令完整匹配一条直接 literal 创建调用（`openspec new change <合法字面量>` 或 `openspec change new <合法字面量>`，保留既有空白、单双引号与 `--json` 变体）时，才把 payload `cwd` 作为判定仓并进入原三分支。
- 命令串含创建字样但不是该有限 grammar 的单条直接调用——包括 `cd`/`pushd`/`env -C`/shell wrapper、复合运算符、换行、前后散文或动态名——统一输出仅含 `hookEventName` 与 `additionalContext` 的 JSON，不设置 `permissionDecision`。
- 既有“多处可识别创建调用必须拆开”的 deny 在此 cwd 判定前保留。
- [spec-review-amendment] 所有未命中直接 grammar 的单调用统一使用 `command-unverifiable` 加人类可读说明，不再按 cwd、change 名或 shell 组合推测细分原因。
- [spec-review-amendment] `SKILL.md` 保留四条通则、frontmatter、Phase 0/A/B/C、C.1 四判、终审、`openspec validate --strict`、`sdflow-spec-grill`/`sdflow-spec-generate` 两个 checkpoint、出口三步，以及“何时读哪个 reference”的条件与相对路径。
- 未启用的外派协议、详细降级诊断和演进依据移入三个 reference。
- 新增测试以 Python `len()` 验证入口不超过 18,000 Unicode 字符，并以 resident-contract token map 逐项锚定上述语义；只保留空标题或无加载条件的链接不得通过。
- [spec-review-amendment] Codex 没有本 session 可调用的 Skill 执行面，因而只记录“用户显式触发被接受”，不把接口缺席误写成模型调用被拒。
- 终审以整个 change 目录为追溯边界，`decision-memo.md` 是被砍候选和理由的合法唯一载体。
- 本 change 只订正 T132 未来 gate 的 A/B 输入契约与台账描述，不实现或关闭 T132：A 需要身份/hash/必填节有效的 `decision-memo.md` 加 `checkpoint(sdflow-spec-grill)`；B 需要既有 `checkpoint(grill)` 或未来 gate 明确认可的 `sdflow:grill-done` 锚。
- 本 change 不向下游执行 update；T239 保持为独立 rollout 待办。
- 不新增外部服务、持久化数据或凭据处理；hook 只处理本机 PreToolUse payload。

### Task 1: FF-0 对错仓不执法并留下未越权审计

**Blocked-by:** none
**R-ID:** FF-0

当命令完整匹配单条直接 literal 创建 grammar 时，FF-0 继续在 payload 仓执行 protected、同 change、
其他 feature + ack 三分支；其余包含创建字样的 wrapper、目录切换、复合命令、散文或动态名统一输出
`command-unverifiable` 审计 context，不设置权限决定，也不尝试解释 shell 或细分未判定原因。多处创建调用仍在 cwd 判断前拒绝拆分。

- [x] 允许的空白、单双引号与 `--json` 直接调用变体都进入原三分支，既有 ack 与哨兵行为不回归
- [x] `cd`、wrapper、compound、换行、decoy、变量、命令替换与 glob 的代表性形态统一产生 `command-unverifiable` context，且没有 `permissionDecision`
- [x] 未判定路径删除 `undecided_reason`、动态 marker、双分支说明与旧原因码兼容断言；不含 shell 形态交叉分类器，不展开 shell，也不推测 cwd/name 的细分原因
- [x] 多调用或名字冲突仍按既有 stacking deny 处理，判定先于 cwd 未决分支
- [x] `sdflow-init/tests/test_ff0_branch_guard.py`、`hack/tests/test_canonical_entry_sync.py`、canonical workflow 与入口叙述同步到正向有限 grammar 和单一未判定边界

### Task 2: 薄化 `sdflow-spec` 常驻入口并保持完整执行契约

**Blocked-by:** none
**R-ID:** SA-01, SA-06, SA-16, SA-15

`sdflow-spec` 默认入口只常驻三相位执行、终审、strict validate、两个 checkpoint 与出口序列；未启用
外派、详细诊断和演进依据改为按条件加载的 versioned reference。宿主能力、整个 change 目录追溯边界
以及 T132 的 A/B 未来输入契约按已批准的证据边界表述，不把缺接口写成已机械拒绝，也不实现 T132。

- [x] 入口以 Python Unicode 字符数计不超过 18,000，且 frontmatter 与四条通则仍完整
- [x] resident-contract token map 逐项证明 Phase 0/A/B/C、C.1 四判、终审、strict validate、两个 checkpoint 与出口三步仍有实质语义
- [x] 三类按需资料各有明确加载条件和可达相对 reference，空标题、裸链接或缺加载条件均被测试拒绝
- [x] Codex 文案只声明用户显式触发已观察，整个 change 目录及 `decision-memo.md` 被终审追溯接受
- [x] T132 仅留下 A/B 分治的未来 gate 输入契约并保持 OPEN，外派仍未启用

### Task 3: 用逐票证据闭合规格与问题台账

**Blocked-by:** 1, 2
**R-ID:** FF-0, SA-01, SA-06, SA-16, SA-15

把已实现的 FF-0 与入口契约同步到权威规格，并按 closure matrix 逐 ID 核对证据后更新问题台账；归档
证据、当前实现证据和仍未处理项采用不同终态规则，不能以 schema 或重建索引成功代替语义闭合。

- [x] T232/T238/T240/T241 仅在归档 artifact 证据真实存在时关闭
- [x] T233–T237/T242 仅在本 change 对应实现与测试通过时关闭，T234 的 A/B 输入订正有独立证据
- [x] T132 仍为 OPEN，T239 仍为未处理，逐 ID 断言可阻止误关
- [x] 主规格、delta、台账状态与证据备注互相一致，重建或校验不会丢失逐票语义

### Task 4: 刷新本机安装并完成端到端验收

**Blocked-by:** 3
**R-ID:** FF-0, SA-01, SA-06, SA-16, SA-15

在 canonical 实现、入口与台账全部闭合后，先完成 focused 与契约测试，再通过开发更新和 setup 刷新
本仓 dogfood workflow、全局 hook 与 Claude/Codex skill 安装，最后跑全量回归并机械比对安装结果；任何
相关 skipped、注册缺失、目标漂移或测试失败都如实判失败。

- [x] hook、canonical-entry、failure/agent、resident-contract、体量门与 issue focused pytest 全部通过
- [x] 通则同步检查、OpenSpec strict validate 与空白检查全部通过
- [x] 开发更新后 canonical hook 与已安装 hook 字节一致，settings 注册存在
- [x] setup 后 Claude/Codex skill 指向正确 canonical source，相关安装步骤没有 skipped 或不一致
- [x] 全量 `uv run --with pytest pytest` 通过，并记录实际结果与任何既有失败
