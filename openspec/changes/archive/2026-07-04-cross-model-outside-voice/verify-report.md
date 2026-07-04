# Verify Report — cross-model-outside-voice

- 日期：2026-07-04
- Change：cross-model-outside-voice
- 验证者：sdflow verify（Do-Not-Trust 冷启动，逐需求锚点核验，不信复选框/报告）

## 结论：PASS

<!-- ship-gate: verify=PASS -->

30/30 pytest 全绿；R1–R6 六条 Requirement 均有可机验证据锚点（helper 契约代码 + pytest + 两 SKILL 锚行/协议节 + workflow 规则行）。发现仅为 Minor 级台账/条件项瑕疵，无核心功能缺口。

## 逐需求核对表

### ADDED Requirements（specs/spec-workflow/spec.md）

| 需求 | 代码出处（文件:行 / 测试名） | 状态 |
|---|---|---|
| **R1** 跨模型 outside voice 默认开、失败回落、非阻塞；v1 锚行；收尾自检 | `outside-voice.sh:129-137`（preflight 三态）、`:91-124`（exec 硬编码 `-s read-only --ephemeral`+`--output-last-message`+timeout 124）；`test_outside_voice.py` 30 passed；两 SKILL 「helper 调用协议」节（spec `:130-147`/code `:112-129`）+ 锚行 `sdflow:outside-voice v1`；收尾自检 spec `:78`/code `:105` | ✅ |
| **R2** outside-voice 复用挂反静默守卫（来源→新鲜度→结构三前置） | `sdflow-spec-review/SKILL.md:39-43`（①simulated 无效 ②stale ③结构，原因码 file-missing\|section-not-found\|zero-findings\|stale\|simulated-source + 回落自跑 + 「仅补偿切片」措辞）；`:27` autoplan 未跑必自跑（P2b 交叉引用 `:41-43`） | ✅ |
| **R3** HR-TG 子集判定并留痕（`sdflow:hr-tg v1`） | spec `:57` / code `:68`（命中集 ∩ HR-TG，正反均写报告 + evidence 必填）；单一源 `trigger-catalog.md:127-131`（成员 TG-04/06/07/08/09/16/17/26） | ✅ |
| **R4** tension 不静默采纳；`runner=codex` 免 <80 滤、`claude-fallback` 照过 | code `:88`（豁免文法）、`:100`（裁决按 runner 分桶）、`:97` defer→buglist/todolist+hand-off；spec `:77` TENSION 进决策登记区 | ✅ |
| **R5** 广审层原生执行、模拟显式降级（`sdflow:step1-broad-review v1`） | spec `:35-37`（原生执行+主 session 落盘 gstack-review.md+native/simulated 锚行）；code `:60-61`（gstack /review 原生+降级标注） | ✅ |
| **R6** gstack 边界守恒（只依赖 codex CLI） | `grep -E '\.gstack/(bin\|sessions)\|gstack-config\|gstack-repo-mode\|gstack-codex-probe\|skills/gstack' outside-voice.sh` → **零命中**；helper 仅调 codex/git/timeout | ✅ |

### tasks.md 分组核对

| 任务组 | 代码出处 | 状态 |
|---|---|---|
| §1 共享 helper（1.1–1.6） | `outside-voice.sh` 全（preflight/exec/render-prompt/version/secret_scan/截断）；`setup.sh:145-150` hack 循环覆盖；`test_outside_voice.py` 30 passed；`.gitignore:18-19` `**/.outside-voice/` | ✅ |
| §2 T25 前置 Step1 原生执行（2.1–2.4） | spec `:35-37`、code `:60-61` 原生执行+降级+v1 锚行 | ✅（2.4 dry-run 为一次性过程验证，SKILL 手术已就位且自洽） |
| §3 spec-review 接入（3.1–3.4） | spec `:39-43`（守卫）、`:27`（P2b MUST）、`:57`（HR-TG）、`:77/:79-97`（TENSION 决策登记区） | ✅ |
| §4 code-review 接入（4.1–4.6） | code `:81`（always code-voice 子步）、`:116`（helper `[ -x ]` 前置检查+缺失提示）、`:68`（HR-TG）、`:88/:97/:100`（豁免/defer/分桶）、`:105`（锚行自检+findings diff） | ✅ |
| §5 trigger-catalog & 契约套件（5.1–5.5） | `trigger-catalog.md:72`（TG-26 行）+`:127-131`（HR-TG 附录）+`:4/:101-133`（五层四处同步）；`design-diagrams.md:45`（TG-26→序列图）；`backend-go.md:15`（CR-GO-06）；`workflow.md:56/:76/:91`（子步引用）；`INDEX.md:16`（TG-01~26 + 五层） | ✅ |
| §6 边界核验与冒烟（6.1–6.2） | 6.1 权威判据 grep 零命中（已验）；6.2 无 codex fallback 由 preflight not_installed→fallback 分支覆盖（`preflight:130-131` + 协议 code `:118`） | ✅ |
| §7 收尾同步（7.1–7.3） | 7.1 pytest 30 passed；7.2 `ROADMAP.md:13` Phase C 状态推进；7.3 `todolist/2026-07-todolist.md:33` T25=DONE | ⚠️ Minor（见下） |

## 缺口清单

### 核心缺口
- 无。

### Minor（PASS 附注，不阻塞）
1. **T25 台账关联对象**（7.3）：`2026-07-todolist.md:33` T25 已 DONE，但 change/commit 列记为 `sdflow-ship` 而非本 change `cross-model-outside-voice`。R5 功能本体（原生执行）已在两 SKILL 落地，属 bookkeeping 归属瑕疵。
2. **CONTEXT.md 缺失**（7.2）：仓库无 CONTEXT.md，HR-TG 术语未补录；但 7.2 措辞为「如需补术语」条件项，ROADMAP 已推进，非硬性缺口。
3. **preflight 三态 vs tasks 1.1「二态」**：实现为 ready/not_installed/missing-deps 三态（多一个 timeout 缺失探测），是对规格的超集加固，R1「codex 未装即天然关停」语义完好，非缺陷。
4. **过程型验证任务**（1.4 dev setup.sh、2.4 dry-run、6.2 fallback 冒烟）：属一次性运行验证，无持久化产物可锚定；其所验证的 SKILL 手术与 helper 分支均已就位且自洽，标记完成合理。

---

PASS — R1–R6 六条 Requirement 全部具备可机验证据锚点（helper 契约代码 + 30/30 pytest + 两 SKILL 锚行/协议节 + workflow 五处规则行 + gstack 边界 grep 零命中）；残留仅 Minor 级台账归属与条件项，无核心功能缺失。
