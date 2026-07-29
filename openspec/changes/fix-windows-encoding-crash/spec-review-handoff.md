# spec-review hand-off — fix-windows-encoding-crash

> ## ⛔ 本文件已作废（SUPERSEDED · 2026-07-29）
>
> 限额恢复后，被杀死的三镜（对抗 ×2 + 接地 ×1）**已重新派发并真实独立跑完**，
> Step 3 / Step 4 已完成，评审报告 = **`spec-review-report.md`**（`anchor_lint` CLEAN）。
> 本文件仅作为「那次中断发生过」的审计留痕保留，**其中的进度表与 `mirrors="domain"` 判断均已过期**，
> MUST NOT 再据此行动。下面 §六 的五条悬案已在报告的「计数定标」与 M1/M2/M3 中结算。

> **这不是评审报告。** 这是一次因**用量限额耗尽**而中断的 `/sdflow-spec-review` 运行的交接单。
> `spec-review-report.md` **尚未产出**；Step 3（合并去重 + 对抗裁决）与 Step 4（出报告 + 落锚）**均未开始**。
> 恢复运行的人 MUST 从下面「恢复步骤」接着跑，**MUST NOT** 把本文件当成评审结论、**MUST NOT** 据此进设计门。

- 交接时间：2026-07-28（本机 UTC+8 深夜）
- 中断原因：`You've hit your session limit · resets 1:20am (Asia/Shanghai)` —— 四镜中的三镜被限额直接杀死
- 当前分支：`feat/fix-windows-encoding-crash` · 工作区干净 · HEAD = `09bbb55 checkpoint(spec-review-autoplan)`

---

## 一、进度总表

| 步 | 内容 | 状态 |
|---|---|---|
| Step 0 | 确认对象 + 规则根 + 宿主档位 + skew 探测 | ✅ 完成 |
| Step 1 | autoplan 广审（native）+ 落盘 `gstack-review.md` + checkpoint | ✅ 完成并已提交（`09bbb55`） |
| Step 1.5 | outside-voice 复用守卫 → 回落自跑 design-voice | ✅ 完成（第三次派发成功，见 §四） |
| Step 2 | HR-TG 判定 + 能力探针 + 四镜 fan-out | ⚠️ **部分完成 —— 1/4 镜有结果** |
| Step 3 | collect barrier + 合并去重 + 对抗裁决 + 决策登记 | ❌ **未开始** |
| Step 4 | `spec-review-report.md` + lens-metric + anchor_lint + checkpoint | ❌ **未开始** |

---

## 二、Step 0 已解析的环境值（恢复时 MUST 重新 eval 一次，不要照抄当既成事实）

```
RULES_ROOT           = /c/Users/ASUS/.skills/sdflow-skills/sdflow-init/assets/workflow
SDFLOW_HOST          = claude
SDFLOW_TIER_STRONG   = opus
SDFLOW_TIER_MID      = sonnet
SDFLOW_TIER_LIGHT    = haiku
SDFLOW_VOICE_RUNNER  = codex
SDFLOW_VOICE_MODEL   = gpt-5.6-sol
```

skew 探测：两条信号（`lens_metric_emit.py --help` 含 `--host`、契约 `runner:` 行含 `none`）**均已探到**，本轮合法。
`openspec/config.yaml:67-68` `metrics.enabled: true` ⇒ **lens-metric 锚本轮必落**。

> 🔴 **本 harness 的坑（下轮必踩，先记住）**：Bash 工具**每次调用是独立 shell**——
> cwd **会**跨调用保持（`cd` 到子目录后下一次调用仍在那儿，会让脚本报假的 `file-missing`），
> 但 `export` 的环境变量**不会**保持。∴ `eval "$(resolve-models.sh)"` 的结果**进不了**后续调用，
> 派 outside-voice 时 MUST 把 `SDFLOW_VOICE_RUNNER=codex SDFLOW_VOICE_MODEL=gpt-5.6-sol` **字面内联**在命令前缀里
> （值取自同一次 resolve，不构成「重判宿主」）；每条命令 MUST 用绝对路径或前缀 `cd /d/projects/sdflow-skills &&`。

---

## 三、Step 2 fan-out 实况（🔴 反假绿关键段）

| 镜 | agentId | 结果 |
|---|---|---|
| 领域镜 · base-checklist | `aff3b4a6d6343fbea` | ✅ **独立完成**，3 条 findings（§五 BASE-*） |
| 对抗镜 A | `a5b86e98e1bc655d9` | ❌ **被限额杀死**，零产出 |
| 对抗镜 B | `a8bc8b9a7cd95dd9a` | ❌ **被限额杀死**，零产出 |
| 接地镜 | `a564f52f374d64d6e` | ❌ **被限额杀死**，零产出 |

**HR-TG 判定（已跑 `hr_tg_intersect.py`）**：declared = `TG-14,TG-18,TG-19,TG-23`，∩ HR-TG = **∅** ⇒ 不开 `hr-tg` 站点。
**能力探针**：`host=claude` ⇒ 免探，`subagents="available"`。

🔴 **恢复时的硬约束（`如实降级 · MUST NOT 假绿`）**：
上面三个死镜**没有任何可用产出**。恢复者只有两条路，**没有第三条**：

- **(A) 重新跑这三镜**（限额恢复后重派 fresh 子代理；`SendMessage` 续跑对已 terminate 的 agent 不可靠，建议直接重派）——
  跑成了才计入 roster。
- **(B) 如实降级**——报告 Step 2 段**显著标注**「⚠️ 对抗镜 ×2 + 接地镜 ×1 因会话限额未能执行，本轮多镜不完整」，
  `<!-- sdflow:fanout-capability ... mirrors="domain" -->` **只写 `domain`**，
  lens-metric 的 `roster` **只含 `domain` + `broad` + `design-voice`**。

**MUST NOT** 为这三镜落锚、计入 roster、或用主 session 自己的复核冒充它们的独立产出。
**强烈建议走 (A)**：接地镜（机械读码核验）恰好是本 change 的高价值镜——四件套里全是「27 个脚本 / 16 处 subprocess」这类
**可机械证伪的数目断言**，而已有的三处独立计数**已经互相打架**（见 §六 D-1）。

---

## 四、outside-voice（design-voice）实况

三次派发，只有第三次有效：

| run dir | rc | 说明 |
|---|---|---|
| `20260728T142819Z-zXcE0L` | 0 | 上一 session 跑成，但 stdout 只存在于那个 session 的后台输出文件里，**已不可恢复** ⇒ 作废 |
| `20260728T145216Z-nW1q85` | 1 | 派发被拒：`SDFLOW_VOICE_RUNNER 未设置（host=unknown…）` —— 根因即 §二 的 env 不跨调用 ⇒ 作废 |
| **`20260728T145835Z-qGaZ8b`** | **0** | ✅ **有效**。`dispatch-manifest.tsv`: `design-voice bzm8tmefh 20260728T145907Z none` |

- 复用守卫 `outside_voice_guard.py` 对 `gstack-review.md` 判 **`section-not-found`（rc=1）** ⇒ 依协议**回落自跑** design-voice。
  （中途曾出现一次 `file-missing`，那是 cwd 漂移导致的**假报**，非真实状态，已复跑纠正。）
- 有效运行的 reason_code = **`ok`**（rc=0）；`declared-sites` 锚 = `<!-- sdflow:declared-sites v1 declared="design-voice" -->`。
- 🔴 **安全边界**：helper 的裸 stderr **绕过 `secret_scan`**。报告正文只可写结构化字段（reason_code / exit code / stderr 行数字节数），
  **MUST NOT 誊写、引用、转述 stderr 文本**——报告是 git-tracked 的，那等于把未扫描的可能含凭据的文本永久提交。
  `.outside-voice/` 保持 gitignored。下面 §五 的 VOICE-* 全部来自 **stdout**（已过 secret_scan），可安全入报告。

---

## 五、已在手的 findings 池（Step 3 的输入 —— 全部尚未裁决）

### 5.1 Step 1 · autoplan 广审（已提交于 `gstack-review.md`，`mode="native"`）

CEO 视角：
- **CEO-1〔high〕** 新机械门无常驻 pytest，而四道同侪门都有。
- **CEO-2〔medium-high〕** 存在性检查用裸文本/正则，可被注释骗过；建议 `ast.parse()`。
- **CEO-3〔medium〕** P2（subprocess / write_text）是点修，无常驻门守。
- **CEO-4〔low-medium〕** CI 真跑只覆盖 ~28 个脚本中的 2 个。
- **CEO-5〔low〕** 标题数字过不了算术/grep 复核。

Eng 视角：
- **ENG-1〔high〕** `setup.sh` 恒退出 0 ⇒ CI 6.2 的**退出码断言部分**是空转。
  ⚠️ 主 session 已修正：「输出不含 `UnicodeEncodeError`」那半**是有效信号**，裁决时 MUST NOT 说 6.2 整条无信号。
- **ENG-2〔high〕** 「前几行」未定义且必然假阴——`hack/check_codex_efficacy_evidence.py` 的 `import sys` 在第 70 行、
  `sdflow-ship/scripts/ship_gate.py` 在第 191 行。
- **ENG-3〔high〕** `sdflow-issues/scripts/migrate_legacy.py:383` 有 `__main__`、在 glob 内，却**漏在 `tasks.md` §2.9 之外**。
- **ENG-4〔high〕** 新门无自动化回归测试（与 CEO-1 同源）。
- **ENG-5〔medium〕** 前导块落在裸模块作用域而非 `__main__` 守卫内；~15 个测试文件把这些脚本当库 import。
- **ENG-6〔medium〕** CI 6.3 的 `--root` 未定义。
- **ENG-7〔low〕** `windows-latest` 并非真正承重（`PYTHONIOENCODING` 与 OS 无关）。
- **ENG-8〔low〕** 沿袭的 `command -v python3` 不一致。

DX 视角：
- **DX-1〔medium〕** 新门失败输出契约未规定，三道同侪门都有 `修：` 提示。
- **DX-2〔medium〕** 那 4 行模版无永久住所（只在 `tasks.md` 里，归档即消失）；`CLAUDE.md:303`「修改本仓库的注意」未提及它。
- **DX-3〔medium-high〕** 新门无常驻测试（第三次独立命中）。
- **DX-4〔medium〕** `design.md` 的「`errors=replace` 不引入新失败模式」被**本仓自己**的
  `sdflow-ship/scripts/ship_gate.py:437-441` docstring 证伪（U+FFFD 替换会让不同字节串比较相等）；
  可疑站点 `sdflow-issues/scripts/issues.py:1109`。
- **DX-5〔low〕** Migration Plan 低估了交付面（~10 个 skill 的 `scripts/**` 走 `setup.sh:60-77` 的 `rm -rf` + `cp -r`，
  **不**走 `sdflow-init update`）。

**主 session 机械复核（autoplan 阶段）**：
- 入口脚本实测 **28** 个，非 27。
- `setup.sh` 无任何 `exit` 语句 ⇒ 恒退出 0。
- `mechanical-gates.yml` 里只有 **2** 道门有独立 CI 步骤（async-branch-parity、`sync_principles --check`）。
- `windows-recorder-smoke.yml` 目前**根本没跑 `setup.sh`**；且 `windows-latest` 默认 pwsh ⇒ 6.2 须显式 `shell: bash`。
- 🔴 **MAIN-1〔high · 高置信〕** `tasks.md` §3.1 把 `ship_gate.py ×2` 指向调用点 334/341，
  但 `_git_run(root, args, text)`（**第 304 行**）只有三个位置参数、无 `**kwargs` ⇒ 在调用点加 `encoding=` 会 **`TypeError`**。
  正解是改进 `_git_run` **函数体内部**（它**已有** `errors="replace"`，只缺 `encoding=`）。

### 5.2 Step 2 · 领域镜 base-checklist（唯一完成的镜）

- **BASE-1 / BASE-07〔高置信 · medium〕** `tasks.md:30` 称「16 处」但其自身枚举只有 15 条。镜独立 grep `text=True` 得 21 个原始命中，
  排除 2 处纯注释（`sdflow_issues_core/__init__.py:1055`、`ship_gate.py:464`）、2 处已带编码
  （`migrate_legacy.py:321`、**`outside-voice-job.py:755` —— decision-memo C7 从未提及它**）、1 处镜像重复
  （`openspec/workflow/tools/trivial_shape.py:210`），得 **15**。
- **BASE-2 / BASE-06〔中置信 · low-medium〕** 4 行模版的裸 `except Exception: pass` 是 catch-all，BASE-06 禁止；
  `design.md:51-56` Risks 无「`reconfigure()` 自身抛异常」条目，`spec.md:7-15` 的 Scenario 只覆盖成功后路径。
  一旦触发，原 bug 静默复现且无痕。
- **BASE-3 / BASE-01〔中置信 · low-medium〕** `spec.md:17-30` Requirement 2 只有成功路径 Scenario，
  缺反向用例「真有漂移 + GBK 环境 → 门正确报非零且打印 🔴 时不崩」。警示符号出现在失败消息里的频率**高于**成功消息。
- 该镜的**通过项**：BASE-02/04/05/08/10/12/13/17/18/19/23/25/27/29 逐条验证通过；
  独立复核了整个 trigger catalog，未发现漏判触发（确认 `{TG-14, TG-18, TG-19, TG-23}`）；领域清单零命中。

> ⚠️ 该镜完成通知附带一条警告：复核其产出时 `claude-sonnet-5[1m]`（安全分类器）不可用 ⇒ 其输出**采信前应复验**。

### 5.3 outside-voice · design-voice（跨模型 `codex/gpt-5.6-sol`，reason_code=`ok`）

四条，全部来自 stdout，`OV_TRUNCATED=false`：

- **VOICE-1〔high〕** CI 的「真实子进程」验证可能只证明入口脚本覆盖了 `PYTHONIOENCODING=gbk`，
  **没有验证 16 处 `subprocess(..., text=True)` 的解码修复**——subprocess 风险发生在**父进程解码子进程输出**时；
  若被调命令未实际输出非 ASCII，漏掉 `encoding=` 也照样绿。
  建议：加专门夹具子进程，稳定输出 UTF-8 中文 + 非法 UTF-8 字节，断言不崩且替换行为符合预期。
- **VOICE-2〔high〕** 裸调 `sys.stdout/stderr.reconfigure(...)` 可能把编码崩溃**换成启动期 `AttributeError`**——
  测试框架 / IDE / 嵌入式宿主可把标准流换成 `StringIO` 等无 `reconfigure` 的对象；材料只讨论了 pytest 捕获不能复现编码问题，
  没覆盖**替换流时前导块自身的兼容性**。建议 `getattr(stream, "reconfigure", None)` 后再调 + 加无 `reconfigure` 流的回归测试。
  （与 **ENG-5** 同一片面，Step 3 去重时注意合并镜集合。）
- **VOICE-3〔medium〕** 机械门只查 `reconfigure(encoding=` 的存在，**守不住所声明的 stdout / stderr / `errors="replace"` 三项契约**；
  只配 stdout、写在注释里、或落在不可达代码里都会假绿。
  🔴 **这条直接反驳 D1 的「无界语法面」论证**：完整前导块本身是**有限、可机械验证的结构**，不是「语义扫描 print 数据流」那种无界面。
  建议：仍保持简单检查，但分别验证 stdout / stderr 两处调用 + 固定参数；或 AST 查顶层调用，或用带明确 marker 的规范化片段做精确文本校验。
  （与 **CEO-2** 同片面但论证角度不同——CEO-2 说「会被注释骗」，VOICE-3 说「D1 援引的基准⑤在这里不适用」。）
- **VOICE-4〔medium〕** `PYTHONIOENCODING=gbk` 的测试模型**没覆盖真实故障面**：该变量会**主动覆盖**标准流编码，
  于是测的是「人为强制 GBK 的进程」，而不是 Windows **无该变量**时由控制台 / 重定向管道 / locale 决定编码的路径，
  还可能掩盖环境继承问题。建议保留该确定性用例，同时在 Windows runner 上加「移除 `PYTHONIOENCODING` + 设 code page + 输出中文/emoji」
  的用例，控制台与重定向管道至少各一。

---

## 六、Step 3 必须先解掉的悬案

- **D-1 · subprocess 站点计数三方打架（🔴 优先）**：`tasks.md` 声称 **16**、其自身枚举 **15**、
  base-checklist 镜独立测得 **15**、主 session autoplan 阶段测得 **14**。
  裁决前 MUST 亲自重跑一次 grep 定标（接地镜本该干这个，见 §三）。
- **D-2 · MAIN-1 与 tasks.md §3.1 直接冲突**：若采信 MAIN-1，§3.1 的「`ship_gate.py` ×2」条目本身写错了修复位置 ⇒
  站点计数还要再动。D-1 与 D-2 须一起结算。
- **D-3 · VOICE-3 vs D1**：这是**对已拍板决策 D1 的正面挑战**，且论据是本仓自己的基准⑤适用边界。
  按 tension 规则 ⇒ 进决策登记区 TENSION 条目（两方视角 + 推荐 + 三面后果 + 主次判定），**绝不静默采纳、也不静默驳回**。
- **D-4 · `outside-voice-job.py:755` 已带编码却未被 decision-memo C7 提及** —— C7 的证据锚需要补或修。
- **D-5 · 入口脚本 27 vs 28** —— 四件套通篇写 27，实测 28（ENG-3 指出漏的正是 `migrate_legacy.py`）。

### 已知需登记的自动决策（autoplan 阶段产生，MUST 进报告决策区）

- **A1** codex voice 在 autoplan 内不可用（本机缺 `codex-windows-sandbox-setup.exe`）⇒ 该阶段标 `[subagent-only]`。
- **A2** Eng / DX 视角并行派发。
- **A3** 不前置 restore-point。
- **A4** premise gate 未弹出（G2 适配）。

---

## 七、恢复步骤（限额恢复后照此接着跑）

1. **重跑 Step 0 的解析与探测**（env 不跨 session，MUST 重来）：unset → `resolve-models.sh` → 捕获 rc → `eval` → 校验 →
   `resolve-workflow.sh` → skew 两探。任一 fail ⇒ fail-loud 硬停。
2. **决定三个死镜的去向**（§三 的 A / B 二选一）。建议 **A**：至少重派**接地镜**（本 change 的数目断言密度高，
   §六 D-1/D-2/D-5 三条悬案都是它的活）+ **对抗镜 ×2**。
   每个子代理 prompt **MUST 原文整段携带** `sdflow:principles` 四条通则区块（不转述、不摘要、不给指针）。
3. **Step 3 collect barrier**：design-voice 已在手（§五 5.3），无其它未决站点 ⇒ barrier 可直接通过。
4. **Step 3 裁决**：合并去重（记录每条 finding 的命中镜集合，供 lens-metric 导出「独立」）→ 对抗裁决 →
   **反静默压制**（判不成立的也 MUST 带原始发现 + 裁掉理由落「已裁掉」区）→ 置信分流（低置信仍一行上抛）→
   先结算 §六 五条悬案。
5. **Step 4 出报告** `spec-review-report.md`，锚行如下（`mirrors=` 按第 2 步的实际结果填）：
   ```
   <!-- sdflow:step1-broad-review v1 mode="native" -->
   <!-- sdflow:hr-tg v1 hit="none" declared="TG-14,TG-18,TG-19,TG-23" -->
   <!-- sdflow:declared-sites v1 declared="design-voice" -->
   <!-- sdflow:fanout-capability v1 host="claude" subagents="available" mirrors="domain" -->
   ```
6. **lens-metric**（`metrics.enabled: true` ⇒ 必落）：构造 input JSON（roster 只含实际独立完成的行键）→
   `python3 $RULES_ROOT/tools/lens_metric_emit.py --layer spec-review --host claude --input <f>` →
   **exit 0 才**把 stdout 落进报告；exit≠0 ⇒ 本段不落 + 注明报错，**MUST NOT 手拼锚行顶替**。
7. **锚行自检**：`python3 $RULES_ROOT/tools/anchor_lint.py --report {change_dir}/spec-review-report.md --layer spec-review --root "$(git rev-parse --show-toplevel)" --trigger-catalog $RULES_ROOT/trigger-catalog.md` ——
   非 0 即阻塞，遵其判定，MUST NOT 静默吞。
8. **checkpoint**：`~/.sdflow/hack/checkpoint-commit.sh spec-review "并行多镜审 + 合并报告 + spec-review-amendment"`。
9. 收敛口一句：是否建议进设计 HARD-GATE。**拍板发生后**才写 `ship-gate` frontmatter
   （`design_approved` + `reviewed_sha` 两字段**同一次写入**落盘；拍板前若四件套有实质改动，MUST 先单独 checkpoint 再回写锚）。

---

## 八、全程适用的红线（恢复者请先读这段）

- **G2**：中途 **MUST NOT** `AskUserQuestion`；决策写进报告「决策登记区」，人在设计门一次性拍板。
- **反静默压制**：判「不成立」的 finding **MUST** 连原始内容 + 裁掉理由落「已裁掉」区；低置信项一行带过，**绝不静默滤除**。
- **如实降级 · MUST NOT 假绿**：没独立跑过的镜，**不落锚、不进 roster、不进 `mirrors=`**。
- **outside-voice stderr MUST NOT 入报告正文**（只可写 reason_code / exit code / 行数字节数）。
- **每次 outside-voice 调用用全新 `mktemp -d` run dir**，绝不复用或覆盖已有 run dir。
