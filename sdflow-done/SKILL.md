---
name: sdflow-done
description: >
  Finalize an OpenSpec change: reconcile tasks → verify (evidence-anchored, anti-false-green) →
  hand-off.md → archive (openspec CLI, with
  delta-spec sync into openspec/specs/) → git commit → merge to the repo's default branch
  BY DEFAULT (opt out by saying so at invocation). Steps are fixed + each runs in its own
  subagent, so model choice is per-step (no coupling): verify → the strong tier (gate /
  judgment), archive → the mid tier (judgment), commit → the light tier (mechanical); tier-to-model defaults are centralized in
  model-tiers.md. The archive subagent verifies each delta against
  actual code so the synced spec reflects post-review reality, not a stale delta; merge
  runs by default (ff) in the main session unless opted out (one-way git kept visible).
  verify writes verify-report.md (every ✅ needs a machine-verifiable anchor — test name / commit /
  file:line; no-anchor ✅ → gap); a hand-off.md (done/not-done + deferred items + next-stage advice)
  is produced after verify and before archive, and travels with the archive. As the final gate after
  stage-3 drops the human gate, verify runs on a strong model with a Do-Not-Trust cold start. Use when
  implementation is complete and reviewed. Trigger with /sdflow-done.
---

# sdflow-done — OpenSpec 变更收尾

将 reconcile → verify → **hand-off** → archive → git commit → merge 串成一条收尾流水线。各步独立子代理、按本步性质选 model（见「模型选择」）：**verify → 强档**（唯一终门），**archive → 中档**（判断），**commit → 弱档**（机械）；**merge** 留主 session（单向 git，缺省执行、调用时可 opt-out）。

> **核心改进（v3，基于实战）**：① 归档**必须**走 `openspec archive` CLI 以**同步 delta 到主 specs**（旧版手动 `mv` 漏了这步，新能力永远进不了 `openspec/specs/`），遇中文遗留 spec 用 `--skip-specs` + 手动同步；② 默认分支自动检测（勿假设 main）；③ **merge 缺省执行**（ff），不想合并就在调用时明说；④ verify 必产 `verify-report.md` 存 change 目录（随归档留档）；⑤ 步骤固定 + 各步独立子代理 → 按本步性质选 model（verify=强档、archive=中档、commit=弱档）。

---

## 第零步：确认 change + 检测默认分支 + 复选框对账

### 0.1 确认 change + 捕获 merge 意图

若未指定 change 名称，`openspec list` 展示 active changes，请用户确认。记为 `{change_name}`，路径 `openspec/changes/{change_name}/`。

**merge 缺省执行**：除非用户在调用本 skill 时**明确说不合并**（如「不要 merge」「don't merge」「只归档别合」「skip merge」「先不合」），否则第五步**默认 ff 合并到 `{base_branch}`**。在此记下 `{merge_intent}` = `merge`（默认）或 `skip`（用户 opt-out）。

### 0.2 检测默认分支（勿假设 main）

```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' \
  || (git rev-parse --verify origin/master >/dev/null 2>&1 && echo master) \
  || echo main
```

记为 `{base_branch}`（很多仓库是 `master`，不是 `main`）。后续 merge 用它。

### 0.3 tasks.md 复选框对账（关键，否则 verify/archive 被误导）

实现常经 `superpowers-plan` / subagent-driven-development 完成，change 自己的 `tasks.md` 复选框**没被勾**。这会让 `openspec archive` 警告 "N/M incomplete"、让 verify 误判。

- Read `openspec/changes/{change_name}/tasks.md`，与实际实现对照（看 git log / 实现 commit）。
- **已真实完成的任务勾上** `- [x]`；**确实未做/部分做的保持 `- [ ]` 并补一句说明**（别为过 archive 假勾——保持记录诚实）。
- 若整批确实完成，可 `sed -i '' 's/^- \[ \]/- [x]/g; s/^  - \[ \]/  - [x]/g'` 批量勾，再单独把未完成项改回。

---

## 第一步：Verify（强档子 agent）

> 用强档而非中档/弱档：verify 是**质量门**且要 grep 代码判 PASS/FAIL、辨核心 vs Minor 缺口，judgment 活，中档/弱档易误判 PASS 放不完整的活进归档。sdflow-done 低频，省那点 token 不值。
>
> **P3h 禁降档（阶段三去人类门后 verify = 唯一终门）**：铁律"带门禁 / 无人逐条复核的步别用弱档——假绿会放不完整的活过关"。verify 用强档 + 下方 prompt 的 **"Do Not Trust the Report" 冷启**，靠证据锚点硬约束堵假✅，不靠人盯。见 design §7.3.1 / adr/0001。

派发 Agent（model: 按规则根 model-tiers.md 强档；config.yaml model-tiers 段可覆盖），prompt：

```
你是 OpenSpec 验证助手。工作目录：{项目根目录}。
任务：verify change `{change_name}`。

**重要（Do Not Trust the Report，P3h 防假✅）**：核对的是**代码是否真的实现了 tasks.md/specs 的每条要求**，不要只看复选框状态、也不要信任任何已有报告的措辞（实现可能经外部计划执行；复选框/报告可能 stale 或乐观）。**每条判 ✅ 的需求必须附一个可机验证据锚点（测试名 / commit hash / 文件:行）；找不到锚点的一律判 gap，绝不凭复选框或"看起来做了"判 ✅**。真实事故：曾有 verify 把两条根本没落实的需求（无 benchmark 实现）标 ✅ 静默放过，靠事后人肉才揪出（见 design §7.3.1 / adr/0001）。

步骤：
1. Read openspec/changes/{change_name}/tasks.md（看要求什么）
2. Read openspec/changes/{change_name}/specs/ 下所有 spec（ADDED/MODIFIED 需求）
3. 用 Grep/Read 核对**代码/迁移/测试**是否反映每条要求（迁移文件、SP、Go、前端、测试）
4. 判定：**只报真实缺口**（代码确实没实现的）。Minor 级（可观测性日志、UX polish、文档）即使缺也判 PASS 并注明「Minor 缺口」；只有**核心功能**缺失才 FAIL
5. **（硬性可交付）必须**写出 `openspec/changes/{change_name}/verify-report.md`（先 Read 是否存在再 Write/Edit），结构：
   - **报告头部 frontmatter（ship-gate 契约，mlh-p5 迁 frontmatter，模板写死二选一，勿改写字段名、勿两键并存）**：
     MUST 在文件**最顶端**（prepend，非追加末尾）写：

     ```yaml
     ---
     ship-gate:
       verify: PASS
     ---
     ```
     或

     ```yaml
     ---
     ship-gate:
       verify: FAIL
     ---
     ```

     ——`verify` 字段二选一（`PASS`/`FAIL`，大写、非布尔），/sdflow-ship 读此 frontmatter 机判。
     若文件已有首块 frontmatter，MUST 合并 `ship-gate:` 键进已有块（不新开第二块）；若无则新建。
   - 标题 + 日期 + change 名
   - **结论**：PASS / FAIL（人读结论行，紧跟标题下方，供人阅读；frontmatter 已是机判锚，此行不可省略）
   - **逐需求核对表**：| 需求/任务 | 代码出处(文件:行/迁移/测试) | 状态(✅实现/⚠️Minor缺口/❌核心缺失) |
   - **缺口清单**：核心缺口（FAIL 项）+ Minor 缺口（注明可接受/deferred）
   - 此文件会随第三步归档一起进 `openspec/changes/archive/`，作为本 change 的验证留档
6. 末行输出：PASS 或 FAIL（附原因）

先 Read 再 Edit。报告**不可省**——没有 verify-report.md 视为 verify 未完成。
```

- **PASS**（含「PASS + Minor 缺口」）→ 继续第二步
- **FAIL**（核心缺口）→ 停止，展示原因，等修复后重新触发

---

## 第二步：产出 hand-off.md（P3g，verify 之后 / archive 之前）

verify 判定完（它才权威定完整性）后、归档前，产出 `{change_dir}/hand-off.md`——**异步人类再入口 + 下个 change 种子**，随归档一起进 `archive/`。主 session 直接写（它有本 change 的 why 与 defer 上下文）或派中档子代理。

**三段内容**：

1. **✅ 完成了什么**：引 verify-report 的 done 项。**P3h-c：不直接搬运 verify 的 ✅**——每条至少复核锚点存在性（测试名 / commit / 文件:行 真的在），再写进"完成"；无锚点的不写成完成。
2. **⏳ 未完成 / 延后**：本 change 新增的 buglist/todolist（sdflow-code-review defer 的，已按下方 §2.1 sweep 分诊进批次 `{change_name}`，见 `openspec/issues/batches.md`）+ 被延后的 ≥2 方案决策（附当时自动选了什么 / 为何拿不准）+ verify 的 Minor 缺口。
3. **▶ 下一阶段建议**：建议开哪个清理 change、优先级；哪些 defer 项该一起清。

> **为何独立成步、不并进 verify 或 archive**：verify 判"完整性"、hand-off 是"给人的高层交接 + 下阶段种子"，altitude 不同；时机必须在 verify **之后**（引其权威结论）、archive **之前**（随归档留档）。sdflow-done 是自制 skill，加此步无碍。

### 2.1 issues sweep 子步（先于上面「三段内容」撰写，I5/I6）

verify 判完之后、写 hand-off 正文之前，先把**本 change 新增**的未分诊 OPEN 项归入一个批次——这样上面第 2 段能引批次号，而不是逐条罗列裸 ID。主 session 直接跑（纯机械 bash，无需额外派子代理；若第二步整体交给了中档子代理，由该子代理顺带执行）。

**脚本路径**：buglist.py / todolist.py / issues.py 分属 `sdflow-buglist`、`sdflow-todolist`、`sdflow-issues` 三个 sibling skill，随 sdflow-skills `setup.sh` 各自独立 symlink 到 `~/.claude/skills/`（同 tag、sdflow-init 等 skill 引用兄弟脚本的既有约定）：

```
~/.claude/skills/sdflow-buglist/scripts/buglist.py
~/.claude/skills/sdflow-todolist/scripts/todolist.py
~/.claude/skills/sdflow-issues/scripts/issues.py
```

若该固定路径不存在（非常规安装/裸源码检出），在 `~/.claude/skills/`、`~/.codex/skills/`、或本仓库内 `find . -name buglist.py` 兜底定位，找不到就停下问用户脚本在哪。

以下命令在 `{项目根目录}`（cwd）下执行，`--root` 缺省即当前目录，脚本自动探测 git 根。原手写 4 步循环（scan 两池 → 逐项 triage → batch add → reindex）已固化为 `issues.py` 的一键封装子命令 `sweep`〔impl-review-fix：措辞订正，非原子、fail-closed、可重跑收敛〕，一行跑完：

```bash
python3 ~/.claude/skills/sdflow-issues/scripts/issues.py --root . sweep --change {change_name}
```

**必须显式传 `--change {本change}`（D4）**——不靠 `detect_change` 猜；sweep 内部即用该值扫描 `--open-ungrouped`（非终态 ∧ 批次空）、逐项 triage 进同一批次、`batch add --if-exists skip`、末尾 `reindex`。**hand-off 引用该批次**：上面「三段内容」第 2 段写批次号 `{change_name}`（指向 `openspec/issues/batches.md` 对应条目 + `openspec/issues/INDEX.md`），不再逐条罗列裸 ID。

**执行纪律（D6）**：调用方 MUST 串行跑本步、勿与手动 triage 交叉——sweep 写窗口比单条命令更长（N 次 triage 写 + batch add + reindex），并发安全未焊接（归 TG-26/Phase C）。

**失败语义（非原子、fail-closed、重跑收敛）**：sweep 不是真原子——任一子步（scan/triage/batch add/reindex）非零退出即整体非零退出，stderr 报明失败步 + 失败点位（第 i 项/哪个 pool/已 tag 的 id 列表），不静默继续；已 tag 项在重跑时被「批次空」过滤天然排除，故半途失败后**直接重跑同一条命令即可收敛到完成**，无需手工回滚。

**范围边界（design §4.2，不在本 sweep 内）**：sweep 只圈**源 == 本 change**的未分诊非终态项（`--open-ungrouped` 口径）。孤儿项（源 = `""`，多 change 并行、`detect_change` 探不出归属的）**不归本 sweep 管**——由独立的通用「清 bug/todo」工作流兜底（`scan --open-ungrouped` → `triage` → 另开 cleanup change），不因 sweep 窄而无声蒸发；sweep 本身保持窄而确定，别为了兜孤儿放宽 `--change` 过滤。

---

## 第三步：Archive + Spec 同步（中档子 agent）

整步交一个**中档**子 agent 执行（隔离主 session 上下文）。它**不能假设知道本次实现细节**（fresh 上下文），所以 prompt 要求它**读真实代码核对每条 delta**——这样同步出的 spec 反映**终审后实况**而非可能过时的 delta，无需控制者口头传递偏差。

⚠️ 归档**必须**用 `openspec archive` CLI（同步 delta→`openspec/specs/` + INDEX + 校验），**禁手动 `mv`**（漏 spec 同步）。

派发 Agent（model: 按规则根 model-tiers.md 中档；config.yaml model-tiers 段可覆盖），prompt：

```
你是 OpenSpec 归档助手。工作目录：{项目根目录}。语言中文。
任务：归档 change `{change_name}` 并把它的 delta 同步进主 specs。

## 1. 先试 CLI（它会自动同步 delta→openspec/specs/ + 更新 INDEX + 校验）
openspec archive {change_name} -y 2>&1 | tail -30
- 输出 "archived as ..." 且无 Validation error → 归档+同步完成，跳到第 3 节核对。
- "incomplete task(s)" 警告（-y 会继续）→ 可接受（复选框已对账）。
- **Validation error / Aborted**（常见：某 MODIFIED 的主 spec 是中文遗留格式——
  用 `### 需求:`/`#### 场景:`、缺 `## Purpose`/`## Requirements`——CLI 重建它时校验失败）
  → 走第 2 节 fallback。

## 2. fallback：--skip-specs + 手动同步
openspec archive {change_name} --skip-specs -y   # 只移归档+更新 active，不碰主 specs

然后手动同步主 specs（**按代码实况写，不要照搬 delta**）：
a. 读归档里的 delta：openspec/changes/archive/{date}-{change_name}/specs/<cap>/spec.md
b. **对每条 ADDED/MODIFIED 需求，用 Grep/Read 核对实际代码**（迁移/SP/Go/前端/测试）
   确认它描述的就是当前代码真正做的；若 delta 与代码不符（审查可能改过方案），
   **以代码为准改写**该需求后再同步。
c. 新能力（proposal New Capabilities）：openspec/specs/<cap>/spec.md 新建，
   套 `# <cap> Specification` + `## Purpose`（一段目的）+ `## Requirements`，放需求。
d. 改的能力：把（已按代码核对的）需求**追加**到主 spec 的 `## Requirements` 末尾，
   **匹配该主 spec 自身风格**：英文结构用 `### Requirement:`/`#### Scenario:`；
   中文遗留用 `### 需求:`/`#### 场景:`（别往遗留中文 spec 塞英文关键字）。
e. INDEX 登记：openspec/INDEX.md「按主题分组（specs/）」对应组加一行新能力。
f. 校验：对每个动过的 spec 跑 `openspec validate <cap> --type spec`。
   - 你新建/追加导致的 valid→invalid **必须修**。
   - 遗留中文主 spec **本就 invalid**（无 Purpose/中文关键字）= pre-existing，
     可 `git stash` 你的改动验证「改前就红」，**别为它返工整篇**。

## 坑（手动同步必看）
`### Requirement:` 标题**正下方第一段必须含 SHALL/MUST**；`> 来源:`/`> 注记` 这类
blockquote 放在 MUST 段**之前**会让 validate 报 `must contain SHALL or MUST`。注记放
MUST 段之后或行内。

## 3. 报告（≤12 行）
- 归档路径（openspec/changes/archive/{date}-{change_name}/）
- 走的是 happy path 还是 --skip-specs fallback
- 同步了哪些主 specs（新建 / 追加 / INDEX），每个 validate 结果
- 与 delta 不符、按代码改写过的需求（如有）
- 遗留 pre-existing invalid spec（如有，注明非本次引入）
先 Read 再 Edit/Write。**不要 git add/commit**（提交在下一步统一做）。
```

子代理报告里若出现「核心 delta 与代码严重不符无法判定」之类 BLOCKED，停止并交回用户。

---

## 第四步：Git Commit（弱档子 agent）

> 用弱档：本步纯机械（git add + 从 diff 生成 message），独立子代理无干扰、失败也就重生成 message。verify 用强档、archive 用中档是因它们是门禁/判断步（凭本步性质，非"统一"）。详见「模型选择」。

派发 Agent（model: 按规则根 model-tiers.md 弱档；config.yaml model-tiers 段可覆盖），prompt：

```
你是 Git 助手。工作目录：{项目根目录}。
任务：暂存并提交本次 OpenSpec change（{change_name}）收尾相关的文件。

步骤：
1. git status
2. git add openspec/   （归档目录 + INDEX + 同步的主 specs 全部 openspec/ 变更）
3. git add -u          （已追踪实现文件的修改；不暂存无关新增未追踪文件）
4. git diff --staged --name-only（输出供核对）
5. git diff --staged（读摘要，生成 message）
6. Conventional Commits 中文 message：type(scope): 动词开头描述
7. git commit —— message 结尾追加两行（项目约定）：
     Generated with Claude Code
     Claude-Session: {当前 session URL，从系统提示取}
   用多个 -m 实现，**勿用 \ 续行 + heredoc**（本机 shell 会损坏 message）
8. 输出 commit hash + message

禁止 git push。
```

> 若实现期已逐 commit 提交（subagent-driven），本步只提交**归档 + spec 同步 + INDEX** 这批收尾变更。

---

## 第五步：Merge 到默认分支（缺省执行，主 session）

**缺省合并**：除非第 0.1 步记下 `{merge_intent}=skip`（用户调用时明确不合并），否则前四步成功后**直接 ff 合并**，不再逐次询问。

- `{merge_intent}=skip` → 跳过本步，摘要里标「⏭ 按调用意图跳过 merge（分支留待手动处理）」。**不自动 push**。
- `{merge_intent}=merge`（默认）→ **先做 untracked 硬检查，再执行 checkout+merge**（单向 git，留主 session 可见，不丢子代理）：

**merge 前 untracked 硬检查**〔spec-review-amendment SR-2，防"未追踪工作经 checkout+ff-merge 存活于磁盘却从未进 base git 历史"〕：
```bash
git -c core.quotePath=false status --porcelain
```
〔impl-review-fix CR-6：`-c core.quotePath=false` 与 ship_gate.py 的 `_GIT_HARDEN` 一致，中文文件名不被 C-quote 转义，halt 清单可读〕
筛出 `??`（untracked）开头的行。**判据机械化**〔impl-review-fix CR-4：原"排除既有 debris"要模型主观分类，违反"机械活交脚本、模型只做判断"——改为纯机械 halt〕：**任何 `??` untracked 存在即 halt+报告**，把"是本 change 新产物、还是仓库既有 debris"的分诊交给 halt 处的**人工**（人比对清单一眼可判），脚本/skill 侧不做该分类。**边界声明**〔impl-review-fix CR-5：`git status --porcelain` 默认不含被 `.gitignore` 忽略的文件——本检查**不覆盖** gitignore 排除的路径；若怀疑某交付物被误 gitignore（该追踪却被 ignore），须另行核查，不在本检查范围〕。
- 存在此类 untracked → **非交互 halt+报告**，停下并列出文件清单，建议「先 `git add` 纳入版本控制并提交，或确认与本 change 无关后再重跑」；复用既有"ff 不可行→停下报告"惯用法，**MUST NOT 用 AskUserQuestion 中途问**、**MUST NOT 静默继续 ff-merge**。
- 无此类 untracked（或人工处理/确认后重入本步）→ 继续：

```bash
git checkout {base_branch}
git merge --ff-only {feat_branch}
```

**合并方式默认 `--ff-only`**（线性历史，符合用户偏好；**别硬编码 `--no-ff`**）。仅当**项目约定明确要保留 merge commit** 才改 `--no-ff -m "merge: {change_name}"`——查项目记忆/约定，无明确约定就 ff。

边界处理：
- **ff 不可行**（`{base_branch}` 已分叉、非快进）→ 不自动改用 merge commit、不强合；停下报告「base 已分叉，需手动 rebase/merge 决策」。
- **冲突** → `git merge --abort`，列冲突文件交用户。
- **不自动 push**（合并后是否推由用户控制；摘要提示「未 push」）。

---

## 第六步：输出最终摘要

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sdflow-done 完成

  Change:  {change_name}
  Verify:  ✅ PASS（+ Minor 缺口 N 项，见 verify-report；每 ✅ 附锚点）
  Hand-off:✅ hand-off.md（done/not-done + 延后项 + 下阶段建议，随归档）
  Archive: openspec/changes/archive/{date}-{change_name}/
  Specs:   ✅ 同步主 specs（新建 / 追加 / INDEX）｜或 ⚠️ --skip-specs 手动同步
  Commit:  {hash} — {message}
  Merge:   ✅ {base_branch} ← {feat_branch}（ff）｜⏭ 按调用意图跳过
  Push:    ⏸ 未 push（用户手动控制）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 设计原则

- **串行门禁**：每步失败即中止；verify FAIL（核心缺口）不归档。
- **model 按本步性质（独立子代理无耦合）**：verify=强档（唯一终门），archive=中档（判断），commit=弱档（机械）；merge 留主 session（单向 git、缺省执行）。
- **归档必同步 spec**：用 `openspec archive` CLI；它做 spec 同步 + INDEX + 校验。手动 `mv` 是错的。
- **中文遗留 spec**：`--skip-specs` + 手动同步（匹配遗留风格、按实况写、修自己引入的 invalid）。
- **复选框对账要诚实**：勾真实完成的，未完成的留 `[ ]` + 说明。
- **默认分支检测**：勿假设 main。
- **merge 缺省执行**（ff-only）；仅当调用时明确 opt-out 才跳过；ff 不可行/冲突则停下交用户；**不自动 push**。
- **verify 必产 `verify-report.md`** 存 change 目录（随归档留档）。
- **verify 防假✅（P3h）**：每条 ✅ 必附机验锚点（测试名/commit/文件:行），无锚点 ✅ 降级 gap；强档 + Do-Not-Trust 冷启（阶段三去人类门后 verify 是唯一终门，禁降档）。见 design §7.3.1 / adr/0001。
- **hand-off.md（P3g）**：verify 之后 / archive 之前产出（done/not-done + 延后项 + 下阶段建议），随归档留档，作异步人类再入口 + 下个 change 种子；**不直接搬运 verify 的 ✅**（复核锚点存在性）。
- **issues sweep 子步（§2.1，D3/D4）**〔impl-review-fix：本条订正——旧版描述手写 4 步循环，§2.1 已改用 sweep 一键封装〕：写 hand-off 正文前先跑 `issues.py sweep --change {本change}` 一键调用（内部固化 scan 两池 → 逐项 triage → batch add → reindex 全部子步，不再手写 4 步循环）；**显式传 `--change {本change}`**（不靠 `detect_change` 猜，D4）；只建 **1 个批次、key=本 change 名**（Q2 保守，禁跨 change 合并）；内部末尾跑 `reindex`（D3）刷新 INDEX + 同步批次状态；只圈 `源==本change` 的未分诊 OPEN 项，孤儿（源=""）不归本 sweep，交独立清理流程兜底；非原子、fail-closed，半途失败直接重跑同一条命令收敛。

## 模型选择（按本步性质，逐步定）

> 档位与缺省见规则根 `model-tiers.md`（经 `~/.sdflow/hack/resolve-workflow.sh` 解析；config.yaml 的 model-tiers 段可覆盖映射）。

**关键前提**：本 skill 步骤**固定**（不是运行时动态路由），且每步**独立子代理**（各自上下文）。所以——
- **混用 model 无干扰**：弱档-commit 与中档-verify 上下文隔离，互不污染；混用没有耦合代价。
- **无运行时误分类**：「误分类风险」是**动态路由**的事（高频循环里运行时按难度挑模型才会挑错）；固定步骤在写 skill 时一次定死，不存在该风险。

因此 model 就是**纯粹的「这一步配不配」**，逐步独立判：

| 步 | 性质 | 档位 | 理由（本步自证） |
|---|---|---|---|
| verify | **唯一终门** + grep 代码判 PASS/FAIL | **强档** | 中档/弱档假 PASS = 放不完整活进归档；门不能省 |
| archive | spec 同步 + 读代码核 delta | **中档** | judgment 活 |
| commit | git add + 从 diff 生成 message | **弱档** | 纯机械；失败也就重生成 message；独立上下文无副作用 |

注 **turn 数 > 单 token 价**：弱档在判断味的步上常多花 2-3× turn、总成本反高 → verify 用强档、archive 用中档不只为质量、也常更省。commit 机械、弱档不会 flail。

> 混用在固定步骤里唯一的**软成本**：分类会**过期**——若日后给某步加复杂逻辑（如 commit 加冲突处理），它不再机械、但 model 还写着弱档。低风险，留注释提醒即可。
>
> 对比 subagent-driven-development 的实现循环（高频、动态、上百任务）：那里「弱档转写实现 + 强档评审」是对的，但它**会**有运行时误分类风险（要靠评审兜底）。**规则随场景变。**

## 附：实战踩坑速记（来自首次执行）

| 坑 | 现象 | 对策 |
|---|---|---|
| 手动归档漏 spec 同步 | 新能力不进 `openspec/specs/` | 用 `openspec archive` CLI |
| 中文遗留主 spec | CLI rebuild 报 `must have Purpose section` → Abort | `--skip-specs` + 手动同步 |
| 复选框 stale | CLI 警告 "23/24 incomplete" | 第 0.3 步先对账勾选 |
| blockquote 在 MUST 前 | validate 报 `must contain SHALL or MUST` | 注记放 MUST 段之后 |
| 照搬旧 delta | spec 与终审后实况不符 | 同步按当前代码真正做的写 |
| 硬编码 main / --no-ff | 仓库是 master、用户偏好 ff | 检测分支 + ff-only |
