# design — implement-workflow-optimization-2026-08-p1

## Context

动机见 `proposal.md` §Why。实现所依赖的现状事实（全部已核验）：

- `checkpoint-commit.sh`（53 行，真相源 `sdflow-init/assets/hack/`，装到 `~/.sdflow/hack/`）：`git status --porcelain` 判空跳过 → `git add -A` → 单行 `-m` commit；`git add -A` 在 `:51`，任何要随 checkpoint 入库的文件必须在此之前写完。
- Claude 宿主给 Bash 注入 `CLAUDE_CODE_SESSION_ID`（本机实测 = 当前 transcript 文件名 `~/.claude/projects/<munged-cwd>/<session>.jsonl`）；transcript 每条 assistant message 带 `message.usage`（`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens`，实测 39 条在场）。
- `retro_report.py`（660 行，view-only 再生）：`build_report` 逐 change 组装 per-change 表 + 聚合①②③；`lens_metric_aggregate.py` 提供 fence-aware 锚解析（`parse_report` / `_fence_aware_lines`）与 `(layer,lens,host,runner,site)` 分组键。
- 归档报告 124 份 / lens-metric 锚 439 条；修复标注唯一形态 `已修[impl-review-fix]`（83 处 / 63 份）；finding 行散文格式跨时期漂移（bullet/表格混杂）。
- `issues_v2.py`（1227 行）：`cmd_set_status` 对 `closed/` 硬拒（`:530`）；终态迁移用 M-2 原子序（先原位原子写、再 `git mv`）；`reorganize`/`migrate` 命令内自动 reindex（`:776`/`:1170`），`set-status` 不自动。

## Goals / Non-Goals

**Goals（设计级边界）**：

- 三个改动面互相独立可回滚：token 采集（checkpoint 侧）、实修率回算（retro 读侧）、reopen（issues CLI）互不依赖，任一失败不牵连其余。
- 采集与回算全走机械路径；机械够不着的样本进未知桶显式呈现，MUST NOT 用模型判断补桶。

**Non-Goals（proposal §Non-Goals 之外的设计级排除）**：

- 不做 token-log 的跨仓聚合视图（单仓 retro 内消费即可）。
- 不做实修率的增量缓存（retro view-only 再生原则，C4；439 锚 / 124 份报告的全量重算是毫秒级）。
- 不改 `lens_metric_aggregate.py` 的任何既有函数签名（实修率是新增只读消费方）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)（D1 token 快照锚机制 / D2 实修率 join 规则 / D3 reopen 语义）。以下为纪要之下的实现级选择：

- **helper 用 Python 独立脚本 `token_snapshot.py`**（落 `sdflow-init/assets/hack/`，随 setup.sh 装 `~/.sdflow/hack/`）：要解析 JSONL，Bash 不合适；带 4 行 `reconfigure` 前导（第五道机械门要求）。checkpoint-commit.sh 在 `git add -A` 前调用：`python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`——`|| true` 是 D1 硬边界（失败不挡 commit）的机械落点。
- **transcript 定位序**：`$CLAUDE_CODE_SESSION_ID`（实测变量名，非纪要草稿里的 `$CLAUDE_SESSION_ID`）→ 命中 `~/.claude/projects/<munged-cwd>/<id>.jsonl` 直取；变量缺席 → 同目录 mtime 最新 jsonl 回退；目录/文件均无 → 无锚行（reason=`no-transcript`）。munged-cwd = `os.getcwd()` 的 `/`→`-` 替换（与宿主既有布局一致，实测核对本仓路径）。
- **change 目录定位**：从当前分支名取 `feat/<change>` 的 `<change>`，存在 `openspec/changes/<change>/` 才写快照；否则静默跳过（main 上的 checkpoint、归档后的收尾 commit 无落点，属接受的边角——见纪要「接受的边角」）。
- **实修率呈现 = 新增「聚合④ per-镜实修率（历史回算）」独立段**，分组粒度 `(layer, lens)`：finding 行的镜归属信号只有 lens 级关键词，比 lens-metric 锚的五元组粗；若把粗粒度率 join 到聚合③的细行会重复计数，独立段无此问题。
- **镜归属窄文法 = 封闭关键词表**：finding 行（含其所在表格行的「来源」列）内查 lens 关键词（`对抗`/`领域`/`接地`/`历史`/`outside-voice`|`voice`/`广审` → LENS_ENUM 六值映射）；精确命中一个 → 可判定；零个或多个 → 未知桶。表是封闭枚举（LENS_ENUM 同源），不是散文解析——基准 5 合规。
- **token 列格式**：per-change 表单列 `tokens`，值形如 `out 12.3k / in 4.5k / cw 89k / cr 1.2M`（output / input / cache_creation / cache_read 四计数紧凑串，无合成总分——四者价格不同，合计会造假象）；无 token-log 的 change 显 `—`。
- **Δ 归属口径**：token-log 行按 `session` 分组，组内相邻行差分归后一行的 `step`（attribute-to-next，与 `stage_walltimes` 同口径）；session 首行全额计入该行 step（该 session 自启动以来的累计，含跨 change 毛边——纪要「接受的边角」已收）。

## 组件与数据流

### 组件/依赖图（TG-14）

```
sdflow-init/assets/hack/                     ~/.sdflow/hack/          （setup.sh 拷贝）
  checkpoint-commit.sh ──调用──▶ token_snapshot.py
                                      │ 读
                                      ▼
                        ~/.claude/projects/<munged-cwd>/<session>.jsonl
                                      │ 追加
                                      ▼
                        openspec/changes/<change>/token-log.jsonl ──随归档──▶ archive/…/token-log.jsonl
                                                                                │ 读（join）
retro_report.py ◀─────── 读（窄文法回算）── archive/**/{spec,code}-review-report.md
      │                                                                         │
      └──▶ report.md：per-change 表 +tokens 列 · 聚合④ 实修率段 ◀───────────────┘

issues_v2.py（reopen 子命令）──▶ sdflow_issues_core/（复用 M-2 原子写 + git mv + reindex）
```

三条链零交叉：token 链（checkpoint→jsonl→retro）、实修率链（报告→retro）、reopen 链（CLI→池）互不依赖。

### 数据流图（TG-11，实修率回算管道）

```
archive/**/…-review-report.md
   │ _fence_aware_lines（复用 LMA，滤示范锚/围栏）
   ▼
逐行窄文法提取：含「已修[impl-review-fix]」→ fixed / 含 defer 标注 → defer / 其余含 finding 特征 → 未修
   │ 同行封闭关键词表查 lens（0 或 >1 命中 → 未知桶）
   ▼
per-(layer,lens) 累计：实修数 · 可判定数 · 未知数 · 覆盖率
   │ + change 边界内修复 commit 存在性（佐证 flag，不参与判定）
   ▼
聚合④ 表：实修率 = 实修 ÷ 可判定；可判定 < 最小样本量阈值 → 标「参考」
```

### 状态机图（TG-09，issue 生命周期新增 reopen 转换）

```
            set-status（既有）                    set-status（既有）
  OPEN ────────────────────▶ PROPOSED ──────┐
   ▲  ◀────────────────────    │            │
   │        （既有互转）        │            ▼
   │                           └─────▶ 终态 FIXED|WONTFIX / DONE|WONTDO   （open/ → closed/，git mv）
   │                                        │
   └────────── reopen（本 change 新增，唯一受控逆转换；--to PROPOSED 可选）
               closed/ → open/，终态字段清 null，原 closed_reason 进历史行
```

终态经 `set-status` 仍不可再改（守卫原样）；reopen 是绕开该守卫的**唯一**受控路径。

## 数据模型与生命周期（TG-05：token-log.jsonl）

行 schema v1（JSONL，一行一快照，只追加不改写）：

```json
{"v": 1, "ts": "2026-08-10T11:30:00+08:00", "step": "sdflow-spec-grill",
 "session": "a848a77f-…", "host": "claude", "anchor": true, "reason": "ok",
 "usage": {"input": 1234, "output": 5678, "cache_read": 900000, "cache_creation": 12000, "messages": 39}}
```

- `anchor=false` 的降级行：`reason` ∈ {`no-transcript`, `parse-error`, `no-env-fallback-used` 不设——mtime 回退成功仍是 `ok`}，`usage` 省略；Codex/无 transcript 环境即此形态，MUST NOT 伪造计数。
- `usage` 四计数是**session 累计值**（非区间 Δ）——Δ 由 retro 差分算，写侧无状态。
- 生命周期：change 活动期由 checkpoint 追加；归档随目录 `git mv` 冻结；retro 只读。无迁移需求（新文件形态，存量 change 无此文件 → 报告显 `—`）。

## Risks / Trade-offs

- [transcript JSONL 为宿主非公开格式，版本漂移] → 解析失败写 `parse-error` 无锚行，宁缺毋假；报告显式「无锚」，不产生错数。
- [窄文法对早期报告覆盖率可能很低] → 三数（可判定/未知/覆盖率）如实呈现，覆盖率低的镜标「参考」（A1 闸门）；MUST NOT 为提覆盖率放宽文法去猜。
- [checkpoint 全局资产改动波及所有消费仓] → helper 调用带 `|| true` + helper 内部全程 try/except 到无锚行；`hack/tests/` 假 HOME 沙盒真跑 bash 验证「helper 缺席/崩溃时 checkpoint 照常提交」。
- [reopen 与 reindex 组合的中断残留] → 镜像 M-2 原子序，closed/ 内出现非终态文件可被 reindex 检出；契约测试覆盖往返 + 拒绝面。
- [token-log 与墙钟的 change 归属毛边（跨 change session / 归档后 checkpoint）] → 与 stage_walltimes 既有毛边同构，口径一致，纪要「接受的边角」已收；不为边角加机制。

## Migration Plan

1. **部署**：merge 后运行 checkout `git pull` + `bash setup.sh`（`hack/` 是拷贝非软链，不重跑 = 新 SKILL 调旧脚本）；消费仓无需 `sdflow-init update`（本 change 不动 workflow bundle 规则文件）。
2. **回滚**：revert commit + 重跑 `setup.sh`（还原 `~/.sdflow/hack/` 两脚本）；已产生的 token-log.jsonl 是惰性数据，留着无害、可批量删除；retro 两个新列/段随代码 revert 消失；reopen 已重开的 issue 不自动还原（数据操作，如需回滚用 set-status 重新关闭）。
3. **顺序约束**：无窗口期问题——helper 缺席时 checkpoint-commit.sh 的 `|| true` 保证旧行为原样。

## Open Questions

- CONTEXT.md 词表是否收录「实修率」词条（与采纳率/独立率同族第三轴）——负责人：用户；不影响 specs/方案/任务拆分，归档前拍板即可。

## Compliance

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1：本文只写最终态）与 `openspec/rules/premise-verification.md`（Context 全部事实已核验，行号/计数来自本轮实读）。
- 新 Python 入口 `token_snapshot.py` 带 4 行 `reconfigure` 前导（第五道机械门）。
- bundle 真相源纪律：checkpoint-commit.sh 与 helper 只改 `sdflow-init/assets/hack/`，经 setup.sh 分发，MUST NOT 直改 `~/.sdflow/hack/` 副本。
- 无豁免项。
