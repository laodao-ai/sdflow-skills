# spec-review report — fix-windows-encoding-crash

阶段二设计评审（`/sdflow-spec-review`）。审的盘面 = `09bbb55` 之后的四件套 + `decision-memo.md`。

<!-- sdflow:step1-broad-review v1 mode="native" -->
<!-- sdflow:hr-tg v1 hit="none" declared="TG-14,TG-18,TG-19,TG-23" evidence="TG-14 新增组件(check_encoding_hygiene.py)/TG-18 测试覆盖图/TG-19 优先级分层/TG-23 ≥2 方案(存在性检查 vs 语义扫描)，四者均不在 HR-TG 子集内" -->
<!-- sdflow:declared-sites v1 declared="design-voice" -->
<!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain,adversarial,grounding" -->
<!-- sdflow:outside-voice v1 site="design-voice" host="claude" runner="codex" reason_code="ok" findings="4" -->

---

## 一、本轮实况（先说降级与代价，再说结论）

| 层 | 实况 |
|---|---|
| Step 1 广审 | ✅ native 原生执行，落盘 `gstack-review.md`，已提交 `09bbb55` |
| 领域镜 ×1（base-checklist） | ✅ 独立完成 |
| 对抗镜 ×2 | ✅ 独立完成 —— **但这是第二次派发**，第一次被会话限额杀死、零产出 |
| 接地镜 ×1 | ✅ 独立完成 —— 同上，第二次派发 |
| outside-voice（design-voice） | ✅ 跨模型 `codex/gpt-5.6-sol`，`reason_code=ok`，4 条 —— **第三次派发**才成功 |

**⚠️ 中断与恢复如实记录**：本轮 Step 2 被 `session limit` 打断，三镜死亡、零产出；交接单
`spec-review-handoff.md` 当时按「如实降级」把 `mirrors=` 记为仅 `domain`。限额恢复后**重新派发**了这三镜，
它们**真的独立跑完了**，故本报告的 `mirrors="domain,adversarial,grounding"` 与 roster 是实打实的，非补记。
**第一次派发的三镜没有产生任何 finding，也没有在任何统计里被计入。**

**🔴 一个自指的实证**：本轮跑 `lens_metric_emit.py` 时，它的中文输出在本机 shell 里**当场变成乱码**
（`采纳` → `����`），带 `PYTHONIOENCODING=utf-8` 重跑才正常。**评审过程自己踩了正在评审的这个 bug**
——这条不进 findings（不是四件套的缺陷），但它是 proposal 问题陈述真实性的一次现场佐证。

**镜间冲突裁决 ×1**：对抗镜 B 把 decision-memo **C6 判为「站得住」**（抽查 3 个 lib 文件确认无 `__main__`），
而接地镜是**穷举**测量、判 C6 错（见 M1）。**以接地镜为准**——抽查 3 个文件不能证伪一个计数断言，
B 的核验方法与结论范围不匹配。此项已回写：B 的该条「已核验通过」**不成立**。

---

## 二、决策登记区

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [自动决策] A1  autoplan 内 codex voice 不可用（本机缺 codex-windows-sandbox-  │
│                setup.exe）⇒ 该阶段标 [subagent-only]；本 skill 已回落自跑     │
│                design-voice 补齐跨模型层                                      │
│ [自动决策] A2  autoplan 的 Eng / DX 视角并行派发                              │
│ [自动决策] A3  不前置 restore-point                                           │
│ [自动决策] A4  autoplan 的 premise gate 未弹窗（G2 适配，连同本区一并拍板）    │
│ [自动决策] A5  接地镜档位由建议的弱档提到中档（本 change 断言密度几乎全是可机 │
│                械证伪的数目，且三处独立计数曾互相打架）——已生效，事后登记     │
│ [自动决策] A6  outside-voice 复用守卫对 gstack-review.md 判 section-not-found │
│                ⇒ 依协议回落自跑 design-voice                                  │
│                                                                              │
│ [需拍板]  Q1  D1 的「无界语法面」论证是否成立？（M9 · 跨模型镜正面挑战已拍板  │
│               决策，本条是 TENSION）                                          │
│ [需拍板]  Q2  M8 的 errors="replace" 分类处理，做到哪一档？                   │
│ [需拍板]  Q3  M3 揭示 write_text 那一半 Requirement 已 100% 满足 —— spec 的   │
│               该 Requirement 与 tasks §3.2 怎么处置？                         │
│ [需拍板]  Q4  M6 揭示 16 处 subprocess 修复零 CI 覆盖 —— 补覆盖 vs 认边角？   │
│                                                                              │
│ [已裁掉]  X1  VOICE-2「裸调 reconfigure 会变成启动期 AttributeError」（崩溃   │
│               场景部分）                                                      │
│ [已裁掉]  X2  ENG-7「windows-latest 并非真正承重」                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Q1〔TENSION · 跨模型镜 vs 已拍板 D1〕D1 的「无界语法面」论证是否成立？

- **D1 的立场**：检测器选存在性检查、砍掉 AST 语义扫描，理由是「语法面无界」（援引 CLAUDE.md 基准⑤）。
- **跨模型镜（VOICE-3）的立场**：D1 砍掉的候选（「风险字符是否流入 `print()`」）确实无界，**这一半没错**；
  但**被检查的对象**（一个固定 4 行的前导块）是**有限、可机械验证的结构**。
  ∴ 「无界 ⇒ 只能做裸字符串存在性检查」是**把两件事混为一谈**：D1 用「扫描 print 数据流无界」
  论证了「连前导块自身的三项契约（stdout / stderr / `errors="replace"`）也不必验证」。
  按基准⑤自己的措辞——**「有界 ⇒ 可手写解析」**——前导块这一面恰恰落在「有界」那一侧。
- **主审判定**：**VOICE-3 的区分成立**。D1 的结论（不做语义扫描）没错，**它的论证覆盖面过宽了**。
  且这一漏洞被 CEO-2 从另一角度独立命中（裸文本匹配会被注释骗过），两条指向同一处。
- **推荐**：**保留 D1 的结论，收窄 D1 的论证，并把检测器从「查一个子串」提到「查三项契约」**
  （分别验 `sys.stdout` / `sys.stderr` 两处调用 + `errors="replace"` 参数）。
  这**不是**回到被砍掉的 AST 语义扫描——它仍是有界匹配，只是从 1 个断言变成 3 个。
- **三面后果**：**系统镜** 检测器复杂度从「一个 `in` 判断」升到「三个」，无新依赖、可回退；
  **用户镜** 无可感知变化（门的输出多一行说明缺哪一项）；**开发循环镜** 实现成本 +~20 行 + 对应测试，
  换来「门真的守住了它声称守的契约」。**主次**：系统镜代价极小，开发循环镜收益直接兑现 M5 要补的那条测试 ⇒ **值得做**。
- **备选**：维持现状（只查子串）+ 在 decision-memo 明写「本门不保证前导块内容正确，靠人 review」
  ——代价是 M13（catch-all 静默失效）在门这一层也没有任何拦截。

### Q2 M8 的 `errors="replace"` 分类处理做到哪一档？

- 本仓**上一个 change** 专门为绕开「`text=True + errors="replace"` 造假等值」新建了 `run_git_bytes`
  （`ship_gate.py:460-473` 的 docstring 白纸黑字写着这个 bug class），而 `design.md` 声称
  「`errors=replace` 不引入新失败模式」时**没有引用这个先例**。
- **推荐（中档）**：对 15 个站点做一次「输出是否流入等值 / 去重 / 分类判断」的分类，
  只对**流入判定路径**的站点（`ship_gate.py` 的 `_git_run`、`trivial_shape.py:210`）在 design.md 写明为何仍沿用；
  其余（取 SHA / 分支名，ASCII-safe）一刀切 `errors="replace"` 即可。
- **三面后果**：**系统镜** 无结构改动，只是文档 + 两处标注；**用户镜** 无；
  **开发循环镜** 多一次 15 站点的分类过目（~30 分钟）。**主次**：开发循环镜为主，成本低，
  但它买的是「下一个人不会再把 `run_git_bytes` 的教训重新踩一遍」。
- **备选（低档）**：只在 design.md Risks 加一条「已知 `errors=replace` 可造假等值，本次 15 处经判定
  均不流入等值判断」+ 附判定依据 —— 代价是这个判定没有机械守，将来新增站点会漂。
- 🔴 **MUST NOT 选的路**：维持 design.md 现在「不引入新失败模式」的表述——它已被本仓自己的代码证伪。

### Q3 write_text 那一半 Requirement 已 100% 满足，怎么处置？

M3 实测：目标 glob 内**全部** `write_text()` 站点已带 `encoding="utf-8"`，tasks §3.2 的「2 处待补」
是 C8 验证命令（逐行 `grep -v encoding`）看不见跨行参数造成的**假阳性**。

- **推荐**：§3.2 改为「**核实确认**（非新增编辑）」+ 换用能感知多行调用的验证方式；
  **spec 的 Requirement 保留不动**（它约束的是目标态，「现在已满足」不等于「不必写进 spec」——
  没有 spec 就没有机械门守住它不回退）。
- **三面后果**：**系统镜** 零改动；**用户镜** 无；**开发循环镜** 少做一次无谓编辑，多改一条验证命令。
  **主次**：这是纯粹的止损——不改的话实现者会去「修」两个没坏的地方，且可能把已有的 `encoding=` 挪位置。

### Q4 16 处 subprocess 修复零 CI 覆盖，补覆盖还是认边角？

M6（对抗镜 B 追调用图 + 跨模型镜独立命中）：6.2 跑的 `setup.sh` 只调那四道门，**四道门全都不调 subprocess**；
6.3 跑的 `init.py update` 也够不着——`init.py:567` 那处只有 `mode == "config-lint"` 走得到。

- **推荐**：把 6.3 改成走一条**真的会调 `text=True` 站点**的路径，并补一个 `PYTHONIOENCODING=gbk` 下
  跑 `issues.py` / `retro_report.py` / `ship_gate.py` 各一次的 CI 步骤（三者覆盖 15 站点里的 7 个）。
  不追求 15/15。
- **三面后果**：**系统镜** CI 多两三个步骤，无生产代码影响；**用户镜** 无；
  **开发循环镜** CI 时长 +，但换来「这层修复不是纯文本改动」的实证。
  **主次**：按通则④，15/15 覆盖的完美成本过高（要造非 UTF-8 字节夹具 × 15），
  **7/15 + 一个夹具子进程**是「成本大幅降、结果可接受」的次优解。
- **备选**：认边角，在 decision-memo 明写「subprocess 层无 CI 覆盖，靠 review」——
  代价是这 15 处将来任何一处被改坏都不会响。

### X1〔已裁掉〕VOICE-2 的崩溃场景

- **原始发现（跨模型镜，标 high）**：「裸调 `sys.stdout/stderr.reconfigure(...)` 可能把原来的编码崩溃
  替换成启动期 `AttributeError`——测试框架 / IDE / 嵌入式宿主可把标准流替换为 `StringIO` 等不提供
  `reconfigure` 的对象。建议用 `getattr(stream, "reconfigure", None)` 后再调用。」
- **裁掉理由（实跑核验）**：`tasks.md:11-13` 的模版**本身就是** `try: … except Exception: pass`，
  而 `AttributeError ⊂ Exception`。本机实跑确认：`io.StringIO()` 确实没有 `reconfigure`
  （`hasattr → False`），调用抛 `AttributeError`，**且被裸 `except Exception` 捕获**。
  ⇒ 「启动期崩溃」这个场景**不成立**；VOICE-2 建议的 `getattr` 与现模版**等效**。
  对抗镜 A 另在本机 pytest 9.1.1 上实测了 `--capture=fd/sys/tee-sys` 三种模式，
  `EncodedFile` / `CaptureIO` / 真实 `TextIOWrapper` **三者都支持 `.reconfigure()`**，未复现破坏。
- 🔴 **但它的残值已升级、未被丢弃**：VOICE-2 真正指出的东西是「**替换流场景下前导块会静默失效**」
  ——这一半**成立**，已并入 **M13**（catch-all 静默吞掉，原 bug 无痕复现）。裁掉的只是「会崩溃」，不是整条。

### X2〔已裁掉〕ENG-7「`windows-latest` 并非真正承重」

- **原始发现（autoplan-eng，标 low）**：`PYTHONIOENCODING` 与 OS 无关，故 CI 用 `windows-latest`
  跑这个用例并不承重，Linux runner 一样能复现。
- **裁掉理由**：**就 6.2/6.3 的现状而言这话没错**，但跨模型镜 VOICE-4 独立指出：真正的故障面恰恰是
  「**不设** `PYTHONIOENCODING` 时，由 Windows 控制台 / 重定向管道 / locale 决定编码」那条路径
  ——**那条路径只在 Windows 上存在**。采纳 M24（补该用例）之后，`windows-latest` 不但承重，
  而且是那条用例的**必要条件**。⇒ ENG-7 的前提被后续采纳项取消，不再成立。
- **注**：这是「裁掉」而非「降级」，因为若照它行动（把 job 挪去 Linux runner）会**直接封死** M24 的补法。

---

## 三、合并 findings（26 条 · 采纳 24 / 裁掉 2 / defer 0）

> 命中镜集合已标注，供 lens-metric 导出「独立」。置信度为主审裁决后的值。

### 高（7 条）

| # | 问题 | 证据 | 命中镜 | 置信 |
|---|---|---|---|---|
| **M1** | **入口脚本是 28 不是 27**，`sdflow-issues/scripts/migrate_legacy.py:383` 有 `__main__`、在 glob 内、被 §2.9 漏枚举。**且 C6 的算术「27 ENTRY + 5 lib = 32」之所以对得上，正是因为把它误计进了 lib**——实测 lib 只有 4 个（`sad_schema.py` / `devenv_paths.py` / `devenv_schema.py` / `sdflow_issues_core/__init__.py`）。C6 是作为「已验证的承重约束」写死的数字，不是待检测器确认的估算。 | `migrate_legacy.py:383`；穷举 glob 实测 32 = 28 ENTRY + 4 LIB | eng + 接地 | 高 |
| **M2** | **按 `tasks.md` §3.1 字面改 `ship_gate.py` 会 `TypeError`**：`_git_run(root, args, text)`（`:304`）三参定签、无 `**kwargs`，334/341 是它的调用点而非 `subprocess.run` 本体。正解是 `:317-320` 的 `kwargs` 构造里加 `kwargs["encoding"] = "utf-8"`（那里**已有** `errors="replace"`，只缺 `encoding`）——**一处**编辑覆盖两个调用点及未来新增调用方。 | `ship_gate.py:304,317-320,334,341` | eng + 接地 | 高 |
| **M3** | **`write_text` 的「2 处待补」是伪任务**：`check_codex_efficacy_evidence.py:418` 与 `devenv_scaffold.py:59` **都已带** `encoding="utf-8"`（写在下一行，多行调用）。目标 glob 内其余全部 `write_text()` 站点亦然。根因 = C8 的验证命令 `grep -rn "write_text(" \| grep -v encoding` 是**逐行** grep，看不见跨行参数。⇒ 该 Requirement 的这一半**当前已 100% 满足**。 | `check_codex_efficacy_evidence.py:418-420`、`devenv_scaffold.py:59-60`；C8 原命令复现 | 接地（**独立**） | 高 |
| **M4** | **「前几行」窗口未定义 ⇒ 新门自己制造假红**。四份文档都用「前几行」描述判据，无任何数值；而 §2.1 的注入点是「`import sys` 之后」，实测 `import sys` 位置跨度 **5 行 → 191 行（38 倍）**：`ship_gate.py:191`（全文 1821 行，长 docstring 顶下去）、`outside-voice-job.py:154`、`ff0-branch-guard.py:79`、`check_codex_efficacy_evidence.py:70`。若实现取常见小窗口，这些文件**即使被正确修复也会被判「仍缺前导」**——本 change 的目标是消除假红，新门却先造一个，且命中的是 ship 门禁本体。 | 四文件行号实测 | eng + 接地 + 对抗A | 高 |
| **M5** | **新门是五道门里唯一没有常驻 pytest 的**。另外四道**每一道**都有 `hack/tests/test_*.py` 直接 import 模块跑逻辑（`test_sync_principles.py:15` / `test_async_branch_parity.py:24` / `test_tier_resolution_parity.py:22` / `test_workflow_split.py:16` / `test_codex_efficacy_evidence.py:20`）；而 §7.3 给新门安排的是「人工核对一次，**然后删掉临时脚本**」，§1 也没提 `hack/tests/test_encoding_hygiene.py`。这是本 change 新增的**唯一常驻防线**，却是自身验证最弱的一道。 | 五个 test 文件的 import 行 + §7.3 原文 | ceo + eng + dx + 对抗B（**四次独立命中**） | 高 |
| **M6** | **15 处 subprocess 修复点，零处被新增 CI 步骤覆盖**。追调用图：6.2 跑的 `setup.sh` 只调那四道门，而 `sync_principles.py` / `gen_workflow_guide.py` / `check_async_branch_parity.py` / `check_tier_resolution_parity.py` **全都不调 subprocess**（grep 零命中）；6.3 跑的 `init.py update` 也够不着——`init.py:567` 在 `_git_root_or_dot()` 里，只有 `mode == "config-lint"`（`:896-898`）走得到，`run()` 从不调它。**且**跨模型镜补充：即便跑到了，若被调命令不实际输出非 ASCII，漏掉 `encoding=` 照样绿。剩下的「覆盖」只有 7.1 的既有 pytest，而 TG-18 覆盖图**自己**标的就是「间接覆盖」。 | 调用图追踪 + `init.py:567,896-898` | 对抗B + **跨模型镜** + ceo | 高 |
| **M8** | **`errors="replace"` 会造静默假等值，而 design.md 的「不引入新失败模式」被本仓自己的代码证伪**。`ship_gate.py:460-473` 的 `run_git_bytes` docstring 白纸黑字：「MUST NOT 复用 run_git/run_git_rc——那条路径 `text=True + errors="replace" + .strip()`，四者各自可造假等值：吞首尾空白、吞末尾换行、CRLF↔LF 不可分辨、**非 UTF-8 字节被替换成 U+FFFD 后两版趋同**」——这是**上一个 change** 专门为此新建的函数。本次新加 `errors="replace"` 的站点里，`ship_gate.py` 的 `_git_run` 与 `trivial_shape.py:210` 恰在 gate 决策路径本体上。行为从「响亮崩溃」变成「静默替换」，而 design.md 把这当纯收益。 | `ship_gate.py:460-473`、`trivial_shape.py:210` | dx + 对抗A | 高 |

### 中（8 条）

| # | 问题 | 证据 | 命中镜 | 置信 |
|---|---|---|---|---|
| **M7** | **6.2 的「退出码 0」半截空转，但另半截有效；6.3 则整条有效——三者 MUST NOT 一刀切**。`setup.sh` 全文无自身 `exit`，四道门全包在 `if ! python3 …; then echo "⚠️"; fi` 里，`set -e` 对 `if` 条件位置的命令豁免 ⇒ 门的非零码传不到 `setup.sh` 退出码（`mechanical-gates.yml` 注释亦自陈 warn-only）。**⇒「退出码 0」改之前就为真、改之后还是真，零信息量**；但「输出不含 `UnicodeEncodeError`」那半是**真信号**。**而 6.3 不同**：`init.py:868` 的崩溃点没被 try/except 或 `if !` 吞，`UnicodeEncodeError` 真会传到非零退出码 ⇒ 6.3 的退出码断言**是有意义的**。 | `setup.sh` 四道门写法 + `grep exit` 仅命中内嵌 `python3 -c`；`init.py:868` | eng + 接地 + 对抗B | 高 |
| **M9** | **存在性检查守不住它声称守的三项契约**（`sys.stdout` / `sys.stderr` 两处调用 + `errors="replace"`）：只配 stdout、写在注释里、落在不可达代码里，都会假绿。**且 D1 援引的「无界语法面」论证在这一面不成立**——完整前导块是有限可机验结构。详见 **Q1（TENSION）**。 | `decision-memo.md` D1 + 基准⑤原文 | ceo + **跨模型镜** | 高 |
| **M10** | **排除 glob 有歧义，naive 实现会连坐排掉需要检测的源**。`find . -path "*/workflow/tools" -type d` 只命中两条，**两条共享完全相同的尾段 `workflow/tools`**。若排除规则写成未锚定仓根的通配（`*/workflow/tools/*` 或 `fnmatch("**/workflow/tools/**")`），会**同时**排掉 `sdflow-init/assets/workflow/tools/` 的 6 个源文件。后果比 M4 更隐蔽：不是「窗口太小误报」，是**该检查的文件根本没进检查集合**，门静默报「全部通过」。 | `find` 输出两条路径 | 对抗A（**独立**） | 高 |
| **M13** | **裸 `except Exception: pass` 是 catch-all，一旦触发原 bug 静默复现且无痕**。`design.md:51-56` Risks 无「`reconfigure()` 自身抛异常」条目，`spec.md:7-15` 的 Scenario 只覆盖 reconfigure 成功后的路径。BASE-06 禁止 catch-all。**跨模型镜 VOICE-2 的残值并入此条**：替换流（无 `reconfigure` 的对象）场景下前导块会被静默吞掉——这一半成立（崩溃那一半见 X1）。 | `tasks.md:11-13`、`design.md:51-56`、`spec.md:7-15` | 领域 + **跨模型镜** | 中 |
| **M14** | **`spec.md:17-30` Requirement 2 只有成功路径 Scenario**，缺反向用例「真有漂移 + GBK 环境 → 门正确报非零且打印 🔴 时不崩」。而警示符号出现在**失败**消息里的频率高于成功消息 ⇒ 缺的恰是更该测的那半。 | `spec.md:17-30` | 领域（**独立**） | 中 |
| **M16** | **P2（subprocess）是点修，无常驻门守**。M3 已把 write_text 那一半剔出（本就满足），残值 = subprocess 15 处改完之后，没有任何机械门防止新增站点漏加 `encoding=`。 | — | ceo（**独立**） | 中 |
| **M20** | **4 行模版无永久住所**：只写在 `tasks.md` 里，而 change 归档后 tasks 就不再是活文档；`CLAUDE.md:303`「修改本仓库的注意」也没提「新增入口脚本要带前导」。下一个写脚本的人无处可查。 | `CLAUDE.md:303` | dx（**独立**） | 中 |
| **M24** | **`PYTHONIOENCODING=gbk` 的测试模型没覆盖真实故障面**：该变量**主动覆盖**标准流编码，于是测的是「人为强制 GBK 的进程」，而不是 Windows **无该变量**时由控制台 / 重定向管道 / locale 决定编码的路径，还可能掩盖环境继承问题。建议保留该确定性用例，**另加**「移除 `PYTHONIOENCODING` + 设 code page + 输出中文/emoji」的用例，控制台与重定向管道至少各一。 | — | **跨模型镜**（**独立**） | 中 |

### 低（9 条）

| # | 问题 | 证据 | 命中镜 | 置信 |
|---|---|---|---|---|
| **M11** | 前导块在**模块导入时**生效（非 `__main__` 守卫内），`pytest hack/tests/test_sync_principles.py` 会因一次 import 就改掉整个 pytest session 的真实 stdout/stderr，且不会被 7.1 抓到（Linux CI 上不报错）。**已降级**：对抗镜 A 在本机 pytest 9.1.1 实测 `--capture=fd/sys/tee-sys` 三种模式下 `EncodedFile` / `CaptureIO` / `TextIOWrapper` **都支持 `.reconfigure()`**，未复现破坏 ⇒ 残值 = **未记录的 blast radius**，建议在 design.md 明示这是有意为之。 | 五个 test 文件 import 行 + 本机实测 | eng + 对抗B | 中 |
| **M15** | `tasks.md:30` 的 header「16 处」与它自己紧跟的枚举（15 条）**内部算术不一致**。**本轮定标见下方「计数定标」**。 | `tasks.md:30` | 领域 + ceo + 接地 | 高 |
| **M17** | **CI 新增步骤需显式 `shell: bash`**。`windows-latest` 的 `run:` 默认 shell 是 pwsh，不认 `VAR=val cmd` 这种 POSIX 内联环境变量前缀语法（会当程序名报错）；`windows-recorder-smoke.yml` 现有步骤都没有 `shell:` 键，§6.2/6.3 也没提。**fail-loud，不是假绿**，但会白费一个迭代。 | `windows-recorder-smoke.yml` 现状 | 接地 + 对抗B | 中 |
| **M18** | **6.3 的 `--root` 未定义**——「临时 checkout 或指向一个已铺设的测试目录」是两个不同的东西，CI 里指哪个没写。 | `tasks.md:46` | eng（**独立**） | 高 |
| **M19** | **§4.1 的裸命令副作用远超「刷新 tools 镜像」**。`init.py` 的 `run()`（`:807-864`）还会注入/改写 `CLAUDE.md`/`AGENTS.md` 的 `sdflow:*` 托管块、改写 `openspec/INDEX.md`、跑 `handle_config()` 合并 `config.yaml`、合并 `.gitignore`、`ensure_global_hooks()`、`retire_hooks()`、`retire_deploy_files()`——全在 proposal 的 Non-Goals（「不改造脚本的业务逻辑或用户可见的判定规则」）之外。且 `copy_bundle()` docstring（`:202-214`）说非 `--dev` 是给**消费仓**用的，`--dev` 才是源仓 dogfood；`openspec/issues/todolist/2026-07-todolist.md:148`（T15）记着本仓用 `--dev` 跑有 2 条已知假警告的未解决 bug ⇒ 这条命令在本仓到底该不该带 `--dev` 是有历史分歧的，本 change 直接抄了一条。 | `init.py:807-864,202-214`；T15 | 对抗A（**独立**） | 中 |
| **M21** | 新门的**失败输出契约未规定**，而三道同侪门都有 `修：` 提示。 | — | dx（**独立**） | 中 |
| **M22** | **Migration Plan 低估交付面**：~10 个 skill 的 `scripts/**` 走 `setup.sh:60-77` 的 `rm -rf` + `cp -r`，**不**走 `sdflow-init update`。 | `setup.sh:60-77` | dx（**独立**） | 中 |
| **M25** | 沿袭的 `command -v python3` 不一致（存量问题，非本 change 引入）。**建议记 todo，不阻塞本 change。** | — | eng（**独立**） | 低 |
| **M26** | `decision-memo.md` C10「paths 仅 3 条」是**排除 workflow 文件自引用路径后**的口径（实际 4 行），与列表一致、不算错，但没写明口径差异，后续读者容易数错。建议补一句「（不含自引用的 workflow 文件路径）」。 | `windows-recorder-smoke.yml` `paths:` | 接地（**独立**） | 高 |

---

## 四、计数定标（本轮三个悬案的最终测量）

主 session 亲自复跑 grep + 逐站点分类（窗口 ±3 行判 `encoding=`，逐条人工复核），与接地镜、领域镜互校：

| 项 | 四件套声称 | **定标值** | 说明 |
|---|---|---|---|
| 入口脚本（含 `__main__`，按 §1.1 glob） | 27 | **28** | 漏 `migrate_legacy.py`；lib 实为 4 非 5 |
| `subprocess text=True` **调用站点** | 16 | **15** | header 写 16，其自身枚举恰好 15，枚举是对的 |
| 同上 **实际编辑点** | — | **14** | `ship_gate.py` 的 334/341 塌缩为 `_git_run` 内**一处** |
| `write_text()` 缺 `encoding=` | 2 | **0** | 两处均已带，C8 验证方法假阳性 |

> **三方计数曾互相打架（16 / 15 / 14）的根因就在这里**：15 是站点数、14 是编辑点数、16 是笔误。
> 本轮四个独立测量（领域镜 15、接地镜 15、主 session 首测 14、主 session 复测 15 站点 / 14 编辑点）**已收敛**。

排除明细（共 20 个原始命中）：docstring / 注释 2 处（`sdflow_issues_core/__init__.py:1055`、
`ship_gate.py:464` —— 后者在 `run_git_bytes` 的 docstring 里，**领域镜排除它是对的**）；
已带 `encoding=` 3 处（`outside-voice-job.py:755`、`migrate_legacy.py:321`、`sdflow_issues_core/__init__.py:1057`）。
🔴 **`outside-voice-job.py:755` 与 `sdflow_issues_core/__init__.py:1057` 这两处已带编码的站点，
`decision-memo.md` C7 从未提及** —— C7 的证据面不完整，建议补。

---

## 五、各镜核验通过项（如实登记，非只报问题）

- **领域镜**：BASE-02/04/05/08/10/12/13/17/18/19/23/25/27/29 逐条验证通过；独立复核整个 trigger catalog
  未发现漏判触发（确认 `{TG-14, TG-18, TG-19, TG-23}`）；领域清单零命中。
- **接地镜**：C1（本机复现崩溃，实跑 `PYTHONIOENCODING=gbk python3 -c "print('test ✅ done')"` → `UnicodeEncodeError`）、
  C2（加前导后 exit=0）、C3（CI matrix 下限 py3.9）、C4（跨 skill 无共享模块）、C5（镜像除 `tests/` 零差异）、
  C9（`PYTHONIOENCODING` 覆盖 `PYTHONUTF8`，含对照组）全部核验为准确；`conftest.py` 的 ✅/⚠️ 确在 docstring 内；
  `setup.sh` 四道门数量与顺序与文档一致。
- **对抗镜 A**：本机 pytest 9.1.1 实测三种 capture 模式均支持 `.reconfigure()`；C6 的 lib 时序无漏洞
  （`sdflow_issues_core` 无模块级 `print()`，`issues.py` 的 `import sys` 先于 `from … import`）；
  `issues.py:1215` 的 `redirect_stdout(io.StringIO())` 路径无新增风险。
- **对抗镜 B**：6.3 对 `init.py` 的退出码断言**真有意义**（与 6.2 相反）；`impl_route.py` 的
  `import sys`(32) 在 `from __future__`(27) 之后，插入语法安全，且未发现任何目标文件顺序倒置；
  decision-memo 两条「接受的边角」确实只砍防御深度、不砍目标范围（符合通则④边界）。
- ⚠️ **对抗镜 B 的一条「已核验通过」不成立**：它抽查 3 个 lib 文件后判 C6 站得住，被接地镜的穷举测量推翻（见 M1）。

---

## 六、度量锚

<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" host="claude" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="2" sev="致0/高4/中2/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" host="claude" runner="claude" site="—" findings="17" 采纳="16" 裁掉="1" defer="0" 独立="6" sev="致0/高6/中4/低6" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" host="claude" runner="claude" site="—" findings="3" 采纳="3" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中2/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" host="claude" runner="claude" site="—" findings="8" 采纳="8" 裁掉="0" defer="0" 独立="2" sev="致0/高4/中1/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" host="claude" runner="codex" site="design-voice" findings="5" 采纳="4" 裁掉="1" defer="0" 独立="1" sev="致0/高1/中3/低0" -->

**信任边界声明（如实标注，勿当机械保证）**：

- 上述锚由 `lens_metric_emit.py`（exit 0）确定性归约产出，**未手拼**。但 emitter 只保证「给定输入的
  确定性归约」，**不保证输入本身对不对**——分类正确性（某条 finding 该归哪个镜）、roster 完备性、
  findings JSON 誊写准确，仍是主 session 的信任边界。
- **outside-voice 行 `findings="5"` 对应 4 条原始 voice findings**：VOICE-2 被**拆成两行**
  （崩溃场景 → 裁掉 X1；静默失效残值 → 并入 M13 采纳）。此为部分采纳的如实建模，特此标注可审计。
- `sdflow:fanout-capability` 的 `subagents="available"` 由主 session 自报（`host=claude` 免探针）；
  锚行文法自洽可被 `anchor_lint` 核，**「是否真派出了子代理」无机械捕获路径**，属语义层。
- `mirrors=` 三个镜均**真实独立完成**（第二次派发），第一次派发被限额杀死的三镜零产出、未计入任何统计。

---

## 六之二、拍板后修订与窄复核（`[spec-review-amendment]` · 2026-07-29）

人已拍板：**同意 Q1–Q4 四项推荐**，并同意「修订 → 窄复核 → 再进设计门」的顺序。

**修订已落盘并单独 checkpoint**：`8d29b89`（四件套 6 文件，+185/−56）。24 条采纳全部处置完毕，
无一条 defer。逐条落点见各文件的 `[spec-review-amendment]` 标记。

**窄复核（只审增量）** —— 🔴 **主 session 亲验，不转述镜子结论**。本报告 §三 的每个承重数字
都来自子代理报告，而它们被写进了 spec 与 decision-memo 的承重约束位 ⇒ 按通则①「落笔前先证伪」，
逐条独立复跑：

| 复验项 | 方法 | 结果 |
|---|---|---|
| 入口 / lib 计数 | 按 §1.1 glob 穷举 + 逐文件读 `__main__` | `TOTAL=32 / ENTRY=28 / LIB=4` ✅ 与 C6 修正值及 lib 清单逐一吻合 |
| `migrate_legacy.py` 是入口 | `grep -n '__main__'` | `:383` ✅ |
| 两处 `write_text` 已带编码 | 读 `:418-420` / `:59-60` 原文 | 均在下一行带 `encoding="utf-8"` ✅ C8 修正成立 |
| `import sys` 位置跨度 | 逐文件 `grep -n '^import sys'` | 191 / 154 / 79 / 70 ✅ 窗口取消的理由成立 |
| `trivial_shape.py:210` 容错语义 | 读原文 | 确已有 `errors="replace"`、只缺 `encoding=` ✅ Q2 的「非本次新加」成立 |
| `init.py:868` 崩溃点未被吞 | 读原文 | 即 `print(f"✓ sdflow-init {mode} 完成…")`，无 try/except ✅ 6.3 退出码判据有效 |
| `init.py:567` 仅 config-lint 可达 | 读 `_git_root_or_dot()` docstring | 自陈「config-lint 专用」✅ M6 成立 |
| 四道同侪门均有常驻测试 | 逐文件 grep import 行 | 5/5 全部直接 import 模块 ✅；`test_encoding_hygiene.py` 确不存在 ✅ |
| `setup.sh` 交付机制与退出码 | 读 `:60-77` + `grep -n '^\s*exit '` | Windows 走 `rm -rf`+`cp -r` ✅；**全文无裸 `exit`** ✅ M7 成立 |

**结论**：§三 写进四件套的承重数字**全部经主 session 独立复核为真**，无一条需要回退。
`openspec validate --strict --type change` 通过。

⚠️ **窄复核的诚实边界**：本次只复核了「被写进四件套的事实断言」，**未**重跑多镜——
增量是文档修订、不是新设计面，且 Q1–Q4 的方向已由人拍板。若后续再有实质改动，须再走一次本流程。

⚠️ **一处无关改动被扫进 `8d29b89`**：`docs/drafts/20260712.md` 少了尾部 4 行（含一行 `/sdflow-spec …` 草稿）。
该文件在 `9d47f8b` 之后被改动，**非本次评审动作所致**，已如实告知人，未自行回滚（原内容存于 `bd90f94`）。

---

## 七、收敛口

**不建议直接进设计 HARD-GATE。** 本轮 24 条采纳里有 7 条 high，其中 **M1 / M2 / M3 三条直接推翻了
四件套自己写死的承重数字或任务**（28≠27、`ship_gate` 改法会 `TypeError`、`write_text` 是伪任务），
**M4 / M10 两条会让新增的机械门自己制造假红或静默漏检**——这与本 change 的核心目标（消除假红）直接冲突。

建议顺序：

1. 先答 **Q1–Q4** 四个拍板项（Q1 是 TENSION，涉及是否收窄已拍板的 D1）。
2. 据拍板结果修订四件套：`decision-memo.md` C6/C7/C8/C10 + D1（若 Q1 采纳收窄）；
   `tasks.md` §2.9 补 `migrate_legacy.py`、§3.1 改 `ship_gate` 修复点与计数、§3.2 改为核实确认、
   §6.2/6.3 拆断言 + 加 `shell: bash` + 定义 `--root`、§1 补 `hack/tests/test_encoding_hygiene.py`、
   §7.3 的一次性人工核对升为常驻测试；`design.md` 定义「前几行」、补 Risks 两条（catch-all、`errors=replace` 假等值）、
   明示模块导入期副作用；`spec.md` Requirement 2 补反向 Scenario。改动处标 `[spec-review-amendment]`。
3. 修订完**再过一次窄复核**（只审增量），然后才进设计门。

🔴 **拍板前流程纪律**：本报告的 findings 只针对**当前**盘面。人读报告后要求的任何修改都会产出新盘面，
若相对镜子审过的提交有**实质**改动，MUST 先把该改动**单独 checkpoint 提交**、取得其 sha，
再回写 `ship-gate` frontmatter（`design_approved` + `reviewed_sha` **同一次写入**落盘）——
否则锚会指向不含该修订的更早提交，拍板刚完成、第一次跑 gate 就判 design 失鲜、当场自锁。
