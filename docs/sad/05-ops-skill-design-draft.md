# 过程轴文档 skill（工作名 `sdflow-ops`）：设计草案占位

> 状态：**草案占位**（explore D 选项；**未启动、低优先**——是否真做待接地拍板，见 §6 前置）。
> 缘起：`04-ecosystem-boundaries.md` §8 ② 待议——`environments.md`/`testing-strategy.md` 等过程轴文档现由项目自写、无 skill 铺设。本文占位记录「若做，长什么样」，不代表决定要做。
> 命名待定：`sdflow-ops`（operations）为工作名；候选见 §5。
> 引用不复述：判据/生态定位引用 04（生态图）、SAD 边界总则，本文只记 skill 增量。

---

## 1. 定位：补生态的第四轴

现有 skill 各管一轴，过程·操作/方法轴无 skill：

```
空间·当下  → sdflow-architecture (L1 SAD)        ✅
空间·下钻  → sdflow-subsystem    (L2 SSD)        ⬜ 设计中(03)
时间       → sdflow-roadmap                       ✅
过程·操作+方法 → sdflow-ops?（environments/testing-strategy）  ⬜ 本文占位
决策/语言  → 无 skill（ADR/CONTEXT 由 architecture 分家写）
```

`sdflow-ops` 候选职责：铺 + 维护消费项目的 **`environments.md`**（dev/test/deploy 操作）与 **`testing-strategy.md`**（测试方法），并维护 `README`/`CLAUDE.md` 的**概要+引用**块。

## 2. 与 architecture 的接力（已定的上游锚）

architecture 步骤⑤ 5.3 已落「**指出不代写**」——交棒时给出过程轴文档待建 + SAD 投影锚，但不成文。`sdflow-ops` 是**接锚成文**的下游：

```
architecture(SAD skeleton-ready) ──5.3 指路+给锚──▶ sdflow-ops(接锚→成文 environments/testing-strategy)
   锚：§2 约束/§3 外边界/§7 部署/§8 配置策略/§1 可测试性/§5 contract
```

## 3. 候选职责范围（若做）

- **init**：从 SAD 投影锚 + `environments-template-draft.md` 骨架，生成 environments/testing-strategy 初稿（架构锚部分填好、操作槽留空待项目填）；
- **维护**：工具链/CI/部署变更时更新对应节；保持 README/CLAUDE 概要与真相源一致（概要漂移检测）；
- **边界守卫**：拒绝把架构决策（→SAD）、排期（→roadmap）、测试方法混进 environments（复用边界总则的镜像判据）。

## 4. 与 C 选项（模板+项目自写）的张力

| | C 模板+自写（现状+草案） | D `sdflow-ops` skill |
|---|---|---|
| 成本 | 零（已有草案） | 一个新 skill 的建设+维护 |
| 一致性 | 靠人自觉 | 机制保证（概要漂移检测/边界守卫） |
| 适配 | 过程轴跟工程实践走、变化频繁，skill 化可能过度 | 若多项目复用、漂移频发才回本 |

**当前倾向**：C 起步；**D 的触发条件** = 接地发现「项目自写 environments 反复漏建/漂移/违边界」的真实痛点，届时才把草案升级为 skill。**不为对称而对称**（承拆分标准：别为凑齐四轴硬造 skill）。

## 5. 命名候选（待定）

- `sdflow-ops`（operations，涵盖 env+test+操作，工作名）
- `sdflow-environments`（太窄，漏 testing-strategy）
- `sdflow-runbook`（偏部署操作，漏 dev/test）
- 也可能**不单独成 skill**，而并入 `sdflow-init`（铺项目骨架时一并铺过程轴模板）——见 04 §8 B 选项残留

## 6. 前置与开放问题

- **前置（硬）**：先在 mqtt-console **接地真写一份 `environments.md`**（把 `technical-architecture.md`/`testing-strategy.md` 从 roadmap 包搬出、按四层归属整理），暴露真实痛点，再判 C→D 是否值得。**MUST NOT 纸上先建 skill**（同 03/L2 的接地先行纪律）。
- **开放问题**：① 命名（§5）② 是独立 skill 还是并入 sdflow-init ③ 维护触发（手动 vs 随 change/CI 钩子）④ 概要漂移检测的机械化档位 ⑤ testing-strategy 与 environments §2 是否合并（04 待拍的测试环境边界）。

---

## 参考锚

- `04-ecosystem-boundaries.md`（六轴生态、四层归属、真相源分工）· `environments-template-draft.md`（模板草案）
- `sdflow-architecture/SKILL.md` §5.3（上游「指出不代写」锚）· `quality-criteria.md` 边界总则
- 拆分标准：别为凑齐四轴硬造 skill（`CLAUDE.md` §设计基准 4 + change-scope-one-complete-stage-result）
