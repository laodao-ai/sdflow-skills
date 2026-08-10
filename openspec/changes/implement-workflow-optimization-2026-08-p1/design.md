# design — implement-workflow-optimization-2026-08-p1

## Context

动机见 `proposal.md` §Why。实现所依赖的现状事实（全部已核验）：

- `checkpoint-commit.sh`（53 行，真相源 `sdflow-init/assets/hack/`，装到 `~/.sdflow/hack/`）：`git status --porcelain` 判空跳过 → `git add -A` → 单行 `-m` commit；`git add -A` 在 `:51`，任何要随 checkpoint 入库的文件必须在此之前写完。
- Claude 宿主给 Bash 注入 `CLAUDE_CODE_SESSION_ID`（本机实测 = 当前 transcript 文件名 `~/.claude/projects/<munged-cwd>/<session>.jsonl`）；transcript 每条 assistant message 带 `message.usage`（`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens`，实测 39 条在场）。
- `retro_report.py`（660 行，view-only 再生）：`build_report` 逐 change 组装 per-change 表 + 聚合①②③；`lens_metric_aggregate.py` 提供 fence-aware 锚解析（`parse_report` / `_fence_aware_lines`）与 `(layer,lens,host,runner,site)` 分组键。
- 归档报告 124 份 / lens-metric 锚 439 条；精确形态 `已修[impl-review-fix]` 83 处 / **15 份** review-report（[spec-review-amendment] 原「63 份」失实，三镜独立复测一致）；裸串 `impl-review-fix` 257 处 / 57 份——修复标注**并非唯一形态**，语料实存带空格、markdown 加粗分隔、全角括号 `〔〕`、`采纳[impl-review-fix]`、段落级「自动修 N 项」台账等变体；finding 行散文格式跨时期漂移（bullet/表格混杂）。
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

- **helper 用 Python 独立脚本 `token_snapshot.py`**（落 `sdflow-init/assets/hack/`，随 setup.sh 装 `~/.sdflow/hack/`）：要解析 JSONL，Bash 不合适；带 4 行 `reconfigure` 前导（第五道机械门要求）。checkpoint-commit.sh 调用：`python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`——`|| true` 是 D1 硬边界（失败不挡 commit）的机械落点。[spec-review-amendment] **接线位置钉死**：插在 `git status --porcelain` 判空 gate（:38-42）**之后**、`git add -A`（:51）**之前**——只在「本来就要 commit」的调用上采集，保持「干净树静默跳过、不建 commit」契约逐字节不变（`sdflow-done` verify 依赖该 no-op 语义）；插在 gate 之前会让 helper 自己弄脏干净树、no-op 永久失效。[spec-review-amendment] **helper 加固三件**：① 内部自设执行超时（如 10s，超时即放弃采集，`|| true` 只防非零退出、防不住挂起——checkpoint 被编排 skill 同步调用，一次 hang 拖死整条流水线）；② token-log 追加写为整行 buffer 后单次 `O_APPEND` write（POSIX 本地 fs 原子，防中断留半行）；③ 输出行字段封闭 schema（只写 spec 列明字段，MUST NOT 透传 transcript 任何其他内容，usage 各计数 MUST 校验为非负整数）+ session-id 文法校验（basename 且匹配 `^[0-9a-fA-F-]+$` 才拼路径，防路径拼接逃逸）。
- **transcript 定位序**：`$CLAUDE_CODE_SESSION_ID`（实测变量名，非纪要草稿里的 `$CLAUDE_SESSION_ID`）→ 命中 `~/.claude/projects/<munged-cwd>/<id>.jsonl` 直取；变量缺席 → 同目录 mtime 最新 jsonl 回退；目录/文件均无 → 无锚行（reason=`no-transcript`）。munged-cwd = `os.getcwd()` 的 `/`→`-` 替换（与宿主既有布局一致，实测核对本仓路径）。
- **change 目录定位**：从当前分支名取 `feat/<change>` 的 `<change>`，存在 `openspec/changes/<change>/` 才写快照；否则静默跳过（main 上的 checkpoint、归档后的收尾 commit 无落点，属接受的边角——见纪要「接受的边角」）。
- **实修率呈现 = 新增「聚合④ per-镜实修率（历史回算）」独立段**，分组粒度 `(layer, lens)`：finding 行的镜归属信号只有 lens 级关键词，比 lens-metric 锚的五元组粗；若把粗粒度率 join 到聚合③的细行会重复计数，独立段无此问题。
- **镜归属窄文法 = 封闭关键词表 + 有界匹配面** [spec-review-amendment]：lens 关键词（`对抗`/`领域`/`接地`/`历史`/`outside-voice`|`voice`/`广审` → LENS_ENUM 六值映射；`域` 作为 `领域` 的别名，仅在来源记号内识别）只在**有界来源记号**内查——表格行「来源」列、或 `〔…〕`/`【…】` 标签形态——**MUST NOT 对整个 finding 行自由文本做无边界子串匹配**（真实语料已实证假阳性：文件名 `outside-voice-reuse-guard` 会误判给 voice 镜、「历史注释」误判给历史镜，且这类误判恰落「可判定」桶，未知桶拦不住）。记号内精确命中一个 → 可判定；零个或多个、或行内无有界记号 → 未知桶。表是封闭枚举（LENS_ENUM 同源），不是散文解析——基准 5 合规。（较纪要 D2 收窄：finding ID 前缀/所在小节两类信号源未采用——前者语料中不带 lens 信息、后者跨行归属易错，仅保留有界同行信号。）
- **fix-status 三态判定（宁缺毋假方向修正）** [spec-review-amendment]：精确 needle `已修[impl-review-fix]` → 实修；行含 defer 类标注 → defer；**行含 `impl-review-fix` 裸串或处置动词（已修/采纳/自动修）但不命中精确 needle → 未知桶**，MUST NOT 默认判「未修」——语料实测 67% 的 `impl-review-fix` 出现不命中精确 needle（变体/段落级台账），默认判未修会方向性压低实修率、恰好污染砍留判据；只有**无任何处置信号**的 finding 行才判「未修」。实现前先用一次性脚本对真实语料跑试算（per-(layer,lens) 可判定数预估），确认分桶密度再进正式实现（tasks 2.0）。
- **token 列格式**：per-change 表单列 `tokens`，值形如 `out 12.3k / in 4.5k / cc 89k / cr 1.2M`（缩写对照钉死：`out`=output / `in`=input / `cc`=cache_creation / `cr`=cache_read，[spec-review-amendment] 原 `cw` 与 schema 字段名 `cache_creation` 对不上，改 `cc` 直接对应；四计数紧凑串，无合成总分——四者价格不同，合计会造假象）；无 token-log 的 change 显 `—`。
- **Δ 归属口径**：token-log 行按 `session` 分组，组内相邻行差分归后一行的 `step`（attribute-to-next，与 `stage_walltimes` 同口径）；session 首行全额计入该行 step（该 session 自启动以来的累计，含跨 change 毛边——纪要「接受的边角」已收）。[spec-review-amendment] ⚠️ 评审证伪了「与 stage_walltimes 同构」类比（walltime 是 delta-only、首提交贡献 0；本口径首行贡献全额绝对值 ⇒ 同一 session 横跨两 change 时前段用量在两处**真实双计数**）——修法待设计门拍板（报告 Q1，推荐读侧全局按 session 跨 change 分组差分）。tokens 列旁恒加脚注「数值为各会话累计口径聚合，tickets 管线下多为独立短会话的首行全额之和，非严格阶段增量」。
- **reopen 中断残留幂等恢复** [spec-review-amendment]：守卫在「位于 closed/」之外加一分支——文件在 closed/ 但 `status` 已非终态 ⇒ 判为 M-2 序中断残留（原位写成功、`git mv` 未跑），**幂等续跑迁移，不重复清字段、不重复追加历史行**（防止二次执行取到已清空的 closed_reason、生成「原 closed_reason：null」误导行）。`reindex` 对 closed/ 内非终态文件输出可见 WARNING（现 `cmd_reindex` 只照单渲染，「可被检出」才成立）；`git mv` 后 reindex 自身失败 ⇒ 错误信息明示「重开已生效，重跑 `reindex` 即自愈（无状态重算）」。历史行格式在原 closed_reason 为空（FIXED/DONE 路径本就不写该字段）时写「（无 closed_reason）」。
- **reopen 拒绝路径错误文案（实现基准，沿用 `_die` 单句惯例）** [spec-review-amendment]：① open 项 → `ID {id} 不在终态（位于 open/），无需 reopen`；② 缺 `--reason` → argparse required 报错（`--reason 必填`）；③ `--to` 终态值 → `--to 只接受非终态状态（OPEN|PROPOSED），收到 {v}`；④ pool 前缀不符 → 沿用既有前缀校验文案。

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

issues_v2.py（reopen 子命令，内联复用自身既有 M-2 原子写 + git mv + reindex mechanics）
```

[spec-review-amendment] 原图中 `sdflow_issues_core/` 节点删除——该包已删除脱钩（`issues_v2.py` docstring 明言不 import 它），mechanics 全部内联在 `issues_v2.py` 自身（`atomic_write_text:251`、`cmd_set_status` M-2 序、`cmd_reindex:717`）。

三条链零交叉：token 链（checkpoint→jsonl→retro）、实修率链（报告→retro）、reopen 链（CLI→池）互不依赖。

**组件清单（BASE-25）** [spec-review-amendment]：

| 组件 | 职责 | 形态/落点 |
|---|---|---|
| `checkpoint-commit.sh` | checkpoint 过场提交（判空→add→commit），gate 后接线调 helper | Bash 全局资产（assets→`~/.sdflow/hack/`） |
| `token_snapshot.py`（新增） | 定位 transcript、累加 usage、追加快照行 | Python 全局资产（同上） |
| `token-log.jsonl`（新形态） | checkpoint 级 token 快照锚，只追加 | change 目录数据文件，随归档冻结 |
| `retro_report.py`（扩展） | 实修率回算（聚合④）+ token join（tokens 列） | Python 只读再生脚本 |
| `issues_v2.py reopen`（新子命令） | 终态唯一受控逆转换 + 自动 reindex | Python CLI（单文件内联 mechanics） |

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
- [token-log 与墙钟的 change 归属毛边（跨 change session / 归档后 checkpoint）] → 归档后无落点静默跳过维持；跨 change 双计数已升级为设计门拍板项（见 Δ 归属口径的 amendment 注记，「同构」类比不成立）。[spec-review-amendment]
- [token-log 单行损坏拖垮整仓报告] → 读侧 MUST 逐行防御解析：无法解析的行按 `anchor=false` 等价处理（不入计数、不中断该 change 及其余 change 的报告生成），镜像 `retro_report.py` 既有 per-file try/except 惯例。[spec-review-amendment]
- [同仓并行子代理 transcript 同目录] → 宿主对主 session 与子代理均稳定注入 `$CLAUDE_CODE_SESSION_ID`（实测在场），mtime 回退实际触发概率低（修正纪要「单人串行为主」的论证措辞：并行子代理场景在本仓是常态，靠 env 精确命中而非串行性保安全）。[spec-review-amendment]

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
