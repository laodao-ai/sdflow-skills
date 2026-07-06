# Design — adaptive-workflow-routing（Q1=A 收敛版）

> 本 design 为设计门 Q1=A 拍板后的重写版。原 D1–D8 前向机制（HR-TG 双向化/四谓词/掏 L2/route.py 三层归口/calibrator）**已整体放弃**，仅保留「code-review 入口无逻辑面白名单免 Step2」这一最小安全子集。放弃理由见 `spec-review-report.md`（4 冷源：时序矛盾/HR-TG 不可机判/门核正交/ROI 抽空）。

## Context

`sdflow-code-review` 每次全跑多镜 fan-out。实测硬化（spec-workflow:52）要求它「每次全跑、非高风险才跑」，因为多镜 fresh 冷独立能抓循环内被 controller 说服放过的真 bug。但对**结构上无行为面**的 diff（纯注释/文档、仅加测试、纯版本号），多镜结构上零产出——免之无损。本 change 把这一窄豁免机判化、落地。

冷审教训（写入 design 供后人）：**「在 diff 存在前用脚本机判语义复杂度」不成立**——谓词多为 diff 派生（净行/形状），而路由/声明本想发生在 ff/grill（diff 前）；HR-TG 成员是语义触发、今天由模型判非脚本。故 A 把豁免限定在**唯一真正机判可靠的时刻与对象**：code-review 入口（diff 已在）× 无逻辑面形状（结构可判）。

## Goals / Non-Goals

**Goals:**
- 让**机判证明零产出**的形状（注释/文档/纯测试/展示版本号）免 code-review Step2 多镜，省 fan-out 成本、零语义风险。
- 豁免**纯机判**（不依赖作者自评）、**post-diff**（diff 已存在）、**语言感知**、**行为面路径豁免**兜住 bundle 自身 markdown。

**Non-Goals:**
- 前向路由 / 非平凡谓词 / 平凡声明 / HR-TG 双向化 / calibrator / grill-spec-review 轻量化（Q1=A 全弃）。
- 覆盖「有逻辑面的 routine change」——有逻辑一律 Step2 照跑。

## Decisions

### A1 · 豁免在 code-review 入口判、对象=无逻辑面形状（而非 ff 前路由）

**决定**：轻量化时刻 = **code-review Step2 之前**（diff 已存在）；对象 = **机判无逻辑面白名单形状**。Step1 恒跑、有逻辑面 Step2 全跑。
**理由**：消除原设计的时序矛盾（diff 派生谓词却在 diff 前判）——形状判定天然需要 diff，放到 code-review 入口才可机判。code-review 是最后一道找新 bug 的门，故守卫从严：Step1 恒跑当地板。
**备选否决**：ff 前路由（冷审证不可机判）；覆盖有逻辑 routine（收益薄且不可靠，见 report Q1）。

### A2 · 白名单三形状 + 语言感知判器（非裸正则）

**决定**：白名单 = ①仅动注释/纯文档行 ②仅新增 `tests/` 下文件（排除生产码 import 的 helper 如 `conftest.py`）③仅改无 code-path 依赖的纯展示版本常量（整行匹配 `^\s*<IDENT>\s*=\s*<version-literal>\s*$`、拒附加 token）。判器 MUST 语言感知（按语言解析注释/块注释/多行字符串边界）。
**理由**：裸正则前缀无法跟踪块注释状态、多行字符串、语言混排（冷审 A-F1/C3）——会把携逻辑行误判注释。版本常量整行+拒 token 防夹带 load-bearing 常量（`API_VERSION`/`SCHEMA_VERSION` 切 code-path）。
**备选否决**：裸正则（不可靠）；「仅动 markdown 文档」宽泛豁免（本 repo markdown 承载行为，见 A3）。

### A3 · 行为面路径豁免清单（吸收原 TG-27 元层护栏，与部署解耦）

**决定**：diff 触及 workflow bundle 自身（`sdflow-init/assets/workflow/**`、编排/评审 `SKILL.md`、`workflow.md`、`ship_gate.py`、判器脚本）→ 判器 MUST 判 NOT 无逻辑面，即便 diff 形状=仅动 markdown。**硬编码路径前缀、不查 HR-TG 表、与是否部署无关**。
**理由**：本 bundle 的编排/评审逻辑就写在 SKILL.md/workflow.md 等 markdown 里（冷审 C1 本repo致命）——「markdown=文档」在此是伪命题。硬编码路径护栏解掉原设计 TG-27 自指引导期（冷审 E2）：改评审机制自身的 change 永不被误免，无需等 TG-27 部署。
**备选否决**：靠 HR-TG/TG-27 判元层（不可脚本化 + 引导期自豁免，冷审 A2/E2）。

### A4 · 判器沿 ship_gate.py 纪律，Step1 scope-drift 守卫豁免

**决定**：判器为 `assets/workflow/tools/` 下确定性脚本，沿 `ship_gate.py`：只读、git-harden（`core.quotePath=false`/`errors=replace`）、双输出（human + JSON）、`--change`/`--root` 纯参数无写盘。豁免 MUST 由 Step1 scope-drift 守卫——揭出隐藏逻辑 → 白名单判定作废 → Step2 照跑。
**理由**：判器读 git diff 判形状，需 git-harden 防非 UTF-8 逸出（冷审 D3）。Step1 恒跑是「伪装成注释的逻辑改」的兜底（冷审 A-F5.4：加错的测试/伪装注释）。
**备选否决**：判器读散文声明（本 A 无平凡声明，判器只读 diff，故不涉 fence-aware 假阳场景——原 D3 顾虑随平凡声明取消而消解）。

### 组件清单

| 组件 | 类型 | owns |
|---|---|---|
| `assets/workflow/tools/<判器>.py`（新） | 脚本 | 无逻辑面形状机判（语言感知 + 行为面路径豁免）+ 双输出 |
| `sdflow-code-review/SKILL.md` | 指令（改） | Step2 前调判器；命中→免 Step2、Step1 恒跑守卫 |
| `spec-workflow` code-review 需求 | 需求（改，原标题） | 两层深度 + 白名单豁免规范 |

### 判器决策流

```
  code-review 入口（diff 已存在，Step1 已跑）
        │
        ▼  判器 [脚本·post-diff·语言感知]
   diff 触行为面路径清单(bundle/SKILL/gate/workflow.md)?
        │yes → NOT 无逻辑面 → Step2 照跑
        │no
        ▼
   diff 仅匹配白名单形状(注释/文档-only ∨ tests/-only ∨ 展示版本常量)?
        │no  → Step2 照跑
        │yes
        ▼
   Step1 scope-drift 有隐藏逻辑?
        │yes → 白名单作废 → Step2 照跑
        │no  → 免 Step2（结构零产出）· 仍产报告
```

## Risks / Trade-offs

- **[语言感知判器实现复杂：跨语言注释/块注释/多行字符串]** → 起手只支持有把握的语言子集 + 明确单行注释语言，不确定即判 NOT 无逻辑面（保守偏 Step2 照跑）。
- **[消费仓自己的「markdown=行为」文件（prompt/config-as-markdown）]** → A3 路径清单只护 sdflow bundle 自身，护不住任意消费仓的行为-markdown。**保守处理**：白名单形状①的「纯文档」MUST 限定为**约定文档路径**（`README*`/`CHANGELOG*`/`docs/**`/`*.txt`）+ **代码内注释行**（语言感知）；**任意其他 `.md`（含消费仓根级/散落 markdown）默认判 NOT 无逻辑面**（可能承载行为）——宁可少免、不误免。消费仓若要扩展自己的文档路径，走 config（本 change 不做，留 todolist）。
- **[tests/ 免多镜放过「加错的测试」]** → tests/ 豁免由 Step1 scope-drift + 「排除生产码 import 的 helper」双重收窄；仍属已知残余，收益（省纯加测试的多镜）对价小。
- **[收益窄]** → 诚实接受：A 只省三类形状的 Step2，是「安全的省」的最大子集；更宽的省已证不安全/不可机判（report Q1）。

## Migration Plan

- 属 `assets/workflow/` 权威源改动 → merge 后 push → 运行 checkout `/sdflow-upgrade`。
- **向后兼容**：默认 = 全 FULL；豁免是 opt-in 机判（命中白名单形状 ∧ 不触行为面路径 ∧ scope-drift 无隐藏逻辑）——存量流程不变松。
- **回滚**：停用判器 = 恢复「Step2 每次全跑」现状。

## Open Questions

（无阻塞）。判器支持的语言子集起手范围可在实现期按有把握程度定（保守未支持语言一律判 NOT 无逻辑面）。

## Compliance

- 承 adr/0004 设计门红线不削弱；承 spec-workflow「code-review 每次全跑」实测硬化（不变式保留、仅机判零产出形状免多镜、非高风险才跑）；承 `grill-not-skippable`（不碰 grill）。
- 冷审放弃的前向机制风险（时序/HR-TG机判/门核正交/calibrator偏差）随 A 收敛**全部消解**（无对应组件）。
