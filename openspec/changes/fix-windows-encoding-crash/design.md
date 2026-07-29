## Context

见 [`proposal.md`](./proposal.md) 的 Why/What Changes：Windows(GBK/cp936) 环境下，本仓 Python 脚本 `print()`/`write_text()` 遇到 GBK 编不出的字符（`✅🔴⚠✓` 等）即 `UnicodeEncodeError` 崩溃，命中 `setup.sh` 的四道机械一致性门与 `sdflow-init` 的 `init.py`，且恰好崩在"打印成功消息"那一行，把通过判定误判成假红（`openspec/issues/buglist/2026-07-28-buglist.md` B23）。本机 Windows Git Bash 实测复现，详细证据见 [`decision-memo.md`](./decision-memo.md) C1/C2/C9。

约束：① 每个 skill 是独立分发目录，被 symlink/复制安装到消费者的 `~/.claude/skills/`，脚本之间**不能共享公共 Python 模块**（`decision-memo.md` C4 已用 grep 验证全仓无此类跨 skill import）；② `openspec/workflow/tools/*.py` 是 `sdflow-init/assets/workflow/tools/*.py` 的托管镜像，只能改源（C5）。

## Goals / Non-Goals

**Goals:**
- 消除全部 **28** 个入口脚本在 GBK 环境下因打印 Unicode 字符触发的崩溃。`[spec-review-amendment]`
- 补全 `subprocess text=True`（**15 个调用站点 / 14 个编辑点**）的显式编码，避免解码崩溃；`write_text()` 经复核**当前已全部带 `encoding="utf-8"`（0 处待补）**，本 change 只做核实确认并写进 spec 防回退。`[spec-review-amendment]`
- 新增机械门防止后续新脚本遗漏防护（面治而非点补）。
- 在真实 Windows CI（`windows-latest` + `PYTHONIOENCODING=gbk` 真实子进程）上验证，而非仅靠此前的 mac 模拟。

**Non-Goals:**
- 不做语义级"扫描字符串内容是否含风险字符"的检测器（见 Decisions D1）。
- 不引入跨 skill 共享模块。
- 不处理本仓之外消费该 bundle 的下游项目自身脚本（它们随后续 `sdflow-init update` 自然获得修复）。

## Components（TG-14：新增组件 `hack/check_encoding_hygiene.py`）

新增一个脚本，与既有 `setup.sh` 四道机械门并列、同构接线（独立守卫，不挂在其它门的条件下）：

```
setup.sh
  ├── hack/sync_principles.py            （既有，四条通则漂移）
  ├── hack/gen_workflow_guide.py         （既有，WORKFLOW-GUIDE 单一源）
  ├── hack/check_async_branch_parity.py  （既有，async host 段落一致）
  ├── hack/check_tier_resolution_parity.py（既有，档位解析段落一致）
  └── hack/check_encoding_hygiene.py     （新增，本 change）
        │  扫描目标 glob（见下）下每个含 `if __name__ == "__main__":` 的脚本，
        │  存在性检查三项契约（见下「判据定义」）
        ▼
  目标 glob：hack/**/*.py + sdflow-*/scripts/**/*.py
            + sdflow-init/assets/{hack,hooks,workflow/tools}/**/*.py
            （排除 **/tests/**；排除 openspec/workflow/tools/**——
             它是 sdflow-init/assets/workflow/tools/ 的托管镜像，检查源即覆盖镜像）
```

### 判据定义（`[spec-review-amendment]` · 消除两个未定义自由变量）

🔴 **① 「前几行」这个窗口取消，改为全文匹配。** 初版用「前几行内是否含 `reconfigure(encoding=`」描述判据，
但**四份文档没有任何地方给出数值**，而实测目标脚本的 `import sys` 位置跨度是 **5 行 → 191 行（38 倍）**：
`sdflow-ship/scripts/ship_gate.py:191`（全文 1821 行，被长模块 docstring 顶下去）、
`sdflow-init/assets/hack/outside-voice-job.py:154`、`sdflow-init/assets/hooks/ff0-branch-guard.py:79`、
`hack/check_codex_efficacy_evidence.py:70`。**任何小窗口实现都会把这几个「已正确修复」的文件误判成「仍缺前导」
——本 change 的目标是消除假红，新门却先造一个，且命中的是 ship 门禁本体。**
∴ 判据取**整文件**匹配：存在性检查本就不需要位置约束（位置约束只是凭空多一个未定义的自由变量）。

🔴 **② 排除规则 MUST 锚定仓根，MUST NOT 用任意深度通配。**
`find . -path "*/workflow/tools" -type d` 只命中两条，而**两条共享完全相同的尾段 `workflow/tools`**：
`./openspec/workflow/tools`（要排除的镜像）与 `./sdflow-init/assets/workflow/tools`（**要检查的源**）。
若排除写成 `*/workflow/tools/*` 或 `fnmatch("**/workflow/tools/**", path)`，会**同时命中两条**，
把 6 个源文件（`anchor_lint.py` / `hr_tg_intersect.py` / `lens_metric_emit.py` / `outside_voice_guard.py` /
`review_disposition_check.py` / `trivial_shape.py`）一并排出检查集合 ⇒ 门**静默报告「全部通过」**。
这比 ① 更隐蔽：不是「该报错时没报错」，是**该检查的文件根本没进入检查集合**。
∴ MUST 用 `path.startswith("openspec/workflow/tools/")`（相对仓根）这类锚定判据。

**三项契约**：对每个入口脚本**分别**验证 ① `sys.stdout` 的 `reconfigure` 调用在场、
② `sys.stderr` 的 `reconfigure` 调用在场、③ `errors="replace"` 在场。缺任一项 ⇒ 报告该文件 + 缺的是哪一项。
（判据仍是有界字符串匹配，不是 AST 语义扫描——收窄理由见 `decision-memo.md` D1 的修正段。）

依赖方向：`setup.sh` → 调用 `check_encoding_hygiene.py` → 读取仓内脚本文件（只读，无侧写）。与既有四道门同级并列，互不依赖。

**失败输出契约** `[spec-review-amendment]`：本门失败时 MUST 与三道同侪门同构，给出 `修：` 行——
逐文件列出「路径 + 缺哪一项契约」，并附 4 行模板的规范位置指针（见下 Migration Plan 的模板住所）。

## Decisions

本 change 的决策全文、砍掉的候选、三镜代价与证据锚见 [`decision-memo.md`](./decision-memo.md)（D1–D5、C1–C10）。TG-23（≥2 合理方案：检测机制存在性检查 vs 语义扫描）命中，其 ADR 结构化记录（方案对比 + 理由 + 三镜代价）已在 `decision-memo.md` D1 与"三镜代价"节完整给出，不在此重复。

补充两条实现顺序上的技术选择（不改变已拍板的 D1–D5，属于落地细节）：

- **先实现 `check_encoding_hygiene.py`，用它的失败列表驱动 28 个脚本的注入顺序**（对应 `decision-memo.md` D5）——避免人工枚举遗漏（grill 已发现人工估算 ~19 与实测的偏差；**spec-review 又发现 memo 自己写的 27 也是错的、真值 28**，见 C6 的修正段——这恰好第二次印证了 D5「手工枚举不可靠」）。`[spec-review-amendment]`
- **`check_encoding_hygiene.py` 只有裸调用模式（无 `--apply`）**，仿 `check_async_branch_parity.py` / `check_tier_resolution_parity.py` 的纯验证模式，而非 `sync_principles.py` 的 `--check/--apply` 模式——因为本检查没有单一"canonical 内容"可回填，各脚本的 reconfigure 前导插入点需要实现时逐文件确认语法正确（比如是否已有 `import sys`、shebang 行位置），批量自动写入有破坏语法的风险。

## Risks / Trade-offs

- **[风险] 28 个脚本手工插入前导块，逐文件确认插入点存在出错概率** → **缓解**：`check_encoding_hygiene.py` 是插入后的验证闸门，任何遗漏或格式错误都会被它挡在 CI/`setup.sh` 之外；且插入内容 4 行固定模板，复制粘贴出错概率低。`[spec-review-amendment]`
- 🔴 **[风险] `errors="replace"` 会造静默假等值——本仓已有先例，初版的"不引入新失败模式"表述被自家代码证伪** `[spec-review-amendment]` → **初版表述作废**。`sdflow-ship/scripts/ship_gate.py:460-473` 的 `run_git_bytes` docstring 白纸黑字写着：「MUST NOT 复用 run_git/run_git_rc——那条路径 `text=True` + `errors="replace"` + `.strip()`，四者各自可造假等值：吞首尾空白、吞末尾换行、CRLF↔LF 不可分辨、**非 UTF-8 字节被替换成 U+FFFD 后两版趋同**」——这是**上一个 change**（`fix-design-gate-freshness-proxy`）专门为绕开这个 bug class 新建的函数。行为不是「崩溃 → 局部字符丢失」的纯收益降级，而是**响亮失败 → 静默错误**，正是本仓反假绿哲学要杀的形态。
  → **缓解（Q2 拍板中档）**：对 15 个站点按「输出是否流入等值 / 去重 / 分类判断」分类——
  **流入判定路径的两处** `sdflow-ship/scripts/ship_gate.py` 的 `_git_run`（gate 决策本体）与
  `sdflow-init/assets/workflow/tools/trivial_shape.py:210`（code-review「免除评审」判器，`git diff` 内容分类）
  MUST 在本节写明为何仍沿用 `errors="replace"`：二者的**判定输入均不经过该条解码路径**
  （`ship_gate` 的保真比对走 `run_git_bytes` 的 `text=False` 原始字节；`trivial_shape` 的既有
  `errors="replace"` 是本次改动**之前**就在的，本 change 只补 `encoding=`、不改其容错语义）——
  ∴ 本次**新加** `errors="replace"` 的站点均不在判定路径上。其余站点（取 SHA hex / 分支名，ASCII-safe）一刀切即可。
- 🔴 **[风险] 前导块的 `except Exception: pass` 是 catch-all，触发时原 bug 静默复现且无痕** `[spec-review-amendment]` → 模板第 3 行 `except Exception: pass` 会吞掉一切失败原因（含标准流被替换成无 `reconfigure` 的对象时的 `AttributeError`——已实测 `io.StringIO()` 无该方法、抛 `AttributeError`、确被裸 `except` 捕获）。**这意味着「前导块不生效」与「前导块生效」在外部完全不可区分**，一旦发生就退回修复前行为且无任何信号。 → **缓解**：接受吞异常（不吞则前导块自身成为新的崩溃源，比 bug 本身更糟），但 D 检测器的三项契约检查 + E 的真实子进程验证共同保证「模板在场且真的生效」；本条**作为已知边角显式记录在案**，不再是未记录的盲区。
- **[风险] 前导块落在模块顶层裸作用域（非 `__main__` 守卫内），`import` 即产生进程级副作用** `[spec-review-amendment]` → 五道门脚本均被各自的 pytest 直接 `import`（`hack/tests/test_sync_principles.py:15` 等），届时**一次 import 就会改掉整个 pytest session 的真实 stdout/stderr**，且不会被"既有套件全绿"抓到（Linux CI 上不报错）。**已实证降级**：本机 pytest 9.1.1 实测 `--capture=fd/sys/tee-sys` 三种模式下 `EncodedFile` / `CaptureIO` / 真实 `TextIOWrapper` **三者都支持 `.reconfigure()`**，未复现破坏。 → **缓解**：**这是有意为之**（放进 `__main__` 守卫内则被当库 import 的路径不受保护，而 lib 模块正是靠调用方的进程级 reconfigure 覆盖，见 `decision-memo.md` C6）；本条显式记录该 blast radius，避免后续 reviewer 重新发现一遍。
- **[风险] CI 新增的 `PYTHONIOENCODING=gbk` 真实子进程验证步骤增加 CI 时长** → **缓解**：只在 `windows-recorder-smoke.yml` 一个已存在的 Windows-only job 里追加步骤，不新建 job，增量时长有限（真跑 `setup.sh` 本身已是现有步骤的量级）。
- **[风险] `check_encoding_hygiene.py` 本身是新脚本，如果它自己打印 emoji 又没加前导，会自相矛盾地成为下一个假红源** → **缓解**：实现时该脚本自身从第一行起就带 reconfigure 前导（构造即满足自己的规则），CI 步骤里让它自检自身文件（目标 glob 覆盖 `hack/**`，包含它自己）。

## Migration Plan

- 无运行时部署步骤——本 change 只改仓内 Python 脚本与 CI 配置，通过正常 PR 合并生效。
- 🔴 **交付面比初版描述的宽** `[spec-review-amendment]`：受影响的 `scripts/**` 分属 ~10 个 skill，它们**不**走 `sdflow-init update`，而是走 `setup.sh:60-77` 的 `rm -rf` + `cp -r`（Windows）/ symlink（Unix）。∴ 交付路径实为**三条**：① `hack/**` 随仓库；② 各 skill 的 `scripts/**` 随 `setup.sh` 重跑（Unix symlink 即时生效，Windows 须重跑）；③ `sdflow-init/assets/workflow/tools/**` → 消费仓的 `openspec/workflow/tools/` 走 `sdflow-init update`。**只提第 ③ 条会让人低估「用户何时真正拿到修复」**。
- **4 行模板的永久住所** `[spec-review-amendment]`：模板目前只写在 `tasks.md` 里，而 change 归档后 tasks 不再是活文档 ⇒ 下一个写入口脚本的人无处可查。本 change MUST 在 `CLAUDE.md` 的「修改本仓库的注意」段补一条（新增入口脚本须带 4 行前导，否则第五道机械门会拦），并由该门的失败输出指向它。
- **回滚**：`git revert` 本 change 的合并提交，或运行 checkout `git checkout <上一已知良好 commit>` + 重跑 `setup.sh`（与本仓既有回滚约定一致，见 `CLAUDE.md`"dev/runtime checkout 纪律"）。

## Compliance

N/A——本仓无外部合规/隐私/安全审计要求适用于本次改动（纯工具链内部编码健壮性修复，无用户数据、无网络暴露面变化，见 `proposal.md` Compliance）。
