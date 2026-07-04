# code-review 报告 — cross-model-outside-voice

> 2026-07-04 · DIFF_BASE=b013172..HEAD（19+ commits，22 文件 +1918）· **本轮同时是本 change 新机制的活体首跑**（Step1 原生执行、helper 双路 codex、fallback、v1 锚行全链首用）

### Step1 · gstack/review（原生执行，scope-drift + 完成度）

<!-- sdflow:step1-broad-review v1 mode="native" -->
（侧信道佐证：gstack /review skill 指令直接进主 session 执行，学习检索/scope 探测命令实跑；非子代理转述）

- **Scope Check: CLEAN** — Intent = superpowers-plan.md 12 任务（R1–R6 全覆盖）；Delivered = helper+测试+两 SKILL 接入+catalog 套件+收尾，diff 内 22 文件全部映射到 plan 任务，无「顺手多改」。
- **完成度: 12/12 DONE**（证据 = SDD 台账 + task1-12 checkpoint 链 + tasks.md 30 项已勾）；plan 审计无 PARTIAL/NOT DONE。
- 附带发现（已修）：tasks.md 勾选状态曾与实况脱节（maintainability specialist 命中，C4 修复回填）。

### 命中范围

栈: bash helper + pytest + markdown 编排（无 domains 栈命中→base 清单镜）· 清单: CR-01~09 · 风险: 高（TG-08 外部依赖 + TG-17 信任边界）→ 对抗镜 ×3 · 历史镜 ×1 · gstack specialists（testing/maintainability/adversarial）×3

<!-- sdflow:hr-tg v1 hit="TG-08,TG-17" evidence="codex CLI 跨服务调用（外部依赖）+ 仓库代码经 context 发外部 LLM（信任边界）" -->

### outside voice（跨模型层，活体首跑实录）

<!-- sdflow:outside-voice v1 site="code-voice" guard="none" runner="claude-fallback" reason_code="timeout" findings="1" truncated="false" -->
<!-- sdflow:outside-voice v1 site="hr-tg" guard="none" runner="codex" reason_code="" findings="3" truncated="false" -->

- code-voice：185KB 全量 diff 喂 codex → **300s 超时（exit 124）** → 按协议回落只读型 Claude 子代理（同源 render 框架），返回 1 条（timeout 可移植性，采纳已修）。**实测数据点：cap 200KB 与 timeout 300s 不匹配**（已记 T31②）。
- hr-tg：31KB 聚焦上下文 → codex 成功，3 条 findings（留档入库 critical / render rc 论断 / timeout 探测），裁决见下。
- helper 全链行为与契约一致：preflight ready、secret 预扫、OV_TRUNCATED 留痕、124 正确传播——**机制自证一次真实故障路径（超时→回落）不中断评审**。

### Findings（裁决后采信；全部已修 [impl-review-fix]，21 项）

| 严重度 | 发现 | 源（多源=高置信） | 修复 |
|---|---|---|---|
| critical | `.outside-voice/` 留档（全量 diff/潜在敏感）未 gitignore，checkpoint `git add -A` 会永久入库；secret 命中前已落盘 | **四源**：领域镜+对抗镜1+gstack-adv+codex(hr-tg) | C1 .gitignore `**/.outside-voice/` + C2 协议节 MUST 句 |
| high | 不可读 ctx → `wc -c` 空值 → **exit 0 假绿** + shell 报错文本混入 UNTRUSTED CONTEXT 喂给模型 | 对抗镜3②（实测复现） | A3 `-r` 校验 + B3 测试 |
| high | timeout 治理三合一：无 `-k` 兜底（TERM 被吞则耗时无上界）/ macOS 无 GNU timeout 时 127 混入 exec-error 无法诊断 / preflight 不探测 | 对抗镜2⑥ + codex(hr-tg#3) + **fallback voice**（三源) | A6 timeout/gtimeout 探测 + `-k 10` + preflight 三态 `missing-deps` + B6/B7 测试 + C3 失败模式表行 |
| high | fallback 子代理工具权限未收紧——diff 内 prompt injection 可获执行面（codex 侧有 CLI 强制，fallback 侧没有对等） | gstack-adv#3 | C2 协议改「只读型子代理（禁写/禁执行副作用）」；本轮 fallback 已按此派发（Explore 只读型） |
| medium | secret 黑名单缺本项目最常见形态（sk-ant-/sk-/JWT） | gstack-adv#4 + testing specialist | A8 扩正则 + B1 四分支测试 |
| medium | OV_MAX 非法值（0/负/非数）→ head/tail 报错混入 context 且 exit 0 | 对抗镜3③（实测） | A1 数值校验回落默认 + B4 |
| medium | exec 路径 ctx 缺失的诊断消息被重定向吞（同 secret 预扫已修模式的不对称遗漏） | 对抗镜3① + codex(hr-tg#2 部分) | A4 预检 + B5（含 fake codex 未被调用断言） |
| medium | rc≠0 但 last-message 非空被静默丢弃，无可观测信号 | 对抗镜3⑤ | A7 stderr 提示 + B8 |
| medium | design 安全节「发送范围限摘录」与现实不符（read-only 沙箱可读仓树含 gitignored） | gstack-adv#2 | C3 措辞修正为接受的剩余风险（黑盒验证记 T31） |
| low-med | `--timeout` 非数值 125 误归 codex 报错桶；flag 缺值 shift 挂死；mktemp 未检 | 对抗镜3④ + T30(a-c) 复确认 | A2/A5 + B2（顺手闭 T30 a/b/c） |
| low | 分隔符可被内容伪造制造边界逃逸假象 | 对抗镜3 附加 | A9 frame 防伪句（nonce 化记 T31⑥） |
| low | tasks.md 30 项未勾与实况脱节 | maint specialist（置信 60，<80 但客观可验→裁决采信） | C4 回填 |

### 已裁掉 / 存疑留痕（反静默压制）

- **X1** codex(hr-tg#2)「do_exec 不检查 render_prompt rc 会继续调 codex」——**部分证伪**：`exit` 在同进程直接终止，不会继续执行；其测试建议（断言 codex 未被调用）有价值已并入 B5。
- **X2** 对抗镜1「setup.sh cp 覆盖运行中脚本」——真实反模式但命中窗口微秒级 + fallback 兜底 → defer T31⑧。
- **X3** 对抗镜2「--ephemeral 残留」「归档丢留档」「pytest 并行互扰」、对抗镜3⑥⑦、对抗镜1 #2/#4/#5——各镜自证 REFUTED，一行留痕。
- **X4** testing specialist UTF-8 截断（置信 55）/边界 off-by-one（30）/时序 flaky（25）——<80 滤除留痕；UTF-8 项升 defer（T31⑦）。
- **X5** maint#1 协议节 18 行重复（置信 82）——真实但属 bundle 结构重构非本轮修 → defer T31①。
- 历史镜：D1–D9/B 组/C 组评审意见兑现核查 **100% 无遗漏无打折**，无 finding。

### 修复 / defer 台账

自动修 **21 项** [impl-review-fix]（A1-A9 helper 硬化 / B1-B8 测试 +13 用例 / C1-C4 配置与文档）；defer **8 项** → T31（voice 层硬化池）；顺手闭 T30(a)(b)(c)。
T10复核: A6 timeout 缺失处置（显式报错 vs 静默降级）| 反静默守卫原则明文可判（客观判据①）| 静默降级=把环境缺陷永久混入 exec-error 桶，选显式 missing-deps
voice分桶: **codex 采纳3/裁掉0/defer0 · fallback 采纳1/裁掉0/defer0**（M4 首份实测样本；注：codex#2 论断部分证伪但其测试建议被采纳，计采纳）

### 锚行自检〔4.5〕

三类 v1 锚行本报告齐备（step1-broad-review ×1 / hr-tg ×1 / outside-voice ×2 按位点）；findings=N 与合并池实收 diff：code-voice 1=1 ✓、hr-tg 3=3 ✓。

### 结论

☑ 建议进 `/sdflow-done`　☑ defer 残差已入 todolist T31（hand-off 会引用）　测试 307 全绿（含新增 13）

<!-- ship-gate: code-review=pass -->
