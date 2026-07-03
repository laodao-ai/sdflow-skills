---
name: spec-review
description: >
  阶段二「设计评审编排器」——把 autoplan（广审）+ 本项目标准的并行多镜审（领域镜 + 对抗镜 + 接地镜）
  编排成一次连续跑、产出**一份** spec-review-report.md 的评审。主 session（强模型）协调：Step1 跑
  autoplan 吃其 findings，Step2 fan-out 多个 fresh 子代理并行审本项目标准，Step3 去重合并 + 对抗裁决 →
  一份报告。**中途不打断**——撞到"≥2 方案 / 核验不了的事实"不 AskUserQuestion，而是写进报告「决策登记区」
  （选项 + 推荐 + 两方后果），人工在设计 HARD-GATE 一次性过报告拍板。**不依赖 /clear**——子代理 fresh
  context 即独立性。只审 prevention（config 固化的结构/约束）焊不住的残差：①Validation ②对抗 ③接地读码。
  与 autoplan 互补不重复（autoplan 已含 eng 镜）。出报告标 [spec-review-amendment]。Trigger with /spec-review。
---

# spec-review — 阶段二设计评审编排器

把 workflow 规则集的 `spec-review.md`（经 resolve-workflow.sh 解析，Detection 方法论）+ `spec-checklists/domains/`（领域 R 项）
操作化为一次**连续跑的编排评审**：Step1 autoplan（广审）→ Step2 并行多镜（本项目标准）→ Step3 合并成
**一份** `spec-review-report.md`。取代旧"autoplan + spec-review 各出报告 + 人工手动合并（旧 step 7）"三步。

> **两条连续性铁律（阶段二自动流的前提）**：
> - **不依赖 `/clear`（G1）**：评审 fan-out 到 fresh-context 子代理，独立性由"子代理冷上下文"给，不由 `/clear` 给。
>   主 session 携带生成历史进裁决，接受一丝合成层偏置——但**反静默压制**焊死其边界（见 Step3）。
> - **中途不 AskUserQuestion（G2）**：撞到决策点写进报告「决策登记区」，继续跑完；人工在设计 HARD-GATE
>   一次性过报告拍板。评审 findings 互相独立不级联，攒到报告一次决即可（且报告摊开两方后果，比中途弹窗看得全）。

---

## 第零步：确认对象 + 读规则

1. 未指定变更则 `openspec list` 让用户确认。记 `{change_dir}` = `openspec/changes/{name}/`。
2. 规则根解析：`[ -x ~/.sdflow/hack/resolve-workflow.sh ]` 不成立 → 提示「resolve-workflow.sh 未安装——先在运行 checkout（~/.skills/sdflow-skills）跑 bash setup.sh」并降级通用评审；否则 `RULES_ROOT=$(~/.sdflow/hack/resolve-workflow.sh --root "$(git rev-parse --show-toplevel)")`——退出码 2 → 显式降级通用评审并原样转发脚本 stderr 告警（绝不静默当"本项目无此评审层"）；成功 → 读 `$RULES_ROOT/spec-review.md`（方法论）、`$RULES_ROOT/trigger-catalog.md`（触发）。禁止自行重实现三步链。

## 第一步：autoplan 子步（广审，吃其 findings）

1. 对 `{change_dir}` 跑 autoplan（gstack 广审 CEO/design/eng/DX·自动决策），评审结论写入 `{change_dir}/gstack-review.md`，改动标 `[gstack-amendment]`。autoplan 跑自己的流程，prompt 不注入。
2. **吃其 findings**：读 `gstack-review.md`，把 autoplan 的 findings + 自动决策纳入 Step3 的合并池（autoplan 的自动决策也登记进报告决策区）。
3. **反静默守卫（显形部分）**：若 `gstack-review.md` **缺失 / 解析不出**，**打印显式降级日志**（"autoplan 输出未找到 → 本次缺广审层"），**绝不静默当'无此层'跑过**。
   > 〔Phase C 补〕完整的 outside-voice 复用（读 gstack-review.md 的 codex outside-voice 段 + 缺失时**回落自跑 codex 设计 voice** + 命中 HR-TG 单开领域 cross-model）属 Phase C（C2/C4）。Phase A 只做"跑 autoplan + 吃 findings + 缺失显式记降级"，不实现回落自跑与 cross-model。
4. **checkpoint 提交（P2c 第 1 次）**：`~/.sdflow/hack/checkpoint-commit.sh spec-review-autoplan "autoplan 广审 + gstack-amendment"`。

## 第二步：规划镜头 + 并行 fan-out 子代理（本项目标准）

**规划镜头（主 session）**：

- 按 `{change_dir}` 实际涉及的栈 + 内容判命中的 TG/领域 → 决定开哪几个**领域镜**（backend·go / embedded·ml307c·esp32 / frontend）。
- 按风险定**对抗镜**数量：普通 2 个，高风险 3 个。固定 1 个**接地镜**（机械读码核验）。
- 只审命中的；config 已固化的结构/占位/一致性（T/S）不进任何镜。
- **防重叠（1.4）**：autoplan 已含 eng 镜 → 本 skill 领域镜**不重复跑 eng 视角**，只跑本项目 `spec-checklists/domains` 里 autoplan 不碰的 R 项，别让两层重复计数。

**fan-out（一条消息内全部派出，各子代理 fresh context、无用户交互、返回结构化 findings）**：

| 镜 | 数量 | 干什么 | 建议 model |
|----|------|--------|-----------|
| **领域镜** | 每命中领域 1 个 | 读 `{change_dir}` design/specs + 相关真实代码，逐条过 `spec-checklists/domains/<栈>` 的 **R 项**，列违反/存疑项（带文件:行证据） | Sonnet（判断） |
| **对抗镜** | 2-3 | 各从一个**不同角度**「证明这份 spec 会在实现期爆炸」：隐藏假设 / 失败模式 / 乐观估计与边界。默认 refuted=true，找不到爆点才放过 | Sonnet（对抗推理） |
| **接地镜** | 1 | grep/读真实代码，核验 spec 里**所有代码事实**（函数名/字段/API 路径/schema）是否真实存在且一致，列不符项 | Haiku（机械） |

> 每个子代理 prompt 必须自带：`{change_dir}` 路径、它负责的清单/角度、"返回结构化 findings 列表（每条带：问题 / 证据 file:line / **置信度(高/中/低)** / 严重度 / 建议），**不要 AskUserQuestion**"。

## 第三步：综合 + 对抗裁决 → 决策登记进报告（主 session · 强模型）

- **合并去重**：把 autoplan findings（Step1）+ 各镜 findings 汇成一池，**去重**（同一问题多镜命中合并）。
- **对抗裁决**：对每条 finding 判"是否真的会在实现期出问题"——对抗镜的反驳若 ≥ 多数成立则采信；存疑的降级或标"需人确认"。
- **反静默压制（escalate-not-drop，Q3 铁律）**：热主 session 裁决对 reviewer 子代理的 finding **只能降级 / 批注、不得静默丢弃**。判"不成立"的也须连理由落入报告「已裁掉」区（原始发现 + 裁掉理由），供人类设计门复核"裁得对不对"。
- **置信分流**：高=直接采信、中=标"需人确认"进决策区、低=**仍上抛（一行带过），绝不静默滤除**。**不照搬 sdflow-code-review 的数值 <80 一刀切**：设计漏掉的代价高（传导进实现），spec 评审优化召回而非精度；对抗裁决（强模型带上下文）已强于数值打分。
- **决策登记（取代中途 AskUserQuestion，G2）**：撞到"≥2 方案 / 核验不了的事实"→ **不打断**，写进报告「决策登记区」（见下格式）。
- 按 `design-diagrams.md`：命中触发的图**只验证存在/正确/未过时**，缺失/过时标记，不重画。
- **checkpoint 提交（P2c 第 2 次）**：产出报告 + amendments 后 → `~/.sdflow/hack/checkpoint-commit.sh spec-review "并行多镜审 + 合并报告 + spec-review-amendment"`。

**报告决策登记区格式**：

```
  spec-review-report.md · 决策登记区
  ┌─────────────────────────────────────────────────────┐
  │ [自动决策] D1  autoplan/裁决已定,附理由,默认接受可覆盖  │  高置信 → 默认采纳
  │ [需拍板]  Q1  ≥2 方案: 选项A/B + 推荐 + 各自后果       │  人工设计门时勾
  │ [需拍板]  Q2  核验不了的事实(函数名/字段/API 路径)     │  人工确认
  │ [已裁掉]  X1  reviewer 原始发现 + 主 session 裁掉理由   │  反静默压制,可审计(不静默丢)
  └─────────────────────────────────────────────────────┘
```

## 第四步：产出

- 写 `{change_dir}/spec-review-report.md`：**决策登记区**（自动决策 / 需拍板 / 已裁掉）+ 各镜 findings（带置信/严重度，低置信项一行带过、可审计不静默丢）+ 裁决。
- 据此更新 design/specs，改动处标 `[spec-review-amendment]`。
- **收敛口（1.6）**：结尾一句——是否建议进设计 HARD-GATE（用户批准 → writing-plans）。人工过这一份报告拍板，即阶段二唯一人类门。

---

## 模型选择（按本步性质，逐步定）

```
  主 session（协调/对抗裁决/决策登记/出报告）  强模型(Opus/Sonnet) ← 这是门禁,弱模型=假绿
  领域镜 / 对抗镜（判断、对抗推理）             Sonnet
  接地镜（grep/读码核验，机械）                 Haiku
```

依据：评审是门禁，综合判断这层弱模型会"看着过其实没深究"；机械读码可下放便宜模型。
**不要**把综合判断委派给弱模型子代理。中途不 AskUserQuestion（决策进报告，G2）。

## 与 autoplan 的分工（编排内两层，别重复）

| | autoplan（Step1） | 多镜 fan-out（Step2，本 skill 标准） |
|---|---|---|
| 镜 | CEO/design/eng/DX + 双声 | 领域镜 + 对抗镜 + 接地镜（我们的标准） |
| 清单 | 四个 gstack skill 各自的 | 本项目 spec-checklists/domains |
| 决策 | 自动决策（登记进报告） | 主 session 对抗裁决（登记进报告） |
| eng 视角 | **已含** | **不重复**（防重叠 1.4） |

## 注意

- **只做 prevention 焊不住的残差**（T/S 项交给 config/lint，不重扫）。
- **必须读真实代码**，不得只验 spec 自洽（接地镜专司此事）。
- 项目无关：规则路径一律经 `~/.sdflow/hack/resolve-workflow.sh` 解析（本地 pin 或全局 canonical），不硬编码 `openspec/workflow/`。
- checkpoint 脚本 = `~/.sdflow/hack/checkpoint-commit.sh`（setup.sh 全局安装）；缺失则先跑 setup，或退化为普通 `git add -A && git commit`。
