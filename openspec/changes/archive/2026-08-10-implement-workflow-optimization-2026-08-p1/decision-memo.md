---
schema_version: 1
change: implement-workflow-optimization-2026-08-p1
branch: feat/implement-workflow-optimization-2026-08-p1
generated_at: 2026-08-10T11:10:25+08:00
decision_hash: 2508953fda3c
---

# 决策纪要 · implement-workflow-optimization-2026-08-p1

## 目标态

retro 报告具备镜砍留拍板的两个判据（per-镜实修率历史回算 + per-change token 维新起累积），且 recorder 支持 `reopen` 命令，解锁 1.A.1 池对账（roadmap 阶段 1 的 1.B 四子任务；1.A 不在本 change）。

## 拍板决策

- **D1 token 快照锚 = checkpoint-commit.sh 内联采集 + 落 change 目录文件**（人 2026-08-10 明确确认）——
  机制：checkpoint 在 `git add -A` 之前调 helper，定位当前 transcript（优先 `$CLAUDE_SESSION_ID`
  对应文件，无则取 `~/.claude/projects/<本仓 munged 路径>/` 下 mtime 最新 jsonl），累加全部 usage
  字段，追加一行快照（session_id + step + 累计值）到 `openspec/changes/<name>/token-log.jsonl`，
  随同一 checkpoint commit 入库。依据：① usage 字段实测在场（本 session 39 条，含 input/output/
  cache_read/cache_creation）；② 落 change 目录 ⇒ 随归档走，retro join 与读 review 报告同构，
  免 git log message 解析；③ 相邻快照差分 = 阶段级 token Δ，与 stage_walltimes 的
  attribute-to-next 口径天然对齐。硬边界：helper 失败 MUST 静默降级（写「无锚」行），
  MUST NOT 挡 checkpoint 主功能；Codex 宿主无 ~/.claude transcript ⇒ 写「无锚」降级行，
  MUST NOT 自报冒充机械锚。**砍掉的候选**：(b) hook 路径（Stop/PostToolUse 拿 transcript_path
  更准，但动全局 hook 配置面 + 与 checkpoint 时点对齐别扭，v1 过重）；(c) commit message
  trailer（破坏 checkpoint 坑① 单行 -m 纪律 + retro 得解析 git log，两头更脆）。

- **D2 实修率 join 规则 = 报告 per-finding 处置标注为主信号（严格窄文法），修复 commit 降为
  佐证 flag**（人 2026-08-10 明确确认）——实修判定：finding 行含精确标注 `已修[impl-review-fix]`
  （语料唯一形态，83 处/63 份报告）⇒ 计实修；镜归属按有界信号解析（finding ID 前缀/裁掉表
  「来源」列/所在小节），解析不出 ⇒ 未知桶 MUST NOT 猜；per-镜输出可判定/未知/覆盖率三数，
  实修率分母 = 可判定数；未达最小无歧义样本量 ⇒ 标「参考」不入砍留依据（阈值在 specs 定）；
  change 边界内存在修复 commit 只打「有 commit 佐证」flag，不参与判定。依据：① 逐 finding→
  commit 映射不可恢复样本真实存在（35cbe38 一 commit 修多 finding，roadmap 风险表自认），
  commit 做门会把真实修判成未知；② `已修` 标注与修复 commit 同轮同 commit 入库，是最细粒度
  信号；③ 窄文法 + 未知桶符合基准 5（散文面无界不手搓全量解析器，只提取精确 needle）。
  **对 roadmap 1.B.1「join 修复 commit」措辞的显式偏离已向人呈现并获确认**（commit 主键降为
  佐证）。**砍掉的候选**：(b) commit 主键 join（聚合 commit 无法逐 finding 归属，覆盖率大幅掉）；
  (c) 只信「采纳」不算实修（等于不做 T108，采纳≠实修缺口原样保留）。

- **D3 reopen 命令语义 = 新子命令五件套**（人 2026-08-10 明确确认）——
  `issues_v2.py reopen <ID> --reason <理由> [--to OPEN|PROPOSED]`：① 守卫（ID 格式合法 +
  必须位于 closed/（在 open ⇒ die）+ pool/前缀一致 + --reason 必填，对称于终态必填 reason
  纪律）；② 状态默认回 OPEN（契合 sweep 纪律 OPEN→PROPOSED），--to PROPOSED 可选，终态值
  一律拒；③ 字段清理 closed_date/closed_reason/resolved_by → null（open 项不变量），原
  closed_reason 进历史行不丢（`> 日期 状态：WONTDO → OPEN（reopen：<理由>；原 closed_reason：
  <原值>）`）；④ 原子序镜像 set-status 的 M-2（先 closed/ 原位原子写，再 git mv 回 open/，
  中断残留可被 reindex 检出）；⑤ 命令内自动 reindex（roadmap 1.B.4 明文；与 reorganize/
  migrate 同惯例，issues_v2.py:776/1170）。set-status 不自动 reindex 的存量不对称本 change
  不动（不加宽）。契约测试 = 往返（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）+
  拒绝面（open 项 reopen / 缺 reason / --to 传终态值）。**砍掉的候选**：(b) 放宽 set-status
  允许 closed→非终态（击穿「终态不可再改」不变量）；(c) 手工搬文件（roadmap 明文 MUST NOT）。

## 承重约束

- **C1 reopen 必须走新命令，不绕 recorder** — 验证方式：读 `cmd_set_status` 终态守卫；
  **证据锚**：`sdflow-issues/scripts/issues_v2.py:530-531`（location=="closed" ⇒ die「已处于
  终态，不可再改 status」）。手工搬 `closed/` 文件即绕过 ID 分配/INDEX 再生一致性
  （roadmap 1.A.1 明文 MUST NOT）。
- **C2 「采纳 ≠ 实修」且 join 歧义真实存在** — 验证方式：读归档报告实样 + 修复 commit 形态；
  **证据锚**：lens-metric 锚（124 份报告/439 条，`grep -c "lens-metric v1" archive/*/{code,spec}-review-report.md`
  汇总）只有 采纳/裁掉/defer/独立 无「实修」字段；finding 行标注是文本级
  （`archive/2026-08-09-absorb-gstack-autoplan/code-review-report.md` Findings 段
  「**已修[impl-review-fix]**」）；修复 commit 是聚合形态（`35cbe38 checkpoint(impl-review):
  多镜代码审自动修复`，一 commit 修多 finding）⇒ 逐 finding→commit 映射存在不可恢复样本，
  报告 MUST 输出可判定/未知/覆盖率三数（design.md 假设 A1）。
- **C3 token 机械采集路径在 Claude 宿主存在；逐镜 token 无机械承诺** — 验证方式：本机实读
  transcript JSONL；**证据锚**：`~/.claude/projects/-Users-cheneyzhao-Documents-04-sdflow-skills/
  <session>.jsonl` 每条 assistant message 带 usage（实测 39 条，字段含 input_tokens/output_tokens/
  cache_read_input_tokens/cache_creation_input_tokens）；per-子代理 token 不在 transcript 分列
  （wco P2 已确认）⇒ 逐镜 token MUST NOT 做机械承诺（design.md 假设 A2）。
- **C4 retro 为 view-only 再生、无持久状态** — 验证方式：读 retro_report.py 全文；
  **证据锚**：`sdflow-retro/scripts/retro_report.py:524-531`（build_report docstring「view-only
  再生，无持久状态」）⇒ 实修率历史回算每次再生重算即可；token 快照是唯一新持久落点（D1 已定）。
- **C5 阶段 1 两条前置条件已满足** — 验证方式：实跑 + 读 task-log；**证据锚**：
  `python3 sdflow-retro/scripts/retro_report.py --root .` 实跑 OK + 86 测试绿；
  `openspec/roadmaps/workflow-optimization-2026-08/task-log.md`「阶段 0 / review + 收尾」
  记录初审完成 + 收尾 checklist 四项通过。

## 接受的边角

- **同仓多并发 session 时 mtime 启发式可能选错 transcript** — 概率低（本仓单人串行为主）/
  影响小（快照行带 session_id 可事后甄别，且 token 列是趋势参考非门禁）/完美成本高
  （需宿主注入 session 身份，无公开机械接口）；**为何接受**：快照锚定位是参考性度量，
  错选可甄别、可重算，不值得为它引入 hook 面。
- **一个 session 横跨两个 change 时 token Δ 归属有毛边** — 同上三镜权衡；与 stage_walltimes
  对墙钟的既有毛边同构（attribute-to-next 也有同类边界），口径一致即可。

## 三镜代价

（三决策均命中 TG-23，逐条写满。）

**D1**：系统镜——checkpoint 脚本是全局资产（`sdflow-init/assets/hack/` 真相源，
改后须重跑 setup.sh），影响所有用 checkpoint 的仓，故 helper 失败必须静默降级不挡 commit；
用户镜——无感（快照随 checkpoint 自动落，无新手工步骤）；开发循环镜——retro join 同构于
读报告文件，零新增解析面。**主次判定**：系统镜为主——采集失败绝不能破坏 checkpoint 主功能。

**D2**：系统镜——纯读侧新函数，报告列可删即回滚，零持久状态；用户镜——报告多两列 +
三数注记，读表成本微增；开发循环镜——「采而未修」从此可见，评审假绿有了机械暴露面。
**主次判定**：开发循环镜为主——判据缺失正是决策端欠账的根因（承 roadmap design 决策 1）。

**D3**：系统镜——纯新增子命令，零触碰既有命令路径（set-status 终态守卫原样保留），
可整体回滚；用户镜——一条新命令，help 一行学习成本；开发循环镜——1.A.1 池对账当即解锁，
理由归真让未来分诊记录恢复可信。**主次判定**：系统镜为主——不破坏既有终态契约是硬约束。
