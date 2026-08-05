# Design: refactor-roadmap-internalize-deps

## Context

现状（动机见 proposal.md · Why，不复述）：

- `sdflow-roadmap/SKILL.md` 635 行，讨论层为三分支路由（explore / wayfinder 长档 /
  office-hours 前置验证），其中 wayfinder 机械（footage 落盘、map 再入、tracker preflight、
  基线记录、checklist ④、陷阱 7）约 150+ 行，且携带宿主探测 + 三层降级路径。
- 同构参照 = `sdflow-spec/SKILL.md` 的三相位结构（A 澄清 → B 拷问 + 纪要增量落盘 → C 生成），
  其「B 轮数无上界 ⇒ 增量落盘收窄中断损失」的结构已在 change 生产路径实证。
- 正式契约面 = `openspec/specs/roadmap-planning/spec.md`（176 行），4 个 Requirement 锚定
  被删机制（承重约束 C2）。
- 决策与约束的单一源 = 本 change `decision-memo.md`（D1–D14 / C1–C10），本文不复述其内容。

约束：SKILL.md 重写 MUST 保留 `sdflow:principles` 托管块原样（`sync_principles.py --check`
是 setup.sh 门禁）；「考古层」在 DOC-1 语境另有语义，改名仅限 roadmap 语境（C5）；
bundle 文件改动受 dev checkout 纪律约束（改后重跑 setup.sh，经 `sdflow-init update` 推下游）。

## Goals / Non-Goals

**Goals（设计层）：**

- 新 SKILL.md 的相位协议与 sdflow-spec 逐节同构（起手判定 → 增量落盘 → 收敛定稿 → 生成 →
  收尾门），差异只保留在「产物形态」（三件套直写 vs 四件套经 CLI）与「无 ship gate ⇒ memo
  轻量化」两处（D4）。
- 所有被删机制在 spec delta 中成对处理（删机制 = 删/改对应 Requirement + Scenario），
  不留悬空 SHALL。
- 存量兼容零告警刷屏：requirements.md 兼容模式与 footage 冻结共用同一条款结构（至多一行提示）。

**Non-Goals（设计层，proposal Non-Goals 之外）：**

- 不为 memo 设计机械核验门（D4 已拍板轻量化，无 hash/schema 断言脚本）。
- 不设计存量 footage → memo 的自动转录工具（冻结即可，手工转录是重入时的例外路径）。

## 组件与依赖〔TG-14 · BASE-25〕

### 外部依赖图（before → after）

```
before:
  sdflow-roadmap ──┬─▶ /opsx:explore（分支 A）
                   ├─▶ wayfinder（分支 B）──┬─▶ /grilling（票内）
                   │                        ├─▶ /domain-modeling（票内）
                   │                        └─▶ openspec/matt/issue-tracker.md（preflight）
                   ├─▶ /office-hours（分支 C）
                   └─▶ /plan-eng-review · /autoplan（review 层）

after:
  （上游可选：/opsx:explore，想法未成形时先发散——非 skill 内部分支）
  sdflow-roadmap ──▶ /plan-eng-review · /autoplan（review 层，唯一保留的外部 skill 依赖）
```

### 改动组件清单

| 组件 | 动作 | 要点 |
|---|---|---|
| `sdflow-roadmap/SKILL.md` | 重写 | 三相位骨架，见下方「新 SKILL.md 骨架」 |
| `sdflow-roadmap/references/memo-template.md` | 重写 | B 相位纪要模板（头部包名+日期，承重约束/拍板决策小节） |
| `references/design|roadmap|task-log-template.md` | 术语改 | 商业化信号/生成/历史存档；结构不动 |
| `references/long-flow-skill-paradigm.md` | 局部改 | wayfinder 段落改历史注记 |
| `openspec/specs/roadmap-planning/spec.md` | delta | 4 ADDED / 3 MODIFIED / 3 REMOVED（机制替换与更名走删+增） |
| `openspec/matt/`（4 文件） | 删除 | D2；无其他运行时消费方（C1） |
| CLAUDE.md / AGENTS.md | 删区块 | matt 三区块 + roadmaps 目录描述行去 footage |
| `sdflow-init/assets/workflow/ff-generation-constraints.md` | 加注 | `wayfinder-resolved:` 前缀标 legacy（D10） |
| `sdflow-init/assets/workflow/workflow-history.md` | 追加 | 一条移除记录 |
| `openspec/CONTEXT.md` | 词条 | footage → 历史存档定义；新增商业化信号（D14） |
| `openspec/adr/` | 新增 | 讨论层内化与 matt 移除（D14） |
| `openspec/issues/`（T134） | 关闭 | OBSOLETE + evidence（D11） |
| `docs/external-dependencies.md` | 更新 | 删 wayfinder/grilling/domain-modeling 节 |

### 新 SKILL.md 骨架

frontmatter（触发面重写，去 wayfinder）→ principles 托管块（原样）→ 定位与层级表（保留）→
三相位总览 + 判定留痕总则（三判定点重编号）→ 硬性规则 1–5（规则 3 改「历史存档」）→
产出模式（存量兼容 ×2 / 逃生舱 / create·continue·replan——判定前移至 B 起手）→
相位 A（澄清 + gate-0 + 商业化信号检查 → 三态路由，判定点①）→
相位 B（起手四步 / 七维拷问与裁剪表 / 术语·ADR 提议制 / 增量落盘 / 停止条件 / 重入 / 放弃清理）→
相位 C（生成三件套 / 近细远雾，保留）→ review 分档（判定点②，仅改术语）→
收尾 checklist 四项（判定点③）→ 命名规范 / 下游阶段实施（保留）→ 常见陷阱（删 7、改 3）→
CLAUDE.md 配合（去 footage 行）→ 参考模板。

## 三态路由决策图〔TG-12〕

```
入口（人触发 /sdflow-roadmap；想法未成形 ⇒ 建议先 opsx:explore 再回来）
  │
  ▼
相位 A：澄清 → gate-0 五项 + 商业化信号检查（两关独立，判定点①显式留痕）
  │
  ├─ gate-0 过 ∧ 无商业化信号 ──────────────▶ 相位 C 直接生成（此路径才在生成时建目录）
  ├─ gate-0 过 ∧ 商业化信号命中 ─▶ 相位 B（裁剪到维度①，Q3 作追问弹药）─▶ 相位 C
  └─ gate-0 未过 ──────────────▶ 相位 B（按信号裁剪七维）──────────────▶ 相位 C
                                    技术重构 → ②③④⑤⑦ 为主
                                    新产品/新项目 → ①②④⑤⑥⑦ 全跑
                                    商业化信号命中 → ① 加重（startup 味逼问）
```

七维 = ①需求真实性 ②现状分析 ③阶段划分压力测试 ④最小可行首阶段 ⑤架构路线对比
⑥术语/概念澄清 ⑦前提质疑（吸收映射见 proposal · What Changes；词表内联 SKILL.md，D13）。

## 包与相位状态机〔TG-09 · BASE-19〕

```
                    ┌────────────（放弃 ⇒ 删包目录；continue/replan 场景只删本次新增）
                    │
absent ──A收束，B起手：定名 + 生命周期判定(create/continue/replan) + 建目录 + 草稿memo──▶ B-draft
                                                                                        │
   （直接生成路径：absent ──gate-0过∧无信号──▶ 生成中(建目录) ──▶ 三件套就绪）          │拷问收敛
                                                                                        ▼
定稿包 ◀──收尾四项过（判定点③）── review+处置（判定点②）◀── 三件套就绪 ◀──C生成── memo定稿
```

- **重入**（异常转换）：新 session 探测 `openspec/roadmaps/*/memo.md` 存在且无定稿标记 ⇒
  呈现包 + memo 摘要，问人「继续 B / 新开」——续则回 B-draft，不静默复用。
- **既有包**（continue/replan）：生命周期判定在 B 起手完成（前移，D9），replan 先落
  task-log 重规划记录再动文件（现行条款保留）。

## Decisions

本 change 的决策全文、依据与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)
（D1–D14，承重约束 C1–C10，三镜代价见其「三镜代价」节）。

## Risks / Trade-offs

- **[同串双语义误替换]**「考古层」（DOC-1 语境）被连带改名 → 改名操作按 C5 范围限定逐文件做，
  完成后 grep `考古层` 核对：`openspec/rules/`、BASE-30、T169、CLAUDE.md:183-184 必须原样。
- **[SKILL.md 重写破坏托管块]** principles 区块被动 → 重写以「区块外全重写、区块内零字节不动」
  执行，收尾跑 `python3 hack/sync_principles.py --check`（setup.sh 门禁同款）。
- **[bundle 窗口期]** assets/workflow 改动后未重跑 setup.sh ⇒ 全局 canonical 陈旧 →
  实施任务显式含「dev checkout 跑 `bash setup.sh`」步骤（CLAUDE.md 纪律）。
- **[存量包续跑回归]** 冻结条款写漏某接触点（如 checklist ③ 未覆盖 footage/）→ 以
  `issues-triage-2026-08` 包做一次续跑演练（Success Metrics 第 5 条）。
- **[下游消费仓漂移]** 下游先 pull skill（symlink 即时）后 update bundle ⇒ 短期内旧
  `wayfinder-resolved:` 规则原文与新 SKILL 并存 → 前缀规则本身保留只加注（D10），两态兼容，
  无行为冲突。
- **[术语改名遗漏]** 「野心/结晶」残留 → 收尾 grep 不带 `--include` 全量扫（含 .py/.sh/.yml），
  历史文档（docs/、archive/）白名单排除。

## Migration Plan

实施顺序（同 tasks 相位展开）：

1. SKILL.md 重写 + references 模板（skill 面先成形）。
2. roadmap-planning spec delta（契约面跟上，与 1 同 change 内成对）。
3. matt 移除：删 `openspec/matt/` + CLAUDE.md/AGENTS.md 区块。
4. bundle 两文件（legacy 标注 + 演进记录）→ dev checkout 跑 `bash setup.sh`。
5. 治理收尾：ADR + CONTEXT.md 词条 + T134 关闭 + external-dependencies.md 更新 +
   INDEX.md 摘要行 + handoff 草稿删除。
6. 验证：全仓 pytest + sync_principles --check + 全量 grep 残留扫描 + 存量包续跑演练。

**回滚**：单分支未合并前 `git checkout main` 即净；合并后回滚 = revert merge commit
（matt 目录、CLAUDE.md 区块随 revert 恢复，无不可逆动作；全局 `~/.claude/skills/` 为
symlink，源恢复即恢复）。

## Open Questions

（无——可安全后置的未知项没有；全部决策已在相位 B 拍板。）

## Compliance

- 遵守 `openspec/rules/doc-authoring.md`（DOC-1）：本文正文只写目标态，演进过程在
  decision-memo（本 change 的过程件）。
- 遵守 `openspec/rules/premise-verification.md`：承重断言均有 C1–C10 证据锚。
- 遵守 CLAUDE.md 设计基准 1–5：无新增机械门（基准 1 的残余划分——收尾 checklist ① 的
  既有脚本门不动）；目标态导向（C6 三态路由不照 handoff 缩水）；无手搓解析器。
- 无豁免项。
