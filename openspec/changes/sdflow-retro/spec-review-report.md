# spec-review 报告 — sdflow-retro

> 阶段二设计评审（sdflow-spec-review 编排）。5 独立冷源：Step1 广审(主session) + 领域镜 + 对抗镜×2 + 接地镜 + codex design-voice。
> 无 HR-TG（TG 命中 {11,12,14,15,18,21,22,23} ∩ HR-TG 子集{04,06,07,08,09,16,17,26}=∅）。

## 命中范围
- 栈：dev-tooling / python 数据类 skill + bundle 部署纪律（无 backend-go/embedded/frontend 领域镜）。
- 清单：数据类 skill 约定（CLAUDE.md）+ view-only 契约 + 部署纪律（spec-workflow）。
- Step1 广审：scope 无声扩张=无；完成度=1 缺口（B1 已 amend）。

## 冷审总判（★核心）
**边界/阶段引擎是从单个乖巧样本（adaptive-workflow-routing，恰是唯一用 `checkpoint(done-archive)` 的 change）外推的，对真实 17-change 语料塌方**。冷镜层这轮兑现了 load-bearing 价值——抓到 grill 用单样本"验证"漏掉的语料级问题。核心结论：**retro 是前向工具，历史 best-effort 且薄**（诚实标注），这与用户 grill 决策"以前不管、后续定规则"一致。

---

## 决策登记区

```
┌─────────────────────────────────────────────────────────────────────┐
│ [自动决策] D-A  归档/done 边界改 path-rename 检测(非 subject 前缀)      │ 实测强制,无备选
│ [自动决策] D-B  边界检测加 seed-mass 提交剔除 + 0/1 提交守卫 + archive  │ 实测强制
│                 路径兜底(pre-archive 空时)                              │
│ [自动决策] D-C  阶段词表补全 + 最长前缀匹配语义 + -fix/-gate 归并规则   │ 实测强制
│ [自动决策] D-D  价值维扫 active+archive 两源、per-change join 跨 spec+  │ codex C3+域轴4-1
│                 code 两份报告分 layer                                   │
│ [自动决策] D-E  hr-tg 双层锚: 拆 spec_hr_tg/code_hr_tg 两列(非单列)     │ codex C4
│ [自动决策] D-F  proposal A2/A3 over-claim 降级(历史薄,诚实)             │ 对抗2 B/D
│ [自动决策] D-G  "显著呈现"锚定机械契约(报告顶部 ⚠️ 区块),非形容词      │ 域轴5 死列风险
│ [自动决策] D-H  report.md 沿用 buglist/todolist 原子写 + 测试           │ 域轴2附
│ [需拍板]  Q1   retro 价值前向、历史 best-effort/薄(2/17有价值锚、2 seed │ 呼应 grill#3;
│                无边界)——认此定位 ship,还是要求补历史回填/降 scope?      │ 设计门确认
│ [已裁掉]  X-refuted  孤儿副本自动清(F1)/名前缀泄漏(probe4)/在途自读     │ 反静默压制,记理由
│                (probe5)/幂等覆盖(probe7)/其它 resolver 引用(F2)/setup    │
│                不装 scripts(F4)                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Findings（按镜，带裁决）

### 接地镜（grounding，机械核事实）
- **G2〔高·采纳〕** = 对抗1 F5 双镜印证：`init.py:125-129` `ignore_patterns("tests")` 是**通用** tools/tests 排除（部署整个 tools/ 含 engine.js/trivial_shape.py），**非聚合器专属**。tasks 5.3"删排除逻辑"照字面做会炸 review 工具 + trivial_shape 部署（重演 CF-6）；且现有回归测试 lens 专属、move 后必 FAIL 逼改写→覆盖丢。**正解：排除逻辑保持不动，test_init 断言改指 trivial_shape 非删**。→ amend tasks 5.3/5.4、proposal/design D2。
- **G6〔高·采纳〕** = codex C2 + 对抗2 A：归档提交前缀非 `checkpoint(done-archive)`（实测 workflow-metrics-loop=`feat`、review-tool-followups=`chore`）→ done 阶段漏计。→ D-A path-rename 检测。
- **G1〔中·采纳〕**：design 组件树 tests/ 画在 skill 根(与 scripts/ 平级) vs tasks"进 scripts/" → parents[1] 解析可能挂。→ 钉死布局 `sdflow-retro/scripts/{lens_metric_aggregate.py,tests/}`，test 的 parents[1] 相应校准。
- **G3〔中·采纳〕**：test_init 漏点 line 126(--dev 断言 test_lens_metric_aggregate.py 部署)。→ tasks 5.4 显式列 line 119+126。
- **G5〔低·采纳〕**：MODIFIED 串改——SR-K 丢 `bundle→sdflow-ship` 方向注 + "不产合成价值分" scenario 丢 SR-J 尾注。→ 恢复。
- **G4〔确认·无动作〕**：ship_gate.py:200 精确 `== "checkpoint(impl-review)"` 属实 → OQ1/D1 不改 tag 站得住。

### 对抗镜1（聚合器迁移）
- **F5〔高·采纳〕**：见 G2（双镜命中）。
- **F3〔中·采纳〕**：retro 调 skill-local 脚本路径未钉死，实现者若用 cwd 相对会找不到。→ 钉死绝对 skill 路径 `~/.claude/skills/sdflow-retro/scripts/…`（两运行时皆在磁盘）。
- **F2b〔低·采纳〕**：prose 迁移点是 4 处非 3（补 `sdflow-spec-review/SKILL.md:120`）。
- **F1/F2/F4〔裁掉·refuted〕**：孤儿副本 copy_bundle rmtree+copytree 自动清；无其它 resolver 运行时引用；setup.sh 软链整 skill 目录含 scripts/。理由留档。

### 对抗镜2（边界/报告）
- **A〔高·采纳〕**：见 G6，15/15 实测 done 阶段测不出。→ D-A。
- **B〔高·采纳〕**：创世 mass 提交致 2 seed change pre-archive 路径 0 提交，证伪 A2。→ D-B（seed 剔除 + 0/1 守卫 + archive 路径兜底）。
- **C〔中·采纳〕**：词表覆盖不足(design-gate/writing-plans/final-review/model-baseline 落 unknown) + 匹配语义未定义。→ D-C。
- **D〔中·采纳〕**：价值锚仅 2/17 change 有 → 证伪 A3；N=2 聚合近乎无意义。→ D-F + 顶部显性"真锚 M"。
- **E〔低-中·采纳〕**：失败模式表无"ts 非单调/负Δ"行（当前语料无实例但潜在）。→ 补 `max(0,Δ)` 钳制 + reorder-suspected 标注。
- **probe4/5/7〔裁掉·refuted〕**：名前缀泄漏 0（git pathspec 按路径分量字面匹配）；在途自读无递归（report 落 change dir 外）；view-only 全量再生确定性、缺失只留空不消行。理由留档。

### 领域镜（数据类 skill 约定）
- **F-A〔高·采纳〕** = codex C1 三方印证：tasks 1.2 `--follow` 与 D1 硬矛盾且技术误用（--follow 只对单文件）。→ 删 --follow。
- **轴4-1〔中-高·采纳〕**：每 change 有 spec-review + code-review 两份报告各带 layer 锚，join 须跨两份分 layer。→ D-D。
- **轴2〔中·采纳〕**：proposal Compliance "零新持久可变态"字面与 tracked report.md 打架。→ 改"零新持久可变**状态**（report 是 view，state 真相源=锚/git）"，与 spec"state"用词统一。
- **轴2附〔中·采纳〕**：report.md 写盘未沿用 buglist/todolist 原子写 + 无测试。→ D-H。
- **轴4-2〔中·采纳〕**：边界降级 case（同名复用/stacking）未列测。→ 补测。
- **轴5〔中·采纳〕**："显著呈现"≥4 处无机械判据（死列风险自我复现）。→ D-G。
- **轴1〔低-中·采纳〕**：design 组件树"change 类型分类 琐碎/routine"与 D3 否决语义分桶矛盾（组件树 stale）。→ 改组件树该行。
- **轴6〔低·采纳〕**：INDEX.md 未加 retro/ 策展条目。→ 补。
- **轴3〔低·采纳〕**：与 maintain description 不撞车；注意运行时有同名 gstack `retro` skill（namespace 隔离，低危）+ description 实体待实现补。→ 记，description 锚定"openspec change/评审工作流/镜价值"限定词。

### Step1 广审（broad）
<!-- sdflow:step1-broad-review v1 mode="simulated" -->
- **B1〔低·已采纳〕**：proposal 部署条 staleness，已 amend（本轮 Step1 已修）。gstack-review.md 详见（mode=simulated：主 session 直接跑 scope/完成度，未原生调 gstack autoplan，诚实标注）。

### codex design-voice（outside-voice，runner=codex）
- C1→F-A / C2→G6/A / C3→D-D / C4→D-E / C5〔低·采纳〕docs/workflow-skills/sdflow-code-review.md:57 仍指 maintain，迁移漏。→ 补 docs/ 进迁移 grep。

---

## 度量锚（lens-metric，metrics.enabled=true）
<!-- sdflow:lens-metric v1 layer="spec-review" lens="broad" runner="claude" site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="domain" runner="claude" site="—" findings="9" 采纳="9" 裁掉="0" defer="0" 独立="6" sev="致0/高1/中5/低3" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="adversarial" runner="claude" site="—" findings="11" 采纳="8" 裁掉="3" defer="0" 独立="5" sev="致0/高3/中3/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="grounding" runner="claude" site="—" findings="6" 采纳="5" 裁掉="0" defer="0" 独立="2" sev="致0/高1/中2/低2" -->
<!-- sdflow:lens-metric v1 layer="spec-review" lens="outside-voice" runner="codex" site="design-voice" findings="5" 采纳="5" 裁掉="0" defer="0" 独立="1" sev="致0/高2/中2/低1" -->
<!-- sdflow:hr-tg v1 hit="none" evidence="命中 TG{11,12,14,15,18,21,22,23}，∩ HR-TG 子集{04,06,07,08,09,16,17,26}=∅；只读观测工具，无运行期爆炸/数据损坏/安全面" -->
<!-- sdflow:outside-voice v1 site="design-voice" guard="none" runner="codex" reason_code="none" findings="5" truncated="false" -->

---

## 收敛口
冷审存活 findings 已全部落 amendment（[spec-review-amendment]）。唯一 [需拍板] Q1（retro 前向定位、历史 best-effort/薄）呼应用户 grill 决策，建议设计门确认后进 HARD-GATE → writing-plans。

## 拍板记录（设计门）
- **2026-07-06 设计门批准**：用户拍板 **Q1 = 批准（前向为主、历史 best-effort/薄）**——认 D8-D13 边界引擎实测修订 + retro"真价值在向前、历史尽力解析不假装全覆盖"的诚实定位。全部 [自动决策] D-A~D-H/D8-D13 采纳、无翻改；lens-metric 锚 5 行反映门后最终裁决（全采纳，SR-M 无需重算）。
- 进 writing-plans（实现）→ code-review → done。

<!-- ship-gate: design-approved -->
