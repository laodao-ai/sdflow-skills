# add-sdflow-spec · Tasks

> 任务 ↔ 需求双向追溯：每任务尾标 〔SA-xx〕；SA-01~SA-10 全部被至少一个任务覆盖。
> checkpoint slug 格式：`task<N>-<desc>`（含横杠，防 TAG_RE 不匹配）。

## 1. agent 定义与托管机制（P0）

- [ ] 1.1 编写 `sdflow-spec/agents/sdflow-researcher.md`：frontmatter（`model: inherit`、`effort: low`、`tools: Read, Glob, Grep, Bash, WebFetch, WebSearch`）+ 正文角色纪律（只读供证、仓内结论+file:line / 联网结论+URL 出处、材料不回传）+ 通则托管块占位 〔SA-07, SA-02〕
- [ ] 1.2 编写 `sdflow-spec/agents/sdflow-spec-writer.md`：frontmatter（`model: inherit`、`effort: medium`、`tools: Read, Glob, Grep, Bash, Write`）+ 正文（四件套单产物生成、自调 `openspec instructions`、读依赖产物、禁 AskUserQuestion）+ 通则托管块占位 〔SA-07, SA-05〕
- [ ] 1.3 `hack/sync_principles.py`：agent 定义纳入投放面（skill 味源渲染进两个 agents 文件），跑 `--apply` 落块 〔SA-07〕
- [ ] 1.4 `hack/tests/test_sync_principles.py`：守卫覆盖 agents 文件（块存在、与源一致、HEADLINES 四子串），跑 `/usr/bin/python3 -m pytest hack/tests/` 全绿 〔SA-07〕
- [ ] 1.5 `setup.sh`：新增 agents 铺设段（`sdflow-spec/agents/*.md` → `~/.claude/agents/`，symlink + 所有权守卫 + 孤儿清理，对齐 `install_into` 模式）；开发 checkout 跑 `setup.sh` 验证铺设与 `--check` 门 〔SA-07〕

## 2. SKILL.md 管线本体（P0）

- [ ] 2.1 编写 `sdflow-spec/SKILL.md` frontmatter（name/description 触发面、`disable-model-invocation: true`）+ 通则托管块（纳入 sync 投放面，重跑 `--apply`/`--check`）〔SA-01〕
- [ ] 2.2 相位 A 澄清指令：grilling 节奏（一次一问/附推荐/事实自查）、openspec CLI 起手上下文核查、外派阈值、提前收束判据（B 不可跳过）〔SA-01, SA-02, SA-03〕
- [ ] 2.3 相位 B 拷问指令：锚点纪要主 session 亲笔（对话内呈现）、承重约束优先攻击、停止信号（共识+约束站稳）、B 收敛节点（FF-0 → `openspec new change` → 亲笔 `decision-memo.md` 落盘 → checkpoint）、决策纪要字段、ADR/术语惰性提议钩子（三条件判据 + 最小模板）〔SA-03, SA-04, SA-10〕
- [ ] 2.4 相位 C 生成指令：起手核验 `decision-memo.md` → status 依赖序串行派 spec-writer（纪要下发 + 自取 instructions + 自读依赖）→ 写后核验 → 终审（纪要↔产物一致性，判断改/措辞放过）→ 纪要并入 design.md 决策记录 〔SA-05, SA-06, SA-04〕
- [ ] 2.5 dispatch 契约段：`agentType` 优先 + `$SDFLOW_TIER_*` 档位变量（`resolve-models.sh` eval 一次）+ fallback prompt 内联通则；降级阶梯（亲查/重试一次后亲写/CLI fail-closed/Codex 整体降级）+ 如实报告与可重入 〔SA-07, SA-08〕
- [ ] 2.6 出口序列段：原样贴 `/clear → 换档 → /sdflow-spec-review` 三步 + 产/审错档一句理由；相位 checkpoint 节点（B 收敛、C 终审后；拷问中途禁提交）〔SA-09〕

## 3. 本仓规范与文档（P1）

- [ ] 3.1 阶段一规范双通道改写 [grill-amendment]：①归属修正改真相源 `sdflow-init/assets/snippets/claude-section.md`（「grill-with-docs 来自 superpowers 插件」→ Matt Pocock skills 集合 `~/.agents/skills`），经托管机制刷新本仓 CLAUDE.md/AGENTS.md 区块（MUST NOT 手改块内）；②本仓 CLAUDE.md/AGENTS.md **非托管区**新增 `sdflow-spec` 使用路径 + 出口序列约定 + 三个原 skill 保留与适用场景；托管块「ff 之后是 grill」保留不动（管旧路径，下游推广另 change）〔SA-09〕
- [ ] 3.2 README「Skills 列表」新增 sdflow-spec；重跑 `setup.sh` 建链接并验证双 runtime 可见 〔SA-01〕

## 4. 验证（P0/P2）

- [ ] 4.1 机械层全量：`/usr/bin/python3 -m pytest` 仓根全绿（含新守卫）；`setup.sh` 幂等重跑无 skipped 异常 〔SA-07〕
- [ ] 4.2 派发链路冒烟：真派一次 `agentType: sdflow-researcher`（trivial 检索任务）验证 agent 定义 + 档位变量覆盖生效；失败则按 fallback 路径验证并在报告记录（对应 proposal 假设①的实测闭环）〔SA-07, SA-08〕
- [ ] 4.3 dogfood 演练（轻量）：对一个小型真实需求跑通 A→B→C 全程，核验：B 不可跳过、纪要字段完整、四件套 status 全 done、终审记录、出口序列原样呈现、checkpoint 锚落盘 〔SA-01, SA-04, SA-05, SA-06, SA-09〕
- [ ] 4.4 /clear 无损抽检：dogfood change 上 `/clear` 后模拟阶段二冷读产物，确认决策 why（含砍掉候选）全部可得 〔SA-04〕

## 测试覆盖图〔TG-18〕

| code path | 测试类型 |
|---|---|
| sync_principles 投放面（agents 块渲染/漂移） | pytest（hack/tests，机械守卫） |
| setup.sh agents 铺设/孤儿清理/幂等 | 脚本实跑核验（4.1） |
| agentType 派发 + 档位覆盖 + fallback | 冒烟实测（4.2） |
| 三相位管线行为（SA-01~06, 09, 10） | dogfood 演练 + 抽检（4.3/4.4，行为层人核） |
| openspec CLI fail-closed / 可重入 | dogfood 中按 status 对账核验（4.3） |
