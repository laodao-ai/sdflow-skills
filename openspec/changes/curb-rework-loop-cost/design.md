## Context

动机与实测数据见 [`proposal.md`](./proposal.md) - Why。此处只列解释方案所需的现状与约束。

**现状的四个边界控制点**，其中三个当前交给模型当场判断：

```
                     sdflow-implement                      sdflow-code-review
  ┌──────────────────────────────────────────────┐   ┌──────────────────────────┐
  │  出票模式                                     │   │  fan-out 多镜             │
  │   └─[闸门①]验收标准约束 :270                  │   │   └─ Step4 自动修         │
  │       现状 = 无语法面有界性判据 ─────⑤        │   │       └─[边界④]复审轮数   │
  │                                              │   │           现状 = 无规定    │
  │  执行模式（每 ticket）                        │   │           无终止条件 ──⑥  │
  │   ├─ implementer ──[TDD 契约 :509]──⑨        │   └──────────────────────────┘
  │   ├─ 双轴审 ──[review package :583]──③        │            ▲
  │   └─[边界②]熔断 :651-657                      │            │ 文档分叉：
  │       现状 = 同文件+问题指纹（可换马甲绕过）─④  │            │ implement:349,353 称其有 fix 循环
  │                                              │            │ code-review:181 称「无 re-review 紧闭环」
  │  收尾票                                       │────────────┘
  │   └─[边界③]测试范围 :313-330                  │
  │       现状 = 每轮全量（实际打折执行）──①②      │
  └──────────────────────────────────────────────┘
                          │
                          ▼  证据 schema 锚 SHA
                   sdflow-done / verify（本 change 不动）
```

**约束**：

- `sdflow-implement/SKILL.md:330-332` 的「所有判通过的行锚同一最终 SHA」是既有正确性契约，**本设计不触碰**。
- 零依赖不变量与 GC-2 边界锁不在本 change 范围内（见 proposal - Non-Goals）。
- 下游消费仓经 symlink（SKILL）与 `sdflow-init update`（bundle/模板）两条独立分发链，二者不同步。

## Goals / Non-Goals

范围见 proposal。此处只补设计级边界：

**Goals**

- 四个边界控制点的判据一律**尽可能**由确定信息界定，失效方向为 fail-safe。
- 配置扩展对未配置的消费仓**行为等价于今天**（缺档位退化为单命令）。

**Non-Goals**

- 不为复审轮数上界新增机械门（`ship_gate` 不动）——本 change 取指令层约束，机械化留待有确定性捕获路径时再议。
- 不改变证据 schema 的字段形状（`<层>|<命令>|<退出码>|<SHA>` 保持不变），只改「哪些行在哪一轮产生」。
- 不统一 `sdflow-implement` 与 `sdflow-code-review` 的循环**实现**，只统一二者对该循环的**表述**。

## Decisions

本 change 的决策全文与砍掉的候选见 [`decision-memo.md`](./decision-memo.md)。

设计原则落 [`openspec/adr/0035`](../../adr/0035-rework-loop-bounds-by-determinate-signals.md)（TG-23）：返工循环的边界由确定信息与硬上限界定，不由模型判断界定；上位原则为 `CONTEXT.md` 的「盘面即状态」。

## 数据模型与生命周期（TG-05）

本 change 唯一涉及的数据对象是 `openspec/config.yaml` 的 `test-suites` 键。

**形状变更**：

```yaml
# 今天（单命令，继续有效）
test-suites:
  unit: pytest
  integration: make integration
  e2e: make e2e

# 扩展后（两档，任一层可独立选用）
test-suites:
  unit: pytest                      # 未分档 → quick 与 full 同命令
  integration:
    quick: make integration-fast
    full:  make integration
  e2e:
    full:  make e2e                 # 只配 full → quick 判「本层无 quick 档」
```

**解析规则**：值为字符串 ⇒ 两档同命令；值为映射 ⇒ 读 `quick` / `full` 两键，缺 `quick` 视为该层无 quick 档，缺 `full` 视为未分档（quick=full 同命令）。**unit 层例外**：unit 在中间轮 MUST 始终跑——若无 quick 则取 full，MUST NOT 因「无 quick 档」跳过 unit（此约束仅适用于 unit 层；集成/e2e 缺 quick 时中间轮可推迟到收口）。

**发现与更新**：`test-suites` 的具体命令因项目而异，由 `sdflow-devenv`（环境初始化 skill）运行时调研项目情况后推荐写入 `config.yaml`。本 change 只定义 schema 与消费语义，不硬编码特定命令。

**生命周期**：由 `sdflow-init` 的 `config.template.yaml` 铺设初值；消费仓可手改；`sdflow-init update` 不覆盖消费仓已有的 `test-suites`（沿用 `handle_config` 既有 update 语义）。**无迁移动作**——旧形状是新形状的合法子集。

## Risks / Trade-offs

- **[集成层回归推迟到收口才暴露，修复更贵]** → 收口全量必然抓到；且现状是中间轮**根本没被可靠跑过**（8 红测实证），修正后严格优于现状。已在 `decision-memo.md` 的「接受的边角」按五问记录。
- **[① 落地但 ② 未落地 ⇒ 收口那次全量仍由 implementer 临时判定范围，退化回今天]** → 二者列为同批 P0，任务上 ② 的配置解析先于 ① 的条款改写；验收以「收口证据行锚同一 SHA」为结构判据，间接要求命令来源确定。
- **[硬上限阈值误伤真·不同问题]** → 熔断处置是**升 strong 档仲裁**而非直接放过，代价有界；阈值可调，落地后按实际误伤率调整。
- **[⑤ 是指令层约束，出票时仍可能漏判]** → ⑫ 的对照表降低漏判率；漏判的后果是退化为今天的状态，不比现状更差。**MUST NOT 在任何产物中声称 ⑤ 是机械保证。**
- **[⑥ 规定「只审修复 diff」，若修复引入了 diff 之外的连带影响则审不到]** → 该风险由 `sdflow-done` 的 verify（位于所有修复之后）兜底；本 change 不扩张 verify 职责。
- **[两条分发链不同步：SKILL 经 symlink 即时生效，config 模板须 `sdflow-init update`]** → 扩展设计为向后兼容，新 SKILL 读到旧 config（无 quick 档）时按单命令处理，**窗口期无破坏**。

## Migration Plan

1. **② 先行**：`config.template.yaml` 增 `test-suites` 两档示例 + 解析规则落 `sdflow-implement/SKILL.md` 的聚合套件发现契约。旧形状继续有效，无需下游动作。
2. **① 随后**：改写单一盘面条款（`:328-330`），中间轮范围改由确定信息界定，收口保留全量 + 同 SHA 锚。
3. **④⑤⑨③** 各自独立改 `sdflow-implement/SKILL.md` 对应段落，互不依赖。
4. **⑥** 改 `sdflow-code-review/SKILL.md`（新增复审边界）+ 对齐 `sdflow-implement:349,353` 与 `code-review:181` 的表述。
5. **⑫** 增 `sdflow-devenv/references/verification-patterns.md` 一节。
6. **spec 同步**：`impl-orchestration` 与 `spec-workflow` 的 delta 随 change 归档时同步进主规格。

**回滚**：revert 本 change 的 commit 集合即可——所有改动是 prose 契约与配置模板，无数据迁移、无状态残留。已按新契约跑过的 change 其证据 schema 形状未变，不受影响。

## Open Questions

无。⑪、体检工具、test impact analysis 均已明确列入 proposal - Non-Goals，不是待答问题。

## Compliance

- **遵守 CLAUDE.md 基准 5（无界语法禁手搓）**：⑤ 正是该基准向出票环节的下沉；本 change 自身不引入任何解析器。
- **遵守通则③（不加宽）**：⑪ 与体检工具虽相关但明确排除，不顺手做；零依赖不变量不顺手改。
- **遵守通则④（简化优先）**：不为「阈值多少轮才最优」反复调参，取启发式并记为假设；不设定量耗时阈值。
- **遵守 `adr/0018` 的机械/语义划分**：⑤⑥ 属指令层约束，产物中已显式标注 MUST NOT 声称机械保证，不伪装成机械门。
- **遵守 DOC-1（正文即最终态）**：本设计正文只写目标态；被砍候选与演进理由留在 `decision-memo.md` 与 `adr/0035`。
