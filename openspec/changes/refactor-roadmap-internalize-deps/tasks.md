# Tasks: refactor-roadmap-internalize-deps

> 任务 ↔ Requirement 双向追溯：每条任务尾部〔〕内为 roadmap-planning delta 的 Requirement 名
> （A=ADDED / M=MODIFIED / R=REMOVED）；无标注 = 治理/验证类，无对应 spec 行为。

## 1. SKILL.md 重写（P0）

- [ ] 1.1 重写 frontmatter description：触发面去 wayfinder/footage，保留「先 `/sdflow-architecture`」指路句与前置条件（存活验证：description 文本含指路句）〔新项目起步的架构先行指路（不变，防重写丢失）〕
- [ ] 1.2 写三相位总览 + 三态路由节：gate-0 与商业化信号两关独立、三态图、判定点①显式留痕、explore 上游指路一句〔A·讨论层三态路由〕
- [ ] 1.3 写相位 B 节：起手**三步**（定名 → create/continue/replan 前移判定 → 建目录 + 草稿 memo 含 `状态：DRAFT`）、七维拷问与裁剪表（词表内联，含操作者覆盖口）、术语/ADR 提议制（**确认后先记 memo、终稿后才写全局**，`[提议]`/`[确认]` 固定前缀 + 目标路径 + 条目名 + 版本锚）、增量落盘、**停止条件（每个选入维度落 已决/显式延后/不适用 三态之一）**、重入协议、放弃清理（create 删目录**并先复述路径** / **continue·replan 不自动删、只记 task-log**）〔A·B 相位拷问与增量落盘 · SR-2/5/6/9/10/11/39/41〕
      🔴 **重入探测 SHALL 提到独立的「第零步」标题、置于三态路由之前**——与 `sdflow-spec` 同构；埋在 B 相位长节子项里会被线性执行的 agent 跳过〔spec-review-amendment SR-36〕
- [ ] 1.4 写相位 C 生成节：三件套直写（改「结晶」→「生成」全文）、包生命周期条款改判定时点（B 起手 / 直接生成路径落盘前）、近细远雾节改术语〔M·三件套直写产出 / M·roadmap.md 近细远雾分层〕
- [ ] 1.5 写历史存档节：定义（memo + 存量 footage 统称）、规则 3 改写、存量 footage 冻结条款（一行提示）、陷阱 3 改写〔A·历史存档引用边界与存量 footage 冻结〕
- [ ] 1.6 写 review 分档节（术语改「商业化信号」，契约原样）+ 收尾 checklist 四项（③ 覆盖历史存档、④ memo 对账含诚实边界声明）+ 判定点②③留痕〔A·review 按商业化信号分档 / M·收尾 checklist 软门〕
- [ ] 1.7 删除 wayfinder 全部机械：三分支路由节、footage 节、map 再入、tracker preflight、基线记录、原 checklist ④、陷阱 7、路由对照表重写为三态版〔R·讨论层按规模分档路由 / R·footage 落盘位置与引用边界〕
- [ ] 1.8 核验 `sdflow:principles` 托管块零字节未动（重写以「块外全重写、块内不动」执行）。核过：本文件仅 **1 个**区块（`:15`–`:154`），`sync_principles.py` 的多区块坑不适用
- [ ] 1.9 **清理「保留」节里内嵌的待删机制**〔spec-review-amendment SR-7〕——骨架标「保留/只改 X」的节里嵌着 wayfinder/footage 引用，逐处处置：
      · `:199` 规则 1 —— 删「长讨论的 footage 落 `…/footage/`」半句
      · `:227` 规则 5 —— 删 wayfinder 铺图期 Task 票整条子条款
      · `:511` 命名规范 —— 删「（如走长档）footage map 头部 `Tracker root:` 字段的锚」
      · `:525` 下游阶段实施 —— fallback 三例外里的「需 wayfinder 跨会话铺图」改中性表述或降为两例外
      · `:546` 陷阱 1 —— 「先进讨论层**三分支路由**」改「进相位 B 拷问」
      · `:603` CLAUDE.md 配合 —— **只删分号后的 footage 子句，保留前半句目录说明建议**（消歧）
      · `:618` 参考模板 —— 「memo 可选、长档由 footage 取代」与 D9（memo 升格为 B 相位唯一载体）矛盾，改写
- [ ] 1.10 **「实战案例：博客 v2 重建」（`:624-635`）显式处置**〔spec-review-amendment SR-24〕——建议**删除**（按 DOC-1，它是正文里的考古层：自述「彼时结构…现行流程见上文」）；同步删除规则 1（`:201`）与陷阱 4（`:568`）里指向该案例的括注旁证，避免留下指向真空的孤证。**MUST NOT 静默丢弃**——留或删都要在实现记录里写一句

## 2. references 模板（P1）

- [ ] 2.1 重写 memo-template.md：B 相位纪要模板（头部包名+日期，承重结论/拍板决策小节，历史存档定位声明）〔A·B 相位拷问与增量落盘〕
- [ ] 2.2 design/roadmap/task-log 三模板术语改（商业化信号 ×2、生成、历史存档），结构不动〔M·roadmap.md 近细远雾分层〕
- [ ] 2.3 long-flow-skill-paradigm.md 的 wayfinder/footage 段落改历史注记

## 3. matt 移除（P1）

- [ ] 3.1 删除 `openspec/matt/` 整目录（4 文件）
- [ ] 3.2 CLAUDE.md 与 AGENTS.md：删 matt 三区块（Issue tracker / Triage labels / Domain docs），roadmaps 目录描述行去 footage 措辞（两文件同步改）

## 4. bundle 同步（P1）

- [ ] 4.1 `ff-generation-constraints.md`：`wayfinder-resolved:` 前缀规则保留 + 加 legacy 标注〔R·footage 落盘位置与引用边界 · Migration〕
- [ ] 4.2 `workflow-history.md` 追加一条 wayfinder 路径移除记录
- [ ] 4.3 `config.template.yaml`：`:41`/`:51` 两行注入规则引用的「wayfinder→ff 衔接契约」章节在当前 `ff-generation-constraints.md` 中已不存在（既存陈旧引用），随本次一并订正——该文件是消费仓 `config.yaml` 的**生成模版**，改动会随 init 注入每个新下游仓〔spec-review-amendment SR-13〕
- [ ] 4.4 dev checkout 跑 `bash setup.sh`（bundle 改动生效纪律）。**验收动作 = 单独跑 `python3 hack/sync_principles.py --check` 看 exit code**——`setup.sh` 里那一处是 `if ! …; then echo "⚠️…"; fi`，**不是 fail-closed 门**（`set -e` 在 `if` 条件里不生效），警告会淹没在大段输出里〔SR-17 附带〕
- [ ] 4.5 **hand-off 记录还原步**：合并后须在运行 checkout（`~/.skills/sdflow-skills`）重跑 `setup.sh` 还原（`/sdflow-upgrade`）——CLAUDE.md 的 dev/runtime checkout 纪律明文要求，5 个历史同类 change 的 tasks 均有此步，本 change 原缺〔spec-review-amendment SR-17〕

## 5. 治理收尾（P2）

- [ ] 5.1 新增 ADR：讨论层内化与 matt 套件移除（权衡：内化分界线——讨论过程内在职责 vs 冷审外部性）。**格式**：参照 `openspec/adr/` 现有 36 个文件的命名规则（4 位零填充序号 + kebab-case 标题），取下一个可用编号 `0037-`；无 template 文件，小节结构从现有 ADR 归纳〔spec-review-amendment SR-37〕
- [ ] 5.2 CONTEXT.md 词条**三处**〔spec-review-amendment SR-15〕：① footage 词条重写为「历史存档」定义（其正文含「决策**结晶**」，一并改「生成」）；② 新增「商业化信号」词条；③ **`ticket（实现分解单位）` 词条**——正文「matt 套件中 wayfinder 的讨论 ticket（map 的 `issues/<NN>`）是另一种 ticket，需限定词区分」与 `_Avoid_` 行的同类表述，改为历史存档语境（「matt 套件已移除；存量冻结 footage 中的历史讨论票沿用该定义」）
- [ ] 5.3 T134 关 **`WONTDO`** + **`--reason`**（前提消解：重构后本仓工作流无 domain-modeling 调用点）。用本仓 `sdflow-issues/scripts/`，勿用全局 symlink 旧版。🔴 **`OBSOLETE` 不是合法状态码**——`issues_v2.py:46-49` 的 todo 池只接受 `OPEN|PROPOSED|DONE|WONTDO`，且 `--evidence` 只服务 `FIXED`/`DONE`、`WONTDO` 必须配 `--reason`〔spec-review-amendment SR-3，实跑复现〕
- [ ] 5.4 更新 `docs/external-dependencies.md`：删 §5 Wayfinder 依赖节，**并同步 §8「内部跨 Skill 依赖」的依赖图**（`:148` 仍有 `/grilling、/domain-modeling`）；gstack review 节保留〔spec-review-amendment SR-14〕
- [ ] 5.5 `openspec/INDEX.md:52` roadmap-planning 摘要行**整句重写**（非局部替词）——该行完整描述了「双判据路由（explore/wayfinder/office-hours）」「footage 落盘（含票状态机 open/claimed/resolved/abandoned）」「按野心分档」「checklist 五项软门（含 wayfinder 闭环）」，须按新结构（三态路由 / 历史存档 / checklist 四项）改写〔spec-review-amendment SR-29〕
- [ ] 5.6 更新 `docs/sdflow-fable5/02-module-reference.md` §4.6——该文件 `:6` **自述「本文是活文档（非冻结快照）」**，不属 Non-Goals 豁免的 docs/ 历史文档，而其 §4.6 用现在时描述 wayfinder footage 与野心分档〔spec-review-amendment SR-16〕
- [ ] 5.7 删除 `docs/drafts/roadmap-refactor-handoff.md`（已被本 change 四件套取代）

## 6. 验证〔TG-18〕

- [ ] 6.1 全量 grep 残留扫描（**不带 `--include`**），词表**扩为** `wayfinder|office-hours|grilling|domain-modeling|openspec/matt|footage|三分支路由|Tracker root|结晶|产品/商业野心|野心信号`〔spec-review-amendment SR-7：原词表不含 `footage` 与「三分支路由」，而 SKILL.md `:199`/`:546`/`:603`/`:618` 四处残留恰好只含这两者，机械门 100% 漏检；裸词「野心」改带上下文锚，避免误伤 T227 的同形异义用法〕。
      🔴 **本步不是机械 pass/fail，命中需人工逐条过滤**——实测全仓命中约 103 个文件。白名单改为**规则化描述**：
      ① 凡「考古层」紧邻 DOC-1 / BASE-30 语境者一律排除（覆盖 `openspec/rules/doc-authoring.md`、`CLAUDE.md` 基准区、`T169`，**以及原白名单遗漏的** `sdflow-architecture/references/` ×4、`openspec/adr/0020-*.md`、`openspec/issues/INDEX.md`）；
      ② `sdflow-init/assets/workflow/ff-generation-constraints.md` 的 `wayfinder-resolved:` 前缀规则**显式保留**（D10 拍板，加 legacy 标注即可）；
      ③ `openspec/issues/`（open 与 closed 两态）、`INDEX.md`、`CLOSED.md` 的历史决策引用不改；
      ④ 非归档的**存量活跃** roadmap 包（如 `openspec/roadmaps/issues-triage-2026-08/roadmap.md:256`）按冻结条款不动；
      ⑤ `.claude/settings.local.json` 的 `"office-hours": "name-only"` 是本机工具授权配置，**MUST NOT 改**；
      ⑥ `openspec/changes/archive/`、`openspec/roadmaps/archive/`、本 change 目录、`workflow-history`（演进史）不改；
      ⑦ 🔴 `docs/` **不再整体白名单**——`docs/sdflow-fable5/02-module-reference.md` 自述活文档、须按 5.6 改；仅 `docs/workflow-skills/*`、`docs/drafts/` 等具名历史文档豁免
- [ ] 6.2 `/usr/bin/python3 -m pytest`：**相对 merge-base 无新增失败**（非「全仓绿」）〔spec-review-amendment SR-18〕。🔴 当前 baseline **已有 1 个先于本分支存在的失败**——`hack/tests/test_harden_sdflow_spec_followup_closure.py::test_spec_authoring_requirement_ids_and_resident_identity_are_consistent`（断言 `SA-14` 存在于 `openspec/specs/spec-authoring/spec.md`，实测 grep 0 命中），与本 change 无关，**不在本 change 修复范围**（要修另开 change）。附：全仓 2461 用例、本机 >280s，需后台跑或加长 timeout
- [ ] 6.3 `python3 hack/sync_principles.py --check` 绿（**单独跑看 exit code**，勿依赖 setup.sh 输出里的告警行，见 4.4）
- [ ] 6.4 **构造 fixture 做存量 footage 演练**〔spec-review-amendment SR-4〕：全仓实测**无任何 `footage/` 目录**（`find . -type d -name footage` 零命中），`issues-triage-2026-08/` 只有一个 `roadmap.md` ⇒ 原演练对象**证不到任何冻结分支**，是恒真锚。改为：临时复制一个存量包 + 手工造 `footage/map.md` 与一张 `footage/issues/01-*.md`（`open` 状态），跑 续跑 / 重入 / 收尾 三条路径，断言：不报错、不迁移文件、不新增票、未决票不阻塞收尾、至多一行冻结提示。演练后删除临时包〔A·历史存档引用边界与存量 footage 冻结〕
- [ ] 6.5 **缺件存量包演练**〔spec-review-amendment SR-25〕：对真实的单文件包 `openspec/roadmaps/issues-triage-2026-08/`（只有 `roadmap.md`）走一次 continue 判定，确认不报错、收尾 ② 对缺失文件判「不适用」而非「不通过」
- [ ] 6.6 **「保留」节逐句核对**〔spec-review-amendment SR-7〕：对新 SKILL.md 中骨架标注为「保留」的每一节（命名规范 / 下游阶段实施 / 参考模板 / 硬性规则 1·5 / 常见陷阱 1 / CLAUDE.md 配合），逐句确认无指向已删机制的残留引用——已知 7 处见 spec-review-report.md SR-7 表
- [ ] 6.7 `openspec validate refactor-roadmap-internalize-deps --strict --type change` 通过
- [ ] 6.8 **主 spec 提升后核验**〔spec-review-amendment SR-42〕：archive 阶段 delta 落进 `openspec/specs/roadmap-planning/spec.md` 后，对结果 spec 再跑一次 6.1 词表扫描，并逐 Requirement 与重写后的 SKILL.md 对码

### 测试覆盖图（code path → 验证方式）

| 改动面 | 验证方式 | 任务 | 是不是机械门 |
|---|---|---|---|
| SKILL.md 指令层（路由/拷问/生成/收尾） | 人读终审 + grep 残留扫描 + 「保留」节逐句核对 | 6.1 / 6.6 | ❌ 半机械（命中需人工过滤） |
| principles 托管块完整性 | `sync_principles.py --check` | 6.3 | ✅ 真机械门 |
| spec delta 结构合法性 | `openspec validate --strict` | 6.7 | ✅ 真机械门 |
| matt 移除对脚本/测试的波及 | pytest（相对 merge-base 无新增失败） | 6.2 | ⚠️ 本 change 不改任何 `.py`，覆盖面近于零；且 baseline 已有 1 个无关红 |
| 存量 footage 兼容行为 | **构造 fixture** 演练（本仓无真实 footage） | 6.4 | ❌ 人工 |
| 缺件存量包兼容行为 | 真实单文件包演练 | 6.5 | ❌ 人工 |
| bundle 安装链路 | `setup.sh` 重跑 + 单独跑 `--check` | 4.4 | ⚠️ setup.sh 内那处非 fail-closed，须单独跑 |
| 主 spec 提升后一致性 | 归档后重扫 + 逐 Requirement 对码 | 6.8 | ❌ 人工 |

> 🔴 **诚实边界〔spec-review-amendment SR-19〕**：`sdflow-roadmap` 是纯 Markdown 编排类 skill，
> **没有 `scripts/`、没有 `tests/`** ⇒ 本 change 的**主体改动（指令层行为）没有任何自动化测试面**。
> 上表只有两道真机械门（6.3 / 6.7），且都不覆盖三态路由 / 七维裁剪 / 增量落盘 / 重入 / 放弃清理这些新行为。
> 这不是可以靠加脚本补上的缺口（无确定性信号可捕获），**是合法的残余划分**——
> 但 Success Metrics MUST NOT 因为「门禁全绿」就宣称行为正确。终审人读是这一层的唯一防线。
