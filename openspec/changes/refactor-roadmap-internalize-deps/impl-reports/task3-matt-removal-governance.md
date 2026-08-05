# Task 3 实现报告：matt 套件移除与治理面收口

commit: `7cc21e7`（`worktree-agent-a3f534f3bee37f6fe` 分支，基于 `4d156ec`）

## 做了什么

### 3.1 · openspec/matt/ 整目录删除
`git rm -r openspec/matt/`（4 文件：`domain.md` / `issue-tracker.md` /
`triage-labels.md` / `setup-matt-pocock-skills-handoff.md`）。删前 grep 全仓
（不带 `--include`）确认消费方：`sdflow-roadmap/SKILL.md:308,384` 仍有引用
（Task 1 SKILL.md 重写范围，本票 MUST NOT 触碰）；`docs/workflow-skills/*` 三份
历史文档、`openspec/specs/roadmap-planning/spec.md`（主 spec，Task 1/archive
范围）、`archive/` 下多个归档 change 有历史引用——均属 D13 拍板的「docs/ 历史
文档不追改」与「归档件不改」范围，本票不动。`.py` 测试文件全仓 grep 零命中
`openspec/matt` 或被删的 CLAUDE.md 三区块字面。

### 3.2 · CLAUDE.md / AGENTS.md
两文件的「## Agent skills」标题 + 三个子节（Issue tracker / Triage labels /
Domain docs）整体删除——确认该区块位于 `<!-- opsx-init:end -->` **之后**，
不在任何 `sdflow:*` / `opsx-init:*` 托管区块内，删除安全。CLAUDE.md 额外处理
「roadmaps 目录描述行去 footage 措辞」（原 `### OpenSpec 的双重角色` 节中
`openspec/roadmaps/{name}/` 条目的 「footage/」措辞改为「历史存档」中性表述），
该行同样在托管区块外。删后跑 `python3 hack/sync_principles.py --check` 退出码
0（20 个投放面全部一致），确认 principles 托管块零字节未动。

### 5.1 · 新增 ADR 0037
`openspec/adr/0037-roadmap-discussion-layer-internalization-and-matt-removal.md`，
编号取现有 36 个 ADR（`0001`–`0036`）之后的下一个可用号；小节结构（Context /
Decision / Considered Options / Consequences）从近期 ADR（0034/0035/0036）
归纳，无 template 文件可循。内容两条权衡：
- **权衡①内化分界线**：讨论过程是内在职责 ⇒ 内化；review 价值恰在外部性
  （独立冷视角）⇒ 留外。
- **权衡②能力承接边界**：memo 的 `## 未决项` 小节只承接 wayfinder frontier
  的**清单**职能，明确不承接 `Blocked-by` 依赖图与 `claimed` 并发语义
  （roadmap 场景单人操作，不需要）。

matt 移除论证按订正后的 D2 写：① matt 早于本 change 已事实废弃（`sdflow-issues`
生于本仓首个 commit 2026-07-03，早于 `openspec/matt/` 建立 2026-07-10 一周，
matt 的 issue-tracker 角色从未真正投入使用）② 独立可删、与本 change 无因果
③ 与本 change 同批做的理由是操作成本低 + 避免半改状态（fold 判据，tasks 拆成
独立第 3 节佐证不违基准 4）。**未沿用「因本次改动才孤立」的旧因果**（SR-1 /
SR-33 订正点）。

### 5.2 · CONTEXT.md 三处词条
- `footage（讨论过程考古层）` 词条重写为 `历史存档（memo 增量落盘 + 存量
  footage 统称）`，正文「决策结晶」改「决策生成」；`_Avoid_` 行补一条禁止与
  DOC-1 语境「考古层」混用改名（C5 范围限定）。
- 新增 `商业化信号（原「产品/商业野心信号」）` 词条，定义 gate-0 独立判定关系
  与词表。
- `ticket（实现分解单位）` 词条正文与 `_Avoid_` 行的 matt/wayfinder 讨论
  ticket 表述改为历史存档语境（「matt 套件已移除；存量冻结历史存档
  （`footage/`）中的历史讨论票……」）。

### 5.3 · T134 关闭
用**本仓** `sdflow-issues/scripts/issues_v2.py`（非全局 symlink）：
```
python3 sdflow-issues/scripts/issues_v2.py set-status --id T134 --to WONTDO \
  --reason "前提消解：refactor-roadmap-internalize-deps 移除 openspec/matt/ 与讨论层四个外部依赖，domain-modeling 不再是本仓工作流的调用点，matt/domain.md 已随 D2 删除"
```
输出 `{"id": "T134", "pool": "todo", "old": "OPEN", "new": "WONTDO", "file": "openspec/issues/closed/todo/T134.md"}`，
随后跑 `reindex` 子命令重建 `INDEX.md`（open 66 项）与 `CLOSED.md`（closed 221
项），确认 T134 已从 INDEX.md 移出、出现在 CLOSED.md 且 `closed_reason` 字段
正确落盘。

### 5.4 · docs/external-dependencies.md
删除「### Wayfinder 依赖（仅 sdflow-roadmap 使用）」子节（`/grilling` /
`/domain-modeling` 两行），改为一句说明「已随本 change 内化，不再是外部依赖」；
`## 5. 三方 Skill 依赖`下的 gstack 系列子节原样保留。同步 §8「内部跨 Skill 依赖」
的依赖图，删去 `sdflow-roadmap` 分支下的 `/grilling、/domain-modeling` 行，
改为「讨论层已内化，无其他外部依赖」的单行注记。

### 5.5 · openspec/INDEX.md:52
`roadmap-planning` 摘要行整句重写（非局部替词）：三相位结构（第零步重入探测
→ A 澄清+gate-0/商业化信号 → B 七维拷问按信号裁剪+memo 增量落盘 → C 生成）、
三态路由三分支、历史存档引用边界与存量 footage 冻结、review 按商业化信号分档、
收尾 checklist 四项软门。

### 5.6 · docs/sdflow-fable5/02-module-reference.md §4.6
按新结构重写：删「wayfinder footage」「野心信号」等旧表述，改为三相位结构 +
三态路由 + 历史存档定义 + 商业化信号分档 + checklist 四项。

### 5.7 · docs/drafts/roadmap-refactor-handoff.md 删除
`git rm`。删前 grep 全仓确认仅本 change 四件套（proposal/design/tasks/
tickets/task3-brief）引用它作为「已被取代」的历史指向，无其他活消费方。

## 验收标准逐条核验证据

| # | 验收标准 | 证据 |
|---|---|---|
| 1 | `openspec/matt/` 4 文件已删除 | `git status` 显示 4 个 `D`；`find openspec/matt` 无结果（目录不存在） |
| 2 | CLAUDE.md/AGENTS.md matt 三区块已删、roadmaps 描述行去 footage，两文件同步 | `grep -rn "openspec/matt" CLAUDE.md AGENTS.md` 零命中；两文件均删除「## Agent skills」整节；CLAUDE.md :190 footage 措辞已改「历史存档」 |
| 3 | ADR 0037，两条权衡，matt 论证按订正后 D2 | 文件已建，见上文摘要；MUST NOT 沿用旧因果——已核对不含「因本次改动才孤立」表述 |
| 4 | CONTEXT.md 三处词条 | `grep -n "历史存档\|商业化信号" openspec/CONTEXT.md` 命中新增/改写的三个词条块 |
| 5 | T134 关 WONTDO 带 --reason，用本仓脚本 | 见上文命令输出 + `openspec/issues/closed/todo/T134.md` frontmatter `status: "WONTDO"` |
| 6 | external-dependencies.md 删 §5 + 同步 §8，gstack 节保留 | `grep -n "grilling\|domain-modeling" docs/external-dependencies.md` 仅剩说明性提示句（非表格行）；`### 评审流程依赖（gstack 系列）` 子节表格原样保留 |
| 7 | INDEX.md:52 整句重写 | 已核对新行含「三相位」「三态路由」「历史存档」「checklist 四项」关键词，不含「wayfinder」「野心」「footage 落盘位置」等旧词 |
| 8 | 02-module-reference.md §4.6 按新结构更新 | 已核对新段落含三相位/三态路由/历史存档/商业化信号/checklist 四项 |
| 9 | roadmap-refactor-handoff.md 已删除 | `git status` 显示 `D docs/drafts/roadmap-refactor-handoff.md` |

## 跑过的命令与退出码

```
python3 hack/sync_principles.py --check          # exit 0（20 个投放面一致）
python3 sdflow-issues/scripts/issues_v2.py set-status --id T134 --to WONTDO --reason "..."   # exit 0
python3 sdflow-issues/scripts/issues_v2.py reindex                                            # exit 0
/usr/bin/python3 -m pytest hack/tests/ sdflow-issues/tests/ -q   # exit 1（2 failed, 482 passed, 6 skipped）
```

`pytest` 的 2 个失败均为**先于本票存在的 baseline 失败**，与本票无关：

1. `hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`
   —— `tasks.md` 6.2 已明文记录为「当前 baseline 已有 1 个先于本分支存在的失败……
   与本 change 无关，不在本 change 修复范围」。
2. `hack/tests/test_subprocess_encoding_contract.py::test_text_mode_subprocesses_declare_utf8_and_replace`
   —— 未在 `tasks.md` 中预先记录，但已用 `git stash` 隔离核验：**本票的改动
   （全部为 Markdown / 一次 issue 状态迁移）落地前跑同一测试同样失败**
   （`git stash` 恢复到 `4d156ec` 状态后单独跑该测试，`189 >= 200` 断言同样
   失败，输出完全一致）。确认这是与本票无关的既有 baseline 失败（该测试统计
   全仓 Python 文件的 subprocess 调用点数量，我的改动零处涉及 `.py` 文件）。

两个失败**相对 merge-base 无新增**，符合 tasks.md 6.2「相对 merge-base 无新增
失败（非全仓绿）」的验收口径。

## Concerns

无。本票范围内改动全部完成，未发现需要上抛编排层的设计缺口或范围外发现。

## 遗留说明（非本票范围，供编排层知悉）

- `sdflow-roadmap/SKILL.md:308,384` 仍引用 `openspec/matt/issue-tracker.md`
  preflight 校验——这是 Task 1（SKILL.md 重写）的范围，本票未触碰该文件。
- `openspec/specs/roadmap-planning/spec.md`（主 spec，非本 change 的 delta）
  仍有 `openspec/matt` 引用——delta spec 覆盖与 archive 阶段同步是 Task 1 /
  归档阶段的范围。
- Task 6（验证）的全量 grep 残留扫描（6.1，词表含 `openspec/matt`）、主 spec
  提升后核验（6.9）等收尾任务由后续票承担，未在本票范围内执行。

---

## 双轴审后补充披露〔编排层追加，非 implementer 原文〕

### 1. `reindex` 副作用：INDEX.md / CLOSED.md 夹带 25 条预存漂移（Standards 轴 Important）

本票为关闭 T134 跑了一次 `reindex`。`reindex` 是**全量重建单一源**，因此除 T134 外，还把
此前已积累但快照未刷新的约 25 条历史条目一并同步进本次 diff（T12/T15/T56/T68/T69/
T93-T96/T128/T130/T131/T139/T140/T174/T176/T188/T199/T207/T229/T230/T250/T252/T253/T261）。

**这些 issue 与本票无关**——它们早已由更早的提交关闭、文件早已存在于
`openspec/issues/closed/todo/` 磁盘上，只是 `INDEX.md` / `CLOSED.md` 的快照落后于磁盘。

编排层核实（非采信自述）：
- `git ls-tree -r --name-only main | grep "issues/closed/todo/T12.md"` 等抽样（T12 / T56 / T229）
  → 三者在 `main` 上即已位于 `closed/`，命中数各 1。
- `git diff --name-status 5262e21..fc221e4 -- openspec/issues/` → 文件级改动**只有** T134 一条
  `R062 open/todo/T134.md → closed/todo/T134.md`，其余仅 `CLOSED.md` / `INDEX.md` 两个快照文件。

⇒ 属**正确的机械行为**（单一源重建），不是本票误动了 25 个 issue。此处显式披露，避免未来读
`git blame` / diff 的人误判本票范围。

### 2. `AGENTS.md` 无「roadmaps 目录描述行」可改（Spec 轴 Minor）

`tasks.md` 3.2 要求「roadmaps 目录描述行去 footage 措辞（两文件同步改）」。实测该描述行
**本就只存在于 `CLAUDE.md`**，`AGENTS.md` 中无对应内容（`grep 'openspec/roadmaps/{name}' AGENTS.md`
零命中）。∴ AGENTS.md 侧「无可改之物」而非「漏改」；matt 三区块的删除两文件均已完成。

### 3. 两项 `cannot-verify-from-diff` 的编排层消解

| 项 | 消解方式 | 结论 |
|---|---|---|
| `reindex` 输出（INDEX open 66 / CLOSED closed 221） | 编排层改为核验**结果一致性**而非命令回显：见上第 1 节的两条 git 证据，双写与磁盘状态一致 | 已消解 |
| `pytest` 相对 merge-base 无新增失败 | **不在本票消解**——转由「实现验证」收尾票（Task 6）承担全量聚合回归，并在那里复核 baseline 已知失败清单（`tasks.md` 6.2 只登记 1 条，Task 2 与 Task 3 两票各自独立用 `git stash` 复现出**第 2 条** `test_subprocess_encoding_contract.py`，该差异 MUST 在 Task 6 证据行如实记录） | 转 Task 6 |
