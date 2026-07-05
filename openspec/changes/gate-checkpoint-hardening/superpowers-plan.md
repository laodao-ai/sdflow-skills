# gate-checkpoint-hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development。逐任务 fresh implementer + review。步用 `- [x]` 追踪。

**Goal:** 把 6 个 gate/checkpoint 硬化项（spec-review 定稿：Q1 熔断锚行集合判据+无状态 helper · Q2 merge 缩简版）落进 workflow bundle 权威源 + 自制 skill + 3 处测试加固。

**Architecture:** 纯规则/文案/注释/模板编辑 + `ship_gate.py` 加一个无状态锚行比较 helper + `sdflow-done` merge untracked 检查；改的是**本仓权威源**（`sdflow-*/`、`sdflow-init/assets/`），symlink 即时生效、hack 脚本需 setup.sh。

**Tech Stack:** Python(pytest, ship_gate.py)、Markdown(SKILL/workflow/spec)、bash(setup.sh)。

## Global Constraints

- 每任务 commit 步 MUST：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task<N>-<slug>`（命名空间格式，gate 只认本 change 标签）。
- 改的是**本仓源**（不是 `~/.claude/skills/` 运行副本——它们 symlink 回本仓；但 `sdflow-init/assets/hack/checkpoint-commit.sh` 改后须 setup.sh）。
- Edit 前 MUST 先 Read 目标文件。机器锚 `<!-- ship-gate: X -->` 一律独占裸行。
- 测试文件路径：`sdflow-ship/tests/`（本仓）。改 `scripts/` 必跑对应 `tests/`。
- 语言中文。

---

### Task 1: checkpoint 标签格式单源（T36 / SR-4 / SR-5）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（TAG_RE 附近加 canonical-shape 头注释 + SR-4 checklist 注释）
- Modify: `sdflow-init/assets/workflow/workflow.md`（规则源一处 + 格式串样例，标"权威见 TAG_RE"）
- Modify: `sdflow-ship/SKILL.md`（派发指令改引用式、删完整格式串复述）
- Modify: `sdflow-ship/tests/test_workflow_authority.py`（SR-5：改断言）

- [x] 1.1 Read `sdflow-ship/scripts/ship_gate.py` TAG_RE 行（grep `TAG_RE = re.compile`），其上方加注释：规范形状 `checkpoint(<change-slug>:task<N>-<slug>)`、"格式权威在此 TAG_RE；test_producer_parser_contract 钉 producer↔parser 一致；checkpoint-commit.sh format-agnostic 非源"；**SR-4**：追一行 checklist「改此正则前先 grep workflow.md 格式串同步」
- [x] 1.2 Read `sdflow-init/assets/workflow/workflow.md`，grep checkpoint 派发指令处：保留规则一处（含格式串样例 + "权威见 ship_gate.py TAG_RE"）
- [x] 1.3 Read `sdflow-ship/SKILL.md`，把 RUN_PLAN 派发句里的完整格式串复述改为"格式见 workflow.md 规则/TAG_RE 契约"引用式（保留 ship 特有派发语义）
- [x] 1.4 **SR-5**：Read `sdflow-ship/tests/test_workflow_authority.py`，找断言"SKILL 含 `<change>:task<N>-<slug>`"处（约 line 23），改为断言 workflow.md 含格式源/规则、sdflow-ship SKILL 含引用且**不含**完整格式串
- [x] 1.5 跑 `pytest sdflow-ship/tests/test_workflow_authority.py -v`，确认改后绿
- [x] 1.6 grep 门：`grep -rn "checkpoint(<change" sdflow-ship/SKILL.md` 应无完整格式串复述（只剩引用/workflow.md 一处）
- [x] 1.7 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task1-tag-format-single-source`

### Task 2: ship-gate 锚模板独占裸行（T43 / SR-6 / SR-10）

**Files:**
- Modify: `sdflow-spec-review/SKILL.md:102`（design-approved 锚去反引号）
- Modify: `sdflow-code-review/SKILL.md:149-150`（pass/blocked 尾注移出，各配各注）
- Modify: `sdflow-ship/tests/test_anchor_contract.py`（SR-6：逐行 strip 断言）

- [x] 2.1 Read `sdflow-spec-review/SKILL.md` 第 102 行附近，把 `` `<!-- ship-gate: design-approved -->` ``（带反引号）改为独占裸行 `<!-- ship-gate: design-approved -->`
- [x] 2.2 Read `sdflow-code-review/SKILL.md` 第 149-150 行，把 `<!-- ship-gate: code-review=pass -->   （建议进 /sdflow-done）` / `...=blocked --> （存在未解 blocker）` 的**同行尾注移到锚行之外**——**SR-10**：pass/blocked 各自语义注释放锚行**上方或下方另起行**，锚本身独占裸行；MUST NOT 合并成共享单脚注
- [x] 2.3 Read `sdflow-done/SKILL.md:80-81`，确认 verify 锚已独占裸行（记录，不改）
- [x] 2.4 **SR-6**：Read `sdflow-ship/tests/test_anchor_contract.py`，把子串断言 `anchor in text` 改为**逐行** `any(line.strip()==anchor for line in text.splitlines())` + 断言该锚行无反引号、无同行尾注
- [x] 2.5 跑 `pytest sdflow-ship/tests/test_anchor_contract.py -v`，确认绿（改前它会因新断言对坏模板失败→改模板后绿）
- [x] 2.6 grep 门：`grep -n "ship-gate:" sdflow-spec-review/SKILL.md sdflow-code-review/SKILL.md` 各锚 strip 后应等值锚字面（无反引号/尾注）
- [x] 2.7 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task2-anchor-bare-line`

### Task 3: 新鲜度 committed-only + merge untracked 硬检查（T35 / SR-2 缩简版）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（新鲜度注释定夺）
- Modify: `sdflow-ship/SKILL.md`（收尾软提示）
- Modify: `sdflow-done/SKILL.md`（第五步 merge 前 untracked 硬检查）

- [x] 3.1 Read `sdflow-ship/scripts/ship_gate.py` 行 64-66 T33 停置注释，更新为定夺：committed-only 正式化 + 理由（无逻辑变更）
- [x] 3.2 Read `sdflow-ship/SKILL.md`，收尾/resume 段加非门禁软提示：工作树有未提交非-openspec 改动时告知"gate 判定不含它们"（明确不改退出码）
- [x] 3.3 Read `sdflow-done/SKILL.md` 第五步（merge），在 `git checkout {base}` 之前加硬检查：`git status --porcelain` 筛**本 change 分支内新产 untracked**（`??` 且非仓库既有 debris）→ 存在则 **halt+报告非交互停下上抛人工**（复用既有"ff 不可行→停下报告"惯用法），**MUST NOT AskUserQuestion**；判据写清（排除既有 debris）
- [x] 3.4 跑 `pytest sdflow-ship/tests/` 全绿（无逻辑改动应零回归）
- [x] 3.5 grep 门：`grep -n "AskUserQuestion" sdflow-done/SKILL.md` 的 merge 步附近无新增交互提问
- [x] 3.6 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task3-freshness-and-untracked-guard`

### Task 4: 熔断锚行集合判据 + 无状态 helper（T26 / SR-1）

**Files:**
- Modify: `sdflow-ship/scripts/ship_gate.py`（加无状态锚行比较 helper + 子命令/函数）
- Create/Modify: `sdflow-ship/tests/test_gate_breaker.py`（新回归测试）
- Modify: `sdflow-ship/SKILL.md`（熔断条款改判据）

**Interfaces:**
- Produces: `anchor_set(text) -> frozenset[str]`（复用/包装 `_line_scoped_hits`/`anchors_in` 语义，返回该报告的结论锚集）；`breaker_no_progress(before_set, after_set) -> bool`（纯函数，无副作用）

- [x] 4.1 Read `sdflow-ship/scripts/ship_gate.py` 的 `_line_scoped_hits`/`anchors_in`。写失败测试 `sdflow-ship/tests/test_gate_breaker.py::test_no_progress_when_anchor_set_unchanged`：两次相同锚集 → `breaker_no_progress` 返 True（无进展）
- [x] 4.2 跑该测试确认 FAIL（函数未定义）
- [x] 4.3 在 `ship_gate.py` 实现 `anchor_set(text)`（复用 `_line_scoped_hits` 对已知锚字面集）+ `breaker_no_progress(before, after)`（`return before == after`，纯函数不落地）
- [x] 4.4 跑测试确认 PASS
- [x] 4.5 加测试：`test_progress_when_new_anchor_added`（after 多一个结论锚 → 返 False）+ `test_failsafe_missing_snapshot`（before=None → 保守返 True 无进展）；实现 fail-safe 分支使其绿
- [x] 4.6 Read `sdflow-ship/SKILL.md` 熔断条款（grep "熔断"），改判据表述：该步 ship-gate 锚行集合无净变化即判无进展熔断；**HEAD 移动/mtime 变化 MUST NOT 作免疫信号**；fail-safe 快照缺失保守判无进展；仅有锚报告步（STEP_IN_PROGRESS/RERUN_STALE）适用；比较经无状态 helper
- [x] 4.7 跑 `pytest sdflow-ship/tests/test_gate_breaker.py -v` 全绿
- [x] 4.8 grep 门：`grep -n "HEAD 未移\|mtime" sdflow-ship/SKILL.md` 熔断条款无残留旧 HEAD/mtime 判据
- [x] 4.9 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task4-breaker-anchor-set`

### Task 5: spec delta 对码核验 + 校验

**Files:**
- Verify: `openspec/changes/gate-checkpoint-hardening/specs/spec-workflow/spec.md`（3 ADDED + 1 MODIFIED）

- [x] 5.1 逐条核 4 需求与 Task 1-4 实现一致（格式源 TAG_RE / 锚裸行 / committed-only+untracked / 锚集判据）；确认 MODIFIED 块的 `<change-slug>` 与代码/文案一致
- [x] 5.2 跑 `openspec validate gate-checkpoint-hardening`，通过
- [x] 5.3 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task5-spec-verify`

### Task 6: 部署 + 全量验证

- [ ] 6.1 开发 checkout 跑 `bash setup.sh`（改 assets/workflow + assets/hack 才让全局 canonical 生效）
- [ ] 6.2 `~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)"` 确认 canonical 指向本 checkout；抽查 workflow.md 改动经全局生效
- [ ] 6.3 全仓 `pytest` 零回归
- [ ] 6.4 commit：`bash ~/.sdflow/hack/checkpoint-commit.sh gate-checkpoint-hardening:task6-deploy-verify`
