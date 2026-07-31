# Task 2 · Standards 轴 Finding 1 修复报告

## Finding

Step1 段（`sdflow-spec-review/SKILL.md` :182-193 附近）通篇未提及需在其内部同时踢出能力探针和
接地镜 dispatch。「能力探针」和「dispatch① 接地镜」的条款物理位置在 Step2 标题（:195）之下，
但声明应在「Step1 开始时」执行。按文档字面顺序执行的模型会先走完 Step1 再读到这些指令——此时
并行窗口已过。

## 修复内容

在 `sdflow-spec-review/SKILL.md` 第一步标题（原 :182）之后、原第 1 条编号列表之前，插入一条前向
指针 blockquote（原 :183 后新增 3 行，现文件 :184-186）：

```
> **并行前向指针**：进入本步的同时，MUST 按下方第二步「能力探针」与「两段 dispatch」的
> dispatch① 条款并行踢出接地镜（不等本步跑完）——具体条款见第二步，此处不重复。
```

## 核验

- Read 确认原文件 :182-193 只有标题 + 编号列表 1-6，无任何前向指针 → 复现 Finding 描述的问题。
- `git diff sdflow-spec-review/SKILL.md`：仅新增上述 3 行（1 空行 + 2 行 blockquote 正文），
  未改动其他任何字符；未重述 Step2「能力探针」「dispatch①」的详细条款内容，仅指路。

```diff
@@ -181,6 +181,9 @@
 
 ## 第一步：autoplan 子步（广审·原生执行，吃其 findings）
 
+> **并行前向指针**：进入本步的同时，MUST 按下方第二步「能力探针」与「两段 dispatch」的
+> dispatch① 条款并行踢出接地镜（不等本步跑完）——具体条款见第二步，此处不重复。
+
 1. **原生执行〔T25·R5〕**：主 session 经 Skill 机制原生执行 autoplan（其指令直接进主 session 执行，MUST NOT 派子代理读其 SKILL.md 转述模拟）。autoplan 跑自己的流程，prompt 不注入；其内部 AskUserQuestion 人类门（premise 确认 / 最终批准）按 G2/C5 适配：不弹窗，连同其自动决策一并登记进本评审报告「决策登记区」，设计门一次拍板。
 2. **主 session 落盘〔R5〕**：autoplan 原生机制只写 plan file，无「写任意路径」能力——执行完由**主 session** 汇总其结论 Write 落盘 `{change_dir}/gstack-review.md`（改动标 `[gstack-amendment]`），文件头 + 本报告 Step1 段各写 v1 锚行 `<!-- sdflow:step1-broad-review v1 mode="native" -->`；native 声明附一句侧信道佐证（如 autoplan 双声真实调用事实/运行痕迹）。
 3. **降级路径**：autoplan skill 不可用 → 子代理模拟广审 + 报告显式标注「模拟广审（降级模式）」+ 锚行 `mode="simulated"`，MUST NOT 伪装原生。
```

## 未改动范围

- 未改动 Step2「能力探针」「两段 dispatch」段落本身（:195 起）——指针只指路，不重述条款。
- 未改动其余任何行。

## 状态

- 修复已落盘，`git diff` 已核验只含预期的 3 行新增。
- 验收复选框 / checkpoint 标签按信号权威表不由本子代理打，留待双轴审通过后由执行模式补打。
