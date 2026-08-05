# Task 6 实现记录：实现验证（收尾）

范围：`tasks.md` §6 的 6.2 / 6.3 / 6.7（聚合套件证据 + 两道机械门）。依据 `tickets.md` Task 6 与
`impl-reports/task6-brief.md`。

**本票豁免 red-before-green**（不写产品代码，验收物是证据）；主证据锚 = 本文件 + 下方三元组；
**不依赖本票产生 commit**（本 change 全程不改任何 `.py`，聚合套件本身无产品代码回归可修）。

---

## 聚合套件发现契约（Q6：MUST NOT 解析构建文件，命令来源优先级②）

`openspec/config.yaml` 顶层实测**无 `test-suites` 键**（① 不适用）。走 ②：依仓内既有约定判定，
判定依据（均已真跑/真查，非凭记忆）：

- **无根级 `Makefile`、无 `package.json`**（`find . -iname Makefile` / `-iname package.json`
  排除 `.git`/`.claude/worktrees`/`openspec/changes`/`openspec/roadmaps` 后均零命中）。
- **CI 唯一测试步骤** `.github/workflows/mechanical-gates.yml` 的 `Full test suite` job 就是
  `python -m pytest -q -rs`——与单元层命令同一条，CI 侧不存在独立的「integration」/「e2e」job。
- 另一 workflow `.github/workflows/windows-recorder-smoke.yml` 是 **Windows-only** 冒烟
  （`chcp.com 936`、cp936 编码专属步骤），按脚本路径过滤触发（含 `sdflow-init/assets/**`——
  本 change 因改了 `config.template.yaml` 会命中该过滤器，push 后 CI 会自动跑它），但它
  **不是面向任意 change 的通用聚合层**，且本机 Darwin 环境无法本地复现其 Windows 专属步骤
  （`chcp.com` 不存在于 macOS）——判「未覆盖（本地）」，不用无法本地验证的 CI 结果冒充本地证据。
- `tasks.md` §6（6.1–6.9）通篇只提到 pytest + `sync_principles.py --check` + `openspec validate`
  三件事，从未提及 integration/e2e 层，与上述判定一致。
- `CLAUDE.md`「常用命令」明文：单元层 = `/usr/bin/python3 -m pytest`（裸 `pytest` 不存在、默认
  `python3`〔`~/.local/bin`〕未装 pytest，本机实测确认）。

**判定结论**：本仓只有 unit 层，integration / e2e 均记「未覆盖（本仓无此层）」。

---

## 三层证据

| 层 | 命令原文 | 退出码 | SHA |
|---|---|---:|---|
| unit | `/usr/bin/python3 -m pytest -q -rs`（与 CI `Full test suite` 步骤同一条命令，全仓根跑） | 1（非 0；**非新增回归**，见下「baseline 失败核实」——3 条失败中 1 条已知 baseline + 2 条环境态 flaky，均已逐条核实为非本 change 引入） | `379de3405a07fc7b23a16bb7a7282e2cf0982b6d` |
| integration | — | 未覆盖 | 判定依据：本仓无 `Makefile`/`package.json`，CI 无独立 integration job，`tasks.md` §6 未提及此层（见上「发现契约」节） |
| e2e | — | 未覆盖 | 判定依据：同上；唯一候选 `windows-recorder-smoke.yml` 是 Windows-only 冒烟，本机 macOS 无法本地真跑其专属步骤（`chcp.com`），且按路径过滤触发、非通用聚合层 |

全仓跑结果：`3 failed, 2448 passed, 10 skipped in 416.41s (0:06:56)`（原始日志：
`/private/tmp/claude-501/-Users-cheneyzhao-Documents-04-sdflow-skills/2d511850-2629-44e1-9418-f571c01236b1/scratchpad/full-pytest-run.log`，
本机临时目录，不随仓库提交）。

---

## baseline 失败逐条核实（判据：相对 merge-base 无新增失败，非「全仓绿」〔SR-18〕）

merge-base = `f464e9bff970b291a5fe1aa5a983720ba696b5c0`（`git merge-base main HEAD`）。

### ① `hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`

**`tasks.md` 6.2 已登记的唯一已知 baseline 失败。**

核实方式：`git checkout --detach f464e9bff970b291a5fe1aa5a983720ba696b5c0`（主工作树内临时 detach，
跑完立即 `git checkout feat/refactor-roadmap-internalize-deps` 还原，全程 `git status --short` 确认
无残留），单独跑该用例：

```
FAILED hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent
assert '### Requirement: SA-14 四入口选择规则' in authoring   # grep 0 命中
```

**结论**：merge-base 上确实红，断言内容与 `tasks.md` 6.2 描述一致。`openspec/specs/spec-authoring/spec.md`
与该测试文件在 `git diff f464e9b..HEAD` 中均无改动（`git diff --stat` 零输出）——本 change 完全未触碰
这两个文件，与本 change 无关，**登记准确，非漏记**。

### ② `hack/tests/test_subprocess_encoding_contract.py::test_text_mode_subprocesses_declare_utf8_and_replace`（编排层通知的「Task 2/3 独立复现的第 2 条」）

**独立核实结论：与编排层通知的预期不同——这条不是稳定锚在 merge-base 的红测，是环境态 flaky，本轮实测未在全仓跑中失败。**

核实过程（三次独立复现，未只信前两票自述）：

1. `git worktree add --detach <临时目录> f464e9bff970b291a5fe1aa5a983720ba696b5c0`（全新隔离 worktree，
   不含本机 `.claude/worktrees/`）→ 该用例 **FAILED**，但失败原因是 `assert sites >= 200`（
   `189 >= 200` 为假，即扫描到的**候选站点数不足**），而不是「发现了缺 encoding/errors 的站点」——
   `misses` 列表为空，即所有被扫到的站点本身都合规。
2. 在**主工作树**（含本机真实 `.claude/worktrees/`，当前有 3 个并行 agent worktree：
   `agent-a3f534f3bee37f6fe` / `agent-abab7c217e1d4f32e` / `agent-acf1f578ab22ed715`）内
   `git checkout --detach` 到同一 merge-base，跑同一用例 → **PASSED**（4 passed）。
3. 跑毕还原到 `feat/refactor-roadmap-internalize-deps` 后，在 HEAD（`379de34`）单独重跑
   → 仍 **PASSED**；本票发起的全仓跑（见上表）中该用例同样不在 3 条失败之列。

**根因**：`hack/tests/test_subprocess_encoding_contract.py:65` 的 `_python_files()` 只排除
`{".git", ".worktrees", "openspec"}`，**漏排 `.claude`**——本机 `.claude/worktrees/` 下有 3 个
并行 agent worktree 的完整仓副本（`find .claude/worktrees -name '*.py' | wc -l` = 387 个 `.py`
文件），会被一并扫描进 `sites` 计数。`git ls-files "*.py"` 在 merge-base 与 HEAD 均为 129
（本 change 不改任何 `.py`，该计数完全相同）——**扫描站点数是否 ≥200 完全取决于本机当时是否有
`.claude/worktrees/`，与 checkout 到哪个 commit 无关**（同一 merge-base，隔离 worktree 里 189
< 200 红，主工作树里（含本机 worktrees）200+ 绿）。这是测试脚本自身排除清单的缺陷（环境耦合），
不是一个可稳定锚定在某个 git commit 上的「先于本分支存在」的红。

**结论**：本次实际全仓跑（HEAD 主锚，含本机真实环境）该用例**通过**，不计入失败清单；
`tasks.md` 6.2 未登记它是准确的（它本来就不是一个稳定态）。

### ③ 两条未在 `tasks.md` 6.2 / brief 中出现的新失败（本票全仓跑独立发现，主动披露）

`hack/tests/test_outside_voice_child_lifecycle.py::test_runner_subtree_dies_when_parent_is_signalled`
的两个参数化用例：

- `[system:/bin/bash-Signals.SIGINT-INT]`
- `[system:/bin/bash-Signals.SIGHUP-HUP]`

均在全仓跑中因 `communicate(timeout=60)` 超时而 `FAILED`（`subprocess.TimeoutExpired`）。

核实方式：单独重跑同一测试函数的全部 3 个参数化用例（含未失败的 SIGTERM）：

```
sdflow-init/tests/test_outside_voice_child_lifecycle.py::test_runner_subtree_dies_when_parent_is_signalled[system:/bin/bash-Signals.SIGTERM-TERM] PASSED
sdflow-init/tests/test_outside_voice_child_lifecycle.py::test_runner_subtree_dies_when_parent_is_signalled[system:/bin/bash-Signals.SIGINT-INT] PASSED
sdflow-init/tests/test_outside_voice_child_lifecycle.py::test_runner_subtree_dies_when_parent_is_signalled[system:/bin/bash-Signals.SIGHUP-HUP] PASSED
3 passed in 2.22s
```

**判定为 flaky（复跑一次即绿），非本 change 回归**，依据：

- 本 change 全程 `git diff --stat` 零 `.py` 改动，未触碰 `sdflow-init/assets/hack/outside-voice.sh`
  或该测试文件本身，逻辑上不可能是本 change 引入的行为回归。
- 该测试函数自身 docstring 显式记录此类用例「复现率环境敏感」（同文件另一条用例
  `test_runner_subtree_survives_...` 的 skip 理由更直接写明「15 次高频混合信号风暴本轮一次都没
  复现（复现率环境敏感，见本用例 docstring 的 105 次跨方法/跨代码版本实测记录）」）——这是一类
  已知的、依赖真实信号时序与系统调度的用例。
- 全仓跑执行期间本机 `git worktree list` 显示 **3 个并行 agent worktree**同时活跃
  （`agent-a3f534f3bee37f6fe` / `agent-abab7c217e1d4f32e` / `agent-acf1f578ab22ed715`），存在真实
  的并发资源竞争，与「60 秒信号回收超时」这类实时性敏感断言的失败模式吻合。
- 隔离重跑（无额外并发负载）2.22 秒内 3/3 全绿，与「60 秒都没等到」形成鲜明对比，佐证是负载态而非
  逻辑态失败。

**MUST NOT** 与「本 change 引入的回归」混同——四类失败分诊中这条落在「flaky」桶，记录并放行。

### baseline 清单差异小结（编排层要求的显式对照）

`tasks.md` 6.2 只登记 1 条（①，SA-14）。编排层通知另有 Task2/Task3 独立复现的「第 2 条」
（指向 `test_subprocess_encoding_contract.py`）——本票独立复核后发现：**它不是一个可稳定归因于
merge-base 的红**，而是本机 `.claude/worktrees/` 是否存在导致的扫描口径 flaky（②，根因已定位到
测试脚本排除清单缺陷，非本 change 相关）；本票全仓跑额外发现两条**此前从未被登记过**的、独立可
复跑归零的 flaky 失败（③）。**三条均非本 change 引入的回归**：① 是稳定登记在案的既有红、②③ 是
环境态 flaky（②的成因甚至比「红」更细——它此刻实测是绿的）。

---

## 另外两道机械门

| 门 | 命令 | 退出码 |
|---|---|---:|
| 6.3 principles 一致性 | `python3 hack/sync_principles.py --check` | 0（`[sync_principles] ✅ 20 个投放面全部与真相源一致`） |
| 6.7 change 结构合法性 | `openspec validate refactor-roadmap-internalize-deps --strict --type change` | 0（`Change 'refactor-roadmap-internalize-deps' is valid`） |

两道门均在 HEAD `379de3405a07fc7b23a16bb7a7282e2cf0982b6d` 上跑出。

---

## 证据锚定 SHA

**所有判「通过」的证据行锚同一个最终 SHA**：`379de3405a07fc7b23a16bb7a7282e2cf0982b6d`
（`git rev-parse HEAD`——这是本报告写入前、全部测试与机械门实际执行时的 SHA；本票不写产品代码，
豁免 red-before-green，未产生任何产品代码 commit，聚合套件证据锚定于测试执行当时的 SHA，
非本报告文件自身提交后的 SHA）。

---

## Hand-off（本票 MUST NOT 执行，仅声明承接）

- **`tasks.md` 6.9**（archive 后对提升进 `openspec/specs/roadmap-planning/spec.md` 的结果重跑
  6.1 词表扫描 + 逐 Requirement 与重写后的 SKILL.md 对码）：依赖 archive 步产出主 spec 的最终内容，
  **由 `sdflow-done` 的 archive 步承接**，本票不执行。
- **`tasks.md` 4.5**（合并后在运行 checkout `~/.skills/sdflow-skills` 重跑 `setup.sh` / 触发
  `/sdflow-upgrade` 还原）：依赖本 change 先合并到运行 checkout 追踪的分支，**由合并后的 hand-off
  步承接**，本票不执行。

---

## 结论

- 单元层：相对 merge-base **无新增失败**——3 条失败逐条核实完毕（① 已知 baseline 稳定复现于
  merge-base；② 编排层预期的「第 2 条」经独立核实实为环境态 flaky 且本次实测为绿；③ 两条新发现的
  独立 flaky，隔离复跑 3/3 绿）。
- integration / e2e：本仓无此层，均已附判定依据，未 fail-closed 罢工。
- `sync_principles.py --check`、`openspec validate --strict` 两道机械门均绿。
- 6.9 / 4.5 两项 hand-off 已声明承接方，本票未越权执行。
- 本票 MUST NOT 勾 `tickets.md` 复选框、MUST NOT 打 `checkpoint(...)` 标签、MUST NOT 改
  `proposal.md` / `design.md` / `tasks.md` / `specs/`——均未触碰，`tasks.md` 6.2 登记差异仅记录于
  本报告，交编排层裁决是否需要回填登记。
