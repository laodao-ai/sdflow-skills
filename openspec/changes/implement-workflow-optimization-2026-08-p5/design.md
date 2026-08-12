# Design · implement-workflow-optimization-2026-08-p5

## Context

见 proposal.md「Why」。三条工作流（T275 考古层清理 / T101 拍板三问机验 / D3 分批条款）
互相独立，无实现顺序依赖；T256 仅调研记录（已落盘，本 change 无实现动作）。

## Goals / Non-Goals

**Goals（design 级边界，proposal 之外）**

- 清理是**编辑动作**：每处删/迁必须可通过 DOC-1 删除测试逐条复核，审计留档使 code-review
  冷层能抽查「删的是不是考古层」。
- 拍板三问是**增量锚**：新锚加入不改变既有锚（`sdflow:hr-tg` / `sdflow:lens-metric` /
  `sdflow:outside-voice` / `sdflow:fanout-capability` / `sdflow:declared-sites` /
  `sdflow:step1-broad-review`）的任何检查语义。
- 分批条款只改**提问节奏**，不动相位 A/B 的收束判据（A.2 禁止清单、B.5 停止信号原样）。

**Non-Goals（design 级）**

- 不给 ship_gate 加拍板层检查——机验只落 anchor_lint（spec-review SKILL Step3 自检链），
  gate 的 design 门判据（`design_approved` + `reviewed_sha` 新鲜度）不变。
- 不建通用「SKILL 行数上限」lint——行数是症状不是判据，DOC-1 删除测试才是判据。

## Decisions

本 change 的产品级决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)（D1–D4）。

以下为 design 级机制决策（memo 之下的派生实现选择）：

- **Da 拍板三问的呈现位**：决策登记区**顶部**新增「拍板三问」小节，置于 `[需拍板]` 条目
  之前——三行固定问题（①范围划界认不认：锚 proposal Non-Goals / Out-of-scope ②依赖/顺序
  认不认：锚 tasks 边界与 Blocked-by ③风险赌注与对策认不认：锚 `sdflow:hr-tg` 的
  hit/declared + 对策条目），每行 = 问题 + 评审侧一句自答（指回报告内证据）+ 人勾选位。
  人先过三问再逐 Q 拍板。备选（放执行摘要内）不取：执行摘要是散文层，勾选交互属拍板层。
- **Db 机验锚形态**：`<!-- sdflow:gate-questions v1 q="scope,deps,risk" -->` 一行，紧邻
  三问小节。`anchor_lint.py` 新增：`ANCHOR_PREFIXES` 登记 `"<!-- sdflow:gate-questions v1"`
  （`anchor_lint.py:70` 既有 dict）+ 新 check 函数——layer=spec-review 时存在性必查
  （**always-on**，沿 `check_fanout_consistency` 先例〔`anchor_lint.py:710`「不接受
  metrics_on」〕：报告结构契约与 metrics 开关无关），layer=code-review 不查（D2）；
  `q` 值必须逐字等于 `scope,deps,risk`（有序、无增减）；fence 内锚不算（复用既有
  fence-aware 口径）。备选（metrics 门控）不取：三问是报告结构不是度量。
- **Dc 审计留档**：`{change_dir}/audit/skill-doc1-audit.md` 单文件，每 SKILL 一节：
  删/迁/留三计数 + 迁移目标路径 + 边界个案逐条注记（原文引用 + 判定理由）。归档随
  change 目录进 `archive/`，长期可查。备选（每 skill 独立文件）不取：14 个碎片不便冷审通读。
- **Dd 外迁载体统一**：`<skill>/references/evolution-notes.md`（沿 sdflow-spec 既有先例，
  文件名统一便于后续机械发现）；SKILL 正文末尾指针统一为一行：
  `历史取舍不进入默认运行；仅在审计历史依据时读取 references/evolution-notes.md。`
  已有该文件的 skill（sdflow-spec）追加不新建。
- **De 分批条款落点**：`sdflow-spec/SKILL.md` A.1 与 B.3 两处条款重写（D3 全文）+
  `spec-authoring` spec SA-03 delta 同步。SKILL.md 为仓内顶层资产（symlink 分发），
  无 bundle 下发面。

## 组件/依赖图

```
T275 清理流                     T101 三问流                          D3 条款流
────────────                   ─────────────                        ──────────
14× SKILL.md ──删──▶ (git)     sdflow-spec-review/SKILL.md          sdflow-spec/SKILL.md
      │                          Step4 报告模版(+三问小节+锚)          A.1 + B.3
      └─迁─▶ <skill>/references/       │                                  │
             evolution-notes.md        ▼                                  ▼
      │                        sdflow-init/assets/workflow/        openspec/specs/
      ▼                          tools/anchor_lint.py               spec-authoring
{change_dir}/audit/              (+ANCHOR_PREFIXES+check)            (SA-03 delta)
 skill-doc1-audit.md                   │
                                       ├─▶ tools/tests/ (正例+负例+回放)
守卫面（三流共用）：                    └─▶ setup.sh 软链 ~/.sdflow/workflow/
 · 全仓 pytest（22 个文本消费测试）          └─▶ 消费仓经 sdflow-init update
 · sync_principles.py --check（托管块）
 · code-review 冷层（语义抽查 audit 留档）
```

## 协议文档套件 scope-check 表（TG-25 · BASE-29）

新锚 `sdflow:gate-questions` 牵连的全部站点（实现时逐行核对）：

| 站点 | 角色 | 动作 |
|---|---|---|
| `sdflow-spec-review/SKILL.md` Step4 报告条款 | emitter（主 session 落锚） | 加三问小节 + 锚行模版 |
| `sdflow-init/assets/workflow/tools/anchor_lint.py` | checker | `ANCHOR_PREFIXES` + check 函数（always-on, layer=spec-review） |
| `tools/tests/test_anchor_lint.py` | 契约测试 | 正例 / 缺锚负例 / q 值变异负例 / fence 内不算 / code-review layer 不查 |
| `sdflow-init/assets/workflow/` 内 spec-review 规则文件（若含报告结构描述，实现时 grep 定位） | 人读文档 | 同步三问描述，MUST NOT 与 SKILL 矛盾 |
| p4 归档 spec-review 报告（只读） | 回放样本 | 手工加段后 lint PASS、原样 lint FAIL（验证检查生效，不改归档文件——副本上做） |
| `~/.sdflow/workflow/`（软链）+ 消费仓 | 分发面 | setup.sh / `sdflow-init update`，无仓内镜像可漂移（D13 后） |

## Risks / Trade-offs

- **[清理误删承重语义]** → 三层兜：audit 留档逐条可复核（Dc）+ 全仓 pytest（memo C2 的
  22 个文本消费测试）+ code-review 冷层抽查；残余为已接受边角（memo「接受的边角」）。
- **[新 lint 检查误伤旧报告]** → anchor_lint 只在 Step3 对**新生成**报告自检，不回扫归档；
  回放核验在副本上做；bundle（SKILL + lint）同 change 原子更新，无版本skew窗口。
- **[三问 dogfood 时序缺口]** → 结构性事实（spec-review 先于实现），不强行制造；测试 +
  回放为本 change 内验证，真实 dogfood 挂 hand-off 给下一 change 设计审。
- **[references 外迁后无人再读]** → 可接受：外迁物本就是「审计历史才需要」内容（D1 依据）；
  指针一行保留可发现性。

## Migration Plan

1. 三流并行实现（互相独立）；anchor_lint 改动走权威源 `sdflow-init/assets/workflow/`。
2. 部署 = 本仓惯例发布边界：merge 后运行 checkout `git pull` + `bash setup.sh`（软链即时
  生效）；消费仓 `sdflow-init update` 拿新 anchor_lint（本仓项目侧经 `~/.sdflow/workflow/`
  软链自动生效，无独立步骤）。
3. 回滚 = `git revert`（全部为文本/脚本增量，无数据迁移、无状态残留）；SKILL.md 删除的
  考古层内容 revert 即复原。

## Open Questions

（无——可安全后决的未知项不存在；三问措辞的最终中文文案属实现细节，锚定 04 提案 §3.1
三问语义即可。）

## Compliance

- `openspec/rules/doc-authoring.md`（DOC-1）：本 change 即其对 SKILL.md 的落实执行，无豁免。
- `openspec/rules/premise-verification.md`：本 design 引用的代码事实（`anchor_lint.py:70/710`
  结构、`spec-authoring/spec.md:61` SA-03 条款、SKILL 行数）均 2026-08-12 实开核验。
- 四条通则③（不加宽）：不动 ship_gate、不建行数 lint、不改 DOC-1 规则文本。
- `sdflow:principles` 托管块纪律：清理 MUST NOT 触碰托管区块（`sync_principles.py --check`
  门守）。
