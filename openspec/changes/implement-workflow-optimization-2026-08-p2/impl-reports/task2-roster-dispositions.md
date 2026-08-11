# Task 2 impl-report — 合法组合扩展 + Roster 条件化 + 处置系统

**R-ID**: R-roster, R-裁决, R-处置 | **Blocked-by**: none

## 范围复述

DD2 合法组合矩阵扩展 + DD1 处置记录 + DD6 roster 条件化 + `retro_report.py` 处置注记——
四件串联成一条「让镜可以条件化跳过且跳过可审计」的垂直切片，四子部分 A-D 全部完成。

## A. 合法组合矩阵扩展（DD2/设计门 Q1）

- **`sdflow-init/assets/workflow/lens-metric-contract.md`**：新增契约文档版本标记（`v2`，与锚字面
  `v1` 前缀/字段集/枚举域区分——只标记合法组合矩阵变更历史）；`runner` 字段散文注记新增「普通镜行
  `runner="none"` 合法（DD2 条件跳过）」；机读输入 schema 约束①段同步放宽。
- **`sdflow-init/assets/workflow/tools/lens_metric_emit.py`**：`reduce()` 非-outside-voice 行键校验
  从「`runner==host`」放宽为「`runner==host` 或 `runner="none"`」（site 仍恒须 `"—"`）。`findings=0`
  不变量**无需额外代码**——`fold_hit` 非-ov 分支恒取 `runner=host`（不读 roster 的 `"none"`），任何真实
  finding hit 折叠后的行键第三分量恒为 host 值而非 `"none"`，与 roster 键 `(lens,host,"none","—")`
  结构性不同，命中即触发既有 C4「finding 命中行不在 roster」fail-closed——机制自然防伪造，非新增校验。
- **`sdflow-init/assets/workflow/tools/anchor_lint.py`**：`check_lens_metric()` 普通镜行 `runner`
  绑定校验新增 `runner="none" ∧ findings="0"` 为放行组合；`findings≠0` 时仍判 `ordinary-runner-host-mismatch`
  （边界锁：只放宽这一种组合，非放宽 `runner="none"` 本身）。

**测试**（TDD：先写红后写绿，已验证）：
- `sdflow-init/assets/workflow/tools/tests/test_lens_metric_emit.py`：改 1（`test_reduce_non_ov_runner_none_fail_closed`
  → `test_reduce_non_ov_runner_none_findings_zero_legal`，语义反转）+ 新增 3（bad-site 边界锁、
  finding 命中行不在 roster 边界锁、`confidence` 额外字段兼容回归锁）。
- `sdflow-init/assets/workflow/tools/tests/test_anchor_lint.py`：新增 2（legal 组合放行 + nonzero-findings
  边界仍拦）。
- 全部 331 项 `sdflow-init/assets/workflow/tools/tests/` 测试绿（`/usr/bin/python3 -m pytest
  sdflow-init/assets/workflow/tools/tests/ -q` → `331 passed`）。

## B. 处置记录（DD1）

新建 `openspec/retro/mirror-dispositions.yaml`（13 面镜完整记录，schema
`{layer,lens,host,runner,site,disposition,condition,date,rationale}`，匹配键与
`lens_metric_aggregate.group_key` 同键）：

- 11 条**保留**、1 条**降采样**（code-review/history）、1 条**不适用**（spec-review outside-voice
  claude/design-voice 回落路径产物），净效果与 design.md DD6 表一致。
- `host` 统一取 `"claude"`（历史语料以 Claude 宿主为主，理由见 yaml 文件头注释）——**已用真实仓库
  archive 语料验证**：对本仓 71 个 change 跑 `retro_report.py` 再生，13 面待复评镜**全部**精确命中
  对应处置条目、零「未命中键」告警（见下方「集成验证」）。
- 降采样条件写具体命令而非定性词：
  `git diff --diff-filter=R -M --name-only "$DIFF_BASE"..HEAD` 非空（rename）**或**
  `git diff --diff-filter=M --numstat "$DIFF_BASE"..HEAD` 中任一既有文件 (加+删) ≥200 行 → 派；否则跳过。

## C. SKILL roster 段条件化（DD6）

- **`sdflow-code-review/SKILL.md`**「规划镜头」段：新增历史镜条件化派发子条目（判定命令同上、锚行
  必落说明、报告注明句式）；fan-out 表历史镜行数量列改 `0-1` 并加条件化标注；「裁决计数」段补一句
  「历史镜若本轮跳过，roster 仍 MUST 含该行、`runner` 填 `"none"`，MUST NOT 整行省略」。
- **`sdflow-spec-review/SKILL.md`**「规划镜头」段：新增 roster 条件化派发说明——本轮 13 面镜设计门
  拍板全 5 类 spec-review 侧镜类型均**保留**（接地镜 Q3 撤回降采样），当前**无**条件跳过镜；机制文档
  与 code-review 侧同构，供未来复评轮判「降采样」时复用（未凭空发明一个当前不存在的条件）。

## D. `retro_report.py` 处置注记（DD1 消费）

- 新增 `DispositionError` 异常类 + 本地 `_yq()` 薄封装（同 `anchor_lint._yq` idiom 重实现，MUST NOT
  `import yaml`——DD1 契约）+ `load_mirror_dispositions(root)`（三态错误语义：文件缺失→`{}` 零注记；
  结构坏〔非列表/条目缺字段/`disposition` 越域/降采样缺 `condition`〕→ `DispositionError` fail-loud，
  未捕获异常经 `main()` 无 try/except 天然向上传播为非零退出码；未命中键不在此函数判）。
- `surfacing_block()` 消费：命中 `counts`（全部扫描到的锚组，非仅 `flagged` 子集）的键即时告警
  （stderr，不阻断）；`flagged` 行内命中处置表则追加 `→ 已处置: <disposition> (<date>)`。

**测试**（TDD）：`sdflow-retro/scripts/tests/test_retro_report.py` 新增 5 项覆盖四态
（文件缺失/命中注记/`disposition` 非法值 fail-loud/yaml 结构坏 fail-loud/未命中键告警不阻断），
均先验证红后实现绿。全部 133 项 `sdflow-retro/scripts/tests/` 测试绿。

## 集成验证（真实仓库语料，非合成 fixture）

对本仓运行 `python3 sdflow-retro/scripts/retro_report.py --root .`：exit 0，`openspec/retro/report.md`
成功再生，待复评区块 13 行**全部**追加 `→ 已处置: …` 注记且与 `mirror-dispositions.yaml` 内容逐字匹配，
零告警。此为处置表 `host="claude"` 假设的经验证据，非仅理论推断。

`report.md` 的 diff 中另含无关的自然漂移（自上次再生以来新归档的 change，如
`implement-workflow-optimization-2026-08-p1` 已归档、`implement-workflow-optimization-2026-08-p2`
新出现于 in-progress 行等）——这是 view-only 再生工具的预期行为，非本 ticket 引入的变更，已随
`mirror-dispositions.yaml` 一并纳入本次改动（该文件的存在必然改变再生输出）。

## 全局约束核对

- Goals 边界：改动收敛在两个评审 SKILL 的 roster 段 + 一个新数据文件 + `retro_report.py` 一处消费；
  未触碰 Step3 裁决协议本体（留给 Task 3）。
- Non-Goals：未改锚字段集，仅按声明豁免扩展合法组合矩阵；未改 Step1/Step2 编排结构，仅 roster 段
  加派发条件行。
- DD1/DD2/DD6 错误语义、锚行必落、处置表格式与阈值具体化——均已落地并测试覆盖。
- 四条通则：无自加约束（未额外限定「后端零改动」等未声明范围）；完成即全部完成，如实报告
  （无遗留子项）；落笔前已用真实语料证伪 host 假设，非空想推断。

## 全仓回归

`/usr/bin/python3 -m pytest -q`（仓根，全量发现）：**2523 passed, 10 skipped, 0 failed**（362.5s）。
10 skip 为既有跳过项，与本 ticket 改动无关（未新增/未消除任何 skip）。

## 已知边界（非本 ticket 缺陷，明确声明）

- `mirror-dispositions.yaml` 的 `host="claude"` 是历史语料统计假设，非机械保证——未来 Codex 宿主
  产出足量同镜数据后，若需独立处置判断，应追加 `host="codex"` 的独立条目（覆写用同键，git 史即
  审计链），本 ticket 不预先造条目（DD1 错误语义「未命中键仅告警不阻断」已覆盖该演进路径）。
- Task 1（validator 机械脚本 `findings_ref_check.py`）与本 ticket 并行、`Blocked-by: none`，本 ticket
  未依赖其产出，交叉验证留给 Task 3/Task 6。

## 状态

DONE
