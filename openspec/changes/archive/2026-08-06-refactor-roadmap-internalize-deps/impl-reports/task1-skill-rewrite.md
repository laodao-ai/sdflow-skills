# Task 1 实现报告：sdflow-roadmap 讨论层三相位重写

**状态**：DONE
**改动文件**：仅 `sdflow-roadmap/SKILL.md`（`git diff --stat`：1 file changed, 179 insertions(+), 184 deletions(-)）
**提交**：`f872abd refactor(sdflow-roadmap): 讨论层三相位重写（Task 1）`（普通 commit，无 `task1-` 完成标签）

## 前置说明：worktree 基线修复

派发时的 worktree 分支（`worktree-agent-acf1f578ab22ed715`）是从 `main` 切出的，不含
`feat/refactor-roadmap-internalize-deps` 上的 change 四件套/tickets/briefs（`openspec/changes/
refactor-roadmap-internalize-deps/` 整目录缺失）。核实 `git merge-base --is-ancestor HEAD
feat/refactor-roadmap-internalize-deps` 为真（本 worktree 分支是该 feature 分支的祖先，工作区
`git status` 为 clean）后，执行 `git merge feat/refactor-roadmap-internalize-deps`——非冲突
fast-forward（`Updating f464e9b..4d156ec`），仅新增该分支已有的 change 文件，未丢失/覆盖任何
本 worktree 内容。之后才能读到 `task1-brief.md` / `design.md` / `tasks.md` / `decision-memo.md` /
`spec.md` / `spec-review-report.md`。

## 做了什么

按 `tasks.md` §1（1.1–1.11）逐条重写 `sdflow-roadmap/SKILL.md`：三分支路由（`/opsx:explore` ·
wayfinder 长档 · `/office-hours` 前置）改为线性三相位协议（第零步重入探测 → 相位 A 澄清 + gate-0 +
商业化信号检查 → 三态路由 → 相位 B 七维拷问裁剪 + 增量落盘 → 相位 C 生成三件套 → review 分档 →
收尾 checklist 四项）。全部 wayfinder/footage/office-hours/grilling/domain-modeling/`openspec/matt`
机械从指令层删除，`sdflow:principles` 托管块零字节未动。

## 逐条验收证据

| brief 验收项 | 对应 tasks.md | 证据（SKILL.md 行号，本次提交后） |
|---|---|---|
| 第零步节独立 `##` 标题，物理位置在相位 A 之前 | 1.2 | `## 第零步：重入探测`（:277），`## 相位 A：...`（:289）——277 < 289 |
| frontmatter 去 wayfinder/footage，保留架构先行指路句 | 1.1 | frontmatter description 无 wayfinder/footage 字样；末句「新项目起步尚无架构设计（SAD）时，先 `/sdflow-architecture`」原样保留 |
| 三相位总览 + 三态路由节，入口含第零步分支，判定点①留痕含维度子集 | 1.3 | `## 工作流概览`（:171）ASCII 图含「第零步」box；`### 三态路由（判定点①）`（:311，加回路由对照表后行号顺移）留痕句含「含本次实际选入的拷问维度子集」；`/opsx:explore` 上游指路句在相位 A 开篇（:291） |
| 相位 B 节：起手三步/七维裁剪表/提议制/增量落盘/停止条件三态/重入协议/放弃清理两路 | 1.4 | `## 相位 B：拷问与增量落盘` 下 7 个 `###` 子节全部写就（起手三步/七维拷问与裁剪表/术语ADR提议制/增量落盘/停止条件/重入协议/放弃清理），放弃清理区分 create（先复述路径再删）与 continue/replan（不自动删+task-log记一行） |
| memo `## 未决项` 小节条款：再触发条件、随包长期存在、承接边界如实声明 | 1.4 🔴 | 「停止条件」子节内「`## 未决项` 小节」段落——三要素齐全（含「MUST NOT 被表述为等价于 wayfinder 票据模型...本 skill 明确不承接」） |
| 相位 C 节：三件套直写/「结晶」→「生成」全文改/生命周期判定时点前移/近细远雾术语改 | 1.5 | `## 相位 C：生成三件套`；全文 grep `结晶` 零命中；开篇句「生命周期判定...已在相位 B 起手或本相位落盘前完成」；`roadmap.md 近细远雾` 节内「商业化信号」已替换（原「产品/商业野心信号」） |
| 历史存档节：定义/规则3改写/存量footage冻结一行提示/陷阱3改写 | 1.6 | `### 规则 3：三件套不引用历史存档`（含定义+引用禁令+冻结条款一行提示）；`### 陷阱 3：历史存档被当成正式文档引用` |
| review分档节（含未审待恢复阻塞收尾）+ 收尾checklist四项（③覆盖历史存档、④memo对账+未决项闭环+诚实边界）+ 判定点②③留痕 | 1.7 | `## review：按商业化信号分档（判定点②）` 含「### review 依赖不可用时不静默，且阻塞收尾」子节明文「该状态阻塞收尾」；`## 收尾 checklist：四项软门`（判定点③）①②③④四项齐全，④含 memo 对账+未决项闭环+诚实边界声明 |
| wayfinder全部机械已删；路由对照表重写为三态版 | 1.8 | grep `wayfinder\|office-hours\|grilling\|domain-modeling\|openspec/matt` 全文件零命中（除历史存档语境下的合法 `footage/wayfinder` 提及，见下）；`### 路由对照表（自检基准）` 5 行示例覆盖①②③三态 + explore 上游 + 小规模场景 |
| principles 托管块零字节未动 | 1.9 | `python3 hack/sync_principles.py --check` 退出码 0，输出「✅ 20 个投放面全部与真相源一致」 |
| 「保留」节内嵌 7 处待删机制逐处处置 | 1.10 | 见下方「1.10 逐条核对」 |
| 「实战案例：博客v2重建」显式处置 + 规则1/陷阱4括注旁证同步删除 | 1.11 | 整节已删除（`grep 实战案例\|博客 v2 重建` 全文件零命中）；**处置决定：删除**（理由：按 DOC-1，该节自述「彼时结构...现行流程见上文」，正是正文里的考古层，且随三相位重写其史实描述已与新流程脱节）；规则1「历史教训」括注、陷阱4「博客 v2 的真实教训」括注均已去除（grep 零命中） |
| 「保留」节逐句核对（命名规范/下游阶段实施/参考模板/硬性规则1·5/常见陷阱1/CLAUDE.md配合） | 6.6（本票同时列出） | 见下方「6.6 逐句核对」 |

### 1.10 逐条核对（7 处内嵌待删机制）

| 原位置（旧 SKILL.md 行号） | 处置 | 新文件核实 |
|---|---|---|
| `:199` 规则1「长讨论的 footage 落…」半句 | 删 | 新规则1（:206-208）仅 3 条，无 footage 字样 |
| `:227` 规则5 wayfinder Task 票整条子条款 | 删 | 新规则5（:233-235）仅 3 条，无 wayfinder/Task 票字样 |
| `:511` 命名规范「footage map 头部 Tracker root」锚 | 删 | 新命名规范（:529）末条只保留目录名+实施变更前缀两项 |
| `:525` 下游阶段实施 fallback 三例外 | 降为两例外 | 新文件（:543）「命中两种例外（用户明确要求分步 / 环境不可用）」 |
| `:546` 陷阱1「先进讨论层三分支路由」 | 改「进相位 B 拷问」 | 新陷阱1（:564）「不足就先进相位 B 拷问」 |
| `:603` CLAUDE.md配合，只删分号后 footage 子句 | 删footage子句，保留前半句 | 新文件（:613）表格行只剩「项目级 roadmap 文档包（长期真相源），按项目分子目录」 |
| `:618` 参考模板 memo 描述与 D9 矛盾 | 改写 | 新文件（:627）「相位 B 拷问纪要模板（走拷问路径必产出；直接生成路径可不产出），历史存档用」 |

### 6.6 逐句核对（保留节）

- **命名规范**：kebab-case/动词开头/长度建议/示例四条原样保留；仅删了 footage 锚一句（见上表），其余无残留引用。
- **下游阶段实施**：`-p<N>` 命名规则、`PREFIX_RE`/`sdflow-done` 回填一致性说明、proposal 三要素引用（背景/设计复用/规范扩展）、brainstorming 切换句，全部原样保留；仅 fallback 例外句改动（见上表）。
- **参考模板**：5 个模板文件列表原样保留，仅 memo-template 一行描述改写（见上表）。
- **硬性规则 1·5**：见 1.10 表，无其余残留。
- **常见陷阱 1**：见 1.10 表，无其余残留。
- **CLAUDE.md 配合**：见 1.10 表，无其余残留。

## 跑过的命令与退出码

```
$ python3 hack/sync_principles.py --check
[sync_principles] ✅ 20 个投放面全部与真相源一致
退出码：0

$ grep -n "结晶\|野心\|三分支路由\|Tracker root\|office-hours\|grilling\|domain-modeling\|openspec/matt" sdflow-roadmap/SKILL.md
（无输出，退出码 1 = 零命中）

$ grep -n "实战案例\|博客 v2 重建\|博客v2重建" sdflow-roadmap/SKILL.md
（无输出，退出码 1 = 零命中）

$ grep -n "博客 v2 初版\|博客 v2 的真实教训" sdflow-roadmap/SKILL.md
（无输出，退出码 1 = 零命中）

$ grep -c '^```' sdflow-roadmap/SKILL.md
12（6 对，闭合）

$ git status --short   # 提交前
 M sdflow-roadmap/SKILL.md   # 仅此一个文件

$ git diff --stat sdflow-roadmap/SKILL.md
1 file changed, 179 insertions(+), 184 deletions(-)
```

**未跑** `/usr/bin/python3 -m pytest`（全仓 hack/tests/）：本票 `Blocked-by: none`、改动仅
Markdown 指令层、不涉及任何 `.py`，tasks.md 6.2 已声明该门属独立验证任务（相对 merge-base 无新增
失败），非本票 scope；本票 Global Constraints 亦明文「本 change 不改任何 `.py`」。`sync_principles.py
--check` 是与本票直接相关、且已验证绿的唯一机械门。

## Concerns

1. **「历史存档节」的结构解读**：`tasks.md` 1.6 写「写历史存档节：定义/规则3改写/冻结条款/陷阱3改写」，
   design.md 的「新 SKILL.md 骨架」清单中未列出独立的「历史存档」顶层 `##` 小节（对照旧文件那个专门的
   `## footage：wayfinder 落盘与引用边界` 顶层节已被 1.8 列入删除清单）。本次实现把「定义 + 引用禁令 +
   冻结条款」全部折叠进「规则 3」（`### 规则 3：三件套不引用历史存档`），未另起顶层 `##` 标题——这是
   对骨架清单字面意思的最贴合解读（骨架清单里「历史存档」三字仅出现在规则3的括注「规则 3 改『历史存档』」
   里，无独立位置）。若评审认为需要一个独立的顶层「## 历史存档」小节，属可低成本调整项。
2. **测试面**：本 change 对 `sdflow-roadmap` 的改动无任何自动化测试面（`tasks.md` 测试覆盖图已如实
   声明「SKILL.md 指令层...是人读终审 + grep 残留扫描 + 保留节逐句核对，❌ 半机械」）。本报告的验证
   手段已穷尽本票 scope 内能做的机械核验（principles gate + 全量 grep + 结构性核对），逐条行为正确性
   （三态路由是否真的会在实际对话中被正确执行）无法在实现期以自动化方式验证，留给收尾阶段的终审场景
   核对清单（tasks.md 6.8，非本票 scope）。
3. **路由对照表位置**：`tasks.md` 1.8 要求「路由对照表重写为三态版」，未指定挂载位置。本次将其作为
   `### 路由对照表（自检基准）` 挂在相位 A 的「三态路由」之后（原文件是独立顶层节挂在旧「讨论层：
   三分支路由」末尾）。选择挂在相位 A 内是因为它本质是三态路由判据的自检示例，与旧文件「三分支路由」
   节末尾挂载逻辑一致，未见明显不妥，仅作留痕说明。

以上三点均不影响四值状态判定为 DONE（无功能性缺口，均为结构性选择留痕），如评审有不同偏好，可在
双轴审阶段低成本调整。
