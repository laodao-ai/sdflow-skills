# tasks — implement-workflow-optimization-2026-08-p1

> Requirement ID 对照：R-IS1 = issues-scripts-shared-core「reopen 命令契约」；
> R-WR1 = workflow-retro「per-镜实修率历史回算」；R-WR2 = workflow-retro「per-change token 维 join」；
> R-TS1/2/3 = token-snapshot-anchor「采集与同 commit 入库」/「失败降级」/「只追加无状态」。

## 1. recorder reopen 命令（R-IS1，P0）

- [x] 1.1 `issues_v2.py` 新增 `reopen` 子命令：守卫（closed/ 限定、pool/前缀一致、--reason 必填、closed/ 内非终态文件判中断残留走幂等恢复 [spec-review-amendment]）、状态（默认 OPEN，--to 非终态白名单）、字段清理（三终态字段→null，原 closed_reason 进历史行，空值写「（无 closed_reason）」[spec-review-amendment]）、M-2 原子序（closed/ 原位原子写 → git mv 回 open/）、命令内自动 reindex（含 closed/ 非终态告警 + 失败自愈提示 [spec-review-amendment]）；复用 `issues_v2.py` 内联既有 mechanics（`_die`/`atomic_write_text`/`cmd_set_status` M-2 序/`cmd_reindex`），MUST NOT 引入对已删除脱钩的 `sdflow_issues_core` 的依赖 [spec-review-amendment]，MUST NOT 改 set-status 守卫【R-IS1】
- [x] 1.2 契约测试：往返（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）、拒绝面三例（open 项 / 缺 reason / --to 终态值，均验「文件与索引零变更」）、中断残留幂等恢复用例（原位写后 mv 前中断 → 重跑收敛且不重复历史行 [spec-review-amendment]）、既有守卫零回归（set-status 对 closed/ 仍拒 + 全量 `sdflow-issues/tests/` 绿）【R-IS1】

## 2. 实修率历史回算（R-WR1，P0）

- [x] 2.0 [spec-review-amendment] 真语料试算前置：一次性脚本对归档报告跑窄文法（fix-status 三态 + 有界记号 lens 匹配），产出 per-(layer,lens) 可判定数预估——确认分桶密度后再进 2.1 正式实现，密度结论写进 impl 记录【R-WR1】
- [x] 2.1 `retro_report.py` 窄文法提取：fix-status 三态（`已修[impl-review-fix]` 精确 needle→实修；含 `impl-review-fix` 裸串/处置动词但不命中 needle→未知桶，MUST NOT 判未修 [spec-review-amendment]）+ 封闭 lens 关键词表（LENS_ENUM 同源六值映射 + `域` 别名，仅有界来源记号内匹配——「来源」列或 `〔〕`/`【】` 标签，MUST NOT 全行子串 [spec-review-amendment]，0/多命中→未知桶）；复用 `LMA._fence_aware_lines` 滤围栏示范锚【R-WR1】
- [x] 2.2 聚合④段渲染：per-(layer,lens) 实修数/可判定/未知/覆盖率/实修率 + 阈值 5 单一源常量（<5 标「参考」）+ change 边界修复 commit 佐证 flag（不参与判定）【R-WR1】
- [x] 2.3 测试：合成语料用例（可判定 / lens 歧义 / 零命中 / 围栏内示范锚不入计 / fix-status 变体——带空格 `已修 [impl-review-fix]`、`采纳[impl-review-fix]`、无标注 `已修：` 均进未知桶 / 自由文本关键词不构成归属 [spec-review-amendment]）+ 真仓再生冒烟（聚合④在场、13 面待复评镜实修率或「参考」可读）【R-WR1】

## 3. token 快照采集（R-TS1/TS2/TS3，P1）

- [x] 3.1 新增 `sdflow-init/assets/hack/token_snapshot.py`（4 行 reconfigure 前导）：transcript 定位序（`$CLAUDE_CODE_SESSION_ID` 精确命中 → munged-cwd 目录 mtime 最新回退 → 无则 `no-transcript` 降级行；session-id 文法校验后才拼路径 [spec-review-amendment]）、usage 四计数+messages 累加（非负整数校验，不过则 `parse-error` [spec-review-amendment]）、change 目录由分支名解析（无落点静默跳过）、追加 v1 行 schema 到 token-log.jsonl（字段封闭 schema、整行单次 O_APPEND 写、内部自设执行超时 [spec-review-amendment]）；全程 try/except 到降级行【R-TS1】【R-TS2】【R-TS3】
- [x] 3.2 `sdflow-init/assets/hack/checkpoint-commit.sh` 在判空 gate 之后、`git add -A` 前接线 `python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`（插入点钉死 gate 后——保持干净树 no-op 契约 [spec-review-amendment]；真相源在 assets，MUST NOT 直改 `~/.sdflow/hack/` 副本）【R-TS1】【R-TS2】
- [x] 3.3 `hack/tests/` 假 HOME 沙盒真跑 bash：正常采集入同一 commit / 无 transcript 写 `no-transcript` 行 / helper 缺席与崩溃时 checkpoint 照常提交 / 无 change 落点零写入 / 连续 checkpoint 只追加且累计单调不减 / **干净树 + helper 在场仍 no-op 不建 commit** [spec-review-amendment] / **canary transcript 断言输出面无泄漏** [spec-review-amendment]【R-TS1】【R-TS2】【R-TS3】
- [x] 3.4 重跑 `bash setup.sh` 分发，dogfood 验收：本 change 的下一次真实 checkpoint 产出 anchor=true 快照行（roadmap 验收标准「跑一次真实 checkpoint 验证」）【R-TS1】

## 4. retro token 列（R-WR2，P2，依赖任务 3 落锚）

- [x] 4.1 `retro_report.py` 读 token-log.jsonl：先扫全部 change 的 token-log、session **全局**分组（跨 change 时后一文件首行对前一文件末行差分、Δ 落行所在 change，不双计数——设计门 Q1 拍板=A [spec-review-amendment]）、组内相邻 anchor=true 行差分归后行 step（attribute-to-next）、仅全局首行全额计入、anchor=false 行不入计数、无法解析行逐行跳过不中断整报 [spec-review-amendment]【R-WR2】
- [x] 4.2 per-change 表 tokens 列渲染：out/in/cc/cr 四计数紧凑串（缩写对照见 design [spec-review-amendment]）、MUST NOT 合成总分、无锚显「—」、列旁累计口径脚注【R-WR2】
- [x] 4.3 测试：合成 token-log 用例（多 session / 跨 change 同 session 不双计数 [spec-review-amendment] / 降级行 / 缺文件 / 含损坏行不崩 [spec-review-amendment]）+ 全仓再生冒烟（存量 change 全「—」不崩）【R-WR2】

## 5. 收尾

- [x] 5.1 全仓 pytest 绿（`/usr/bin/python3 -m pytest`）+ `openspec/retro/report.md` 再生提交（含聚合④与 tokens 列）
- [x] 5.2 roadmap `task-log.md` 追加 1.B 交付记录；CONTEXT.md「实修率」词条按用户拍板结果处置（未确认 MUST NOT 写入）
- [x] 5.3 [spec-review-amendment] SKILL.md 文档面同步：`sdflow-issues/SKILL.md` 补 `reopen` 用法块（与既有命令文档密度一致）并把「不可再改 status」措辞改为「不可经 set-status 再改，唯一受控逆转换见 reopen」；`sdflow-retro/SKILL.md` 补聚合④实修率段与 per-change tokens 列的一句说明【R-IS1】【R-WR1】【R-WR2】

## 测试覆盖图（TG-18）

```
code path                                  测试类型                    落点
─────────────────────────────────────────────────────────────────────────────
issues_v2.py reopen（守卫/迁移/reindex） → 契约测试（往返+拒绝面）    sdflow-issues/tests/
set-status 既有守卫                      → 回归（全量既有用例）       sdflow-issues/tests/
retro 窄文法提取 + 聚合④                → 单元（合成语料）+ 冒烟     sdflow-retro/scripts/tests/
retro token join + tokens 列             → 单元（合成 jsonl）+ 冒烟   sdflow-retro/scripts/tests/
token_snapshot.py + checkpoint 接线      → 沙盒集成（假 HOME 真跑）   hack/tests/
setup.sh 分发后真实链路                  → dogfood（本 change 自证）  任务 3.4
```
