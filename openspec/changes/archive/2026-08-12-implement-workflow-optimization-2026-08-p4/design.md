# Design · implement-workflow-optimization-2026-08-p4

## Context

动机见 `proposal.md · Why`。与本设计相关的现状机制（均实查核验）：

- **档位解析单维**：`model-tiers.md` 机读块 `model-tier-defaults` 固定 6 键（2 机队 × 3 档），
  `resolve-models.sh` 行锚定提取、经 `printf %q` 导出 `SDFLOW_HOST` + 三个 `SDFLOW_TIER_*`
  （eval 契约）；消费仓覆盖走 `openspec/config.yaml` `model-tiers.{claude,codex}.{strong,mid,light}`
  有界键路径解析（`resolve-models.sh:105-174`，与 `init.py::_model_tiers_from_dict` 同口径
  `[spec-review-amendment]`：原引用名 `_parse_model_tiers_block` 不存在，接地镜核验修正）。
- **effort 原语**：宿主只在 agent 定义 frontmatter 层支持 `effort:`（Agent 派发 per-call 参数
  仅 `model`）；本仓 `sdflow-spec/agents/*.md` 已实用（`effort: low/medium`）。
- **镜 prompt 组装**：散文契约驱动（`sdflow-code-review/SKILL.md:310-335`），通则区块已内联、
  清单由子代理运行时自读 `$RULES_ROOT`；无组装序约定、无 byte-stable 保证。
- **报告机械层**：ship_gate 只读两报告 frontmatter（`ship_gate.py:1783-1800`），不校验
  lens-metric 锚/引用核落盘/defer 台账——B25/B26 的断链面。
- **install_agents**：`setup.sh` 已有逐文件 `ln -snf` + 所有权守卫（readlink 命中自有源才接管）+
  孤儿清理 + 假 HOME 真跑 bash 测试（`hack/tests/test_install_agents.py`）。

## Goals / Non-Goals

**Goals（设计层边界，scope 见 proposal）**：

- effort 维全链一致：机读块 → resolver 导出 → SKILL 派发 → agent 定义，四层同一单一源推导，
  任何一层缺席都按既有降级语义如实告警，不静默。
- 段① 稳定前缀 byte-stable 是**可测断言**（golden test），不是散文承诺。
- B25/B26 门是**消费点机械门**（ship_gate），不是被监管方自报。

**Non-Goals（设计层）**：

- 不给 emitter/anchor_lint/引用核增加新功能——只恢复调用与落盘、加存在性门。
- 不改 lens-metric contract 的锚 schema 与合法组合矩阵。
- 不动 `sdflow-spec/agents/` 三个既有角色定义。
- proposal 级 Non-Goals 照抄生效（不回填 / 不动编排大改 / 不碰裁决协议与 roster 等）。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。
机制类决策的 ADR：[`openspec/adr/0043`](../../adr/0043-effort-tiering-via-global-effort-keyed-agents.md)
（effort 分档经全局 effort-keyed agent 定义，TG-23）。

设计层细化（决策纪要之下的实现形态，实施可在等价范围内微调）：

- **effort 机读块**：`model-tiers.md` 新增独立 fence `effort-tier-defaults`，键路径
  `claude.{strong,mid,light}: {high,medium,low}`（**仅 claude 机队**——codex 无对应物，
  不写键即 n/a，杜绝「空值语义」）；`resolve-models.sh` 同款行锚定提取，导出
  `SDFLOW_EFFORT_{STRONG,MID,LIGHT}`（codex/unknown 宿主导出空值 + 注释性告警不阻断）。
- **config 覆盖**：`openspec/config.yaml` 新段 `effort-tiers.claude.{strong,mid,light}`，
  解析复用 model-tiers 段的有界键路径 idiom；值域校验 ∈ {low,medium,high,xhigh,max}，
  非法值忽略覆盖回落缺省 + 告警（与 model 覆盖同语义）。
- **agent 定义内容**：每个 `sdflow-effort-<E>.md` = frontmatter（`name` / `description`
  排他式声明「仅由 sdflow 编排 SKILL 派发选用」/ `model: inherit` / `effort: <E>`）+ 一行
  正文说明。无 tools 限制（工具面由派发 prompt 约束，与现行镜派发一致）。
- **SKILL 派发条款**：各编排 SKILL 的镜/步表格增「effort 档」列，派发时
  `subagent_type: sdflow-effort-$SDFLOW_EFFORT_<该步档位>`；`$SDFLOW_EFFORT_*` 为空
  （codex/unknown/未升级 resolver）⇒ **不带 subagent_type，行为与今天完全相同**（前向兼容，
  pull/setup 窗口期安全）。
- **render-review-prefix.sh**：落 `sdflow-init/assets/hack/`（setup 装 `~/.sdflow/hack/`，
  与既有 hack 脚本同布署链）；`--layer code-review|spec-review`；输出 = 按固定序 cat
  通则区块（`~/.sdflow/hack/skill-principles.md`）+ 通用契约段（脚本内嵌 heredoc，含 T103
  封顶句）+ base checklist（`$RULES_ROOT` 解析）；任一源缺失 ⇒ fail-loud 非零退出
  （评审 SKILL 按既有降级条款处置，MUST NOT 半段前缀继续）。
- **ship_gate 两道新门**：挂在现有 code-review 报告判定函数内（`ship_gate.py:1783` 起的
  消费点）：① `metrics.enabled=true`（读 config——复用 `_yq()` 非 frontmatter file 模式，
  MUST NOT 引入 yaml import；**config.yaml 文件不存在 / `metrics:` 在而 `enabled` 键缺失 =
  同缺省放行**，实现先判文件存在性再调 `_yq`——`_yq()` 对缺文件裸 raise，不判则误落
  fail-closed `[spec-review-amendment]`；仅 yq 非零退出 = 不可解析 ⇒ fail-closed 报
  problem+cause+fix）∧ 报告缺 `sdflow:lens-metric layer="code-review"` 锚行或缺
  `sdflow:ref-check` 结构化锚（status + pass/fail/uncheckable 计数，由评审 SKILL Step3 落盘，
  gate 检测锚而非段标题/散文——「标题存在」形同虚设、「[ref-check] 行存在」误伤零裁掉报告，
  两头都不可判 `[spec-review-amendment]`）⇒ 判「该步进行中，重跑」；② defer 台账行缺
  `T\d+|B\d+` id、或 `openspec/issues/open/**/<id>.md` 文件系统不存在、或池文件 frontmatter
  `source_change` ≠ 当前 change 名（防误抄既有票号假绿；defer 台账只承载本轮新入池项，
  既有票引用写裁决说明不入台账 `[spec-review-amendment]`）⇒ 同前处置。
  **台账行判别窄化 `[spec-review-amendment]`**：台账行 = 表格数据行，id 取专用 id 列且单元格
  全部内容 = 单个 id——MUST NOT 全行子串搜索（现模板聚合摘要句含 "defer" 字面无 id 会恒假阳，
  描述列提及的 T105 等真实旧票号会假阴误抓，[[gate-substring-detection-dogfood]] 同族双向坑）；
  SKILL 报告模板的聚合摘要句同步改写移出检测范围。fence-aware 解析复用 ship_gate 既有口径。
  两门失败输出按根因分诊四类 cause 文案（缺 lens-metric 锚/缺 ref-check 锚/defer 无 id/池文件
  缺失或 change 不符），verdict **字面复用 `STEP_IN_PROGRESS`** 不新增名（sdflow-ship 熔断按
  verdict 字面分治，新名绕开熔断 = 无限重跑 `[spec-review-amendment]`）。spec-review 报告在
  design 门读取处加同款 ①，其失败指引提示转换态（metrics 在报告写就后翻 true ⇒ 重跑该层评审
  或人工处置 `[spec-review-amendment]`）。

## 组件清单（BASE-25，TG-14）

| 组件 | 新/改 | 落点 | 消费方 |
|---|---|---|---|
| `effort-tier-defaults` 机读块 | 新 | `sdflow-init/assets/workflow/model-tiers.md` | resolve-models.sh |
| `SDFLOW_EFFORT_*` 导出 | 改 | `sdflow-init/assets/hack/resolve-models.sh` | 4 个编排 SKILL |
| `effort-tiers` config 段 | 新 | 消费仓 `openspec/config.yaml`（模板：bundle config.template） | resolve-models.sh |
| `sdflow-effort-{low,medium,high,xhigh,max}.md` | 新 | `sdflow-spec/agents/`（设计门拍板 Q2=C：复用既有源目录，铺设/守卫/孤儿清理/manifest/测试自动覆盖新增 `.md`，零改守卫 `[spec-review-amendment]`）→ `~/.claude/agents/` | 宿主 subagent_type |
| `install_agents` | 不改 | `setup.sh` 守卫/manifest 零改动（Q2=C）；仅 `hack/tests/` 加 effort 定义专项断言 + CLAUDE.md/design 对该目录的描述同步 + 目录内一行注记 `[spec-review-amendment]` | 布署链 |
| `render-review-prefix.sh` | 新 | `sdflow-init/assets/hack/` → `~/.sdflow/hack/` | 两评审 SKILL 段① |
| ship_gate B25/B26 门 | 改 | `sdflow-ship/scripts/ship_gate.py` | ship 链 / Stop hook |
| 派发条款（effort 列 + 三段组装序 + defer 当场入池） | 改 | 4 个编排 SKILL.md | 运行时 |
| 测试群 | 新/改 | 各 skill `tests/` + `hack/tests/` | pytest |

## 依赖图

```
model-tiers.md ──(机读块×2)──▶ resolve-models.sh ──(eval 六+三变量)──▶ 编排 SKILL 派发
     ▲                              ▲                                      │
     │ config.template              │ config.yaml effort-tiers 覆盖         │ subagent_type
     │ (sdflow-init update 推下游)   │                                      ▼
     └── bundle 权威源            消费仓                        ~/.claude/agents/sdflow-effort-*
                                                                    ▲
skill-principles.md ─┐                                              │ setup.sh install_agents
$RULES_ROOT/checklists ─┼──▶ render-review-prefix.sh ──▶ 段①前缀 ──▶ 镜 dispatch prompt
（通用契约段内嵌）───┘                                    （段②③ SKILL 组装）
                                                                    │
评审报告（lens-metric 锚 + 引用核段 + defer id 台账）◀──────────────┘
     │
     ▼
ship_gate（B25 锚存在门 + B26 defer 对账门 + 既有 frontmatter 门）──▶ RUN_VERIFY / 重跑
```

### B26 defer 入池回路时序（TG-10，跨 SKILL / recorder / gate 三组件）`[spec-review-amendment]`

```
code-review Step4          recorder(issues_v2)         报告文件                ship_gate
     │ 裁决=defer               │                        │                      │
     ├─ add --source-change ──▶│                        │                      │
     │                          ├─ 写池文件+git add      │                      │
     │◀── 返回 id（exit 0）─────┤                        │                      │
     ├─ id 写台账行 ───────────────────────────────────▶│                      │
     │                          │                        │                      │
     │  〔recorder exit≠0〕      │                        │                      │
     ├─ fail-loud：不写「已入池」，报告记失败+待补录 ────▶│                      │
     │                          │                        │                      │
     │                          │      〔gate 在 commit 前跑〕                   │
     │                          │                        │◀── 读台账行 id ──────┤
     │                          │        池文件文件系统存在 ∧ source_change 对账 ──┤
     │                          │                        │   任一不满足 ⇒ STEP_IN_PROGRESS
```

## 协议文档套件 scope-check 表（BASE-29，TG-25）

model-tiers 机读契约扩维牵连的文档组（改一处必查全组，防 [[deployed-copy-drift]]）：

| 文档 | 须同步内容 |
|---|---|
| `model-tiers.md` 表格 + 机读块 | effort 列 + `effort-tier-defaults` fence（两处 MUST NOT 漂移） |
| `resolve-models.sh` 头注释 | 导出变量清单 6→9 |
| bundle `config.template` / `claude-section.md` | effort-tiers 覆盖段示例与说明 |
| 4 个编排 SKILL 派发段 | effort 列引用（一句指向 model-tiers.md，MUST NOT 内联值） |
| `CLAUDE.md`/`AGENTS.md` 托管区块 | 若提及档位机制则同步（经 sync/init 工具，勿手改托管块） |
| `hack/tests/` + 各 tests/ | 契约测试同步 |
| `anchor_lint.py::_metrics_enabled` ↔ ship_gate B25 门新读取点 | `metrics.enabled` 四态语义两处独立实现，改一处必查另一处 + 一致性测试 `[spec-review-amendment]` |
| `init.py::lint_config` ↔ `effort-tiers` 新键 | 新 config 键接入 lint 结构/值域校验，与 resolver 解析同口径 `[spec-review-amendment]` |

## Risks / Trade-offs

- [A1：frontmatter effort 对 subagent_type 派发未在镜场景实测] → 实现首票先做最小实测
  （effort=low 探针对比输出规模）；失效 ⇒ 面 A 止损重估（memo K1 的备选路径均已记录）。
- [gate 新门假阳：报告在 fence 内讨论锚自身] → 复用 ship_gate 既有 fence-aware 解析口径
  （[[gate-substring-detection-dogfood]] 前科的既有修法）。
- [config 读取双态坑：缺失=放行 vs 存在坏=fail-closed] → 双向测试显式覆盖
  （[[dogfood-blind-spot-source-config]]）。
- [pull/setup 窗口：新 SKILL 条款先于 agent 定义就位] → 派发条款设计为 `$SDFLOW_EFFORT_*`
  空值即完全回落现行为（前向兼容），窗口期零破坏。
- [bundle 权威源改动忘回灌 / 只改部署副本] → 全部 bundle 改动落 `sdflow-init/assets/`
  权威源，scope-check 表复查（[[deployed-copy-drift-surfaces-only-on-update]]）。
- [B26 门与评审 session 写池的时序：gate 在 commit 前跑，池文件未 add] → 门用文件系统存在
  判定，不走 git ls-files（[[tracked-file-guard-blind-to-uncommitted]]）。
- [段① 内嵌通用契约段与 SKILL 散文重复漂移] → 契约段唯一源在脚本 heredoc，SKILL 对应段落
  改为一句引用（同「勿内联模型名」idiom）。

## Migration Plan

0. **实现期自审窗口 `[spec-review-amendment]`**：本 change 自身 code-review/verify 触发前，
   在**开发 checkout** 跑一次 `bash setup.sh`（CLAUDE.md「全局窗口层」时间盒操作）——否则
   `~/.claude/skills/sdflow-ship` 等软链仍指运行 checkout，自审跑的是**旧 gate（无 B25/B26 门）
   与旧 SKILL**，「dogfood 自证」不成立且可能产出第 7 个缺锚样本（对抗镜机器实测）。自审完毕
   按既有纪律回运行 checkout 重跑 setup 还原。
1. 实现合并 main 后：运行 checkout `git pull` + **立即** `bash setup.sh`（新 agent 定义 +
   新 hack 脚本 + resolver 升级一次就位；既有发布边界纪律）。
2. 消费仓：各仓下次 `sdflow-init update` 拿到 model-tiers/config.template 新块；未 update
   期间 resolver 读旧块 ⇒ `$SDFLOW_EFFORT_*` 空 ⇒ 行为不变。
3. 回滚：revert 本 change → 删 `agents/` 源目录后在运行 checkout 重跑 `bash setup.sh`
   （孤儿清理撤软链；顺序不可颠倒，同 CLAUDE.md「移除 agents」既有纪律）；ship_gate 门随
   revert 消失，无独立回滚步。

## Open Questions

- Q1（同 proposal）：B25 直接成因（emitter 未调用 vs 调用失败未记录）——修复票内诊断定案；
  门的设计对两种成因同等有效，故可安全后置，不影响 specs/任务拆分。
- Q2 **已拍板（设计门 2026-08-12，选项 C）**`[spec-review-amendment]`：effort agent 定义
  直接放进既有 `sdflow-spec/agents/`——铺设/守卫/孤儿清理/manifest/测试全按「目录下全部
  .md」工作（`test_install_agents.py:39` 明示新增定义自动纳入），零改 🔴 守卫段；已接受
  代价 = 目录语义错位（文档同步 + 目录内注记，随 tasks 2.4）与 sdflow-spec 退役时的回滚
  耦合（低概率，删前挪走即可）。备选 A（泛化多源 + manifest union）留待未来第三组定义出现。
- Q3 **已拍板（设计门 2026-08-12，选项 B）**`[spec-review-amendment]`：补第 5 个
  `sdflow-effort-max` 定义，值域 {low,medium,high,xhigh,max} 与资产一致，消除「值合法但
  资产未铺」的无文案第三态——与 memo D1「max 进值域留逃生口」拍板一致；max 仍不进缺省映射。

## Compliance

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文只写最终态，无演进史。
- 遵守基准 5：机读块/config 解析均为有界键路径行锚定，MUST NOT 长成通用解析器；gate 判定
  不解析 Markdown 语义，只做行锚定 + fence 口径。
- 遵守「SKILL.md 禁静态内联」（T124 拍板）与「MUST NOT 内联模型名/effort 值」（ADR-1 同构）。
- 通则托管块（`sdflow:principles`）不手改；如需动通则走 `sync_principles.py`——本 change
  不改通则内容，仅由脚本 cat 其产物文件。
