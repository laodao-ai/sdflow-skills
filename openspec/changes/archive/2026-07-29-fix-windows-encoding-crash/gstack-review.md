<!-- sdflow:step1-broad-review v1 mode="native" -->

# gstack autoplan 广审报告 · fix-windows-encoding-crash

> **native 声明的侧信道佐证**：本轮经 Skill 机制原生加载 `autoplan/SKILL.md` 进主 session 执行，
> 其 preamble 实跑（`BRANCH: feat/fix-windows-encoding-crash` / `REPO_MODE: solo` / `SLUG: laodao-ai-sdflow-skills`
> 由 `gstack-repo-mode` / `gstack-slug` 真实返回），Phase 0.5 的 `gstack-codex-probe` 实源、
> `_gstack_codex_auth_probe` 实跑返回 ok，Phase 1/3/3.5 的 Claude 子代理经 Agent 工具实派并返回
> （agentId `ac61b547b1b27dd2d` / `aa2d77f2e91920d1f` / `a5070a51b59b042c4`）。非转述模拟。

## 执行盘面（如实登记，含降级）

| 相位 | 状态 | 说明 |
|---|---|---|
| Phase 0 意图/范围检测 | ✅ 跑 | UI 镜命中数 1（阈值 2）⇒ **无 UI scope**；DX scope 命中（本仓即开发者工具） |
| Phase 0.5 codex preflight | ✅ 跑 | binary 在、auth ok、版本 0.145.0 |
| Phase 1 CEO 镜 | ⚠️ `[subagent-only]` | Claude 子代理跑成；**codex 声不可用** |
| Phase 2 Design 镜 | ⏭ 跳过 | 无 UI scope（autoplan 自身跳过条件） |
| Phase 3 Eng 镜 | ⚠️ `[subagent-only]` | 同上 |
| Phase 3.5 DX 镜 | ⚠️ `[subagent-only]` | 同上 |

🔴 **codex 声不可用的实测原因（非"没跑"，是"跑了但拿不到证据"）**：本机 codex 的 Windows
sandbox helper 二进制**实际缺失** —— `orchestrator_helper_launch_failed: helper=codex-windows-sandbox-setup.exe,
error=program not found`（`~/.codex/.sandbox/sandbox.2026-07-28.log` 两次实录）。
`~/AppData/Local/Programs/OpenAI/Codex/bin/` 下只有 `codex.exe` 与 `codex-code-mode-host.exe`，
`find` 全目录无任何 `*sandbox*` 命中。read-only sandbox 下 codex **一个仓内文件都读不到**，
它据此拒绝产出（原话：「I won't invent file:line evidence」）——**该拒绝是正确行为，不是失败**。
未用 `--sandbox danger-full-access` 绕过：那等于在无人授权下把仓库写权限交给外部模型。
⇒ 四相位一律记 `[subagent-only]`，**MUST NOT 记为"双声一致"**。

**顺序偏离声明**：autoplan 要求各相位严格串行。本轮 Eng 与 DX 两个子代理**并行**派出。
依据：二者按 autoplan 自身规定「NO prior-phase context — subagent must be truly independent」，
不消费前相位产物；而串行的唯一实质消费方（codex 声的 prompt 要注入前相位摘要）本轮已不可用
⇒ 串行约束在本轮结构性落空。主 session 侧的综合仍按 CEO → Eng → DX 顺序做。

## 三镜 findings（原样收录，未裁剪）

### CEO 镜（strategy · Claude 子代理 · 已实跑本机复现）

子代理在本机实跑复现了核心前提：`sys.stdout.encoding=gbk` / `locale.getpreferredencoding()=cp936`；
`python3 -c "print('test ✅ done')"` → `UnicodeEncodeError: 'gbk' codec can't encode character '✅'`（exit 1）；
加 4 行前导后 → exit 0 正常输出。**C1/C2 经第三方独立复现成立。**

- **CEO-1〔high〕新门无常驻 pytest，四个兄弟门都有** — `hack/tests/` 下 `test_sync_principles.py`
  / `test_async_branch_parity.py` / `test_tier_resolution_parity.py` / `test_codex_efficacy_evidence.py`
  齐全；`tasks.md` 7.3 的负向用例是"建临时脚本→验证→**删掉**"，跑完零留存。
- **CEO-2〔medium-high〕"存在性检查"若按裸文本/正则实现，会被注释骗过** — 本仓注释文化
  routinely 在真调用上方复述代码形状（实例：`sdflow_issues_core/__init__.py:1055` 注释里就写着
  `text=True 须显式 encoding="utf-8"`）。且这正撞 CLAUDE.md 基准⑤「让那个工具自己回答」——
  Python 自带 `ast` 就是这里的"那个工具"。**建议改 `ast.parse()` 找真 Call 节点。**
- **CEO-3〔medium〕P2（subprocess/write_text）只做点补、无常驻门，与本 change 自己的"面治非点补"逻辑不一致** —
  `spec.md` Requirement 4 无条件声明了契约，`tasks.md` §3 却无任何门任务，覆盖图里标的是"现有 pytest 间接覆盖"。
- **CEO-4〔low-medium〕CI 真跑只覆盖 ~28 个脚本中的 2 个** — 6.2/6.3 只跑 setup.sh（5 个 hack 门）+ init.py，
  其余 ~22 个脚本在 CI 里只过静态存在性检查，从未在 GBK 下真执行过。而 D2 自己论证的正是"必须真子进程跑"。
- **CEO-5〔low〕两个 headline 数字过不了算术/grep 复核** — 见下方主 session 复核，已确认并细化。

### Eng 镜（architecture · Claude 子代理 · 读了 setup.sh / 两个 workflow / ~10 个真脚本）

- **ENG-1〔high〕`setup.sh` 恒退 0 ⇒ CI 6.2 的"断言退出码 0"对回归零信号** — 见下方主 session 复核（已确认，但口径需修正）。
- **ENG-2〔high〕"前几行"未定义，且对本仓真实文件形态必然误判** — 实测
  `hack/check_codex_efficacy_evidence.py` 的 `import sys` 在**第 70 行**，
  `sdflow-ship/scripts/ship_gate.py` 的在**第 191 行**（前面都是长篇设计理由注释块，本仓主流风格）。
  按 tasks.md 2.1「`import sys` 之后」插入 ⇒ 前导落在第 195 行左右。任何有意义的"前 N 行"窗口
  （10/20/30）都会对本仓自己的文件假阴。**建议直接全文件扫，仍是有界字符串检索、不违基准⑤。**
- **ENG-3〔high〕tasks.md 手工枚举的 27 条清单在动工前就已经错了** — `sdflow-issues/scripts/migrate_legacy.py:383`
  有 `__main__`、在声明的 glob 内、不在 `tests/` 也不在镜像目录，但**不在 §2.9 的列举里**。
  这正是 D5 写来防的失效模式，产物却仍把静态清单钉进 tasks.md。
- **ENG-4〔high〕新门无自动化回归测试**（与 CEO-1 同一条，两镜独立命中）。
- **ENG-5〔medium〕前导写在裸模块作用域、未置于 `__main__` 守卫内** — 实测 ~15 个测试文件把这些入口脚本
  当库直接 import（`sdflow-issues/tests/test_buglist.py:15` `import buglist as buglist_mod`、
  `sdflow-architecture/tests/test_sad_lint.py:3` 等）⇒ `reconfigure()` 会在**仅仅 import** 时对真实
  `sys.stdout/stderr` 产生进程级副作用。今天基本无害（UTF-8 下 no-op；pytest 每测重绑另一对象），
  但它是"库 import 触发全局状态突变"的味道。**建议挪进 `if __name__ == "__main__":`。**
- **ENG-6〔medium〕CI 6.3 的 `--root` 留白** — "临时 checkout 或已铺设的测试目录"未定；
  `update --root .` 会自改 CI 工作区且除退出码外无成功判据。
- **ENG-7〔low〕`windows-latest` 对这条检查未必必要** — `PYTHONIOENCODING=gbk` 强制的是 CPython 自己的
  codec 机制，与 OS locale 无关，同样断言在 ubuntu 上等价成立。不是缺陷，但设计把 Windows-only 说成
  承重，名不副实。
- **ENG-8〔low〕沿袭了 setup.sh 既有的 `command -v python3` 不一致** — 只有 `python` 没有 `python3` 的机器上
  五道门一起静默不跑且无告警。非本 change 引入，照抄既有约定，不建议在此阻塞。

**Eng 镜复核为"不是问题"的项**（同样收录）：Python 版本下限 3.9 ≥ reconfigure 的 3.7（C3 成立）；
`write_text()` = 2 处（C8 成立）；仓内无既有 stdout 编码 workaround（`TextIOWrapper`/`codecs.getwriter`），
无双补丁风险；`issues.py` 自调 `buglist.py`/`todolist.py` 的父子两侧被本 change 对称修好；
声明边界（只管 subprocess + write_text）没漏掉同样脆弱的 read 路径。

### DX 镜（developer experience · Claude 子代理）

- **DX-1〔medium〕新门的失败输出契约完全未规定，而三个兄弟门都有** —
  `hack/sync_principles.py:180-183` 打漂移路径 + `修：python3 hack/sync_principles.py --apply`；
  `check_async_branch_parity.py:120-136`、`check_tier_resolution_parity.py:113-129` 同形；
  `setup.sh:526-555` 每道门在调用点**再**给一次 `修：` 提示。`spec.md:31-38` 只规定了退出码，
  `tasks.md:5.1` 的 setup.sh 接线也漏了 `修：` 那行。而 tasks.md 1.1 说的"仿 `check_async_branch_parity.py` 模式"，
  在 `design.md:49` 里被明确释义为**CLI 模式**（纯验证 vs `--check/--apply`）而非消息格式 ⇒ 实现者无义务复刻 `修：`。
- **DX-2〔medium〕那 4 行模板没有常驻落点，只活在 tasks.md 里，而 tasks.md 会被归档** —
  `grep -n "reconfigure" CLAUDE.md README.md` 零命中；`CLAUDE.md:303`「修改本仓库的注意」那节
  （贡献者加脚本时唯一会扫的清单）只字未提前导与第五道门。对照本仓自己对同类"必须逐字复制"内容的做法：
  四条通则的真相源常驻 `sdflow-init/assets/hack/skill-principles.md` 并被 CLAUDE.md 引用。
- **DX-3〔medium-high〕新门无常驻测试**（与 CEO-1/ENG-4 同一条，**三镜独立命中**）。
- **DX-4〔medium〕`design.md` 断言"errors=replace 不引入新的失败模式"，被本仓自己的在案结论证伪** —
  `sdflow-ship/scripts/ship_gate.py:437-441`（`run_git_bytes` 的 docstring，来自
  `fix-design-gate-freshness-proxy`/`harden-gate-git-layer`）白纸黑字写着：
  「MUST NOT 复用 run_git/run_git_rc——那条路径 text=True + errors="replace" + .strip()，
  四者各自可造假等值：……非 UTF-8 字节被替换成 U+FFFD 后两版趋同。」
  即 `errors="replace"` **确实**引入一种新失败模式：静默把两串不同字节判成相等——
  对门禁/比较逻辑尤其危险（正是本仓反假绿哲学要防的）。本仓既有约定是「取值展示可以，精确比较不行」，
  而本 change 的 16 站点一刀切没按这条区分做审计。具体可疑站点：`sdflow-issues/scripts/issues.py:1109`
  的 `json.loads(proc.stdout)` 后 `it["id"]` 又拿去当下一条命令的 `--id` 实参。
- **DX-5〔low〕Migration Plan 少说了下游实际拿到的面** — 文里只说下游经 `sdflow-init update`/`sdflow-upgrade`
  拿到修好的 `hack/` 与 `openspec/workflow/tools/` 镜像，但本次实际改的是约 10 个 skill 的 `scripts/**`，
  它们经的是另一条路：`setup.sh:60-77` 的 Windows 路径每次 `rm -rf` + `cp -r` **整个 skill 目录**。
  机制本身是通的（子代理已验），只是文字把到达面说窄了。

## 主 session 对上述 findings 的机械复核（含三条修正 + 一条新发现）

> 通则①：落笔前先证伪。以下每条我亲自跑过命令，结论与镜子不一致处一律以实测为准。

**✅ 证实 · 入口脚本 = 28 不是 27**
```
$ find hack sdflow-*/scripts sdflow-init/assets/{hack,hooks,workflow/tools} -name '*.py' \
    -not -path '*/tests/*' | xargs grep -l '__main__' | wc -l
28
$ ... | grep -c migrate_legacy
1
```
ENG-3 / CEO-5 成立。`migrate_legacy.py` 确在 glob 内、确不在 tasks.md §2.9 列举里。

**✅ 证实 · `setup.sh` 无任何 `exit` 语句，且末句是那道 `if ! …; then echo …; fi`**
```
$ grep -n '^\s*exit ' setup.sh      → 无输出
$ tail -20 setup.sh                 → 末块 = check_tier_resolution_parity 的 if 守卫
```
bash 语义下「条件为假且无 else 的 `if`」返回 0，条件为真时返回 `echo` 的 0 ⇒ **`bash setup.sh` 恒退 0**。

🔧 **修正 ENG-1 的口径（镜子说过头了）**：tasks.md 6.2 的完整原文是「断言退出码 0 **且输出不含
`UnicodeEncodeError`**」。**后半句是有效信号**——真崩了 traceback 会进输出、grep 抓得到。
∴ 准确说法是：6.2 的**退出码那一半是恒真的废断言**（五道门全报漂移 + 全崩，它照样绿），
**输出 grep 那一半对本 bug 有效**。**MUST NOT 说 6.2 整体零信号。** 真正的缺口在下一条。

🔧 **修正 ENG-1/CEO-1 隐含的「每个兄弟门都有 CI 步」（半错）**：实测 `mechanical-gates.yml`
只给了**两道**门独立 CI 步——`Gate — async 调度段两处字节等值`（`python hack/check_async_branch_parity.py`）
与 `Gate — 四条通则托管块与真相源一致`（`python hack/sync_principles.py --check`）。
`gen_workflow_guide.py --check` 与 `check_tier_resolution_parity.py` **没有**独立 CI 步。
⇒ "为新门补一条 CI 步"仍是对的建议（且新门是纯静态检查、不需要 Windows，属最便宜的一类），
但它是**补齐一个本就只落实了一半的约定**，不是"唯一的例外"。

**✅ 证实 · `windows-recorder-smoke.yml` 现在根本不跑 `setup.sh`** — 全文件唯一实质步骤是
`py -m pytest -q sdflow-issues/tests/test_task2_windows_local_fs_smoke.py -W error`。
⇒ 6.2 要新增的是**该 job 里第一次出现 bash**。`windows-latest` 的 `run:` 默认 shell 是 pwsh，
**跑 `bash setup.sh` 必须显式 `shell: bash`**，plan 未提。这是一条会让 6.2 直接跑不起来的落地缺口。

🔴 **新发现 · MAIN-1〔high · 高置信〕tasks.md 3.1 给 `ship_gate.py` 指错了修复位置，照做会 TypeError**
```
$ grep -n '_git_run' sdflow-ship/scripts/ship_gate.py
304:def _git_run(root, args, text):        ← 三个位置参数，没有 **kwargs
334:    r = _git_run(root, args, text=True)
341:    r = _git_run(root, args, text=True)
472:    r = _git_run(root, args, text=False)
```
`_git_run` 内部自己拼 kwargs：`if text: kwargs["text"]=True; kwargs["errors"]="replace"`——
**已有 `errors="replace"`，缺的只是 `encoding`**。而 tasks.md 3.1 写的是「`ship_gate.py` ×2」，
指向 334/341 两个**调用点**。在调用点加 `encoding="utf-8"` ⇒ `_git_run() got an unexpected
keyword argument 'encoding'` **TypeError**，且 `ship_gate` 是 `/sdflow-ship` 的 pre-flight 门，
崩了直接卡住阶段三。**正解是改 `_git_run` 内部那一处**（一行，同时惠及 `run_git`/`run_git_rc`，
且天然不碰 `text=False` 的 `run_git_bytes` ⇒ DX-4 担心的比较路径不受影响）。

**🔧 修正 · subprocess 站点数三方不一致，且三个数都不对**
实测（排除 `tests/`、排除 `openspec/` 镜像、排除 2 处纯注释、排除 3 处已带 `encoding=`）：
真实需改的 `subprocess.run` **调用点 = 14**（devenv_scaffold ×2、roadmap_writeback_draft、impl_route、
init.py、issues.py ×4、retro_report、outside-voice-job:357、ff0-branch-guard、trivial_shape、
**ship_gate 的 `_git_run` ×1**）。
而 tasks.md **标称 16**、其**自己的列举只有 15 项**、其中 ship_gate 的 ×2 还是错位的。
已确认排除项：`migrate_legacy.py:321` 已带 `encoding="utf-8"`（C7 说法成立）、
`sdflow_issues_core/__init__.py:1057` 已带、`outside-voice-job.py:755` 已带。

## 双声一致性表（如实降级）

```
CEO DUAL VOICES — CONSENSUS TABLE:
  Dimension                              Claude   Codex   Consensus
  1. 前提是否成立?                        ✅实测复现  N/A    N/A（单声）
  2. 是否在解对的问题?                     ✅是      N/A    N/A（单声）
  3. scope 标定是否正确?                   ✅是      N/A    N/A（单声）
  4. 备选是否充分探索?                     ⚠️ast 未列 N/A    N/A（单声）
  5. 竞品/市场风险?                        N/A(内部工具) N/A  N/A
  6. 6 个月轨迹是否稳健?                    ⚠️见下    N/A    N/A（单声）
── codex 声不可用 ⇒ 全表 N/A，MUST NOT 记 CONFIRMED ──
```

Eng / DX 两表同理，一律 `[subagent-only]`，不落 CONFIRMED。
**跨相位主题（2+ 相位独立命中 = 高置信信号）**：
- **「新门自己没有测试」被 CEO / Eng / DX 三镜各自独立命中** —— 本轮最强信号。
- **「防再犯这一层有洞」**（CEO-1/2/3 + ENG-1/2 + DX-1/2/3）—— 六个 finding 指向同一处：
  这个 change 的 P0 止血是扎实的，**薄的是它自己声称的 P1「防再犯」**。

## 6 个月后悔场景（CEO 镜结论，主 session 采信）

最可能的后悔**不是**"修复没生效"，而是**"我们建来防复发的那道门，其实没防住复发"**：
(a) 它自己的逻辑无常驻测试保护、(b) 它可能被一行注释骗过、(c) 它的孪生失败模式
（subprocess/write_text）根本没有门。这比原 bug 更贵，因为它会给出"这类 bug 已被机械杜绝"的
虚假安全感——而本仓 CLAUDE.md 的整套哲学正是反假绿。

## 自动决策（登记进 spec-review-report.md 决策区，不在此拍板）

| # | 决策 | 分类 | 原则 | 理由 |
|---|---|---|---|---|
| A1 | codex 声不可用 ⇒ 记 `[subagent-only]`，不用 `danger-full-access` 绕过 | Mechanical | P6/如实降级 | 绕过 = 无授权给外部模型写权限；且假装双声 = 假绿 |
| A2 | Eng/DX 子代理并行派出 | Mechanical | P3/P6 | 二者按规定无前相位 context，串行的唯一实质消费方（codex）已不可用 |
| A3 | 不把 autoplan 的 restore-point 注释 prepend 进四件套 | Mechanical | P5 | 那会改动正被评审的产物本身 |
| A4 | autoplan 的 premise 人类门不弹窗 | Mechanical | sdflow G2/C5 | 阶段二唯一人类门 = 设计门过报告；前提已被子代理实测复现，无待确认项 |

## 收敛

autoplan 广审判定：**P0 止血层扎实（前提经第三方实测复现），P1「防再犯」层有实质缺口**。
findings 全部移交 Step3 合并池；本文件不做拍板。
