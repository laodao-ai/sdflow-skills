# hand-off — harden-gate-git-layer

失鲜判定从「反推锚 + 帧枚举 + 全阶段求值」换成「**录锚 + 比内容 + 限定求值窗口**」。
下面是消费方（本仓与下游）在升级后 MUST 知道的行为变化与自查动作。决策与实证见 `openspec/adr/0026`。

## 1. 存量 active 报告须重审一次（缺 `reviewed_sha` 会 fail-closed）

新 gate 以报告 frontmatter 的 `reviewed_sha` 为失鲜判定**唯一真相源**。产出于本次硬化**之前**的
报告没有这个字段 ⇒ gate 判 `UNKNOWN(6)` fail-closed（**不**回退任何反推锚，这是有意的方向安全）。
∴ 每个存量 active change 的 spec-review / code-review / verify 报告都须**重跑对应评审补锚一次**
（补锚 = 结论字段与 `reviewed_sha` 同一次写入落盘）。

### 消费仓只读自查命令（一次列出「几个 active 报告会因缺锚 fail-closed」）

```bash
# 在仓根跑：列出缺 reviewed_sha 的 active 评审报告（跨 bash/zsh 稳，不写盘、纯只读）
find openspec/changes -maxdepth 2 -mindepth 2 -type f \
     \( -name spec-review-report.md -o -name code-review-report.md -o -name verify-report.md \) \
     ! -path '*/archive/*' \
     -exec sh -c 'grep -q reviewed_sha "$1" || echo "缺锚(须重审): $1"' _ {} \;
```

无输出 = 无缺锚、可直接推进；有输出 = 逐个重审补锚，别等撞门才发现代价（全仓无下游消费仓清单，
实际影响面不可估算，故给命令让人自查）。

**本仓现状（2026-07-21 实测）**：唯一 active change = 本 change 自身，`0` 缺锚
（本 change 自身补锚 = 原 todolist T193，**已在本链路兑现**：`spec-review-report.md` 已带
`reviewed_sha=edefe35`，见提交 `0b750ae`，标**已完成**）。

## 2. 撞 code 域失鲜先确认不是真漏审

code 域改用「锚 vs HEAD 顶层条目映射比较」（排除 openspec）。它会真实抓到「代码审后经 merge
提交 resolve 出源码」「`git mv` 把源码迁进 openspec」这类**过去会漏检**的改动 ⇒ 判 `RERUN_STALE`。
撞到 code 域失鲜时 **MUST 先确认这不是一次真的漏审**（源码在放行后确实被改过），再决定重审；
不要默认「gate 误报」而手改锚绕过——手改锚 = 显式越权同权级（git 留痕可审计），但会把真漏审放行。

## 3. 行为收紧：实现期直接改设计纠偏今后被 `REFUSE_START` 拦下 —— 有意为之、非 bug

design 域失鲜**只在实现窗口（`RUN_SOP` / `RUN_PLAN` / `CONTINUE_IMPL`）内求值**，进入代码审后不再检查。
后果两面，**都是有意设计**：

- **代码审期 / done 期**对四件套的修订（`opsx:verify` 明文允许「revise design.md to match reality」）
  落在窗口外，**不再触发** design 失鲜——消除了全阶段求值在 14 类历史情形上的纯噪声假阳。
- **实现期**（窗口内）「照着已批准设计边写边纠偏」这类直接改四件套的动作，今后会被 `REFUSE_START(exit 3)`
  拦下。**这是行为收紧、不是缺陷**：正解 = 走「halt → 重走 spec-review → 重新拍板」的正规流程，
  **窗口内不设逃生口**。全仓有 3 个确证反例（实现期 checkpoint 改过自身设计产物，最近一个在拍板后
  1.6 小时）——它们今后会被拦，这正是判据的目的。

维护者若见到「实现期改设计被拒」的反馈，**先按此条判定为预期行为**，别当 bug 去加旁路。

## 4. 生效路径：`sdflow-init update` 对本 change 无效，须 `/sdflow-upgrade`

`ship_gate.py` 与三个评审 SKILL 都**不在** `sdflow-init/assets/workflow/` bundle 内，`sdflow-init update`
只刷新项目本地 `openspec/workflow/` 规则副本 ⇒ **对本 change 的改动无效**。
生效路径 = **`/sdflow-upgrade`**（或手动 `git pull` + `bash setup.sh`）。

⚠ **producer 与 gate MUST 同批发布**：只发 producer 则新锚读不到，只发 gate 则所有存量报告 fail-closed。
Windows 上 `setup.sh` 走逐目录 `cp -r`，字母序 `sdflow-ship` 在 `sdflow-spec-review` 之前 ⇒ 中断会产生
「新 gate + 旧 producer」（方向 fail-closed，安全但挡流程）；**勿中断，中断后重跑可自愈（幂等）**。

⚠ **回滚不对称，MUST 人工核验后再回**：旧 gate 在 design 域**无条件全阶段求值**。若某 change 已在新
gate 下进入代码审后修订过四件套（新语义下合法、历史有 14 例），回滚会使其立刻撞 `REFUSE_START` 打回。
回滚前 MUST 核验在途 change 的阶段。

## 5. 已完成 / 未完成 · defer 批次

**本票（Task 6）已完成**：
- ADR-7(a) 两段提交时序（`sdflow-code-review/SKILL.md`）+ ADR-7(b) 拍板前二次修订单独落盘
  （`sdflow-spec-review/SKILL.md`）+ 收敛口窄复核纪律 + 人工补锚指引（补两字段 + ADR-1 语义句）。
- `ship_gate.py` 头注释重写（录锚 + 比内容 + 限定求值窗口，指向 adr/0026；已知不覆盖段登记归档终态盲区、
  窗口右边界间隙、T189 耦合）+ `sdflow-ship/SKILL.md` 链序段行为边界。
- 测试 5.13（code-review 自动修复两段时序不自锁）+ 5.17（design 拍板前二次修订，锚指含修订提交不被拒），
  各附变异证明（对照用例 + 真实 ship_gate 守卫变异体，双角色，见 impl-report）。
- 6.3 全历史核验：A2 的三个 strict-口径确证反例仍是全部（编排层已跑，结论登记进 impl-report）。

**未完成 / 延后（defer，见批次 `harden-gate-git-layer`，共 14 项）**：本 change 执行期识别的残余项
已登记进 todolist 并经 `sdflow-done` sweep 归入批次 `harden-gate-git-layer`（见 `openspec/issues/batches.md`
与 `INDEX.md`；T193 本 change 自身补锚已 DONE 不在批内）。分四簇——① **诚实边界残余**（T200/T201/T202：
CAUSE_READ_FAILED 触发点回验、6 vs 5 类 cause、Task3 两处 fail-closed 收紧偏离 design 字面）
② **文档完备性**（T204：A2 宽口径低计，非缺陷、MUST NOT 当风险缩设计）③ **独立面/超本 change scope**
（T189 勾选框归一化口径反转、T203 门禁用例偶发 flake 定性、T192 emitter 输入不落盘致 SR-M 不可执行、
T194–T199 各 Task 的 Minor 与 pytest 环境）④ **冷代码审残余**（T205：code 域排除整个 openspec/ 含
`workflow/tools/*.py` 真实运行代码，大半是已登记「规则漂移」残余的锐化；T206：归档报告 `.strip()` 与
live 读口径不一致）。均**不阻断本 change 归档**：属残余诚实登记或独立面，非本 change 承诺的目标态缺口。

## 6. 冷代码审（阶段三承重墙）—— 抓出 4 条跨 ticket 缺口，全部当场修复

**六轮双轴审 + 每票窄复核都没抓到的 4 个跨 ticket 缺口，冷层（5 镜 + 2 跨模型 codex voice）一次全挖出**——
实证「独立冷主审不可优化掉」。全部当场修复（`bc748bc`，标 `[impl-review-fix]`）+ 编排层独立变异复核：

- **F1（多镜收敛：领域+历史+对抗A+对抗B）** `ship_gate.py` 头注释描述**已删的** `checkpoint(impl-review)`
  subject 豁免（Task3 换 ls-tree 已删）；「三报告各自必带 reviewed_sha」契约对 design 报告实为**窗口内**
  保证（plan 全勾后窗口关、锚校验活在 window-gated is_stale 里）；main「捕获整个函数体」假注释
  （parse_args 在 try 外，SystemExit(2) 逸出）；退化测试守 prose → **注释订正三处 + 删退化测试**。
- **F2（对抗镜 B 本地复现）** ADR-4 要求 design/code/verify 三处 stale 都带 reviewed_sha，实际只 design 域带；
  code/verify 漏带 → **两域补锚 + 测试（变异删锚双 KeyError 红）**。
- **F3（跨模型 voice hr-tg）** 报告读 `read_text` 不捕 `OSError`，PermissionError/TOCTOU 逸出退出码 1
  脱契约集（同 Task2 UnicodeEncodeError 类）→ **抽 `_read_report_text` 面治 3 点 + 单元&端到端测试**。
- **F4（跨模型 voice code-voice）** code-review SKILL 两段时序自相矛盾（报告先落盘被 `git add -A` 卷入
  「仅源码」修复提交）→ **重排编号步骤，报告写盘明确移到取锚后/report-only 提交前**。

裁剪边界：**冷独立主审与注入点 B（subagent-dev 循环内即时修复确认）机制不同、不可互相替代**——本轮实证
（F1-F4 是循环内被各票局部视角放过的真缺口）。撤任一层都留洞。

## 7. verify 结论 + roadmap

- **verify = PASS**（强档 opus，Do-Not-Trust 冷启，每 ✅ 附机验锚点）：5 条 spec Requirement 全部 Scenario
  均有实现 + 测试锚点，核心缺口 0，`sdflow-ship/tests/` 331 passed。见 `verify-report.md`。
- **roadmap 回填**：exit 3 NO_ASSOCIATION——本 change 非 roadmap 驱动（standalone gate 硬化），无草稿。

## 8. 全套件回归

- **本地半场**：`sdflow-ship/tests/` = **331 passed**（含冷审 F2/F3 新增用例）；仓根全套件 **2083 passed**。
- **合并后主干再跑一次**：归 merge 后（tasks 5.16 后半）。
