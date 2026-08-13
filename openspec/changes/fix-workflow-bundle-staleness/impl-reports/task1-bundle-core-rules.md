# Task 1 impl report：bundle 核心规则修正

范围：`sdflow-init/assets/workflow/` 下 9 个文件，按 memo D1/D2/D3/D6/D9 的措辞替换。全部按**内容定位**（非硬编号行号）核实原文后修改，无新增机制/文件/路径。

## 位点清单（before → after）

### 1. `spec-review.md`
- **:29**（D9）— 删除「`` `/clear` 后重审 ``」措辞：
  `fresh-context 子 agent / 第二声音（如 Codex）/ \`/clear\` 后重审 / grill。`
  → `fresh-context 子 agent / 第二声音（如 Codex）/ grill。`
- **:72**（D1，G2 现行口径）— AskUserQuestion → 决策登记区：
  `置信中 → 标"需人确认"，进 AskUserQuestion`
  → `置信中 → 标"需人确认"，写入报告决策登记区`
- **:91**（D9）— brainstorming 自检 → 生成期自检：
  `| **brainstorming 自检**（占位/歧义/scope） | self | ...`
  → `| **生成期自检**（占位/歧义/scope） | self | ...`
- **:92**（D6，号段去上界）— 删 `BASE-01~28`：
  `...别全 BASE-01~28 逐条 |` → `...别全 BASE 逐条 |`

### 2. `reference/README.md`
- **:6-8**（D9，部署观改 canonical 口径）— 「`openspec/workflow/`（上一级）」改为「上一级目录（本 bundle 权威源，运行时经全局 canonical `~/.sdflow/workflow/` 解析）」。
- **:17**（D7/D9）— 删 `Token_Saving_Strategies.md` 行（该文件已由 Task 3 git mv 出 `reference/`，此处随之清除唯一引用面）。
- **:18**（D1，P3c 现行口径）— quality-layering 描述「事后 sdflow-code-review 缩成高风险残差」（被 P3c 否决的旧结论）→「事后 sdflow-code-review 仍每次全跑·独立冷·强制主审（P3c；消的是通用质量冗余，非缩掉 sdflow-code-review。...）」。

### 3. `reference/quality-layering.md`
- **:25**（D2，独立性来源改口径）— 「事后 `` `/clear + /sdflow-code-review` `` 再加的独立性」→「事后 sdflow-code-review（独立编排器 + fresh 子代理 fan-out）再加的独立性」（与 G1「独立性由 fresh 子代理提供，非 `/clear`」对齐）。
- **:38**（D6，号段去上界）— 表行「通用代码质量（CR-01~09 base）」→「通用代码质量（CR base）」。
- **:42**（D2，退役机制改现行）— 表行「PR 级 DB/API/Auth 改动 | ❌ | 官方 code-review」→「... | sdflow-code-review」（P3d 已弃用官方独立 step）。
- **:84**（D2，删 subagent-dev）— 「阶段三内部（含 subagent-dev / sdflow-implement 调度期间...」→「阶段三内部（含 sdflow-implement 调度期间...」（adr/0042 后 tickets 唯一管线，subagent-dev 已退役）。
- **:14 出处标注**（保留，未改动）— 核实仍在：`已退役的 superpowers \`subagent-driven-development\`（reviewer 模板 / pre-flight 冲突扫描，见其自身...）`，`grep -n "退役的 superpowers"` 命中 :14。

### 4. `spec-checklists/spec-quality-base.md`
- **:37**（D2，退役机制改现行）— 「时间允许时执行（writing-plans 前尤为有用）」→「时间允许时执行（出 ticket 前尤为有用）」。
- **:7 来源行**（保留，未改动）— 核实仍在：`来源：综合 GStack plan-ceo/eng-review、SuperPowers brainstorming/writing-plans、IEEE 830/29148、NFR 标准。`（provenance 出处非失鲜，故保留原样，不因 writing-plans 退役而删）。

### 5. `spec-checklists/README.md`
- **:62**（D9，错路径修正）— 「见 `` `rules/ff-generation-constraints.md` ``」→「见 `` `../ff-generation-constraints.md` ``」（该文件实际位于 `spec-checklists/` 的上一级，非 `rules/` 子目录）。
- **:64**（D9，R 落点现行化）— 「需人判断，留 brainstorming / eng-review」→「需人判断，留 `` `/sdflow-spec` 相位 B 拷问 / `/sdflow-spec-review` ``」。

### 6. `/review` 消费方统一改写（8 处，D3）
全部改为 `sdflow-code-review`（+ `sdflow-implement` Standards 轴必填槽），措辞按上下文语法调整：

- `code-checklists/README.md`
  - :3 — 「在 `` `/review` ``（代码阶段）使用」→「在 `` `sdflow-code-review` ``（代码阶段，含 `` `sdflow-implement` `` Standards 轴必填槽）使用」
  - :13 — 「每次 `` /review `` 必过」→「每次 `` sdflow-code-review `` 必过」
  - :28 — 「`` `/review` `` 按变更命中的 TG...」→「`` `sdflow-code-review` ``（及 `` `sdflow-implement` `` Standards 轴必填槽）按变更命中的 TG...」
  - :53 — 「代码期(/review) → code-checklists/」→「代码期(sdflow-code-review + sdflow-implement Standards 轴) → code-checklists/」
  - :68 — 「代码审查（/review 阶段）」→「代码审查（sdflow-code-review / sdflow-implement Standards 轴阶段）」
- `code-checklists/code-review-base.md`
  - :3 — 「`` `/review` `` 阶段每次必过」→「`` `sdflow-code-review` ``（及 `` `sdflow-implement` `` Standards 轴必填槽）阶段每次必过」
- `code-checklists/domains/llm.md`
  - :5 — 「代码审（`` `/review` ``）侧登记」→「代码审（`` `sdflow-code-review` `` + `` `sdflow-implement` `` Standards 轴）侧登记」
- `trigger-catalog.md`
  - :108 — 「`` code-checklists/ ``（代码期 /review）」→「`` code-checklists/ ``（代码期 sdflow-code-review + sdflow-implement Standards 轴必填槽）」

## 核验

- `grep -n "/review"` 对全部 9 个位点文件复扫：仅剩 `spec-review.md:92` 的「spec-quality/review-checklist」——这是历史文件名提及，非 `/review` skill 消费方引用，不在 D3 范围内，保留。
- `quality-layering.md:14` 出处标注：`grep -n "退役的 superpowers" reference/quality-layering.md` 命中 :14，未被误删。
- `spec-quality-base.md:7` 来源行：`grep -n "来源：综合" spec-checklists/spec-quality-base.md` 命中 :7，未被误删。
- `/usr/bin/python3 -m pytest hack/tests/test_canonical_entry_sync.py -q` → 8 passed（generation-process.md 本 task 未改动，presence/absence 措辞不受影响）。
- 全仓 `/usr/bin/python3 -m pytest -q` 已在后台起跑（单次超 120s 超时移入后台），结果留待编排层核验门统一核对；本 task 未修改任何 Python 脚本，预期不受影响。

## 未做/超出本 task 范围

- `reference/README.md` 中 `Token_Saving_Strategies.md` 的实际 `git mv` 到 `docs/` 属 Task 3 范围，本 task 只删了 README 表格中的引用行（因该文件已不在 `reference/` 下，行本身即失效）。
- `generation-process.md`（D4）、`ff-generation-constraints.md`（D5）、`config.template.yaml`/`index-section.md`/`openspec/config.yaml`（D6/D9 同族）、`reference/Spec_Quality_Methodology.md`/`Spec_Quality_Collaboration.md`/`PRD_vs_Spec.md`（D7/D8/D9）均不在本 task（Task 1）范围内，按 scope-check 表分属其他 task。
