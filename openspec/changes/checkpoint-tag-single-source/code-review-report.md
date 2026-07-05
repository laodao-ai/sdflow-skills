# code-review 报告 — checkpoint-tag-single-source

<!-- sdflow:step1-broad-review v1 mode="native" -->

## 命中范围

- **栈/清单**：Python 测试 + skills 元仓——`domains/`（backend-go/backend/embedded*/frontend）无一命中；按通用 `code-review-base.md` CR-01~09 审（CR-09 测试质量最相关）。
- **代码审面**：唯一代码/测试改动 = `sdflow-ship/tests/test_producer_parser_contract.py`（DIFF_BASE=7a413f5..HEAD 中仅此为代码；其余为四件套 + 审报告 + issues 记录 doc 产物）。
- **gstack/review（Step1 原生，scope-drift + 完成度）**：**无 scope 漂移**——`git diff --stat` 实现三 commit 仅动测试文件 + openspec 文档产物，`ship_gate.py`/`workflow.md`/`SKILL.md`/既有测试断言零触碰（历史镜 + 三镜 diff 一致）。**完成度**：delta spec Scenario ↔ tasks ↔ 实现一一对应，仓级 350 pytest 全绿。
- **镜**：领域镜（CR 清单）×1 + 对抗镜 ×1 + 历史镜 ×1 + code outside-voice（codex）。

<!-- sdflow:hr-tg v1 hit="none" evidence="纯测试新增,零运行时行为/数据路径/安全面,不满足HR-TG(运行期爆炸/数据损坏/安全泄漏)入选判据" -->

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="codex" reason_code="" findings="1" truncated="false" -->

## Findings（置信 ≥80）

- **[中] CV-1 测试覆盖 | test_producer_parser_contract.py:27-41（原正例）| code-voice(codex)**：producer→parser 正例仅测 `demo:task1-slug`（`demo` 无 dash、单数字号），未覆盖正则命名空间 `[a-z0-9-]*` 的**内部 dash** 与**多位数号**——恰是本 change 真实标签形态 `checkpoint-tag-single-source:task<N>-`。命名空间若被收紧成 `[a-z0-9]+` 或号位截断，`demo` 正例仍绿而真实 kebab 命名空间/多位号静默失守（对称于 DF1 负例侧缺口）。置信 90 | **已修 [impl-review-fix]**：加 `test_kebab_namespace_multidigit_captures`（`checkpoint-tag-single-source:task12-slug` → 断言 group `("checkpoint-tag-single-source","12")`）。同时闭 DF7/T40。
- **[低] CR-09 测试隔离 | test_producer_parser_contract.py:12-14（原 sys.path 块）| 领域镜 + 对抗镜（两镜共识）**：模块级 `sys.path.insert(0,…)` + 裸名 `import ship_gate` 是本套件 12 个测试文件中**唯一**内存态 import gate 的文件（其余全走 subprocess 黑盒 CLI）；该插入 collection 时执行、永久污染整个 pytest session 的 `sys.path`/`sys.modules`，无作用域回收。当前 scripts/ 仅一份 ship_gate.py 故休眠无害，但仓根 pytest 发现全部 skill，未来任一 skill 出现同名 `scripts/ship_gate.py`（"ship"命名通用）会按 import 顺序静默复用错模块。置信 85 | **已修 [impl-review-fix]**：改 `importlib.util.spec_from_file_location` 按文件路径显式加载，不碰 sys.path（保 D4 意图「import TAG_RE 无副作用」，仅硬化机制——见「裁决/机制精化」）。
- **[低] DF6 可移植 | test_producer_parser_contract.py:19（原 f-{step}.txt）| code-voice(codex) 复提**：`run_producer` 造变更用 `f"f-{step}.txt"`，`step` 含冒号时（`demo:task1-slug`）产 NTFS 非法文件名，Windows CI 误红。置信 85 | **已修 [impl-review-fix]**：改固定文件名 `change.txt`（文件名与契约无关，只需 porcelain 非空）。闭 DF6/T39。

## 已裁掉（反静默压制，可审计）

- **X1（对抗镜 F2，gpgsign/HOME 隔离，<80 滤除·一行带过）**：`conftest.py:8-19` 的 `repo` fixture 未隔离 `HOME`/`GIT_CONFIG_GLOBAL`/gpgsign，理论上某机全局 `commit.gpgsign=true` 且无 GPG agent 时 `git commit` 子进程可能挂起。**裁掉理由**：非本 PR 引入的面——`conftest.commit_all` 早已直接 `git commit`、被既有 `test_gate_freshness.py` 等大量测试复用；属既有 conftest 基建、非本改动行；本机 `git config --global --list` 无 gpgsign 未触发。若要焊属 conftest 级独立改进，不在本 change 范围（对抗镜自身也标"非新爆点、仅完整披露"）。
- **假绿路径核实（对抗镜攻击面 2/4/5）**：无变更静默跳过→`git log -1` 无 HEAD 会 `check=True` loud fail（非读旧 subject 假绿）；`tmp_path` function-scoped 自动隔离清理、无 race；硬编码正例断言是设计意图的真锚（非脆性缺陷）——均核实无问题。
- **历史镜**：测试文件全新无 revert；TAG_RE 首入 6e91a2b（T32），本 change 协同演进无反复；直指 T32 + buglist 根因，非重蹈旧坑。

## 裁决 / 机制精化

- **F-C（sys.path→importlib）机制精化决策**：D4 原文选「sys.path 注入」，其**意图** = "import 到 TAG_RE 且无副作用"。两镜共识指出 sys.path 注入本身是全局不可逆副作用 + 未来同名模块静默遮蔽的休眠隐患。改用 importlib 按路径加载**达成同一意图、更安全**，属实现机制精化而非设计语义变更。**不改 design.md D4 文本**（避免设计门锚后触碰四件套）——由本报告 + 代码内 `[impl-review-fix]` 注释留痕，archive 步 delta 对码核验时可据实同步。
- **DF6/DF7 由 defer 提前落地**：设计门时 DF6/DF7 记 todolist「择机」；code review（code-voice CV-1 + 复提）判"择机=现在"（改测试便宜、且属核心交付覆盖），自动修后 T39/T40 回写 DONE。

## 修复 / defer 台账

- **自动修 3 项 [impl-review-fix]**：CV-1（kebab-命名空间 + 多位数号正例）· sys.path→importlib（消全局污染）· 文件名冒号→固定名。
- **自动选推荐 0 项**（无 ≥2 方案分歧需 T10 复核）。
- **defer 0 项**（所有站得住的 finding 均已修；X1 为既有 conftest 面、非本 change）。
- **voice 分桶（M4 采纳率数据源）**：codex 采纳 1 / 裁掉 0 / defer 0 · claude-fallback 0（本轮 code-voice codex exec 成功、无回落）。

## 结论

☑ **建议进 /sdflow-done**（verify → hand-off → archive → commit → merge）。残差已闭：DF6/DF7 修复回写 DONE、sys.path 隐患修掉；无 defer 未决项。仓级 350 pytest 全绿。

<!-- ship-gate: code-review=pass -->
