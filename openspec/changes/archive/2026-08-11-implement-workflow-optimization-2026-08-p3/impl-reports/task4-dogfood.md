# Task 4: 首轮 dogfood + 收口 — 实现报告

## 概述

按 `impl-reports/task4-brief.md` 逐项跑通 `sdflow-upstream-watch` 首轮真实链路（真网络四源采集
→ 模型写分诊报告 → advance 建锚）+ 收口 T264/T245/T246/T267 四个散点 + 全仓回归。全部 8 项验收
标准逐条核验通过，无跳过项。

## 逐步执行结果

### 1. setup.sh 验证

```bash
bash setup.sh
```

- `sdflow-upstream-watch` 新链在 `~/.claude/skills/` 与 `~/.codex/skills/` 均建立成功（symlink
  → `~/Documents/04-sdflow-skills/sdflow-upstream-watch`，`readlink` 核实过）。
- `python3 hack/sync_principles.py --check` → `✅ 23 个投放面全部与真相源一致`，exit 0。
- setup.sh 输出同时含 `[gen_workflow_guide]` `[async-branch-parity]` `[tier-resolution-parity]`
  `[encoding-hygiene]` 四道机械门，均 ✅。

### 2. 首轮 collect（真实网络）

```bash
python3 sdflow-upstream-watch/scripts/upstream_watch.py collect
```

facts 落 `openspec/upstream/.facts/20260811T123253Z.json`（该目录 `.gitignore`，非留存产物）。
四源均 `status: ok`，无降级：

- **gstack**：`status: ok`，`head_sha=94993f74…`，`commits` 含 1 条（v1.61.0.0 fix wave）。
  本地锚源 `~/.skills/gstack` 实测 HEAD = `960c3a8d6c4d…`（v1.60.2.0），已用
  `git -C ~/.skills/gstack log --oneline 960c3a8..FETCH_HEAD` 核实区间非空——**真 delta 确认**，
  非「当前态即基线」零 delta 分支。
- **matt**：`status: ok`，`head_sha=84fdeffd…`，首轮无持久锚 → `commits=[]`（design 定义的
  预期行为），`installed_skills` 附带 36 个本地已装 skill 的 hash 快照。
- **superpowers**：`status: ok`，`head_sha=920824c3…`，`installed_version=6.2.0`，首轮同样
  `commits=[]`（无持久锚 ⇒ 当前态即基线）。
- **openspec**：`status: ok`，`installed_version=latest_version=1.8.0`（无版本差）；
  `schema_drift.status=ok`，`changed=[schema.yaml, templates/proposal.md]`，`added=[]`，
  `removed=[]`。

### 3. 模型写报告

报告落 `openspec/upstream/reports/20260811T123502Z.md`，按 SKILL.md 模板逐源分节 + 三分诊。
关键判断（均基于 `git show`/`diff` 实际读取内容，非解析上游语义）：

- **gstack**（1 条 squashed 发布提交，9 个子修复）→ **不吸**（整体）。逐项核对：
  - AskUserQuestion / `permissionDecision:'defer'` 语义漂移修复 → 已核对本仓唯一 PreToolUse
    判定型 hook（`sdflow-init/assets/hooks/ff0-branch-guard.py`），其未判定路径本就只输出
    `additionalContext`、从不设 `permissionDecision`（`ff-generation-constraints.md` 明文
    约束）——本仓已站在正确一侧，无对应缺陷可修。
  - `/careful` 链式 rm 绕过、`/context-restore` worktree 误读、`/sync-gbrain` drift 重注册、
    developer-profile 计数重复、one-way-door 凭据网、design CLI 数值 flag NaN → 均已核实本仓
    无对应机制/无同类缺陷面（已 grep 全部 `add_argument` 调用确认无数值型 flag 静默失败面）。
- **matt/superpowers**：首轮零 delta（设计预期），无可分诊内容。
- **OpenSpec**：**吸收候选** 1 条——`diff` 实读两文件后确认 schema drift 混合两类差异：
  本仓既有意图性定制（`name: sdflow-spec-driven`、`sdflow:delegation` STOP 指令块）+ 上游
  真实新能力（capability 标识从扁平 `<name>` 改为支持嵌套路径的 `<capability-path>`，如
  `identity/user-auth`）。已在报告内预生成完整 `recorder add` 命令（含
  `source_change: "sdflow-upstream-watch"`），未执行（人拍板后才执行，watch 自身不改池）。
- **Seed T245/T246**：观望（D8 mid 档钉死前置决定未解除）。
- **Seed T267**：吸收候选（scope 已由此前评审定义清楚，无阻塞前置决定；已在池内以 T267
  追踪，本轮无需重新 add）。

### 4. advance 建锚

```bash
python3 sdflow-upstream-watch/scripts/upstream_watch.py advance \
  openspec/upstream/reports/20260811T123502Z.md \
  openspec/upstream/.facts/20260811T123253Z.json
```

（注：`upstream_watch.py advance` 的实际 CLI 是位置参数 `advance <报告路径> <facts路径>`，
非 `--report`/`--facts` 具名参数——已核实脚本 `argparse` 定义并按实际签名调用。）

输出 `advance: 锚已推进`，exit 0。`openspec/upstream/anchors.yaml` 首次建档：

```yaml
schema_version: 1
last_run: "2026-08-11T12:36:49Z"
remind_after_days: 30
sources:
  gstack:
    anchor_sha: 94993f74012782fd94416dd44b8314f6363a13a4
  matt:
    anchor_sha: 84fdeffd12f2ee307994d1eb6feb48173b6e0502
  superpowers:
    anchor_sha: 920824c3e9509890fbec03ba6097014222393022
    installed_version: 6.2.0
  openspec:
    anchor_version: 1.8.0
```

### 5. T264 → DONE

```bash
python3 sdflow-issues/scripts/issues_v2.py --root ~/Documents/04-sdflow-skills \
  set-status --id T264 --to DONE \
  --evidence "schema drift 采集器实现 + 测试：sdflow-upstream-watch/scripts/upstream_watch.py collect_openspec() + _diff_dirs_sha256() + tests/test_upstream_watch.py 相关用例"
```

（注：脚本实际 CLI 是 `--to`（非 brief 里写的 `--status`）、`--root` 须置于子命令前——已按
`issues_v2.py --help` 实际签名调整，非按 brief 字面死跑。）

输出 `{"id": "T264", "pool": "todo", "old": "PROPOSED", "new": "DONE", "file":
"openspec/issues/closed/todo/T264.md"}`，exit 0。文件已迁移到
`openspec/issues/closed/todo/T264.md`。

### 6. T245/T246/T267 池内原状核验

执行前后各取一次 sha1sum，逐字节比对：

| 文件 | 执行前 | 执行后 | 一致 |
|---|---|---|---|
| T245.md | `3550b235…` | `3550b235…` | ✅ |
| T246.md | `4999d4ff…` | `4999d4ff…` | ✅ |
| T267.md | `8a1841f6…` | `8a1841f6…` | ✅ |

三文件哈希在 collect/advance/set-status 全程前后完全一致，未被本轮任何机械操作触动。

### 7. 全仓 pytest

```bash
/usr/bin/python3 -m pytest -q
```

`2607 passed, 10 skipped in 361.41s (0:06:01)`，0 failed。

### 8. 手工验收 upgrade 提醒两分支 [e2e]

未真跑 `sdflow-upgrade`（会真升级运行 checkout，超出本票范围），改为按 `sdflow-upgrade/SKILL.md`
第 5 步文本描述的确定性 shell 逻辑逐分支手工模拟验证（`yq` 命令与判定条件均取自 SKILL.md 原文）：

| 分支 | 输入 | 预期 | 实测结果 |
|---|---|---|---|
| 文件不存在 | 不存在的 anchors.yaml 路径 | 静默跳过（yq 非零退出被捕获） | `yq` 报 `Error: open … no such file`，exit 1 → 符合「静默跳过」前置条件 |
| `last_run: null` | 构造的 scratch anchors.yaml | 静默跳过 | `yq -o json '.last_run'` → 输出字面 `null` → 符合「静默跳过」判据 |
| 真实当前态（0 天） | 本轮刚建的真实 anchors.yaml | 未超阈值，不提醒 | `last_run` 距今 0 天 < 30 天阈值 → 不提醒 ✅ |
| 超阈值（40 天前） | 构造的 scratch anchors.yaml（`last_run` = 40 天前） | 输出含天数的提醒行 | 输出：「距上次 `/sdflow-upstream-watch` 已 40 天（阈值 30 天），建议找时间跑一轮」✅ |

四分支（含 brief 要求的「超阈值提醒」与「无锚静默」两条核心分支）逻辑均验证通过，构造文件均在
scratchpad 临时目录操作、验证后清理，未污染仓内任何文件。

## 验收标准逐条核验

- [x] setup.sh 新链建立成功 + sync_principles --check 绿
- [x] 首轮 collect 四源均产出 facts（4 源全部 `status: ok`，均有据——gstack 有真 delta，
      matt/superpowers/openspec 首轮零 delta 为设计预期行为，非降级）
- [x] 报告落盘且 gstack 节含真 delta（`960c3a8..94993f7` 区间非空，1 条 commit）
- [x] advance 建锚成功（`anchors.yaml` 已创建、`last_run` 已写入）
- [x] T264 已 set-status DONE（evidence 指采集器实现+测试）
- [x] T245/T246/T267 池内原状未变（sha1sum 前后逐字节比对一致）
- [x] 全仓 pytest 绿（2607 passed, 10 skipped, 0 failed）
- [x] [e2e] upgrade 提醒超阈值时输出一行含天数的提醒、无锚时静默跳过（四分支手工模拟验证）

## 发现与偏离

- brief 中 `advance --report <路径> --facts <路径>` 与 `set-status --status <值>` 两处命令语法
  与脚本实际 CLI 不符（实际为位置参数 `advance <报告> <facts>`、`set-status --to <值>` 且
  `--root` 须在子命令前）。已按脚本 `--help`/`argparse` 定义实际签名调整执行，未改动脚本本身——
  这是 brief 文本的笔误，不是代码缺陷，如实记录供后续参考。
- OpenSpec schema drift 的 `changed` 结果混合了「本仓既有意图性定制」与「上游真实新能力
  （嵌套 capability 路径）」两类差异，报告内已用人工 diff 阅读区分并只把后者判「吸收候选」，
  前者判「不吸/预期差异」——避免把已知定制误报为待办漂移。

## 产出物清单

- `openspec/upstream/anchors.yaml`（新建，首轮建锚）
- `openspec/upstream/reports/20260811T123502Z.md`（新建，首轮分诊报告）
- `openspec/upstream/.facts/20260811T123253Z.json`（`.gitignore`，非留存产物，未提交）
- `openspec/issues/open/todo/T264.md` → `openspec/issues/closed/todo/T264.md`（DONE）
- `openspec/changes/implement-workflow-optimization-2026-08-p3/impl-reports/task4-dogfood.md`（本文件）

## 未改动确认

- 未修改 `tickets.md` / `design.md` / `proposal.md` / `specs/` / `tasks.md`（`tickets.md` 的
  工作区改动是任务开始前已存在的 Task 3 复选框补打，非本次改动，`git diff` 已核实内容与本票
  执行内容无关）。
- 未打 `task4-` 标签，未 `git commit`——按输出契约留给编排层双轴审后处理。
