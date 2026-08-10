---
impl-pipeline: tickets
---

## Global Constraints

以下逐字摘自该 change design.md 的 MUST/MUST NOT/SHALL 硬约束与 Compliance 条款：

- 三个改动面互相独立可回滚：token 采集（checkpoint 侧）、实修率回算（retro 读侧）、reopen（issues CLI）互不依赖，任一失败不牵连其余。
- 采集与回算全走机械路径；机械够不着的样本进未知桶显式呈现，MUST NOT 用模型判断补桶。
- 不改 `lens_metric_aggregate.py` 的任何既有函数签名（实修率是新增只读消费方）。
- helper 失败 MUST 静默降级（写「无锚」行），MUST NOT 挡 checkpoint 主功能。
- Codex 宿主无 transcript ⇒ 写「无锚」降级行，MUST NOT 自报冒充机械锚。
- 复用 `issues_v2.py` 内联既有 mechanics，MUST NOT 引入对已删除脱钩的 `sdflow_issues_core` 的依赖。
- MUST NOT 改 set-status 守卫。
- 新 Python 入口 `token_snapshot.py` 带 4 行 `reconfigure` 前导（第五道机械门）。
- bundle 真相源纪律：checkpoint-commit.sh 与 helper 只改 `sdflow-init/assets/hack/`，经 setup.sh 分发，MUST NOT 直改 `~/.sdflow/hack/` 副本。
- 窄文法 fix-status 三态：精确 needle `已修[impl-review-fix]` → 实修；行含 defer 类标注 → defer；行含 `impl-review-fix` 裸串或处置动词但不命中精确 needle → 未知桶，MUST NOT 默认判「未修」。
- 镜归属窄文法：封闭关键词表只在有界来源记号内查（表格行「来源」列、或 `〔…〕`/`【…】` 标签），MUST NOT 对整个 finding 行自由文本做无边界子串匹配。
- token-log 读侧 MUST 逐行防御解析：无法解析的行按 `anchor=false` 等价处理，不中断该 change 及其余 change 的报告生成。
- token 列 MUST NOT 合成总分（四计数价格不同，合计会造假象）。
- reopen 拒绝路径错误文案沿用 `_die` 单句惯例。
- session-id 文法校验（basename 且匹配 `^[0-9a-fA-F-]+$` 才拼路径，防路径拼接逃逸）。
- token_snapshot.py 内部自设执行超时（如 10s）；追加写整行 buffer 后单次 O_APPEND write；输出行字段封闭 schema（只写 spec 列明字段，MUST NOT 透传 transcript 任何其他内容）。
- checkpoint-commit.sh 接线位置钉死：插在 `git status --porcelain` 判空 gate 之后、`git add -A` 之前。
- Δ 归属口径：读侧全局按 session 跨 change 分组差分，消除跨 change 双计数。
- reopen 中断残留幂等恢复：closed/ 内非终态文件判中断残留走幂等续跑迁移。
- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）与 `openspec/rules/premise-verification.md`。

### Task 1: recorder reopen 命令

**Blocked-by:** none
**R-ID:** R-IS1

在 `sdflow-issues/scripts/issues_v2.py` 新增 `reopen` 子命令，实现 closed→open 的唯一受控逆转换。

行为描述：
- `issues_v2.py reopen <ID> --reason <理由> [--to OPEN|PROPOSED]`
- 守卫：ID 必须位于 closed/（在 open/ ⇒ `_die`「ID {id} 不在终态（位于 open/），无需 reopen」）、pool/前缀一致、`--reason` 必填（argparse required）、`--to` 只接受非终态值（OPEN|PROPOSED，终态值 ⇒ `_die`「--to 只接受非终态状态（OPEN|PROPOSED），收到 {v}」）
- closed/ 内文件状态已非终态 ⇒ 判中断残留，幂等续跑迁移（不重复清字段、不重复追加历史行）
- 状态默认回 OPEN，`--to PROPOSED` 可选
- 字段清理：closed_date/closed_reason/resolved_by → null；原 closed_reason 进历史行（空值写「（无 closed_reason）」）
- 历史行格式：`> 日期 状态：WONTDO → OPEN（reopen：<理由>；原 closed_reason：<原值>）`
- M-2 原子序：closed/ 原位原子写 → git mv 回 open/
- 命令内自动 reindex（含 closed/ 非终态文件 WARNING 输出；git mv 后 reindex 失败文案「重开已生效，重跑 reindex 即自愈」）
- 复用 `issues_v2.py` 内联 mechanics（`_die`/`atomic_write_text`/`cmd_set_status` M-2 序/`cmd_reindex`），MUST NOT import `sdflow_issues_core`
- MUST NOT 改 set-status 既有守卫
- 契约测试（`sdflow-issues/tests/`）：往返（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）、拒绝面三例（open 项 / 缺 reason / --to 终态值，均验「文件与索引零变更」）、中断残留幂等恢复用例（原位写后 mv 前中断 → 重跑收敛且不重复历史行）、既有守卫零回归（set-status 对 closed/ 仍拒 + 全量既有测试绿）
- SKILL.md 文档同步：`sdflow-issues/SKILL.md` 补 `reopen` 用法块并修正措辞

- [x] reopen 子命令实现（守卫 + 字段清理 + M-2 原子序 + 自动 reindex + 中断残留恢复）
- [x] 契约测试：往返 + 拒绝面三例 + 中断残留幂等 + 既有守卫零回归
- [x] SKILL.md 文档同步

### Task 2: 实修率历史回算

**Blocked-by:** none
**R-ID:** R-WR1

在 `sdflow-retro/scripts/retro_report.py` 新增实修率回算（聚合④段），从归档报告 finding 行机械提取 fix-status 与 lens 归属。

行为描述：
- 真语料试算前置：先用一次性脚本对归档报告跑窄文法（fix-status 三态 + 有界记号 lens 匹配），产出 per-(layer,lens) 可判定数预估，密度结论写进 impl 记录后再进正式实现
- fix-status 三态判定：精确 needle `已修[impl-review-fix]` → 实修；含 defer 类标注 → defer；含 `impl-review-fix` 裸串或处置动词但不命中精确 needle → 未知桶（MUST NOT 判未修）；无任何处置信号 → 未修
- 封闭 lens 关键词表（LENS_ENUM 同源六值映射 + `域` 别名）：只在有界来源记号内匹配（表格行「来源」列或 `〔…〕`/`【…】` 标签），MUST NOT 全行子串匹配；0 或多命中 → 未知桶
- 复用 `lens_metric_aggregate.py` 的 `_fence_aware_lines` 滤围栏示范锚，不改该模块任何既有函数签名
- 聚合④段渲染：per-(layer,lens) 实修数/可判定/未知/覆盖率/实修率 + 阈值 5 单一源常量（<5 标「参考」）+ change 边界修复 commit 佐证 flag（不参与判定）
- 测试（`sdflow-retro/scripts/tests/`）：合成语料用例（可判定/lens 歧义/零命中/围栏内示范锚不入计/fix-status 变体/自由文本关键词不构成归属）+ 真仓再生冒烟（聚合④在场、13 面待复评镜实修率或「参考」可读）

- [x] 真语料试算前置：一次性脚本跑窄文法密度预估，结论写进 impl 记录
- [x] 窄文法提取函数（fix-status 三态 + lens 有界匹配）
- [x] 聚合④段渲染（实修率表 + 阈值 + 佐证 flag）
- [x] 测试：合成语料单元 + 真仓再生冒烟

### Task 3: token 快照采集

**Blocked-by:** none
**R-ID:** R-TS1, R-TS2, R-TS3

新增 `token_snapshot.py` helper 并在 `checkpoint-commit.sh` 接线，实现 checkpoint 级 token 快照采集。

行为描述：
- 新增 `sdflow-init/assets/hack/token_snapshot.py`（带 4 行 `reconfigure` 前导）
- transcript 定位序：`$CLAUDE_CODE_SESSION_ID` 精确命中 `~/.claude/projects/<munged-cwd>/<id>.jsonl` → munged-cwd 目录 mtime 最新 jsonl 回退 → 无则 `no-transcript` 降级行；session-id 文法校验（basename + `^[0-9a-fA-F-]+$`）后才拼路径
- usage 四计数 + messages 累加（非负整数校验，不过则 `parse-error` 降级行）；字段封闭 schema（只写 spec 列明字段）
- change 目录由分支名解析（无落点静默跳过）
- 追加 v1 行 schema 到 `token-log.jsonl`（整行 buffer 后单次 O_APPEND write）
- 内部自设执行超时（10s，超时放弃采集）
- 全程 try/except 到降级行
- `sdflow-init/assets/hack/checkpoint-commit.sh` 接线：判空 gate 之后、`git add -A` 之前插入 `python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`
- 测试（`hack/tests/`）假 HOME 沙盒真跑 bash：正常采集入同一 commit / 无 transcript 写 `no-transcript` 行 / helper 缺席与崩溃时 checkpoint 照常提交 / 无 change 落点零写入 / 连续 checkpoint 只追加且累计单调不减 / 干净树+helper 在场仍 no-op 不建 commit / canary transcript 断言输出面无泄漏
- 重跑 `bash setup.sh` 分发，dogfood 验收：本 change 下一次真实 checkpoint 产出 anchor=true 快照行

- [x] token_snapshot.py 实现（定位/累加/v1 行/降级/超时/文法校验/封闭 schema）
- [x] checkpoint-commit.sh 接线（gate 后 add 前）
- [x] 假 HOME 沙盒集成测试（7 场景）
- [x] [e2e] setup.sh 分发后 dogfood 验收：真实 checkpoint 产出 anchor=true 快照行

### Task 4: retro token 列渲染

**Blocked-by:** 3
**R-ID:** R-WR2

在 `sdflow-retro/scripts/retro_report.py` 新增 token-log.jsonl 读取与 per-change token 列渲染。

行为描述：
- 读 token-log.jsonl：先扫全部 change 目录（活动 + 归档）的 token-log.jsonl，按 `session` 全局分组
- Δ 归属口径：跨 change 时后一文件首行对前一文件末行差分、Δ 落行所在 change，消除跨 change 双计数；仅全局首行全额计入；anchor=false 行不入计数
- 逐行防御解析：无法解析的行按 anchor=false 等价处理，不中断该 change 及其余 change 的报告生成
- per-change 表 tokens 列渲染：`out 12.3k / in 4.5k / cc 89k / cr 1.2M` 四计数紧凑串（MUST NOT 合成总分）；无锚显「—」
- 列旁恒加脚注「数值为各会话累计口径聚合，tickets 管线下多为独立短会话的首行全额之和，非严格阶段增量」
- 测试（`sdflow-retro/scripts/tests/`）：合成 token-log 用例（多 session/跨 change 同 session 不双计数/降级行/缺文件/含损坏行不崩）+ 全仓再生冒烟（存量 change 全「—」不崩）

- [x] token-log 读取与 Δ 归属计算（全局 session 分组 + 差分）
- [x] per-change tokens 列渲染（四计数紧凑串 + 脚注）
- [x] 测试：合成 jsonl 单元 + 全仓再生冒烟

### Task 5: 收尾集成与文档同步

**Blocked-by:** 1,2,3,4
**R-ID:** R-IS1, R-WR1, R-WR2

全仓聚合验证 + 报告再生 + 文档同步。

行为描述：
- 全仓 pytest 绿（`/usr/bin/python3 -m pytest`）：sdflow-issues/tests/ + sdflow-retro/scripts/tests/ + hack/tests/ + 仓根 conftest 全量
- `openspec/retro/report.md` 再生提交（`python3 sdflow-retro/scripts/retro_report.py --root .`）：聚合④实修率段在场 + per-change tokens 列在场（存量 change 显「—」）
- roadmap `task-log.md` 追加 1.B 交付记录
- CONTEXT.md「实修率」词条按用户拍板结果处置（未确认 MUST NOT 写入）
- `sdflow-retro/SKILL.md` 补聚合④实修率段与 per-change tokens 列的一句说明

- [x] 全仓 pytest 绿
- [x] report.md 再生并验证聚合④与 tokens 列在场
- [x] roadmap task-log.md 追加 1.B 交付记录
- [x] SKILL.md 文档同步（sdflow-retro）

### Task 6: 实现验证（收尾，不计入 3–6 预算）

**Blocked-by:** 1,2,3,4,5
**R-ID:** all

按「聚合套件发现契约」运行本 change 的单元+集成+e2e 测试套件并全部通过，证据落
`impl-reports/task6-verify.md`（每层一行 `<层>|<命令原文>|<退出码>|<SHA>`）。

- [ ] 单元测试证据齐全并通过
- [ ] 集成测试证据齐全并通过（或记「未覆盖」+ 判定依据）
- [ ] e2e 测试证据齐全并通过（或记「未覆盖」+ 判定依据）
