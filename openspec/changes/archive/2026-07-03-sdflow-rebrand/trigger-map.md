# trigger-map.md — 触发等价表（2.1/2.2）

> 决策依据：[design.md](./design.md) §四 D2「触发等价表」。约束：9 个改名 skill 的 description 重写
> **原触发场景语句集全保留**，只换 slash 名、荡涤旧名指称，可酌情追加新名短语。
> 旧短语抽取自改名前 commit `04f4a0e`（`git show 04f4a0e:<旧目录>/SKILL.md`）。

## sdflow-init（旧 opsx-project-init）

| 旧触发短语 | 新 description 保留情况 |
|---|---|
| "给这个项目初始化 openspec 工作流" | 保留原文 |
| "把 workflow 铺过来" | 保留原文 |
| "装一下 spec 工作流" | 保留原文 |
| "新项目搭一套和 04-iot-tools 一样的 openspec" | 保留原文 |
| "更新这个项目的 workflow 规则到最新" | 保留原文 |

slash：`/opsx-project-init` → `/sdflow-init`；name 字段：`opsx-project-init` → `sdflow-init`；H1：`# opsx-project-init — …` → `# sdflow-init — …`。未追加新名短语（原句式已密，未再堆叠）。

## sdflow-done（旧 opsx-done）

英文功能性描述，无中文"当用户说…"引号短语清单；仅末句 `Use when implementation is complete and reviewed.` 为触发条件，原文保留。

slash：`/opsx-done` → `/sdflow-done`；name 字段同步；H1：`# opsx-done — OpenSpec 变更收尾` → `# sdflow-done — OpenSpec 变更收尾`。全篇无中文触发短语可核对，故本节机械断言用英文触发句锚定。

## sdflow-maintain（旧 opsx:maintain）

无引号触发短语清单、原 description 本就无 slash 引用（旧 frontmatter 无 `Trigger with` 句）。原句 "扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。" 逐字保留。

name 字段：`opsx:maintain` → `sdflow-maintain`（与目录名及其余 8 个 skill 的 dash 命名一致，RENAME-MAP 无冒号形态）。**追加**新句尾 `Trigger with /sdflow-maintain。`（原本没有 slash 触发句，属于酌情补充，非替换任何旧短语）。无 H1（Task 4 起本文件即无自标题行，跳过）。

## sdflow-roadmap（旧 opsx:roadmap-planner）

| 旧触发短语 | 新 description 保留情况 |
|---|---|
| "做一个 roadmap" | 保留原文 |
| "帮我规划 xxx" | 保留原文 |
| "分阶段实现 xxx" | 保留原文 |
| "先想清楚再动手" | 保留原文 |
| "有一堆事不知道从哪开始" | 保留原文 |
| "重构计划" | 保留原文 |
| "新项目怎么起步" | 保留原文 |
| "这个项目太大了要拆" | 保留原文 |
| 即使没明说"roadmap"三个字也建议触发 | 保留原文 |

name 字段：`opsx:roadmap-planner` → `sdflow-roadmap`（同上，dash 命名统一）。原 description 无 slash 引用，**追加** `Trigger with /sdflow-roadmap。`。H1 为通用标题 `# Roadmap Planner`，未自称旧名，不在本次改名重写范围（Task 4/5 均未触碰）。

## sdflow-spec-review（旧 spec-review）

无引号"用户说"式清单，为功能性编排描述；核心识别短语原文保留：`阶段二「设计评审编排器」`、`中途不打断`、`不依赖 /clear`、`只审 prevention（config 固化的结构/约束）焊不住的残差`。产出物文件名 `spec-review-report.md` 与标签 `[spec-review-amendment]` 属通用工作流约定（非 skill 自称），维持不变（与 sdflow-code-review 侧 `[impl-review-fix]` 标签同一处理原则）。

slash：`/spec-review` → `/sdflow-spec-review`；name 字段同步；H1：`# spec-review — 阶段二设计评审编排器` → `# sdflow-spec-review — 阶段二设计评审编排器`。**追加**新名短语"也可说'sdflow 设计审'"。

## sdflow-code-review（旧 impl-review）

无引号"用户说"式清单；核心识别短语原文保留：`阶段三「代码评审编排器」`、`每次全跑·独立冷视角·强制主审`、`阶段三无人类门`、`不依赖 /clear`。产出物文件名 `code-review-report.md` 与标签 `[impl-review-fix]`（工作流通用标签约定，同 spec-review-amendment）维持不变；正文中 "buglist/todolist" 为通用池名词（非 skill 自称）不改。

slash：`/impl-review` → `/sdflow-code-review`；name 字段同步；H1：`# impl-review — 阶段三代码评审编排器（每次全跑·独立冷·强制主审）` → `# sdflow-code-review — 阶段三代码评审编排器（每次全跑·独立冷·强制主审）`。**追加**新名短语"也可说'sdflow 代码审'"。

## sdflow-buglist（旧 buglist-recorder）

| 旧触发短语 | 新 description 保留情况 |
|---|---|
| "记一下这个 bug" | 保留原文 |
| "这个问题记到 buglist" | 保留原文 |
| "标记 Bxx 已修" | 保留原文 |
| "列一下还没修的 bug" | 保留原文 |
| 场景句：烧板验证/日志分析/代码审查/调试中发现 bug 或缺陷 | 保留原文 |

slash：`/buglist-recorder` → `/sdflow-buglist`；name 字段同步；H1：`# buglist-recorder — 自动记录 / 回写 / 扫描 buglist` → `# sdflow-buglist — 自动记录 / 回写 / 扫描 buglist`。未再追加新名短语（原句式密度已高）。

## sdflow-todolist（旧 todolist-recorder）

| 旧触发短语 | 新 description 保留情况 |
|---|---|
| "以后可以改进" | 保留原文 |
| "这里能优化" | 保留原文 |
| "这是个技术债" | 保留原文 |
| "记个 TODO" | 保留原文 |
| "加进待办池" | 保留原文 |
| "记一下这个优化" | 保留原文 |
| "这个改进想法存一下" | 保留原文 |
| "标记 Txx 已完成" | 保留原文 |
| "列一下待办" | 保留原文 |

slash：`/todolist-recorder` → `/sdflow-todolist`；name 字段同步；H1：`# todolist-recorder — 自动记录 / 回写 / 扫描 todolist` → `# sdflow-todolist — 自动记录 / 回写 / 扫描 todolist`。sibling 自称句"已确认的 bug…该用 `buglist-recorder`"同步换 `sdflow-buglist`（与 Task 4 已对正文其余处所做的同类替换保持一致，此处补齐 frontmatter 内漏项）。

## sdflow-issues（旧 issues-recorder）

无引号"用户说"式清单；核心识别短语原文保留：`共享 issues 层的**薄操作型 skill**`、场景句"想重建 INDEX.md、新建/推进/改名一个批次、盘点批次完成度时"、`DO NOT EDIT` banner 提示。自称句"主要由 `opsx-done` 的 issues sweep 子步…自动调用"同步换 `sdflow-done`（与 Task 4 sweep 一致处理，frontmatter 内此前遗漏）。

slash：`/issues-recorder` → `/sdflow-issues`；name 字段同步；H1：`# issues-recorder — 共享 issues 层（reindex / batch）` → `# sdflow-issues — 共享 issues 层（reindex / batch）`。

---

## 机械断言（Step 3）

一次性 python（未留脚本文件），对每个 skill 的**新 SKILL.md frontmatter 文本**逐条核验上表列出的旧触发短语 `in` 新文本（硬编码短语输入，取自本文件人工列出的清单，slash/name 变更点另行人工核对，机械断言只锚触发短语存续）：

```
$ python3 - <<'PYEOF'
import re

REPO = "/Users/cheneyzhao/Documents/04-sdflow-skills"

def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"no frontmatter found in {path}"
    return m.group(1)

CASES = {
    "sdflow-init (opsx-project-init)": ("sdflow-init/SKILL.md", [
        "给这个项目初始化 openspec 工作流", "把 workflow\n  铺过来", "装一下 spec 工作流",
        "新项目搭一套和 04-iot-tools 一样的 openspec", "更新这个项目的 workflow\n  规则到最新",
    ]),
    "sdflow-done (opsx-done)": ("sdflow-done/SKILL.md", [
        "Use when\n  implementation is complete and reviewed.", "Finalize an OpenSpec change",
    ]),
    "sdflow-maintain (opsx:maintain)": ("sdflow-maintain/SKILL.md", [
        "扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。",
    ]),
    "sdflow-roadmap (opsx:roadmap-planner)": ("sdflow-roadmap/SKILL.md", [
        "做一个 roadmap", "帮我规划 xxx", "分阶段实现 xxx", "先想清楚再动手", "有一堆事不知道从哪开始",
        "重构计划", "新项目怎么起步", "这个项目太大了要拆", "即使用户没明说\"roadmap\"三个字",
    ]),
    "sdflow-spec-review (spec-review)": ("sdflow-spec-review/SKILL.md", [
        "阶段二「设计评审编排器」", "中途不打断", "不依赖 /clear", "只审 prevention",
    ]),
    "sdflow-code-review (impl-review)": ("sdflow-code-review/SKILL.md", [
        "阶段三「代码评审编排器」", "每次全跑·独立冷视角·强制主审", "阶段三无人类门", "不依赖 /clear",
    ]),
    "sdflow-buglist (buglist-recorder)": ("sdflow-buglist/SKILL.md", [
        "记一下这个 bug", "这个问题记到 buglist", "标记 Bxx 已修", "列一下还没修的 bug",
        "烧板验证、日志分析、代码审查、\n  调试中发现了 bug 或缺陷",
    ]),
    "sdflow-todolist (todolist-recorder)": ("sdflow-todolist/SKILL.md", [
        "以后可以改进", "这里能优化", "这是个技术债", "记个 TODO", "加进待办池",
        "记一下这个优化", "这个改进想法存一下", "标记 Txx 已完成", "列一下待办",
    ]),
    "sdflow-issues (issues-recorder)": ("sdflow-issues/SKILL.md", [
        "共享 issues 层的**薄操作型 skill**", "想重建 INDEX.md、新建/推进/\n  改名一个批次、盘点批次完成度时",
        "DO NOT EDIT",
    ]),
}

all_pass = True
for skill, (relpath, phrases) in CASES.items():
    fm = frontmatter(f"{REPO}/{relpath}")
    print(f"### {skill}  ({relpath})")
    for p in phrases:
        ok = p in fm
        all_pass = all_pass and ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {p!r}")
    print()

print("=" * 60)
print("OVERALL:", "ALL PASS" if all_pass else "FAILURES PRESENT")
PYEOF
```

### 断言输出（实跑，留档）

```
### sdflow-init (opsx-project-init)  (sdflow-init/SKILL.md)
  [PASS] '给这个项目初始化 openspec 工作流'
  [PASS] '把 workflow\n  铺过来'
  [PASS] '装一下 spec 工作流'
  [PASS] '新项目搭一套和 04-iot-tools 一样的 openspec'
  [PASS] '更新这个项目的 workflow\n  规则到最新'

### sdflow-done (opsx-done)  (sdflow-done/SKILL.md)
  [PASS] 'Use when\n  implementation is complete and reviewed.'
  [PASS] 'Finalize an OpenSpec change'

### sdflow-maintain (opsx:maintain)  (sdflow-maintain/SKILL.md)
  [PASS] '扫描 openspec 目录状态，对比 INDEX.md，报告差异并修复。归档变更后、手动增删 spec 后、合并上游更新后使用。'

### sdflow-roadmap (opsx:roadmap-planner)  (sdflow-roadmap/SKILL.md)
  [PASS] '做一个 roadmap'
  [PASS] '帮我规划 xxx'
  [PASS] '分阶段实现 xxx'
  [PASS] '先想清楚再动手'
  [PASS] '有一堆事不知道从哪开始'
  [PASS] '重构计划'
  [PASS] '新项目怎么起步'
  [PASS] '这个项目太大了要拆'
  [PASS] '即使用户没明说"roadmap"三个字'

### sdflow-spec-review (spec-review)  (sdflow-spec-review/SKILL.md)
  [PASS] '阶段二「设计评审编排器」'
  [PASS] '中途不打断'
  [PASS] '不依赖 /clear'
  [PASS] '只审 prevention'

### sdflow-code-review (impl-review)  (sdflow-code-review/SKILL.md)
  [PASS] '阶段三「代码评审编排器」'
  [PASS] '每次全跑·独立冷视角·强制主审'
  [PASS] '阶段三无人类门'
  [PASS] '不依赖 /clear'

### sdflow-buglist (buglist-recorder)  (sdflow-buglist/SKILL.md)
  [PASS] '记一下这个 bug'
  [PASS] '这个问题记到 buglist'
  [PASS] '标记 Bxx 已修'
  [PASS] '列一下还没修的 bug'
  [PASS] '烧板验证、日志分析、代码审查、\n  调试中发现了 bug 或缺陷'

### sdflow-todolist (todolist-recorder)  (sdflow-todolist/SKILL.md)
  [PASS] '以后可以改进'
  [PASS] '这里能优化'
  [PASS] '这是个技术债'
  [PASS] '记个 TODO'
  [PASS] '加进待办池'
  [PASS] '记一下这个优化'
  [PASS] '这个改进想法存一下'
  [PASS] '标记 Txx 已完成'
  [PASS] '列一下待办'

### sdflow-issues (issues-recorder)  (sdflow-issues/SKILL.md)
  [PASS] '共享 issues 层的**薄操作型 skill**'
  [PASS] '想重建 INDEX.md、新建/推进/\n  改名一个批次、盘点批次完成度时'
  [PASS] 'DO NOT EDIT'

============================================================
OVERALL: ALL PASS
```

**结论**：9 个 skill、共 39 条旧触发短语（含场景句），逐条核验均 `PASS`——原触发场景语句集**无一丢失**，满足设计门 D2 触发等价约束。name 字段、slash 引用、H1 自标题的旧→新对照见上表；这两类是"换新"而非"保留"项，机械断言不覆盖（人工逐节核对，见上表"slash：… → …"行）。
