# tasks — implement-workflow-optimization-2026-08-p1

> Requirement ID 对照：R-IS1 = issues-scripts-shared-core「reopen 命令契约」；
> R-WR1 = workflow-retro「per-镜实修率历史回算」；R-WR2 = workflow-retro「per-change token 维 join」；
> R-TS1/2/3 = token-snapshot-anchor「采集与同 commit 入库」/「失败降级」/「只追加无状态」。

## 1. recorder reopen 命令（R-IS1，P0）

- [ ] 1.1 `issues_v2.py` 新增 `reopen` 子命令：守卫（closed/ 限定、pool/前缀一致、--reason 必填）、状态（默认 OPEN，--to 非终态白名单）、字段清理（三终态字段→null，原 closed_reason 进历史行）、M-2 原子序（closed/ 原位原子写 → git mv 回 open/）、命令内自动 reindex；复用 `sdflow_issues_core` 既有 mechanics，MUST NOT 改 set-status 守卫【R-IS1】
- [ ] 1.2 契约测试：往返（add→终态→reopen→字段/目录/INDEX/CLOSED 全一致）、拒绝面三例（open 项 / 缺 reason / --to 终态值，均验「文件与索引零变更」）、既有守卫零回归（set-status 对 closed/ 仍拒 + 全量 `sdflow-issues/tests/` 绿）【R-IS1】

## 2. 实修率历史回算（R-WR1，P0）

- [ ] 2.1 `retro_report.py` 窄文法提取：`已修[impl-review-fix]` 精确 needle + 封闭 lens 关键词表（LENS_ENUM 同源六值映射，同行含「来源」列匹配，0/多命中→未知桶）；复用 `LMA._fence_aware_lines` 滤围栏示范锚【R-WR1】
- [ ] 2.2 聚合④段渲染：per-(layer,lens) 实修数/可判定/未知/覆盖率/实修率 + 阈值 5 单一源常量（<5 标「参考」）+ change 边界修复 commit 佐证 flag（不参与判定）【R-WR1】
- [ ] 2.3 测试：合成语料用例（可判定 / lens 歧义 / 零命中 / 围栏内示范锚不入计）+ 真仓再生冒烟（聚合④在场、13 面待复评镜实修率或「参考」可读）【R-WR1】

## 3. token 快照采集（R-TS1/TS2/TS3，P1）

- [ ] 3.1 新增 `sdflow-init/assets/hack/token_snapshot.py`（4 行 reconfigure 前导）：transcript 定位序（`$CLAUDE_CODE_SESSION_ID` 精确命中 → munged-cwd 目录 mtime 最新回退 → 无则 `no-transcript` 降级行）、usage 四计数+messages 累加、change 目录由分支名解析（无落点静默跳过）、追加 v1 行 schema 到 token-log.jsonl；全程 try/except 到降级行【R-TS1】【R-TS2】【R-TS3】
- [ ] 3.2 `sdflow-init/assets/hack/checkpoint-commit.sh` 在 `git add -A` 前接线 `python3 ~/.sdflow/hack/token_snapshot.py --step "$step" || true`（真相源在 assets，MUST NOT 直改 `~/.sdflow/hack/` 副本）【R-TS1】【R-TS2】
- [ ] 3.3 `hack/tests/` 假 HOME 沙盒真跑 bash：正常采集入同一 commit / 无 transcript 写 `no-transcript` 行 / helper 缺席与崩溃时 checkpoint 照常提交 / 无 change 落点零写入 / 连续 checkpoint 只追加且累计单调不减【R-TS1】【R-TS2】【R-TS3】
- [ ] 3.4 重跑 `bash setup.sh` 分发，dogfood 验收：本 change 的下一次真实 checkpoint 产出 anchor=true 快照行（roadmap 验收标准「跑一次真实 checkpoint 验证」）【R-TS1】

## 4. retro token 列（R-WR2，P2，依赖任务 3 落锚）

- [ ] 4.1 `retro_report.py` 读 token-log.jsonl：session 分组、组内相邻 anchor=true 行差分归后行 step（attribute-to-next）、session 首行全额计入、anchor=false 行不入计数【R-WR2】
- [ ] 4.2 per-change 表 tokens 列渲染：out/in/cw/cr 四计数紧凑串、MUST NOT 合成总分、无锚显「—」【R-WR2】
- [ ] 4.3 测试：合成 token-log 用例（多 session / 降级行 / 缺文件）+ 全仓再生冒烟（存量 change 全「—」不崩）【R-WR2】

## 5. 收尾

- [ ] 5.1 全仓 pytest 绿（`/usr/bin/python3 -m pytest`）+ `openspec/retro/report.md` 再生提交（含聚合④与 tokens 列）
- [ ] 5.2 roadmap `task-log.md` 追加 1.B 交付记录；CONTEXT.md「实修率」词条按用户拍板结果处置（未确认 MUST NOT 写入）

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
